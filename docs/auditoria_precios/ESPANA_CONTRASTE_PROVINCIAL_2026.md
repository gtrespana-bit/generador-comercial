# España 2026: contraste provincial de mano de obra

> **Actualización posterior:** se han aplicado cuatro referencias operativas por punto medio. Véase [decisión y cálculo](ESPANA_REFERENCIA_OPERATIVA_2026.md); este documento conserva la fotografía y conclusiones anteriores.

**Revisión: 2026-11-06.** Alcance: construcción y obras públicas; Madrid, Barcelona, Palencia y Bizkaia. Se comparan tablas salariales y pensiones, no presupuestos finales ni un promedio nacional. Los datos transcritos y sus fuentes figuran en [`espana_mano_obra_provincias_2026.csv`](espana_mano_obra_provincias_2026.csv). Son fuentes provinciales elegidas para empezar, **no una muestra estadística representativa de España**.

**Resultado:** aumentan la evidencia y el detalle territorial para `MO-AYU`, `MO-AYU-ESP` y `MO-OF1-ALB`, pero las correspondencias con los niveles de convenio son aproximadas. Ninguno queda confirmado nacionalmente. Las retribuciones anuales de las tablas incluyen conceptos y complementos de alcance diferente según el convenio, potencialmente extrasalariales; por tanto no se equiparan a la base de cotización ni al coste total de empresa.

## Datos comprobados

Importes anuales publicados para una persona a jornada completa. La pensión es aportación empresarial al plan por año completo, cuando se ha podido localizar. No sumarla dos veces a la retribución si una nómina ya la incorpora. Una contribución cotizable podría estar incluida en la base, aunque también se pague como aportación.

