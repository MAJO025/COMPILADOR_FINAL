/* =====================================================================
   AST RENDERER — dibuja el árbol sintáctico en un <canvas>
   • Nodos = rectángulos redondeados (pill) con colores por tipo
   • Conexiones = líneas en L desde el centro del padre al hijo
   • Alta resolución (devicePixelRatio)
   ===================================================================== */

const AST_FONT_SIZE = 13;
const AST_NODE_H    = 28;
const AST_V_GAP     = 52;
const AST_H_GAP     = 16;

let _lastAst = null;
let zA = 1;

/* ── Colores por meta-tipo de nodo ── */
function nodeStyle(n) {
  const lbl = n.label.toLowerCase();
  const m   = n.meta || '';
  if (n.label === 'PROGRAMA')                        return { fill:'#4DD9C0', stroke:'#2ab89f', text:'#000', bold:true };
  if (m === 'func')                                  return { fill:'#fff',    stroke:'#555',    text:'#111', bold:true };
  if (m === 'class')                                 return { fill:'#C3A6FF', stroke:'#8B5CF6', text:'#1a0050', bold:true };
  if (m === 'var')                                   return { fill:'#fff',    stroke:'#555',    text:'#111', bold:false };
  if (m === 'if'  || lbl==='if'  || lbl==='else' || lbl==='elif') return { fill:'#F5CB5C', stroke:'#d4a800', text:'#3a2a00', bold:true };
  if (m === 'while'|| lbl==='while')                 return { fill:'#F5CB5C', stroke:'#d4a800', text:'#3a2a00', bold:true };
  if (m === 'for'  || lbl==='for')                   return { fill:'#F5CB5C', stroke:'#d4a800', text:'#3a2a00', bold:true };
  if (m === 'return'|| lbl==='return')               return { fill:'#F47C7C', stroke:'#c0392b', text:'#fff',    bold:true };
  if (m === 'call')                                  return { fill:'#fff',    stroke:'#555',    text:'#111', bold:false };
  if (m === 'op')                                    return { fill:'#000',    stroke:'#F5A623', text:'#F5A623', bold:true, opStyle:true };
  if (m === 'num')                                   return { fill:'#000',    stroke:'#57FF00', text:'#57FF00', bold:false };
  if (m === 'str')                                   return { fill:'#000',    stroke:'#38b6ff', text:'#38b6ff', bold:false };
  if (m === 'id')                                    return { fill:'#000',    stroke:'#ccc',    text:'#dde3f0', bold:false };
  if (m === 'lit')                                   return { fill:'#000',    stroke:'#C3A6FF', text:'#C3A6FF', bold:false };
  return { fill:'#000', stroke:'#8892a8', text:'#ccc', bold:false };
}

function measureText(label, bold, fontSize) {
  const charW = fontSize * (bold ? 0.65 : 0.6);
  return Math.max(label.length * charW + 20, 40);
}

/* ── Layout ── */
function astLayout(n) {
  if (!n.children || n.children.length === 0) {
    n._w = measureText(n.label, nodeStyle(n).bold, AST_FONT_SIZE) + 8;
    n._x = 0;
    return;
  }
  n.children.forEach(astLayout);
  const totalW = n.children.reduce((s, c) => s + c._w, 0) + (n.children.length - 1) * AST_H_GAP;
  const selfW  = measureText(n.label, nodeStyle(n).bold, AST_FONT_SIZE) + 8;
  n._w = Math.max(selfW, totalW);
  let x = 0;
  n.children.forEach(c => {
    c._x = x + (c._w - measureText(c.label, nodeStyle(c).bold, AST_FONT_SIZE) - 8) / 2;
    x += c._w + AST_H_GAP;
  });
  const childSpan = n.children.reduce((s, c) => s + c._w, 0) + (n.children.length - 1) * AST_H_GAP;
  const offset    = (n._w - childSpan) / 2;
  n.children.forEach(c => { c._x += offset; });
  n._x = 0;
}

function astAssignPos(n, x, y) {
  const nw = measureText(n.label, nodeStyle(n).bold, AST_FONT_SIZE) + 8;
  n._ax = x + n._x;
  n._ay = y;
  n._nw = nw;
  n._nh = AST_NODE_H;
  (n.children || []).forEach(c => astAssignPos(c, x + n._x, y + AST_NODE_H + AST_V_GAP));
}

function astGetBounds(n) {
  let mnX = n._ax, mxX = n._ax + n._nw, mxY = n._ay + n._nh;
  (n.children || []).forEach(c => {
    const b = astGetBounds(c);
    mnX = Math.min(mnX, b.mnX);
    mxX = Math.max(mxX, b.mxX);
    mxY = Math.max(mxY, b.mxY);
  });
  return { mnX, mxX, mxY };
}

