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
On Windows, `preview.cmd` does the second line and opens the browser.

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
4. **A second round**: every corrected lesson fact-checked again (`qa/factcheck/final/`), the points ruled on by a
   second set of editors (`qa/adjudication/*.round2.json`), and the textbook terms added where a lesson already
   taught the idea. Then only the fields that round changed were sent back to Gemini, old text beside new
   (`build/factcheck_diff.py`, `qa/factcheck/round2_diff/`, rulings in `qa/adjudication/round2_diff.decisions.json`).
5. **Audio**: each clip transcribed back and compared with its text (`build/tts_verify.py`, `qa/audio_report.json`);
   every flagged clip decided on, with a second transcriber for the doubtful ones (`qa/audio_flags_reviewed.json`).
   Each clip carries a fingerprint of the words it was recorded from, and the build refuses a stale one.
6. **Site**: two code reviews (`qa/site_review_code.json`, `qa/site_review_round2.json`), a design review
   (`qa/design/REVIEW.md`) and a learner walkthrough at phone and laptop sizes (`qa/ux/report.json`). The findings
   about progress and the lock are now tests (`build/test_site.mjs`).

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

On Windows, double-click `go-live.cmd`: it signs in to Cloudflare (a browser window, once), then runs the script
below, then shows the address and the passphrase. `show-login.cmd` shows them again at any time.

```bash
cd site && npx wrangler login && cd ..     # once
bash build/deploy.sh                       # tests, builds, creates the KV namespace, deploys with its secrets,
                                           # then runs build/smoke.sh against the live site and fails loudly
                                           # if anything is readable without a sign-in
```

The passphrase, the session-signing key and the tutor relay's secret are generated on first deploy and kept in
`.secrets/` (ignored by git); they are uploaded as Worker secrets together with the code. `site/wrangler.jsonc` is
a template: the real KV namespace id goes into `site/wrangler.deploy.jsonc`, which is not committed either.

`bash build/smoke.sh <url> <passphrase-file>` can be run against `npx wrangler dev` too, which is Cloudflare's own
runtime on your machine: that is how the Worker, the Durable Object and the audio byte ranges were checked before
the first real deploy.

## The tutor

A lesson page can ask Claude a question, and the question carries the moment it was asked from: the lesson, the
part and second of the video, the sentence being spoken, what the slide showed, the question on screen during a
check, and which lessons are already finished.

Claude is reached on the owner's own Claude subscription, which only Claude Code may use. So the site does not call
Claude. Instead:

```
lesson page --question--> Worker --> TutorRoom (Durable Object, site/tutor.js)
                                          ^  one request held open
                          relay/tutor_relay.py  --runs-->  claude -p   (no tools, no settings, nothing saved)
```

`relay/tutor_relay.py` runs wherever Claude Code is signed in (`tutor-relay.cmd` on Windows, or any always-on
machine: `python relay/tutor_relay.py --config relay.json`). While it is connected, answers appear on the page.
When it is not, the same question, with the same context, opens claude.ai in a new tab. The Worker never holds a
Claude credential. This arrangement is for the owner's own questions; a site with other users would need the
Claude API and an API key instead.

## Not in the repository

API keys and deploy secrets; the uncompressed audio masters and transcription cache (`data/audio_wav/`,
`data/audio_transcripts/`); screenshots from test runs; local tools (`.tools/`, `node_modules/`).

Fonts are bundled under their open licences: see `THIRD_PARTY.md`.
