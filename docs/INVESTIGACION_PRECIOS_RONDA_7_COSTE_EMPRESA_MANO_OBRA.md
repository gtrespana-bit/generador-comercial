# Investigación de precios — Ronda 7: coste real de la mano de obra para la empresa (Latam)

**Fecha de corte:** 2026-09-08
**Alcance:** 16 mercados Latam del catálogo (CO, PE, MX, EC, PA, SV, CL, AR, DO, UY, PY, BO, CR, GT, HN, NI). España ya fue revisada a coste-empresa en `docs/INVESTIGACION_PRECIOS_ESPANA.md` (2026-08-25) y no se modifica aquí.

> **Motivo.** Las horas de mano de obra publicadas hasta ahora eran el **jornal de mercado ÷ 8**, es decir lo que cobra el trabajador (o el mercado pide) por jornada, **sin** lo que la empresa paga además: aportes patronales, seguridad social, pagas extras, vacaciones y demás prestaciones legales. Eso deja el coste real **corto**. La política del catálogo («tarifas = coste; el margen se aplica encima») exige que la referencia nacional sea el **coste que asume la empresa**, no el sueldo del trabajador.

## Regla adoptada

```text
coste-empresa por hora = jornal bruto de mercado × factor de coste-empresa ÷ 8 h
factor de coste-empresa = 1 + aportes patronales (SS/seguridad social) + provisiones de prestaciones (paga extra, vacaciones, cesantía/indemnización)
```

- El **jornal bruto de mercado** por país y oficio es el investigado en la ronda 5 y las rondas país (2026-08-25): `docs/INVESTIGACION_PRECIOS_RONDA_5_MANO_OBRA.md`, `INVESTIGACION_PRECIOS_CL_AR.md`, `INVESTIGACION_PRECIOS_DO_UY_PY.md`, `INVESTIGACION_PRECIOS_PA_SV.md`, `INVESTIGACION_PRECIOS_BO_CR_GT.md`, `INVESTIGACION_PRECIOS_HN_NI.md`.
- Se aplica el **factor legal de una empresa formalizada** que contrata por jornada. Donde el mercado observado es mayoritariamente informal (jornal que "pide" el trabajador), el factor documenta el coste de formalizar: exactamente lo que pide el usuario ("lo que le cuesta a la empresa tener ese trabajador").
- **No** se añade margen de beneficio ni tarifa de autónomo: eso lo pone el 30–35 % de margen del catálogo encima del coste (política `basedatos_partidas/README.md`). No hay doble margen.
- El rango min–max de cada fila conserva el rango de mercado observado multiplicado por el mismo factor (la incertidumbre de mercado sigue siendo la misma; la carga legal es tasa fija).

## Factor por país (detalle y fuentes)

