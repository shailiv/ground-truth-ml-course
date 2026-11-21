# Standing instructions for my AI coding assistant

I am a data analyst. When I ask you for modelling or analysis work, follow this file.

## How we work
1. Work in stages and stop at each gate for me to check: (1) the table, (2) the target and the split, (3) baseline then model, (4) the report.
2. Every output carries an audit block: row counts and distinct entities after every step; date ranges; the label rate; every feature with its source table and the latest date of data it used; the baseline beside the model; training and test scores side by side; group sizes and intervals beside every comparison.
3. Numbers in any report text are produced from the computed results, never typed. State what the reader should not conclude.
4. Say which claims are observed, adjusted or tested. Do not write causal language over an association.
5. If a result looks too good, say so yourself and show the result without the strongest column.
6. Never drop rows, fill missing values or join tables silently: report what changed.

## The path for any new question

1. What decision does this feed, and who will act on it?
2. What kind of problem is it: a category, a number, groups, something unusual, a series, a cause, text?
3. What is one row, what is the target, and what is the timeline (snapshot, what is known before, what happens after)?
4. What is the baseline: the rule or the naive answer you would use today?
5. How will we know it worked, on which rows, with which measure, and how wide is the noise?
6. Simplest model first. Add complexity only if it beats the simple one by more than the noise.
7. Who is it wrong about? Cut the result by the segments the business cares about.
8. Is this a prediction, or a claim about cause? If cause: observed, adjusted or tested?
9. How will it be used, measured and watched once it ships?

# Reference: the brief and the checks for each kind of question

Complete from day one: it covers every lesson of the course, including ones I may not have studied yet.
Version 2026-11-22, from the Ground Truth course.

## Module 1: Thinking in ML

### From rules to learned models

Brief:

Before building anything, describe the table you would train on to answer this: [the question, in one sentence]. In one sentence, say what one row is, and give the row count and the number of distinct [units, such as advertisers, leads or creatives]. Name the label column, the outcome to be predicted, and write its exact definition in plain words. List every feature column with a one-line description; the label must not be in that list. Show five example rows including the label, with at least one row for [each outcome]. Do not train a model yet: stop and wait for my go-ahead.

The output must show:

- A one-sentence statement of what one row is, with the row count and the number of distinct units
- The label column, named, with its definition in plain words
- The full feature list, one line each, and the label is not in it
- Example rows, label included, that you can check against accounts you know

### Which kind of problem is this?

Brief:

