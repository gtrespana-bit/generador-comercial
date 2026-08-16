# Base de datos de partidas (trabajo externo)

Carpeta **independiente** del código de la aplicación. Aquí se construye y valida
el catálogo de partidas; no se toca ni un módulo del proyecto. Lo único que se
lee del proyecto es `app/services/importer.py`, y solo para **validar** que lo
generado se detecta perfectamente al subirlo.

```
basedatos_partidas/
├── datos/partidas.csv   ← FUENTE DE VERDAD (aquí van tus datos)
├── construir.py         ← genera y valida
└── salida/              ← ficheros listos para subir a la app
    ├── catalogo_partidas.csv
    ├── catalogo_partidas.xlsx
    └── catalogo_partidas.json
```

## Cómo se usa

1. Añadir/editar filas en `datos/partidas.csv` (separador `;`, UTF-8).
2. Ejecutar: `python3 basedatos_partidas/construir.py`
3. Subir `salida/catalogo_partidas.xlsx` (o el .csv) en la app:
   **Partidas → Importar** (`/presupuestos/importar?destino=catalogo`).

## Columnas del maestro (`datos/partidas.csv`)

| Columna | Obligatoria | Notas |
|---|---|---|
| `codigo` | recomendada | Código interno/externo. Se comprueba que no se repita. |
| `capitulo` | sí | Capítulo de obra (ALBAÑILERÍA, FONTANERÍA…). |
| `partida` | **sí** | Nombre. **Único** en todo el fichero: el catálogo omite duplicados (máx. 200 car.). |
| `descripcion` | sí | Texto técnico/comercial largo. |
| `unidad` | sí | `ud, m2, m, ml, m3, juego, hora, glb, kg`. `m²`→`m2` se normaliza solo. |
| `precio` | sí | Precio unitario de venta, > 0. Acepta coma o punto decimal. |
| `categoria` | no | Si se deja vacía se usa el capítulo. |
| `subcategoria` | no | Solo informativa / JSON. |
| `coste_materiales` | no | Desglose. La suma no puede superar al precio. |
| `coste_mano_obra` | no | Desglose. |
| `coste_complementarios` | no | Costes directos complementarios (estilo CYPE). |
| `coste_otros` | no | Desglose. |
| `rendimiento` | no | Texto libre (p. ej. `12 m2/jornada`). |
| `desperdicio_pct` | no | % de desperdicio recomendado. |
| `notas_tecnicas` | no | Texto libre. |

## Qué garantiza el validador

`construir.py` hace dos pasadas:

- **Calidad propia**: nombres y códigos duplicados, longitudes, precios a 0,
  desglose de costes incoherente, descripciones o capítulos vacíos, unidades raras.
- **Compatibilidad real**: pasa el CSV generado por `leer_csv` → `analizar_matriz`
  → `detectar_mapeo` → `validar_filas` del propio proyecto. El objetivo es siempre
  **8 campos detectados, 0 errores, 0 advertencias**.

## Correspondencia con el modelo `Partida`

El asistente en modo catálogo (`_importar_a_catalogo`) rellena: `nombre`,
`descripcion`, `precio_unitario`, `unidad`, `categoria`, `codigo_interno`,
`codigo_externo`, `descomposicion_json` y los cuatro `coste_*`.
El `.json` de salida conserva además `subcategoria`, `rendimiento`,
`desperdicio_recomendado_pct` y `notas_tecnicas` para una carga enriquecida futura.

---

# Descompuestos (formato hoja tipo CYPE)

`descompuestos.py` genera hojas .xlsx con **el layout exacto que ya lee
`analizar_cype_xlsx`**: cabecera con código/unidad/título, descripción larga,
fila de encabezados «Código · Unidad · Descripción · Rendimiento · Precio
unitario · Importe», grupos, subtotales, % de costes directos complementarios
y total de costes directos.

Cada partida es un JSON en `datos/descompuestos/`:

```json
{
  "codigo": "PRO-ALB-001",
  "unidad": "m²",
  "titulo": "...",
  "descripcion": "...",
  "complementarios_pct": 2,
  "recursos": [
    {"grupo": "materiales", "codigo": "...", "unidad": "m²",
     "descripcion": "...", "rendimiento": 4.2, "precio": 4.8}
  ]
}
```

