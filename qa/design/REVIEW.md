### 1. Verdict

* **Pretty: 6.5 / 10**
  The typographic trio (`Bricolage Grotesque`, `Inter`, `JetBrains Mono`) and dark green-black palette establish a calm, credible foundation, but half the screens still look like an unstyled Tailwind/shadcn developer build rather than an art-directed product. Washed-out white-on-white surfaces in light mode, vast empty voids inside slides, colliding chart labels, and raw browser-default `<audio>` and `<details>` elements break visual polish repeatedly.
* **Engaging: 6.5 / 10**
  The writing voice and pedagogical premise—auditing AI-generated analysis rather than memorizing formulas—are sharp, respectful, and genuinely compelling. Visually, however, uniform rounded rectangles, under-scaled diagrams floating in empty boxes, pre-revealed "guess first" widgets, and case files styled identically to course chrome make the experience feel flat and static.
* **Not confusing: 5.5 / 10**
  Player transport controls are pushed completely below the fold on both `1440×900` laptops and `390px` phones, Home pits two primary teal CTAs against each other while repeating due reviews in three places, and first-time visitors get zero explanation of how the five top-level tabs fit together. Trust-breaking details—a missing Lesson `1` in Module 3, module durations that do not match their contents, an `AUC` axis going to `1.1`, and an optional `Explain` step that makes completed lessons look unfinished—create unnecessary friction for a detail-oriented analyst.

---

### 2. The Ten Changes That Would Improve It Most (Ranked)

#### 1. Fit the `Watch` stage and its transport bar inside a single viewport on both laptop and phone
* **Screenshots:** `#4` (Watch poster), `#7–#19` (all desktop Watch slides/widgets at `1440×900`), `#29–#30` (Phone Watch).
* **Problem:** Above the slide stage, the global nav, breadcrumb, `H1`, multi-line `"After this lesson..."` objective, and five step buttons consume `~275px` vertically on desktop and `~345px` (over 40% of the screen) on phone. Combined with a `~600px`-tall stage, the play/pause button, scrub bar, timer, playback speed, `CC`, and audio-only toggle are pushed completely off-screen on every single `1440×900` screenshot (in `#16`, the top 3 pixels of the play circle peek up at `y=900px`) and sliced in half on phone (`#29`). A "wide stage that plays like a video" cannot hide its pause button and timeline below the scroll fold.
* **Exact fix:**
  * **Compact header in active steps (`Guess`, `Watch`, `Check`, `Explain`):** Hide the 2–4 line `"After this lesson you can..."` paragraph once the learner enters `Watch` or `Check` (show it on `Guess` and `Take away`, or behind a subtle `Lesson goal ▾` toggle). Combine breadcrumb + title on the left and the step pills on the right (desktop) so everything above the stage fits inside `108px` below the `56px` global nav (`164px` total top chrome).
  * **Viewport-locked stage + docked transport bar:** Cap the combined stage + control bar height at `calc(100vh - 196px)` (`max-height: 640px` on `1440×900`). Dock the `52px` transport bar *inside* the bottom border of the stage container (`border-top: 1px solid var(--border-subtle)`) rather than floating outside below it, so stage and controls always appear as one instrument.
  * **Phone (`390px`):** Collapse the global nav's second row inside lessons into a slim sticky bar (`← Module 1` on left, compact `1 · 2 · 3 · 4` step indicator on right, `48px` height), bringing the entire slide + play/scrub bar above `y=760px` with zero scrolling.

