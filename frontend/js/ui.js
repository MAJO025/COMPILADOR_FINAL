/* =====================================================================
   UI.JS — toda la lógica de interfaz del compilador
   (renderizado de tablas, estadísticas, gráfica, zoom, eventos)
   ===================================================================== */

/* ── Constantes de badge y colores ── */
const BADGE_STYLE = {
  keyword:    'border-color:#A8E6CF;color:#A8E6CF;background:rgba(168,230,207,.1)',
  identifier: 'border-color:#FF6B6B;color:#FF6B6B;background:rgba(255,107,107,.1)',
  number:     'border-color:#85C1E9;color:#85C1E9;background:rgba(133,193,233,.1)',
  string:     'border-color:#4ECDC4;color:#4ECDC4;background:rgba(78,205,196,.1)',
  operator:   'border-color:#FFE66D;color:#c4b041;background:rgba(255,230,109,.08)',
  symbol:     'border-color:#FF8B94;color:#FF8B94;background:rgba(255,139,148,.1)',
  comment:    'border-color:#C3A6FF;color:#C3A6FF;background:rgba(195,166,255,.1)',
  unknown:    'border-color:#F39C12;color:#F39C12;background:rgba(243,156,18,.1)'
};

const PIE_TYPES = [
  { t:'identifier', lbl:'Identificador',   col:'#FF6B6B' },
  { t:'string',     lbl:'Literales',        col:'#4ECDC4' },
  { t:'operator',   lbl:'Operadores',       col:'#FFE66D' },
  { t:'keyword',    lbl:'Palabras clave',   col:'#A8E6CF' },
  { t:'comment',    lbl:'Comentarios',      col:'#C3A6FF' },
  { t:'symbol',     lbl:'Separadores',      col:'#FF8B94' },
  { t:'number',     lbl:'Números',          col:'#85C1E9' },
  { t:'unknown',    lbl:'No identificado',  col:'#F39C12' }
];

/* ── Estado global ── */
let allToks = [], curFilter = '', curPhase = 'lexico';
let pieSegments = [];
const PIE_CSS_W = 170, PIE_CSS_H = 170;

/* ── Zoom ── */
let zC = 1, zT = 1, zC2 = 1, zC3 = 1, zC4 = 1;
const ZS = 0.1, ZMN = 0.5, ZMX = 3;

function zI(t) {
  if      (t==='c')  zC  = Math.min(ZMX, zC  + ZS);
  else if (t==='t')  zT  = Math.min(ZMX, zT  + ZS);
  else if (t==='c2') zC2 = Math.min(ZMX, zC2 + ZS);
  else if (t==='c3') zC3 = Math.min(ZMX, zC3 + ZS);
  else if (t==='c4') zC4 = Math.min(ZMX, zC4 + ZS);
  applyZ(t);
}
function zO(t) {
  if      (t==='c')  zC  = Math.max(ZMN, zC  - ZS);
  else if (t==='t')  zT  = Math.max(ZMN, zT  - ZS);
  else if (t==='c2') zC2 = Math.max(ZMN, zC2 - ZS);
  else if (t==='c3') zC3 = Math.max(ZMN, zC3 - ZS);
  else if (t==='c4') zC4 = Math.max(ZMN, zC4 - ZS);
  applyZ(t);
}
function zR(t) {
  if (t==='c') zC=1; else if (t==='t') zT=1;
  else if (t==='c2') zC2=1; else if (t==='c3') zC3=1; else if (t==='c4') zC4=1;
  applyZ(t);
}
function applyZ(t) {
  if (t === 'c') {
    const fs = Math.round(13 * zC), lh = '1.7';
    const ta = document.getElementById('codeInput');
    const ln = document.getElementById('lineNums');
    const hl = document.getElementById('codeHighlight');
    ta.style.fontSize = fs + 'px'; ta.style.lineHeight = lh;
    ln.style.fontSize = fs + 'px'; ln.style.lineHeight = lh;
    if (hl) { hl.style.fontSize = fs + 'px'; hl.style.lineHeight = lh; }
    document.getElementById('zoomCodeVal').textContent = Math.round(zC * 100) + '%';
    syncLineNumsScroll(); syncHighlightScroll();
  } else if (t === 't') {
    const tbl = document.getElementById('tokTable');
    if (tbl) tbl.style.fontSize = Math.round(11 * zT) + 'px';
    document.getElementById('zoomTokVal').textContent = Math.round(zT * 100) + '%';
  } else if (t === 'c2') {
    const el  = document.getElementById('codeInput2');
    const fs2 = Math.round(13 * zC2), lh2 = '1.7';
    el.style.fontSize = fs2 + 'px'; el.style.lineHeight = lh2;
    const hl2 = document.getElementById('codeHighlight2');
    if (hl2) { hl2.style.fontSize = fs2 + 'px'; hl2.style.lineHeight = lh2; }
    document.getElementById('zoomCode2Val').textContent = Math.round(zC2 * 100) + '%';
    syncHighlightScroll2();
  } else if (t === 'c3') {
    const el  = document.getElementById('codeInput3');
    const fs3 = Math.round(13 * zC3), lh3 = '1.7';
    if (el) { el.style.fontSize = fs3 + 'px'; el.style.lineHeight = lh3; }
    const hl3 = document.getElementById('codeHighlight3');
    if (hl3) { hl3.style.fontSize = fs3 + 'px'; hl3.style.lineHeight = lh3; }
    const ln3 = document.getElementById('lineNums3');
    if (ln3) { ln3.style.fontSize = fs3 + 'px'; ln3.style.lineHeight = lh3; }
    document.getElementById('zoomCode3Val').textContent = Math.round(zC3 * 100) + '%';
    syncHighlightScroll3();
  } else if (t === 'c4') {
    const el  = document.getElementById('codeInput4');
    const fs4 = Math.round(13 * zC4), lh4 = '1.7';
    if (el) { el.style.fontSize = fs4 + 'px'; el.style.lineHeight = lh4; }
    const hl4 = document.getElementById('codeHighlight4');
    if (hl4) { hl4.style.fontSize = fs4 + 'px'; hl4.style.lineHeight = lh4; }
    const ln4 = document.getElementById('lineNums4');
    if (ln4) { ln4.style.fontSize = fs4 + 'px'; ln4.style.lineHeight = lh4; }
    document.getElementById('zoomCode4Val').textContent = Math.round(zC4 * 100) + '%';
    syncHighlightScroll4();
  }
}

