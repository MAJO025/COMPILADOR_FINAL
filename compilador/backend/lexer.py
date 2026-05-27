"""
Analizador Léxico — Implementación con Expresiones Regulares (Regex)
=====================================================================
Usa un único patrón maestro compilado con grupos nombrados + re.finditer().
Cada grupo corresponde a un tipo de token.

Ventajas sobre el scanner manual:
  • Un solo re.compile() → motor de regex ejecuta el AFD internamente en C
  • Orden de patrones es la "tabla de prioridades" del AFD
  • Mucho más conciso y sin riesgo de off-by-one en el avance de caracteres
  • Trivial de extender: agregar un patrón nuevo = una línea
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# Palabras clave del lenguaje (frozenset para búsqueda O(1))
# ─────────────────────────────────────────────────────────────────────────────

KEYWORDS: frozenset = frozenset({
    # Control de flujo
    'if', 'else', 'elif', 'for', 'while',
    'break', 'continue', 'return', 'pass', 'yield',
    # Declaradores
    'def', 'class', 'lambda', 'async', 'await', 'with',
    # Literales especiales Python
    'True', 'False', 'None',
    # Lógicos Python
    'not', 'and', 'or', 'is', 'in',
    # Importación
    'import', 'from', 'as',
    # Excepciones
    'try', 'except', 'finally', 'raise',
    # Ámbito / otros
    'global', 'nonlocal', 'del', 'assert', 'type',
    # Funciones built-in (resaltado)
    'print', 'input', 'range', 'len', 'open',
    'int', 'float', 'str', 'bool',
    'list', 'dict', 'set', 'tuple',
})

# ─────────────────────────────────────────────────────────────────────────────
# Patrones de tokens ordenados por prioridad
# ─────────────────────────────────────────────────────────────────────────────
# REGLA: el primer patrón que coincide gana.
# Por eso los tokens más específicos (/* */, """) van ANTES que los generales.

