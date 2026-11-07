# Auditoría de identidad: ¿falta el artículo o no lo sabemos encontrar?

Fecha: 2026-11-07 · Base contrastada: Extremadura 2026 (`BCEXTGREM_26_v1.bc3`, SHA-256
`ac6f88c7…d5cafd5`) · Registro: `espana_2026-11-06.csv` (388 recursos).

## La pregunta

«Una base de datos para construcción tiene que rellenar absolutamente todos los huecos:
si quedan 168 recursos sin precio es porque estamos emparejando nombres que parecen el
mismo artículo y no lo son (o al revés).»

La respuesta corta, medida sobre la base y no sobre impresiones: **de los 164 recursos que
siguen sin precio revisado, 62 tienen el artículo en la base con otra medida o clase, 19 son
cestas de consumibles que ninguna base cotiza como una sola ficha, 64 solo comparten
palabras con un artículo distinto y 19 no tienen ninguna ficha parecida. Sí había huecos
reales que estábamos dejando pasar: cinco de ellos se han cerrado en este lote, y uno de
ellos porque nuestro propio rechazo manual estaba mal argumentado.**

## 1. La base no es infinita: lo que de verdad no contiene

Búsqueda literal sobre los 30.137 precios simples utilizables (29.112 materiales, 1.370
maquinaria, 94 manutención):

| Término buscado | Fichas encontradas | Lectura |
|---|---|---|
| `atornillador*` | **0** | No hay atornilladora: `MQ-ATORN` (162 usos) no se puede cotizar con esta base. |
| `cortadora` + azulejo/agua/cerámica | **0** | Solo cortadoras de hormigón (disco radial, diésel). `MQ-CORT-AGUA` queda fuera. |
| `aspirador` industrial | **0** | Solo barredora autopropulsada (109,56 €/h) y bombas autoaspirantes. |
| `disco de corte`, `punta`, `cincel` como precio simple | **0** | Son consumibles: la base no los vende sueltos (`MT-CONS-DEM`, 398 usos). |
| `andamio` | 90 fichas, **todas en €/m²·día o €/m² de montaje** | El recurso está en €/h: el problema es de unidad y de concepto, no de nombre. |
| `hormigón` premezclado | 1.029 fichas, **solo suministro en central** | No hay «puesto en obra»: transporte y bombeo son siempre un pendiente aparte. |

Esto no es una excusa: es lo que hay que decirle a un cliente cuando pide un precio que la
base no puede sostener. Los cuatro huecos de arriba suman 615 usos (19 recursos).

## 2. La base sí tiene el artículo en casos que estábamos perdiendo

### 2.1 Un rechazo nuestro estaba mal: el bloque de 20 cm

`MT-BLQ-20` («Bloque de concreto hueco de 20x20x40 cm») figuraba como divergencia con este
motivo escrito a mano: *«el candidato de Extremadura es bloque de 25x20x40 cm»*. Era falso:
el candidato de **rango 1** del cribado era `P01BG200`, «Bloque de hormigón hueco
**20x20x40** cm», 0,63 €/ud, precisión 0,83 y números compatibles. El rechazo se redactó
mirando la fila 4 de la tabla. El rechazo se ha revertido y el recurso queda confirmado
(precio propio 0,68 €, −7,4 % frente a la ficha).

### 2.2 El hormigón: la clase de resistencia es la identidad

La base publica una escalera completa de hormigón de central. La equivalencia
`kg/cm² = N/mm² × 10` da la identidad del artículo, cosa que el parecido de palabras nunca
iba a dar:

| Recurso | Precio propio | Ficha de la base | €/ud | Δ |
|---|---|---|---|---|
| `MT-CONC-180` (4 usos) | 92,00 | `P01HCM003` HM-20/B/20/X0 central | 94,00 | +2,2 % |
| `MT-CONC-210` (106 usos) | 100,00 | `P01HCA300` HA-25/B/20/X0 central | 105,00 | +5,0 % |
| `MT-CONC-250` (66 usos) | 108,00 | `P01HCA300` HA-25/B/20/X0 central | 105,00 | −2,8 % |
| `MT-CONC-300` (3 usos) | 118,00 | `P01HCA320` HA-30/B/20/X0 central | 110,00 | −6,8 % |

Los cuatro quedan **confirmados sin cambiar el precio**: el valor propio incluye puesta en
obra y la ficha es suministro en central, de modo que la comparación acredita la banda
(±15 %), no una sustitución. 179 usos dejan de estar sin verificar.

### 2.3 El extintor: el nombre elegía el artículo equivocado

`MT-EXTINTOR` («polvo químico, con soporte y señalización») tenía como contraste un extintor
de **50 kg** a 421,04 € porque la ficha es corta y "puntúa" alto. La base sí tiene el mismo
artículo: `P23FJ020`, *Extintor polvo ABC 6 kg 34A/233B*, 34,08 €. Se fija la ficha a mano
y el recurso pasa a divergencia honesta (−45,9 %): el precio propio de 63 € incluye soporte
y señalización que la ficha no acredita.

### 2.4 La tornillería: dos palabras para el mismo artículo