/* ── Cambio de fase / vista ── */
function setPhase(p) {
  curPhase = p;
  ['lexico','sintactico','semantico','intermedio','optimizacion'].forEach(ph => {
    document.getElementById('view-' + ph).style.display = 'none';
    const btn = document.getElementById('btn-' + ph);
    btn.className = 'pbtn';
    if (ph === p) btn.classList.add('active-' + p);
  });
  document.getElementById('view-' + p).style.display = 'flex';
  if (p === 'sintactico') {
    document.getElementById('codeInput2').value = document.getElementById('codeInput').value;
    updateLineNums2();
    updateHighlight2();
  }
  if (p === 'semantico') {
    document.getElementById('codeInput3').value = document.getElementById('codeInput').value;
    updateLineNums3();
    updateHighlight3();
  }
  if (p === 'intermedio') {
    const el4 = document.getElementById('codeInput4');
    if (el4) {
      el4.value = document.getElementById('codeInput').value;
      updateLineNums4();
      updateHighlight4();
    }
  }
}

/* ── Tabla de tokens ── */
function renderTokTable() {
  const body  = document.getElementById('tokBody');
  const tbl   = document.getElementById('tokTable');
  const empty = document.getElementById('tokEmpty');
  const badge = document.getElementById('tokCountLabel');
  const flt   = curFilter ? allToks.filter(t => t.t === curFilter) : allToks;

  if (!flt.length) {
    tbl.style.display   = 'none';
    empty.style.display = 'flex';
    badge.textContent   = '0 tokens';
    return;
  }
  tbl.style.display   = 'table';
  empty.style.display = 'none';
  badge.textContent   = flt.length + ' tokens';

  body.innerHTML = flt.map((tk, i) => `
    <tr class="${tk.t === 'unknown' ? 'err-row' : ''}" onclick="selTok(${i})">
      <td class="td-n">${i + 1}</td>
      <td><span style="font-family:var(--font);font-size:11px;">${esc(tk.v)}</span></td>
      <td><span class="tbadge" style="${BADGE_STYLE[tk.t]}">${tk.tname}</span></td>
      <td style="color:rgba(255,255,255,.7);font-size:10px;">${tk.clasif}</td>
      <td style="color:rgba(145,192,253,.6);font-size:10px;">${tk.subclasif}</td>
      <td style="color:rgba(145,192,253,.5);font-size:10px;">${tk.ln}</td>
      <td style="color:rgba(145,192,253,.5);font-size:10px;">${tk.col}</td>
    </tr>`).join('');

  applyZ('t');
}

