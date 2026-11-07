# Punto de continuidad: auditoría de precios por país

**Para retomar rápidamente:** [resumen actualizado, pendientes y pasos siguientes](REANUDAR_AUDITORIA_ESPANA.md). Las secciones siguientes conservan el historial y sus resultados de prueba son fotografías de cada momento.

## Octavo barrido parcial — 7 de noviembre de 2026

**8 recursos examinados, 0 precios nuevos aplicados**: [informe y decisiones](ESPANA_OCTAVO_BARRIDO_PARCIAL_2026-11-07.md). Alerta de unidad `m2` frente a medición por unidad en `10.02.02.060`. Revisar señalización específica y tubería en BIE, alcances de fijaciones de fachada, y dimensionamiento/conexiones de separador de grasas. No se modificaron precios, estados ni partidas; el corte sigue en 202 precios revisados. Inventario regenerado; 72 pruebas focalizadas aprobadas y `git diff --check` limpio. Instaladas en el entorno local las dependencias de pruebas `tinycss2==1.5.1` y `pytest-xdist==3.8.0` ya declaradas: suite completa lanzada antes de crear el test de este bloque, 3.581 aprobadas y 13 omitidas en 260,63 s; las dos pruebas nuevas pasaron aparte en las focalizadas. SQL no ejecutado ni despliegue.

## Séptimo barrido parcial — 7 de noviembre de 2026

**15 recursos examinados y 0 precios nuevos aplicados:** [informe y decisiones](ESPANA_SEPTIMO_BARRIDO_PARCIAL_2026-11-07.md). Prioridades de revisión: alarma de asistencia con timbre genérico, posible divergencia entre poliuretano cementoso y bicomponente, compatibilidad de imprimación, posible solape de clavos, armaduras y transporte, y suministro de cortina y papel sin recurso o metadata específicos. Nada demuestra automáticamente incumplimiento, duplicidad o ausencia de material en la obra. Corte sin cambios; inventario regenerado, 70 pruebas focalizadas superadas y `git diff --check` limpio. Suite completa no validada (bloqueo previo por `tinycss2`). SQL no ejecutado ni despliegue.

## Sexto barrido parcial — 7 de noviembre de 2026

**14 recursos examinados y 0 precios nuevos aplicados**: [informe, fuentes y alertas](ESPANA_SEXTO_BARRIDO_PARCIAL_2026-11-07.md). En `04.08.02.040` el campo unidad es m2 pero la descripción dice metro lineal, y falta especificar compatibilidad de equipo de micropilotaje. Las líneas de vida requieren definición de sistema y soporte; pintura intumescente requiere verificar dosis para el sistema y grado requerido. Posibles solapes de tira LED de cliente, cama de arena, anclajes y aspiración. No se modificaron partidas ni precios; siguen abiertas las alertas anteriores. Inventario regenerado; 68 pruebas focalizadas aprobadas y `git diff --check` limpio. Suite completa no validada (bloqueo previo por `tinycss2`). SQL no ejecutado ni despliegue.

## Quinto barrido parcial — 7 de noviembre de 2026

**16 recursos examinados, 0 precios nuevos aplicados**: [fuentes y alertas](ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md). La iluminación de emergencia usa lámpara de obra sin prestaciones de emergencia descritas; la red vertical se mide por metro sin altura ni soporte separado identificable. Revisar ambos sistemas antes de confiar en presupuestos o ejecutar. Posibles solapes en persianas, malla de microcemento y remates PVC; metadata de motor de portón en partida de persiana motorizada. Persisten las alertas anteriores. Sin cambios de precios ni estados; inventario regenerado, 66 pruebas focalizadas superadas y `git diff --check` limpio. Suite completa no validada: intento previo bloqueado por `tinycss2`. SQL no ejecutado ni despliegue.

## Cuarto barrido parcial completado documentalmente — 7 de noviembre de 2026

**30 recursos examinados; 0 precios nuevos aplicados.** [Fuentes, bloqueos y alertas](ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md). En 17.07.01.080 falta recurso específico de camilla; en 14.10.01.110 aparece limpiador de climatización en piscina, sin aptitud acreditada; en 06.09.01.230 se usa pasivante de armaduras para anticarbonatación. Revisar antes de confiar en estos presupuestos o aplicar productos. Posible solape herraje/riel en cinco partidas; se mantienen alertas de EPI, fachadas, bovedillas y apeo. No se han modificado partidas ni precios. Corte sin cambios: 388 recursos, 13 confirmados, 227 en revisión, 148 pendientes y 202 precios revisados. Inventario regenerado; 64 pruebas focalizadas superadas y `git diff --check` limpio. Suite completa no validada: intento anterior bloqueado por `tinycss2`. SQL no ejecutado ni despliegue.

## Tercer barrido completado documentalmente — 7 de noviembre de 2026

