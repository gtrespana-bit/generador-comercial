# Análisis precios España en EUR — mano de obra a fondo (2026-08-25)

**Pregunta:** ¿Estamos poniendo un precio muy alto en España, sobre todo mano de obra?  
**Respuesta corta:** Sí, la matriz anterior usaba **tarifa de autónomo con beneficio** (27 €/h oficial, 18 peón) y generaba doble margen. Se corrige a **coste empresa** 21 €/h oficial y 15 €/h peón (zona media), con especialidades 20-24 €/h. Es 22% más barato y está alineado con coste real 20,50 €/h.

---

## 1. Qué cobra realmente un trabajador en España (2024-2026)

### 1.1 Convenio colectivo (salario bruto)

| Categoría | Fuente | Salario bruto | Hora bruta | Observaciones |
|---|---|---|---|---|
| Peón ordinario Nivel XII | Convenio General 2024-2026 BOE + Barcelona BOP 17/03/2026 | Total anual 20.311,18 € (990,40 base + 379,42 plus + 119,59 extrasalarial + pagas 1.309,21×3) | 11,70 €/h (20.311/1.736h) | Base Barcelona 2026: Salario Base 35,76 €/día, Total Día 42,72 € |
| Peón especialista XI | Barcelona BOP | Total anual 20.925,68 € | 12,05 €/h | Base 36,47 €/día |
| Oficial 2ª IX | Barcelona BOP | 21.814,62-24.016,87 € | 12,56-13,83 €/h | |
| Oficial 1ª VIII | Barcelona BOP + Skello 24k anual + ObraHub 1.700-2.000/mes | Total anual 22.196,63-31.290,43 € (Barcelona oficial 1ª 31.290,43 €) | 12,79-18,02 €/h | Skello: oficial 1ª 24.000 €/año (2025), incremento 3% vs 2024. ObraHub: oficial 1ª 11,50-13,50 €/h bruto (1.700-2.000/mes) |
| Capataz VII | Barcelona | 25.521,63-34.954,33 € | 14,70-20,13 €/h | |
| Encargado | Skello 30k, ObraHub 2.300-2.900/mes (15,50-19,50 €/h) | 30.000-40.600 € | 17,28-23,39 €/h | |

**Horas año convenio España:** 1.736h (límite legal construcción, con festivos) a 1.752h. Algunas provincias usan 1.736, otras 1.750. Para cálculo coste hora se usa 1.736 o 1.400 horas facturables reales (Presupix descuenta absentismo, vacaciones no facturables).

### 1.2 Coste empresa (lo que paga la empresa por tener al trabajador)

Fórmula 2026:
```
SS empresa 32,15% = CC 23,60% + Desempleo 5,50% + FOGASA 0,20% + FP 0,60% + MEI 0,75% (sube 0,10/año hasta 2029) + AT 1,50% mínimo
Coste empresa = Bruto anual ×1,3215 + costes fijos (EPI 95,40€/mes, gestor 110,80, seguro vida 48,50, formación 48,83, baja 62, despido 133, SS vacaciones 70,83, etc. según Autopromotor)
```

| Caso | Bruto anual | SS empresa 32,15% | Coste fijo anual | Coste empresa anual | Horas año | Coste hora empresa |
|---|---|---|---|---|---|---|
| Peón ordinario 20.311 € (Barcelona) | 20.311 | 6.530 | ~2.500 (EPI+gestor+etc.) | 29.341 | 1.736 | **16,90 €/h** |
| Oficial 1ª 24.000 € (Skello media nacional) | 24.000 | 7.716 | ~2.500 | 34.216 | 1.736 | **19,71 €/h** |
| Oficial 1ª 31.290 € (Barcelona alta) | 31.290 | 10.060 | ~2.500 | 43.850 | 1.736 | **25,26 €/h** |
| Autopromotor coste mensual 3.431,76 € ×12 =41.181 €/año | — | — | — | 41.181 | 1.736 | **23,72 €/h** con 1.736h, **20,50 €/h** con 1.736h? Autopromotor calcula 19,95 €/h con 172h/mes (4,3×5×8) y 20,50 con festivos |
| Presupix ejemplo oficial 21.000 € bruto + SS 6.720 =27.720 €/año /1.400h facturables = **19,80 €/h** coste hora real |

**Rango coste empresa real 2026 España:**
- Zona media (Castilla, Murcia, Andalucía): **17-20 €/h oficial 1ª** (Presupix)
- Zona alta (Madrid, Cataluña): **19-23 €/h** (Presupix, Barcelona 23,81 €/h con 31.290 anual)
- País Vasco/Navarra: **22-27 €/h**
- Autónomo con empresa propia (sin SS empresa pero con RETA, gestoría, seguro, herramienta): **20-26 €/h coste**

