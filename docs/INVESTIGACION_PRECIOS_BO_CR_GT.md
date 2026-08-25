# Investigación precios Bolivia, Costa Rica y Guatemala — 2026-08-25

**Países:** BO (BOB), CR (CRC), GT (GTQ)
**Fecha corte:** 2026-08-25
**Matriz:** `basedatos_partidas/salida/precios_recursos_latam.csv` (388×14 países tras esta ronda)
**Tasas corte:** BO 11.55 BOB/USD (exchange-rates.org 11.551 20/08, pluang 11.58 14/08), CR 449.39 CRC/USD (currency.me.uk 449.3937, pluang 446.30 20/08), GT 7.62 GTQ/USD (pluang 7.6239 16/08, foreignexchange 7.6258 15/08)
**Metodología:** `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`

## Bolivia (BO)

### Mano de obra

Fuentes: OneEstimate Bolivia 2026 (costos por m2, APU muro ladrillo gambote), tabla jornales por oficio.

| Especialidad | Santa Cruz BOB/día | La Paz BOB/día | Cochabamba BOB/día | USD/día ref (11.55) |
|---|---|---|---|---|
| Maestro obra | 350-500 | 380-550 | 340-480 | 30-43 |
| Albañil oficial | 220-320 | 240-350 | 210-300 | 19-27 |
| Ayudante/peón | 130-180 | 140-190 | 125-170 | 11-15 |
| Electricista | 280-400 | 300-430 | 270-380 | 24-34 |
| Plomero | 260-380 | 280-410 | 250-360 | 22-32 |

Tabla nacional mínima: maestro 180-280, albañil 150-240, ayudante 100-160, peón general 95-150. Factor prestaciones sociales 1.55-1.62 (Ley General del Trabajo). APU ejemplo muro ladrillo gambote 15cm: oficial 1.20h×35 BOB/h=42 BOB + ayudante 1.20h×20=24 BOB.

Adopción CotizaT:
- Oficial general MO-OF1: 270 BOB/jornada 8h (220-320) → 33.75 BOB/h
- Ayudante MO-AYU: 140 BOB/jornada (125-170) → 17.5 BOB/h

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento IP-30 50kg | 1.08 BOB/kg | 0.98 | 1.58 | OneEstimate Bolivia 2026: SOBOCE 52-58 La Paz, 50-56 Santa Cruz, FANCESA 50-56 La Paz, 49-55 Santa Cruz, COBOCE 51-57; Constructor Bolivia Viacha IP30 79 BOB/50kg (1.58/kg), Ecebol planta 37 BOB/50kg — mediana 54/50=1.08 | kg |
| MT-ARENA | Arena fina | 150 BOB/m3 | 130 | 170 | OneEstimate APU Bolivia arena fina 150 BOB/m3, 0.025m3×150=3.75 BOB/m2 | m3 |
| MT-PIEDRA-PIC | Piedra / ripio | 160 BOB/m3 | 140 | 180 | Estimado similar arena | m3 |
| MT-ACERO-CAB | Fierro corrugado | 12 BOB/kg | 10 | 14 | OneEstimate varilla Ø12mm USD 1.52-1.72/kg → BOB 17.5-19.8/kg, pero tabla APU usa acero por kg más bajo — se adopta 12 BOB/kg referencia nacional | kg |
| MT-BLQ-15 | Bloque cemento / ladrillo gambote 6 huecos | 2.5 BOB/ud | 2.0 | 3.0 | OneEstimate Bolivia ladrillo gambote 6 huecos 1.10 BOB/pza (41.80 BOB/m2 ×38 pza), bloque estimado 2.5 | ud |
| MT-CONC-210 | Hormigón H25 | 600 BOB/m3 | 500 | 700 | SOBOCE informe comparativo: premezclado equilibrio 4m3 Bs 4.242, etc. Ahorro 16% Cochabamba, 28% Santa Cruz — estimado 600 BOB/m3 | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 180 BOB/h | 150 | 210 | Estimado Bolivia retroexcavadora, operador maquinaria 300-380 BOB/día |

## Costa Rica (CR)

### Mano de obra

Fuentes: El Financiero CR salarios mínimos 2026, CFIA.

- **Salario mínimo por día:**
  - Peón construcción: 12.436,41 CRC/día
  - Ayudante operario construcción: 13.523,69 CRC/día
  - Albañil / operario construcción / operador maquinaria pesada: 13.991,86 CRC/día

