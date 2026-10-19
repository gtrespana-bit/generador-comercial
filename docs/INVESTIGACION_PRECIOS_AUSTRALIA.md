# Investigación de precios de referencia — Australia (2026-10-19)

Estudio de mercado que sustenta la matriz nacional
`basedatos_partidas/salida/precios_recursos_australia.csv` (388 recursos, AUD, sin GST).
Metodología en `docs/METODOLOGIA_PRECIOS_REFERENCIA_AUSTRALIA.md`; modelo de coste empresa en
`tools/coste_empresa_australia.py`; generador en `tools/generar_matriz_precios_australia.py`.

Tercer estudio de la secuencia de mercados angloparlantes (GB → **IE** → **AU** → CA → US,
`docs/HOJA_DE_RUTA_MERCADOS_INGLESES.md`).

## 1. La advertencia que ordena todo lo demás

Australia es el mercado angloparlante con **menos precios públicos**:

- El canal profesional funciona con cuentas comerciales ligadas al ABN («trade pricing»):
  **Cooper** publica tiendas y catálogos pero no precios unitarios; los merchants independientes
  hacen lo mismo.
- Las dos grandes empresas de alquiler, **Coates** (mismo grupo económico que Guinness Peat vía
  Seven Group) y **Kennards Hire**, no publican tarifas: cada máquina se presupuesta.
- Los productores de hormigón (Holcim, Hy-Tec/Adbri, Heidelberg) venden «bajo presupuesto»;
  el precio por m³ solo lo dan intermediarios que gestionan la compra (MixHub, BuiltSimple) y
  sus horquillas son anchas (N25 en NSW: 250-370 $/m³).
- Las fuentes con precio visible son las retail que ya incluyen GST (Bunnings) y merchants
  medianos con tienda online (Sydney Building Materials, Network Building Supplies, ARC).

Consecuencia: la matriz australiana tiene **56 anclas `referencia` (14 %)**, menos que Irlanda
(106), y un número mayor de **derivados explícitos por recurso** (precio fijado por analogía
documentada en la observación de cada fila, que no alimenta los factores por familia). Es el
mismo patrón honesto de IE: nunca se finge una cotización que el mercado no publica.

## 2. Criterio de mano de obra: coste empresa, no tarifa de autónomo

Un *sole trader* australiano cotiza 80-120 $/h de venta. Como en ES/GB/IE se descarta: el
catálogo ya aplica un 35 % de margen sobre el coste directo y mezclar ambos produciría margen
sobre margen. La mano de obra sale del **coste empresa por hora trabajada** de un empleado
*weekly hire* bajo el Modern Award, con sus cargas legales.

### 2.1 El mapa salarial: tres awards, una «standard rate»

Los salarios mínimos de la construcción los fijan los **Modern Awards** de la Fair Work
Commission, revisados cada 1 de julio. Tres awards cubren los 17 oficios del catálogo:

| Award | Oficios | Tarifa adoptada (1/7/2026) |
|---|---|---|
| Building and Construction General On-site [MA000020] | obra general y acabados | CW3 tradesperson **1.119,10 $/semana** |
| Electrical, Electronic and Communications [MA000025] | electricista | grado 5 **31,13 $/h** all-purpose |
| Plumbing and Fire Sprinklers [MA000036] | plomero, climatización | tradesperson L1 **31,63 $/h** all-purpose |

El detalle que ordena el sistema: los tres comparten la misma base semanal —la «standard rate»
de 1.119,10 $— y las diferencias salen **solo de los pluses** (*allowances*). En el Building
Award (cl. 19.1, weekly hire, 38 h/semana):

| Nivel | $/semana | Equivalencia |
|---|---|---|
| CW1(a)–(d) | 1.013,50 – 1.066,00 | peón (labourer), por antigüedad |
| CW2 | 1.087,50 | operario cualificado (**steel fixer**, andamista, paisajista) |
| CW3 (=ECW3) | 1.119,10 | tradesperson |

Pluses «all-purpose» que forman el salario ordinario a todos los efectos:

- **Industry allowance:** 67,15 $/semana (construcción general) o 53,72 (residencial). Se adopta
  la general: la estructura horquilla del catálogo (oficial genérico, estructuras) es obra
  general, y la banda baja del rango (−3 %) ya absorbe el caso residencial.
- **Tool allowance** (si la empresa exige herramienta propia): 41,22 $/semana carpinteros y
  alicatadores; 34,10 yeseros y especialistas de suelos; 29,26 albañiles; 9,89 pintores y
  vidrieros.
- **Fares and travel pattern allowance:** 22,41 $ por día atendido (4.728,51 $/año para el
  perfil del modelo). Es coste empresa real aunque fiscalmente sea *allowance*.

Electricista grado 5: (1.119,10 + industry 41,41 + tool 22,31) / 38 = **31,13 $/h**. Queda unas
décimas por debajo del CW3 general (31,22) porque su industry allowance es menor. No es un
error: es la aritmética de los awards, y el test de la matriz lo respeta sin imponer un orden
que el sistema no garantiza.

