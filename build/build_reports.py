"""Two HTML reports on the same churn model, for lesson 7-4 and the practice page.

  python build/build_reports.py   ->  site/public/reports/handsome.html, site/public/reports/plain.html

Both are generated from data/facts.json. The handsome one is the report an assistant writes by default: confident,
good-looking, and unanswerable. Its flaws are deliberate and listed at the bottom of this file's output
(site/public/reports/notes.json) so the practice page can reveal them. The plain one binds every number in its prose
to the results file, which is the habit the lesson teaches - so this script does exactly that.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
F = json.loads((ROOT / "data/facts.json").read_text(encoding="utf-8"))
OUT = ROOT / "site/public/reports"; OUT.mkdir(parents=True, exist_ok=True)

d, b, t, u = F["data"], F["baseline"], F["logreg"]["test"], F["uncertainty"]
k200 = next(x for x in F["top_k"] if x["k"] == 200)
k400 = next(x for x in F["top_k"] if x["k"] == 400)
cal = F["calibration"]["overall"]
size = {s["slice"].split(" ")[0]: s for s in F["slices"]["by_size"]}
tr = F["tracking_story"]
cmp_ = {c["comparison"]: c for c in F["noise"]["comparisons"]}
gam, trk = cmp_["gaming in April vs gaming in March"], cmp_["no tracking vs tracking"]
pct = lambda x, n=1: f"{100 * x:.{n}f}%"
n = lambda x: f"{x:,}"
src = []                                  # (what the sentence says, the value, where it was read from)
def bind(label, value, path):
    src.append((label, value, path)); return value

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><link rel="icon" href="../favicon.svg" type="image/svg+xml"><title>{title}</title><style>{css}</style></head><body>"""

# ------------------------------------------------------------------ the handsome one
css_h = """*{box-sizing:border-box}body{margin:0;font:16px/1.6 "Segoe UI",system-ui,sans-serif;color:#1d2433;background:#f4f6fb}
header{background:linear-gradient(120deg,#5b3df5,#b14bf4 55%,#ff7eb3);color:#fff;padding:54px 24px 64px;text-align:center}
header h1{margin:0 0 8px;font-size:2.4rem;letter-spacing:-.02em}header p{margin:0;opacity:.92;font-size:1.1rem}
main{max-width:880px;margin:-36px auto 60px;padding:0 20px}.card{background:#fff;border-radius:18px;padding:28px 30px;box-shadow:0 12px 40px -18px rgba(40,30,120,.35);margin-bottom:22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px}.kpi{background:linear-gradient(160deg,#f3efff,#fdeef6);border-radius:14px;padding:18px}
.kpi b{display:block;font-size:2.2rem;line-height:1.1;color:#5b3df5}.kpi span{color:#5a6276;font-size:.9rem}h2{margin:0 0 12px;font-size:1.35rem}
.bar{display:grid;grid-template-columns:190px 1fr 60px;gap:12px;align-items:center;margin:9px 0;font-size:.95rem}.bar i{display:block;height:16px;border-radius:9px;background:linear-gradient(90deg,#5b3df5,#ff7eb3)}
.tag{display:inline-block;background:#e9fbf1;color:#0d7a44;border-radius:99px;padding:3px 12px;font-weight:600;font-size:.85rem}.rec{border-left:5px solid #5b3df5;padding-left:16px}
footer{text-align:center;color:#8a90a2;font-size:.85rem;padding:0 0 40px}"""
handsome = HEAD.format(title="Churn Risk Model: Results", css=css_h) + f"""
<header><h1>Churn Risk Model: Results</h1><p>Identifying at-risk advertisers with high accuracy</p></header><main>
<div class="card"><span class="tag">Production ready</span><h2 style="margin-top:14px">Executive summary</h2>
<p>The model identifies at-risk advertisers with high accuracy. All 200 of the top 200 churned, giving account managers a reliable list to work from. Conversion tracking reduces churn by {abs(tr['naive_diff_pts']):.0f} points, making it the single most powerful lever for retention.</p>
<div class="kpis"><div class="kpi"><b>{pct(t['accuracy'])}</b><span>accuracy</span></div><div class="kpi"><b>{t['auc']}</b><span>AUC</span></div><div class="kpi"><b>{k200['churners']}</b><span>churners in the top 200</span></div></div></div>
<div class="card"><h2>What drives churn</h2>
<div class="bar"><span>No conversion tracking</span><i style="width:100%"></i><b>+{abs(tr['naive_diff_pts'])}</b></div>
<div class="bar"><span>Gaming vertical</span><i style="width:{100 * cmp_['gaming vs ecommerce']['difference_pts'] / abs(tr['naive_diff_pts']):.0f}%"></i><b>+{cmp_['gaming vs ecommerce']['difference_pts']}</b></div>
<div class="bar"><span>April, gaming</span><i style="width:{100 * gam['difference_pts'] / abs(tr['naive_diff_pts']):.0f}%"></i><b>+{gam['difference_pts']}</b></div>
<p>Gaming churn rose sharply in April, pointing to growing dissatisfaction in the vertical.</p></div>
<div class="card"><h2>Recommendation</h2><div class="rec"><p><b>Roll out conversion tracking to every account.</b> At {abs(tr['naive_diff_pts']):.0f} points of churn per account this is the highest-return action available, and the model's list tells account managers exactly where to start.</p></div></div>
</main><footer>Generated automatically · Churn Risk Model v2</footer></body></html>"""
(OUT / "handsome.html").write_text(handsome, encoding="utf-8")

