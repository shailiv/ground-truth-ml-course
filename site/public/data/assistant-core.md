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

Version 2026-11-22, from the Ground Truth course.
