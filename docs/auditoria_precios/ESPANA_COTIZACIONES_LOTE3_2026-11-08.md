# Cotizaciones reales de España, lote 3 — 8 de noviembre de 2026

**Resultado: los cuatro últimos recursos del punto 2 con uso relevante dejan de ser
precio derivado.** Suman **56 usos**: 17 (`MT-SELLA-PASE`), 17 (`MT-RIEL-CORRED`),
13 (`MT-SAN-FIJA`) y 9 (`MT-AISL-REFLECT`). Tres mueven precio y uno lo mantiene con
banda medida.

Con este lote, de las 39 referencias `mercado_rango` con uso real, **12 están
cotizadas** y quedan 27. Las referencias ES con `confianza = 'referencia'` pasan de
48 a **52**; las `derivado`, de 342 a **338**.

**Y con esto el punto 2 queda agotado en lo que importa**: los 27 recursos que quedan
tienen entre 1 y 5 usos cada uno (el mayor, `MT-QUIMICO-LIMP-AC`, con 5). No quedan
recursos de mercado con decenas de partidas detrás sin evidencia real.

## 1. Qué se ha cambiado

| Recurso | Usos | Antes (derivado) | Ahora (cotizado) | Δ | Evidencia |
|---|---|---|---|---|---|
| `MT-SELLA-PASE` | 17 | 5,24 | **9,96** | +90,1 % | Tienda Reco: 3 collares Tyvek-EPDM por diámetro + masilla LAP-SEALANT |
| `MT-RIEL-CORRED` | 17 | 15,95 | **15,95** | 0,0 % | INDAUX JUNIOR-1 + kit de 2 puertas + kit Tourly |
| `MT-SAN-FIJA` | 13 | 5,47 | **8,90** | +62,7 % | Anillo de cera OATEY (Bricosanitarios) + juego de tornillos BCCA `IF17200` |
| `MT-AISL-REFLECT` | 9 | 3,65 | **3,60** | −1,4 % | Leroy Merlin: RF1, BLH y multicapa de doble burbuja |

Las cuatro filas pasan a `confianza = referencia`, `incluye_iva = 'no'`,
`fecha_consulta = 2026-11-08` y banda medida en las columnas numéricas.

## 2. Las once ofertas, una a una

Todas consultadas el **2026-11-08**. El detalle completo, con conversión de IVA y de
unidad, está en `espana_cotizaciones_2026-11-08.csv`.

| Recurso | Producto | Publicado | Sin IVA | €/unidad | Δ vs matriz |
|---|---|---|---|---|---|
| `MT-AISL-REFLECT` | Rollo OPTIMER RF1, 4 mm, 42 m² | 118,00 €/rollo | 97,52 | 2,32 €/m² | −36,4 % |
| `MT-AISL-REFLECT` | Rollo OPTIMER BLH, 8 mm, 36 m² | 185,00 €/rollo | 152,89 | 4,25 €/m² | +16,4 % |
| `MT-AISL-REFLECT` | Rollo multicapa doble burbuja, 48 m² | 209,00 €/rollo | 172,73 | 3,60 €/m² | −1,4 % |
| `MT-SAN-FIJA` | Anillo de cera para inodoro OATEY | 6,83 €/ud | 5,65 | 5,65 €/ud | +3,3 % |
| `MT-SAN-FIJA` | Juego de tornillos cromados, banco `IF17200` | 3,25 €/ud | 3,25 | 3,25 €/ud | −40,6 % |
| `MT-SELLA-PASE` | Collar Tyvek-EPDM 4-8 mm, 150×150 mm (`D1`) | 5,45 €/ud | 4,50 | 4,50 €/ud | −14,1 % |
| `MT-SELLA-PASE` | Collar Tyvek-EPDM 40-55 mm, 230×230 mm (`GD23`) | 12,05 €/ud | 9,96 | 9,96 €/ud | +90,1 % |
| `MT-SELLA-PASE` | Collar Tyvek-EPDM 100-110 mm, 320×320 mm (`RGD100`) | 20,81 €/ud | 17,20 | 17,20 €/ud | +228,2 % |
| `MT-RIEL-CORRED` | Kit INDAUX JUNIOR-1: 2 rieles de 2 m, carros y ruedas | 24,80 €/kit | 20,50 | 5,12 €/m | −67,9 % |
| `MT-RIEL-CORRED` | Kit 2 puertas, perfil de 2 m, carros y topes | 49,90 €/kit | 41,24 | 20,62 €/m | +29,3 % |
| `MT-RIEL-CORRED` | Kit completo Tourly de 183 cm | 41,99 €/kit | 34,70 | 18,96 €/m | +18,9 % |