# ------------------------------------------------------------------ the plain one
css_p = """*{box-sizing:border-box}body{margin:0;font:16px/1.6 Georgia,"Times New Roman",serif;color:#16211e;background:#fbfcfa}
main{max-width:820px;margin:0 auto;padding:36px 22px 70px}h1{font-size:1.7rem;margin:0 0 6px;line-height:1.2}h2{font-size:1.15rem;margin:30px 0 8px;border-top:2px solid #16211e;padding-top:10px}
.prov{font:13px/1.5 Consolas,"Cascadia Code",monospace;color:#44524d;background:#eef2ef;padding:10px 12px;border-radius:4px;margin:14px 0}
table{border-collapse:collapse;width:100%;font:14.5px/1.45 "Segoe UI",system-ui,sans-serif;margin:8px 0}th{text-align:left;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:#5b6c67;border-bottom:1.5px solid #16211e;padding:6px 8px}
td{padding:7px 8px;border-bottom:1px solid #d5deda;vertical-align:top}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.tier{font:600 12px "Segoe UI",sans-serif;letter-spacing:.04em;text-transform:uppercase;color:#0a6e63}
.no{background:#fdf1d2;border-left:4px solid #f0a81c;padding:10px 14px;margin:10px 0;font-family:"Segoe UI",system-ui,sans-serif;font-size:15px}small{color:#5b6c67}"""
top = bind("churners in the model's top 200", k200["churners"], "top_k[k=200].churners")
lo, hi = bind("95% interval on that count", u["top_200_churners_95"], "uncertainty.top_200_churners_95")
rnd = bind("a random 200 would hold", k200["random_expected"], "top_k[k=200].random_expected")
rule_n, rule_tp = bind("advertisers the hand rule flags", b["rule_flagged"], "baseline.rule_flagged"), bind("of whom churned", b["rule_tp"], "baseline.rule_tp")
same = bind("churners in the model's top 711", b["model_same_count"]["churners"], "baseline.model_same_count.churners")
auc, auc_ci = bind("AUC on the test months", t["auc"], "logreg.test.auc"), bind("its 95% interval", u["logreg_auc_95"], "uncertainty.logreg_auc_95")
tr_auc = bind("AUC on the training months", F["logreg"]["train_auc"], "logreg.train_auc")
said, happened = bind("average predicted churn, test", cal["avg_predicted"], "calibration.overall.avg_predicted"), bind("actual churn, test", cal["actual"], "calibration.overall.actual")
rs, rl = bind("share of small-account churners in the top 400", size["small"]["recall"], "slices.by_size[small].recall"), bind("share of large-account churners in the top 400", size["large"]["recall"], "slices.by_size[large].recall")
lost_l, lost_all = bind("spend lost to churn, large accounts", size["large"]["spend_lost_to_churn"], "slices.by_size[large].spend_lost_to_churn"), bind("spend lost to churn, all", F["slices"]["overall"]["spend_lost_to_churn"], "slices.overall.spend_lost_to_churn")
with_t, without_t = bind("churn with tracking", tr["churn_with_tracking"], "tracking_story.churn_with_tracking"), bind("churn without tracking", tr["churn_without_tracking"], "tracking_story.churn_without_tracking")
gap, gap_ci = bind("observed gap, points", trk["difference_pts"], "noise.comparisons[no tracking vs tracking].difference_pts"), bind("its interval", trk["ci95_pts"], "noise.comparisons[no tracking vs tracking].ci95_pts")
adj = bind("gap after adjusting, points", abs(tr["adjusted_diff_pts"]), "tracking_story.adjusted_diff_pts")
g_d, g_ci = bind("gaming, April minus March, points", gam["difference_pts"], "noise.comparisons[gaming in April vs gaming in March].difference_pts"), bind("its interval", gam["ci95_pts"], "noise.comparisons[gaming in April vs gaming in March].ci95_pts")
acc, base_acc = bind("model accuracy at cut-off 0.5", t["accuracy"], "logreg.test.accuracy"), bind("accuracy of predicting that everyone stays", b["always_no_accuracy"], "baseline.always_no_accuracy")

