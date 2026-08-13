# Guía de importación de Excel: descompuestos de partidas (formato CYPE)

Este documento explica **cómo deben ser los archivos Excel que se suben a la
aplicación** y **cómo funciona todo el proceso**: lectura, clasificación de
gastos, cálculos, edición de precios y conservación de los datos.

> Resumen rápido: cada archivo `.xlsx` contiene **una partida** con su
> descompuesto de costes (recursos por grupo). La app lee el archivo sin
> perder **ninguna fila ni columna**, clasifica los gastos en **materiales,
> mano de obra, directos complementarios y otros**, y permite **editar
> rendimientos y precios** recalculando toda la cascada de importes con las
> mismas reglas que usan las fórmulas del Excel.

---

## 1. Qué archivos acepta la aplicación

| Requisito | Detalle |
| --- | --- |
| Formato | `.xlsx` (Excel) sin contraseña |
| Contenido | **Una partida por archivo** (una hoja con su descompuesto) |
| Varios a la vez | Sí: se pueden subir varios archivos juntos; cada uno se convierte en una partida del presupuesto |
| Detección | Automática: la app reconoce el formato por sus encabezados (`Código`, `Unidad`, `Descripción`, `Rendimiento`, `Precio unitario`, `Importe`) |
| Tamaño máximo | 8 MB por archivo |

Ejemplos reales incluidos en el repositorio:

- `DPT020.xlsx` — partida de demolición, **solo mano de obra** (+ complementarios).
- `RBE010c8_0_1_1c7_0_1_1c10_0_0.xlsx` — capa base de mortero, **con materiales** y mano de obra (+ complementarios y bloque de normativa).

**Importante:** no todas las partidas tienen gastos de materiales. La app
está preparada para ambos tipos y refleja la composición real de gastos en
cada caso (materiales a 0 cuando no existen).

---

## 2. Anatomía del archivo

Todos los descompuestos comparten la misma estructura, aunque el número de
columnas puede variar (ver sección 4):

```text
Fila 1-2  (vacías / márgenes)
Fila 3    CABECERA DE LA PARTIDA →  Código | Unidad | Título
Fila 5    DESCRIPCIÓN TÉCNICA larga de la partida
Fila 8    ENCABEZADOS DE LA TABLA → Código · Unidad · Descripción · Rendimiento · Precio unitario · Importe
Fila 9+   GRUPOS Y RECURSOS:
            1  Materiales                      ← fila de grupo
               mt...  recurso (material)       ← filas de recurso
               ...
               Subtotal materiales:            ← fila de subtotal
            2  Mano de obra                    ← fila de grupo
               mo...  recurso (trabajador)
               ...
               Subtotal mano de obra:
            3  Costes directos complementarios ← fila de grupo
               %   Costes directos compl.      ← fila de porcentaje
          Costes directos (1+2+3):             ← fila de TOTAL
Fila 23+  BLOQUES EXTRA (opcionales): normativa/marcado CE, coste de
          mantenimiento decenal, etc.
```

### Tipos de fila que distingue la aplicación

| Tipo | Ejemplo | Cómo se trata |
| --- | --- | --- |
| `cabecera` | Código/unidad/título de la partida, descripción técnica | Identifica la partida (código, unidad, nombre y descripción) |
| `encabezado` | `Código · Unidad · Descripción · Rendimiento · Precio unitario · Importe` | Marca dónde empieza la tabla y define la posición de cada columna |
| `grupo` | `1 · Materiales`, `2 · Mano de obra` | Abre un grupo; todos los recursos siguientes pertenecen a él |
| `recurso` | `mo039 · h · Oficial 1ª revocador · 0,516 · 25,28 · 13,04` | Línea de coste editable (ver sección 7) |
| `subtotal` | `Subtotal mano de obra: 20,52` | Derivado: suma de los importes del grupo. **Nunca se suma aparte** (evita duplicar) |
| `total` | `Costes directos (1+2+3): 23,98` | Coste directo final de la partida |
| `otro` | Bloque de normativa EN 998-1, mantenimiento decenal | Se conserva íntegro en la matriz, sin tratamiento de coste |
| `vacia` | Filas en blanco de separación | Se conservan para no alterar el layout |

---

## 3. Qué significa cada columna (semántica)

La columna **Unidad** de un recurso indica la unidad *del propio recurso*
(hora de trabajador, kg de cemento, m de junquillo…). El **Rendimiento**
expresa cuántas unidades de ese recurso se consumen **por cada unidad de la
partida** (la partida da el precio final por su unidad: m², m³, ml…). El
**Precio unitario** es lo que cuesta una unidad del recurso. El **Importe**
es el coste de ese recurso por unidad de partida.