| País | Factor | Cargas incluidas | Fuentes (2025–2026) |
|---|---:|---|---|
| CO Colombia | **1,45** | Pensión 12 % + ARL clase V 6,96 % + caja de compensación 4 % = 22,96 % (exento parafiscales SENA/ICBF y salud para <10 SMMLV, art. 114-1 Ley 1607) + prestaciones 21,83 % (cesantías 8,33 + prima 8,33 + intereses 1 + vacaciones 4,17). Sin exención el total sería 58,3 % (1,58). | Andasolutions calculadora 27/05/2026; oneestimate 31/05/2026 (52–58 %); calculadoranomina.co 26/03/2026 (SMMLV 2026 1.750.905 COP, auxilio 249.095) |
| MX México | **1,46** | IMSS patronal ≈35,7 % sobre SBC (componentes fijos 26,15 % + cesantía/vejez 7,51 % para >4 UMA + riesgos de trabajo ≈2 %) con factor de integración 1,0493 (aguinaldo 15 días + 12 días vacaciones × 25 % prima) ≈ 37,4 % del salario + pago de aguinaldo/prima/vacaciones 8,2 %. | Teamed Mexico 13/06/2026 (26,15 % fijos; coste total 130–140 %); cifrasnet 2026 (25–35 % + ISN); hacecuentas 2026 (factor 1,0493); tucalculadorasat 10/07/2026 |
| PE Perú | **1,45** | EsSalud 9 % (Ley 26790) + gratificaciones 2 × (1 + 9 % bonificación) /12 = 18,17 % (Leyes 27735 y 30334) + CTS ≈9,75 % (DL 650, incluye 1/6 de gratificación) + vacaciones 30 días 8,33 % (DL 713). Sin asignación familiar (S/ 113/mes) ni utilidades. | Krowdy 06/08/2026 (≈45 % adicional); Deel 24/07/2026 (40–55 %); FacturaSimple 29/03/2026 (44 %) |
| EC Ecuador | **1,35** | IESS patronal 11,15 % + IECE 0,50 % + SECAP 0,50 % = 12,15 % + décimo tercero 8,33 % + décimo cuarto ≈7,5 % (1 SBU = 482 USD fijo sobre jornales de ~528–565 USD/mes) + vacaciones 4,17 % + fondo de reserva 8,33 % (desde el año 2). Sin fondo de reserva: 1,32; con fondo: 1,40 → se adopta el punto medio. | Deltech Audit 29/04/2026 (636,16 / 676,31 sobre 482 = 1,32 / 1,40); rolesdepago 16/04/2026 (12,15 %); tagline 15/07/2026 |
| CL Chile | **1,25** | Seguro de cesantía 3 % (contrato por obra/faena) + SIS ≈1,53 % + mutualidad Ley 16.744 0,90 % + tasa diferenciada ≈1,5 % + cotización adicional reforma previsional 3,5 % (vigente ago-2026, sube hasta 8,5 % en 2033) ≈ 10,4 % + vacaciones/feriados/gratificación/provisión indemnización ≈15 %. **Corrección:** la ronda CL estimaba +35–40 % mezclando AFP 10 % y salud 7 %, que **descuenta el trabajador**, no paga la empresa. | orgdch 2026 (resumen empleadores reforma previsional); MP Asociados 24/05/2026 (empleador ≈5,5–7 % + riesgo); Teamed Chile 13/06/2026 (0,90 % base + riesgo hasta 3,4 %) |
| AR Argentina | **1,50** | Contribuciones patronales construcción (UOCRA) ≈23 % (incluye ART sectorial de riesgo alto ≈10 %) + fondo de cese 12 % + SAC (aguinaldo) 8,33 % + provisión vacaciones ≈6 %. Rango publicado 35–40 % sin SAC y ≈45–50 % anualizado. | hacecuentas UOCRA 2026 (bruto oficial 900.000 ARS, contribuciones 23 %, fondo cese 12 %); estudiorizzo 2026 (cargas ≈21,5 % + ART ≈10 % construcción); servidos 22/06/2026 |
| DO Rep. Dominicana | **1,30** | TSS empleador 16,39 % (SFS 7,09 + AFP 7,10 + SRL 1,20 + INFOTEP 1,00) + regalía pascual 8,33 % + vacaciones 4,17 % + provisión cesantía ≈5 %. Rango publicado 28,8 % (sin cesantía) a ~33 %. | tuFacturaRD 16/04/2026 (16,39 % total empleador); gestiondo 11/08/2026 (28,8 % con provisiones); siemprealdia 2025 (tasas por rama) |
| UY Uruguay | **1,32** | BPS patronal 12,625 % (jubilatorio 7,50 + FONASA 5,00 + FRL 0,10 + FGCL 0,025) + BSE seguro accidentes ≈4 % (construcción, rango 0,49–10 %) + aguinaldo 8,33 % + salario vacacional 5,5 %. | datosuruguay 2026; cuantomecuesta UY 2026; OpenAccountants 04/06/2026 (12,625 %) |
| PY Paraguay | **1,30** | IPS 16,5 % (pensión + salud + accidentes) + seguro de riesgo laboral ≈1,5 % + aguinaldo 8,33 % + vacaciones ≈3,3 % + provisión indemnización 15 días ≈4 %. Total publicado 125–135 % del bruto. | Employsome Paraguay 25/06/2026 (16,5 % + 1–2 % + aguinaldo + cesantía = 125–135 %) |
| BO Bolivia | **1,36** | SIP/AFP patronal 4,71 % (3 % + 1,71 % riesgo común) + CNS 10 % + prima vivienda 2 % = 16,71 % + aguinaldo 8,33 % + indemnización 8,33 % (1 mes/año, única en la región aplicable también a renuncia) + vacaciones 4,17 %. Cálculo publicado: 35,5 % sobre el SMN. | boliviaempresas 06/06/2026 (3.388 sobre 2.500 = 1,355); finiquitojusto 18/06/2026 (SMN 3.300, DS 5516); boliviatrabajos 2026 |
| CR Costa Rica | **1,41** | CCSS patronal 26,83 % (2026: IVM sube 5,42 → 5,58) + INS riesgos del trabajo ≈2,5 % + aguinaldo 8,33 % + vacaciones 4,17 %. Total publicado ≈39 %. | BDO CR 11/12/2025 (26,83 % 2026); GlobalEx 19/12/2025; Employsome CR 22/04/2026 (39 % total) |
| GT Guatemala | **1,43** | IGSS patronal 10,67 % + IRTRA 1 % + INTECAP 1 % = 12,67 % + bono 14 8,33 % + aguinaldo 8,33 % + vacaciones 4,17 % + provisión indemnización 9,72 % (integra bono y aguinaldo). Total publicado 41,83 %; rango 1,45–1,55× del salario nominal. | calculogt 21/07/2026 (33,5 % sin indemnización; 41,83 % con); asesoríaglobal 29/04/2026 (12,67 % + 30,55 % pasivo); Prensa Libre 26/01/2026 |
| HN Honduras | **1,25** | IHSS patrono 5 % + RAP patrono 1,5 % + INFOP 1 % = 7,5 % + aguinaldo 8,33 % + catorceavo ≈5 % (1 SMN fijo sobre jornales de ~800 HNL/día) + vacaciones 4,17 %. Rango publicado 25–30 % adicional. | koddix simulador 2026 (7,5 % + provisiones; 25–30 %); toptrabajos 30/03/2026 |
| NI Nicaragua | **1,40** | INSS patronal 21,5 % (<50 empleados) + INATEC 2 % = 23,5 % + aguinaldo 8,33 % + vacaciones 8,33 % (30 días/año). Con indemnización 8,33 % el total publicado es 46,5 % (1,46). | somosnortex 30/06/2026 (23,5 % + aguinaldo); BPN Nicaragua (46,5 % total); finiquitojusto 19/06/2026 |
| PA Panamá | **1,33** | CSS patronal 13,25 % + Seguro Educativo patronal 1,50 % + riesgos profesionales ≈1,5 % = 16,25 % + décimo tercer mes 8,33 % + vacaciones 8,33 % (1 mes por 11 trabajados). | vorluno 19/04/2026 (1.979,60 sobre 1.500 = 1,32); finiquitojusto 18/06/2026 (Decreto 13/2026; décimo tercero) |
| SV El Salvador | **1,26** | ISSS patronal 7,5 % (tope $1.000) + AFP patronal 8,75 % (sin tope) + INCAF 1 % = 17,25 % + aguinaldo ≈3,4 % (10–18 días) + vacaciones 15 días + 30 % ≈5,3 %. Ejemplo publicado: $500 → $640 (1,28). | saplic calculadora 2026 (cargas + provisiones); finiquitojusto 18/06/2026 (descuentos regionales 2026) |

