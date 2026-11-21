### 1. VERDICT

This syllabus is not ready to ship because its evidence base contains serious methodological flaws—including temporal label leakage, log-retransformation bias, conflated decision-economics metrics, and simulated data artefacts that teach false rules of thumb about real-world models. It also devotes scarce lessons to academic model families an analyst will never deploy while omitting the data-engineering, calibration, and AI-sycophancy failure modes that actually break analyst-built HTML reports.

---

### 2. TECHNICAL RED FLAGS

*   **Missing embargo window and repeated-entity leakage**
    *   *Quote:* "12,000 advertiser snapshots over 6 months... churned in next 60 days... Train Jan–Apr, test May–Jun" and "bootstrap CI for logistic minus boosting is −0.001 to +0.009."
    *   *Why:* A snapshot on April 1 has a 60-day outcome window extending to May 31, overlapping the May–Jun test set; on May 1 you do not know March or April labels, so training on them leaks future macro conditions and entity outcomes across the split. Furthermore, 12,000 snapshots over 6 months implies ~2,000 repeated advertisers; standard row-level cross-validation and row-level bootstrapping violate independence, leaking entities across CV folds and artificially narrowing the bootstrap CI.
    *   *Correct statement:* A time split for a 60-day forward label requires a 60-day embargo between the last training snapshot date and the first test snapshot date, and both CV and bootstrap CIs must be clustered/grouped at the advertiser level (using expanding-window or group-aware splits).

*   **AUC as the universal metric and buried calibration**
    *   *Quote:* "Churn classification, test AUC: depth-3 tree 0.783 · logistic regression 0.848..." and "4-3 Opening the black box... calibration."
    *   *Why:* Treating ROC-AUC as the primary scoreboard on a 12.6% base rate hides poor precision in the top tail where adtech retention teams actually operate. Burying calibration inside an interpretability lesson ("Opening the black box") instead of Module 3 ("Judging models") teaches that predicted probabilities can be trusted out of the box, which breaks expected-value and threshold decisions.
    *   *Correct statement:* Pair ROC-AUC with PR-AUC (Average Precision) and top-K precision for imbalanced targets, and treat probability calibration (reliability diagrams, Brier score / log-loss) as a core evaluation gate in Module 3 before any score is used for decisions.

*   **Confusing marginal probability with cumulative list precision**
    *   *Quote:* "Decision economics (hypothetical costs): break-even precision 10%; best list size is ~1,600 of 4,000, far from the default 0.5 cut-off that flags 163." and "Always predict stays = 86.1% accuracy."
    *   *Why:* If 86.1% stay in the test set, the base churn rate is 13.9%—meaning flagging all 4,000 advertisers gives 13.9% precision, already above 10%. The optimal stopping point (~1,600) occurs where the *marginal* advertiser's calibrated churn probability drops to 10%, not where the *cumulative* precision of the list equals 10%; calling this "break-even precision 10%" will cause analysts to over-flag lists until average precision hits 10%, losing money on every marginal account below break-even.
    *   *Correct statement:* Optimal list sizing stops when the *marginal* calibrated probability (times expected save rate and LTV) equals intervention cost, not when the average precision of the entire list equals the break-even rate.

