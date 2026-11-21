"""Part 3 of the evidence (added after the review council): who the model is wrong about (slices),
real-or-noise and how-much-data, uplift (who changes because you acted), and time-to-event.
Runs in the same Pyodide interpreter after analysis.py / analysis2.py. RESULT3 = facts json to merge.
"""


def main3():
    H = {}
    df, hid = simulate()
    y = df.churned_next_60d.values
    month = hid.month.values
    tr, te = month <= TRAIN_LAST, month >= TEST_FIRST
    yt = y[te]
    X = df[NUM + CAT].copy()
    X["spend_8w"] = np.log10(X["spend_8w"])
    lr = lr_pipe().fit(X[tr], y[tr])
    p = lr.predict_proba(X[te])[:, 1]
    spend = df.spend_8w.values
    q1, q2 = np.percentile(spend[tr], [33.33, 66.67])
    K = 400
    top = np.zeros(te.sum(), bool)
    top[np.argsort(-p)[:K]] = True

    # ================= slices: an average hides who the model fails =================
    def slice_row(name, mk):
        n_ch = int(yt[mk].sum())
        return {"slice": name, "n": int(mk.sum()), "churn_rate": r(yt[mk].mean()), "churners": n_ch,
                "auc": (r(roc_auc_score(yt[mk], p[mk])) if 0 < n_ch < mk.sum() else None),
                "flagged_in_top_400": int((top & mk).sum()), "precision_when_flagged": (r(yt[top & mk].mean()) if (top & mk).sum() else None),
                "recall": (r((top & mk & (yt == 1)).sum() / n_ch) if n_ch else None),
                "avg_predicted": r(p[mk].mean()), "avg_actual": r(yt[mk].mean()),
                "spend_lost_to_churn": int(spend[te][mk & (yt == 1)].sum()), "spend_lost_that_was_flagged": int(spend[te][mk & top & (yt == 1)].sum())}

    s_te = spend[te]
    slices = {
        "by_size": [slice_row("small (bottom third by spend)", s_te <= q1), slice_row("medium", (s_te > q1) & (s_te <= q2)), slice_row("large (top third by spend)", s_te > q2)],
        "by_account_manager": [slice_row("no account manager", df.managed.values[te] == 0), slice_row("has account manager", df.managed.values[te] == 1)],
        "by_tenure": [slice_row("new (under 12 weeks)", df.tenure_weeks.values[te] < 12), slice_row("established (12 weeks or more)", df.tenure_weeks.values[te] >= 12)],
        "by_vertical": [slice_row(v, (df.vertical.values[te] == v)) for v in VERTS],
        "by_tracking": [slice_row("no conversion tracking", df.has_conversion_tracking.values[te] == 0), slice_row("has conversion tracking", df.has_conversion_tracking.values[te] == 1)],
    }
    tot_lost = float(s_te[yt == 1].sum())
    exp_loss = p * s_te
    top_val = np.zeros(te.sum(), bool)
    top_val[np.argsort(-exp_loss)[:K]] = True
    H["slices"] = {"model": "logistic regression, test months; 'flagged' = the 400 highest churn scores", "overall": slice_row("everyone", np.ones(te.sum(), bool)),
                   **slices,
                   "rank_by_what": {
                       "list_size": K, "total_spend_lost_to_churn": int(tot_lost),
                       "rank_by_churn_probability": {"churners_on_list": int(yt[top].sum()), "share_of_churners": r(yt[top].sum() / yt.sum()),
                                                     "spend_of_churners_on_list": int(s_te[top & (yt == 1)].sum()), "share_of_lost_spend": r(s_te[top & (yt == 1)].sum() / tot_lost),
                                                     "median_spend_of_listed": int(np.median(s_te[top]))},
                       "rank_by_probability_times_spend": {"churners_on_list": int(yt[top_val].sum()), "share_of_churners": r(yt[top_val].sum() / yt.sum()),
                                                           "spend_of_churners_on_list": int(s_te[top_val & (yt == 1)].sum()), "share_of_lost_spend": r(s_te[top_val & (yt == 1)].sum() / tot_lost),
                                                           "median_spend_of_listed": int(np.median(s_te[top_val]))},
                       "overlap_between_the_two_lists": int((top & top_val).sum())}}

    # ================= real or noise? and how much data is enough? =================
    rs = np.random.default_rng(21)
    rs_aa = np.random.default_rng(2121)
    base = float(y.mean())
    ci_half = lambda p_, n: 1.96 * np.sqrt(p_ * (1 - p_) / n)
    by_n = [{"n": n, "plus_minus_pts": r(100 * ci_half(base, n), 1)} for n in (50, 100, 250, 500, 1000, 2000, 4000, 12000)]
    aa = {}
    for n in (250, 1000, 4000):
        # two separate groups drawn from a large platform: sample WITH replacement, or groups of 4,000 out of 12,000
        # would overlap and share a finite pool, understating the noise by about a fifth. Own generator, so the draws
        # further down (learning curves) are the same ones as before this was corrected.
        d = np.array([y[rs_aa.choice(len(y), n, replace=True)].mean() - y[rs_aa.choice(len(y), n, replace=True)].mean() for _ in range(2000)]) * 100
        for _ in range(2000): rs.choice(len(y), n, replace=False); rs.choice(len(y), n, replace=False)
        aa[str(n)] = {"group_size": n, "typical_gap_pts": r(np.median(np.abs(d)), 2), "gap_exceeded_1_time_in_20_pts": r(np.percentile(np.abs(d), 95), 2),
                      "share_of_gaps_over_2_pts": r((np.abs(d) > 2).mean(), 3)}

    def diff_ci(a, b, label):
        pa, pb, na, nb = a.mean(), b.mean(), len(a), len(b)
        se = np.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)
        d = pa - pb
        return {"comparison": label, "rate_a": r(pa), "n_a": int(na), "rate_b": r(pb), "n_b": int(nb), "difference_pts": r(100 * d, 1),
                "ci95_pts": [r(100 * (d - 1.96 * se), 1), r(100 * (d + 1.96 * se), 1)], "ci_excludes_zero": bool(abs(d) > 1.96 * se)}

    v = df.vertical.values
    g = v == "gaming"
    H["noise"] = {
        "overall_churn_rate": r(base, 4),
        "margin_of_error_for_a_churn_rate": {"what": f"95% margin of error around an observed churn rate of about {100 * base:.1f}% (the overall rate), by number of advertisers in the group", "rows": by_n},
        "aa_test": {"what": "draw two groups of advertisers at random 2,000 times and record the gap in churn rate; there is no real difference between the groups, so every gap is pure noise", "by_group_size": aa},
        "comparisons": [diff_ci(y[df.has_conversion_tracking.values == 0], y[df.has_conversion_tracking.values == 1], "no tracking vs tracking"),
                        diff_ci(y[v == "health"], y[v == "education"], "health vs education"),
                        diff_ci(y[v == "gaming"], y[v == "ecommerce"], "gaming vs ecommerce"),
                        diff_ci(y[g & (month == 3)], y[g & (month == 2)], "gaming in April vs gaming in March"),
                        diff_ci(y[g & (month == 5)], y[g & (month <= 3)], "gaming in June vs gaming in January-April")],
        "gaming_monthly": [{"month": MONTH_NAMES[m], "n": int((g & (month == m)).sum()), "churn_rate": r(y[g & (month == m)].mean()),
                            "plus_minus_pts": r(100 * ci_half(y[g & (month == m)].mean(), (g & (month == m)).sum()), 1)} for m in range(MONTHS)],
    }
    # learning curve: how the test score grows with the number of training rows
    gb_pre = ColumnTransformer([("num", "passthrough", NUM), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)]).fit(X[tr])
    Xg_te = gb_pre.transform(X[te])
    tr_idx = np.where(tr)[0]
    curve = []
    n_tr = int(tr.sum())
    for n in (100, 250, 500, 1000, 2000, 4000, n_tr):
        a_lr, a_gb = [], []
        for rep in range(1 if n == n_tr else 8):
            idx = tr_idx if n == n_tr else rs.choice(tr_idx, n, replace=False)
            if y[idx].sum() < 5:
                continue
            a_lr.append(roc_auc_score(yt, lr_pipe().fit(X.iloc[idx], y[idx]).predict_proba(X[te])[:, 1]))
            m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_depth=4, random_state=0).fit(gb_pre.transform(X.iloc[idx]), y[idx])
            a_gb.append(roc_auc_score(yt, m.predict_proba(Xg_te)[:, 1]))
        curve.append({"training_rows": n, "churners_in_training": int(round(n * y[tr].mean())), "logistic_auc": r(np.mean(a_lr)), "logistic_min": r(np.min(a_lr)), "logistic_max": r(np.max(a_lr)),
                      "boosting_default_auc": r(np.mean(a_gb)), "boosting_min": r(np.min(a_gb)), "boosting_max": r(np.max(a_gb))})
    H["learning_curve"] = {"what": "train on a random sample of the training rows, score on all 4,000 May-June rows; 8 repeats per size",
                           "boosting_settings": "default-ish (depth 4, 200 rounds)", "rows": curve}

    # ================= uplift: who changes because you acted =================
    # A simulated randomised outreach programme. Because the world is simulated we know, for every
    # advertiser, what happens with AND without the call - something no real dataset can show.
    ru = np.random.default_rng(33)
    lgt = hid.churn_logit.values
    cpa = np.where(df.has_conversion_tracking.values == 1, df.cpa_vs_goal.values, 1.0)
    engaged = df.active_days_28.values >= 12
    fixable_perf = (cpa > 1.0) & (cpa < 1.7)
    stale = df.creative_refresh_days.values > 30
    tau = np.where(engaged, 2.2 * fixable_perf + 1.2 * stale, 0.0)                 # help lands when there is something fixable and someone is still there
    tau = tau - 0.6 * ((df.managed.values == 0) & (spend < q1) & (df.spend_trend.values >= 1.0))   # small healthy self-serve accounts: the call is an annoyance
    u = Z["u_churn"]
    y0 = (u < sig(lgt)).astype(int)
    y1 = (u < sig(lgt - tau)).astype(int)
    assert (y0 == y).all()
    true_ate = float((y0 - y1).mean())
    runs = []
    for _ in range(200):
        T_ = (ru.uniform(size=N) < 0.5).astype(int)
        c_, t_ = y0[T_ == 0], y1[T_ == 1]
        d_ = c_.mean() - t_.mean()
        se_ = np.sqrt(c_.mean() * (1 - c_.mean()) / len(c_) + t_.mean() * (1 - t_.mean()) / len(t_))
        runs.append((d_, se_, T_))
    eff = np.array([a for a, _, _ in runs])
    covered = np.mean([abs(a - true_ate) <= 1.96 * b for a, b, _ in runs])
    T = runs[int(np.argsort(eff)[len(eff) // 2])][2]          # the run whose measured effect is the median of the 200
    yobs = np.where(T == 1, y1, y0)
    many = {"what": "the same experiment repeated 200 times, each with a fresh coin flip for who gets called (all 12,000 advertisers)",
            "true_effect_pts": r(100 * true_ate, 1), "measured_effect_lowest_pts": r(100 * eff.min(), 1), "measured_effect_highest_pts": r(100 * eff.max(), 1),
            "middle_90pct_of_runs_pts": [r(100 * np.percentile(eff, 5), 1), r(100 * np.percentile(eff, 95), 1)],
            "share_of_runs_whose_95pct_interval_contains_the_truth": r(covered, 3),
            "share_of_runs_that_could_tell_the_effect_from_zero": r(np.mean([abs(a) > 1.96 * b for a, b, _ in runs]), 3),
            "illustration": "the single experiment shown elsewhere in this section is the run with the median measured effect, so it is typical by construction"}
    quad = {"persuadable (leaves unless called)": float(((y0 == 1) & (y1 == 0))[te].mean()), "lost cause (leaves either way)": float(((y0 == 1) & (y1 == 1))[te].mean()),
            "sure thing (stays either way)": float(((y0 == 0) & (y1 == 0))[te].mean()), "sleeping dog (leaves only if called)": float(((y0 == 0) & (y1 == 1))[te].mean())}
    m_t = lr_pipe().fit(X[tr & (T == 1)], yobs[tr & (T == 1)])
    m_c = lr_pipe().fit(X[tr & (T == 0)], yobs[tr & (T == 0)])
    gbp = dict(max_iter=100, learning_rate=0.05, max_depth=2, random_state=0)
    Xg = gb_pre.transform(X)
    g_t = HistGradientBoostingClassifier(**gbp).fit(Xg[tr & (T == 1)], yobs[tr & (T == 1)])
    g_c = HistGradientBoostingClassifier(**gbp).fit(Xg[tr & (T == 0)], yobs[tr & (T == 0)])
    risk = m_c.predict_proba(X[te])[:, 1]
    up_lr = risk - m_t.predict_proba(X[te])[:, 1]
    up_gb = g_c.predict_proba(Xg[te])[:, 1] - g_t.predict_proba(Xg[te])[:, 1]
    true_up = (y0 - y1)[te]
    rule_score = risk * (engaged & (fixable_perf | stale))[te]                     # the rule a thoughtful analyst would write: riskiest accounts that are still active and have a fixable problem
    pol = lambda score, k: {"called": k, "churns_prevented": int(true_up[np.argsort(-score)[:k]].sum()), "would_have_churned_anyway_or_stayed_anyway": int(k - np.abs(true_up[np.argsort(-score)[:k]]).sum()),
                            "pushed_out_by_the_call": int((true_up[np.argsort(-score)[:k]] == -1).sum())}
    def readout(mk, label):
        c, t_ = yobs[mk & (T == 0)], yobs[mk & (T == 1)]
        d = c.mean() - t_.mean()
        se_ = np.sqrt(c.mean() * (1 - c.mean()) / len(c) + t_.mean() * (1 - t_.mean()) / len(t_))
        return {"who": label, "n_called": int(len(t_)), "n_not_called": int(len(c)), "churn_without_call": r(c.mean()), "churn_with_call": r(t_.mean()),
                "measured_effect_pts": r(100 * d, 1), "ci95_pts": [r(100 * (d - 1.96 * se_), 1), r(100 * (d + 1.96 * se_), 1)],
                "true_effect_pts": r(100 * (y0[mk] - y1[mk]).mean(), 1), "ci_excludes_zero": bool(abs(d) > 1.96 * se_)}
    rnd = np.random.default_rng(1)
    H["uplift"] = {
        "setup": "a simulated randomised outreach programme: half of all advertisers, chosen by coin flip, get a call from the success team. In the simulation the call helps accounts that are still active and have a fixable problem (CPA moderately over goal, or stale creatives), does nothing for accounts already gone quiet or already healthy, and slightly annoys small healthy self-serve accounts.",
        "why_simulated_matters": "for each advertiser we know the outcome both with and without the call, so we can count exactly how many churns each calling policy would prevent",
        "many_experiments": many,
        "experiment_readout": {"all_advertisers": readout(np.ones(N, bool), "all 12,000 advertisers"),
                               "one_month_only": readout(month == 0, "January only (2,000 advertisers)"),
                               "note": "true_effect is knowable only because the data is simulated; a real experiment gives you the measured effect and its interval"},
        "four_kinds_of_advertiser_share": {k: r(v_, 3) for k, v_ in quad.items()},
        "policies_call_400_note": "churns_prevented is NET: advertisers a call saves minus advertisers a call pushes out (a few would have stayed if left alone)",
        "policies_call_400": {"at_random": {"called": 400, "churns_prevented_expected": r(400 * true_up.mean(), 1)},
                              "highest_churn_risk": pol(risk, 400), "business_rule_active_with_a_fixable_problem_ranked_by_risk": pol(rule_score, 400),
                              "highest_predicted_uplift_two_logistic_models": pol(up_lr, 400),
                              "highest_predicted_uplift_two_boosted_models": pol(up_gb, 400), "perfect_knowledge": pol(true_up + 1e-6 * rnd.uniform(size=len(true_up)), 400)},
        "policies_call_800": {"highest_churn_risk": pol(risk, 800), "business_rule_active_with_a_fixable_problem_ranked_by_risk": pol(rule_score, 800),
                              "highest_predicted_uplift_two_logistic_models": pol(up_lr, 800), "highest_predicted_uplift_two_boosted_models": pol(up_gb, 800)},
        "share_of_the_risk_list_that_stayed_without_any_call": r(1 - y0[te][np.argsort(-risk)[:400]].mean()),
        "about_the_business_rule": "the rule 'still active and has a fixable problem' matches how this simulation was written, so its score here is a best case for a hand rule. In real life you would not know the rule is right - the randomised data is what lets you test it, exactly as it tests a model.",
        "who_the_risk_list_calls": {"share_lost_causes": r(((y0 == 1) & (y1 == 1))[te][np.argsort(-risk)[:400]].mean()), "share_persuadable": r(((y0 == 1) & (y1 == 0))[te][np.argsort(-risk)[:400]].mean()),
                                    "avg_active_days": r(df.active_days_28.values[te][np.argsort(-risk)[:400]].mean(), 1)},
        "who_the_uplift_list_calls": {"share_lost_causes": r(((y0 == 1) & (y1 == 1))[te][np.argsort(-up_gb)[:400]].mean()), "share_persuadable": r(((y0 == 1) & (y1 == 0))[te][np.argsort(-up_gb)[:400]].mean()),
                                      "avg_active_days": r(df.active_days_28.values[te][np.argsort(-up_gb)[:400]].mean(), 1)},
        "method": "two-model approach: fit one churn model on the called group and one on the not-called group; predicted uplift = predicted churn without the call minus predicted churn with it",
        "caveat": "uplift can only be learned from data where the action was assigned at random (or as good as); it is noisier than risk because it is a difference between two predictions",
    }

    # ================= time to event: when, not whether =================
    rt = np.random.default_rng(55)
    n = 6000
    managed_ = (rt.uniform(size=n) < 0.31).astype(int)
    health = rt.normal(size=n)
    weeks_observed = rt.integers(4, 105, n)                       # joined 4 to 104 weeks before the analysis date
    shape = 0.75                                                  # hazard falls with tenure: the first months are the dangerous ones
    scale = 60 * np.exp(0.55 * managed_ + 0.6 * health)
    life = scale * rt.weibull(shape, n)                           # true weeks until churn
    event = (life <= weeks_observed).astype(int)
    dur = np.minimum(life, weeks_observed)

    def km(d, e, at):
        order = np.argsort(d)
        d, e = d[order], e[order]
        surv, out, k, at_risk = 1.0, [], 0, len(d)
        for t_ in at:
            while k < len(d) and d[k] <= t_:
                if e[k]:
                    surv *= 1 - 1 / at_risk
                at_risk -= 1
                k += 1
            out.append(surv)
        return out

    grid = [4, 8, 13, 26, 39, 52, 78, 104]
    km_all = km(dur, event, grid)
    fine = np.arange(1, 105)
    km_fine = km(dur, event, fine)
    median_km = int(fine[np.argmax(np.array(km_fine) <= 0.5)]) if min(km_fine) <= 0.5 else None
    true_surv = lambda t_, mk: float((life[mk] > t_).mean())
    allm = np.ones(n, bool)
    old = weeks_observed >= 52
    H["time_to_event"] = {
        "setup": "a separate simulation of 6,000 advertisers who joined at different times over the last two years. For each we know how long they have been a customer and whether they have churned yet. Those who have not are 'censored': we only know they lasted at least this long.",
        "n": n, "churned_so_far": int(event.sum()), "still_active_censored": int(n - event.sum()), "share_censored": r(1 - event.mean()),
        "naive_average_lifetime_of_those_who_churned_weeks": r(dur[event == 1].mean(), 1),
        "naive_share_churned": r(event.mean()),
        "kaplan_meier": {"what": "share of advertisers still active after t weeks, estimated in a way that uses censored advertisers for as long as we watched them",
                         "weeks": grid, "share_still_active": [r(s_) for s_ in km_all], "true_share_still_active": [r(true_surv(t_, allm)) for t_ in grid],
                         "median_lifetime_weeks": median_km, "true_median_lifetime_weeks": r(np.median(life), 1)},
        "weekly_curve": {"weeks": [int(w) for w in fine], "everyone": [r(s_) for s_ in km_fine],
                         "with_manager": [r(s_) for s_ in km(dur[managed_ == 1], event[managed_ == 1], fine)],
                         "without_manager": [r(s_) for s_ in km(dur[managed_ == 0], event[managed_ == 0], fine)]},
        "by_account_manager": {"weeks": grid, "with_manager": [r(s_) for s_ in km(dur[managed_ == 1], event[managed_ == 1], grid)],
                               "without_manager": [r(s_) for s_ in km(dur[managed_ == 0], event[managed_ == 0], grid)]},
        "risk_by_quarter_of_tenure": {"what": "of the advertisers still active at the start of each 13-week block, the share who churn during it",
                                      "rows": [{"weeks": f"{a + 1}-{a + 13}", "share_who_churn": r(1 - km_fine[a + 12] / (km_fine[a - 1] if a else 1.0))} for a in (0, 13, 26, 39, 52, 65)]},
        "the_classification_shortcut": {"what": "a fixed-window label ('churned within 26 weeks of joining') only works for advertisers we have watched for at least 26 weeks",
                                        "advertisers_usable": int((weeks_observed >= 26).sum()), "advertisers_thrown_away": int((weeks_observed < 26).sum()),
                                        "share_churned_within_26_weeks_among_usable": r((life[weeks_observed >= 26] <= 26).mean()),
                                        "wrong_way_counting_everyone": r(((life <= 26) & (life <= weeks_observed)).mean())},
    }
    return json.dumps(clean_json(H), allow_nan=False)


RESULT3 = main3()
