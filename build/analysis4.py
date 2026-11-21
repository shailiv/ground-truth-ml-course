"""Part 4 of the evidence (added after the review council): three things the main table cannot show.
  1. repeated advertisers: why validation folds must respect groups (and what an ID column does)
  2. dirty tables: what a careless dropna or join does before any model is fitted
  3. before/after with a comparison group (difference-in-differences)
Runs in the same Pyodide interpreter after analysis.py. RESULT4 = facts json to merge.
"""
from sklearn.model_selection import GroupKFold, KFold, cross_val_predict


def main4():
    K = {}

    # ================= 1. the same advertiser in many rows =================
    def panel(n_adv, seed, months=6):
        g = np.random.default_rng(seed)
        stable = g.normal(size=(n_adv, 5))          # traits that barely change from month to month: in effect a fingerprint
        signal = g.normal(size=n_adv)               # the part of the risk the table can see, noisily, each month
        hidden = g.normal(size=n_adv)               # a lasting risk the table does not record
        fate = (g.uniform(size=n_adv) < sig(-1.3 + 1.4 * signal + 1.0 * hidden)).astype(int)   # the outcome belongs to the ADVERTISER
        ids, Xs, ys = [], [], []
        for _ in range(months):
            moving = np.column_stack([signal + 0.7 * g.normal(size=n_adv), g.normal(size=(n_adv, 2))])
            flip = g.uniform(size=n_adv) < 0.08     # consecutive snapshots share most of their outcome window, so labels rarely differ
            ids.append(np.arange(n_adv))
            Xs.append(np.column_stack([stable + 0.05 * g.normal(size=stable.shape), moving]))
            ys.append(np.where(flip, 1 - fate, fate))
        return np.concatenate(ids), np.vstack(Xs), np.concatenate(ys)

    ida, Xa, ya = panel(1500, 1)
    idb, Xb, yb = panel(1500, 2)                    # advertisers nobody has seen: the honest exam
    rf = lambda: RandomForestClassifier(n_estimators=150, random_state=0, n_jobs=1)
    lg = lambda: Pipeline([("sc", StandardScaler()), ("m", LogisticRegression(max_iter=2000))])

    def three_ways(make, X_, Xnew):
        shuffled = roc_auc_score(ya, cross_val_predict(make(), X_, ya, cv=KFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1])
        grouped = roc_auc_score(ya, cross_val_predict(make(), X_, ya, cv=GroupKFold(5), groups=ida, method="predict_proba")[:, 1])
        fresh = roc_auc_score(yb, make().fit(X_, ya).predict_proba(Xnew)[:, 1])
        return {"shuffled_rows": r(shuffled), "whole_advertisers_held_out": r(grouped), "truth_on_new_advertisers": r(fresh), "overstatement_from_shuffling": r(shuffled - fresh)}

    Xa_id, Xb_id = np.column_stack([ida, Xa]), np.column_stack([idb + 1500, Xb])
    K["panel_leak"] = {
        "setup": "a separate small simulation: 1,500 advertisers, each observed in 6 monthly rows (9,000 rows). Five of their columns hardly change from month to month, and - because consecutive snapshots share most of their 60-day outcome window - an advertiser's rows usually carry the same label.",
        "rows": int(len(ya)), "advertisers": 1500, "rows_per_advertiser": 6, "positive_rate": r(ya.mean()),
        "three_ways_to_score": {"shuffled_rows": "ordinary 5-fold cross-validation: rows are dealt out at random, so the same advertiser sits on both sides",
                                "whole_advertisers_held_out": "5 folds where all of an advertiser's rows go to the same side",
                                "truth_on_new_advertisers": "train on everything, then score 1,500 advertisers the model has never seen"},
        "random_forest": three_ways(rf, Xa, Xb), "logistic_regression": three_ways(lg, Xa, Xb),
        "random_forest_with_the_id_column_left_in": three_ways(rf, Xa_id, Xb_id),
        "why": "a flexible model can recognise an advertiser from its near-constant columns (or its ID) and simply recall how that advertiser turned out in its other months. That is memory, not prediction, and it disappears on advertisers it has not met.",
        "the_fix": "split by advertiser (and by time) so nobody appears on both sides; never feed an ID column to a model"}

    # ================= 2. dirty tables: damage done before any model is fitted =================
    df, hid = simulate()
    y = df.churned_next_60d.values
    month = hid.month.values
    tr, te = month <= TRAIN_LAST, month >= TEST_FIRST
    yt = y[te]
    X = df[NUM + CAT].copy()
    X["spend_8w"] = np.log10(X["spend_8w"])
    full = df.cpa_vs_goal.notna().values
    base = lr_pipe().fit(X[tr], y[tr])
    auc_std = roc_auc_score(yt, base.predict_proba(X[te])[:, 1])
    no_flag = [c for c in BIN if c != "has_conversion_tracking"]
    blind = lr_pipe(binf=no_flag).fit(X[tr][CONT + no_flag + CAT], y[tr])           # CPA silently filled in, and nothing says it was missing
    cc = lr_pipe().fit(X[tr & full], y[tr & full])                                  # trained only on rows that survive dropna()
    unt = te & ~full
    camp = df.campaigns_active.values
    mgr = df.managed.values == 1
    K["dirty_tables"] = {
        "dropna": {"what": "dropping every row with a missing value (CPA vs goal is empty for advertisers without conversion tracking)",
                   "rows_before": int(len(df)), "rows_after": int(full.sum()), "share_of_rows_lost": r(1 - full.mean()),
                   "churn_rate_before": r(y.mean()), "churn_rate_after": r(y[full].mean()),
                   "churners_before": int(y.sum()), "churners_after": int(y[full].sum()),
                   "model_trained_on_survivors_scoring_the_untracked": {"auc_on_untracked_advertisers": r(roc_auc_score(y[unt], cc.predict_proba(X[unt])[:, 1])),
                                                                        "same_for_a_model_trained_on_everyone": r(roc_auc_score(y[unt], base.predict_proba(X[unt])[:, 1])),
                                                                        "avg_predicted_churn": r(cc.predict_proba(X[unt])[:, 1].mean()), "actual_churn": r(y[unt].mean())}},
        "missing_is_information": {"churn_when_cpa_is_missing": r(y[~full].mean()), "churn_when_cpa_is_present": r(y[full].mean()),
                                   "test_auc_keeping_a_missing_flag": r(auc_std), "test_auc_filling_silently_with_no_flag": r(roc_auc_score(yt, blind.predict_proba(X[te][CONT + no_flag + CAT])[:, 1]))},
        "join_fan_out": {"what": "joining the advertiser table to a campaigns table that has one row per campaign, then counting as if each row were an advertiser",
                         "advertisers": int(len(df)), "rows_after_join": int(camp.sum()), "rows_per_advertiser": r(camp.mean(), 2),
                         "total_spend_before": int(df.spend_8w.sum()), "total_spend_after_join": int((df.spend_8w.values * camp).sum()),
                         "spend_overstated_by": r((df.spend_8w.values * camp).sum() / df.spend_8w.sum() - 1, 3),
                         "churn_rate_before": r(y.mean(), 4), "churn_rate_after_join": r((y * camp).sum() / camp.sum(), 4),
                         "the_check": "count distinct advertisers and total rows before and after every join; if rows grew, something fanned out"},
        "inner_join_drop": {"what": "an inner join to the account-managers table keeps only advertisers who have one",
                            "advertisers_before": int(len(df)), "advertisers_after": int(mgr.sum()), "share_lost": r(1 - mgr.mean()),
                            "churn_rate_before": r(y.mean()), "churn_rate_after": r(y[mgr].mean())},
    }

    # ================= 3. before/after with a comparison group =================
    g = np.random.default_rng(77)
    weeks, launch = 24, 12
    n_t, n_c = 900, 2100
    wk = np.arange(1, weeks + 1)
    post = wk > launch
    true_effect = 0.04

    def world(trend_c):
        p_t = 0.58 + 0.004 * (wk - 1) + true_effect * post
        p_c = 0.64 + trend_c * (wk - 1)
        rt_, rc_ = g.binomial(n_t, p_t) / n_t, g.binomial(n_c, p_c) / n_c
        d = (rt_[post].mean() - rt_[~post].mean()) - (rc_[post].mean() - rc_[~post].mean())
        var = sum(v.mean() * (1 - v.mean()) / (n_ * 12) for v, n_ in ((rt_[post], n_t), (rt_[~post], n_t), (rc_[post], n_c), (rc_[~post], n_c)))
        dif = (rt_ - rc_)[~post]
        (b_, a_), cov = np.polyfit(wk[~post], dif, 1, cov=True)      # is the gap between the groups drifting before launch?
        return rt_, rc_, d, 1.96 * var ** 0.5, (float(b_), float(1.96 * cov[0, 0] ** 0.5))

    rt_, rc_, did, half, gap = world(0.004)
    _, _, did_bad, half_bad, gap_bad = world(0.0005)
    K["before_after"] = {
        "setup": "a separate small simulation. Ecommerce advertisers get a guided creative-setup flow from week 13; other verticals do not. Outcome: share of advertisers hitting their CPA goal each week. Everyone is slowly improving anyway (the season), and ecommerce starts from a lower level.",
        "true_effect_pts": r(100 * true_effect, 1), "weeks": weeks, "launch_after_week": launch, "advertisers_per_week": {"got_the_flow": n_t, "comparison": n_c},
        "weekly_hit_rate": {"week": [int(w) for w in wk], "got_the_flow": [r(v) for v in rt_], "comparison": [r(v) for v in rc_]},
        "averages": {"got_the_flow_before": r(rt_[~post].mean()), "got_the_flow_after": r(rt_[post].mean()), "comparison_before": r(rc_[~post].mean()), "comparison_after": r(rc_[post].mean())},
        "three_answers": {"before_vs_after_in_the_treated_group_pts": r(100 * (rt_[post].mean() - rt_[~post].mean()), 1),
                          "treated_vs_comparison_after_launch_pts": r(100 * (rt_[post].mean() - rc_[post].mean()), 1),
                          "difference_in_differences_pts": r(100 * did, 1),
                          "difference_in_differences_ci95_pts": [r(100 * (did - half), 1), r(100 * (did + half), 1)]},
        "the_assumption": {"what": "the two groups would have moved in parallel without the change; check it on the weeks BEFORE launch",
                           "pre_launch_drift_of_the_gap_pts_per_week": r(100 * gap[0], 2), "plus_minus": r(100 * gap[1], 2),
                           "drift_distinguishable_from_zero": bool(abs(gap[0]) > gap[1])},
        "when_the_assumption_fails": {"what": "the same exercise in a world where the comparison group was barely improving on its own",
                                      "difference_in_differences_pts": r(100 * did_bad, 1), "pre_launch_drift_of_the_gap_pts_per_week": r(100 * gap_bad[0], 2),
                                      "plus_minus": r(100 * gap_bad[1], 2), "drift_distinguishable_from_zero": bool(abs(gap_bad[0]) > gap_bad[1]),
                                      "reading": "the method now credits the launch with improvement the treated group was already making; the pre-launch trend gap is the warning sign"},
    }
    return json.dumps(clean_json(K), allow_nan=False)


RESULT4 = main4()