## Valores adoptados (coste-empresa por hora = jornal × factor ÷ 8)

| País | Oficial 1ª base R5 (jornal) | × factor | **MO-OF1 nuevo** | **Δ vs anterior** | Ayudante base | **MO-AYU nuevo** | **Δ** |
|---|---|---|---|---:|---:|---:|---:|---:|
| CO | 110.000 COP | 1,45 | **19.937,50 COP/h** | +45 % | 72.500 → **13.140,63 COP/h** | +45 % |
| PE | 69,75 PEN | 1,45 | **12,64 PEN/h** | +45 % | 62,80 → **11,38 PEN/h** | +45 % |
| MX | 750 MXN | 1,46 | **136,88 MXN/h** | +46 % | 400 → **73,00 MXN/h** | +46 % |
| EC | 21,67 USD | 1,35 | **3,66 USD/h** | +35 % | 20,315 → **3,43 USD/h** | +35 % |
| CL | 55.000 CLP | 1,25 | **8.593,75 CLP/h** | +25 % | 35.000 → **5.468,75 CLP/h** | +25 % |
| AR | 45.624 ARS | 1,50 | **8.554,50 ARS/h** | +50 % | 38.808 → **7.276,50 ARS/h** | +50 % |
| DO | 2.000 DOP | 1,30 | **325,00 DOP/h** | +30 % | 900 → **146,25 DOP/h** | +30 % |
| UY | 2.412,65 UYU | 1,32 | **398,09 UYU/h** | +32 % | 1.554,29 → **265,58 UYU/h** | +32 % |
| PY | 125.875 PYG | 1,30 | **20.454,69 PYG/h** | +30 % | 107.627 → **17.489,39 PYG/h** | +30 % |
| BO | 270 BOB | 1,36 | **45,90 BOB/h** | +36 % | 140 → **23,80 BOB/h** | +36 % |
| CR | 13.991,86 CRC | 1,41 | **2.466,07 CRC/h** | +41 % | 13.523,69 → **2.383,55 CRC/h** | +41 % |
| GT | 220 GTQ | 1,43 | **39,33 GTQ/h** | +43 % | 130 → **23,24 GTQ/h** | +43 % |
| HN | 800 HNL | 1,25 | **125,00 HNL/h** | +25 % | 450 → **70,31 HNL/h** | +25 % |
| NI | 532,60 NIO | 1,40 | **93,21 NIO/h** | +40 % | 350 → **61,25 NIO/h** | +40 % |
| PA | 45 USD | 1,33 | **7,48 USD/h** | +33 % | 35 → **5,82 USD/h** | +33 % |
| SV | 28 USD | 1,26 | **4,41 USD/h** | +26 % | 16 → **2,52 USD/h** | +26 % |

