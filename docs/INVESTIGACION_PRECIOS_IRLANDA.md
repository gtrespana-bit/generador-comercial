# Investigación de precios de referencia — Irlanda (2026-10-18)

**Objetivo:** anclas de mercado irlandesas observadas para la matriz de precios de recursos en EUR
(`basedatos_partidas/salida/precios_recursos_irlanda.csv`). Mismo contrato que las rondas de España,
LatAm y Reino Unido: cada cifra conserva rango, fuente y fecha, y no es una cotización de tienda.

**Tasa de corte:** 1 USD = 0,8886 EUR (EUR/USD 1,1253, tipo de referencia del BCE del 16/10/2026;
Yahoo Finance 1,1242 el 17/10). Solo normaliza el precio base USD antes de aplicar el factor de
mercado; el resultado queda congelado en EUR y con fecha.

**Ámbito:** reforma y obra residencial en la República de Irlanda. Materiales sin porte salvo
indicación y **sin IVA**: en Irlanda el tipo general es el 23 % y el reducido del 13,5 % aplica a
los servicios de construcción y reforma de vivienda, así que mezclar precios con IVA dentro de un
presupuesto sería un error de base. Mano de obra = **coste empresa**, no tarifa de autónomo.

> **Estado de esta ronda: primera fase.** 57 anclas investigadas sobre 388 recursos (15 %). Las
> familias sin ancla se derivan con el factor de su categoría y quedan marcadas como `derivado`.
> Lo que falta está listado en el apartado 6, sin adornos.

---

## 1. La advertencia que ordena todo lo demás

Los precios base de `basedatos_partidas/datos/recursos.json` están en USD pero su ámbito declarado
es **Venezuela** (`"mercado_base": "VE"`; un oficial de 1ª está a 5,5 USD/h). No son precios
internacionales ni precios europeos.

Por tanto **ninguna conversión de divisa puede producir un precio irlandés**: 5,5 USD/h son
4,89 EUR/h, y el coste empresa de un oficial irlandés es de 32,96 EUR/h. La matriz irlandesa se
reconstruye desde precios irlandeses, que es lo que hace este documento.

## 2. Mano de obra: el Sectoral Employment Order manda

La construcción irlandesa tiene tarifas mínimas legales por rama, fijadas por el **Sectoral
Employment Order** (SEO) del sector de la construcción. Las vigentes desde el **1 de agosto de
2026** son:

| Clasificación del SEO | €/hora |
| --- | ---: |
| Craftsperson | 23,74 |
| Categoría A | 23,03 |
| Categoría B | 21,37 |
| Nuevo entrante | 17,28 |

El SEO impone además una **aportación patronal al plan de pensiones de 32,89 € por semana y
trabajador** (21,95 € el trabajador), lo que añade 1.710,28 € al año por operario.

El coste empresa se construye en `tools/coste_empresa_irlanda.py`:

| Concepto | Parámetro |
| --- | --- |
| Jornada | 39 h/semana → 2.028 h contratadas al año |
| Vacaciones | 20 días de permiso anual + 9 festivos = 29 días |
| Bajas | 5 días de baja remunerada estatutaria (70 %, tope 110 €/día) |
| PRSI empresa | 11,40 % desde el 01/10/2026, sin techo |
| Pensión | 32,89 €/semana (SEO) |
| Despido | 2 semanas de salario por año de servicio, amortizadas al año |
| Horas facturables | 1.762,8 h/año |

Resultado: **32,96 €/h** facturable para un craftsperson y **29,81 €/h** para un operario general,
es decir un recargo del 20,7 % sobre el salario. El rango publicado (±8 % a +20 %) recoge la
dispersión real entre el oeste del país y el área de Dublín: el SEO es el suelo, no la tarifa de
mercado.

**Limitación declarada:** el SEO fija una sola tarifa de craftsperson, así que los 15 oficios
cualificados comparten base. Diferenciar por oficio exige la mediana del CSO por ocupación, que
esta ronda no ha levantado; el rango lo compensa en parte.

## 3. Maquinaria: alquiler por día de 8 horas

El alquiler irlandés se cotiza por día o por semana. Se adopta el día de 8 horas y se publica el
equivalente horario, sin IVA ni combustible, con operador solo donde el recurso lo declara.

