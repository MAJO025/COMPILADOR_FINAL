# Compilador Multi-Etapa — Semestre 5

Compilador educativo completo con interfaz web que implementa todas las fases del proceso de compilación. Soporta sintaxis tipo **Python**, **C/C++** y **JavaScript**. Funciona 100% offline.

---

## Requisitos

- Python 3.10 o superior
- pip

---

## Instalación y Arranque

### Windows
```bat
instalar_y_arrancar.bat
```

### Linux / macOS
```bash
chmod +x instalar_y_arrancar.sh
./instalar_y_arrancar.sh
```

### Manual
```bash
pip install flask pywebview
python app.py
```

Luego abre **http://localhost:5000** en tu navegador.

---

## Arquitectura del Proyecto

```
compilador/
├── app.py                    # Punto de entrada principal
├── requirements.txt          # Dependencias Python
├── instalar_y_arrancar.bat   # Script de arranque Windows
├── instalar_y_arrancar.sh    # Script de arranque Linux/macOS
├── backend/
│   ├── __init__.py
│   ├── lexer.py              # Analizador léxico (Regex + AFD)
│   ├── grammar.py            # Gramática formal BNF + tabla de precedencia
│   ├── parser.py             # Parser ascendente (Shunting-Yard + Shift-Reduce)
│   ├── ast_nodes.py          # Enriquecimiento y clasificación de tokens
│   ├── semantic.py           # Análisis semántico (Visitor sobre el AST)
│   ├── codegen.py            # Generación de código intermedio (TAC + Pila)
│   ├── optimizer.py          # Optimizador de código (5 pasadas)
│   ├── object_code.py        # Generación de código objeto (RISC ficticio)
│   └── server.py             # API REST Flask
└── frontend/
    ├── index.html            # Interfaz principal
    ├── assets/
    │   └── Logo_compilador.ico
    ├── css/
    │   ├── styles.css        # Estilos globales
    │   └── fonts.css         # Fuentes embebidas (offline)
    └── js/
        ├── api.js            # Comunicación con el backend
        ├── ast-renderer.js   # Visualización del AST en Canvas HTML5
        └── ui.js             # Gestión de UI, zoom y visualización por fase
```

---

## Pipeline de Compilación (6 Fases)

### 1. Análisis Léxico — `backend/lexer.py`

Implementado con **expresiones regulares** y un patrón maestro compilado (`re.compile`). Equivalente a un Autómata Finito Determinista (AFD) ejecutado en C por el motor de regex.

**Tokens reconocidos:**
| Tipo | Descripción | Ejemplos |
|------|-------------|---------|
| `keyword` | Palabras reservadas | `if`, `def`, `for`, `class`, `return` |
| `identifier` | Identificadores de usuario | `x`, `mi_variable`, `_privado` |
| `number` | Literales numéricos | `42`, `3.14`, `0xFF`, `0b1010`, `0o777` |
| `string` | Cadenas de texto | `"hola"`, `f"valor: {x}"`, `"""triple"""` |
| `operator` | Operadores (1–3 chars) | `+`, `==`, `**=`, `//=` |
| `symbol` | Delimitadores | `(`, `)`, `{`, `}`, `;`, `,` |
| `comment` | Comentarios | `# Python`, `// C`, `/* bloque */` |
| `unknown` | Error léxico | Carácter no reconocido |

**Características:**
- Soporte de f-strings, r-strings, b-strings, u-strings
- Números hexadecimales (`0xFF`), binarios (`0b1010`), octales (`0o777`)
- Comentarios de bloque (`/* */`), línea (`//`) y hash (`#`)
- Rastreo de línea y columna por token

---

### 2. Análisis Sintáctico — `backend/parser.py` + `backend/grammar.py`

Parser **ascendente (Bottom-Up)** que combina dos algoritmos:

#### a) Shunting-Yard (Dijkstra, 1961) — Expresiones