#### 2. Eliminate competing primary CTAs and triple-entry Review clutter on Home
* **Screenshots:** `#1, #2, #5, #6` (Desktop Home), `#20, #33` (Phone Home).
* **Problem:** Two solid survey-teal primary buttons (`Continue` on the left and the wider, heavier `Start today's review` on the right—or stacked consecutively on phone) compete for first click. Worse, spaced-repetition review is surfaced **three times** in one viewport: `Review 10` in the top nav, `Review 10 cards` inside the `NEXT UP` lesson card (falsely implying those 10 cards belong specifically to Lesson 4), and `Start today's review` in the right rail. Meanwhile, the right rail displays a dead `—` (`#1`) or a giant `50% review answers right` (`#5`, `#33`), which feels like a failing grade after answering just two cards.
* **Exact fix:**
  * **One primary CTA per screen:** Keep `Continue` (`height: 44px`, `padding: 0 22px`, solid survey-teal) as the sole filled primary button on Home.
  * **Decouple Review from the Next Up card:** Delete the `Review 10 cards` button from inside the `NEXT UP` card; let that card focus 100% on the current lesson.
  * **Restyle the right-rail Review button:** Make `Start today's review` a strong secondary button (`background: transparent`, `border: 1px solid var(--amber-border)`, amber dot + ink label `Review 10 cards · ~2 min`). When `0` cards are due, collapse it to muted text `All caught up for today`.
  * **Replace the punitive accuracy stat:** Replace `review answers right` (`—` / `50%`) with a constructive memory metric: `Cards in rotation` (e.g., `18` / `active cards`) or `Reviewed this week`.

#### 3. Fix trust-breaking chart math, axis distortions, and broken widget states
* **Screenshots:** `#15` (Learning curve), `#16 & #30` (Overfitting tree depth), `#17` (Drivers dot plot), `#18` (Anomalies), `#19` (Logistic regression weights).
* **Problem:** Your user is a working data analyst; sloppy chart mechanics undermine a brand called *Ground Truth*:
  1. **`#16 & #30` (`Overfitting`):** Y-axis (`AUC`) has a gridline and label at **`1.1`**—mathematically impossible since AUC cannot exceed `1.0`. X-axis plots unevenly spaced tree depths (`1..25` subset) at equal pixel intervals, warping the curve's slope relative to the linear `1–25` slider underneath.
  2. **`#15` (`Learning curve`):** Exponential/irregular sample sizes (`100, 250, 500, 1,000, 2,000, 4,000, 6,000`) are plotted as equally spaced categories (`4,000 → 6,000` is 1.5× while `100 → 250` is 2.5×, yet same width!), and `Lowest of 8 samples` introduces a third bright-green series that violates your two-series chart specification.
  3. **`#17` (`Drivers are not causes`):** All three series (`Naive gap`, `Adjusted`, `True effect`) are revealed upfront while the grey prompt at the *bottom* says `"Guess the true effect of each practice before you reveal it."` Table column headers `ADJUSTED` and `TRUE EFFECT` collide (`<2px` gap), and on row 5 (`-25.3` vs `-25.5`) the blue dot completely occludes the grey dot.
  4. **`#18` (`Anomalies`):** Missing space in **`Band width3`**; KPI counts (`17 alert days · 6 of 7 incidents caught · 9 false alarm days`) crash directly into the legend (`🟠 planted incident | alert`); X-axis ticks use US `MM-DD` (`01-31`) while caption uses UK `20 January`.
  5. **`#19` (`Logistic regression`):** Only row 1 (`-5.1pts`) is blue while `+2.3pts` (`Payment failures`, the sole churn-increasing driver) is dull grey, and numbers have inconsistent precision and signs (`-3pts` vs `-5.1pts` vs unsigned `2.3pts`).
* **Exact fix:**
  * **`#16 / #30`:** Clamp Y-axis strictly to `[0.4, 1.0]` (step `0.1`). Plot X-axis on a true linear `1–25` scale with ticks at `1, 5, 10, 15, 20, 25` so the vertical cursor aligns proportionally with the slider thumb.
  * **`#15`:** Use a true base-2 log scale (`125, 250, 500, 1,000, 2,000, 4,000` or label `(log scale)`) and render `Highest`–`Lowest` as a single translucent blue shaded range band (`fill-opacity: 0.14`, thin hairline bounds) around the solid orange `Average` line—eliminating the rogue green line.
  * **`#17`:** Default `True effect` to **off/hidden** on load (`pill` unselected, `TRUE EFFECT` column showing `—`), and move `"Guess the true effect, then toggle True effect to check"` directly beside the top pills (`13px` Inter). Set right-hand numeric columns to `width: 76px` each (`gap: 16px`, right-aligned `JetBrains Mono`) and vertically offset dots within `0.5` units by `±4px` (or render `Naive` as a hollow `1.5px` ring so stacked dots stay visible).
  * **`#18`:** Fix flex spacing to `Band width` (`13px` Inter secondary) + `3` (`14px` `JetBrains Mono` badge, `gap: 8px`). Put the 3 KPI counts in metric pills on row 1 and right-align the 2 legend items on row 2. Format X-axis dates as `4 Aug`, `3 Oct`, `2 Dec`, `31 Jan`, `1 Apr`.
  * **`#19`:** Color churn-reducing bars (`< 0`) survey-blue and churn-increasing bars (`> 0`) survey-orange (if narration spotlights row 1, dim non-active rows via `opacity: 0.45` rather than stripping semantic color). Format all values to 1 decimal with explicit signs and `tabular-nums`: `-5.1 pts`, `-3.0 pts`, `+2.3 pts`.

