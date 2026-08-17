# Base de datos de partidas

> **¿Vienes nuevo a esto? Lee antes [`EMPEZAR_AQUI.md`](EMPEZAR_AQUI.md).**
> Ahí está el estado, las reglas ya decididas y por dónde seguir.

El catálogo de partidas se construye y se valida aquí, en una carpeta aparte
del código de la aplicación. `datos/recursos.json` es la fuente única de los
precios y `salida/` son los ficheros listos para subir.

Durante la mayor parte del trabajo **no se tocó ni un módulo del proyecto**: lo
único que se leía era `app/services/importer.py`, y solo para validar que lo
generado se detecta al subirlo. Eso cambió al construir la barra lateral del
editor de presupuestos; los archivos de la aplicación que se modificaron están
listados en [`USO_EN_LA_APLICACION.md`](USO_EN_LA_APLICACION.md).

```
basedatos_partidas/
├── datos/recursos.json             ← FUENTE ÚNICA DE PRECIOS
├── datos/clasificacion.json        ← árbol numérico de tres niveles
├── datos/descompuestos/            ← 540 partidas, una por archivo
├── datos/objetivos_cobertura.json  ← metas 3.000/5.000 por capítulo
├── datos/sinonimos_busqueda.json   ← diccionario de sinónimos
├── descompuestos.py                ← genera hojas, maestro y árbol
├── construir.py                    ← genera y valida el catálogo importable
├── planificar_cobertura.py         ← genera matriz y prioridades
└── salida/                         ← catálogo, hojas e informes regenerables
```

## Cómo se usa

1. Añadir o editar la partida en `datos/descompuestos/*.json` y, si hace falta,
   sus recursos en `datos/recursos.json`.
2. Ejecutar:
   ```bash
   .venv/bin/python basedatos_partidas/descompuestos.py
   .venv/bin/python basedatos_partidas/construir.py
   .venv/bin/python basedatos_partidas/planificar_cobertura.py
   ```
3. Verificar terminología y cobertura.
4. La aplicación carga directamente las fuentes empaquetadas; para una carga
   manual también se puede usar `salida/catalogo_partidas.xlsx` desde
   **Partidas → Importar**.

`datos/partidas.csv` es un maestro **generado**: no se edita a mano.

## Columnas del maestro (`datos/partidas.csv`)

| Columna | Obligatoria | Notas |
|---|---|---|
| `codigo` | sí | Código numérico `CC.SS.AA.NNN`, único. |
| `codigo_legacy` | catálogo v2 | Alias histórico `CT-CC-SS-NNN`; también sirve como UID de las 540 actuales. |
| `capitulo` | sí | Nombre del capítulo de obra. |
| `partida` | **sí** | Nombre único (máx. 200 caracteres). |
| `descripcion` | sí | Texto técnico/comercial largo. |
| `unidad` | sí | `ud, m2, m, ml, m3, juego, hora, glb, kg`. `m²`→`m2` se normaliza solo. |
| `precio` | sí | Precio unitario de venta, > 0. Acepta coma o punto decimal. |
| `categoria` | sí | Capítulo numerado visible. |
| `subcategoria` | sí | Subcapítulo numerado visible. |
| `apartado` | sí | Tercer nivel numerado visible. |
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
  **12 campos detectados, 0 errores, 0 advertencias**.

## Correspondencia con el modelo `Partida`

La carga enriquecida rellena identificación, los tres niveles de clasificación,
precio, unidad, descomposición, costes, tiempos y notas. Las partidas oficiales
llevan además `catalogo_uid`, `es_oficial`, `oculta`, `version_catalogo` y
`version_alta_catalogo`, lo que permite ocultarlas por organización y recibir
altas incrementales sin duplicados.

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

Tres niveles numéricos alimentan el árbol de la barra lateral:

```text
12  Revestimientos y acabados
└─ 12.05  Pisos, pavimentos y sus bases
   └─ 12.05.03  Pisos cerámicos y porcelanato
      ├─ 12.05.03.010  Piso cerámico colocado con adhesivo
      └─ 12.05.03.020  Piso de porcelanato colocado con adhesivo
```

