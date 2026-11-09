# Cotizaciones reales de España, lote 2 — 8 de noviembre de 2026

**Resultado: tres recursos que llevaban precio derivado pasan a precio cotizado.**
Son los tres de mayor uso que quedaban y suman **184 usos en 183 partidas**: 74
(`MT-PERFIL-ALUM`), 73 (`MT-SENAL-OBRA`) y 37 (`MT-REGUL-GAS`). Dos cambian de
precio, uno lo mantiene y gana evidencia, y los tres dejan de repetir el mismo
número en `precio_min`, `precio_referencia` y `precio_max`.

Con este lote, de las 39 referencias de mercado con uso real, **8 están cotizadas**
y quedan 31. Las referencias ES con `confianza = 'referencia'` pasan de 45 a **48**;
las `derivado`, de 345 a **342**.

## 1. Qué se ha cambiado

| Recurso | Usos | Antes (derivado) | Ahora (cotizado) | Δ | Evidencia |
|---|---|---|---|---|---|
| `MT-PERFIL-ALUM` | 74 | 10,82 | **10,82** | 0,0 % | Arialpro (3 perfiles) + Proycsa (1 perfil) |
| `MT-SENAL-OBRA` | 73 | 6,27 | **9,90** | +57,9 % | Conos de 75 cm: López Parra, Atprotección y Leroy Merlin |
| `MT-REGUL-GAS` | 37 | 27,34 | **15,69** | −42,6 % | Bauhaus + banco BCCA `IG03300` / `IG03400` |

Las tres filas pasan a `confianza = referencia`, `incluye_iva = 'no'`,
`fecha_consulta = 2026-11-08` y banda medida en las columnas numéricas.

## 2. Las diez ofertas, una a una

Todas consultadas el **2026-11-08**. El detalle completo, con conversión de IVA y de
unidad, está en `espana_cotizaciones_2026-11-08.csv`.

| Recurso | Producto | Publicado | Sin IVA | €/unidad | Δ vs matriz |
|---|---|---|---|---|---|
| `MT-PERFIL-ALUM` | Perfil 3030, 6063 T6 anodizado (0,932 kg/m) | 10,75 €/m | 8,88 | 9,53 €/kg | −11,9 % |
| `MT-PERFIL-ALUM` | Perfil 4040, 6063 T6 anodizado (1,508 kg/m) | 17,95 €/m | 14,83 | 9,84 €/kg | −9,1 % |
| `MT-PERFIL-ALUM` | Perfil 6060, 6063 T6 anodizado (2,63 kg/m) | 23,99 €/m | 19,83 | 7,54 €/kg | −30,3 % |
| `MT-PERFIL-ALUM` | Perfil básico 40×40 anodizado (1,51 kg/m) | 26,41 €/m | 21,83 | 14,46 €/kg | +33,6 % |
| `MT-SENAL-OBRA` | Cono 75 cm con banda reflectante (Coysa) | 7,90 €/ud | 6,53 | 6,53 €/ud | +4,1 % |
| `MT-SENAL-OBRA` | Cono 2 piezas 75 cm, base de caucho | 11,98 €/ud | 9,90 | 9,90 €/ud | +57,9 % |
| `MT-SENAL-OBRA` | Cono 75 cm lastrado con banda reflectante | 12,99 €/ud | 10,74 | 10,74 €/ud | +71,3 % |
| `MT-REGUL-GAS` | Regulador butano/propano 30 mbar con llave de corte | 18,99 €/ud | 15,69 | 15,69 €/ud | −42,6 % |
| `MT-REGUL-GAS` | Conjunto regulador con tubo de 1,5 m y abrazadera | 13,99 €/ud | 11,56 | 11,56 €/ud | −57,7 % |
| `MT-REGUL-GAS` | Regulador baja presión propano 1/2″ (banco BCCA 2024-01) | 14,64 €/ud | 14,64 | 14,64 €/ud | −46,5 % |

Dos conversiones que no se pueden saltar, igual que en el lote 1:

