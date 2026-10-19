# Metodología — precios de referencia nacionales de Estados Unidos (USD) — 2026-10-19

Extiende a Estados Unidos la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_CANADA.md`, que a su
vez extiende la de Australia, Irlanda, el Reino Unido y España. Cambian las fuentes, las
cargas y el tratamiento de unidades; el contrato de la matriz es idéntico. El contexto de
mercado (sistema imperial, impuesto por estado) y las decisiones de producto están en
`docs/ANALISIS_MERCADO_ESTADOS_UNIDOS.md`: esta matriz es su **Fase 0** (precios); la capa
de cantidades imperiales en la interfaz y el motor fiscal por estado son fases posteriores
aprobadas, no parte de este corte.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado de
   Estados Unidos documentado en `docs/INVESTIGACION_PRECIOS_ESTADOS_UNIDOS.md` (fecha de
   consulta 2026-10-19). Cada ancla guarda precio central, mínimo, máximo, fuente y confianza
   `referencia`. En este corte: **52 anclas** (17 mano de obra + 8 maquinaria + 27 materiales).

2. **Tasa de corte 1,0 — y por qué eso no es una conversión.** El precio base del catálogo ya
   está en USD (**ámbito Venezuela**), así que no hay divisa que convertir: el factor de
   familia es directamente `precio EE. UU. / precio base VE` en la misma moneda. La trampa
   que hay que evitar es la inversa — asumir que compartir moneda hace comparables los
   precios venezolanos con los estadounidenses —: por eso existen las anclas.

3. **Impuestos fuera, sin deflactar.** El precio publicado en EE. UU. es siempre **antes
   de «sales tax»** (estantería, listas de planta, alquileres): la cifra observada ya es
   ex-impuesto y entra tal cual, como en Canadá. Que el impuesto se añada en caja y varíe
   por estado/condado/ciudad no contamina la matriz porque ningún precio lo incluye. En la
   mayoría de los estados, además, el contratista soporta ese impuesto al comprar los
   materiales y no lo repercute al cliente (marcos documentados en el análisis): el precio
   de referencia ex-impuesto es el comparable con el resto de matrices y el motor de
   márgenes trabaja igual.

4. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código)
   se calcula la mediana del ratio `referencia EE. UU. / base` sobre las anclas de esa familia.
   Los recursos sin ancla reciben `base × mediana`. Si la familia no tiene anclas se cae al
   factor de la categoría (**materiales 1,841; maquinaria 2,174** en este corte). Confianza
   `derivado`.

5. **Derivados explícitos, declarados.** Donde no hay observación directa fiable se publica un
   precio explícito por analogía documentada con confianza `derivado`, en lugar de fingir una
   cotización. También donde el factor de familia daría un precio sin sentido: la llave de
   esfera, el latiguillo o el sifón no pueden derivar del pie de PEX; el relleno de celdas no
   puede derivar del saco de grout (es hormigón fino de planta); la madera tratada de pérgola
   no deriva del «stud» SPF sin tratar. Esos precios **no** alimentan los factores por familia.

6. **Maquinaria.** El alquiler se cotiza por día (con mínimo de 4 h en Home Depot Tool Rental),
   semana o mes. Se publica el equivalente horario dividiendo la tarifa de día entre 8.
   Fuentes: tarifas por día de **United Rentals** por metro según guías 2026 (plancha
   compactadora, miniexcavadora), bandas de Home Depot Tool Rental y **listas públicas de
   alquileres independientes** (doitatdukes, Central Tool Rental Cincinnati, Grants Pass
   Rental mar-2026, TC Rentals). Sin «sales tax» ni combustible; con operador solo donde el
   recurso lo declara. El baño portátil se mide por mes, como el recurso.

7. **Mano de obra — coste empresa sobre la mediana nacional BLS.** Los 17 oficios salen del
   modelo `tools/coste_empresa_eeuu.py`, no de un factor. Salario: **medianas nacionales por
   ocupación del programa OEWS del Bureau of Labor Statistics (mayo 2025, publicado el
   15/05/2026)** elevadas un 5 % a octubre de 2026 — EE. UU. no tiene escala legal sectorial y
   el salario mínimo federal (7,25 $/h) no describe al oficial; el procedimiento es el de GB
   con la ONS y el de Canadá con Job Bank —. Cargas: **FICA empresarial** (Seguridad Social
   6,2 % con base máxima 2026 de **184.500 $**, no vinculante a salarios de oficio; Medicare
   1,45 % sin techo); **FUTA neto 0,6 %** sobre 7.000 $ (42 $/año); **SUTA representativo
   2,7 % sobre 10.000 $** (270 $; las bases estatales van de 7.000 a 78.200 $ y la dispersión
   queda en el rango); **workers' compensation por código de clase NCCI** (electricidad
   4,00 $/100 $; fontanería/HVAC 4,25; pintura 4,50; albañilería 6,00; carpintería general
   6,75; estructura 7,75; peonaje 7,00; hormigón 7,50; acero de refuerzo 10,00); 1.620 $/año
   de gastos fijos. Todo dividido por **1.912 h trabajadas** (239 días × 8 h; 2.080 h pagadas
   con 10 días de vacaciones, 8 festivos y 3 de baja pagados dentro).

   **El seguro médico y la jubilación quedan fuera a propósito**: no son obligación federal
   para la pyme (el mandato ACA empieza en 50 equivalentes a tiempo completo), a diferencia
   de la pensión GB/IE o el superannuation AU. El BLS (ECEC) los cifra en ≈4 $/h para el
   empleador de construcción que sí los ofrece: ese empleador se presupuesta hacia el techo
   del rango. Igual que en los demás mercados, se descarta la tarifa del subcontratista
   independiente (1099) porque el catálogo ya aplica un 35 % de margen sobre el coste directo.

   **El rango es el más ancho de los mercados anglófonos: −15 % / +35 %.** La dispersión
   estatal/metro del OEWS es de ±20-40 % por ocupación (HVAC: DC 40,57 $/h frente a Arkansas
   23,13; jardinería: DC 23,46 frente a Misisipi 15,21) y el paquete sindical de las grandes
   metros queda por encima del techo: la referencia presupuesta el empleador *open-shop*
   mediano nacional, y el ajuste por estado/metro se hace con el rango y con el override de
   empresa, no con 50 matrices (el esquema de precios es nacional por mercado, como en AU/CA).

8. **Unidades: imperial en el comercio, métrico en la matriz — y esto es contractual.** La
   unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`. Estados Unidos
   vende en formatos imperiales y la investigación trabaja con ellos, pero **la matriz se
   publica ya convertida a la unidad del recurso** porque la ruta de carga por SQL inserta el
   precio tal cual (la conversión automática de precios imperiales solo existe en el
   importador del panel, como red de seguridad para ficheros del operador; un test de esta
   matriz lo garantiza). Conversiones documentadas en cada ancla: hormigón $/yd³ × 1,30795 →
   $/m³ con mapeo kg/cm² → PSI (180 ≈ 2.500; 210 ≈ 3.000; 250 ≈ 3.500; 300 ≈ 4.000);
   cemento saco de **94 lb (42,64 kg)**; adhesivos de 50 lb (22,68 kg); placa **4×8 ft =
   2,967 m²**; bloque CMU 8×8×16" (390×190 mm reales); áridos $/yd³ × 1,30795 → $/m³;
   aislamiento $/ft² × 10,7639 → $/m²; tubo y cable ¢/ft × 3,2808 → $/m; pintura $/gal US
   ÷ 3,785 → $/l; acero $/t corta → $/kg (0,60 $/lb = 1,32 $/kg); madera vía «stud» 2×4×8 ft
   y $/bf. Equivalencias de producto: PPR → **PEX-B ½"** (el PPR es residual en EE. UU.);
   conductor THW → **THHN de cobre en bobina de 500 ft** (no el cable «Romex» completo);
   adhesivo C1/C2TE → **thinset A118.4 / A118.11 (LFT)**; pasta de agarre → compuesto de
   fraguado (*Easy Sand 90*); tubo de drenaje → ADS corrugado perforado con calcetín.

9. **Residuos desde el contenedor «roll-off», no desde el factor.** El canon se construye
   desde las tarifas públicas de alquiler de contenedor de 20 yd³ (350-680 $, media ≈475,
   con 2-3 t incluidas) y el exceso de tonelaje (60-110 $/t; canon medio de vertido C&D
   ≈66 $/t según EREF 2024): una carga mixta corriente sale a **45 $/m³**. La tierra limpia
   es aquí **más barata** que el RCD mixto (32 $/m³, a menudo solo acarreo), al contrario
   que en Ontario con su régimen de suelo excedente.

10. **Salida.** `basedatos_partidas/salida/precios_recursos_estados_unidos.csv`, generado
    por `tools/generar_matriz_precios_eeuu.py`. Mismas 16 columnas y mismo delimitador (`;`)
    que las demás matrices. Verificada contra el importador real con
    `tools/verificar_matriz_importable.py US` (388/388 aplicables, 0 errores). La carga en
    base de datos sustituirá únicamente referencias nacionales `US`; no tocará precios
    propios de organizaciones ni referencias de otros países.
