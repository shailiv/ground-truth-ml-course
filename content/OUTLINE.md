# Ground Truth — course outline and lesson briefs (v3)

37 short lessons in 7 modules; about one module a week at 1½–2 hours. Every lesson: a guess-first
question, a 4½–6 minute narrated visual lesson, 4 scenario questions, an optional explain-it-back.
One work mission per module. A capped daily review draws rotating variants of two core ideas per lesson.

## The simulated worlds (all in `data/facts.json`; quote nothing else)

**A. Advertiser table** — 12,000 different advertisers, each seen once, in one of six monthly cohorts
(2,000 a month, Jan–Jun). 17 feature columns describing the 8 weeks before a snapshot date, and four
outcomes: `churned_next_60d`, `spend_next_8w`, `adopted_video_next_60d`, `hit_cpa_goal`.
Train on Jan–Mar (6,000), **leave April out** (its labels would not exist yet when May is scored),
test on May–Jun (4,000). A hidden trait, "sophistication", drives good practices and good outcomes
and is never in the table. In June something changes for gaming advertisers.
Columns: advertiser_id, snapshot_month, vertical, managed, tenure_weeks, spend_8w, spend_trend (last 4
weeks ÷ first 4 weeks), active_days_28, days_since_login, campaigns_active, creatives_per_campaign,
creative_refresh_days, has_conversion_tracking, uses_auto_bidding, had_optimisation_review, cpa_vs_goal
(above 1 = missing their goal; empty without tracking), ctr_pct, support_tickets_8w, payment_failures_8w.
**B. Daily platform spend** — 851 days; trend, weekly and yearly rhythm, holidays, noise. Forecasting
results use the series *without* the 7 planted incidents; the anomaly lesson uses it *with* them.
**C. Support tickets** — about a thousand synthetic tickets in 6 categories; the test tickets were written by a
different model and whole batches are held out (`facts.tickets`: use `n_test`, `n_test_hard` for the counts).
**D. Small side simulations** — repeated advertisers (`panel_leak`), an outreach experiment (`uplift`),
a launch with a comparison group (`before_after`), advertiser lifetimes (`time_to_event`).

Notation below: `→ key` means "numbers are in facts.json under key". **Before** = ideas you may rely
on. **Not here** = belongs to another lesson; do not teach it.

---

## Module 1 — Thinking in ML

### 1-1 From rules to learned models
**Idea:** a model is a rule whose columns, cut-offs and weights are chosen by data instead of by you.
**Hook:** the rule they would write today: flag advertisers whose spend trend is below 0.7.
**Cover:** that rule is a one-column model with a hand-picked cut-off · ML tries many columns and
cut-offs against thousands of past advertisers whose outcome is already known · vocabulary: row,
feature, label, training, score (a number between 0 and 1, not a yes/no) · learning = adjust until
outputs match known outcomes; then freeze and apply to new rows · matching the past is easy; holding
up on new rows is the whole game · what ML is not: it knows only the columns it was given ·
their role: director and auditor — the assistant writes code in minutes but cannot know what churn
means for the business or when a column was recorded.
**Evidence:** → data (n, one_row_is, feature_columns, sample_rows). No model results yet.
**Visuals:** SQL `CASE WHEN` (code), a small table (features | label), flow (learn → freeze → score).
**Not here:** metrics, splits, any algorithm by name.

### 1-2 Which kind of problem is this?
**Idea:** the first decision is the kind of problem; the same business question can be framed several ways.
**Hook:** five questions from one week: who will leave · how much will they spend · what kinds of
advertisers do we have · is yesterday's drop unusual · does auto-bidding actually help.
**Cover:** the map — predict a category (classification), predict a number (regression), find groups
without an answer column (clustering), judge what is unusual (anomaly detection), project a series
forward (forecasting), ask what happens if we *change* something (causal), read or write text
(language models) · four triage questions: is there an answer column for past cases? category or
number? is time the main axis? do I want to predict it or change it? · one question, several
framings (retention as yes/no in 60 days, as dollars next quarter, as how long they last, as who can
be saved) — choose by the decision it feeds · the ladder: a report → a rule → a simple model → a
complex model; climb only when the step pays.
**Evidence:** none needed; you may name the four outcome columns of world A.
**Visuals:** table (question → kind), bullets (triage), flow (ladder).
**Not here:** how any method works.

### 1-3 Framing: target, unit and time
**Idea:** the label is a business decision, pinned to a timeline — and whoever is not eligible or not
yet observed quietly distorts it.
**Hook:** "is an advertiser who paused for three weeks churned?" Nobody in the room agrees.
**Cover:** unit and grain (one row = one advertiser at one snapshot) · snapshot date; observation
window before it (8 weeks), outcome window after it (60 days) · eligibility: who is in — an account
that already stopped is not a prediction · the outcome window must have fully elapsed (a customer
who joined 20 days ago has not "survived 60 days") · proxies have blind spots: "happy" = hit their CPA
goal, measurable only for the 58% with tracking, and those differ (churn about 7% vs 18%) · check a
label before modelling: rate by month, read twenty examples of each class.
**Evidence:** → data (churn_by_month, tracking_rate, n_tracked, hit_goal_rate_tracked, why_a_gap),
churn_by.has_conversion_tracking.
**Visuals:** timeline (observation | snapshot | outcome), compare (tracked vs untracked), bar (churn by month).
**Not here:** leakage (next lesson — end by pointing to it).