| Campo | Significado | Ej. mano de obra | Ej. material (cemento) |
| --- | --- | --- | --- |
| **Código** | Identificador del recurso en la base de precios (`mo…` mano de obra, `mt…` materiales) | `mo039` | `mt...` |
| **Unidad** | Unidad del recurso | `h` (hora) | `kg` |
| **Descripción** | Nombre del recurso | Oficial 1ª revocador | Cemento |
| **Rendimiento** | Cantidad de recurso por unidad de partida | `0,537` h por m² | `8,500` kg por m² |
| **Precio unitario** | Precio de 1 unidad del recurso | `24,41` $/hora | `0,23` $/kg |
| **Importe** | `Rendimiento × Precio unitario` = coste del recurso por unidad de partida | `13,11` $/m² | `1,96` $/m² |

**Regla fundamental:**

```text
Importe del recurso = Rendimiento × Precio unitario
```

Por eso, si un trabajador o un material sube o baja de precio, basta con
cambiar el **Precio unitario** (o el **Rendimiento**) y la aplicación
recalcula el importe y todos los totales derivados (ver sección 7).

---

## 4. Los dos layouts conocidos (y cualquier variante futura)

El exportador de CYPE no usa una única disposición de columnas. La app **no
tiene posiciones fijas**: localiza las columnas buscando la fila de
encabezados y leyendo en qué columna está cada campo.

### Layout de 8 columnas — `DPT020.xlsx`

| A | B | C | D | E | F | G | H |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Código | · | · | Unidad | Descripción | Rendimiento | Precio unitario | Importe |

### Layout de 10 columnas — `RBE010…xlsx` (con columnas separadoras)

| A | B | C | D | E | F | G | H | I | J |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Código | · | Unidad | · | Descripción | · | Rendimiento | · | Precio unitario | Importe |

En el de 10 columnas, B, D, F y H son separadores estrechos sin datos.

**Consecuencia:** cualquier archivo que respete los seis encabezados
(`Código, Unidad, Descripción, Rendimiento, Precio unitario, Importe`) se
importará correctamente, aunque el exportador cambie el layout. El título de
la partida también se localiza de forma flexible (va en C3 en el layout de 8
columnas y en D3 en el de 10, por las celdas combinadas).

---

## 5. Qué se conserva del archivo (garantía de no pérdida)

Al importar, la aplicación guarda:

1. **Todas las filas físicas** del libro, incluidas las vacías, la fila de
   título, la descripción técnica, los subtotales, el total y los bloques
   extra (normativa EN, mantenimiento decenal…).
2. **Todas las columnas** (A, B, C… hasta la última con datos).
3. **Las fórmulas originales** de cada celda (visibles al pasar el cursor
   sobre la insignia `fx` en la matriz).
4. **Los rangos de celdas combinadas** (listados en la vista).
5. **El archivo .xlsx original**, guardado en el servidor y descargable con
   el botón «Descargar Excel original».

Nada se aplana ni se recorta: la matriz completa puede consultarse en la
vista «Matriz original completa» del descompuesto de la partida.

---

## 6. Clasificación de los gastos

Cada recurso se clasifica en una de **cuatro categorías**, según su grupo
(apoyándose en el prefijo del código cuando el grupo no es concluyente):

| Categoría | Cuándo | Ejemplos |
| --- | --- | --- |
| **Materiales** | Grupo con «material», o código `mt…` | Cemento, mortero, junquillos, agua |
| **Mano de obra** | Grupo con «mano de obra»/«personal», o código `mo…` | Oficial, peón |
| **Directos complementarios** | Grupo con «complementario» | La línea de `%` sobre los subtotales |
| **Otros** | Cualquier otro grupo | Maquinaria, medios auxiliares… |

Partidas **sin materiales** (p. ej. `DPT020`): la categoría Materiales queda
a 0 y los gastos se reparten entre mano de obra y complementarios. La app lo
refleja exactamente así, sin inventar materiales.

---

## 7. Reglas de cálculo (la cascada)

Son **las mismas reglas que aplican las fórmulas del Excel original**, por lo
que los resultados coinciden al céntimo:

```text
1) Recurso        Importe = Rendimiento × Precio unitario          (redondeado a 2 decimales)
2) Subtotal grupo = suma de los importes de los recursos del grupo
3) Complementarios: su «Precio unitario» es la BASE = suma de los demás
   subtotales, y su Importe = % × BASE / 100
4) Coste directo  = suma de todos los importes (subtotales + complementarios)
```

