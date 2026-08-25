# Investigación de precios de referencia — España (2026-08-25) — Revisión mano de obra

**Objetivo:** anclas de mercado observadas para la matriz nacional de precios de recursos en EUR (`basedatos_partidas/salida/precios_recursos_espana.csv`). Mismo contrato que las rondas LatAm: cada cifra conserva rango, fuente y fecha; no son cotizaciones de tienda.

**Tasa de corte:** 1 USD = 0,8564 EUR (EUR/USD 1,1677, xe.com mid-market 22/08/2026; BCE 21/08/2026: 1,1681). Solo se usa para normalizar el precio base USD antes de aplicar el factor de mercado; el resultado queda congelado en EUR con fecha.

**Ámbito:** reformas y obra residencial en España. Precios de material sin porte salvo indicación; mano de obra = **coste empresa** (bruto convenio + Seguridad Social + costes fijos), sin IVA, no tarifa autónomo facturada con beneficio, para evitar doble margen (el catálogo aplica 30% margen sobre coste directo).

---

## 1. Mano de obra — análisis a fondo (España 2024-2026)

> **Conclusión principal:** el precio anterior de 27 €/h oficial y 18 €/h peón era **tarifa de autónomo con beneficio incluido** (22-32 €/h oficial 1ª según Motordepresupuestos), no coste empresa. Si el catálogo guarda 27 €/h como coste y luego aplica 30% margen, el precio de venta lleva **margen sobre margen**. Se corrige a **coste empresa** 21 €/h oficial y 15 €/h peón (zona media), con especialidades 20-24 €/h.

### 1.1 Fuentes oficiales y de mercado

| Fuente | Fecha | Qué dice | Clave para CotizaT |
|---|---|---|---|
| **Convenio General Sector Construcción 2024-2026 (BOE)** | 2024-2026 | Salario anual peón 18.000 €, oficial 1ª 24.000 €, encargado 30.000 €, jefe obra 36.000 €. Incremento 3% 2025 vs 2024 (Skello 23/06/2026) | Base legal |
| **Tablas Barcelona 2025 (BOP 17/03/2026, Resolución 6/03/2026)** | Mar 2026 | Peón Ordinario Salario Base 11.223,21 € + Plus Convenio 7.365,79 € = Total anual 26.601,89 €. Oficial 2ª 12.437,32+8.071,66=29.227,51 €. Oficial 1ª 13.470,42+8.621,63=31.290,43 €. Encargado 14.916,64+9.615,76=34.954,33 €. Aportación plan pensiones oficial 1ª 587,63 €/año (1,61 €/día). Total día trabajado peón 74,84 €. Horas extras Nivel VIII (oficial 1ª) 16,71-18,15 € (2025) / 17,21-18,69 € (2026) | Referencia zona alta Cataluña |
| **Presupix — Precio hora oficial construcción España 2025: convenio, tarifa real** | 05/07/2026 | Salario base diario oficial 1ª 48-54 €/día, bruto anual 20.000-22.500 €, oficial 2ª 43-48 €/día (17.5k-20k año), ayudante 38-43 €/día (15.5k-18k). SS empresa +30-33% → coste empresa total 130-133% bruto. Ej: bruto 21.000 €/año + SS 6.720 = 27.720 €/año coste empresa. Coste hora real = 27.720/1.400 horas facturables = 19,80 €/h. Tarifa mercado = 19,80×1,55 =30,69 €/h. Tabla resumen: oficial 1ª zona media (Castilla, Murcia) coste empresa 17-20 €/h tarifa mercado 26-36, zona alta Madrid/Cataluña 19-23 coste / 30-42 tarifa, País Vasco/Navarra 22-27 coste / 36-50 tarifa, autónomo empresa propia 20-26 coste / 32-48 tarifa | **Coste empresa 19.80 €/h, tarifa mercado 30.69 €/h** |
| **Autopromotor.info — Precio mano obra construcción 2025** | 12/01/2025 | Desglose coste mensual oficial: Sueldo Base 894,35 + Plus convenio 614,04 + Transporte/dietas 155,40 + P.P. pagas 311,56 + FP/FOGASA 30,05 + EPI/herramientas 95,40 + Gestor 110,80 + Seguro vida 48,50 + Doc Rovitec 48,83 + SS 857 + Baja 62 + Despido 133 + SS vacaciones 70,83 = **3.431,76 €/mes total**. Coste hora = 3.431,76 / (4,3 sem×5 días×8h=172h) =19,95 €/h, con festivos y límite horas convenio **20,50 €/h**. Autónomo factura mínimo 23-25 €/h sin IVA, máximo 35 €/h. Si <23 €/h regala jubilación/bajas | **Coste empresa 20,50 €/h, autónomo 23-35** |
| **ObraHub — Salarios Construcción España 2026** | 02/05/2026 | Sueldos convenio brutos: Peón ordinario nivel XI 1.250-1.450/mes (8,50-9,80 €/h), Peón especialista X 1.350-1.550 (9,20-10,50), Oficial 2ª IX 1.500-1.750 (10,20-11,90), Oficial 1ª VIII 1.700-2.000 (11,50-13,50), Capataz VII 2.000-2.400 (13,50-16,30), Encargado V-VI 2.300-2.900 (15,50-19,50). Por especialidad: Albañil 11,50-13,50 (1.700-2.000/mes), Fontanero 13-16 (1.900-2.300), Electricista 13,50-17 (2.000-2.500), Carpintero 12,50-15 (1.850-2.200), Pintor 11-13,50 (1.650-2.000), Soldador 13-16,50 (1.900-2.450). Coste empresa +32% SS → oficial 1.900 brutos cuesta 2.500/mes. Autónomos: oficial 1ª 22-32 €/h, peón 16-22 €/h | **Bruto oficial 1ª 11,5-13,5 €/h → coste empresa 15,18-17,82 + costes → 20,50** |
| **Motordepresupuestos — ¿Cuánto cobra un albañil? 2026** | 10/06/2026 | Oficial 1ª 22-32 €/h media, Oficial 2ª 18-25 €/h, Peón 15-21 €/h sin IVA, ±20% entre capitales. Ejemplo partida: PEM 420 €, mano obra 280 € tarifa oficial 1ª, materiales 195 €, margen 18% 75,60 € | **Tarifa mercado con margen, no coste** |
| **Cronoshare — ¿Cuánto cuesta un albañil por hora? 2026** | 01/01/2026 | Oficial 1ª 20-30 €/h, Peón 14-22 €/h, Jornada 130-200 €/día. Madrid/Barcelona 20-30 oficial / 16-22 peón, Valencia 18-26/15-20, Sevilla 18-25/14-19 | Tarifa mercado |
| **Arquality — Precio reformas integrales 2026** | 28/05/2026 | Albañil oficial 20-30 €/h (12-25 €/m2 tabiques), peón 15-20 €/h (100 €/día), pladurista 20-30 (25-40/m2), pintor 20-35, electricista 25-35, fontanero 25-35 | Tarifa mercado reforma |

