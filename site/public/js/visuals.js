// Renders one lesson visual into the stage. Every list-like item carries data-cue="n" so the
// player can reveal it in step with the narration. No innerHTML with content: text goes in as text.

export function h(tag, attrs, ...kids) {
  const el = tag === "svg" || attrs?.ns ? document.createElementNS("http://www.w3.org/2000/svg", tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false || k === "ns") continue;
    if (k === "class") el.setAttribute("class", v);
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "style" && typeof v === "object") for (const [p, val] of Object.entries(v)) (p.startsWith("--") ? el.style.setProperty(p, val) : (el.style[p] = val));
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return el;
}
const s = (tag, attrs, ...kids) => h(tag, { ...attrs, ns: 1 }, ...kids);
const cue = (el, i) => (el.classList.add("cue"), (el.dataset.cue = i + 1), el);
export const fmt = (v, unit = "") => {
  if (v == null || Number.isNaN(v)) return "–";
  const a = Math.abs(v);
  const t = a >= 10000 ? Math.round(v).toLocaleString("en-US") : a >= 100 ? v.toLocaleString("en-US", { maximumFractionDigits: 0 }) : a >= 10 ? v.toLocaleString("en-US", { maximumFractionDigits: 1 }) : v.toLocaleString("en-US", { maximumFractionDigits: 3 });
  return unit === "$" ? "$" + t : t + (unit || "");
};

// "cut-off" must not break after the hyphen in a 40px headline
const nb = (t) => String(t).replace(/([A-Za-z0-9])-([A-Za-z])/g, "$1" + String.fromCharCode(8209) + "$2");
const isNumberish = (c) => /^[\s~<>+\u2212\u2013$-]*[0-9][0-9.,]*\s*(%|pts?|K|M|x|days?|weeks?|min|s)?$/i.test(String(c).trim()) || ["-", "\u2013", "\u2014", ""].includes(String(c).trim());

function niceTicks(lo, hi, n = 5) {
  if (lo === hi) { lo -= 1; hi += 1; }
  const raw = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(raw)), norm = raw / mag;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const t0 = Math.floor(lo / step) * step, t1 = Math.ceil(hi / step) * step, out = [];
  for (let v = t0; v <= t1 + step / 2; v += step) out.push(+v.toFixed(10));
  return out;
}

let tipEl;
function tip(host, x, y, node) {
  if (!tipEl) tipEl = h("div", { class: "tip", role: "status" });
  if (!node) return tipEl.remove();
  tipEl.replaceChildren(node);
  const r = host.getBoundingClientRect();
  host.append(tipEl);
  tipEl.style.left = Math.max(60, Math.min(r.width - 60, x - r.left)) + "px";
  tipEl.style.top = Math.max(34, y - r.top) + "px";
}

