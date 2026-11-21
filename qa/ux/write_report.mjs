// Writes qa/ux/report.json from the findings of the learner walkthrough, then re-reads it to prove it parses.
import fs from "node:fs";
const S = (n) => `qa/ux/shots/${n}.png`;
const F = [];
const add = (kind, severity, where, shot, what, why, fix) => F.push({ id: "U" + (F.length + 1), kind, severity, where, screenshot: S(shot), what, why_it_matters: why, fix });

add("bug", "high", "every page, laptop + phone, both themes (css/app.css lines 111 and 497)", "c12-check-score-2of4",
  "A global rule `.ghost { visibility: hidden }` (and `display: none` at 640px and below) hides every secondary button built with the `btn ghost` class. Measured in the page: computed visibility is `hidden` on all of them. Invisible today: Home \"How this course was checked\" and the \"Got it\" that dismisses the how-it-works strip; Guess \"Skip the guess\"; player \"Start from the beginning\"; the four tutor shortcuts (\"Explain it differently\", \"Give me a harder example\", \"How would this go wrong on real data?\", \"Quiz me on this\") on every lesson and lab; Check \"Skip to the take-aways\"; Explain \"Skip\" and \"Have Claude grade it\"; Take away and case file \"Course map\"; Review \"Rewatch the lesson\"; Settings \"Start over\" and \"Sign out\". On laptop they still take up room, so cards show blank bands (how-it-works strip, every tutor box). The class was meant for one widget slider (widgets.js line 167).",
  "The quiet exits are gone. After the quiz the only visible button is the optional \"Explain it back\", the how-it-works strip can never be closed, the tutor shortcuts this learner would actually tap do not exist, and progress cannot be reset from Settings. A learner who is bored by padding has lost every skip.",
  "Delete both `.ghost` rules and rename the widget helper to something that cannot collide (for example `.wg-hide`, toggled in widgets.js:167). Then re-shoot Home, a score banner, Explain, a tutor box and Settings.");

add("confusing", "high", "/#/ first visit, phone 390x844 and tablet 820x1100, both themes", "a06-home-phone-dark",
  "Below 980px the four-part how-it-works strip is laid out above the hero. The whole first phone screen is \"01 Lessons / 02 Review and drills / 03 Practice / 04 Field guide\"; the headline, the pitch and \"Begin lesson 1\" start on the second screen (the button is about 1,020px down). Because its \"Got it\" button is hidden (U1) the strip also sits above \"Continue\" on later visits until two lessons are done (f12-p-home-after-one.png).",
  "On the phone, the first thing a new learner sees is a list of features with nothing to press and no statement of what the site is. That is the opposite of \"obvious what to do first\".",
  "In the one-column layout put the hero first and the strip second (`.howto { order: 2 }` and shift the rest), or fold the strip into the hero as a single line. Make the dismissal work.");

add("bug", "medium", "/#/lesson/1-1/watch, phone 390x844, dark", "e03-p-watch-arrive",
  "On the opening slide the big play button is drawn on top of the slide's subtitle: \"Your CASE WHEN is already most of a\" is readable and the second line (\"model\") is under the button. The hint beside it says \"space pauses, arrows move between parts\", which means nothing on a phone.",
  "This is the first frame of every lesson on the phone and it looks broken before a single second has played.",
  "On narrow screens reserve room under the title slide for the play row (or hide the subtitle until playback starts), and show the keyboard hint only when a fine pointer is present.");

add("ugly", "medium", "/#/lesson/1-1/watch with CC on, laptop 1366x768 and phone, dark", "e06-p-slide2-table-cc",
  "Captions are overlaid on the slide content. On the phone table slide the caption box covers the slide's own note and touches the last table row; on the laptop (b08-slide2.png) it covers the second line of the note (\"Simulated data.\").",
  "This learner will watch on a phone with the sound low and captions on. The caption hides exactly the line that explains the table.",
  "Give captions their own band between the stage and the controls, or add bottom padding to the slide while captions are on.");