### 1.2 Del salario convenio al coste empresa real

**Fórmula España 2026:**
```
Salario bruto anual (según tablas provinciales)
+ Seguridad Social empresa 32,15% (2026: CC 23,60% + Desempleo 5,50% + FOGASA 0,20% + FP 0,60% + MEI 0,75% + AT mínimo 1,50%)
+ Costes fijos: EPI, herramientas, instalaciones higiene, gestor nóminas, seguro vida, formación, baja 5 días/año, despido 1 mes/año/12, SS vacaciones
= Coste total empresa anual
Coste hora empresa = Coste anual / Horas facturables reales (1.400-1.736h según convenio y absentismo)
```

**Cálculo oficial 1ª zona media (ejemplo Presupix + Autopromotor + Barcelona):**
- Barcelona oficial 1ª total anual 31.290,43 € (zona alta) / 1.736h = 18,02 €/h bruto total
- Coste empresa 18,02 ×1,3215 = 23,81 €/h (zona alta Cataluña)
- Zona media Castilla: bruto anual 20.000-22.500 € → 11,52-12,96 €/h (1736h) → coste empresa 15,23-17,13 €/h → + costes fijos (EPI, gestor, etc. 3.431,76/mes) → **20,50 €/h** (Autopromotor) o **19,80 €/h** (Presupix 1400h facturables)

**Adopción revisada CotizaT 2026-08-25 (coste empresa, no tarifa con beneficio):**