| Equipo | Tarifa observada | €/h publicado |
| --- | --- | ---: |
| Miniexcavadora 3 t + martillo | 150 €/día + 60 €/día | 26,25 |
| Miniexcavadora 1,7 t | 120 €/día | 15,00 (derivado de familia) |
| Martillo neumático con compresor | 95 €/día | 11,88 |
| Pisón de zanja | 55 €/día | 6,88 |
| Plancha compactadora | 45 €/día | 5,63 |
| Hormigonera de un saco | 35 €/día | 4,38 |
| Torre móvil de aluminio 2,2 m | 45 €/día | 5,63 |
| Aspirador industrial clase M | 45 €/día | 5,63 |
| Nivel láser rotativo | 50 €/día | 6,25 |
| Camión volqueta 6 m³ con chofer | 480 €/día | 60,00 |
| Baño portátil (mensual) | 175 €/mes | unidad, no hora |

Fuentes: tarifas publicadas de Xcav8 (1,7 t a 120 €/día, 3 t a 150 €/día, 5 t a 450 €/semana),
DCM Hire y dublinplantanddiggerhire (rango 115–180 €/día para 1,5–3 t), consultadas el 18/10/2026.

## 4. Materiales: canasta observada

Precios de proveedor irlandés, **ex IVA**. Cuando la ficha del proveedor da el precio con IVA se
publica el valor sin IVA y se dice en la observación.

| Familia | Recurso | €/unidad | Rango | Fuente observada |
| --- | --- | ---: | --- | --- |
| Hormigón | `MT-CONC-180` (C16/20) | 100,00 /m³ | 92–115 | boqcalc Ireland; Roadstone |
| Hormigón | `MT-CONC-210` (C20/25) | 112,00 /m³ | 100–126 | boqcalc Ireland |
| Hormigón | `MT-CONC-250` (C25/30) | 126,00 /m³ | 115–140 | Hanly Quarries, 126,00 €/m³ ex IVA |
| Hormigón | `MT-CONC-300` (C28/35) | 132,00 /m³ | 122–150 | Hanly Quarries, 132,00 €/m³ ex IVA |
| Cemento | `MT-CEMENTO` | 0,30 /kg | 0,26–0,34 | Irish Cement 25 kg a 9,25–10,16 € con IVA |
| Áridos | `MT-ARENA` | 45,00 /m³ | 32–65 | boqcalc 28 €/m³ suelta; big bag 50,81 € ex IVA |
| Áridos | `MT-GRAVILLA` | 48,00 /m³ | 38–62 | cantera, por m³ suelto |
| Áridos | `MT-PIEDRA-PIC` | 42,00 /m³ | 32–55 | clause 804, por m³ suelto |
| Zahorra | `MT-MAT-PRESTAMO` | 36,00 /m³ | 28–48 | clause 804 / MOT Type 1 |
| Agua | `MT-AGUA-OBRA` | 2,40 /m³ | 1,90–3,00 | tarifa industrial |
| Bloques | `MT-BLQ-10` (440×215×100, 7,5 N) | 1,45 /ud | 1,25–1,85 | Goodwins 1,50 € ex IVA; TJ O'Mahony 1,37 € trade |
| Bloques | `MT-BLQ-12` (140 mm) | 2,05 /ud | 1,80–2,60 | Grange, bloque de 6" |
| Bloques | `MT-BLQ-15` (215 mm) | 2,60 /ud | 2,30–3,20 | TJ O'Mahony 2,60 € ex IVA |
| Placa yeso | `MT-PYL-PLACA125` | 6,40 /m² | 5,40–8,00 | Chadwicks Wallboard 2438×1200: 18,84 € ex IVA |
| Placa yeso | `MT-PYL-PLACA` (15 mm) | 7,60 /m² | 6,40–9,50 | Brooks / Chadwicks, hoja de 8×4 |
| Placa yeso | `MT-PYL-PLACA-IG` (Fireline) | 8,45 /m² | 7,20–10,60 | TJ O'Mahony 24,35 € trade la hoja |
| Aislamiento | `MT-PYL-LANA` | 7,20 /m² | 5,60–9,50 | Woodie's Earthwool 200 mm, 5,50 m² a 54,99 € |
| Yeso | `MT-YESO-REP` | 0,65 /kg | 0,55–0,85 | Gyproc Skimcoat 25 kg a 16,22–17,44 € ex IVA |
| Yeso | `MT-PASTA-YESO` | 0,68 /kg | 0,55–0,90 | pasta de agarre, saco de 25 kg |
| Placa yeso | `MT-PYL-PASTA` | 0,75 /kg | 0,60–1,00 | compuesto de juntas 25 kg a 17,03 € |
| Cerámica | `MT-ADH-C2TE` | 1,33 /kg | 1,15–1,60 | Brooks Arc Proflex 20 kg: 26,56 € ex IVA |
| Cerámica | `MT-ADH-C1` | 0,83 /kg | 0,70–1,00 | Brooks Arc Rapid Set 20 kg: 16,50 € ex IVA |
| Cerámica | `MT-JUN-CG2` | 2,59 /kg | 2,20–3,20 | Brooks Pro-Line 5 kg: 12,97 € ex IVA |
| Cerámica | `MT-GROUT` | 2,30 /kg | 1,90–2,90 | formato profesional de 10 kg |
| Pintura | `MT-PIN-CAUCHO` | 1,90 /l | 1,60–2,40 | Screwfix Leyland Retail 10 L a 20,95 € con IVA |
| Pintura | `MT-PIN-FONDO` | 2,30 /l | 1,90–3,00 | imprimación acrílica de fondo |
| Madera | `MT-MADERA-LISTON` | 2,60 /m | 2,10–3,40 | listón 100×44 mm: 12,47 € ex IVA la pieza de 4,8 m |
| Electricidad | `MT-ELE-CABLE` | 1,55 /m | 1,30–1,90 | Screwfix 2,5 mm² 100 m a 187,95 € con IVA |
| Residuos | `MT-CANON` | 75,00 /m³ | 55–105 | contenedor 6 yd a 349 € con IVA; tasas 85 €/t + 10 €/t |
| Residuos | `MT-CANON-TIERRA` | 45,00 /m³ | 32–62 | tasa de valorización sobre tierra |