Las dos conversiones que ya venían del lote 1 y del lote 2:

* **IVA.** Las tiendas publican con IVA (21 %); el banco BCCA publica sin IVA. Todo se
  normaliza a sin IVA antes de comparar.
* **Unidad.** Dos recursos no se venden en la unidad de la matriz:
  * `MT-AISL-REFLECT` se vende por **rollo**; el precio se divide por los m² que
    declara la ficha (42, 36 y 48).
  * `MT-RIEL-CORRED` se vende por **kit**; el precio se reparte entre los metros de
    riel que trae el kit (4 m en el JUNIOR-1, 2 m en el kit de dos puertas, 1,83 m en
    el Tourly).

## 3. Por qué cada decisión es la que es

* **`MT-SELLA-PASE` sube un 90 % y el motivo está en el diámetro.** El recurso pide
  «collarín y masilla» para el paso de instalaciones. Los collares de sellado
  Tyvek-EPDM se venden por diámetro: 4,50 €/ud el de 4-8 mm, 9,96 € el de 40-55 mm y
  17,20 € el de 100-110 mm. Se adopta el de 40-55 mm, que es el diámetro de los pases
  de fontanería y saneamiento que valoran las partidas (`08.04.01.070`, `10.08.02.060`,
  `08.02.02.050`). La masilla no desplaza el precio: el cartucho LAP-SEALANT cuesta
  15,95 € sin IVA y **rinde 8 m de junta**, así que por pase aporta menos de 1 €. El
  precio derivado de 5,24 € solo alcanzaba para el collar más pequeño del mercado, que
  no es el que se instala en una bajante.
* **`MT-SAN-FIJA` sube un 63 % porque el kit son dos piezas con precio propio.** El
  anillo de cera OATEY cuesta 5,65 € sin IVA en Bricosanitarios y el juego de tornillos
  cromados 3,25 € sin IVA en el banco BCCA `IF17200`: la suma da 8,90 € por aparato. El
  dato que zanja la duda es que **el anillo solo ya cuesta más que el precio derivado
  (5,47)**: la horquilla del 7 de noviembre no cubría ni la mitad del producto.
* **`MT-RIEL-CORRED` no se mueve, y es el caso difícil del lote.** El recurso se llama
  «riel superior e inferior con carros» sin decir si es herraje de armario o kit de
  puerta corredera, y el mercado cobra cosas muy distintas: el kit INDAUX JUNIOR-1
  (dos rieles de 2 m con carros y ruedas) sale a 5,12 €/m de riel, mientras el kit de
  dos puertas con perfil de 2 m y topes se va a 20,62 €/m y el Tourly de 183 cm a
  18,96 €/m. Un rango que va de 5,12 a 20,62 €/m no permite elegir sin cambiar el
  alcance del recurso, así que **se mantiene 15,95** —dentro de la banda y en la zona
  de los kits de puerta de paso— y se deja escrito el motivo. Si algún día se separan
  «riel de armario» y «kit de puerta corredera» en dos recursos, este se parte con
  precios distintos.
* **`MT-AISL-REFLECT` se queda prácticamente igual porque el mercado lo confirma.** Tres
  rollos con foil de aluminio y burbuja de polietileno dan 2,32, 3,60 y 4,25 €/m² sin
  IVA. Se adopta 3,60 €/m², que es el **único cuya ficha declara doble capa de burbuja**,
  que es justo lo que pide el recurso; el de 4,25 € es monocapa de 8 mm (más aislante
  por espesor, no por composición) y el de 2,32 € es de 4 mm. El precio derivado de
  3,65 € caía a 5 céntimos: la diferencia no es el número, es que ahora hay banda.

