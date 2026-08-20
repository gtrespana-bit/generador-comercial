# Inventario del catálogo de partidas

**Estado auditado: 20/08/2026.** Catálogo integrado en CotizaT, taxonomía
numérica v2 para reforma y remodelación. La integridad técnica y la cobertura
referencial nacional pasan; ver
[`../docs/AUDITORIA_CATALOGO_PRELANZAMIENTO_2026-08-20.md`](../docs/AUDITORIA_CATALOGO_PRELANZAMIENTO_2026-08-20.md).

## Cifras verificadas

| Concepto | Cantidad |
|---|---:|
| Partidas JSON | **3.006** |
| Hojas de descompuesto `.xlsx` | 3.006 |
| Partidas con producto de elección del cliente | 363 |
| Partidas con mano de obra explícita | **3.006 / 3.006** |
| Líneas de mano de obra | **6.062** |
| Recursos declarados | **392** |
| Recursos físicos que carga la aplicación | **388** |
| — mano de obra / materiales / maquinaria | 17 / 331 / 44 |
| — tarifa interna confirmada / mercado VE verificado / derivados / provisionales | 17 / 131 / 4 / 240 |
| Peso económico VE verificado o confirmado | **79,6 %** del coste directo acumulado |
| Peso económico VE provisional | **20,4 %** |
| Clasificación v2 | **18 capítulos · 172 subcapítulos · 256 apartados** |
| Código visible | `CC.SS.AA.NNN` |
| Moneda base Venezuela | USD |

Los cuatro recursos `derivado` son mezclas que se abren en sus componentes al
calcular; por eso 392 declaraciones producen 388 filas físicas en la
aplicación y en cada mercado nacional.

## Resultado de calidad

- 3.006 partidas calculables, con código, clasificación, recursos, unidad,
  rendimiento y precio de recurso válidos.
- 3.006 partidas con oficio y horas por unidad; el modelo recibe desglose de
  oficial, ayudante y equipo.
- 0 errores estructurales en la auditoría de lanzamiento.
- **218 grupos / 875 partidas** comparten exactamente APU con otra partida;
  quedan identificados para revisión técnica progresiva (la coincidencia no es
  por sí sola un error).
- Los 388 recursos VE tienen precio referencial; 240 están marcados
  `provisional` por menor evidencia pública o mayor volatilidad.
- CO/PE/MX/EC tienen **388/388 referencias nacionales cada uno**: 73
  observaciones directas y 1.479 derivaciones transparentes en el conjunto.

## Fuentes de verdad

| Archivo | Qué contiene |
|---|---|
| `datos/recursos.json` | Cuadro base de precios, roles y composiciones. |
| `datos/clasificacion.json` | Taxonomía v2. |
| `datos/descompuestos/*.json` | Una partida por archivo, con APU y rendimientos. |
| `datos/mapa_migracion_v2.json` | Equivalencia de las 540 partidas históricas v1 → v2. |
| `salida/precios_recursos_latam.csv` | Matriz trazable CO/PE/MX/EC; huecos pendientes. |
| `salida/precios_recursos_latam_completa.csv` | Respaldo convertido, siempre provisional. |
| `salida/auditoria_partidas.csv` | Revisión partida por partida (3.006 filas). |
| `datos/objetivos_cobertura.json` | Metas 3.000/5.000 por capítulo. |
| `datos/sinonimos_busqueda.json` | Diccionario de búsqueda. |

`datos/partidas.csv` y todo `salida/` son generados; no se editan a mano.

## Programas de control

| Programa | Función |
|---|---|
| `auditar_lanzamiento.py` | Revisa las 3.006 partidas, recursos y mercados; genera informe y CSV exhaustivo. |
| `descompuestos.py` | Resuelve recursos, calcula costes y genera hojas/maestro/árbol. |
| `construir.py` | Genera catálogo masivo y lo valida con el importador real. |
| `precios.py` / `precio.py` | Revisión en bloque / cambio controlado de un precio. |
| `contraste.py` | Aplica rondas documentadas de contraste. |
| `terminologia.py` | Audita vocabulario venezolano. |
| `cobertura.py` | Informa cobertura por capítulo y apartado. |
| `equidad.py` | Informa tarifas y reparto de mano de obra. |

## Capítulos

| Cap. | Nombre | Subcap. | Apart. | Partidas |
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
| 11 | Techos y cubiertas | 9 | 9 | 130 |
| 12 | Revestimientos y acabados | 14 | 30 | 401 |
| 13 | Equipamiento, mobiliario y señalización | 9 | 9 | 140 |
| 14 | Obras exteriores y urbanismo | 11 | 11 | 160 |
| 15 | Gestión de residuos y limpieza | 7 | 7 | 50 |
| 16 | Control de calidad y ensayos | 8 | 8 | 80 |
| 17 | Seguridad y salud en obra | 8 | 9 | 60 |
| 18 | Rehabilitación energética | 9 | 9 | 100 |
|  | **TOTAL** | **172** | **256** | **3.006** |

## Reproducción

```bash
.venv/bin/python tools/generar_matriz_precios_latam.py
.venv/bin/python tools/completar_matriz_referencias.py
.venv/bin/python basedatos_partidas/auditar_lanzamiento.py
.venv/bin/python basedatos_partidas/descompuestos.py
.venv/bin/python basedatos_partidas/construir.py
```

La opción `auditar_lanzamiento.py --strict` debe terminar en cero antes de
publicar: comprueba integridad, mano de obra y cobertura referencial completa.
Los niveles de confianza y APUs coincidentes permanecen visibles para el ciclo
de mantenimiento, sin convertir una referencia en una promesa de precio exacto.
