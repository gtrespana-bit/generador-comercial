# Metodología — precios de referencia nacionales Irlanda (EUR) — 2026-10-19

Extiende a Irlanda la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_REINO_UNIDO.md`, que a su
vez extiende la de España. Solo cambian las fuentes, las cargas y los impuestos irlandeses; el
contrato de la matriz es idéntico.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado irlandés
   documentado en `docs/INVESTIGACION_PRECIOS_IRLANDA.md` (fecha de consulta 2026-10-19). Cada
   ancla guarda precio central, mínimo, máximo, fuente y confianza `referencia`.

2. **Tasa de corte.** El precio base del catálogo (USD, **ámbito Venezuela**) se normaliza a EUR
   con la tasa de corte 1 USD = 0,8886 EUR (EUR/USD 1,1253, tipo de referencia del BCE del
   16/10/2026). Solo sirve para expresar la base en la moneda local antes de aplicar el factor de
   mercado; el resultado se congela en EUR y no se recalcula en producción. La base venezolana
   hace que la conversión de divisa sea por sí sola inútil: el factor de mercado es
   imprescindible. La misma tasa actualiza la sugerencia EUR de `app/services/tasa.py`
   (compartida con España).

3. **IVA fuera, siempre con la cifra del comercio.** Irlanda aplica dos tipos a los materiales:
   13,5 % al hormigón y a los bloques, 23 % al resto. Los comercios irlandeses (TJ O'Mahony,
   McMahons, Brooks, Goodwins) publican la pareja con/sin IVA; la matriz toma siempre su cifra
   «ex VAT». Solo en Screwfix IE, que muestra un único precio con IVA, la cifra sin IVA se
   obtiene dividiendo por 1,23, y la observación de cada ancla lo declara. Nunca se aplica un
   tipo único a ciegas: hacerlo sobre el hormigón (13,5 %) infravaloraría el precio neto.

4. **DCPL dentro del precio, una sola vez.** El *Defective Concrete Products Levy* (5 % desde el
   1/09/2023) se devenga en la primera venta del hormigón de vertido y de los bloques, así que ya
   forma parte del precio de lista observado (Hanly Quarries lo declara expresamente). No se suma
   ningún recargo adicional.

5. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código:
   `MT-CONC`, `MT-BLQ`, `MT-PYL`, `MQ-MART`…) se calcula la mediana del ratio
   `referencia irlandesa / base normalizada` sobre las anclas `referencia` de esa familia. Los
   recursos sin ancla reciben `base × mediana`. Si la familia no tiene anclas se cae al factor de
   la categoría (materiales 1,495; maquinaria 1,685 en este corte). Confianza `derivado`.

6. **Anclas por analogía, declaradas.** Irlanda publica menos tarifas que el Reino Unido: el
   hormigón de los grandes productores es «bajo presupuesto» y parte de la maquinaria especialista
   no tiene lista pública. Donde falta la observación directa se publica un precio explícito por
   analogía documentada (p. ej. bomba de hormigón por jornada de equipo, XPS acotado por el PIR
   observado) con confianza `derivado`, en lugar de fingir una cotización. Esos precios no
   alimentan los factores por familia.

7. **Maquinaria.** El alquiler irlandés se cotiza por día (8 h) o por semana, no por hora. Se
   publica el equivalente horario dividiendo la tarifa de día entre 8. Fuente principal: lista
   pública sin IVA de Mr Hire, contrastada con Laois Hire y guías DCM/Kerwin. Sin IVA ni
   combustible; con operador solo donde el recurso lo declara (bomba de hormigón, grúa,
   perforadora, volqueta). El baño portátil se mide por mes, como en el recurso.

8. **Mano de obra — coste empresa, no tarifa con beneficio.** Los 17 oficios salen del modelo
   `tools/coste_empresa_irlanda.py`, no de un factor. Salario: mínimos del *Construction Sector
   SEO* desde el 1/08/2026 (craftsperson 23,74 €/h; categoría A 23,03; categoría B 21,37) para la
   obra general; escala pactada AECI del 16/02/2026 para electricistas (3.er año: 27,60 €/h) y
   escala Connect del sector mecánico desde el 1/05/2026 para fontaneros, soldadores y
   climatización (3.er año: 29,12 €/h), porque los SEO eléctrico y mecánico fueron anulados y no
   hay orden en vigor en esos sectores. Cargas: PRSI empresa 11,40 % (desde el 1/10/2026, sin
   techo; todos los oficios superan el umbral de 552 €/semana de la tasa reducida), CWPS
   36,43 €/semana (pensión, muerte en servicio y enfermedad, desde el 3/08/2026), seguro, EPI,
   formación (Safe Pass/CSCS), gestoría y previsión de *redundancy* (1 semana al tope legal de
   600 €/año). Todo dividido por **1.747,2 horas facturables al año** (2.028 contratadas − 241,8
   de vacaciones y festivos − 39 de bajas).

   Igual que en España y el Reino Unido, se descarta la tarifa de autónomo (50-100 €/h en
   Irlanda) porque el catálogo ya aplica un 35 % de margen sobre el coste directo y eso
   produciría margen sobre margen.

   **El rango no baja como en el Reino Unido.** Allí la base (mediana ONS) queda sobre el
   convenio y el mínimo puede caer un 10 %. Aquí la base es el mínimo legal o pactado, nacional
   y sin rebaja regional posible: el rango es −3 % (estructura de gastos) / +20 % (Dublín y pagas
   por encima del SEO).

9. **Unidades.** La unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`.
   Conversiones documentadas en la investigación: densidades de áridos (arena 1,5 t/m³, piedra
   triturada 1,5 t/m³, Clause 804 compactado 2,1 t/m³, tierra 1,6 t/m³) y formatos irlandeses
   (hoja de yeso laminado de 2,88-2,93 m², bloque de 440×215 mm, panel de malla de 4,8×2,4 m).

10. **Salida.** `basedatos_partidas/salida/precios_recursos_irlanda.csv`, generado por
    `tools/generar_matriz_precios_irlanda.py`. Mismas 16 columnas y mismo delimitador (`;`) que
    las matrices de España y el Reino Unido. Verificada contra el importador real con
    `tools/verificar_matriz_importable.py IE` (388/388 aplicables, 0 errores). La carga en base
    de datos sustituirá únicamente referencias nacionales `IE`; no tocará precios propios de
    organizaciones ni referencias de otros países.
