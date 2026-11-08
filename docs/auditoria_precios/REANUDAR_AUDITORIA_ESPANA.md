# Guía para reanudar la auditoría de precios de España

**Corte: 7 de noviembre de 2026, tras el cierre total: los 388 recursos tienen precio.** Este documento es el punto de entrada para retomar el trabajo; el historial detallado está en [CONTINUIDAD.md](CONTINUIDAD.md). Las cifras son una fotografía: recalcularlas desde los archivos antes de continuar si ha habido cambios posteriores.

## Objetivo y situación

Se está auditando la matriz de precios de recursos para España, contrastando las descripciones, unidades y usos de las partidas con fuentes trazables. El propósito es mejorar las referencias de presupuesto sin presentar estimaciones o precios provinciales como precios universales. **La auditoría no está terminada.**

| Estado en el registro | Recursos | Con precio revisado | Sin precio revisado |
|---|---:|---:|---:|
| Confirmado como referencia | 52 | 52 | 0 |
| En revisión | 336 | 336 | 0 |
| Pendiente | 0 | 0 | 0 |
| **Total** | **388** | **388** | **0** |

**Ningún recurso queda sin precio ni pendiente de decisión:** los 388 tienen cifra, fuente, código, criterio y reserva. Los 133 que estaban abiertos se cerraron el 7 de noviembre con un método declarado por recurso; ver [cierre total](ESPANA_CIERRE_TOTAL_2026-11-07.md). Estado de verificación en [ESPANIA_BANCOS_PRECIOS_2026-11-07.md](ESPANIA_BANCOS_PRECIOS_2026-11-07.md): 52 confirmados, 6 contrastes comerciales, 66 divergencias y 263 de fuente única (1 más confirmado independientemente); **ningún recurso sin precio auditado**. Ambos bancos están ingestados y cribados: BCCA 2023 con 5.925 precios simples leídos por `tools/leer_bcca.py` y Extremadura 2026 con su esquema nativo. Los 133 huecos que hubo quedaron clasificados por causa en [la auditoría de identidad](ESPANA_IDENTIDAD_EXTREMADURA_2026-11-07.md), que se conserva como registro histórico. La base de Extremadura 2026 ya está ingerida (`bases_precios/`, no versionada). Los 388 precios revisados comprenden mano de obra, materiales, 25 fichas directas de banco, 28 analogías de familia, 12 composiciones, 13 máquinas con modelo propio, 2 alquileres y 54 contrastes de mercado. **Que un precio esté revisado no lo hace universal**: `en_revision` sigue significando que falta una segunda fuente independiente.

### Último cambio: cierre total, 133 recursos (7 de noviembre)

Los 133 recursos que quedaban sin precio ya lo tienen, con el método escrito al lado:
**ficha del banco 25, familia análoga 28, composición de consumibles 12, modelo de
maquinaria por compra y amortización 12, alquiler calibrado 2 y contraste de mercado 54**.
Regla aplicada: si el alcance de la ficha no es el del recurso, **no se sustituye el
precio**; 16 analogías que pasaban el filtro automático se descartaron al leer la ficha
completa. Impacto: 1.076 partidas, mediana +0,1 %, mínimo −77,8 %, máximo +36,9 %. Los 54
de contraste de mercado conservan el precio de la matriz dentro de una horquilla declarada
y son el primer objetivo de la próxima cotización; `MT-PLANTA-ELEC` queda marcado para
revisión por estar por debajo de su banda y no tener uso. Detalle completo en
[cierre total](ESPANA_CIERRE_TOTAL_2026-11-07.md).

### Cambio anterior: maquinaria por compra y amortización (7 de noviembre)

Los 18 recursos cerrados por **convención de medida** (621 usos) están documentados en [convenciones](ESPANA_CONVENCIONES_MEDIDA_2026-11-07.md): caja 100×100, tornillo de placa 3,5×25, tubo estructural rectangular, AISI 304, caja de registro, arena 0/5, celosía de aluminio… Los 38 restantes de esa tanda se cerraron después en el cierre total.

