# Estado de adaptación por país — análisis, partidas y recursos

**Fecha:** 2026-08-25 (actualizado tras PA/SV + CL/AR + DO/UY/PY)  
**Fuente:** `app/paises.py`, `basedatos_partidas/glosarios/`, `basedatos_partidas/salida/precios_recursos_*.csv`, `app/seo.py`, `app/seo_contenido.py`, `app/services/tasa.py`

> Listo = APU recalculable con precios mercado nacionales + partidas traducidas vía glosario + recursos 388 con precio nacional + SEO propio + tasa verificada

---

## ✅ PAÍSES LISTOS (13 de 18) — 7 nuevos en esta sesión

| País | Código | Moneda | IVA | ID Fiscal | Glosario | Recursos nacionales | Tasa verificada | SEO | Estado |
|---|---|---|---|---|---|---|---|---|---|
| Venezuela | VE | USD | 16% | RIF | Base | 388 base `recursos.json` | 773.31 VES | `/ve/` | LISTO nativo |
| Colombia | CO | COP | 19% | NIT | `CO.json` 142 | 388 | 3128.65 COP | `/co/` | LISTO |
| México | MX | MXN | 16% | RFC | `MX.json` 112 | 388 | 17.06 MXN | `/mx/` | LISTO |
| Perú | PE | PEN | 18% | RUC | `PE.json` 93 | 388 | 3.37 PEN | `/pe/` | LISTO |
| Ecuador | EC | USD | 15% | RUC | `EC.json` 91 | 388 | 1.0 USD | `/ec/` | LISTO |
| Panamá | PA | USD (PAB 1:1) | 7% | RUC | `PA.json` 56 — 2026-08-25 | 388 — cemento $8.25/42.5kg, bloque $0.95, arena $34/m3, concreto $125/m3 | PAB 1.0 | `/pa/` | LISTO 2026-08-25 |
| El Salvador | SV | USD | 13% | NIT | `SV.json` 57 | 388 — cemento $8.73 CASALCO, bloque $0.40, arena $35, grava $45.05, concreto $135.35 | USD 1.0 | `/sv/` | LISTO 2026-08-25 |
| Chile | CL | CLP | 19% | RUT | `CL.json` 66 — 2026-08-25 | 388 — cemento $4.790/25kg (191.6 CLP/kg), bloque $1.840, arena $33.190/m3, hormigón $110k/m3 | 925.90 CLP | `/cl/` | LISTO 2026-08-25 |
| Argentina | AR | ARS | 21% | CUIT | `AR.json` 65 | 388 — cemento $11.433/50kg, bloque $1.500, arena $33.500/m3, hormigón H21 $168.478/m3 | 1497.38 ARS | `/ar/` | LISTO 2026-08-25 |
| **Rep. Dominicana** | **DO** | **DOP** | **18%** | **RNC** | **`DO.json` 58 — nuevo** | **388 — cemento RD$535/funda 94lb (12.56 DOP/kg), block 6'' RD$42, arena RD$1.550/m3, grava RD$1.700/m3** | **58.33 DOP — nuevo** | **`/do/` — nuevo** | **LISTO 2026-08-25** |
| **Uruguay** | **UY** | **UYU** | **22%** | **RUT** | **`UY.json` 58 — nuevo** | **388 — cemento $240/25kg (9.6 UYU/kg), bloque 15x19x39 $70, arena $1.200/m3, hormigón $5.500/m3** | **40.21 UYU — nuevo** | **`/uy/` — nuevo** | **LISTO 2026-08-25** |
| **Paraguay** | **PY** | **PYG** | **10%** | **RUC** | **`PY.json` 57 — nuevo** | **388 — cemento Gs 59.000/50kg (1.180 PYG/kg), bloque Gs 5.300, piedra Gs 104.000/m3, hormigón Gs 650.000/m3** | **5946.10 PYG — nuevo** | **`/py/` — nuevo** | **LISTO 2026-08-25** |
| España | ES | EUR | 21% | NIF | `ES.json` 136 | 388 `precios_recursos_espana.csv` | 0.8564 EUR | `/es/` | LISTO |

