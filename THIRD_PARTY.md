# Third-party material

## Fonts (in `site/public/fonts/`)

All three families are distributed under the SIL Open Font License, Version 1.1
(<https://openfontlicense.org/open-font-license-official-text/>). The files here are Latin and Latin-extended
subsets in WOFF2 format, fetched from Google Fonts by `build/fonts.py`.

| Family | Copyright |
|---|---|
| Bricolage Grotesque | Copyright 2022 The Bricolage Grotesque Project Authors (<https://github.com/ateliertriay/bricolage>) |
| Inter | Copyright 2016 The Inter Project Authors (<https://github.com/rsms/inter>) |
| JetBrains Mono | Copyright 2020 The JetBrains Mono Project Authors (<https://github.com/JetBrains/JetBrainsMono>) |

## Libraries (installed by `npm install`, not included here)

- Pyodide (Mozilla Public License 2.0), with scikit-learn, NumPy, pandas and SciPy (BSD-style licences): used only to
  compute `data/facts.json`.
- Wrangler (MIT or Apache 2.0): used only to deploy.

## Generated material

Narration audio was synthesised with Google's Gemini text-to-speech. The research notes in `docs/council/` and the
fact-check records in `qa/factcheck/` are outputs of Gemini models; the reviews in `qa/redteam/` and the lessons
themselves were written with Claude.