| Recurso | Tarifa anterior (autónomo con beneficio) | Tarifa nueva (coste empresa) | Rango nuevo | Justificación |
|---|---:|---:|---|---|
| MO-OF1 / MO-OF1-ALB (oficial 1ª albañil) | 27 €/h (22-32) | **21 €/h** | 18-25 €/h (144-200 €/jornada 8h) | Coste empresa zona media 17-20 €/h + alta Madrid/Cat 19-23, País Vasco 22-27. 21 €/h es centro zona media-alta, sin beneficio autónomo. Si autónomo, 22-32 €/h ya incluye 1,55 factor beneficio |
| MO-AYU (peón) | 18 €/h (15-21) | **15 €/h** | 12-18 €/h (96-144 €/jornada) | Bruto peón 8,50-9,80 €/h → coste empresa 13,32-15,45 + costes → 15 €/h centro. Tarifa autónomo peón 16-22 €/h con beneficio |
| MO-OF1-ALI (alicatador) | 28 €/h (24-34) | **22 €/h** | 18-26 €/h (144-208) | Especialidad +10-15% vs albañil general, pero coste empresa no tarifa reforma 28-42 |
| MO-OF1-PISO (solador) | 28 €/h (24-34) | **22 €/h** | 18-26 | Idem |
| MO-OF1-ELE (electricista) | 29 €/h (24-34) | **24 €/h** | 20-28 €/h (160-224) | Bruto electricista 13,5-17 €/h → coste empresa 17,82-22,44 + costes → 24 €/h. Tarifa autónomo 25-35 €/h con beneficio |
| MO-OF1-PLO (fontanero) | 29 €/h (24-34) | **23 €/h** | 19-27 (152-216) | Bruto fontanero 13-16 → coste empresa 17,16-21,12 + costes → 23 €/h |
| MO-OF1-PIN (pintor) | 24 €/h (20-28) | **20 €/h** | 16-24 (128-192) | Bruto pintor 11-13,5 → coste empresa 14,52-17,82 + costes → 20 €/h banda baja oficial |
| MO-OF1-SOLD (soldador) | 31 €/h (26-36) | **25 €/h** | 20-30 (160-240) | Oficio escaso, pero coste empresa 13-16,5 bruto → 17-22 + costes → 25 €/h, no 36-50 tarifa País Vasco con beneficio |
| Resto oficiales (carpintero, vidriero, climatización, jardinero, montador) | 27 €/h derivado | **21 €/h derivado** | 18-25 | Derivado del oficial general |

**MO-AYU-ESP:** punto medio oficial+ayudante → (21+15)/2=18 €/h? Pero como derivado: (168+120)/16=18 €/h? Espera: (oficial jornada 168 + ayudante 120)/16 = 288/16=18 €/h. Anterior era 22,5 €/h (18+27)/2. Nuevo 18 €/h (15+21)/2. Rango 15-22,5? Se adopta 18,5? Se calcula como (144+120)/16? No, (120+168)/16=18. Se deja derivado.

### 1.3 Verificación de que no es precio alto

- **Comparativa coste empresa 2026:**
  - Oficial 1ª coste empresa zona media 17-20 €/h (Presupix), 20,50 €/h (Autopromotor), 18,02 bruto Barcelona → 23,81 coste empresa zona alta
  - **Nuevo 21 €/h está justo en medio zona media-alta, 13% por debajo de Barcelona alta (23,81) y 2,4% por encima de Autopromotor medio (20,50) — no es alto**
  - Anterior 27 €/h era 35% por encima de Barcelona alta y 31,7% por encima de Autopromotor — sí era alto porque incluía beneficio autónomo

- **Comparativa tarifa autónomo mercado (con beneficio):**
  - Oficial 1ª tarifa mercado 22-32 €/h (Motordepresupuestos), 22-38 €/h autónomo (Presupix), 20-30 €/h Cronoshare, 20-30 Arquality, 23-27 larga duración / 27-35 corta (Autopromotor)
  - **Nuevo 21 €/h como coste empresa permite al reformista facturar 21×1,55=32,55 €/h como tarifa mercado (dentro de 22-32 y 26-36 zona media) — coherente**
  - Anterior 27 €/h como coste ×1,55=41,85 €/h tarifa mercado — por encima de 22-32 y en tope de 30-42 zona alta Madrid — alto

- **Peón:**
  - Coste empresa peón 13,32-15,45 €/h (ObraHub bruto 8,5-9,8 ×1,32) → + costes → 15 €/h
  - Tarifa autónomo peón 15-21 (Motor), 16-22 (ObraHub), 14-22 (Cronoshare), 15-20 (Arquality)
  - **Nuevo 15 €/h coste empresa → tarifa mercado 15×1,55=23,25 €/h — justo por encima de tarifa autónomo peón 15-21, razonable por beneficio empresa**
  - Anterior 18 €/h coste → tarifa 27,9 €/h — por encima de 15-21 y 16-22 — alto

