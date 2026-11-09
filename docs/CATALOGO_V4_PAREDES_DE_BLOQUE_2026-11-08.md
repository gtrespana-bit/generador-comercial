# Despliegue del catálogo v4: paredes de bloque de 17 y 25 cm — 8 de noviembre de 2026

**Resultado: las dos partidas dejan de estar «en el repositorio pero en ninguna
organización».** El problema no era de datos ni de despliegue: era una condición de
versión que nunca se cumplía. Se corrige con la versión de alta explícita en cada
descompuesto y una subida del catálogo a la versión 4.

## 1. El síntoma

`06.03.01.160` (pared de bloque de 17 cm) y `06.03.01.170` (pared de bloque de 25 cm)
estaban en `basedatos_partidas/datos/descompuestos/` desde hacía semanas, con sus
precios y sus seis recursos cada una. El catálogo que se construye las incluye
(3.008 partidas), pero **ninguna organización las recibía**.

En producción, antes del cambio:

| Dato | Valor |
|---|---|
| Partidas con `codigo_clasificacion = '06.03.01'` y estas dos altas | 2 |
| Organizaciones que las tienen | 1 (la 75, `id` 169061 y 169062) |
| `version_alta_catalogo` en esas filas | 2 |
| Organizaciones activas en el catálogo | 61 |
| Referencias ES en `precios_recursos_mercado` | 390 |

Es decir: una sola organización las veía, y por una siembra antigua, no por el alta.

## 2. La causa

`actualizar_taxonomia_catalogo_propio()` incorpora una partida nueva solo si se
cumplen las dos condiciones:

```python
version_previa >= 2 and version_alta > version_previa
```

`version_alta` se calculaba así:

```python
version_alta = int(item.get("version_alta_catalogo")
                   or (2 if codigo_legacy else CATALOGO_VERSION))
```

Las dos partidas tienen `codigo_legacy` (`CT-06-01-160` y `CT-06-01-170`, la retícula
antigua del catálogo). Sin `version_alta_catalogo` en el JSON, la expresión caía al
`2` del `codigo_legacy` y **nunca** superaba el `version_previa = 3` que tienen las
organizaciones. Se actualizaban las que ya existían y la condición de alta no se
cumplía nunca.

De ahí la conclusión que importa: **subir solo `CATALOGO_VERSION` no habría
desplegado nada.** La partida habría seguido cayendo al `2` por tener código legado.
El arreglo necesita las dos piezas.

## 3. El arreglo

1. **`version_alta_catalogo: 4`** explícito en `06.03.01.160.json` y `06.03.01.170.json`.
   Con el campo presente, `version_alta` vale 4 y la condición `4 > 3` se cumple.
2. **`CATALOGO_VERSION = 4`** en `app/services/catalogo_propio.py`, con el comentario
   de qué trae la v4. Sin esto, `asegurar_catalogo_propio()` corta antes de llegar:
   si la organización ya está en la versión vigente no construye el catálogo.
3. **Dos pruebas nuevas** en `tests/test_catalogo_propio.py` que fijan el contrato:
   las dos partidas existen en el catálogo construido y la actualización incremental
   las incorpora para una organización que venía de la versión anterior. La prueba
   incremental ya no usa un número fijo, sino `servicio.CATALOGO_VERSION + 1`, para
   que la siguiente subida de versión no la deje mintiendo.

## 4. Cómo llega a las organizaciones

No hay tarea de migración ni endpoint de administración: el catálogo se sincroniza
**de forma perezosa** la primera vez que alguien de la organización abre el catálogo
de partidas, el de recursos o el diálogo de presupuesto nuevo
(`asegurar_catalogo_propio()` en `partidas.py`, `recursos.py` y `presupuestos.py`).
La configuración de cada organización está en `version_catalogo = 3`, así que el
próximo acceso de cada una ejecuta la actualización y, como `version_alta = 4 > 3`,
inserta las dos partidas.

Consecuencia práctica que conviene tener escrita: **el despliegue del código no
puebla las 61 organizaciones de golpe**. Se pueblan al usarse. La comprobación de
que ha ido bien es esta, y debe dar 122 filas (61 organizaciones × 2 partidas) cuando
todas hayan entrado al menos una vez:

```sql
SELECT codigo_legacy, count(*) AS organizaciones, count(DISTINCT organizacion_id) AS orgs
  FROM public.partidas
 WHERE codigo_legacy IN ('CT-06-01-160', 'CT-06-01-170')
 GROUP BY codigo_legacy;
```

Mientras tanto, la organización 75 seguirá siendo la única con las dos filas; sus
`id` no cambian (se actualizan por `catalogo_uid`), así que las líneas de presupuesto
que ya las usan no se rompen.

## 5. Precio de las dos partidas

Base **USD** (el catálogo propio es USD y se convierte a la moneda del presupuesto en
la vista). Los dos materiales de bloque se actualizaron en producción el mismo día:

| Recurso | Precio | Antes |
|---|---|---|
| `MT-BLQ-17` | 0,70 | 0,62 |
| `MT-BLQ-25` | 0,86 | 0,70 |

Con esos precios, el desglose que calcula `construir_catalogo()` es:

| Partida | Materiales | Mano de obra | Complementarios | Otros | Coste directo | Margen 35 % | **Precio** |
|---|---|---|---|---|---|---|---|
| `06.03.01.160` — 17 cm | 10,99 | 5,58 | 0,17 | 0,30 | 17,04 | 5,96 | **23,00 /m²** |
| `06.03.01.170` — 25 cm | 13,62 | 6,30 | 0,20 | 0,38 | 20,50 | 7,18 | **27,68 /m²** |

Composición, idéntica salvo espesor y rendimientos:

* `MT-BLQ-17` / `MT-BLQ-25` — 12,6 ud/m² (bloque de 17×20×40 y 25×20×40).
* `MT-MOR-PEGA` — 0,014 y 0,020 m³/m² de mortero de pega.
* `MT-ANCLA-MURO` — 1,2 ud/m² de amarre a la estructura.
* `MQ-MEZCL` — 0,082 y 0,105 h/m² de amasadora.
* `MO-OF1-ALB` — 0,62 y 0,70 h/m² de oficial de primera albañil.
* `MO-AYU` — 0,62 y 0,70 h/m² de ayudante.

1 % de costes complementarios y 35 % de margen, como el resto del capítulo 06.

## 6. Estado de la verificación

* Catálogo construido: **3.008 partidas**, 542 con código legado `CT-`, 18 capítulos,
  172 subcapítulos, 256 apartados. `CATALOGO_VERSION = 4`.
* Las dos partidas se construyen con `version_alta_catalogo = 4`.
* Pruebas dirigidas del catálogo: 23 de 23 en verde, incluidas las dos nuevas.
* **Suite completa: 3.658 superadas, 13 omitidas, 0 fallidas** (256 s con `-n auto`).
  Antes de este PR eran 3.649: +2 del catálogo y +7 del registro de cotizaciones.
* En producción las dos filas siguen en la organización 75 hasta que cada
  organización vuelva a abrir su catálogo; el código que las propaga se despliega
  con este PR.
