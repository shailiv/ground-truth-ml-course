# Syllabus council — findings and rulings (2026-11-21)

The draft syllabus (v2, 30 lessons) was reviewed by five independent seats before any lesson
was written. Full reviews are in this folder. This file records what was decided and why.

| Seat | Who | Brief |
|---|---|---|
| Curriculum | Gemini 4 Carbon | ML-education expert: coverage, sequence, pedagogy, generality |
| Practitioner | Gemini 4 Neon | Principal data scientist in adtech: technical red flags, suspicious results |
| Benchmark | Gemini Deep Research | Compare with established curricula, failure-mode checklists, learning science |
| The learner | Claude (fresh agent) | In persona: would I start it, finish it, use it on Monday? |
| Sceptical expert | Claude (fresh agent) | Audit the code and re-run the numbers; find what is wrong or over-claimed |

## Accepted

**Structure**
1. Metrics before model families: nothing is quoted before the learner can read it. (Carbon, learner)
2. Briefing and auditing taught in module 1, not lesson 30; the audit checklist grows cumulatively. (Carbon, learner, Neon)
3. Causality directly after model explanations, so "importance" is never left standing as a lever. (Carbon)
4. One idea per lesson: split overfitting/validation, features/dirty data, score-to-action/calibration. (all)
5. Cut the k-NN lesson, the PCA lesson, the neural-net internals and the "about this course" lesson. (Carbon, Neon, learner)
6. New lessons: calibration; real or noise; dirty tables; validation with time and groups; slices;
   quasi-experiments; uplift; time-to-event; the report you can stand behind. (all, in different mixes)
7. Homework cut to one mission per module; a capped daily review; rotating question variants so the
   learner cannot memorise an answer's position; no streak guilt; a published time budget. (learner, Carbon)
8. Lessons are screen-first with at most two rounded numbers per sentence; the audio-only product is a
   separate recall drill (question, pause, answer), not a re-read of the lesson. (Carbon, Deep Research)
9. Transfer happens in the questions, not in a footnote: quiz and review items set in other problems
   (creative fatigue, invalid traffic, lead scoring, upsell). (Carbon, learner)

**Evidence — the numbers were wrong or misleading and have been rebuilt**
10. A gap month between training and test: churn labels need 60 days to mature, so April's labels do
    not exist when May is scored. Train Jan–Mar, leave April out, test May–Jun. (Neon, sceptic)
11. "Break-even precision 10%" was a mis-statement: the rule is about the *next* advertiser's own
    probability (marginal), not the list's average hit rate. Renamed and recomputed. (Neon, Carbon)
12. Bug: the "true effect" of fresh creatives compared advertisers moved to the 14/15-day boundary,
    not the groups the naive comparison compares (6 vs 29 days). Fixed; truth is 13.1 points, not 5.8. (sceptic)
13. Every causal example pointed the same way (truth smaller than naive). Added a practice whose naive
    effect has the **wrong sign** (reviews go to struggling accounts): −25.3 naive, +8.8 true. (sceptic)
14. "The simple model ties the fancy one" was built into an additive simulation. Added a second task
    (video-ad adoption) driven by thresholds and combinations, where boosting clearly wins
    (+0.040 AUC, interval 0.031–0.049). The lesson is now "run both and compare with the noise". (Carbon, Neon, sceptic)
15. Forecast interval coverage and "error grows with horizon" were artefacts of planted incidents.
    Forecasting is now judged on the series without incidents; incidents are kept for the anomaly lesson. (sceptic)
16. The anomaly-detector comparison was unfair to isolation forest (extremes of 12+ SD, detector fitted
    on a subsample). Removed rather than taught. (sceptic, Carbon)
17. Keyword rules were a strawman and the top three text methods were indistinguishable on 108
    tickets. Rebuilt: about 400 test tickets written by a different model, whole batches held out, a third
    deliberately hard, a bag-of-words rung added, the classifier given its own category wording,
    intervals on every score. (sceptic, Neon)
18. The "four behavioural segments" are mostly two yes/no flags and unstable across random starts.
    Now taught as exactly that, with the stability check and a plain GROUP BY alongside. (sceptic)
19. The spend ladder had no intervals and hid the median-versus-mean bias of a log model. Now every
    neighbouring pair carries a paired interval and total-revenue error is shown beside MAE. (sceptic, Neon)
