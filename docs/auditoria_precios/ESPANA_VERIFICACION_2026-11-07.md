# Verificación cruzada de precios de España

**Corte: 7 de noviembre de 2026.** Segundo paso del cierre: comprobar, precio a precio, si la cifra tiene detrás una evidencia **independiente** del documento que la originó. Solo eso permite hablar de precio confirmado.

## 1. Resultado

| Veredicto | Recursos | Usos | Qué significa |
|---|---:|---:|---|
| `ya_confirmado` | 25 | — | Confirmados con la regla del ±15 % (18 del cierre + 7 de esta verificación) |
| `confirmado_independiente` | 0 | — | Nuevos candidatos pendientes de aplicar (ninguno: el lote de esta fecha ya está aplicado) |
| `contraste_comercial` | 8 | — | Dos comercios coinciden, pero no hay referencia oficial detrás |
| `divergencia_verificada` | 26 | — | Hay observación independiente y no coincide: la diferencia está documentada |
| `solo_fuente_propia` | 161 | — | El precio descansa en una única fuente y no se ha podido contrastar |
| `sin_precio_revisado` | 168 | — | No hay precio auditado: la matriz conserva la referencia histórica |
| **Total** | **388** | | |

Estado del registro tras la verificación: **25 `confirmado_referencia` / 363 `en_revision`**, 220 con precio revisado, 0 pendientes de decisión.

## 2. Reglas aplicadas (publicadas para que se puedan discutir)

1. Una observación es **independiente** si pertenece a otra familia documental que la que ya sostiene el precio: banco andaluz (BCCA), Diputación de Palencia, Junta de Extremadura, BOE/modelo propio de coste empresarial, o un comercio distinto.
2. Si el documento que originó el precio ya es de esa familia, la observación **no confirma nada**: no se puede circular con la misma fuente. Esto descarta, por ejemplo, confirmar los ocho oficios de 23,18 €/h con la propia tabla BCCA que ya se usó para fijarlos.
3. Solo se compara con **unidad compatible**; una observación en otra unidad se descarta y queda anotado el motivo.
4. Banda de confirmación: **±15 %**. Dentro de la banda y con fuente oficial → confirmado; dentro de la banda y solo con comercios → `contraste_comercial`; fuera de la banda → `divergencia_verificada`.
5. Los **comercios no confirman**: dos tiendas son un contraste útil, no una referencia de coste. Por eso `MT-CINTA-ENM` (1,83 €, dos ferreterías idénticas) no se eleva a confirmado.

## 3. Las 7 confirmaciones nuevas (730 usos)

| Recurso | Precio | Fuente independiente | Código | Δ | Usos |
|---|---:|---|---|---:|---:|
| `MO-OF1-MON` | 23,18 €/h | BCCA oficial de mano de obra | `TO02100` | −0,04 % | 319 |
| `MO-OF1-CARPM` | 23,18 €/h | BCCA `TO02100` | `TO02100` | −0,04 % | 209 |
| `MO-OF1-PISO` | 23,18 €/h | BCCA `TO02100` | `TO02100` | −0,04 % | 63 |
| `MO-OF1-ALI` | 23,18 €/h | BCCA `TO02100` | `TO02100` | −0,04 % | 53 |
| `MO-OF1-CAB` | 23,18 €/h | BCCA `TO02100` | `TO02100` | −0,04 % | 48 |
| `MT-AGUA-OBRA` | 0,84 €/m3 | Junta de Extremadura 2026 | `P01DW010` | +8,3 % | 27 |
| `MT-AISL-TERM` | 8,15 €/m2 | BCCA panel de lana mineral 25 mm | `XT80000` | −11,4 % | 11 |

Los cinco oficios venían de un **modelo de coste empresarial propio** construido con tablas provinciales y cuotas del BOE; la tabla oficial del banco coincide con su resultado en 1 céntimo por hora, que es exactamente el criterio con el que se confirmaron los otros cinco oficios en el cierre. Antes estaban clasificados como «mantener sin cambio» pese a cumplir la misma regla: era una inconsistencia del cierre anterior y queda corregida.

`MT-AGUA-OBRA` se fijó con el banco de Palencia (0,77 €/m3) y ahora lo respalda Extremadura (0,91 €/m3). `MT-AISL-TERM` se fijó con Extremadura y ahora lo respalda el banco andaluz.

## 4. Las 26 divergencias: qué dicen de verdad

No son 26 precios mal puestos. Son 26 casos en los que una fuente independiente da otro número, y la mayoría apunta a **productos distintos**, no a errores de precio:

| Recurso | Usos | Revisado | Independiente | Δ | Lectura |
|---|---:|---:|---:|---:|---|
| `MT-PYL-PASTA` | 99 | 1,01 | 2,14 | +111,9 % | El banco separa pasta y cinta; el recurso las agrupa |
| `MT-CLAVOS` | 94 | 3,21 | 4,05 | +26,2 % | Paquete de 2,5 kg frente a unidad de venta distinta |
| `MT-APEO` | 54 | 1,04 | 21,87 | +2002,9 % | El banco cotiza puntal metálico; el recurso es madera de apeo |
| `MT-BANDA-REF` | 46 | 3,01 | 0,12 | −96,0 % | Banda elástica de 10 mm frente a banda de refuerzo de obra |
| `MT-MORT-IMPER` | 39 | 1,75 | 0,42 | −76,0 % | Mortero impermeabilizante rígido frente a bicomponente flexible |
| `MT-REJILLA-VENT` | 39 | 9,19 | 4,68 | −49,1 % | Tamaño y acabado distintos |
| `MT-VALV-CHECK` | 38 | 17,22 | 9,33 | −45,8 % | Diámetro y material sin fijar en el recurso |

