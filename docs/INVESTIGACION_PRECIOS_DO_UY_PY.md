# Investigación precios República Dominicana, Uruguay y Paraguay — 2026-08-25

**Países:** DO (DOP), UY (UYU), PY (PYG)
**Fecha corte:** 2026-08-25
**Matriz:** `basedatos_partidas/salida/precios_recursos_latam.csv` (388×11 países tras esta ronda)
**Tasas corte:** DO 58.33 DOP/USD (Xe 58.3369 24/08), UY 40.21 UYU/USD (Xe 40.2124 18/08), PY 5946.10 PYG/USD (pluang 08/08 5946.10, Xe 6009.42 24/08)
**Metodología:** `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`

## República Dominicana (DO)

### Mano de obra

Fuente: Cazvid DO 2026, Listín Diario 2026, ONE ICDV.

- **Salario mínimo general:** 16.993 RD$ microempresa, 18.421 pequeña, 27.489 mediana, 29.988 grande (feb 2026)
- **Sector construcción jornal (régimen propio):** albañil primera 2.000 RD$/jornada 8h, segunda 1.600 RD$/día, peón no calificado 900 RD$/día (Listín Diario: "Un albañil de primera ganará al menos RD$2,000 por día")
- **Adopción CotizaT:**
  - Oficial general MO-OF1: 2.000 DOP/jornada 8h (1.600-2.200) → 250 DOP/h
  - Ayudante MO-AYU: 900 DOP/jornada (800-1.000) → 112.5 DOP/h
  - Oficial especializado con destajo bloque: ~29 RD$/block ×125 blocks/día ≈ 3.625 RD$/día (rango alto)

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento gris 94lb | 12.56 DOP/kg | 10.33 | 14.67 | ControlObra RD julio 2026: funda gris 94lb (~42.6kg) RD$535 típico, rango $530-1,495 (blanco $1,474-1,495), Ferremix $535, Cima $504.24, ferreteros $440-450, levantamiento 490-625 | kg (535/42.6=12.56) |
| MT-BLQ-15 | Block 6" 15x20x40 | 42 DOP/ud | 38 | 50 | Ferretería Yessenia Block casa 8 RD$48, casa 6 RD$34.5, Mayol Block 8 RD$50, Ferremix Block industrial 6 RD$51, 8 RD$64, SonProject Block 6 RD$42, Block 4 RD$38, Block 8 RD$53 — mediana 42 | ud |
| MT-ARENA | Arena Itabo mina | 1550 DOP/m3 | 1400 | 1700 | SonProject Arena Itabo mina RD$1.550/m3 Santo Domingo | m3 |
| MT-PIEDRA-PIC | Grava 1/2" | 1700 DOP/m3 | 1500 | 1850 | SonProject Grava 1/2" RD$1.700/m3 | m3 |
| MT-ACERO-CAB | Varilla 3/8" quintal | 55 DOP/kg | 48 | 62 | SonProject Acero @3/8 RD$3.853/quintal? Actually quintal? Paduamateriales quintal varilla 3,650-4,200 DOP, ferreteros varilla 435-495 → 540 consumidor, Inmobiliario.do varilla 3/8" 2,920-3,845/quintal — se normaliza a ~55 DOP/kg | kg |
| MT-CONC-210 | Hormigón / concreto | 4500 DOP/m3 | 4000 | 5000 | Estimado RD: ICDV 236.07 ene 2025 (+46% desde 2020), mano obra +7.14% mensual ene 2025, validar con concretera | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 2500 DOP/h | 2000 | 3000 | Estimado RD retroexcavadora, validar operador/combustible |

## Uruguay (UY)

### Mano de obra

Fuentes: Pietropinto.uy laudo construcción abril 2025-marzo 2026, FiniquitoJusto Decreto 319/025, GenzClima UY.

- **Jornal mínimo nacional:** $982.88/día (SMN $24.572/25, Decreto 319/025 ene-jun 2026), $1.015,32/día desde julio 2026 (SMN $25.383)
- **Laudo construcción 2025-2026 (Ley 14.411 incluido):**
  - Peón común Cat I: $1.554,29/jornal
  - Peón práctico Cat II: $1.652,86/jornal
  - Medio oficial albañil Cat V: $2.069,21/jornal (no incluido Ley 14.411: $2.520,37)
  - Oficial albañil Cat VII: $2.412,65/jornal