add("confusing", "medium", "/#/lesson/1-1/check after answering, phone 390x844 (also laptop)", "f02-p-check-q1-wrong",
  "After an answer the page jumps down to bring \"Next question\" into view (scrollY 769 on the phone). The feedback says \"Not quite. The answer is marked in green.\" but both the green and the red option are now off-screen above; only two unmarked options are visible. On the laptop the same jump slides the first lines of the question under the sticky header (c10-check-q2-wrong.png).",
  "The one moment the learner most wants to compare their pick with the right one, the page hides both.",
  "Do not scroll on answer; if the button must be reachable, scroll the feedback box with `block: 'nearest'`. On phones repeat the right answer in the feedback (\"Answer: A - ...\").");

add("confusing", "medium", "lesson steps, any viewport", "m05-back-between-steps",
  "Step changes rewrite the URL with replaceState. Going Guess -> Watch -> Check and then pressing the browser's back button lands on the course home (`#/`), not on Watch.",
  "On a phone the back gesture is the natural way to return to the video. It throws the learner out of the lesson instead.",
  "Push a history entry per step and switch steps on hashchange, so back walks Check -> Watch -> Guess -> Home.");

add("bug", "medium", "/#/lesson/1-1/check, laptop 1366x768", "m07-check-after-reload",
  "Quiz progress lives only in memory. Reloading at question 3 of 4 returns to question 1 with nothing saved; so does tapping the Watch tab to re-check something and coming back. There is no warning either way.",
  "A learner on the move gets interrupted. Losing three answered questions, or being punished for looking back at the slide, is the kind of friction that ends a session.",
  "Keep the current index and answers in the lesson record (or sessionStorage) and resume; store by question index, since the option order is reshuffled on each render.");

add("bug", "medium", "/#/review, laptop 1366x768, dark", "h10-review-finish",
  "The amber count next to \"Review\" is only refreshed on navigation. It stays at 10 while cards are answered, and on the finish screen (\"0 of 8 right\", nothing left today) it still reads 8.",
  "The badge is the site's daily call to action. Showing 8 due right after finishing tells the learner the session did not count.",
  "Recompute the badge after every answer (the store already emits on change) and when the queue ends.");

add("copy", "medium", "/#/ sidebar, laptop + phone", "d09-home-after-one",
  "Three untrue lines in the review card. (1) After finishing the first lesson, with \"2 ideas in rotation\" shown beside it, it still says \"Review cards appear here after your first lesson.\" (2) After hitting the daily cap with 8 cards still due it says \"0 cards to review today / Nothing due today.\" (h12-home-after-review.png). (3) With the next card five days away it says \"Come back tomorrow.\" (n03-home-finished-laptop.png). The Review page itself gets all three right.",
  "The learner comes back the next day to find out what is due. Wrong answers here teach them to ignore the panel.",
  "Reuse the Review page's logic: \"First cards come back tomorrow\", \"Next cards due Sunday 22 Nov\", and \"Today's 10 done, 8 more waiting - do 6 more?\" when capped.");

add("confusing", "medium", "/#/drills with lessons 1-1 to 1-3 finished", "j09-drills-playing",
  "The page says drills are \"drawn from lessons you have finished\", and a drill unlocks after any one lesson in its module. The audio is one fixed file per module: with three of five lessons done, the Module 1 drill asks \"What is leakage...\", \"What is the time-travel test for a feature?\" and \"What goes into the audit block...\" - lessons 1-4 and 1-5.",
  "Being quizzed aloud on a commute about things not yet taught feels like the course is broken, or like the learner forgot something they never saw.",
  "Unlock a drill when its module is finished, or say \"covers all 5 lessons of the module\" and mark which questions come from lessons still ahead, or cut the audio per lesson.");

add("ugly", "medium", "tables on phone 390x844: lesson slide and case-file report", "i10-case-phone-report",
  "Table cells break in the middle of words. Case report: header \"RAN/K\", \"days_since_last_spen/d\", \"snapshot_feature/s\". Lesson slide (e06-p-slide2-table-cc.png): header \"ADVE/RTISE/R\", \"+14 MOR/E\", advertiser ids split as \"1000/02\".",
  "Column names and ids are the content an analyst reads first; split identifiers look like a rendering fault and are hard to scan.",
  "Drop `overflow-wrap: anywhere` on headers and identifier cells, keep them `nowrap`, and let the table scroll sideways inside its wrapper (or shorten headers on narrow screens).");