const R = {
  title: (v) => [h("div", { class: "kicker", text: v.kicker }), h("h2", { text: v.title }), v.sub && h("p", { text: v.sub })],
  bullets: (v) => h("ul", { class: "bul" }, v.items.map((t, i) => cue(h("li", {}, h("span", { text: t })), i))),
  quote: (v) => [h("blockquote", { text: v.text }), v.sub && h("p", { class: "sub", text: v.sub })],
  compare: (v) => h("div", { class: "cmp" }, [v.left, v.right].map((d, i) => cue(h("div", {}, h("span", { class: "lab", text: d.label }), h("span", { class: "val" + (String(d.value).length > 34 ? " vlong" : String(d.value).length > 14 ? " long" : ""), text: nb(d.value) }), d.sub && h("span", { class: "sub", text: d.sub })), i))),
  stat: (v) => h("div", { class: "stats-v" }, v.stats.map((d, i) => cue(h("div", {}, h("b", { text: nb(d.value) }), h("span", { text: d.label })), i))),
  formula: (v) => h("div", { class: "formula" }, v.lines.map((t, i) => cue(h("div", { text: t }), i))),
  table: (v) => {
    const numeric = v.columns.map((_, k) => k > 0 && v.rows.length > 0 && v.rows.every((r) => isNumberish(r[k])));
    return h("div", { class: "tbl-wrap" }, h("table", { class: "tbl" },
      h("thead", {}, h("tr", {}, v.columns.map((c, k) => h("th", { class: numeric[k] ? "n" : null, text: c })))),
      h("tbody", {}, v.rows.map((r, i) => cue(h("tr", { class: (v.highlight || []).includes(i) ? "hl" : "" }, r.map((c, k) => h("td", { class: numeric[k] ? "n" : null, text: c }))), i)))));
  },
  flow: (v) => h("div", { class: "flow" }, v.steps.flatMap((st, i) => [i ? h("span", { class: "arr", text: "→", "aria-hidden": "true" }) : null,
    cue(h("div", { class: "st" }, h("b", { text: st.label }), st.sub && h("span", { text: st.sub })), i)])),
  matrix: (v) => {
    const pos = v.positive || "positive", neg = v.negative || "negative";
    const cell = (cls, n, label) => h("div", { class: "c " + cls }, h("b", { text: n.toLocaleString("en-US") }), h("span", { text: label }));
    return h("div", { class: "matrix" },
      h("div", {}), h("div", { class: "h", text: `Model said: ${pos}` }), h("div", { class: "h", text: `Model said: ${neg}` }),
      h("div", { class: "h side", text: `Actually ${pos}` }), cell("tp", v.tp, "caught"), cell("fn", v.fn, "missed"),
      h("div", { class: "h side", text: `Actually ${neg}` }), cell("fp", v.fp, "false alarm"), cell("tn", v.tn, "correctly left alone"));
  },
  timeline: (v) => {
    const pts = [...v.spans.flatMap((x) => [x.from, x.to]), ...(v.marks || []).map((m) => m.at)];
    const lo = Math.min(...pts), hi = Math.max(...pts), pct = (x) => ((x - lo) / (hi - lo || 1)) * 100;
    return h("div", { class: "timeline" },
      v.spans.map((sp, i) => cue(h("div", { class: "tl-row" }, h("div", { class: "span " + sp.kind, style: { left: pct(sp.from) + "%", width: Math.max(2, pct(sp.to) - pct(sp.from)) + "%" }, text: sp.label })), i)),
      (v.marks || []).map((m) => h("div", { class: "mark", style: { left: `calc(${pct(m.at)}% - 1px)` } }, h("span", { text: m.label }))));
  },
  code: (v) => h("pre", { class: "codeblk" }, highlight(v.code, v.lang)),
  bar: (v, host) => {
    const vals = v.data.map((d) => d.value), max = Math.max(0, ...vals), min = Math.min(0, ...vals), span = max - min || 1;
    const zero = (-min / span) * 100, hl = v.highlight || [], signed = min < 0 && max > 0;
    const dec = Math.min(2, Math.max(0, ...vals.map((x) => (String(x).split(".")[1] || "").length)));
    const show = (x) => (signed && x > 0 ? "+" : "") + (v.unit === "$" ? "$" : "") + x.toLocaleString("en-US", { minimumFractionDigits: Math.abs(x) >= 1000 ? 0 : dec, maximumFractionDigits: Math.abs(x) >= 1000 ? 0 : dec }) + (v.unit && v.unit !== "$" ? (v.unit === "%" ? "%" : " " + v.unit) : "");
    return h("div", { class: "bars" + (signed ? " signed" : ""), role: "img", "aria-label": v.title },
      v.data.map((d, i) => {
        const w = (Math.abs(d.value) / span) * 100, neg = d.value < 0;
        const row = h("div", { class: "bar-row" + (hl.length ? (hl.includes(i) ? "" : " mute") : ""), tabindex: 0 },
          h("span", { class: "lbl", text: d.label }),
          h("span", { class: "trk" }, min < 0 && h("span", { class: "zero", style: { left: zero + "%" } }),
            h("span", { class: "fill" + (neg ? " neg" : "") + (signed && !neg ? " up" : ""), style: { left: (neg ? zero - w : zero) + "%", width: w + "%" } })),
          h("span", { class: "v", text: show(d.value) }));
        const tipIt = (e) => tip(host, e.clientX ?? row.getBoundingClientRect().left + 80, row.getBoundingClientRect().top, h("span", {}, h("b", { text: show(d.value) }), " " + d.label));
        row.addEventListener("pointermove", tipIt); row.addEventListener("focus", tipIt);
        row.addEventListener("pointerleave", () => tip(host)); row.addEventListener("blur", () => tip(host));
        return cue(row, i);
      }));
  },
  line: (v, host) => lineChart(v, host, { width: 760 }),          // a slide is wide and short: a wider canvas fills it
};

function highlight(code, lang) {
  const kw = lang === "sql"
    ? /\b(select|from|where|and|or|group by|order by|join|left|on|as|case|when|then|else|end|with|having|between|interval|sum|count|avg|max|min|date|distinct|not|null|is|in|over|partition by)\b/gi
    : /\b(import|from|def|return|for|in|if|else|elif|and|or|not|None|True|False|print|lambda|with|as|class)\b/g;
  const rx = new RegExp(`(${lang === "sql" ? "--[^\\n]*" : "#[^\\n]*"})|('[^'\\n]*'|"[^"\\n]*")|(${kw.source})|(\\b\\d[\\d_.]*\\b)`, "g" + (lang === "sql" ? "i" : ""));
  const out = [];
  let last = 0, m;
  if (lang === "text") return [code];
  while ((m = rx.exec(code))) {
    if (m.index > last) out.push(code.slice(last, m.index));
    out.push(h("span", { class: m[1] ? "c" : m[2] ? "s" : m[3] ? "k" : "n", text: m[0] }));
    last = m.index + m[0].length;
  }
  out.push(code.slice(last));
  return out;
}

