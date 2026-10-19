# Investigación de precios de referencia — Estados Unidos (2026-10-19)

> Registro de evidencia de la matriz `precios_recursos_estados_unidos.csv`
> (Fase 0 del mercado según `docs/ANALISIS_MERCADO_ESTADOS_UNIDOS.md`).
> Todas las consultas: **19/10/2026**. Precios **sin «sales tax»** (en
> EE. UU. el precio publicado es antes de impuestos), tal como se
> observan; la mano de obra a **coste empresa** (`tools/coste_empresa_eeuu.py`).

## 1. La advertencia que ordena todo lo demás

Estados Unidos es el único mercado **imperial** del producto, y eso
afecta a la investigación en dos sentidos distintos que no deben
confundirse:

- **Formal**: el comercio vende por yarda cúbica, pie cuadrado, galón
  US y libra. Cada ancla se investiga en su formato nativo y se
  convierte a la unidad métrica del recurso dejando la conversión
  citada — el mismo procedimiento que Canadá —, porque la carga por
  SQL inserta el precio tal cual y una matriz en $/yd³ corrompería los
  precios (ver metodología §8).
- **De fondo**: no existe «el» precio estadounidense. Los salarios
  OEWS varían ±20-40 % entre estados y metros, el hormigón cotiza por
  planta y zona, y Home Depot precia por tienda (el mismo saco de
  cemento aparece a 17,21 $ en una metro y a 20,49 $ en otra). La
  matriz publica la **mediana nacional** salarial y puntos medios de
  listas nacionales, con rangos que admiten esa dispersión (mano de
  obra −15 %/+35 %). Publicar, por ejemplo, una referencia «Nueva
  York» o «Texas» sería más precisa y menos útil: el esquema de
  precios del producto es nacional por mercado (como Ontario para CA
  o NSW para AU), y el ajuste fino se hace con el rango y el override
  de empresa.

La advertencia mala sería la contraria: dejarse engañar porque base y
destino comparten moneda. Que el catálogo venezolano esté en USD no
acerca sus precios a los estadounidenses ni un milímetro (factor de
materiales resultante: 1,841).

## 2. Criterio de mano de obra: coste empresa, no tarifa de autónomo

El catálogo aplica un 35 % de margen sobre el coste directo; si el
recurso de mano de obra fuera la tarifa facturada de un subcontratista
(1099 o «labor rate» de un GC, que incluye su propio beneficio,
seguro y vehículo), habría margen sobre margen. El recurso es el
**coste empresa por hora trabajada** del empleador que contrata (W-2),
como en ES/GB/IE/AU/CA.

### 2.1 El mapa salarial: medianas OEWS del BLS (mayo 2025)

EE. UU. no tiene escala legal sectorial: el salario mínimo federal lleva
en 7,25 $/h desde 2009 y ni los mínimos estatales describen el coste de
un oficial. La base publicable es la encuesta oficial **OEWS** (Bureau
of Labor Statistics, mayo 2025, publicada el 15/05/2026; registros de
nómina, tiempo ordinario, sin beneficios ni horas extra). Medianas
nacionales adoptadas ($/h; entre paréntesis el código SOC):

| Ocupación OEWS | Mediana | Recurso |
| --- | ---: | --- |
| Plumbers, pipefitters & steamfitters (47-2152) | 30,67 | MO-OF1-PLO |
| Electricians (47-2111) | 30,38 | MO-OF1-ELE |
| Brickmasons & blockmasons (47-2021) | 29,87 | MO-OF1-ALB |
| HVAC mechanics & installers (49-9021) | 29,33 | MO-OF1-AC |
| Carpenters (47-2031) | 29,12 | MO-OF1 / MO-OF1-CARP |
| Drywall installers & tapers (47-2081+2082) | 28,74 | MO-OF1-MON |
| Reinforcing iron & rebar workers (47-2171) | 28,35 | MO-OF1-CAB |
| Floor layers (47-2042) | 27,15 | MO-OF1-PISO |
| Tile & stone setters (47-2044) | 26,77 | MO-OF1-ALI |
| Glaziers (47-2121) | 27,44 | MO-OF1-VIDR |
| Welders, cutters & brazers (51-4121) | 25,84 | MO-OF1-SOLD |
| Painters, construction & maintenance (47-2141) | 23,75 | MO-OF1-PIN |
| Construction laborers (47-2061) | 22,66 (media 25,02) | MO-AYU (MO-AYU-ESP = media) |
| Cabinetmakers & bench carpenters (51-7011) | 22,44 | MO-OF1-CARPM |
| Landscaping & groundskeeping (37-3011) | 18,82 | MO-OF1-JARD @ 20,50 adoptado |