My request: [the question, in the stakeholder's words]. It feeds this decision: [who will do what differently with the answer]. Before writing any code, restate it. Say what kind of problem you think it is and why, and whether I am asking to predict something or to change it. Name the answer column and how many past rows have it filled in, or say plainly that there is none. Propose the simplest approach that could answer it (a report, a rule or a simple model) and describe what it would hand back. List any other reasonable framings, then stop and wait for my go-ahead.

The output must show:

- The kind of problem in plain words, with a reason; a question about changing something is not restated as a prediction
- The answer column by name, with how many past rows have it filled in, or an explicit statement that there is none
- The decision the output feeds, in one sentence that matches the one you gave
- The lowest rung of the ladder that could answer it, proposed first, with what it would hand back

### Framing: target, unit and time

Brief:

Before any modelling, write the label definition in one sentence: [outcome] within [number of days] of [reference date]. Say what one row is, [unit] at [snapshot date], and which rows are eligible. List the snapshot dates beside the date the data was pulled, and keep only snapshots whose [outcome window] had fully closed by then; say which you dropped. Show the row count and [outcome] rate by snapshot [period], how many rows were excluded and why, and how you treated rows whose outcome was not yet decided. Then show twenty example rows with the outcome and twenty without.

The output must show:

- The label in one sentence, with its window in days
- Snapshot dates beside the data pull date: every snapshot kept is at least one full outcome window older than the pull
- Label rate and row count by month, with no unexplained jump or drop in the newest months
- Rows excluded as not eligible or not measurable: how many, and how they differ

### Leakage: features that know the future

Brief:

Build every feature from dated event tables, such as [event tables], filtered to dates on or before each row's [prediction date]. From a table that only shows the present, such as [current-state table], use only fields the outcome cannot change, such as [stable fields], and flag each one; any other field needs a copy dated at the [prediction date]. In the output, list each feature with its source table and the latest date of data it used, next to the [prediction date]. After fitting, list the five columns the model relies on most and when each value is recorded. If a column cannot be computed as of that date, leave it out and tell me which.

The output must show:

- A list of every feature with its source table and the latest date of data it used: none later than the snapshot date
- Every field taken from a current-state table, each marked 'outcome cannot change it' (vertical, sign-up date) or 'copy dated at the snapshot' (status, tier, last-activity dates)
- The columns the model relies on most, each with when its value is recorded
- For any suspect column: the result with and without it, on the same advertisers

### Brief in stages, audit by evidence

Brief:

Work in four stages: (1) the table, (2) the [outcome] definition and the held-back rows, (3) a baseline, then the model, on those rows, (4) the report. One stage per reply, then stop and wait for my go-ahead. End every reply with an audit block that grows by stage: from stage one, row counts after every step and the date range; from stage two, the [outcome] rate overall and by [period]; from stage three, each feature's source table and latest date, and the baseline beside the model. In stage four, quote every number from those blocks. Start with stage one for [table]: what one row is, rows and distinct [units], dates covered, duplicates, missing values.

The output must show:

- From stage one: row counts after every step and the date range, with any drop or growth explained
- From stage two: the label rate, overall and by month
- From stage three: every feature with its source table and the latest date of data it used, and the baseline beside the model on the same held-back rows
- In the report: every number in a sentence matches the audit block of the latest run, and both carry the same run date


## Module 2: The scoreboard

### Hold-out, the gap, and baselines

Brief:

Split by [date column], not at random. Train only on periods whose [outcome window] had closed before the first test date, test on [the latest periods], and say which period you left out and why. Make every modelling choice on the training periods. Score the test rows once, as a final stage I trigger, and list every evaluation run with the rows it used. On the test rows, put two baselines beside the model: predicting [the most common outcome] for everyone, and my rule [rule]. For each, show rows flagged and how many of those really had [outcome], with the model also shown at my rule's number of flags. Print rows and [outcome] rate for train, left-out and test.

The output must show:

- A split table: which periods train, which are left out and which test, with first and last date, rows and outcome rate for each
- The gap, in dates: the last training period's outcome window ends before the first test date
- Test scoring is its own final stage that you trigger, and the output lists every evaluation run with the rows it used
- Both baselines beside the model on the same test rows: how many flagged and how many of those really had the outcome, with the model also shown at the rule's number of flags

### Accuracy lies: precision and recall

Brief:

For [model], report results on [the test period] only, at a stated cut-off of [cut-off]. Show the four counts (flagged and had [outcome], flagged and did not, had [outcome] but not flagged, neither) with precision and recall, and put the same figures for 'predict [the common outcome] for everyone' and for my rule [rule] in the same table. Print the test row count and the [outcome] rate beside them, so I can check that the counts add up. Do not rebalance or resample the test rows. If you reweighted or resampled the training rows, say so and show the average predicted rate beside the actual rate. Do not lead with accuracy.

The output must show:

- The four counts are shown and add up to the test row count (4,000 here).
- Churners caught plus churners missed equals the churner total from the audit block (527 here).
- Precision and recall are stated with their cut-off, beside the same figures for both baselines.
- The churn rate in the test rows matches the real rate (about 13 percent): nothing was rebalanced.

### Scores, cut-offs and ranked lists

Brief:

Output a score for every test row, not a yes or no. Show a table of number flagged, precision and recall at [several cut-offs across the range]. Show the top [list sizes my team could handle] by score, with the number of real [outcome] cases on each list and the number a random list of that size would hold. Compare the model with my rule [rule] at the rule's own list size, on the same test rows. Report AUC on [the test period] beside these tables, not instead of them, and print the test row count and [outcome] rate.

The output must show:

- Every precision or recall figure names the cut-off or list size it belongs to.
- The model and the baseline are compared at the same number flagged.
- Each top-K row shows what a random list of that size would hold.
- AUC is stated for the test months and sits beside the top-of-list numbers, not in place of them.

### Can you trust the percentage?

Brief:

On [the test rows: a period or holdout the model never trained on] only, group rows by predicted probability into [8 to 10] score buckets. For each bucket print the number of rows, the average prediction and the actual [outcome] rate, and add one line with the overall average prediction beside the overall actual rate. State how many rows the table covers and which [period] they come from. Repeat the table for [the two or three segments the business cares about]. Do not adjust the scores yet. If I later ask for recalibration, say which rows it was fitted on and show this table again on rows it did not use.

The output must show:

- The table is built on test rows: the bucket counts add up to the test row count (4,000 here), not the training count (6,000).
- Every bucket shows its row count, and the overall average prediction sits beside the overall actual rate (10.9% against 13.2% here).
- The same table appears for each segment the business cares about.
- After any recalibration: the output names the rows the adjustment was fitted on, and the table is shown again on rows it did not use.

### Judging number predictions

Brief:

Predict [the number] for each [unit], training on [training period] and scoring only on [test rows the model never saw]. In one table, on the same rows, show [the simplest baseline, such as same as last period], [a sharper baseline if there is one] and each model, with MAE, RMSE and predicted total versus actual total, and state the row count. Add MAE by [size tier or segment] and list the [10] largest misses with predicted and actual values. State how many test rows have an actual value of zero and how many rows any percentage error was computed on; if I need a percentage, use total absolute error divided by total actual.

The output must show:

- Both baselines and every model scored on the same test rows, with the row count stated
- MAE, RMSE and predicted total versus actual total side by side
- Error by size tier and a list of the largest individual misses
- The count of rows with zero actual spend, and the row count behind any percentage error: if it is smaller than the test set, rows were dropped

### Real or noise?

Brief:

For every comparison in this analysis, between [groups, periods or models], show the number of [units] behind each figure and the difference with a 95% interval, and say in one line how the interval was computed. For model comparisons, bootstrap the difference on the same [test rows]. List every cut you examined with its group size and interval, not only the one you report. Do not call a change a rise or a fall unless its interval excludes zero; when zero is inside, write 'cannot tell'. Beside each headline gap, show the same metric for [the last 6 to 12 periods] so I can see how much it normally moves.

The output must show:

- The number of advertisers beside every rate
- A 95% interval beside every difference, with the method named
- Wording that matches the interval: no 'rose' or 'beats' while zero is inside it
- Every cut that was examined is listed with its group size and interval, not only the biggest mover


## Module 3: Core models, and reading the work

### Linear regression: predicting a number

Brief:

Predict [numeric outcome] with a linear regression fitted two ways: on the raw values, and on the log of [outcome] with [skewed size columns] logged too. Give both models [my baseline rule] as a column. Train on [training period], score on [test period], and show [baseline] beside both: MAE, RMSE, predicted total versus actual total, and a bootstrap interval on each MAE gap. State the rows fitted and the rows scored for each model, and what happened to rows where [outcome] is zero. For the log model, say how you converted back to [units], and show the total with and without the correction to averages. Print the weights with their units.

The output must show:

- The weights table shows its units: dollars per unit for the raw fit, percent per unit for the log fit
- Row counts for every model: rows fitted, rows scored, and how many zero-outcome rows there were and what was done with them
- Predicted total beside actual total, with and without the correction to averages, and the row count each total covers
- The baseline in the same table on the same test rows, with an interval on each gap

### Logistic regression: predicting yes or no

Brief:

Fit a logistic regression for [yes/no outcome] on [training period] only, with continuous columns standardised and yes/no flags left as 0 or 1, and score [test period]. Show a weights table with each column's unit (per standard deviation, or yes versus no), its odds ratio, and the average shift in predicted probability in points. Report AUC on the training rows and on the test rows side by side, with row counts, and how many [positives] the model finds at the same list size as [my current rule or baseline]. Describe weights as associations; do not write that any column drives or reduces [outcome].

The output must show:

- Every weight states its unit (per standard deviation, or yes versus no) and its average shift in probability points, not only an odds ratio.
- AUC on training rows and on test rows sit side by side with their row counts, and are close.
- The current rule or baseline is scored on the same test rows at the same list size, beside the model.
- The summary says 'is associated with', never 'drives', 'causes' or 'reduces'.

### Decision trees

Brief:

Fit a decision tree for [yes/no outcome] on [training period] only, with a maximum depth of [small depth, such as 3] and at least [minimum rows] rows in every leaf, and print it as rules. For every leaf show the rule, the number of training rows and their [outcome] rate. Report AUC on the training rows and on [test period], with row counts, next to [my simpler model or rule] scored on the same test rows. List every column used and when each is recorded; use no ID column and nothing recorded after [prediction date].

The output must show:

- Every leaf shows its row count and its rate, and no leaf is smaller than the minimum you set.
- The printed rules name each question's column, and the column list shows when each is recorded: nothing after the prediction date, and no ID.
- AUC on training rows and on test rows with their row counts, and the simpler model scored on the same test rows beside it.

### Dirty tables

Brief:

Before any modelling, build the table step by step. After each step print the number of rows, the number of distinct [unit ID] and the [outcome] rate, and flag any step where a count changes. Do not drop rows because a feature is missing, and do not fill anything yet: report missing values per column and add a yes/no flag column for each feature that has any. Fill values come later, computed from the training rows only. Never fill a missing [outcome]: list those rows separately. Start from [main table], join with left joins, and aggregate any table with several rows per [unit] to one row per [unit] before joining. Leave ID columns out of the feature list.

The output must show:

- A step table: rows, distinct advertisers and churn rate after every step, with rows equal to advertisers throughout.
- Missing values per column, and what was done with each: no row dropped for a missing feature, a flag column for each, no outcome value filled in.
- The final churn rate matches a number you already trust, such as the dashboard.
- The feature list contains no ID column.

### Reading the assistant's script

Brief:

Write the modelling script in six labelled parts: load, choose, split, prepare, fit, score. Open it with a header comment stating what one row is and the row count, the definition of [outcome], the named feature list with confirmation that each column is known at [prediction date], which [periods] train and which test, and that all preparation is inside the pipeline. Print the row counts for training and test, then the score from predict_proba on each, labelled with its rows, beside [baseline] on the same test rows. Do not wrap data steps in try/except: let errors stop the script. Finally, list which line numbers belong to each of the six parts.

The output must show:

- Printed row counts for training and test, and two scores, each labelled with its rows, beside a baseline on the same test rows.
- Training and test rows defined by named periods in the split line, not by a random split.
- Scores with many distinct values between 0 and 1, not a column of zeros and ones.
- A header that states one row, the label, the named features, the split and where preparation happens, and a line in the script that matches each statement.


## Module 4: Stronger models, honestly validated

### Overfitting: memorising versus learning

Brief:

For every model you fit, report the score on the training rows and on held-out rows side by side, in [measure], each labelled with its rows and row count. For [model], also fit it at [several values of its complexity setting, from simplest to most flexible] and give me a table of the training score beside the cross-validated score, with folds made inside the training rows only (or scored on [a validation period I name]), plus [a size check, such as number of leaves and smallest leaf]. Keep the test rows out of that table: they are scored once, later, after a setting is fixed. Never quote a score without saying which rows it was measured on.

The output must show:

- Training and held-out scores side by side for every model, in the same measure, each labelled with its rows and row count
- The table of scores by setting shows training beside cross-validated or validation-period scores, and has no test-row column
- For a tree: the number of leaves and the size of the smallest leaf; a churn rate from about 100 advertisers is only good to about 6 points either way
- The headline number in the summary is a held-out score, named as such, and it matches the table

### Validation without cheating

Brief:

Choose every setting by cross-validation on the training rows only. Case one, one row per [unit] from [periods] that are alike: rotating shuffled folds are fine. Case two, several rows per [unit] or [periods] that differ: keep all rows of one [unit] in the same fold, make each fold check on later [periods] than it trains on, say how many such checks the data allows, and print how many [units] sit on both sides of any fold. Tell me which case applied and why. Remove ID columns. Report every fold score per candidate, with mean and range. Then stop: score [test period] only when I approve the frozen setting, and list every scoring run with the rows it used.

The output must show:

- How the folds were made (by advertiser, by time, or shuffled) and why that case applies, with the count of advertisers on both sides of any fold: 0
- Every fold score for each candidate setting, with mean and range, not only the winner's mean
- Test scoring is its own final stage that you trigger, and the output lists every scoring run with the rows it used: the test rows appear once
- The feature list, with no ID column in it

### Forests and boosting

Brief:

Fit two models on the same training rows and score both on the same held-out rows: a simple one ([logistic or linear regression]) and a gradient-boosted one. Choose the boosted model's tree depth, number of rounds and step size (learning rate) by cross-validation on the training rows only; print every combination tried with its score. For each model print training score, test [metric], test row count and [outcome] cases in the top [list size]. Print the difference in test [metric] with a 95% interval from resampling the same test rows (a paired bootstrap), and the difference in top-list counts with its interval. If the gap is small, refit from [several] seeds and print the range.

The output must show:

- One table with the baseline, the simple model and the boosted model, each beside the number of test rows it was scored on; the counts match
- Training score beside test score for each; a boosted model near 1.0 in training has probably not been tuned
- The tuning table: every combination of settings tried, its cross-validation score on training rows, and the depth that won
- An interval on the difference itself, not two separate intervals, and the same difference as a count in the top-K list

### Features: where your knowledge goes in

Brief:

Build the feature table in SQL from dated event tables: one row per [unit] per [snapshot date], every aggregate limited to the [window length] before the snapshot and strictly before it. Print a feature list: each column, its source table, its date window and whether it will exist on scoring day; flag any column read from a current-state table. Print rows and distinct [units] before and after each join. Then fit the same [simple model] with the column groups added one at a time and each group alone, and print [metric] for each on the same [test period]. Add a learning curve: [metric] for growing samples of training rows, with the count of [outcome] cases at each size.

The output must show:

- A feature list: every column with its source table, its date window and when its value is known; current-state sources are flagged, and no flagged column is among the big movers
- Row count and distinct advertisers equal to the snapshot table, before and after the feature joins
- Test AUC with column groups added cumulatively and each group alone, on the same test months
- A learning curve: the score at growing numbers of training rows, with the count of positives at each size

### Opening the black box

Brief:

For [model], produce three exhibits, and state on each the model and the rows used. One: permutation importance on [held-out rows] for each column and for each group of related columns ([groups]), as the drop in [metric]. Two: a partial dependence curve for [columns the business asks about]. Three: for each of the top [list size] rows, the three largest per-row contributions (coefficient times distance from the training mean for a linear model, SHAP values otherwise), with the row's value and the training mean beside each, plus the base value, so that base plus all contributions reproduces the row's score. Caption every exhibit as a description of the model; no causal wording such as drives or impact.

The output must show:

- The importance table names its rows (held-out, with the row count) and shows single-column and grouped drops side by side
- Each dependence curve names the model that drew it and is captioned as the model's behaviour
- Per-row reasons show the row's value, the training average and the contribution; base value plus all contributions reproduces the printed score
- A search of the text for drives, causes and impact finds none attached to a column

### Who is the model wrong about?

Brief:

Take [model]'s scores on [held-out rows] and the top [list size] list. Recompute every headline result by [segments the business cares about]: for each slice print the rows, the [outcome] cases, the places on the list, the share of its [outcome] cases caught, [ranking metric] within the slice, and predicted against actual [outcome] rate. Show that the slice counts add up to the totals. Then build the list a second way, ranked by probability times [value at stake], and print for both lists the [outcome] cases reached, the [value] reached and how many names they share. Do not recommend a ranking; lay out the trade.

The output must show:

- Every headline number repeated by segment, with the count of advertisers and churners in each; the segment counts add up to the totals
- Per segment: places on the list, share of churners caught, and AUC within the segment
- Predicted churn beside actual churn for each segment
- The list built both ways, by probability and by probability × spend, with churners and dollars reached


## Module 5: From drivers to decisions

### Drivers are not causes

Brief:

For each practice in [list of practices], compare [units] that have it with those that do not on [outcome] over [window]. Show both group sizes, both rates, the raw gap with a 95 percent interval, and the gap after adjusting for [columns fixed before the practice was adopted]; list exactly what you adjusted for, and adjust for nothing the practice itself could change. Beside each gap print, word for word, the line I supply on how [units] come to have that practice: [practice: chosen by them / assigned by us / triggered by poor performance]. Do not infer that from the data. Describe every result as an association; do not write 'drives', 'impact' or 'lift'.

The output must show:

- Group sizes and an interval beside every gap
- The list of columns adjusted for, with nothing on it that the practice itself changes (CPA, spend trend): controlling for the route a practice works through removes the very effect you are measuring
- Beside each gap, the line you supplied on who gets or chooses the practice, printed word for word, and no guess about assignment that the assistant inferred from the table
- The wording says 'associated with'; 'drives', 'causes' and 'impact' appear only where a change was actually tested

### Experiments

Brief:

Design first; do not analyse anything yet. We want to test whether [change or encouragement] raises [outcome] over [window]. Propose the unit to randomise ([advertiser / account / user]), the group size needed to detect a lift of [smallest lift worth acting on] from today's [baseline rate], and your assumptions. If the change cannot be withheld, propose a random holdout or a rollout in random order instead. When results arrive, compare by assignment (everyone assigned against everyone not, whatever they did next) and report: counts per group, a table showing the groups were alike beforehand, the share who took the change up, the estimate with its 95 percent interval, and every date on which results were computed.

The output must show:

- A plan dated before launch: outcome, window, group size, and the smallest lift that size can detect
- Counts assigned to each group, and a before-the-change table showing the two groups were alike
- The result table compares everyone assigned with everyone not assigned, its counts match the assigned counts, and the share who took the practice up is a separate line
- One estimate with its interval, on the planned group sizes, beside a list of every date the results were computed: one date, no early stop

### When you cannot experiment

Brief:

[Change] launched for [treated group] on [launch date] and for nobody else. Estimate its effect on [outcome] as a difference-in-differences: the treated group's change from before to after, minus the change in [comparison group] over the same periods. Show the [weekly] rate for both groups across all periods, the four averages (each group, before and after) with counts, the estimate with a 95 percent interval, and how fast the gap between the groups was drifting before launch, with its margin. Other changes around the launch that I know of: [list, or 'none known']. Print that list back, and report any break at launch in either group's size or mix that the data shows; do not guess at causes.

The output must show:

- The weekly series for both groups, before and after launch, not just two averages
- The four averages (each group, before and after) with group sizes, and the estimate with its interval
- The pre-launch check: how fast the gap was drifting per week, with its margin, and whether that is distinguishable from zero (a borderline result is a warning, not a pass)
- The other changes around launch that you listed, printed back, and each group's size and mix on either side of the launch date, so a break would show

### Uplift: who changes because you acted

Brief:

We ran [action] with [units] assigned to it at random; the assignment is in [assignment column]. Fit one [outcome] model on the treated group and one on the untreated group, using only features known at [decision date], and rank held-out [units] by predicted [outcome] without the action minus predicted [outcome] with it. For the top [list size] by that uplift, the top [list size] by plain risk and a random [list size], show [outcome] among treated versus untreated inside each list, with group sizes and 95 percent intervals. Start the output with the size of each group, a table showing the two groups were alike before the action, and the overall effect with its interval.

The output must show:

- The size of the called and not-called groups, with a table showing they were alike before the calls: a coin flip leaves them alike, hand-picking does not
- The overall effect of the call, with its interval
- On held-out advertisers: called versus not-called churn inside the top of the uplift list, the risk list and a random list
- The group size and an interval beside every one of those gaps

### From score to action

Brief:

Using the [outcome] scores on [evaluation period], compute the net value of acting on the top N [units] for every N, assuming [cost per action], [value of a success] and [share of cases where the action works]. State the break-even probability these imply and apply it to each [unit]'s own probability, not to the list's average hit rate. Show predicted versus actual around the break-even, and mark the default cut-off and our capacity of [capacity] on the curve. Then draw a random holdout of [size] that nobody acts on: show how it was drawn, its average score beside the rest, and the size needed to detect a gap of [smallest gap worth acting on].

The output must show:

- The three assumptions in dollars, and the break-even probability they imply
- Predicted versus actual churn for the score bands around the cut-off
- Net value by list size, with the default 0.5 cut-off and the team's capacity marked
- The holdout: how many names, how it was drawn, and its average score beside the called names'; once outcomes arrive, the called-versus-holdout gap with its interval

### Keeping a model honest

Brief:

Build a monitoring table for [model], one block per [period]. For each [period] whose [outcome window] has closed, show predicted and actual [outcome] rates overall and by [segments the business cares about], with the number of [units] and a 95 percent margin on each actual rate; where [the action] has been taken, use only the untouched holdout and label those rows. For the newest [period], which has no labels yet, show the missing-value rate and mean of every input column and the share of [units] above [working cut-off], next to the same figures for the training period. Flag every segment whose predicted rate falls outside the margin, and state which [period] each row describes.

The output must show:

- Predicted and actual rates by segment, each with its group size and margin
- The month behind every row, so a two-month-old result is not read as current
- Input and score checks for the newest month, beside the training-month values
- A label on every row saying where its actuals come from (the untouched holdout, or accounts the team acted on), with that row's count


## Module 6: Time

### Forecasting: start with the calendar

Brief:

Forecast [series] for each [day or week] of the next [horizon]. Start with two naive baselines: the same [weekday] one [week] back, and the average of the last [four] of them. Then fit a regression on the log of [series] with a trend, [weekday] effects, time-of-year terms and a flag for each event date in this list: [event dates]. Score every method on the same forecasts: [horizon] ahead from each of the last [twelve] [month starts], each trained only on data before its forecast date. Show, per method, the average error and the worst [month]; list the event dates you used and each forecast's last training date; and report the fitted effects in percent.

The output must show:

- Baselines and model are scored side by side on the same forecast dates
- Each forecast shows its last training day, and that day is before the days it predicts
- The worst month is reported next to the average
- The event dates used are listed, and the fitted trend and weekend effects match your dashboards

### Backtesting and uncertainty

Brief:

Backtest this forecast of [series]: from each of the last [twelve] [month starts], train only on data before that date and forecast the next [horizon]. For each backtest print the forecast date and the last training date. Report the average percentage error by [month] and by [week ahead], for the model and for two naive methods. Build an [80] percent range for [the number I need: one day, or the total over the horizon] from backtest errors of that same kind, using the earlier backtests, and report how often it held on the later ones. If I name a break date, add a step from that date and re-run the backtest: [break date, or none].

The output must show:

- Every backtest lists its forecast date and its last training day, and the training day is always earlier
- Errors are shown by month and by week ahead, beside the naive methods
- The range names what it covers, a day or a total, was built from errors of that same kind, and shows how often it held on backtests it was not built from
- If you named a break date: the fitted size of the step is printed, and the error by month is shown before and after adding it

### Anomalies: is this unusual?

Brief:

Build an anomaly alert for [metric] by [day]. Compare each [day] with an expectation that knows the calendar: [the median of the same weekday over the last few weeks, or a forecast]. Alert when the gap exceeds [k] times its typical size over recent weeks, and say how you measured that typical size. Test it by injecting incidents of several sizes and lengths, including a slow multi-day one, into a copy of the history, and list them. For [three] band settings report alert days, incidents caught, incident days flagged and false-alarm days, and list the dates of the false alarms.

The output must show:

- A table of sample days shows actual, expected and the gap; the expectation is not simply yesterday's value, and the output says how the normal variation behind the band was measured
- Alert days, incidents caught and false-alarm days are reported separately, for more than one band setting
- The planted incidents are listed with their size and length, including a slow one
- The false-alarm dates are listed, so you can see whether they are holidays or other known events

### When, not whether: time to event

Brief:

Estimate how long [customers] last with a survival curve (Kaplan–Meier), not an average over those who have already [left]. Treat everyone still [active] as censored at their tenure so far. Report how many went in, how many are still [active], the share still [active] at [four or five tenure points] with the number still being watched at each, and the median lifetime. Add the risk of [leaving] per [block of tenure], and the curve split by [join period]. For any '[event] within [N weeks]' rate, use only those who started at least [N weeks] ago and print how many you left out.

The output must show:

- The counts add up: everyone in = already churned + still active, and the curve's first point starts from everyone
- Each point on the curve shows how many advertisers were still being watched
- The median lifetime is the week where the plotted curve crosses one half, and curves by join period show whether recent joiners differ
- Any fixed-window churn rate prints how many advertisers were left out because their window had not closed


## Module 7: No labels, text, and the playbook

### Clustering: segments without labels

Brief:

Cluster [the rows: one per what] with k-means on [the columns I list], each put on a common scale, with no outcome column among the inputs. Show the error for [a range of k], and for [the k I pick] a profile table: each segment's size, the average of every input column, and [an outcome the method never saw]. Re-run from [several] different random seeds and report an agreement score (adjusted Rand index) between each run and the first. Repeat on [a second period] and say which segments return. Beside the segments, show the same outcome for a plain GROUP BY on [two or three columns I already use]. Do not name the segments.

The output must show:

- The input columns and how each was scaled are listed, and no outcome column is among them.
- A profile table per segment shows its size and the average of every input, so a segment that is one column in disguise is visible.
- An agreement score is printed for each re-run from a different random start (the same segments coming back score close to 1), not one run with a fixed seed.
- The same unseen outcome is shown for the segments and for a plain GROUP BY side by side, with the error for each k tried.

### Embeddings: meaning as coordinates

Brief:

Before sending anything, tell me which embedding model you would use, whether it is hosted or runs on [our own machines], where [the text] would go and what [that many texts] will cost; wait for my go-ahead. Then embed [the text column] and report the number of columns per text. Show [the items I name], each with its [N] nearest neighbours and similarity scores. Train logistic regression on the embeddings using [a few] labelled examples per [category], score it on labelled examples it never saw, and report accuracy at several training sizes with the range over repeated random draws, beside [guessing or the commonest category]. Split the final accuracy by [easy and hard cases].

The output must show:

- The embedding model is named before any text is sent: hosted or run in-house, where the text goes, the quoted cost, and the number of columns per text.
- Nearest neighbours are printed, with similarity scores, for items you chose, so you can read whether near means similar.
- The counts of labelled examples used for training and for testing are printed, with none in both, and the guessing baseline sits beside the accuracy.
- Accuracy is shown at several training sizes with the range over repeated draws, and the final figure is split by easy and hard cases.

### Language models as classifiers

Brief:

Classify [the text] into [our categories, one line describing each] with an approved language model given instructions only. Before sending any text, show me the exact instructions, the model name and version, and where the text will go, and wait for my go-ahead. Score it on [the test set people labelled, which no method has seen], beside [the simpler methods] and [guessing or the commonest category], each with a 95 percent interval, plus an interval on the gap between neighbouring methods on the same items. Report precision and recall per category, and accuracy on [easy and hard cases] separately. Never adjust the instructions after seeing test items; list every version you tried and on which items.

The output must show:

- The test set is described: how many items, who labelled them (people, blind to every model's answer), and a list of every version of the instructions with the items it was tried on, none of them test items.
- One table holds every method on the same items: the number scored, the guessing baseline, an interval on each score and on each gap between neighbours.
- Precision and recall are shown per category, and accuracy for easy and hard cases separately.
- The exact instructions, the model name and version, and where the text goes are printed, and were shown before any text was sent.

### The report you can stand behind

Brief:

For every report you draft for me: build it only from [the results file we checked in earlier stages]. Insert every number in the text from that file by code, and append a table matching each number in the prose to its source. Beside every comparison print both group sizes and a 95 percent interval. Put [the baseline] next to the model on the same unseen rows at the same list size, and break headline results out by [segments]. Tag each finding observed, adjusted, compared with an untreated group, or tested; use causal verbs only for tested ones. Open with a provenance line ([pull date, rows in and out, model version]) and what the report does not show.

The output must show:

- A source table at the end: every number in the prose matched to the computed result it was read from, with none missing
- Both group sizes and an interval beside every comparison, and the baseline beside every model result, on the same unseen rows and at the same list size
- Every finding tagged observed, adjusted, compared with an untreated group, or tested; no causal verb on an untested one, and each compared one states its assumption
- A first page that opens with the provenance line (pull date, rows in and out, model version) and what not to conclude, with headline results broken out by segment

### Choosing an approach: the playbook

Brief:

Before any code, draft a one-page plan for [the question as asked]. State the decision it feeds and who acts, on [how many cases, how often]. Name the kind of problem, one other framing you considered, and whether it predicts or claims a cause. Define one row, the target with its [outcome window], and when each feature is known. Fix the simplest baseline ([today's rule or report]), the measure that matches the decision, and exactly which rows are held out. Say which [segments] results will be cut by and which random slice stays untouched. End with the result at which we stop at the baseline, and any column standing in for [something we must not decide on].

The output must show:

- Frame: the decision with who acts and on how many cases; the kind of problem with one other framing considered; one row, the target and the timeline, a sentence each
- Score: the baseline, the measure tied to the decision and the exact held-out rows are written in the plan before any model is fitted, and every later result repeats them unchanged
- Trust: the segments every result will be cut by, a line saying prediction or claim about cause, and the random slice nobody acts on
- Stop: the result, as a number, at which the baseline rule or report is enough, with any column that could stand in for something we must not decide on
