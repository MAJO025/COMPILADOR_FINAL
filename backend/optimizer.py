"""
Optimizador de Código Intermedio (TAC)
========================================
Cinco pasadas de optimización local aplicadas sobre el
Código de Tres Direcciones generado por backend/codegen.py

  Pasada 1 — Plegado de constantes        (Constant Folding)
  Pasada 2 — Propagación de constantes    (Constant Propagation)
  Pasada 3 — Simplificación algebraica    (Algebraic Simplification)
  Pasada 4 — Propagación de copias        (Copy Propagation)
  Pasada 5 — Eliminación de código muerto (Dead Code Elimination)

Se ejecuta en punto fijo: repite hasta que ninguna pasada
produzca cambios (máximo MAX_ITER iteraciones).
"""

from __future__ import annotations
import re
import operator

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

# dst = a OP b
_BIN_RE  = re.compile(
    r'^(\w[\w.]*)\s*=\s*(\S+)\s*(\+|-|\*\*|//|\*|/|%|==|!=|<=|>=|<|>)\s*(\S+)$'
)
# dst = OP a   (unario)
_UN_RE   = re.compile(r'^(\w[\w.]*)\s*=\s*(-|not|!)\s*(\S+)$')
# dst = a      (copia simple)
_COPY_RE = re.compile(r'^(\w[\w.]*)\s*=\s*(\S+)$')

_OPS: dict = {
    '+':  operator.add,   '-':  operator.sub,
    '*':  operator.mul,   '/':  operator.truediv,
    '//': operator.floordiv,  '%': operator.mod,
    '**': operator.pow,
    '==': operator.eq,    '!=': operator.ne,
    '<':  operator.lt,    '>':  operator.gt,
    '<=': operator.le,    '>=': operator.ge,
}


def _is_num(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _to_num(s: str):
    try:
        return int(s)
    except ValueError:
        return float(s)


def _fmt(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, bool):
        return 'True' if v else 'False'
    return str(v)


def _is_temp(s: str) -> bool:
    return bool(re.match(r'^t\d+$', s))


def _clone(ins: dict) -> dict:
    return dict(ins)


# ─────────────────────────────────────────────────────────────────────────────
# Pasada 1 — Plegado de constantes
# ─────────────────────────────────────────────────────────────────────────────

def _pass_constant_folding(instrs: list) -> tuple[list, list]:
    result, changes = [], []
    for ins in instrs:
        if ins.get('is_label'):
            result.append(_clone(ins))
            continue
        code = ins['instr']
        m = _BIN_RE.match(code)
        if m:
            dst, a, op, b = m.groups()
            if _is_num(a) and _is_num(b) and op in _OPS:
                try:
                    val = _OPS[op](_to_num(a), _to_num(b))
                    new_code = f'{dst} = {_fmt(val)}'
                    changes.append({
                        'pass':   'Plegado de constantes',
                        'before': code,
                        'after':  new_code,
                        'ln':     ins.get('ln', 0),
                    })
                    r = _clone(ins)
                    r['instr']      = new_code
                    r['comment']    = f'fold: {a} {op} {b} = {_fmt(val)}'
                    r['_tag']       = 'modified'
                    r['_technique'] = 'constant_folding'
                    result.append(r)
                    continue
                except Exception:
                    pass
        result.append(_clone(ins))
    return result, changes


# ─────────────────────────────────────────────────────────────────────────────
# Pasada 2 — Propagación de constantes
# ─────────────────────────────────────────────────────────────────────────────

def _pass_constant_propagation(instrs: list) -> tuple[list, list]:
    const_map: dict[str, str] = {}
    result, changes = [], []

    for ins in instrs:
        if ins.get('is_label'):
            const_map.clear()
            result.append(_clone(ins))
            continue
        code = ins['instr']
        new_code = code

        m = _BIN_RE.match(code)
        u = _UN_RE.match(code)
        c = _COPY_RE.match(code)

        if m:
            dst, a, op, b = m.groups()
            na, nb = const_map.get(a, a), const_map.get(b, b)
            if na != a or nb != b:
                new_code = f'{dst} = {na} {op} {nb}'
                changes.append({'pass': 'Propagación de constantes',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})
        elif u:
            dst, op, a = u.groups()
            na = const_map.get(a, a)
            if na != a:
                new_code = f'{dst} = {op} {na}'
                changes.append({'pass': 'Propagación de constantes',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})
        elif c:
            dst, src = c.groups()
            ns = const_map.get(src, src)
            if ns != src:
                new_code = f'{dst} = {ns}'
                changes.append({'pass': 'Propagación de constantes',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})

        # Actualizar mapa de constantes
        fc = _COPY_RE.match(new_code)
        if fc:
            d2, s2 = fc.groups()
            if _is_num(s2):
                const_map[d2] = s2
            else:
                const_map.pop(d2, None)

        r = _clone(ins)
        r['instr'] = new_code
        if new_code != code:
            r['_tag']       = 'modified'
            r['_technique'] = 'constant_propagation'
        result.append(r)
    return result, changes


# ─────────────────────────────────────────────────────────────────────────────
# Pasada 3 — Simplificación algebraica
# ─────────────────────────────────────────────────────────────────────────────

_ALGE: list[tuple] = [
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*\*\s*1$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x * 1 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*1\s*\*\s*(\w[\w.]*)$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   '1 * x → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*\+\s*0$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x + 0 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*0\s*\+\s*(\w[\w.]*)$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   '0 + x → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*-\s*0$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x - 0 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*\*\s*0$'),
     lambda m: f'{m.group(1)} = 0',               'x * 0 → 0'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*0\s*\*\s*(\w[\w.]*)$'),
     lambda m: f'{m.group(1)} = 0',               '0 * x → 0'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*/\s*1$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x / 1 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*//\s*1$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x // 1 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*\*\*\s*1$'),
     lambda m: f'{m.group(1)} = {m.group(2)}',   'x ** 1 → x'),
    (re.compile(r'^(\w[\w.]*)\s*=\s*(\w[\w.]*)\s*\*\*\s*0$'),
     lambda m: f'{m.group(1)} = 1',               'x ** 0 → 1'),
]