**Lo que el banco no daba.** Los cuatro recursos tenían candidatos BCCA y los cuatro se
descartaron al leer la ficha, igual que en el lote 2:

| Recurso | Candidato BCCA | Por qué no sirve |
|---|---|---|
| `MT-SELLA-PASE` | `IC90049` (22,80 €), `WW00001` (10,55 €) | Conexión de radiador y sellado de junta de ventana, no un pase de instalación |
| `MT-RIEL-CORRED` | `IM02131` (92,40 €) | «Equipo de incremento por m de recorrido» de puente grúa, no un riel de puerta |
| `MT-SAN-FIJA` | `IF17250` (62,63 €), `IS08` (0,28 €) | Inodoro para discapacitado y taco suelto; solo `IF17200` (3,25 €) sirve, y para la tornillería |
| `MT-AISL-REFLECT` | `IS071` (2,09 €), `VL04500A` (62,26 €) | EPS de 20 mm y doble luna: ni reflexivo ni burbuja |

Impacto en el catálogo: **39 partidas** tocan alguno de los cuatro recursos. Mediana
**+5,54 %**, p10 −0,64 %, p90 +26,85 %, mínimo **−0,64 %** y máximo **+43,01 %**
(`08.04.01.070`, sellado de paso de tubería con collarín).

## 4. Registro y herramientas

No hay formato nuevo: se reutilizan las tres piezas de los lotes anteriores.

1. **`espana_cotizaciones_2026-11-08.csv`** — once ofertas más (20 → 31), con precio
   publicado, IVA, conversión de unidad, precio sin IVA por unidad, URL, fecha y
   comparabilidad.
2. **`espana_decision_cotizaciones_2026-11-08.csv`** — cuatro decisiones más (8 → 12),
   con `metodo`, banda, confianza, fuente y criterio.
3. **`tools/aplicar_cotizaciones_espana.py`** — sin cambios de lógica; la cabecera del
   SQL ya decía «todos los lotes» desde el lote 2.

El SQL (`cotizaciones_es_2026-11-08.sql`) cubre los **doce** recursos del registro. Los
ocho de los lotes 1 y 2 se actualizan con los mismos valores que ya están en
producción, así que repetirlo no cambia nada; los cuatro nuevos son los que mueven el
precio. Sigue siendo de alcance mínimo: doce `UPDATE` con `codigo_recurso`,
`pais_codigo = 'ES'` y `organizacion_id IS NULL`.

## 5. Carga en producción

Proyecto `CotizaT-Generador` (`ivsuiyfljcajrijgwisg`). Cuatro `UPDATE` acotados y tres
entradas en `public.historial_precios_recursos` (`MT-RIEL-CORRED` no genera historial
porque su precio no cambia, igual que el perfil de aluminio en el lote 2).

| Comprobación | Resultado |
|---|---|
| Referencias nacionales ES | 390 (sin cambio) |
| Referencias ES con `confianza = 'referencia'` | **52** (48 + 4) |
| Referencias ES `derivado` / `referencia` | **338 / 52** (eran 342 / 48) |
| Overrides de empresa tocados | 0 |
| Referencias de otros países | 8.162 (sin cambio) |
| Filas nuevas en `historial_precios_recursos` | 3 (`MT-AISL-REFLECT` 3,65 → 3,60; `MT-SAN-FIJA` 5,47 → 8,90; `MT-SELLA-PASE` 5,24 → 9,96), ids 12-14 |
| Moneda / IVA de los cuatro | `EUR` / `no` |
| `fecha_consulta` | 2026-11-08 en los cuatro |

## 6. Verificación

* `tests/test_cotizaciones_espana.py`: de 10 a **13 pruebas**. Las tres nuevas fijan el
  lote 3: los cuatro recursos con su precio, banda y método; que `MT-RIEL-CORRED` es el
  único que mantiene precio y que la banda lo enmarca por los dos lados; y que el anillo
  de cera solo ya supera el derivado y que el precio del kit es exactamente la suma de
  las dos piezas publicadas.