`MT-TORNILLO-EST` no podía ver `P01UT040` («Tornillo 6,8 cincado + arandela + tuerca
autoblocante») porque el recurso empieza por *tornillería* y el cribado exigía el token
literal del núcleo. Con el colapso de variantes (`tornillería/tornillo`,
`hormigón/concreto`, `motosierra/sierra`, `perno/anclaje`…) el cribado pasa de 339 a **346
recursos con candidato** y de 72 a **79 con precisión ≥ 0,75 y números compatibles**.

## 3. Cambios de método (todos con prueba)

1. **La identidad manda sobre el precio** (`verificar_precios_espana.py`). Antes, entre
   varias observaciones dentro del ±15 %, se elegía la de precio más cercano: así un bloque
   de 25 cm «confirmaba» un recurso de 20 cm y un extintor de 50 kg, uno de 6 kg. Ahora se
   elige por `f1` (media armónica de precisión y cobertura), que es lo que ordena el
   parecido real del artículo.
2. **Ficha forzada** (`espana_revision_manual_*.csv`, columna `codigo_elegido`). Cuando el
   banco tiene el artículo exacto, se nombra el código y el verificador solo compara con
   esa ficha. Es el contrato explícito de «es el mismo artículo».
3. **Sinónimos en el cribado** (`--sinonimos`): mapa corto y revisable de familias
   (`torNILLO`, `ANCLAJE`, `HORMIGON`, `TALADRO`, `MARTILLO`, `SIERRA`…). No se usa para
   confirmar automáticamente: genera una tabla de revisión
   (`espana_equivalencias_extremadura_2026-11-07.csv`).
4. **El cierre ya es idempotente**: reaplicar la adjudicación borraba las confirmaciones ya
   escritas (`limpiar_marca` llegaba hasta el final del texto) y podía degradar un recurso
   confirmado a `en_revision`. Ambas cosas están corregidas y probadas.

## 4. Estado tras el lote

| Métrica | Antes | Ahora |
|---|---|---|
| `confirmado_referencia` | 32 | **37** |
| `en_revision` | 356 | **351** |
| Con precio revisado | 220 | **224** |
| Veredictos | 168/125/56/32/7 | **164 / 126 / 54 / 37 / 7** |
| Confirmaciones aplicadas | 14 | **19** |

Nuevas confirmaciones: `MT-BLQ-20` (P01BG200), `MT-CONC-180` (P01HCM003), `MT-CONC-210` y
`MT-CONC-250` (P01HCA300), `MT-CONC-300` (P01HCA320) — 181 usos.

## 5. Los 164 huecos, clasificados

`docs/auditoria_precios/espana_identidad_huecos_2026-11-07.csv` (reproducible con
`tools/auditar_huecos_identidad_espana.py`):

| Diagnóstico | Recursos | Usos | Qué significa |
|---|---|---|---|
| `misma_familia_sin_medida` | 62 | 2.479 | El banco tiene la familia; falta fijar medida, clase o acabado. |
| `agregado_por_componentes` | 19 | 968 | Cesta de consumibles: hay que desglosarla antes de cotizar. |
| `solo_parecido_de_nombre` | 64 | 795 | Comparte palabras con otro producto: no se puede confirmar. |
| `sin_candidato` | 19 | 615 | El artículo no está en la base. |

Los casos de más uso y su lectura: `MQ-TALADRO` (1.025 usos) — la base tiene taladro
eléctrico 750 W a 0,84/0,91 €/h, pero el recurso incluye percutor, brocas y consumo: la
diferencia de alcance es de 2,4× y no se puede cerrar sin cambiar la descripción;
`MT-CONS-DEM` (398) y `MQ-ATORN` (162) no existen como ficha; `MQ-ANDAMIO` (190) está en
€/m²·día.

## 6. Lo que sigue abierto, con nombre y apellidos

- **Desglosar 19 recursos agregados** (968 usos) en componentes simples: es trabajo de
  catálogo, no de búsqueda de precios.
- **Fijar especificación en 62 recursos** (2.479 usos): medida, clase o acabado; sin eso
  cualquier precio sería inventado.
- **`MQ-TALADRO`, `MQ-MART-ELEC`, `MQ-SOLDADORA`, `MQ-MEZCL`**: el banco cotiza la máquina,
  el recurso cotiza máquina + consumibles + amortización. Decidir si se modela por coste
  horario propio (recomendado) o se cambia el alcance del recurso.
- **Concreto**: la ficha es de central; transporte y bombeo siguen `no_confirmado` y hay que
  cuantificarlos por obra.
- La base de Extremadura es 2026 pero **regional (EX)**: confirma la banda de precio, no un
  precio nacional ni una oferta de proveedor.

## 7. Reproducir

```bash
# cribado con sinónimos (tabla de revisión, no confirma nada)
python tools/cribar_precios_espana.py --bc3 bases_precios/BCEXTGREM_26_v1.bc3 \
    --banco extremadura --edicion 2026 --limite 5 --sinonimos \
    --salida docs/auditoria_precios/espana_equivalencias_extremadura_2026-11-07.csv

# clasificación de los huecos
python tools/auditar_huecos_identidad_espana.py

# verificación y confirmaciones (no escriben precios)
python tools/verificar_precios_espana.py --aplicar
python tools/confirmar_precios_espana.py --aplicar
```