// a phone draws charts on a smaller canvas, so the same 11px labels stay readable instead of shrinking with the picture
export const narrow = () => matchMedia("(max-width: 640px)").matches;
export function lineChart(v, host, opt = {}) {
  const small = narrow(), W = small ? 340 : opt.width || 640, H = small ? Math.min(opt.height || 280, 280) : opt.height || 300, longNames = v.series.length > 1 && v.series.some((se) => se.name.length > 14);   // long names live in the legend, not at the line ends
  const m = { l: (small ? 38 : 46) + (v.ylabel ? 14 : 0), r: small || longNames ? 14 : opt.right ?? 92, t: 14, b: 40 };
  const colors = ["var(--s1)", "var(--s2)", "var(--s3)"];
  const xs = v.x, n = xs.length, all = v.series.flatMap((se) => se.values).filter((y) => y != null);
  const pad = (Math.max(...all) - Math.min(...all)) * 0.08 || 1;
  const cap = Math.max(...all) <= 1 && Math.max(...all) > 0.5 && v.unit !== "%" ? 1 : v.unit === "%" && Math.max(...all) <= 100 && Math.max(...all) > 60 ? 100 : Infinity;
  const ticks = niceTicks(opt.zero ? 0 : Math.min(...all) - pad, Math.min(cap, Math.max(...all) + pad), 4).filter((t) => t <= cap + 1e-9), y0 = ticks[0], y1 = ticks.at(-1);
  const numericX = xs.every((x) => typeof x === "number");
  const ratio = numericX && !opt.even && xs[0] > 0 && xs.at(-1) / xs[0] >= 16 && xs.every((x, i) => !i || x / xs[i - 1] <= 3.5);     // 100, 250, 500, 1,000 ...
  const xfrac = (i) => (ratio ? Math.log(xs[i] / xs[0]) / Math.log(xs.at(-1) / xs[0]) : numericX && !opt.even ? (xs[i] - xs[0]) / (xs.at(-1) - xs[0] || 1) : i / (n - 1 || 1));
  const xpos = (i) => m.l + xfrac(i) * (W - m.l - m.r);
  const ypos = (y) => m.t + (1 - (y - y0) / (y1 - y0)) * (H - m.t - m.b);
  const svg = s("svg", { class: "plot", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": v.title, style: `--ar:${(W / H).toFixed(3)}` });
  const yf = (t) => (Math.abs(y1) >= 10000 ? Math.round(t / 1000) + "K" : fmt(t, v.unit));      // one style per axis: compact once it reaches 10K
  for (const t of ticks) svg.append(s("line", { class: "gr", x1: m.l, x2: W - m.r, y1: ypos(t), y2: ypos(t) }), s("text", { x: m.l - 8, y: ypos(t) + 4, "text-anchor": "end" }, yf(t)));
  svg.append(s("line", { class: "ax", x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }));
  const every = Math.ceil(n / (small ? 5 : 10));
  xs.forEach((x, i) => { if (i % every === 0 || (i === n - 1 && (n - 1) % every > every * 0.6)) svg.append(s("text", { x: xpos(i), y: H - m.b + 16, "text-anchor": "middle" }, String(x))); });
  if (v.xlabel) svg.append(s("text", { class: "ttl", x: (m.l + W - m.r) / 2, y: H - 4, "text-anchor": "middle" }, v.xlabel + (ratio ? " (each step doubles, roughly)" : "")));
  if (v.ylabel) svg.append(s("text", { class: "ttl", x: 12, y: (m.t + H - m.b) / 2, "text-anchor": "middle", transform: `rotate(-90 12 ${(m.t + H - m.b) / 2})` }, v.ylabel));
  const ends = [];
  v.series.forEach((se, k) => {
    const pts = se.values.map((y, i) => (y == null ? null : [xpos(i), ypos(y)])).filter(Boolean);
    svg.append(s("path", { class: "ln", stroke: colors[k], d: pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ") }));
    if (n <= 16) pts.forEach((p) => svg.append(s("circle", { class: "ring", cx: p[0], cy: p[1], r: 4, fill: colors[k] })));
    else svg.append(s("circle", { class: "ring", cx: pts.at(-1)[0], cy: pts.at(-1)[1], r: 4, fill: colors[k] }));
    ends.push({ y: pts.at(-1)[1], name: se.name, val: se.values.at(-1) });
  });
  if (opt.mark != null && opt.mark >= 0 && opt.mark < n) {       // "you are here": the position a widget's slider has selected
    svg.append(s("line", { x1: xpos(opt.mark), x2: xpos(opt.mark), y1: m.t, y2: H - m.b, stroke: "var(--ink)", "stroke-width": 1.5 }));
    v.series.forEach((se, k) => { if (se.values[opt.mark] != null) svg.append(s("circle", { class: "ring", cx: xpos(opt.mark), cy: ypos(se.values[opt.mark]), r: 5.5, fill: colors[k] })); });
  }
  ends.sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 17) ends[i].y = ends[i - 1].y + 17;   // keep end labels apart
  if (m.r >= 60) ends.forEach((e) => svg.append(s("text", { class: "lab", x: W - m.r + 9, y: e.y + 4 }, v.series.length > 1 ? e.name : fmt(e.val, v.unit))));
  // hover: crosshair snaps to the nearest x, one tooltip lists every series
  const cross = s("line", { class: "ax", y1: m.t, y2: H - m.b, visibility: "hidden" });
  const hit = s("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent", tabindex: 0 });
  const at = (i, e) => {
    cross.setAttribute("x1", xpos(i)); cross.setAttribute("x2", xpos(i)); cross.setAttribute("visibility", "visible");
    const box = svg.getBoundingClientRect();
    tip(host, box.left + (xpos(i) / W) * box.width, box.top + (m.t / H) * box.height + 8,
      h("span", {}, h("b", { text: String(xs[i]) }), v.series.map((se) => h("div", {}, `${se.name}: `, h("b", { text: fmt(se.values[i], v.unit) })))));
  };
  let focusI = n - 1;
  hit.addEventListener("pointermove", (e) => {
    const box = svg.getBoundingClientRect(), px = ((e.clientX - box.left) / box.width) * W;
    let best = 0; for (let i = 1; i < n; i++) if (Math.abs(xpos(i) - px) < Math.abs(xpos(best) - px)) best = i;
    at((focusI = best), e);
  });
  hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); tip(host); });
  hit.addEventListener("keydown", (e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { focusI = Math.max(0, Math.min(n - 1, focusI + (e.key === "ArrowRight" ? 1 : -1))); at(focusI); e.preventDefault(); } });
  hit.addEventListener("blur", () => { cross.setAttribute("visibility", "hidden"); tip(host); });
  svg.append(cross, hit);
  const wrap = h("div", { class: "chart" });
  if (v.series.length > 1 || small) wrap.append(h("div", { class: "legend" }, v.series.map((se, k) => h("span", {}, h("i", { style: { background: colors[k] } }), se.name))));
  wrap.append(svg);
  // the table twin: every value reachable without hovering
  const table = h("div", { class: "tbl-wrap", hidden: true }, h("table", { class: "tbl" },
    h("thead", {}, h("tr", {}, h("th", { text: v.xlabel || "" }), v.series.map((se) => h("th", { text: se.name })))),
    h("tbody", {}, xs.map((x, i) => h("tr", {}, h("td", { text: String(x) }), v.series.map((se) => h("td", { text: fmt(se.values[i], v.unit) })))))));
  const tg = h("button", { class: "data-toggle", type: "button", text: "Show the numbers", onclick: () => { table.hidden = !table.hidden; svg.style.display = table.hidden ? "" : "none"; tg.textContent = table.hidden ? "Show the numbers" : "Show the chart"; } });
  if (!opt.noTable) wrap.append(table, tg);
  return wrap;
}

/** Builds the slide and returns it. The caller mounts it, so a slide that arrives late can be thrown away. */
export async function renderVisual(v, ctx) {
  const slide = h("section", { class: "slide t-" + v.type });
  if (v.type !== "title" && v.title) slide.append(h("h2", { text: v.title }));
  let body;
  if (v.type === "widget") {
    const { renderWidget } = await import("./widgets.js");
    body = await renderWidget(v, slide, ctx);
  } else body = (R[v.type] || (() => h("p", { text: `Unknown visual: ${v.type}` })))(v, slide);
  if (v.type === "title") slide.append(...[body].flat().filter(Boolean));
  else { slide.append(h("div", { class: "s-body" }, body)); if (v.note) slide.append(h("p", { class: "note", text: v.note })); }
  return slide;
}

// `waiting` is the set of item numbers whose marker the voice has not reached yet. An item with no marker in the
// narration is never in it, so it is on screen from the start (the authoring spec promises exactly that).
export function applyCues(slide, waiting) {
  slide.querySelectorAll(".cue").forEach((el) => el.classList.toggle("off", waiting.has(+el.dataset.cue)));
}