Las medianas se elevan un 5 % a octubre de 2026 (mayo 2025 + 17 meses
al ritmo del ECI de construcción). Notas:

- **Mediana, no media**: la media OEWS va un 10-13 % por encima por la
  tracción sindical y de las metros caras; la mediana es el empleador
  intermedio, el mismo criterio que la ONS en GB y Job Bank en CA.
  La única excepción es el «ayudante especializado», que se aproxima
  con la **media** del peón (el peón experimentado dentro de su
  propia distribución).
- **El cabillero tiene ocupación propia** (47-2171, mediana 28,35),
  así que no hace falta el ratio 0,87 que necesitó Canadá. Su
  percentil 75 (37,17) y las metros sindicales (medias estatales de
  89-112 mil $/año en NJ/IL/WI/NY) muestran la dispersión que cubre
  el rango.
- **Jardinería**: la mediana de 37-3011 es de mantenimiento; el
  oficial de paisajismo de obra se adopta a 20,50 $/h corrientes.
- **Contexto sindical/«prevailing wage»**: los salarios Davis-Bacon y
  los paquetes de convenio en metros grandes quedan 30-80 % por
  encima (p. ej., medias de rodworkers en NJ +70 % sobre la nacional).
  Como en AU (award frente a EBA) y CA (open-shop frente a ICI), la
  referencia es el mercado abierto mediano y así se declara.

### 2.2 De salario a coste empresa

Cargas 2026 (SSA 24/10/2025; IRS Publication 15; guías de tarifas de
workers' compensation 2026):

- **FICA empresarial**: Seguridad Social 6,2 % hasta la base de
  **184.500 $** (máximo 11.439 $/parte — ningún oficio de la matriz la
  alcanza: el bruto mayor es ≈67.000 $) + Medicare 1,45 % sin techo.
- **FUTA**: 6,0 % sobre los primeros 7.000 $ con crédito del 5,4 % →
  **0,6 % neto = 42 $/año**.
- **SUTA**: adoptado **2,7 % sobre 10.000 $** (270 $) como nuevo
  empleador representativo. La realidad estatal va de tipos del ~1 %
  a la construcción de nueva creación en Pensilvania al 10,5924 %
  (2026); es una partida pequeña en el total y la dispersión queda en
  el rango.
- **Workers' compensation por clase NCCI** ($/100 $ de nómina, puntos
  medios de los rangos nacionales publicados en 2026 — Florida 2026
  tras la bajada NCCI del 6,9 %, Texas en el suelo, NY/CA en el
  techo): electricidad (5190) 4,00; fontanería/HVAC (5183) 4,25;
  pintura (5474) 4,50; revestimientos 4,50; ebanistería instalada
  (5437) 4,90; drywall (5445) 5,00; jardinería (9102) 5,00; vidriería
  (5462) 5,25; soldadura 5,50; albañilería (5022) 6,00 (FL 5,22 ·
  WI 6,36 · NY 13,17 loss cost); carpintería general (5651) 6,75;
  peonaje 7,00; hormigón (5213) 7,50; carpintería de estructura
  (5403/5645) 7,75; acero de refuerzo (banda 5059/5102) 10,00. Es,
  con diferencia, la carga que ordena los oficios tras el salario.
- **Divisor**: 2.080 h pagadas (el PTO se paga dentro: 10 días de
  vacaciones + 8 festivos + 3 de baja) ÷ **1.912 h trabajadas** (239
  días). Es el divisor menos duro junto al de Canadá (1.904): EE. UU.
  no garantiza vacaciones por ley federal y el coste del permiso
  pagado en construcción que mide el BLS es coherente con ~168 h.
