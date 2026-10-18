# Investigación de precios de referencia — Reino Unido (2026-10-18)

**Objetivo:** anclas de mercado británicas observadas para la matriz de precios de recursos en GBP
(`basedatos_partidas/salida/precios_recursos_reino_unido.csv`). Mismo contrato que las rondas de
España y LatAm: cada cifra conserva rango, fuente y fecha; no son cotizaciones de tienda.

**Tasa de corte:** 1 USD = 0,7502 GBP (GBP/USD 1,3330, exchangerates.org.uk mid-market 16/10/2026;
Yahoo Finance 1,3330; Banco de Inglaterra 1,3160 el 14/10). Solo normaliza el precio base USD antes
de aplicar el factor de mercado; el resultado queda congelado en GBP y con fecha.

**Ámbito:** reforma y obra residencial en el Reino Unido. Materiales sin porte salvo indicación.
Mano de obra = **coste empresa**, sin IVA, no tarifa de autónomo.

---

## 1. La advertencia que ordena todo lo demás

Los precios base de `basedatos_partidas/datos/recursos.json` están en USD pero su ámbito declarado
es **Venezuela** (`"mercado_base": "VE"`; un oficial de 1ª está a 5,5 USD/h). No son precios
internacionales ni precios de Estados Unidos.

Por tanto **ninguna conversión de divisa puede producir un precio británico**. Convertir 5,5 USD/h a
4,13 GBP/h y presentarlo como coste de un oficial británico daría un error de casi seis veces. La
matriz británica tiene que reconstruirse desde precios británicos, que es lo que hace este
documento.

## 2. Criterio de mano de obra: coste empresa, no tarifa de autónomo

El catálogo aplica un **35 % de margen sobre el coste directo** (`app/services/precios_partidas.py`,
margen por defecto desde 2026-08-25). Es el mismo motivo por el que España corrigió sus tarifas en
la revisión de agosto de 2026: si el recurso de mano de obra guarda una tarifa de mercado con
beneficio, el precio de venta lleva **margen sobre margen**.

Las tarifas que circulan por la red (electricista 280–500 £/día, albañil 180–280 £/día) son
**tarifas de autónomo facturadas**, no coste de empresa. El modelo británico usa las dos fuentes que
sí miden al asalariado:

* **ONS ASHE** (Annual Survey of Hours and Earnings), mediana de asalariados en PAYE, que incluye
  horas extras. Es la base adoptada.
* **CIJC Working Rule Agreement**, las tarifas mínimas pactadas entre patronal y sindicatos, que
  sirven de suelo: el salario adoptado nunca queda por debajo del convenio.

### 2.1 Salarios por oficio (ONS ASHE 2026, asalariados)

| Oficio | Mediana anual | £/hora |
|---|---:|---:|
| Electricistas | 39.647 £ | 19,20 |
| Fontaneros e instaladores de calefacción | 37.881 £ | 18,18 |
| Otros oficios de la construcción | 34.822 £ | 17,65 |
| Yeseros | 34.016 £ | 16,58 |
| Carpinteros y ebanistas | 34.014 £ | 17,04 |
| Albañiles | 33.030 £ | 16,75 |
| Peones | — | 13,50 |

Contraste con el suelo del convenio: las tarifas del CIJC vigentes desde el **20 de julio de 2026**
son peón general **13,18 £/h**, skill rate 1 **15,61 £/h** y craft rate **16,40 £/h**. Los salarios
ONS quedan entre un 1 % y un 17 % por encima del craft rate, coherente con un convenio que es suelo
y no techo.

### 2.2 De salario a coste empresa

```
Horas contratadas = 39 h/semana × 52 = 2.028 h/año      (jornada CIJC: L-J 8 h, V 7 h)
− Vacaciones       = 31 días × 7,8 h = 241,8 h          (23 de industria + 8 festivos, WR.18)
− Bajas            = 4,4 días × 7,8 h =  34,3 h         (media británica del sector)
= Horas facturables                     1.751,9 h/año
```

Cargas aplicadas al salario anual:

| Concepto | 2026/27 | Base legal |
|---|---|---|
| National Insurance empresa | 15 % sobre lo que exceda de 5.000 £ | Class 1 secundaria; vigente desde el 6/4/2025 y congelada hasta 2030/31 |
| Pensión de auto-enrolment | 3 % de la banda computable 6.240–50.270 £ | Mínimo legal de aportación empresarial |
| CITB levy | 0,35 % de la nómina PAYE | 1,25 % sobre CIS neto, que aquí no aplica |
| Seguro de responsabilidad de empleador | ~180 £/año | |
| EPI, ropa y herramienta menor | ~350 £/año | |
| Formación (CSCS, SMSTS/SSSTS) | ~150 £/año | |
| Gestoría de nóminas | ~100 £/año | |
| Previsión de indemnización | una semana de salario al año | |

El reparto entre horas contratadas y horas facturables (2.028/1.751,9 = 1,158) es lo que incorpora
las vacaciones y las bajas **sin pagarlas dos veces**: el operario cobra 2.028 horas pero solo
produce 1.751,9.

### 2.3 Resultado

Coste empresa por hora facturable, con el rango de dispersión regional (Escocia e Irlanda del Norte
−10 %, área de Londres +20 %):

| Recurso | Oficio británico | £/h |
|---|---|---:|
| MO-AYU | Peón general | **18,71** |
| MO-AYU-ESP | Peón especializado / improver | **19,50** |
| MO-OF1-JARD | Operario de jardinería | **20,85** |
| MO-OF1-PIN | Pintor y decorador | **22,99** |
| MO-OF1-CAB | Ferrallista | **22,74** |
| MO-OF1-ALB | Albañil | **23,23** |
| MO-OF1-CARP / MO-OF1-CARPM / MO-OF1-VIDR / MO-OF1-MON | Carpintero, ebanista, vidriero, montador | **23,64** |
| MO-OF1 / MO-OF1-ALI / MO-OF1-PISO | Oficial general, alicatador, solador | **24,48** |
| MO-OF1-PLO / MO-OF1-AC | Fontanero, técnico de climatización | **25,22** |
| MO-OF1-SOLD | Soldador / montador de estructura | **25,67** |
| MO-OF1-ELE | Electricista | **26,64** |

**Verificación de que el número es razonable.** Aplicando el margen del catálogo del 35 %, el precio
de venta que resulta se compara con las tarifas de autónomo observadas en el mercado:

| Oficio | Coste ×1,35 | Jornada de 8 h | Tarifa de mercado observada |
|---|---:|---:|---|
| Peón | 25,26 £/h | 202 £/día | 120–180 £/día |
| Albañil | 31,36 £/h | 251 £/día | 180–280 £/día |
| Electricista | 35,96 £/h | 288 £/día | 200–350 £/día |

Los tres caen dentro del rango de mercado. Que la empresa cobre algo por encima del autónomo es
correcto: el autónomo no carga con seguros, gestoría, vacaciones ni bajas.

## 3. Maquinaria

En el Reino Unido el alquiler se cotiza por día (jornada de 8 h) o por semana, no por hora. Se
publica el equivalente horario dividiendo el día entre 8. Las 44 máquinas llevan ancla propia.
Tarifas sin IVA ni combustible.

| Máquina | Día | £/h |
|---|---:|---:|
| Borriquetas | 7 £ | 0,88 |
| Hormigonera eléctrica | 22 £ | 2,75 |
| Amoladora angular 230 mm | 14 £ | 1,75 |
| Martillo eléctrico 5 kg | 33 £ | 4,13 |
| Rozadora de doble disco | 40 £ | 5,00 |
| Plancha compactadora | 38 £ | 4,75 |
| Compactador de zanja | 130 £ | 16,25 |
| Vibrador de aguja | 40 £ | 5,00 |
| Alisadora helicóptero | 85 £ | 10,63 |
| Torre móvil de 2,2 m | 33,50 £ | 4,19 |
| Retroexcavadora 3 t con martillo | 250 £ | 31,25 |
| Nivel láser rotativo | 45 £ | 5,63 |
| Baño portátil | — | 150 £/mes |

Dos avisos de mercado que cambian el recurso:

* **El andamio.** El recurso dice «andamio tubular o de borriquetas» para trabajo en altura. En el
  Reino Unido eso es una **torre móvil de aluminio**, no un caballete: se adopta la torre de 2,2 m a
  33,50 £/día. Contratada por semana la torre sale mucho más barata, pero la tarifa diaria es la
  conservadora.
* **Las torres se facturan por semana.** Una torre de 4 m cuesta unos 74 £/semana frente a 54 £/día.
  En trabajos de más de cuatro días conviene revisar la partida.

## 4. Materiales

