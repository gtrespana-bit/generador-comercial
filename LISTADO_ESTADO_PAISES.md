# Estado de adaptación por país — análisis, partidas y recursos

**Fecha:** 2026-08-25 — CIERRE FINAL 18/18  
**Fuente:** `app/paises.py`, `basedatos_partidas/glosarios/`, `basedatos_partidas/salida/precios_recursos_*.csv`, `app/seo.py`, `app/seo_contenido.py`, `app/services/tasa.py`

> Listo = APU recalculable con precios mercado nacionales + partidas traducidas vía glosario + recursos 388 con precio nacional + SEO propio + tasa verificada

---

## ✅ PAÍSES LISTOS (18 de 18) — CIERRE TOTAL

| País | Código | Moneda | IVA | ID Fiscal | Glosario | Recursos nacionales | Tasa verificada | SEO | Estado |
|---|---|---|---|---|---|---|---|---|---|
| Venezuela | VE | USD | 16% | RIF | Base | 388 base `recursos.json` | 773.31 VES (BCV 18/08) | `/ve/` | LISTO nativo |
| Colombia | CO | COP | 19% | NIT | `CO.json` 142 | 388 — cemento 28k/50kg, arena 100k/m3, etc. | 3128.65 COP (TRM 19/08) | `/co/` | LISTO |
| México | MX | MXN | 16% | RFC | `MX.json` 112 | 388 | 17.06 MXN | `/mx/` | LISTO |
| Perú | PE | PEN | 18% | RUC | `PE.json` 93 | 388 | 3.37 PEN | `/pe/` | LISTO |
| Ecuador | EC | USD | 15% | RUC | `EC.json` 91 | 388 | 1.0 USD | `/ec/` | LISTO |
| Panamá | PA | USD (PAB 1:1) | 7% | RUC | `PA.json` 56 | 388 — cemento $8.25/42.5kg Novey/CEMEX/Doit, bloque $0.95 Panablock/HOPSA, arena $34/m3, concreto $125/m3 | PAB 1.0 | `/pa/` | LISTO 2026-08-25 |
| El Salvador | SV | USD | 13% | NIT | `SV.json` 57 | 388 — cemento $8.73 CASALCO, bloque $0.40, arena $35, grava $45.05, concreto $135.35 | USD 1.0 | `/sv/` | LISTO 2026-08-25 |
| Chile | CL | CLP | 19% | RUT | `CL.json` 66 | 388 — cemento $4.790/25kg (191.6 CLP/kg Sodimac Melón), bloque $1.840, arena $33.190/m3 EmpresasPro, hormigón $110k/m3 GlobalGTC | 925.90 CLP | `/cl/` | LISTO 2026-08-25 |
| Argentina | AR | ARS | 21% | CUIT | `AR.json` 65 | 388 — cemento $11.433/50kg Loma Negra/Holcim, bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3 ML | 1497.38 ARS | `/ar/` | LISTO 2026-08-25 |
| Rep. Dominicana | DO | DOP | 18% | RNC | `DO.json` 58 | 388 — cemento RD$535/funda 94lb (12.56 DOP/kg ControlObra/Ferremix), block 6'' RD$42 Yessenia/Mayol/Ferremix/SonProject, arena RD$1.550/m3, grava RD$1.700/m3 SonProject | 58.33 DOP (Xe 58.3369 24/08) | `/do/` | LISTO 2026-08-25 |
| Uruguay | UY | UYU | 22% | RUT | `UY.json` 58 | 388 — cemento $240/25kg (9.6 UYU/kg Otto Wulff/Barraca/EMAT), bloque 15x19x39 $70 Gallinal/EMAT/Sodimac, arena $1.200/m3, hormigón $5.500/m3 SAU | 40.21 UYU (Xe 40.2124 18/08) | `/uy/` | LISTO 2026-08-25 |
| Paraguay | PY | PYG | 10% | RUC | `PY.json` 57 | 388 — cemento Gs 59.000/50kg (1.180 PYG/kg Costeo/INC), bloque Gs 5.300 Clasipar, piedra Gs 104.000/m3, hormigón Gs 650.000/m3 | 5946.10 PYG (pluang 5946.10 08/08) | `/py/` | LISTO 2026-08-25 |
| Bolivia | BO | BOB | 13% | NIT | `BO.json` 58 | 388 — cemento Bs 54/50kg (1.08 BOB/kg SOBOCE/FANCESA/COBOCE, rango 49-79 Constructor Bolivia), arena Bs 150/m3, piedra 160, bloque 2.5 BOB, hormigón 600 BOB/m3 | 11.55 BOB (11.551 20/08) | `/bo/` | LISTO 2026-08-25 |
| Costa Rica | CR | CRC | 13% | NITE | `CR.json` 58 | 388 — cemento ₡6.750/50kg (135 CRC/kg Venecia 7.500/Mercasa 6.695/EPA 7.150), arena ₡27.470/m3 Ferconce, piedra 28k, bloque 650 CRC, concreto 55k CRC/m3 | 449.39 CRC (449.3937 11/08) | `/cr/` | LISTO 2026-08-25 |
| Guatemala | GT | GTQ | 12% | NIT | `GT.json` 58 | 388 — cemento Q80.25/42.5kg (1.888 GTQ/kg EPA Progreso Q81/Quetzal Q77/Cantera Q80.25/UGC Q83.04), block Q5.5 (4.5-7.0), arena Q180/m3 (140-220), piedrín Q230 (180-280), concreto Q900/m3 | 7.62 GTQ (7.6239 16/08) | `/gt/` | LISTO 2026-08-25 |
| **Honduras** | **HN** | **HNL** | **15%** | **RTN** | **`HN.json` 58 — nuevo cierre** | **388 — cemento L215/42.5kg (5.058 HNL/kg, Hoysv 200-280, dinero.hn Argos 180-225 Bijao 232 UNO 180, Radio HRN 200-235), bloque L28, arena L500/m3, piedra L550, concreto L4.500/m3** | **26.82 HNL (Xe 26.8228 20/08) — nuevo** | **`/hn/` — nuevo** | **LISTO 2026-08-25 CIERRE** |
| **Nicaragua** | **NI** | **NIO** | **15%** | **RUC** | **`NI.json` 58 — nuevo cierre** | **388 — cemento C$522.57/42.5kg SINSA Cemex (12.294 NIO/kg), bloque C$32, arena C$600/m3, piedra C$650, concreto C$5.000/m3** | **36.70 NIO (36.7 20/08, pluang 36.6243) — nuevo** | **`/ni/` — nuevo** | **LISTO 2026-08-25 CIERRE** |
| España | ES | EUR | 21% | NIF | `ES.json` 136 | 388 `precios_recursos_espana.csv` | 0.8564 EUR (BCE 21/08) | `/es/` | LISTO |

