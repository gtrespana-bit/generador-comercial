# España: segundo contraste de maquinaria con Extremadura 2026

**Consulta:** 7 de noviembre de 2026. Se han localizado **23 candidatos**, de los cuales 10 ya tenían un contraste preliminar de Palencia y 13 estaban pendientes. Se mantiene el precio anterior de todos; ninguno se ha confirmado por este contraste.

## Fuente y alcance

La [Junta de Extremadura publica la base 2026](https://www.juntaex.es/w/base-precios-construccion-2026) y enlaza un [archivo BC3](https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923). Se han consultado **fragmentos concretos** del archivo mediante el lector web, que sustituyó algunos caracteres acentuados. Las descripciones se transcribieron con acentos normalizados en [el registro de observaciones](espana_maquinaria_extremadura_2026.csv), que conserva código, precio, unidad, fecha de campo `240426`, enlace y número de fragmento. No se ha descargado el BC3 completo ni calculado su hash, y no se ha comprobado de forma integral si hay descomposiciones o condiciones adicionales en otros registros. La fecha del campo se conserva literalmente, sin atribuirle un significado no verificado.

Los importes son los mostrados por el archivo en euros por hora. Las descripciones consultadas **no aclaran todas las condiciones** de IVA, energía, accesorios, operador, transporte, montaje o duración. No es una muestra nacional ni una cotización en firme. El registro es una selección manual, no el resultado de un cruce masivo completo; cotejar archivo íntegro y condiciones antes de cualquier incorporación masiva o aplicación.

## Diez recursos con antecedentes de dos territorios

| Recurso | Matriz €/h | Palencia €/h | Extremadura €/h | Decisión técnica preliminar |
|---|---:|---:|---:|---|
| Taladro | 2,199013 | 3,11 | 0,84 | Palencia agrupa herramienta eléctrica y Extremadura no indica percusión ni brocas. No promediar. |
| Sierra | 4,251425 | 4,78 | 2,32 | Dos motosierras, pero Palencia no identifica potencia; el recurso también admite sierra circular. Consumibles por aclarar. |
| Vibrador | 4,984430 | 4,42 | 3,02 | En Extremadura es eléctrico de 50 mm; Palencia no especifica motor ni aguja. |
| Mezcladora | 3,00 | 3,10 | 1,91 | Palencia cita 250 l; Extremadura, 160 l gasolina. No se ha definido capacidad equivalente a un saco. |
| Grúa | 70,00 | 51,02 | 50,15 | Hasta 10 t frente a telescópica sobre camión de 20 t; operador no aclarado. |
| Retro con martillo | 45,00 | 36,81 | 40,55 | Minirretro <60 CV frente a minicargadora; alcance del operador y potencia sin verificar. |
| Plancha compactadora | 5,570833 | 7,73 | 3,31 | Bandeja gasolina frente a vibrante de 100 kg; no constan todos los detalles comparables. |
| Compactador de salto | 6,597039 | 5,42 | 3,13 | Pisón gasolina frente a pisón vibrante de 70 kg; faltan condiciones comparables. |
| Bomba de achique | 3,518421 | 10,83 | 3,09 | Grupo hasta 10 CV frente a bomba eléctrica para agua limpia de 5,5 kW; mangueras y alcance distintos o desconocidos. |
| Bomba de hormigón | 78,00 | 125,16 | 212,50 | Las capacidades, condiciones y la interpretación del alcance por volumen no están suficientemente claras. |

Los códigos y las descripciones de Palencia están en [su contraste anterior](ESPANA_MAQUINARIA_PALENCIA_2026.md) y, para mezcladora y retro, en [la revisión inicial](ESPANA_2026-11-06.md). La sola existencia de dos cifras **no demuestra equivalencia**. No se calcula aquí la media aprobada por el usuario porque podría mezclar prestaciones o componentes de coste distintos. Tampoco se suman operadores, energía o impuestos arbitrariamente.

## Trece recursos nuevos en revisión

`MQ-MONTAC`, `MQ-PROYECT-MORT`, `MQ-DESBROZ`, `MQ-INYECTORA`, `MQ-BATID`, `MQ-PULIDORA`, `MQ-HIDROLAV`, `MQ-NIVEL-LASER`, `MQ-OXICORTE`, `MQ-AMOLA`, `MQ-SOLDADORA`, `MQ-ROZAD` y `MQ-PERF-PILOTE`. El CSV detalla cada candidato y las limitaciones. Por ejemplo, la batidora propia exige doble varilla, pero el concepto extremeño no la especifica; la rozadora propia exige dos discos y aspiración, tampoco descritos en la fuente. No se trasladan los valores al producto.

## Siguiente paso

Priorizar el taladro y la maquinaria con mayor propagación; obtener condiciones y otra referencia comparable o desagregar equipos excesivamente genéricos. Conseguir los archivos íntegros de dos territorios sigue pendiente para ejecutar el cruce automatizado real con trazabilidad y verificar posibles descomposiciones. No se ha ejecutado SQL ni modificado producción o precios de clientes.