- **Mercado reparaciones:** jornal $1.750-2.250 UYU/día (GenzClima), Montevideo $250-400/h
- **Adopción CotizaT:**
  - Oficial general: 2.412,65 UYU/jornada (2.000-2.600) → 301.58 UYU/h
  - Ayudante (peón común): 1.554,29 UYU/jornada (1.400-1.700) → 194.28 UYU/h

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Portland 25kg | 9.6 UYU/kg | 9.0 | 11.44 | Otto Wulff Cielo Azul 25kg $286 tarjeta ($11.44/kg), $263 efectivo ($10.52/kg), Barraca Central 25kg $225 (9/kg), EMAT $240 (9.6/kg), Barraca 5 Esquinas ANCAP 25kg $228 (9.12/kg) — mediana 240/25=9.6 | kg |
| MT-BLQ-15 | Bloque 15x19x39 | 70 UYU/ud | 49 | 84 | Barraca Gallinal MODULBLOCK 15x19x39 $70, Vibrado $49, U Vibrado 15 $89, EMAT Bloque prensado s/fondo 15x19x39 $78.56, U prensado $84, Sodimac UY bloque 12x19x39 $49, 12x19x40 $36 — mediana 70 | ud |
| MT-ARENA | Arena | 1200 UYU/m3 | 1000 | 1400 | Estimado UY: SAU Rubrado precios unitarios Ago22 hormigón armado encofrado dos lados $59k/m3 incluye hierro, etc. Validar arena con Barraca | m3 |
| MT-PIEDRA-PIC | Piedra / balasto | 1300 UYU/m3 | 1100 | 1500 | Estimado similar arena | m3 |
| MT-ACERO-CAB | Hierro / varilla | 65 UYU/kg | 55 | 75 | Estimado UY hierro, validar con Barraca | kg |
| MT-CONC-210 | Hormigón | 5500 UYU/m3 | 5000 | 6000 | SAU Rubrado: hormigón armado encofrado dos lados (140kg hierro/m3) $59.055/m3 materiales + $14.906 mano obra, bloque cementicio armado e=20cm $5.029/m3 — estimado 5.500/m3 hormigón | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 1800 UYU/h | 1500 | 2100 | Estimado UY retroexcavadora |

## Paraguay (PY)

### Mano de obra

Fuentes: MTESS Paraguay Resolución reajuste jornal mínimo, Cazvid Paraguay 2026.

- **Salario mínimo general:** G 2.798.309 mensual, jornal 107.627 G/día, hora 11.660 G diurna (vigente hasta junio 2024). Desde 1 julio 2026: 3.044.000 mensual, jornal 117.077 G/día (+5% sobre 2.899.048)
- **Construcción escalafonada:** albañil y carpintero oficial primera G 3.272.760 mensual, jornal 125.875 G/día (MTESS). Pintores similar.
- **Mercado:** 3.044.000-5.948.568 G/mes base según categoría (peón, medio oficial, oficial, maestro)
- **Adopción CotizaT:**
  - Oficial general: 125.875 PYG/jornada (107.627-130.000) → 15.734 PYG/h
  - Ayudante: 107.627 PYG/jornada (93.000-115.000) → 13.453 PYG/h (hora diurna parcial)

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento PZ 50kg | 1180 PYG/kg | 940 | 1180 | Costeo.com.py Cemento PZ 50kg Gs 59.000/bolsa (1.180/kg), INC CPII-F32 Gs 47.000/50kg (940/kg), CPIV-32 Gs 55.000/50kg (1.100/kg) | kg |
| MT-BLQ-15 | Bloque cemento | 5300 PYG/ud | 5000 | 5500 | Clasipar Bloques Gs 5.300 c/u puesto obra, 5.000 retirando; generadordeprecios Paraguay bloque 40x20x15 R10 5.153 PYG/ud | ud |
| MT-ARENA | Piedra bruta / arena | 104000 PYG/m3 | 90000 | 120000 | Costeo.com.py Piedra Bruta m3 Gs 104.000 | m3 |
| MT-PIEDRA-PIC | Piedra picada | 110000 PYG/m3 | 95000 | 125000 | Estimado similar piedra bruta | m3 |
| MT-ACERO-CAB | Varilla hierro | 5500 PYG/kg | 4800 | 6200 | Estimado PY varilla, validar | kg |
| MT-CONC-210 | Hormigón | 650000 PYG/m3 | 600000 | 700000 | Estimado PY hormigón, validar con concretera | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 120000 PYG/h | 100000 | 140000 | Estimado PY retroexcavadora |

## Factores canasta

Tasas corte: DO 58.33, UY 40.21, PY 5946.10 (USD base × tasa).

- DO materiales factor = precio_local / (precio_base_USD × 58.33)
- UY factor = precio_local / (precio_base_USD × 40.21)
- PY factor = precio_local / (precio_base_USD × 5946.10)

Ejemplo cemento base VE $0.225/kg:
- DO base local 0.225×58.33=13.124 DOP/kg, observado 12.56 → factor 0.957
- UY base local 0.225×40.21=9.047 UYU/kg, observado 9.6 → factor 1.061
- PY base local 0.225×5946.10=1337.87 PYG/kg, observado 1180 → factor 0.882

## Generación

```bash
python tools/generar_matriz_precios_latam.py
# 388×11=4268 filas
python tools/generar_sql_precios_latam.py
```