Los 13 recursos de maquinaria con precio propio se han modelado como **compra dividida por vida útil** (no alquiler), con energía a 0,20 €/kWh, mantenimiento del 10–15 % y consumibles incluidos. Bajan entre el 47 % y el 92 % y afectan a 1.511 partidas con mediana −0,5 %. Detalle, fuentes de cada precio de adquisición y sensibilidad: [decisión de maquinaria](ESPANA_MAQUINARIA_DECISION_2026-11-07.md). Los 19 agregados se han medido por su peso real en el coste directo y solo 7 pasan el corte de recompostura: [decisión de agregados](ESPANA_AGREGADOS_DECISION_2026-11-07.md).

### Qué significa «precio revisado»

El campo `precio_revisado` del registro contiene una cifra nueva documentada y trasladada a la matriz local. **No significa necesariamente que el precio sea definitivo, universal ni apropiado para una obra concreta.** Muchos son estimaciones provisionales: 218 de los 255 todavía están `en_revision`. `confirmado_referencia` significa que se ha aceptado la referencia bajo el método y las condiciones documentados, no que se garantice el coste de cualquier proveedor o proyecto. `estado_auditoria` es independiente de la confianza que figure en la matriz y del estado del catálogo base.

Ejemplos: `MT-CEMENTO`, 0,19 €/kg, es media de dos ofertas puntuales sin IVA ni porte, no media nacional; `MT-APEO`, 1,04 €/ud, es una hipótesis provisional de un apeo específico y tiene una alerta de posible solape de madera. Consultar siempre `criterio_revisado`, evidencias y fuente antes de interpretar o usar una cifra.

## Qué se ha realizado

- Inventario completo de los 388 recursos, cruce de candidatos de bancos de precios y varias rondas de contraste comercial y regional. Los candidatos por coincidencia de texto **no** se aplicaron automáticamente; los bancos regionales y ofertas puntuales no demuestran un promedio nacional.
- **Cierre total (7 de noviembre de 2026):** los 133 recursos sin precio se valoran con un método declarado por recurso y validación todo-o-nada; el registro pasa a **388/388 con precio revisado**. [Informe de cierre total](ESPANA_CIERRE_TOTAL_2026-11-07.md). El comando `tools/cerrar_huecos_espana.py` falla si falta una decisión, si sobra o si el método no está en la jerarquía.
- **Cierre del primer ciclo (7 de noviembre de 2026):** cribado completo de los 388 recursos contra un banco oficial (1.167 candidatos), adjudicación explícita de los 375 recursos no confirmados y **18 precios nuevos aplicados** con validación todo-o-nada. [Informe de cierre, método, tablas e impacto](ESPANA_CIERRE_2026-11-07.md). La cadena (`cribar` → `cerrar_auditoria_espana.py` → generadores) es reutilizable para el resto de países.
- Se prepararon referencias revisadas y sus artefactos locales, con fuentes, supuestos y reservas en el registro y los informes por lote. La matriz, el índice público local de España y un SQL de carga fueron generados; **el SQL no se ha ejecutado y no se ha realizado despliegue**. No se ha validado el contenido actual de producción en esta auditoría.
- En los dos primeros barridos recientes de 30 recursos se aplicaron, respectivamente, 9 precios provisionales y 1 precio provisional. Los barridos tercero a octavo documentaron, respectivamente, **30, 30, 16, 14, 15 y 8 recursos**, sin aplicar nuevos precios. El octavo terminó los ocho recursos de un uso que no se mencionaban en los siete barridos recientes. No asumir que «no mencionado en esos barridos» signifique «nunca examinado» en todos los informes anteriores.
- Se documentaron alertas de unidades, descripción, especificación y posibles solapes sin modificar automáticamente los descompuestos. No se ha demostrado que cada posible solape sea una duplicidad o que toda ausencia de un componente en el catálogo sea una ausencia en obra.

## Alertas que siguen abiertas

