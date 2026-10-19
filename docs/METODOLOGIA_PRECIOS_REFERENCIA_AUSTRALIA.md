# Metodología — precios de referencia nacionales Australia (AUD) — 2026-10-19

Extiende a Australia la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md`, que a su vez
extiende la del Reino Unido y la de España. Solo cambian las fuentes, las cargas y los impuestos
australianos; el contrato de la matriz es idéntico.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado australiano
   documentado en `docs/INVESTIGACION_PRECIOS_AUSTRALIA.md` (fecha de consulta 2026-10-19). Cada
   ancla guarda precio central, mínimo, máximo, fuente y confianza `referencia`. En este corte:
   **56 anclas** (17 mano de obra + maquinaria con lista pública + materiales observados).

2. **Tasa de corte.** El precio base del catálogo (USD, **ámbito Venezuela**) se normaliza a AUD
   con la tasa de corte 1 USD = 1,4395 AUD (AUD/USD 0,6947, tipo del Banco de la Reserva de
   Australia del 16/10/2026). Solo sirve para expresar la base en la moneda local antes de
   aplicar el factor de mercado; el resultado se congela en AUD y no se recalcula en
   producción. Coincide con la sugerencia AUD ya publicada en `app/services/tasa.py`.

3. **GST fuera.** Australia tiene un único tipo (10 %). Las fuentes *retail* (Bunnings) publican
   con GST y se dividen entre 1,1; las *trade* que desglosan (Sydney Building Materials, ARC) se
   copian en su cifra «ex GST». La observación de cada ancla declara el tratamiento.

4. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código:
   `MT-CONC`, `MT-BLQ`, `MT-PYL`, `MQ-MART`…) se calcula la mediana del ratio
   `referencia australiana / base normalizada` sobre las anclas `referencia` de esa familia. Los
   recursos sin ancla reciben `base × mediana`. Si la familia no tiene anclas se cae al factor de
   la categoría (materiales 2,110; maquinaria 1,781 en este corte —más altos que en IE porque la
   base VE queda más lejos del nivel australiano—). Confianza `derivado`.

5. **Derivados explícitos, declarados.** Australia publica aún menos que Irlanda: el canal
   profesional (Cooper y cuentas ABN) y las grandes empresas de alquiler (Coates, Kennards) no
   dan listas. Donde falta la observación directa se publica un precio explícito por analogía
   documentada (excavadora por clase de peso, core fill como premezclado bombeable, PEX como
   equivalente del PPR que en AU apenas se vende) con confianza `derivado`, en lugar de fingir
   una cotización. Esos precios **no** alimentan los factores por familia.

6. **Residuos desde el *levy*, no desde el factor.** El canon no deriva de la base venezolana:
   se construye desde el *NSW waste levy* metropolitano (180,20 $/t en 2026-27) y el precio de
   skip en Sydney (6 m³ a 845-911 $ con GST). La familia `MT-CANON` tendría un factor ≈25 si se
   dejara al algoritmo: por eso tanto el escombro general como la tierra llevan precio explícito.

7. **Maquinaria.** El alquiler australiano se cotiza por día (8 h) o por semana. Se publica el
   equivalente horario dividiendo la tarifa de día entre 8. Fuentes: listas públicas de Elimbah
   Hire, Perth Hills Tool Hire y STK, y guías iseekplant/goingrate. Sin GST ni combustible; con
   operador solo donde el recurso lo declara. El baño portátil se mide por mes, como el recurso.

8. **Mano de obra — coste empresa, no tarifa con beneficio.** Los 17 oficios salen del modelo
   `tools/coste_empresa_australia.py`, no de un factor. Salario: *Modern Awards* de la Fair Work
   Commission desde el 1/7/2026 — Building and Construction [MA000020] para obra general (CW3
   1.119,10 $/semana + *industry allowance* 67,15 + *tool allowance* por oficio), Electrical
   [MA000025] grado 5 (31,13 $/h) y Plumbing [MA000036] L1 (31,63 $/h). Contratación *weekly
   hire*, 38 h/semana. Cargas: superannuation guarantee 12 % (desde el 1/7/2025), workers
   compensation NSW «House Construction» 4,95 % (icare WIC 411100, incluido el 0,11 % de
   enfermedades por polvo), devengo de *long service leave* 1,7 %, *leave loading* 17,5 %
   sobre las vacaciones, *fares & travel* 22,41 $/día y 2.230 $/año de gastos fijos. **Payroll
   tax excluido** (umbral NSW 1,2 M$: no aplica al perfil pyme y varía por estado); el *levy*
   de LSL de NSW (0,35 %) grava el proyecto, no la nómina, y tampoco entra. Todo dividido por
   **1.688 h facturables al año** (211 días trabajados × 8 h; 1.976 h pagadas con vacaciones,
   festivos, bajas y 13 RDO).

   Igual que en ES/GB/IE, se descarta la tarifa del *sole trader* (80-120 $/h) porque el catálogo
   ya aplica un 35 % de margen sobre el coste directo y eso produciría margen sobre margen.

   **El rango no baja como en el Reino Unido.** La base es el mínimo legal del award, nacional y
   sin rebaja regional posible: el rango es **−3 % / +20 %** (estructura de gastos / acuerdos
   EBA, *daily hire*, capitales caras y payroll tax donde aplique), igual que en Irlanda.

9. **Unidades.** La unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`.
   Conversiones documentadas: densidades de áridos (arena 1,5 t/m³, piedra 1,5 t/m³, *road base*
   compactado 2,1 t/m³), formatos australianos (hoja Gyprock 2400×1200 mm, bloque Besser
   390×190 mm, malla 6×2,4 m, saco de cemento de 20 kg) y equivalencias de producto (PPR→PEX,
   *base coat* CSR→pasta de juntas, *cornice cement*→pasta de agarre).

10. **Salida.** `basedatos_partidas/salida/precios_recursos_australia.csv`, generado por
    `tools/generar_matriz_precios_australia.py`. Mismas 16 columnas y mismo delimitador (`;`)
    que las matrices de España, Reino Unido e Irlanda. Verificada contra el importador real con
    `tools/verificar_matriz_importable.py AU` (388/388 aplicables, 0 errores). La carga en base
    de datos sustituirá únicamente referencias nacionales `AU`; no tocará precios propios de
    organizaciones ni referencias de otros países.