add("ugly", "medium", "/#/lesson/4-1/watch widget part after narration ends, laptop + phone", "g06-w41-phone-ended",
  "When the narration of a widget part ends, the \"Done exploring - continue\" pill appears on top of the widget's own instruction note, hiding the middle of the sentence. Same on laptop (g04-w41-ended-continue.png).",
  "The note tells the learner what to try with the slider; the button covers it at the exact moment they are invited to explore.",
  "Place the continue button in the control bar (or under the note with reserved space) instead of floating it over the slide.");

add("confusing", "medium", "/#/lesson/1-1/check score banner, laptop + phone", "c12-check-score-2of4",
  "The banner is \"2 of 4.\" with one button, \"Explain it back (30 seconds)\". Nothing shows which two were missed, there is no retry, and the \"Take away\" tab is already ticked although it has not been opened. The step the tabs call optional is the only way forward that is offered.",
  "The learner wants to know what they got wrong and to move on. They get a number, and a nudge into the one step marked optional.",
  "List the missed questions with their one-line reason and a \"rewatch that part\" link; make \"See the take-aways\" the primary button and \"Explain it back (optional, 30 s)\" the secondary; tick Take away when it is visited.");

add("confusing", "medium", "/#/case/c1 after \"Check my audit\", laptop 1366x768", "i06-case-judged-result",
  "The page scrolls so the result heading (\"2 of 6 judged correctly\" and \"The numbered marks on the report above show where each real problem lives\") is under the sticky header; the first thing visible is item 1. The red marks are about 1,000px up, so a mark and its explanation are never on screen together, and reading the report top to bottom the marks run 3, 2, 1 (i07-case-judged-redline-report.png).",
  "The red-pen report is the best moment on the site, and the learner has to discover it by scrolling back up after missing their own score.",
  "Add scroll-margin-top to the result block, make each numbered badge a link that jumps to its mark (and back), and number marks in document order.");

add("missing", "medium", "/#/drills, laptop + phone", "j10-drills-phone",
  "The drill player has play, a scrub bar and 15-second skips, but no speed control and no way to jump to the next or previous question. The lesson player offers 0.85x to 2x.",
  "This learner listens fast and forgets fast: replaying one question, or running the drill at 1.5x, is the whole use case for audio on the move.",
  "Reuse the lesson player's speed chip (and remember the setting), and add previous/next question using the per-question timings.");

add("confusing", "low", "/#/lesson/1-1/watch, phone on its side 844x390", "m12-watch-phone-landscape",
  "In landscape the header, breadcrumb, title and step tabs take the first 200px of a 390px window; the stage starts below that and its control bar ends 330px past the bottom edge. Nothing of the slide content is visible on arrival.",
  "Turning the phone sideways is what people do to watch a video. Here it shows less.",
  "On short, wide viewports collapse the lesson header while watching, or scroll the stage to the top and offer full screen.");

add("copy", "low", "/#/lesson/1-1/watch resume overlay, laptop 1366x768", "c04-resume-overlay",
  "Returning to a half-watched lesson shows \"Pick up at part 8 of 9\" with \"Continue - 5 min\" although about one minute is left (3:53 of 4:58).",
  "A learner deciding whether they have time reads \"5 min\" and may put it off.",
  "Show the time remaining (\"about 1 min left\").");

add("ugly", "low", "copy boxes on phone: take-away, lab stages, field guide", "f09-p-take-s2",
  "The Copy button reserves a blank column down the full height of the brief, so the text runs in a strip about 60 percent of the card width (25 lines for one brief). Same in labs (j07-lab-phone-stage.png) and the field guide (k06-guide-phone-s2.png).",
  "The briefs are the take-home value of each lesson; on the phone they are the longest, emptiest thing on the page.",
  "On narrow screens put the Copy button on its own row above or below the text and drop the right padding.");

