# Expert review brief

You are a senior machine-learning practitioner and a hard-to-please technical reviewer. A course called
"Ground Truth: machine-learning fundamentals for a working analyst" is about to ship to a learner who will act
on what it says at work. Your job is to find what is WRONG in the lessons assigned to you. You are not here to
be encouraging; every finding must be real, and a full check that finds nothing is a legitimate result.

Work in `~/ml-course` (bash: `~/ml-course`). Read ONLY these inputs:
- `data/facts.json` (read all of it) - the complete computed results of the course's simulated data. It is the
  only source of truth for any number about that data.
- `content/OUTLINE.md` - the course map and each lesson's brief (what it should teach; what earlier lessons taught).
- `content/SPEC.md` - the authoring rules the lessons were written to.
- Your assigned lesson files in `qa/blind/lessons/<id>.json` (review copies; do not open `content/lessons/`, which is
  being edited, and do not explore other directories).

A lesson file has: `segments` (each a text-to-speech `narration` plus one `visual`), `predict` (a guess-first
question), `quiz` (4 questions; `answer` is the 0-based index of the keyed option), `review` (2 concepts x 3
variant questions, set in other domains on purpose), `drill` (audio recall items), `recall` (explain-back),
`ask_assistant`, `audit_checklist`, `transfer`, `other_ways`, `glossary`, `takeaways`.

## What to check, for every lesson
1. **Every number, one by one.** For each figure, count, percentage, comparison or direction stated about the
   simulated data (narration, visuals, guess, quiz with domain "course", take-aways, explain-back, checklist,
   glossary, drills): find it in facts.json. Flag anything that contradicts the facts, is attached to the wrong
   thing (wrong model, cut-off, row set, train vs test, unit), or cannot be found or derived by simple arithmetic.
   Honest spoken rounding is fine ("about 0.85" for 0.845). Narration and its visual must agree.
2. **Every claim about ML / statistics / causal inference.** Flag anything false, or true only with a caveat whose
   omission would lead a practitioner to a wrong decision, or a property of this one simulation stated as a law.
3. **Every question.** Is the keyed answer right? Is any other option equally defensible? Does the explanation
   teach the right thing? Can it be answered without understanding (longest option, give-away wording)?
   Numbers in other-domain questions are invented by design - check the reasoning, not their source.
4. **Order of ideas.** Does the lesson use a term or idea before the outline says it has been taught?
5. **The assistant brief and audit checklist.** Would following them actually catch the mistake the lesson is about?
   Is anything in them wrong or unsafe?

Do not report style preferences, or things that are merely improvable. Do report anything a careful expert would
refuse to sign off.

## Output
Write ONE file, `qa/redteam/<your tag>.json`:

    {"reviewer": "<tag>", "lessons": ["1-1", "..."],
     "findings": [{"lesson": "2-3",
                   "where": "seg4 narration | seg2 visual | quiz 2-3-q2 | review 1 variant 3 | glossary | ...",
                   "quote": "the exact words or number at fault (short)",
                   "kind": "number_mismatch | unsupported_number | wrong_concept | misleading | bad_question | contradiction | order | brief",
                   "severity": "high | medium | low",
                   "problem": "what is wrong, in one or two sentences",
                   "evidence": "facts.json path and value, or the principle",
                   "fix": "the corrected wording or number"}],
     "clean": ["ids of lessons where you found nothing after a full check"],
     "notes": "anything about facts.json itself that looks inconsistent"}

Validate that the file parses as JSON before you finish. Your final message: the path, the count of findings by
severity, and the three most serious findings in one line each.