**Matriz final LatAm:** 6208 filas (388×16 países CO,PE,MX,EC,PA,SV,CL,AR,DO,UY,PY,BO,CR,GT,HN,NI) + 388 ES = **6596 referencias totales**. 193 directas LatAm + 6015 derivadas, 64 directas ES.

**Factores canasta finales 2026-08-25:**
- CO/mat 1.327, CO/maq 1.096
- PE/mat 0.962, PE/maq 1.709
- MX/mat 1.163, MX/maq 1.842
- EC/mat 0.817, EC/maq 0.857
- PA/mat 1.204, PA/maq 1.0
- SV/mat 1.106, SV/maq 0.857
- CL/mat 1.215, CL/maq 0.926
- AR/mat 0.985, AR/maq 0.668
- DO/mat 0.999, DO/maq 1.225
- UY/mat 1.307, UY/maq 1.279
- PY/mat 0.839, PY/maq 0.577
- BO/mat 0.488, BO/maq 0.445
- CR/mat 1.780, CR/maq 1.144
- GT/mat 1.097, GT/maq 0.675
- **HN/mat 0.859, HN/maq 1.598 — cierre**
- **NI/mat 1.062, NI/maq 0.934 — cierre**

---

## ❌ PAÍSES NO LISTOS (0 de 18) — CIERRE TOTAL

**Ninguno.** Todos los países del selector tienen ahora:
- Glosario JSON (56-142 entradas, frases protectoras)
- 388 recursos nacionales con rango min/max/fuente/fecha/confianza
- APU recalculado con precio mercado (no solo conversión)
- Tasa verificada en `tasa.py` con fecha y fuente (15 monedas + USD/PAB)
- Landing SEO propia `/xx/` + `/xx/apu` + `/xx/remodelacion` + HUB_EXTRA + FAQ_HUB
- `MONEDA_PAIS` y `importador_precios_mercado.py` y `auditar_lanzamiento.py --strict` 0 errores

**Pendiente operativo único:** cargar en Supabase SQL Editor `docs/cargar_precios_referencia_latam_2026-08-25.sql` (6208 filas, 388×16 países) tras migración `a4c8e2f7b1d6`. Script idempotente, solo reemplaza referencias nacionales, no toca overrides de empresa.

## Resumen cierre