add("ugly", "low", "\"New words\" on the take-away page and the glossary grid, laptop", "k07-guide-laptop-light-gloss",
  "Entries in the same row are stretched to equal height by spreading the gaps, so the space between a term, its definition and its lesson link differs from one neighbour to the next (compare \"anomaly\" with \"anomaly detection\", or \"model\" with \"feature\" in d07-take-bottom.png).",
  "It reads as slightly off rather than wrong, but it is on two pages the learner returns to.",
  "Set `align-content: start` on the entries so gaps stay fixed and the spare height falls at the bottom.");

add("ugly", "low", "/#/ course map, phone 390x844", "a08-home-phone-dark-s3",
  "Every lesson's subtitle is cut to one line with an ellipsis: \"What does a model do that your CASE ...\", \"Five requests in one week: are they all ...\", \"When does a model's result actually c...\". Minutes per lesson are also dropped on the phone.",
  "The subtitle is the hook question for each lesson; on the phone none of them can be read, and the learner cannot see how long a lesson is before opening it.",
  "Allow two lines (line-clamp: 2) and keep the minutes, for example after the title.");

add("copy", "low", "/#/ sidebar and /#/guide", "k02-guide-unlocked-open",
  "Unexplained labels: \"ideas in rotation\" on the home page, and \"BM 1-1\" in front of each unlocked brief in the field guide.",
  "A first-time visitor has to guess; \"BM\" in particular looks like a code that should mean something.",
  "Say \"ideas under review\" and \"Lesson 1-1\" (or explain the bench-mark idea once).");

add("missing", "low", "/#/guide glossary search, laptop", "k04-guide-glossary-nomatch",
  "Searching for a term that is not in the glossary leaves an empty panel under the search box: no \"no match\" line and no suggestion.",
  "The learner cannot tell whether the search is broken or the term is absent.",
  "Show \"No term matches zzzz\" with a link to ask the tutor.");

add("confusing", "low", "/#/settings and header, laptop + phone", "k10-settings-laptop",
  "Settings is the last block of the About page, reachable only from a small footer link; on `/#/settings` no navigation item is highlighted. The theme switch lives separately in the header and shows a moon in both themes. Two of the settings (Start over, Sign out) are invisible because of U1.",
  "The brief lists theme, daily cap, tutor link, export, reset and sign out; a learner looking for \"reset\" will not find it, and has to know that settings sit under \"How this course was built\".",
  "Give Settings its own short page with the theme choice in it, a gear in the header, and a sun/moon icon that reflects the current theme.");

add("missing", "low", "/#/ first visit, laptop 1366x768", "a01-home-laptop-dark",
  "The home page gives minutes per lesson and per module but never the total or a pace. The About page knows it is 200 minutes of narration for 37 lessons.",
  "\"How long does this take?\" is the first question of someone with a few hours a week.",
  "Add one line to the hero, for example \"About 5 hours of lessons in all; one a day finishes in five weeks.\"");

add("confusing", "low", "/#/lesson/1-1/explain, laptop + phone", "f07-p-explain-shown",
  "After \"Show a strong answer\" the same button stays lit and active, and the way on is three small outline buttons that wrap on the phone as \"How close were you? [Missed it]\" / \"[Partly] [Nailed it]\". Nothing says that rating yourself moves you on.",
  "The page looks finished with no next step; the learner hunts for a Continue.",
  "Replace the reveal button with the rating once shown, as one full-width three-way control labelled \"Rate yourself to continue\".");

add("a11y", "low", "lesson player, any viewport (js/player.js key handler)", "b05-watch-playing-6s",
  "The scrub bar is focusable and announced as a slider, but arrow keys on it do nothing (the key handler ignores events from `[role=slider]`) and it has no value text. The step tabs carry role=tab without arrow-key movement or a tab panel. The speed button only cycles upward: from 1.15x back to 1x is six presses.",
  "Keyboard and screen-reader users cannot seek; everyone overshoots the speed they want.",
  "Handle Left/Right/Home/End on the scrub bar and set aria-valuetext; either implement the tabs pattern fully or use plain buttons with aria-current; make speed a small menu or add Shift-click to step down.");

