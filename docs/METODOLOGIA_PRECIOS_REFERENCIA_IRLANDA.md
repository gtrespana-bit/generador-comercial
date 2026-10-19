# Metodología — precios de referencia nacionales Irlanda (EUR) — 2026-10-18

Extiende a Irlanda la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md`, con las
particularidades que impone el mercado irlandés.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado irlandés
   documentado en `docs/INVESTIGACION_PRECIOS_IRLANDA.md` (consulta 2026-10-18). Cada ancla guarda
   precio central, mínimo, máximo, fuente y confianza `referencia`.

2. **Tasa de corte.** El precio base del catálogo (USD, **ámbito Venezuela**) se normaliza a EUR con
   la tasa de corte 1 USD = 0,8886 EUR (EUR/USD 1,1253, BCE 16/10/2026). Solo sirve para expresar la
   base en moneda local antes del factor de mercado; el resultado se congela en EUR y no se
   recalcula en producción.

3. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código:
   `MT-CONC`, `MT-BLQ`, `MT-PIN`, `MQ-MART`…) se calcula la mediana del ratio
   `referencia irlandesa / base normalizada` sobre las anclas `referencia` de esa familia. Los
   recursos sin ancla reciben `base × mediana` y confianza `derivado`. Si la familia no tiene anclas
   se usa el factor de la categoría.

4. **Contraste con la matriz británica.** Cuando un derivado se separa más del doble del ancla
   británica equivalente (convertida a 1,1846 EUR/GBP), el factor de la familia está midiendo otra
   cosa y se adopta el ancla británica convertida, con la observación explicando el traslado. Es un
   límite de error, no una segunda fuente: la confianza sigue siendo `derivado`.

5. **Mano de obra — coste empresa, no tarifa con beneficio.** Los 17 oficios salen de
   `tools/coste_empresa_irlanda.py`: tarifa del Sectoral Employment Order de la construcción (1 de
   agosto de 2026), PRSI empresa del 11,40 % (desde el 1 de octubre de 2026), pensión del SEO de
   32,89 €/semana, vacaciones de 29 días, bajas estatutarias y previsión de despido de dos semanas
   por año; todo dividido por **1.762,8 horas facturables** (2.028 contratadas − 226,2 de vacaciones
   − 39,0 de bajas). Se descarta la tarifa de autónomo porque el catálogo ya aplica un 35 % de
   margen sobre el coste directo.

6. **IVA.** Los precios de proveedor se publican **sin IVA** (`incluye_iva = no`); la mano de obra y
   la maquinaria con operador llevan `no_aplica`. Irlanda combina el 23 % general con el 13,5 %
   reducido de los servicios de construcción y reforma, de modo que un presupuesto solo puede
   aplicar el tipo correcto si la matriz está limpia de impuesto.

7. **Unidades.** La unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`. Las
   conversiones están documentadas en la investigación: hoja de placa de yeso de 2,93 m², bloque de
   440×215 mm, bobina de cable de 100 m, pieza de madera de 4,8 m.

8. **Salida.** `basedatos_partidas/salida/precios_recursos_irlanda.csv`, generado por
   `tools/generar_matriz_precios_irlanda.py` (388 recursos). La carga se prepara con
   `python3 tools/generar_sql_precios_pais.py IE`, que escribe
   `docs/cargar_precios_referencia_irlanda_2026-10-18.sql` y sustituye únicamente referencias
   nacionales `IE`; no toca precios propios de organizaciones ni referencias de otros países.

9. **Cobertura y honestidad.** Esta primera ronda deja 57 anclas investigadas (15 %). Las 331
   restantes son `derivado` y así se muestran; el apartado 6 de la investigación lista exactamente
   qué falta. No se publica ninguna cifra irlandesa sin fuente y fecha.