Usa dos pilas locales por invocación (`_out` y `_ops`):
- **SHIFT**: empuja operandos hoja a `_out`; operadores a `_ops`
- **REDUCE**: cuando un operador nuevo tiene menor/igual precedencia, combina los nodos ya construidos

Maneja correctamente:
- Precedencia de operadores (12 niveles, ver tabla abajo)
- Asociatividad izquierda y derecha (`**` es derecha)
- Operadores unarios (`-x`, `not x`, `!x`, `~x`)
- Llamadas a función (`f(a, b)`)
- Acceso a índice (`arr[i]`)
- Acceso a atributo (`obj.prop`)
- Lambdas (`lambda x, y: x + y`)
- Listas literales y comprensiones (`[x for x in range(10)]`)

#### b) Shift-Reduce con Gramática Explícita — Sentencias

Consulta las reglas de producción definidas en `grammar.py` y registra cada reducción en el log de análisis.

**Tabla de Precedencia de Operadores:**
| Nivel | Operadores | Asociatividad |
|-------|-----------|---------------|
| 1 | `or` `\|\|` | Izquierda |
| 2 | `and` `&&` | Izquierda |
| 3 | `==` `!=` `===` `!==` | Izquierda |
| 4 | `<` `>` `<=` `>=` `in` `is` | Izquierda |
| 5 | `\|` | Izquierda |
| 6 | `^` | Izquierda |
| 7 | `&` | Izquierda |
| 8 | `<<` `>>` | Izquierda |
| 9 | `+` `-` | Izquierda |
| 10 | `*` `/` `%` `//` | Izquierda |
| 11 | `**` | **Derecha** |
| 12 | `not` `!` `-` (unario) `~` | Derecha |

**Construcciones soportadas:**
- Funciones: `def` (Python), `function` (JS), tipo-retorno (C)
- Clases: Python, herencia `extends`
- Variables: `var`, `let`, `const`, tipo explícito (C-style)
- Control de flujo: `if/elif/else`, `while`, `for in` (Python), `for(;;)` (C)
- Excepciones: `try/except` (Python), `try/catch` (JS/C++)
- Importaciones: `import`, `from ... import`, `include`
- `break`, `continue`, `pass`, `return`, `del`, `assert`
- Bloques con llaves `{}` y por **indentación** (Python)

**Salida:** AST (Árbol de Sintaxis Abstracta) + log de producciones con BNF

---

### 3. Análisis Semántico — `backend/semantic.py`

Patrón **Visitor** sobre el AST. Mantiene una pila de scopes anidados.

**Verificaciones implementadas:**

| # | Verificación | Tipo |
|---|-------------|------|
| 1 | Variable usada sin declarar | Error |
| 2 | Redeclaración en el mismo scope | Error |
| 3 | Reasignación de constante (`const`) | Error |
| 4 | Parámetros duplicados en función | Error |
| 5 | Llamada a función no declarada | Error |
| 6 | Llamada a variable como función | Error |
| 7 | Número incorrecto de argumentos | Error |
| 8 | Tipo de argumento incorrecto | Error |
| 9 | Retorno de tipo incorrecto | Error |
| 10 | `return` fuera de función | Error |
| 11 | `break`/`continue` fuera de bucle | Error |
| 12 | División o módulo por cero literal | Error |
| 13 | Declaración estilo C inválida en Python | Error |
| 14 | Incompatibilidad de tipos (num vs string) | Error |
| 15 | Variable no asignada antes de uso | Advertencia |
| 16 | Shadowing de built-ins | Advertencia |
| 17 | No todos los caminos retornan valor | Advertencia |
| 18 | Punto y coma innecesario en Python | Advertencia (estilo) |

**Tabla de Símbolos:** cada símbolo registra `declared_type`, `inferred_type`, `use_count`, `is_func`, `is_const`, `is_param`, `arity`, `param_types`, `return_type`, número de línea.