### Ejemplo real: `RBE010` (materiales + mano de obra)

| Grupo | Recurso | Rendimiento | Precio unitario | Importe |
| --- | --- | --- | --- | --- |
| Materiales | Agua (m³) | 0,005 | 1,50 | 0,01 |
| Materiales | Mortero (kg) | 16,00 | 0,17 | 2,72 |
| Materiales | Junquillo PVC (m) | 0,75 | 0,35 | 0,26 |
| | **Subtotal materiales** | | | **2,99** |
| Mano de obra | Oficial 1ª (h) | 0,516 | 25,28 | 13,04 |
| Mano de obra | Peón especializado (h) | 0,302 | 24,77 | 7,48 |
| | **Subtotal mano de obra** | | | **20,52** |
| Complementarios | 2 % | 2 | 23,51 (base) | 0,47 |
| | **Costes directos (1+2+3)** | | | **23,98** |

### Ejemplo real: `DPT020` (solo mano de obra)

| Grupo | Recurso | Rendimiento | Precio unitario | Importe |
| --- | --- | --- | --- | --- |
| Mano de obra | Peón ordinario (h) | 0,219 | 22,96 | 5,03 |
| | **Subtotal mano de obra** | | | **5,03** |
| Complementarios | 2 % | 2 | 5,03 (base) | 0,10 |
| | **Costes directos (1+2)** | | | **5,13** |

> Los subtotales y el total **se muestran pero nunca se suman como recursos**:
> si se sumaran, los gastos saldrían duplicados.

---

## 8. Flujo de importación en la aplicación

1. **Dónde empezar.** Hay dos accesos:
   - **Presupuestos → Importar CSV / Excel** (botón «⇧ Importar CSV / Excel»
     en la lista de presupuestos): las partidas entran en un presupuesto.
   - **Partidas → Importar desde Excel** (botón «⇧ Importar desde Excel» en
     el catálogo de partidas): el asistente abre en **modo catálogo** y las
     partidas detectadas se guardan en el **Catálogo de Partidas** (con su
     código, unidad, descripción y costes), sin crear ni modificar ningún
     presupuesto. Desde el catálogo se reutilizan en cualquier presupuesto y
     su descomposición ya aparece poblada y editable.
2. **Revisión.** El asistente muestra cada partida detectada: código, nombre,
   unidad, número de filas/columnas conservadas y el desglose de costes.
3. **Destino.** En modo presupuesto se elige crear un presupuesto nuevo (con
   cliente y título) o añadir las partidas a un presupuesto editable
   existente, indicando el nombre del capítulo donde entrarán. En modo
   catálogo no hay destino: todo va al catálogo.
4. **Confirmación.** Cada archivo se convierte en una partida presupuestable:
   - **Cantidad inicial:** 1 (se ajusta después a la medición real de obra).
   - **Precio unitario inicial:** el **coste directo** del archivo (el
     presupuesto nace consistente; el margen comercial se define después).
   - **Gastos internos:** materiales, mano de obra, complementarios y otros,
     con los valores del desglose.
   - La partida queda vinculada a su **descompuesto** (matriz completa) y al
     archivo `.xlsx` original descargable.
   - Además, la partida se guarda en el **catálogo** para reutilizarla
     (si ya existe con el mismo nombre, no se duplica).

---

## 9. Edición de costes y recálculo

Desde el detalle del presupuesto → partida → **vista del descompuesto**:

1. En la tabla «Costes por recurso», cada recurso tiene **editable** su
   **Rendimiento** y su **Precio unitario**.
   - En la fila de `%` (complementarios) el precio es **derivado**: muestra la
     base (suma de los demás subtotales) y se actualiza sola; solo se edita
     el porcentaje.
2. Mientras se escribe, la vista **recalcula en vivo** (con las reglas de la
   sección 7): importes, subtotales, base e importe de complementarios y
   coste directo.
3. Al pulsar **«Guardar y recalcular»** el cálculo se fija y se persiste:
   - Se actualizan las filas del descompuesto (incluida la matriz completa de
     celdas, que queda sincronizada con los nuevos valores).
   - Se actualizan los gastos de la partida (`coste_materiales`,
     `coste_mano_obra`, `coste_complementarios`, `coste_otros`) y el
     `coste_directo_unitario`, que es el **coste interno unitario** usado en
     todos los cálculos del presupuesto (coste interno, beneficio, margen).
   - El archivo `.xlsx` original **no se modifica nunca** (sigue siendo la
     referencia descargable de lo que se subió).