### 4.1 Hormigón y áridos

| Material | Precio británico | Fuente |
|---|---|---|
| Hormigón C16/20 | 92–115 £/m³ | mixdesigncalc, SE Inglaterra |
| Hormigón C20/25 | 100–128 £/m³ | ídem |
| Hormigón C25/30 | 108–136 £/m³ | ídem |
| Hormigón C30/37 | 115–145 £/m³ | ídem |
| Cemento CEM I | 6,78–7,73 £/25 kg ex IVA | Travis Perkins |
| Arena de construcción | 30–42 £/t suelta | Davis Aggregates, concretemath |
| Arena de hormigonar | 32–48 £/t | ídem |
| Zahorra MOT Type 1 | 28–38 £/t | ídem |
| Grava de 20 mm | 32–48 £/t | ídem |
| Armadura corrugada | 520–680 £/t | buildersmerchantsdirect |

Los grados españoles se han traducido a los británicos por resistencia, no por nombre: 180 kg/cm² ≈
17,7 MPa ≈ C16/20, y así sucesivamente.

Las densidades usadas para pasar de tonelada a metro cúbico son 1,5 t/m³ en arena, 1,5 t/m³ en árido
triturado y 2,1 t/m³ en zahorra.

### 4.2 El impuesto de vertedero explica el mayor salto de toda la matriz

El **Landfill Tax** británico, vigente desde el 1 de abril de 2026:

| Material enviado a vertedero | 2025/26 | **2026/27** |
|---|---:|---:|
| Tipo general | 126,15 £/t | **130,75 £/t** |
| Tipo reducido (inerte: roca, tierra) | 4,05 £/t | **8,65 £/t** |

El tipo reducido **subió un 114 %** en un año (GOV.UK, HMRC). Con densidades de 2,2 t/m³ para el
cascote de hormigón y 1,5 t/m³ para la tierra, el impuesto por sí solo ya explica que `MT-CANON`
cueste en el Reino Unido unas siete veces lo que en España y `MT-CANON-TIERRA` unas diez. No es un
error de la matriz: es el mercado.

### 4.3 Yeso laminado, fábrica y aislamiento

| Material | Precio británico | Nota |
|---|---|---|
| Placa de yeso 12,5 mm (2400×1200) | 8,92–10,38 £ ex IVA | 2,88 m² por hoja → 3,30 £/m² |
| Placa de yeso 15 mm | ~11,50 £ | → 4,15 £/m² |
| Placa resistente al fuego | 14–16,50 £ | → 5,80 £/m² |
| Bloque denso de 100 mm | 1,60–2,57 £/ud | Formato británico 440×215 mm |
| Ladrillo de cara vista estándar | 450–700 £/1.000 | → 0,65 £/ud |
| Lana de roca de 100 mm | 8,57 £/m² | Rockwool RWA45 |
| Lana de vidrio en rollo 100 mm | 32,20 £/rollo de 13,89 m² | → 2,32 £/m² |
| PIR de 100 mm (Celotex GA4100) | 34–40 £/plancha de 2,88 m² | → 12,17 £/m² |

Nota de mercado: **Celotex ya no existe como marca**. Saint-Gobain vendió el negocio de PIR a
Soprema y la gama se llama ahora Sopratherm, con los mismos códigos (GA4000, GA4100). Si un
proveedor presupuesta GA4000 y entrega una plancha con la marca Soprema, es el mismo producto.

### 4.4 Instalaciones

En fontanería hay una diferencia de mercado relevante: **la tubería de PPR es residual en el Reino
Unido**. El equivalente funcional es el tubo barrera de polietileno de los dos sistemas que dominan
el mercado, **JG Speedfit** y **Hep2O**, ambos conforme a BS 7291. El recurso `MT-PLO-PPR20` se ha
tarificado como tubo barrera de 15 mm (Speedfit 47,20 £/25 m; Hep2O 47,16 £/25 m).

| Material | Precio británico |
|---|---|
| Tubo de cobre de 15 mm | 13,74–15,60 £/3 m IVA incl. → ~4,00 £/m ex IVA |
| Tubo barrera de 15 mm | 1,89–2,26 £/m |
| Saneamiento enterrado de 110 mm | 3,50–6,00 £/m |
| Cable 6242Y de 2,5 mm² | 88,69–96 £/100 m IVA incl. → 0,77 £/m ex IVA |
| Silicona sanitaria 310 ml | 9,97–14,14 £ |
| Adhesivo C2 TE S1, saco de 20 kg | 24,66 £ |
| Mortero de juntas CG2, saco de 5 kg | 16,32 £ |