- **Fuera, declarado**: seguro médico y jubilación (no obligatorios
  para <50 FTE; BLS ECEC ≈4 $/h en construcción para quien los
  ofrece → techo del rango), horas extra (la OEWS es tiempo
  ordinario) y bonos de producción.

### 2.3 Resultado

Coste empresa por hora trabajada (extracto): fontanero 40,21;
electricista 39,76; albañil 39,78; encofrador 39,40; cabillero 39,11;
oficial general (carpintero) **39,07**; climatización 38,50;
montador de drywall 38,00; vidriero 36,39; colocador de pisos 35,79;
enchapador 35,31; soldador 34,41; ayudante especializado 33,78;
pintor 31,44; peón **30,68**; ebanista 29,86; jardinero 26,13.
Recargos sobre salario entre el 14,6 % (electricista) y el 20,8 %
(cabillero): el spread lo pone el workers' compensation.

## 3. Maquinaria

El alquiler estadounidense se mueve entre las cadenas (United Rentals,
Sunbelt) con tarifas por metro y los independientes con lista pública.
Tarifas adoptadas (día de 8 h, sin impuesto ni combustible):

- **Plancha compactadora**: UR entre 95 y 115 $/día según metro 2026 →
  105 adoptado.
- **Miniexcavadora (≈3,5-5 t)**: UR 280 $/día (Austin, pequeña),
  395 (Raleigh), 420 (Nueva York) → 395 + martillo hidráulico ≈80 =
  **475** para MQ-RETRO (el operador va en la MO de la partida).
- **Martillo demoledor eléctrico**: 40-70 $/día (guías 2026) y 85 $/día
  en lista pública (doitatdukes) → 65.
- **Hidrolavadora**: Home Depot 60 $/día (45/4 h); listas públicas 65
  (2.400 psi) → 65.
- **Sierra húmeda**: banda Home Depot Tool Rental 55-60 $/día → 58.
- **Motosierra**: listas públicas 2026 — 16" a 65 $/día, 20" a
  70-100 $/día → 75.
- **Bomba de achique**: sumergible eléctrica 2" 30-35 $/día; «trash
  pump» 2" gasolina 40-56 $/día (Grants Pass mar-2026: 40; Central
  Tool Cincinnati: 45) → 45.
- **Amoladora**: banda de herramienta pequeña 20-45 $/día → 30.
- El resto (36 referencias) es `derivado` explícito por analogía de
  banda (p. ej., bomba de hormigón y grúa con operador por jornada
  estimada), sin fingir tarifa pública donde el mercado cotiza por
  cuenta. Home Depot fija precios por tienda y UR por cuenta: las
  bandas adoptadas son las publicadas, y el precio negociado de
  cuenta queda en la parte baja del rango.

## 4. Materiales

Estantería nacional (Home Depot / Lowe's, oct-2026) y listas
publicadas; todo ex-«sales tax»:

- **Hormigón preparado** por clase PSI (mapeo kg/cm²→PSI en la
  metodología): listas publicadas — Supreme Concrete (New York, sep-2026)
  3.000 PSI 127,05 $/yd³ · 4.000 132,00 · 5.000 137,50; Gehring
  Construction (Columbus Nebraska, lista 01/01/2026) «6-bag» 3.000 PSI
  148 (menú 140-164); American Concrete (Augusta Georgia, abr-2026) 3.000
  174 · 4.000 182; media de productores NRMCA (2023) 160 $/yd³.
  Adoptados (planta/zona corta, sin recargo de carga corta):
  2.500 PSI 145 → **189,65 $/m³**; 3.000 PSI 152 → **198,81**;
  3.500 PSI 160 → **209,27**; 4.000 PSI 168 → **219,74**.
- **Cemento Portland 94 lb**: 17,21-20,49 $ según metro (18,44-19,77
  corriente) → 19,00 adoptado = **0,446 $/kg**. Ojo con los sacos de
  «concrete mix» de 60/80 lb (premezcla, no cemento), el mismo error
  que en Canadá con Sakrete 30 kg.
- **Bloque CMU 8×8×16"**: 1,85-2,85 $ (2,38 corriente; guías 2026:
  1,90-2,60) → **2,40**; 6" y 4" por escalado `derivado`.
