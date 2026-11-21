# Ground Truth

A private course in machine-learning fundamentals for a working data analyst: someone strong in SQL and BI, light on
Python and new to ML, whose modelling work is done by an AI coding assistant. The goal is not to write models by hand
but to **frame a question, brief the assistant in stages, and audit what comes back**.

37 short narrated lessons in 7 modules (about 200 minutes of audio), spaced review cards, audio drills, five case
files to audit, five labs, and a field guide. It runs as one Cloudflare Worker with static files and a KV namespace
for progress, behind a passphrase.

Everything a lesson claims is computed on **simulated** advertiser data, so the truth is known and nothing is
confidential.

## How it is put together

| Path | What it is |
|---|---|
| `content/SPEC.md`, `content/OUTLINE.md` | The learner, the voice, the lesson format; the brief and the evidence each lesson may quote |
| `content/lessons/*.json` | The lessons: narration with cue marks, one visual per part, questions, review cards, briefs, checks |
| `data/facts.json` | **The only source of numbers.** Produced by `build/analysis*.py` (scikit-learn, run under Pyodide) |
| `build/` | Analysis, validation, audio, site build, tests, review tooling |
| `site/worker.js` | Login, progress API, byte ranges for audio, security headers |
| `site/public/` | The site: plain ES modules, no framework, no build step |
| `qa/` | The review record: planted-error calibration, expert and learner reviews, fact-checks, rulings, design and code reviews |
| `docs/council/` | The syllabus council: research and second opinions that shaped the outline |

## Run it locally

Needs Node 20 or newer and Python 3.11 or newer. No install step for the site itself.

```bash
python build/build_site.py              # content/ + data/ -> site/public/data/course.json
node build/dev_server.mjs 8788          # http://localhost:8788   passphrase: test
node build/test_site.mjs                # progress merge + "is the site really locked" tests
python build/validate.py                # lesson format rules (word limits, cue marks, question rules)
```

The local server runs the real `site/worker.js` against an in-memory stand-in for Cloudflare (`build/local_env.mjs`).

## Reproduce the numbers

```bash
npm install                             # pyodide (scikit-learn in WebAssembly) and wrangler
node build/run_analysis.mjs             # about 3 minutes -> data/facts.json, site/public/data/widgets.json, CSVs
node build/run_tickets.mjs              # the support-ticket text analysis -> data/tickets_facts.json
python build/lint_numbers.py            # every number in a lesson traced to facts.json (a tripwire, not a proof)
```

All random seeds are fixed in the analysis files. `qa/facts_changes.json` lists every figure that changed after
review, and why.

## How it was checked

1. **Calibration first.** `build/plant.py` planted 58 known errors (48 numeric, 10 conceptual) into copies of the
   lessons. Reviewers were scored on those before their real findings were trusted (`build/score_reviews.py`,
   `qa/review_scores.json`).
2. **Seven readers**: four expert reviewers, two learner personas, and a Gemini model checking each lesson against
   `facts.json` (`build/factcheck.py`).
3. **Adjudication**: every finding accepted, partly accepted or rejected with a reason
   (`qa/adjudication/*.decisions.json`), under course-wide rulings in `qa/adjudication/FIXER_BRIEF.md`.
4. **Audio**: each clip transcribed back and compared with its text (`build/tts_verify.py`, `qa/audio_report.json`).
5. **Site**: a code review (`qa/site_review_code.json`), a design review (`qa/design/REVIEW.md`) and a learner
   walkthrough at phone and laptop sizes (`qa/ux/report.json`).

## If you are asked to cross-check this course

The useful checks, in order of value:

1. **Numbers.** For each `content/lessons/<id>.json`, every figure in `narration`, visuals, questions and briefs must
   be derivable from `data/facts.json` (the lesson's permitted evidence keys are listed under its id in
   `content/OUTLINE.md`). Report: lesson, part, the claim, the facts path, what the facts say.
2. **Concepts.** Is each statement about machine learning correct as a general principle, not only on this dataset?
   The lessons deliberately simplify; flag what is *wrong*, not what is incomplete.
3. **Narration against visual.** The slide must show what the voice says, with the same numbers.
4. **Questions.** One defensible answer; the explanation must say why the tempting wrong answers are wrong; the
   right answer should not be guessable from length or wording.
5. **Re-run the analysis** and diff `data/facts.json`.

`qa/planted_key.json` and `qa/blind/` hold the planted-error set if you want to calibrate a new reviewer the same way.

## Deploy

```bash
cf-login.cmd            # Windows: one-time Cloudflare sign-in (or: npx wrangler login, inside site/)
bash build/deploy.sh    # builds, creates the KV namespace, deploys, sets the secrets, smoke-tests the lock
```

The passphrase and the session secret are generated at deploy time and stored as Worker secrets. They are never in
this repository; `.secrets/` is ignored.

## Not in the repository

API keys and deploy secrets; the uncompressed audio masters and transcription cache (`data/audio_wav/`,
`data/audio_transcripts/`); screenshots from test runs; local tools (`.tools/`, `node_modules/`).

Fonts are bundled under their open licences: see `THIRD_PARTY.md`.