#### 4. Fix the internal slide grid so text and diagram slides stop floating in empty black voids
* **Screenshots:** `#7, #8, #9, #10, #11, #12, #13, #14`.
* **Problem:** Because the stage uses a tall fixed height while pinning titles top-left and pushing content or captions to the bottom edge, simple slides have a `200–260px` dead chasm across the middle (`#8, #10, #12, #14`). Takeaway lines in `#8` and `#14` sit stranded on the floor in low-contrast `13px` grey where the eye misses them; `#11` (and `#29`) awkwardly breaks **`1 column, 1 cut-` / `off`** across lines; `#9` left-aligns numeric columns; `#14` uses a muddy dark-brown fill (`#3b2219`) for the outcome window; and `#13` uses barely legible dark-teal numbered circles (`< 3:1` contrast).
* **Exact fix:**
  * **Standardize a centered 3-band slide template (`padding: 40px 56px`):** Keep Header (`eyebrow` + `H2`, `max-width: 24ch–32ch`) and Body grouped with a predictable `32px–40px` gap, vertically centered *together* as one optical block inside the stage (`margin: auto 0`). Replace floor-pinned grey footnotes (`#8, #14`) with a structured takeaway callout `24px` directly below the visual (`border-left: 2px solid var(--teal)`, `padding-left: 14px`, `16px` Inter `#d6dfdc`).
  * **Typography & tables:** Add `white-space: nowrap` to hyphenated terms (`cut-off`, `cut-offs`) and step two-up comparison card headlines (`#11`) from `~40px` down to `32px` (`line-height: 1.15`, `text-wrap: balance`). In `#9`, right-align `SPEND TREND`, `ACTIVE DAYS (OF 28)`, and `DAYS SINCE LOGIN` headers and cells (`font-variant-numeric: tabular-nums`).
  * **Diagram upgrades:** In `#12` (`Learn, freeze, score`), add `01 / 02 / 03` mono indices inside the cards, increase card padding to `28px`, and replace tiny `14px` grey arrows with `24px` crisp `#9fb0aa` connectors. In `#14` (`Timeline`), draw a continuous horizontal time axis with ticks, a vertical amber `Snapshot date` line + badge, a survey-blue observation block (`rgba(59,130,246,0.16)`, `1px solid #3b82f6`), and an orange outcome block (`rgba(234,88,12,0.16)`, `1px solid #ea580c`, `#fed7aa` text—eliminating muddy brown). In `#13`, give numbered circles `background: rgba(45,212,191,0.14)`, `border: 1px solid rgba(45,212,191,0.45)`, and `#99f6e4` numerals.

#### 5. Audit and repair syllabus numbering, duration math, item icons, and the "skipped Step 4" state
* **Screenshots:** `#3, #4, #5, #22, #24, #34`.
* **Problem:**
  * On Full Home (`#5`), **Module 3 starts at Lesson `2`** (`Logistic regression`)—Lesson `1` is missing, while the progress card claims `31 lessons` (and your product brief says `37`).
  * Module header durations contradict their rows: `MODULE 2 · 8 MIN` lists a `5 min` lesson, a `20 min` lab, and a `10 min` case file (`35 min` total, `5 min` video); `MODULE 1 · 41 MIN` lists five `5 min` lessons + a `10 min` case file (`35 min`), while the `NEXT UP` card says Lesson 4 is `about 8 min with questions`.
  * Labs use an invisible `2px` dot `[·]` (`#5`) or a video play icon `[▷]` (`#24`), and Case files use `[?]`, which reads as a broken glyph or help tooltip.
  * Inside completed Lesson 1 (`#3, #22, #34`), `4 Explain` remains an un-checked grey numbered pill between `✓ Check` and `✓ Take away`, making finished lessons look incomplete because nothing signals `Explain` is optional.