plain = HEAD.format(title="Churn model: what it can and cannot do", css=css_p) + f"""<main>
<h1>Churn model: what it can and cannot do</h1>
<div class="prov">Rows: one per advertiser, {n(d['n'])} in six monthly snapshots. Trained on Jan-Mar ({n(d['n_train'])} advertisers, {pct(d['churn_rate_train'])} churned). April left out: its 60-day outcomes were not yet known on the day May is scored. Tested once on May-Jun ({n(d['n_test'])} advertisers, {n(d['churners_test'])} churned, {pct(d['churn_rate_test'])}), which the model never saw. Churned = no spend at all in the 60 days after the snapshot. Model: logistic regression, 17 columns from the 8 weeks before the snapshot. Simulated data.</div>

<h2>What was found</h2>
<p>Of the {k200['k']} advertisers the model ranked highest, <b>{top} really churned</b> (95% interval {lo} to {hi}). A random {k200['k']} would hold about {rnd:.0f}. At the size of the list the team uses today, the model also does better than the hand rule: the rule "spend trend below 0.7" flags {rule_n} advertisers, of whom {rule_tp} churned; the model's top {rule_n} hold {same}.</p>
<table><tr><th>On the same {n(d['n_test'])} test advertisers</th><th class="n">Flagged</th><th class="n">Really churned</th><th class="n">Share right</th></tr>
<tr><td>Predict that everyone stays</td><td class="n">0</td><td class="n">0</td><td class="n">n/a</td></tr>
<tr><td>Hand rule: spend trend below 0.7</td><td class="n">{rule_n}</td><td class="n">{rule_tp}</td><td class="n">{pct(b['rule_precision'], 0)}</td></tr>
<tr><td>Model, same list size</td><td class="n">{rule_n}</td><td class="n">{same}</td><td class="n">{pct(b['model_same_count']['precision'], 0)}</td></tr>
<tr><td>Model, top {k200['k']}</td><td class="n">{k200['k']}</td><td class="n">{top}</td><td class="n">{pct(k200['precision'], 0)}</td></tr></table>
<p><small>Ranking quality: AUC {auc} on the test months (95% interval {auc_ci[0]} to {auc_ci[1]}), {tr_auc} on the training months. The two are close, so the model is not memorising.</small></p>

<h2>What not to conclude</h2>
<div class="no"><b>Accuracy says nothing here.</b> The model is {pct(acc)} accurate at a 0.5 cut-off; predicting that everyone stays is {pct(base_acc)} accurate and finds no one.</div>
<div class="no"><b>The scores are not percentages you can add up.</b> On the test months the model said {pct(said)} on average and {pct(happened)} churned. Use the scores to rank, not to total revenue at risk.</div>
<div class="no"><b>The list leans towards small accounts.</b> The top 400 hold {pct(rs, 0)} of the small-account churners and {pct(rl, 0)} of the large-account ones, while large accounts are {pct(lost_l / lost_all, 0)} of the spend lost to churn.</div>
<div class="no"><b>Nothing here says what causes churn</b>, or that calling a listed advertiser changes anything. That needs a test.</div>

<h2>Two findings, with the wording they have earned</h2>
<table><tr><th>Finding</th><th>Evidence</th><th>What may be said</th></tr>
<tr><td>Conversion tracking</td><td><span class="tier">Observed</span><br>{pct(with_t)} churned with tracking ({n(trk['n_b'])} advertisers) against {pct(without_t)} without ({n(trk['n_a'])}): a gap of {gap} points, interval {gap_ci[0]} to {gap_ci[1]}.<br><span class="tier">Adjusted</span><br>{adj} points after holding tenure, spend, campaigns, creatives, account manager and vertical fixed.<br><span class="tier">Tested</span><br>Not tested.</td><td>Advertisers with tracking churned less, and a gap remains after adjusting for what the table can see. Whether switching tracking on reduces churn is not known.</td></tr>
<tr><td>Gaming in April</td><td><span class="tier">Observed</span><br>{pct(gam['rate_b'])} of {gam['n_b']} advertisers in March, {pct(gam['rate_a'])} of {gam['n_a']} in April: +{g_d} points, interval {g_ci[0]} to +{g_ci[1]}.</td><td>The change is within what chance produces at these group sizes. No rise has been shown.</td></tr></table>

<h2>Where every number in the text came from</h2>
<table><tr><th>In the text</th><th class="n">Value</th><th>Read from the results file</th></tr>
{''.join(f'<tr><td>{a}</td><td class="n">{v}</td><td><small>{p}</small></td></tr>' for a, v, p in src)}</table>
<p><small>Every figure above was inserted by the script that built this page, from the same results file as the tables. None was typed.</small></p>
</main></body></html>"""
(OUT / "plain.html").write_text(plain, encoding="utf-8")