**30 recursos examinados, ninguno aplicado; las 20 decisiones adicionales quedan documentadas, sin equivalencia completa acreditada.** [Fuentes y bloqueos](ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md). En 23 partidas coexisten MT-APEO y MT-VIGA-APEO: el precio provisional del primero ya incluye madera; revisar posible duplicidad y dimensionamiento antes de presupuestar. Precios y estados sin cambios; inventario regenerado, 63 pruebas focalizadas superadas y `git diff --check` limpio. Suite completa no validada en esta continuación: el intento anterior quedó bloqueado por falta de `tinycss2`. SQL no ejecutado, sin despliegue.


## Otros 30 recursos — 7 de noviembre de 2026

Examinados **otros 30 recursos distintos**, seleccionados por uso: **1 estimación provisional aplicada y 29 sin precio revisado**. [Informe y decisiones](ESPANA_LOTE_OTROS_30_2026-11-07.md). MT-APEO: 1,04 €/ud en la hipótesis concreta de viga CYPE, a partir de materiales amortizados redondeados, no de la partida ejecutada; IVA y vigencia no acreditados. Exige dimensionamiento técnico, no es media nacional. No se ha convertido el salario del metal ni alquileres diarios sin cargas o condiciones completas.

Corte: **388 recursos; 13 confirmados como referencia, 227 en revisión y 148 pendientes; 202 precios revisados** (193 materiales y 9 laborales); 38 en revisión sin precio revisado. Matriz, inventario, SQL local e índice ES regenerados. **150 pruebas superadas**; 388 filas técnicamente importables, 0 errores (no valida el mercado). SQL no ejecutado ni despliegue. Sigue incompleta la auditoría. La corrección de MQ-RODILLO (pintura) y unidad de MT-TORN se hizo en el informe anterior y el registro, sin alterar estados ni precios.


## Barrido de 30 recursos — 7 de noviembre de 2026

Examinados **30 recursos en un solo bloque**, priorizando los de mayor uso: **9 estimaciones provisionales en revisión** y **21 sin precio revisado**, con fuentes y razones por código en [informe y cálculo](ESPANA_LOTE_30_2026-11-07.md). Los nueve no son 30 precios completados ni referencias confirmadas; seis son domóticos sin uso actual. IVA, vigencia y transporte CYPE no acreditados. Sensores de luz y movimiento usan la misma referencia multifunción: si son un solo equipo debe evitarse doble medición. El controlador queda sin precio por software no acreditado.

Corte: **388 recursos; 13 confirmados de referencia, 226 en revisión, 149 pendientes; 201 precios revisados** (192 materiales y 9 laborales); 38 en revisión sin precio. Matriz, inventario, SQL local e índice ES regenerados (2016 partidas y 183 apartados). **112 pruebas superadas**, con otras 24 después de regenerar el índice; verificador 388 importables y 0 errores; importabilidad no valida mercado. SQL no ejecutado y sin despliegue. La auditoría sigue incompleta; cortes siguientes históricos.


## Evacuación y epoxi — 7 de noviembre de 2026

Añadidas **3 estimaciones provisionales en revisión**, con cinco componentes: [cálculos, fuentes y descartes](ESPANA_LOTE_EVACUACION_EPOXI_2026-11-07.md). PVC 110 mm **10,36 €/m**, condicionado a la equivalencia con 4 pulgadas, con consumibles CYPE y tubo comercial; cazoleta con parahojas **37,82 €/ud**; resina epoxi **24,23 €/l**, conversión aproximada usando ficha del fabricante y precio por kg CYPE. No son medias nacionales. IVA de CYPE y portes no acreditados; validar especificación, compatibilidad y anclaje. El tubo de acero continúa pendiente por pesos contradictorios y heterogeneidad. El precio comercial del epoxi no se usa por formato ambiguo.

Corte: **388 recursos; 13 confirmados como referencia, 217 en revisión y 158 pendientes; 192 precios revisados** (183 materiales y 9 laborales); 38 en revisión sin precio. **110 pruebas superadas**, 388 filas técnicamente importables y 0 errores; importabilidad no valida adecuación comercial. Matriz, inventario, SQL e índice ES regenerados localmente (2016 partidas, 183 apartados). SQL no ejecutado ni despliegue. La auditoría continúa incompleta; los cortes siguientes son históricos.

## Continuación del 7 de noviembre de 2026 — sistemas y materiales

Añadidas **6 referencias provisionales de 7 componentes**, todas en revisión: [fuentes, cálculos y exclusiones](ESPANA_LOTE_CONTINUACION_2026-11-07.md). Cubren gravilla, crucetas y cuñas, mampara de oficina, panel de PVC, mosaico y adhesivo específico para piedra sensible. El 1,8 t/m³ de gravilla es un rendimiento inferido para una cubierta concreta; las cuñas son reutilizables pero se imputa su coste íntegro en un uso. El adhesivo de Mosafil se envía desde Alemania, se supone IVA peninsular y el porte no está incluido. CYPE no confirma IVA ni vigencia. Ninguna es media nacional ni garantía de adecuación al proyecto. La caja eléctrica genérica sigue sin precio revisado: las cajas de mecanismo y de derivación tienen importes muy diferentes y falta mezcla representativa.