`grupo` admite `materiales`, `maquinaria` y `mano_obra`; el generador los
rotula como «Materiales», «Equipo y maquinaria» y «Mano de obra», que son las
etiquetas que `_categoria_coste_cype` clasifica correctamente.

**Rendimientos**: la columna Rendimiento es la cantidad de recurso por unidad
de partida (h/m², kg/m², m/m²…). Sumando los recursos de mano de obra sale
directamente el tiempo de ejecución por unidad, que es lo que alimenta el
cálculo de horas, plazos y márgenes.

**Importante**: los importes, subtotales y el total se escriben como valores
numéricos literales, no como fórmulas. openpyxl no guarda el resultado
cacheado de una fórmula, y el lector del proyecto leería celdas vacías.

Ejecutar: `python3 basedatos_partidas/descompuestos.py [CODIGO ...]`
El script valida cada archivo con `es_formato_cype_xlsx` y `analizar_cype_xlsx`
e imprime los costes tal y como los va a leer la aplicación.

---

# Cuadro de recursos (datos/recursos.json)

**Fuente única de verdad de los precios.** Agrupa mano de obra, materiales y
maquinaria. Cada partida referencia recursos por su código:

```json
{"ref": "MO-OF1-SOL", "rendimiento": 0.400}
```

y hereda unidad, descripción y precio del cuadro. Cambiar el precio de un
recurso **recalcula automáticamente todas las partidas que lo usan**: no hay
que tocar ninguna partida para actualizar el coste de la hora de oficial o el
precio del porcelánico.

Cada recurso lleva un campo `estado`. Todo lo que ponga `provisional` está
pendiente de sustituir por el dato real de vuestros proveedores y convenio.

## Cadena completa

```
datos/recursos.json  +  datos/descompuestos/*.json
          │
          ▼   descompuestos.py
   salida/descompuestos/*.xlsx      (hoja de descompuesto, se sube una a una)
          +
   datos/partidas.csv               (maestro consolidado, regenerado)
          │
          ▼   construir.py
   salida/catalogo_partidas.{csv,xlsx,json}   (carga masiva del catálogo)
```

El precio de venta del catálogo sale de `coste directo × (1 + margen)`, con
`margen` por partida (0,30 por defecto).

## Orden de ejecución

```bash
python3 basedatos_partidas/descompuestos.py   # 1. descompuestos + maestro
python3 basedatos_partidas/construir.py       # 2. catálogo importable
```


---

# Clasificación jerárquica (datos/clasificacion.json)

Tres niveles, pensados para alimentar el árbol de la barra lateral del presupuestador:

```
Capítulo (1 letra)  →  Subcapítulo (2 letras)  →  Grupo (3 letras)  →  Partida (grupo + 3 dígitos)

R  Revestimientos y trasdosados
└─ RS  Pavimentos
   └─ RSG  Cerámicos y porcelánicos
      ├─ RSG010  Pavimento formato estándar
      └─ RSG020  Pavimento gran formato
```

Cada partida declara `capitulo`, `subcapitulo` y `grupo`. El generador **valida** que los
tres existan en `clasificacion.json` y que el código empiece por el grupo; si no, falla.
Así es imposible que se cuele una partida descolgada del árbol.

Hay **18 capítulos** declarados desde el principio, aunque estén vacíos: el árbol se
construye completo y las ramas se van llenando.

## Salida para el front

`salida/arbol_catalogo.json` contiene el árbol ya montado, con el contador de partidas de
cada rama y, en las hojas, código, título, unidad, precio, horas y si requiere producto de
cliente. Es lo que consumirá la barra lateral arrastrable.

---

# Productos de elección del cliente

Una partida **no incluye el material de acabado que elige el cliente**. El solado incluye
adhesivo, junta, crucetas, corte y mano de obra — pero **no la cerámica**, porque esa
depende de lo que escoja cada cliente y vive en el catálogo de productos.

Cada partida afectada declara:

```json
"producto_cliente": {
  "tipo": "Pieza cerámica o porcelanato para pavimento, formato hasta 60x60 cm",
  "unidad": "m2",
  "consumo": 1.06,
  "nota": "Consumo con 6 % de desperdicio por cortes y roturas."
}
```

