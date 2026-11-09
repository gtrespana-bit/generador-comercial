# Cotizaciones reales de España, lote 1 — 8 de noviembre de 2026

**Resultado: cinco recursos que llevaban precio derivado pasan a precio cotizado**,
con dos ofertas publicadas por recurso, su banda medida en `precio_min` / `precio_max`
y la fecha de consulta del día. Tres cambian de precio, uno lo mantiene y gana
evidencia, y uno se queda igual porque las dos fuentes lo enmarcan.

Esto arranca el **punto 2** de la lista de trabajo: convertir las 39 referencias de
mercado que sí se usan en algún presupuesto en cotizaciones trazables. La sesión
anterior dejó el inventario hecho (54 referencias `mercado_rango`, 39 con uso real,
15 sin uso) y cinco evidencias recogidas; esta cierra la primera tanda con registro,
herramienta, SQL y carga en producción.

## 1. Qué se ha cambiado

| Recurso | Usos | Antes (derivado) | Ahora (cotizado) | Δ | Evidencia |
|---|---|---|---|---|---|
| `MT-SOPORTE-AC` | 36 | 18,23 | **10,98** | −39,8 % | Leroy Merlin, escuadras STAG 50×45 y 50×50 |
| `MT-VIDRIO-TEMP` | 35 | 77,47 | **77,47** | 0,0 % | CYPE LVT010 (banco) + Plakglass (minorista) |
| `MT-CIELO-PVC` | 4 | 18,23 | **18,01** | −1,2 % | Leroy Merlin, lámina alveolar y panel alero 10 mm |
| `MT-PERSIANA-ALU` | 4 | 62,66 | **56,19** | −10,3 % | Avosdim, persiana de aluminio aislado con cinta |
| `MT-TRAMPA-GRASA` | 1 | 88,86 | **169,00** | +90,2 % | Bomdesa, separador ECO 72 l + Eurosur 55 l |

Cinco recursos cubren **80 usos** en descomposiciones (36 + 35 + 4 + 4 + 1). Los
cinco salen de `mercado_rango` y pasan a `confianza = referencia`: ya no son «precio
de matriz dentro de una horquilla declarada», son oferta publicada con URL y fecha.

Además, la banda deja de ser decorativa: hasta hoy la matriz repetía el mismo número
en `precio_min`, `precio_referencia` y `precio_max` y la horquilla real solo vivía en
el texto de `observaciones`. Las cinco filas cotizadas llevan ahora la banda medida
en las columnas numéricas.

## 2. Las diez ofertas, una a una

Todas consultadas el **2026-11-08**. El detalle completo, con conversión de IVA y de
unidad, está en `espana_cotizaciones_2026-11-08.csv`.

| Recurso | Producto | Publicado | Sin IVA | €/unidad | Δ vs matriz |
|---|---|---|---|---|---|
| `MT-CIELO-PVC` | Panel alero PVC 300×25 cm × 10 mm | 21,79 €/m² | 18,01 | 18,01 €/m² | −1,2 % |
| `MT-CIELO-PVC` | Lámina alveolar Renolam blanco brillo | 20,25 €/m² | 16,74 | 16,74 €/m² | −8,2 % |
| `MT-PERSIANA-ALU` | Persiana manual 120×120 cm (1,44 m²) | 97,90 €/ud | 80,91 | 56,19 €/m² | −10,3 % |
| `MT-PERSIANA-ALU` | Persiana manual 155×120 cm (1,86 m²) | 119,90 €/ud | 99,09 | 53,27 €/m² | −15,0 % |
| `MT-SOPORTE-AC` | Escuadra STAG 50×50 cm | 13,29 €/ud | 10,98 | 10,98 €/ud | −39,8 % |
| `MT-SOPORTE-AC` | Escuadra STAG 50×45 cm | 9,29 €/ud | 7,68 | 7,68 €/ud | −57,9 % |
| `MT-TRAMPA-GRASA` | Separador 55 l bajo fregadero | 531,58 €/ud | 439,32 | 439,32 €/ud | +394,4 % |
| `MT-TRAMPA-GRASA` | Separador ECO UNE-EN 1825, 72 l | 204,49 €/ud | 169,00 | 169,00 €/ud | +90,2 % |
| `MT-VIDRIO-TEMP` | Vidrio templado claro 10 mm a medida | 152,40 €/m² | 125,95 | 125,95 €/m² | +62,6 % |
| `MT-VIDRIO-TEMP` | Vidrio templado 10 mm 1C1 (banco CYPE) | 59,13 €/m² | 59,13 | 59,13 €/m² | −23,7 % |

Dos conversiones que hay que hacer a mano y no se pueden saltar:

* **IVA.** Las tiendas publican con IVA; el banco CYPE publica sin IVA. Mezclarlos
  sin normalizar produce errores del 21 %, no del 2 %. En el registro queda la
  columna `iva_incluido` y la conversión explícita.