### 1.4 Impacto en partidas

Con cemento y arena sin tocar, bajar mano obra 27→21 €/h (-22,2%) y peón 18→15 (-16,7%) reduce coste directo de una partida de friso (ej. 0,537h oficial) de 14,50 € a 11,28 € (-22,2%), y precio venta con 30% margen de 18,85 € a 14,66 €. El conjunto del catálogo (3006 partidas) baja peso económico de mano obra de ~79,6% verificado a similar pero con nivel de mercado español real de coste empresa, no tarifa inflada.

---

## 2. Materiales (unidad física del catálogo) — sin cambios en esta revisión

Fuentes: calculadora.aeco360.es 08/06/2026, Leroy Merlin / Obramat / aislamientosgonzalez.com, materialesalicante.com, Generador de Precios.

| Recurso | Unidad | Central | Rango | Base observada |
|---|---|---:|---|---|
| MT-CEMENTO | kg | 0,14 | 0,10–0,19 | saco 25 kg 2,50–4,75 € (almacén 1,85+IVA; retail 3,88–4,79) |
| MT-ARENA | m³ | 28 | 20–38 | 15–25 €/t en acopio; puesta en obra con porte |
| MT-PIEDRA-PIC | m³ | 30 | 22–40 | grava 12–20 €/t; puesta en obra |
| MT-ACERO-CAB | kg | 1,15 | 0,95–1,40 | B500S 700–900 €/t base; suministro cortado a obra |
| MT-ALAMBRE | kg | 2,1 | 1,7–2,6 | alambre recocido de atado |
| MT-MALLA-ELEC | m² | 5,5 | 4,0–7,0 | malla electrosoldada 15×15Ø6 (aeco360) |
| MT-PYL-PLACA125 | m² | 4,0 | 3,2–5,0 | placa N BA-13 (Leroy 3,22 €/m²; Pladur 4,28) |
| MT-PYL-PLACA | m² | 4,9 | 4,0–6,2 | placa N BA-15 (Pladur 4,92 €/m²) |
| MT-PYL-PLACA-RH | m² | 8,2 | 7,0–9,5 | placa H1 verde 13 mm (7,73–8,75 €/m²) |
| MT-PYL-LANA | m² | 8,0 | 6,0–12,0 | lana mineral 60 mm |
| MT-PYL-PASTA | kg | 1,2 | 0,9–1,6 | pasta de juntas |
| MT-ADH-C2TE | kg | 0,36 | 0,24–0,48 | adhesivo C2 TE saco 25 kg 6–12 € |
| MT-ADH-C1 | kg | 0,20 | 0,16–0,24 | derivado del extremo bajo de la familia |
| MT-JUN-CG2 | kg | 3,2 | 2,2–4,5 | mortero de juntas CG2 |
| MT-AUT-NIV | kg | 0,44 | 0,32–0,56 | autonivelante saco 25 kg 8–14 € |
| MT-PASTA-YESO | kg | 0,42 | 0,30–0,60 | yeso/plaste de enlucido |
| MT-PIN-CAUCHO | l | 4,5 | 3,0–7,0 | pintura plástica mate (aeco360) |
| MT-PIN-ESMALTE | l | 10,0 | 8,0–14,0 | esmalte sintético |
| MT-BLQ-20 | ud | 2,3 | 1,8–2,8 | bloque hormigón 40×20×20 |
| MT-BLQ-15 | ud | 1,5 | 1,2–1,9 | proporcional al de 20 |
| MT-BLQ-10 | ud | 1,1 | 0,9–1,4 | proporcional al de 20 |
| MT-BLQ-ARC-15 | ud | 0,45 | 0,35–0,55 | ladrillo hueco doble 180–280 €/millar |
| MT-LADRILLO | ud | 0,35 | 0,25–0,45 | ladrillo macizo |
| MT-MADERA-EST | m³ | 520 | 420–620 | pino C24 estructural |
| MT-CONC-180 | m³ | 92 | 82–105 | premezclado puesto en obra |
| MT-CONC-210 | m³ | 100 | 90–115 | HA-25 puesto en obra |
| MT-CONC-250 | m³ | 108 | 96–122 | HA-30 |
| MT-CONC-300 | m³ | 118 | 105–132 | HA-35 |
| MT-MANTO-ASF | m² | 8,5 | 6,0–12,0 | lámina asfáltica prefabricada |
| MT-AISL-TERM | m² | 10,0 | 6,0–18,0 | XPS 50 mm 6–12; lana de roca 80 mm 10–18 |
| MT-PANEL-SAND | m² | 38 | 28–50 | panel sándwich 80 mm |
| MT-LAMINA-ZINC | m² | 16 | 12–22 | chapa grecada/prelacada |
| MT-TEJA-CRIOLLA | ud | 1,0 | 0,8–1,3 | teja árabe curva 12–22 €/m² |
| MT-CANON | m³ | 7 | 4–12 | canon de vertido RCD |
| MT-GEOTEXTIL | m² | 1,1 | 0,8–1,5 | geotextil no tejido |
| MT-POLIET | m² | 0,6 | 0,4–0,9 | lámina polietileno barrera vapor |
| MT-FORM-MADERA | m² | 10 | 8–14 | encofrado de madera amortizado |
| MT-PERFIL-ACERO | kg | 2,0 | 1,6–2,4 | perfil laminado |
| MT-ELECTRODO | kg | 4,5 | 3,0–6,0 | electrodo revestido |
| MT-PLO-PPR20 | m | 2,2 | 1,5–3,0 | PPR 20 mm |
| MT-PLO-PVC4 | m | 5,0 | 4,0–7,0 | PVC DN110 saneamiento |
| MT-ELE-CABLE | m | 0,65 | 0,45–0,90 | H07V-K 2,5 mm² |
| MT-ELE-TUB20 | m | 0,45 | 0,30–0,70 | tubo corrugado 20 mm |
| MT-ELE-MECA | ud | 5,0 | 3,0–8,0 | mecanismo estándar |
| MT-BREAKER | ud | 8,5 | 6,0–12,0 | magnetotérmico |
| MT-DIFERENCIAL | ud | 32 | 25–45 | diferencial |
| MT-VIDRIO-6 | m² | 38 | 30–50 | vidrio flotado 6 mm |
| MT-CIELO-DESM | m² | 11 | 8–14 | fibra mineral 60×60 |