Corte: **388 recursos; 13 confirmados como referencia, 214 en revisión y 161 pendientes; 189 precios revisados** (180 materiales y 9 laborales); 38 en revisión sin precio revisado. **139 pruebas superadas**, 388 filas técnicamente importables y 0 errores; importabilidad no valida mercado ni equivalencia. Matriz, inventario, SQL e índice ES regenerados localmente (2016 partidas, 183 apartados). SQL no ejecutado ni despliegue. La auditoría sigue incompleta; los cortes siguientes son históricos.

## Verificación adicional del 7 de noviembre de 2026

Añadidas **7 referencias provisionales de 8 componentes**, todas en revisión: [fuentes, cálculos y exclusiones](ESPANA_LOTE_VERIFICACION_2026-11-07.md). Corte: **13 confirmados como referencia, 208 en revisión y 167 pendientes; 183 precios revisados** (174 materiales y 9 laborales); 38 en revisión sin precio revisado. CYPE sin IVA ni vigencia acreditados, masilla normalizada con densidad húmeda nominal y tubo con IVA supuesto y transporte peninsular condicionado. No son medias nacionales ni garantía de adecuación al proyecto. **137 pruebas superadas**, 388 filas técnicamente importables y 0 errores; importabilidad no valida el mercado. Matriz, inventario, SQL e índice ES regenerados localmente. SQL no ejecutado ni despliegue. Los cortes siguientes son históricos.

## Bloque amplio del 7 de noviembre de 2026

Añadidas **12 referencias provisionales de 14 componentes**, todas en revisión: [informe y exclusiones](ESPANA_LOTE_BLOQUE_AMPLIO_2026-11-07.md). Corte: **13 confirmados como referencia, 201 en revisión, 174 pendientes; 176 precios revisados** (167 materiales y 9 laborales); 38 en revisión sin precio revisado. Son referencias puntuales, no medias nacionales. La revisión amplia incluyó maquinaria, hormigones, seguridad, drenaje y fontanería; permanecen pendientes si no se pudo justificar alcance completo. El extintor con soporte y señal sí se ha incorporado ahora, a diferencia del corte anterior. **135 pruebas superadas**, 388 filas importables y 0 errores; importabilidad no valida mercado. Matriz, inventario, SQL e índice ES regenerados localmente. SQL no ejecutado ni despliegue. Los cortes siguientes son históricos.

## Lote de sistemas del 7 de noviembre de 2026

Añadidas **7 referencias provisionales de 18 componentes**: [informe, cálculos y exclusiones](ESPANA_LOTE_SISTEMAS_2026-11-07.md). Corte histórico: **13 confirmados como referencia, 189 en revisión y 186 pendientes; 164 precios revisados** (155 materiales y 9 laborales), y 38 en revisión sin precio revisado. No son medias nacionales; verificar IVA y vigencia de CYPE y las reservas de compatibilidad. El detector y el aspirador no se aplicaron por falta de condiciones completas. Matriz, inventario, SQL e índice ES regenerados localmente; **133 pruebas superadas**, 388 filas importables y 0 errores, `git diff --check` limpio. La importabilidad no valida los precios. SQL generado sin ejecutar y sin despliegue. Los cortes siguientes son históricos.

## Lote de componentes del 7 de noviembre de 2026

Añadidas **8 referencias provisionales de 19 componentes**: [informe y reservas](ESPANA_LOTE_COMPONENTES_2026-11-07.md). Corte: **13 confirmados como referencia, 182 en revisión y 193 pendientes; 157 precios revisados** (148 materiales y 9 laborales), 38 en revisión sin precio revisado. Las referencias no son medias nacionales; los descompuestos CYPE tienen IVA y vigencia sin confirmar. Matriz, inventario, SQL e índice ES regenerados localmente; **107 pruebas superadas**, 388 filas importables y 0 errores, `git diff --check` limpio. Importabilidad no implica validación comercial. SQL generado sin ejecutar y sin despliegue. Las cifras siguientes son históricas.

## Lote ampliado por familias del 7 de noviembre de 2026

Añadidas **28 referencias provisionales de 29 componentes**, todas en revisión: [informe con fuentes y exclusiones](ESPANA_LOTE_FAMILIAS_2026-11-07.md). Corte: **13 confirmados como referencia, 174 en revisión, 201 pendientes y 149 precios revisados** (140 materiales y 9 laborales); 38 revisiones sin precio revisado. No son medias nacionales. CYPE tiene IVA y vigencia pendientes; algunas ofertas presentan reservas de equivalencia. Matriz, inventario, SQL e índice ES regenerados localmente; **140 pruebas superadas**, 388 filas técnicamente importables y 0 errores, diff limpio. SQL no ejecutado ni despliegue. Las cifras siguientes son históricas.