* **Unidad.** Las persianas se venden por unidad de hueco, no por metro cuadrado.
  119,90 € no es «119,90 €/m²»: es 64,46 €/m² con IVA, porque la unidad mide 1,86 m².
  Con la unidad sin convertir, la persiana parecería un 91 % más cara que la matriz.

## 3. Por qué cada decisión es la que es

* **`MT-VIDRIO-TEMP` no baja.** Es el caso más interesante del lote. El banco da
  59,13 €/m² y el minorista 125,95 €/m², así que el precio de la matriz (77,47) cae
  justo en medio de dos fuentes reales. La ficha del recurso incluye perforaciones,
  que el precio de banco no valora, y el minorista sí. Sustituirlo por el banco
  habría rebajado un 24 % un material que el recurso define con mecanizado. Lo que
  cambia aquí no es el número, es la evidencia: deja de ser «sin ficha de banco».
* **`MT-SOPORTE-AC` baja un 40 %.** La horquilla declarada el 7 de noviembre era
  15–60 €/ud y el mercado real son 7,68–10,98 € sin IVA. La horquilla estaba mal
  puesta, no el precio: se declaró sin consultar y el resultado era el doble del
  precio de tienda. Con 36 usos, era el error de mayor impacto del lote.
* **`MT-TRAMPA-GRASA` sube un 90 %.** Al contrario: la horquilla declarada 60–150 €/ud
  no existe en el mercado de separadores prefabricados. El más barato localizado con
  norma UNE-EN 1825 cuesta 204,49 € con IVA. Se adopta 169,00 € —el mínimo real— y se
  deja escrito que el recurso no declara capacidad: si la partida pide un separador
  de cocina de mayor caudal, el precio se queda corto. Solo lo usa una partida.
* **`MT-CIELO-PVC` y `MT-PERSIANA-ALU` se ajustan poco.** En el cielo de PVC se adopta
  el extremo alto porque el recurso incluye perfilería de remate, que la tienda cobra
  aparte. En la persiana se adopta la unidad pequeña, que es la que peor €/m² tiene.
* **`MT-SOPORTE-AC` y los anclajes.** La descripción del recurso dice «con sus
  anclajes», pero las escuadras de tienda no los llevan. El catálogo valora los
  pernos y los antivibratorios como recursos propios (`MT-PERNO-ANCLA`,
  `MT-SOPORTE-ANTIVIB`), así que el precio de tienda es el comparable correcto y
  añadir 1–2 € por anclajes duplicaría coste en las partidas que ya los llevan.

## 4. Cómo queda registrado

El formato de registro, que era la decisión pendiente, es de tres piezas:

1. **`espana_cotizaciones_2026-11-08.csv`** — las diez ofertas tal como se ven en la
   tienda: precio publicado, IVA, conversión de unidad, precio sin IVA por unidad,
   URL, fecha y comparabilidad. Es la prueba.
2. **`espana_decision_cotizaciones_2026-11-08.csv`** — una fila por recurso con
   `metodo`, `precio`, `precio_min`, `precio_max`, `confianza`, `fuente` y `criterio`.
   Es la decisión, y lleva escrito por qué se adopta ese número y qué queda fuera.
3. **`tools/aplicar_cotizaciones_espana.py`** — valida el registro contra la matriz y
   emite el SQL de carga. Valida que el código exista, que la moneda sea EUR, que la
   banda contenga el precio, que el método y la confianza sean conocidos y que ni
   fuente ni criterio lleven el separador del CSV. Sin `--aplicar` solo valida.

**La matriz tiene un solo escritor.** `basedatos_partidas/salida/precios_recursos_espana.csv`
se genera con `tools/generar_matriz_precios_espana.py`, que ahora lee este registro en
la capa `referencias_cotizadas_espana()`, aplicada **la última**: manda sobre el cierre
del 7 de noviembre y sobre cualquier lote anterior del mismo recurso. Si la herramienta
escribiera también la matriz, la siguiente regeneración desharía el cambio sin avisar,
así que en vez de escribirla **comprueba** que ya la refleja y falla con un mensaje
explícito si alguien olvidó regenerar. El SQL se construye leyendo la matriz, no el
registro, para que producción y repositorio no puedan divergir.

El SQL (`docs/auditoria_precios/cotizaciones_es_2026-11-08.sql`) es de **alcance
mínimo**: cinco `UPDATE` con `codigo_recurso`, `pais_codigo = 'ES'` y
`organizacion_id IS NULL`. No reescribe la carga entera de 390 referencias, así que
no puede arrastrar cambios que nadie ha decidido hoy.

Las dos pruebas de `tests/test_cierre_auditoria_espana.py` que exigían coincidencia
entre el libro del 7 de noviembre y la matriz ahora excluyen los códigos que tienen
precio posterior, con el motivo escrito en el propio test: el cierre describe con qué
evidencia se cerró cada recurso **ese día**, no cuál es su precio hoy.