Especialidades directas (CO electricista/plomero/pintor/soldador, MX idem, EC idem) se multiplican por el mismo factor; especialidades sin jornal local (MO-OF1-MON, CAB, CARP, CARPM, VIDR, AC, JARD y MO-AYU-ESP) se derivan de oficial/ayudante ya factorizados, por lo que heredan el coste-empresa.

## Verificación de coherencia (ni cortos ni pasados)

- **Contra el jornal informal:** el coste-empresa resultante está un 25–50 % por encima del jornal de mercado, en línea con los multiplicadores legales publicados por país (25–58 %). No se aplicó ningún factor de beneficio: multiplicar por 1,30 (30 % margen del catálogo) sobre el coste-empresa da la tarifa interna de venta.
- **Ejemplo CO:** jornal oficial 110.000 COP/día → coste-empresa 159.500 COP/día (19.937,50 COP/h) → tarifa con margen 30 % ≈ 25.918,75 COP/h. Los precios de mano de obra de mercado en Bogotá con prestaciones publicados por oneestimate (52 % de carga) están en ese entorno una vez formalizados.
- **Ejemplo EC:** jornal 21,67 USD/día → coste-empresa 29,25 USD/día (3,66 USD/h) → con margen ≈ 4,76 USD/h (38 USD/día). El coste real con beneficios publicado por Deltech sobre el SBU da exactamente el mismo multiplicador (1,32–1,40) aplicado aquí.
- **Riesgo de "pasarse":** los factores no incluyen costes indirectos de la empresa (gestoría, EPI, herramientas, transporte a obra, inactividad por lluvia). Esos siguen siendo costes propios que la empresa debe cubrir con su margen; incluirlos aquí duplicaría el margen. La política del catálogo se mantiene: **coste + margen encima**.

## Limitaciones

- Los jornales de mercado son referencias nacionales (capitales/zonas medias), no una encuesta formal; cada fila conserva rango y `referencia`/`derivado`.
- Las tasas de seguridad social cambian (p. ej. reforma previsional CL sube a 8,5 % en 2033; cesantía progresiva MX; IVM CR). La matriz es una fotografía fechada: fíjate en `fecha_consulta` y en `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md` antes de reutilizarla.
- Argentina (inflación alta) y CL (reforma previsional) requieren revisión trimestral; el resto, anual.
- La empresa siempre puede sobrescribir con su tarifa propia (jerarquía de `app/services/precios_mercado.py`: organización → nacional → base).