El `consumo` es el factor de conversión: por cada m² de partida hacen falta 1,06 m² de
producto. Al presupuestar, se elige el producto, se multiplica por el consumo y se suma.
El precio de la partida es **solo de ejecución**, y así se puede ofrecer el mismo trabajo
con tres cerámicas distintas sin recalcular nada.

La nota se arrastra al campo `notas_tecnicas` del catálogo, dejando constancia explícita
de qué NO está incluido.

---

# Actualización de precios en bloque (precios.py)

Los precios viven **solo** en `datos/recursos.json`. Las partidas guardan
rendimientos y referencian recursos por código, así que **actualizar precios
nunca obliga a tocar una partida**.

```bash
python3 basedatos_partidas/precios.py exportar
# -> salida/precios_para_revisar.csv, ordenado POR IMPACTO
#    (los recursos que más pesan en el coste del catálogo, primero)

# rellenar la columna «precio_nuevo» y:
python3 basedatos_partidas/precios.py aplicar
# -> actualiza recursos.json, marca los recursos como «confirmado»
#    y deja copia de seguridad con fecha

python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py
```

El CSV incluye `partidas_que_lo_usan` y `peso_en_catalogo_usd` para saber
dónde merece la pena invertir el tiempo de buscar precios.

**Conclusión práctica**: no hay que tener los precios antes de escribir
partidas. Lo único que sí conviene fijar desde el principio es la **unidad de
compra** de cada recurso (kg o saco, m o rollo), porque cambiar la unidad sí
obliga a revisar los rendimientos.

---

# Cobertura (cobertura.py)

Informe del avance del catálogo sobre la taxonomía, para trabajar **capítulo a
capítulo y grupo a grupo** sin dejar huecos:

```bash
python3 basedatos_partidas/cobertura.py              # resumen por capítulo
python3 basedatos_partidas/cobertura.py D            # detalle del capítulo D
python3 basedatos_partidas/cobertura.py --pendientes # grupos declarados y vacíos
```

## Criterio de trabajo

1. Se elige un **grupo** (tercer nivel, p. ej. `DRS`).
2. Se completa **entero**, con todas las variantes de material y sus remates.
3. Se pasa al siguiente grupo del mismo subcapítulo.

Un grupo se considera cerrado cuando cubre las tipologías que realmente se
encuentran en obra en Venezuela, no cuando iguala a ninguna base ajena.

## Terminología

El catálogo usa vocabulario de obra venezolano:

| No usar | Usar |
|---|---|
| hormigón | concreto |
| pavimento / solado | piso |
| enfoscado / guarnecido | friso |
| falso techo | cielo raso |
| terrazo (continuo) | granito vaciado en sitio |
| escayola | yeso |
| fontanero | plomero |
| bote de escombro | bote de escombro / retiro a vertedero |


---

# Codificación propia de CotizaT y ámbitos

## Por qué se migró

El catálogo nació usando la estructura y los códigos del Generador de Precios de
CYPE (`DPT020`, `DRS020`, `RSG130`…). Se detectó que **cada banco de precios del
sector usa una codificación propia y distinta** — BCCA `10SCS00002`, Extremadura
`E10EGO110`, PREOC `U01AA007`, IVE `ERSA11$` — de modo que el código es la firma
de identidad de cada base, no un estándar compartido. Coincidir carácter por
carácter con CYPE creaba **riesgo de asociación** (arts. 6 y 11 LCD) además de
colisiones reales: nuestro `DPT020` y el `DPT020` de CYPE significaban cosas
distintas.

Se migró a codificación propia el 16/08/2026. El contenido — descripciones,
rendimientos y precios — no se tocó: era original desde el principio.

`datos/mapa_migracion.json` guarda la equivalencia código antiguo → nuevo para
trazabilidad interna. **No se publica ni se distribuye.**

## Esquema

```
CT - CC - SS - NNN
│    │    │    └── partida, de 10 en 10 para poder intercalar
│    │    └─────── subcapítulo (2 dígitos)
│    └──────────── capítulo (2 dígitos)
└───────────────── prefijo de marca (CotizaT)
```

Dos niveles de navegación, 20 capítulos organizados según la práctica de obra
venezolana: los frisos, los pisos, los cielos rasos y la herrería son capítulos
de primer nivel, no subgrupos.