add("ugly", "low", "/#/lesson/1-1/watch stat slide, phone 390x844", "e07-p-slide3-stat",
  "Three figures are laid out two-and-one: \"0.886\" and \"5 of 28\" share a row, \"Churned\" sits alone underneath, and the lower third of the frame is empty.",
  "The slide's point is the contrast between the three; the layout separates the punchline from its evidence.",
  "Stack three figures in one column on the phone, or keep three narrow columns.");

add("missing", "low", "/#/ with every lesson and practice file finished; /#/lesson/7-5/take", "n03-home-finished-laptop",
  "Finishing the course ends on a take-away page whose button is \"Back to the course\". Home then says \"You have finished every lesson\" and offers \"Practice files\" even when all ten are ticked.",
  "Thirty-seven lessons deserve an ending, and the learner needs to know what the site is for from now on.",
  "Add a closing card: what you can now do, your weakest ideas from review, the assistant pack, and the review schedule ahead. Offer \"Practice files\" only while some are open.");

add("ugly", "low", "/#/lesson/1-1 guess step, phone 390x844", "e01-p-guess-before",
  "The small capitals line \"BEFORE YOU WATCH - NO PENALTY FOR A WRONG GUESS\" wraps to two lines with no leading, so the lines almost touch.",
  "Minor, but it is the first line of every lesson on the phone.",
  "Give eyebrow text a line-height of about 1.4 when it can wrap, or shorten it to \"Before you watch\".");

add("confusing", "low", "/#/guide and the downloaded data/assistant-pack.md", "k01-guide-laptop",
  "The field guide says briefs \"unlock\" as lessons are finished (3 of 37 here), yet the assistant pack it offers already contains all 37 lessons' briefs and checks: 523 lines, 45 KB. The opening (\"How we work\", six rules, and the nine-step path) is excellent standing instruction; the other 480 lines are a per-lesson reference, including checks the learner cannot yet judge.",
  "Handed to an assistant as \"standing instructions\", it is long enough to crowd a chat, and it makes the on-site unlocking feel like decoration.",
  "Offer two files: a one-page core (rules + path) to paste or pin, and the full reference. Add a version date. Say on the page that the pack is complete from day one.");

add("confusing", "low", "/#/lesson/4-1/watch \"depth\" widget, laptop vs phone", "g01-w41-laptop-dark",
  "The x axis shows the twelve depths tried at equal spacing, so 1, 3, 5, 8, 12, 20 on the laptop and 1, 4, 8, 15, 25 on the phone look like a linear scale.",
  "An analyst reads slope off an axis by habit; here the steep fall between \"8\" and \"12\" is partly an artefact of spacing.",
  "Label the axis \"depths tried (not to scale)\" or plot on a true scale, and use the same ticks at both sizes.");

add("copy", "low", "/#/lesson/9-9 and any missing route", "m01-lesson-missing",
  "A lesson that is not in the build shows only \"That page does not exist\" with a button home. Glossary entries link by lesson id, so a lesson withdrawn for editing leads here from the field guide.",
  "The learner cannot tell a typo from a lesson that is temporarily away.",
  "For lesson routes say \"Lesson 9-9 is not available right now\" and offer the next unfinished lesson.");

add("ugly", "low", "/#/about, laptop 1366x768, dark", "k08-about-laptop",
  "The page title \"How this course was built and checked\" is rendered in the muted body colour, unlike the full-strength title on every other page.",
  "Small inconsistency on the page a sceptical learner reads to decide whether to trust the course.",
  "Exclude headings from the `.prose` colour.");