## Lote de alta frecuencia del 7 de noviembre de 2026

Cinco referencias adicionales provisionales con siete componentes: [informe, fuentes y exclusiones](ESPANA_LOTE_ALTA_FRECUENCIA_2026-11-07.md). **13 confirmados como referencia, 146 en revisión y 229 pendientes; 121 precios revisados** (112 materiales, 9 laborales); 38 revisiones todavía sin precio revisado. No son medias nacionales. El tablero de melamina está basado en precio indexado con ficha que devolvió HTTP 500; sigue en revisión. Maquinaria, hormigón, señalización y malla de junta no se aplicaron por equivalencias o condiciones incompletas. Matriz, inventario, SQL local e índice ES regenerados, sin ejecutar SQL, desplegar ni modificar precios de clientes. **92 pruebas superadas** y 388 filas técnicamente importables sin errores; importabilidad no implica validación comercial. `git diff --check` limpio. Las cifras siguientes son históricas.

## Lote adicional priorizado del 7 de noviembre de 2026

Añadidas **18 referencias provisionales** mediante 20 componentes de cadenas y descomposiciones: [cálculos, fuentes y reservas](ESPANA_LOTE_PRIORIDAD_2026-11-07.md). Corte: **13 confirmados como referencia, 141 en revisión, 234 pendientes; 116 precios revisados** (107 materiales y 9 laborales). De los 141 en revisión, 38 no tienen precio revisado. La estimación no es media nacional; el IVA de CYPE no se ha confirmado. Matriz, inventario, SQL local e índice ES regenerados; 61 pruebas superadas y 388 filas técnicamente importables sin errores. No se ejecutó SQL ni se desplegó. Las cifras siguientes son históricas.

## Barrido de cadenas del 7 de noviembre de 2026

Incorporados **20 precios provisionales** con 21 observaciones minoristas y reservas por formato, equivalencia, IVA y vendedor: [informe y tablas](ESPANA_LOTE_CADENAS_2026-11-07.md). **13 confirmados como referencia, 123 en revisión y 252 pendientes; 98 precios revisados** (89 materiales y 9 de mano de obra), de los cuales 38 recursos en revisión aún no tienen precio revisado. Es una muestra puntual, no catálogo exhaustivo ni media nacional. Matriz, inventario, SQL local e índice ES regenerados; 61 pruebas superadas y 388 filas importables sin errores (la importabilidad no valida mercado). Sin ejecutar SQL, desplegar ni cambiar precios de clientes. Las cifras siguientes son históricas.

## Lote anterior — siete materiales

Añadidas **siete referencias provisionales** de Extremadura y descomposiciones CYPE: [fuentes y reservas](ESPANA_LOTE_MATERIALES_2026-11-07.md). **13 confirmados como referencia, 103 en revisión y 272 pendientes; 78 precios revisados** (69 materiales y 9 mano de obra). De los 103 en revisión, 38 no tienen precio revisado. El C1 no acredita color; para lámina anticapilaridad se descartó convertir de €/m² a €/m sin ancho. CYPE no acredita vigencia, IVA ni portes; no representa media nacional. Extremadura fue consultada parcialmente. Matriz, inventario, SQL local e índice ES regenerados; 23 pruebas focalizadas superadas y 388 filas importables sin errores. Sin ejecutar SQL, desplegar ni cambiar precios de clientes. Las cifras siguientes son históricas.

## Lote de cuadros oficiales del 7 de noviembre de 2026

Añadidos **8 precios provisionales** de Palencia y Extremadura, con especificaciones, exclusiones y fuentes individuales en [lote de cuadros](ESPANA_LOTE_CUADROS_2026-11-07.md). El BC3 extremeño se consultó por fragmentos, no íntegramente; son precios regionales, no medias nacionales. Estado: **13 confirmados, 96 en revisión, 279 pendientes y 71 precios revisados** (62 materiales, 9 mano de obra); 38 en revisión sin precio revisado. Sin ejecutar SQL ni desplegar. Cifras siguientes históricas.

## Lote por descomposiciones del 7 de noviembre de 2026

Se incorporaron **10 precios provisionales** de descomposiciones CYPE consultadas individualmente, con equivalencias y condiciones señaladas en [lote banco](ESPANA_LOTE_BANCO_2026-11-07.md). Una fuente por recurso, no media nacional; la fecha de edición, IVA y porte no se han confirmado. **13 confirmados, 88 en revisión, 287 pendientes, 63 precios revisados** (54 materiales, 9 mano de obra); 38 en revisión siguen sin precio revisado. La base multirregional DDC no se usó: BCCA 2023, transformaciones PPP y licencia no comercial de la compilación. No se ha ejecutado SQL ni desplegado. Cifras inferiores históricas.

## Lote posterior del 7 de noviembre de 2026