20. Odds ratios translated into probability shifts; binary flags are not standardised (they never
    were — the syllabus wording was wrong). (Neon)
21. "Early warning or already gone?": 107 of the top 200 highest-risk accounts were already winding
    down. Now reported, with the model's performance on still-active accounts only. (Neon)
22. Repeated-advertiser leakage and row-fan-out joins cannot be shown on a one-row-per-advertiser
    table. Two small separate simulations added. (Carbon, Neon, sceptic)
23. Scoreboard noise: the neural net is reported as a range over six runs; grouped permutation
    importance added; segment monitoring carries intervals. (sceptic, Neon)

## Rejected, with reasons
- **Replace binary churn with survival analysis** (Deep Research). A fixed-window label is the right
  first framing for a beginner; time-to-event gets its own lesson and censoring is taught in framing.
- **Marketing-mix modelling vs multi-touch attribution** (Deep Research). Adtech measurement, not ML
  fundamentals — the learner asked for general fundamentals.
- **Named frameworks and tooling** (REFORMS, ML Test Score, Polars) (Deep Research). The substance is
  in the audit checklists; the names are not.
- **External statistics about AI-written code** (Deep Research). Cannot be verified here; the course
  quotes only numbers it computed.
- **FSRS scheduling** (Carbon). A capped fixed-interval queue with rotating variants is enough.
- **CUPED, ALE plots, auction interference** (Neon). Named as "where next", not taught.
- **Ad headlines instead of support tickets** (learner). Tickets give a clean labelled task; headline
  scenarios appear in quiz questions instead.

## Stands as a caveat in every relevant lesson
Results come from simulated worlds built to be learnable. Lessons state which findings are properties
of ML and which are properties of this simulation, and never turn one simulated result into a rule.


---

# Post-writing review - rulings (2026-11-22)

After the 37 lessons were written they were read by seven independent reviewers (Gemini with the results file, four
Claude experts, two Claude learner personas). The copies they read carried 58 planted errors so the reviewers could be
scored; see `qa/review_scores.json`. Their 186 genuine findings are in `qa/findings_real.json`; each lesson's
adjudication is in `qa/adjudication/<id>.decisions.json`. The brief the editors worked to is
`qa/adjudication/FIXER_BRIEF.md`. Course-wide rulings made from the findings:

- **R1 General, not "the churn course"** (both learner reviewers; the owner asked for general fundamentals): each lesson
  states its idea in general form early and names another analyst question where it applies; 2-1, 2-4 and 4-4 open on a
  non-churn situation.
- **R3 Briefs are templates**: `ask_assistant` is written with [slots] so it can be pasted at work; the labs carry the
  course-table versions.
- **R4 Short recaps**: the last segment does not re-read the take-aways.
- **R5 Questions cannot be gamed**: the keyed answer may be the longest option in at most 4 of a lesson's 10 questions
  (now enforced by `build/validate.py`; six lessons failed it), and "nothing is wrong" filler options were replaced.
- **R6** the most practical alternative is spoken once, not left in the `other_ways` box.
- **R7** audit items must be checkable from output, not a statement the assistant makes about itself.
- **Evidence corrected before lessons** (`qa/facts_changes.json`): the A/A noise figures (two samples from a finite pool
  understated noise by about a fifth), the SD the logistic model actually used for cpa_vs_goal, the bag-of-words model
  (one vectoriser setting in two places), cross-validated scores by tree depth (added, so 4-1/4-2 can choose honestly),
  and several stale descriptions.
- **Structure changes**: 3-1 cut from five ideas to three; 6-2 from seven to three; 4-2 gained the honest depth choice
  and its learning-curve segment moved to 4-4; 1-3's open-window teaching corrected for the "no spend at all" label.
- **Rejected or deferred**: re-ordering lessons (3-4 earlier, 7-4 earlier) - prerequisites depend on the order, so 1-5
  carries the two habits instead; new lessons on impression-level problems and fairness - listed on the About page under
  what the course leaves out.

A player bug found by an editor (items without a reveal marker stayed hidden) and one found by the slide audit (the
reveal animation's offset was measured as overflow, shrinking slides) were fixed in `site/public/js/player.js`.