function selTok(idx) {
  document.querySelectorAll('#tokBody tr').forEach(r => r.classList.remove('sel'));
  document.querySelectorAll('#tokBody tr')[idx]?.classList.add('sel');
}

function filterTok(type) {
  curFilter = type;
  document.getElementById('fltBadge').style.display = type ? 'inline-flex' : 'none';
  renderTokTable();
}

/* ── Estadísticas sidebar ── */
function renderStats() {
  const count = t => allToks.filter(tk => tk.t === t).length;
  const lit   = count('string') + count('number');
  document.getElementById('sk-id').textContent  = count('identifier');
  document.getElementById('sk-lit').textContent = lit;
  document.getElementById('sk-op').textContent  = count('operator');
  document.getElementById('sk-kw').textContent  = count('keyword');
  document.getElementById('sk-cm').textContent  = count('comment');
  document.getElementById('sk-sy').textContent  = count('symbol');
  document.getElementById('sk-nm').textContent  = count('number');
  document.getElementById('sk-unk').textContent = count('unknown');
  document.getElementById('sk-tot').textContent = allToks.length;
  renderMiniTable();
}

function renderMiniTable() {
  const types = [
    { t:'identifier', lbl:'Identificador' },
    { t:'string',     lbl:'Literales' },
    { t:'operator',   lbl:'Operadores' },
    { t:'keyword',    lbl:'Palabras clave' },
    { t:'comment',    lbl:'Comentarios' },
    { t:'symbol',     lbl:'Separadores' },
    { t:'number',     lbl:'Números' },
    { t:'unknown',    lbl:'No identificado' }
  ];
  const total = allToks.length || 1;
  document.getElementById('miniTableBody').innerHTML = types.map(({ t, lbl }) => {
    const cnt = allToks.filter(tk => tk.t === t).length;
    const pct = total > 0 ? Math.round(cnt / total * 100) : 0;
    return `<tr><td>${lbl}</td><td>${cnt}</td><td>${pct}%</td></tr>`;
  }).join('');
}

function updateExtraInfo(lines, chars) {
  document.getElementById('ei-lines').textContent = lines;
  document.getElementById('ei-chars').textContent = chars;
  document.getElementById('stLines').textContent  = lines;
  document.getElementById('stChars').textContent  = chars;
}

/* ── Gráfica de torta (donut) ── */
function initPieCanvas() {
  const cv  = document.getElementById('pieChart');
  const dpr = window.devicePixelRatio || 1;
  cv.width  = PIE_CSS_W * dpr;
  cv.height = PIE_CSS_H * dpr;
  cv.style.width  = PIE_CSS_W + 'px';
  cv.style.height = PIE_CSS_H + 'px';
  cv.getContext('2d').scale(dpr, dpr);
}

function drawPie() {
  const cv  = document.getElementById('pieChart');
  const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, PIE_CSS_W, PIE_CSS_H);
  const total = allToks.length;
  pieSegments = [];
  const cx = PIE_CSS_W / 2, cy = PIE_CSS_H / 2, r = 72, inner = 32;

  if (!total) {
    ctx.fillStyle = '#1a1a1a';
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, inner, 0, Math.PI * 2);
    ctx.fillStyle = '#000'; ctx.fill();
    ctx.fillStyle = 'rgba(145,192,253,.3)';
    ctx.font = '11px Inconsolata,monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('sin datos', cx, cy);
    return;
  }

  let angle = -Math.PI / 2;
  PIE_TYPES.forEach(({ t, lbl, col }) => {
    const cnt = allToks.filter(tk => tk.t === t).length;
    if (!cnt) return;
    const slice = (cnt / total) * Math.PI * 2;
    pieSegments.push({ t, lbl, col, cnt, pct: Math.round(cnt / total * 100), startA: angle, endA: angle + slice });
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r, angle, angle + slice); ctx.closePath();
    ctx.fillStyle = col; ctx.fill();
    ctx.strokeStyle = '#000'; ctx.lineWidth = 1.5; ctx.stroke();
    if (cnt / total > 0.055) {
      const mid = angle + slice / 2;
      const tx  = cx + Math.cos(mid) * r * 0.67, ty = cy + Math.sin(mid) * r * 0.67;
      ctx.fillStyle = 'rgba(0,0,0,.85)';
      ctx.beginPath(); ctx.arc(tx, ty, 9, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.font = 'bold 9px Inconsolata,monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(Math.round(cnt / total * 100) + '%', tx, ty);
    }
    angle += slice;
  });

  ctx.beginPath(); ctx.arc(cx, cy, r + 1, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(145,192,253,.15)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, cy, inner, 0, Math.PI * 2);
  ctx.fillStyle = '#000'; ctx.fill();
  ctx.fillStyle = 'rgba(145,192,253,.9)'; ctx.font = 'bold 15px Inconsolata,monospace';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(total, cx, cy - 7);
  ctx.font = '9px Inconsolata,monospace'; ctx.fillStyle = 'rgba(145,192,253,.5)';
  ctx.fillText('Token', cx, cy + 7);
}