**Matriz actual:** 4268 filas (388×11 países CO,PE,MX,EC,PA,SV,CL,AR,DO,UY,PY) + 388 ES = 4656 referencias totales. 143 directas LatAm + 4125 derivadas, 64 directas ES.

**Factores canasta 2026-08-25:**
- CO/mat 1.327, CO/maq 1.096
- PE/mat 0.962, PE/maq 1.709
- MX/mat 1.163, MX/maq 1.842
- EC/mat 0.817, EC/maq 0.857
- PA/mat 1.204, PA/maq 1.0
- SV/mat 1.106, SV/maq 0.857
- CL/mat 1.215, CL/maq 0.926
- AR/mat 0.985, AR/maq 0.668
- **DO/mat 0.999, DO/maq 1.225 — nuevo**
- **UY/mat 1.307, UY/maq 1.279 — nuevo**
- **PY/mat 0.839, PY/maq 0.577 — nuevo**

---

## ❌ PAÍSES NO LISTOS (5 de 18)

| País | Código | Moneda | IVA | Vocab corto | Glosario | Recursos | Tasa verificada | SEO largo | Falta |
|---|---|---|---|---|---|---|---|---|---|
| Bolivia | BO | BOB | 13% | hormigón, revoque, cielo falso, zócalo, plomero | ❌ | ❌ | ❌ | ❌ | Glosario BO, matriz BOB, tasa BCB, landing `/bo/` |
| Costa Rica | CR | CRC | 13% | concreto, repello, cielo raso, rodapié, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario CR, matriz CRC, tasa BCCR |
| Guatemala | GT | GTQ | 12% | concreto, repello, cielo falso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario GT, matriz GTQ |
| Honduras | HN | HNL | 15% | concreto, repello, cielo falso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario HN, matriz HNL |
| Nicaragua | NI | NIO | 15% | concreto, repello, cielo raso, zócalo, fontanero | ❌ | ❌ | ❌ | ❌ | Glosario NI, matriz NIO |

**Tienen hoy:** entrada `PAISES` y `ORDEN_SELECTOR`, selector visible, `defaults_para_pais()`, tasa vía API pero sin sugerida, sitemap con ruta pero copy genérico.

## Checklist pendientes

1. Glosario JSON (70-150 entradas)
2. Investigación precios → `docs/INVESTIGACION_PRECIOS_{COD}.md`
3. Añadir a `generar_matriz_precios_latam.py` (PAISES, TASAS_CORTE, REFERENCIAS, OFICIAL_GENERAL, AYUDANTE)
4. `python tools/generar_matriz_precios_latam.py`
5. `python tools/generar_sql_precios_latam.py` + `completar_matriz_referencias.py`
6. Tasa en `app/services/tasa.py`
7. Landing `seo.py` + `seo_contenido.py`
8. Tests + `auditar_lanzamiento.py --strict`

## Resumen

- Total países código: 18
- Listos completos: 13 (VE,CO,MX,PE,EC,PA,SV,CL,AR,DO,UY,PY,ES) — **+7 en esta sesión**
- Parciales: 5 (BO,CR,GT,HN,NI)
- Cobertura recursos: 388 base + 4268 LatAm (11 países) + 388 ES = 4656
- Glosarios: 12 JSON (CO,MX,PE,EC,PA,SV,CL,AR,DO,UY,PY,ES) + base VE
- SEO largo: 13 landings propias
- Tasas verificadas: USD, PAB, VES, COP, MXN, PEN, EUR, CLP, ARS, DOP, UYU, PYG (12) — faltan BOB, CRC, GTQ, HNL, NIO

Próximo: BO + CR + GT (cierre Centroamérica y Bolivia)
