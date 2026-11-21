> **SUPERSEDED.** This is syllabus v2 (30 lessons), kept only as the document the review council read. The course as built is `content/OUTLINE.md` (v3, 37 lessons); several statements below are no longer true (for example the split is now train Jan-Mar, April left out, test May-Jun).

# Machine learning fundamentals for a working analyst — syllabus v2 (draft for council review)

## Who it is for

One learner: a data analyst at an adtech / native-advertising platform (clients = advertisers).
Strong in SQL, spreadsheets, BI. Basic statistics (knows correlation is not causation). Reads
simple pandas, writes little Python. Almost no ML. Most of their analysis is now produced by
an AI coding assistant, and deliverables are HTML reports — so the target skill is **direct
and audit**: frame the problem, choose an approach, brief the assistant, read what comes back,
catch the classic mistakes. Not hand-coding models. Fast learner who forgets without
reinforcement; prefers audio/video; has a few hours a week; wants lessons short and engaging.

They gave two *examples* of questions they are asked — "what separates happy advertisers from
unhappy ones, can we derive best practices?" and "can we predict which advertisers will churn?"
— and were explicit that the course must teach **general ML fundamentals**, not just those two
problems solved one way.

## Format

- 30 narrated lessons, 5–7 minutes each (750–1,000 spoken words), one idea per lesson. Each is
  a sequence of 7–10 segments; a visual (chart, table, diagram, small interactive widget)
  builds in step with a text-to-speech voice. The same audio works as an audio-only podcast.
- Every lesson: a take-a-guess question before, 5 scenario quiz questions after (at least one
  "the assistant's output has a flaw — spot it"), a 30-second explain-it-back prompt, a small
  mission to do at work, a ready-to-paste brief for the AI assistant, and an audit checklist.
  Each lesson also lists "where else this applies" (transfer) and "other ways to attack this".
- Retention: all quiz questions feed a spaced-repetition review queue (1, 3, 7, 14, 30, 60
  days), interleaved across lessons; a recap-only audio playlist; progress and streak tracking.
- Practice: 5 "case files" (audit a mock report from an AI assistant and find what is wrong)
  and 5 hands-on labs to run with their own assistant on downloadable CSVs, with expected
  results to check against.
- Tutor: an "Ask Claude" button on every lesson opens a chat pre-loaded with the lesson context.

## Evidence base — every number in the course is computed, none is quoted from memory

Simulated data, so nothing confidential is involved **and the true causal effects are known**
(we wrote the equations), which lets lessons compare a naive analysis with the truth.

1. **Advertiser table** — 12,000 advertiser snapshots over 6 months, 16 feature columns (profile,
   setup/practices, performance vs goal, recent behaviour), three outcomes: churned in next 60
   days (12.6%), spend in the next 8 weeks (dollars), hit own CPA goal ("happy" proxy, known only
   for the 58% with conversion tracking). A hidden trait ("sophistication") drives both good
   practices and good outcomes and is never in the table. Train Jan–Apr, test May–Jun; something
   changes for one vertical in June (for the drift lesson).
2. **Daily platform spend** — 851 days with trend, weekly and yearly seasonality, holiday
   effects, noise, and 7 planted incidents.
3. **Support tickets** — 360 synthetic tickets in 6 categories, embedded and classified.

Headline results the lessons are built on (all in `data/facts.json`):
- Churn classification, test AUC: depth-3 tree 0.783 · **logistic regression 0.848** · random
  forest 0.839 · gradient boosting 0.833 untuned / 0.844 tuned · small neural net 0.834 · k-NN
  0.795 (k=25, scaled) vs 0.618 unscaled. The simple model ties or wins; bootstrap CI for
  logistic minus boosting is −0.001 to +0.009.
- "Always predict stays" = 86.1% accuracy and finds no churners. Logistic at 0.5: precision 75.5%,
  recall 22.2%. Top 200 by score contain 142 churners vs ~28 at random. Hand rule
  `spend_trend < 0.7` flags 748 → 263 churners; the model's top 748 → 338.