* El recuento del registro pasa de 8 a 12; el resto de pruebas (banda coherente, dos
  ofertas con URL por recurso, SQL acotado, validador que rechaza bandas incoherentes)
  valida los doce recursos sin cambios.
* Regenerados los artefactos que cuelgan de la matriz:
  `tools/generar_matriz_precios_espana.py` (390 filas, **52 directas** + 338 derivadas),
  `tools/inventario_precios_espana.py` y `tools/analizar_impacto_precios_espana.py`.
* Regenerado el índice público `basedatos_partidas/datos/precios_publicos/ES.json` con
  `tools/generar_precios_publicos.py`: solo cambia ES; los otros 21 mercados se
  reescriben idénticos.
* Suite completa: **3673 superadas, 13 omitidas, 0 fallidas**.

## 7. Lo que queda del punto 2

De las 39 referencias `mercado_rango` con uso real, **12 están cotizadas** (5 del lote 1,
3 del lote 2 y 4 de este) y **quedan 27, todas con 5 usos o menos**:

| Recurso | Usos | Precio derivado | Unidad |
|---|---:|---|---|
| `MT-QUIMICO-LIMP-AC` | 5 | 9,68 | ud |
| `MT-PASIVANTE` | 5 | 11,16 | l |
| `MT-CONTENEDOR` | 5 | 74,05 | ud |
| `MT-TOLDO` | 4 | 54,68 | m² |
| `MT-LAMP-OBRA` | 4 | 10,82 | ud |
| `MT-GRAMA` | 4 | 3,65 | m² |
| `MT-ESTRUCT-MESON` | 4 | 13,67 | m |
| `MT-CIELO-METAL` | 4 | 15,95 | m² |
| `MT-CANON` | 4 | 7,00 | m³ |
| `MT-TABLERO-DIST` | 3 | 54,68 | ud |
| `MT-LINEA-VIDA` | 3 | 7,06 | m |
| `MT-CINTA-LED` | 3 | 7,06 | m |
| `MT-CASETA-BIEN` | 3 | 136,71 | ud |

Y doce más con 1 o 2 usos: `MT-ZIPPER`, `MT-VAPOR`, `MT-TIMBRE`, `MT-TEJA-ASF`,
`MT-TABLERO-PROV`, `MT-PERFIL-CORTINERO`, `MT-GAS-REFRIG`, `MT-BLQ-VIDRIO`,
`MT-VIDRIO-DECOR`, `MT-SOPORTE-ANTIVIB`, `MT-PLATINA-DIV`, `MT-PIEDRA-FACHADA`,
`MT-GABINETE-MANG` y `MT-FIBRA-NAT`.

Las 15 referencias de mercado **sin uso** siguen sin cotizar, como estaba decidido:
`MT-PLANTA-ELEC`, `MT-PARARRAYOS-PUNTA`, `MT-PARARRAYOS-PDA`, `MT-PANEL-SOLAR`,
`MT-INVERSOR`, `MT-HIDRONEUMATICO`, `MT-DPS-3`, `MT-DOM-TECLADO`,
`MT-DOM-SENSOR-TEMP`, `MT-DOM-REPETIDOR`, `MT-DOM-PANEL`, `MT-CONT-DESCARGAS`,
`MT-CAMARA-CCTV`, `MT-BOMBA-AGUA` y `MT-AUTOM-PORTON`.

**Qué significa para el punto 2.** El criterio del usuario era cotizar solo lo que tiene
uso real y repercusión en presupuesto. Eso está hecho: los recursos que se cotizan ahora
mueven 39, 183 y 39 partidas por lote; los 27 que quedan mueven 1-5 partidas cada uno.
Seguir por ahí ya no mejora la fiabilidad de los presupuestos de forma apreciable; lo que
sí la mejoraría es atacar los recursos `derivado` de mucho uso que **no** venían de
`mercado_rango` (mano de obra y maquinaria, que se auditó por otra vía, y los materiales
compuestos), y eso es otro trabajo, no este punto.