/* Hover tooltip en la torta */
document.getElementById('pieChart').addEventListener('mousemove', function (e) {
  const rect = this.getBoundingClientRect();
  const mx   = e.clientX - rect.left  - PIE_CSS_W / 2;
  const my   = e.clientY - rect.top   - PIE_CSS_H / 2;
  const dist = Math.sqrt(mx * mx + my * my);
  const tip  = document.getElementById('pieTooltip');
  if (dist > 32 && dist < 74) {
    let ang = Math.atan2(my, mx);
    const seg = pieSegments.find(s => {
      let a = ang; if (a < s.startA) a += Math.PI * 2;
      let ea = s.endA; if (ea < s.startA) ea += Math.PI * 2;
      return a >= s.startA && a <= ea;
    });
    if (seg) {
      tip.style.display = 'block';
      tip.style.left    = (e.clientX + 14) + 'px';
      tip.style.top     = (e.clientY - 14) + 'px';
      tip.innerHTML = `<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
        <div style="width:10px;height:10px;border-radius:50%;background:${seg.col};flex-shrink:0"></div>
        <span style="color:${seg.col};font-weight:700">${seg.lbl}</span></div>
        Cantidad: <b>${seg.cnt}</b><br>Porcentaje: <b>${seg.pct}%</b>`;
      return;
    }
  }
  tip.style.display = 'none';
});
document.getElementById('pieChart').addEventListener('mouseleave', () => {
  document.getElementById('pieTooltip').style.display = 'none';
});

/* ── Log de producciones ── */
function renderLog(log) {
  const body = document.getElementById('logBody');
  const em   = document.getElementById('logEmpty');
  if (!body) return;
  if (!log.length) {
    body.innerHTML = '';
    if (em) em.style.display = 'flex';
    return;
  }
  if (em) em.style.display = 'none';
  body.innerHTML = log.map(e => `
    <div class="log-entry ${e.ok ? 'log-ok' : 'log-err'}">
      <span class="log-icon">${e.ok ? '✓' : '✗'}</span>
      <span class="log-text">${esc(e.msg)}${e.ln ? ' <span style="color:rgba(145,192,253,.4)">[L' + e.ln + ']</span>' : ''}</span>
      ${e.rule ? `<span class="log-rule">${esc(e.rule)}</span>` : ''}
    </div>`).join('');
}

/* ── Números de línea ── */
function updateLineNums() {
  const src = document.getElementById('codeInput').value;
  const n   = src.split('\n').length;
  document.getElementById('lineNums').textContent = Array.from({ length: n }, (_, i) => i + 1).join('\n');
  document.getElementById('stLines').textContent  = n;
  document.getElementById('stChars').textContent  = src.length;
  document.getElementById('ei-lines').textContent = n;
  document.getElementById('ei-chars').textContent = src.length;
}
function syncLineNumsScroll() {
  const ta = document.getElementById('codeInput');
  document.getElementById('lineNums').scrollTop = ta.scrollTop;
}
function updateLineNums2() {
  const src = document.getElementById('codeInput2').value;
  const n   = src.split('\n').length;
  const ln2 = document.getElementById('lineNums2');
  if (ln2) ln2.textContent = Array.from({ length: n }, (_, i) => i + 1).join('\n');
}
let _semErrLines  = new Map();
let _semWarnLines = new Map();