Ninguna de estas divergencias se ha corregido automáticamente: cambiar el precio sin fijar antes la especificación sería empeorar el dato.

## 5. Los 8 contrastes comerciales

Dos comercios distintos coinciden dentro del ±15 % en `MT-TORN-TECHO` (0,21 €), `MT-CINTA-ENM` (1,83 €), `MT-CRU-NIV` (0,19 €), `MT-EPOXI-ANCLA` (24,23 €), `MT-FLOTANTE` (8,16 €), `MT-PLO-PVC4` (10,36 €), `MT-TUB-FRIGO` (5,53 €) y `MT-CABLE-ALARMA` (0,62 €). Es evidencia razonable de que el precio es de mercado, pero **no** una referencia de coste: siguen `en_revision`.

## 6. La cola de trabajo: qué falta exactamente

`espana_pendientes_verificacion_2026-11-07.csv` tiene **363 recursos** con el dato concreto que falta en cada uno, ordenado por esfuerzo y usos:

| Esfuerzo | Recursos | Usos afectados | Qué falta |
|---|---:|---:|---|
| Alta | 44 | 3.215 | Maquinaria: precio de adquisición, vida útil y horas/año para un modelo de coste horario, o alquiler 2026 comparable |
| Media | 287 | 7.451 | Una segunda fuente independiente (banco o proveedor distinto) con la especificación exacta |
| Baja | 32 | 0 | Recursos sin uso actual: se pueden dejar documentados sin coste de oportunidad |

Los diez primeros por uso: `MQ-TALADRO` (1.025), `MQ-SIERRA` (199), `MQ-ANDAMIO` (190), `MQ-ATORN` (162), `MQ-RODILLO` (151), `MQ-VIBRADOR` (135), `MQ-MEZCL` (120), `MQ-MART-ELEC` (110), `MQ-SOLDADORA` (105), `MQ-ASPIR` (91). Todos son maquinaria: no falta un número, falta el **método** (amortización, mantenimiento, energía y operador) o un alquiler con condiciones completas.

## 7. Por qué no se puede llegar al 100 % con lo que hay

Para confirmar un precio hacen falta **dos observaciones independientes**. Hoy hay una sola fuente completa disponible (el banco andaluz vía CERP) y, como mucho, una observación más por recurso repartida en los informes de los lotes. Con eso el techo es exactamente el que muestra la tabla del apartado 1.

Lo que desbloquearía el resto:

1. **Base de Precios de Construcción de Extremadura 2026 (formato BC3, texto plano).** Está publicada y es accesible: `https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/...`. Es la segunda base más útil porque incluye materiales, maquinaria y mano de obra con precios de 2026. **No se ha podido ingerir completa desde este entorno**: la red del sandbox solo permite GitHub y PyPI, y el archivo son ~20 MB servidos en 2.339 fragmentos por la herramienta de lectura de páginas. Con una descarga normal basta `tools/cruzar_precios_bc3.py`, que ya sabe leer BC3.
2. **Banco con licencia de uso** (Generador de Precios de CYPE, Presto, ITeC). Es la vía que resuelve de una vez la cobertura nacional y la vigencia 2026, y la única que permite decir «precio de mercado» con fundamento.
3. **Cotizaciones de proveedor** para los 287 recursos de esfuerzo medio, con la especificación que ya está descrita en el catálogo.
4. **Precios de adquisición de maquinaria** para construir el modelo horario de los 44 recursos de esfuerzo alto.

## 8. Reproducibilidad

```bash
python3 tools/verificar_precios_espana.py            # matriz de verificación + cola de trabajo
python3 tools/verificar_precios_espana.py --aplicar  # + lote de confirmaciones
python3 tools/confirmar_precios_espana.py            # valida sin escribir
python3 tools/confirmar_precios_espana.py --aplicar  # eleva a confirmado_referencia
python3 tools/inventario_precios_espana.py           # inventario actualizado
python3 tools/generar_matriz_precios_espana.py && python3 tools/generar_sql_precios_espana.py
```

Artefactos: `espana_verificacion_2026-11-07.csv` (388 filas, una por recurso, con familias, observación independiente y veredicto), `espana_confirmaciones_2026-11-07.csv` (7 confirmaciones aplicadas), `espana_pendientes_verificacion_2026-11-07.csv` (363 recursos con lo que falta).

Pruebas: `tests/test_verificar_precios_espana.py` (7 pruebas: familias documentales, regla de no circularidad, completitud de la matriz, coherencia de la cola, y validación/idempotencia del aplicador).

## 9. Conclusión honesta

- **25 precios están confirmados con evidencia independiente.** Son los de mayor uso del catálogo: los 13 oficios de oficial y ayudante (`MO-AYU` 2.922 usos, `MO-OF1-ALB` 881, `MO-OF1-ELE` 405, `MO-OF1-MON` 319…), más materiales concretos.
- **220 precios son operativos y trazables**, pero 161 descansan en una única fuente.
- **168 recursos no tienen precio auditado** y 44 de ellos son maquinaria de alto uso que necesita un modelo, no una búsqueda.
- Ningún recurso está sin decisión: la diferencia entre «auditado» y «confirmado» está escrita recurso a recurso, con la fuente y el motivo.