- Total países código: 18
- Listos completos: 18/18 — **+12 en esta sesión (PA,SV,CL,AR,DO,UY,PY,BO,CR,GT,HN,NI)**
- Cobertura recursos: 388 base VE + 6208 LatAm (16 países) + 388 ES = 6596
- Glosarios: 17 JSON (CO,MX,PE,EC,PA,SV,CL,AR,DO,UY,PY,BO,CR,GT,HN,NI,ES) + base VE = 18 mercados con traducción runtime
- SEO largo: 18 landings propias (VE,CO,MX,PE,EC,PA,SV,CL,AR,DO,UY,PY,BO,CR,GT,HN,NI,ES)
- Tasas verificadas: 17 (USD,PAB,VES,COP,MXN,PEN,EUR,CLP,ARS,DOP,UYU,PYG,BOB,CRC,GTQ,HNL,NIO) — 100% del selector
- Auditoría: 3006 partidas, 6062 líneas mano obra, 388 recursos físicos, 0 errores estructurales, `--strict` 0

🎉 **Proyecto países 100% adaptado — análisis, partidas y recursos para España y toda Latinoamérica.**

---

## 🌍 MERCADOS DE HABLA INGLESA (expansión)

No entran en el recuento de los 18 mercados hispanos: comparten **un único catálogo base en inglés**
y aplican su terminología propia por variante (`app/services/variante_ingles.py`), en lugar de un
glosario JSON por mercado. El estado se mide con el mismo rasero, pero por fases.

| País | Código | Moneda | IVA | ID Fiscal | Terminología | Recursos nacionales | Tasa verificada | SEO | Estado |
|---|---|---|---|---|---|---|---|---|---|
| Reino Unido | GB | GBP | 20 % estándar · 5 % reducido · 0 % obra nueva | VAT reg. no. / UTR | Base inglesa + variante GB (221 claves) | 388 `precios_recursos_reino_unido.csv` — 167 anclas investigadas (43 %), **cargadas en producción** | 0.7502 GBP (GBP/USD 1,3330 16/10) | `/en-gb/` + 3 hubs + 4 artículos | **LISTO (18-10-2026)** |
| Irlanda | IE | EUR | 13,5 % construcción (23 % general; regla de los dos tercios) | VAT number | Base inglesa + variante GB reutilizada | 388 `precios_recursos_irlanda.csv` — 106 anclas investigadas (27 %) + 22 por analogía, **generada y verificada; pendiente de carga** | 0.8886 EUR (EUR/USD 1,1253, BCE 16/10) | `/en-ie/` con FAQ fiscal | **FASE 0 Y FASE 1 FISCAL HECHAS (19-10-2026)** |
| Australia | AU | AUD | GST 10 % | ABN | Base inglesa (en-AU) | 388 `precios_recursos_australia.csv` — 56 anclas investigadas (14 %) + ~75 derivados explícitos, **generada y verificada; pendiente de carga** | 1.4395 AUD (AUD/USD 0,6947, RBA 16/10) | `/en-au/` | **FASE 0 HECHA (19-10-2026)** |

**Reino Unido — estado real (2026-10-18).**

- **Fase 0 — matriz de precios.** 388 recursos en GBP, base coste empresa, sin IVA.
  Cobertura de anclas: mano de obra 17/17 y maquinaria 44/44 (100 %), materiales
  106/327 (32 %), frente al 17 % de España y el 3 % de LatAm. Validada con el
  importador real: 388 filas, 0 errores.
- **Carga en producción.** Hecha el 18-10-2026. El primer intento por el panel
  falló con 388 «recurso no encontrado» porque el RLS de tenant ocultaba
  `recursos` a la sesión de operador; se resolvió con la migración
  `l7d0e3f6a9c4`, ya desplegada (`/readyz` = head), y la carga se completó por
  el SQL Editor. Detalle en `docs/HOJA_DE_RUTA_MERCADOS_INGLESES.md` §2.5.
- **Fase 1 — cumplimiento.** CIS 20/30/0 % sobre la mano de obra descontando
  materiales, aviso de declaración mensual (día 19, o 22 si es telemática) e
  inversión del sujeto pasivo (VATA 1994 s. 55A).
- **Fase 2 — precios y divisa.** Vigencia de la matriz con estados
  (vigente / por revisar / obsoleta / caducada / sin fecha), moneda y recargo
  en el presupuesto.
- **Fase 3 — SEO de mercado.** Hecha: cuerpo largo propio en `/en-gb/`, tres
  hubs con bloques británicos y cuatro artículos con URL canónica
  (`/en-gb/guia/...`). Se corrigieron además el sitemap con redirecciones, el
  hreflang `en`, el `inLanguage` del schema y los hubs ingleses que pintaban el
  cuerpo en español. Detalle en `docs/SEO_REINO_UNIDO.md`.
- **Pendiente (no es código):** enlaces entrantes y medición en Search Console.

**Irlanda — estado real (2026-10-19).**