4. Casilla opcional **«Actualizar también el precio de venta de la partida al
   nuevo coste directo»**: si se marca, el precio de venta se iguala al nuevo
   coste directo. Si no se marca, el precio de venta se conserva (útil cuando
   ya se aplicó un margen comercial y solo se quiere ver su efecto).

### Ejemplo de edición (RBE010)

El oficial sube de 25,28 a 30,00 $/h:

| Concepto | Antes | Después |
| --- | --- | --- |
| Importe oficial (0,516 h/m²) | 13,04 | **15,48** |
| Subtotal mano de obra | 20,52 | **22,96** |
| Base de complementarios | 23,51 | **25,95** |
| Complementarios (2 %) | 0,47 | **0,52** |
| **Coste directo de la partida** | **23,98** | **26,47** |

---

## 10. Dónde queda guardada cada cosa

| Dato | Ubicación |
| --- | --- |
| Código externo, nombre, unidad, descripción y gastos (4 categorías) | Partida del presupuesto (`PresupuestoItem`) |
| Matriz completa (filas, celdas, fórmulas, rangos combinados) y coste directo | Descompuesto vinculado a la partida (`DescomposicionPartida` + `DescomposicionFila`) |
| Archivo `.xlsx` original | Carpeta de uploads del servidor (descargable desde la vista) |
| Copia en versiones congeladas | Las versiones del presupuesto incluyen la matriz del descompuesto vigente en ese momento |
| Copia de seguridad | La copia completa de Configuración incluye base de datos y uploads |
| Catálogo | La partida también se guarda en el catálogo de partidas (categoria «CYPE») para reutilizarla |

---

## 11. Casos límite y preguntas frecuentes

**¿Qué pasa si el archivo tiene un grupo desconocido (p. ej. «Maquinaria»)?**
Sus recursos se clasifican en **Otros** y participan igualmente en el coste
directo y en la base de los complementarios.

**¿Y si una celda de Importe viene sin valor (fórmula sin caché)?**
La app calcula el importe equivalente (`Rendimiento × Precio unitario`) para
el coste inicial y conserva la fórmula original en la matriz.

**¿La cantidad de la partida afecta al coste?**
Sí: el coste interno de la partida es `cantidad × coste directo unitario`.
Al importar, la cantidad es 1; al ajustar la medición de obra (m² reales),
el coste interno del presupuesto se escala automáticamente.

**¿Puedo editar los gastos a mano sin tocar el descompuesto?**
Sí: el formulario del presupuesto (funciones avanzadas → costes internos)
permite fijar materiales / mano de obra / complementarios / otros
manualmente. El descompuesto CYPE, cuando existe, sigue siendo la fuente del
`coste_directo_unitario`.

**¿Se puede re-importar el mismo archivo?**
Sí: cada importación crea partidas nuevas (o las añade al presupuesto
elegido). Las partidas ya editadas no se sobrescriben. En modo catálogo, si
una partida ya existe con el mismo nombre, se omite y se avisa en el
mensaje de confirmación.

**Al subir un `.xlsx` aparece «Falta el componente para leer archivos
Excel (.xlsx)»: ¿qué hago?**
Falta la librería `openpyxl` en la instalación (entornos creados antes de
que se añadiera a los requisitos). Solución: cierra la aplicación y vuelve
a abrirla con **INICIAR.bat** (Windows) o **INICIAR.sh** (macOS/Linux) — el
lanzador detecta la dependencia ausente y la instala automáticamente — o
ejecuta a mano:

```text
pip install openpyxl
```

En la aplicación empaquetada (.exe), vuelve a crear el instalador con
**CREAR_INSTALADOR.bat**.

**¿Qué unidades se conservan?**
Tal cual vengan del archivo (`m²`, `h`, `kg`, `%`, `m³`…), sin normalizar.

---

## 12. Checklist de un archivo válido

- [ ] Extensión `.xlsx`, sin contraseña, menos de 8 MB.
- [ ] Una partida por archivo (una hoja con el descompuesto).
- [ ] Fila de cabecera con **código**, **unidad** y **título** de la partida.
- [ ] Tabla con encabezados **Código, Unidad, Descripción, Rendimiento,
      Precio unitario, Importe** (en las columnas que use el exportador).
- [ ] Grupos con sus recursos y, idealmente, subtotales y la fila final de
      «Costes directos».
- [ ] Valores con el formato numérico del archivo original (la app entiende
      tanto `1.234,56` como `1,234.56`).

Si el archivo cumple esto, la importación conservará el 100 % de las filas y
columnas y los gastos quedarán correctamente clasificados y recalculables.