Cada partida declara `capitulo`, `subcapitulo` y `apartado`. El generador
valida los tres nodos y exige que el código `CC.SS.AA.NNN` empiece por esa ruta.
El antiguo código `CT-CC-SS-NNN` queda en `codigo_legacy` y en
`mapa_migracion_v2.json` para trazabilidad.

Hay **18 capítulos y 172 subcapítulos** preparados. Los apartados se crean con
contenido real; actualmente hay 147 con las 540 partidas migradas.

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

# Cambiar el precio de UN artículo (precio.py)

En Venezuela el cemento puede amanecer en 10 y anochecer en 20. Esta es la
herramienta del día a día. **Nunca se edita el precio dentro de una partida**:
se cambia en el cuadro de recursos y las 540 partidas se recalculan solas.

```bash
# ¿cómo se llama el recurso?
python3 basedatos_partidas/precio.py buscar cemento

# ¿qué precio tiene hoy y a qué partidas afecta?
python3 basedatos_partidas/precio.py ver MT-CEMENTO

# el saco de 42,5 kg amaneció en 20 USD -> SIMULACIÓN, no escribe nada
python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5

# convencido: escribe, hace copia de seguridad y regenera las 540 partidas
python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5 --aplicar
```

La simulación es lo importante: antes de tocar nada dice **cuántas partidas
cambian, cuáles son las más castigadas y cuánto sube el conjunto**. Ejemplo real
con el cemento al doble: 67 partidas afectadas, la peor sube un 56 % (nivelación
con mortero seco) y el conjunto de esas 67 sube un 4,4 %.

Se indica el precio **como lo da el proveedor** y él convierte a la unidad del
cuadro:

| Opción | Para qué |
|---|---|
| `--por-saco KG` | Cemento, pego, estuco, yeso |
| `--por-galon` | Pinturas, selladores, imprimaciones (3,785 l) |
| `--por-rollo M` | Cable, manto, manguera |
| `--por-lamina M2` | Drywall, policarbonato, melamina |
| `--por-unidad N` | Cajas y paquetes |

Sin ninguna opción, el valor se toma tal cual en la unidad del recurso.

## Recursos compuestos: el caso del cemento

Un mortero elaborado en obra **no lleva precio propio**. Declara de qué está
hecho y el precio sale solo:

```json
"MT-MOR-PEGA": {
  "unidad": "m3",
  "descripcion": "Mortero de pega para mampostería, elaborado en obra…",
  "composicion": [
    {"ref": "MT-CEMENTO",   "cantidad": 340},
    {"ref": "MT-ARENA",     "cantidad": 1.05},
    {"ref": "MT-AGUA-OBRA", "cantidad": 0.20}
  ]
}
```

Hay cuatro: `MT-MOR-PEGA` (1:4), `MT-MOR-FRISO` (1:5), `MT-MORT-AFIRM` (1:6)
y `MT-MORT-EST` (1:3). Su `estado` es `derivado` y su precio se recalcula en
cascada; `precio.py` se niega a fijarlo a mano y te dice qué componente tocar.

Además, al escribir la hoja de descompuesto el mortero **se abre en sus
componentes**: donde antes salía una línea opaca de «mortero de pega» ahora
salen el cemento, la arena y el agua que realmente lleva, con la coletilla
«Para mortero de pega». Es como se lee un análisis de precio unitario en
Venezuela y es lo que hace que el cemento se propague también dentro de la
aplicación.

> **Por qué importa.** Antes de esto, subir el cemento movía **10 partidas de
> 540**. Las otras 89 que llevan cemento lo llevaban escondido dentro de un
> mortero con precio congelado. Ahora mueve **67**. Las que faltan hasta 99 usan
> concreto premezclado, que se compra hecho y tiene su propio precio de mercado:
> es correcto que no dependa del saco de cemento.

El concreto premezclado (`MT-CONC-210`, `MT-CONC-250`…) **no** es compuesto a
propósito: se compra puesto en obra y su precio lo pone la planta.

## Qué NO depende del cemento

Solo esos cuatro. Todo lo que se **compra hecho** tiene precio propio y se
cambia por separado: el pego cerámico (`MT-ADH-C1`, `MT-ADH-C2TE`), la
boquilla, el autonivelante, el grout, el mortero de reparación, el
impermeabilizante, el microcemento y los cuatro concretos premezclados.

Comprobación con el saco de cemento a 20 USD:

| Partida | Antes | Ahora | Lleva | |
|---|---:|---:|---|---|
| Afirmado de nivelación | 9,77 | 14,61 | mortero de obra | +49,5 % |
| Friso maestreado | 6,45 | 8,38 | mortero de obra | +29,9 % |
| Tabique de bloque de 10 | 12,38 | 13,18 | mortero de obra | +6,5 % |
| Piso cerámico | 6,28 | 6,28 | pego en saco | sin cambio |
| Losa nervada | 397,57 | 397,57 | premezclado | sin cambio |
| Nivelación autonivelante | 18,92 | 18,92 | saco industrial | sin cambio |

---

# Terminología (terminologia.py)

El presupuesto lo lee el cliente: si la palabra no es la suya, el documento
pierde credibilidad por mucho que el número esté bien. El vocabulario no se
corrige a mano archivo por archivo, sino desde `datos/glosario.json`.

```bash
python3 basedatos_partidas/terminologia.py auditar   # busca términos peninsulares
python3 basedatos_partidas/terminologia.py listar    # qué cambiaría el glosario
python3 basedatos_partidas/terminologia.py aplicar   # lo escribe y regenera
```

La sustitución respeta la mayúscula inicial y los plurales, alcanza a los tres
sitios donde vive el texto (recursos, clasificación y las 540 partidas), y
puede renombrar además el código del recurso.

## Tres niveles de palabra

| Nivel | Dónde | Qué hace la auditoría |
|---|---|---|
| `cambios` | Sustituciones a ejecutar | Se aplican con `aplicar` |
| `_prohibidos` | Peninsular que no debe aparecer nunca | Falla y los lista |
| `_matizados` | Correcto en un contexto, incorrecto en otro | Avisa, no falla |

`solo_en` acota un cambio a unos archivos concretos. Se usó con «pavimento»:
en Venezuela es correcto en exteriores (pavimento de adoquín, asfáltico,
deportivo) y no en interiores, donde es «piso».

## La auditoría solo mira lo que ve el cliente

Recorre el título y la descripción de cada partida, la descripción de cada
recurso y los nombres de capítulo, subcapítulo y apartado. **No** mira `fuente` ni
`nota`: son apuntes internos de procedencia que citan nombres comerciales tal
cual los publica el vendedor («bisagra de cazoleta»), y auditarlos solo
produce falsas alarmas.

## Lo que se corrigió en el barrido

| De | A | Dónde |
|---|---|---|
| contrapiso | **afirmado** | 26 sitios, y el recurso `MT-MORT-CONTRA` → `MT-MORT-AFIRM` |
| encimera | mesón | 8 |
| solador | colocador de pisos | 2, y `MO-OF1-SOL` → `MO-OF1-PISO` |
| recrecido | afirmado | 4 |
| pavimento | piso | 6, solo en las dos partidas de piso interior |
| falso techo | cielo raso | 1 |
| forjado | losa | 1 |
| recrecerlo | engrosarlo | 1 |

Se descartaron dos reglas que parecían obvias y eran falsas: **«zócalo» no
siempre es rodapié** —las 18 apariciones son zócalo escalonado de escalera,
zócalo de realce del domo y zócalo del mueble de cocina, todas correctas— y
**«cazoleta»** en el catálogo es siempre la bisagra de mueble.

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

```text
CC . SS . AA . NNN
│    │    │     └── partida, de 10 en 10 para poder intercalar
│    │    └──────── apartado (2 dígitos)
│    └───────────── subcapítulo (2 dígitos)
└────────────────── capítulo (2 dígitos)
```

Tres niveles de clasificación y 18 capítulos. Instalaciones comparten el
capítulo 09; frisos, pisos, cielos rasos y pintura se ordenan dentro de
`12 Revestimientos y acabados`.

## Dos ámbitos

Cada partida lleva el campo `ambito`, y cada ámbito tiene su propia
clasificación y su propio esquema de código:

| Ámbito | Codificación | Base legal | Estado |
|---|---|---|---|
| **reforma** | `CC.SS.AA.NNN`, propia | COVENIN 2000-2 codifica solo edificaciones nuevas y deja **expresamente sin codificar** las reparaciones y reformas (Parte II.B nunca publicada). Codificación libre. | en construcción |
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
