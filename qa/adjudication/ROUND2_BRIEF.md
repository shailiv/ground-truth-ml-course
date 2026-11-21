# Round 2 brief: last corrections, and the textbook names

You are the final editor for a set of lessons in **Ground Truth: machine-learning fundamentals for a working
analyst**. The lessons were written, reviewed by seven readers, corrected by a first round of editors, and then
fact-checked again by a Gemini model against the results file. Two jobs remain for your lessons.

Work in `~/ml-course` (bash: `~/ml-course`). Edit only your assigned `content/lessons/<id>.json` files
and write one record per lesson. Plain Python only (no Node, no browsers): the machine is short on memory.

## Read first
1. `content/SPEC.md` (the learner, the voice, the rules) and `qa/adjudication/FIXER_BRIEF.md` (the course-wide rulings
   R1-R9 the first round applied - they still bind you; do not undo them).
2. `data/facts.json` - all of it; the only source of truth for numbers.
3. Your lessons, `content/lessons/<id>.json`, and for each one `qa/factcheck/final/<id>.json` (the re-check's
   findings; `issues` may be empty; a missing file means the re-check has not reported - skip job A for that lesson
   and say so).

## Job A - the re-check's findings
For every issue in `qa/factcheck/final/<id>.json`: verify it yourself against facts.json or the principle, then
accept (fix it), partly accept, or reject with the reason. These are mostly small. Fix every one that is right,
including the low-severity ones when the fix is cheap. Prefer fixes that do not touch narration (a card, a note,
a glossary line, a question) because narration is already recorded; when a spoken sentence is wrong or misleading,
fix the sentence.

## Job B - the textbook names
The learner asked: lesson titles are in plain words, and that is fine, but they want to pick up the standard
technical vocabulary along the way so they can read documentation, talk to data scientists and brief an assistant
in its own terms. The lessons already speak and define most of it. These terms are still missing. Add each one in
the lesson named, where the idea is ALREADY taught - you are naming something the learner has just understood, not
adding a topic:

| Term | Lesson | The idea it names there |
|---|---|---|
| supervised learning, unsupervised learning (and one clause: reinforcement learning is a third family this course does not cover) | 1-2 | "is there an answer column for past cases?" - with one: supervised (classification, regression); without: unsupervised (clustering, anomaly detection) |
| generalisation / to generalise | 2-1 | holding up on rows the model never saw |
| class imbalance; F1 score | 2-2 | a rare outcome; one blended number from precision and recall (already in `other_ways`) |
| lift; precision at K | 2-3 | how much richer the top of the list is than a random list; share right in the top K |
| R-squared | 2-5 | a score an assistant will print for number predictions: share of the variation explained; why the lesson reads errors in dollars instead |
| p-value / statistically significant | 2-6 | how often noise alone would produce a gap this large; why the lesson reads the interval instead |
| one-hot encoding (dummy columns) | 3-2 or 3-5, whichever already shows a category turned into yes/no columns | a category column turned into one yes/no column per value |
| imputation | 3-4 | filling empty cells |
| bias-variance trade-off | 4-1 | too simple to see the pattern (bias / underfitting) against so flexible it learns the noise (variance / overfitting) |
| ensemble; random seed | 4-3 | many models voting or correcting each other; the number that fixes the random choices, so a rerun gives the same answer |
| counterfactual; selection bias | 5-1 | what would have happened to the same advertiser otherwise; groups that differ because of who chose the practice |
| statistical power | 5-2 | whether the test has enough advertisers to detect the effect it is looking for |
| dimensionality reduction (PCA is the classic method) | 7-2 | 256 numbers squashed to 2 so they can be drawn |
| zero-shot, few-shot, fine-tuning | 7-3 | instructions only; instructions plus a handful of examples; retraining the model on your labelled data |

How to add a term:
- **A glossary entry, always** (`glossary`: up to 7 items per lesson now). Term first, then the plain-words meaning
  the lesson already uses; put an alternative name in brackets after the term where useful.
- **One spoken naming sentence where it costs little**, placed right after the idea lands: "The textbook name for
  this is the bias-variance trade-off." Keep it to one short sentence (two for the supervised / unsupervised pair).
  Mandatory spoken: supervised and unsupervised (1-2), generalise (2-1), bias-variance trade-off (4-1), ensemble
  (4-3), zero-shot and few-shot (7-3). The others may live on a card or in the glossary only if the lesson is at
  its word limit - say which you chose.
- **Never define a term the lesson has not earned**, and do not start using the new word everywhere afterwards:
  name it once, then carry on in the lesson's own language.
- If a lesson already names the term somewhere you can find, leave it and say so.
- Optional, only if it fits in a clause and the lesson already teaches the idea: cosine similarity (7-2),
  hallucination (7-3), stratified sampling (4-2), holdout (2-1), data drift versus concept drift (5-6).

## Limits (unchanged)
- 6-9 segments, at most 950 spoken words per lesson (aim near 900), segments 25-140 words, at most 3 numbers in a
  spoken sentence, no symbols in narration. If a spoken addition would break the cap, trim an equal amount from the
  SAME segment so only one clip is re-recorded.
- Leave every other segment's narration byte-identical (audio is recorded per segment and re-recorded only when the
  text changes).
- Every number you touch re-verified against facts.json. Narration and its visual must agree.
- `python build/validate.py content/lessons/<id>.json` must show no ERROR after each lesson.

## Output
For each lesson write `qa/adjudication/<id>.round2.json`:

    {"lesson": "4-1",
     "recheck": [{"n": 0, "issue": "one line", "decision": "accepted | partly | rejected", "reason": "...", "change": "..."}],
     "terms": [{"term": "bias-variance trade-off", "spoken": true, "segment": 5, "glossary": true, "note": ""}],
     "segments_changed": [5],
     "open_questions": []}

Final message: per lesson, the re-check issues accepted / rejected, the terms added and whether each is spoken,
the segments whose narration changed, the validator status, and anything the course owner must decide.