1. **Unidades contradictorias:** `04.08.02.040` tiene `m2`, pero su descripción indica metro lineal para micropilotes. `10.02.02.060` tiene `m2`, pero dice medición por unidad instalada para soportes antivibratorios. Comprobar unidad, alcance y rendimientos antes de corregir o presupuestar.
2. **Seguridad y adecuación:** revisar equipo y método para micropilotes; proyecto, soporte y anclajes de líneas de vida; tipo de sistema y dosis de pintura intumescente; señalización y tubería de la BIE `09.10.01.030`; prestaciones de alarma de baño accesible `13.06.01.100`; iluminación de emergencia `17.03.01.080`. La documentación actual no demuestra por sí sola incumplimiento ni seguridad real.
3. **Posibles solapes, no probados:** `MT-APEO`/`MT-VIGA-APEO` en 23 partidas; componentes de anclaje de líneas de vida y fachada ventilada; tira LED que también figura como `producto_cliente`; cama de arena de adoquín; aspiración de lijadora; clavos de teja asfáltica; armadura en bloque de vidrio; transporte de material de préstamo y protecciones de cuadro de obra. Determinar qué incluye cada recurso antes de cambiar precios o partidas.
4. **Otros alcances:** posible divergencia entre poliuretano cementoso y el recurso genérico bicomponente; cortina térmica y reposición de papel sin recurso textil/papel ni `producto_cliente` identificado; capacidad y conexiones del separador de grasas; vidrio decorativo sin sistema de fijación definido. Cada informe detalla los códigos y las reservas.

## Cómo continuar

1. Leer [el informe de cierre](ESPANA_CIERRE_2026-11-07.md) y [CONTINUIDAD.md](CONTINUIDAD.md). El primer ciclo está cerrado; lo que queda son cuatro frentes de método, no de búsqueda de precios.
2. Para **seguir confirmando** ya no falta una base ni un precio: los 388 tienen cifra. Lo que bloquea los 271 de fuente única es una **segunda fuente independiente**. Orden rentable: (a) cotización de tienda con URL y fecha para los 54 de contraste de mercado, empezando por los 39 que usan partidas (`MT-PERFIL-ALUM` 74 usos, `MT-SENAL-OBRA` 73, `MT-REGUL-GAS` 37, `MT-SOPORTE-AC` 36, `MT-VIDRIO-TEMP` 35); (b) cerrar la especificación de los 28 de familia análoga para poder pedir cotización del artículo exacto; (c) resolver las 72 divergencias de la verificación.
3. Orden de trabajo recomendado por impacto: **desglosar los 64 recursos agregados** (`MT-CONS-DEM` 398 usos, `MT-ELE-CAJA` 177, `MT-PLO-SOP` 169, `MT-TORN` 154); **construir el modelo de coste horario** de la maquinaria de mayor uso (`MQ-TALADRO` 1.025, `MQ-SIERRA` 199, `MQ-ANDAMIO` 190, `MQ-ATORN` 162); **resolver las 23 alertas de divergencia** (`MT-PYL-PASTA` 99, `MT-MADERA-LISTON` 91, `MT-ALAMBRE` 49); y **buscar un banco nacional y vigente** con licencia de uso. Los usos se solapan entre recursos y no equivalen a frecuencia comercial ni impacto económico.
3. Solicitar o buscar especificaciones y fuentes comparables que permitan resolver los bloqueos: unidad, prestaciones, alcance, zona, fecha, IVA, transporte, consumos y vida útil según corresponda. **No aplicar un precio solo por encontrar un número** ni dar por equivalente una partida instalada y un material, un alquiler diario y un coste horario, o una compra y su amortización.
4. De los recursos sin precio revisado, 23 de uso cero no se mencionaban en los ocho barridos recientes; no son necesariamente inéditos en los demás informes. Antes de priorizarlos, valorar si tienen utilidad actual en el catálogo y consultar al usuario si procede.
5. Al adoptar una cifra, documentar fuente, normalización, supuestos y reservas; actualizar de forma reproducible registro, generador y artefactos pertinentes, añadir pruebas y comprobar el impacto en partidas. Mantener el estado `en_revision` cuando falte validación. No sobrescribir precios propios de clientes ni ejecutar SQL o desplegar sin una decisión controlada.