* **Exact fix:**
  * Renumber Module 3 sequentially (`1` through `4`) or restore missing Lesson `3-1`, and reconcile the `31` vs `37` count everywhere (`Home`, `Field guide`).
  * Make row durations and module headers add up identically: show total expected lesson time on each row (`8 min` instead of video-only `5 min`), sum all items accurately in the module header (e.g., `MODULE 2 · 38 MIN`), or write `MODULE 2 · 1 LESSON, 1 LAB, 1 CASE`.
  * Replace `[·]` / `[▷]` on Labs with a `16px` code/prompt icon (`>_`) and `[?]` on Case files with a `16px` file-magnifying-glass / clipboard-audit icon (`28×28px` rounded-`6px` badge).
  * Move `Explain` after `Take away` (or remove its step number: `1 Guess · 2 Watch · 3 Check · 4 Take away` + a dashed-border pill `Explain · optional`), so completing the 4 core steps leaves a clean, unbroken row of checkmarks.

#### 6. Give Light Theme true "cool paper & green-black ink" contrast and separate "done" from "primary CTA"
* **Screenshots:** `#2, #6` (Light Home), `#9, #11, #17` (Light slides), `#24` (Light Practice).
* **Problem:** Light mode places `#ffffff` cards on a `#f8faf9` background (`< 2%` luminance delta), making pages look washed-out and clinical (`#24`). Worse, Light mode colors primary CTA buttons (`Continue`, `Start today's review`), completed lesson checkmarks (`✓`), the progress ring, and the 7-day bar in the **exact same dark pine green (`#0d6b5c`)**—conflating "already finished" with "click here next".
* **Exact fix:**
  * Darken the Light page background to cool surveyor's rag paper (`#ebf0ed`), keep cards crisp warm-cool white (`#fbfcfb`) with `1px solid #cdd7d2` borders (and `#dce4e0` subtle inner dividers), and set primary ink to `#0d1a17`, secondary ink to `#465953`.
  * Separate semantic roles: reserve rich survey-teal (`#0d7666` hover `#0a5f52`) strictly for interactive primary CTAs; render completed `✓` circles and progress fills in soft sage (`#dcebe6` fill, `#1f574c` check icon, no heavy solid dark-green discs) so `Continue` pops unmistakably against completed syllabus rows.