### 4.5 Pintura

| Producto | Precio británico |
|---|---|
| Emulsión vinílica mate profesional | 4,50–9,50 £/l |
| Emulsión satinada | 5,50–10,50 £/l |
| Esmalte brillante sintético | 8,00–11,70 £/l |
| Pintura para fachada (masonry) | 7,20–8,40 £/l |

Referencia: Dulux Trade Vinyl Matt 5 L a 28,41 £ ex IVA en Travis Perkins; Johnstone's Trade
Stormshield 5 L a 36 £.

## 5. Cobertura y derivación

| Categoría | Recursos | Investigados | Derivados |
|---|---:|---:|---:|
| Mano de obra | 17 | 17 (100 %) | 0 |
| Maquinaria | 44 | 44 (100 %) | 0 |
| Materiales | 327 | 106 (32 %) | 221 |
| **Total** | **388** | **167 (43 %)** | **221** |

La casa trabaja con un 17 % de anclas en España y un 3 % en LatAm. Para el Reino Unido se ha
exigido bastante más: **43 %, con mano de obra y maquinaria al 100 %**.

### 5.1 Factor por familia, no por categoría

El generador de España calcula **un** factor por categoría, con lo que una cámara CCTV heredaba el
factor del cemento. Aquí el factor se calcula **por familia** (los dos primeros tramos del código:
`MT-CONC`, `MT-BLQ`, `MT-PIN`…), y solo si una familia no tiene anclas se cae al factor de la
categoría.

Factores de categoría resultantes (mediana de precio británico / precio base convertido):

| Categoría | Factor |
|---|---:|
| Maquinaria | 2,056 |
| Materiales | 1,839 |

Cuando una familia mezcla productos de estructuras de precio incompatibles se le da ancla propia en
lugar de dejarla heredar. Es el caso del **bloque de vidrio** (`MT-BLQ-VIDRIO`), que por el factor
de la familia `MT-BLQ` habría salido a 33 £/unidad cuando en el mercado británico ronda las 5,50 £.

### 5.2 Comprobación frente a España

Con 1 EUR = 0,8760 GBP:

| Categoría | Mediana GB/ES |
|---|---:|
| Mano de obra | 1,27× |
| Materiales | 1,38× |
| Maquinaria | 1,16× |

Los valores extremos están todos explicados: el escombro y la tierra (7× y 10×) por el impuesto de
vertedero; la tornillería (0,40×) porque en el Reino Unido es más barata; el acero inoxidable y
alguna maquinaria (0,5×) porque las referencias españolas son altas.

Muestra de valores derivados contrastados con el mercado real:

| Recurso | Derivado | Mercado real |
|---|---:|---|
| Doble acristalamiento | 76,15 £/m² | 60–110 £/m² |
| Vidrio laminado | 58,15 £/m² | 45–75 £/m² |
| Mosaico vítreo | 24,92 £/m² | 20–60 £/m² |
| Cámara CCTV | 117,69 £/ud | 50–200 £ |
| Panel solar | 249,23 £/ud | 150–400 £ |
| Batería de ciclo profundo | 304,62 £/ud | 150–400 £ |
| Generador de respaldo | 1.661,54 £/ud | 800–3.000 £ |

## 6. Lo que queda abierto

1. **Ampliar la cesta de materiales.** El 32 % de anclas en materiales es el punto mejorable. Las
   familias sin ancla propia (`MT-DOM`, `MT-DPS`, `MT-VIDRIO`, `MT-CIELO`, `MT-ESTUCO`) dependen
   todavía del factor de categoría.
2. **Dispersión regional.** La matriz es una media nacional. Londres y el sureste están entre un 15 %
   y un 20 % por encima; Escocia, Gales, Irlanda del Norte y el norte de Inglaterra entre un 8 % y un
   15 % por debajo. Si el producto lo pide, el siguiente paso es un factor regional explícito.
3. **Coste de autónomo (CIS).** El modelo es de personal asalariado. Un subcontratista acogido al CIS
   no paga NI empresa ni pensión, pero asume sus propias vacaciones, bajas, herramientas y seguro.
   Es un perfil distinto que merece su propia tabla si el producto va a presupuestar para
   subcontratistas.
