# Investigación precios Chile y Argentina — 2026-08-25

**Países:** CL (Chile, CLP) y AR (Argentina, ARS)
**Fecha corte:** 2026-08-25
**Matriz:** `basedatos_partidas/salida/precios_recursos_latam.csv` (388×8 países tras esta ronda)
**Tasas corte:** CL 925.90 CLP/USD (18/08/2026 925.903, currency.me.uk), AR 1497.38 ARS/USD (pluang 08/08/2026)
**Metodología:** `docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`

## Chile (CL)

### Mano de obra

Fuentes: ObraHub.app Chile 2026, OneEstimate.ai Chile 2026, CChC.

| Cargo | Jornal día CLP | Mes CLP | USD/día ref (925.9 CLP) | Observaciones |
|---|---|---|---|---|
| Ayudante / jornal | 30.000–40.000 | 650k–850k | 32–43 | Base ObraHub |
| Albañil 1ª | 45.000–60.000 | 950k–1.250k | 48–65 | ObraHub, OneEstimate 40k-60k |
| Albañil calificado (RM) | 65.000–85.000 | 1.2M–1.7M | 70–92 | ObraHub maestro mayor, OneEstimate listado Chile 65k-85k |
| Carpintero moldaje | 50.000–70.000 | 1.05M–1.4M | 54–75 | |
| Gasfíter | 55.000–85.000 | 1.15M–1.7M | 60–92 | |
| Eléctrico SEC | 55.000–90.000 | 1.15M–1.8M | 60–97 | |

Costo empleador: +35–40% sobre bruto (AFP 10%, salud 7%, gratificación, vacaciones, finiquito). Un maestro contrato 1.2M CLP cuesta ~1.7M CLP empresa.

Adopción CotizaT:
- Oficial general MO-OF1, MO-OF1-ALB: 55.000 CLP/jornada 8h (rango 45k-65k) → 6.875 CLP/h, referencia directa.
- Ayudante MO-AYU: 35.000 CLP/jornada 8h (30k-40k) → 4.375 CLP/h.
- MO-AYU-ESP derivado punto medio.
- Especialidades sin jornal propio: derivadas.

### Materiales directos observados

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento puzolánico | 191.6 CLP/kg | 143.6 | 203.6 | Sodimac CL: Transex 25kg $3.590 (144/kg), Polpaico 25kg $4.790 (192/kg), Melón 25kg $4.790, Fibra Chile $3.669/25kg, Imperial $4.790 — mediana 4.790/25=191.6 | kg |
| MT-ARENA | Arena fina | 33190 CLP/m3 | 16379 | 38190 | EmpresasPro Arena Fina M3 $33.190 IVA incl., Arena Gruesa $35.190-38.190, Madesal $16.379/m3 bulk, Piedra Natura $34.100 | m3 |
| MT-PIEDRA-PIC | Gravilla / ripio | 34500 CLP/m3 | 32190 | 36190 | EmpresasPro Gravilla 3/4 $32.190-36.190, Piedra Natura Gravilla Chancada $34.500, Arena Gruesa $35.190 | m3 |
| MT-ACERO-CAB | Fierro estriado | 1100 CLP/kg | 900 | 1300 | Estimado Chile 2026: fierro A63-42H, validar con Acma / Sodimac | kg |
| MT-BLQ-15 | Bloque hormigón 15 | 1840 CLP/ud | 990 | 1840 | Sodimac CL Bloque liso gris 14x19x39 $1.840, 140x190x390 $990 | ud |
| MT-CONC-210 | Hormigón HN25 / H25 | 110000 CLP/m3 | 80000 | 118405 | GlobalGTC Hormigón HN25 90% 20 C/7-8 $118.405/m3, calculaobrachile $80k-110k/m3 H20-H30, ONDAC G25 hecho obra $89.959/m3 | m3 |

Resto materiales: derivados canasta CL (factor materiales = precio_local / (precio_base_USD * tasa_corte)). Tasa corte 925.90.

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 30000 CLP/h | 25000 | 35000 | Estimado Chile retroexcavadora, operador maquinaria 65k-95k CLP/día OneEstimate |

## Argentina (AR)

### Mano de obra

Fuentes: UOCRA paritaria junio-agosto 2026, La Nación abril 2026, calcular.ar, Cronista, Infobae julio 2026.

Zonas UOCRA: A (CABA, BsAs y mayoría provincias), B (La Pampa, Neuquén, Río Negro, Chubut), C, C Austral.

Escala agosto 2026 por jornal (sitioandino.com.ar):
- Oficial especializado: $7.420 Zona A, $8.237 Zona B, $11.392 Zona C, $14.841 C Austral
- Oficial (albañil calificado): $6.348 Zona A, $7.049 Zona B, $10.680 Zona C, $12.695 C Austral
- Medio oficial: $5.866 Zona A, $6.502 Zona B, $10.306 Zona C, $11.732 C Austral
- Ayudante: $5.399 Zona A, $6.020 Zona B, $10.007 Zona C, $10.798 C Austral