const report = {
  findings: F,
  first_impression: "The sign-in card told me in one sentence what this is, which is more than most private tools manage. On the laptop the home page is calm and obvious: a headline that speaks to my job, one teal button, \"about 8 min with questions\", and a strip that explains the four parts. The first lesson won me over quickly: a guess before the video, a narrator who starts from my own CASE WHEN, slides that build in time with the voice, and four questions that are about judgement, not vocabulary. On my phone the same site opened on a list of four features with no title and no button, and the first lesson's play button sat on top of its own subtitle. Then small things kept catching: after the quiz the only button offered was the step labelled optional, the back gesture threw me out to the home page, the answer \"marked in green\" had scrolled off my screen, and there were blank gaps where buttons clearly used to be. The case file with its red-pen marks is the moment I would show a colleague. I would come back tomorrow, but I would be irritated twice before I got to the good part.",
  best_things: [
    "The guess-first step with \"A common guess.\" / \"Good instinct.\" feedback: it creates a reason to watch and never scolds.",
    "The lesson player: narration and slide build in step, segmented progress bar, a real time readout (0:05 of 4:58 after six seconds of play), captions, listening mode, speeds from 0.85x to 2x, and it fits a 1366x768 and a 1280x640 window without scrolling.",
    "The widgets in 2-3 and 4-1: one slider, live counts beside the chart, and a note that says what to look for. They work at phone width too.",
    "Case files: the report as a paper document labelled \"written by your assistant - not checked by anyone\", and the numbered red marks after the audit. \"Two reports, one model\" is a strong five-minute start.",
    "Quiz explanations say why the tempting wrong answers are wrong, and review cards re-ask the idea in a different business setting.",
    "The take-away page: three lines to keep, a brief to paste, what the output must show before you believe it, where else it applies.",
    "Honest framing throughout: simulated data and why, \"what not to conclude\", a colophon with counts, and a sync indicator that says where progress is kept.",
    "Both themes are finished and consistent; the contour motif, the amber \"you are here\" marker and the amber review button give it an identity.",
    "The home page the next day: \"Next up\" with an in-progress pill, an amber \"Review 10 cards - about 5 min\", and the seven-day strip.",
    "Custom drill player in the site's own style, with the questions readable underneath.",
  ],
  verdict: {
    pretty: 8,
    engaging: 7,
    not_confusing: 6,
    why: "On a laptop this is a good-looking, well-paced course with a clear identity, and the lesson loop (guess, watch, check) is short enough to finish in one sitting. One CSS rule hides every secondary button on the site, which removes the skips, the tutor shortcuts, the strip's dismissal and two settings, and leaves blank bands in cards; that single fault is behind much of the confusion score. The phone is the weaker half: the first screen has no call to action, the play button covers the subtitle, captions and the continue pill sit on slide content, and tables split words. State handling is thin in places a returning learner will notice: back leaves the lesson, a reload restarts the quiz, the review badge and the home review card say things that are not true. Fix the first five findings and I would score it 8 / 8 / 8.",
  },
  method: {
    build_tested: "site files as of 2026-11-21 23:50 local (after the design pass); 37 lessons in the build",
    how: "13 scenario files of 12 shots each, run one at a time through build/shots_once.sh; 156 screenshots in qa/ux/shots. Whole-lesson walkthrough on 1-1 (laptop and phone), widgets on 4-1 and 2-3, next-day state with 18 due cards, case c1, lab l1, drills, field guide, about/settings, login, edge routes, all-finished state.",
    not_covered: "Widgets in modules 5 to 7 and lesson 3-3 were not re-shot after the design pass (those lessons were being edited). Full screen, the real clipboard and the Claude tab cannot be exercised headless; the tutor link was checked by capturing the URL it would open (claude.ai/new?q=..., 1,308 characters). The harness's phone emulation does not report a touch-only pointer, so hints the CSS hides on touch devices were not counted as findings.",
  },
};
fs.writeFileSync("qa/ux/report.json", JSON.stringify(report, null, 1));
const back = JSON.parse(fs.readFileSync("qa/ux/report.json", "utf8"));
const sev = {};
back.findings.forEach((f) => (sev[f.severity] = (sev[f.severity] || 0) + 1));
const missing = back.findings.filter((f) => !fs.existsSync(f.screenshot)).map((f) => f.id + " " + f.screenshot);
const named = [...JSON.stringify(back).matchAll(/([a-n]\d{2,3}-[a-z0-9-]+)\.png/g)].map((m) => m[1]).filter((n) => !fs.existsSync(S(n)));
console.log("parsed ok:", back.findings.length, "findings", JSON.stringify(sev), "| missing screenshot fields:", missing, "| missing shots named in text:", [...new Set(named)]);