## 5. Carga en producción

Proyecto `CotizaT-Generador` (`ivsuiyfljcajrijgwisg`). Aplicado con una transacción
que actualiza las cinco filas y, antes, escribe cuatro entradas en
`public.historial_precios_recursos` con precio anterior, precio nuevo y motivo
(`MT-VIDRIO-TEMP` no genera historial porque su precio no cambia).

| Comprobación | Resultado |
|---|---|
| Referencias nacionales ES activas | 390 (sin cambio) |
| Referencias ES con `confianza = 'referencia'` | 45 (40 + 5) |
| Overrides de empresa tocados | 0 |
| Referencias de otros países | 8.162 (sin cambio; incluye los 14 overrides) |
| Filas nuevas en `historial_precios_recursos` | 4 |
| Moneda / IVA de las cinco | `EUR` / `no` |
| `fecha_consulta` | 2026-11-08 en las cinco |
| md5 de `fuente` y `observaciones` (BD vs matriz) | idéntico en las 5 filas |
| Referencias ES `derivado` / `referencia` | 345 / 45 |

El contraste final no se hace «a ojo»: se compara el `md5()` que calcula Postgres
sobre `fuente` y `observaciones` con el que se calcula en local sobre la matriz. La
primera carga dejó las observaciones de producción más cortas que el criterio del
registro; se detectó con ese contraste y se corrigió en las cinco filas antes de
cerrar. Los precios y las bandas coincidían desde el principio.

## 6. La cuestión de la moneda, resuelta

Quedaba abierto si las cotizaciones en EUR debían convertirse a los USD de
`basedatos_partidas/datos/recursos.json`. **No hace falta convertir nada, y hacerlo
habría sido un error**: el catálogo base es USD (`precio_local = precio_usd × tasa`),
pero los precios nacionales viven en `public.precios_recursos_mercado`, que **guarda
la moneda de cada mercado** y la aplica al presupuesto en el momento de dibujarlo
(`app/services/precios_partidas.py`: si la moneda de la fila no es la del mercado, la
descarta como dato inválido y convierte solo con tasa verificada). Es decir:
`recursos.json` no se toca, y las cotizaciones EUR entran como EUR en su mercado. La
arquitectura ya lo tenía resuelto; lo que faltaba era comprobarlo antes de escribir.

## 7. Verificación

* **Suite completa: 3.658 superadas, 13 omitidas, 0 fallidas** (256 s con `-n auto`).
* Las siete pruebas nuevas (`tests/test_cotizaciones_espana.py`) atan el registro, la
  matriz y el SQL: banda coherente, matriz que publica la cotización y no el valor
  derivado, dos ofertas con URL por recurso, SQL que solo toca referencias nacionales
  ES, y el validador rechazando bandas incoherentes y fuentes con separador.
* Regenerados los artefactos que colgaban de la matriz: el inventario integral
  (`tools/inventario_precios_espana.py`) y las dos pruebas del cierre que comparaban
  libro y matriz (`tests/test_cierre_auditoria_espana.py`), que ahora excluyen los
  códigos con precio posterior y lo dicen por escrito.

## 8. Lo que queda del punto 2

De las 39 referencias de mercado con uso real, **5 están cotizadas**. Las siguientes
por impacto y sin fuente externa todavía:

| Recurso | Usos | Precio derivado | Unidad |
|---|---|---|---|
| `MT-PERFIL-ALUM` | 74 | 10,82 | kg |
| `MT-SENAL-OBRA` | 73 | 6,27 | ud |
| `MT-REGUL-GAS` | 37 | 27,34 | ud |
| `MT-SELLA-PASE` | 17 | 5,24 | ud |
| `MT-RIEL-CORRED` | 17 | 15,95 | m |

`MT-PERFIL-ALUM` y `MT-SENAL-OBRA` son los dos de mayor uso de toda la matriz
(74 y 73 partidas): por volumen, valen más que los cinco de este lote juntos. Los
perfiles de aluminio se venden por kg con aleación y acabado muy variables, y la
señal de obra es un producto normalizado (UNE 81301), así que ambos piden catálogo de
fabricante más que búsqueda de tienda. Es el siguiente bloque natural.

Las 15 referencias de mercado **sin uso** siguen sin cotizar, como estaba decidido:
`MT-PLANTA-ELEC`, `MT-PARARRAYOS-PUNTA`, `MT-PARARRAYOS-PDA`, `MT-PANEL-SOLAR`,
`MT-INVERSOR`, `MT-HIDRONEUMATICO`, `MT-DPS-3`, `MT-DOM-TECLADO`,
`MT-DOM-SENSOR-TEMP`, `MT-DOM-REPETIDOR`, `MT-DOM-PANEL`, `MT-CONT-DESCARGAS`,
`MT-CAMARA-CCTV`, `MT-BOMBA-AGUA` y `MT-AUTOM-PORTON`.
