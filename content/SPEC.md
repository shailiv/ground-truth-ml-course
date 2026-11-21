# Lesson authoring spec (v3 — after the review council)

You are writing lessons for a private course, **Ground Truth: machine-learning fundamentals for a
working analyst**. Each lesson is one JSON file. A player shows one visual per segment while a
text-to-speech voice reads that segment's narration, and the visual builds in step with the voice.

Read, in this order, before writing a word: this file · `content/OUTLINE.md` (the whole course map,
then your lessons' briefs in detail) · `data/facts.json` in full · `docs/council/DECISIONS.md`.

## The learner (write to this person, in the second person)

- A working data analyst at an adtech / native-advertising platform. Their clients are
  **advertisers**; their world is spend, clicks, conversions, CPA, campaigns, creatives, bidding,
  account managers. Never name a real company.
- Strong in SQL, spreadsheets and BI dashboards. Basic statistics. Reads simple pandas, writes
  little Python. Almost no ML. In a baseline quiz they were unsure why 95% accuracy can be useless.
- Their analysis is mostly produced by an AI coding assistant and shipped as HTML reports. The skill
  being built is **direct and audit**: frame the problem, choose an approach, brief the assistant
  in stages, read what comes back, catch the classic mistakes. Not hand-coding models.
- Fast learner who forgets without reinforcement. Bored by padding. Prefers audio/video.
- They want **general ML fundamentals**. Two questions they are often asked — "what separates happy
  advertisers from unhappy ones?" and "can we predict churn?" — were given as *examples only*. Do
  not write "the churn course". Each lesson teaches an idea that outlives its example.

## Voice

A senior analyst mentoring a sharp colleague: warm, direct, concrete, a little dry, never
condescending, no hype. Explain each term in plain words the first time, then use it. Lean on what
they know ("this is a GROUP BY the data designed", "a CASE WHEN with learned cut-offs").

## Non-negotiable teaching rules

1. **One idea per lesson.** If your brief lists a secondary point, give it one sentence or leave it
   to the reference fields below. 650–900 spoken words across 6–9 segments (about 4½–6 minutes);
   each segment 50–130 words. Hard cap 950.
2. **Open with a situation from their job**, never a definition. Concrete before abstract: show the
   number or picture, then name the concept.
3. **Screen-first, ear-safe.** The learner watches the first time, so exact tables, code and long
   number lists live in the VISUAL. The narration carries the story with **at most two numbers in a
   sentence, rounded for speech** ("about 0.85", "roughly one in five"). Never read a table aloud.
   Never say "as you can see", "this chart", "on the left", "the red bar".
4. **Write for a voice.** Short sentences. No parentheses, no markdown, no symbols, no emoji, no
   headings. "14 percent", not "14%". Column names as words ("spend trend", "CPA versus goal").
   Capitals for AUC, CPA, CTR, SQL, MAE. Say "scikit-learn". Say "return on ad spend".
5. **Only numbers from `data/facts.json`.** Copy them (rounding for speech is fine). If the number you
   want is not there, make the point without a number, or use a clearly labelled toy example ("say
   you have 1,000 advertisers…"). Never state facts about the wider world (history, industry
   statistics, "studies show") — they cannot be checked here.
6. **Never turn one simulated result into a rule.** The data is simulated so that the truth is
   knowable. When a result is a property of this simulation (the simple model winning on churn, a
   forecast within a percent a year out, tidy clusters), say so in one plain sentence and say what
   you would expect on real data only if your brief tells you. The meta-lesson is always "measure it".
7. **Terms only after they are taught.** Your brief lists what earlier lessons established. Do not
   use a concept from a later lesson; if you must point ahead, say "a later lesson" without the term.
8. The second-to-last segment is **"Brief and audit"**: what to ask the assistant for at this stage,
   and what its output must *show* for you to believe it (row counts, dates, baselines — evidence in
   the output, not code you have to read).
9. The last segment is a short recap and one sentence on what comes next.
10. Be correct before being simple. If a simplification would be false, say the true thing plainly.

## File format

`content/lessons/<id>.json`, UTF-8, valid JSON, exactly this shape:

```json
{
  "id": "2-2",
  "module": 2,
  "title": "Max 6 words",
  "subtitle": "The question this lesson answers, one line",
  "goal": "After this lesson you can … (one observable skill)",
  "predict": {"q": "A take-a-guess question shown BEFORE the lesson. The lesson must answer it.",
              "options": ["3 or 4 short options"], "answer": 0,
              "reveal": "One sentence shown after they guess: the answer, and that the lesson shows why."},
  "segments": [{"narration": "50–130 words. May contain [[1]] cue markers.", "visual": {"type": "…"}}],
  "takeaways": ["exactly 3 short sentences"],
  "quiz": [{"id": "2-2-q1", "concept": "precision", "domain": "course", "q": "Scenario question?",
            "options": ["A", "B", "C", "D"], "answer": 1,
            "why": "Why the right one is right AND why the tempting wrong one is wrong. 1–3 sentences."}],
  "review": [{"concept": "precision vs recall",
              "variants": [{"q": "…", "options": ["A", "B", "C", "D"], "answer": 2, "why": "…"}]}],
  "drill": [{"q": "A question to be read ALOUD, answerable in a sentence.", "a": "The spoken answer, 1–2 sentences."}],
  "recall": {"prompt": "Explain-it-back question, 30 seconds", "model_answer": "2–4 sentence strong answer"},
  "ask_assistant": "A ready-to-paste brief for their AI assistant for this stage of the work, 2–5 sentences.",
  "audit_checklist": ["2–4 things the assistant's OUTPUT must show before you believe it"],
  "transfer": ["exactly 3 other questions, outside this lesson's example, where the same idea applies"],
  "other_ways": [{"approach": "another way to attack the same problem", "when": "when you would prefer it"}],
  "glossary": [{"term": "precision", "def": "one plain sentence"}]
}
```

- **quiz**: exactly 4 questions, each with 4 options and a 0-based `answer`; vary the position of the
  right answer. Realistic scenarios (a stakeholder says X, the assistant returns Y — what is the right
  read?), never trivia or recall of a number. Distractors are the mistakes a smart beginner really
  makes. **At least one** is an audit question (the assistant's output hides a flaw — spot it).
  **At least one** has `"domain": "other"` and is set in a different problem from the lesson's
  example: creative fatigue, invalid traffic, lead scoring, upsell, pricing, a support inbox, a
  forecast for finance. The rest are `"domain": "course"`.
- **review**: exactly 2 concepts — the two ideas from this lesson worth remembering in three months.
  Each has exactly 3 `variants`: the *same* idea tested in three *different* settings with different
  numbers, at least two of them outside the lesson's example. These, not the quiz, feed spaced
  review; a different variant is shown each time, so no variant may depend on another.
- **drill**: exactly 2 question-and-answer pairs for an eyes-free audio drill. Written for the ear:
  no options, no numbers that need a screen. The question must make sense on its own a month later.
- **transfer**: exactly 3. **other_ways**: 2 or 3. **glossary**: 2–5 terms introduced here.
- **audit_checklist**: 2–4 items, each something visible in the assistant's output.

## Visuals — only these types, exactly these fields

Text in a visual is read at a glance while listening: aim under 40 words. Numbers may be exact.

```json
{"type": "title", "kicker": "Module 2 · Lesson 2", "title": "Big title", "sub": "one line"}
{"type": "bullets", "title": "Heading", "items": ["up to 5 short lines"]}
{"type": "quote", "text": "One key sentence to remember", "sub": "optional small line"}
{"type": "compare", "title": "Heading", "left": {"label": "Naive", "value": "−11.2 pts", "sub": "small text"}, "right": {"label": "True", "value": "−2.3 pts", "sub": "small text"}}
{"type": "stat", "title": "Heading", "stats": [{"value": "86.8%", "label": "accuracy"}, {"value": "0", "label": "churners found"}]}
{"type": "table", "title": "Heading", "columns": ["A", "B"], "rows": [["1", "2"]], "highlight": [0], "note": "optional"}
{"type": "bar", "title": "Heading", "unit": "%", "data": [{"label": "No tracking", "value": 18.4}, {"label": "Tracking", "value": 7.2}], "highlight": [0], "note": "optional"}
{"type": "line", "title": "Heading", "xlabel": "Tree depth", "ylabel": "AUC", "x": [1, 2, 3], "series": [{"name": "Train", "values": [0.7, 0.76, 0.8]}, {"name": "Test", "values": [0.68, 0.74, 0.79]}], "note": "optional"}
{"type": "matrix", "title": "Heading", "tp": 104, "fp": 37, "fn": 423, "tn": 3436, "positive": "churned", "negative": "stayed"}
{"type": "flow", "title": "Heading", "steps": [{"label": "Snapshot", "sub": "features up to here"}, {"label": "60 days", "sub": "outcome window"}]}
{"type": "timeline", "title": "Heading", "spans": [{"label": "Observation: 8 weeks", "from": 0, "to": 56, "kind": "obs"}, {"label": "Outcome: 60 days", "from": 56, "to": 116, "kind": "out"}], "marks": [{"at": 56, "label": "Snapshot date"}], "note": "optional"}
{"type": "formula", "title": "Heading", "lines": ["precision = real churners flagged ÷ everyone flagged", "= 104 ÷ 141 = 73.8%"], "note": "optional"}
{"type": "code", "title": "Heading", "lang": "python", "code": "max 12 short lines", "note": "what to notice"}
{"type": "widget", "name": "threshold", "title": "Heading", "note": "what to try"}
```

- `bar`: 2–8 bars, numeric values (negatives allowed), horizontal; `unit` is `%`, `$`, `pts` or omitted.
- `line`: 1–3 series; `x` and every `values` the same length (≤ 30 points).
- `table`: at most 6 columns × 7 rows; every cell a string.
- `timeline`: numbers are positions on one shared axis; `kind` is `obs`, `out`, `bad` or `ok`.
- `code`: `lang` is `python`, `sql` or `text`; lines under 70 characters. Use sparingly: this learner
  reads code, the assistant writes it. SQL is their home turf.
- First segment's visual is always `title`.
- **Widgets** (interactive; use only where your brief names one; end that segment's narration by
  inviting them to try it): `threshold` (drag a cut-off over the real test scores: live counts,
  precision, recall) · `depth` (tree depth: train vs test AUC) · `tree` (the fitted depth-3 churn
  tree) · `practices` (naive vs adjusted vs true effect per practice) · `calibration` (predicted vs
  actual by bin) · `ranklist` (list size: churners reached, net value, rank by probability or by
  expected dollars) · `forecast` (the daily series with each method's backtest forecast) ·
  `anomalies` (the series with incidents and each detector's alerts) · `ticket_map` (support tickets
  as dots; nearby dots are similar) · `survival` (share of advertisers still active over time).

### Cue markers — make the visual build with the voice

Inside a narration you may place `[[1]]`, `[[2]]`, … The marker is silent; at that moment the player
reveals item N of that segment's visual: `bullets.items`, `flow.steps`, `stat.stats`, `formula.lines`,
`table.rows`, `bar.data`, `timeline.spans`, and for `compare` 1 = left, 2 = right. Put each marker
immediately before the sentence about that item, in ascending order. Items without a marker are
visible from the start. Use them whenever the narration walks through items one at a time.

## Before you finish

Re-read each lesson as the learner: is every sentence true; is every number in `facts.json`; is there
exactly one idea; could a listener follow it with the screen off even if they would miss the detail?
Then run `python build/validate.py content/lessons/<id>.json` for each file and fix every ERROR and
every warning you can. Your final message lists: files written, word counts, and any number you
wanted but could not find in `facts.json`. Nothing else.