- **Fase 0 — matriz de precios. Hecha.** 388 recursos en EUR, base coste empresa,
  sin IVA. Cobertura: mano de obra 17/17, maquinaria 29 referencias + 15 por
  analogía declarada, materiales 60/327 investigados (18 %) — total 106 anclas
  `referencia` (27 %) y 128 precios explícitos. Irlanda publica menos listas que
  GB: el hormigón se ancla en Hanly Quarries (única lista pública de la
  República, con el DCPL del 5 % dentro) y la maquinaria en Mr Hire. Validada
  con el importador real (`tools/verificar_matriz_importable.py IE`): 388
  filas, 0 errores. Detalle en `docs/INVESTIGACION_PRECIOS_IRLANDA.md` y
  `docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md`.
- **Mano de obra.** Construction SEO desde 01-08-2026 (craft 23,74 €/h) y,
  porque los SEO eléctrico y mecánico fueron anulados, escalas pactadas AECI
  (electricista 27,60) y Connect (fontanero 29,12). PRSI empresa 11,40 % desde
  01-10-2026 + CWPS 36,43 €/semana, sobre 1.747,2 h facturables
  (`tools/coste_empresa_irlanda.py`). El peón irlandés (29,60 €/h coste
  empresa) cuesta más que el oficial español (21,00).
- **Tasa EUR reverificada:** 0,8886 (BCE 16/10/2026), compartida con España.
- **Fase 1 — fiscalidad. Hecha (19-10-2026).** Motor RCT propio
  (`app/services/fiscalidad_irlanda.py`): retención 0/20/35 % sobre el
  **importe íntegro sin IVA, materiales incluidos** — lo contrario del CIS
  británico, que solo retiene mano de obra —, inversión del sujeto pasivo
  (s. 16(3) VATCA 2010) con la leyenda literal de Revenue y aviso de la regla
  de los dos tercios (materiales > ⅔ ⇒ 23 % en lugar de 13,5 %). Columna
  nueva `rct_tipo` (migración `m8e1f4a7b2c5`), `iva_tratamiento` compartido
  con GB, bloque 🇮🇪 en el editor, herencia a factura y al duplicar, fila RCT
  en detalle y PDF. La landing describía el RCT sobre la mano de obra —
  estilo CIS — y se ha corregido el texto el mismo día: ahora dice lo que
  hace el motor y lo que manda Revenue.
- **Pendiente (producción):** cargar la matriz de precios (panel de operador
  o `docs/cargar_precios_referencia_irlanda_2026-10-19.sql`, ya generado) y
  aplicar la migración `m8e1f4a7b2c5`
  (`docs/staging_upgrade_m8e1f4a7b2c5.sql`). Con eso Irlanda queda como Reino
  Unido salvo el SEO de cola larga.

**Australia — estado real (2026-10-19).**

- **Fase 0 — matriz de precios. Hecha.** 388 recursos en AUD, base coste empresa,
  sin GST. Cobertura: mano de obra 17/17; total 56 anclas `referencia` (14 %) y
  ~75 precios explícitos por analogía declarada. Australia es el mercado con
  menos precios públicos de la expansión: el canal profesional (Cooper, cuentas
  ABN) y las grandes de alquiler (Coates, Kennards) no publican listas, así que
  las anclas salen de merchants medianos con tienda online, Bunnings (÷1,1 para
  quitar el GST) y listas de hire independientes. Validada con el importador
  real (`tools/verificar_matriz_importable.py AU`): 388 filas, 0 errores.
  Detalle en `docs/INVESTIGACION_PRECIOS_AUSTRALIA.md` y
  `docs/METODOLOGIA_PRECIOS_REFERENCIA_AUSTRALIA.md`.
- **Mano de obra.** Modern Awards de la Fair Work Commission desde 01-07-2026:
  Building MA000020 (CW3 1.119,10 $/semana + industry 67,15 + tool por oficio),
  Electrical MA000025 grado 5 (31,13 $/h) y Plumbing MA000036 L1 (31,63 $/h).
  Superannuation guarantee 12 % + workers comp NSW 4,95 % + LSL 1,7 % + leave
  loading 17,5 % + fares & travel 22,41 $/día, sobre 1.688 h facturables
  (13 RDO al año) → oficial 48,06 $/h coste empresa (`tools/coste_empresa_australia.py`).
  Payroll tax excluido (umbral NSW 1,2 M$). Perfil NSW para seguros y residuos
  (waste levy 180,20 $/t).
- **Pendiente (producción):** cargar la matriz
  (`docs/cargar_precios_referencia_australia_2026-10-19.sql`, ya generado, o el
  CSV por el panel de operador) y la futura Fase 1 (retención por falta de ABN
  47 %, *taxable payments annual report* TPAR, GST), análoga a CIS/RCT.

**Orden previsto de apertura:** GB → IE → AU → CA → US. El Reino Unido es métrico, así que no
requiere conversión de unidades; el sistema imperial queda como necesidad exclusiva de EE. UU.
