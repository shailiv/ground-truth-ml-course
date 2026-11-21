const st = document.createElement('style'); st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}'; document.head.append(st);
const out = [];
for (const les of __gt.course.lessons) {
  location.hash = `#/lesson/${les.id}/watch`;
  await new Promise(r => setTimeout(r, 300));
  const pl = __gt.player; if (!pl) { out.push(les.id + ' no player'); continue; }
  for (let i = 0; i < pl.segments.length; i++) {
    await pl.show(i, false);
    document.querySelector('.overlay').hidden = true;
    document.querySelectorAll('.cue.off').forEach(e => e.classList.remove('off'));
    await new Promise(r => setTimeout(r, 40));      // no second fit: measure what playback's own fit (cues still hidden) produced
    const stage = document.querySelector('.stage').getBoundingClientRect();
    const slide = document.querySelector('.slide'), body = slide.querySelector('.s-body'), v = pl.segments[i].visual;
    let worst = 0, who = '';
    slide.querySelectorAll('*').forEach(el => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return; const d = Math.max(r.bottom - stage.bottom, r.right - stage.right, stage.left - r.left, stage.top - r.top); if (d > worst) { worst = d; who = (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || el.tagName; } });
    const clip = body ? body.scrollHeight - body.clientHeight : 0;
    const wrap = slide.querySelector('.tbl-wrap'), tclip = wrap ? Math.max(wrap.scrollHeight - wrap.clientHeight, wrap.scrollWidth - wrap.clientWidth) : 0;
    const small = [...slide.querySelectorAll('h2, p, li, td, th, span, b, text')].reduce((m, el) => { const f = parseFloat(getComputedStyle(el).fontSize) * (el.namespaceURI.includes('svg') ? (el.ownerSVGElement.getBoundingClientRect().width / el.ownerSVGElement.viewBox.baseVal.width || 1) : 1); return el.textContent.trim() && f < m ? f : m; }, 99);
    const fit = +(slide.style.getPropertyValue('--fit') || 1);
    if (worst > 2 || clip > 2 || tclip > 2 || small < 9.5 || fit < 0.85) out.push(`fit=${fit} ` + `${les.id}#${i} ${v.type}${v.name ? ':' + v.name : ''} out=${Math.round(worst)} clip=${clip} tbl=${tclip} minfont=${small.toFixed(1)} ${String(who).slice(0, 30)}`);
  }
}
return out;