- **Acero de refuerzo**: «spot» doméstico #4 de 870-970 $/t corta
  (Kallanish, ene-oct 2026; IndexBox 09/10/2026: 1.033 $/t EXW);
  suministro al contratista en largos comerciales 1.100-1.450 $/t →
  **1.200 $/t corta = 1,32 $/kg** (la barra suelta de estantería
  llega a ≈0,94 $/lb y queda en el rango).
- **Malla electrosoldada**: hoja «remesh» 42"×84" a 10,87-19,98 $ →
  **5,50 $/m²**.
- **Áridos a granel recogidos**: arena de construcción/mampostería
  30-45 $/yd³ → 40 (**52,32 $/m³**); piedra ¾" (#57) 35-65 $/yd³
  (35-58 $/t) → 50 (**65,40**); granular de base («crusher run») →
  38 $/yd³ (**49,70**). El porte añade típicamente 10-25 $/t y queda
  fuera (`incluye_transporte = no_confirmado`).
- **Placa de yeso ½" 4×8 ft**: USG UltraLight 12,98-16,68 $
  (volumen ≥34: 10,64-14,18) → 15,00 = **5,05 $/m²**; la
  antimoho a 19,98-24,58 alimenta la RH `derivada`.
- **Pasta de juntas**: USG Plus 3, cubo 4,5 gal (17,0 l ≈ 21,8 kg)
  22,45-24,50 $ → **1,08 $/kg**; fraguado Easy Sand 90 18 lb ≈14 $ →
  **1,71**.
- **Adhesivos y juntas** (Custom Building Products, sacos de 50 lb):
  VersaBond 14,97 $ → **0,66 $/kg** (C1); VersaBond-LFT 19,97-21,97 →
  **0,92** (C2TE); Polyblend Plus 25 lb ≈16 $ → **1,41** (CG2).
- **Autonivelante**: Quikrete Fast-Setting 50 lb 41,99-45,79 $ →
  **1,94 $/kg**. **Grout sin retracción**: Quikrete 1585 50 lb
  22,97 $ → **1,01**.
- **Pintura**: ProMar 200 (Sherwin-Williams) 28-36 $/gal con cuenta
  profesional y lista 40-50 (contrato institucional 2025-26:
  26-29); adoptado 40 $/gal → **10,57 $/l**; el resto de la familia
  por escalado `derivado`.
