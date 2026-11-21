// Interactive widgets: each draws real computed results from data/widgets.json and lets the
// learner move one control. Marks follow the chart rules used across the site: thin lines,
// one fixed colour per meaning (blue = stayed / default, orange = churned / emphasis), text in ink.
import { h, fmt, lineChart, narrow } from "./visuals.js";

const s = (tag, attrs, ...kids) => h(tag, { ...attrs, ns: 1 }, ...kids);
const pct = (v, d = 0) => (v == null || Number.isNaN(v) ? "–" : (100 * v).toFixed(d) + "%");
const NAMES = {
  spend_trend: "spend trend", active_days_28: "active days (of 28)", spend_8w: "spend, 8 weeks", ctr_pct: "click rate, %", tenure_weeks: "weeks as a customer",
  cpa_vs_goal: "CPA vs goal", creative_refresh_days: "days since a new creative", creatives_per_campaign: "creatives per campaign", days_since_login: "days since login",
  support_tickets_8w: "support tickets", payment_failures_8w: "payment failures", managed: "has an account manager", has_conversion_tracking: "has tracking",
  uses_auto_bidding: "uses auto-bidding", had_optimisation_review: "had a review", campaigns_active: "active campaigns",
};
const kpi = (label) => { const b = h("b", { text: "–" }); return { el: h("div", {}, b, h("span", { text: label })), set: (t) => (b.textContent = t) }; };
const slider = (label, min, max, step, value, on, show = (v) => v) => {
  const out = h("b", { text: show(value) });
  const inp = h("input", { type: "range", min, max, step, value, "aria-label": label, oninput: (e) => { out.textContent = show(+e.target.value); on(+e.target.value); } });
  return { el: h("div", { class: "ctl" }, h("label", {}, h("span", { text: label }), out), inp), inp, set: (v) => { inp.value = v; out.textContent = show(v); } };
};
const seg = (options, value, on) => {
  const wrap = h("div", { class: "seg-btns", role: "group" });
  options.forEach(([key, label]) => wrap.append(h("button", { type: "button", text: label, "aria-pressed": String(key === value), onclick: (e) => { wrap.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", "false")); e.target.setAttribute("aria-pressed", "true"); on(key); } })));
  return wrap;
};
/** A bare plot frame with hairline grid and axis labels; returns scale functions. */
function frame({ W = 640, H = 300, m = { l: 46, r: 16, t: 12, b: 34 }, xd, yd, yticks = 4, xfmt = (v) => v, yfmt = (v) => fmt(v), xticks = [], label = "" }) {
  if (narrow()) { W = Math.min(W, 340); H = Math.min(H, 250); m = { ...m, l: Math.min(m.l, 38) }; }      // phone: smaller canvas, same label size
  const svg = s("svg", { class: "plot", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": label, style: `--ar:${(W / H).toFixed(3)}` });
  const x = (v) => m.l + ((v - xd[0]) / (xd[1] - xd[0] || 1)) * (W - m.l - m.r), y = (v) => m.t + (1 - (v - yd[0]) / (yd[1] - yd[0] || 1)) * (H - m.t - m.b);
  for (let i = 0; yticks && i <= yticks; i++) { const v = yd[0] + ((yd[1] - yd[0]) * i) / yticks; svg.append(s("line", { class: "gr", x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }), s("text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, yfmt(v))); }
  svg.append(s("line", { class: "ax", x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }));
  xticks.forEach((v) => svg.append(s("text", { x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, xfmt(v))));
  return { svg, x, y, W, H, m };
}

const W = {
  // ---------- drag a cut-off over the real test scores ----------
  threshold(d) {
    const { p, y } = d.scores, n = p.length, pos = y.reduce((a, b) => a + b, 0);
    const bins = 25, hc = Array(bins).fill(0), hs = Array(bins).fill(0);
    p.forEach((v, i) => (y[i] ? hc : hs)[Math.min(bins - 1, Math.floor(v * bins))]++);
    const top = Math.max(...hc.map((v, i) => v + hs[i]));
    const f = frame({ W: 460, H: 230, m: { l: 8, r: 8, t: 10, b: 30 }, xd: [0, 1], yd: [0, Math.sqrt(top)], yticks: 0, xticks: [0, 0.25, 0.5, 0.75, 1], xfmt: (v) => String(v), label: "Churn scores of the 4,000 test advertisers" });
    const bw = (f.W - f.m.l - f.m.r) / bins - 2;
    for (let i = 0; i < bins; i++) {
      const a = Math.sqrt(hs[i] + hc[i]), b = Math.sqrt(hc[i]) * (hc[i] / (hs[i] + hc[i] || 1)) ** 0.5;
      f.svg.append(s("rect", { x: f.x(i / bins) + 1, y: f.y(a), width: bw, height: f.y(0) - f.y(a), fill: "var(--s1)", opacity: 0.55 }), s("rect", { x: f.x(i / bins) + 1, y: f.y(b), width: bw, height: f.y(0) - f.y(b), fill: "var(--s2)" }));
    }
    const line = s("line", { y1: f.m.t, y2: f.H - f.m.b, stroke: "var(--ink)", "stroke-width": 2 }), shade = s("rect", { y: f.m.t, height: f.H - f.m.t - f.m.b, fill: "var(--marker)", opacity: 0.14 });
    f.svg.prepend(shade); f.svg.append(line);
    const k = { fl: kpi("flagged"), tp: kpi("really churned"), fp: kpi("false alarms"), fn: kpi("churners missed"), pr: kpi("precision"), rc: kpi("recall") };
    const upd = (t) => {
      let tp = 0, fl = 0; for (let i = 0; i < n; i++) if (p[i] >= t) { fl++; tp += y[i]; }
      line.setAttribute("x1", f.x(t)); line.setAttribute("x2", f.x(t)); shade.setAttribute("x", f.x(t)); shade.setAttribute("width", f.W - f.m.r - f.x(t));
      k.fl.set(fl.toLocaleString()); k.tp.set(tp.toLocaleString()); k.fp.set((fl - tp).toLocaleString()); k.fn.set((pos - tp).toLocaleString()); k.pr.set(fl ? pct(tp / fl) : "–"); k.rc.set(pct(tp / pos));
    };
    const sl = slider("Flag everyone scoring at least", 0.02, 0.9, 0.01, 0.5, upd, (v) => v.toFixed(2));      // the lessons say "a cut-off of 0.5", so the slider does too
    upd(0.5);
    return h("div", { class: "wg" }, h("div", { class: "chart" }, h("div", { class: "legend" }, h("span", {}, h("i", { style: { background: "var(--s2)" } }), "churned"), h("span", {}, h("i", { style: { background: "var(--s1)", opacity: 0.55 } }), "stayed")), f.svg, sl.el),
      h("div", { class: "kpis" }, Object.values(k).map((x) => x.el)));
  },

  // ---------- tree depth: memorising vs learning ----------
  depth(d, host) {
    const rows = d.depth_sweep, k = { lv: kpi("leaves"), tr: kpi("score on training rows"), te: kpi("score on new advertisers"), gap: kpi("gap") };
    const chartHost = h("div");
    const draw = (i) => {
      const r = rows[i];
      chartHost.replaceChildren(lineChart({ title: "AUC by tree depth", xlabel: "Tree depth", ylabel: "AUC", x: rows.map((x) => x.depth), series: [{ name: "Training rows", values: rows.map((x) => x.train_auc) }, { name: "New advertisers", values: rows.map((x) => x.test_auc) }] }, host, { width: 480, height: 230, even: true, mark: i, right: 12, noTable: true }));
      k.lv.set(r.leaves.toLocaleString()); k.tr.set(r.train_auc.toFixed(3)); k.te.set(r.test_auc.toFixed(3)); k.gap.set((r.train_auc - r.test_auc).toFixed(3));
    };
    const sl = slider("Let the tree grow to depth", 0, rows.length - 1, 1, 2, draw, (i) => rows[i].depth);
    draw(2);
    return h("div", { class: "wg" }, h("div", { class: "chart" }, chartHost, sl.el), h("div", { class: "kpis" }, Object.values(k).map((x) => x.el)));
  },

  // ---------- the fitted depth-3 tree, click through it ----------
  tree(d) {
    const root = d.tree, levels = [[], [], [], []], max = 0.7;
    const walk = (n, depth, path, q) => { levels[depth].push({ n, path, q }); if (n.feature) { walk(n.yes, depth + 1, path + "y", "yes"); walk(n.no, depth + 1, path + "n", "no"); } };
    walk(root, 0, "", "");
    const els = {};
    const select = (path) => Object.entries(els).forEach(([p, el]) => el.classList.toggle("on", path.startsWith(p)));
    const node = ({ n, path, q }) => (els[path] = h("button", { class: "tnode" + (n.feature ? "" : " leaf"), type: "button", onclick: () => select(path) },
      h("span", { class: "q" }, path ? h("em", {}, q, h("span", { class: "arr", text: " → " })) : null, n.feature ? `${NAMES[n.feature] || n.feature} ≤ ${n.threshold}?` : h("span", { class: "lf" }, pct(n.churn, 0), h("span", { class: "w", text: " churn" }))),
      h("span", { class: "rate" }, h("i", { style: { width: `${Math.max(4, (n.churn / max) * 100)}%` } }), n.feature ? `${pct(n.churn, 0)} · ${n.n.toLocaleString()}` : n.n.toLocaleString())));
    const wrap = h("div", { class: "tree" }, levels.map((lv) => h("div", { class: "tlevel" }, lv.map(node))));
    select("yy");
    return wrap;
  },

  // ---------- naive vs adjusted vs true effect per practice: one row each, three marks on a shared scale ----------
  practices(d) {
    const P = d.practices, keys = Object.keys(P.labels), on = { naive: true, adjusted: false, truth: false }, T = ["naive", "adjusted", "truth"];
    const all = keys.flatMap((k) => T.map((t) => P[t][k])), lo = Math.min(0, ...all) - 3, hi = Math.max(...all) + 3, x = (v) => ((v - lo) / (hi - lo)) * 100;
    const colors = { naive: "var(--ink-3)", adjusted: "var(--s1)", truth: "var(--s2)" }, lab = { naive: "Naive gap", adjusted: "Adjusted", truth: "True effect" };
    const body = h("div", { class: "dots" });
    const draw = () => { const A = T.filter((t) => on[t]); body.style.setProperty("--k", A.length); body.replaceChildren(
      h("div", { class: "dot-row head" }, h("span"), h("span", { class: "trk" }, h("span", { class: "zl", style: { left: x(0) + "%" } }, h("em", { text: "0" }))), ...A.map((t) => h("span", { class: "num", text: lab[t] }))),
      ...keys.map((k) => h("div", { class: "dot-row" }, h("span", { class: "lbl", text: P.labels[k] }),
        h("span", { class: "trk" }, h("span", { class: "zero", style: { left: x(0) + "%" } }), ...A.map((t) => h("i", { class: t === "naive" ? "ring" : null, title: `${lab[t]}: ${P[t][k] > 0 ? "+" : ""}${P[t][k]} points`, style: { left: x(P[t][k]) + "%", background: colors[t] } }))),
        ...A.map((t) => h("span", { class: "num", text: (P[t][k] > 0 ? "+" : "") + P[t][k] }))))); };
    const btn = (t) => h("button", { type: "button", "aria-pressed": String(on[t]), onclick: (e) => { on[t] = !on[t]; if (!Object.values(on).some(Boolean)) on[t] = true; e.currentTarget.setAttribute("aria-pressed", String(on[t])); draw(); } }, h("i", { class: "key" + (t === "naive" ? " ring" : ""), style: { background: colors[t] } }), lab[t]);
    draw();
    return h("div", { class: "chart" }, h("div", { class: "row" }, h("div", { class: "seg-btns" }, T.map(btn)), h("span", { class: "note", text: "points of difference in hitting the CPA goal" })), body);
  },

  // ---------- predicted vs actual, by score band: two marks per band on one scale ----------
  calibration(d) {
    const c = d.calibration, hi = Math.max(...c.bins.map((b) => Math.max(b.predicted, b.actual))) * 1.06, x = (v) => (v / hi) * 100;
    const rows = c.bins.map((b) => h("div", { class: "dot-row" }, h("span", { class: "lbl", text: `said ${b.bin}` }),
      h("span", { class: "trk" }, h("i", { title: `said ${pct(b.predicted, 1)}`, style: { left: x(b.predicted) + "%", background: "var(--s1)" } }), h("i", { title: `happened ${pct(b.actual, 1)}`, style: { left: x(b.actual) + "%", background: "var(--s2)" } })),
      h("span", { class: "num", text: pct(b.predicted, 1) }), h("span", { class: "num", text: pct(b.actual, 1) }), h("span", { class: "num", style: { fontWeight: 400, color: "var(--ink-3)" }, text: b.n.toLocaleString() })));
    return h("div", { class: "wg", style: { gridTemplateColumns: "minmax(0, 1.9fr) minmax(0, 1fr)" } },
      h("div", { class: "dots" }, h("div", { class: "dot-row head" }, h("span", { text: "Score band" }), h("span", { class: "legend" }, h("span", {}, h("i", { class: "dot", style: { background: "var(--s1)" } }), "said"), h("span", {}, h("i", { class: "dot", style: { background: "var(--s2)" } }), "happened")), h("span", { class: "num", text: "Said" }), h("span", { class: "num", text: "Happened" }), h("span", { class: "num", text: "Accounts" })), rows),
      h("div", { class: "kpis" }, [["Test months: said", c.overall.avg_predicted], ["Test months: happened", c.overall.actual], ["Training months: said", c.training.avg_predicted], ["Training months: happened", c.training.actual]].map(([l, v]) => h("div", {}, h("b", { text: pct(v, 1) }), h("span", { text: l })))));
  },

  // ---------- how long a list, ranked by what ----------
  ranklist(d) {
    const { p, y, spend } = d.scores, n = p.length, A = d.economics.assumptions, gain = A.value_of_a_saved_advertiser * A.share_of_contacted_churners_saved;
    const idx = { prob: [...p.keys()].sort((a, b) => p[b] - p[a]), value: [...p.keys()].sort((a, b) => p[b] * spend[b] - p[a] * spend[a]) };
    const pos = y.reduce((a, b) => a + b, 0), lost = y.reduce((a, b, i) => a + b * spend[i], 0), rule = p.filter((v) => v >= d.economics.break_even_probability).length;
    const k = { ch: kpi("churners on the list"), sh: kpi("of all churners"), sp: kpi("of the spend about to be lost"), net: kpi("net value (toy numbers)"), lowest: kpi("lowest score on the list"), med: kpi("median spend of listed accounts") };
    let mode = "prob", size = 200;
    const upd = () => {
      const ids = idx[mode].slice(0, size), ch = ids.reduce((a, i) => a + y[i], 0), sp = ids.reduce((a, i) => a + y[i] * spend[i], 0), srt = ids.map((i) => spend[i]).sort((a, b) => a - b);
      k.ch.set(ch.toLocaleString()); k.sh.set(pct(ch / pos)); k.sp.set(pct(sp / lost)); k.net.set("$" + Math.round(ch * gain - size * A.cost_per_outreach).toLocaleString());
      k.lowest.set(pct(Math.min(...ids.map((i) => p[i])), 1)); k.med.set("$" + srt[Math.floor(srt.length / 2)].toLocaleString());
    };
    const sl = slider("Accounts on the list", 50, n, 50, size, (v) => { size = v; upd(); }, (v) => v.toLocaleString());
    upd();
    return h("div", { class: "wg" }, h("div", { class: "ctl" }, h("div", { class: "row" }, h("span", { class: "eyebrow", text: "Rank by" }), seg([["prob", "chance of churning"], ["value", "chance × spend"]], mode, (m) => { mode = m; upd(); })), sl.el,
      h("div", { class: "row" }, h("button", { class: "btn small", type: "button", text: `Apply the ${pct(d.economics.break_even_probability)} rule (${rule.toLocaleString()} accounts)`, onclick: () => { size = Math.round(rule / 50) * 50; sl.set(size); mode = "prob"; upd(); } }),
        h("button", { class: "btn small ghost", type: "button", text: "Default cut-off of 50%", onclick: () => { size = Math.max(50, Math.round(p.filter((v) => v >= 0.5).length / 50) * 50); sl.set(size); upd(); } })),
      h("p", { class: "note", text: `Toy economics: a call costs $${A.cost_per_outreach}, saves 1 churner in ${1 / A.share_of_contacted_churners_saved}, and a saved advertiser is worth $${A.value_of_a_saved_advertiser.toLocaleString()}.` })),
      h("div", { class: "kpis" }, Object.values(k).map((x) => x.el)));
  },

  // ---------- one backtest, method by method ----------
  forecast(d, host) {
    const e = d.forecast.example, M = [["last_value", "Yesterday's value"], ["same_weekday_last_week", "Same weekday last week"], ["average_of_last_4_same_weekdays", "Average of 4 same weekdays"], ["trend_plus_seasonality_regression", "Trend + rhythm + holidays"], ["gradient_boosting_on_calendar", "Boosted trees"]];
    const xs = [...e.history_dates, ...e.dates].map((t) => t.slice(5)), hist = e.history.length, ch = h("div"), k = { one: kpi("off per day, this forecast"), all: kpi("off per day, 12 backtests") };
    const draw = (m) => {
      const f = e.forecasts[m];
      ch.replaceChildren(lineChart({ title: "Daily spend and a 28-day forecast", unit: "", x: xs, series: [{ name: "Actual", values: [...e.history, ...e.actual] }, { name: "Forecast", values: [...Array(hist).fill(null), ...f] }] }, host, { height: 230, even: true, noTable: true }));
      k.one.set(pct(f.reduce((a, v, i) => a + Math.abs(v - e.actual[i]) / e.actual[i], 0) / f.length, 1)); k.all.set(pct(d.forecast.mape[m], 1));
    };
    draw("same_weekday_last_week");
    return h("div", { class: "chart" }, seg(M, "same_weekday_last_week", draw), ch, h("div", { class: "kpis" }, Object.values(k).map((x) => x.el)));
  },

  // ---------- incidents and three detectors ----------
  anomalies(d) {
    const a = d.anomalies, n = a.dates.length, inc = a.incident.map((v) => v >= 0), nInc = new Set(a.incident.filter((v) => v >= 0)).size;
    let mode = "naive", kk = 3;
    const step = 40000, lo = Math.floor((Math.min(...a.spend) * 0.92) / step) * step, hi = Math.ceil((Math.max(...a.spend) * 1.03) / step) * step;
    const f = frame({ H: 205, xd: [0, n - 1], yd: [lo, hi], yticks: (hi - lo) / step, yfmt: (v) => Math.round(v / 1000) + "K", xticks: [0, 60, 120, 180, 240], xfmt: (i) => new Date(a.dates[i] + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" }), label: "Daily spend with planted incidents" });
    f.svg.append(s("path", { class: "ln", stroke: "var(--s1)", "stroke-width": 1.4, d: a.spend.map((v, i) => (i ? "L" : "M") + f.x(i).toFixed(1) + " " + f.y(v).toFixed(1)).join(" ") }));
    a.spend.forEach((v, i) => { if (inc[i]) f.svg.append(s("circle", { class: "ring", cx: f.x(i), cy: f.y(v), r: 4.5, fill: "var(--s2)" })); });
    const alerts = s("g", {}); f.svg.append(alerts);
    const read = h("span", { class: "readout" });
    const upd = () => {
      const flag = a.spend.map((_, i) => (mode === "naive" ? Math.abs(a.day_over_day_pct[i]) > 0.15 : Math.abs(a[mode === "weekday" ? "z_same_weekday" : "z_forecast"][i]) > kk));
      alerts.replaceChildren(...flag.flatMap((on, i) => (on ? [s("line", { x1: f.x(i), x2: f.x(i), y1: f.m.t, y2: f.m.t + 9, stroke: inc[i] ? "var(--s2)" : "var(--ink-3)", "stroke-width": 2 })] : [])));
      read.replaceChildren(h("b", { text: flag.filter(Boolean).length }), " alert days · ", h("b", { text: `${new Set(a.incident.filter((v, i) => v >= 0 && flag[i])).size} of ${nInc}` }), " incidents caught · ", h("b", { text: flag.filter((on, i) => on && !inc[i]).length }), " false alarm days");
      sl.el.classList.toggle("ctl-off", mode === "naive");
    };
    const sl = slider("Band width", 2, 5, 0.5, 3, (v) => { kk = v; upd(); });
    upd();
    return h("div", { class: "chart" }, h("div", { class: "row" }, seg([["naive", "Moved >15% vs yesterday"], ["weekday", "vs same weekday"], ["forecast", "vs the forecast"]], mode, (m) => { mode = m; upd(); }), h("div", { style: { flex: "0 1 230px", minWidth: "170px" } }, sl.el)),
      h("div", { class: "row" }, read, h("div", { class: "legend" }, h("span", {}, h("i", { class: "dot", style: { background: "var(--s2)" } }), "planted incident"), h("span", {}, h("i", { style: { background: "var(--ink-3)", width: "3px", height: "10px" } }), "alert (orange = real)"))), f.svg);
  },

  // ---------- tickets as dots: near means similar ----------
  ticket_map(d) {
    const t = d.ticket_map, cats = [...new Set(t.category)], col = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)", "var(--s6)"];
    const pad = (a) => { const lo = Math.min(...a), hi = Math.max(...a), p = (hi - lo) * 0.06; return [lo - p, hi + p]; };
    const f = frame({ H: 300, m: { l: 10, r: 10, t: 8, b: 8 }, xd: pad(t.x), yd: pad(t.y), yticks: 0, label: "Support tickets placed by meaning" });
    f.svg.querySelectorAll("text, .gr").forEach((e) => e.remove());
    const shape = (k, cx, cy) => {     // a different mark per category, so identity never rests on colour alone
      const r = 4.2, c = { fill: col[k], class: "ring", "data-c": k };
      if (k === 0) return s("circle", { cx, cy, r, ...c });
      if (k === 1) return s("rect", { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r, ...c });
      if (k === 2) return s("path", { d: `M${cx} ${cy - r - 1}L${cx + r + 1} ${cy + r}L${cx - r - 1} ${cy + r}Z`, ...c });
      if (k === 3) return s("path", { d: `M${cx} ${cy - r - 1}L${cx + r + 1} ${cy}L${cx} ${cy + r + 1}L${cx - r - 1} ${cy}Z`, ...c });
      if (k === 4) return s("path", { d: `M${cx} ${cy + r + 1}L${cx + r + 1} ${cy - r}L${cx - r - 1} ${cy - r}Z`, ...c });
      return s("path", { d: `M${cx - r} ${cy - 1.6}h${r - 1.6}v${-r + 1.6}h3.2v${r - 1.6}h${r - 1.6}v3.2h${-r + 1.6}v${r - 1.6}h-3.2v${-r + 1.6}h${-r + 1.6}Z`, ...c });
    };
    t.x.forEach((x, i) => f.svg.append(shape(cats.indexOf(t.category[i]), f.x(x), f.y(t.y[i]))));
    const iso = (k) => f.svg.querySelectorAll("[data-c]").forEach((e) => (e.style.opacity = k == null || +e.dataset.c === k ? 1 : 0.12));
    const legend = h("div", { class: "legend" }, cats.map((c, k) => { const sw = s("svg", { viewBox: "0 0 14 14", width: 14, height: 14 }, shape(k, 7, 7)); const b = h("button", { type: "button", class: "chip", onpointerenter: () => iso(k), onpointerleave: () => iso(null), onfocus: () => iso(k), onblur: () => iso(null) }, sw, " " + c.replace("_", " ")); return b; }));
    return h("div", { class: "chart" }, legend, f.svg, h("p", { class: "note", text: "Point at a category to isolate it." }));
  },

  // ---------- share of advertisers still active ----------
  survival(d, host) {
    const v = d.survival, ch = h("div"), k = { a: kpi("still active"), b: kpi("with an account manager"), c: kpi("without") };
    let split = false, wk = 52;
    const draw = () => {
      const pick = (arr) => arr.filter((_, i) => i % 2 === 1 || i === 0);
      ch.replaceChildren(lineChart({ title: "Share of advertisers still active", xlabel: "Weeks since joining", ylabel: "", x: pick(v.weeks), unit: "%", series: split ? [{ name: "With manager", values: pick(v.with_manager).map((x) => 100 * x) }, { name: "Without", values: pick(v.without_manager).map((x) => 100 * x) }] : [{ name: "Everyone", values: pick(v.everyone).map((x) => 100 * x) }] }, host, { width: 480, height: 230, zero: true, mark: Math.round(wk / 2), right: 12, noTable: true }));
      k.a.set(pct(v.everyone[wk - 1])); k.b.set(pct(v.with_manager[wk - 1])); k.c.set(pct(v.without_manager[wk - 1]));
    };
    const sl = slider("After this many weeks", 1, 104, 1, wk, (x) => { wk = x; draw(); });
    draw();
    return h("div", { class: "wg" }, h("div", { class: "chart" }, ch, sl.el), h("div", { class: "ctl" }, seg([["all", "Everyone"], ["split", "By account manager"]], "all", (m) => { split = m === "split"; draw(); }),
      h("div", { class: "kpis" }, Object.values(k).map((x) => x.el)), h("p", { class: "note", text: `Half of advertisers are still active after ${v.median} weeks.` })));
  },
};

export async function renderWidget(v, host, ctx) {
  try {
    const fn = W[v.name];
    if (!fn) return h("p", { text: `Unknown widget: ${v.name}` });
    return fn(await ctx.widgets(), host);
  } catch (e) { console.error(e); return h("p", { class: "note", text: "This interactive could not be loaded. The narration continues without it." }); }
}