## Dos ámbitos

Cada partida lleva el campo `ambito`, y cada ámbito tiene su propia
clasificación y su propio esquema de código:

| Ámbito | Codificación | Base legal | Estado |
|---|---|---|---|
| **reforma** | `CT-CC-SS-NNN`, propia | COVENIN 2000-2 codifica solo edificaciones nuevas y deja **expresamente sin codificar** las reparaciones y reformas (Parte II.B nunca publicada). Codificación libre. | en construcción |
| **obra nueva** | COVENIN 2000-2: `M`+9 dígitos (<1.000 m²), `E`+9 (1.000-10.000 m²), `I`+9 (>10.000 m²) | COVENIN-MINDUR 2000-92 Parte II.A, **obligatoria** por Gaceta Oficial N.º 35.225 del 3/6/1993. Ante organismos públicos y contralorías la codificación **no es libre**. | pendiente |

Ambos ámbitos comparten el **mismo cuadro de recursos** (`recursos.json`) y el
**mismo motor de descompuestos**. Solo cambian el árbol y el esquema de código.

Cada partida tiene además el campo `codigo_covenin`, hoy vacío, para poder
declarar la equivalencia cuando se disponga del texto de la norma.

### Para arrancar obra nueva hace falta

Conseguir la **COVENIN 2000-2 y su Suplemento N.º 1 (1999)** para replicar su
árbol de capítulos y su esquema de codificación exactos. Sin la norma se puede
avanzar en las partidas, pero no fijar los códigos definitivos.

---

# Contraste de precios con el mercado venezolano

Revisión de agosto de 2026. Se contrastaron **66 recursos** contra precios
publicados del mercado venezolano y se marcaron con el estado
`verificado-mercado`, añadiendo el campo `fuente` con la referencia y el
razonamiento de cada uno.

## Fuentes empleadas

- MercadoLibre Venezuela (cemento, drywall, melamina, PPR, porcelanato, concreto premezclado)
- EPA en línea Venezuela (manto asfáltico, cerámica, cemento)
- Ferreterías y fabricantes con lista pública (bloques de concreto)
- Tabuladores de precios de la construcción Venezuela 2026 (APU de referencia)

## Criterio aplicado

- Se tomó la **mediana del rango** publicado, no el extremo bajo.
- Los materiales vendidos por presentación se convirtieron a la unidad del
  cuadro: saco de 42,5 kg a kg, galón de 3,785 l a litro, plancha de 1,22x2,44
  (2,98 m²) o de 1,83x2,44 (4,46 m²) a m², rollo de 100 m a metro.
- Los **morteros elaborados en obra** (pega, friso, contrapiso) no se toman de
  lista: se derivan del cemento y la arena que los componen.

## Estados del cuadro de recursos

| Estado | Significado |
|---|---|
| `confirmado` | Dato facilitado directamente por el cliente (mano de obra) |
| `verificado-mercado` | Contrastado con precios publicados del mercado venezolano |
| `provisional` | Sin contrastar. Pendiente de precio de proveedor real |

## Segunda ronda de contraste (agosto 2026)

Fichero de evidencia: **`datos/contraste_mercado_2026-08.json`**.
Se aplica con `python3 basedatos_partidas/contraste.py aplicar`.

Cada entrada guarda el precio adoptado, el **rango observado**, la
**conversión** de presentación comercial a unidad del cuadro y las **tiendas
consultadas**. No es una lista de números sueltos: es una lista auditable, para
que dentro de seis meses se pueda rehacer el mismo barrido y comparar.

**51 recursos revisados: 33 al alza, 16 a la baja, 2 confirmados sin cambio.**
El peso económico con precio cerrado pasó del **55,2 % al 79,6 %**.

El **alquiler de equipos queda fuera de esta ronda** por decisión del cliente:
los 43 recursos de maquinaria se mantienen tal y como estaban. El script los
salta expresamente y lo deja escrito en el informe.

### Errores de unidad que destapó el contraste

Lo más valioso no fueron los ajustes de precio, sino tres precios que estaban
mal por **confundir la presentación comercial con la unidad del cuadro**:

| Recurso | Antes | Ahora | Qué pasaba |
|---|---:|---:|---|
| `MT-EPOXI-ANCLA` | 22,00 /l | 95,00 /l | Se había tomado el precio del **cartucho de 300 ml** como si fuera el del litro |
| `MT-CIELO-PVC` | 8,50 /m² | 16,00 /m² | Se había tomado el precio de la **lámina de 0,60 m²** como si fuera el del m² |
| `MT-AUT-NIV` | 0,42 /kg | 1,55 /kg | Se había puesto el precio de un **mortero de contrapiso corriente**, no el de un autonivelante |

A los que se suman `MT-SELLA-ELAST`, `MT-SILICONA-EST` y `MT-SIL-SAN`, donde el
cartucho de 290-300 ml se estaba tratando como litro.

### Ajustes a la baja

No todo subió. Bajaron los que estaban inflados: `MT-CABLE-DATOS` (−68 %, la
bobina de 305 m sale a 0,22-0,28 USD/m), `MT-DUCTO-VENT` (−48 %),
`MT-HERRAJE-PUERTA` (−28 %), `MT-DOMO` (−24 %), `MT-BOTIQUIN` (−22 %).

### Precios que resistieron el contraste

`MT-FORM-MADERA` (−3,6 %), `MT-POLICARB` (+2,8 %), `MT-HERRAJE-CLOSET` (+7,1 %),
`MT-EPP` y `MT-PROT-OBRA` (sin cambio). Son señal de que el criterio de estimación
del primer pase no iba desencaminado.

### Fuentes de esta ronda

- **EPA Venezuela** (`ve.epaenlinea.com`), catálogo en línea con precios en USD:
  perfilería de acero, siliconas y selladores, cerraduras, espejos.
- **MercadoLibre Venezuela**, listados por familia: madera, herrajes, vidrio,
  epóxicos, cielos rasos, adoquines, seguridad, cableado, ventilación.
- Cuando el recurso es un **conjunto** (juego de herrajes, gabinete con manguera,
  dotación de EPP) no se busca el conjunto: se compone sumando sus partes con
  las cantidades reales de obra, y así queda escrito en `conversion`.
- Cuando el material se vende **por barra o perfil**, se convierte a kg por el
  **peso teórico de la sección**, no por el peso que anuncia el vendedor.

## Verificación cruzada

El catálogo recalculado se contrastó contra un presupuesto tipo de vivienda de
80 m² en Caracas. La pared de bloque con friso a dos caras y la losa nervada
quedan dentro del rango de mercado; las partidas de acabado e instalaciones
quedan por debajo, lo que es coherente porque el benchmark incluye el material
de acabado que en nuestro modelo se factura aparte como producto de cliente.

---

# Política de mano de obra y reparto (equidad.py)

Las tarifas de mano de obra de este catálogo están **por encima de la tarifa
habitual del mercado venezolano** por decisión expresa del titular. No es un
error de calibración: es la posición del negocio.

| | Este catálogo | Mercado VE 2026 |
|---|---:|---:|
| Oficial de 1ª | 44,00 USD/jornada | ~15,00 |
| Ayudante especializado | 32,00 USD/jornada | ~11,00 |
| Ayudante | 28,00 USD/jornada | ~9,00 |

## El dato que importa

Pagar **3 veces** la tarifa de mercado encarece el precio final del catálogo
solo un **17 %**, porque en la mayoría de las partidas manda el material. A
cambio, la parte del precio de venta que llega al trabajador pasa del
**6,5 % al 16,5 %**.

```bash
python3 basedatos_partidas/equidad.py
python3 basedatos_partidas/equidad.py --escenario 4.5 3.2 2.8
```

El informe desglosa el peso de la mano de obra por capítulo, que es donde se
ve cuánto pesa la decisión: en demoliciones y pintura la mano de obra es el
40 % del coste; en fundaciones y estructuras, apenas el 13-16 %.

## Uso comercial

El porcentaje que llega al trabajador es un dato defendible frente al cliente y
un argumento de diferenciación: explica por qué el presupuesto no es el más
barato y qué se está comprando con esa diferencia. También sostiene la calidad,
porque la rotación de personal y los repasos por mala ejecución cuestan más que
el 17 %.

**Importante para el cálculo**: estas tarifas son **coste**, no precio de venta.
El margen del 30 % se aplica encima del coste directo, de modo que no hay doble
margen sobre la mano de obra.