Añadidos tres precios provisionales y en revisión: pasta y cinta **1,01 €/kg**, cable de alarma **0,62 €/m** y tornillo con arandela **0,21 €/ud**. La cinta usa un rendimiento documentado de un sistema específico; el trenzado del cable no se acredita y las medidas de tornillos difieren. Ver [cálculos y reservas](ESPANA_LOTE_POSTERIOR_2026-11-07.md). Estado actual: **13 confirmados, 78 en revisión y 297 pendientes** de 388; **53 precios revisados** (44 materiales y 9 laborales), de los que 38 son en revisión. No es auditoría completa. Sin ejecutar SQL ni desplegar. Cifras inferiores históricas.

## Investigación adicional del 7 de noviembre de 2026

Se añadieron dos referencias **provisionales**: abasto flexible **2,21 €/ud** y membrana líquida de poliuretano **7,85 €/kg**. Son medias de dos ofertas, limitadas a los formatos, conexiones y condiciones documentadas; transporte condicionado o no confirmado. Las búsquedas de silicona, adhesivo C1, protección compuesta y pasta con cinta no se aplicaron por alcance o equivalencia insuficiente. Véase [detalle y fuentes](ESPANA_LOTE_TIENDAS_2026-11-07.md). Estado: **13 confirmados, 75 en revisión y 300 pendientes**, 50 precios revisados (41 materiales y 9 mano de obra). No hay validación integral ni despliegue o SQL ejecutado. Las cifras de secciones posteriores son históricas.

## Inventario integral del 7 de noviembre de 2026

Se consolidaron los **388 recursos** en [inventario integral](ESPANA_INVENTARIO_INTEGRAL_2026-11-07.md) con estados actuales y candidatos de la copia BCCA, sin aplicar cruces textuales. 359 tienen propuestas y 29 no; las propuestas son antiguas, no verificadas y pueden ser falsas. La base completa de Extremadura 2026 no se obtuvo en este entorno. El inventario es integral; la **validación de precios no lo es**.

Se añadieron `MT-YESO-REP` **0,16 €/kg** y `MT-PIN-ESMALTE` **9,84 €/l**, provisionalmente, con dos ofertas cada uno: [fuentes y límites](ESPANA_LOTE_TIENDAS_2026-11-07.md). Estado actual **13 confirmados, 73 en revisión y 302 pendientes**; **48 precios revisados** (39 materiales y 9 de mano de obra). Matriz, índice público local ES y SQL local regenerados; **130 pruebas superadas**, 388 filas importables sin errores y diff limpio. No se ejecutó SQL ni se desplegó. Cifras de secciones posteriores son históricas.

## Séptimo lote del 7 de noviembre de 2026 — tiendas de construcción

Aplicadas localmente cuatro referencias **provisionales y en revisión**: `MT-PINT-ANTICORR` **7,75 €/l**, `MT-BANDA-REF` **3,01 €/m**, `MT-CURADOR` **2,25 €/l** y `MT-POLIESTIRENO-EXT` **4,74 €/m²**. Se consultaron Obramat y Leroy Merlin, entre otros proveedores: la oferta de imprimación de Leroy es de un tercero, Pinturas Proa. La banda requiere verificar compatibilidad con el sistema; el curador se convierte de kg a litros usando densidad nominal; el XPS es de 40 mm y no representa todos los espesores. La oferta Proa declara envío gratis, por lo que las condiciones de transporte de la referencia quedan no confirmadas. [Cálculos, fuentes y descartes](ESPANA_LOTE_TIENDAS_2026-11-07.md).

Inventario actual: **13 confirmados de referencia, 71 en revisión y 304 pendientes**, de 388; **46 precios revisados** (37 materiales y 9 laborales). Matriz, índice público ES y SQL local regenerados; **118 pruebas superadas**, 388 filas importables y 0 errores. Importabilidad no verifica los precios. No se ejecutó SQL ni desplegó. Las secciones siguientes son históricas.

## Sexto lote del 7 de noviembre de 2026 — recursos prioritarios

Se han incorporado localmente cuatro referencias **provisionales, en revisión**, basadas en dos ofertas cada una: `MT-PYL-LANA` **2,30 €/m²**, `MT-PIN-CAUCHO` **3,35 €/l**, `MT-PLO-PPR20` **0,91 €/m** y `MT-TUB-PPR25` **1,41 €/m**. La ficha de una oferta de lana es contradictoria sobre el revestimiento y debe comprobarse; una pintura no especifica tintabilidad; los tubos no incluyen accesorios ni termofusión. Precios, enlaces y reservas en [lote prioritario](ESPANA_LOTE_PRIORITARIO_2026-11-07.md). Se excluyeron PVC cementado, malla de encuentros, cinta y bloque por alcance o equivalencia incompletos.

