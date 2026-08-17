# Inventario del trabajo — base de datos de partidas

Estado a 16/08/2026. El catálogo está integrado en CotizaT y usa la taxonomía
numérica v2 aprobada para reforma y remodelación en Venezuela.

## Cifras

| | |
|---|---:|
| Partidas | **2.363** |
| Hojas de descompuesto `.xlsx` | 2.363 |
| Partidas con producto de elección del cliente | 69 |
| Recursos en el cuadro de precios | **391** |
| — mano de obra / materiales / maquinaria | 17 / 330 / 44 |
| — confirmados / verificados con el mercado / provisionales | 17 / 113 / 257 |
| **Peso económico con precio cerrado** | **79,6 %** del coste directo |
| — confirmado (mano de obra) | 20,2 % |
| — verificado con el mercado venezolano | 59,4 % |
| — provisional | 20,4 % (de los cuales 6,3 % es alquiler de equipos) |
| Coste directo del catálogo | 15.745,67 USD |
| Clasificación v2 | **18 capítulos · 172 subcapítulos · 161 apartados con partidas** |
| — capítulos con partidas / preparados para ampliación | **15 / 3** |
| Código visible | `CC.SS.AA.NNN` |
| Moneda | USD (Venezuela) |

**Validación:** las 540 partidas pasan `es_formato_cype_xlsx` y
`analizar_cype_xlsx`. El catálogo masivo se detecta con **12 campos, 0 errores y
0 advertencias**. La suite de aplicación pasa con **483 tests y 6 omitidos**.

---

## Fuentes de verdad

| Archivo | Qué es |
|---|---|
| `datos/recursos.json` | **Cuadro de precios.** Fuente única de precios y composiciones. |
| `datos/clasificacion.json` | **Taxonomía v2.** Capítulos, subcapítulos y apartados. |
| `datos/descompuestos/*.json` | **Una partida por archivo**, con ruta v2, código anterior, descripción y recursos. |
| `datos/mapa_migracion_v2.json` | Equivalencia de las 540 partidas `CT-CC-SS-NNN` → `CC.SS.AA.NNN`. |
| `datos/objetivos_cobertura.json` | Metas 3.000/5.000, operaciones y variaciones por capítulo. |
| `datos/sinonimos_busqueda.json` | Diccionario de sinónimos: 146 grupos y 661 términos. |

`datos/partidas.csv` no se edita: lo regenera `descompuestos.py`.

## Programas

| Programa | Qué hace |
|---|---|
| `descompuestos.py` | Valida los tres niveles, resuelve recursos, calcula costes y genera hojas, maestro y árbol. |
| `construir.py` | Genera el catálogo masivo (`.csv`, `.xlsx`, `.json`) y lo valida con el importador real. |
| `tools/migrar_taxonomia_v2.py` | Documentación ejecutable de la migración única de v1 a v2. |
| `precios.py` | Revisión y actualización de precios en bloque. |
| `contraste.py` | Aplica rondas de contraste de mercado documentadas. |
| `precio.py` | Cambia un recurso y simula su impacto antes de escribir. |
| `terminologia.py` | Aplica y audita vocabulario venezolano en recursos, árbol y partidas. |
| `cobertura.py` | Informe por capítulo, subcapítulo y apartado. |
| `planificar_cobertura.py` | Genera matriz JSON/CSV y prioridades desde los objetivos. |
| `equidad.py` | Reparto del precio de venta y simulación de tarifas. |

## Salidas

| Archivo | Destino |
|---|---|
| `salida/descompuestos/*.xlsx` | Descompuestos individuales con clasificación v2. |
| `salida/catalogo_partidas.xlsx` | Carga masiva del catálogo. |
| `salida/arbol_catalogo.json` | Árbol capítulo → subcapítulo → apartado → partida. |
| `salida/precios_para_revisar.csv` | Plantilla de revisión de precios. |
| `salida/matriz_cobertura.{json,csv}` | 172 familias con estado, metas y brechas. |
| `salida/RESUMEN_COBERTURA.md` | Tablero de avance y primeras prioridades. |

---

## Los 18 capítulos de la taxonomía v2