### 1-4 Leakage: features that know the future
**Idea:** a column recorded after the prediction moment makes a model look brilliant and be useless.
**Hook:** the assistant returns in four minutes: of its 200 highest-risk advertisers, all 200 churned.
**Cover:** the honest model's top 200 contain 136 churners; with one extra column, 200 of 200 ·
the column: days since last spend, read from *today's* accounts table — typical value 86 days for
churners, 3 for the rest: the outcome in disguise · why it fails in production: on the day you
score, that value does not exist yet · where leaks come from: current-state tables, fields updated
after the event, totals computed over a window that runs past the snapshot, the label in another
form · the time-travel test: could I have computed this on the snapshot date using only data up to
then? · the fix: build features from dated events with a date filter.
**Evidence:** → leakage (top_200_churners_with_leak / _honest, median_value_churned / _stayed).
Describe success as "how many of the top 200 really churned". Do not use the term AUC.
**Visuals:** compare (200 of 200 vs 136 of 200), timeline with a `bad` span, table (leak sources), SQL with a date filter.
**Before:** label, snapshot, outcome window. **Not here:** train/test (say "on advertisers the model had not seen").

### 1-5 Brief in stages, audit by evidence
**Idea:** never ask for "a model and a report" in one go; work in gated stages, and make the assistant
*show* its work so you audit outputs, not code.
**Hook:** one prompt, one beautiful HTML report, and no way to tell which of its numbers to trust.
**Cover:** four stages, each with a gate you check before the next — (1) the table: what one row is,
row counts, date range, duplicates, missing values; (2) the target and the split: definition, rate by
month, which rows train and which test; (3) baseline, then model, on the same test rows; (4) the report,
built from the checked numbers · the **audit block** every output must carry: row counts after
every step, dates, label rate, the feature list with where each column came from, the baseline next
to the model · you check evidence in the output, not Python · what to send back when a number looks
too good: "show me the top five columns and when each was recorded" · data hygiene with assistants:
do not paste client data into a tool that is not approved for it.
**Evidence:** → data (n, n_train, n_gap, n_test, churn_rate_train, churn_rate_test) as the kind of facts an audit block states.
**Visuals:** flow (four stages), bullets (audit block), compare (one-shot prompt vs staged).
**Not here:** specific metrics or bugs — later lessons add one check each to this list.

---

## Module 2 — The scoreboard: how to judge before you build

### 2-1 Hold-out, the gap, and baselines
**Idea:** a result only counts on rows the model never saw, split the way it will be used, and next to a baseline.
**Hook:** "the model is 88 percent accurate." Compared with what, measured on what?
**Cover:** hold out a test set · split by time when the question is about the future: train Jan–Mar,
test May–Jun · **why April is left out**: churn takes 60 days to show, so on the day you score May
you do not know April's answers · the test set is a sealed envelope · baseline one: predict that
everyone stays — about 87 percent "accurate", finds none of 527 churners · baseline two: the hand
rule flags 711 and 246 really churn; that is the bar · baselines for a number: the average,
same-as-last-period.
**Evidence:** → data, baseline, split (the three AUC-free facts: say only that on this table a random
split and a time split score almost the same, and why time is still right).
**Visuals:** timeline (train | gap | test), stat (always-stay), stat (the rule).
**Before:** label, outcome window, leakage. **Not here:** precision/recall as terms (say "of those flagged, how many really churned").

### 2-2 Accuracy lies: precision and recall
**Idea:** when the outcome is rare, accuracy says almost nothing; ask two questions instead.
**Hook:** predicting "nobody churns" is about 87 percent accurate.
**Cover:** the four boxes for the model at a 0.5 cut-off: 141 flagged — 104 right, 37 false alarms;
423 churners missed · accuracy about 88.5 percent, barely above doing nothing · precision: of those
flagged, how many were right (about 74 percent) — the cost of acting on false alarms · recall: of all
who churned, how many were caught (about 20 percent) — the cost of the ones nobody called · they pull
against each other; which matters is a business call · rarity is not a bug to "fix" by rebalancing
the data; keep the data, choose the right measures.
**Evidence:** → thresholds (the row with threshold 0.5), baseline, uncertainty (precision_at_half_95, recall_at_half_95 — one sentence that these wobble).
**Visuals:** matrix, formula (precision), formula (recall), compare (accuracy of nothing vs of the model).
**Before:** baselines, test set. **Not here:** moving the cut-off (next lesson).

### 2-3 Scores, cut-offs and ranked lists
**Idea:** the model gives a score; where to cut is your decision, and the honest summary is how well it ranks.
**Hook:** nobody said the cut-off had to be 0.5.
**Cover:** lower the cut-off to 0.2: about 690 flagged, 60 percent of churners caught, precision about
46 percent · **widget `threshold`** · often simpler: sort and take the top K the team can handle —
top 200 hold 136 churners where a random 200 would hold about 26 · same list size as the hand rule
(711): the model finds 321 against the rule's 246 — the only fair comparison · AUC, properly: pick
one churner and one stayer at random; AUC is how often the churner gets the higher score; 0.5 is a
coin, 1 is perfect; here about 0.85 · what AUC hides: the top of the list, and whether the percentages are right.
**Evidence:** → thresholds, top_k, lift, baseline.model_same_count, logreg.test.auc, uncertainty.top_200_churners_95.
**Visuals:** widget threshold, table (top-K), bar (churn rate by decile, first four), quote (AUC in one sentence).
**Before:** precision, recall. **Not here:** calibration (next).

