// Step-by-step charts for the one-file HTML deck (inserted by slides/build_deck_html.py).
// Data: slides/interactive.json (slides/interactive_data.R). Each chart registers IX[slideId] = {steps, set(k), cues}.
// The deck's key handler moves through the steps before it moves to the next slide.
(function () {
  const D = JSON.parse(document.getElementById('ixdata').textContent);
  const NS = 'http://www.w3.org/2000/svg';
  const C = { ink: '#191f28', ink2: '#333d4b', muted: '#6b7684', grid: '#e5e8eb', red: '#f04452', blue: '#3182f6',
              light: '#90c2ff', grey: '#d1d6db', soft: '#b0b8c1' };
  const BAND_COL = [C.light, C.blue, C.red];
  const BAND_LAB = ['Below 20 m', '20-40 m', '40 m and above'];
  const FONT = "Inter, 'Noto Sans KR', 'Segoe UI', sans-serif";
  const pct = (v, d = 1) => (v * 100).toFixed(d) + '%';
  const IX = window.IX = {};

  function el(tag, at, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in at) n.setAttribute(k, at[k]);
    parent.appendChild(n);
    return n;
  }
  function txt(s, at, parent) { const n = el('text', at, parent); n.textContent = s; return n; }
  function makeSvg(box, W, H) {
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H }, box);
    svg.style.fontFamily = FONT;
    svg.style.overflow = 'visible';
    return svg;
  }
  function fade(n, on, t = 450) { n.style.transition = `opacity ${t}ms`; n.style.opacity = on ? 1 : 0; }
  function sideItems(id) { return [...document.querySelectorAll(`#${id} .side > *`)]; }
  function reveal(items, upto) { items.forEach((n, j) => fade(n, j < upto)); }
  function stop(n) { n.addEventListener('click', e => e.stopPropagation()); }
  function buttons(box, labels, onPick, at) {
    const bar = document.createElement('div');
    bar.style.cssText = `position:absolute;${at};display:flex;gap:8px;font:600 18px ${FONT};transition:opacity 400ms`;
    const bs = labels.map((l, j) => {
      const b = document.createElement('button');
      b.textContent = l;
      b.style.cssText = 'border:0;border-radius:999px;padding:8px 16px;cursor:pointer;font:inherit;';
      b.addEventListener('click', e => { e.stopPropagation(); onPick(j); });
      bar.appendChild(b);
      return b;
    });
    box.appendChild(bar);
    return {
      bar,
      pick(j) { bs.forEach((b, k) => { b.style.background = k === j ? C.blue : '#f2f4f6'; b.style.color = k === j ? '#fff' : C.ink2; }); },
    };
  }

  // ---------- slide 5: elevation, band by band, then the curve ----------
  (function () {
    const box = document.getElementById('ix-elev');
    if (!box) return;
    const E = D.elev, W = 1071, H = 600, L = 84, R = 24, T = 84, B = 84, XM = 80, YM = 0.92;
    const x = e => L + e / XM * (W - L - R), y = s => H - B - s / YM * (H - T - B);
    const svg = makeSvg(box, W, H);
    [0, .25, .5, .75].forEach(v => {
      el('line', { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: C.grid }, svg);
      txt(Math.round(v * 100) + '%', { x: L - 12, y: y(v) + 6, 'text-anchor': 'end', 'font-size': 17, fill: C.muted }, svg);
    });
    [0, 20, 40, 60, 80].forEach(v => txt(v, { x: x(v), y: H - B + 28, 'text-anchor': 'middle', 'font-size': 17, fill: C.muted }, svg));
    [20, 40].forEach(v => el('line', { x1: x(v), x2: x(v), y1: T - 20, y2: H - B, stroke: C.muted, 'stroke-dasharray': '6 5' }, svg));
    txt('Station elevation (m)', { x: (L + W - R) / 2, y: H - B + 58, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, svg);
    txt('Morning shortage (07-09 h)', { x: 0, y: 0, transform: `translate(26 ${(T + H - B) / 2}) rotate(-90)`,
      'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, svg);
    txt(`Each dot is one station. The ${E.n_above} stations above 80 m are left out: too few to smooth.`,
      { x: L, y: H - 6, 'font-size': 14, fill: C.muted }, svg);
    const band = e => (e < 20 ? 0 : e < 40 ? 1 : 2);
    const gs = [0, 1, 2].map(() => { const g = el('g', {}, svg); g.style.transition = 'fill 500ms, fill-opacity 500ms'; return g; });
    E.points.forEach(p => el('circle', { cx: x(p.e).toFixed(1), cy: y(p.s).toFixed(1), r: 3 }, gs[band(p.e)]));
    const span = [[0, 20], [20, 40], [40, 80]];
    const segs = E.bands.map((b, k) => {
      const g = el('g', {}, svg);
      el('line', { x1: x(span[k][0]) + 4, x2: x(span[k][1]) - 4, y1: y(b.v), y2: y(b.v), stroke: BAND_COL[k] === C.light ? '#5aa2ff' : BAND_COL[k],
        'stroke-width': 5, 'stroke-linecap': 'round' }, g);
      const lab = txt(pct(b.v), { x: (x(span[k][0]) + x(span[k][1])) / 2, y: y(b.v) - 14, 'text-anchor': 'middle',
        'font-size': 30, 'font-weight': 700, fill: k === 2 ? C.red : k === 1 ? C.blue : C.ink }, g);
      lab.setAttribute('paint-order', 'stroke'); lab.setAttribute('stroke', '#fff'); lab.setAttribute('stroke-width', 6);
      g.style.opacity = 0;
      return g;
    });
    const tops = E.bands.map((b, k) => {
      const g = el('g', {}, svg);
      const cx = (x(span[k][0]) + x(span[k][1])) / 2;
      txt(BAND_LAB[k], { x: cx, y: T - 46, 'text-anchor': 'middle', 'font-size': 18, fill: C.ink }, g);
      txt(b.n.toLocaleString('en') + ' stations', { x: cx, y: T - 22, 'text-anchor': 'middle', 'font-size': 18, fill: C.muted }, g);
      g.style.opacity = 0;
      return g;
    });
    const curve = el('path', { d: 'M' + E.curve.map(c => x(c.x).toFixed(1) + ',' + y(c.y).toFixed(1)).join('L'),
      fill: 'none', stroke: C.red, 'stroke-width': 4.5, 'stroke-linecap': 'round', pathLength: 1 }, svg);
    curve.style.strokeDasharray = 1; curve.style.strokeDashoffset = 1; curve.style.transition = 'stroke-dashoffset 1200ms ease-out';
    // hover, only on the last step
    const ring = el('circle', { r: 9, fill: 'none', stroke: C.ink, 'stroke-width': 2.5, visibility: 'hidden' }, svg);
    const dot = el('circle', { r: 5, fill: C.red, visibility: 'hidden' }, svg);
    const tip = document.createElement('div');
    tip.style.cssText = 'position:absolute;pointer-events:none;display:none;background:#191f28;color:#fff;border-radius:14px;' +
      `padding:14px 18px;font:20px/1.45 ${FONT};white-space:nowrap;box-shadow:0 6px 20px #0003`;
    box.appendChild(tip);
    let hoverOn = false;
    const row = (k, v) => { const d = document.createElement('div'), a = document.createElement('span');
      a.style.color = C.soft; a.textContent = k + '  '; d.append(a, v); return d; };
    const hide = () => { tip.style.display = 'none'; ring.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); };
    box.addEventListener('mousemove', ev => {
      if (!hoverOn) return;
      const r = box.getBoundingClientRect(), k = W / r.width, mx = (ev.clientX - r.left) * k, my = (ev.clientY - r.top) * k;
      let best = null, bd = 14 * 14;
      for (const p of E.points) { const dx = x(p.e) - mx, dy = y(p.s) - my, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = p; } }
      if (!best) return hide();
      const px = x(best.e), py = y(best.s);
      [ring, dot].forEach(c => { c.setAttribute('cx', px); c.setAttribute('cy', py); c.setAttribute('visibility', 'visible'); });
      const h = document.createElement('div'); h.style.cssText = 'font-weight:700;font-size:22px'; h.textContent = best.n;
      const gu = document.createElement('div'); gu.style.color = C.soft; gu.textContent = best.g + '-gu';
      tip.replaceChildren(h, gu, row('Elevation', best.e + ' m'), row('Morning shortage', pct(best.s)), row('Rides a day', best.u.toFixed(1)));
      if (best.m) { const b = document.createElement('div'); b.style.cssText = 'margin-top:6px;color:#ff9aa3;font-weight:600';
        b.textContent = 'Merge candidate (bottom 20% of use)'; tip.append(b); }
      tip.style.display = 'block';
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      tip.style.left = (px + 18 + tw > W ? px - 18 - tw : px + 18) + 'px';
      tip.style.top = Math.max(0, Math.min(H - th, py - th / 2)) + 'px';
    });
    box.addEventListener('mouseleave', hide);
    stop(box);
    const side = sideItems('elev');
    IX.elev = {
      steps: 5,
      cues: ['Each dot is a station: elevation across, how often it had no bikes at 7 to 9 am up.',
             'Below 20 m: empty 4.8% of commute hours.', '20 to 40 m: 9.5%.',
             '40 m and above: 25.1%, five times the lowest band.',
             'The LOESS curve: flat to about 25 m, then climbing. Hover a dot to name the station.'],
      set(k) {
        gs.forEach((g, b) => { const on = k > b; g.style.fill = on ? BAND_COL[b] : C.muted;
          g.style.fillOpacity = on ? (k >= 4 ? 0.3 : 0.55) : 0.22; });
        segs.forEach((g, b) => fade(g, k > b && k < 4));
        tops.forEach((g, b) => fade(g, k > b));
        curve.style.strokeDashoffset = k >= 4 ? 0 : 1;
        reveal(side, k >= 4 ? side.length : k);
        hoverOn = k >= 4;
        if (!hoverOn) hide();
      },
    };
  })();

  // ---------- slide 7: merge candidates, one dot each ----------
  (function () {
    const box = document.getElementById('ix-cands');
    if (!box) return;
    const CU = D.cands, W = 1100, H = 506, cell = 16, cols = 40, X0 = 200, Y0 = 70, GAP = 40;
    const svg = makeSvg(box, W, H);
    let cut = 1, last = 0;
    const lg = el('g', {}, svg);
    el('circle', { cx: X0 + 6, cy: 24, r: 7, fill: C.red }, lg);
    txt('Often empty in the morning (30% or more)', { x: X0 + 22, y: 30, 'font-size': 18, fill: C.ink }, lg);
    el('circle', { cx: X0 + 420, cy: 24, r: 7, fill: C.grey }, lg);
    txt('Not often empty', { x: X0 + 436, y: 30, 'font-size': 18, fill: C.ink }, lg);
    const maxN = [0, 1, 2].map(b => Math.max(...CU.map(c => c.n[b])));
    let top = Y0;
    const blocks = maxN.map((m, b) => {
      const g = el('g', {}, svg);
      g.style.transition = 'opacity 450ms';
      txt(BAND_LAB[b], { x: X0 - 24, y: top + 12, 'text-anchor': 'end', 'font-size': 20, 'font-weight': 600, fill: C.ink }, g);
      const dots = [];
      for (let j = 0; j < m; j++) {
        const c = el('circle', { cx: X0 + (j % cols) * cell + cell / 2 - 8, cy: top + Math.floor(j / cols) * cell + 6, r: 6, fill: C.grey }, g);
        c.style.transition = `fill 350ms ${Math.min(j * 4, 700)}ms, opacity 350ms`;
        dots.push(c);
      }
      const lab = txt('', { x: X0 + cols * cell + 8, y: top + 13, 'font-size': 22, fill: C.ink }, g);
      top += Math.ceil(m / cols) * cell + GAP;
      return { g, dots, lab };
    });
    const bar = buttons(box, ['Bottom 10% of use', '20%', '30%'], j => { cut = j; IX.cands.set(last); },
      `left:${X0 - 8}px;top:${top - 6}px`);
    const side = sideItems('cands');
    const nums = side.map(n => n.querySelector('.stat-num')), labs = side.map(n => n.querySelector('.stat-lab'));
    IX.cands = {
      steps: 4,
      cues: ['These are the stations a ride-count rule would merge: bottom 20% of use, another station within 300 m. One dot each.',
             'Red: already empty most commute mornings. 128 of 427.',
             'On the hills, 95 of 192: half of them.',
             'Change the cut-off to 10% or 30% of use: on the hills it stays about half.'],
      set(k) {
        last = k;
        const c = CU[cut], tot = c.n.reduce((a, b) => a + b, 0), gap = c.gap.reduce((a, b) => a + b, 0);
        blocks.forEach((bl, b) => {
          bl.dots.forEach((d, j) => { d.style.opacity = j < c.n[b] ? 1 : 0; d.style.fill = k >= 1 && j < c.gap[b] ? C.red : C.grey; });
          bl.g.style.opacity = k === 2 && b < 2 ? 0.25 : 1;
          bl.lab.textContent = k === 0 ? `${c.n[b]} stations` : `${c.gap[b]} of ${c.n[b]} (${pct(c.gap[b] / c.n[b], 0)})`;
          bl.lab.setAttribute('font-weight', k >= 2 && b === 2 ? 700 : 400);
          bl.lab.setAttribute('fill', k >= 2 && b === 2 ? C.red : C.ink);
        });
        fade(bar.bar, k >= 3);
        bar.bar.style.pointerEvents = k >= 3 ? 'auto' : 'none';
        bar.pick(cut);
        if (nums[0]) {
          nums[0].textContent = tot;
          labs[0].textContent = `merge candidates: bottom ${Math.round(c.p * 100)}% of use, with another station within 300 m`;
          nums[1].textContent = `${gap} (${pct(gap / tot, 0)})`;
          nums[2].textContent = c.gap[2];
        }
        reveal(side, k + 1);
      },
    };
    stop(box);
  })();

  // ---------- slide 11: dry, wet, then the Tukey mean-difference view ----------
  (function () {
    const box = document.getElementById('ix-rain');
    if (!box) return;
    const RN = D.rain, W = 1071, H = 600, L = 84, R = 24, T = 70, B = 84;
    const PW = W - L - R, PH = H - T - B;
    const xE = e => L + e / 80 * PW, yS = s => T + PH - s * PH;           // elevation view, shortage 0 to 100%
    const xT = m => L + m * PW, yT = d => T + PH / 2 - d / 0.4 * (PH / 2); // mean-difference view
    const svg = makeSvg(box, W, H);
    const clipId = 'rainclip';
    const cp = el('clipPath', { id: clipId }, el('defs', {}, svg));
    el('rect', { x: L - 6, y: T - 6, width: PW + 12, height: PH + 12 }, cp);
    const axE = el('g', {}, svg), axT = el('g', {}, svg);
    [0, .25, .5, .75, 1].forEach(v => {
      el('line', { x1: L, x2: W - R, y1: yS(v), y2: yS(v), stroke: C.grid }, axE);
      txt(Math.round(v * 100) + '%', { x: L - 12, y: yS(v) + 6, 'text-anchor': 'end', 'font-size': 17, fill: C.muted }, axE);
    });
    [0, 20, 40, 60, 80].forEach(v => txt(v, { x: xE(v), y: H - B + 28, 'text-anchor': 'middle', 'font-size': 17, fill: C.muted }, axE));
    [20, 40].forEach(v => el('line', { x1: xE(v), x2: xE(v), y1: T, y2: T + PH, stroke: C.muted, 'stroke-dasharray': '6 5' }, axE));
    txt('Station elevation (m)', { x: L + PW / 2, y: H - B + 58, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, axE);
    txt('Morning shortage (07-09 h)', { x: 0, y: 0, transform: `translate(26 ${T + PH / 2}) rotate(-90)`, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, axE);
    [-.4, -.2, 0, .2, .4].forEach(v => {
      el('line', { x1: L, x2: W - R, y1: yT(v), y2: yT(v), stroke: v === 0 ? C.muted : C.grid, 'stroke-width': v === 0 ? 1.5 : 1 }, axT);
      txt((v > 0 ? '+' : '') + Math.round(v * 100) + ' pp', { x: L - 12, y: yT(v) + 6, 'text-anchor': 'end', 'font-size': 17, fill: C.muted }, axT);
    });
    [0, .25, .5, .75].forEach(v => txt(Math.round(v * 100) + '%', { x: xT(v), y: H - B + 28, 'text-anchor': 'middle', 'font-size': 17, fill: C.muted }, axT));
    txt('Mean of wet and dry shortage', { x: L + PW / 2, y: H - B + 58, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, axT);
    txt('Wet minus dry', { x: 0, y: 0, transform: `translate(26 ${T + PH / 2}) rotate(-90)`, 'text-anchor': 'middle', 'font-size': 19, fill: C.ink }, axT);
    txt('Points near the zero line: rain does not change that station’s shortage.', { x: L, y: H - 6, 'font-size': 14, fill: C.muted }, axT);
    txt(`Stations with at least 30 wet commute mornings (rain 06-10 h), ${RN.points.length.toLocaleString('en')} stations.`,
      { x: L, y: H - 6, 'font-size': 14, fill: C.muted }, axE);
    const pg = el('g', { 'clip-path': `url(#${clipId})` }, svg);
    const dots = RN.points.map(p => {
      const c = el('circle', { r: 3, fill: BAND_COL[p.b - 1], 'fill-opacity': 0.45 }, pg);
      c.style.transition = 'cx 1000ms ease-in-out, cy 1000ms ease-in-out, opacity 500ms';
      return c;
    });
    const span = [[0, 20], [20, 40], [40, 80]];
    const segs = RN.bands.map((b, k) => {
      const g = el('g', {}, svg);
      el('line', { x1: xE(span[k][0]) + 4, x2: xE(span[k][1]) - 4, y1: 0, y2: 0, stroke: k === 0 ? '#5aa2ff' : BAND_COL[k],
        'stroke-width': 5, 'stroke-linecap': 'round' }, g);
      const lab = txt('', { x: (xE(span[k][0]) + xE(span[k][1])) / 2, y: -14, 'text-anchor': 'middle', 'font-size': k === 2 ? 30 : 22,
        'font-weight': 700, fill: k === 2 ? C.red : k === 1 ? C.blue : C.ink, 'paint-order': 'stroke', stroke: '#fff', 'stroke-width': 6 }, g);
      g.style.transition = 'transform 1000ms ease-in-out, opacity 450ms';
      return { g, lab };
    });
    const curve = el('path', { d: 'M' + RN.curve.map(c => xT(c.x).toFixed(1) + ',' + yT(c.y).toFixed(1)).join('L'),
      fill: 'none', stroke: C.ink, 'stroke-width': 3.5, 'stroke-linecap': 'round' }, svg);
    const tag = txt('', { x: W - R, y: T - 30, 'text-anchor': 'end', 'font-size': 24, 'font-weight': 700, fill: C.ink }, svg);
    const bar = buttons(box, ['Dry mornings', 'Wet mornings', 'Mean-difference'], j => window.goStep && window.goStep(j), `left:${L}px;top:${T - 58}px`);
    const side = sideItems('rain');
    const TAGS = ['Dry commute mornings', 'Wet commute mornings', 'Tukey mean-difference view'];
    IX.rain = {
      steps: 3,
      cues: ['Rain cuts morning rentals by 51 to 89%. On dry mornings, hill-top stations are empty 25.1% of the time.',
             'Now the same stations on wet mornings. Demand halves, yet hill-tops are still empty 20.9%.',
             'Mean-difference view: each station’s wet minus dry sits near zero across the range.'],
      set(k) {
        RN.points.forEach((p, j) => {
          const d = dots[j];
          if (k < 2) { d.style.cx = xE(Math.min(p.e, 80)) + 'px'; d.style.cy = yS(k === 0 ? p.dry : p.wet) + 'px'; d.style.opacity = p.e > 80 ? 0 : 1; }
          else { d.style.cx = xT((p.dry + p.wet) / 2) + 'px'; d.style.cy = yT(p.wet - p.dry) + 'px'; d.style.opacity = 1; }
        });
        segs.forEach((s, b) => {
          const v = k === 0 ? RN.bands[b].dry : RN.bands[b].wet;
          s.g.style.transform = `translate(0px, ${yS(k < 2 ? v : 0)}px)`;
          s.lab.textContent = pct(v);
          fade(s.g, k < 2);
        });
        fade(axE, k < 2, 600); fade(axT, k === 2, 600); fade(curve, k === 2, 800);
        tag.textContent = TAGS[k];
        bar.pick(k);
        reveal(side, k === 0 ? 1 : side.length);
      },
    };
    stop(box);
  })();
})();