**Inferencia de tipos:** el analizador infiere automáticamente el tipo de expresiones (`int`, `float`, `str`, `bool`, `null`, `any`).

---

### 4. Generación de Código Intermedio — `backend/codegen.py`

Genera **tres representaciones** simultáneamente:

#### a) TAC — Código de Tres Direcciones

Cada instrucción tiene a lo sumo una operación:
```
t1 = a + b
t2 = t1 * c
x = t2
```

Instrucciones generadas: asignaciones, operaciones binarias/unarias, `IF`/`IF_FALSE`/`GOTO`, `FUNC_BEGIN`/`FUNC_END`, `PARAM`/`ARG`/`CALL`, `RETURN`.

#### b) Código Basado en Pila

Traduce cada operación a instrucciones de pila:
```
PUSH a
PUSH b
ADD
STORE x
```

Instrucciones: `PUSH`, `POP`, `STORE`, `LOAD`, `ADD`/`SUB`/`MUL`/`DIV`/`MOD`/`POW`/`IDIV`, `NEG`, `AND`/`OR`, `EQ`/`NEQ`/`LT`/`GT`/`LEQ`/`GEQ`, `JUMP`/`JUMP_IF_FALSE`, `CALL`, `RETURN`, `DUP`, `ROT3`, `INDEX`, `LEN`.

#### c) Representación Textual del AST

Árbol ASCII con conectores `├──` / `└──`, anotaciones de tipo (`[meta]`) y número de línea.

---

### 5. Optimización — `backend/optimizer.py`

Cinco pasadas en **punto fijo** (se repite hasta convergencia, máximo 5 iteraciones):

| Pasada | Nombre | Descripción | Ejemplo |
|--------|--------|-------------|---------|
| 1 | Plegado de constantes | Evalúa operaciones con constantes en compilación | `t1 = 3 + 4` → `t1 = 7` |
| 2 | Propagación de constantes | Sustituye variables conocidas por su valor | `t2 = t1 * 2` → `t2 = 7 * 2` |
| 3 | Simplificación algebraica | Aplica identidades algebraicas | `x * 1 → x`, `x + 0 → x`, `x * 0 → 0`, `x ** 0 → 1` |
| 4 | Propagación de copias | Reemplaza temporales de copia por su fuente | `t3 = t2` + uso de `t3` → usa `t2` directo |
| 5 | Eliminación de código muerto | Elimina asignaciones a temporales sin uso | Elimina `t4 = ...` si `t4` nunca se usa |

**Traza de optimización:** genera hasta 500 frames con el estado de cada instrucción antes y después de cada pasada, para visualización educativa en el frontend.

**Estadísticas reportadas:** instrucciones originales, instrucciones optimizadas, instrucciones eliminadas, cambios totales, pasadas ejecutadas, técnicas aplicadas y conteo por técnica.

---

### 6. Generación de Código Objeto — `backend/object_code.py`

Produce ensamblador para una **arquitectura RISC ficticia de 8 registros de 32 bits**.

**Registros:**
| Registro | Uso |
|----------|-----|
| `R0` | Acumulador / resultado de función |
| `R1–R7` | Propósito general |
| `LR` | Dirección de retorno |

**Instrucciones soportadas:**
```
MOVI  Rn, #imm       ; carga inmediata
LOAD  Rn, [addr]     ; carga desde memoria
STORE Rn, [addr]     ; almacena en memoria
MOVE  Rd, Rs         ; copia entre registros
ADD / SUB / MUL / DIV / MOD / POW / IDIV  Rd, Ra, Rb
NEG   Rd, Ra         ; negación
NOT   Rd, Ra         ; not lógico
AND / OR  Rd, Ra, Rb ; lógica binaria
CMP   Ra, Rb         ; comparación (actualiza flags)
CMP_EQ / CMP_NE / CMP_LT / CMP_GT / CMP_LE / CMP_GE
SETF  Rn             ; resultado de comparación → registro
JMP   L              ; salto incondicional
JZ    L              ; salta si cero (IF_FALSE)
JNZ   L              ; salta si no cero (IF)
PUSH  Rn             ; apila registro
POP   Rn             ; desapila
CALL  func           ; llamada (resultado → R0)
RET                  ; retorna
HALT                 ; fin del programa
PROC  nombre / ENDP  ; directivas de procedimiento
.data / .code        ; secciones
```