### 2-4 Can you trust the percentage?
**Idea:** ranking well and being right about the percentage are different things; check the second before you multiply by money.
**Hook:** the model says 30 percent. Of advertisers it said that about, how many left?
**Cover:** calibration: group advertisers by predicted risk and compare with what happened — **widget
`calibration`** · here every group ran a little low: it said about 25 percent, about 33 percent left ·
why: it learned from months with 11 percent churn and is tested when churn is 13 percent — on its
own training months, predicted and actual match exactly · ranking is intact; the numbers are low ·
when it matters: any time you multiply a probability by dollars or compare it with a cut-off in
percent · what to ask for: a predicted-versus-actual table, overall and by segment.
**Evidence:** → calibration (logreg bins, overall, on_training_months, why_it_runs_low).
**Visuals:** widget calibration, compare (training months vs test months), table (bins).
**Before:** scores, cut-offs. **Not here:** fixing calibration methods (name "recalibration" at most); drift as a topic (5-6).

### 2-5 Judging number predictions
**Idea:** for a predicted number, choose the error measure by what a miss costs — the measures can disagree.
**Hook:** finance asks how much each advertiser will spend in the next 8 weeks; two candidate models, and each "wins".
**Cover:** MAE: the typical miss, in dollars · the bar to beat: same-as-last-period misses by about
2,400 dollars; the run-rate (twice the last four weeks) by about 2,000 · RMSE counts big misses much
more · two models with nearly the same typical miss (about 1,700) — one has far worse big misses:
which wins depends on whether a rare huge miss hurts more than many small ones · bias and totals:
same-as-last runs about 23 percent low in total · averages hide: nearly half of all error comes from
5 percent of advertisers; look by size tier · percentage errors break when the actual is zero.
**Evidence:** → regression (models: same_as_last_8_weeks, run_rate, linear_regression_dollars_plus_run_rate,
gradient_boosting_squared_loss; paired_differences; error_concentration; by_size_tier; share_zero).
Refer to the two candidates as "model A" and "model B" — their internals come later.
**Visuals:** table (baselines and two models: MAE, RMSE, total error), bar (MAE by tier), stat (concentration).
**Before:** baselines. **Not here:** how regression works (3-1); log scale (3-1).

### 2-6 Real or noise?
**Idea:** every number from a sample wobbles; before reacting to a difference, ask how big it would be by chance.
**Hook:** gaming churn was 14 percent in March and 19 percent in April. A stakeholder wants a meeting.
**Cover:** margin of error shrinks with the square root of the group: about ±6 points for 100
advertisers, ±2 for 1,000, under ±1 for 12,000 · the A/A test: split advertisers at random into two
groups of 250 and half the time the "gap" exceeds 2 points — with nothing going on · that March to
April jump is within noise (about 250 advertisers a month); June against the first four months is not ·
the same for models: a score has an interval too; a gap between two models smaller than their
interval is a tie · what to ask for: the group size and an interval beside every comparison.
**Evidence:** → noise (margin_of_error_for_a_churn_rate, aa_test, comparisons, gaming_monthly), uncertainty (logreg_auc_95).
**Visuals:** bar (margin of error by group size), stat (A/A result), table (three comparisons with intervals).
**Before:** AUC as a score. **Not here:** experiment design (5-2).

---

## Module 3 — Core models, and reading the work

