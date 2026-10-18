# Metodología — precios de referencia nacionales Reino Unido (GBP) — 2026-10-18

Extiende al Reino Unido la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md`.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado británico
   documentado en `docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md` (fecha de consulta 2026-10-18). Cada
   ancla guarda precio central, mínimo, máximo, fuente y confianza `referencia`.

2. **Tasa de corte.** El precio base del catálogo (USD, **ámbito Venezuela**) se normaliza a GBP con
   la tasa de corte 1 USD = 0,7502 GBP (GBP/USD 1,3330, 16/10/2026). Solo sirve para expresar la
   base en la moneda local antes de aplicar el factor de mercado; el resultado se congela en GBP y
   no se recalcula en producción. La base venezolana hace que la conversión de divisa sea por sí
   sola inútil: el factor de mercado es imprescindible.

3. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código:
   `MT-CONC`, `MT-BLQ`, `MT-PIN`, `MQ-MART`…) se calcula la mediana del ratio
   `referencia británica / base normalizada` sobre las anclas `referencia` de esa familia. Los
   recursos sin ancla reciben `base × mediana`. Confianza `derivado`.

   Esto es una mejora deliberada sobre el generador de España, que calcula un único factor por
   categoría: allí una cámara CCTV heredaba el factor del cemento. Si una familia no tiene ninguna
   ancla se cae al factor de la categoría, y se le da ancla propia a toda familia que mezcle
   productos con estructuras de precio incompatibles (caso del bloque de vidrio frente al bloque de
   hormigón).

4. **Maquinaria.** El alquiler británico se cotiza por día de 8 horas o por semana, no por hora. Se
   publica el equivalente horario dividiendo la tarifa de día entre 8. Las 44 máquinas llevan ancla
   propia. Sin IVA ni combustible salvo indicación; con operador solo donde el recurso lo declara
   (camión grúa, volqueta, bomba de hormigón).

5. **Mano de obra — coste empresa, no tarifa con beneficio.** Los 17 oficios salen del modelo
   `tools/coste_empresa_reino_unido.py`, no de un factor. Salario ONS ASHE de asalariados, con el
   suelo del CIJC Working Rule Agreement; más NI empresa 15 % sobre 5.000 £, pensión 3 %, CITB levy
   0,35 %, seguros, EPI, formación, gestoría y previsión de indemnización; todo dividido por
   **1.751,9 horas facturables al año** (2.028 contratadas − 241,8 de vacaciones − 34,3 de bajas).

   Igual que en la revisión española de agosto de 2026, se descarta la tarifa de autónomo porque el
   catálogo ya aplica un 35 % de margen sobre el coste directo y eso produciría margen sobre margen.

6. **Unidades.** La unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`. Las
   conversiones necesarias están documentadas en la investigación: densidades de áridos (arena
   1,5 t/m³, árido triturado 1,5 t/m³, zahorra 2,1 t/m³, cascote de hormigón 2,2 t/m³, tierra
   1,5 t/m³) y formatos británicos (hoja de yeso laminado de 2,88 m², bloque de 440×215 mm).

7. **Salida.** `basedatos_partidas/salida/precios_recursos_reino_unido.csv`, generado por
   `tools/generar_matriz_precios_reino_unido.py`. Mismas 16 columnas y mismo delimitador (`;`) que
   la matriz de España. La carga en base de datos sustituirá únicamente referencias nacionales `GB`;
   no tocará precios propios de organizaciones ni referencias de otros países.