/* ── Draw ── */
function astDrawNode(ctx, n) {
  const st = nodeStyle(n);
  const x = n._ax, y = n._ay, nw = n._nw, nh = n._nh;

  (n.children || []).forEach(c => {
    const px  = x + nw / 2,  py  = y + nh;
    const cx2 = c._ax + c._nw / 2, cy2 = c._ay;
    const lc  = st.opStyle ? '#F5A623' : n.label === 'PROGRAMA' ? '#4DD9C0' : n.meta === 'func' ? '#aaa' : '#666';
    const midY = py + (cy2 - py) * 0.45;
    ctx.strokeStyle = lc;
    ctx.lineWidth   = 1.5;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px, midY);
    ctx.lineTo(cx2, midY);
    ctx.lineTo(cx2, cy2);
    ctx.stroke();
    astDrawNode(ctx, c);
  });

  const r = nh / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);       ctx.lineTo(x + nw - r, y);
  ctx.arcTo(x + nw, y,        x + nw, y + r, r);   ctx.lineTo(x + nw, y + nh - r);
  ctx.arcTo(x + nw, y + nh,   x + nw - r, y + nh, r); ctx.lineTo(x + r, y + nh);
  ctx.arcTo(x, y + nh,        x, y + nh - r, r);   ctx.lineTo(x, y + r);
  ctx.arcTo(x, y,             x + r, y, r);
  ctx.closePath();

  if (st.opStyle) {
    ctx.fillStyle = 'rgba(0,0,0,0)'; ctx.fill();
    ctx.strokeStyle = st.stroke; ctx.lineWidth = 1.5; ctx.stroke();
  } else {
    ctx.fillStyle = st.fill; ctx.fill();
    ctx.strokeStyle = st.stroke; ctx.lineWidth = 1; ctx.stroke();
  }

  ctx.fillStyle    = st.text;
  const fs         = Math.max(9, Math.round(nh * 0.5));
  ctx.font         = `${st.bold ? '700' : '500'} ${fs}px Inconsolata,monospace`;
  ctx.textAlign    = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(n.label, x + nw / 2, y + nh / 2);
}

/* ── Public API ── */
function renderAST(ast) {
  const cv  = document.getElementById('astCanvas');
  const em  = document.getElementById('astEmpty');
  if (!cv || !em) return;
  if (!ast) {
    cv.style.display = 'none';
    em.style.display = 'flex';
    _lastAst = null;
    return;
  }
  _lastAst = ast;
  _drawASTAtZoom(ast, zA);
  cv.style.display = 'block';
  em.style.display = 'none';
  document.getElementById('astBadge').textContent = ast.id + ' nodos';
}

function _drawASTAtZoom(ast, zoom) {
  const cv  = document.getElementById('astCanvas');
  const dpr = window.devicePixelRatio || 1;

  astLayout(ast);
  astAssignPos(ast, 0, 30);
  const b   = astGetBounds(ast);
  const PAD = 40;
  const cssW = Math.max((b.mxX - b.mnX + PAD * 2) * zoom, 600);
  const cssH = Math.max((b.mxY + PAD * 2) * zoom, 300);

  const shiftX = PAD - b.mnX;
  function sh(n) {
    n._ax = (n._ax + shiftX) * zoom;
    n._ay = (n._ay + PAD / 2) * zoom;
    n._nw = n._nw * zoom;
    n._nh = n._nh * zoom;
    (n.children || []).forEach(sh);
  }
  sh(ast);

  cv.width  = Math.round(cssW * dpr);
  cv.height = Math.round(cssH * dpr);
  cv.style.width  = Math.round(cssW) + 'px';
  cv.style.height = Math.round(cssH) + 'px';

  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssW, cssH);
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, cssW, cssH);
  astDrawNode(ctx, ast);
}

/* Zoom del AST */
function zoomAstIn()    { zA = Math.min(3,  zA + 0.1); if (_lastAst) _drawASTAtZoom(_lastAst, zA); document.getElementById('zoomAstVal').textContent = Math.round(zA * 100) + '%'; }
function zoomAstOut()   { zA = Math.max(0.5, zA - 0.1); if (_lastAst) _drawASTAtZoom(_lastAst, zA); document.getElementById('zoomAstVal').textContent = Math.round(zA * 100) + '%'; }
function zoomAstReset() { zA = 1;                        if (_lastAst) _drawASTAtZoom(_lastAst, zA); document.getElementById('zoomAstVal').textContent = '100%'; }