#### 7. Replace raw browser-default `<audio>` and `<details>` elements on `Drills` and `Field guide`
* **Screenshots:** `#26` (Field guide), `#28` (Recall drills).
* **Problem:** `Recall drills` (`#28`) drops a raw Chromium `<audio controls>` widget (`0:00 / 0:00` duration because metadata isn't preloaded, plus a native `⋮` download menu) and an unstyled `<details>` `▸ The 10 questions` triangle onto a bespoke dark page. `Field guide` (`#26`) uses raw `▸` `<summary>` triangles for unlocked briefs and dumps ~35 glossary entries into an endless single-column wall with 40% empty whitespace on the right side of the card.
* **Exact fix:**
  * **`Drills` (`#28`):** Build a dedicated audio card using your `Watch` player tokens: `44px` survey-teal play button, preloaded duration badge (`10 questions · 6 min 20 sec` visible before pressing play), `-15s` / `+15s` commuter skip buttons, custom hairline scrub bar, and a styled accordion row (`Show the 10 questions` with right-aligned chevron). Center the container at `max-width: 760px` (or pair unlocked modules in a 2-column grid).
  * **`Field guide` (`#26`):** Style `Briefs and checks` as full-width interactive rows (`padding: 14px 18px`, `border-bottom: 1px solid var(--border)`, mono badge `1·1`, title, right-aligned `▾` chevron), and add a collapsed row at the bottom (`+ 27 more unlock as you finish lessons`) to explain `4 of 31`. Convert the `Glossary` body into a 2-column card/entry grid (`grid-template-columns: repeat(2, minmax(0, 1fr))`, `gap: 20px 36px`) with sticky `A–Z` / `By module` filter pills under the search input.

#### 8. Fix clipped mobile navigation, mystery header icons, and mismatched audio-mode copy
* **Screenshots:** `#20, #29, #30, #32, #33, #34` (Phone at `390px`).
* **Problem:** On `390px` screens, the horizontal nav row clips `About` mid-letter (`ㅏ` in `#29, #32–#34`, or a stray `1px` dot in `#20`) with no scroll fade, silently renames `Field guide` to `Guide`, leaves an unlabeled green sync dot next to the moon icon, and in `#30` prints `"The ear button gives an audio-only second pass"` right underneath a **headphones (`🎧`)** icon.
* **Exact fix:**
  * Move `About` out of the mobile top tab bar (place it in a compact footer link or a logo/overflow popover) so the five working tabs—`Course`, `Review`, `Practice`, `Drills`, `Guide`—fit 100% inside `390px` (`padding: 6px 10px`, `font-size: 13px`, `gap: 4px`, no horizontal clipping).
  * Hide the lone green sync dot on mobile unless syncing fails/is in progress (show `Syncing…` / `Offline` pill only on state change), giving the theme toggle a clean `40×40px` tap target.
  * In `#30`, update copy to `"The headphones button switches to audio-only for a second pass."` and move `Show the transcript` alongside it as a compact utility bar directly under the player.

#### 9. Differentiate Case File artifacts from course UI, and center narrow single-task views on desktop
* **Screenshots:** `#21` (Check), `#23` (Review), `#25` (Case file `200 out of 200`), `#28` (Drills).
* **Problem:** In `200 out of 200` (`#25`), `churn_model_v1.html` uses the exact same dark surface, fonts, and KPI cards as Ground Truth itself, so the flawed "assistant's report" looks visually indistinguishable from authoritative course teaching; below it, the prompt asks two opposite questions at once (`"Would you forward this to the account team? Tick what you would send back."`) with a broken mid-sentence line wrap. Meanwhile, `Check` (`#21`), `Review` (`#23`), and `Drills` (`#28`) hug a `680px` column to the left edge of the layout, leaving a `440px` dead black void on the right (and stranding `Next question` far off in the bottom-right corner of `#21`).
* **Exact fix:**
  * **`Case file` (`#25`):** Frame `churn_model_v1.html` as an unmistakable external document: give it an elevated contrasting sheet (`#16201f` in dark mode with a `1px solid #2b3b38` frame and `#1e2b29` top document bar; crisp `#ffffff` paper with subtle drop shadow on `#ebf0ed` in light mode), add realistic report metadata (`Author: AI Assistant · Generated in 4m · Attachment: churn_model_v1.html`), and set report body slightly tighter (`14.5px`) so it reads as an artifact under inspection. Rewrite the audit header to: `"Audit this report. Tick every real problem you would send back to your assistant:"` and remove the hard `<br>` on the subtitle.
  * **`Check` (`#21`) & `Review` (`#23`):** Center single-task cards horizontally (`max-width: 720px; margin: 0 auto`). Keep `Next question` aligned to the right edge *of that `720px` column*, `20px` beneath the feedback box. Fix the pluralization bug in `#23` & `#32`: **`about 1 minutes`** → `about 1 minute`.

#### 10. Add front-door context on Sign-in and a collapsible first-visit map on Home
* **Screenshots:** `#1, #2` (Home), `#27` (About), `#35, #36` (Sign-in).
* **Problem:** Sign-in (`#35–#36`) is a generic passphrase box floating in an empty void with zero indication of what *Ground Truth* is. Once inside, a first-time learner gets no explanation of how a lesson's five parts work or how `Course`, `Review`, `Practice`, `Drills`, and `Field guide` relate (`Practice` isn't even mentioned in the Home right rail, and `About` (`#27`) explains the syllabus verification council but never explains how to use the site).
* **Exact fix:**
  * **Sign-in (`#35–#36`):** Add the topographic contour SVG delicately across the full viewport (`opacity: 0.06` dark / `0.10` light), widen the card to `400px` (`padding: 32px`), and replace `"This is a private course."` with `"Machine-learning fundamentals for working analysts — framing, directing, and auditing AI work. Enter your passphrase to open the field book."`
  * **First-visit Home banner + Right-rail parity:** Above Module 1 on first visit (dismissible into a quiet `How this course works` link), show a compact 3-step horizontal strip: `01 Lessons (8 min) — Guess, watch, check` · `02 Practice — Audit case files & run AI labs` · `03 Retention — 1-min daily Review & audio Drills`. Add a compact `Practice` card (`5 case files · 5 labs`) to the Home right rail above `On the move?` so all four companion modes are introduced on Home.