- **Aislamiento**: ROCKWOOL Safe'n'Sound 3" a **1,40 $/ft² → 15,07
  $/m²** (el recurso es de 60 mm; el mercado vende 3"); panel rígido
  tipo ComfortBoard 2,00-2,80 $/ft² → **25,83 $/m²**.
- **Fontanería**: PEX-B ½" rollo de 100 ft 27,97-33,30 $ (28-33 ¢/ft)
  → **1,08 $/m** como equivalente del PPR20 (el PPR es residual);
  válvula de esfera, latiguillo y sifón con precio explícito propio
  (8/7/12 $) porque el factor del tubo daría valores imposibles.
- **Electricidad**: THHN cobre 12 AWG en bobina de 500 ft a
  150-155 $ (30 ¢/ft) → **1,00 $/m**; el rollo de 100 ft cotiza a
  82-88 ¢/ft (recargo de menudeo, fuera de la referencia).
- **Drenaje**: ADS corrugado perforado 4" con calcetín, rollo de
  100 ft 129-207 $ → **5,09 $/m**.
- **Madera**: «stud» 2×4×8 ft ≈3,90 $ (banda 3,25-4,50) → **1,60 $/m**;
  estructura a ≈1,25 $/bf → 560 $/m³ `derivado`. Es el precio más
  volátil de la matriz y el primero a revisar en actualizaciones.
- **Residuos**: «roll-off» de 20 yd³ a 350-680 $ (media ≈475, 2-3 t
  incluidas), exceso 60-110 $/t y canon C&D medio ≈66 $/t (EREF
  2024) → **45 $/m³** mezclado; tierra limpia 32 (en EE. UU. el
  relleno limpio es barato: lo contrario que en Ontario).

## 5. Divisa, impuestos y unidades

- **Divisa**: ninguna conversión (base VE en USD). El factor de
  familia resultante mide nivel de precios, no tipo de cambio.
- **Impuestos**: matriz ex-«sales tax». El tipo combinado estatal+local
  medio 2026 es 7,53 % (Tax Foundation), de 0 % (OR/NH/MT/DE) a
  10,13 % (Luisiana) — pero ningún precio de la canasta lo incluye,
  así que la dispersión fiscal no contamina las anclas. El
  tratamiento del impuesto en los documentos (quién lo soporta, sobre
  qué base) es materia de la Fase 2 fiscal, no de esta matriz.
- **Unidades**: conversiones imperial→métrico en la observación de
  cada ancla (1 yd³ = 0,764555 m³; 1 ft² = 0,092903 m²; 1 gal US =
  3,785412 l — el galón imperial británico, 4,546 l, no se usa en
  EE. UU. —; 1 lb = 0,453592 kg; 1 t corta = 907,185 kg). La matriz
  se publica en la unidad del recurso porque la carga por SQL no
  convierte (el importador del panel sí, y queda como red de
  seguridad para ficheros del operador en unidades imperiales).

## 6. Limitaciones

1. **Mediana nacional**: quien presupueste en Nueva York, Boston, San Francisco o
   con convenio sindical debe trabajar en el tercio alto del rango o
   con override; quien lo haga en el sur/interior rural, en el bajo.
   No hay matrices por estado (decisión y alternativa en el análisis).
2. **Estantería frente a cuenta profesional**: Home Depot/Lowe's es
   retail transparente; el contratista con cuenta en distribuidor
   (Ferguson, White Cap, ABC Supply) paga menos en instalaciones y
   acero, y las plantas cotizan el hormigón por proyecto. El precio
   de referencia es el de mercado observado sin cuenta, coherente con
   IE/AU/CA.
3. **Madera y acero son índices vivos**: «stud» y rebar deben
   revisarse en cada actualización (ambos subieron a lo largo de 2026
   con los anuncios de molino de +30 $/t).
4. **El SUTA y el workers' comp reales son por empresa y estado**: el
   modelo usa representativos nacionales deliberados; una póliza de
   California o Nueva York puede duplicar la clase adoptada.
5. **Cantidades en la interfaz**: esta fase alimenta precios; la
   entrada/visualización en pies y pulgadas es la Fase 1 aprobada y
   aún no está en el producto (la landing se ha corregido en este
   mismo corte para no afirmarla).

## Fuentes (consultadas el 19-10-2026)

- BLS OEWS mayo 2025 (publicado 15/05/2026) y Occupational Outlook
  Handbook: medianas nacionales por ocupación; espejos por ocupación
  (simplywise, jobbls) para ocupaciones sin página OOH.
- SSA (24/10/2025) e IRS Pub. 15 (2026): base de la Seguridad Social
  184.500 $, FICA 7,65 %, FUTA 0,6 % neto sobre 7.000 $.
- Guías de tarifas de workers' compensation 2026 por código de clase
  NCCI (tarifas presentadas en Florida/Texas/California/Wisconsin/NY).
- Listas de hormigón: Supreme Concrete (sep-2026), Gehring
  Construction (01/01/2026), American Concrete Augusta (abr-2026);
  media NRMCA 2023 (Benchmarking Survey).
- Home Depot y Lowe's (estantería nacional, oct-2026): cemento 94 lb,
  CMU, placa de yeso, pastas, adhesivos, PEX, THHN, drenaje ADS,
  aislamiento ROCKWOOL, Quikrete/Custom Building Products/USG.
- Mercado siderúrgico: Kallanish (ene/oct-2026), IndexBox (09/10/2026),
  builderscount (precios de barra, oct-2026).
- Alquiler: tarifas United Rentals por metro según guías 2026
  (countbricks y agregadores), Home Depot Tool Rental, listas
  públicas (doitatdukes, Central Tool Rental Cincinnati, Grants Pass
  Rental mar-2026, TC Rentals).
- Áridos: guías nacionales 2026 y tarifas de cantera publicadas
  (State Crushing, Harbor Soils, Grillo, Groundhog).
- Residuos: guías nacionales de «roll-off» 2026 (Dumpsters.com,
  dumpsterrentalguide, usecalcpro) y canon medio C&D EREF 2024.
- Tax Foundation, «State and Local Sales Tax Rates, Midyear 2026»
  (contexto impositivo de §5).