function updateLineNums3() {
  const ta  = document.getElementById('codeInput3');
  const src = ta ? ta.value : '';
  const n   = src.split('\n').length;
  const ln3 = document.getElementById('lineNums3');
  if (!ln3) return;
  const prevScroll = ta ? ta.scrollTop : 0;
  let html = '';
  for (let i = 1; i <= n; i++) {
    const errMsg  = _semErrLines.get(i);
    const warnMsg = _semWarnLines.get(i);
    let dot = '';
    if (errMsg) {
      dot = `<span class="ln-dot ln-dot-err" title="${esc(errMsg)}">●</span>`;
    } else if (warnMsg) {
      dot = `<span class="ln-dot ln-dot-warn" title="${esc(warnMsg)}">●</span>`;
    }
    html += `<div class="ln-row"><span class="ln-n">${i}</span>${dot}</div>`;
  }
  ln3.innerHTML = html;
  ln3.scrollTop = prevScroll;
}

function setSemanticErrorLines(errMap, warnMap) {
  _semErrLines  = errMap  || new Map();
  _semWarnLines = warnMap || new Map();
  updateLineNums3();
}

/* ── Barra de estado ── */
function setStatus(s, msg) {
  const c = { ok:'#57FF00', err:'#FF0040', run:'#F5CB5C', idle:'rgba(145,192,253,.4)' };
  document.getElementById('stDot').style.background = c[s] || c.idle;
  document.getElementById('stTxt').textContent = msg;
}

/* ── Tabla resumen (colapsable) ── */
function toggleInfoTable() {
  document.getElementById('infoTableWrap').classList.toggle('open');
  document.getElementById('infoArrow').classList.toggle('open');
}

/* ── Limpiar todo ── */
function clearAll() {
  try {
    const _s = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v; };
    const _d = (id, v) => { const e = document.getElementById(id); if (e) e.style.display = v; };

    /* Limpiar editores */
    ['codeInput','codeInput2','codeInput3'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
    const el4 = document.getElementById('codeInput4');
    if (el4) el4.value = '';

    /* Restablecer tokens y gráficas */
    allToks = []; curFilter = '';
    try { renderTokTable(); } catch(_) {}
    try { renderStats();    } catch(_) {}
    try { drawPie();        } catch(_) {}
    try { renderLog([]);    } catch(_) {}
    try { renderAST(null);  } catch(_) {}

    /* Actualizar números de línea y highlight en todos los editores */
    try { updateLineNums();   } catch(_) {}
    try { updateHighlight();  } catch(_) {}
    try { updateLineNums2();  } catch(_) {}
    try { updateHighlight2(); } catch(_) {}
    try { updateLineNums3();  } catch(_) {}
    try { updateHighlight3(); } catch(_) {}
    try { updateLineNums4();  } catch(_) {}
    try { updateHighlight4(); } catch(_) {}

    /* Stats léxico */
    _s('ei-err', '0');
    _d('stErrItem', 'none');

    /* Stats sintáctico */
    _s('syn-nodes', '0'); _s('syn-prods', '0');
    _s('syn-pos', '—');   _s('syn-estado', '—');
    _s('syn-errs', '0');  _s('astBadge', 'esperando');
    _s('logBadge', '0 reglas');

    /* Semántico */
    try { if (typeof setSemanticErrorLines === 'function') setSemanticErrorLines(new Map(), new Map()); } catch(_) {}
    try { if (typeof renderSemantic === 'function') renderSemantic([], [], [], {}); } catch(_) {}

    /* Código intermedio y optimización */
    try { if (typeof clearIntermediateState === 'function') clearIntermediateState(); } catch(_) {}
  } catch(e) {
    console.warn('[clearAll]', e);
  }
  setStatus('idle', 'Listo');
}

/* ── Carga de archivo ── */
function loadFile(input) {
  const f = input.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = e => {
    document.getElementById('codeInput').value = e.target.result;
    const el2 = document.getElementById('codeInput2');
    if (el2) el2.value = e.target.result;
    const el3 = document.getElementById('codeInput3');
    if (el3) el3.value = e.target.result;
    const el4 = document.getElementById('codeInput4');
    if (el4) el4.value = e.target.result;
    updateLineNums(); updateHighlight(); updateHighlight2();
    updateLineNums3(); updateHighlight3();
    updateLineNums4(); updateHighlight4();
    compile();
  };
  r.readAsText(f); input.value = '';
}

/* ── Carga de logo ── */
function loadLogo(input) {
  const f = input.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = e => {
    document.getElementById('logoSlot').innerHTML = `<img src="${e.target.result}" alt="logo">`;
  };
  r.readAsDataURL(f); input.value = '';
}

