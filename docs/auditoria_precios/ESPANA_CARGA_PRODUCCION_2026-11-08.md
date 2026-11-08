# Carga en producción de las referencias nacionales de España — 8 de noviembre de 2026

**Resultado: 390 referencias nacionales ES activas en `public.precios_recursos_mercado`,
todas selladas con fecha de revisión 2026-11-07, sin tocar precios propios de
organizaciones ni referencias de otros países.** Es el último punto abierto del PR #213
(`arena/9350282b-generador-comercial`), que dejó la matriz auditada y el SQL generado
pero no ejecutado.

## 1. Destino y punto de partida

| Dato | Valor |
|---|---|
| Proyecto Supabase | `CotizaT-Generador` (`ivsuiyfljcajrijgwisg`, ca-central-1, Postgres 17) |
| Tabla | `public.precios_recursos_mercado` |
| Referencias ES nacionales antes | 388 (`organizacion_id IS NULL`, `pais_codigo = 'ES'`, `activo`) |
| Texto genérico de partida | 315 filas con `Precio referencial nacional derivado de la canasta…` |
| Texto auditado de partida | 73 filas, todas con `fecha_consulta = 2026-10-20` |
| Overrides de empresa | 14 (intactos) |
| Referencias de otros países | 8.148 (intactas) |

Las 390 filas de la matriz superan en 2 a las 388 cargadas: `MT-BLQ-17` y `MT-BLQ-25`,
que no existían como recurso en ninguna organización. Decisión del titular: **cargar las
390** creando esos dos recursos con precio propio 0 en las organizaciones que ya tienen la
familia de bloque.

## 2. Creación de los dos recursos que faltaban

`MT-BLQ-17` y `MT-BLQ-25` se han creado en las **56 organizaciones** que ya tenían
`MT-BLQ-15` (112 filas), heredando unidad, categoría, grupo y moneda de su hermana
`MT-BLQ-15` y con **precio propio 0**: no hay partida desplegada que los use todavía, así
que el precio propio se rellenará cuando se cotice; la referencia nacional ES ya les da
cifra y fuente.

| Código | Descripción | Unidad | Categoría | Precio propio | Organizaciones |
|---|---|---|---|---|---:|
| `MT-BLQ-17` | Bloque de concreto hueco de 17x20x40 cm. | ud | materiales | 0 | 56 |
| `MT-BLQ-25` | Bloque de concreto hueco de 25x20x40 cm. | ud | materiales | 0 | 56 |

`public.recursos` no tiene restricción de unicidad por `codigo` (es multi-tenant), así que
la inserción se hizo con `NOT EXISTS` por `(organizacion_id, codigo)`: no se ha duplicado
ninguna fila preexistente.

## 3. Traspaso verificado a una tabla de paso

En lugar de ejecutar el script monolítico de 171 KB o un `DELETE`+`INSERT` de 390 filas de
golpe, la matriz se cargó primero en `backup.stage_es_20261108` (11 columnas del CSV,
`codigo_recurso` como clave primaria, `NOT NULL` en todas) y se comparó contra el CSV
auditado antes de tocar producción:

| Comprobación | CSV local | En `backup.stage_es_20261108` |
|---|---|---|
| Filas | 390 | 390 |
| md5 de códigos ordenados | `f3daa656f03053d4f76ba5dbd29a57b6` | idéntico |
| md5 de observaciones ordenadas | `4e7673dc7791c670d206460f0e2f2672` | idéntico |
| md5 de fuentes ordenadas | `8f5cc43e70e6a9caba3e2debd4253307` | idéntico |
| Suma de precio | 12.563,3766 | 12.563,3766 |
| Suma de precio mínimo | 12.337,7890 | 12.337,7890 |
| Suma de precio máximo | 12.829,8310 | 12.829,8310 |

Coincidencia exacta en los tres md5 y en las tres sumas: el stage no perdió ni corrompió
ningún carácter de fuente, observación o precio. El preflight también confirmó que
`es_actuales_fuera_de_stage = 0`, es decir, ninguna de las 388 referencias vigentes quedaba
fuera de la matriz nueva.

## 4. Sustitución y fecha del panel

El reemplazo se hizo por código (`DELETE` de las 388 filas ES nacionales y `INSERT` de las
390) apoyándose en un mapa precalculado `backup.mapa_es_20261108` (390 códigos → `min(id)`
en `public.recursos`). Se escribieron `moneda = 'EUR'`, `proveedor = ''`,
`fecha_vigencia = NULL`, `activo = true`, `fecha_actualizacion = CURRENT_TIMESTAMP` y

- `fecha_consulta = 2026-11-07` en las 390: es el equivalente exacto del botón
  **«Confirmar hoy»** del panel (`POST /admin/matriz-precios/confirmar-revision`), que hace
  `fecha_consulta = CURRENT_DATE` sobre las referencias nacionales activas. Se ha sellado a
  la fecha de revisión del cierre, no a la fecha interna de cada fuente.
- La fecha de procedencia de cada fuente (307 filas 2026-11-07, 55 a 2026-08-25, 28 a
  2026-11-06) se conserva en `basedatos_partidas/salida/precios_recursos_espana.csv` y en
  cada informe de lote, pero no en la base: la tabla guarda una sola fecha de revisión por
  referencia, que es la que lee el panel.

Con la fecha de hoy (8 de noviembre) y los umbrales de `app/services/vigencia_precios.py`
—`DIAS_POR_REVISAR = 180`, `DIAS_OBSOLETA = 365`—, el panel muestra **390 vigentes, 0 por
revisar, 0 obsoletas, 0 caducadas, 0 sin fecha** para España.

## 5. Verificación posterior