- Leakage trap column: AUC 0.972 instead of 0.848.
- Tree depth sweep: train AUC → 1.00 while test AUC falls from 0.79 to 0.62.
- Feature groups (logistic): profile only 0.661 → + setup 0.754 → + performance 0.792 → + recent
  behaviour 0.848. Swapping the algorithm moved AUC by 0.004.
- Regression (next-8-week spend, MAE in dollars): same-as-last 2,380 · run-rate 1,996 · linear
  regression on raw dollars 2,265 · + run-rate feature 1,704 · gradient boosting 1,694 (squared
  loss) / 1,491 (absolute loss) · linear model on log spend 1,428 · two-stage (P(stay) × spend if
  stay) 1,412. Worst 5% of rows = 49% of total error. Perfect-model noise floor known: 17.0%
  median error vs 18.9% achieved.
- PCA: first component = 22% of variance, correlates 0.815 with the hidden trait, alone gives AUC
  0.801; 11 of 15 components needed for 80% of variance.
- Clustering: 4 behavioural segments with churn from 5.0% to 36.5% (labels not used).
- Forecasting, 12 rolling 28-day backtests (MAPE): last value 14.9% · same weekday last week 7.3%
  · average of last 4 same weekdays 6.8% · trend + seasonality regression 3.7% · gradient boosting
  on calendar features 6.6%. One year ahead, boosting under-forecasts by 8.7% (trees cannot
  extrapolate); regression is within 0.3%. An 80% interval built from past errors covered 72%.
- Anomalies in the series: "moved >15% vs yesterday" → 89 alerts in 270 days, 83 false, 83% on
  Saturdays/Mondays. Seasonal baseline + robust z-score at 3 → 17 alerts, 6 of 7 incidents; the
  5-day slow leak is missed. Row anomalies (60 planted): max z-score finds all 40 single-column
  extremes; all four detectors mostly miss the 20 "odd combination" accounts; isolation forest
  instead surfaces genuinely rare real accounts (46% with a payment failure vs 6.4%).
- Text: keyword rules 57.4% · embeddings + logistic regression 93.5% (80% with only 12 labelled
  tickets) · zero-shot LLM 95.4% (cheap) / 98.1% (stronger). Clustering embeddings recovers the
  topics with 92% purity.
- Causality: tracking vs churn — naive −11.5 pts, adjusted −6.6, **true −2.3**. Practices vs
  hitting the CPA goal (naive / adjusted / true): auto-bidding 19.0 / 14.9 / 11.1 · 4+ creatives
  21.6 / 17.1 / 9.2 · fresh creatives 18.4 / 14.9 / 5.8 · account manager 11.0 / 3.8 / 0.
- Drift: in June, one vertical's churn was predicted at 15.1% and came in at 31.2% while overall
  AUC barely moved (0.854 → 0.842).
- Decision economics (hypothetical costs): break-even precision 10%; best list size is ~1,600 of
  4,000, far from the default 0.5 cut-off that flags 163.

## Modules and lessons

### Module 0 — Start here
**0-1 How this works, and what ML is for.** What an analyst gains from ML (and what a dashboard
already does fine). The "direct and audit" role. How the course is built (guess → listen → quiz →
explain back → apply; spaced review). The datasets, and why simulated data lets us check the truth.

