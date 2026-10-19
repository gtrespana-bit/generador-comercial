# Metodología — precios de referencia nacionales Canadá (CAD) — 2026-10-19

Extiende a Canadá la metodología de `METODOLOGIA_PRECIOS_REFERENCIA_AUSTRALIA.md`, que a su vez
extiende la de Irlanda, el Reino Unido y España. Cambian las fuentes, las cargas y el
tratamiento de impuestos; el contrato de la matriz es idéntico.

1. **Anclas observadas.** Materiales, mano de obra y maquinaria con precio de mercado
   canadiense documentado en `docs/INVESTIGACION_PRECIOS_CANADA.md` (fecha de consulta
   2026-10-19). Cada ancla guarda precio central, mínimo, máximo, fuente y confianza
   `referencia`. En este corte: **52 anclas** (17 mano de obra + 8 maquinaria + 27 materiales).

2. **Tasa de corte.** El precio base del catálogo (USD, **ámbito Venezuela**) se normaliza a CAD
   con la tasa de corte 1 USD = 1,4154 CAD (Banco de Canadá, 16/10/2026). Solo sirve para
   expresar la base en la moneda local antes de aplicar el factor de mercado; el resultado se
   congela en CAD y no se recalcula en producción. Coincide con la sugerencia CAD ya publicada
   en `app/services/tasa.py`.

3. **Impuestos fuera, sin deflactar.** Al contrario que en Australia (retail con GST → ÷1,1),
   en Canadá el precio publicado es «+ taxes»: la cifra de estantería **ya es sin GST/HST** y
   entra tal cual. La dispersión provincial del impuesto (HST 13 % ON, GST 5 % AB…) no contamina
   la matriz porque ningún precio lo incluye.

4. **Canasta derivada por familia.** Para cada **familia** (los dos primeros tramos del código:
   `MT-CONC`, `MT-BLQ`, `MT-PYL`, `MQ-MART`…) se calcula la mediana del ratio
   `referencia canadiense / base normalizada` sobre las anclas `referencia` de esa familia. Los
   recursos sin ancla reciben `base × mediana`. Si la familia no tiene anclas se cae al factor
   de la categoría (materiales 1,822; maquinaria 2,032 en este corte). Confianza `derivado`.

5. **Derivados explícitos, declarados.** Donde no hay observación directa fiable (ladrillo —
   Brampton Brick cotiza por cuenta —, tubería ABS, montantería de acero, silicona, buena
   parte de la maquinaria) se publica un precio explícito por analogía documentada con
   confianza `derivado`, en lugar de fingir una cotización. También donde el factor de familia
   daría un precio sin sentido: las piezas de fontanería no pueden derivar del metro de PEX
   (llave de esfera, latiguillo, sifón llevan precio propio), ni el relleno de celdas del saco
   de grout, ni la madera tratada de pérgola del listón SPF sin tratar. Esos precios **no**
   alimentan los factores por familia.

6. **Maquinaria.** El alquiler canadiense se cotiza por día (8 h), semana o mes. Se publica el
   equivalente horario dividiendo la tarifa de día entre 8. Fuentes: listas públicas de Toronto
   Rental Equipment (2025), guías y marketplaces del GTA (2026) y listas de Ontario de 2022
   actualizadas (éstas, `derivado`). Sin GST/HST ni combustible; con operador solo donde el
   recurso lo declara. El baño portátil se mide por mes, como el recurso.

7. **Mano de obra — coste empresa sobre mediana, no sobre mínimo legal.** Los 17 oficios salen
   del modelo `tools/coste_empresa_canada.py`, no de un factor. Salario: **medianas del Job
   Bank para Ontario** (19/11/2025, referencia 2023-24) elevadas un 5 % a octubre de 2026 —
   porque Canadá no tiene escala legal sectorial (salvo los decretos CCQ de Quebec, fuera del
   perfil) y el procedimiento es el de GB con la ONS —. Cargas: CPP empresa 5,95 % **con
   exención de 3.500 $, techo YMPE 74.600 $ y CPP2 del 4 % hasta 85.000 $**; EI empresa
   2,282 % **con techo de 68.900 $**; WSIB de Ontario **por clase** (G1 residencial 2,18 %;
   G3 estructura 3,55 %; G4 instalaciones 1,54 %; G5 acabados 2,15 %); *vacation pay* 4 %
   (ESA); 4.120 $/año de gastos fijos (beneficios de grupo incluidos). **Employer Health Tax
   excluido** (exención del primer 1 M$ de nómina). Todo dividido por **1.904 h facturables**
   (238 días × 8 h; 1.976 h pagadas con festivos, vacaciones ESA y 3 días de baja no pagados).

   Igual que en ES/GB/IE/AU, se descarta la tarifa del contratista independiente (75-110 $/h)
   porque el catálogo ya aplica un 35 % de margen sobre el coste directo.

   **El rango sí baja, como en el Reino Unido: −10 % / +25 %.** La base es una mediana de
   mercado, no un suelo legal: hay empleo lícito por debajo (provincias atlánticas, rural) y
   por encima (GTA, Alberta, tracción sindical). El «total package» ICI del GTA
   (peón ≈54-61 $/h todo incluido según tablas públicas de LIUNA 527) queda por encima del
   rango: presupuesta el empleador *open-shop* mediano, no el convenio.

8. **Unidades.** La unidad de cada recurso es la de `basedatos_partidas/datos/recursos.json`.
   Canadá es métrico en el precio pero imperial en el formato; conversiones documentadas:
   placa 4×8 ft = 2,97 m²; CMU 390×190 mm (90/140/190); cemento 40 kg/saco; adhesivos 50 lb =
   22,7 kg; áridos $/yd³ × 1,308 → $/m³; aislamiento $/ft² × 10,764 → $/m²; tubo $/ft × 3,281
   → $/m; madera vía $/MBF (2×4 real 38×89 mm, 5,33 bf por pieza de 8 ft). Equivalencias de
   producto: PPR→PEX 1/2", PVC sanitario→ABS DWV 4", *twin & earth*→NMD90 12/2, pasta de
   agarre→Durabond (fraguado químico).

9. **Residuos desde el contenedor, no desde el factor.** El canon se construye desde las
   tarifas públicas de *bin rental* del GTA (14 yd³, 439 $ con 2 t; exceso 120-130 $/t) y, para
   la tierra, del régimen de exceso de suelo de Ontario (O. Reg. 406/19). Sin *levy* tipo NSW:
   es el residuo más barato de los mercados anglófonos estudiados (60 $/m³ frente a 125 A$ en AU).

10. **Salida.** `basedatos_partidas/salida/precios_recursos_canada.csv`, generado por
    `tools/generar_matriz_precios_canada.py`. Mismas 16 columnas y mismo delimitador (`;`) que
    las demás matrices. Verificada contra el importador real con
    `tools/verificar_matriz_importable.py CA` (388/388 aplicables, 0 errores). La carga en base
    de datos sustituirá únicamente referencias nacionales `CA`; no tocará precios propios de
    organizaciones ni referencias de otros países.
