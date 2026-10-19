# Investigación de precios de referencia — Canadá (2026-10-19)

Estudio de mercado que sustenta la matriz nacional
`basedatos_partidas/salida/precios_recursos_canada.csv` (388 recursos, CAD, sin GST/HST).
Metodología en `docs/METODOLOGIA_PRECIOS_REFERENCIA_CANADA.md`; modelo de coste empresa en
`tools/coste_empresa_canada.py`; generador en `tools/generar_matriz_precios_canada.py`.

Cuarto estudio de la secuencia de mercados angloparlantes (GB → IE → AU → **CA** → US,
`docs/HOJA_DE_RUTA_MERCADOS_INGLESES.md`). Perfil provincial: **Ontario** (ver §6).

## 1. La advertencia que ordena todo lo demás

Canadá es el caso **inverso** a Australia en transparencia, y el inverso a Irlanda/Australia
en salarios:

- **El retail publica con precio y sin impuestos.** Home Depot Canadá, RONA y los *lumber
  yards* de Ontario (Turkstra, Chamberlain, IHL) muestran la cifra «+ taxes»: el precio
  observado ya es sin GST/HST y entra tal cual en la matriz. Hamilton Builders' Supply publica
  incluso su **guía de precios mayorista 2026 completa** (áridos, cementos, malla, drenaje).
- **Dos productores de hormigón publican lista de planta** para el GTA (Canada Building
  Materials y Ontario Redi-Mix, enero 2026), algo impensable en IE/AU.
- Pero **no existe escala salarial legal del sector**: ni SEO irlandés ni awards australianos.
  El único suelo es el salario mínimo general (Ontario 17,60 $/h), que no describe el coste
  de un oficial. La mano de obra se ancla por tanto en la **mediana salarial oficial** (Job
  Bank), como la ONS en el Reino Unido — y eso cambia el rango (−10 % / +25 %, §2.3).
- Y el mercado convive con un sector **sindicalizado ICI** cuyos paquetes (LIUNA, Carpenters)
  quedan un 35-50 % por encima de la mediana. La matriz representa al empleador *open-shop*
  mediano; el convenio se documenta pero no es la base (§2.3).

Resultado: **52 anclas `referencia` (13 %)** y ~80 derivados explícitos por analogía
declarada. Menos anclas que AU (56) pese a la mejor transparencia retail, porque varias
familias canadienses (ladrillo, ABS, montantería) se cotizan por cuenta o no se capturaron
listas fiables en este corte, y se prefiere el derivado honesto.

## 2. Criterio de mano de obra: coste empresa, no tarifa de autónomo

Un contratista independiente canadiense cotiza 75-110 $/h de venta. Como en ES/GB/IE/AU se
descarta: el catálogo ya aplica un 35 % de margen sobre el coste directo. La mano de obra sale
del **coste empresa por hora trabajada** de un empleado por horas con sus cargas.

### 2.1 El mapa salarial: medianas Job Bank (Ontario)

El **Job Bank del Gobierno de Canadá** publica por oficio y provincia las bandas
bajo/mediana/alto (actualizadas 19/11/2025; periodo de referencia 2023-24, Labour Force
Survey de Statistics Canada). Se eleva cada mediana un **5 %** (≈2,5 %/año) para expresarla
a octubre de 2026:

| Oficio (Job Bank, Ontario) | Mediana 2023-24 | Adoptado 2026 |
|---|---:|---:|
| Carpenter | 32,00 | **33,60** |
| Bricklayer | 38,00 | **39,90** |
| Drywall finisher & plasterer | 35,48 | **37,25** |
| HVAC mechanic | 37,00 | **38,85** |
| Electrician (construction) | 34,00 | **35,70** |
| Plumber | 32,50 | **34,13** |
| Tile installer | 31,92 | **33,52** |
| Construction labourer & helper | 27,00 | **28,35** |
| Floor covering installer | 26,00 | **27,30** |
| Painter / Cabinetmaker | 25,00 | **26,25** |
| Ironworker (mediana mixta) | 44,34 | rodworker **40,50** (×0,87) |