def _pass_algebraic_simplification(instrs: list) -> tuple[list, list]:
    result, changes = [], []
    for ins in instrs:
        if ins.get('is_label'):
            result.append(_clone(ins))
            continue
        code = ins['instr']
        applied = False
        for pat, transform, rule_name in _ALGE:
            m = pat.match(code)
            if m:
                new_code = transform(m)
                changes.append({'pass': f'Simplificación algebraica',
                                 'rule': rule_name,
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})
                r = _clone(ins)
                r['instr']      = new_code
                r['comment']    = rule_name
                r['_tag']       = 'modified'
                r['_technique'] = 'algebraic'
                result.append(r)
                applied = True
                break
        if not applied:
            result.append(_clone(ins))
    return result, changes


# ─────────────────────────────────────────────────────────────────────────────
# Pasada 4 — Propagación de copias
# ─────────────────────────────────────────────────────────────────────────────

def _pass_copy_propagation(instrs: list) -> tuple[list, list]:
    """Reemplaza usos de temporales de copia por su fuente original."""
    copy_map: dict[str, str] = {}
    result, changes = [], []

    for ins in instrs:
        if ins.get('is_label'):
            copy_map.clear()
            result.append(_clone(ins))
            continue
        code = ins['instr']
        new_code = code

        m = _BIN_RE.match(code)
        u = _UN_RE.match(code)
        c = _COPY_RE.match(code)

        if m:
            dst, a, op, b = m.groups()
            na, nb = copy_map.get(a, a), copy_map.get(b, b)
            if na != a or nb != b:
                new_code = f'{dst} = {na} {op} {nb}'
                changes.append({'pass': 'Propagación de copias',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})
        elif u:
            dst, op, a = u.groups()
            na = copy_map.get(a, a)
            if na != a:
                new_code = f'{dst} = {op} {na}'
                changes.append({'pass': 'Propagación de copias',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})
        elif c:
            dst, src = c.groups()
            ns = copy_map.get(src, src)
            if ns != src:
                new_code = f'{dst} = {ns}'
                changes.append({'pass': 'Propagación de copias',
                                 'before': code, 'after': new_code,
                                 'ln': ins.get('ln', 0)})

        fc = _COPY_RE.match(new_code)
        if fc:
            d2, s2 = fc.groups()
            if _is_temp(d2) and not _is_num(s2):
                copy_map[d2] = s2
            else:
                copy_map.pop(d2, None)

        r = _clone(ins)
        r['instr'] = new_code
        if new_code != code:
            r['_tag']       = 'modified'
            r['_technique'] = 'copy_propagation'
        result.append(r)
    return result, changes