---

### 3. Everything Else (Grouped by Screen)

#### Global Navigation & Typography (`#1–#34`)
* **RGB green clashes with survey-teal (`#1, #5, #22`):** The `• Synced` dot and the 7th segment of `LAST 7 DAYS` use bright grass-green (`#22c55e`), which clashes visibly against the cyan-leaning survey-teal (`#2dd4bf`) primary button right below it → Shift both to your survey-teal (`#2dd4bf` dark / `#0d7666` light) so the accent palette stays strictly two-tone (survey-teal + warm amber).
* **Active `Review` pill badge contrast (`#23, #32`):** When `Review` is active, the bright amber `2` circle sits directly on an off-white `#edf2f0` pill with weak edge definition → Add a `1px solid rgba(0,0,0,0.12)` ring or switch the badge inside an active light pill to dark ink `#0f1715` text on `#fbbf24`.
* **Spaced ASCII hyphens in prose (`#1, #25, #27`):** Copy uses spaced hyphens (`in one place - and one file`, `Not every item is one - knowing`, `Claude agents - one playing`) alongside British spelling (`modelling`, `memorising`, `sceptical`) → Replace all ` - ` with proper spaced en-dashes ` – `.

#### Course Home & Syllabus (`#1, #2, #5, #6, #20, #33`)
* **Unlabeled `LAST 7 DAYS` segments (`#1, #5`):** Seven thin grey/green dashes have no day labels and don't explain what lights a segment up → Add `10px` `JetBrains Mono` single-letter day initials (`T F S S M T W`) underneath and a `title` / sublabel (`Active days (last 7)`).
* **Out-of-order completion state in Module 5 (`#5`):** `The best-practices playbook` shows a green `✓` while Lessons `1–6` above it are untouched and the module's top-right progress bar reads `0%` → Include Case files/Labs in the module progress bar calculation, or visually separate `Practice` items under a subtle sub-divider (`PRACTICE FOR MODULE 5`) at the bottom of each module card.
* **Barely visible contour graphic in Dark Mode (`#1, #5`):** The topographic lines in `NEXT UP` are clearly legible in Light mode (`#2, #6`) but nearly invisible (`~2–3%` contrast) in Dark mode → Bump stroke opacity in Dark mode from `~0.04` to `0.09` (`stroke: #2dd4bf` or `#3b524d`).

#### Watch Player & Slides (`#4, #7–#19, #29, #30`)
* **Redundant blurred poster (`#4`):** Blurring the title slide behind an overlay that repeats the exact same title (`From rules to learned models` on top of blurred `From rules to learned models`) creates visual mush → Render the unblurred title slide cleanly and place a compact pill button (`▶ Play lesson · 5 min`) below the subtitle instead of a giant frosted-glass overlay.
* **`+14 MORE` table column (`#9`):** `+14 MORE` with `...` looks weight-equal to real feature columns → Style that column header and `...` cells in muted `#8a9994` at `width: 80px` so it reads immediately as an elided schema indicator.
* **Tight touch targets on mobile transport chevrons (`#30`):** Previous/Next slide chevrons (`<` `>`) sit tightly beside the `48px` white Play circle → Give `<` and `>` `40×40px` hit boxes with `8px` spacing so thumbs never skip a slide while trying to pause.

