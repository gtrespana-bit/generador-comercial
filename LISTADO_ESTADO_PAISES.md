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
