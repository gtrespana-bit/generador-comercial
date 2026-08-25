# Investigación precios Panamá y El Salvador — 2026-08-25

**Países:** PA (Panamá) y SV (El Salvador) — ambos dolarizados (USD, PA con PAB paridad 1:1)
**Fecha corte:** 2026-08-25
**Matriz:** `basedatos_partidas/salida/precios_recursos_latam.csv` (388×6 países tras esta ronda)
**Metodología:** `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`

Ambos países cotizan en USD nativo, igual que EC. No se aplica tasa de conversión. Los precios se toman en USD y se congelan con rango min/max, fuente y confianza.

## Panamá (PA)

### Mano de obra

- **Fuente:** Cazvid Panamá 2026, CAPAC-SUNTRACS convenio colectivo 2025-2026, TrabajosWeb Panamá.
- **Salario mínimo construcción:** 3.30 PAB/h Región 2 (~686 PAB/mes), 3.51 PAB/h Región 1 (~730 PAB/mes). Balboa paridad 1:1 USD.
- **Convenio CAPAC-SUNTRACS (obra cubierta):** ayudante desde 4.67 PAB/h, obrero calificado hasta 6.30 PAB/h → 970-1300 PAB/mes a jornada 48h.
- **Adopción CotizaT:**
  - Oficial general (MO-OF1, MO-OF1-ALB): 45 USD/jornada 8h (rango 40-50) → 5.625 USD/h media, dentro de convenio.
  - Ayudante (MO-AYU): 35 USD/jornada 8h (30-40) → 4.375 USD/h, alineado con 4.67 mínimo convenio.
  - MO-AYU-ESP derivado punto medio oficial+ayudante.
  - Especialidades sin jornal local directo: derivadas del oficial general (confianza derivado).
- **Nota:** no incluye cargas patronales (13º, seguro, etc.). Validar con empresa.

### Materiales directos observados

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento Portland gris | 0.1941 USD/kg | 0.188 | 0.2023 | Novey PA CEMEX $8.60/42.5kg, DoitCenter CHAGRES $7.99/42.5kg, HOPSA Argos $8.25/42.5kg — mediana 8.25 | kg |
| MT-BLQ-15 | Bloque concreto 15x20x40 | 0.95 USD/ud | 0.71 | 0.99 | Panablock 15x20x45 $0.71, HOPSA 6x8x16 $0.95, HOPSA gris $0.99 | ud |
| MT-ARENA | Arena cribada | 34 USD/m3 | 30 | 38 | Panablock Arena de Mar a granel 30yd $772.5/22.94m3=33.67, 20yd $515/15=34.33 | m3 |
| MT-PIEDRA-PIC | Piedra picada / agregado grueso | 35 USD/m3 | 30 | 40 | Estimado a partir de arena + transporte; validar con cantera Panamá | m3 |
| MT-ACERO-CAB | Acero corrugado varilla | 1.10 USD/kg | 0.95 | 1.25 | Derivado de EC $0.98/kg + mercado PA ligeramente superior | kg |
| MT-CONC-210 | Concreto premezclado f'c 210 | 125 USD/m3 | 100 | 150 | PremExpress PA $100-300/m3, generadordeprecios.info Panamá $124.33/m3 premezclado 210, $117.74 plantilla | m3 |

Resto de materiales: derivados de canasta nacional PA (factor mediano materiales = precio_local / (precio_base_USD * tasa_corte)). Tasa corte PA=1.0, factor se calcula sobre los 6 anclas directas.

### Maquinaria

| Código | Descripción | Precio | Min | Max | Fuente |
|---|---|---|---|---|---|
| MQ-RETRO | Retroexcavadora | 35 USD/h | 30 | 45 | Estimado Panamá 2026: superior a EC $30/h por costo equipo y combustible; validar con operador, combustible, flete |

Resto maquinaria: derivado de factor maquinaria PA.

## El Salvador (SV)

### Mano de obra

- **Fuentes:** CASALCO abril 2025, ConstruccionElSalvador.com 2026, Computrabajo SV, Cazvid SV.
- **Salario mínimo legal sector industria/comercio/servicios:** 408.80 USD/mes (~13.44 USD/día, 1.68 USD/h) vigente junio 2025, sin cambios 2026.
- **Mercado real construcción:**
  - Jornal albañil calificado: $25-40/día (ConstruccionElSalvador.com), $25 diario maestro en zonas diáspora, $30-40 en AMSS.
  - Ayudante: $15-20/día (ConstruccionElSalvador.com), $10-15/día informal, $18-35/día según dificultad (Reddit SV).
  - Computrabajo: oficial 776 USD/mes (~29.8/día), albañil 375 USD/mes (~12.5/día informal), ayudante 352 USD/mes.