### 1.3 Tarifa autónomo / mercado (lo que factura el autónomo al reformista)

Es coste empresa + beneficio del autónomo + gastos (RETA ~350€/mes, gestoría, seguro RC, furgoneta, herramienta).

| Fuente | Oficial 1ª tarifa mercado | Peón tarifa | Observaciones |
|---|---|---|---|
| Motordepresupuestos 2026 | **22-32 €/h** oficial 1ª, 18-25 oficial 2ª, **15-21 peón** sin IVA | ±20% entre capitales | Tarifa con beneficio, no coste |
| Presupix autónomo | **22-38 €/h** autónomo trabajo habitual, oficial 1ª ref obra 28-42, oficial 2ª 24-35, peón 18-28 | Desplazamiento aparte | Orientación mercado |
| Autopromotor | **23-25 €/h mínimo autónomo sin IVA, máximo 35 €/h**. Larga duración casas 25 €/h, corta <10 días 30 €/h. Si <23 regala jubilación | — | Mínimo rentable |
| Cronoshare 2026 | **20-30 €/h oficial 1ª**, 14-22 peón, jornada 130-200 €/día (16,25-25 €/h) | Madrid/Barcelona 20-30/16-22, Valencia 18-26/15-20 | |
| Arquality 2026 | **20-30 oficial**, 15-20 peón (100 €/día), pladurista 20-30, pintor 20-35, electricista 25-35, fontanero 25-35 | Tabique pladur 25-42 €/m2 | Reforma integral |
| ObraHub autónomos TRADE | **Oficial 1ª 22-32 €/h**, peón 16-22 €/h | — | Factura completa sin SS |

**Factor beneficio autónomo:** Presupix usa 1,55× coste empresa → tarifa mercado. Ej: coste 19,80×1,55=30,69 €/h tarifa mercado (dentro de 22-32 y 26-36 zona media).

---

## 2. Matriz España anterior vs nueva

### Anterior (2026-08-22) — tarifa autónomo con beneficio

| Código | Descripción | Precio EUR/h | Min | Max | Origen | Problema |
|---|---|---|---|---|---|---|
| MO-OF1 | Oficial 1ª | 27 | 22 | 32 | referencia | Tarifa mercado 22-32 con beneficio, no coste empresa 17-23. Si catálogo aplica 30% margen → precio venta 35,1 €/h (27×1,3) = tarifa País Vasco 36-50, alto para zona media |
| MO-AYU | Peón | 18 | 15 | 21 | referencia | Tarifa mercado peón 15-21 con beneficio, no coste empresa 12-18. Venta 23,4 €/h alto vs mercado peón 15-21 |
| MO-OF1-ELE | Electricista | 29 | 24 | 34 | referencia | Tarifa mercado electricista 25-35 con beneficio, no coste empresa 18-22 |
| MO-OF1-PLO | Fontanero | 29 | 24 | 34 | — | Idem |
| MO-OF1-PIN | Pintor | 24 | 20 | 28 | — | Pintor banda baja oficial, pero 24 tarifa mercado no coste |
| MO-OF1-SOLD | Soldador | 31 | 26 | 36 | — | Oficio escaso, pero 31 es tarifa alta zona |

### Nueva (2026-08-25) — coste empresa

| Código | Descripción | Precio EUR/h | Min | Max | Jornada 8h | Origen | Justificación |
|---|---|---|---|---|---|---|---|
| MO-OF1 | Oficial 1ª albañil | **21** | 18 | 25 | 168 €/día (144-200) | referencia | Coste empresa zona media 17-20 + alta 19-23, País Vasco 22-27. 21 es centro zona media-alta, -22% vs 27 anterior. Venta con 30% margen =27,3 €/h → dentro tarifa mercado 22-32 y 26-36 zona media, no alto |
| MO-AYU | Peón/ayudante | **15** | 12 | 18 | 120 €/día (96-144) | referencia | Coste empresa peón 13,32-15,45 + costes → 15 €/h centro. Venta 19,5 €/h dentro tarifa peón 15-21 y 16-22 |
| MO-OF1-ALI | Alicatador | **22** | 18 | 26 | 176 €/día | referencia | +10-15% vs albañil general por especialidad, pero coste empresa no tarifa reforma 28-42 |
| MO-OF1-PISO | Solador | **22** | 18 | 26 | 176 | referencia | Idem |
| MO-OF1-ELE | Electricista | **24** | 20 | 28 | 192 | referencia | Bruto 13,5-17 → coste empresa 17,82-22,44 + costes → 24 €/h. Venta 31,2 €/h dentro tarifa mercado 25-35 |
| MO-OF1-PLO | Fontanero | **23** | 19 | 27 | 184 | referencia | Bruto 13-16 → coste 17,16-21,12 + costes → 23 €/h |
| MO-OF1-PIN | Pintor | **20** | 16 | 24 | 160 | referencia | Bruto 11-13,5 → coste 14,52-17,82 + costes → 20 €/h banda baja |
| MO-OF1-SOLD | Soldador | **25** | 20 | 30 | 200 | referencia | Oficio escaso, bruto 13-16,5 → coste 17-22 + costes → 25 €/h, no 36-50 tarifa País Vasco con beneficio |
| MO-OF1-CAB, CARP, CARPM, VIDR, AC, JARD, MON | Resto oficiales | **21** | 18 | 25 | 168 | derivado | Derivado del oficial general |
| MO-AYU-ESP | Ayudante especializado | **18** | 15 | 21,5 | — | derivado | (168+120)/16=18 €/h, antes 22,5 |

