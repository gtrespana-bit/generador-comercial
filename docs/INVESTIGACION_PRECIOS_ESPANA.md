# Investigación de precios de referencia — España (2026-08-22)

**Objetivo:** anclas de mercado observadas para la matriz nacional de precios
de recursos en EUR (`basedatos_partidas/salida/precios_recursos_espana.csv`).
Mismo contrato que las rondas LatAm: cada cifra conserva rango, fuente y
fecha; no son cotizaciones de tienda.

**Tasa de corte:** 1 USD = 0,8564 EUR (EUR/USD 1,1677, xe.com mid-market
22/08/2026; BCE 21/08/2026: 1,1681). Solo se usa para normalizar el precio
base USD antes de aplicar el factor de mercado; el resultado queda congelado
en EUR con fecha.

**Ámbito:** reformas y obra residencial en España. Precios de material sin
porte salvo indicación; mano de obra = tarifa facturada por oficio
(autónomo/empresa), sin IVA y sin cargas del empleador cuando se contrata
plantilla propia.

---

## 1. Mano de obra (€/hora, jornada normalizada a 8 h)

Fuentes: Convenio General del Sector de la Construcción 2024-2026 (BOE);
tablas 2026 de motordepresupuestos.com (albañiles y reformas, 10/06/2026);
tejarsantateresa.com (19/04/2026); autopromotor.info (coste empresa
~20,50 €/h); presunow.com (14/04/2026).

| Recurso | Tarifa central | Rango observado | Notas |
|---|---:|---|---|
| MO-OF1 / MO-OF1-ALB (oficial 1ª albañil) | 27 €/h | 22–32 €/h | Convenio + mercado 2026; Madrid/BCN en zona alta |
| MO-OF1-ALI (alicatador) | 28 €/h | 24–34 €/h | Alicatado 18–35 €/m² → tarifa de oficial alto |
| MO-OF1-PISO (solador) | 28 €/h | 24–34 €/h | Solado 15–30 €/m² |
| MO-OF1-ELE (electricista) | 29 €/h | 24–34 €/h | Oficio con demanda alta |
| MO-OF1-PLO (fontanero) | 29 €/h | 24–34 €/h | Idem |
| MO-OF1-PIN (pintor) | 24 €/h | 20–28 €/h | Banda baja del oficial |
| MO-OF1-SOLD (soldador) | 31 €/h | 26–36 €/h | Oficio escaso |
| MO-AYU (peón) | 18 €/h | 15–21 €/h | Peón 15–21 €/h (convenio base 9,44 €/h + pluses) |
| MO-AYU-ESP | derivado | — | Punto medio ayudante–oficial, como LatAm |
| Resto de oficiales | derivado | — | Del oficial general (metodología) |

## 2. Materiales (unidad física del catálogo)