Fuentes consultadas el 18/10/2026: Chadwicks, TJ O'Mahony, Brooks, Goodwins, Murdock Builders
Merchants, Grange, Woodie's, Screwfix Irlanda, Hanly Quarries, boqcalc Ireland y Kollect (guía de
contenedores 2026).

## 5. Residuos: la tasa explica el precio

Desde marzo de 2026 la **tasa de vertedero es de 85 €/t** y la **tasa de valorización de 10 €/t**
se aplica a toda la red de tratamiento de residuos de construcción y demolición. Un contenedor de
6 yardas (~4,6 m³) cuesta entre 280 y 400 € con IVA según operador y condado. Por eso el canon
irlandés por m³ (75 €) es varias veces el español: no es inflación del proveedor, es política
fiscal.

## 6. Lo que falta, dicho sin adornos

Familias **sin ancla irlandesa** en esta ronda (se publican derivadas, con confianza `derivado`):

* Fontanería (`MT-PLO`, `MT-TUB`, `MT-VALV`, `MT-TRAGANTE`, `MT-ACC`): tubería de cobre, PPR, PVC y
  grifería. Hay referencia de cobre (Screwfix 15 mm × 3 m a 20,45 € con IVA) sin incorporar aún.
* Electricidad de aparamenta (`MT-ELE-CAJA`, `MT-ELE-MECA`, `MT-ELE-PROV`, `MT-TOMA`, `MT-CABLE-*`,
  `MT-DPS`, `MT-DIFERENCIAL`, `MT-BREAKER`): mecanismos, cuadros y protecciones.
* Cubierta (`MT-TEJA`, `MT-CUMBRERA`, `MT-CANAL`, `MT-BAJANTE`): teja, slate y evacuación de aguas.
* Carpintería y vidrio (`MT-MARCO`, `MT-CERRADURA`, `MT-VIDRIO`, `MT-ESPEJO`).
* Climatización y domótica (`MT-DUCTO`, `MT-DOM`, `MT-REGUL`).
* Seguridad en obra (`MT-EPP`, `MT-ARNES`, `MT-RED`, `MT-LINEA`, `MT-BARANDA`).

Dieciocho recursos derivados se sustituyen por el ancla británica convertida (1,1846 EUR/GBP) porque
el factor de su familia se separaba más del doble de ese valor; van marcados en la observación. Es
una referencia provisional, no un precio irlandés.

**Prioridad de la siguiente ronda:** fontanería y electricidad de aparamenta, que son las dos
familias con más peso en una reforma de baño o cocina y las que hoy descansan en un factor de
categoría.