Adopción CotizaT:
- Oficial general: 13.991,86 CRC/jornada (12.436-15.500) → 1.748,98 CRC/h
- Ayudante: 13.523,69 CRC/jornada (12.436-14.500) → 1.690,46 CRC/h

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento 50kg | 135 CRC/kg | 133.9 | 150 | Venecia CR 50kg ₡7.500 (150/kg), Mercasa Fortaleza 50kg ₡6.695 (133.9/kg), EPA Holcim fuerte 50kg ₡7.150 (143/kg), Ferconce Progreso 50kg ₡6.750 (135/kg) — mediana 6.750/50=135 | kg |
| MT-ARENA | Arena fina metro | 27470 CRC/m3 | 25000 | 30000 | Ferconce Arena Fina Metro ₡27.470 IVA incl. | m3 |
| MT-PIEDRA-PIC | Piedra / lastre | 28000 CRC/m3 | 25000 | 31000 | Estimado similar arena | m3 |
| MT-ACERO-CAB | Varilla corrugada | 700 CRC/kg | 600 | 800 | Estimado CR varilla, validar con EPA/Construmax | kg |
| MT-BLQ-15 | Bloque 15x20x40 | 650 CRC/ud | 550 | 750 | Estimado CR bloque 15, validar con ferretería | ud |
| MT-CONC-210 | Concreto premezclado | 55000 CRC/m3 | 50000 | 60000 | Estimado CR concreto, validar con Holcim/Cemex CR | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 18000 CRC/h | 15000 | 21000 | Estimado CR retroexcavadora |

## Guatemala (GT)

### Mano de obra

Fuentes: LivinginGuatemala.com mayo 2026, Cazvid Guatemala julio 2026, OneEstimate GT 2026.

- **Salario mínimo actividades no agrícolas:** 3.816,90 GTQ/mes resto país, 4.002,28 GTQ Departamento Guatemala + bonificación incentivo 250 GTQ aparte → total mínimo ~4.066,90-4.252,28 GTQ/mes
- **Jornal mercado:**
  - Albañil Q150-250/día (LivinginGuatemala), Q180-260/día OneEstimate, Q150-250 Cazvid
  - Ayudante/peón Q100-150/día, Q120-160 OneEstimate
  - Armador hierro Q200-280, Maestro obra Q260-380, Maestro planta Q4.500-7.500/mes
  - Promedio Computrabajo Q3.867/mes albañil, Tusalario 4.245-8.122/mes inicial

Adopción CotizaT:
- Oficial general: 220 GTQ/jornada 8h (150-250) → 27.5 GTQ/h
- Ayudante: 130 GTQ/jornada (100-150) → 16.25 GTQ/h

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento UGC 42.5kg | 1.888 GTQ/kg | 1.609 | 2.147 | EPA GT Progreso 4060 PSI 42.5kg Q81 (1.905/kg), Quetzal Q77 (1.811/kg), Cantera Q80.25 (1.888/kg), UGC Q83.04 (1.954/kg), Montaña Q68.42 (1.609/kg), Estructural Q91.25 (2.147/kg) — mediana 80.25/42.5=1.888; INE IPC dic 2025 cemento gris UGC 42.5kg índice 110.11 | kg |
| MT-ARENA | Arena río | 180 GTQ/m3 | 140 | 220 | OneEstimate GT Arena río Q140-220/m3 | m3 |
| MT-PIEDRA-PIC | Piedrín | 230 GTQ/m3 | 180 | 280 | OneEstimate Piedrín Q180-280/m3 | m3 |
| MT-ACERO-CAB | Hierro / varilla | 14 GTQ/kg | 12 | 16 | Estimado GT hierro, validar con EPA/Cemaco | kg |
| MT-BLQ-15 | Block 14x19x39 | 5.5 GTQ/ud | 4.5 | 7.0 | OneEstimate GT Block concreto 14x19x39 Q4.50-7.00 c/u | ud |
| MT-CONC-210 | Concreto | 900 GTQ/m3 | 800 | 1000 | Estimado GT concreto premezclado, validar con Mixto Listo | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 180 GTQ/h | 150 | 220 | Estimado GT retroexcavadora |

## Factores canasta

Tasas corte: BO 11.55, CR 449.39, GT 7.62

- BO cemento base local 0.225×11.55=2.598 BOB/kg, observado 1.08 → factor 0.415 (cemento BO más barato que base VE convertido, coherente con producción local SOBOCE/FANCESA)
- CR base local 0.225×449.39=101.11 CRC/kg, observado 135 → factor 1.335
- GT base local 0.225×7.62=1.714 GTQ/kg, observado 1.888 → factor 1.101

## Generación

```bash
python tools/generar_matriz_precios_latam.py
# 388×14=5432 filas
python tools/generar_sql_precios_latam.py
```