Escala abril 2026 por hora (La Nación):
- Oficial Especializado $6.011/h, Oficial $5.142/h, Medio Oficial $4.752/h, Ayudante $4.374/h Zona A

Escala junio 2026 por hora (calcular.ar CCT 76/75):
- Oficial $5.703/h Zona A, $6.333 Zona B, $9.595 Zona C, $11.405 C Austral
- Ayudante $4.851/h Zona A, $5.409 Zona B, $8.990 Zona C, $9.701 C Austral
- Mensual sereno $881.193 Zona A, etc.

Adopción CotizaT (jornada 8h, Zona A):
- Oficial general: 45.624 ARS/jornada 8h (5.703/h ×8) — rango 41.136 (5.142×8) a 50.784 (6.348×8) → referencia.
- Ayudante: 38.808 ARS/jornada 8h (4.851×8) — rango 34.992 (4.374×8) a 43.192 (5.399×8).
- No incluye 20% asistencia perfecta ni SNR no remunerativa ni cargas (fondo cese laboral Ley 22.250).

### Materiales directos observados

| Código | Descripción | Precio adoptado | Min | Max | Fuente | Unidad |
|---|---|---|---|---|---|---|
| MT-CEMENTO | Cemento Portland CPN40 | 228.66 ARS/kg | 181 | 280 | MercadoLibre AR: Holcim 50kg $9.050-11.986, Avellaneda $11.433-12.729, Loma Negra $14.000, Avellaneda 25kg $4.999-6.680 — mediana 11.433/50=228.66; onemake.ai AR 2026 USD 8-12/bolsa ARS 9k-13.5k | kg |
| MT-ARENA | Arena | 33500 ARS/m3 | 28000 | 47644 | MercadoLibre AR Arena m3 $28.000-34.100-38.850, Corralón del Pero Arena fina $47.644/m3, Guanzetti $30.606/m3 por 6m3 | m3 |
| MT-PIEDRA-PIC | Piedra partida / ripio | 40000 ARS/m3 | 31445 | 67900 | MercadoLibre Piedra Partida $67.900/m3 bolsón, Corralón Ripio bruto fino $31.445/m3 | m3 |
| MT-ACERO-CAB | Hierro redondo ADN 420 | 1200 ARS/kg | 1000 | 1500 | Estimado AR siderurgia local Ternium/Acindar, validar con corralón | kg |
| MT-BLQ-15 | Bloque hormigón 19x19x39 | 1500 ARS/ud | 1300 | 1800 | MercadoLibre Bloque Hormigón 19x19x39 $1.650, $1.400, $1.386, $1.495, $1.760, $1.300-1.800 | ud |
| MT-CONC-210 | Hormigón elaborado H21 | 168478 ARS/m3 | 137655 | 199876 | MercadoLibre Hormigón Elaborado H21 $168.477 (5% off), $177.345, $174.294, $199.875 financiación — mediana $168.478; onemake.ai USD 95-130/m3 → ARS 142k-194k | m3 |

Resto materiales: derivados canasta AR (tasa corte 1497.38).

### Maquinaria

| Código | Precio | Min | Max | Fuente |
|---|---|---|---|---|
| MQ-RETRO | 35000 ARS/h | 30000 | 40000 | Estimado AR retroexcavadora, validar con operador, combustible, flete |

## Factores esperados

- CL materiales factor = precio_local / (precio_base_USD * 925.9). Con cemento base VE $0.225/kg → base local 0.225*925.9=208.33 CLP/kg, observado 191.6 → factor 0.92.
- AR materiales factor = precio_local / (precio_base_USD * 1497.38). Cemento base 0.225*1497.38=336.91 ARS/kg, observado 228.66 → factor 0.68 (cemento AR más barato que base VE convertido, coherente con producción local).
- Maquinaria CL factor ~0.8-1.2, AR ~1.0-1.3.

## Pendientes

- Validar con Sodimac CL, Easy, Imperial, GlobalGTC y corralones AR (Blaisten, Construmax) precios de: adhesivo C2TE, pintura látex, tubería PVC 110mm, cable THW 12 AWG, placa volcanita/Durlock 12.5mm, membrana asfáltica.
- Confirmar jornal con planilla real empresa chilena/argentina (incluye leyes sociales 29% CL, asistencia 20% AR).
- IVA: CL 19%, AR 21% — por_verificar en matriz, usuario configura.

## Generación

```bash
python tools/generar_matriz_precios_latam.py
# 388*8=3104 filas
python tools/generar_sql_precios_latam.py
# docs/cargar_precios_referencia_latam_2026-08-25.sql actualizado a 8 países
```
