# Compilador — Semestre 5

Aplicación de escritorio y web que simula las etapas internas de un compilador real,
procesando código fuente escrito en Python y mostrando paso a paso lo que ocurre
desde que se escribe hasta que se convierte en instrucciones ejecutables.

---

## Tabla de contenidos

1. [¿Qué es un compilador?](#1-qué-es-un-compilador)
2. [Estructura del proyecto](#2-estructura-del-proyecto)
3. [Cómo ejecutar la aplicación](#3-cómo-ejecutar-la-aplicación)
4. [Etapas del compilador](#4-etapas-del-compilador)
   - [4.1 Análisis Léxico](#41-análisis-léxico)
   - [4.2 Análisis Sintáctico](#42-análisis-sintáctico)
   - [4.3 Análisis Semántico](#43-análisis-semántico)
   - [4.4 Código Intermedio](#44-código-intermedio)
   - [4.5 Optimización](#45-optimización)
5. [Arquitectura técnica](#5-arquitectura-técnica)
6. [Glosario de términos](#6-glosario-de-términos)
7. [Dependencias](#7-dependencias)

---

## 1. ¿Qué es un compilador?

Un **compilador** es un programa que traduce código fuente escrito por una persona
(por ejemplo, Python) a una forma que la computadora puede entender y ejecutar.

Este proceso no ocurre de golpe: el compilador pasa el código por varias **etapas**,
cada una con una responsabilidad específica. Esta aplicación implementa y visualiza
las primeras cinco de esas etapas.

```
Código fuente
      │
      ▼
 Análisis Léxico      → ¿Cuáles son las palabras?
      │
      ▼
 Análisis Sintáctico  → ¿Están bien ordenadas?
      │
      ▼
 Análisis Semántico   → ¿Tienen sentido?
      │
      ▼
 Código Intermedio    → Representación simplificada
      │
      ▼
 Optimización         → Versión más eficiente
```

---

## 2. Estructura del proyecto

```
compilador_semestre5/
│
├── app.py                        Punto de entrada — arranca el servidor
│
├── requirements.txt              Lista de librerías necesarias
│
├── instalar_y_arrancar.bat       Script de instalación para Windows
├── instalar_y_arrancar.sh        Script de instalación para Mac/Linux
│
├── backend/                      Toda la lógica del compilador (Python)
│   ├── server.py                 Servidor web (Flask) — recibe el código y responde
│   ├── lexer.py                  Etapa 1: Análisis Léxico
│   ├── parser.py                 Etapa 2: Análisis Sintáctico
│   ├── grammar.py                Reglas gramaticales usadas por el parser
│   ├── ast_nodes.py              Funciones auxiliares para el árbol sintáctico
│   ├── semantic.py               Etapa 3: Análisis Semántico
│   ├── codegen.py                Etapa 4: Generación de Código Intermedio
│   └── optimizer.py              Etapa 5: Optimización del código intermedio
│
└── frontend/                     La interfaz visual (lo que ve el usuario)
    ├── index.html                Página principal
    ├── assets/
    │   └── Logo_compilador.ico   Ícono de la aplicación
    ├── css/
    │   ├── styles.css            Estilos visuales de la aplicación
    │   └── fonts.css             Tipografías
    └── js/
        ├── ui.js                 Controla la interfaz: pestañas, botones, limpieza
        ├── api.js                Se comunica con el backend y renderiza resultados
        └── ast-renderer.js       Dibuja el árbol sintáctico en pantalla
```

---

## 3. Cómo ejecutar la aplicación

### Requisitos previos
- Tener **Python 3.10 o superior** instalado.

### Pasos

**Windows:**
```
Doble clic en instalar_y_arrancar.bat
```

**Mac / Linux:**
```bash
chmod +x instalar_y_arrancar.sh
./instalar_y_arrancar.sh
```

**Manual (cualquier sistema):**
```bash
pip install -r requirements.txt
python app.py
```

Una vez iniciado, abre tu navegador en: **http://localhost:5000**

> Si tienes `pywebview` instalado, se abrirá automáticamente como ventana de escritorio.

---

## 4. Etapas del compilador

### 4.1 Análisis Léxico

**Archivo:** `backend/lexer.py`  
**Pestaña en la app:** *Léxico*

#### ¿Qué hace?
Divide el código fuente en **tokens**: las unidades mínimas de significado del
lenguaje, equivalente a como un lector humano reconoce palabras en una oración.

Por ejemplo, el código:
```python
x = 10 + y
```
Produce los tokens:
| Token | Tipo |
|-------|------|
| `x` | Identificador |
| `=` | Operador |
| `10` | Número |
| `+` | Operador |
| `y` | Identificador |

#### Categorías de tokens reconocidas
| Categoría | Ejemplos |
|-----------|---------|
| **Identificador** | `x`, `nombre`, `mi_variable` |
| **Literal** | `"hola"`, `'mundo'`, `"""texto largo"""` |
| **Operador** | `+`, `-`, `*`, `/`, `==`, `!=`, `>=` |
| **Palabra clave** | `if`, `else`, `for`, `while`, `def`, `class`, `return` |
| **Comentario** | `# esto es un comentario` |
| **Separador** | `(`, `)`, `[`, `]`, `:`, `,` |
| **Número** | `42`, `3.14`, `0xFF` |
| **No identificado** | Cualquier símbolo que el lexer no reconoce |

#### Cómo funciona internamente
Utiliza **expresiones regulares** (regex): patrones de texto que describen la forma
de cada tipo de token. El lexer aplica estos patrones uno por uno sobre el código
fuente hasta clasificar cada carácter.

#### Lo que muestra la app
- Tabla completa de tokens con su tipo, valor y número de línea.
- Gráfica de torta con el porcentaje de cada categoría.
- Conteo de errores léxicos (caracteres no reconocidos).

---

### 4.2 Análisis Sintáctico

**Archivo:** `backend/parser.py` y `backend/grammar.py`  
**Pestaña en la app:** *Sintáctico*

#### ¿Qué hace?
Verifica que los tokens estén ordenados correctamente según las **reglas del
lenguaje**, de la misma forma en que la gramática del español dice que un sujeto
va antes del verbo. Si el orden es correcto, construye el **AST**.

#### ¿Qué es el AST?
**AST** significa *Abstract Syntax Tree* (Árbol de Sintaxis Abstracta). Es una
representación del código en forma de árbol donde:
- Cada **nodo** representa una operación o estructura (una suma, una función, un `if`).
- Cada **hoja** (nodo sin hijos) representa un valor concreto (un número, un nombre de variable).

Ejemplo para `x = 10 + y`:
```
      Asignación
      /        \
     x         Suma
              /    \
            10      y
```

#### Algoritmo utilizado
El parser es **ascendente (bottom-up)**: en lugar de empezar por la regla más
general e ir bajando (como hacen los parsers más simples), este parte de los
tokens individuales y los va combinando hacia arriba hasta formar la estructura
completa. Usa dos técnicas:

- **Shunting-Yard** (Dijkstra, 1961): para analizar expresiones matemáticas con
  prioridad de operadores (`*` antes que `+`, etc.).
- **Shift-Reduce**: para analizar sentencias completas (`if`, `for`, `def`, etc.)
  usando las reglas de `grammar.py`.

#### Lo que muestra la app
- Árbol sintáctico dibujado visualmente (con zoom y desplazamiento).
- Log de producciones: cada regla gramatical que se aplicó.
- Conteo de nodos, producciones y errores sintácticos.

---

### 4.3 Análisis Semántico

**Archivo:** `backend/semantic.py`  
**Pestaña en la app:** *Semántico*

#### ¿Qué hace?
Verifica que el código tenga **sentido lógico**, no solo que esté bien escrito
formalmente. El análisis léxico y sintáctico son como revisar ortografía y
gramática; el semántico es como revisar si lo que se dice tiene coherencia.

#### Verificaciones que realiza
| Tipo de error | Ejemplo que lo dispara |
|---------------|----------------------|
| Variable no declarada | Usar `z` sin haberla definido |
| Redeclaración de variable | Declarar la misma variable dos veces en el mismo ámbito |
| Variable usada antes de asignarse | `print(x)` antes de `x = 5` |
| Tipos incompatibles | Sumar un número con un texto: `5 + "hola"` |
| Aridad incorrecta | Llamar `mi_funcion(1, 2)` cuando solo acepta 1 argumento |
| División por cero | `x = 10 / 0` literal |
| `break`/`continue` fuera de bucle | Usar `break` fuera de un `for` o `while` |
| `return` fuera de función | Usar `return` en el nivel principal del programa |
| Sobrescritura de built-in | Nombrar una variable `print = 5` |
| Parámetros duplicados | `def f(x, x):` |

#### Tabla de símbolos
Durante el análisis semántico se construye una **tabla de símbolos**: un registro
de todas las variables y funciones declaradas, incluyendo su tipo, en qué ámbito
fueron declaradas y cuántas veces se usaron.

#### Lo que muestra la app
- Lista de errores semánticos con número de línea.
- Lista de advertencias (estilo, usos cuestionables).
- Tabla de símbolos completa con tipo, usos y ámbito.

---

### 4.4 Código Intermedio

**Archivo:** `backend/codegen.py`  
**Pestaña en la app:** *Cód. Intermedio*

#### ¿Qué hace?
Convierte el AST en instrucciones más simples, independientes del lenguaje de
destino. Es un paso previo a generar código máquina real. La aplicación produce
dos formatos:

#### TAC — Código de Tres Direcciones
Cada instrucción tiene la forma `resultado = operando1 operador operando2`.
Las expresiones complejas se descomponen en pasos simples usando variables
temporales (`t1`, `t2`, ...).

Ejemplo: `x = (a + b) * c`
```
t1 = a + b
t2 = t1 * c
x  = t2
```

#### Código basado en pila
Versión alternativa que usa una **pila** (stack) de operandos. Cada instrucción
empuja (`PUSH`) o saca (`POP`) valores de la pila. Es la base de lenguajes como
Java (bytecode de la JVM).

Ejemplo: `x = a + b`
```
PUSH a
PUSH b
ADD
POP x
```

#### Lo que muestra la app
- Panel izquierdo: TAC original instrucción por instrucción.
- Panel derecho: código basado en pila.
- Botón de exportar: descarga el TAC como archivo `.tac`.

---

### 4.5 Optimización

**Archivo:** `backend/optimizer.py`  
**Pestaña en la app:** *Optimización*

#### ¿Qué hace?
Aplica cinco técnicas para producir un TAC más eficiente: menos instrucciones,
sin cálculos repetidos, sin código que nunca se ejecuta.

#### Las cinco pasadas de optimización

**Pasada 1 — Plegado de constantes (Constant Folding)**  
Si una operación involucra solo constantes conocidas, se calcula en tiempo de
compilación, no en tiempo de ejecución.
```
# Antes       →  Después
t1 = 3 + 5    →  t1 = 8
t2 = t1 * 2   →  t2 = 16
```

**Pasada 2 — Propagación de constantes (Constant Propagation)**  
Si una variable siempre tiene el mismo valor, se reemplaza por ese valor
directamente donde se usa.
```
# Antes       →  Después
x = 10
y = x + 5    →  y = 10 + 5  →  y = 15
```

**Pasada 3 — Simplificación algebraica (Algebraic Simplification)**  
Reglas matemáticas que reducen expresiones sin necesidad de calcular nada.
```
x * 1   →  x
x + 0   →  x
x * 0   →  0
x ** 1  →  x
```

**Pasada 4 — Propagación de copias (Copy Propagation)**  
Si una variable es solo una copia de otra, se reemplaza directamente.
```
# Antes       →  Después
a = b
c = a + 1    →  c = b + 1
```

**Pasada 5 — Eliminación de código muerto (Dead Code Elimination)**  
Elimina instrucciones cuyos resultados nunca se usan. Si calculas algo pero
no lo lees en ningún lado, esa instrucción sobra.
```
# t3 se calcula pero nunca se usa → se elimina
t3 = x * 2      ← ELIMINADO
resultado = y + 1
```

#### Modo de ejecución: punto fijo
Las cinco pasadas se repiten en ciclo hasta que ninguna produce cambios nuevos
(máximo 20 repeticiones). Esto garantiza que las optimizaciones se encadenen:
el resultado de una pasada puede habilitar otra.

#### Lo que muestra la app
- Comparativa lado a lado: TAC original vs TAC optimizado.
- Las instrucciones eliminadas aparecen tachadas en rojo.
- Botón "Exportar" y "Copiar al portapapeles".

---

## 5. Arquitectura técnica

La aplicación tiene dos partes que se comunican entre sí:

```
┌─────────────────────────────────────┐     HTTP/JSON     ┌──────────────────────┐
│           FRONTEND                  │ ◄───────────────► │       BACKEND        │
│  HTML + CSS + JavaScript            │                   │   Python + Flask     │
│                                     │                   │                      │
│  ui.js         → interfaz general   │  POST /api/compilar  server.py → orquesta│
│  api.js        → llama al backend   │  POST /api/exportar  lexer.py  → tokens  │
│  ast-renderer.js → dibuja el árbol  │                   │  parser.py → AST     │
└─────────────────────────────────────┘                   │  semantic.py → errores│
                                                          │  codegen.py → TAC    │
                                                          │  optimizer.py → opt. │
                                                          └──────────────────────┘
```

Cuando el usuario presiona **Compilar**:
1. El frontend envía el código fuente al backend vía HTTP.
2. El backend ejecuta las 5 etapas en secuencia.
3. Devuelve todos los resultados en un solo JSON.
4. El frontend renderiza cada pestaña con su parte del resultado.

El análisis completo tiene un **límite de 8 segundos**. Si el código es
demasiado complejo y tarda más, se devuelve un error de tiempo excedido.

---

## 6. Glosario de términos

| Término | Definición |
|---------|-----------|
| **Token** | Unidad mínima de significado en el código: una palabra clave, un número, un operador, etc. |
| **Lexer / Analizador léxico** | Módulo que divide el código en tokens. |
| **Parser / Analizador sintáctico** | Módulo que verifica el orden de los tokens y construye el AST. |
| **AST** | *Abstract Syntax Tree*. Árbol que representa la estructura lógica del programa. |
| **Gramática** | Conjunto de reglas que definen qué secuencias de tokens son válidas en el lenguaje. |
| **Producción gramatical** | Una regla específica de la gramática, como `sentencia → if expresión bloque`. |
| **Shift-Reduce** | Técnica de parsing: "shift" apila el token actual; "reduce" combina tokens en una estructura mayor. |
| **Shunting-Yard** | Algoritmo de Dijkstra para analizar expresiones con prioridad de operadores usando dos pilas. |
| **Semántica** | El significado del código, más allá de su forma: tipos correctos, variables declaradas, etc. |
| **Tabla de símbolos** | Registro de todas las variables y funciones del programa con su tipo y ámbito. |
| **Ámbito / Scope** | El contexto donde una variable existe: global, dentro de una función, dentro de un bloque. |
| **Aridad** | Cantidad de argumentos que acepta una función. |
| **Built-in** | Función o variable que ya viene definida en el lenguaje (ej: `print`, `len`, `range`). |
| **TAC** | *Three-Address Code*. Código Intermedio donde cada instrucción tiene máximo un operador y dos operandos. |
| **Variable temporal** | Variable auxiliar (`t1`, `t2`, ...) creada por el compilador para almacenar resultados intermedios. |
| **Pila / Stack** | Estructura de datos tipo "plato apilado": el último en entrar es el primero en salir (LIFO). |
| **Constant Folding** | Optimización: calcular operaciones entre constantes en tiempo de compilación. |
| **Constant Propagation** | Optimización: reemplazar variables de valor fijo por su valor directo. |
| **Copy Propagation** | Optimización: eliminar variables que son solo copias de otras. |
| **Dead Code Elimination** | Optimización: eliminar instrucciones cuyos resultados nunca se usan. |
| **Algebraic Simplification** | Optimización: aplicar reglas matemáticas para simplificar expresiones (`x * 1 = x`). |
| **Punto fijo** | Se repite un proceso hasta que no produce más cambios. Garantiza que todas las optimizaciones posibles se aplicaron. |
| **Flask** | Librería de Python para crear servidores web. Maneja las rutas `/api/compilar` y `/api/exportar`. |
| **pywebview** | Librería que permite abrir una ventana de escritorio que muestra una página web local. |
| **JSON** | Formato de texto para intercambiar datos entre el frontend y el backend. |
| **Regex / Expresión regular** | Patrón de texto que describe la forma de una cadena (ej: "empieza con una letra, seguida de letras o números"). |
| **Bottom-up parsing** | Estrategia de parsing que parte de los tokens y construye hacia arriba hasta la raíz del árbol. |
| **AFD** | *Autómata Finito Determinista*. Máquina de estados que el motor de regex usa internamente para reconocer patrones. |

---

## 7. Dependencias

| Librería | Versión mínima | Para qué se usa |
|----------|---------------|-----------------|
| `flask` | 3.0.0 | Servidor web que sirve la app y expone la API del compilador |
| `pywebview` | 5.0.0 | Abrir la app como ventana de escritorio nativa (opcional) |
| `pyinstaller` | 6.0.0 | Empaquetar la app como ejecutable `.exe` o `.app` (opcional) |

Las tres librerías se instalan con:
```bash
pip install -r requirements.txt
```

> `pywebview` y `pyinstaller` son opcionales: si no están instaladas, la app
> funciona igual abriendo http://localhost:5000 en cualquier navegador.
