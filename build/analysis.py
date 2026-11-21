"""Synthetic advertiser data + every number the course quotes (part 1: the advertiser table).

The data is SIMULATED from known equations, which buys two things a real dataset cannot:
nothing confidential is involved, and the TRUE causal effect of a practice is knowable
(re-run the same world with the practice switched on/off), so the lessons can show how far
a naive comparison lands from the truth.

Revised after the review council (docs/council/): a gap month between training and test, a
practice whose naive effect has the WRONG SIGN, a second prediction task with real
interactions, interventions that match the contrast the naive comparison makes, and
intervals on the numbers that get compared.

Runs under Pyodide (see run_analysis.mjs). RESULT = (facts json, csv, csv with trap column).
"""
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (adjusted_rand_score, average_precision_score, brier_score_loss, confusion_matrix,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

N, MONTHS = 12000, 6
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
TRAIN_LAST, TEST_FIRST = 2, 4        # train Jan-Mar, leave April out (its 60-day labels are not known when May is scored), test May-Jun
VERTS = ["ecommerce", "finance", "health", "gaming", "education", "other"]
V_P = [0.30, 0.14, 0.16, 0.12, 0.10, 0.18]
V_PERF = {"ecommerce": 0.00, "finance": -0.05, "health": 0.04, "gaming": 0.08, "education": 0.02, "other": 0.03}
V_CHURN = {"ecommerce": 0.00, "finance": -0.25, "health": 0.05, "gaming": 0.30, "education": 0.10, "other": 0.10}


def sig(x):
    return 1 / (1 + np.exp(-x))


rng = np.random.default_rng(20261121)
Z = dict(
    S=rng.normal(size=N),                      # hidden "sophistication" - never exported
    month=np.repeat(np.arange(MONTHS), N // MONTHS),
    vertical=rng.choice(VERTS, size=N, p=V_P),
    u_man=rng.uniform(size=N), u_trk=rng.uniform(size=N), u_ab=rng.uniform(size=N),
    u_tick=rng.uniform(size=N), u_churn=rng.uniform(size=N),
    e_spend=rng.normal(size=N), e_perf=rng.normal(size=N), e_trend=rng.normal(size=N),
    e_act=rng.normal(size=N), e_login=rng.normal(size=N), e_ctr=rng.normal(size=N),
    e_ref=rng.exponential(size=N), tenure=np.clip(rng.gamma(1.3, 30, size=N), 1, 400).round(),
    pay_fail=rng.poisson(0.07, size=N), camp=1 + rng.poisson(1.6, size=N),
)
Z["creat"] = 1 + rng.poisson(np.exp(0.75 + 0.35 * Z["S"]))
Z["e_next"] = rng.normal(size=N)
Z["u_review"] = rng.uniform(size=N)
Z["u_video"] = rng.uniform(size=N)


def simulate(do=None):
    """One pass through the world. `do` forces a practice for everyone (same noise)."""
    do = do or {}
    S, month = Z["S"], Z["month"]
    vperf = np.array([V_PERF[v] for v in Z["vertical"]])
    vchurn = np.array([V_CHURN[v] for v in Z["vertical"]])
    managed = (Z["u_man"] < sig(-0.9 + 0.9 * S)).astype(int)
    tracking = (Z["u_trk"] < sig(0.4 + 1.1 * S)).astype(int)
    if "tracking" in do:
        tracking = np.full(N, do["tracking"])
    auto_bid = (Z["u_ab"] < sig(-0.4 + 0.7 * S + 0.6 * tracking)).astype(int)
    if "auto_bid" in do:
        auto_bid = np.full(N, do["auto_bid"])
    creat = Z["creat"].copy()
    if "creat_min" in do:
        creat = np.maximum(creat, do["creat_min"])
    if "creat_max" in do:
        creat = np.minimum(creat, do["creat_max"])
    refresh = np.clip(Z["e_ref"] * np.exp(3.1 - 0.45 * S), 1, 120).round()
    if "refresh_values" in do:                 # give everyone a creative age drawn from a chosen group
        refresh = np.asarray(do["refresh_values"], float)
    # an optimisation review from the support team goes mostly to accounts that are struggling for
    # reasons the table cannot see (e_perf) - so the reviewed group LOOKS worse although the review helps
    review = (Z["u_review"] < sig(-1.5 + 1.4 * Z["e_perf"])).astype(int)
    if "review" in do:
        review = np.full(N, do["review"])
    tenure = Z["tenure"]
    log_spend = 7.4 + 0.6 * S + 0.5 * managed + 1.0 * Z["e_spend"]
    log_ratio = (0.10 - 0.13 * S - 0.12 * auto_bid - 0.10 * (creat >= 4) + 0.0045 * (refresh - 30)
                 - 0.04 * tracking - 0.10 * review + vperf + 0.36 * Z["e_perf"])
    log_trend = -0.03 - 0.45 * log_ratio + 0.05 * S + 0.30 * Z["e_trend"]
    active = np.clip(np.round(28 * sig(1.2 + 0.5 * S - 0.9 * log_ratio + 0.8 * Z["e_act"])), 0, 28)
    login = np.clip(np.round(np.exp(1.0 - 0.4 * S + 0.6 * log_ratio + 0.7 * Z["e_login"])), 0, 60)
    tickets = np.floor(-np.log(Z["u_tick"]) * np.exp(-0.7 + 0.7 * np.maximum(log_ratio, 0) + 0.25 * managed))
    ctr = 0.25 * np.exp(0.2 * S - 0.15 * log_ratio + 0.3 * Z["e_ctr"])
    new_struggling = (tenure < 6) & (log_ratio > 0.25)
    gaming_shock = (month == 5) & (Z["vertical"] == "gaming")
    logit = (-2.20 + 1.5 * np.clip(log_ratio, -1, 1.5) - 1.3 * log_trend - 0.07 * (active - 16)
             - 0.010 * np.minimum(tenure, 104) + 0.8 * Z["pay_fail"] + 0.22 * np.minimum(tickets, 5)
             - 0.35 * S - 0.15 * tracking - 0.30 * managed + 0.9 * new_struggling + vchurn
             + 0.05 * month + 1.4 * gaming_shock)
    churn = (Z["u_churn"] < sig(logit)).astype(int)
    # outcome 2: dollars spent in the NEXT 8 weeks (0 for churners) - the regression target
    log_next = (log_spend - 0.02 + 0.55 * log_trend - 0.45 * np.clip(log_ratio, -1, 1.5) + 0.10 * managed
                - 0.30 * Z["pay_fail"] + 0.15 * (tenure < 12) + 0.05 * S + 0.25 * Z["e_next"])
    spend_next = np.where(churn == 1, 0.0, np.exp(log_next)).round(0)
    # outcome 3: adopts the new video ad format - built from THRESHOLDS and COMBINATIONS, not a tidy weighted sum
    savvy = (creat >= 4) & (ctr >= 0.28)
    scale_ready = (log_spend >= np.log(3000)) & (log_ratio <= 0.05)
    growth = (tenure >= 8) & (tenure <= 52) & (active >= 18)
    midsize = (log_spend > np.log(1500)) & (log_spend < np.log(8000))          # a hump: mid-sized spenders adopt most
    lv = (-3.9 + 1.5 * savvy + 1.1 * scale_ready + 1.2 * (savvy & scale_ready) + 0.9 * growth
          + 1.4 * ((auto_bid == 1) & (creat >= 4)) - 0.9 * ((auto_bid == 1) & (creat < 4))     # the same setting helps or hurts depending on another
          + 1.1 * midsize - 1.2 * (tenure < 4) + 0.2 * S)
    video = (Z["u_video"] < sig(lv)).astype(int)
    df = pd.DataFrame({
        "advertiser_id": np.arange(100000, 100000 + N),
        "snapshot_month": [MONTH_NAMES[m] for m in month],
        "vertical": Z["vertical"],
        "managed": managed,
        "tenure_weeks": tenure.astype(int),
        "spend_8w": np.exp(log_spend).round(0),
        "spend_trend": np.exp(log_trend).round(3),
        "active_days_28": active.astype(int),
        "days_since_login": login.astype(int),
        "campaigns_active": Z["camp"],
        "creatives_per_campaign": creat,
        "creative_refresh_days": refresh.astype(int),
        "has_conversion_tracking": tracking,
        "uses_auto_bidding": auto_bid,
        "had_optimisation_review": review,
        "cpa_vs_goal": np.where(tracking == 1, np.exp(log_ratio).round(3), np.nan),
        "ctr_pct": ctr.round(3),
        "support_tickets_8w": tickets.astype(int),
        "payment_failures_8w": Z["pay_fail"],
        "spend_next_8w": spend_next,
        "adopted_video_next_60d": video,
        "churned_next_60d": churn,
    })
    hidden = pd.DataFrame({"hit_goal": (np.exp(log_ratio).round(3) <= 1).astype(int), "S": S, "month": month,
                           "log_next_without_noise": log_next - 0.25 * Z["e_next"], "churn_logit": logit, "true_churn_prob": sig(logit)})
    return df, hidden


def r(x, n=3):
    return round(float(x), n)


CONT = ["tenure_weeks", "spend_8w", "spend_trend", "active_days_28", "days_since_login", "campaigns_active",
        "creatives_per_campaign", "creative_refresh_days", "cpa_vs_goal", "ctr_pct", "support_tickets_8w", "payment_failures_8w"]
BIN = ["managed", "has_conversion_tracking", "uses_auto_bidding", "had_optimisation_review"]
CAT = ["vertical"]
NUM = CONT + BIN
OUTCOMES = ["spend_next_8w", "adopted_video_next_60d", "hit_cpa_goal", "churned_next_60d"]
GROUPS = [("profile", ["tenure_weeks", "spend_8w", "campaigns_active", "managed", "vertical"]),
          ("setup and practices", ["creatives_per_campaign", "creative_refresh_days", "has_conversion_tracking", "uses_auto_bidding", "had_optimisation_review"]),
          ("performance vs goal", ["cpa_vs_goal", "ctr_pct"]),
          ("recent behaviour", ["spend_trend", "active_days_28", "days_since_login", "support_tickets_8w", "payment_failures_8w"])]


def lr_pipe(cont=CONT, binf=BIN, cat=CAT, extra=()):
    """Logistic regression: continuous columns filled (median) and standardised, flags as 0/1,
    vertical one-hot with ecommerce as the reference category."""
    parts = []
    if cont:
        parts.append(("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), list(cont)))
    if list(binf) + list(extra):
        parts.append(("bin", "passthrough", list(binf) + list(extra)))
    if cat:
        parts.append(("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), list(cat)))
    return Pipeline([("pre", ColumnTransformer(parts)), ("m", LogisticRegression(max_iter=3000, C=1.0))])


def metrics(p, yy, thr=0.5):
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
    return {"auc": r(roc_auc_score(yy, p)), "pr_auc": r(average_precision_score(yy, p)), "brier": r(brier_score_loss(yy, p), 4),
            "threshold": thr, "flagged": int(tp + fp), "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
            "accuracy": r((tp + tn) / len(yy)), "precision": r(tp / max(tp + fp, 1)), "recall": r(tp / max(tp + fn, 1))}


def tree_json(model, names, key="rate"):
    t = model.tree_

    def node(i):
        d = {"n": int(t.n_node_samples[i]), key: r(t.value[i][0][1] / t.value[i][0].sum(), 3)}
        if t.children_left[i] != -1:
            f, thr = names[t.feature[i]], float(t.threshold[i])
            if f == "spend_8w":
                thr = 10 ** thr
            d.update({"feature": f, "threshold": r(thr, 2), "yes": node(int(t.children_left[i])), "no": node(int(t.children_right[i]))})
        return d

    return node(0)


def boot_ci(fn, n, reps=500, seed=3):
    rb = np.random.default_rng(seed)
    vals = [fn(rb.integers(0, n, n)) for _ in range(reps)]
    return [r(np.percentile(vals, 2.5)), r(np.percentile(vals, 97.5))]


def tune_boosting(Xg_tr, ytr, cv):
    grid = []
    for depth in (1, 2, 3, 4):
        for iters in (100, 300):
            for lr_ in (0.03, 0.1):
                sc_ = cross_val_score(HistGradientBoostingClassifier(max_iter=iters, learning_rate=lr_, max_depth=depth, random_state=0),
                                      Xg_tr, ytr, cv=cv, scoring="roc_auc")
                grid.append({"max_depth": depth, "max_iter": iters, "learning_rate": lr_, "cv_auc": r(sc_.mean(), 4), "cv_std": r(sc_.std(), 4)})
    grid.sort(key=lambda g: -g["cv_auc"])
    return grid, dict(max_iter=grid[0]["max_iter"], learning_rate=grid[0]["learning_rate"], max_depth=grid[0]["max_depth"], random_state=0)


def main():
    F = {}
    df, hid = simulate()
    y = df.churned_next_60d.values
    month = hid.month.values
    tr, te = month <= TRAIN_LAST, month >= TEST_FIRST
    X = df[NUM + CAT].copy()
    X["spend_8w"] = np.log10(X["spend_8w"])  # spend is very skewed: model its order of magnitude
    yt = y[te]
    nt = int(te.sum())
    trk = (df.has_conversion_tracking == 1).values

    # A column that only exists because the table was exported AFTER the outcome was known.
    rng2 = np.random.default_rng(7)
    delay = rng2.integers(60, 121, N)              # exported 60-120 days after each snapshot
    came_back = rng2.uniform(size=N) < 0.22        # some churners re-activated before the export
    lapsed_later = rng2.uniform(size=N) < 0.10     # some survivors stopped after the 60-day window
    leak = np.where(y == 1, np.where(came_back, rng2.exponential(5, N), delay + rng2.integers(0, 10, N)),
                    np.where(lapsed_later, rng2.uniform(0, 1, N) * (delay - 60), rng2.exponential(4, N))).round()

    F["data"] = {
        "n": N, "n_train": int(tr.sum()), "n_gap": int((month == 3).sum()), "n_test": nt, "months": MONTH_NAMES,
        "train_months": "Jan-Mar", "gap_month": "Apr", "test_months": "May-Jun", "per_month": N // MONTHS,
        "why_a_gap": "churn is judged over the 60 days after a snapshot, so on the day you score the May advertisers you do not yet know who churned from the April cohort; training on April would use answers that did not exist yet",
        "one_row_is": "one advertiser, observed once (12,000 different advertisers; nobody appears twice)",
        "churn_rate": r(y.mean(), 4), "churn_rate_train": r(y[tr].mean(), 4), "churn_rate_test": r(yt.mean(), 4),
        "churners_train": int(y[tr].sum()), "churners_test": int(yt.sum()), "churners_total": int(y.sum()),
        "churn_by_month": {MONTH_NAMES[m]: r(y[month == m].mean(), 4) for m in range(MONTHS)},
        "tracking_rate": r(trk.mean(), 4), "n_tracked": int(trk.sum()), "n_untracked": int((~trk).sum()),
        "missing_cpa_rate": r(df.cpa_vs_goal.isna().mean(), 4),
        "hit_goal_rate_tracked": r(hid.hit_goal[trk].mean(), 4),
        "video_adoption_rate": r(df.adopted_video_next_60d.mean(), 4),
        "columns": list(df.columns), "feature_columns": NUM + CAT, "n_feature_columns": len(NUM + CAT),
        "outcome_columns": {"churned_next_60d": "no spend at all in the 60 days after the snapshot",
                            "spend_next_8w": "dollars spent in the 8 weeks after the snapshot (0 for churners)",
                            "adopted_video_next_60d": "started using the video ad format in the 60 days after the snapshot",
                            "hit_cpa_goal": "CPA at or below the advertiser's own target during the 8 weeks BEFORE the snapshot; empty without conversion tracking"},
        "sample_rows": json.loads(df.iloc[[2, 4, 0, 5, 3]].to_json(orient="records")),
        "median_spend_8w": r(df.spend_8w.median(), 0),
        "feature_stats_train": {c: {"mean": r(df[c][tr].mean(), 3), "sd": r(df[c][tr].std(), 3), "median": r(df[c][tr].median(), 3),
                                    "p10": r(df[c][tr].quantile(0.1), 3), "p90": r(df[c][tr].quantile(0.9), 3)} for c in CONT + BIN},
    }

    def grp(col):
        return {str(k): {"n": int(len(g)), "churn": r(g.churned_next_60d.mean(), 4)} for k, g in df.groupby(col)}

    F["churn_by"] = {c: grp(c) for c in ["has_conversion_tracking", "managed", "vertical", "uses_auto_bidding", "had_optimisation_review"]}

    # ---- logistic regression: the course's main churn model
    lr = lr_pipe().fit(X[tr], y[tr])
    p_lr = lr.predict_proba(X[te])[:, 1]
    names = [n.split("__", 1)[1] for n in lr.named_steps["pre"].get_feature_names_out()]
    coef = lr.named_steps["m"].coef_[0]
    kind = {**{c: "per 1 SD" for c in CONT}, **{c: "yes vs no" for c in BIN}}
    # "one SD" must be the step the model itself used: the scaler's, fitted after empty cells were filled with the median.
    # (For cpa_vs_goal the raw column's SD among tracked advertisers is wider, and would not reproduce the model's pushes.)
    sd_model = dict(zip(CONT, lr.named_steps["pre"].named_transformers_["num"].named_steps["sc"].scale_))
    sd_note = {c: r(sd_model[c], 3) for c in CONT}

    def prob_shift(c):                    # how far the average predicted probability moves, in points
        Xa, Xb = X[te].copy(), X[te].copy()
        if c in BIN:
            Xa[c], Xb[c] = 1, 0
        else:
            Xa[c] = Xa[c] + sd_model[c]
        return r(100 * (lr.predict_proba(Xa)[:, 1].mean() - lr.predict_proba(Xb)[:, 1].mean()), 1)

    F["logreg"] = {
        "test": metrics(p_lr, yt), "train_auc": r(roc_auc_score(y[tr], lr.predict_proba(X[tr])[:, 1])),
        "intercept": r(lr.named_steps["m"].intercept_[0]), "n_weights": int(len(coef) + 1),
        "how_to_read": "coef is the change in log-odds of churn; odds_ratio = exp(coef). Continuous features are standardised, so 'per 1 SD'. spend_8w is on a log10 scale. Flags are yes vs no. Verticals are relative to ecommerce. avg_probability_shift_pts is the plain-language version: how many points the average predicted churn probability moves. None of these is a causal effect.",
        "coefs": sorted([{"feature": n, "coef": r(c), "odds_ratio": r(np.exp(c)), "unit": kind.get(n, "vs ecommerce"),
                          **({"one_sd_is": sd_note[n]} if n in sd_note else {}),
                          **({"avg_probability_shift_pts": prob_shift(n)} if n in NUM else {})} for n, c in zip(names, coef)], key=lambda d: -abs(d["coef"])),
        "best_possible_auc": r(roc_auc_score(yt, hid.true_churn_prob.values[te])),
        "best_possible_note": "the AUC of the simulation's own true churn probability, which uses hidden inputs no model is given; nothing trained on this table can beat it",
    }
    order = np.argsort(-p_lr)

    # ---- baselines (test months)
    rule = (df.spend_trend < 0.7).astype(int).values
    tn, fp, fn, tp = confusion_matrix(yt, rule[te]).ravel()
    k_rule = int(tp + fp)
    F["baseline"] = {"always_no_accuracy": r(1 - yt.mean()), "always_no_recall": 0.0, "always_no_churners_found": 0,
                     "rule": "spend_trend < 0.7", "rule_flagged": k_rule, "rule_precision": r(tp / (tp + fp)), "rule_recall": r(tp / (tp + fn)),
                     "rule_accuracy": r((tp + tn) / nt), "rule_tp": int(tp), "rule_fp": int(fp), "rule_fn": int(fn), "rule_tn": int(tn),
                     "model_same_count": {"flagged": k_rule, "churners": int(yt[order[:k_rule]].sum()),
                                          "precision": r(yt[order[:k_rule]].mean()), "recall": r(yt[order[:k_rule]].sum() / yt.sum())}}

    # ---- decision tree (depth 3) + depth sweep
    tree_pre = ColumnTransformer([("num", SimpleImputer(strategy="constant", fill_value=-1), NUM),
                                  ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    Xt_tr, Xt_te = tree_pre.fit_transform(X[tr]), tree_pre.transform(X[te])
    tnames = [n.split("__", 1)[1] for n in tree_pre.get_feature_names_out()]
    dt = DecisionTreeClassifier(max_depth=3, min_samples_leaf=100, random_state=0).fit(Xt_tr, y[tr])
    F["tree"] = {"depth": 3, "min_rows_per_leaf": 100, "leaves": int(dt.get_n_leaves()), "test": metrics(dt.predict_proba(Xt_te)[:, 1], yt),
                 "note": "this is the tree shown in the lessons: depth 3 and at least 100 training rows in every end point. depth_sweep grows trees with no minimum leaf size, so its depth-3 row scores slightly differently.",
                 "train_auc": r(roc_auc_score(y[tr], dt.predict_proba(Xt_tr)[:, 1])),
                 "root": tree_json(dt, tnames, "churn"), "text": export_text(dt, feature_names=tnames, decimals=2)}
    sweep = []
    for d in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]:
        m = DecisionTreeClassifier(max_depth=d, random_state=0).fit(Xt_tr, y[tr])
        pt = m.predict_proba(Xt_te)[:, 1]
        cv_d = cross_val_score(DecisionTreeClassifier(max_depth=d, random_state=0), Xt_tr, y[tr], scoring="roc_auc",
                               cv=StratifiedKFold(5, shuffle=True, random_state=0))
        sweep.append({"depth": d, "leaves": int(m.get_n_leaves()), "train_auc": r(roc_auc_score(y[tr], m.predict_proba(Xt_tr)[:, 1])),
                      "cv_auc_on_training_months": r(cv_d.mean()), "test_auc": r(roc_auc_score(yt, pt)), "distinct_scores_on_test": int(len(np.unique(pt))),
                      "train_acc": r(m.score(Xt_tr, y[tr])), "test_acc": r(m.score(Xt_te, yt))})
    F["depth_sweep"] = sweep
    F["depth_sweep_note"] = ("test_auc is shown to demonstrate over-fitting; it must not be used to CHOOSE the depth. cv_auc_on_training_months "
                             "(5-fold cross-validation inside January-March) is the honest way to choose: best depth by cross-validation is "
                             f"{max(sweep, key=lambda s_: s_['cv_auc_on_training_months'])['depth']}, best by the test months is {max(sweep, key=lambda s_: s_['test_auc'])['depth']}.")

    # ---- forest and boosting
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=1).fit(Xt_tr, y[tr])
    p_rf = rf.predict_proba(Xt_te)[:, 1]
    F["forest"] = {"test": metrics(p_rf, yt), "train_auc": r(roc_auc_score(y[tr], rf.predict_proba(Xt_tr)[:, 1])), "n_trees": 300}
    gb_pre = ColumnTransformer([("num", "passthrough", NUM), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    Xg_tr, Xg_te = gb_pre.fit_transform(X[tr]), gb_pre.transform(X[te])
    gnames = [n.split("__", 1)[1] for n in gb_pre.get_feature_names_out()]
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    U = dict(max_iter=200, learning_rate=0.05, max_depth=4)
    gb0 = HistGradientBoostingClassifier(random_state=0, **U).fit(Xg_tr, y[tr])
    grid, GBP = tune_boosting(Xg_tr, y[tr], cv)
    gb = HistGradientBoostingClassifier(**GBP).fit(Xg_tr, y[tr])
    p_gb = gb.predict_proba(Xg_te)[:, 1]
    F["boosting"] = {"test": metrics(p_gb, yt), "train_auc": r(roc_auc_score(y[tr], gb.predict_proba(Xg_tr)[:, 1])),
                     "params": {k: v for k, v in GBP.items() if k != "random_state"},
                     "tuning": {"grid_size": len(grid), "chosen_by": "5-fold cross-validation on the training months only", "best": grid[0], "top5": grid[:5], "worst": grid[-1]},
                     "untuned": {"params": U, "test_auc": r(roc_auc_score(yt, gb0.predict_proba(Xg_te)[:, 1])),
                                 "train_auc": r(roc_auc_score(y[tr], gb0.predict_proba(Xg_tr)[:, 1]))}}

    # ---- cross-validation on the training months, and uncertainty on the test months
    s_lr = cross_val_score(lr_pipe(), X[tr], y[tr], cv=cv, scoring="roc_auc")
    s_gb = cross_val_score(HistGradientBoostingClassifier(**GBP), Xg_tr, y[tr], cv=cv, scoring="roc_auc")
    F["cv"] = {"folds": 5, "note": "shuffled folds are fine here only because every row is a different advertiser from the same three months; with repeated advertisers or a time trend, folds must respect groups and time",
               "logreg": {"scores": [r(s) for s in s_lr], "mean": r(s_lr.mean()), "std": r(s_lr.std()), "min": r(s_lr.min()), "max": r(s_lr.max())},
               "boosting": {"scores": [r(s) for s in s_gb], "mean": r(s_gb.mean()), "std": r(s_gb.std()), "min": r(s_gb.min()), "max": r(s_gb.max())}}
    F["uncertainty"] = {
        "method": "bootstrap: 500 resamples of the 4,000 test advertisers (covers the luck of which advertisers landed in the test months, not the luck of training)",
        "logreg_auc_95": boot_ci(lambda i: roc_auc_score(yt[i], p_lr[i]), nt), "boosting_auc_95": boot_ci(lambda i: roc_auc_score(yt[i], p_gb[i]), nt),
        "difference_logreg_minus_boosting_95": boot_ci(lambda i: roc_auc_score(yt[i], p_lr[i]) - roc_auc_score(yt[i], p_gb[i]), nt),
        "difference_logreg_minus_tree_95": boot_ci(lambda i: roc_auc_score(yt[i], p_lr[i]) - roc_auc_score(yt[i], dt.predict_proba(Xt_te)[:, 1][i]), nt),
        "difference_point": r(roc_auc_score(yt, p_lr) - roc_auc_score(yt, p_gb), 3),
        "top_200_churners_95": [int(v) for v in boot_ci(lambda i: yt[i][np.argsort(-p_lr[i])[:200]].sum(), nt)],
        "recall_at_half_95": boot_ci(lambda i: ((p_lr[i] >= 0.5) & (yt[i] == 1)).sum() / max(yt[i].sum(), 1), nt),
        "precision_at_half_95": boot_ci(lambda i: yt[i][p_lr[i] >= 0.5].mean(), nt)}

    # ---- how to hold data out: random vs time, and what peeking at April would change
    i_tr, i_te = train_test_split(np.arange(N), test_size=1 / 3, random_state=0, stratify=y)
    lr_r = lr_pipe().fit(X.iloc[i_tr], y[i_tr])
    lr_apr = lr_pipe().fit(X[month <= 3], y[month <= 3])
    F["split"] = {"random_split_auc": r(roc_auc_score(y[i_te], lr_r.predict_proba(X.iloc[i_te])[:, 1])), "time_split_auc": F["logreg"]["test"]["auc"],
                  "trained_through_april_auc": r(roc_auc_score(yt, lr_apr.predict_proba(X[te])[:, 1])),
                  "note": "all logistic regression. On this table the three numbers barely differ, because every row is a separate advertiser and little changes between months. The time split and the gap are still the only honest design: they are what expose the June surprise, and on real tables with repeated advertisers the difference is large (see panel_leak)."}
    pa = lr.predict_proba(X)[:, 1]
    gaming = (df.vertical == "gaming").values

    def pva(mk):
        n_, a_ = int(mk.sum()), float(y[mk].mean())
        return {"n": n_, "predicted": r(pa[mk].mean(), 3), "actual": r(a_, 3), "actual_plus_minus": r(1.96 * np.sqrt(a_ * (1 - a_) / n_), 3)}

    F["drift"] = {"auc_by_month": {MONTH_NAMES[m]: r(roc_auc_score(y[month == m], pa[month == m])) for m in (4, 5)},
                  "gaming_churn_by_month": {MONTH_NAMES[m]: r(y[(month == m) & gaming].mean(), 3) for m in range(MONTHS)},
                  "gaming_may": pva((month == 4) & gaming), "gaming_jun": pva((month == 5) & gaming),
                  "non_gaming_jun": pva((month == 5) & ~gaming), "all_may": pva(month == 4), "all_jun": pva(month == 5),
                  "by_vertical_jun": {v: pva((month == 5) & (df.vertical == v).values) for v in VERTS},
                  "base_rate_creep": "churn also drifts up slightly every month in the simulation, so by May-June the model's probabilities run a little low everywhere",
                  "what_happened": "in the simulation, something changes for gaming advertisers in June only; no column records it"}

    # ---- leakage demo (same model, one extra column)
    XL = X.copy()
    XL["days_since_last_spend"] = leak
    lrl = lr_pipe(cont=CONT + ["days_since_last_spend"]).fit(XL[tr], y[tr])
    p_leak = lrl.predict_proba(XL[te])[:, 1]
    F["leakage"] = {"feature": "days_since_last_spend",
                    "why": "it was read from the live accounts table when each month's snapshot was exported, 60-120 days AFTER that snapshot's date - the day the prediction is supposed to be made",
                    "auc_with_leak": r(roc_auc_score(yt, p_leak)), "auc_honest": F["logreg"]["test"]["auc"],
                    "top_200_churners_with_leak": int(yt[np.argsort(-p_leak)[:200]].sum()), "top_200_churners_honest": int(yt[order[:200]].sum()),
                    "mean_value_churned": r(leak[y == 1].mean(), 1), "mean_value_stayed": r(leak[y == 0].mean(), 1),
                    "median_value_churned": r(np.median(leak[y == 1]), 0), "median_value_stayed": r(np.median(leak[y == 0]), 0),
                    "leak_metrics_at_half": metrics(p_leak, yt)}

    # ---- thresholds, top-k, lift, calibration: logistic regression on the test months
    F["thresholds"] = [metrics(p_lr, yt, thr) for thr in [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7]]
    dec, cum = [], 0
    for k in range(10):
        idx = order[k * len(order) // 10:(k + 1) * len(order) // 10]
        cum += int(yt[idx].sum())
        dec.append({"decile": k + 1, "n": int(len(idx)), "churners": int(yt[idx].sum()), "churn_rate": r(yt[idx].mean()),
                    "lift": r(yt[idx].mean() / yt.mean(), 2), "cum_capture": r(cum / yt.sum())})
    F["lift"] = dec
    F["top_k"] = [{"k": k, "churners": int(yt[order[:k]].sum()), "precision": r(yt[order[:k]].mean()), "recall": r(yt[order[:k]].sum() / yt.sum()),
                   "random_expected": r(k * yt.mean(), 1), "times_better_than_random": r(yt[order[:k]].mean() / yt.mean(), 1),
                   "lowest_score_on_list": r(p_lr[order[k - 1]], 3)} for k in (100, 200, 400, 800)]
    cal = {}
    for nm, p in (("logreg", p_lr), ("boosting", p_gb), ("forest", p_rf)):
        bins = [0, .05, .1, .2, .3, .4, .5, .7, 1.0001]
        rows = []
        for a, b in zip(bins[:-1], bins[1:]):
            mk = (p >= a) & (p < b)
            if mk.sum() >= 15:
                rows.append({"bin": f"{int(a * 100)}-{int(min(b, 1) * 100)}%", "n": int(mk.sum()), "predicted": r(p[mk].mean()), "actual": r(yt[mk].mean())})
        cal[nm] = rows
    F["calibration"] = dict(cal, overall={"avg_predicted": r(p_lr.mean()), "actual": r(yt.mean())},
                            on_training_months={"avg_predicted": r(lr.predict_proba(X[tr])[:, 1].mean()), "actual": r(y[tr].mean())},
                            why_it_runs_low="the model learned from months with a lower churn rate than the months it is tested on; its ranking is intact, its percentages are a little low")
    fpr, tpr, _ = roc_curve(yt, p_lr)
    step = max(1, len(fpr) // 60)
    F["roc"] = [{"fpr": r(a), "tpr": r(b)} for a, b in list(zip(fpr, tpr))[::step]] + [{"fpr": 1.0, "tpr": 1.0}]
    mrow = lambda nm, key, note: {"model": nm, "test_auc": F[key]["test"]["auc"], "train_auc": F[key]["train_auc"], "pr_auc": F[key]["test"]["pr_auc"],
                                  "top_200_churners": int(yt[np.argsort(-{"tree": dt.predict_proba(Xt_te)[:, 1], "logreg": p_lr, "forest": p_rf, "boosting": p_gb}[key])[:200]].sum()), "note": note}
    F["model_table"] = [
        {"model": "Always predict 'stays'", "test_auc": 0.5, "train_auc": 0.5, "pr_auc": r(yt.mean()), "top_200_churners": r(200 * yt.mean(), 0), "note": "the floor"},
        mrow("Decision tree, depth 3", "tree", "at most 8 readable rules"),
        mrow("Logistic regression", "logreg", "one weight per feature"),
        mrow("Random forest, 300 trees", "forest", "many trees, averaged"),
        {"model": "Gradient boosting, default-ish settings", "test_auc": F["boosting"]["untuned"]["test_auc"], "train_auc": F["boosting"]["untuned"]["train_auc"], "pr_auc": None,
         "top_200_churners": int(yt[np.argsort(-gb0.predict_proba(Xg_te)[:, 1])[:200]].sum()), "note": "depth 4, 200 rounds"},
        mrow("Gradient boosting, tuned by cross-validation", "boosting", f"depth {GBP['max_depth']}, {GBP['max_iter']} rounds"),
    ]

    # ---- which feature GROUPS carry the signal (logistic regression, cumulative)
    used, abl = [], []
    for nm, cols in GROUPS:
        used = used + cols
        m = lr_pipe([c for c in used if c in CONT], [c for c in used if c in BIN], [c for c in used if c in CAT]).fit(X[tr][used], y[tr])
        abl.append({"added": nm, "columns_added": cols, "n_columns": len(used), "test_auc": r(roc_auc_score(yt, m.predict_proba(X[te][used])[:, 1]))})
    only = {}
    for nm, cols in GROUPS:
        m = lr_pipe([c for c in cols if c in CONT], [c for c in cols if c in BIN], [c for c in cols if c in CAT]).fit(X[tr][cols], y[tr])
        only[nm] = r(roc_auc_score(yt, m.predict_proba(X[te][cols])[:, 1]))
    aucs = {"tree": F["tree"]["test"]["auc"], "logistic": F["logreg"]["test"]["auc"], "forest": F["forest"]["test"]["auc"], "boosting": F["boosting"]["test"]["auc"]}
    F["feature_groups"] = {"cumulative": abl, "each_group_alone": only,
                           "spread_across_feature_sets": r(abl[-1]["test_auc"] - abl[0]["test_auc"], 3),
                           "spread_across_algorithms": {"best_minus_worst": r(max(aucs.values()) - min(aucs.values()), 3), "best": max(aucs, key=aucs.get), "worst": min(aucs, key=aucs.get),
                                                        "gap_between_the_two_best": r(sorted(aucs.values())[-1] - sorted(aucs.values())[-2], 3)}}

    # ---- what drives the predictions
    pi = permutation_importance(lr, X[te], yt, scoring="roc_auc", n_repeats=10, random_state=0)
    rp = np.random.default_rng(4)
    grouped = []
    for nm, cols in GROUPS:
        drops = []
        for _ in range(10):
            Xp = X[te].copy()
            perm = rp.permutation(nt)
            Xp[cols] = Xp[cols].values[perm]
            drops.append(roc_auc_score(yt, p_lr) - roc_auc_score(yt, lr.predict_proba(Xp)[:, 1]))
        grouped.append({"group": nm, "columns": cols, "auc_drop": r(np.mean(drops), 4)})
    F["importance"] = {"method": "permutation importance on the test months: shuffle one column, see how far AUC falls", "model": "logistic regression",
                       "rows": sorted([{"feature": n, "auc_drop": r(m, 4), "std": r(s, 4)} for n, m, s in zip(NUM + CAT, pi.importances_mean, pi.importances_std)],
                                      key=lambda d: -d["auc_drop"]),
                       "grouped": {"method": "shuffle a whole group of related columns together, so correlated columns cannot cover for each other", "rows": sorted(grouped, key=lambda d: -d["auc_drop"])},
                       "caveat": "columns that carry overlapping information share (and so understate) importance; importance says what the model relies on, not what causes churn"}
    pdp = {}
    for feat in ("cpa_vs_goal", "spend_trend", "active_days_28", "tenure_weeks"):
        j = gnames.index(feat)
        col = Xg_tr[:, j].astype(float)
        base = Xg_tr[~np.isnan(col)] if feat == "cpa_vs_goal" else Xg_tr
        rows_ = []
        for v in np.linspace(np.nanpercentile(col, 5), np.nanpercentile(col, 95), 12):
            Xv = base.copy()
            Xv[:, j] = v
            rows_.append({"x": r(v, 2), "avg_predicted_churn": r(gb.predict_proba(Xv)[:, 1].mean(), 4)})
        pdp[feat] = rows_
    F["partial_dependence"] = {"model": "tuned gradient boosting", "method": "set the column to x for every training advertiser and average the predictions (for cpa_vs_goal: every training advertiser with conversion tracking, since the others have no value to move)", "curves": pdp,
                               "caveat": "describes the MODEL's behaviour, not what would happen if you changed the advertiser; it also averages over combinations that never occur together"}
    pre_ = lr.named_steps["pre"]
    Ztr, Zte = pre_.transform(X[tr]), pre_.transform(X[te])
    Ztr, Zte = (a.toarray() if hasattr(a, "toarray") else a for a in (Ztr, Zte))
    contrib = (Zte - Ztr.mean(axis=0)) * coef
    base_logit = float(lr.named_steps["m"].intercept_[0] + (Ztr.mean(axis=0) * coef).sum())
    te_idx = np.where(te)[0]
    cpa_te = X[te].cpa_vs_goal.values
    hi_pick = int(next(i for i in order[20:] if not np.isnan(cpa_te[i])))
    mid_pick = int(next(i for i in order[450:] if not np.isnan(cpa_te[i])))
    ex = []
    for label, pick in (("high risk", hi_pick), ("borderline", mid_pick), ("low risk", int(np.argsort(p_lr)[400]))):
        c = sorted(zip(names, contrib[pick]), key=lambda t: -abs(t[1]))[:5]
        row = df.iloc[te_idx[pick]]
        ex.append({"label": label, "advertiser_id": int(row.advertiser_id), "predicted": r(p_lr[pick], 3), "churned": int(yt[pick]),
                   "row": {k: (None if pd.isna(row[k]) else (row[k].item() if hasattr(row[k], "item") else row[k])) for k in NUM + CAT},
                   "top_pushes": [{"feature": n, "log_odds_push": r(v, 2)} for n, v in c]})
    F["explain_examples"] = {"average_advertiser_probability": r(sig(base_logit), 3), "how_to_read": "positive push = raises churn risk relative to an average advertiser; pushes add up on the log-odds scale", "examples": ex}

    # ---- early warning or already gone? what the top of the list is made of
    act, trd = df.active_days_28.values[te], df.spend_trend.values[te]
    winding = (act <= 7) | (trd < 0.5)
    alive = (act >= 14) & (trd >= 0.8)
    ord_alive = np.argsort(-np.where(alive, p_lr, -1))
    F["early_warning"] = {
        "winding_down_means": "7 or fewer active days in the last 28, or spend in the last 4 weeks under half of the 4 weeks before",
        "still_fully_active_means": "14 or more active days and spend holding at 80% or more",
        "top_200": {"winding_down": int(winding[order[:200]].sum()), "share_winding_down": r(winding[order[:200]].mean()),
                    "still_fully_active": int(alive[order[:200]].sum()), "churn_rate_of_winding_down_on_list": r(yt[order[:200]][winding[order[:200]]].mean())},
        "everyone": {"share_winding_down": r(winding.mean()), "churn_rate_winding_down": r(yt[winding].mean()), "share_still_fully_active": r(alive.mean()), "churn_rate_still_fully_active": r(yt[alive].mean()),
                     "share_of_all_churners_who_were_still_fully_active": r((alive & (yt == 1)).sum() / yt.sum())},
        "model_on_still_fully_active_only": {"n": int(alive.sum()), "churners": int(yt[alive].sum()), "auc": r(roc_auc_score(yt[alive], p_lr[alive])),
                                             "top_200_churners": int(yt[ord_alive[:200]].sum()), "top_200_precision": r(yt[ord_alive[:200]].mean()),
                                             "random_200_expected": r(200 * yt[alive].mean(), 1)},
    }

    # ---- money: what a ranked list is worth, under stated (hypothetical) assumptions
    A = {"cost_per_outreach": 30, "value_of_a_saved_advertiser": 1500, "share_of_contacted_churners_saved": 0.2}
    gain = A["value_of_a_saved_advertiser"] * A["share_of_contacted_churners_saved"]
    net = np.cumsum(yt[order] * gain - A["cost_per_outreach"])
    econ = [{"contacted": k, "churners_reached": int(yt[order[:k]].sum()), "net_value": int(round(net[k - 1])),
             "net_value_if_random": int(round(k * yt.mean() * gain - k * A["cost_per_outreach"])), "score_of_last_advertiser_on_list": r(p_lr[order[k - 1]], 3)} for k in (100, 200, 400, 800, 1600, nt)]
    be = A["cost_per_outreach"] / gain
    k_rule_ = int((p_lr >= be).sum())
    F["economics"] = {"assumptions": A, "assumptions_are": "hypothetical round numbers to show the method; replace with your own",
                      "break_even_probability": r(be, 3),
                      "the_rule": "contact an advertiser if THEIR OWN churn probability is above cost / (value x save rate). It is a rule about the next advertiser on the list (marginal), not about the average hit rate of the whole list.",
                      "table": econ,
                      "list_from_the_rule": {"contacted": k_rule_, "net_value": int(round(net[k_rule_ - 1])), "churners_reached": int(yt[order[:k_rule_]].sum())},
                      "best_list_in_hindsight": {"contacted": int(np.argmax(net) + 1), "net_value": int(round(net.max()))},
                      "default_cutoff_half": {"contacted": int((p_lr >= 0.5).sum()), "net_value": int(round(net[int((p_lr >= 0.5).sum()) - 1]))},
                      "whole_list_average_hit_rate": r(yt.mean(), 3),
                      "caveat": "assumes outreach saves 1 in 5 churners whoever they are; the model predicts who will leave, not who can be persuaded (see uplift)"}

    # ---- Question: what separates advertisers who hit their goal
    d1 = df[trk].copy()
    d1["hit_goal"] = hid.hit_goal[trk].values
    d1["creatives_4plus"] = (d1.creatives_per_campaign >= 4).astype(int)
    d1["fresh_creatives"] = (d1.creative_refresh_days <= 14).astype(int)
    PR = ["uses_auto_bidding", "creatives_4plus", "fresh_creatives", "managed", "had_optimisation_review"]
    naive = {}
    for p_ in PR:
        a, b = d1[d1[p_] == 1].hit_goal.mean(), d1[d1[p_] == 0].hit_goal.mean()
        se = np.sqrt(a * (1 - a) / (d1[p_] == 1).sum() + b * (1 - b) / (d1[p_] == 0).sum())
        naive[p_] = {"hit_rate_with": r(a), "hit_rate_without": r(b), "diff_pts": r(100 * (a - b), 1), "ci95_pts": [r(100 * (a - b - 1.96 * se), 1), r(100 * (a - b + 1.96 * se), 1)],
                     "adoption": r(d1[p_].mean()), "n_with": int((d1[p_] == 1).sum()), "n_without": int((d1[p_] == 0).sum())}
    happy, unhappy = d1[d1.hit_goal == 1], d1[d1.hit_goal == 0]
    prof = {c: {"happy": r(happy[c].mean(), 2), "unhappy": r(unhappy[c].mean(), 2), "stat": "mean"} for c in
            ["uses_auto_bidding", "creatives_per_campaign", "creative_refresh_days", "managed", "had_optimisation_review", "active_days_28", "tenure_weeks", "campaigns_active", "ctr_pct", "spend_trend"]}
    prof["spend_8w"] = {"happy": r(happy.spend_8w.median(), 0), "unhappy": r(unhappy.spend_8w.median(), 0), "stat": "median"}
    prof["churned_next_60d"] = {"happy": r(happy.churned_next_60d.mean(), 3), "unhappy": r(unhappy.churned_next_60d.mean(), 3), "stat": "rate"}

    def true_effect(on, off, outcome, mask=None):
        a_df, a_h = simulate(on)
        b_df, b_h = simulate(off)
        a, b = (a_h.hit_goal.values, b_h.hit_goal.values) if outcome == "hit_goal" else (a_df.churned_next_60d.values, b_df.churned_next_60d.values)
        mk = np.ones(N, bool) if mask is None else mask
        return {"if_everyone_did": r(a[mk].mean()), "if_nobody_did": r(b[mk].mean()), "effect_pts": r(100 * (a[mk].mean() - b[mk].mean()), 1)}

    rf_ = np.random.default_rng(12)
    ref_all = df.creative_refresh_days.values
    fresh_vals, stale_vals = ref_all[trk & (ref_all <= 14)], ref_all[trk & (ref_all > 14)]
    truth = {"uses_auto_bidding": true_effect({"auto_bid": 1}, {"auto_bid": 0}, "hit_goal", trk),
             "creatives_4plus": true_effect({"creat_min": 4}, {"creat_max": 3}, "hit_goal", trk),
             # compare like with like: give everyone the creative ages of the fresh group, then of the stale group
             "fresh_creatives": dict(true_effect({"refresh_values": rf_.choice(fresh_vals, N)}, {"refresh_values": rf_.choice(stale_vals, N)}, "hit_goal", trk),
                                     median_age_fresh_group=r(np.median(fresh_vals), 0), median_age_stale_group=r(np.median(stale_vals), 0)),
             "managed": {"if_everyone_did": None, "if_nobody_did": None, "effect_pts": 0.0,
                         "note": "in the simulation an account manager has no effect on CPA performance at all (it does lower churn directly)"},
             "had_optimisation_review": true_effect({"review": 1}, {"review": 0}, "hit_goal", trk)}
    CTRL = ["tenure_weeks", "spend_8w", "campaigns_active"]
    Aj = d1[PR + CTRL].copy()
    Aj["spend_8w"] = np.log10(Aj.spend_8w)
    Aj = pd.concat([Aj, pd.get_dummies(d1.vertical, dtype=float)], axis=1)
    Aj[CTRL] = StandardScaler().fit_transform(Aj[CTRL])
    adj_m = LogisticRegression(max_iter=3000, C=10).fit(Aj, d1.hit_goal)
    adjusted = {}
    for p_ in PR:
        A1, A0 = Aj.copy(), Aj.copy()
        A1[p_], A0[p_] = 1, 0
        adjusted[p_] = r(100 * (adj_m.predict_proba(A1)[:, 1].mean() - adj_m.predict_proba(A0)[:, 1].mean()), 1)
    HF = ["uses_auto_bidding", "creatives_per_campaign", "creative_refresh_days", "managed", "campaigns_active"]
    ht = DecisionTreeClassifier(max_depth=3, min_samples_leaf=150, random_state=0).fit(d1[HF], d1.hit_goal)
    F["happy"] = {"definition": "happy = actual CPA at or below the advertiser's own target CPA over the 8-week window; only knowable for advertisers with conversion tracking",
                  "n_tracked": int(trk.sum()), "share_of_all_advertisers": r(trk.mean()), "hit_goal_rate": r(d1.hit_goal.mean()),
                  "n_happy": int(len(happy)), "n_unhappy": int(len(unhappy)), "profile": prof,
                  "practices": {"uses_auto_bidding": "uses automated bidding", "creatives_4plus": "runs 4 or more creatives per campaign",
                                "fresh_creatives": "newest creative is at most 14 days old", "managed": "has an account manager",
                                "had_optimisation_review": "had an optimisation review with the support team"},
                  "naive": naive, "adjusted_pts": adjusted, "adjusted_for": CTRL + ["vertical", "the other practices"], "truth": truth,
                  "share_of_naive_gap_removed_by_adjusting": {p_: (r(1 - (adjusted[p_] - truth[p_]["effect_pts"]) / (naive[p_]["diff_pts"] - truth[p_]["effect_pts"]), 2)
                                                                   if abs(naive[p_]["diff_pts"] - truth[p_]["effect_pts"]) > 0.5 else None) for p_ in PR},
                  "review_story": "reviews go to accounts that are struggling for reasons the table cannot see, so reviewed accounts look worse even though the review helps: the naive comparison has the wrong sign, and adjusting for what we can see does not rescue it",
                  "tree_root": tree_json(ht, HF, "hit_rate"), "tree_text": export_text(ht, feature_names=HF, decimals=1)}

    # tracking vs churn: a big naive gap, a small true effect
    ta, tb = y[trk].mean(), y[~trk].mean()
    Bc = ["tenure_weeks", "spend_8w", "campaigns_active", "creatives_per_campaign", "creative_refresh_days"]

    def adj_churn(treat, cont_cols, flag_cols, extra_df=None):
        B = df[[treat] + flag_cols + cont_cols].copy()
        if "spend_8w" in B:
            B["spend_8w"] = np.log10(B.spend_8w)
        if extra_df is not None:
            B = pd.concat([B, extra_df], axis=1)
            cont_cols = cont_cols + [c for c in extra_df.columns if extra_df[c].nunique() > 2]
        B[cont_cols] = StandardScaler().fit_transform(B[cont_cols])
        B = pd.concat([B, pd.get_dummies(df.vertical, dtype=float)], axis=1)
        m = LogisticRegression(max_iter=3000, C=10).fit(B, y)
        B1, B0 = B.copy(), B.copy()
        B1[treat], B0[treat] = 1, 0
        return r(100 * (m.predict_proba(B1)[:, 1].mean() - m.predict_proba(B0)[:, 1].mean()), 1)

    F["tracking_story"] = {"churn_with_tracking": r(ta), "churn_without_tracking": r(tb), "naive_diff_pts": r(100 * (ta - tb), 1),
                           "adjusted_diff_pts": adj_churn("has_conversion_tracking", Bc, ["managed"]),
                           "adjusted_for": Bc + ["managed", "vertical"],
                           "truth": true_effect({"tracking": 1}, {"tracking": 0}, "churn"),
                           "model_weight_for_tracking": next({"odds_ratio": c["odds_ratio"], "avg_probability_shift_pts": c.get("avg_probability_shift_pts")} for c in F["logreg"]["coefs"] if c["feature"] == "has_conversion_tracking"),
                           "why": "a hidden trait (advertiser sophistication) makes advertisers both more likely to install tracking and less likely to churn; it is not in the table, so no adjustment can fully remove it"}
    # the wrong controls: adjusting for something the practice itself changes
    med = pd.DataFrame({"cpa_filled": df.cpa_vs_goal.fillna(df.cpa_vs_goal.median()).values, "spend_trend": df.spend_trend.values, "active_days_28": df.active_days_28.values}, index=df.index)
    ab1, ab0 = y[df.uses_auto_bidding.values == 1].mean(), y[df.uses_auto_bidding.values == 0].mean()
    F["bad_controls"] = {"question": "does automated bidding reduce churn?",
                         "how_it_works_in_the_simulation": "only indirectly: auto-bidding improves CPA, and better CPA keeps advertisers spending",
                         "naive_diff_pts": r(100 * (ab1 - ab0), 1),
                         "adjusted_for_background_only_pts": adj_churn("uses_auto_bidding", Bc, ["managed", "has_conversion_tracking"]),
                         "adjusted_also_for_what_it_changes_pts": adj_churn("uses_auto_bidding", Bc, ["managed", "has_conversion_tracking"], med),
                         "what_it_changes": ["CPA versus goal", "spend trend", "active days"],
                         "truth": true_effect({"auto_bid": 1}, {"auto_bid": 0}, "churn"),
                         "lesson": "controlling for the route a practice works through removes the very effect you are trying to measure"}

    # ---- how big an experiment would have to be (two-proportion test, normal approximation)
    def n_per_arm(p1, p2, za=1.959964, zb=0.841621):
        return int(np.ceil((za + zb) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2))

    F["experiment"] = {"formula": "two-sided test of two proportions, 5% significance, 80% power, equal arms",
                       "examples": [{"base_rate": a, "target_rate": b, "lift_pts": r(100 * (b - a), 1), "n_per_arm": n_per_arm(a, b)}
                                    for a, b in ((0.60, 0.65), (0.60, 0.70), (0.60, 0.62), (0.126, 0.10))]}

    # ---- segments: k-means on behaviour, no label involved - and an honest look at what it found
    CL = ["spend_8w", "campaigns_active", "creatives_per_campaign", "creative_refresh_days", "active_days_28", "uses_auto_bidding", "has_conversion_tracking", "tenure_weeks"]
    C = df[CL].copy()
    C["spend_8w"] = np.log10(C.spend_8w)
    Cs = StandardScaler().fit_transform(C)
    inertia = [{"k": k, "inertia": r(KMeans(k, n_init=5, random_state=0).fit(Cs).inertia_, 0)} for k in range(2, 9)]
    km = KMeans(4, n_init=10, random_state=0).fit(Cs)

    def profile(labels, cols):
        out_ = []
        for k in sorted(set(labels)):
            mk = labels == k
            out_.append({"n": int(mk.sum()), "share": r(mk.mean()), "churn": r(y[mk].mean()),
                         "hit_goal_rate_among_tracked": (r(hid.hit_goal[mk & trk].mean()) if (mk & trk).sum() >= 100 else None),
                         "median_spend_8w": r(df.spend_8w[mk].median(), 0), **{c: r(df[c][mk].mean(), 2) for c in cols if c != "spend_8w"}})
        out_.sort(key=lambda s: s["churn"])
        for i, s in enumerate(out_):
            s["segment"] = "ABCDEFGH"[i]
        return out_

    flags = df.has_conversion_tracking.values * 2 + df.uses_auto_bidding.values
    seeds = [KMeans(4, n_init=1, random_state=s_).fit(Cs).labels_ for s_ in range(6)]
    CL2 = [c for c in CL if c not in ("uses_auto_bidding", "has_conversion_tracking")]
    km2 = KMeans(4, n_init=10, random_state=0).fit(StandardScaler().fit_transform(C[CL2]))
    tier = pd.qcut(df.spend_8w, 3, labels=["small", "medium", "large"]).astype(str).values
    gb_rates = [float(y[(tier == t_) & (df.managed.values == m_)].mean()) for t_ in ("small", "medium", "large") for m_ in (0, 1)]
    F["segments"] = {"method": "k-means, k=4, on 8 standardised behaviour columns; the churn label was NOT used", "features": CL, "inertia_by_k": inertia,
                     "segments": profile(km.labels_, CL),
                     "honesty_checks": {
                         "agreement_with_a_plain_group_by": {"what": "how closely the four clusters match simply grouping by the two yes/no columns (tracking x auto-bidding); 1 = identical, 0 = unrelated",
                                                             "adjusted_rand_index": r(adjusted_rand_score(flags, km.labels_), 2)},
                         "stability": {"what": "re-run k-means from six different random starts and compare each result with the first",
                                       "agreement_min": r(min(adjusted_rand_score(seeds[0], s_) for s_ in seeds[1:]), 2), "agreement_max": r(max(adjusted_rand_score(seeds[0], s_) for s_ in seeds[1:]), 2)},
                         "without_the_two_flags": {"what": "the same method on the 6 remaining columns", "agreement_with_the_first_clustering": r(adjusted_rand_score(km.labels_, km2.labels_), 2),
                                                   "segments": profile(km2.labels_, CL2)},
                         "simple_business_segments": {"what": "churn rate in the six groups from spend tier x account manager - no ML at all", "churn_min": r(min(gb_rates)), "churn_max": r(max(gb_rates))},
                         "no_elbow": "the error keeps falling smoothly as k grows; nothing in the data says the right number of segments is four"}}

    # ---- a second prediction task where the pattern is thresholds and combinations: who adopts video ads?
    yv = df.adopted_video_next_60d.values
    yvt = yv[te]
    lv = lr_pipe().fit(X[tr], yv[tr])
    pv_lr = lv.predict_proba(X[te])[:, 1]
    tv = DecisionTreeClassifier(max_depth=3, min_samples_leaf=100, random_state=0).fit(Xt_tr, yv[tr])
    fv = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=1).fit(Xt_tr, yv[tr])
    gridv, GBV = tune_boosting(Xg_tr, yv[tr], cv)
    gv = HistGradientBoostingClassifier(**GBV).fit(Xg_tr, yv[tr])
    pv_gb = gv.predict_proba(Xg_te)[:, 1]
    gv0 = HistGradientBoostingClassifier(random_state=0, **U).fit(Xg_tr, yv[tr])
    XE = X.copy()                      # the same simple model, handed three combinations an analyst might think of
    XE["many_creatives_and_good_ctr"] = ((df.creatives_per_campaign >= 4) & (df.ctr_pct >= 0.28)).astype(int).values
    XE["big_spender_hitting_goal"] = ((df.spend_8w >= 3000) & (df.cpa_vs_goal <= 1.05)).astype(int).values
    XE["growing_and_active"] = ((df.tenure_weeks >= 8) & (df.tenure_weeks <= 52) & (df.active_days_28 >= 18)).astype(int).values
    EX = ["many_creatives_and_good_ctr", "big_spender_hitting_goal", "growing_and_active"]
    le = lr_pipe(extra=EX).fit(XE[tr], yv[tr])
    pv_le = le.predict_proba(XE[te])[:, 1]
    tk = lambda p_: int(yvt[np.argsort(-p_)[:200]].sum())
    F["video"] = {
        "question": "which advertisers will start using the new video ad format in the next 60 days? (an upsell / propensity list)",
        "how_it_was_built": "unlike churn, adoption in the simulation is driven by thresholds and combinations - e.g. many creatives AND a good click rate, a big spender AND hitting goal - not by a tidy weighted sum",
        "adoption_rate_test": r(yvt.mean(), 4), "adopters_test": int(yvt.sum()),
        "scoreboard": [
            {"model": "Decision tree, depth 3", "test_auc": r(roc_auc_score(yvt, tv.predict_proba(Xt_te)[:, 1])), "top_200_adopters": tk(tv.predict_proba(Xt_te)[:, 1])},
            {"model": "Logistic regression", "test_auc": r(roc_auc_score(yvt, pv_lr)), "train_auc": r(roc_auc_score(yv[tr], lv.predict_proba(X[tr])[:, 1])), "top_200_adopters": tk(pv_lr)},
            {"model": "Random forest, 300 trees", "test_auc": r(roc_auc_score(yvt, fv.predict_proba(Xt_te)[:, 1])), "top_200_adopters": tk(fv.predict_proba(Xt_te)[:, 1])},
            {"model": "Gradient boosting, default-ish settings", "test_auc": r(roc_auc_score(yvt, gv0.predict_proba(Xg_te)[:, 1])), "top_200_adopters": tk(gv0.predict_proba(Xg_te)[:, 1])},
            {"model": "Gradient boosting, tuned by cross-validation", "test_auc": r(roc_auc_score(yvt, pv_gb)), "train_auc": r(roc_auc_score(yv[tr], gv.predict_proba(Xg_tr)[:, 1])), "top_200_adopters": tk(pv_gb),
             "note": f"depth {GBV['max_depth']}, {GBV['max_iter']} rounds"},
            {"model": "Logistic regression + 3 hand-built combination flags", "test_auc": r(roc_auc_score(yvt, pv_le)), "top_200_adopters": tk(pv_le)},
        ],
        "random_200_expected": r(200 * yvt.mean(), 1),
        "tuning": {"best": gridv[0], "worst": gridv[-1]},
        "boosting_minus_logistic_auc": r(roc_auc_score(yvt, pv_gb) - roc_auc_score(yvt, pv_lr), 3),
        "boosting_minus_logistic_95": boot_ci(lambda i: roc_auc_score(yvt[i], pv_gb[i]) - roc_auc_score(yvt[i], pv_lr[i]), nt),
        "boosting_minus_logistic_with_flags_95": boot_ci(lambda i: roc_auc_score(yvt[i], pv_gb[i]) - roc_auc_score(yvt[i], pv_le[i]), nt),
        "compare_with_churn": {"churn_boosting_minus_logistic": r(F["boosting"]["test"]["auc"] - F["logreg"]["test"]["auc"], 3), "churn_boosting_depth_chosen": GBP["max_depth"], "video_boosting_depth_chosen": GBV["max_depth"]},
        "the_point": "whether a flexible model beats a simple one depends on the shape of the pattern, which you cannot know in advance - so run both and compare the gap with the noise",
    }

    F["widget_scores"] = {"model": "logistic regression, May-Jun test months", "base_rate": r(yt.mean(), 4), "n": nt,
                          "p": [r(v, 4) for v in p_lr], "y": [int(v) for v in yt], "spend": [int(v) for v in df.spend_8w.values[te]]}

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
            return None
        if isinstance(o, np.generic):
            return clean(o.item())
        return o

    out = df.drop(columns=["spend_next_8w", "adopted_video_next_60d", "churned_next_60d"]).copy()
    out["hit_cpa_goal"] = np.where(trk, hid.hit_goal.values.astype(float), np.nan)
    for c in ("spend_next_8w", "adopted_video_next_60d", "churned_next_60d"):
        out[c] = df[c].values
    F["data"]["columns"] = list(out.columns)          # exactly the columns of the published CSV, in its order
    leaky = out.copy()
    leaky.insert(list(leaky.columns).index("hit_cpa_goal"), "days_since_last_spend", leak.astype(int))
    return json.dumps(clean(F), allow_nan=False), out.to_csv(index=False), leaky.to_csv(index=False)


RESULT = main()