function tryLoadLogoPath() {
  const LOGO_PATH = 'assets/Logo_compilador.ico';
  if (!LOGO_PATH) return;
  const img = new Image();
  img.onload = () => {
    const slot = document.getElementById('logoSlot');
    slot.innerHTML = '';
    const el = document.createElement('img');
    el.src = LOGO_PATH;
    el.style.cssText = 'width:100%;height:100%;object-fit:contain;';
    slot.appendChild(el);
    slot.onclick = null;
  };
  img.src = LOGO_PATH;
}

/* ── Cursor ── */
function updateCursor() {
  const ta = document.getElementById('codeInput');
  const v  = ta.value.substring(0, ta.selectionStart).split('\n');
  document.getElementById('cursorInfo').textContent = `L${v.length}:C${v[v.length - 1].length + 1}`;
}

/* ── Highlight (overlay pre detrás del textarea) ── */
const KW_HL = new Set([
  'if','else','elif','for','while','do','switch','case','break','continue','return',
  'int','float','double','char','bool','void','string','var','let','const','def','class','struct',
  'enum','interface','extends','implements','import','from','as','new','delete','this','super',
  'public','private','protected','static','final','true','false','null','None','True','False',
  'undefined','typeof','instanceof','try','catch','finally','throw','in','not','and','or','is',
  'pass','lambda','yield','async','await','print','input','include','using','namespace','template',
  'auto','extern','inline','sizeof','typedef','union','goto','function','module','export','default',
  'with','global','nonlocal','del','assert','raise','except','range','len','type','open'
]);
const HL = {
  keyword:'#569cd6', identifier:'#9cdcfe', string:'#ce9178',
  number:'#b5cea8',  comment:'#6a9955',    operator:'#d4d4d4',
  symbol:'#abb2bf',  unknown:'#f44747'
};
function escH(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function lexHighlight(src) {
  let out = '', i = 0;
  const sp = (t, v) => `<span style="color:${HL[t]}">${escH(v)}</span>`;
  while (i < src.length) {
    const c = src[i];
    if (c === '\n' || c === ' ' || c === '\t' || c === '\r') { out += escH(c); i++; continue; }
    if (c === '/' && src[i+1] === '*') { let v='/*';i+=2;while(i<src.length-1&&!(src[i]==='*'&&src[i+1]==='/')){v+=src[i++];}v+='*/';i+=2;out+=sp('comment',v);continue; }
    if (c === '/' && src[i+1] === '/') { let v='';while(i<src.length&&src[i]!=='\n'){v+=src[i++];}out+=sp('comment',v);continue; }
    if (c === '#') { let v='';while(i<src.length&&src[i]!=='\n'){v+=src[i++];}out+=sp('comment',v);continue; }
    if ((c==='"'||c==="'")&&src[i+1]===c&&src[i+2]===c){const q=c+c+c;let v=q;i+=3;while(i<src.length&&!(src[i]===c&&src[i+1]===c&&src[i+2]===c)){v+=src[i++];}v+=q;i+=3;out+=sp('string',v);continue;}
    if ((c==='f'||c==='F')&&(src[i+1]==='"'||src[i+1]==="'")){const q=src[i+1];let v=c+q;i+=2;while(i<src.length&&src[i]!==q&&src[i]!=='\n'){if(src[i]==='\\'){v+=src[i++];}v+=src[i++];}if(src[i]===q){v+=q;i++;}out+=sp('string',v);continue;}
    if (c==='"'||c==="'"){const q=c;let v=c;i++;while(i<src.length&&src[i]!==q&&src[i]!=='\n'){if(src[i]==='\\'){v+=src[i++];}v+=src[i++];}if(src[i]===q){v+=q;i++;}out+=sp('string',v);continue;}
    if (/[0-9]/.test(c)||(c==='.'&&/[0-9]/.test(src[i+1]||''))){let v='';while(i<src.length&&/[0-9a-fA-FxXbBoO._eE]/.test(src[i])){v+=src[i++];}out+=sp('number',v);continue;}
    if (/[a-zA-Z_$]/.test(c)){let v='';while(i<src.length&&/[a-zA-Z0-9_$]/.test(src[i])){v+=src[i++];}out+=sp(KW_HL.has(v)?'keyword':'identifier',v);continue;}
    const p3=src.slice(i,i+3),p2=src.slice(i,i+2);
    if(['===','!==','**=','//='].includes(p3)){out+=sp('operator',p3);i+=3;continue;}
    if(['==','!=','<=','>=','&&','||','++','--','+=','-=','*=','/=','%=','**','//','->','::','<<','>>','&=','|=','^=','?.','??','=>'].includes(p2)){out+=sp('operator',p2);i+=2;continue;}
    if('+-*/%=<>!&|^~@'.includes(c)){out+=sp('operator',c);i++;continue;}
    if('(){}[];:,.\\'+'?'.includes(c)){out+=sp('symbol',c);i++;continue;}
    out+=sp('unknown',c);i++;
  }
  return out;
}
function updateHighlight() {
  const el = document.getElementById('codeHighlightCode');
  if (el) el.innerHTML = lexHighlight(document.getElementById('codeInput').value) + '\n';
}
function syncHighlightScroll() {
  const ta = document.getElementById('codeInput');
  const hl = document.getElementById('codeHighlight');
  if (hl) hl.style.transform = `translate(-${ta.scrollLeft}px,-${ta.scrollTop}px)`;
}
function updateHighlight2() {
  const el = document.getElementById('codeHighlightCode2');
  if (el) el.innerHTML = lexHighlight(document.getElementById('codeInput2').value) + '\n';
}
function syncHighlightScroll2() {
  const ta = document.getElementById('codeInput2');
  const hl = document.getElementById('codeHighlight2');
  if (hl) hl.style.transform = `translate(-${ta.scrollLeft}px,-${ta.scrollTop}px)`;
}
function updateHighlight3() {
  const el = document.getElementById('codeHighlightCode3');
  if (el) el.innerHTML = lexHighlight(document.getElementById('codeInput3').value) + '\n';
}
function syncHighlightScroll3() {
  const ta = document.getElementById('codeInput3');
  const hl = document.getElementById('codeHighlight3');
  if (ta && hl) hl.style.transform = `translate(-${ta.scrollLeft}px,-${ta.scrollTop}px)`;
}
function updateLineNums4() {
  const ta  = document.getElementById('codeInput4');
  const src = ta ? ta.value : '';
  const n   = src.split('\n').length;
  const ln4 = document.getElementById('lineNums4');
  if (!ln4) return;
  const prevScroll = ta ? ta.scrollTop : 0;
  let html = '';
  for (let i = 1; i <= n; i++) {
    html += `<div class="ln-row"><span class="ln-n">${i}</span></div>`;
  }
  ln4.innerHTML = html;
  ln4.scrollTop = prevScroll;
}
function updateHighlight4() {
  const el = document.getElementById('codeHighlightCode4');
  if (el) el.innerHTML = lexHighlight(document.getElementById('codeInput4').value) + '\n';
}
function syncHighlightScroll4() {
  const ta = document.getElementById('codeInput4');
  const hl = document.getElementById('codeHighlight4');
  if (ta && hl) hl.style.transform = `translate(-${ta.scrollLeft}px,-${ta.scrollTop}px)`;
}

/* ── Tab en el editor ── */
function handleTab(e) {
  if (e.key !== 'Tab') return;
  e.preventDefault();
  const ta = e.target, start = ta.selectionStart, end = ta.selectionEnd;
  ta.value = ta.value.substring(0, start) + '    ' + ta.value.substring(end);
  ta.selectionStart = ta.selectionEnd = start + 4;
  ta.dispatchEvent(new Event('input'));
}

/* ── Utilidad HTML escape ── */
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ── Depth del AST ── */
function getASTDepth(n, d = 0) {
  if (!n || !n.children || !n.children.length) return d;
  return Math.max(...n.children.map(c => getASTDepth(c, d + 1)));
}

/* ── Debounce para compile() ── */
let _compileTimer = null;
function scheduleCompile() {
  clearTimeout(_compileTimer);
  _compileTimer = setTimeout(() => {
    if (document.getElementById('codeInput').value.length < 3000) compile();
  }, 300);
}

/* ── Highlight diferido (no bloquea el hilo principal en paste) ── */
let _hlRafPending = false;
function scheduleHighlight() {
  if (_hlRafPending) return;
  _hlRafPending = true;
  requestAnimationFrame(() => {
    _hlRafPending = false;
    updateHighlight();
  });
}
let _hlRafPending2 = false;
function scheduleHighlight2() {
  if (_hlRafPending2) return;
  _hlRafPending2 = true;
  requestAnimationFrame(() => {
    _hlRafPending2 = false;
    updateHighlight2();
  });
}
let _hlRafPending3 = false;
function scheduleHighlight3() {
  if (_hlRafPending3) return;
  _hlRafPending3 = true;
  requestAnimationFrame(() => {
    _hlRafPending3 = false;
    updateHighlight3();
  });
}
let _lnRafPending3 = false;
function scheduleLineNums3() {
  if (_lnRafPending3) return;
  _lnRafPending3 = true;
  requestAnimationFrame(() => {
    _lnRafPending3 = false;
    updateLineNums3();
  });
}

/* ── Eventos globales ── */
document.getElementById('codeInput').addEventListener('input', () => {
  updateLineNums(); scheduleHighlight(); scheduleCompile();
});
document.getElementById('codeInput').addEventListener('scroll', () => {
  syncLineNumsScroll(); syncHighlightScroll();
});
document.getElementById('codeInput').addEventListener('keyup', updateCursor);
document.getElementById('codeInput').addEventListener('click', updateCursor);
document.getElementById('codeInput').addEventListener('keydown', handleTab);

document.getElementById('codeInput2').addEventListener('input', () => {
  document.getElementById('codeInput').value = document.getElementById('codeInput2').value;
  document.getElementById('codeInput3').value = document.getElementById('codeInput2').value;
  updateLineNums(); updateLineNums2(); updateLineNums3();
  scheduleHighlight(); scheduleHighlight2();
  scheduleCompile();
});
document.getElementById('codeInput2').addEventListener('scroll', () => {
  const ta  = document.getElementById('codeInput2');
  const ln2 = document.getElementById('lineNums2');
  if (ln2) ln2.scrollTop = ta.scrollTop;
  syncHighlightScroll2();
});
document.getElementById('codeInput2').addEventListener('keydown', handleTab);

document.getElementById('codeInput3').addEventListener('input', () => {
  const v = document.getElementById('codeInput3').value;
  document.getElementById('codeInput').value  = v;
  document.getElementById('codeInput2').value = v;
  const el4 = document.getElementById('codeInput4');
  if (el4) el4.value = v;
  scheduleLineNums3();
  scheduleHighlight3();
  scheduleCompile();
});
document.getElementById('codeInput3').addEventListener('scroll', () => {
  const ta  = document.getElementById('codeInput3');
  const ln3 = document.getElementById('lineNums3');
  if (ln3) ln3.scrollTop = ta.scrollTop;
  syncHighlightScroll3();
});
document.getElementById('codeInput3').addEventListener('keydown', handleTab);

/* ── Editor 4 (código intermedio) ── */
let _hlRafPending4 = false;
function scheduleHighlight4() {
  if (_hlRafPending4) return;
  _hlRafPending4 = true;
  requestAnimationFrame(() => { _hlRafPending4 = false; updateHighlight4(); });
}
let _lnRafPending4 = false;
function scheduleLineNums4() {
  if (_lnRafPending4) return;
  _lnRafPending4 = true;
  requestAnimationFrame(() => { _lnRafPending4 = false; updateLineNums4(); });
}

const _ci4 = document.getElementById('codeInput4');
if (_ci4) {
  _ci4.addEventListener('input', () => {
    const v = _ci4.value;
    document.getElementById('codeInput').value  = v;
    document.getElementById('codeInput2').value = v;
    document.getElementById('codeInput3').value = v;
    scheduleLineNums4(); scheduleHighlight4(); scheduleCompile();
  });
  _ci4.addEventListener('scroll', () => {
    const ln4 = document.getElementById('lineNums4');
    if (ln4) ln4.scrollTop = _ci4.scrollTop;
    syncHighlightScroll4();
  });
  _ci4.addEventListener('keydown', handleTab);
}

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); compile(); }
});

document.getElementById('tokScroll').addEventListener('wheel', e => {
  if (e.ctrlKey) { e.preventDefault(); e.deltaY < 0 ? zI('t') : zO('t'); }
}, { passive: false });
document.getElementById('astScroll').addEventListener('wheel', e => {
  if (e.ctrlKey) { e.preventDefault(); e.deltaY < 0 ? zoomAstIn() : zoomAstOut(); }
}, { passive: false });

/* ── Init ── */
initPieCanvas();
tryLoadLogoPath();
updateLineNums();
drawPie();
setStatus('idle', 'Listo — Ctrl+Enter para compilar');
updateHighlight();