Cuatro oficios no tienen mediana directamente utilizable y se valoran a 2026 sin el +5 %:
ayudante especializado 30,00 (Indeed: concrete labourer ON 29,83, sep-2026); soldador 30,00
(Job Bank 28,00 mezcla manufactura; Indeed ON 30,41 oct-2026); vidriero 30,00 (Job Bank
Ottawa 22,94-43,60; nivel de la mediana de BC); jardinero de obra 28,00 (entre *landscape
worker* 20,96 y *landscaper* 31,05).

Dos particularidades que el test protege:

1. **El cabillero es el oficio más caro de la matriz** (no el menor, como en IE/AU): el
   *reinforcing rodworker* es suboficio del *ironworker*, cuya mediana (44,34) es la más
   alta de la obra. Las escalas que separan estructura y armadura (Manitoba ICI) ponen la
   armadura ≈13 % por debajo → 40,50 $/h.
2. **Encofrador y oficial general ganan lo mismo pero no cuestan lo mismo**: el WSIB cobra
   por clase de riesgo (G3 estructura 3,55 % vs G1 residencial 2,18 %).

En Toronto las medianas son mayores (carpintero 36,00): esa dispersión va en el rango, no en
la base, porque la matriz es nacional con perfil Ontario, no GTA.

### 2.2 De salario a coste empresa

| Concepto | Cuánto | Fuente |
|---|---|---|
| CPP empresa | **5,95 %** con exención 3.500 $ y techo YMPE **74.600 $** (máx. 4.230,45 $) + **CPP2 4 %** hasta YAMPE 85.000 $ (máx. 416 $) | CRA/ESDC 2026 |
| EI empresa | **2,282 %** (1,4 × 1,63 %) con techo de ganancias asegurables **68.900 $** (máx. 1.572,30 $) | CEIC, 12/09/2025 |
| WSIB Ontario | **G1 2,18 · G3 3,55 · G4 1,54 · G5 2,15** $/100 $ según clase (techo 121.700 $) | WSIB 2026 |
| Vacation pay | **4 %** del salario bruto (6 % tras 5 años) | ESA Ontario |
| Festivos | 9 *public holidays* pagados (72 h) | ESA Ontario |
| Gastos fijos | 4.120 $/año | beneficios de grupo 2.400 (salud/dental: el sistema público no cubre dental ni medicamentos del adulto), EPI 700, formación/licencias 300, nómina 320, previsión de terminación ESA 400 |

**Los techos importan** (a diferencia de IE/AU, donde PRSI/super no tienen): un % plano
sobrevaloraría un 6-8 % el coste de los oficios de estructura. El modelo los aplica de forma
explícita y el test lo fija (a 60 $/h el CPP empresa es exactamente el máximo legal
4.646,45 $).

**Employer Health Tax fuera, deliberadamente** (1,95 % en Ontario, pero con exención del
primer 1.000.000 $ de nómina: la pyme tipo no lo paga; mismo criterio que el *payroll tax*
australiano).

**Divisor:** 260 − 10 vacaciones (2 semanas ESA) − 9 festivos − 3 de baja (el ESA protege 3
días pero **no los paga**) = **238 días × 8 h = 1.904 h facturables**; horas pagadas 1.976
(+72 de festivos) y vacation pay del 4 % aparte, que es la forma canadiense estándar de
liquidar las vacaciones del personal por horas. Es el divisor menos duro de los cinco
mercados (IE 1.747 h; AU 1.688 h): el ESA solo garantiza 2 semanas de vacaciones.

### 2.3 Resultado

| recurso | oficio | salario $/h | WSIB | coste empresa $/h facturable |
|---|---|---:|---|---:|
| MO-OF1 | oficial general (carpintero) | 33,60 | G1 | **42,09** |
| MO-AYU | peón | 28,35 | G1 | **35,84** |
| MO-AYU-ESP | peón especializado | 30,00 | G1 | **37,81** |
| MO-OF1-CAB | rodworker | 40,50 | G3 | **50,66** |
| MO-OF1-ALB | albañil | 39,90 | G3 | **49,96** |
| MO-OF1-AC | HVAC | 38,85 | G4 | **47,90** |
| MO-OF1-MON | montador drywall | 37,25 | G5 | **46,32** |
| MO-OF1-ELE | electricista | 35,70 | G4 | **44,30** |
| MO-OF1-PLO | plomero | 34,13 | G4 | **42,47** |
| MO-OF1-CARP | Carpintero | 33,60 | G3 | **42,59** |
| MO-OF1-ALI | alicatador | 33,52 | G5 | **41,99** |
| MO-OF1-SOLD / VIDR | soldador / vidriero | 30,00 | G5 | **37,80** |
| MO-OF1-JARD | jardinero de obra | 28,00 | G5 | **35,41** |
| MO-OF1-PISO | solador | 27,30 | G5 | **34,58** |
| MO-OF1-PIN / CARPM | pintor / mueblista | 26,25 | G5 | **33,33** |

