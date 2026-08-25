# Investigación precios Honduras y Nicaragua — 2026-08-25

**Países:** HN (Honduras, HNL) y NI (Nicaragua, NIO) — últimos 2 de Centroamérica
**Fecha corte:** 2026-08-25
**Matriz:** `basedatos_partidas/salida/precios_recursos_latam.csv` (388×16 países tras cierre)
**Tasas corte:** HN 26.82 HNL/USD (Xe 26.8228 20/08, pluang 26.8068), NI 36.70 NIO/USD (currency.me.uk 36.7, pluang 36.6243, Xe 36.759)
**Metodología:** `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`

## Honduras (HN)

### Mano de obra

Fuentes: Inpac Honduras 2026, La Prensa Honduras 2025, Hoysv.com 2026.

- **Jornal oficial:** Albañil 700 HNL/día (Inpac tabla precio mano obra: Albañil DIA 700, Armador hierro 700, Ayudante 450), pero La Prensa 2025: "Un albañil que antes cobraba 700 lempiras ahora pide 1,000 por día, maestro hasta 1,500"
- **Adopción CotizaT:**
  - Oficial general MO-OF1: 800 HNL/jornada 8h (700-1000) → 100 HNL/h
  - Ayudante MO-AYU: 450 HNL/jornada (400-500) → 56.25 HNL/h
  - Maestro obra hasta 1,500 HNL/día rango alto

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento Argos/Bijao/UNO 42.5kg | 5.058 HNL/kg | 4.235 | 5.529 | Hoysv.com: cemento quintal 200-280 L (42.5kg), dinero.hn: Argos L180-225, Bijao L232, UNO L180, rango 185-235, Radio HRN L200-235, Reformasy L240-280 — mediana 215/42.5=5.058 | kg |
| MT-ARENA | Arena | 500 HNL/m3 | 400 | 600 | Estimado HN arena, validar con ferretería | m3 |
| MT-PIEDRA-PIC | Piedra picada | 550 HNL/m3 | 450 | 650 | Estimado | m3 |
| MT-ACERO-CAB | Varilla corrugada | 28 HNL/kg | 24 | 32 | Estimado HN varilla, validar | kg |
| MT-BLQ-15 | Bloque 6" 15x20x40 | 28 HNL/ud | 22 | 32 | Estimado HN bloque, similar a PA/SV pero en lempiras | ud |
| MT-CONC-210 | Concreto premezclado | 4500 HNL/m3 | 4000 | 5000 | Estimado HN concreto | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 1500 HNL/h | 1200 | 1800 | Estimado HN retroexcavadora |

## Nicaragua (NI)

### Mano de obra

Fuentes: Computrabajo NI 2026, Tusalario.org NI 2026, FiniquitoJusto salario mínimo NI 2026.

- **Salario mínimo:** C$6,188 agropecuario a C$13,848 construcción/financieros (MITRAB mar 2026-feb 2027, +4%)
- **Albañil:**
  - Computrabajo: media 13,958 NIO/mes albañil (6,400-15,987), oficial 12,084/mes, ayudante construcción 11,697/mes
  - Tusalario: albañil C$9,672-15,169 entry, C$11,298-20,326 tras 5 años (48h/semana)
  - Construcción mínimo: C$13,848.23/mes → diario 13,848/26=532.6 NIO/día, hora 54.57 NIO/h
- **Adopción CotizaT:**
  - Oficial general: 532.6 NIO/jornada 8h (400-600) → 66.57 NIO/h
  - Ayudante: 350 NIO/jornada (300-400) → 43.75 NIO/h

### Materiales directos

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento gris Canal 42.5kg Cemex | 12.294 NIO/kg | 9.411 | 14.117 | SINSA Nicaragua Cemento gris Canal 42.5kg C$522.57 (12.294/kg), TikTok $10/bolsa (~367 NIO) — se adopta SINSA | kg |
| MT-ARENA | Arena | 600 NIO/m3 | 500 | 700 | Estimado NI arena | m3 |
| MT-PIEDRA-PIC | Piedra picada | 650 NIO/m3 | 550 | 750 | Estimado | m3 |
| MT-ACERO-CAB | Varilla / acero | 38 NIO/kg | 32 | 44 | Estimado NI varilla | kg |
| MT-BLQ-15 | Bloque 15x20x40 | 32 NIO/ud | 28 | 38 | Estimado NI bloque | ud |
| MT-CONC-210 | Concreto | 5000 NIO/m3 | 4500 | 5500 | Estimado NI concreto | m3 |

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 1200 NIO/h | 1000 | 1400 | Estimado NI retroexcavadora |

## Factores canasta

Tasas corte: HN 26.82, NI 36.70

- HN cemento base local 0.225×26.82=6.0345 HNL/kg, observado 5.058 → factor 0.838
- NI base local 0.225×36.70=8.2575 NIO/kg, observado 12.294 → factor 1.489 (cemento NI más caro que base USD convertido)

## Generación

```bash
python tools/generar_matriz_precios_latam.py
# 388×16=6208 filas
python tools/generar_sql_precios_latam.py
```