Particularidad australiana que el catálogo debe respetar, como el SEO irlandés con el steel
fixer: **el steel fixer es CW2** (no tradesperson), igual que el ayudante especializado y el
paisajista. El peón se valora como CW1(d) (experimentado, ayuda directa al oficial), no como
recién ingresado.

Contratación: se adopta **weekly hire** (plazo indefinido). El *daily hire* de obra paga un
recargo del ~9 % a cambio de la terminación por días; el modelo lo trata como escenario del
rango (+20 %), no como base.

### 2.2 De salario a coste empresa

| Concepto | Cuánto | Fuente |
|---|---|---|
| Superannuation guarantee | **12 %** del salario ordinario (OTE) | ATO; al 12 % desde el 1/7/2025 (tope legal alcanzado) |
| Workers compensation | **4,95 %** (4,84 + 0,11 enfermedades por polvo) | icare NSW, WIC 411100 *House Construction*; tarifas 2025-26 congeladas en 2026-27 (SIRA) |
| Long service leave | **1,7 %** de devengo | NSW: 8,67 semanas cada 10 años |
| Leave loading | 17,5 % sobre las 4 semanas de vacaciones (152 h) | Awards |
| Fares & travel | 22,41 $/día × 211 días = 4.728,51 $/año | MA000020 cl. 26 |
| Gastos fijos | 2.230 $/año | responsabilidad civil 350, EPI/herramienta menor 600, licencias (white card, high-risk) 250, nómina 280, previsión de redundancy 750 |

**Payroll tax queda fuera, deliberadamente.** En NSW es el 5,45 % pero solo por encima de
1,2 M$ de masa salarial anual: no aplica a la pyme constructora que es el usuario tipo, varía
por estado y por tamaño, y meterla castigaría a quien no la paga. El rango +20 % la absorbe
donde aplique. Tampoco entra el *Building and Construction Industry Long Service Payments Levy*
de NSW (0,35 %): grava el **proyecto**, no la nómina, y es coste indirecto de obra.

**Divisor:** 38 h × 52 = 1.976 h **pagadas**. El día de obra es de 8 h porque el award acumula
0,4 h/día para el RDO (*rostered day off*, 13 al año). Días trabajados: 260 − 20 vacaciones −
11 festivos (NSW) − 5 de baja personal − 13 RDO = **211 días × 8 h = 1.688 h facturables**. Es
un divisor más duro que el irlandés (1.747 h) y explica buena parte del coste australiano: se
paga 1,17 horas por cada hora de obra.

### 2.3 Resultado

| recurso | oficio | ordinario $/h | coste empresa $/h facturable | recargo |
|---|---|---:|---:|---:|
| MO-OF1 | oficial general CW3 | 31,22 | **48,06** | 31,5 % |
| MO-AYU | peón CW1(d) | 29,82 | **46,10** | 32,1 % |
| MO-AYU-ESP / CAB / JARD | CW2 | 30,39 | **46,89** | 31,8 % |
| MO-OF1-ELE | electricista g5 | 31,13 | **47,94** | 31,6 % |
| MO-OF1-PLO / AC | plomero L1 | 31,63 | **48,65** | 31,4 % |
| MO-OF1-ALB | albañil | 31,99 | **49,15** | 31,3 % |
| MO-OF1-CARP / CARPM / MON / ALI | carpintería y alicatado | 32,30 | **49,59** | 31,1 % |
| MO-OF1-PIN / VIDR | pintor, vidriero | 31,48 | **48,43** | 31,4 % |
| MO-OF1-PISO | especialista de suelos | 32,11 | **49,33** | 31,2 % |
| MO-OF1-SOLD | soldador ECW3 | 31,22 | **48,06** | 31,5 % |

El total anual de un CW3 sale a **81.133 $/año**. Las encuestas salariales (Hays, SEEK) sitúan
al carpintero empleado en 75-90 k$ de coste total y al obrero en 65-80 k$: el modelo queda en
banda, del lado prudente porque la base es el **mínimo legal**. Igual que en Irlanda, el rango
es **−3 % / +20 %**: la base ya es el suelo legal nacional (sin rebaja regional posible), y el
+20 % cubre acuerdos de empresa (EBA), *daily hire*, ciudades caras (Sydney/Melbourne) y payroll
tax cuando aplica.

## 3. Maquinaria

Fuente: las pocas listas públicas de día que existen (Elimbah Hire, Perth Hills Tool Hire,
STK), más las guías de mercado de iseekplant/goingrate; Coates y Kennards no publican tarifas.
La tarifa de día se divide entre 8 h, como en GB/IE. Sin GST ni combustible; con operador solo
donde el recurso lo declara.

Ejemplos (sin GST): mezcladora 65 $/día, plancha compactadora 70, nivel láser rotativo 60,
excavadora 3,5 t en seco ~400 (470 con martillo = MQ-RETRO 58,75 $/h), tijera 19 ft 180. La
mayoría de las 44 máquinas se fijan como **derivados explícitos** por analogía con estas listas,
con la equivalencia declarada en cada fila. El baño portátil se mide por mes (240 $/mes,
derivado), como manda el recurso.

