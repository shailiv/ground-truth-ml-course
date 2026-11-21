# Adjudication and fix brief

You are the editor responsible for a set of lessons in **Ground Truth: machine-learning fundamentals for a working
analyst**. Seven independent reviewers (a Gemini fact-checker, four Claude ML experts, two Claude reviewers playing
the learner) have read the course. Your job: **adjudicate every finding about your lessons, fix what is real, apply
the course-wide rulings below, and leave each lesson correct, general and usable.** You did not write these lessons
and you are not their defender. You are also not the reviewers' servant: reject a finding that is wrong, and say why.

Work in `~/ml-course` (bash: `~/ml-course`). Edit only your assigned `content/lessons/<id>.json` files and
write your decision files. Touch nothing else.

## Read first
1. `content/SPEC.md` - the learner, the voice, the non-negotiable rules. They still bind you.
2. `content/OUTLINE.md` - the course map; read your lessons' briefs and the briefs just before and after them.
3. `data/facts.json` - ALL of it. The only source of truth for numbers. **It changed after the lessons were written**:
   `qa/facts_changes.json` lists every change (path, was, now). If a lesson of yours quotes a changed figure, update it.
4. Your lessons: `content/lessons/<id>.json` (the real files - never `qa/blind/`).
5. Your findings: `qa/adjudication/<id>.findings.json` (one file per lesson; each finding names its reviewer).

## About the findings
- Reviewers read review copies made earlier, and those copies also contained deliberately planted errors used to
  measure the reviewers (they caught all of them). Findings about planted errors were removed, but check: **if a
  finding quotes text or a number that is not in the current lesson file, mark it `not_applicable`** and move on.
- `gemini` and `expert-*` findings are about correctness. Verify each against facts.json or the principle yourself.
  Accept when right; reject with the evidence when wrong.
- `learner-*` findings are about clarity, pace, relevance and usability for the learner described in SPEC.md. Accept
  when the fix makes the lesson better for that person without breaking a SPEC rule. Many are right. Some ask for a
  different course (new lessons, re-ordering): mark those `out_of_scope` with a one-line note; they are collected.

## Course-wide rulings (apply to EVERY lesson you own, finding or not)
- **R1 General, not "the churn course".** The learner asked for general fundamentals; churn was one of their examples.
  Within the first two segments, one spoken sentence must state the lesson's idea in its general form and name one
  other question from an ad-platform analyst's week where it applies identically (invalid traffic, which leads will
  convert, which advertisers will hit their CPA goal, video-format adoption, creative fatigue, spend forecasts,
  support-ticket routing - vary them across your lessons). Say "a yes-or-no model" or "a model that predicts a
  number" before "the churn model" where the idea is general. The worked numbers stay on the course's tables.
- **R2 New openings for three lessons** (only if you own them): `2-1` opens on a vendor or teammate claiming an
  invalid-traffic filter is "99 percent accurate"; `2-4` opens on a sales forecast that multiplies each open deal's
  win probability by its value; `4-4` opens on the video-adoption list. Each bridges in one sentence to the course
  table where the answer can be checked, and the rest of the lesson keeps its evidence.
- **R3 The assistant brief becomes a template the learner can paste at work.** Rewrite `ask_assistant` in general
  terms with square-bracket slots for what changes between questions, e.g. "Split by [date column]. Train only on
  periods whose [outcome window] had closed before the first test date, and say which period you left out. Print rows
  and [outcome] rate for train and test...". No course-specific months, column names, thresholds or list sizes
  (the labs carry the course-table versions). Keep every demand for evidence. 60-120 words, plain text.
- **R4 Short recap.** The last segment's narration is at most 50 spoken words: one sentence that ties the idea to
  what the learner will do with it, one that points to the next lesson. It must NOT re-read the take-aways (they are
  shown on screen right after). Keep its visual.
- **R5 Questions cannot be gamed.** Across the lesson's 10 questions (4 quiz + 6 review variants) the keyed answer may
  be the longest option in at most 4 (the validator now enforces this). Make distractors as specific and as long as
  the answer; do not pad the answer's rivals with filler. Replace "nothing is wrong" / "all of the above" style
  options unless that option is the keyed answer of that question (at most one such question per lesson). Every
  keyed answer must stay unambiguously correct. Options are shuffled on screen, so position does not matter.
- **R6 Say the practical alternative out loud.** If the most usable move sits only in `other_ways` (a random holdout,
  a rollout in random order, a cohort table, asking the assistant to map a script to its parts...), give it one
  spoken sentence in the "Brief and audit" segment.
- **R7 Audit items are evidence, not promises.** Every `audit_checklist` item must be checkable from the OUTPUT (row
  counts, dates, a table, a baseline beside the model). "The assistant states that it only scored the test rows once"
  is a claim; "test scoring is its own final stage that you trigger, and the output lists every evaluation run with
  the rows it used" is evidence.
- **R8 Change as little as you need.** Audio is already recorded per segment and is re-recorded only when a segment's
  narration text changes. Leave a segment's narration byte-identical unless a finding or a ruling requires a change.
  Do not restyle text that is fine.
- **R9 Every number re-verified.** After your edits, re-check every figure in each lesson against facts.json, one by
  one, including the ones you did not touch. Narration and its visual must agree.

## Lesson-specific rulings (apply the ones for lessons you own)
- `1-3`: the open-window problem must be taught correctly for the course's label (churned = no spend at all in the 60
  days after the snapshot). With only 20 days observed, advertisers who already spent are already stayers; the unknown
  ones are those with no spend so far (pausers or churners). Depending on how the label is computed, an immature
  window overstates churn (zero spend so far counted as churned) or understates it (undecided rows defaulted to
  stayed). Fix the narration, the quiz item and the drill so they are consistent with the definition.