**Ahorro:** oficial -22,2%, peón -16,7%, especialidades -20-21%. Partida tipo friso 0,537h oficial: antes 14,50 € coste → ahora 11,28 € (-22,2%), venta 18,85→14,66 €.

---

## 3. Verificación de que no es precio alto (comparativas)

### 3.1 Coste empresa

| Zona | Coste empresa oficial 1ª (fuente) | Nuevo 21 €/h | Anterior 27 €/h |
|---|---|---|---|
| Media Castilla/Murcia | 17-20 €/h (Presupix) | +5-23% sobre rango bajo, dentro | +35-58% alto |
| Alta Madrid/Cataluña | 19-23 €/h (Presupix) + Barcelona 23,81 €/h (31.290/1.736×1,32) | -11,8% vs Barcelona alta (conservador) | +13,4% sobre Barcelona alta (alto) |
| Autopromotor medio | 20,50 €/h | +2,4% (no alto) | +31,7% alto |
| Presupix 19,80 €/h (1.400h facturables) | 19,80 | +6% (no alto) | +36% alto |

**Conclusión:** 21 €/h está en centro de coste empresa real, no alto. 27 €/h sí era alto.

### 3.2 Tarifa mercado (con beneficio empresa)

Si reformista cobra tarifa mercado = coste empresa ×1,55 (Presupix factor medio):

| Concepto | Coste empresa | Tarifa mercado (×1,55) | Mercado observado | ¿Alto? |
|---|---|---|---|---|
| Oficial 1ª nuevo | 21 €/h | **32,55 €/h** | 22-32 (Motor), 26-36 zona media (Presupix), 22-38 autónomo (Presupix) | En tope zona media, dentro zona alta 30-42 — **no alto** |
| Oficial 1ª anterior | 27 €/h | **41,85 €/h** | 22-32, 26-36 media, 30-42 alta | Por encima de 22-32 y tope 30-42 alta — **alto** |
| Peón nuevo | 15 €/h | **23,25 €/h** | 15-21 (Motor), 16-22 (ObraHub), 14-22 (Cronoshare) | Ligeramente por encima de 15-21 por beneficio empresa — **razonable** |
| Peón anterior | 18 €/h | **27,90 €/h** | 15-21, 16-22, 14-22 | Por encima de todos — **alto** |

### 3.3 Jornada

- Cronoshare jornada 130-200 €/día oficial → 16,25-25 €/h
- Nuevo oficial 168 €/día (21×8) → dentro 130-200, centro
- Anterior 216 €/día (27×8) → por encima de 200 tope jornada — alto

---

## 4. Recomendación final España

**Usar coste empresa como referencia nacional, no tarifa autónomo con beneficio.**

- **Oficial general 21 €/h (18-25)**, **peón 15 €/h (12-18)**, especialidades 20-24 €/h, soldador 25 €/h
- Mantener materiales sin cambios (cemento 0,14 €/kg, arena 28 €/m3, hormigón HA-25 100 €/m3, etc.)
- Mostrar en `/recursos` aviso "Coste empresa; tarifa autónomo mercado 22-32 €/h oficial con beneficio aparte"
- En PDF, mano obra no se muestra al cliente (interna), evita reclamación "el papel decía 5h"

**Archivos actualizados 2026-08-25:**
- `tools/generar_matriz_precios_espana.py` OFICIAL_GENERAL 168 (21/h), AYUDANTE 120 (15/h), especialidades 160-192
- `basedatos_partidas/salida/precios_recursos_espana.csv` 388 filas con nuevos precios
- `docs/cargar_precios_referencia_espana_2026-08-25.sql` 388 filas
- `docs/INVESTIGACION_PRECIOS_ESPANA.md` revisada con análisis a fondo
- `tests/test_espana.py` rango coste empresa 17-26 oficial, 11-19 peón

**Próximo paso operativo:** cargar en Supabase `cargar_precios_referencia_espana_2026-08-25.sql` (reemplaza solo ES).