| Cap. | Nombre | Subcap. | Apart. con partidas | Partidas |
|---|---|---:|---:|---:|
| 01 | Actuaciones previas | 8 | 10 | 100 |
| 02 | Demoliciones y desmontajes | 12 | 21 | 265 |
| 03 | Acondicionamiento del terreno | 6 | 7 | 80 |
| 04 | Fundaciones | 8 | 11 | 100 |
| 05 | Estructuras | 9 | 13 | 170 |
| 06 | Fachadas y particiones | 9 | 19 | 180 |
| 07 | Carpintería, herrería, vidrios y protección solar | 10 | 16 | 180 |
| 08 | Remates y ayudas | 9 | 16 | 120 |
| 09 | Instalaciones | 17 | 35 | 540 |
| 10 | Aislamientos e impermeabilizaciones | 9 | 16 | 150 |
| 11 | Techos y cubiertas | 9 | 5 | 18 |
| 12 | Revestimientos y acabados | 14 | 30 | 401 |
| 13 | Equipamiento, mobiliario y señalización | 9 | 7 | 21 |
| 14 | Obras exteriores y urbanismo | 11 | 10 | 19 |
| 15 | Gestión de residuos y limpieza | 7 | 6 | 8 |
| 16 | Control de calidad y ensayos | 8 | 0 | 0 |
| 17 | Seguridad y salud en obra | 8 | 7 | 11 |
| 18 | Rehabilitación energética | 9 | 0 | 0 |
| | **TOTAL** | **172** | **229** | **2.363** |

Los capítulos 08, 16 y 18 están deliberadamente preparados para la primera
ampliación. No se inventaron partidas de relleno solo para que aparezcan llenos.

## Cadena de generación

```text
datos/recursos.json ─┐
datos/clasificacion.json ─┼─► descompuestos.py ─► salida/descompuestos/*.xlsx
datos/descompuestos/*.json ─┘                  ├─► datos/partidas.csv
                                               └─► salida/arbol_catalogo.json
                                                        │
                              datos/partidas.csv ──► construir.py ─► salida/catalogo_partidas.*
```

```bash
.venv/bin/python basedatos_partidas/descompuestos.py
.venv/bin/python basedatos_partidas/construir.py
```

---

## Integración en la aplicación

- `CategoriaPartida` es un árbol normalizado con `parent_id`, código, nivel y orden.
- `Partida.categoria_id` apunta al apartado terciario.
- Los nombres denormalizados se conservan por compatibilidad y exportación.
- `codigo_legacy` conserva el código v1; el usuario ve el código numérico v2.
- `version_catalogo=2` evita reaplicar la migración.
- El esquema `f8a1b2c3d4e5` fue ejecutado en Supabase el 16/08/2026.
- La actualización conserva ids y precios locales, no revive partidas borradas
  y no modifica partidas creadas por una organización.
- El árbol del presupuestador muestra tres ramas, busca por toda la ruta y
  admite código anterior como alias.

---

## Siguiente ampliación

Los hitos de 800 y 1.500 son internos. El catálogo general tendrá un mínimo
aproximado de **3.000 partidas base** y un objetivo amplio de **4.000–5.000**.
La aplicación ya superó una prueba sintética con 5.000 partidas mediante índice
ligero, fichas bajo demanda, árbol progresivo y gestión paginada. La
ocultación/restauración y actualización incremental ya están implantadas. La
matriz 3.000/5.000 y el diccionario de sinónimos de 146 grupos cubren los 18 capítulos. El
siguiente paso es producir las familias pendientes. Prioridades:

1. Instalaciones sanitarias, eléctricas, climatización, ventilación, datos,
   seguridad y protección contra incendios.
2. Revestimientos, cielos rasos, pinturas y preparaciones de soporte.
3. Carpintería, herrería, vidrios y protección solar.
4. Impermeabilización y techos.
5. Remates y ayudas, control de calidad y rehabilitación energética.

**Progreso 17/08/2026:**
- `09.13 Protección contra rayos y sobretensiones` (13 partidas).
- `09.12 Domótica y automatización` (18 partidas).
- **Capítulo 12 Revestimientos y acabados completo hasta el mínimo** (401/400).
- **Capítulo 07 Carpintería, herrería, vidrios y protección solar completo
  hasta el mínimo** (180/180).
- **Capítulo 10 Aislamientos e impermeabilizaciones completo hasta el mínimo**
  (150/150).
- **Capítulo 02 Demoliciones y desmontajes completo hasta el mínimo**
  (265/260).
- **Capítulo 06 Fachadas y particiones completo hasta el mínimo** (180/180).
- **Capítulo 01 Actuaciones previas completo hasta el mínimo** (100/100).
- **Capítulo 03 Acondicionamiento del terreno completo hasta el mínimo**
  (80/80).
- **Capítulo 04 Fundaciones completo hasta el mínimo** (100/100).
- **Capítulo 05 Estructuras completo hasta el mínimo** (170/170).
- **Capítulo 08 Remates y ayudas completo hasta el mínimo** (120/120).
- **Capítulo 09 Instalaciones completo hasta el mínimo** (540/540), el
  capítulo más extenso del catálogo.

Siguen pendientes 257 precios de material provisionales. Los 44 precios de
alquiler de equipos permanecen fuera de alcance por decisión del cliente.