Recargo sobre salario: 19-22 %. El total anual del oficial sale a **80.147 $**.

**Rango −10 % / +25 %** (no el −3 %/+20 % de IE/AU): la base es una **mediana**, no un suelo
legal, y existe mercado lícito por debajo (Atlántico, rural) y por encima (GTA, Alberta,
BC). El paquete ICI sindical del GTA (LIUNA 527 publica peón general a 55,60 $/h de
«total compensation», carpintero-formsetter 58,58 — ya con vacation 10 %, beneficios y
pensión, antes de CPP/EI/WSIB) queda **por encima del rango**: quien presupueste obra ICI
sindicalizada debe sobrescribir la mano de obra con su convenio, igual que en AU con el EBA.

## 3. Maquinaria

Fuentes: lista pública por día de Toronto Rental Equipment (2025), guías y *marketplaces*
2026 del GTA para excavadoras/plataformas (DOZR, NAM Rentals) y listas de Ontario de 2022
actualizadas para mezcladoras/compactadores (éstos, `derivado` por antigüedad). United
Rentals/Sunbelt publican tarifas en su marketplace pero ligadas a cuenta/ubicación. Día ÷ 8
h, sin GST/HST ni combustible; con operador solo donde el recurso lo declara.

Ejemplos observados (sin impuestos): plancha 95 $/día, sierra de cerámica 87, martillo de
20 lb 82, hidrolavadora 87, bomba de achique 2" 89, amoladora 50, motosierra 75;
miniexcavadora ≈3,5 t 250-450 + martillo ≈150 → MQ-RETRO 550 $/día. Baño portátil por mes:
285 $ (derivado).

## 4. Materiales

Todos los precios **sin GST/HST** (así se publican en Canadá; no hay que deflactar nada):

