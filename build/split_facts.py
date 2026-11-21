"""Split the full results into (a) data/facts.json - the numbers people and reviewers read - and
(b) site/public/data/widgets.json - the long arrays the interactive widgets draw.
Run after build/run_analysis.mjs (which calls it)."""
import json
import os
import pathlib

SRC = pathlib.Path("data/facts_full.json")
F = json.loads(SRC.read_text(encoding="utf-8"))


def take(path):
    """Remove and return a nested key."""
    *head, last = path.split(".")
    cur = F
    for k in head:
        cur = cur[k]
    return cur.pop(last)


W = {
    "scores": take("widget_scores"),
    "depth_sweep": F["depth_sweep"],
    "tree": F["tree"]["root"],
    "calibration": {"bins": F["calibration"]["logreg"], "overall": F["calibration"]["overall"], "training": F["calibration"]["on_training_months"]},
    "economics": {k: F["economics"][k] for k in ("assumptions", "break_even_probability")},
    "practices": {"labels": F["happy"]["practices"], "naive": {k: v["diff_pts"] for k, v in F["happy"]["naive"].items()},
                  "adjusted": F["happy"]["adjusted_pts"], "truth": {k: v["effect_pts"] for k, v in F["happy"]["truth"].items()},
                  "outcome": "points of difference in the share of advertisers hitting their CPA goal",
                  "tracking": {"naive": F["tracking_story"]["naive_diff_pts"], "adjusted": F["tracking_story"]["adjusted_diff_pts"], "truth": F["tracking_story"]["truth"]["effect_pts"]}},
    "forecast": {"example": take("forecast.example_backtest"), "sample": take("forecast.sample"),
                 "mape": {m: v["mape"] for m, v in F["forecast"]["backtest"]["methods"].items()}},
    "anomalies": dict(take("series_anomalies.widget"), incidents=F["series_anomalies"]["incidents"]),
    "survival": dict(take("time_to_event.weekly_curve"), median=F["time_to_event"]["kaplan_meier"]["median_lifetime_weeks"]),
    "ticket_map": take("tickets.map") if "tickets" in F else None,
}
F.pop("roc", None)
out = pathlib.Path("data/facts.json.tmp")
out.write_text(json.dumps(F, indent=1), encoding="utf-8")
os.replace(out, "data/facts.json")
pathlib.Path("site/public/data").mkdir(parents=True, exist_ok=True)
pathlib.Path("site/public/data/widgets.json").write_text(json.dumps(W, separators=(",", ":")), encoding="utf-8")
print(f"facts.json {os.path.getsize('data/facts.json') // 1024} KB (for reading) · widgets.json {os.path.getsize('site/public/data/widgets.json') // 1024} KB (for the site)")