## 4. Materiales

Todos los precios **sin GST (10 %)**: las fuentes retail (Bunnings) lo incluyen y se dividen
entre 1,1; las trade que lo desglosan se copian en su cifra «ex GST».

| Familia | Anclas y evidencia |
|---|---|
| Hormigón premezclado | N20 **300 $/m³**, N25 **325**, N32 **355** (MixHub ago-2026: Sydney N20 320-340, N25 340-370, N32 370-400; BuiltSimple NSW 30-70 $ por debajo: se adopta banda media ex GST). El relleno de celdas (core fill) se valora como premezclado bombeable: 335 $/m³. |
| Cemento y áridos | cemento **0,45 $/kg** (saco 20 kg 9,01-10,70 con GST); arena lavada 105 $/m³, *blue metal* 98, material de préstamo/*road base* 126 (bulk ~60-70 $/t ex GST → $/m³ con densidad). |
| Acero | corrugado **1,60 $/kg**; malla SL72 ~6,30 $/m² (lámina 6×2,4 m a 79-106 $ con GST). |
| Bloques y ladrillo | Besser Bright: 90 mm 3,34 $, 140 mm 3,92, 190 mm 4,31 (con GST 3,67/4,31/4,74); ladrillo cara vista 1,45 $ (listas Austral 1.729-3.453 $/1000 con GST; guías 900-1.200: banda baja *common/standard face*). |
| Yeso laminado | Gyprock 13mm **11,50 $/m²** (hoja 2400×1200 a 29,25-42,57 según canal); montante Rondo 64 mm 0,5 BMT 3 m **9,62 $ ex GST** (Sydney BM) → 3,30 $/m; base coat 20 kg 48,48-52,90 con GST → 2,55 $/kg; cornice cement 55,28-67,28 → 2,75; batts Earthwool R2.5HD ~10,50 $/m². |
| Morteros/adhesivos | Dunlop C2S1 37,74/20 kg → 1,70 $/kg; Davco Mastic 29,40 → C1 1,35; junta CG2 5 kg 32,82 → 5,50; autonivelante Ardit 53,96 → 2,45; grout 21,04-33,78 → 1,55. |
| Pintura y selladores | Dulux Wash&Wear 10 L 239 $ con GST → 21,50 $/L (el semibrillo PLUS, 290 → 24); silicona sanitaria Selleys 15,60 → 14,20. |
| Madera | pino MGP10 90×45 a 5,36 $/m con GST → listón 4,90; estructural derivado 980 $/m³. |
| Fontanería | PEX 16 mm (el PPR por termofusión apenas se vende en AU: equivalencia declarada) 1,60 $/m; PVC DWV 100 mm 8,00 $/m. |
| Eléctrica | cable TPS 2,5 mm² 100 m 194-251 $ ex GST → 2,15 $/m. |
| Residuos | NSW metro *waste levy* **180,20 $/t** 2026-27 (regional 103,80); skip Sydney 6 m³ 845-911 $ con GST. Canon de escombro **125 $/m³** (skip, no vertedero puro: incluye transporte y *gate fee* de mezcla 440-510 $/t ex GST), tierra 110 (derivado, *clean fill* más barato). |

## 5. Divisa, GST y unidades

- **Tasa de corte:** 1 USD = 1,4395 AUD (AUD/USD 0,6947, Banco de la Reserva de Australia,
  cierre 16/10/2026). La misma tasa ya publicada en `app/services/tasa.py`; solo normaliza la
  base VE en USD antes del factor de mercado. El resultado se congela en AUD.
- **GST:** todo sin GST. Retail con GST → ÷1,1. Nunca se observa un precio «con GST» como ancla.
- **Sistema métrico** pleno (como GB): sin conversiones salvo densidad de áridos ($/t → $/m³:
  arena 1,5 t/m³, piedra 1,5, *road base* 2,1) y formatos (hoja Gyprock 2400×1200, bloque Besser
  390×190 mm, malla 6×2,4 m, saco de cemento de 20 kg —en AU el saco estándar es de 20 kg, no
  de 25—).

## 6. Limitaciones

1. **Perfil NSW.** Workers comp (icare), festivos (11), LSL, *waste levy* y skip son de NSW,
   el mayor mercado; los awards son nacionales. Otros estados (WorkCover VIC/QLD, levy QLD
   95 $/t) mueven el coste dentro de la banda ± del rango.
2. **Opacidad trade.** 257 recursos derivan por factor de familia/categoría y ~75 son derivados
   explícitos. Quien tenga cuenta Cooper/Reece debe sobrescribir con sus precios propios: la
   matriz es referencia nacional, no sustituto de la cuenta comercial.
3. **Award ≠ mercado.** En obra comercial sindicalizada (CFMEU/EBA) el salario real supera el
   award un 20-40 %. La matriz representa el empleo bajo award, el suelo legal —conservador y
   defendible—, como el SEO en Irlanda.
4. **Caducidad:** los awards se revisan cada 1 de julio (siguiente: 1/7/2027); el *waste levy*
   NSW, cada ejercicio. Reinvestigar en julio de 2027.