## Archivos principales

- [Registro maestro](espana_2026-11-06.csv): estados, `precio_revisado`, fuentes, evidencias y criterios. `precio_matriz` en este registro conserva el importe de la fotografía inicial; no debe confundirse necesariamente con el importe actual.
- [Inventario integral actual](espana_inventario_integral_2026-11-07.csv): precios de la matriz local, usos, estados y candidatos. [Metodología y límites](ESPANA_INVENTARIO_INTEGRAL_2026-11-07.md).
- [Continuidad y enlaces a todos los lotes](CONTINUIDAD.md); los valores de sus secciones antiguas son cortes históricos. En particular, el bloqueo antiguo de la suite por `tinycss2` quedó superado en el último corte.
- [Octavo barrido](ESPANA_OCTAVO_BARRIDO_PARCIAL_2026-11-07.md) y [decisiones CSV](espana_decisiones_octavo_barrido_parcial_2026-11-07.csv); los barridos anteriores tienen informes y CSV equivalentes.
- [Verificación cruzada](ESPANA_VERIFICACION_2026-11-07.md): reglas de independencia, las 7 confirmaciones nuevas (730 usos), las 26 divergencias explicadas y la cola de 363 recursos con lo que falta a cada uno.
- [Cierre del primer ciclo](ESPANA_CIERRE_2026-11-07.md): método por lotes, 18 precios aplicados, 5 confirmaciones, lo descartado con motivo, impacto en partidas y límites. Artefactos: `espana_adjudicacion_2026-11-07.csv` (375 decisiones), `espana_referencias_cierre_2026-11-07.csv` (18 referencias aceptadas, las que consume el generador) y `espana_cierre_decisiones_2026-11-07.csv` (libro de decisiones).
- `basedatos_partidas/datos/descompuestos/*.json`: descripciones, unidades y rendimientos reales de las partidas.
- `basedatos_partidas/salida/precios_recursos_espana.csv`: matriz local actual. `basedatos_partidas/datos/precios_publicos/ES.json`: índice público local. `tools/generar_matriz_precios_espana.py` y `tools/inventario_precios_espana.py`: generadores. `docs/cargar_precios_referencia_espana_2026-11-06.sql`: SQL generado, **no ejecutado**.

## Comprobaciones y precauciones al retomar

- Última suite completa (cierre): **3.590 aprobadas y 13 omitidas** con `.venv/bin/python -m pytest -q -n 4`. Un proceso trabajador se cayó por memoria durante `tests/test_recorrido_critico.py`; esa prueba pasa aislada (4/4). Con `-n 2` el reparto consume menos memoria y evita ese fallo. Las omitidas no se consideran aprobadas. Último `git diff --check`: limpio. `.venv` no se conserva en la instantánea del entorno: recrear con `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`.
- Para repetir la suite completa, incluida la prueba nueva: `.venv/bin/python -m pytest -q -n 4`. Para verificar espacios y conflictos de formato: `git diff --check`. No inferir precisión de mercado de una prueba de importabilidad o de un test automatizado.
- El trabajo está en la rama de sesión `arena/a40ccb19-generador-comercial`. El cierre se registra con commit en esa rama; **no se ejecutó SQL ni se desplegó**. Consultar `git status` antes de trabajar; no descartar cambios existentes.
- Los generadores de matriz e inventario **ejecutan regeneración incluso con `--help`**; no usar esa opción solo para inspeccionarlos. No volver a ejecutar scripts de `/tmp` de lotes ya aplicados: pueden repetir evidencias o cambios. Consultar el código fuente y los informes antes de regenerar.
- Las fuentes y ofertas se consultaron en las fechas indicadas y pueden cambiar. El BC3 íntegro de Extremadura y el ZIP de Madrid no se obtuvieron en esta sesión; una fuente identificada con licencia no comercial no debe incorporarse como base comercial sin autorización.