### 3-1 Linear regression: predicting a number
**Idea:** a weighted sum fitted to past outcomes — and the scale you fit on matters more than the cleverness of the fit.
**Hook:** the run-rate baseline misses by about 2,000 dollars. Can a model that looks at every column beat it?
**Cover:** one weight per column, chosen to make the squared misses as small as possible; a weight
reads "holding the rest fixed" · in raw dollars with every column: misses by about 2,360 — *worse*
than the baseline · give it the run-rate as a column: about 1,730 · money is skewed: a few very
large accounts dominate a squared-error fit · fit on the log of spend, so effects multiply ("a
managed account spends about 13 percent more") — about 1,430, the best of the ladder · the catch:
turned back into dollars, a log model gives the *typical* advertiser, not the average; added up it
runs about 4 percent low unless corrected · limits: straight-line effects, extrapolation.
**Evidence:** → regression (models, paired_differences, typical_vs_average, log_model.effects, target_median, target_mean, target_max).
**Visuals:** bar (MAE ladder), formula (weighted sum), table (log-model effects), compare (typical vs average total).
**Before:** MAE, RMSE, baselines. **Not here:** boosting by name beyond "a more flexible model"; the two-stage model (5-5).

### 3-2 Logistic regression: predicting yes or no
**Idea:** the same weighted sum, squashed into a probability; readable weights — which are not causes.
**Hook:** account managers already keep a mental scorecard. This learns the weights.
**Cover:** points for each column, summed, pushed through an S-curve to land between 0 and 1 ·
reading the result: spend trend is the heaviest — one typical step up cuts the odds of churn by more
than half; in plain terms about 5 points off the predicted probability · why continuous columns are
put on a common scale first; yes/no flags are left as they are · train and test scores nearly equal
(about 0.85 both): it is not memorising · limits: each column pushes one way at a steady rate;
overlapping columns share the credit · a weight is an association: tracking gets a big weight; a
later lesson shows its true effect is small.
**Evidence:** → logreg (coefs with odds_ratio and avg_probability_shift_pts, test.auc, train_auc, n_weights), baseline.model_same_count.
**Visuals:** formula, bar (probability shift per column, top 6), stat (train vs test), quote (weight ≠ cause).
**Before:** AUC, calibration. **Not here:** trees, tuning.

### 3-3 Decision trees
**Idea:** a flowchart of yes/no questions learned from data — a GROUP BY the data designed; readable, but coarse alone.
**Hook:** left to choose its own questions, the tree asks about active days first — and then, on both branches, whether spend trend is below about 0.7. It rediscovered your rule on its own.
**Cover:** how it is grown: try every column and cut, keep the split that best separates churners,
repeat in each branch, stop at a depth · **widget `tree`**: read two paths — few active days, shrinking spend and a small
account: about two in three churn; active with spend holding up: about one in thirty · each leaf is a segment
with a rate · "it depends" comes free: low activity matters more when spend is also falling · the
price: eight leaves means eight possible scores — it ranks worse than the weighted sum on churn
(about 0.76 against 0.85) · the same idea predicts numbers: a leaf predicts its average.
**Evidence:** → tree (root, test.auc, train_auc, leaves), logreg.test.auc.
**Visuals:** widget tree, table (three leaves: rule, advertisers, churn rate), compare (tree vs weighted sum).
**Not here:** many trees (4-3), overfitting with depth (4-1).

### 3-4 Dirty tables: what breaks before the model
**Idea:** the commonest damage is done by a join or a dropped row before any model is fitted, and it leaves no error message.
**Hook:** the report says churn is 7 percent. Your dashboard says 12. Nothing crashed.
**Cover:** dropping rows with a missing value: CPA versus goal is empty for advertisers without
tracking, so 42 percent of rows vanish — and with them nearly two thirds of the churners · a model
trained on the survivors tells the untracked they have a 9 percent risk; the truth is about 20 ·
missing is information: keep a flag, do not fill silently · a join to a table with several rows per
advertiser multiplies rows: 12,000 advertisers become 31,000 rows and total spend is overstated by
about 160 percent · an inner join keeps only the matched: 69 percent of advertisers gone · ID columns are
never features · the check that catches all of these: count rows and distinct advertisers before and
after every step.
**Evidence:** → dirty_tables (dropna, missing_is_information, join_fan_out, inner_join_drop).
**Visuals:** stat (rows and churners before/after), SQL showing a fan-out join, table (step | rows | advertisers), compare.
**Before:** staged briefing. **Not here:** repeated advertisers in validation (4-2).

### 3-5 Reading the assistant's script
**Idea:** every modelling script has the same six parts; if you can find them you can audit it without being able to write it.
**Hook:** eighty lines of Python and "AUC 0.98".
**Cover:** the skeleton: load · choose features and label · split · prepare (fill, scale, encode) ·
fit on training rows · score on test rows · the words: `fit` learns, `predict_proba` gives scores, a
pipeline keeps preparation and model together · four places bugs live, each tied to a line: the
label or a leak inside the features; scoring on the training rows (the forest scores 0.98 on rows it
trained on and 0.83 on new ones); preparation fitted on everything before the split; a shuffled
split when the question is about the future · two quiet ones: `try/except` that swallows an error and
carries on; hard yes/no predictions used where scores were needed · ask for a header comment that
states all of this.
**Evidence:** → forest (train_auc, test.auc).
**Visuals:** code (a clean 12-line script), flow (six parts), code (a short buggy snippet), bullets (where to look).
**Before:** everything in modules 1–2, the three model types.

---

## Module 4 — Stronger models, honestly validated

### 4-1 Overfitting: memorising versus learning
**Idea:** a flexible enough model can memorise its training rows; the gap between training and new rows is the tell.
**Hook:** let the tree grow to 25 levels: a perfect score on its training rows.
**Cover:** **widget `depth`**: training score climbs to 1.0 while the score on new advertisers peaks
around depth 3–4 (about 0.77) and falls to about 0.6 — worse than a single question; a fully grown tree
ends up answering only yes or no · why: hundreds of leaves
each holding a handful of advertisers; their quirks become "rules" · the other failure: too simple
(one question scores about 0.66) · so every report shows both numbers · a gap is a warning to look,
not a verdict: the test number is the truth · the general cure, in one idea: make the model pay for
complexity (shallower, fewer, smaller weights).
**Evidence:** → depth_sweep, logreg (train_auc vs test), forest.
**Visuals:** widget depth, compare (train vs test at depth 25), bullets.
**Not here:** how to choose the setting (next lesson).

### 4-2 Validation without cheating
**Idea:** choosing settings is also learning from data — do it on training data, in folds that respect time and who is who.
**Hook:** if you pick the depth that scores best on the test set, the test set has trained your model.
**Cover:** settings are chosen before the final exam: train / validation / test · cross-validation:
cut the training data in five, train on four, check on the fifth, rotate; the five scores also show
the wobble (here about 0.82 to 0.87) · the trap: when the same advertiser appears in many rows,
shuffled folds put it on both sides — a flexible model then scores 0.80 in validation and 0.63 on
advertisers it has never met; a simple model shows no such gap · leave an ID column in and it is
worse · fix: whole advertisers held out together, and never train on the future · how much data is
enough: the simple model gets most of the way with about a thousand rows.
**Evidence:** → cv, depth_sweep (cv_auc_on_training_months), panel_leak (random_forest, logistic_regression, random_forest_with_the_id_column_left_in), boosting.tuning.
*(After review: this lesson now shows choosing the depth honestly by cross-validation; "how much data is enough" and the learning curve moved to 4-4.)*
**Visuals:** flow (train | validation | test), bar (three ways to score, flexible vs simple), line (learning curve).
**Before:** overfitting, noise. **Not here:** boosting itself.

### 4-3 Forests and boosting
**Idea:** many trees fix one tree's coarseness — and whether that beats a simple model depends on the shape of the pattern, so you measure.
**Hook:** two questions, same table, same models. On one the simple model wins. On the other it loses clearly.
**Cover:** forest: many trees on shuffled samples, averaged · boosting: small trees in sequence, each
correcting the last; powerful, with settings to choose · untuned boosting on churn memorises (0.94
on training rows, 0.83 on new); tuned by cross-validation it prefers very shallow trees and lands
just *below* the weighted sum (0.836 against 0.845) · second question — who will adopt video ads —
is driven by thresholds and combinations: boosting wins by about 0.04 and prefers deeper trees; a
hand-built combination column closes half the gap for the simple model · a small neural network on
churn: no better, and its score moves by a few points between runs · the rule: run both, compare
the gap with the noise, and pay for complexity only when it buys something.
**Evidence:** → model_table, boosting, uncertainty (difference_logreg_minus_boosting_95), video (scoreboard, boosting_minus_logistic_95, compare_with_churn, how_it_was_built), neural_net.
**Visuals:** table (two scoreboards side by side), compare (the two gaps with intervals), flow (forest vs boosting).
**Caveat to state:** which model wins on churn here is a property of how this world was built.

### 4-4 Features: where your knowledge goes in
**Idea:** what you feed a model moves the result far more than which model you pick.
**Hook:** swapping between the two best algorithms moved the score by about 0.01. Watch what the columns do.
**Cover:** add column groups one at a time: who they are 0.66 → how they are set up 0.76 → performance
against goal 0.79 → recent behaviour 0.85 · recent behaviour alone nearly matches everything ·
recipes that travel: how recent, how often, how much, the trend, the ratio to a goal, the breadth ·
features are built in SQL from dated events with a date filter — their home turf, and where a leak
gets in · spend is modelled on a log scale; a ratio to the advertiser's own goal beats a raw CPA ·
every new column: when is it known, and will it exist on the day we score?
**Evidence:** → feature_groups (cumulative, each_group_alone, spread_across_feature_sets, spread_across_algorithms), video, learning_curve.
*(After review: opens on the video-adoption list; carries the learning-curve segment "would more rows help, or better columns?")*
**Visuals:** bar (cumulative AUC by group), SQL (point-in-time aggregation), table (recipes).
**Before:** leakage, both scoreboards. **Not here:** dirty-table bugs (3-4).

### 4-5 Opening the black box
**Idea:** three questions you can ask any model — what does it lean on, how does its answer move, why this advertiser — none of which is "what causes churn".
**Hook:** an account manager asks why advertiser 111754 is on her list at 73 percent.
**Cover:** overall: shuffle one column and see how much the score falls — spend trend first, activity
second · overlapping columns hide each other, so shuffle a whole group: recent behaviour costs 0.18,
every other group under 0.03 · shape: as CPA versus goal rises the predicted risk climbs — that is
the model's behaviour, not a promise about the advertiser · this advertiser: few active days, CPA
far over goal and stale creatives push her risk up; each push is the column's weight times how far
she is from average (for complex models the same idea goes by the name SHAP) · that is what makes a
list usable · and it is the model's arithmetic, not a cause — the next module.
**Evidence:** → importance (rows, grouped), partial_dependence (curves.cpa_vs_goal), explain_examples (the "high risk" example, average_advertiser_probability).
**Visuals:** bar (importance), line (CPA vs goal → predicted churn), table (pushes for one advertiser).
**Not here:** calibration (done), causality (5-1).

### 4-6 Who is the model wrong about?
**Idea:** one overall score hides who the model fails; cut the result by segment, and choose what you rank by.
**Hook:** the list of 400 looks great. 259 of the 400 are small accounts.
**Cover:** by size: the model catches about 55 percent of small churners and 25 percent of large
ones — though large accounts are two thirds of the dollars lost · the ranking score is almost equal
across sizes; the *list* is not · rank by probability alone and you reach 42 percent of churners and
25 percent of lost spend; rank by probability times spend and you reach fewer churners and 57
percent of lost spend · neither is right: it is a decision · also check the percentages by segment
(large accounts run low) · the same cut is how you check a model is not quietly failing a group of
clients · ask for every result by the segments the business cares about.
**Evidence:** → slices (by_size, by_account_manager, by_tenure, rank_by_what, overall).
**Visuals:** table (by size: churners, flagged, recall, spend lost), compare (two ways to rank), bar.
**Before:** top-K, recall, calibration.

---

## Module 5 — From drivers to decisions

### 5-1 Drivers are not causes
**Idea:** a gap between groups — or a model's weight — tells you what goes with an outcome, not what happens if you change it.
**Hook:** the slide: "advertisers with conversion tracking churn 11 points less — push tracking."
**Cover:** in this simulated world we can switch tracking on for everyone and off for everyone: the
true effect is about 2 points · the missing 9: sophisticated advertisers both install tracking and
would churn less anyway — a common cause · adjust for what the table can see and the gap shrinks to
about 6½: better, still wrong, because the real cause is not in the table · **widget `practices`**:
most gaps shrink the same way; an account manager's 10-point gap is entirely mirage · and one goes
the *wrong way*: accounts that had an optimisation review hit goal 25 points *less* often, yet the
review helps by about 9 — reviews go to accounts already in trouble; adjusting does not rescue it ·
a model's weight is the same kind of number · so: "is associated with", not "drives".
**Evidence:** → tracking_story, happy (naive, adjusted_pts, truth, share_of_naive_gap_removed_by_adjusting, review_story), bad_controls (one sentence at most, in the audit list).
**Visuals:** compare (naive vs true), widget practices, bar (the review: naive, adjusted, true).
**Before:** weights, importance. **Caveat:** we know the truth only because the world is simulated.

### 5-2 Experiments
**Idea:** randomising who gets the change is the one design that removes the hidden common cause.
**Hook:** three candidate best practices, one playbook due. What can you responsibly write?
**Cover:** flip a coin for who gets the nudge; the hidden trait lands equally on both sides ·
you often cannot force a practice, but you can randomise the *encouragement* · decide the outcome
and its window before you look · size: detecting a 5-point lift from 60 percent needs about 1,470
advertisers per group; a 2-point lift over 9,000 · reading a result: the estimate and its interval —
run the same experiment 200 times and the measured effect ranged from about 1 to 4 points around a
true 2.9; with only one month of advertisers the interval ran from almost nothing to over 5 points · do not stop early because it
looks good · evidence tiers for wording a claim: observed · adjusted · tested.
**Evidence:** → experiment (examples), uplift (many_experiments, experiment_readout).
**Visuals:** flow (randomise → treat → compare), table (sample sizes), stat (200 experiments), bullets (evidence tiers).
**Before:** intervals. **Not here:** who to target (5-4).

### 5-3 When you cannot experiment
**Idea:** compare the change in the treated group with the change in a similar group that was not treated — and check the two were moving together before.
**Hook:** the new creative-setup flow launched for ecommerce in week 13. Goal-hit rate rose 9 points. Success?
**Cover:** before versus after alone: +9, but everyone was improving that season · treated versus
comparison after launch: −1.6, but ecommerce started lower · the change in the treated group minus
the change in the comparison group: +4.7, with an interval of about 3 to 6 — the true effect is 4 ·
it rests on one assumption: without the launch the two would have moved in parallel; check it on the
weeks *before* launch · when that fails, the same arithmetic credits the launch with about 8 — and
the pre-launch drift is the warning · this is the tier between "adjusted" and "tested".
**Evidence:** → before_after (averages, three_answers, the_assumption, when_the_assumption_fails, weekly_hit_rate).
**Visuals:** line (two weekly series), table (the three answers), compare (assumption holds vs fails).
**Before:** confounding, intervals. Name the method once: difference-in-differences.

### 5-4 Uplift: who changes because you acted
**Idea:** the accounts most likely to leave are not the accounts most worth calling.
**Hook:** the team calls the 400 riskiest accounts. Nearly half were going to leave whatever anyone did.
**Cover:** four kinds of account: leaves unless called; leaves either way; stays either way; leaves
*because* you called — in this world about 3, 10, 87 and under 1 percent · the risk list is 45
percent "leaves either way"; and 47 percent of it would have stayed with no call, which is why "we
called them and many stayed" proves nothing · uplift: from a randomised outreach, fit one model on
the called and one on the not-called; the difference is who changes · calling the top 400 by
uplift prevents 44 churns against 32 by risk and about 13 at random — perfect knowledge would
prevent 136 · it needs randomised data and is noisy · a rule that encodes the mechanism can do
better still, and is tested the same way.
**Evidence:** → uplift (four_kinds_of_advertiser_share, policies_call_400, who_the_risk_list_calls, who_the_uplift_list_calls, share_of_the_risk_list_that_stayed_without_any_call, about_the_business_rule, method, caveat).
**Visuals:** table (four kinds), bar (churns prevented by policy), compare (who each list calls).
**Before:** experiments, risk lists.

### 5-5 From score to action
**Idea:** the cut-off comes from costs and capacity, applied to each advertiser's own probability — and the action must be measured.
**Hook:** the default cut-off of 0.5 flags 141 advertisers. Is that the right number to call?
**Cover:** expected value of one call = probability × chance the call works × value saved, minus the
cost · under stated toy numbers that breaks even at a probability of 10 percent — a rule about the
*next* advertiser down the list, not the list's average · **widget `ranklist`**: the rule says call
about 1,300, worth roughly three times the default 141 · this multiplies a probability by money, so
the percentages must be trustworthy (they run low here) · expected value is the general pattern:
chance it happens × what it is worth — the same two-stage idea predicts spend · a list needs
reasons attached, and different reasons need different plays · hold out a random slice of the list
so the action can be measured.
**Evidence:** → economics (assumptions, break_even_probability, the_rule, list_from_the_rule, best_list_in_hindsight, default_cutoff_half, table), regression.models (two_stage_chance_of_staying_x_average — one sentence).
**Visuals:** formula (expected value), widget ranklist, compare (default vs rule).
**Before:** calibration, uplift. The numbers are hypothetical: say so.

### 5-6 Keeping a model honest
**Idea:** the world moves after you ship; watch predicted against actual, by segment, with intervals — and know your labels arrive late.
**Hook:** June. The headline score barely moved. Gaming churn was predicted at 14 percent and came in at 31.
**Cover:** what changed is in no column — the relationship moved, not the inputs · where to look:
predicted versus actual by segment; everywhere else June matched (about 11 predicted, 11 actual) ·
use intervals: gaming in May was already 23 against 15, with only about 220 advertisers — a warning,
not proof · labels are late: churn takes 60 days to show, so watch early signals too — the inputs
(missing values, averages), the share flagged · a second trap: once the team acts on the list, saved
accounts look like the model was wrong; keep the untouched holdout · retrain on a schedule and when
the checks trip; keep the old model until the new one wins on the same test.
**Evidence:** → drift (gaming_jun, gaming_may, non_gaming_jun, auc_by_month, gaming_churn_by_month, base_rate_creep).
**Visuals:** bar (gaming churn by month), compare (gaming vs everyone else in June), bullets (what to watch).
**Before:** calibration, slices, holdouts.

---

## Module 6 — Time

### 6-1 Forecasting: start with the calendar
**Idea:** most of a forecast is trend, rhythm and known events; name them and you beat the naive methods by a wide margin.
**Hook:** finance wants next month's platform spend. The quick answer: "same as last week."
**Cover:** what is in the series: growth of about 15 percent a year; weekends about 20 percent below
weekdays; a yearly rise into late November; Black Friday week and Christmas · naive methods as
baselines: yesterday's value is off by about 14 percent a day; the same weekday last week about 6;
the average of the last four same weekdays a little better · **widget `forecast`** · a model with a
trend, a weekday effect, yearly waves and the holiday dates: under 3 percent — and it tells you what
it found · leave the holidays out and its worst month doubles: the calendar is domain knowledge.
**Evidence:** → forecast (weekday_index, month_index, growth_2025_vs_2024, backtest.methods, regression_model).
**Visuals:** widget forecast, bar (MAPE by method), table (what the model found).
**Caveat to state:** this world is stable and the model has the same shape as the world; real series do worse.

### 6-2 Backtesting and uncertainty
**Idea:** test a forecast the way it will be used — from a past date forward, many times — and give a range, not a point.
**Hook:** the model scores 3 percent when tested on randomly held-out days. Believe it?
**Cover:** shuffled testing lets a flexible model fill in days *between* days it has seen: it scores
3 percent that way and 5 the honest way · the honest way: stand on the first of each month, forecast
the next 28 days, twelve times · naive methods get worse the further out; a model of trend and
rhythm stays flat · a range from past errors: roughly ±4 percent held 78 percent of the time
against a promised 80 — and only 71 percent once incidents happen: a range covers only the kind of
days it has seen · a shift nobody announced (+12 percent in November): the long-memory model takes
four months to recover, a four-week average one · a tree model fed the raw level cannot follow a
trend: a year out it runs 9 percent low · a forecast cannot see what has never happened: give scenarios.
**Evidence:** → forecast (shuffled_folds_vs_backtest, backtest.methods[*].mape_by_week_ahead, interval, level_shift, one_year_ahead).
*(After review: cut to three ideas - the backtest, the honest range, a level shift and its fix; error by week ahead and trees-versus-trend are reference only.)*
**Visuals:** compare (shuffled vs honest), line (error by week ahead), line (level shift by month), stat (interval coverage).
**Before:** validation, intervals.

### 6-3 Anomalies: is this unusual?
**Idea:** "unusual" means far from what was expected, so first say what was expected — then the cut-off is precision and recall again.
**Hook:** the alert "spend moved more than 15 percent since yesterday" fired 89 times in nine months. It was right 6 times.
**Cover:** four in five of those alerts were Saturdays and Mondays: the rule has no idea what a
weekend is · better expectation: the same weekday over recent weeks, with a band from how much it
normally wobbles — 17 alert days, six of seven incidents; seven of its nine false alarms were
holidays · best: expect what the forecast expected — ten alert days, every incident, no false alarm,
including a five-day leak of 12 percent a day that the others missed · **widget `anomalies`** ·
tighten the band and alerts fall while misses rise: precision and recall · test a detector by
planting known incidents · the same recipe works on rows of a table: define normal, measure
distance, choose a cut-off, test with planted cases.
**Evidence:** → series_anomalies (naive_rule, seasonal_baseline.by_threshold, forecast_as_baseline, incidents).
**Visuals:** widget anomalies, table (three detectors: alerts, caught, false), bar.
**Caveat:** the forecast baseline is a best case in this stable world.

### 6-4 When, not whether: time to event
**Idea:** "how long do advertisers last?" needs a method that respects customers who have not left *yet*.
**Hook:** average lifetime of churned advertisers: 21 weeks. Typical lifetime, done properly: 43.
**Cover:** half the advertisers are still active: we know only that they lasted *at least* this long
(censored) · averaging the ones who left counts only the quick leavers · the survival curve: of
those still here at each week, what share leave — **widget `survival`**; three quarters remain at
13 weeks, about 45 percent at a year · risk falls with tenure: a quarter leave in the first 13
weeks, about one in eight per quarter after a year · the yes/no shortcut ("churned within 26 weeks")
is fine, but only for advertisers watched at least 26 weeks — it throws away a fifth of them and
counting everyone gives the wrong rate · when to use which.
**Evidence:** → time_to_event (kaplan_meier, naive_average_lifetime_of_those_who_churned_weeks, share_censored, risk_by_quarter_of_tenure, by_account_manager, the_classification_shortcut).
**Visuals:** compare (21 vs 43 weeks), widget survival, bar (risk by quarter of tenure).
**Before:** framing (outcome windows). Name the curve once: Kaplan–Meier.

---

## Module 7 — No labels, text, and the playbook

### 7-1 Clustering: segments without labels
**Idea:** clustering always returns groups; whether they mean anything is yours to check.
**Hook:** "segment our advertisers." The algorithm returns four tidy segments with churn from 4 to 35 percent.
**Cover:** k-means: a GROUP BY where the groups are not given — it places k centres and assigns each
row to the nearest · "nearest" needs a ruler: with raw columns, dollars drown everything (a
nearest-neighbour test scores 0.63 on raw columns and 0.80 once columns share a scale) · the honest
look: the four segments match grouping by two yes/no columns almost exactly; start from a different
random point and you can get a different answer; drop those two columns and you get unrelated
segments with the same churn spread; nothing in the data says four · a plain GROUP BY on size and
account manager already spreads churn from 5 to 19 percent · when it earns its place: many columns,
no obvious cut, and segments that hold up on an outcome they never saw, twice.
**Evidence:** → segments (segments, honesty_checks), distance.
**Visuals:** table (the four segments), stat (three honesty checks), compare (raw vs scaled ruler).
**Before:** GROUP BY intuition. Other methods by name only.

### 7-2 Embeddings: meaning as coordinates
**Idea:** a model can turn a piece of text into a list of numbers where similar meanings sit close together — after which text is just another table.
**Hook:** two support tickets with no words in common, about the same broken pixel.
**Cover:** an embedding: a few hundred numbers per ticket, produced by a neural network trained on
enormous amounts of text · a neural network in two sentences: stacked weighted sums with a bend
between layers, which learn their own features · near means similar: the closest tickets to a pixel
complaint are other pixel complaints · **widget `ticket_map`** · once text is numbers, everything
earlier applies: cluster them (topics fall out without labels), or train a simple model on a few
labelled examples · what it costs and what it cannot do: it captures topic far better than fine
distinctions.
**Evidence:** → tickets (nearest_example, clustering, map, learning_curve, examples).
**Visuals:** widget ticket_map, table (a ticket and its nearest neighbours), line (accuracy vs labelled tickets).
**Before:** distance, clustering, logistic regression. **Not here:** LLM classification (next).

### 7-3 Language models as classifiers
**Idea:** a language model can label text with no training at all — and must be scored exactly like any other model.
**Hook:** a few hundred tickets to sort. Five ways to do it, from an afternoon of keywords to one sentence of instructions.
**Cover:** the ladder, all scored on the same unseen test tickets: hand keyword rules · a bag-of-words
model · embeddings plus a simple model · a cheap language model given only instructions · a stronger
one — with accuracy *and* its interval, and which neighbours are a tie · where they fail: the
deliberately tangled tickets · the trade: labelled examples and effort against cost per ticket,
speed, and sending text out of the building · score it like any model: a labelled test set it has
not seen, per-category precision and recall, an interval · two models disagreeing is a cheap flag
for human review · the ceiling: if two people disagree on the label, no model can beat that.
**Evidence:** → tickets (methods, paired, two_llms, honest_limits, llm_misses, n_test, n_test_hard).
**Visuals:** bar (accuracy by method), table (ordinary vs hard tickets), table (paired comparisons).
**Caveat to state:** synthetic tickets, same model family wrote and judged them — real inboxes score lower.

### 7-4 The report you can stand behind
**Idea:** a report is trustworthy when every number can be traced, every claim matches its evidence tier, and the limits are on the first page.
**Hook:** two reports on the same model. One is prettier. Only one can survive a question.
**Cover:** numbers in the text come from the computed results, never typed — a regenerated chart and a
stale sentence is the classic failure · every comparison states its group size and interval · the
baseline sits next to the model · wording matches evidence: observed, adjusted, tested · results by
segment, not only overall · a provenance line: data pulled when, which rows were in, which model
version · the first paragraph says what the reader should *not* conclude · assistants write
confident stories around noisy bars: read the prose as critically as the code.
**Evidence:** reuse earlier facts only as examples (→ baseline, uncertainty, slices). No new numbers.
**Visuals:** compare (weak sentence vs strong sentence), bullets (the six things a report must show), table (claim → tier → wording).
**Before:** everything.

### 7-5 Choosing an approach: the playbook
**Idea:** the fundamentals fit on one page: the question picks the kind of problem, the decision picks the measure, and the cheapest method that clears the bar wins.
**Hook:** a question you have not met in this course lands on Monday. What do you do in the first ten minutes?
**Cover:** the path — what decision does it feed · what kind of problem · what is one row, the target,
the timeline · what is the baseline · how will we know it worked, and on which rows · simplest model
first, complexity only if it beats the noise · who does it fail · is this prediction or a claim about
cause · how will it be used and watched · when *not* to use ML: a rule or a report already answers
it, too few examples, nobody will act on the output · using it responsibly: columns that stand in
for something you should not decide on, client data and outside tools, models that change the data
they learn from · where next, by name: recommendation, deeper causal methods, deep learning.
**Evidence:** none new.
**Visuals:** flow (the path), table (question → kind → first baseline), bullets (when not to).
**Before:** everything. This is the recap of the whole course: no new concepts.
