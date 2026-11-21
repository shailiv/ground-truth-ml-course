// The lesson player: one visual per segment, built in step with the narration.
// Works with real audio, and falls back to a silent clock (reading pace) when a clip is missing.
import { h, renderVisual, applyCues } from "./visuals.js";

const SPEEDS = [0.85, 1, 1.15, 1.3, 1.5, 1.75, 2];
const ICON = {
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>',
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="5.5" y="4" width="4.5" height="16" rx="1.2"/><rect x="14" y="4" width="4.5" height="16" rx="1.2"/></svg>',
  prev: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>',
  next: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>',
  full: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V5h4M20 9V5h-4M4 15v4h4M20 15v4h-4"/></svg>',
  ear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4.5" height="6" rx="1.5"/><rect x="16.5" y="14" width="4.5" height="6" rx="1.5"/></svg>',
};
const svgBtn = (cls, label, svg, onclick) => { const b = h("button", { class: cls, type: "button", "aria-label": label, title: label, onclick }); b.innerHTML = svg; return b; };

/** Split a narration into its spoken text, cue points (as fractions of the text) and sentences. */
export function parseNarration(raw) {
  const cues = [];
  let spoken = "";
  for (const part of raw.split(/(\[\[\d+\]\])/)) {
    const m = part.match(/^\[\[(\d+)\]\]$/);
    if (m) cues.push({ n: +m[1], at: spoken.length });
    else spoken += part.replace(/\s+/g, " ");
  }
  spoken = spoken.trim();
  const total = spoken.length || 1, sentences = [];
  let pos = 0;
  for (const sn of spoken.match(/.*?[.!?]+["')\]]*(?=\s|$)\s*|.+$/g) || [spoken]) { sentences.push({ text: sn.trim(), from: pos / total, to: (pos + sn.length) / total }); pos += sn.length; }
  return { spoken, cues: cues.map((c) => ({ n: c.n, at: c.at / total })), sentences, words: spoken.split(/\s+/).length };
}

export class Player {
  /** segments: [{ narration, visual, src?, dur?, label? }] */
  constructor(mount, { segments, title, startAt = 0, ctx = {}, prefs, onSegment, onComplete }) {
    Object.assign(this, { segments, title, ctx, prefs, onSegment, onComplete });
    this.parsed = segments.map((s) => parseNarration(s.narration));
    this.durs = segments.map((s, i) => s.dur || Math.max(6, this.parsed[i].words / 2.55));
    this.total = this.durs.reduce((a, b) => a + b, 0);
    this.i = Math.min(Math.max(0, startAt), segments.length - 1);
    this.playing = false; this.silent = false; this.t = 0; this.token = 0;
    this.rate = prefs.get("speed") || 1; this.captions = !!prefs.get("captions"); this.listen = !!prefs.get("listen");
    this.audio = new Audio(); this.audio.preload = "auto";
    this.audio.addEventListener("timeupdate", () => { if (!this.silent) this.tick(this.audio.currentTime); });
    this.audio.addEventListener("ended", () => this.segmentEnded());
    this.audio.addEventListener("error", () => { if (!this.dead && this.audio.error && this.audio.getAttribute("src")) this.goSilent(); });
    this.build(mount);
    this.initial = true;                      // the first show is the page opening, not the learner moving
    this.show(this.i, false);
    this.onKey = (e) => this.key(e);
    addEventListener("keydown", this.onKey);
  }

  build(mount) {
    this.stage = h("div", { class: "stage" });
    this.host = h("div", { class: "slide-host" });
    this.cap = h("div", { class: "cap-band", hidden: true, "aria-live": "off" }, (this.capText = h("span")));
    this.listenEl = h("div", { class: "listen paused", hidden: true }, h("div", { class: "box" },
      h("div", { class: "wave", "aria-hidden": "true" }, [1, 2, 3, 4, 5].map(() => h("i"))), h("div", { class: "eyebrow", text: "Listening mode" }),
      (this.listenTitle = h("h3")), h("p", { style: { color: "var(--ink-2)" }, text: "Visuals are off. Everything you need is in the audio." })));
    this.startOverlay = h("div", { class: "overlay", onclick: (e) => { if (!e.target.closest("button")) this.play(); } }, h("div", { class: "box" },
      svgBtn("bigplay", "Play", ICON.play, () => this.play()),
      this.i ? h("h3", { class: "resume", text: `Pick up at part ${this.i + 1} of ${this.segments.length}` }) : null,
      h("p", {}, this.i ? `Continue · about ${Math.max(1, Math.round(this.durs.slice(this.i).reduce((a, b) => a + b, 0) / 60))} min left` : `Play lesson · ${Math.round(this.total / 60)} min`,
        h("span", { class: "kbd-hint", text: " · space pauses, arrows move between parts" })),
      this.i ? h("button", { class: "btn small ghost", type: "button", text: "Start from the beginning", onclick: () => this.show(0, true) }) : null));
    this.moreEl = h("div", { class: "more-band", hidden: true }, h("span", { text: "Take your time with it." }),
      h("button", { class: "btn primary small", type: "button", text: "Done exploring: continue", onclick: () => this.afterWidget() }));
    this.stage.append(this.host, this.listenEl, this.startOverlay);
    this.btnPlay = svgBtn("play", "Play", ICON.play, () => this.toggle());
    this.rail = h("div", { class: "rail" }, this.durs.map((d) => h("i", { style: { width: `calc(${(d / this.total) * 100}% - 2px)` } })));
    this.scrub = h("div", { class: "scrub", role: "slider", tabindex: 0, "aria-label": "Lesson position", "aria-valuemin": 0, "aria-valuemax": Math.round(this.total) }, this.rail);
    const seek = (e) => { const r = this.scrub.getBoundingClientRect(); this.seekTotal(Math.max(0, Math.min(0.999, (e.clientX - r.left) / r.width)) * this.total); };
    this.scrub.addEventListener("pointerdown", (e) => { this.scrub.setPointerCapture(e.pointerId); seek(e); this.scrub.onpointermove = seek; });
    for (const t of ["pointerup", "pointercancel", "lostpointercapture"]) this.scrub.addEventListener(t, () => (this.scrub.onpointermove = null));
    this.scrub.addEventListener("keydown", (e) => {          // a slider must work from the keyboard
      const step = { ArrowRight: 5, ArrowLeft: -5, PageUp: 30, PageDown: -30 }[e.key], at = +this.scrub.getAttribute("aria-valuenow") || 0;
      if (e.key === "Home") this.seekTotal(0); else if (e.key === "End") this.seekTotal(this.total - 1);
      else if (step) this.seekTotal(Math.max(0, Math.min(this.total - 0.5, at + step))); else return;
      e.preventDefault();
    });
    this.noAudio = h("span", { class: "chip quiet", hidden: true, text: "No audio for this part: reading pace" });
    this.timeEl = h("span", { class: "time" });
    this.btnSpeed = h("button", { class: "chip", type: "button", title: "Playback speed", onclick: () => this.setRate(SPEEDS[(SPEEDS.indexOf(this.rate) + 1) % SPEEDS.length]) });
    this.btnCap = h("button", { class: "chip", type: "button", text: "CC", title: "Captions (c)", "aria-pressed": String(this.captions), onclick: () => this.setCaptions(!this.captions) });
    this.btnListen = svgBtn("icon-btn", "Listening mode: audio only", ICON.ear, () => this.setListen(!this.listen));
    this.controls = h("div", { class: "controls" },
      h("div", { class: "left" }, this.btnPlay, svgBtn("icon-btn", "Previous part", ICON.prev, () => this.prev()), svgBtn("icon-btn", "Next part", ICON.next, () => this.next(true))),
      this.scrub,
      h("div", { class: "right" }, this.noAudio, this.timeEl, this.btnSpeed, this.btnCap, this.btnListen, (this.btnFull = svgBtn("icon-btn", "Full screen (f)", ICON.full, () => this.fullscreen()))));
    this.wrap = h("div", { class: "stage-wrap" }, this.stage, this.cap, this.moreEl, this.controls);
    this.btnFull.hidden = !this.wrap.requestFullscreen;
    mount.replaceChildren(this.wrap);
    let rt = 0;
    this.ro = new ResizeObserver(() => { clearTimeout(rt); rt = setTimeout(() => this.fit(), 80); });
    this.ro.observe(this.stage);
    document.fonts?.ready.then(() => this.fit());
    this.setRate(this.rate, true); this.setListen(this.listen, true);
    if ("mediaSession" in navigator) {
      const ms = navigator.mediaSession;
      ms.setActionHandler("play", () => this.play()); ms.setActionHandler("pause", () => this.pause());
      ms.setActionHandler("previoustrack", () => this.prev()); ms.setActionHandler("nexttrack", () => this.next(true));
    }
  }

  async show(i, autoplay = this.playing, startAt = 0) {
    if (this.dead) return;
    const token = ++this.token;
    this.stopClock();
    this.audio.pause();                       // the old clip must not keep talking, or end and skip ahead, while the next slide is drawn
    this.i = i; this.t = 0; this.silent = false; this.moreEl.hidden = true; this.noAudio.hidden = true;
    const seg = this.segments[i];
    let slide;
    try { slide = await renderVisual(seg.visual, this.ctx); }
    catch { slide = h("section", { class: "slide t-quote" }, h("div", { class: "s-body" }, h("p", { class: "sub", text: "This part could not be drawn. The narration continues." }))); }
    if (token !== this.token || this.dead) return;
    this.host.replaceChildren(slide);
    this.slide = slide;
    this.hasCues = this.parsed[i].cues.length > 0;
    applyCues(this.slide, new Set(this.parsed[i].cues.map((c) => c.n)));
    this.fit();
    this.listenTitle.textContent = seg.label || seg.visual.title || this.title;
    if ("mediaSession" in navigator) navigator.mediaSession.metadata = new MediaMetadata({ title: seg.label || seg.visual.title || this.title, artist: "Ground Truth", album: this.title });
    if (seg.src) {
      this.audio.src = seg.src; this.audio.playbackRate = this.rate;
      if (startAt) this.audio.addEventListener("loadedmetadata", () => { if (token === this.token) this.audio.currentTime = Math.min(this.audio.duration - 0.2, (startAt / this.durs[i]) * this.audio.duration); }, { once: true });
    } else this.silent = true;
    const nx = this.segments[i + 1];
    if (nx?.src) { this.pre = new Audio(); this.pre.preload = "auto"; this.pre.src = nx.src; }
    this.tick(startAt);
    this.onSegment?.(i, this.initial);
    this.initial = false;
    if (autoplay || this.playing) this.play();   // Play pressed while the slide was being drawn still counts
  }

  play() {
    if (this.dead) return;
    if (!this.moreEl.hidden) return this.afterWidget();        // Play after exploring a widget means "go on", not "say it again"
    this.onPlay?.();
    this.startOverlay.hidden = true;
    this.playing = true;
    this.btnPlay.innerHTML = ICON.pause; this.btnPlay.setAttribute("aria-label", "Pause");
    this.listenEl.classList.remove("paused");
    if (this.silent) return this.startClock();
    this.audio.playbackRate = this.rate;
    const token = this.token;
    // a play() interrupted by Pause, Next or a seek rejects with AbortError: that is routine, not a missing clip
    this.audio.play().catch((e) => { if (token !== this.token || this.dead || e.name === "AbortError") return; if (e.name === "NotAllowedError") this.pause(); else this.goSilent(); });
  }
  afterWidget() { this.moreEl.hidden = true; if (this.i >= this.segments.length - 1) this.finish(); else this.show(this.i + 1, true); }
  finish() {
    this.pause(); this.tick(this.durs[this.i]);
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});       // the "that is the lesson" banner lives outside the stage
    if (!this.completed) { this.completed = true; this.onComplete?.(); }
  }
  pause() {
    this.playing = false;
    this.btnPlay.innerHTML = ICON.play; this.btnPlay.setAttribute("aria-label", "Play");
    this.listenEl.classList.add("paused");
    this.audio.pause(); this.stopClock();
  }
  toggle() { this.playing ? this.pause() : this.play(); }
  goSilent() { if (this.silent || this.dead) return; this.silent = true; this.noAudio.hidden = !this.segments[this.i].src; if (this.playing) this.startClock(); }
  startClock() {
    this.stopClock();
    let last = performance.now();
    this.clock = setInterval(() => {
      const now = performance.now(); this.t += ((now - last) / 1000) * this.rate; last = now;
      if (this.t >= this.durs[this.i]) { this.stopClock(); this.tick(this.durs[this.i]); this.segmentEnded(); } else this.tick(this.t);
    }, 120);
  }
  stopClock() { clearInterval(this.clock); this.clock = null; }

  tick(t) {
    this.t = t;
    const d = (!this.silent && this.audio.duration) || this.durs[this.i], f = Math.min(1, t / d), p = this.parsed[this.i];
    if (this.hasCues) applyCues(this.slide, new Set(p.cues.filter((c) => f < c.at - 0.015).map((c) => c.n)));
    const sn = p.sentences.find((x) => f >= x.from && f < x.to) || p.sentences.at(-1);
    if (this.captions && sn && this.capText.textContent !== sn.text) this.capText.textContent = sn.text;
    this.rail.childNodes.forEach((el, k) => el.style.setProperty("--f", k < this.i ? 1 : k === this.i ? f : 0));
    const before = this.durs.slice(0, this.i).reduce((a, b) => a + b, 0) + f * this.durs[this.i];
    this.timeEl.textContent = `${clock(before)} / ${clock(this.total)}`;
    this.scrub.setAttribute("aria-valuenow", Math.round(before));
    this.scrub.setAttribute("aria-valuetext", `${clock(before)} of ${clock(this.total)}`);
  }

  segmentEnded() {
    if (this.hasCues) applyCues(this.slide, new Set());
    if (this.segments[this.i].visual.type === "widget" && !this.listen) { this.pause(); this.moreEl.hidden = false; return; }
    this.next(false);
  }
  next(manual) {
    if (this.i >= this.segments.length - 1) return this.finish();
    const keep = this.playing || !manual ? true : false;
    this.show(this.i + 1, manual ? this.playing : keep);
  }
  prev() { if (this.t > 3 && !this.silent) { this.audio.currentTime = 0; this.tick(0); } else this.show(Math.max(0, this.i - 1)); }
  seekTotal(sec) {
    let acc = 0;
    for (let k = 0; k < this.durs.length; k++) {
      if (sec < acc + this.durs[k]) {
        const within = sec - acc;
        if (k !== this.i) return this.show(k, this.playing, within);
        return this.seekIn(within);
      }
      acc += this.durs[k];
    }
  }
  seekIn(within) {
    if (!this.silent && this.audio.readyState > 0) { const d = this.audio.duration || this.durs[this.i]; this.audio.currentTime = Math.min(d - 0.2, (within / this.durs[this.i]) * d); }
    this.t = within; this.tick(within);
  }
  setRate(r, quiet) { this.rate = r; this.audio.playbackRate = r; this.btnSpeed.textContent = `${r}×`; if (!quiet) this.prefs.set("speed", r); }
  setCaptions(on) { this.captions = on; this.cap.hidden = !on || this.listen; this.btnCap.setAttribute("aria-pressed", String(on)); this.prefs.set("captions", on); this.tick(this.t); }
  setListen(on, quiet) {
    this.listen = on; this.listenEl.hidden = !on; this.cap.hidden = !this.captions || on;
    this.btnListen.style.color = on ? "var(--accent)" : ""; this.btnListen.setAttribute("aria-pressed", String(on));
    if (on) this.moreEl.hidden = true;
    if (!quiet) this.prefs.set("listen", on);
  }
  fullscreen() { document.fullscreenElement ? document.exitFullscreen() : this.wrap.requestFullscreen?.().catch(() => {}); }
  key(e) {
    if (!(e.target instanceof Element) || e.repeat || e.target.closest("input, textarea, select, [contenteditable]") || e.metaKey || e.ctrlKey || e.altKey) return;
    if (!this.wrap.isConnected || this.dead) return;
    const k = e.key;
    if (k === " " && !e.target.closest("button, a, [role=slider]")) { e.preventDefault(); this.toggle(); }
    else if (k === "ArrowRight" && !e.target.closest("svg, [role=slider], .bar-row")) this.next(true);
    else if (k === "ArrowLeft" && !e.target.closest("svg, [role=slider], .bar-row")) this.prev();
    else if (k === "c") this.setCaptions(!this.captions);
    else if (k === "f") this.fullscreen();
  }
  // A slide is a fixed frame, like a video: if its content is taller than the frame, scale the type (and the charts with it)
  // down in small steps until it fits. On a phone the frame grows with the content instead, so there is nothing to do.
  fit() {
    const sl = this.slide;
    if (!sl) return;
    sl.style.removeProperty("--fit");
    sl.classList.add("measure");            // items waiting to be revealed sit half a line low; measure them where they will land
    try { this.fitNow(sl); } finally { sl.classList.remove("measure"); }
  }

  fitNow(sl) {
    // chart labels are drawn in the chart's own units; when a chart is shown small, scale them back up to a readable size
    const labels = () => sl.querySelectorAll("svg.plot").forEach((g) => { const k = g.getBoundingClientRect().width / (g.viewBox.baseVal.width || 1); if (k > 0) g.style.setProperty("--tk", Math.max(1, Math.min(1.3, 10.4 / (11 * k))).toFixed(2)); });
    if (getComputedStyle(sl).position !== "absolute") return labels();
    const body = sl.querySelector(".s-body");
    const over = () => (body && body.scrollHeight - body.clientHeight > 1) || sl.scrollHeight - sl.clientHeight > 1 || [...sl.querySelectorAll(".tbl-wrap:not([hidden])")].some((w) => w.scrollHeight - w.clientHeight > 1 || w.scrollWidth - w.clientWidth > 1);
    let f = 1;
    while (over() && f > 0.6) { f -= 0.04; sl.style.setProperty("--fit", f.toFixed(2)); }
    // ... and a slide that says little should not sit small in a big empty frame: scale it up until it holds the stage
    if (f === 1 && !sl.classList.contains("t-widget") && !sl.classList.contains("t-title") && sl.children.length) {
      const used = () => (sl.lastElementChild.getBoundingClientRect().bottom - sl.firstElementChild.getBoundingClientRect().top) / sl.clientHeight;
      const wide = () => [...sl.querySelectorAll(".s-body > *")].some((el) => el.scrollWidth - el.clientWidth > 1);
      while (used() < 0.52 && f < 1.34) {
        f += 0.04; sl.style.setProperty("--fit", f.toFixed(2));
        if (over() || wide() || used() > 0.7) { f -= 0.04; sl.style.setProperty("--fit", f.toFixed(2)); break; }
      }
    }
    labels();
  }

  destroy() {
    this.dead = true; this.token++;
    this.audio.pause(); this.stopClock(); this.audio.removeAttribute("src"); this.audio.load(); this.pre = null;
    removeEventListener("keydown", this.onKey); this.ro?.disconnect();
    if ("mediaSession" in navigator) {            // a headset button must not wake a lesson the learner has left
      for (const a of ["play", "pause", "previoustrack", "nexttrack"]) { try { navigator.mediaSession.setActionHandler(a, null); } catch { /* not supported */ } }
      navigator.mediaSession.metadata = null;
    }
  }
}

const clock = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
