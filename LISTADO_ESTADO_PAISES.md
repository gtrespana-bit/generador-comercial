# Estado de adaptación por país — análisis, partidas y recursos

**Fecha:** 2026-08-25 (actualizado tras PA/SV + CL/AR)  
**Fuente:** `app/paises.py`, `basedatos_partidas/glosarios/`, `basedatos_partidas/salida/precios_recursos_*.csv`, `app/seo.py`, `app/seo_contenido.py`, `app/services/tasa.py`

> Definición de "listo": análisis APU recalculable con precios mercado nacionales + partidas traducidas vía glosario + recursos 388 con precio nacional + SEO propio + tasa verificada

---

## ✅ PAÍSES LISTOS (10 de 18) — PA/SV + CL/AR completados en esta sesión

| País | Código | Moneda | IVA | ID Fiscal | Glosario | Recursos nacionales | APU mercado | Tasa verificada | SEO landing | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| Venezuela | VE | USD | 16% | RIF | Base | 388 base `recursos.json` | Sí base | 773.31 VES (BCV 18/08) | `/ve/` | LISTO nativo |
| Colombia | CO | COP | 19% | NIT | `CO.json` 142 | 388 latam.csv | Sí | 3128.65 COP (TRM 19/08) | `/co/` | LISTO |
| México | MX | MXN | 16% | RFC | `MX.json` 112 | 388 | Sí | 17.06 MXN | `/mx/` | LISTO |
| Perú | PE | PEN | 18% | RUC | `PE.json` 93 | 388 | Sí | 3.37 PEN | `/pe/` | LISTO |
| Ecuador | EC | USD | 15% | RUC | `EC.json` 91 | 388 | Sí | 1.0 USD | `/ec/` | LISTO |
| Panamá | PA | USD (PAB 1:1) | 7% | RUC | `PA.json` 56 — 2026-08-25 | 388 — cemento $8.25/42.5kg, bloque $0.95, arena $34/m3, concreto $125/m3 | Sí | PAB 1.0 | `/pa/` | LISTO 2026-08-25 |
| El Salvador | SV | USD | 13% | NIT | `SV.json` 57 | 388 — cemento $8.73 CASALCO, bloque $0.40, arena $35, grava $45.05, concreto $135.35 | Sí | USD 1.0 | `/sv/` | LISTO 2026-08-25 |
| **Chile** | **CL** | **CLP** | **19%** | **RUT** | **`CL.json` 66 — nuevo 2026-08-25** | **388 — cemento $4.790/25kg Sodimac Melón (191.6 CLP/kg), bloque $1.840, arena $33.190/m3, hormigón $110k/m3 GlobalGTC** | **Sí** | **925.90 CLP (18/08)** | **`/cl/` — nuevo** | **LISTO 2026-08-25** |
| **Argentina** | **AR** | **ARS** | **21%** | **CUIT** | **`AR.json` 65 — nuevo** | **388 — cemento $11.433/50kg Loma Negra/Holcim, bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3** | **Sí** | **1497.38 ARS (08/08)** | **`/ar/` — nuevo** | **LISTO 2026-08-25** |
| España | ES | EUR | 21% | NIF | `ES.json` 136 | 388 `precios_recursos_espana.csv` | Sí EUR | 0.8564 EUR | `/es/` | LISTO |

**Matriz actual:** 3104 filas (388×8 países CO,PE,MX,EC,PA,SV,CL,AR) + 388 ES = 3492 referencias totales. 113 directas LatAm + 2991 derivadas, 64 directas ES.

**Factores canasta 2026-08-25:**
- CO/mat 1.327, CO/maq 1.096
- PE/mat 0.962, PE/maq 1.709
- MX/mat 1.163, MX/maq 1.842
- EC/mat 0.817, EC/maq 0.857
- PA/mat 1.204, PA/maq 1.0
- SV/mat 1.106, SV/maq 0.857
- **CL/mat 1.215, CL/maq 0.926 — nuevo**
- **AR/mat 0.985, AR/maq 0.668 — nuevo**

---

## ❌ PAÍSES NO LISTOS (8 de 18)

| País | Código | Moneda | IVA | Vocab corto | Glosario | Recursos | Tasa verificada | SEO largo | Falta |
|---|---|---|---|---|---|---|---|---|---|
| Rep. Dominicana | DO | DOP | 18% | hormigón, pañete, plafón, zócalo, plomero | ❌ | ❌ | ❌ | ❌ | Glosario DO, matriz DOP, tasa BCRD, landing `/do/` |
| Uruguay | UY | UYU | 22% | hormigón, revoque, cielorraso, zócalo, sanitario | ❌ | ❌ | ❌ | ❌ | Glosario UY, matriz UYU |
| Paraguay | PY | PYG | 10% | hormigón, revoque, cielorraso, zócalo, plomero | ❌ | ❌ | ❌ | ❌ | Glosario PY, matriz PYG (0 dec) |
| Bolivia | BO | BOB | 13% | hormigón, revoque, cielo falso, zócalo, plomero | ❌ | ❌ | ❌ | ❌ | Glosario BO, matriz BOB |
| Costa Rica | CR | CRC | 13% | concreto, repello, cielo raso, rodapié, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario CR, matriz CRC |
| Guatemala | GT | GTQ | 12% | concreto, repello, cielo falso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario GT, matriz GTQ |
| Honduras | HN | HNL | 15% | concreto, repello, cielo falso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario HN, matriz HNL |
| Nicaragua | NI | NIO | 15% | concreto, repello, cielo raso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario NI, matriz NIO |

**Tienen hoy:** entrada `PAISES` y `ORDEN_SELECTOR`, selector visible, `defaults_para_pais()`, tasa vía API pero sin sugerida, sitemap con ruta pero copy genérico.

## Checklist para pendientes

1. Glosario JSON
2. Investigación precios → `docs/INVESTIGACION_PRECIOS_{COD}.md`
3. Añadir a `generar_matriz_precios_latam.py` (PAISES, TASAS_CORTE, REFERENCIAS, OFICIAL_GENERAL, AYUDANTE)
4. `python tools/generar_matriz_precios_latam.py`
5. `python tools/generar_sql_precios_latam.py` + `completar_matriz_referencias.py`
6. Tasa en `app/services/tasa.py`
7. Landing `seo.py` + `seo_contenido.py`
8. Tests + `auditar_lanzamiento.py --strict`

## Resumen

- Total países código: 18
- Listos completos: 10 (VE,CO,MX,PE,EC,PA,SV,CL,AR,ES) — **+4 en esta sesión (PA,SV,CL,AR)**
- Parciales: 8
- Cobertura recursos: 388 base + 3104 LatAm (8 países) + 388 ES = 3492
- Glosarios: 9 JSON (CO,MX,PE,EC,PA,SV,CL,AR,ES) + base VE
- SEO largo: 10 landings propias

Próximo: DO, UY, PY, BO (Sur) + CR, GT, HN, NI (Centroamérica)