# ─────────────────────────────────────────────────────────────────────────────
# Pasada 5 — Eliminación de código muerto
# ─────────────────────────────────────────────────────────────────────────────

def _pass_dead_code_elimination(instrs: list) -> tuple[list, list]:
    """Elimina asignaciones a temporales que no se usan más adelante."""
    # Recolectar todos los usos del lado derecho
    used: set[str] = set()
    for ins in instrs:
        if ins.get('is_label'):
            continue
        code = ins['instr']
        m = _BIN_RE.match(code)
        u = _UN_RE.match(code)
        c = _COPY_RE.match(code)
        if m:
            _, a, _, b = m.groups()
            used.add(a); used.add(b)
        elif u:
            _, _, a = u.groups()
            used.add(a)
        elif c:
            _, src = c.groups()
            used.add(src)
        else:
            for tok in re.findall(r'\b\w[\w.]*\b', code):
                used.add(tok)

    result, changes = [], []
    for ins in instrs:
        if ins.get('is_label'):
            result.append(_clone(ins))
            continue
        code = ins['instr']
        m = _BIN_RE.match(code)
        u = _UN_RE.match(code)
        c = _COPY_RE.match(code)
        dst = None
        if m:   dst = m.group(1)
        elif u: dst = u.group(1)
        elif c: dst = c.group(1)

        if dst and _is_temp(dst) and dst not in used:
            changes.append({'pass': 'Eliminación de código muerto',
                             'before': code, 'after': '(eliminado)',
                             'ln': ins.get('ln', 0)})
            continue  # no incluir en resultado
        result.append(_clone(ins))
    return result, changes


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada — punto fijo
# ─────────────────────────────────────────────────────────────────────────────

MAX_ITER = 5

def optimize(tac_instructions: list) -> dict:
    """
    Aplica las cinco pasadas en orden hasta convergencia.

    Retorna:
      {
        original:       list[dict],   # TAC sin cambios
        optimized:      list[dict],   # TAC optimizado
        changes:        list[dict],   # log de cada transformación
        stats: {
          original_count, optimized_count, removed,
          changes_count, passes_run, techniques: list[str]
        }
      }
    """
    original = [dict(i) for i in tac_instructions]
    instrs   = [dict(i) for i in tac_instructions]
    all_changes: list[dict] = []
    passes_run = 0

    for _ in range(MAX_ITER):
        prev_codes = [i['instr'] for i in instrs]
        prev_len   = len(instrs)

        instrs, c1 = _pass_constant_folding(instrs)
        instrs, c2 = _pass_constant_propagation(instrs)
        instrs, c3 = _pass_algebraic_simplification(instrs)
        instrs, c4 = _pass_copy_propagation(instrs)
        instrs, c5 = _pass_dead_code_elimination(instrs)

        batch = c1 + c2 + c3 + c4 + c5
        all_changes.extend(batch)
        passes_run += 1

        if [i['instr'] for i in instrs] == prev_codes and len(instrs) == prev_len:
            break

    def _non_label(lst):
        return [i for i in lst if not i.get('is_label')]

    orig_nl = _non_label(original)
    opti_nl = _non_label(instrs)
    techniques = list(dict.fromkeys(c['pass'] for c in all_changes))

    # Count occurrences per technique
    tech_counts: dict[str, int] = {}
    for c in all_changes:
        tech_counts[c['pass']] = tech_counts.get(c['pass'], 0) + 1

    return {
        'original':  original,
        'optimized': instrs,
        'changes':   all_changes,
        'stats': {
            'original_count':  len(orig_nl),
            'optimized_count': len(opti_nl),
            'removed':         len(orig_nl) - len(opti_nl),
            'changes_count':   len(all_changes),
            'passes_run':      passes_run,
            'techniques':      techniques,
            'tech_counts':     tech_counts,
        },
    }