Fuentes: tabla de materiales España 2026 de calculadora.aeco360.es
(08/06/2026); Leroy Merlin / Obramat / aislamientosgonzalez.com (placas de
yeso laminado, observación directa 2026); materialesalicante.com (cemento
almacén); Generador de Precios (unidades de obra, orden de magnitud).

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
| MT-JUN-CG2 | kg | 3,2 | 2,2–4,5 | mortero de juntas CG2 (retail 1–5 kg) |
| MT-AUT-NIV | kg | 0,44 | 0,32–0,56 | autonivelante saco 25 kg 8–14 € |
| MT-PASTA-YESO | kg | 0,42 | 0,30–0,60 | yeso/plaste de enlucido |
| MT-PIN-CAUCHO | l | 4,5 | 3,0–7,0 | pintura plástica mate (aeco360) |
| MT-PIN-ESMALTE | l | 10,0 | 8,0–14,0 | esmalte sintético |
| MT-BLQ-20 | ud | 2,3 | 1,8–2,8 | bloque hormigón 40×20×20 (aeco360) |
| MT-BLQ-15 | ud | 1,5 | 1,2–1,9 | proporcional al de 20 |
| MT-BLQ-10 | ud | 1,1 | 0,9–1,4 | proporcional al de 20 |
| MT-BLQ-ARC-15 | ud | 0,45 | 0,35–0,55 | ladrillo hueco doble 180–280 €/millar |
| MT-LADRILLO | ud | 0,35 | 0,25–0,45 | ladrillo macizo |
| MT-MADERA-EST | m³ | 520 | 420–620 | pino C24 estructural (aeco360) |
| MT-CONC-180 | m³ | 92 | 82–105 | premezclado puesto en obra |
| MT-CONC-210 | m³ | 100 | 90–115 | HA-25 puesto en obra |
| MT-CONC-250 | m³ | 108 | 96–122 | HA-30 |
| MT-CONC-300 | m³ | 118 | 105–132 | HA-35 |
| MT-MANTO-ASF | m² | 8,5 | 6,0–12,0 | lámina asfáltica prefabricada |
| MT-AISL-TERM | m² | 10,0 | 6,0–18,0 | XPS 50 mm 6–12; lana de roca 80 mm 10–18 |
| MT-PANEL-SAND | m² | 38 | 28–50 | panel sándwich 80 mm (aeco360) |
| MT-LAMINA-ZINC | m² | 16 | 12–22 | chapa grecada/prelacada |
| MT-TEJA-CRIOLLA | ud | 1,0 | 0,8–1,3 | teja árabe curva (12–22 €/m²) |
| MT-CANON | m³ | 7 | 4–12 | canon de vertido RCD en vertedero autorizado |
| MT-GEOTEXTIL | m² | 1,1 | 0,8–1,5 | geotextil no tejido |
| MT-POLIET | m² | 0,6 | 0,4–0,9 | lámina polietileno barrera vapor |
| MT-FORM-MADERA | m² | 10 | 8–14 | encofrado de madera amortizado |
| MT-PERFIL-ACERO | kg | 2,0 | 1,6–2,4 | perfil laminado cortado a medida |
| MT-ELECTRODO | kg | 4,5 | 3,0–6,0 | electrodo revestido |
| MT-PLO-PPR20 | m | 2,2 | 1,5–3,0 | PPR 20 mm (multicapa 20: 2–4 €/m, aeco360) |
| MT-PLO-PVC4 | m | 5,0 | 4,0–7,0 | PVC DN110 saneamiento (aeco360) |
| MT-ELE-CABLE | m | 0,65 | 0,45–0,90 | H07V-K 2,5 mm² (aeco360) |
| MT-ELE-TUB20 | m | 0,45 | 0,30–0,70 | tubo corrugado 20 mm |
| MT-ELE-MECA | ud | 5,0 | 3,0–8,0 | mecanismo estándar con placa |
| MT-BREAKER | ud | 8,5 | 6,0–12,0 | magnetotérmico |
| MT-DIFERENCIAL | ud | 32 | 25–45 | diferencial alta sensibilidad |
| MT-VIDRIO-6 | m² | 38 | 30–50 | vidrio flotado 6 mm cortado |
| MT-CIELO-DESM | m² | 11 | 8–14 | fibra mineral 60×60 |

## 3. Maquinaria y equipo (€/h salvo indicación)

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

- 17/17 recursos de mano de obra con referencia propia o derivada.
- Materiales y maquinaria sin observación directa se completan con la canasta
  nacional derivada (mediana de ratios sobre el precio base USD convertido a
  la tasa de corte), igual que en LatAm:
  `docs/METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md`.

## 5. Limitaciones conocidas

- Los precios de material no incluyen IVA (21 %; reformas de vivienda
  habitual pueden tributar al 10 %) ni porte salvo indicación.
- La mano de obra es tarifa de mercado facturada; el coste de empresa con
  cargas ronda 20,50 €/h (autopromotor.info) y no se usa para no duplicar
  cargas que cada empresa aplica en su presupuesto.
- Zonas con tensión de demanda (Madrid, Barcelona, Baleares) quedan en la
  parte alta de los rangos; Extremadura/Castilla-La Mancha en la baja.