| Comprobación | Resultado |
|---|---|
| Referencias ES nacionales activas | **390** |
| Con `fecha_consulta = 2026-11-07` | **390** |
| Filas que difieren del stage en precio, mín/máx, unidad, fuente, confianza, IVA, transporte u observaciones | **0** |
| md5 de observaciones en base vs CSV | idéntico (`4e7673dc…`) |
| Suma de precios en base | 12.563,3766 (idéntica al CSV) |
| Códigos duplicados en ES | 0 |
| Filas ES con un `recurso_id` ajeno al mapa | 0 |
| Filas cuyo `recursos.codigo` no coincide con su `codigo_recurso` | 0 |
| Overrides de empresa | 14 (sin cambios) |
| Referencias de otros países | 8.148 (sin cambios) |
| Moneda | EUR en las 390 |
| Confianza | 350 `derivado`, 40 `referencia` |

## 6. Incidencia y causa

La primera tentativa (guarda + `DELETE` + `INSERT` en una sola llamada) **no llegó a
aplicarse**: el cliente de la API cortó a los 30 s y, al inspeccionar `pg_stat_activity`,
la sentencia seguía viva reteniendo el bloqueo, con el `DELETE` posterior esperando por
`transactionid`. Se cancelaron los dos backends y se verificó que la base seguía en 388
filas con fecha 2026-10-20 y el stage en 390: **ningún cambio parcial**.

Causa: `public.recursos` **no tiene índice sobre `codigo`** (solo `pkey(id)` y
`ix_recursos_organizacion_id`). El `NOT EXISTS (SELECT 1 FROM public.recursos WHERE
r.codigo = s.codigo_recurso)` y el `recurso_id IN (SELECT r.id … WHERE r.codigo = …)` del
script barrían las ~21.800 filas de recursos una vez por cada código de la matriz. La
solución aplicada —y ya incorporada al script— es resolver el mapa código → `id` con un
único recorrido agrupado y eliminar/insertar por `codigo_recurso`, que sí está indexado.

**Recomendación abierta (no aplicada):** crear `ix_recursos_codigo` sobre
`public.recursos(codigo)`. No es un cambio de datos, pero es un cambio de esquema: requiere
migración y revisión aparte. Mientras tanto, cualquier consulta por `codigo` sobre
`recursos` es un escaneo secuencial.

## 7. Reversión

Los tres artefactos siguen en la base, en el esquema `backup`:

| Tabla | Contenido |
|---|---|
| `backup.precios_es_20261108` | las 388 filas ES nacionales anteriores a la carga |
| `backup.stage_es_20261108` | las 390 filas exactas que se cargaron |
| `backup.mapa_es_20261108` | correspondencia `codigo` → `recurso_id` usada en la carga |

Para volver al estado anterior, en una transacción:

```sql
DELETE FROM public.precios_recursos_mercado
WHERE organizacion_id IS NULL AND pais_codigo = 'ES'
  AND codigo_recurso IN (SELECT codigo_recurso FROM backup.stage_es_20261108);

INSERT INTO public.precios_recursos_mercado
SELECT * FROM backup.precios_es_20261108;
```

Los dos recursos nuevos (`MT-BLQ-17`, `MT-BLQ-25`) no se deshacen con eso: si se revierte
la carga, hay que decidir si se eliminan las 112 filas de `public.recursos` o se dejan con
precio propio 0 (no las usa ninguna partida desplegada).

## 8. Suite de pruebas

Esta carga **no toca código**: solo documentación y el script SQL. Aun así se ha pasado la
suite completa tras el cambio:

| Medida | Resultado |
|---|---|
| Pruebas | 3643 superadas, 13 omitidas, **6 fallidas** (total 3662) |
| Mismo conjunto en un árbol limpio de `HEAD` (sin este cambio) | **los mismos 6 fallos** |
| CI de `main` en el commit `36e1813` | **en rojo** (`failure`, igual que el commit anterior) |

Los 6 fallos son previos y ajenos a esta carga:

- `test_inventario_precios_espana::test_inventario_integral_reproducible_y_estados_actuales`
  espera `374 confirmado_referencia / 16 en_revision`; el registro versionado ya tiene
  **390 confirmados** tras el cierre total.
- `test_confirmaciones_aplicadas_son_coherentes_con_el_registro` y
  `test_confirmaciones_aplicadas_incluyen_la_segunda_base` fijan **321** confirmaciones;
  `espana_confirmaciones_2026-11-07.csv` tiene **337**.
- Los tres restantes (`test_valida_estado_banda_y_duplicados`, `test_aplicar_es_idempotente`,
  `test_rechaza_decisiones_invalidas`) necesitan algún recurso `en_revision` y ya no queda
  ninguno: el cierre total confirmó los 390.

Causa común: el registro de auditoría se regeneró en el cierre total y las pruebas siguen
describiendo el estado anterior. **No se han retocado ni los datos ni las pruebas**: decidir
si el registro vuelve a distinguir `en_revision` o si las pruebas se actualizan a 390/337 es
una decisión de auditoría, no de esta carga. Queda anotado como pendiente aparte.

## 9. Lo que esta carga no dice

- **Cargar no es verificar.** 350 de las 390 referencias llevan `confianza = 'derivado'`:
  son bandas de cordura o analogías, no cotizaciones. La referencia da orden de magnitud y
  fuente trazable; no garantiza el precio de un proveedor ni de una obra concreta.
- Las 306 confirmaciones con BCCA 2023 / Extremadura 2026 dentro de ±15 % y las 16 con
  fuente propia son del registro de auditoría (`estado_auditoria`), no de esta tabla: aquí
  solo se guarda la cifra, la fuente documental y la confianza.
- `MT-BLQ-17` y `MT-BLQ-25` quedan con precio propio 0 hasta que se coticen; su referencia
  nacional sí está cargada.