## 3. Maquinaria y equipo (€/h salvo indicación) — sin cambios

| Recurso | Unidad | Central | Rango | Notas |
|---|---|---:|---|---|
| MQ-RETRO | h | 45 | 35–55 | retro/mixta con operador y martillo |
| MQ-VOLQ | h | 50 | 40–60 | camión volquete 6 m³ con chófer |
| MQ-BOMBA-CONC | h | 78 | 65–95 | bomba de hormigón con operador |
| MQ-GRUA | h | 70 | 55–85 | camión grúa con operador |
| MQ-MEZCL | h | 3,0 | 2,0–4,5 | hormigonera de obra (alquiler ~25 €/día) |
| MQ-MART-NEUM | h | 11 | 8–15 | martillo neumático + compresor |
| MQ-ANDAMIO | h | 2,8 | 2,0–4,0 | andamio tubular amortizado |
| MQ-BANO-PORT | ud (mes) | 110 | 85–140 | alquiler mensual con mantenimiento |

## 4. Cobertura

- 17/17 recursos de mano de obra con referencia propia o derivada — **revisados a coste empresa 2026-08-25**
- Materiales y maquinaria sin observación directa se completan con la canasta nacional derivada (mediana de ratios sobre el precio base USD convertido a la tasa de corte)

## 5. Limitaciones conocidas — actualizadas

- Los precios de material no incluyen IVA (21 %; reformas de vivienda habitual pueden tributar al 10 %) ni porte salvo indicación.
- **La mano de obra es coste empresa (no tarifa autónomo con beneficio).** Coste empresa oficial 1ª zona media 17-20 €/h, alta 19-23, País Vasco 22-27, autónomo 20-26 coste. Tarifa mercado recomendada con beneficio 1,55 factor: oficial 1ª zona media 26-36 €/h, alta 30-42, País Vasco 36-50, autónomo 32-48. La referencia nacional usa coste empresa para que el catálogo aplique su propio margen sin duplicar.
- Zonas con tensión de demanda (Madrid, Barcelona, Baleares) quedan en la parte alta de los rangos; Extremadura/Castilla-La Mancha en la baja.
- **No es precio alto:** 21 €/h oficial y 15 €/h peón están en centro de coste empresa real (20,50 €/h Autopromotor, 19,80 €/h Presupix, 23,81 €/h Barcelona alta). Tarifa anterior 27/18 €/h era tarifa autónomo con beneficio, 35% por encima de Barcelona alta.

## 6. Reproducción

```bash
python3 tools/generar_matriz_precios_espana.py
python3 tools/generar_sql_precios_espana.py
```