| Familia | Anclas y evidencia |
|---|---|
| Hormigón premezclado | 20 MPa **245 $/m³**, 25 MPa **260**, 30 MPa **270**: listas de planta GTA 2026 de CBM (20→240, 25→245, 30→255) y Ontario Redi-Mix (20→254, 25→266, 30→275). Sin recargos de entrega/ambientales (≈9-15 $/m³) ni carga corta. Las guías web de 175-225 $ «entregado» quedan bajo ambas listas y no se adoptan. Core-fill: 275 $/m³ derivado. |
| Cemento y áridos | Portland GU **0,56 $/kg** (saco 40 kg 19,99-24,68 $; HBS 2026: 21,90). Áridos HBS 2026 por yd³ → m³ (×1,308): arena de hormigón 60,16 → **79 $/m³**; piedra 3/4" 72,50 → **95**; Granular A 54,12 → **72**. |
| Acero | 15M **2,00 $/kg** (1.800-2.200 $/t GTA, jul-2026); malla 6×6 W2.9 hoja 4×8 ft 19-40 $ → **7,50 $/m²**. |
| Bloques | CMU 8" (190 mm) **4,40 $** (Chamberlain ON 4,19 a 2026); 6"/4" derivados por proporción (3,80/3,30). Ladrillo visto derivado (Brampton Brick cotiza por cuenta). |
| Yeso laminado | CGC 1/2" 4×8 ft **5,55 $/m²** (16,52 $/hoja HD; guías 14-18 $); pasta premezclada 17 L 31,75 $ → **1,50 $/kg**; Durabond 90 15 kg 40,88 $ → **2,70**; fibra de vidrio R-20 **10,00 $/m²** (0,78-1,08 $/ft²); lana mineral R-20 **17,00** (1,35-1,85 $/ft²). Montantería: derivada (sin tarifa capturada). |
| Adhesivos | VersaBond 50 lb 19,98 $ → C1 **0,90 $/kg**; MAPEI Ultraflex LFT 34,30 $ → C2TE **1,50**; junta Polyblend Plus (formatos pequeños 6,9-7,2 $/kg) → **4,50** en formato trade; autonivelante 36,98-40,38 $/22,7 kg → **1,70**; grout expansivo 26,55 $ → **1,15**. |
| Pintura | Látex interior estándar 60-80 $/gal (3,78 L) → **15,50 $/L** (contratista 40-55 $/gal); semibrillo premium derivado 19. |
| Madera | SPF 2×6 a 700-900 $/MBF (GTA) → listón 2×4 **1,90 $/m**; estructural derivada **620 $/m³**. Canadá produce la madera: es el material estructural barato (cf. AU 980 A$/m³). |
| Fontanería | PEX 1/2" **1,25 $/m** (Apollo 100 ft 37,95 $; PEX-A 1,87) como equivalente del PPR; desagüe **ABS** 4" derivado 11,00 $/m (en CA el estándar es ABS, no PVC); llave/latiguillo/sifón con precio explícito (el factor de familia sale del PEX y los infravalora). |
| Eléctrica | NMD90 14/2 150 m 228-270 $ (1,52-1,80 $/m); recurso ≈2,5 mm² como 12/2 → **2,50 $/m**. |
| Drenaje | *Weeping tile* 4" perforado 1,73-1,75 $/ft (HBS 2026) → **5,75 $/m**. |
| Residuos | Sin *levy* tipo NSW: bin GTA 14 yd³ 439 $ con 2 t y exceso 120-130 $/t → escombro **60 $/m³**. La tierra está regulada (O. Reg. 406/19) y no es barata: **70 $/m³** derivado. |

## 5. Divisa, impuestos y unidades

- **Tasa de corte:** 1 USD = 1,4154 CAD (Banco de Canadá, cierre 16/10/2026), la misma ya
  publicada en `app/services/tasa.py`. Solo normaliza la base VE antes del factor; el
  resultado se congela en CAD.
- **Impuestos:** todo sin GST/HST. La aplicación usa el GST federal (5 %) como referencia y
  marca CA como impuesto regional (HST 13 % en Ontario, GST+PST en BC, solo GST en Alberta):
  la matriz nunca incluye el impuesto, así que la variación provincial no la contamina.
- **Métrico de precio, imperial de formato:** bloque CMU 390×190 mm (8×8×16"), placa 4×8 ft
  (2,97 m²), saco de cemento 40 kg, adhesivos 50 lb (22,7 kg), áridos por yd³ (×1,308 → m³),
  aislamiento por ft² (×10,764 → m²), tubería por ft (×3,281 → m), madera por MBF
  (1 MBF ≈ 2,36 m³ nominales; el 2×4 real es 38×89 mm).

## 6. Limitaciones

1. **Perfil Ontario.** Salarios (Job Bank ON), WSIB, ESA, festivos (9) y residuos son de
   Ontario, el mayor mercado. Quebec difiere de raíz (QPP/QPIP, CNESST, decretos de la CCQ
   con salarios fijados por oficio en obra ICI/residencial — de hecho Quebec sí tiene algo
   parecido a una escala sectorial —) y su coste se mueve dentro del rango, pero quien
   opere bajo CCQ debe sobrescribir la mano de obra.
2. **Mediana ≠ convenio.** El ICI sindicalizado del GTA cuesta un 35-50 % más por hora que
   esta matriz (ver §2.3). La matriz es el empleador mediano *open-shop*, como la ONS en GB.
3. **La mediana envejece:** referencia 2023-24 subida un 5 % plano. El Job Bank actualiza
   cada noviembre; reinvestigar con la edición de 2026 (nov-2026) y los parámetros CPP/EI
   de 2027 (el EI se anuncia en septiembre; el YMPE en otoño).
4. **Hormigón de planta, no puesto en obra:** faltan entrega, recargo ambiental/combustible
   y carga mínima; el m³ efectivo residencial sale un 10-25 % por encima en cargas cortas.
