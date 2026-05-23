"""
Gramática Formal del Compilador — GLC (Gramática Libre de Contexto)
===================================================================
Definida en BNF (Backus-Naur Form).

Esta gramática es la especificación formal que implementa el parser.
El analizador sintáctico ascendente la consulta directamente:
  • La tabla de precedencia la usa el algoritmo shunting-yard.
  • Las reglas de producción documentan cada reducción que realiza
    el parser shift-reduce.

Notación BNF usada aquí:
  →   se deriva en
  |   alternativa
  *   cero o más repeticiones
  ε   cadena vacía (producción nula)
  "x" terminal literal
  X   no terminal (mayúscula o CamelCase)
"""

from collections import namedtuple

# ─────────────────────────────────────────────────────────────────────────────
# Tipos de datos de la gramática
# ─────────────────────────────────────────────────────────────────────────────

Rule = namedtuple('Rule', ['lhs', 'rhs', 'bnf'])
"""
  lhs : str        — No terminal del lado izquierdo (Left-Hand Side)
  rhs : list[str]  — Símbolos del lado derecho  (Right-Hand Side)
  bnf : str        — Representación legible en BNF (solo documentación)
"""

Prec = namedtuple('Prec', ['level', 'assoc'])
"""
  level : int  — Prioridad del operador (mayor número = más ligante)
  assoc : str  — Asociatividad: 'L' = izquierda  |  'R' = derecha
"""

# ─────────────────────────────────────────────────────────────────────────────
# Tabla de Precedencia de Operadores
# ─────────────────────────────────────────────────────────────────────────────
# Usada por el algoritmo Shunting-Yard para decidir cuándo REDUCIR vs DESPLAZAR.
#
# Ejemplo — por qué importa el nivel:
#   a + b * c
#   Al ver '*' (nivel 6) con '+' (nivel 5) en la pila → NO reducir '+' todavía
#   Al ver el final → reducir '*' primero (b*c), luego '+' (a + b*c) → correcto
#
# Ejemplo — por qué importa la asociatividad:
#   a ** b ** c
#   '**' es RIGHT (R) → NO reducir el '**' de la pila al ver otro '**'
#   Resultado: a ** (b ** c)  ← matemáticamente correcto

PRECEDENCE: dict[str, Prec] = {
    # Nivel 1 — Disyunción lógica (menor prioridad binaria)
    'or':  Prec(1, 'L'),  '||':  Prec(1, 'L'),

    # Nivel 2 — Conjunción lógica
    'and': Prec(2, 'L'),  '&&':  Prec(2, 'L'),

    # Nivel 3 — Igualdad / Desigualdad
    '==':  Prec(3, 'L'),  '!=':  Prec(3, 'L'),
    '===': Prec(3, 'L'),  '!==': Prec(3, 'L'),

    # Nivel 4 — Relacionales / Pertenencia
    '<':   Prec(4, 'L'),  '>':   Prec(4, 'L'),
    '<=':  Prec(4, 'L'),  '>=':  Prec(4, 'L'),
    'in':  Prec(4, 'L'),  'is':  Prec(4, 'L'),

    # Nivel 5 — Aditivos
    '+':   Prec(5, 'L'),  '-':   Prec(5, 'L'),

    # Nivel 6 — Multiplicativos
    '*':   Prec(6, 'L'),  '/':   Prec(6, 'L'),
    '%':   Prec(6, 'L'),  '//':  Prec(6, 'L'),

    # Nivel 7 — Potencia  (asociativa a la DERECHA: 2**3**4 = 2**(3**4))
    '**':  Prec(7, 'R'),

    # Nivel 8 — Operadores bit a bit
    '|':   Prec(8, 'L'),  '&':   Prec(8, 'L'),
    '^':   Prec(8, 'L'),  '<<':  Prec(8, 'L'),  '>>': Prec(8, 'L'),

    # Nivel 9 — Unarios (mayor prioridad, asociativos a la derecha)
    'not':     Prec(9, 'R'),
    '!':       Prec(9, 'R'),
    'unary-':  Prec(9, 'R'),
    '~':       Prec(9, 'R'),
}