- `1-4`: give the working rule for which account-table columns are safe: fields that cannot change because of the
  outcome (vertical, sign-up date) are fine with a note; fields that can (status, tier, last-activity dates) need a
  copy dated at the snapshot. facts `leakage.why` was reworded - keep the on-screen wording consistent with it.
- `1-5`: add the "read the prose against the numbers" habit in one sentence and one audit item (a report's sentences
  can be stale after a re-run), and make clear the audit block accumulates by stage.
- `2-6`: the A/A figures changed (see facts_changes: groups of 1,000 and 4,000). Update them.
- `3-1`: overloaded (five ideas). Restructure to at most three: the baseline ladder, why raw dollars mislead (the
  log scale), and typical versus average when converting back. Give the zero-spend row filter its own short segment
  before the ladder if it must stay; the brief makes four plain asks; move "two errors cancel" to a glossary note or
  drop it. Keep within the word limits.
- `3-2`: add one spoken sentence giving the learner what they MAY say today about "what separates happy advertisers":
  the observed association in careful words ("advertisers with X churned N points less than otherwise similar ones;
  we have not tested whether changing X helps"), using a real figure from facts. facts `logreg.coefs[].one_sd_is` and
  one `avg_probability_shift_pts` changed for cpa_vs_goal - update if quoted.
- `3-3`, `4-1`, `4-3`: facts now explain the two depth-3 trees (`tree.note`, `tree.min_rows_per_leaf` = 100 versus
  no minimum in `depth_sweep`). State it correctly wherever both appear.
- `3-5`: the "clean" script must pass the course's own checklist (it should print row counts, the baseline and both
  scores, each labelled). End on one card: the strings to search a long script for, and what each should look like.
- `4-1`: the brief must not set the trap 4-2 warns about. `depth_sweep` now has `cv_auc_on_training_months`; the
  brief asks for training score beside a cross-validated (or validation-period) score by depth, and the lesson says
  in one sentence that its own chart uses the test months only to show the effect, not to choose.
- `4-2`: you may now show choosing the depth honestly (cross-validation picks depth 5, the test months would have
  picked 4 - see `depth_sweep` and `depth_sweep_note`). The brief separates two cases: one row per unit (rotating
  folds inside the training period are acceptable, and why) and repeated or dated rows (grouped, forward-in-time).
- `4-3`: do not judge the gap between two models against one model's own interval; use the paired interval where
  facts have one, otherwise say the comparison is not settled.
- `4-5`: brief in the assistant's vocabulary ("per-row contributions: coefficient times distance from the training
  mean for a linear model, SHAP values otherwise"). The cpa_vs_goal SD and push figures: re-verify against facts.
- `5-1`: where a card shows two rounded rates and their gap (10.7%, 12.9%, 2.3 points), add "gap computed before
  rounding" or show enough decimals. In the brief the LEARNER supplies how each practice gets assigned; the assistant
  prints that line beside each gap.
- `5-2`: give the sentence the learner can write from an encouragement test ("advertisers prompted to switch hit goal
  X points more often; about N percent switched") using facts.
- `5-3`: the pre-launch drift check is borderline (0.33 +/- 0.31); do not state it flatly.
- `5-4`: `uplift.policies_call_400_note` - churns prevented are NET of advertisers a call pushes out. Show, if facts
  allow, the check a learner can actually run (called versus not called inside the list); otherwise say plainly that
  the lesson's counts use knowledge only a simulation has.
- `6-2`: overloaded (seven ideas). Cut to three: the backtest (rolling origins, never shuffled), the honest range,
  and what a level shift does. Put the level-shift fix in the narration and the brief ("if I name a break date, add a
  step from that date and re-run the backtest"). A range built from daily errors must not be handed over as a
  monthly figure.
- `6-4`: open from the cohort retention table the learner already builds ("you leave the unfinished cells blank; a
  survival curve is that table pooled across join months"), then introduce the terms.
- `7-2`, `7-3`: the bag-of-words model is now 54.2% in both `tickets.methods` and `tickets.learning_curve` (it was
  53.1% in one place), and the paired gaps moved slightly - update. The test set is 450 tickets, 300 of them hard.
  In `7-3`, do not recommend embeddings for text that "must not leave the building" unless the embedding model runs
  locally - say so.
- `7-4`: add the fourth evidence tier and its verb: compared with a similar untreated group ("rose N points more than
  the comparison group; assumes the two would have moved together").

## Output
1. Edit your lesson files in place. After each lesson: `python build/validate.py content/lessons/<id>.json` must show
   **no ERROR** (fix warnings where you reasonably can; do not introduce new ones).
2. For each lesson write `qa/adjudication/<id>.decisions.json`:

       {"lesson": "2-3",
        "decisions": [{"n": 0, "reviewer": "expert-1", "finding": "one line", "decision": "accepted | partly | rejected | not_applicable | out_of_scope",
                       "reason": "why, with the facts.json path or principle", "change": "what you changed, or empty"}],
        "rulings": {"R1": "what you did", "R2": "...", "R3": "...", "R4": "...", "R5": "...", "R6": "...", "R7": "...", "specific": "..."},
        "segments_changed": [1, 4, 8],
        "numbers_verified": 57,
        "open_questions": ["anything you could not resolve, for the course owner"]}

   `n` is the finding's index in the findings file. Every finding gets a decision.
3. Final message: for each lesson, counts of accepted / rejected / not_applicable / out_of_scope, the segments whose
   narration changed, validator status, and anything the course owner must decide.