_PATTERNS: list[tuple[str, str]] = [

    # ── Comentarios ──────────────────────────────────────────────────────────
    # Bloque debe ir ANTES que la línea "//" para evitar match parcial
    ('BLOCK_CMT',  r'/\*[\s\S]*?\*/'),          # /* comentario de bloque */
    ('LINE_CMT',   r'//[^\n]*'),                 # // comentario de línea
    ('HASH_CMT',   r'#[^\n]*'),                  # # comentario Python/bash

    # ── Cadenas de texto ─────────────────────────────────────────────────────
    # Triple comilla ANTES que simple para que """ no matchee como tres ""
    ('TRIPLE_STR', r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''),

    # f-strings, r-strings, b-strings, combinaciones (Python)
    ('PREFIX_STR',
     r'[fFrRbBuU]{1,2}'
     r'(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')'),

    # Cadena regular con escapes (doble y simple)
    ('STRING',
     r'"[^"\\]*(?:\\.[^"\\]*)*"'
     r"|'[^'\\]*(?:\\.[^'\\]*)*'"),

    # ── Números ──────────────────────────────────────────────────────────────
    # Más específicos primero: hex/bin/oct antes que decimal
    ('NUMBER',
     r'0[xX][0-9a-fA-F][0-9a-fA-F_]*'      # Hexadecimal: 0xFF, 0xDEAD_BEEF
     r'|0[bB][01][01_]*'                     # Binario:     0b1010, 0b1111_0000
     r'|0[oO][0-7][0-7_]*'                   # Octal:       0o777
     r'|\d[\d_]*\.\d[\d_]*(?:[eE][+-]?\d+)?' # Real:        3.14, 1_000.5e-3
     r'|\d[\d_]*'),                           # Entero:      42, 1_000_000

    # ── Identificadores y palabras clave ─────────────────────────────────────
    # Debe ir DESPUÉS de números para que "3e5" no matchee 'e5' como WORD
    ('WORD', r'[a-zA-Z_\$][a-zA-Z0-9_\$]*'),

    # ── Operadores (de 3 a 1 carácter, mayor longitud primero) ───────────────
    # 3 caracteres: ===, !==, **=, //=
    ('OP3', r'===|!==|\*\*=|//='),

    # 2 caracteres: ==, !=, <=, >=, &&, ||, ++, --, +=, -=, *=, /=, %=,
    #               **,  //, ->, ::, <<, >>, &=, |=, ^=, ?., ??, =>
    ('OP2',
     r'==|!=|<=|>=|&&|\|\|'
     r'|\+\+|--'
     r'|\+=|-=|\*=|/=|%=|&=|\|=|\^='
     r'|\*\*|//|->|::|<<|>>|\?\.|=>'
     r'|\?\?'),

    # 1 carácter: + - * / % = < > ! & | ^ ~ @
    ('OP1', r'[+\-*/%=<>!&|^~@]'),

    # ── Separadores / Delimitadores ───────────────────────────────────────────
    ('SYM', r'[(){}\[\];:,\.\?\\]'),

    # ── Ignorar (no generan token) ────────────────────────────────────────────
    ('NEWLINE', r'\n'),
    ('SKIP',    r'[ \t\r]+'),

    # ── Error léxico ─────────────────────────────────────────────────────────
    # Captura cualquier carácter que no coincidió con ningún patrón anterior
    ('MISMATCH', r'.'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Compilación del patrón maestro (una sola vez al importar el módulo)
# ─────────────────────────────────────────────────────────────────────────────
# re.DOTALL  → el punto '.' también coincide con '\n' (necesario para /* ... */)

_MASTER_RE: re.Pattern = re.compile(
    '|'.join(f'(?P<{name}>{pat})' for name, pat in _PATTERNS),
    re.DOTALL,
)

# ─────────────────────────────────────────────────────────────────────────────
# Mapeo de grupos nombrados a tipos de token semánticos
# ─────────────────────────────────────────────────────────────────────────────

_KIND_TO_TYPE: dict[str, str | None] = {
    'BLOCK_CMT':  'comment',
    'LINE_CMT':   'comment',
    'HASH_CMT':   'comment',
    'TRIPLE_STR': 'string',
    'PREFIX_STR': 'string',
    'STRING':     'string',
    'NUMBER':     'number',
    'WORD':       None,       # → 'keyword' si está en KEYWORDS, si no 'identifier'
    'OP3':        'operator',
    'OP2':        'operator',
    'OP1':        'operator',
    'SYM':        'symbol',
    'MISMATCH':   'unknown',
    # ignorados (no producen token):
    'NEWLINE':    None,
    'SKIP':       None,
}

# ─────────────────────────────────────────────────────────────────────────────
# Función principal del lexer
# ─────────────────────────────────────────────────────────────────────────────

def lex(src: str) -> list[dict]:
    """
    Tokeniza el código fuente usando el patrón maestro regex.

    Algoritmo:
      1. re.finditer() recorre el texto izquierda → derecha
      2. En cada posición, el motor de regex prueba los grupos nombrados en orden
         (gracias al operador '|') — equivalente a las transiciones de un AFD
      3. El grupo que coincide determina el tipo de token
      4. Se rastrean línea y columna incrementalmente

    Retorna lista de dicts:
      {'t': tipo, 'v': valor, 'ln': línea, 'col': columna}
    """
    tokens: list[dict] = []
    line    = 1
    line_start = 0   # índice en src donde empieza la línea actual

    for m in _MASTER_RE.finditer(src):
        kind  = m.lastgroup          # nombre del grupo que coincidió
        value = m.group()            # texto capturado
        start = m.start()            # posición absoluta en src

        # Actualizar número de línea cuando encontramos salto de línea
        if kind == 'NEWLINE':
            line      += 1
            line_start = start + 1
            continue

        # Ignorar espacios en blanco
        if kind == 'SKIP':
            continue

        # Obtener tipo semántico del token
        tok_type = _KIND_TO_TYPE.get(kind)

        if tok_type is None:
            # Solo llega aquí el grupo WORD; determinar keyword vs identifier
            if kind == 'WORD':
                tok_type = 'keyword' if value in KEYWORDS else 'identifier'
            else:
                continue   # grupo ignorado (NEWLINE/SKIP ya se manejaron arriba)

        # Calcular columna (1-indexed)
        col = start - line_start + 1

        tokens.append({
            't':   tok_type,
            'v':   value,
            'ln':  line,
            'col': col,
        })

    return tokens