# Operadores de asignación — tratados con prioridad 0 (mínima)
ASSIGN_OPS: frozenset = frozenset({
    '=', '+=', '-=', '*=', '/=', '%=',
    '**=', '//=', '&=', '|=', '^=',
})

# Operadores que son unarios cuando aparecen al inicio de expresión
UNARY_OPS: frozenset = frozenset({'not', '!', '-', '~'})

# ─────────────────────────────────────────────────────────────────────────────
# Gramática Libre de Contexto (GLC) — Reglas de Producción
# ─────────────────────────────────────────────────────────────────────────────

GRAMMAR: list[Rule] = [

    # ── Programa ─────────────────────────────────────────────────────────────
    Rule('Program', ['Decl', 'Program'],   'Program → Decl Program'),
    Rule('Program', [],                    'Program → ε'),

    # ── Declaraciones ────────────────────────────────────────────────────────
    Rule('Decl', ['FuncDef'],              'Decl → FuncDef'),
    Rule('Decl', ['ClassDef'],             'Decl → ClassDef'),
    Rule('Decl', ['VarDecl'],              'Decl → VarDecl'),
    Rule('Decl', ['Import'],               'Decl → Import'),
    Rule('Decl', ['Stmt'],                 'Decl → Stmt'),

    # ── Definición de Función ────────────────────────────────────────────────
    # Python
    Rule('FuncDef', ['"def"','ID','"("','Params','")"','":"','Block'],
         'FuncDef → "def" ID "(" Params ")" ":" Block'),
    # JavaScript
    Rule('FuncDef', ['"function"','ID','"("','Params','")"','Block'],
         'FuncDef → "function" ID "(" Params ")" Block'),
    # C / Java / C++
    Rule('FuncDef', ['Type','ID','"("','Params','")"','Block'],
         'FuncDef → Type ID "(" Params ")" Block'),

    # ── Definición de Clase ──────────────────────────────────────────────────
    Rule('ClassDef', ['"class"','ID','Block'],
         'ClassDef → "class" ID Block'),
    Rule('ClassDef', ['"class"','ID','"("','ID','")"','Block'],
         'ClassDef → "class" ID "(" ID ")" Block'),
    Rule('ClassDef', ['"class"','ID','"extends"','ID','Block'],
         'ClassDef → "class" ID "extends" ID Block'),

    # ── Declaración de Variable ──────────────────────────────────────────────
    Rule('VarDecl', ['Type','ID','"="','Expr','";"'],
         'VarDecl → Type ID "=" Expr ";"'),
    Rule('VarDecl', ['Type','ID','";"'],
         'VarDecl → Type ID ";"'),
    Rule('VarDecl', ['"let"','ID','"="','Expr'],
         'VarDecl → "let" ID "=" Expr'),
    Rule('VarDecl', ['"const"','ID','"="','Expr'],
         'VarDecl → "const" ID "=" Expr'),
    Rule('VarDecl', ['"var"','ID','"="','Expr'],
         'VarDecl → "var" ID "=" Expr'),

    # ── Importaciones ────────────────────────────────────────────────────────
    Rule('Import', ['"import"','ID'],
         'Import → "import" ID'),
    Rule('Import', ['"from"','ID','"import"','ID'],
         'Import → "from" ID "import" ID'),
    Rule('Import', ['"include"','STRING'],
         'Import → "include" STRING'),

    # ── Sentencias ───────────────────────────────────────────────────────────
    Rule('Stmt', ['IfStmt'],              'Stmt → IfStmt'),
    Rule('Stmt', ['WhileStmt'],           'Stmt → WhileStmt'),
    Rule('Stmt', ['ForStmt'],             'Stmt → ForStmt'),
    Rule('Stmt', ['ReturnStmt'],          'Stmt → ReturnStmt'),
    Rule('Stmt', ['TryStmt'],             'Stmt → TryStmt'),
    Rule('Stmt', ['Expr','";"'],          'Stmt → Expr ";"'),
    Rule('Stmt', ['Expr'],                'Stmt → Expr'),
    Rule('Stmt', ['"break"'],             'Stmt → "break"'),
    Rule('Stmt', ['"continue"'],          'Stmt → "continue"'),
    Rule('Stmt', ['"pass"'],              'Stmt → "pass"'),
    Rule('Stmt', ['"del"','Expr'],        'Stmt → "del" Expr'),
    Rule('Stmt', ['"assert"','Expr'],     'Stmt → "assert" Expr'),

    # ── If / Elif / Else ─────────────────────────────────────────────────────
    Rule('IfStmt', ['"if"','"("','Expr','")"','Block'],
         'IfStmt → "if" "(" Expr ")" Block'),
    Rule('IfStmt', ['"if"','"("','Expr','")"','Block','"else"','Block'],
         'IfStmt → "if" "(" Expr ")" Block "else" Block'),
    Rule('IfStmt', ['"if"','Expr','":"','Block'],
         'IfStmt → "if" Expr ":" Block'),
    Rule('IfStmt', ['"if"','Expr','":"','Block','"else"','":"','Block'],
         'IfStmt → "if" Expr ":" Block "else" ":" Block'),
    Rule('IfStmt', ['"if"','Expr','":"','Block','"elif"','Expr','":"','Block'],
         'IfStmt → "if" Expr ":" Block "elif" Expr ":" Block'),

    # ── While ────────────────────────────────────────────────────────────────
    Rule('WhileStmt', ['"while"','"("','Expr','")"','Block'],
         'WhileStmt → "while" "(" Expr ")" Block'),
    Rule('WhileStmt', ['"while"','Expr','":"','Block'],
         'WhileStmt → "while" Expr ":" Block'),

    # ── For ──────────────────────────────────────────────────────────────────
    Rule('ForStmt', ['"for"','"("','VarDecl','Expr','";"','Expr','")"','Block'],
         'ForStmt → "for" "(" VarDecl Expr ";" Expr ")" Block'),
    Rule('ForStmt', ['"for"','ID','"in"','Expr','":"','Block'],
         'ForStmt → "for" ID "in" Expr ":" Block'),

    # ── Return ───────────────────────────────────────────────────────────────
    Rule('ReturnStmt', ['"return"','Expr','";"'],  'ReturnStmt → "return" Expr ";"'),
    Rule('ReturnStmt', ['"return"','Expr'],         'ReturnStmt → "return" Expr'),
    Rule('ReturnStmt', ['"return"'],                'ReturnStmt → "return"'),

    # ── Try / Except ─────────────────────────────────────────────────────────
    Rule('TryStmt', ['"try"','Block','"except"','Block'],
         'TryStmt → "try" Block "except" Block'),
    Rule('TryStmt', ['"try"','Block','"catch"','"("','ID','")"','Block'],
         'TryStmt → "try" Block "catch" "(" ID ")" Block'),

    # ── Bloque ───────────────────────────────────────────────────────────────
    Rule('Block', ['"{"','Program','"}"'],  'Block → "{" Program "}"'),
    Rule('Block', ['Stmt'],                 'Block → Stmt'),

    # ── Expresiones ──────────────────────────────────────────────────────────
    # (implementadas por el algoritmo Shunting-Yard; listadas aquí como referencia)
    Rule('Expr', ['Expr','BinOp','Expr'],       'Expr → Expr BinOp Expr'),
    Rule('Expr', ['UnOp','Expr'],               'Expr → UnOp Expr'),
    Rule('Expr', ['ID','"("','ArgList','")"'],  'Expr → ID "(" ArgList ")"'),
    Rule('Expr', ['Expr','"["','Expr','"]"'],   'Expr → Expr "[" Expr "]"'),
    Rule('Expr', ['Expr','"."','ID'],           'Expr → Expr "." ID'),
    Rule('Expr', ['Primary'],                   'Expr → Primary'),

    # ── Primarios ────────────────────────────────────────────────────────────
    Rule('Primary', ['NUMBER'],                 'Primary → NUMBER'),
    Rule('Primary', ['STRING'],                 'Primary → STRING'),
    Rule('Primary', ['ID'],                     'Primary → ID'),
    Rule('Primary', ['"("','Expr','")"'],       'Primary → "(" Expr ")"'),
    Rule('Primary', ['"["','ArgList','"]"'],    'Primary → "[" ArgList "]"'),
    Rule('Primary', ['"true"'],                 'Primary → "true"'),
    Rule('Primary', ['"false"'],                'Primary → "false"'),
    Rule('Primary', ['"True"'],                 'Primary → "True"'),
    Rule('Primary', ['"False"'],                'Primary → "False"'),
    Rule('Primary', ['"null"'],                 'Primary → "null"'),
    Rule('Primary', ['"None"'],                 'Primary → "None"'),
    Rule('Primary', ['"undefined"'],            'Primary → "undefined"'),

    # ── Listas de argumentos ─────────────────────────────────────────────────
    Rule('ArgList', ['Expr','","','ArgList'],    'ArgList → Expr "," ArgList'),
    Rule('ArgList', ['Expr'],                   'ArgList → Expr'),
    Rule('ArgList', [],                         'ArgList → ε'),

    # ── Parámetros ───────────────────────────────────────────────────────────
    Rule('Params', ['Param','","','Params'],     'Params → Param "," Params'),
    Rule('Params', ['Param'],                   'Params → Param'),
    Rule('Params', [],                          'Params → ε'),
    Rule('Param',  ['Type','ID'],               'Param → Type ID'),
    Rule('Param',  ['ID'],                      'Param → ID'),

    # ── Tipos de dato (terminales keyword) ───────────────────────────────────
    Rule('Type', ['"int"'],     'Type → "int"'),
    Rule('Type', ['"float"'],   'Type → "float"'),
    Rule('Type', ['"double"'],  'Type → "double"'),
    Rule('Type', ['"char"'],    'Type → "char"'),
    Rule('Type', ['"bool"'],    'Type → "bool"'),
    Rule('Type', ['"void"'],    'Type → "void"'),
    Rule('Type', ['"string"'],  'Type → "string"'),

    # ── Operadores Binarios ───────────────────────────────────────────────────
    Rule('BinOp', ['"+"'],   'BinOp → "+"'),   Rule('BinOp', ['"-"'],   'BinOp → "-"'),
    Rule('BinOp', ['"*"'],   'BinOp → "*"'),   Rule('BinOp', ['"/"'],   'BinOp → "/"'),
    Rule('BinOp', ['"%"'],   'BinOp → "%"'),   Rule('BinOp', ['"**"'],  'BinOp → "**"'),
    Rule('BinOp', ['"//"'],  'BinOp → "//"'),  Rule('BinOp', ['"=="'],  'BinOp → "=="'),
    Rule('BinOp', ['"!="'],  'BinOp → "!="'),  Rule('BinOp', ['"<"'],   'BinOp → "<"'),
    Rule('BinOp', ['">"'],   'BinOp → ">"'),   Rule('BinOp', ['"<="'],  'BinOp → "<="'),
    Rule('BinOp', ['">="'],  'BinOp → ">="'),  Rule('BinOp', ['"&&"'],  'BinOp → "&&"'),
    Rule('BinOp', ['"||"'],  'BinOp → "||"'),  Rule('BinOp', ['"and"'], 'BinOp → "and"'),
    Rule('BinOp', ['"or"'],  'BinOp → "or"'),  Rule('BinOp', ['"in"'],  'BinOp → "in"'),
    Rule('BinOp', ['"is"'],  'BinOp → "is"'),

    # ── Operadores Unarios ────────────────────────────────────────────────────
    Rule('UnOp', ['"-"'],   'UnOp → "-"'),
    Rule('UnOp', ['"!"'],   'UnOp → "!"'),
    Rule('UnOp', ['"not"'], 'UnOp → "not"'),
    Rule('UnOp', ['"~"'],   'UnOp → "~"'),
]

# Índice de reglas por LHS (para búsqueda rápida en el parser)
RULES_BY_LHS: dict = {}
for _r in GRAMMAR:
    RULES_BY_LHS.setdefault(_r.lhs, []).append(_r)