Inventario al terminar ese lote: **13 confirmados de referencia, 67 en revisión y 308 pendientes**, de 388; **42 precios revisados** (33 materiales y 9 laborales). Se regeneraron matriz, índice público ES y SQL local. Comprobación: **117 pruebas superadas**, 388 filas importables y 0 errores; `git diff --check` limpio. Importabilidad no valida precios. No se ejecutó SQL ni desplegó. Las cifras posteriores son históricas.

## Cruce masivo real con copia de BCCA — 7 de noviembre de 2026

Se obtuvo una copia íntegra y verificable de `basicos.json` del banco abierto CERP Tech (versión 0.7.0, commit fijo y SHA-256 documentados). El archivo atribuye los datos a la Junta de Andalucía y declara precios BCCA de edición 2024; muchos son de 2021–2022. Se cruzaron **388 recursos** con **5.656 básicos utilizables**: **359 tienen candidatos textuales**, 29 ninguno, y hay 1.637 propuestas. Son coincidencias no validadas, no precios verificados; existen falsos positivos y mezcla posible de descripciones. La fuente es una copia derivada, no el BC3 oficial. Detalles y reproducción: [cruce BCCA](ESPANA_CRUCE_BCCA_2026-11-07.md); resultados: [candidatos](espana_candidatos_bcca_2026-11-07.csv). No se han aplicado precios ni cambiado estados por este cruce, dado que los importes son antiguos y la similitud no acredita equivalencia. El lote más reciente y su inventario figuran al principio de este documento. El cruce BC3 de Extremadura 2026 sigue sin acceso íntegro.

Pruebas del nuevo lector, cruce previo y lotes: **8 pasadas**; `git diff --check` limpio. No se ejecutó SQL ni desplegó.

## Quinto lote del 7 de noviembre de 2026 — materiales comerciales

Aplicados localmente cuatro precios **provisionales**: `MT-MADERA-LISTON` **0,82 €/m**, `MT-PIN-FONDO` **4,09 €/l**, `MT-SEPARADOR` **0,06 €/ud** y `MT-GEOTEXTIL` **0,68 €/m²**. Sus restricciones incluyen diferencias de formulación y recubrimiento, disponibilidad incierta de una oferta de fijador, una discrepancia de imagen en un mazo de listones y una oferta de geotextil solo para Mallorca. Véase [lote comercial](ESPANA_LOTE_COMERCIAL_2026-11-07.md). Los cuatro siguen en revisión; no son medias nacionales. No se modificaron otros recursos por equivalencias dudosas.

Inventario al terminar ese lote: **13 confirmados de referencia, 63 en revisión y 312 pendientes**, de 388; **38 precios revisados** (29 materiales y 9 laborales). Comprobación local: **119 pruebas superadas**, 388 filas importables sin errores y diff limpio. Matriz, índice público ES y SQL local regenerados. No se ejecutó SQL ni se desplegó. La búsqueda de un acceso legítimo e íntegro a una base para el cruce masivo sigue pendiente; las consultas fragmentarias no constituyen un cruce integral. Las cifras siguientes son históricas.

## Cuarto lote del 7 de noviembre de 2026 — contraste regional y comercial

Aplicados localmente tres precios provisionales: `MT-AGUA-OBRA` **0,84 €/m³** (antes 1,822785), `MT-MALLA-ELEC` **2,51 €/m²** (antes 5,50) y `MT-CLAVOS` **3,21 €/kg** (antes 2,962025). Todos siguen en revisión: malla nominal de 6 mm y 15×15, clavo de un único formato y agua genérica, no todos los posibles componentes del catálogo. Los cuadros oficiales no aclaran IVA y porte en los extractos: están marcados como no confirmados para agua y malla. Detalles, cálculos y fuentes: [lote regional](ESPANA_LOTE_REGIONAL_2026-11-07.md). Se han regenerado matriz, índice público ES y SQL local sin ejecutarlo ni desplegarlo.

Inventario actual: **13 confirmados de referencia, 59 en revisión y 316 pendientes**, de 388; **34 precios revisados** (25 materiales y 9 laborales). La consulta del BC3 de Extremadura sigue siendo parcial: no se ha ejecutado un cruce integral sobre el archivo completo. La auditoría está lejos de completarse y aún hace falta un mecanismo escalable con bases íntegras para ir más rápido; no interpretar el lote como confirmación nacional. Las cifras de secciones siguientes son históricas.

Comprobación: **112 pruebas superadas**, 388 filas importables y 0 errores; `git diff --check` limpio. La importabilidad no valida el mercado. Frente a la matriz del commit base solo cambian los seis recursos de los dos últimos lotes. No se ha ejecutado SQL ni desplegado.

## Tercer lote del 7 de noviembre de 2026 — materiales

