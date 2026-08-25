# Metodología — precios de referencia nacionales España (EUR) — Revisión 2026-08-25

Extiende a España la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de
   mercado documentado en `docs/INVESTIGACION_PRECIOS_ESPANA.md` (fecha de
   consulta 2026-08-25, revisión mano obra). Cada ancla guarda precio central, mínimo, máximo,
   fuente y confianza `referencia`.

2. **Tasa de corte.** El precio base del catálogo (USD, ámbito VE) se
   normaliza a EUR con la tasa de corte 1 USD = 0,8564 EUR. Solo sirve para
   expresar la base en la moneda local antes de aplicar el factor de mercado;
   el resultado se congela en EUR y no se recalcula en producción.

3. **Canasta derivada.** Para cada categoría (materiales, maquinaria) se
   calcula la mediana del ratio `referencia local / base normalizada` sobre
   todas las anclas `referencia` de la categoría. Los recursos sin ancla
   reciben `base × mediana` (central) y límites con las medianas equivalentes
   de los rangos. Confianza: `derivado`. No es una cotización de tienda:
   localiza el nivel de mercado español sin fingir precios de proveedor.

4. **Mano de obra — coste empresa, no tarifa con beneficio.** Los 17 roles tienen jornal propio (directo o derivado
   del oficial general), normalizado a jornada de 8 h, como en LatAm. **Revisión 2026-08-25:** se usa **coste empresa** (bruto convenio + SS 32,15% + costes fijos EPI/gestor/seguro) como referencia nacional, no tarifa autónomo facturada (22-32 €/h oficial 1ª) que ya incluye beneficio 1,55×. Así el catálogo aplica su propio margen 35% sin doble margen. Fuentes: Convenio General 2024-2026 BOE, tablas Barcelona 2025 BOP 31.290€/año oficial 1ª, Presupix coste empresa 19,80 €/h (27.720€/año/1.400h), Autopromotor coste mensual 3.431,76€ → 20,50 €/h, ObraHub bruto 11,5-13,5 €/h → coste empresa 15,18-17,82 + costes → 20,50. Nuevo: oficial general 21 €/h (18-25) y peón 15 €/h (12-18), especialidades 20-24 €/h.

5. **Salida.** `basedatos_partidas/salida/precios_recursos_espana.csv`
   (generado por `tools/generar_matriz_precios_espana.py`) y carga en
   Supabase con `docs/cargar_precios_referencia_espana_2026-08-25.sql`
   (generado por `tools/generar_sql_precios_espana.py`). La carga sustituye
   únicamente referencias nacionales ES; no toca precios propios de
   organizaciones ni referencias de otros países.