### Module 1 — Thinking in ML
**1-1 What a model is.** A model is a function learned from examples. Your hand-written rule
(`CASE WHEN spend_trend < 0.7`) is a one-feature model; ML lets the data choose columns,
cut-offs and weights. Vocabulary: row, feature, label, training, prediction, score.
**1-2 The map of machine learning.** Five analyst questions, five problem types. Supervised
(classification, regression, ranking), unsupervised (clustering, dimensionality reduction, anomaly
detection), forecasting, causal questions, generative/LLMs. Triage questions to pick the type.
The same business question can be framed several ways; choose by the decision it feeds. The
ladder: report → rule → simple model → complex model, and when ML is not worth it.
**1-3 Framing: target, unit, time.** The label is a business decision. Unit of analysis and grain.
Snapshot date, observation window, outcome window, eligibility. Proxies and their blind spots
("happy" measurable only for tracked advertisers, who differ: churn 7.9% vs 19.3%). Sanity-check
the label before modelling. Worked for churn, spend, and "happy".
**1-4 Leakage: too good to be true.** A feature that knows the future. AUC 0.972 vs 0.848 from one
column pulled from a current-state table. Sources of leakage, the time-travel test, point-in-time
SQL.

### Module 2 — First models
**2-1 Hold-out and baselines.** Test on data the model never saw; split by time when the question
is about the future. Baselines for a category (always-majority, a hand rule) and for a number
(mean, same-as-last, run-rate). A result means nothing without one.
**2-2 Linear regression: predicting a number.** Weighted sum fitted by least squares; reading a
coefficient ("holding the rest fixed"). Next-8-week spend: raw-dollar model loses to the run-rate
baseline until given the right feature; modelling log spend (multiplicative effects) beats the
fancier model. Skew, outliers, extrapolation.
**2-3 Logistic regression: predicting yes/no.** The same weighted sum squashed into a probability.
Reading weights as odds; why standardise. Test AUC 0.848, train 0.849. Limits: additive, correlated
features share credit, a weight is not a cause.
**2-4 Decision trees.** A flowchart learned from data = a GROUP BY the data designed. Reading the
fitted depth-3 tree (its first split rediscovers the hand rule). Interactions for free; coarse and
unstable alone (0.783). Trees for numbers too.
**2-5 Reading the assistant's code.** The six-part skeleton of every modelling script (load, X/y,
split, preprocess, fit, score). `fit`, `predict_proba`, pipelines. Four bugs to hunt: label/leak in
X, scoring on training rows (0.981 vs 0.839), fitting preprocessing before the split, a random
split on time-ordered data.

### Module 3 — Judging models
**3-1 Accuracy lies: precision and recall.** Rare outcomes make accuracy useless (86.1% for doing
nothing). Confusion matrix; precision and recall as two business costs; why not to "fix" imbalance
by default.
**3-2 Scores, thresholds and ranking.** The model gives a score; the cut-off is your decision.
Moving the threshold; top-K lists and lift; AUC as a ranking measure and what it hides. Interactive
threshold slider on the real test scores.
**3-3 Judging number predictions.** MAE vs RMSE vs R² vs percentage errors; bias; why the winner
depends on the metric and on the training loss; errors by segment; where the error concentrates;
the noise floor.
**3-4 Overfitting and honest validation.** Memorising vs learning (depth sweep, k=1 neighbours).
Underfitting. Train-vs-test gap as a warning. Hyperparameters; cross-validation on training data;
the fold spread as a noise ruler; regularisation in one idea; never tune on the test set.

### Module 4 — Stronger models, and what goes into them
**4-1 Forests and boosting.** Many trees averaged vs trees correcting each other. Untuned boosting
overfits (0.918 train / 0.833 test); tuned by CV it chooses depth-1 trees and ties logistic
regression. The scoreboard, the confidence interval, and the rule: adopt complexity only when it
beats the simple model by more than the noise.
**4-2 Features beat algorithms.** Feature groups ablation (0.661 → 0.848). Recipes: recency,
frequency, amounts, trends, ratios to a goal, breadth. Building them point-in-time in SQL. Skew
and logs, missing values as information, categories, dates.
**4-3 Opening the black box.** Permutation importance, partial dependence, per-prediction
contributions (SHAP idea), calibration. What each can and cannot tell you.