* **IVA.** Las tres tiendas publican con IVA (21 %); el banco BCCA publica sin IVA.
  Arialpro lo dice en la ficha («Impuestos incluidos»), Atprotección publica además
  el precio sin IVA (9,90 €), y el BCCA ya viene neto. Mezclarlos sin normalizar
  produce errores del 21 %.
* **Unidad.** El perfil se vende **por metro**, no por kilo: el precio se divide por
  los kg/m que declara la ficha del producto (0,932 / 1,508 / 2,63 / 1,51). Sin esa
  división, el perfil 6060 parecería tres veces más caro que la matriz.

## 3. Por qué cada decisión es la que es

* **`MT-PERFIL-ALUM` no se mueve, y era el riesgo del lote.** Con 74 usos, era el
  recurso de mayor impacto de toda la matriz. Las cuatro ofertas dan 7,54–14,46 €/kg
  sin IVA y el precio de la matriz (10,82) cae dentro. Se mantiene por dos motivos
  escritos en el criterio: la banda lo enmarca y el recurso incluye «sus accesorios»,
  que el perfil desnudo no lleva (los herrajes de ventana se cobran aparte). Lo que
  cambia no es el número, es la evidencia. **El banco BCCA no sirve aquí**: sus tres
  candidatos son perfiles de acero, no de aluminio, y usarlos habría metido un
  precio de 1,50 €/kg en un recurso de aluminio.
* **`MT-SENAL-OBRA` sube un 58 %.** La horquilla declarada el 7 de noviembre era
  3–10 €/ud y **el cono más barato localizado ya cuesta 6,53 €**: el suelo de la
  horquilla no existe en el mercado. Se adopta 9,90 €, el precio que la tienda
  publica sin IVA para un cono de 75 cm con base de caucho reciclado. El banco BCCA
  solo ofrece señales de peligro tipo A (48–219 €), que no son el cono que mide este
  recurso; y la cinta de balizamiento tiene recurso propio (`MT-CINTA-ENM`), así que
  la unidad se valora como cono y no como «señal + cinta + cono».
* **`MT-REGUL-GAS` baja un 43 %.** Es el primer recurso del punto 2 en el que el
  banco y el minorista dicen lo mismo: BCCA 2024-01 valora el regulador de butano en
  11,36 € y el de propano de 1/2″ en 14,64 €; el minorista de 2026 da 11,56 € (conjunto
  con tubo y abrazadera) y 15,69 € (con llave de corte incluida). Se adopta 15,69 €
  porque es el único que declara la llave de corte que el recurso nombra. La horquilla
  declarada 15–40 €/ud estaba puesta al doble del mercado.

Impacto en el catálogo: **183 partidas** tocan alguno de los tres recursos. Mediana
**0,0 %** (las 74 del perfil no se mueven), mínimo **−25,1 %**
(`01.01.02.030`, aislamiento de servicio de gas) y máximo **+62,8 %**
(`17.03.01.060`, señalización de vías de evacuación).

## 4. Registro y herramientas

No hay formato nuevo: se reutilizan las tres piezas del lote 1.

1. **`espana_cotizaciones_2026-11-08.csv`** — diez ofertas más, con precio publicado,
   IVA, conversión de unidad, precio sin IVA por unidad, URL, fecha y comparabilidad.
2. **`espana_decision_cotizaciones_2026-11-08.csv`** — tres decisiones más, con
   `metodo`, banda, confianza, fuente y criterio. El fichero agrupa **todas las
   decisiones cerradas el 8 de noviembre** (lote 1 y lote 2), que es lo que leen tanto
   el generador de la matriz como el aplicador.
3. **`tools/aplicar_cotizaciones_espana.py`** — sin cambios de lógica. Lo único que se
   ha tocado es la cabecera del SQL, que ya no dice «lote 1» sino la fecha del registro,
   y avisa de que repetir los `UPDATE` de un lote ya cargado es idempotente.

El SQL (`cotizaciones_es_2026-11-08.sql`) vuelve a cubrir los ocho recursos del
registro. Los cinco del lote 1 se actualizan con **los mismos valores** que ya están
en producción, así que ejecutarlo no cambia nada de lo cargado ayer; los tres nuevos
son los que mueven el precio. Sigue siendo de alcance mínimo: ocho `UPDATE` con
`codigo_recurso`, `pais_codigo = 'ES'` y `organizacion_id IS NULL`.