**Asignador de registros:** asignación lineal con spilling automático cuando se agotan los 7 registros. Los variables se mapean a la sección `.data` con dirección base `0x1000`.

**Estadísticas:** instrucciones totales, registros usados, variables en memoria, etiquetas, ciclos estimados (instrucciones de multiplicación/división/llamada valen 3 ciclos).

---

## API REST

El servidor Flask expone dos endpoints:

### `POST /api/compilar`
Recibe el código fuente y ejecuta el pipeline completo.

**Request:**
```json
{ "codigo": "x = 5 + 3\nprint(x)" }
```

**Response:** JSON con todos los resultados de las 6 fases:
```json
{
  "tokens":        [...],
  "ast":           {...},
  "log":           [...],
  "nodeCount":     12,
  "errorCount":    0,
  "lang":          "python",
  "lines":         2,
  "chars":         18,
  "semErrors":     [...],
  "semWarnings":   [...],
  "semErrCount":   0,
  "semWarnCount":  0,
  "symbolTable":   {...},
  "semTotalUses":  3,
  "semTotalDecls": 1,
  "semScopeNames": ["global"],
  "codegen":       { "tac": [...], "stack": [...], "ast_text": [...], "stats": {...} },
  "optimization":  { "original": [...], "optimized": [...], "changes": [...], "trace": {...}, "stats": {...} },
  "object_code":   { "instructions": [...], "data_segment": [...], "register_table": [...], "stats": {...} }
}
```

**Timeout:** 8 segundos (devuelve error 408 si el código es demasiado complejo).

### `POST /api/exportar`
Descarga un archivo de texto (Tabla de Símbolos o Código Objeto).

**Request (JSON o form-data):**
```json
{ "content": "...", "filename": "tabla_simbolos.txt" }
```

**Response:** archivo descargable (`Content-Disposition: attachment`).

---

## Frontend

La interfaz web tiene una barra superior con botones para cambiar entre las 6 fases, un editor de código y un panel de resultados.

| Módulo | Descripción |
|--------|-------------|
| `api.js` | Comunicación AJAX con el backend Flask |
| `ast-renderer.js` | Visualización del AST en Canvas HTML5 con zoom y pan |
| `ui.js` | Gestión de estado de UI, renderizado por fase, zoom, exportación |

---

## Dependencias

| Paquete | Versión mínima | Uso |
|---------|---------------|-----|
| `flask` | 3.0.0 | Servidor web / API REST |
| `pywebview` | 5.0.0 | Ventana nativa de escritorio (opcional) |
| `pyinstaller` | 6.0.0 | Empaquetado en ejecutable standalone |
| `gunicorn` | 21.0.0 | Servidor WSGI para producción |

---

## Modo Escritorio vs Modo Web

- **Modo escritorio:** `pywebview` abre una ventana nativa apuntando a `http://localhost:5000`
- **Modo web:** si `pywebview` no está disponible, el servidor sigue corriendo y se accede por navegador
- **Modo Replit/cloud:** detecta `REPL_ID` y escucha en `0.0.0.0` en lugar de `localhost`

---

## Ejemplos de Código

### Python
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

resultado = factorial(5)
print(resultado)
```

### JavaScript
```javascript
function suma(a, b) {
    return a + b;
}
let x = suma(3, 4);
```

### C-style
```c
int suma(int a, int b) {
    return a + b;
}
int x = suma(3, 4);
```