#### Check & Review Questions (`#21, #23, #31, #32`)
* **Generic `Not quite.` copy (`#21, #31`):** Selecting wrong option `A` displays a canned paragraph explaining why `C` is right without addressing `A`'s specific flaw → Either add one sentence addressing the chosen distractor, or change the callout heading from `Not quite.` to `Not quite — why C is right` with a `2px` coral/amber left accent bar.
* **Missing keyboard affordances (`#21, #23`):** `Watch` advertises keyboard shortcuts (`space`, `arrows`), while `Check` and `Review` don't → Allow `1–4` / `A–D` to select an option and `Enter` / `Space` to advance, and show a subtle `Press A–D to answer` hint in `12px` muted text on desktop.

#### Lesson Take-away (`#3, #22, #34`)
* **Three distinct blocks crammed into one left-hand card (`#22`):** `Ask your assistant`, `Before you believe what comes back`, and `New words` sit inside a single card container with tight `20px` gaps, making `New words` look like part of the AI prompt checklist → Split `New words` into its own full-width card (2-column definition grid) above `Stuck? Ask your tutor`, and place a `1px solid var(--border)` divider + `24px` spacing between `Ask your assistant` and `Before you believe what comes back`.
* **Competing `Ask Claude` button (`#22`):** `Ask Claude` uses the primary solid survey-teal button style, competing with `Next: Which kind of problem is this?` → Demote `Ask Claude` to an outlined secondary button (`border: 1px solid var(--border-strong)`, transparent background, `#d8e0dd` text).

#### About (`#27`)
* **Overly wide reading measure (`#27`):** Paragraphs span `~960px` (`~115–125` characters per line), making dense prose tiring to scan → Constrain prose column to `max-width: 65ch` (`~620px`) on the left and place a `JetBrains Mono` **Colophon / Verification Specs** box on the right (`31 lessons · 5 labs · 5 case files · Simulated via Python & scikit-learn · Checked automatically against pipeline output`).

---

### 4. What Already Works and Must Not Be Touched

* **The writing voice:** Direct, concrete, respectful, and completely free of edtech fluff (`"Your CASE WHEN is already most of a model"`, `"Matching the past proves nothing: what counts is new rows"`). Do not soften or gamify a single sentence.
* **The pedagogical loop and AI-audit framing:** Teaching an SQL-fluent analyst to *brief in stages and audit by evidence*—backed by copyable prompts, verification checklists, and flawed reports to inspect—is sharp product thinking.
* **The core typographic hierarchy and dark-mode ink palette:** `Bricolage Grotesque` headlines, `Inter` body text, and `JetBrains Mono` SQL/metrics over deep green-black (`#0b0f0e` / `#111716`) feel calm, technical, and grown-up.
* **Zero sidebar clutter inside lessons:** Keeping the syllabus rail off the screen while a learner is inside `Guess / Watch / Check` preserves focus.

---

### 5. One Idea for a Memorable Identity: "Benchmark Cards & Redline Audits"

Right now, the *surveyor's field book* concept stops at faint contour lines on one card and four tiny `┌ ┘` corner ticks on the slide stage; everything else could belong to any clean developer dashboard. Carry the metaphor into the **two core artifacts** of the course without adding a single ounce of childish gamification:

1. **Numbered Survey Benchmark Cards (`Take away` & `Field guide`):** Give every unlocked brief-and-audit checklist a ruled top datum header in `JetBrains Mono` (`BM 01·04  |  LEAKAGE & TEMPORAL JOINS  |  UNLOCKED`) with fine grid hairlines and a crisp geometric trig-point mark (`△`, echoing your logo) when its companion Practice check is passed. Over 31 lessons, the learner visibly assembles a numbered field manual rather than unlocking generic `<details>` rows.
2. **Redline Markup in Case Files (`Practice`):** Render the AI assistant's report (`churn_model_v1.html`) on a distinct light-paper/slate "submitted printout" with line numbers in the margin. When the learner ticks the real flaws and clicks `Check my audit`, draw crisp survey-orange **redline callouts and margin notes** directly onto the offending lines of the report above (circling `200 of 200` in the KPI header and `CURRENT_DATE - a.last_spend_date` in the SQL query). Marking up a flawed report in redline ink feels tactile, authoritative, and unmistakably *Ground Truth*.