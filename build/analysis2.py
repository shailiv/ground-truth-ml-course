"""Part 2 of the evidence: predicting a number, scaling and distance, a small neural net,
forecasting and anomalies in a daily series. Runs in the same Pyodide interpreter after
analysis.py (reuses its globals). RESULT2 = (facts json to merge, daily series csv).

Revised after the review council: every model comparison carries an interval, the spend model
shows the median-vs-mean trap, forecasts are judged on a series WITHOUT planted incidents
(those are kept for the anomaly lesson only), and a level shift shows what no forecast can see.
"""
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier


def reg_metrics(y, p):
    e = p - y
    return {"mae": r(np.abs(e).mean(), 0), "rmse": r(np.sqrt((e ** 2).mean()), 0),
            "r2": r(1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum(), 3),
            "median_abs_error": r(np.median(np.abs(e)), 0), "wape": r(np.abs(e).sum() / y.sum(), 3), "bias": r(e.mean(), 0),
            "total_error": r(p.sum() / y.sum() - 1, 3)}


def clean_json(o):
    if isinstance(o, dict):
        return {k: clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean_json(v) for v in o]
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, np.generic):
        return clean_json(o.item())
    return o


def main2():
    G = {}
    df, hid = simulate()
    y = df.churned_next_60d.values
    month = hid.month.values
    tr, te = month <= TRAIN_LAST, month >= TEST_FIRST
    yt = y[te]
    nt = int(te.sum())
    X = df[NUM + CAT].copy()
    X["spend_8w"] = np.log10(X["spend_8w"])

    # ================= regression: next-8-week spend in dollars =================
    y2 = df.spend_next_8w.values.astype(float)
    last4 = df.spend_8w.values * df.spend_trend.values / (1 + df.spend_trend.values)   # spend in the most recent 4 weeks
    run_rate = 2 * last4
    Xr = df[NUM + CAT].copy()                       # raw dollars this time: the target is in dollars
    Xr["run_rate_8w"] = run_rate
    num_r = NUM + ["run_rate_8w"]
    pre_r = lambda cols: ColumnTransformer([("num", SimpleImputer(strategy="median"), cols), ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT)])
    lin_plain = Pipeline([("pre", pre_r(NUM)), ("m", LinearRegression())]).fit(Xr[tr], y2[tr])
    lin_rr = Pipeline([("pre", pre_r(num_r)), ("m", LinearRegression())]).fit(Xr[tr], y2[tr])
    gpre = ColumnTransformer([("num", "passthrough", num_r), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    Gtr, Gte = gpre.fit_transform(Xr[tr]), gpre.transform(Xr[te])
    HG = dict(max_iter=300, learning_rate=0.05, max_depth=4, random_state=0)
    gbr = HistGradientBoostingRegressor(**HG).fit(Gtr, y2[tr])
    gbr_abs = HistGradientBoostingRegressor(loss="absolute_error", **HG).fit(Gtr, y2[tr])
    # log-scale models, fitted on training advertisers who kept spending
    churn_lr = lr_pipe().fit(X[tr], y[tr])
    p_stay = 1 - churn_lr.predict_proba(X[te])[:, 1]
    XL = X[NUM + CAT].copy()
    XL["log_run_rate"] = np.log10(np.clip(run_rate, 1, None))
    cont_l = list(CONT) + ["log_run_rate"]
    stay_tr = tr & (y2 > 0)
    logm = Pipeline([("pre", ColumnTransformer([("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), cont_l),
                                                ("bin", "passthrough", BIN), ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT)])),
                     ("m", LinearRegression())]).fit(XL[stay_tr], np.log(y2[stay_tr]))
    res_log = np.log(y2[stay_tr]) - logm.predict(XL[stay_tr])
    smear = float(np.mean(np.exp(res_log)))                  # turns "typical" (median) into "average" (mean)
    med_if_stay = np.exp(logm.predict(XL[te]))
    mean_if_stay = med_if_stay * smear
    gl_pre = ColumnTransformer([("num", "passthrough", NUM + ["log_run_rate"]), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT)])
    gb_log = HistGradientBoostingRegressor(**HG).fit(gl_pre.fit_transform(XL[stay_tr]), np.log(y2[stay_tr]))
    res_gb = np.log(y2[stay_tr]) - gb_log.predict(gl_pre.transform(XL[stay_tr]))
    gb_mean_if_stay = np.exp(gb_log.predict(gl_pre.transform(XL[te]))) * float(np.mean(np.exp(res_gb)))
    preds = {
        "mean_of_training": np.full(nt, y2[tr].mean()),
        "same_as_last_8_weeks": df.spend_8w.values[te],
        "run_rate": run_rate[te],
        "linear_regression_dollars": np.clip(lin_plain.predict(Xr[te]), 0, None),
        "linear_regression_dollars_plus_run_rate": np.clip(lin_rr.predict(Xr[te]), 0, None),
        "gradient_boosting_squared_loss": np.clip(gbr.predict(Gte), 0, None),
        "gradient_boosting_absolute_loss": np.clip(gbr_abs.predict(Gte), 0, None),
        "log_model_typical_value": med_if_stay,
        "log_model_average_value": mean_if_stay,
        "two_stage_chance_of_staying_x_average": p_stay * mean_if_stay,
        "two_stage_chance_of_staying_x_typical": p_stay * med_if_stay,
        "two_stage_with_boosting_on_log_spend": p_stay * gb_mean_if_stay,
    }
    y2t = y2[te]
    M = {k: reg_metrics(y2t, v) for k, v in preds.items()}
    rb = np.random.default_rng(8)

    def paired(a, b):
        d = np.abs(preds[a] - y2t) - np.abs(preds[b] - y2t)
        bs = [d[rb.integers(0, nt, nt)].mean() for _ in range(1000)]
        return {"a": a, "b": b, "mae_a_minus_mae_b": r(d.mean(), 0), "ci95": [r(np.percentile(bs, 2.5), 0), r(np.percentile(bs, 97.5), 0)],
                "clear_winner": (a if np.percentile(bs, 97.5) < 0 else b if np.percentile(bs, 2.5) > 0 else None)}

    G_reg = {"target": "spend_next_8w: dollars spent in the 8 weeks after the snapshot (0 for advertisers who churn)",
             "test_rows": nt, "target_mean": r(y2t.mean(), 0), "target_median": r(np.median(y2t), 0),
             "target_p90": r(np.percentile(y2t, 90), 0), "target_p99": r(np.percentile(y2t, 99), 0), "target_max": r(y2t.max(), 0),
             "share_zero": r((y2t == 0).mean(), 3), "total_actual": int(y2t.sum()),
             "definitions": {"mae": "mean absolute error in dollars: the typical size of a miss", "rmse": "root mean squared error: like MAE but big misses count much more",
                             "r2": "share of the variance explained (1 = perfect, 0 = no better than the average)",
                             "wape": "total absolute error divided by total actual spend", "bias": "average of (prediction - actual), in dollars",
                             "total_error": "predicted total across all advertisers divided by actual total, minus 1: what matters if predictions are summed into a revenue forecast",
                             "run_rate": "2 x the most recent 4 weeks' spend"},
             "models": M,
             "winner_depends_on_the_metric": {"lowest_mae": min(M, key=lambda k: M[k]["mae"]), "lowest_rmse": min(M, key=lambda k: M[k]["rmse"]),
                                              "total_closest_to_actual": min(M, key=lambda k: abs(M[k]["total_error"]))},
             "paired_differences": [paired("run_rate", "same_as_last_8_weeks"), paired("linear_regression_dollars", "run_rate"),
                                    paired("linear_regression_dollars_plus_run_rate", "run_rate"), paired("gradient_boosting_squared_loss", "linear_regression_dollars_plus_run_rate"),
                                    paired("gradient_boosting_absolute_loss", "gradient_boosting_squared_loss"), paired("log_model_typical_value", "gradient_boosting_absolute_loss"),
                                    paired("two_stage_chance_of_staying_x_average", "log_model_typical_value"), paired("two_stage_chance_of_staying_x_typical", "two_stage_chance_of_staying_x_average"),
                                    paired("two_stage_with_boosting_on_log_spend", "two_stage_chance_of_staying_x_average")],
             "paired_method": "bootstrap, 1,000 resamples of the 4,000 test advertisers; a difference whose interval includes 0 is a tie"}
    st = y2t > 0
    G_reg["typical_vs_average"] = {
        "what": "a model fitted on log spend predicts the TYPICAL (median) advertiser. Turned straight back into dollars and added up, that runs low, because a few large spenders pull the average above the typical value.",
        "advertisers_who_kept_spending": int(st.sum()), "actual_total": int(y2t[st].sum()),
        "total_error_using_typical_values": r(med_if_stay[st].sum() / y2t[st].sum() - 1, 3),
        "total_error_after_correcting_to_averages": r(mean_if_stay[st].sum() / y2t[st].sum() - 1, 3),
        "correction_factor": r(smear, 3),
        "but_on_mae": "the uncorrected 'typical' prediction scores a LOWER mean absolute error, because MAE rewards typical values. Which is right depends on the use: typical account vs revenue total."}
    lnames = [n_.split("__", 1)[1] for n_ in logm.named_steps["pre"].get_feature_names_out()]
    lcoef = logm.named_steps["m"].coef_
    sds = {c: float(XL[c][stay_tr].std()) for c in cont_l}
    eff = []
    for n_, c_ in zip(lnames, lcoef):
        if n_ in ("spend_8w", "log_run_rate"):
            continue
        d_ = {"feature": n_, "pct_change_in_spend": r(100 * (np.exp(c_) - 1), 1), "per": ("1 SD" if n_ in sds else ("yes vs no" if n_ in BIN else "vs ecommerce"))}
        if n_ in sds:
            d_["one_sd_is"] = r(sds[n_], 3)
            d_["pct_change_per_one_unit"] = r(100 * (np.exp(c_ / sds[n_]) - 1), 1)
        eff.append(d_)
    G_reg["log_model"] = {"what": "linear regression on log(spend_next_8w), fitted on training advertisers who kept spending",
                          "how_to_read": "on a log target the effects multiply: each row is the percent change in predicted spend, other columns held fixed. Associations, not causes.",
                          "effects": sorted(eff, key=lambda d: -abs(d["pct_change_in_spend"]))[:9], "residual_sd_log": r(float(np.std(res_log)), 3)}
    lm = lin_rr.named_steps["m"]
    ln = [n.split("__", 1)[1] for n in lin_rr.named_steps["pre"].get_feature_names_out()]
    G_reg["linear_dollars_coefs"] = {"model": "linear regression in dollars with the run-rate feature", "intercept": r(lm.intercept_, 0),
                                     "rows": sorted([{"feature": n, "dollars_per_unit": r(c, 2)} for n, c in zip(ln, lm.coef_)], key=lambda d: -abs(d["dollars_per_unit"]))[:8]}
    best = preds["two_stage_chance_of_staying_x_average"]
    q1, q2 = np.percentile(df.spend_8w.values[tr], [33.33, 66.67])
    tier = np.where(df.spend_8w.values[te] <= q1, 0, np.where(df.spend_8w.values[te] <= q2, 1, 2))
    G_reg["by_size_tier"] = {"model": "two-stage (chance of staying x average spend if staying)",
                             "rows": [{"tier": nm, "spend_8w_range": rng_, "n": int((tier == i).sum()), "mean_actual": r(y2t[tier == i].mean(), 0),
                                       "mae_model": r(np.abs(best - y2t)[tier == i].mean(), 0), "mae_same_as_last": r(np.abs(preds["same_as_last_8_weeks"] - y2t)[tier == i].mean(), 0),
                                       "wape_model": r(np.abs(best - y2t)[tier == i].sum() / y2t[tier == i].sum(), 3)}
                                      for i, (nm, rng_) in enumerate((("small", f"up to {q1:,.0f}"), ("medium", f"{q1:,.0f} to {q2:,.0f}"), ("large", f"above {q2:,.0f}")))]}
    ae = np.abs(best - y2t)
    top5 = ae >= np.percentile(ae, 95)
    G_reg["error_concentration"] = {"model": "two-stage", "share_of_total_error_from_worst_5pct_of_rows": r(ae[top5].sum() / ae.sum(), 3),
                                    "share_of_total_error_from_churners": r(ae[yt == 1].sum() / ae.sum(), 3), "share_of_rows_that_are_churners": r((yt == 1).mean(), 3),
                                    "mae_on_churners": r(ae[yt == 1].mean(), 0), "mae_on_stayers": r(ae[yt == 0].mean(), 0)}
    worst = np.argsort(-ae)[:5]
    te_idx = np.where(te)[0]
    G_reg["worst_misses"] = [{"advertiser_id": int(df.advertiser_id.values[te_idx[i]]), "spend_8w": r(df.spend_8w.values[te_idx[i]], 0),
                              "predicted": r(best[i], 0), "actual": r(y2t[i], 0), "churned": int(yt[i])} for i in worst]
    oracle = np.exp(hid.log_next_without_noise.values[te])
    mape_ = lambda p_: r(np.median(np.abs(p_[st] - y2t[st]) / y2t[st]), 3)
    G_reg["stayers_only"] = {"n": int(st.sum()), "what": "median percentage error among advertisers who kept spending",
                             "same_as_last": mape_(preds["same_as_last_8_weeks"]), "run_rate": mape_(preds["run_rate"]),
                             "gradient_boosting_absolute_loss": mape_(preds["gradient_boosting_absolute_loss"]), "log_model_typical_value": mape_(med_if_stay),
                             "noise_floor": mape_(oracle),
                             "noise_floor_is": "the error of the simulation's own formula with its random part removed - it even uses inputs the table does not contain. No model can beat it; the rest is noise."}
    G["regression"] = G_reg

    # ================= distance needs a ruler (for the clustering lesson) =================
    raw = df[NUM].copy()
    imp = SimpleImputer(strategy="median").fit(raw[tr])
    Utr, Ute = imp.transform(raw[tr]), imp.transform(raw[te])
    sc_raw = StandardScaler().fit(Utr)
    prep = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())])
    Ztr, Zte = prep.fit_transform(X[NUM][tr]), prep.transform(X[NUM][te])
    knn_auc = lambda A, B: r(roc_auc_score(yt, KNeighborsClassifier(n_neighbors=25).fit(A, y[tr]).predict_proba(B)[:, 1]))
    G["distance"] = {"what": "predict churn from the 25 most similar past advertisers (nearest neighbours); only the measuring stick changes",
                     "raw_columns": knn_auc(Utr, Ute), "standardised_columns": knn_auc(sc_raw.transform(Utr), sc_raw.transform(Ute)), "standardised_and_log_spend": knn_auc(Ztr, Zte),
                     "why_raw_fails": "spend is in the thousands while every other column is in single or double digits, so raw distance is almost entirely a spend difference",
                     "note": "25 neighbours was not tuned; the point is the comparison between rulers, not the level"}

    # ================= one hidden axis: PCA (kept small; used for a 2-D map, not as a lesson of its own) =================
    pca = PCA(n_components=len(NUM), random_state=0).fit(Ztr)
    evr = pca.explained_variance_ratio_
    G["pca"] = {"n_columns": len(NUM), "first_component_share_of_variance": r(evr[0], 3), "components_for_80pct": int(np.searchsorted(np.cumsum(evr), 0.8) + 1),
                "pc1_correlation_with_hidden_sophistication": r(abs(np.corrcoef(pca.transform(prep.transform(X[NUM]))[:, 0], hid.S.values)[0, 1]), 3),
                "caveat": "a tidy single hidden trait is how this simulation was built; on real account tables the first component is usually just account size"}

    # ================= a small neural network on the same table =================
    aucs, n_w = [], None
    for seed in range(6):
        mlp = Pipeline([("pre", lr_pipe().named_steps["pre"]), ("m", MLPClassifier(hidden_layer_sizes=(32, 16), early_stopping=True, max_iter=400, random_state=seed))]).fit(X[tr], y[tr])
        aucs.append(roc_auc_score(yt, mlp.predict_proba(X[te])[:, 1]))
        n_w = int(sum(c.size for c in mlp.named_steps["m"].coefs_) + sum(b.size for b in mlp.named_steps["m"].intercepts_))
    G["neural_net"] = {"architecture": "2 hidden layers (32 and 16 units)", "n_weights": n_w, "runs": 6,
                       "test_auc_lowest": r(min(aucs)), "test_auc_highest": r(max(aucs)), "test_auc_mean": r(np.mean(aucs)),
                       "note": "the same network trained six times from different random starting points; the spread between runs is itself a noise ruler"}

    # ================= forecasting: daily platform spend =================
    rs = np.random.default_rng(99)
    dates = pd.date_range("2024-01-01", "2026-04-30", freq="D")
    n = len(dates)
    t = np.arange(n)
    dow = dates.dayofweek.values
    doy = dates.dayofyear.values
    weekly = np.array([1.00, 1.04, 1.06, 1.05, 1.00, 0.82, 0.78])[dow]
    yearly = 1 + 0.10 * np.cos(2 * np.pi * (doy - 330) / 365.25) + 0.05 * np.cos(4 * np.pi * (doy - 330) / 365.25)
    level = 100000 * np.exp(0.00038 * t)
    bf_week, xmas, newyear = np.zeros(n, int), np.zeros(n, int), np.zeros(n, int)
    for yr_ in (2024, 2025):
        nov = pd.date_range(f"{yr_}-11-01", f"{yr_}-11-30")
        bf = nov[nov.dayofweek == 4][3]                               # the fourth Friday of November
        bf_week[(dates >= bf - pd.Timedelta(days=3)) & (dates <= bf + pd.Timedelta(days=3))] = 1
        xmas[(dates >= f"{yr_}-12-24") & (dates <= f"{yr_}-12-26")] = 1
    newyear[(dates.month == 1) & (dates.day == 1)] = 1
    known_event = (bf_week + xmas + newyear) > 0
    special = (1 + 0.22 * bf_week) * (1 - 0.20 * xmas) * (1 - 0.25 * newyear)
    e = np.zeros(n)
    sh = rs.normal(0, 0.028, n)
    for i in range(1, n):
        e[i] = 0.5 * e[i - 1] + sh[i]
    clean = (level * weekly * yearly * special * np.exp(e)).round(0)
    incidents = [("2025-09-16", 1, -0.40, "one-day outage"), ("2025-10-22", 2, -0.22, "two-day tracking bug"),
                 ("2025-12-09", 1, 0.35, "one-day traffic spike"), ("2026-01-20", 5, -0.12, "five-day slow leak"),
                 ("2026-02-28", 1, 0.30, "weekend spike"), ("2026-03-17", 1, -0.30, "one-day drop"), ("2026-04-08", 2, 0.25, "two-day surge")]
    mult = np.ones(n)
    inc_id = np.full(n, -1)
    for j, (d0, ln_, ch, _) in enumerate(incidents):
        i0 = int(np.where(dates == d0)[0][0])
        mult[i0:i0 + ln_] *= 1 + ch
        inc_id[i0:i0 + ln_] = j
    spend = (clean * mult).round(0)                 # the series people download; incidents included
    four = np.column_stack([f(2 * np.pi * k * doy / 365.25) for k in range(1, 4) for f in (np.sin, np.cos)])
    D = np.column_stack([t / 365.25, np.eye(7)[dow][:, 1:], four, bf_week, xmas, newyear])
    D_noev = D[:, :-3]
    H = 28
    origins = [int(np.where(dates == d)[0][0]) for d in pd.date_range("2025-05-01", "2026-04-01", freq="MS")]
    METHODS = ["last_value", "same_weekday_last_week", "average_of_last_4_same_weekdays", "trend_plus_seasonality_regression",
               "regression_not_told_about_holidays", "gradient_boosting_on_calendar"]
    HGB = dict(max_iter=300, learning_rate=0.05, max_depth=4, random_state=0)

    def forecasts(series, o, methods=METHODS):
        hz = np.arange(o, o + H)
        f = {}
        if "last_value" in methods:
            f["last_value"] = np.full(H, series[o - 1])
        if "same_weekday_last_week" in methods:
            f["same_weekday_last_week"] = np.array([series[o - 7 + (h % 7)] for h in range(H)])
        if "average_of_last_4_same_weekdays" in methods:
            f["average_of_last_4_same_weekdays"] = np.array([np.mean([series[o - 7 * w + (h % 7)] for w in range(1, 5)]) for h in range(H)])
        if "trend_plus_seasonality_regression" in methods:
            f["trend_plus_seasonality_regression"] = np.exp(LinearRegression().fit(D[:o], np.log(series[:o])).predict(D[hz]))
        if "regression_not_told_about_holidays" in methods:
            f["regression_not_told_about_holidays"] = np.exp(LinearRegression().fit(D_noev[:o], np.log(series[:o])).predict(D_noev[hz]))
        if "gradient_boosting_on_calendar" in methods:
            f["gradient_boosting_on_calendar"] = np.exp(HistGradientBoostingRegressor(**HGB).fit(D[:o], np.log(series[:o])).predict(D[hz]))
        return f

    def backtest(series, methods=METHODS):
        rec = {m: {"ape": [], "abs": [], "act": [], "tot": [], "byweek": [[] for _ in range(4)], "pct": []} for m in methods}
        for o in origins:
            act = series[o:o + H]
            for m, v in forecasts(series, o, methods).items():
                ape = np.abs(v - act) / act
                rec[m]["ape"].append(ape.mean())
                rec[m]["abs"].append(np.abs(v - act).sum())
                rec[m]["act"].append(act.sum())
                rec[m]["tot"].append(v.sum() / act.sum() - 1)
                rec[m]["pct"].append((act - v) / v)
                for w in range(4):
                    rec[m]["byweek"][w].append(ape[w * 7:(w + 1) * 7].mean())
        return rec

    def summarise(rec):
        return {m: {"mape": r(np.mean(v["ape"]), 4), "mape_worst_month": r(np.max(v["ape"]), 4), "wape": r(np.sum(v["abs"]) / np.sum(v["act"]), 4),
                    "error_of_28_day_total_typical": r(np.mean(np.abs(v["tot"])), 4), "error_of_28_day_total_average_signed": r(np.mean(v["tot"]), 4),
                    "mape_by_week_ahead": [r(np.mean(w), 4) for w in v["byweek"]]} for m, v in rec.items()}

    bt_clean, bt_inc = backtest(clean), backtest(spend)
    reg_pct = np.array(bt_clean["trend_plus_seasonality_regression"]["pct"])
    lo, hi = np.percentile(reg_pct[:6].ravel(), [10, 90])
    wk_bands = [[float(np.percentile(reg_pct[:6][:, w * 7:(w + 1) * 7].ravel(), q)) for q in (10, 90)] for w in range(4)]
    cover_wk = [float(((reg_pct[6:][:, w * 7:(w + 1) * 7] >= wk_bands[w][0]) & (reg_pct[6:][:, w * 7:(w + 1) * 7] <= wk_bands[w][1])).mean()) for w in range(4)]
    inc_pct = np.array(bt_inc["trend_plus_seasonality_regression"]["pct"])
    # a level shift no model was told about: +12% from 1 November 2025 onward
    shift_at = int(np.where(dates == "2025-11-01")[0][0])
    shifted = clean.copy()
    shifted[shift_at:] = (shifted[shift_at:] * 1.12).round(0)
    sm = ["average_of_last_4_same_weekdays", "trend_plus_seasonality_regression"]
    bt_shift = backtest(shifted, sm)
    lab = [str(dates[o].date())[:7] for o in origins]
    # a year ahead: can each method carry a trend forward?
    o1 = int(np.where(dates == "2025-05-01")[0][0])
    hz1 = np.arange(o1, n)
    f_reg = np.exp(LinearRegression().fit(D[:o1], np.log(clean[:o1])).predict(D[hz1]))
    f_gb = np.exp(HistGradientBoostingRegressor(**HGB).fit(D[:o1], np.log(clean[:o1])).predict(D[hz1]))
    trend_fit = LinearRegression().fit(D[:o1, :1], np.log(clean[:o1]))                       # take the trend out first ...
    resid = np.log(clean[:o1]) - trend_fit.predict(D[:o1, :1])
    f_gbd = np.exp(HistGradientBoostingRegressor(**HGB).fit(D[:o1, 1:], resid).predict(D[hz1, 1:]) + trend_fit.predict(D[hz1, :1]))   # ... and add it back
    yr = lambda f: {"mape": r(np.mean(np.abs(f - clean[hz1]) / clean[hz1]), 4), "error_of_total": r(f.sum() / clean[hz1].sum() - 1, 4), "error_of_total_last_90_days": r(f[-90:].sum() / clean[hz1][-90:].sum() - 1, 4)}
    # judging a forecaster the wrong way: shuffled folds let it fill in days BETWEEN days it has seen
    kf = KFold(5, shuffle=True, random_state=0)
    shuf = {"gradient_boosting_on_calendar": [], "trend_plus_seasonality_regression": []}
    for a_, b_ in kf.split(D):
        shuf["gradient_boosting_on_calendar"].append(np.mean(np.abs(np.exp(HistGradientBoostingRegressor(**HGB).fit(D[a_], np.log(clean[a_])).predict(D[b_])) - clean[b_]) / clean[b_]))
        shuf["trend_plus_seasonality_regression"].append(np.mean(np.abs(np.exp(LinearRegression().fit(D[a_], np.log(clean[a_])).predict(D[b_])) - clean[b_]) / clean[b_]))
    mfull = LinearRegression().fit(D, np.log(clean))
    coefs = mfull.coef_
    s_clean = summarise(bt_clean)
    G["forecast"] = {
        "series": "simulated daily platform ad spend, 2024-01-01 to 2026-04-30", "n_days": int(n),
        "what_is_in_it": "an upward trend (about 15% a year), a weekly rhythm (weekends about 20% lower), a yearly rhythm peaking in late November, Black Friday week, Christmas and New Year's Day effects, and day-to-day noise",
        "two_versions": "forecasting results below use the series WITHOUT the 7 planted incidents, so that forecast error is not confused with incident days; the downloadable file and the anomaly lesson use the series WITH them",
        "honest_caveat": "this world is stable by construction and the regression has the same form as the equation that generated the data (it is even told the holiday dates), so its accuracy is a best case; real series have breaks, pacing cycles and large-client moves",
        "mean_daily_spend_2024": r(clean[dates.year == 2024].mean(), 0), "mean_daily_spend_2025": r(clean[dates.year == 2025].mean(), 0),
        "growth_2025_vs_2024": r(clean[dates.year == 2025].mean() / clean[dates.year == 2024].mean() - 1, 3),
        "weekday_index": {d_: r(clean[dow == i].mean() / clean.mean(), 3) for i, d_ in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])},
        "month_index": {m_: r(clean[(dates.month == i + 1) & (dates.year == 2025)].mean() / clean[dates.year == 2025].mean(), 3) for i, m_ in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])},
        "backtest": {"how": "12 forecasts, one made on the first day of each month from May 2025 to April 2026, each for the next 28 days, each using only earlier data",
                     "metrics": {"mape": "average absolute percentage error per day", "wape": "total absolute error divided by total actual spend", "error_of_28_day_total": "how far the sum of the 28 daily forecasts is from the actual 28-day total"},
                     "methods": s_clean, "origins": lab, "mape_by_origin_regression": [r(v, 4) for v in bt_clean["trend_plus_seasonality_regression"]["ape"]],
                     "with_incidents_left_in": {m: {"mape": v["mape"], "mape_by_week_ahead": v["mape_by_week_ahead"]} for m, v in summarise(bt_inc).items()}},
        "regression_model": {"what": "log(spend) = trend + weekday effect + three yearly waves + Black Friday week + Christmas + New Year's Day",
                             "trend_per_year": r(np.exp(coefs[0]) - 1, 3), "black_friday_week_effect": r(np.exp(coefs[-3]) - 1, 3),
                             "christmas_effect": r(np.exp(coefs[-2]) - 1, 3), "new_year_effect": r(np.exp(coefs[-1]) - 1, 3),
                             "saturday_vs_monday": r(np.exp(coefs[5]) - 1, 3), "sunday_vs_monday": r(np.exp(coefs[6]) - 1, 3)},
        "interval": {"how": "take the regression's percentage errors from the first six backtests; the 10th and 90th percentiles give an 80% band; check it on the last six",
                     "one_band_for_all_horizons": {"low_pct": r(lo, 4), "high_pct": r(hi, 4), "coverage_on_later_backtests": r(((reg_pct[6:] >= lo) & (reg_pct[6:] <= hi)).mean(), 3)},
                     "by_week_ahead": [{"week": w + 1, "low_pct": r(wk_bands[w][0], 4), "high_pct": r(wk_bands[w][1], 4), "coverage_on_later_backtests": r(cover_wk[w], 3)} for w in range(4)],
                     "target_coverage": 0.8,
                     "same_band_when_incidents_happen": {"coverage_on_later_backtests": r(((inc_pct[6:] >= lo) & (inc_pct[6:] <= hi)).mean(), 3),
                                                         "why": "an interval built from past errors only covers the kinds of days it has already seen"}},
        "level_shift": {"what": "the same series, but from 1 November 2025 everything is 12% higher and stays there - a change no method was told about",
                        "months": lab,
                        "mape_by_month_normal_world": {m: [r(v, 4) for v in bt_clean[m]["ape"]] for m in sm},
                        "mape_by_month_after_the_shift": {m: [r(v, 4) for v in bt_shift[m]["ape"]] for m in sm},
                        "months_until_back_within_1_point_of_normal": {m: next((i for i in range(6, 12) if bt_shift[m]["ape"][i] - bt_clean[m]["ape"][i] < 0.01), None) and
                                                                          (next(i for i in range(6, 12) if bt_shift[m]["ape"][i] - bt_clean[m]["ape"][i] < 0.01) - 6) for m in sm},
                        "note": "index 6 is the November forecast, made the day the shift happens; both methods are wrong that month because neither had seen it"},
        "one_year_ahead": {"trained_through": "2025-04-30", "forecast_days": int(len(hz1)), "trend_plus_seasonality_regression": yr(f_reg),
                           "gradient_boosting_on_raw_level": yr(f_gb), "gradient_boosting_with_trend_removed_first": yr(f_gbd),
                           "why": "a tree can only output values it has seen, so asked about a date beyond its training data it reuses the most recent level; taking the trend out first (or predicting growth instead of level) fixes it"},
        "shuffled_folds_vs_backtest": {"what": "the same model judged two ways: on randomly held-out days (it has seen the days around them) versus on the 28 days after its training data ends",
                                       "gradient_boosting_on_calendar": {"mape_shuffled_folds": r(np.mean(shuf["gradient_boosting_on_calendar"]), 4), "mape_backtest": s_clean["gradient_boosting_on_calendar"]["mape"]},
                                       "trend_plus_seasonality_regression": {"mape_shuffled_folds": r(np.mean(shuf["trend_plus_seasonality_regression"]), 4), "mape_backtest": s_clean["trend_plus_seasonality_regression"]["mape"]}},
        "sample": {"dates": [str(d.date()) for d in dates[-140:]], "spend": [int(v) for v in spend[-140:]], "without_incidents": [int(v) for v in clean[-140:]]},
        "example_backtest": {"what": "the forecast made on 1 March 2026 for the next 28 days, by each method, with the 8 weeks before it",
                             "history_dates": [str(d.date()) for d in dates[origins[-2] - 56:origins[-2]]], "history": [int(v) for v in clean[origins[-2] - 56:origins[-2]]],
                             "dates": [str(d.date()) for d in dates[origins[-2]:origins[-2] + H]], "actual": [int(v) for v in clean[origins[-2]:origins[-2] + H]],
                             "forecasts": {m: [int(v) for v in f_] for m, f_ in forecasts(clean, origins[-2]).items()}},
        "monthly_totals": {"labels": [f"{d.year}-{d.month:02d}" for d in pd.date_range("2024-01-01", "2026-04-01", freq="MS")],
                           "millions": [r(clean[(dates.year == d.year) & (dates.month == d.month)].sum() / 1e6, 2) for d in pd.date_range("2024-01-01", "2026-04-01", freq="MS")]},
    }

    # ================= anomalies in the series (the version WITH incidents) =================
    w0 = int(np.where(dates == "2025-08-04")[0][0])
    idx = np.arange(w0, n)
    truth = inc_id[idx] >= 0
    ev = known_event[idx]

    def episodes(fl):
        fl = np.asarray(fl, bool)
        return int((fl & ~np.r_[False, fl[:-1]]).sum())

    def score(flags):
        fl = np.asarray(flags, bool)
        caught = sorted({int(j) for j in inc_id[idx][fl & truth]})
        false = fl & ~truth
        return {"alert_days": int(fl.sum()), "alert_episodes": episodes(fl), "incidents_caught": len(caught), "incident_days_caught": int((fl & truth).sum()),
                "false_alert_days": int(false.sum()), "false_alert_days_on_known_holidays": int((false & ev).sum()), "false_alert_days_unexplained": int((false & ~ev).sum()),
                "precision_by_day": (r((fl & truth).sum() / fl.sum(), 3) if fl.sum() else None),
                "missed": [incidents[j][3] for j in range(len(incidents)) if j not in caught]}

    dod = spend[idx] / spend[idx - 1] - 1
    expected = np.array([np.median([spend[i - 7 * w] for w in range(1, 7)]) for i in range(42, n)])
    dev = np.full(n, np.nan)
    dev[42:] = spend[42:] / expected - 1
    z = np.full(n, np.nan)
    for i in range(42 + 56, n):
        w = dev[i - 56:i]
        mad = 1.4826 * np.median(np.abs(w - np.median(w)))
        z[i] = (dev[i] - np.median(w)) / mad
    roll = np.full(n, np.nan)
    for i in range(42 + 6, n):
        roll[i] = dev[i - 6:i + 1].mean()                # average deviation over the last 7 days: small shifts add up
    zr = np.full(n, np.nan)
    for i in range(42 + 6 + 56, n):
        w = roll[i - 56:i]
        mad = 1.4826 * np.median(np.abs(w - np.median(w)))
        zr[i] = (roll[i] - np.median(w)) / mad
    naive = np.abs(dod) > 0.15
    leak_z = np.abs(zr[idx][inc_id[idx] == 3]) > 3
    # a baseline that knows the calendar: the forecasting regression, refitted at the start of each month on past data only
    exp_m = np.full(n, np.nan)
    for o in [int(np.where(dates == d)[0][0]) for d in pd.date_range("2025-04-01", "2026-04-01", freq="MS")]:
        end = min(n, o + 31)
        exp_m[o:end] = np.exp(LinearRegression().fit(D[:o], np.log(spend[:o])).predict(D[o:end]))
    res = spend / exp_m - 1
    zm, zm7 = np.full(n, np.nan), np.full(n, np.nan)
    r7 = np.full(n, np.nan)
    first = int(np.where(dates == "2025-04-01")[0][0])
    for i in range(first + 6, n):
        r7[i] = res[i - 6:i + 1].mean()
    for i in range(first + 70, n):
        w = res[i - 56:i]
        zm[i] = (res[i] - np.median(w)) / (1.4826 * np.median(np.abs(w - np.median(w))))
        w7 = r7[i - 56:i]
        zm7[i] = (r7[i] - np.median(w7)) / (1.4826 * np.median(np.abs(w7 - np.median(w7))))
    leak_m = np.abs(zm7[idx][inc_id[idx] == 3]) > 3
    G["series_anomalies"] = {
        "window": "2025-08-04 to 2026-04-30", "days": int(len(idx)), "incidents": [{"start": d0, "days": ln_, "change": ch, "what": nm} for d0, ln_, ch, nm in incidents],
        "incident_days": int(truth.sum()), "n_incidents": len(incidents), "known_holiday_days_in_window": int(ev.sum()),
        "naive_rule": {"rule": "alert when spend moves more than 15% versus yesterday", **score(naive),
                       "share_of_alerts_on_sat_or_mon": r(naive[(dow[idx] == 5) | (dow[idx] == 0)].sum() / max(naive.sum(), 1), 3)},
        "seasonal_baseline": {"rule": "expected = median of the same weekday over the previous 6 weeks; alert when today's deviation is more than k robust standard deviations from its recent norm",
                              "by_threshold": [dict(k=k, **score(np.abs(z[idx]) > k)) for k in (2, 2.5, 3, 3.5, 4, 5)],
                              "by_threshold_ignoring_known_holidays": [dict(k=k, **score((np.abs(z[idx]) > k) & ~ev)) for k in (2.5, 3, 3.5, 4)]},
        "seven_day_average": {"rule": "the same deviation averaged over the last 7 days, to catch small shifts that persist",
                              "by_threshold": [dict(k=k, **score((np.abs(zr[idx]) > k) & ~ev)) for k in (2.5, 3, 3.5, 4)],
                              "days_until_the_slow_leak_is_flagged_at_k3": (int(np.argmax(leak_z)) + 1 if leak_z.any() else None)},
        "forecast_as_baseline": {"rule": "expected = the trend-plus-seasonality forecast (refitted each month on past data); alert on the day's surprise, or on the average surprise over the last 7 days",
                                 "daily_by_threshold": [dict(k=k, **score(np.abs(zm[idx]) > k)) for k in (2.5, 3, 3.5, 4)],
                                 "seven_day_average_by_threshold": [dict(k=k, **score(np.abs(zm7[idx]) > k)) for k in (2.5, 3, 3.5, 4)],
                                 "either_at_k3": score((np.abs(zm[idx]) > 3) | (np.abs(zm7[idx]) > 3)),
                                 "slow_leak_first_flagged_on_day_at_k3": (int(np.argmax(np.abs(zm[idx][inc_id[idx] == 3]) > 3)) + 1 if (np.abs(zm[idx][inc_id[idx] == 3]) > 3).any() else None),
                                 "slow_leak_days_flagged_at_k3": int((np.abs(zm[idx][inc_id[idx] == 3]) > 3).sum()),
                                 "best_case_note": "this baseline is the same regression that generated-style data favours; on real series expect more false alerts",
                                 "typical_daily_surprise_pct": r(np.nanmedian(np.abs(res[idx])), 4)},
        "typical_daily_deviation_pct": r(np.nanmedian(np.abs(dev[idx])), 4),
        "widget": {"dates": [str(d.date()) for d in dates[idx]], "spend": [int(v) for v in spend[idx]], "incident": [int(v) for v in inc_id[idx]],
                   "holiday": [int(v) for v in ev], "day_over_day_pct": [r(v, 4) for v in dod],
                   "expected_same_weekday": [int(v) for v in spend[idx] / (1 + dev[idx])], "z_same_weekday": [r(v, 4) for v in z[idx]],
                   "expected_forecast": [int(v) for v in exp_m[idx]], "z_forecast": [r(v, 4) for v in zm[idx]]},
    }
    out = pd.DataFrame({"date": [str(d.date()) for d in dates], "spend": spend.astype(int)})
    return json.dumps(clean_json(G), allow_nan=False), out.to_csv(index=False)


RESULT2 = main2()
