# Guía para reanudar la auditoría de precios de España

**Corte: 7 de noviembre de 2026, tras el octavo barrido.** Este documento es el punto de entrada para retomar el trabajo; el historial detallado está en [CONTINUIDAD.md](CONTINUIDAD.md). Las cifras son una fotografía: recalcularlas desde los archivos antes de continuar si ha habido cambios posteriores.

## Objetivo y situación

Se está auditando la matriz de precios de recursos para España, contrastando las descripciones, unidades y usos de las partidas con fuentes trazables. El propósito es mejorar las referencias de presupuesto sin presentar estimaciones o precios provinciales como precios universales. **La auditoría no está terminada.**

| Estado en el registro | Recursos | Con precio revisado | Sin precio revisado |
|---|---:|---:|---:|
| Confirmado como referencia | 13 | 13 | 0 |
| En revisión | 227 | 189 | 38 |
| Pendiente | 148 | 0 | 148 |
| **Total** | **388** | **202** | **186** |

Los 202 precios revisados comprenden 193 materiales y 9 recursos de mano de obra. De los 186 sin precio revisado, 162 aparecen en una o más partidas y 24 no tienen usos actuales. **Sin precio revisado no significa sin precio en la matriz**: esos recursos conservan una referencia previa que no se ha sustituido por una nueva cifra auditada.

### Qué significa «precio revisado»

El campo `precio_revisado` del registro contiene una cifra nueva documentada y trasladada a la matriz local. **No significa necesariamente que el precio sea definitivo, universal ni apropiado para una obra concreta.** Muchos son estimaciones provisionales: 189 de los 202 todavía están `en_revision`. `confirmado_referencia` significa que se ha aceptado la referencia bajo el método y las condiciones documentados, no que se garantice el coste de cualquier proveedor o proyecto. `estado_auditoria` es independiente de la confianza que figure en la matriz y del estado del catálogo base.

Ejemplos: `MT-CEMENTO`, 0,19 €/kg, es media de dos ofertas puntuales sin IVA ni porte, no media nacional; `MT-APEO`, 1,04 €/ud, es una hipótesis provisional de un apeo específico y tiene una alerta de posible solape de madera. Consultar siempre `criterio_revisado`, evidencias y fuente antes de interpretar o usar una cifra.

## Qué se ha realizado

- Inventario completo de los 388 recursos, cruce de candidatos de bancos de precios y varias rondas de contraste comercial y regional. Los candidatos por coincidencia de texto **no** se aplicaron automáticamente; los bancos regionales y ofertas puntuales no demuestran un promedio nacional.
- Se prepararon referencias revisadas y sus artefactos locales, con fuentes, supuestos y reservas en el registro y los informes por lote. La matriz, el índice público local de España y un SQL de carga fueron generados; **el SQL no se ha ejecutado y no se ha realizado despliegue**. No se ha validado el contenido actual de producción en esta auditoría.
- En los dos primeros barridos recientes de 30 recursos se aplicaron, respectivamente, 9 precios provisionales y 1 precio provisional. Los barridos tercero a octavo documentaron, respectivamente, **30, 30, 16, 14, 15 y 8 recursos**, sin aplicar nuevos precios. El octavo terminó los ocho recursos de un uso que no se mencionaban en los siete barridos recientes. No asumir que «no mencionado en esos barridos» signifique «nunca examinado» en todos los informes anteriores.
- Se documentaron alertas de unidades, descripción, especificación y posibles solapes sin modificar automáticamente los descompuestos. No se ha demostrado que cada posible solape sea una duplicidad o que toda ausencia de un componente en el catálogo sea una ausencia en obra.

## Alertas que siguen abiertas

1. **Unidades contradictorias:** `04.08.02.040` tiene `m2`, pero su descripción indica metro lineal para micropilotes. `10.02.02.060` tiene `m2`, pero dice medición por unidad instalada para soportes antivibratorios. Comprobar unidad, alcance y rendimientos antes de corregir o presupuestar.
2. **Seguridad y adecuación:** revisar equipo y método para micropilotes; proyecto, soporte y anclajes de líneas de vida; tipo de sistema y dosis de pintura intumescente; señalización y tubería de la BIE `09.10.01.030`; prestaciones de alarma de baño accesible `13.06.01.100`; iluminación de emergencia `17.03.01.080`. La documentación actual no demuestra por sí sola incumplimiento ni seguridad real.
3. **Posibles solapes, no probados:** `MT-APEO`/`MT-VIGA-APEO` en 23 partidas; componentes de anclaje de líneas de vida y fachada ventilada; tira LED que también figura como `producto_cliente`; cama de arena de adoquín; aspiración de lijadora; clavos de teja asfáltica; armadura en bloque de vidrio; transporte de material de préstamo y protecciones de cuadro de obra. Determinar qué incluye cada recurso antes de cambiar precios o partidas.
4. **Otros alcances:** posible divergencia entre poliuretano cementoso y el recurso genérico bicomponente; cortina térmica y reposición de papel sin recurso textil/papel ni `producto_cliente` identificado; capacidad y conexiones del separador de grasas; vidrio decorativo sin sistema de fijación definido. Cada informe detalla los códigos y las reservas.