- **Adopción CotizaT:**
  - Oficial general: 28 USD/jornada 8h (25-35) → 3.5 USD/h, dentro de rango $25-40 y por encima del mínimo legal.
  - Ayudante: 16 USD/jornada 8h (13-20) → 2.0 USD/h, alineado con $15-20 mercado.
  - MO-AYU-ESP derivado.
- **Nota:** no incluye prestaciones (vacaciones, aguinaldo, ISSS, AFP). En SV factor prestaciones ~1.30-1.40 sobre jornal base si se quiere costo empresa.

### Materiales directos observados

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento Portland | 0.2054 USD/kg | 0.1859 | 0.2318 | CASALCO abril 2025 Bolsa 42.5kg $8.73, EPA SV Holcim Maestro $7.90, Holcim Fuerte $9.85, Fortaleza $8.70, Maya $8.60 — mediana CASALCO $8.73 | kg |
| MT-BLQ-15 | Bloque 15x20x40 | 0.40 USD/ud | 0.35 | 0.45 | ConstruccionElSalvador.com julio 2026: block 15x20x40 $0.35-0.45 AMSS, $0.30-0.40 interior; CASALCO millar 10x20x40 $528 → $0.528/ud para 10cm | ud |
| MT-ARENA | Arena de río | 35 USD/m3 | 17 | 38 | CASALCO Arena Río $35/m3, viaje 5m3 arena fina $85-110 (17-22/m3) AMSS, $65-85 cerca cantera | m3 |
| MT-PIEDRA-PIC | Grava | 45.05 USD/m3 | 22 | 50 | CASALCO Grava $45.05/m3, viaje 5m3 grava $110-140 (22-28/m3) AMSS | m3 |
| MT-ACERO-CAB | Hierro corrugado varilla | 1.15 USD/kg | 1.0 | 1.35 | EPA SV varilla 3/8\" 6m $3.50 (~3.35kg → $1.04/kg), 1/2\" $9.50-12.00/6m (~5.95kg → $1.6-2.0/kg) — mediana $1.15 | kg |
| MT-CONC-210 | Concreto 210 kg/cm2 | 135.35 USD/m3 | 130 | 145 | CASALCO Producto Cemento Concreto 210 $135.35/m3, FISDL 2024 $271-275 premezclado (incluye colocación) — se adopta CASALCO puesto en obra | m3 |

Resto materiales: derivados canasta SV (tasa corte 1.0).

### Maquinaria

| Código | Descripción | Precio | Min | Max | Fuente |
|---|---|---|---|---|---|
| MQ-RETRO | Retroexcavadora | 30 USD/h | 25 | 35 | Estimado SV similar a EC $30/h, Panamá $35/h — validar con operador, combustible, flete, mínimo horas |

## Factores de canasta

Al generar matriz, se calcula mediana de (precio_local / precio_base_USD) para materiales y maquinaria por país, usando solo referencias con confianza referencia.

Esperado:
- PA materiales factor ~0.86-1.2 (cemento más barato que base VE $0.225/kg, arena similar, bloque similar)
- SV materiales factor similar ~0.9-1.1
- Maquinaria PA ~1.1-1.3 × base USD, SV ~1.0-1.2

Estos factores alimentan 382 recursos restantes como confianza derivado, con observación "Precio referencial nacional derivado de la canasta de mercado investigada para esta familia; no es una cotización de tienda."

## Pendientes y validación

- Validar con ferreterías locales Panamá (Cochez, Novey, Doit) y El Salvador (EPA, Freund, Vidrí) precios de: adhesivo cerámico C2TE, pintura caucho/acrílica, tubería PVC 4\", cable THW 12 AWG, placa yeso 12.5mm, manto asfáltico.
- Confirmar jornal oficial con planilla real de empresa panameña/salvadoreña (CAPAC-SUNTRACS tabla 2026 y CASALCO).
- Añadir MQ-VOLQ para PA/SV cuando haya tarifa volquete local.
- IVA: PA 7%, SV 13% — documentado en app/paises.py, no incluye IVA en precios por defecto (por_verificar).

## Uso en CotizaT

Tras generar matriz:

```bash
python tools/generar_matriz_precios_latam.py
# genera 388*6=2328 filas
```

Luego SQL:

```bash
python tools/generar_sql_precios_latam.py
# genera docs/cargar_precios_referencia_latam_2026-08-25.sql
```

Cargar en Supabase SQL Editor (transacción idempotente, solo reemplaza referencias nacionales PA/SV sin tocar overrides de empresa).