## 5. Carga en producción

Proyecto `CotizaT-Generador` (`ivsuiyfljcajrijgwisg`). Tres `UPDATE` acotados y dos
entradas en `public.historial_precios_recursos` con precio anterior y nuevo
(`MT-PERFIL-ALUM` no genera historial porque su precio no cambia, igual que el vidrio
en el lote 1).

| Comprobación | Resultado |
|---|---|
| Referencias nacionales ES | 390 (sin cambio) |
| Referencias ES con `confianza = 'referencia'` | **48** (45 + 3) |
| Referencias ES `derivado` / `referencia` | **342 / 48** (eran 345 / 45) |
| Overrides de empresa tocados | 0 |
| Referencias de otros países | 8.162 (sin cambio; 21 mercados × 388 + 14 overrides de CR) |
| Filas nuevas en `historial_precios_recursos` | 2 (`MT-SENAL-OBRA` 6,27 → 9,90; `MT-REGUL-GAS` 27,34 → 15,69) |
| Moneda / IVA de los tres | `EUR` / `no` |
| `fecha_consulta` | 2026-11-08 en los tres |
| md5 de `fuente` y `observaciones` (BD vs matriz) | idéntico en las 3 filas |

El contraste se hace con `md5()` calculado en Postgres sobre `fuente` y
`observaciones` y el mismo cálculo en local sobre la matriz, como en el lote 1: los
seis valores coinciden.

## 6. Verificación

* `tests/test_cotizaciones_espana.py`: de 7 a **10 pruebas**. Las tres nuevas fijan el
  lote 2: los tres recursos con su precio, banda y método; que la banda deja de repetir
  el precio; y que `MT-PERFIL-ALUM` mantiene 10,82 con ofertas de **dos distribuidores
  distintos**.
* El recuento del registro pasa de 5 a 8; el resto de pruebas del fichero (banda
  coherente, dos ofertas con URL por recurso, SQL acotado, validador que rechaza bandas
  incoherentes) valida los ocho recursos sin cambios.
* Regenerados los artefactos que cuelgan de la matriz: `tools/generar_matriz_precios_espana.py`
  (390 filas, 48 directas) y `tools/inventario_precios_espana.py`. El inventario solo
  cambia las tres filas de estos recursos.
* Regenerado el índice público `basedatos_partidas/datos/precios_publicos/ES.json`
  con `tools/generar_precios_publicos.py`: los precios de las páginas públicas salen
  de ahí y, sin regenerarlo, el artefacto servido se queda con los importes viejos.
  Solo cambia ES; los otros 21 mercados se reescriben idénticos.
* Suite completa: **3670 superadas, 13 omitidas, 0 fallidas** (274 s con `-n auto`).

## 7. Lo que queda del punto 2

De las 39 referencias de mercado con uso real, **8 están cotizadas** (5 del lote 1 y 3
de este). Las siguientes por impacto, ya sin lote asignado:

| Recurso | Usos | Precio derivado | Unidad |
|---|---|---|---|
| `MT-SELLA-PASE` | 17 | 5,24 | ud |
| `MT-RIEL-CORRED` | 17 | 15,95 | m |
| `MT-SAN-FIJA` | 13 | 5,47 | ud |
| `MT-AISL-REFLECT` | 9 | 3,65 | m² |

Las 15 referencias de mercado **sin uso** siguen sin cotizar, como estaba decidido:
`MT-PLANTA-ELEC`, `MT-PARARRAYOS-PUNTA`, `MT-PARARRAYOS-PDA`, `MT-PANEL-SOLAR`,
`MT-INVERSOR`, `MT-HIDRONEUMATICO`, `MT-DPS-3`, `MT-DOM-TECLADO`,
`MT-DOM-SENSOR-TEMP`, `MT-DOM-REPETIDOR`, `MT-DOM-PANEL`, `MT-CONT-DESCARGAS`,
`MT-CAMARA-CCTV`, `MT-BOMBA-AGUA` y `MT-AUTOM-PORTON`.