Se han aplicado tres referencias provisionales adicionales: `MT-ALAMBRE` **4,92 €/kg** (antes 2,10), `MT-CABLE-DATOS` **0,42 €/m** (antes 0,341772) y `MT-DESMOLD` **5,93 €/l** (antes 3,189873). La suma de usos por recurso es 141, pero puede haber partidas solapadas: no son necesariamente 141 partidas distintas. Véanse [cálculos, fuentes y limitaciones](ESPANA_MATERIALES_2026-11-07.md). Los tres siguen en revisión. La matriz, el índice público ES local y el SQL de carga se han regenerado; el nombre histórico del SQL se conserva por compatibilidad. No se ha ejecutado ni desplegado.

El inventario actual tiene **13 confirmados de referencia, 56 en revisión y 319 pendientes**, de 388. Son 31 precios revisados (22 materiales y 9 laborales), no precios garantizados. La comparación con la matriz del commit base detectó cambios únicamente en esos tres recursos. Comprobación local: **110 pruebas superadas**, 388 filas importables y 0 errores; `git diff --check` limpio. La importabilidad no verifica los precios. Las cifras de las secciones posteriores son históricas.

## Segunda revisión del 7 de noviembre de 2026

Se han consultado fragmentos del BC3 oficial de Extremadura y registrado 23 candidatos de maquinaria: diez tienen también antecedente en Palencia y trece pasan de pendientes a revisión. Véanse [el contraste](ESPANA_MAQUINARIA_EXTREMADURA_2026.md) y [las observaciones](espana_maquinaria_extremadura_2026.csv). Las fuentes no permiten concluir equivalencia ni promediar todavía. El registro suma ahora **13 referencias contrastadas, 53 en revisión y 322 pendientes**, sobre 388. No se han cambiado precios. La extracción es parcial, no un cruce real del BC3 completo.

Comprobación local tras este segundo lote: **108 pruebas superadas** y 388 filas importables con 0 errores. La importabilidad no verifica el mercado. `git diff --check` sin errores.

## Primera revisión del 7 de noviembre de 2026

La continuación se realiza en la rama actual de la sesión; la mención al PR #210 y la rama anterior debajo es histórica (ese PR está incorporado al commit base actual). Se ha revisado por lote maquinaria con el cuadro oficial de Palencia: once recursos documentados, diez de ellos pasan de pendiente a revisión; el taladro ya estaba en revisión. Véase [contraste de maquinaria](ESPANA_MAQUINARIA_PALENCIA_2026.md). El registro ahora tiene **13 referencias contrastadas, 40 en revisión y 335 pendientes**, sobre 388. Siguen existiendo 28 precios provisionales revisados (19 materiales y 9 de mano de obra); no se ha cambiado ningún precio por este contraste. Las cifras y situación que siguen son la fotografía del 6 de noviembre.

El cuadro es provincial y sus condiciones no permiten confirmar equivalencias ni hacer una media nacional. El BC3 de Extremadura sigue sin descargarse completo al workspace; no se ha ejecutado el cruce masivo real. No se ha accedido ni cargado SQL en producción.

Comprobación local del 7 de noviembre: 107 pruebas superadas (suite anterior más `tests/test_maquinaria_palencia_auditoria.py`); verificador ES: 388 filas importables y 0 errores. La importabilidad no confirma precios de mercado. `git diff --check` sin errores.