notes = {"handsome": [
    "'High accuracy' cannot be checked, and accuracy is the wrong boast: predicting that everyone stays is %s accurate." % pct(base_acc),
    "The summary says all 200 of the top 200 churned; the tile beside it says %d. The sentence was typed around an earlier, leaky run and never updated." % top,
    "No baseline, no interval, and no word on which rows the results come from.",
    "'Reduces churn by %.0f points' is a causal verb on an observed gap. Adjusted, the gap is %s points; in this simulated world the true effect is %s." % (abs(tr["naive_diff_pts"]), adj, abs(tr["truth"]["effect_pts"])),
    "'Rose sharply ... growing dissatisfaction' explains a change of +%s points whose interval runs from %s to +%s: it may not exist." % (g_d, g_ci[0], g_ci[1]),
    "The recommendation promises %.0f points per account from a practice nobody has tested." % abs(tr["naive_diff_pts"]),
    "Nothing says what not to conclude, and nothing is cut by segment."],
    "plain": ["A count, a baseline beside it at the same list size, an interval, and the rows it was measured on.",
              "Train and test scores side by side.", "A 'what not to conclude' section on the first screen.",
              "Each finding tagged observed, adjusted or tested, with wording to match.", "A source table: every number in the prose with where it was read from."]}
(OUT / "notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"reports written: {len(src)} bound numbers in the plain report")