| Provincia | Categoría según fuente | Retribución de tabla €/año | Plan empresa €/año | Jornada convenio h/año | Estado y fuente |
|---|---|---:|---:|---:|---|
| Madrid | Peón suelto, XII | 23.051,90 | 456,40 | 1.736 | [BOCM, anexos VIII y XIX](https://www.bocm.es/boletin/CM_Orden_BOCM/2025/12/31/BOCM-20251231-1.PDF) |
| Madrid | Ayudante de oficio, X | 23.346,63 | 460,90 | 1.736 | BOCM, anexos VIII y XIX |
| Madrid | Peón especializado, XI | 23.079,10 | 456,89 | 1.736 | BOCM, anexos VIII y XIX |
| Madrid | Oficial 1.ª de oficio, VIII | 25.103,23 | 498,33 | 1.736 | BOCM, anexos VIII y XIX |
| Barcelona | Peón ordinario | 27.351,74 | 558,65 | 1.736 | [BOPB, anexos I-A y VI](https://ugtficabcn.cat/calaix/conveni/Convenio_colectivo_de_trabajo_de_la_industria_de_la_construccion_y_obras_publicas_de_la_provincia_de_Barcelona_2017_2021_ts_2026_BOPB.pdf); tablas **provisionales** |
| Barcelona | Ayudante | 28.362,17 | 578,83 | 1.736 | BOPB, anexos I-A y VI; tablas provisionales |
| Barcelona | Peón especialista | 27.824,43 | 567,16 | 1.736 | BOPB, anexos I-A y VI; tablas provisionales |
| Barcelona | Oficial 1.ª | 32.178,55 | 661,64 | 1.736 | BOPB, anexos I-A y VI; tablas provisionales |
| Palencia | Peón, XII | 20.298,22 | 440,45 | 1.736 | [BOP 02/01/2026](https://www.cnccyl.es/system/files/servicios/2021/11/tabla_salariales_y_plan_pensiones_2025-2026.pdf); cómputo anual contrastado en [transcripción](https://noticias.juridicas.com/base_datos/Laboral/983185-tablas-salariales-horas-extraordinarias-y-aportacion-al-plan-de-pensiones.html) |
| Palencia | Peón especialista, XI | 20.602,68 | 447,06 | 1.736 | Mismas fuentes de Palencia |
| Palencia | Oficial 1.ª, VIII | 21.543,77 | 467,47 | 1.736 | Mismas fuentes de Palencia |
| Bizkaia | Peón ordinario | 28.446,14 | Pendiente | 1.700 | [BOB, tablas 02/02/2026](https://www.ascobi.com/wp-content/uploads/2026/02/BOB-2-2-2026-tablas-salariales-2026.pdf); [convenio, art. 17](https://www.bizkaia.eus/lehendakaritza/Bao_bob/2025/12/18/III-194_cas.pdf?hash=7ab41ddf649518d45da10453ff4957c9) |
| Bizkaia | Ayudante | 29.190,17 | Pendiente | 1.700 | Mismas fuentes de Bizkaia |
| Bizkaia | Peón especialista | 28.845,09 | Pendiente | 1.700 | Mismas fuentes de Bizkaia |
| Bizkaia | Oficial 1.ª | 34.186,45 | Pendiente | 1.700 | Mismas fuentes de Bizkaia |

Las aportaciones de Madrid se contrastaron además con la [transcripción de los anexos XVIII y XIX](https://obrania.es/convenio-construccion/plan-pensiones/). En Palencia, el PDF del boletín disponible mediante la confederación no permitió extraer la última columna de la tabla 2026 con el lector automático: los cómputos anuales se contrastaron con la transcripción citada; falta comprobación visual directa de esa columna. Para Bizkaia no se ha verificado el importe individual del sistema EPSV y se deja vacío, **no se asume cero**.

El [calendario de Barcelona 2026](https://ccoo.app/convenio/convenio-colectivo-construccion-y-obras-publicas-de-barcelona/) fija 1.736 horas; en Madrid son 1.736 por art. 49 y en Bizkaia 1.700 por art. 17. Palencia se contrasta en el [convenio provincial](https://convenioscolectivos.org/convenios/construccion-obras-publicas-palencia/). Las jornadas de convenio no son necesariamente horas productivas.

## Qué implica para nuestras referencias

- `MO-AYU` tiene **15 €/h** en la matriz. Si la categoría de Barcelona fuera efectivamente el «ayudante» de su convenio y se trabajara todo el año conforme a la tabla, solo la retribución publicada dividida entre 1.736 horas es **16,34 €/h**, sin incluir cotización empresarial ni pensión. Esto es una **alerta de insuficiencia en ese escenario**, no la prueba de un precio nacional ni de que todos los `MO-AYU` correspondan al mismo convenio o categoría. Además, la tabla incluye un concepto de transporte, distancia y herramientas que puede estar presupuestado en otro lugar: evitar duplicarlo.
- `MO-AYU-ESP` tiene 18 €/h; «peón especialista» es un contraste plausible pero no identidad demostrada. Se necesitan base, costes y horas productivas antes de compararlo como coste total.
- `MO-OF1-ALB` tiene 21 €/h. Las tablas de oficial 1.ª varían considerablemente entre territorios y no distinguen por sí solas todos los costes reales del oficio. No corresponde confirmar o reemplazar ese precio a partir de estas cuatro referencias.
- Una comparación nacional requiere una metodología de ponderación y cobertura, convenios correctos para las funciones, cotizaciones sobre bases efectivas, costes restantes y fuentes fechadas. No se calcula la media de cuatro provincias como si fuese España.

## Corrección de fuente histórica

El documento anterior citaba **31.290,43 €/año** para oficial 1.ª de Barcelona como si fuera 2026. Ese valor corresponde a la tabla **2025**; la tabla publicada para 2026 indica **32.178,55 €/año**. Fuente: [BOPB 2025, CVE 202610047891](https://cartaslaborales.app/novedades-convenios/construccion-barcelona-tablas-plan-pensiones-2025) y [BOPB 2026, CVE 202610047915](https://ugtficabcn.cat/calaix/conveni/Convenio_colectivo_de_trabajo_de_la_industria_de_la_construccion_y_obras_publicas_de_la_provincia_de_Barcelona_2017_2021_ts_2026_BOPB.pdf). Ambas tablas se publicaron en 2026: fecha de publicación y año de la tabla no son lo mismo. Las tablas 2026 se califican de provisionales en el acta. Se conserva el documento antiguo con aviso para mantener trazabilidad; no se han sustituido precios operativos.

## Próximas comprobaciones

1. Comprobar visualmente la columna 2026 de Palencia y la aportación EPSV de Bizkaia; ampliar la cobertura a más provincias y convenios de especialidades.
2. Identificar las bases reales por mes y cotización aplicable, reducciones o bonificaciones, pensiones, complementos y costes laborales adicionales, y las horas efectivamente productivas. El [modelo de auditoría](ESPANA_MANO_OBRA_2026.md) permite calcular un escenario documentado, no inventa estos datos.
3. Reconciliar cada gasto con el descompuesto y con gastos generales y beneficios, verificar los rendimientos y definir cómo obtener una referencia nacional antes de confirmar o cambiar las cifras.