**Corte:** 6 de noviembre de 2026, fecha local de la sesión (America/Caracas).
**Rama:** `arena/6a7ec8e3-generador-comercial`.
**PR abierto:** [#210 — calculadora pública](https://github.com/gtrespana-bit/generador-comercial/pull/210). Los avances de esta auditoría se guardan también en esa rama y PR; no significa que hayan sido fusionados o desplegados.

## Qué pide el usuario

- Auditar los precios país por país, empezando por **España**, con referencia nacional operativa. Quiere terminar la auditoría y ver avances efectivos; rechazó un ritmo de búsqueda manual de uno en uno.
- Buscar un **método escalable por lotes** y realizarlo autónomamente: el usuario no quiere descargar, aportar archivos ni realizar gestiones.
- La mano de obra debe representar el coste de la empresa, no solo el salario. El usuario autorizó expresamente usar la media aritmética de dos referencias provinciales comparables como punto operativo (por ejemplo, 16 y 17 → 16,50).
- No inventar datos ni presentar una referencia operativa de dos fuentes como media estadística de toda España o como coste real garantizado. No confirmar recursos heterogéneos o insuficientemente sustentados. Distinguir coste empresarial de gastos generales y beneficio, y contemplar rendimientos para obtener coste por unidad de obra.

La calculadora del PR es una demostración de **una partida**, no presupuestos completos gratuitos. No implementar recuperación ni transferencia del cálculo después de registrarse o iniciar sesión: el usuario descartó expresamente esa complejidad. Las horas-persona no son duración de obra sin datos de cuadrilla.

## Estado exacto del corte

Inventario: **388 recursos**, de los que **13** están `confirmado_referencia`, **30** `en_revision` y **345** `pendiente`. El estado describe la auditoría, no que se conozca o garantice el coste de todas las empresas. Dentro de los 30 en revisión, 15 tienen precio provisional revisado y 15 aún no. En total se han actualizado precios de **19 materiales y 9 referencias de mano de obra**. La lista y el estado por recurso están en [`espana_2026-11-06.csv`](espana_2026-11-06.csv).

- Las cuatro referencias laborales contrastadas son `MO-AYU` 20,39 €/h, `MO-AYU-ESP` 20,59 €/h y `MO-OF1` / `MO-OF1-ALB` 23,18 €/h. Los otros cinco oficios tienen 23,18 €/h como hipótesis condicionada al convenio de construcción y permanecen en revisión. El modelo incluye retribución de tabla, aportación al plan y cargas estimadas, pero no todos los costes reales ni horas improductivas; detalle y fuentes en [`ESPANA_REFERENCIA_OPERATIVA_2026.md`](ESPANA_REFERENCIA_OPERATIVA_2026.md).
- Los materiales están documentados en [`ESPANA_MATERIALES_2026.md`](ESPANA_MATERIALES_2026.md), con las 38 ofertas y sus condiciones en [`espana_materiales_ofertas_2026.csv`](espana_materiales_ofertas_2026.csv). Son medias de dos ofertas puntuales sin IVA deducible ni transporte, no cotizaciones garantizadas ni una muestra estadística nacional. Algunos precios siguen en revisión por equivalencia o disponibilidad.
- La matriz local `basedatos_partidas/salida/precios_recursos_espana.csv` y el índice público local `basedatos_partidas/datos/precios_publicos/ES.json` reflejan estas referencias. El inventario conserva la fotografía inicial y los campos revisados por separado. No confundir el estado antiguo `confirmado` del catálogo base, que corresponde a otro flujo, con la auditoría española.
- Se ha generado `docs/cargar_precios_referencia_espana_2026-11-06.sql` para 388 filas, **sin ejecutarlo**. La instantánea anterior de cuatro referencias laborales está en [`cargar_precios_espana_mano_obra_2026-11-06.sql`](cargar_precios_espana_mano_obra_2026-11-06.sql). No se ha desplegado ni cambiado la base de datos de producción ni los precios propios de clientes.
- El último control ejecutado pasó **106 pruebas** de las suites de BC3, materiales, coste empresarial, calculadora, España y precios públicos. `tools/verificar_matriz_importable.py ES` informó de **388 filas importables y 0 errores**: esto solo valida compatibilidad de importación, no confirma que los 388 precios sean correctos. `git diff --check` no encontró errores.

## Tarea pendiente prioritaria: cruce real por lotes

Se ha creado `tools/cruzar_precios_bc3.py`, documentado en [`CRUCE_MASIVO_BC3.md`](CRUCE_MASIVO_BC3.md), con pruebas en `tests/test_cruzar_precios_bc3.py`. Lee BC3 locales, propone candidatos con fuente, ámbito, hash, unidad y alertas, y **no aplica precios**. Solo se ha probado con BC3 sintéticos: **no se ha ejecutado un cruce real completo**.

La [Junta de Extremadura publica una base oficial BC3 2026](https://www.juntaex.es/w/base-precios-construccion-2026); el [archivo BC3](https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923) se pudo consultar por fragmentos con la herramienta de lectura web, pero no se consiguió descargar íntegro al workspace por las restricciones de acceso de la sesión. La lectura web produjo 2339 fragmentos con problemas de caracteres; no reconstruir ni afirmar un archivo completo a partir de unos pocos. No se encontró un espejo íntegro en GitHub en las búsquedas hechas. Una base de Extremadura es regional, no una media nacional.

**Siguiente trabajo:** obtener autónomamente bancos completos y utilizables de dos o más zonas, respetando sus condiciones de uso; ejecutar el cruce de verdad; validar equivalencias, unidades, IVA, transporte y alcance antes de aplicar medias; ampliar pruebas, actualizar inventario, matriz y fuentes. La clasificación por prefijos de la herramienta corresponde a Extremadura y debe comprobarse antes de usar otra base. Si la infraestructura sigue impidiendo obtener los datos, dejar constancia precisa del bloqueo y no pedir al usuario que los descargue. Una puntuación textual no confirma equivalencia ni costes reales.

Para reproducir los controles actuales, con dependencias instaladas:

```bash
python -m pytest -q tests/test_cruzar_precios_bc3.py tests/test_materiales_espana_auditoria.py tests/test_coste_empresa_espana_auditoria.py tests/test_calculadora.py tests/test_espana.py tests/test_precios_publicos.py
python tools/verificar_matriz_importable.py ES
git diff --check
```

El entorno de esta sesión usó `.venv/bin/python`. Para regeneración existen `tools/generar_matriz_precios_espana.py`, `tools/generar_sql_precios_espana.py` y el generador de precios públicos. No ejecutar SQL ni desplegar silenciosamente: informar del alcance y conservar la trazabilidad de cada corte.