## Cómo continuar

1. Leer [CONTINUIDAD.md](CONTINUIDAD.md), el [octavo barrido](ESPANA_OCTAVO_BARRIDO_PARCIAL_2026-11-07.md) y los informes de alertas pertinentes. Verificar con el usuario si desea continuar la auditoría o resolver una alerta concreta.
2. Si se continúa la auditoría general, priorizar los recursos **sin precio revisado y con más usos**, pero consultar sus evidencias previas antes de repetir búsquedas. Entre los de mayor propagación en este corte están `MQ-TALADRO` (1.025), `MO-OF1-ELE` (405), `MT-CONS-DEM` (398), `MO-OF1-PLO` (218), `MQ-SIERRA` (199) y `MQ-ANDAMIO` (190). Los usos se solapan entre recursos y no equivalen a frecuencia comercial ni impacto económico.
3. Solicitar o buscar especificaciones y fuentes comparables que permitan resolver los bloqueos: unidad, prestaciones, alcance, zona, fecha, IVA, transporte, consumos y vida útil según corresponda. **No aplicar un precio solo por encontrar un número** ni dar por equivalente una partida instalada y un material, un alquiler diario y un coste horario, o una compra y su amortización.
4. De los recursos sin precio revisado, 23 de uso cero no se mencionaban en los ocho barridos recientes; no son necesariamente inéditos en los demás informes. Antes de priorizarlos, valorar si tienen utilidad actual en el catálogo y consultar al usuario si procede.
5. Al adoptar una cifra, documentar fuente, normalización, supuestos y reservas; actualizar de forma reproducible registro, generador y artefactos pertinentes, añadir pruebas y comprobar el impacto en partidas. Mantener el estado `en_revision` cuando falte validación. No sobrescribir precios propios de clientes ni ejecutar SQL o desplegar sin una decisión controlada.

## Archivos principales

- [Registro maestro](espana_2026-11-06.csv): estados, `precio_revisado`, fuentes, evidencias y criterios. `precio_matriz` en este registro conserva el importe de la fotografía inicial; no debe confundirse necesariamente con el importe actual.
- [Inventario integral actual](espana_inventario_integral_2026-11-07.csv): precios de la matriz local, usos, estados y candidatos. [Metodología y límites](ESPANA_INVENTARIO_INTEGRAL_2026-11-07.md).
- [Continuidad y enlaces a todos los lotes](CONTINUIDAD.md); los valores de sus secciones antiguas son cortes históricos. En particular, el bloqueo antiguo de la suite por `tinycss2` quedó superado en el último corte.
- [Octavo barrido](ESPANA_OCTAVO_BARRIDO_PARCIAL_2026-11-07.md) y [decisiones CSV](espana_decisiones_octavo_barrido_parcial_2026-11-07.csv); los barridos anteriores tienen informes y CSV equivalentes.
- `basedatos_partidas/datos/descompuestos/*.json`: descripciones, unidades y rendimientos reales de las partidas.
- `basedatos_partidas/salida/precios_recursos_espana.csv`: matriz local actual. `basedatos_partidas/datos/precios_publicos/ES.json`: índice público local. `tools/generar_matriz_precios_espana.py` y `tools/inventario_precios_espana.py`: generadores. `docs/cargar_precios_referencia_espana_2026-11-06.sql`: SQL generado, **no ejecutado**.

## Comprobaciones y precauciones al retomar

- Última suite completa: **3.581 aprobadas y 13 omitidas**, ejecutada antes de que se crease `tests/test_octavo_barrido_parcial_espana.py`. Sus dos pruebas se ejecutaron después dentro de las **72 pruebas focalizadas aprobadas**. Último `git diff --check`: limpio. Las omitidas no se consideran aprobadas. `tinycss2==1.5.1` y `pytest-xdist==3.8.0`, ya declarados en las dependencias de desarrollo, se instalaron en el entorno local para ejecutar la suite; si el entorno se recrea puede ser necesario reinstalar dependencias.
- Para repetir la suite completa, incluida la prueba nueva: `.venv/bin/python -m pytest -q -n 4`. Para verificar espacios y conflictos de formato: `git diff --check`. No inferir precisión de mercado de una prueba de importabilidad o de un test automatizado.
- El trabajo está en la rama de sesión `arena/15e1703f-generador-comercial`, con cambios locales sin commit al cierre de este documento. **No se hizo commit, push, carga de SQL ni despliegue** al documentar. Consultar `git status` antes de trabajar; no descartar cambios existentes.
- Los generadores de matriz e inventario **ejecutan regeneración incluso con `--help`**; no usar esa opción solo para inspeccionarlos. No volver a ejecutar scripts de `/tmp` de lotes ya aplicados: pueden repetir evidencias o cambios. Consultar el código fuente y los informes antes de regenerar.
- Las fuentes y ofertas se consultaron en las fechas indicadas y pueden cambiar. El BC3 íntegro de Extremadura y el ZIP de Madrid no se obtuvieron en esta sesión; una fuente identificada con licencia no comercial no debe incorporarse como base comercial sin autorización.
