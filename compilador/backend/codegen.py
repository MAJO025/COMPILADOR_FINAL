"""
Generador de Código Intermedio
===============================
Produce tres representaciones a partir del AST:

  1. TAC  — Código de Tres Direcciones
  2. STACK — Código Basado en Pila
  3. AST_TEXT — Visualización textual del AST

Recibe el mismo AST que genera backend/parser.py:
  { label, children, meta, id, ln }
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Helpers comunes
# ─────────────────────────────────────────────────────────────────────────────

_ARITH  = frozenset({'+', '-', '*', '/', '%', '**', '//', '<<', '>>'})
_COMPARE= frozenset({'==', '!=', '<', '>', '<=', '>=', '===', '!=='})
_LOGIC  = frozenset({'&&', '||', 'and', 'or'})
_UNARY  = frozenset({'-', '!', 'not', '~'})
_ASSIGN = frozenset({'=', '+=', '-=', '*=', '/=', '%=', '**=', '//='})

def _is_op(label: str) -> bool:
    return label in (_ARITH | _COMPARE | _LOGIC)

def _is_leaf(node: dict) -> bool:
    return not node.get('children')

def _label(node: dict) -> str:
    return str(node.get('label', '?'))


# ─────────────────────────────────────────────────────────────────────────────
# 1. CÓDIGO DE TRES DIRECCIONES (TAC)
# ─────────────────────────────────────────────────────────────────────────────

class TACGenerator:
    def __init__(self):
        self.instructions: list[dict] = []
        self._temp  = 0
        self._label = 0

    def _new_temp(self) -> str:
        self._temp += 1
        return f't{self._temp}'

    def _new_label(self) -> str:
        self._label += 1
        return f'L{self._label}'

    def _emit(self, instr: str, comment: str = '', ln: int = 0):
        self.instructions.append({'instr': instr, 'comment': comment, 'ln': ln})

    def _emit_label(self, lbl: str, ln: int = 0):
        self.instructions.append({'instr': f'{lbl}:', 'comment': '', 'ln': ln, 'is_label': True})

    # ── Visitores ──────────────────────────────────────────────────────────

    def visit(self, node: dict | None) -> str:
        """Visita un nodo y devuelve el lugar donde queda el resultado."""
        if node is None:
            return ''
        label    = _label(node)
        meta     = node.get('meta', '')
        children = node.get('children', [])
        ln       = node.get('ln', 0)

        # Hoja (literal / identificador)
        if _is_leaf(node):
            return label

        # ── Operación binaria ──────────────────────────────────────────────
        if _is_op(label) and len(children) == 2:
            left  = self.visit(children[0])
            right = self.visit(children[1])
            t = self._new_temp()
            self._emit(f'{t} = {left} {label} {right}', ln=ln)
            return t

        # ── Operación unaria ───────────────────────────────────────────────
        if label in _UNARY and len(children) == 1:
            operand = self.visit(children[0])
            t = self._new_temp()
            self._emit(f'{t} = {label}{operand}', ln=ln)
            return t

        # ── Asignación ────────────────────────────────────────────────────
        if label in _ASSIGN and len(children) == 2:
            target = _label(children[0])
            val    = self.visit(children[1])
            if label == '=':
                self._emit(f'{target} = {val}', ln=ln)
            else:
                op = label[:-1]
                t  = self._new_temp()
                self._emit(f'{t} = {target} {op} {val}', ln=ln)
                self._emit(f'{target} = {t}', ln=ln)
            return target

        # ── Definición de función (meta='func', label='def: nombre()') ────
        if meta == 'func' or label in ('def', 'function', 'FUNCTION') or label.startswith('def: ') or label.startswith('function: '):
            # Extraer nombre de función del label ('def: nombre()' → 'nombre')
            fname = label
            for prefix in ('def: ', 'function: '):
                if fname.startswith(prefix):
                    fname = fname[len(prefix):]
            fname = fname.split('(')[0].strip() or label

            # Separar parámetros del cuerpo: los params tienen meta vacío y sin hijos
            params     = [c for c in children if not c.get('children') and c.get('meta') in ('', None)]
            body_nodes = [c for c in children if c not in params]

            self._emit(f'FUNC_BEGIN {fname}',
                       comment=f'params: {", ".join(_label(p) for p in params) or "ninguno"}',
                       ln=ln)
            for p in params:
                self._emit(f'PARAM {_label(p)}', ln=ln)
            for b in body_nodes:
                self.visit(b)
            self._emit(f'FUNC_END {fname}', ln=ln)
            return fname

        # ── Llamada a función (meta='call') ───────────────────────────────
        if meta == 'call':
            # label = nombre de la función, children = argumentos directos
            arg_temps = [self.visit(a) for a in children]
            for a in arg_temps:
                self._emit(f'ARG {a}', ln=ln)
            t = self._new_temp()
            self._emit(f'{t} = CALL {label}, {len(arg_temps)}', ln=ln)
            return t

        # ── If / elif / else ──────────────────────────────────────────────
        if label in ('if', 'elif'):
            cond   = self.visit(children[0]) if children else '?'
            l_true = self._new_label()
            l_end  = self._new_label()
            self._emit(f'IF {cond} GOTO {l_true}', ln=ln)
            self._emit(f'GOTO {l_end}', ln=ln)
            self._emit_label(l_true, ln=ln)
            for ch in children[1:]:
                if _label(ch) != 'else':
                    self.visit(ch)
            for ch in children[1:]:
                if _label(ch) == 'else':
                    l_else = self._new_label()
                    self._emit(f'GOTO {l_else}', ln=ln)
                    self._emit_label(l_end, ln=ln)
                    l_end = l_else
                    self.visit(ch)
                    break
            self._emit_label(l_end, ln=ln)
            return ''

        # ── While ─────────────────────────────────────────────────────────
        if label == 'while':
            l_start = self._new_label()
            l_end   = self._new_label()
            self._emit_label(l_start, ln=ln)
            cond = self.visit(children[0]) if children else '?'
            self._emit(f'IF_FALSE {cond} GOTO {l_end}', ln=ln)
            for ch in children[1:]:
                self.visit(ch)
            self._emit(f'GOTO {l_start}', ln=ln)
            self._emit_label(l_end, ln=ln)
            return ''

        # ── For ───────────────────────────────────────────────────────────
        if label == 'for':
            l_start = self._new_label()
            l_end   = self._new_label()
            if len(children) >= 2 and _label(children[1]) == 'in':
                var      = _label(children[0])
                iterable = self.visit(children[2]) if len(children) > 2 else '?'
                idx      = self._new_temp()
                self._emit(f'{idx} = 0', comment='índice inicial', ln=ln)
                self._emit_label(l_start, ln=ln)
                t_cond = self._new_temp()
                self._emit(f'{t_cond} = {idx} < LEN({iterable})', ln=ln)
                self._emit(f'IF_FALSE {t_cond} GOTO {l_end}', ln=ln)
                self._emit(f'{var} = {iterable}[{idx}]', ln=ln)
                for ch in children[3:]:
                    self.visit(ch)
                self._emit(f'{idx} = {idx} + 1', ln=ln)
                self._emit(f'GOTO {l_start}', ln=ln)
            else:
                # for estilo C: init; cond; incr
                if children: self.visit(children[0])
                self._emit_label(l_start, ln=ln)
                cond = self.visit(children[1]) if len(children) > 1 else '1'
                self._emit(f'IF_FALSE {cond} GOTO {l_end}', ln=ln)
                for ch in children[3:]:
                    self.visit(ch)
                if len(children) > 2: self.visit(children[2])
                self._emit(f'GOTO {l_start}', ln=ln)
            self._emit_label(l_end, ln=ln)
            return ''

        # ── Return ────────────────────────────────────────────────────────
        if label == 'return':
            val = self.visit(children[0]) if children else ''
            self._emit(f'RETURN {val}', ln=ln)
            return val

        # ── Print / funciones especiales con 1 arg directo ────────────────
        if label == 'print':
            args = [self.visit(ch) for ch in children]
            for a in args:
                self._emit(f'ARG {a}', ln=ln)
            self._emit(f'CALL print, {len(args)}', ln=ln)
            return ''

        # ── Nodo bloque / programa: visitar hijos ─────────────────────────
        result = ''
        for ch in children:
            result = self.visit(ch)
        return result

    def generate(self, ast: dict | list) -> list[dict]:
        self.instructions = []
        self._temp  = 0
        self._label = 0
        if isinstance(ast, list):
            for node in ast:
                self.visit(node)
        else:
            self.visit(ast)
        return self.instructions


# ─────────────────────────────────────────────────────────────────────────────
# 2. CÓDIGO BASADO EN PILA (STACK)
# ─────────────────────────────────────────────────────────────────────────────

class StackGenerator:
    def __init__(self):
        self.instructions: list[dict] = []
        self._label = 0

    def _new_label(self) -> str:
        self._label += 1
        return f'L{self._label}'

    def _emit(self, instr: str, comment: str = '', ln: int = 0):
        self.instructions.append({'instr': instr, 'comment': comment, 'ln': ln})

    def _emit_label(self, lbl: str, ln: int = 0):
        self.instructions.append({'instr': f'{lbl}:', 'comment': '', 'ln': ln, 'is_label': True})

    def visit(self, node: dict | None):
        if node is None:
            return
        label    = _label(node)
        meta     = node.get('meta', '')
        children = node.get('children', [])
        ln       = node.get('ln', 0)

        # Hoja
        if _is_leaf(node):
            self._emit(f'PUSH {label}', ln=ln)
            return

        # Operación binaria
        if _is_op(label) and len(children) == 2:
            self.visit(children[0])
            self.visit(children[1])
            op_map = {
                '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV',
                '%': 'MOD', '**': 'POW', '//': 'IDIV',
                '==': 'EQ', '!=': 'NEQ', '<': 'LT', '>': 'GT',
                '<=': 'LEQ', '>=': 'GEQ',
                '&&': 'AND', '||': 'OR', 'and': 'AND', 'or': 'OR',
            }
            self._emit(op_map.get(label, label.upper()), ln=ln)
            return

        # Operación unaria
        if label in _UNARY and len(children) == 1:
            self.visit(children[0])
            self._emit('NEG' if label == '-' else label.upper(), ln=ln)
            return

        # Asignación
        if label in _ASSIGN and len(children) == 2:
            if label != '=':
                self._emit(f'LOAD {_label(children[0])}', ln=ln)
            self.visit(children[1])
            if label != '=':
                op_map = {'+=':'ADD','-=':'SUB','*=':'MUL','/=':'DIV','%=':'MOD','**=':'POW','//=':'IDIV'}
                self._emit(op_map.get(label, 'ADD'), ln=ln)
            self._emit(f'STORE {_label(children[0])}', ln=ln)
            return

        # Definición de función (meta='func', label='def: nombre()')
        if meta == 'func' or label in ('def', 'function', 'FUNCTION') or label.startswith('def: ') or label.startswith('function: '):
            fname = label
            for prefix in ('def: ', 'function: '):
                if fname.startswith(prefix):
                    fname = fname[len(prefix):]
            fname = fname.split('(')[0].strip() or label

            params     = [c for c in children if not c.get('children') and c.get('meta') in ('', None)]
            body_nodes = [c for c in children if c not in params]

            self._emit(f'FUNC_BEGIN {fname}',
                       comment=f'params: {", ".join(_label(p) for p in params) or "ninguno"}',
                       ln=ln)
            for p in params:
                self._emit(f'POP {_label(p)}', comment='recibir parámetro', ln=ln)
            for b in body_nodes:
                self.visit(b)
            self._emit(f'FUNC_END {fname}', ln=ln)
            return

        # Llamada a función (meta='call', label=nombre, children=argumentos)
        if meta == 'call':
            for a in children:
                self.visit(a)
            self._emit(f'CALL {label}, {len(children)}', ln=ln)
            return

        # If
        if label in ('if', 'elif'):
            self.visit(children[0]) if children else self._emit('PUSH 0')
            l_false = self._new_label()
            l_end   = self._new_label()
            self._emit(f'JUMP_IF_FALSE {l_false}', ln=ln)
            for ch in children[1:]:
                if _label(ch) != 'else':
                    self.visit(ch)
            self._emit(f'JUMP {l_end}', ln=ln)
            self._emit_label(l_false, ln=ln)
            for ch in children[1:]:
                if _label(ch) == 'else':
                    self.visit(ch)
            self._emit_label(l_end, ln=ln)
            return

        # While
        if label == 'while':
            l_start = self._new_label()
            l_end   = self._new_label()
            self._emit_label(l_start, ln=ln)
            self.visit(children[0]) if children else self._emit('PUSH 0')
            self._emit(f'JUMP_IF_FALSE {l_end}', ln=ln)
            for ch in children[1:]:
                self.visit(ch)
            self._emit(f'JUMP {l_start}', ln=ln)
            self._emit_label(l_end, ln=ln)
            return

        # For
        if label == 'for':
            l_start = self._new_label()
            l_end   = self._new_label()
            if len(children) >= 2 and _label(children[1]) == 'in':
                var = _label(children[0])
                self.visit(children[2]) if len(children) > 2 else self._emit('PUSH []')
                self._emit('DUP', comment='duplicar iterable para LEN', ln=ln)
                self._emit('LEN', ln=ln)
                self._emit('PUSH 0', comment='índice', ln=ln)
                self._emit_label(l_start, ln=ln)
                self._emit('DUP', ln=ln)
                self._emit('ROT3', ln=ln)
                self._emit('DUP_AT 2', ln=ln)
                self._emit('LT', ln=ln)
                self._emit(f'JUMP_IF_FALSE {l_end}', ln=ln)
                self._emit('DUP', ln=ln)
                self._emit('INDEX', ln=ln)
                self._emit(f'STORE {var}', ln=ln)
                for ch in children[3:]:
                    self.visit(ch)
                self._emit('PUSH 1', ln=ln)
                self._emit('ADD', comment='incrementar índice', ln=ln)
                self._emit(f'JUMP {l_start}', ln=ln)
            else:
                if children: self.visit(children[0])
                self._emit_label(l_start, ln=ln)
                self.visit(children[1]) if len(children) > 1 else self._emit('PUSH 1')
                self._emit(f'JUMP_IF_FALSE {l_end}', ln=ln)
                for ch in children[3:]:
                    self.visit(ch)
                if len(children) > 2: self.visit(children[2])
                self._emit(f'JUMP {l_start}', ln=ln)
            self._emit_label(l_end, ln=ln)
            return

        # Return
        if label == 'return':
            if children:
                self.visit(children[0])
            self._emit('RETURN', ln=ln)
            return

        # Print
        if label == 'print':
            for ch in children:
                self.visit(ch)
            self._emit(f'CALL print, {len(children)}', ln=ln)
            return

        # Bloque genérico
        for ch in children:
            self.visit(ch)

    def generate(self, ast: dict | list) -> list[dict]:
        self.instructions = []
        self._label = 0
        if isinstance(ast, list):
            for node in ast:
                self.visit(node)
        else:
            self.visit(ast)
        return self.instructions


# ─────────────────────────────────────────────────────────────────────────────
# 3. REPRESENTACIÓN TEXTUAL DEL AST
# ─────────────────────────────────────────────────────────────────────────────

def ast_to_text(node: Any, prefix: str = '', is_last: bool = True, depth: int = 0) -> list[str]:
    """Convierte el AST a una representación textual tipo árbol."""
    lines = []
    if node is None:
        return lines

    connector = '└── ' if is_last else '├── '
    extension = '    ' if is_last else '│   '

    if isinstance(node, list):
        for i, child in enumerate(node):
            lines += ast_to_text(child, prefix, i == len(node) - 1, depth)
        return lines

    label    = _label(node)
    meta     = node.get('meta', '')
    ln       = node.get('ln', 0)
    children = node.get('children', [])

    annotation = ''
    if meta:
        annotation = f'  [{meta}]'
    if ln:
        annotation += f'  :{ln}'

    lines.append(f'{prefix}{connector}{label}{annotation}')

    child_prefix = prefix + extension
    for i, child in enumerate(children):
        lines += ast_to_text(child, child_prefix, i == len(children) - 1, depth + 1)

    return lines


def generate_ast_text(ast: Any) -> list[str]:
    """Genera representación textual del AST completo."""
    lines = ['ÁRBOL DE SINTAXIS ABSTRACTA', '']
    if isinstance(ast, list):
        for i, node in enumerate(ast):
            lines += ast_to_text(node, '', i == len(ast) - 1)
    else:
        lines += ast_to_text(ast, '', True)
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada principal
# ─────────────────────────────────────────────────────────────────────────────

def generate_intermediate(ast: Any) -> dict:
    """
    Genera las tres representaciones de código intermedio.
    Retorna un dict con: tac, stack, ast_text, stats
    """
    tac_gen   = TACGenerator()
    stack_gen = StackGenerator()

    tac_instructions   = tac_gen.generate(ast)
    stack_instructions = stack_gen.generate(ast)
    ast_text_lines     = generate_ast_text(ast)

    tac_temps  = len({i['instr'].split('=')[0].strip()
                      for i in tac_instructions
                      if '=' in i['instr'] and i['instr'].split('=')[0].strip().startswith('t')
                      and not i.get('is_label')})
    tac_labels = len([i for i in tac_instructions if i.get('is_label')])

    stack_calls  = len([i for i in stack_instructions if 'CALL' in i['instr']])
    stack_labels = len([i for i in stack_instructions if i.get('is_label')])

    return {
        'tac':   tac_instructions,
        'stack': stack_instructions,
        'ast_text': ast_text_lines,
        'stats': {
            'tac_count':    len(tac_instructions),
            'tac_temps':    tac_temps,
            'tac_labels':   tac_labels,
            'stack_count':  len(stack_instructions),
            'stack_calls':  stack_calls,
            'stack_labels': stack_labels,
            'ast_nodes':    len(ast_text_lines),
        }
    }