*   **Log-target retransformation bias and silent zero handling**
    *   *Quote:* "linear model on log spend 1,428... modelling log spend (multiplicative effects) beats the fancier model."
    *   *Why:* Exponentiating a prediction trained on `log(spend)` estimates the conditional geometric mean (roughly the median), not the conditional mean (Jensen's inequality). That systematically *under-predicts* total spend/revenue—often by 20–40% in heavy-tailed adtech data—while artificially winning on MAE because MAE is minimized by the median (comparing `exp(linear_log)` to squared-loss GBDT on MAE is a loss-function mismatch). Worse, 12.6% of accounts churn and likely have zero spend, meaning the model silently relies on an arbitrary `log(spend + c)` offset whose choice changes predictions.
    *   *Correct statement:* Modelling `log(spend)` requires explicit zero handling (or a two-stage hurdle model), bias correction on the back-transform (e.g., Duan's smearing estimator) whenever predictions will be summed into revenue forecasts, and comparing models under the same loss function aligned to the business objective (plus reporting total portfolio bias alongside MAE).

*   **Standardizing binary features and misreading odds ratios**
    *   *Quote:* "2-3 Logistic regression... Reading weights as odds; why standardise."
    *   *Why:* Standardizing binary indicators (e.g., `has_tracking`, `auto_bidding`) produces nonsensical stakeholder units ("odds per 1-SD increase in turning on auto-bidding") and conflates feature prevalence with effect size. Additionally, at 12.6%–36.5% churn rates, odds ratios diverge sharply from relative risks, and analysts routinely misreport an odds ratio of 2.0 as "twice as likely to churn."
    *   *Correct statement:* Standardize continuous features (or use meaningful business units like per-$1k or per-log-unit), leave binary flags unscaled, and translate logistic effects into predicted probability shifts (average marginal effects) rather than raw odds ratios for stakeholder reports.

*   **Interpretability methods that break under collinearity**
    *   *Quote:* "4-3 Opening the black box. Permutation importance, partial dependence, per-prediction contributions (SHAP idea)."
    *   *Why:* In adtech tables (and this dataset specifically, where PC1 captures 22% of variance), features like spend, impressions, clicks, and campaigns are strongly correlated. Permutation importance severely understates correlated features (credit splits across twins), PDPs average over impossible feature combinations (e.g., $100k spend with 0 impressions), and SHAP values on correlated features remain strictly non-causal associative decompositions that stakeholders misread as levers.
    *   *Correct statement:* Teach grouped permutation importance and ALE (or ICE plots with correlation warnings) over naive PDP, and explicitly warn that SHAP explains *the model's arithmetic*, not real-world business mechanics—especially when correlated proxies absorb credit from true drivers.

*   **Causal adjustment gaps and unrealistic B2B experimentation framing**
    *   *Quote:* "8-2 Experiments... sample size (1,468 per arm for a 5-point lift from 60%); when you cannot experiment; evidence tiers for wording a claim: observed, adjusted, tested."
    *   *Why:* Presenting a binary-proportion RCT needing 2,936 advertisers as the default causal path misleads a B2B adtech analyst: mid-market/enterprise advertiser pools rarely have 3,000 eligible accounts, spend/revenue metrics are power-law skewed (requiring 5–10x larger N or CUPED variance reduction), and advertisers compete in the same auction (network/marketplace interference violates SUTVA). Jumping straight from "adjusted" (cross-sectional regression) to "tested" (RCT) omits the main workhorse of B2B causal inference: quasi-experiments.
    *   *Correct statement:* Teach quasi-experimental designs (difference-in-differences, matched panel before/after, interrupted time series, regression discontinuity) as the primary tier between observational adjustment and RCTs, and cover power for heavy-tailed revenue metrics (CUPED) and auction interference.

*   **Forecasting: "trees cannot extrapolate", MAPE, and naive intervals**
    *   *Quote:* "Forecasting, 12 rolling 28-day backtests (MAPE)... One year ahead, boosting under-forecasts by 8.7% (trees cannot extrapolate); regression is within 0.3%. An 80% interval built from past errors covered 72%."
    *   *Why:* "Trees cannot extrapolate" is only true for raw level targets without detrending or differencing; real forecasting pipelines detrend or predict period-over-period growth/ratios with GBDT routinely. Daily MAPE over-weights low-volume days (weekends/holidays) and hides directional bias—adtech leadership cares about cumulative monthly/quarterly revenue error (WAPE and bias). Building a single 80% interval from pooled past errors ignores horizon-dependent variance growth and serial correlation of residuals.
    *   *Correct statement:* Evaluate spend forecasts primarily on WAPE and cumulative period bias (plus worst-case error), explain that tree models require differencing/detrending to handle trends, and build horizon-specific out-of-sample conformal/backtest intervals.

*   **Anomaly detection: ambiguous alert accounting and unscaled multivariate bias**
    *   *Quote:* "Seasonal baseline + robust z-score at 3 → 17 alerts, 6 of 7 incidents; the 5-day slow leak is missed. Row anomalies (60 planted)... all four detectors mostly miss the 20 'odd combination' accounts."
    *   *Why:* Reporting "17 alerts, 6 of 7 incidents" blurs point-level vs. incident-level evaluation (are the other 11 false alarms, or multi-day fires on the same 6 incidents?), and skips cumulative-sum / rolling-window methods (CUSUM, 7-day YoY) that catch slow leaks. Telling learners that "all four detectors mostly miss odd combinations" without diagnosing *why* (raw heavy-tailed spend/payment columns dominate isolation forest and distance metrics unless log-scaled or ratio-engineered) teaches fatalism instead of feature engineering.
    *   *Correct statement:* Measure time-series detectors on episode-level precision/recall and time-to-detect, pair point detectors with rolling/CUSUM checks for slow leaks, and teach that multivariate row anomalies require ratio/residual features or PCA reconstruction error on properly transformed scales.

*   **Text classification: accuracy on an underpowered 108-row test set**
    *   *Quote:* "360 synthetic tickets in 6 categories... keyword rules 57.4% · embeddings + logistic regression 93.5%... zero-shot LLM 95.4% (cheap) / 98.1% (stronger)."
    *   *Why:* Those exact percentages (`62/108`, `101/108`, `103/108`, `106/108`) reveal a test set of just 108 tickets (~18 per class). The gap between embeddings+LR (93.5%), cheap LLM (95.4%), and strong LLM (98.1%) is 2 to 5 tickets—statistically indistinguishable noise—and quoting plain accuracy violates Module 3's own rule against unweighted accuracy on multiclass/imbalanced data.
    *   *Correct statement:* Evaluate text classifiers with macro-F1, per-class precision/recall, and confidence intervals on a sufficiently sized test set (at least 50+ examples per rare class), and do not declare a model "stronger" on a 3-ticket difference.

*   **Monitoring & drift: late labels without leading proxies or intervention feedback loops**
    *   *Quote:* "9-2 Keeping a model honest... Monitoring predicted vs actual by segment; labels arrive late; retraining and champion/challenger."
    *   *Why:* For 60-day churn, waiting for "predicted vs actual" means you discover a June breakdown in September—two full months too late. Worse, once retention teams act on model scores, high-risk advertisers get saved, poisoning the training labels for the next retraining cycle (performative/intervention feedback loop); mentioning "feedback loops" only as an ethics bullet in 9-3 misses its operational impact on retraining.
    *   *Correct statement:* Pair delayed label monitoring with leading operational checks (upstream pipeline/null alerts, feature distribution shifts, score calibration drift, 7-day proxy outcomes), and log treatment/holdout flags so retraining either excludes treated rows or models the intervention explicitly.

---

### 3. SUSPICIOUS RESULTS

*   **Logistic regression beats/ties tuned GBDT (`0.848` vs `0.844`), and CV picks depth-1 trees**
    *   *Why suspicious:* This is a textbook artefact of simulating churn from an additive log-odds equation with no real interactions or thresholds. On real adtech tabular data (missingness patterns, non-linear CPA-vs-goal cliffs, vertical × tenure × spend interactions), tuned GBDT (LightGBM/XGBoost) beats unengineered logistic regression by 0.02–0.06 AUC almost every time.
    *   *Required caveat:* Explicitly state that the tie happened because the simulated data-generating process is nearly linear and clean; on real messy tabular data with non-linear interactions and missingness, GBDT usually wins, so always benchmark logistic regression *against* GBDT rather than assuming linear models tie.

*   **Linear model on log spend (`$1,428` MAE) beats GBDT (`$1,491` / `$1,694`)**
    *   *Why suspicious:* Pure artefact of a multiplicative log-normal simulation formula combined with comparing median-targeting (`exp(log_y)`) against mean-targeting (`L2` loss) using MAE.
    *   *Required caveat:* Show the total-dollar portfolio bias alongside MAE for every model, explain that `exp(log_y)` cheats on MAE by under-predicting high spenders, and note that GBDT trained on log-spend or Tweedie/Gamma loss typically matches or beats linear models on real skewed spend data.

*   **Feature ablation jumps `0.792 → 0.848` on "recent behaviour", with 71% precision in top 200**
    *   *Why suspicious:* In B2B adtech churn, a 5.5x lift at top 5% driven by "recent behaviour" (where `spend_trend < 0.7` alone flags 748 rows at 35% precision) strongly signals **functional churn**: accounts that already paused campaigns or ran out of budget 2–3 weeks before the snapshot date and are merely waiting for the 60-day inactivity clock to mark them "churned."
    *   *Required caveat:* Audit whether high-scoring accounts are already functionally dead (e.g., $0 spend in the last 14 days); teach analysts to separate "early warning" churn models (active accounts, actionable) from "already gone" accounts that inflate AUC without adding business value.

*   **Trend + seasonality regression hits `3.7%` MAPE and `0.3%` error one year ahead**
    *   *Why suspicious:* Forecasting daily adtech platform spend a full year out within 0.3% is pure fantasy—it only happens because the synthetic series has a fixed linear slope, deterministic seasonality, and zero structural breaks, budget-pacing cycles, macro shifts, or whale-advertiser churn.
    *   *Required caveat:* State bluntly that 0.3% one-year error is an artefact of stationary synthetic data; real adtech forecasts degrade rapidly past 4–8 weeks due to macro shocks, privacy/platform changes, and large-client shifts, and should be paired with scenario ranges rather than point accuracy claims.

*   **PCA first component = `22%` variance, `r = 0.815` with hidden trait, `0.801` AUC alone**
    *   *Why suspicious:* Clean single-factor latent variable artefact. On real advertiser tables, PC1 is almost always raw **account size/scale** (spend, impressions, clicks, campaigns), not "sophistication", and unlogged heavy-tailed columns hijack PCA entirely.
    *   *Required caveat:* Warn that real PCA on adtech tables usually just rediscovers "big vs. small advertiser" unless every scale column is log-transformed, normalized per dollar/impression, and winsorized.

*   **Text classification: `93.5%` embeddings, `95.4%`–`98.1%` zero-shot LLM, `92%` cluster purity**
    *   *Why suspicious:* LLM-generated synthetic tickets are clean, single-topic, typo-free, and aligned with the LLM's own priors. Real support tickets are multi-label, full of forwarded email chains/disclaimers/screenshots, and typically cap out at 75–85% human inter-annotator agreement—making 98.1% impossible in production.
    *   *Required caveat:* Disclose that synthetic tickets lack multi-label ambiguity and noise; require learners to measure human inter-annotator agreement on a 100-ticket sample first, because no model can meaningfully exceed the ambiguity ceiling of real labels.

*   **Clustering cleanly separates churn from `5.0%` to `36.5%`**
    *   *Why suspicious:* Because a single hidden trait drives all features and churn, almost *any* partition—including splitting spend into quartiles—produces a wide churn spread. Meanwhile, k-means on real power-law adtech metrics collapses into "1 cluster of 10 whale advertisers and 3 blobs of everyone else."
    *   *Required caveat:* Benchmark cluster outcome separation against simple business segments (e.g., spend tier × tenure) to prove clustering found genuine behavioural archetypes rather than rediscovering account size.

---

### 4. PRACTICE GAPS

*   **Silent data-engineering bugs in AI-generated Python scripts:** Coding assistants routinely introduce `pd.merge` many-to-many row fan-outs (silently duplicating advertisers across train and test), silent `dropna()` calls that drop 40% of rows (skewing results toward tracked advertisers), broken date/timezone parsing, and misaligned one-hot columns between train and test. The syllabus only checks 4 textbook ML bugs in 2-5.
*   **AI sycophancy and fabricated narrative in HTML reports:** When asked to produce an HTML report, AI assistants invent authoritative business explanations for noisy SHAP bars or collinear coefficients ("Account managers drive +11 pts goal attainment!"), hide small-N subgroups, omit baselines, and write executive summaries that contradict the caveats buried in footnotes.
*   **HTML deliverable reproducibility and chart integrity:** Analysts iterate with an AI assistant on HTML reports and routinely ship stale hard-coded numbers in prose that no longer match regenerated charts, misleading dual-axis or zero-truncated plots, missing sample sizes (`N`), and zero provenance (which SQL pull, date filter, eligibility rule, or model version produced the page).
*   **Population eligibility and "already dead" leakage:** Before modelling, analysts fail to audit who belongs in the scoring universe (e.g., excluding trial/test accounts, already-paused accounts with $0 spend for 30 days, agency shell accounts, or accounts without billing setup).
*   **Data privacy and governance with AI assistants:** Sending raw advertiser PII, contract revenue, or real support ticket transcripts to external LLM endpoints without verifying enterprise zero-data-retention policies.
*   **Staged briefing instead of one-shot prompting:** Asking an AI assistant for "a churn model and HTML report" in one prompt hides every upstream error; working analysts need a gated workflow (Stage 1: schema, row counts, null/duplicate assertions → Stage 2: target & split audit → Stage 3: baseline + model + slice calibration → Stage 4: HTML report generated programmatically from verified JSON outputs).

**Add to every lesson/case audit checklist:**
1. *Row-count & key conservation:* Does `len(df)` match the expected unique `(entity_id, snapshot_date)` count after every join and filter, with zero silent `dropna()` exclusions?
2. *Split & embargo proof:* Print `max(train_date)`, `min(test_date)`, entity overlap, and verify `max(train_date) + outcome_window <= min(test_date)`.
3. *Eligibility & dead-account check:* What % of top-decile predicted churners already had $0 spend or zero activity before the snapshot date?
4. *Slice & calibration check:* Are predicted averages within ±10% of actuals across major verticals, spend tiers, and tracked vs. untracked accounts?
5. *Prose-to-data binding:* Is every number in the HTML narrative rendered programmatically from the computed results object (not typed by the LLM), and does every claim stay within its causal evidence tier?
6. *Report provenance footer:* Does the HTML report state data pull date, eligibility filters, sample size `N`, baseline comparison, and key limitations at the top?

---

### 5. WHAT TO CUT

*   **Lesson 5-1 (Similarity and neighbours / k-NN):** A working adtech analyst will never deploy k-NN on tabular data. Fold the one useful takeaway ("distance-based and regularized models need feature scaling") into 2-3 and 5-2 in 60 seconds; if lookalikes matter, teach them via propensity scores or embeddings, not Euclidean k-NN.
*   **Lesson 5-3 (Compressing columns: PCA) and the "health index" half of Lab 4:** Analysts almost never ship a PCA-based "account health index" because executives cannot interpret or act on linear combinations of 15 standardized columns, and the weights shift every time you refit. Replace with a 2-minute mention inside EDA/collinearity.
*   **The neural-network anatomy half of Lesson 7-1 ("a neuron is a weighted sum with a bend; layers; 1,217 weights"):** An analyst who does not write Python and works on tabular adtech data + LLMs will never architect or tune a tabular MLP. Cut the toy MLP comparison entirely; move **embeddings** directly into 7-2 alongside LLMs and text classification.

---

### 6. TOP 10 CHANGES

1. **Fix the train/test embargo and grouped validation** by enforcing a 60-day gap between the last training snapshot and the first test snapshot, and switching all CV and bootstrap CIs to advertiser-grouped splits.
2. **Fix the log-spend regression lesson (2-2 and 3-3)** to handle zero-spend churners explicitly, expose Jensen's inequality / retransformation bias (Duan's smearing), compare models under matched loss functions, and report total portfolio dollar bias alongside MAE.
3. **Promote calibration and PR-AUC into Module 3** (reliability curves, Brier score, slice calibration) and fix 9-1's decision-economics math to separate marginal probability cut-offs from cumulative list precision.
4. **Replace Lesson 5-1 (k-NN) with an AI-assistant data and HTML audit lesson** covering silent `merge` fan-outs, `dropna()` bias, dead-account eligibility checks, programmatic prose-to-data binding, and staged assertion-gated prompting.
5. **Re-simulate the churn, spend, and ticket datasets to remove misleading DGP artefacts** by adding realistic non-linearities/interactions (so GBDT beats logistic regression), adding a budget-pacing cycle and regime shift to the time series, and injecting noisy/multi-label/ambiguous tickets with a larger test set (300+ test rows).
6. **Audit and remove "functional churn" leakage** from the recent-behaviour features—or explicitly teach separating already-inactive accounts from active early-warning accounts in 1-3 and 4-2.
7. **Replace Lesson 5-3 (PCA) with B2B quasi-experiments and heavy-tailed experimentation** (difference-in-differences, matched before/after, CUPED for revenue metrics, and marketplace interference) so Module 8 works when 3,000-advertiser RCTs are impossible.
8. **Overhaul Lesson 4-3 (interpretability)** to demonstrate how collinear adtech features break permutation importance, PDP, and SHAP, and add an audit test for catching causal overclaiming in AI-generated SHAP commentary.
9. **Fix Module 6 (forecasting)** to score daily spend with WAPE and cumulative monthly bias alongside MAPE, teach detrended/differenced tree forecasting instead of "trees cannot extrapolate," and compute horizon-specific out-of-sample intervals.
10. **Upgrade Lesson 9-2 (monitoring)** to pair delayed-label tracking with leading proxy monitors (pipeline/null assertions, input and score drift) and explain how retention interventions create retraining feedback loops unless holdouts are logged.