### Module 5 — Learning without labels
**5-1 Similarity and neighbours.** Distance needs a ruler: scaling (0.618 → 0.795). k-nearest
neighbours as the simplest model; k as a complexity dial. Lookalike lists. Why distance gets
harder with many columns.
**5-2 Clustering.** k-means as "GROUP BY without telling it the groups". Four behavioural
segments; choosing k has no right answer; results depend on columns and scaling; validate segments
on outcomes they never saw. Other methods by name.
**5-3 Compressing columns: PCA.** Many correlated columns, a few underlying directions. The first
component as an "account health" index that tracks a trait we never measured. When compression
helps (maps, indices, de-noising) and its cost (interpretability).

### Module 6 — Time
**6-1 Forecasting: start with the calendar.** Trend, weekly and yearly rhythm, events, noise.
Naive forecasts as baselines. A trend-plus-seasonality regression halves the error of the best
naive method.
**6-2 Backtesting and uncertainty.** Rolling-origin evaluation; error grows with horizon; worst
month vs average; prediction intervals from past errors and why they run narrow; why tree models
cannot extrapolate a trend; what forecasts cannot see.
**6-3 Anomalies: is this unusual?** Define usual first. The naive rule that fires every weekend;
seasonal baseline with a robust band; threshold = precision/recall again (alert fatigue); slow
leaks; anomalies in rows (single extremes vs odd combinations); "rare is not the same as wrong";
testing a detector with planted cases.

### Module 7 — Text and neural networks
**7-1 Neural networks and embeddings.** A neuron is a weighted sum with a bend; layers learn their
own features; trained by the same nudge loop. Where they win (images, audio, text) and why not on
a small table (1,217 weights: 0.834; logistic's 21 weights: 0.848). Embeddings: meaning as
coordinates; similar tickets sit close together.
**7-2 LLMs as analyst tools.** What a language model is. Four ways to classify text: keyword
rules, embeddings + simple model, zero-shot LLM, stronger LLM — and their costs. Evaluate an LLM
like any model: a labelled test set, confusion matrix, precision/recall. Failure modes
(confident errors, prompt sensitivity, privacy, cost). Why this is also the reason to audit your
coding assistant.

### Module 8 — From insight to decision
**8-1 Drivers are not causes.** Naive vs adjusted vs true effects (we know the truth here).
Confounding, reverse causation, selection; controlling for the wrong things; why a model weight or
importance is not a lever.
**8-2 Experiments.** Randomisation; encouragement designs; outcome and window fixed in advance;
sample size (1,468 per arm for a 5-point lift from 60%); when you cannot experiment; evidence
tiers for wording a claim: observed, adjusted, tested. Uplift: who changes because of the action.

### Module 9 — ML at work
**9-1 From score to action.** Capacity and unit economics pick the cut-off (break-even precision
10%, not 0.5); reasons attached to a risk list; holdout groups to measure the intervention;
predicted-to-leave is not the same as can-be-saved.
**9-2 Keeping a model honest.** Drift (inputs, relationships, definitions). Monitoring predicted
vs actual by segment; labels arrive late; retraining and champion/challenger. The June surprise.
**9-3 The brief, the audit, and choosing an approach.** One-page brief template; the ten-question
audit; a decision guide from business question to candidate approaches; when not to use ML;
responsible use (proxies for protected traits, privacy, feedback loops). Where to go next
(survival analysis, uplift modelling, recommendation).

## Case files and labs
- Case 1 *The 97% model* (after M2) · Case 2 *Which model ships?* (after M4) · Case 3 *What
  separates happy advertisers?* (after M5, revisited after M8) · Case 4 *The board forecast*
  (after M6) · Case 5 *The churn programme* (after M9).
- Lab 1 find the trap · Lab 2 baseline → model → top-K list · Lab 3 predicting spend: raw vs log
  · Lab 4 segments and a health index · Lab 5 forecast backtest.

## Known gaps we chose (challenge these)
- No maths derivations, no gradient descent beyond "nudge the weights to be less wrong".
- Named but not taught: SVMs, naive Bayes, survival analysis, recommender systems,
  reinforcement learning, deep-learning architectures, fine-tuning, MLOps tooling.
- Python is read, not written.
