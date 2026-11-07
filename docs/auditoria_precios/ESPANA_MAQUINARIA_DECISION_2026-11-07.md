# Maquinaria: por qué el banco no la confirma y qué hace falta para cerrarla

Fecha: 2026-11-07 · 14 recursos de maquinaria sin precio (1.415 usos) · Base de contraste:
Extremadura 2026 · Parámetros: `espana_maquinaria_horaria_parametros_2026-11-07.csv` ·
Resultado: `espana_maquinaria_horaria_propuesta_2026-11-07.csv`
(reproducible con `tools/coste_horario_maquinaria_espana.py`).

## 1. La tarifa horaria del banco no es un modelo de coste

Buscando la misma máquina en la base aparecen tarifas que no pueden convivir en un
mismo modelo de amortización:

| Máquina | Fichas del banco | €/h |
|---|---|---|
| Taladro 750 W | `M11T010`, `M16A590` | 0,84 / 0,91 |
| Taladradora mecánica | `M03L010`, `M11T030` | **8,11 / 8,27** |
| Motosierra eléctrica | `M09AM010` | 2,26 |
| Martillo picador 9 kg | `M06MI010` | 1,90 |
| Martillo picador 12 kg | `M06MI020` | **21,64** |
| Cortadora de pavimentos | `M13F010` | 9,15 |

Si se invierte el cálculo —qué vida útil implicaría cada tarifa con un precio de
adquisición real— el taladro de 750 W implica **≈230 h** de vida y la motosierra
eléctrica **≈41 h** para la misma convención. No es un modelo: son tarifas de origen
distinto (alquiler, precio de mercado, conserje incluido…). Por eso **ninguna de estas
fichas puede «confirmar»** el precio de un recurso horario: confirmaríamos una convención
desconocida.

## 2. El modelo, con parámetros explícitos

    coste_h = adquisición / vida_útil × (1 + mantenimiento)
              + potencia × precio_energía × factor de carga
              + consumibles

Precios de adquisición con fuente y fecha (IVA incluido en la ficha, convertido a neto):

| Recurso | Precio actual | Adquisición | Fuente | Modelo 250 h | Modelo 500 h | Modelo 1.000 h |
|---|---|---|---|---|---|---|
| `MQ-TALADRO` (1.025 usos) | 2,199 | 149,33 € | Bosch GBH 2-26 DRE 790 W, 180,69 € IVA incl. | **0,78** | 0,44 | 0,27 |
| `MQ-SIERRA` (199) | 4,251 | 72,57 € | Einhell GC-EC 2040 2.000 W, 87,81 € IVA incl. | **0,57** | 0,41 | 0,32 |
| `MQ-CORT-AGUA` (91) | 4,691 | 296,69 € | Zipper ZI-FS200 800 W, 359,00 € IVA incl. | **1,46** | 0,78 | 0,44 |
| `MQ-ATORN` (162) | 2,052 | 95,00 € | Atornillador pladur 18 V, 114,95 € IVA incl. (sin batería) | **0,44** | 0,22 | 0,11 |

Energía 0,20 €/kWh y factor de carga 0,6 — **parámetros de trabajo, no datos**: hay que
fijarlos con la factura eléctrica y la práctica de taller. Con 250 h de vida, el modelo
del taladro (0,78 €/h) coincide con la ficha del banco (0,84 €/h) y deja el precio actual
(2,199 €/h) en 2,8 veces el coste de la máquina. La diferencia razonable son las **brocas**,
que el recurso incluye y que nadie ha cotizado todavía.

## 3. Lo que no se puede cerrar todavía

Ocho máquinas no tienen aún precio de adquisición con fuente y por eso no llevan número:
`MQ-MEZCL` (120 usos), `MQ-MART-ELEC` (110), `MQ-LIJAD` (60), `MQ-BATID` (60),
`MQ-DETECTOR` (61), `MQ-AMOLA` (50), `MQ-ASPIR` (91), `MQ-SOLDADORA` (105). Para ellas el
banco tampoco tiene ficha equivalente (solo barredora de 109,56 €/h, soldadura de
polietileno de 18,30 €/h y lijadora de gotelé de 2,03 €/h, que son otros artículos).

`MQ-ANDAMIO` queda fuera del modelo por unidad: el banco lo alquila en €/m²·día
(0,11–0,36) y cobra el montaje en €/m² (5,22–7,46); convertirlo a €/h exige un rendimiento
de montaje y una superficie por persona que no están definidos.

## 4. Decisión pendiente (no aplicada)

1. **Convención de vida útil**: 250 h (una temporada, lo que parece usar el banco) frente a
   500 o 1.000 h. Cambia el precio de un taladro entre 0,78 y 0,27 €/h.
2. **Energía**: 0,20 €/kWh es un supuesto. Con factura real (0,14–0,25) el efecto es de
   ±0,05 €/h en herramienta pequeña.
3. **Brocas, discos y cadenas**: el recurso dice «con brocas» (taladro) y la cortadora
   «con disco de diamante». Hay que cotizar consumible y vida, o cambiar la descripción
   para que no los incluya.
4. **Sustituir o no el precio actual**: la propuesta deja los precios como están hasta que
   se fijen 1–3. Aplicar 0,78 €/h en `MQ-TALADRO` bajaría el coste de 1.025 partidas
   (−64 %), un cambio que necesita decisión explícita, no un lote automático.

## 5. El caso de los agregados: 968 partidas

19 recursos son cestas de artículos (`MT-CONS-DEM` 398 usos, `MQ-RODILLO` 151,
`MQ-SOLDADORA` 105, `MT-OXI-CONS` 54…). Desglosarlos no es una búsqueda de precio: exige
crear recursos nuevos y **reescribir los descompuestos de 968 partidas**. Es una decisión
de catálogo, con impacto en presupuestos ya emitidos, y no se ha hecho.

## 6. Reproducir

```bash
python tools/coste_horario_maquinaria_espana.py --precio-energia 0.20
```
