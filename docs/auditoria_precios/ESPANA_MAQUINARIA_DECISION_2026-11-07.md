# Maquinaria: modelo de compra y amortización, aplicado

Fecha: 2026-11-07 · 13 recursos de maquinaria (2.185 usos) · Decisión del titular:
**no se modela el alquiler, se modela la compra dividida por la vida útil** ·
Parámetros: `espana_maquinaria_horaria_parametros_2026-11-07.csv` · Resultado:
`espana_maquinaria_horaria_propuesta_2026-11-07.csv` · Impacto:
`espana_impacto_maquinaria_2026-11-07.csv` · Reproducible con
`tools/coste_horario_maquinaria_espana.py`, `tools/adjudicar_maquinaria_espana.py` y
`tools/impacto_maquinaria_espana.py`.

## 1. Qué se ha decidido y con qué aritmética

El precio de cada máquina es lo que cuesta tenerla en obra una hora, comprándola:

    coste_h = adquisición / vida_útil × (1 + tasa_mantenimiento)
              + potencia_kW × 0,20 €/kWh × factor_carga
              + consumibles_€/h

* **Adquisición**: precio de tienda con IVA, convertido a neto, con URL y fecha en la
  ficha de parámetros. Una máquina, una fuente.
* **Vida útil**: hipótesis de ingeniería declarada por máquina (herramienta ligera 250 h,
  herramienta de uso medio 400–500 h, equipo con motor de inducción o electrónica 500–1.000 h).
  Es el parámetro que más mueve el resultado, así que cada precio se publica con su
  sensibilidad a ×0,5 y ×2 de vida.
* **Mantenimiento**: 10–15 % del valor de compra repartido en la vida (correas, escobillas,
  rodamientos, reparaciones). No incluye mano de obra de taller.
* **Energía**: 0,20 €/kWh fijado por el titular, con factor de carga 0,4–0,8 según si la
  máquina trabaja por impulsos (taladro) o de forma continua (soldadora, aspirador, hormigonera).
* **Consumibles**: sí, incluidos, porque el recurso los describe («con brocas», «con disco de
  diamante»). Se valoran a precio de tienda y se reparten por horas de uso reales: brocas SDS
  cada 100 h, disco de diamante cada 25 h, electrodo a 0,20 kg/h, cadena de motosierra cada 40 h.

## 2. Los 13 precios publicados

| Recurso | Usos | Antes €/h | **Ahora €/h** | Adquisición neta | Vida | Mant. | Consumibles | Sensibilidad ×0,5–×2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `MQ-TALADRO` | 1.025 | 2,199 | **1,03** | 149,33 € (Bosch GBH 2-26 DRE) | 250 h | 15 % | 0,25 (brocas SDS cada 100 h) | 1,72–0,69 |
| `MQ-SIERRA` | 199 | 4,251 | **0,97** | 72,57 € (Einhell GC-EC 2040) | 300 h | 15 % | 0,45 (cadena + aceite) | 1,25–0,83 |
| `MQ-ATORN` | 162 | 2,052 | **0,62** | 142,15 € (pladur 18 V, 2 baterías) | 300 h | 15 % | 0,08 (puntas) | 1,17–0,35 |
| `MQ-RODILLO` | 151 | 1,319 | **0,50** | 49,59 € (juego completo de pintura) | 100 h | — | incluidos (se repone el juego) | 0,99–0,25 |
| `MQ-MEZCL` | 120 | 3,000 | **1,25** | 350,72 € (hormigonera Hecht 200 l) | 500 h | 15 % | 0,20 (paletas) | 2,05–0,84 |
| `MQ-MART-ELEC` | 110 | 5,717 | **2,09** | 461,40 € (SDS-Max 1.100 W) | 400 h | 15 % | 0,63 (punta/cincel cada 40 h) | 3,42–1,43 |
| `MQ-SOLDADORA` | 105 | 5,278 | **1,43** | 148,76 € (inverter 200 A) | 800 h | 15 % | 0,70 (electrodo 0,20 kg/h) | 1,65–1,33 |
| `MQ-ASPIR` | 91 | 3,079 | **0,61** | 180,00 € (1.400 W / 30 l) | 800 h | 15 % | 0,13 (sacos y filtros) | 0,87–0,48 |
| `MQ-CORT-AGUA` | 91 | 4,691 | **1,95** | 296,69 € (Zipper ZI-FS200) | 400 h | 15 % | 1,00 (disco diamante cada 25 h) | 2,80–1,52 |
| `MQ-DETECTOR` | 61 | 3,812 | **0,30** | 255,37 € (Bosch D-tect 120) | 1.000 h | 10 % | 0,02 (pilas) | 0,58–0,16 |
| `MQ-BATID` | 60 | 2,346 | **0,67** | 119,39 € (mezcladora 1.600 W) | 500 h | 15 % | 0,20 (varilla) | 0,94–0,53 |
| `MQ-LIJAD` | 60 | 3,079 | **0,95** | 122,31 € (lijadora de pared 750 W) | 250 h | 15 % | 0,30 (lijas) | 1,52–0,67 |
| `MQ-AMOLA` | 50 | 3,518 | **1,86** | 198,00 € (2.400 W, 230 mm) | 400 h | 15 % | 1,00 (disco diamante cada 25 h) | 2,43–1,57 |

Los precios ya están volcados en el registro maestro y en la matriz
(`basedatos_partidas/salida/precios_recursos_espana.csv`), con código de fuente
`MODELO-MQ-2026-11-07`, ámbito «España (modelo propio, sin banco)» y estado
`en_revision`: el modelo sustituye a la tarifa, no la confirma.

## 3. Por qué el precio baja entre un 47 % y un 92 %

El precio anterior no era una tarifa de alquiler: era una referencia de mercado sin
convención declarada. Ahora hay convención y se puede auditar. Dos comprobaciones
independientes de que el orden de magnitud nuevo es el correcto:

1. **Inversión de la ficha del banco.** Extremadura 2026 publica el taladro de 750 W a
   0,84 €/h. Con 149 € de adquisición, esa tarifa implica **≈230 h** de vida; nuestro
   modelo, con 250 h declaradas y consumibles, da 1,03 €/h. Coherente.
2. **BCCA 2023 (segunda base oficial, cargada en esta ronda).** Publica
   `MARTILLO ELÉCTRICO` a **1,40 €/h**. Nuestro martillo SDS-Max de 5 kg, con punta y
   cincel incluidos, sale a 2,09 €/h; el precio anterior era 5,72 €/h, **cuatro veces**
   la base oficial andaluza. El modelo cae donde debe caer.

Las tarifas del banco siguen sin poder confirmar nada (0,84 frente a 8,11 €/h para dos
taladros), así que la banda del banco se guarda como contraste, nunca como precio.

## 4. Efecto sobre el catálogo

`tools/impacto_maquinaria_espana.py` propaga el cambio con el rendimiento de cada
descompuesto y el porcentaje de complementarios:

* **1.511 partidas** afectadas de 2.016.
* Efecto por partida: **mediana −0,5 %**, mínimo −10,8 %, máximo −0,0 %.
* Efecto acumulado sobre la suma de precios unitarios: **−886,52 €** en todo el catálogo.

Es decir: la maquinaria pesa poco en el precio unitario, y ese poco estaba
sobrevalorado. Ninguna partida cambia de orden de magnitud, que es la prueba de que el
modelo no rompe el catálogo.

## 5. Qué queda fuera y por qué

* **`MQ-ANDAMIO` (190 usos)**: el banco lo cotiza en €/m²·día (0,11–0,36) y el montaje en
  €/m² (5,22–7,46). El recurso está en €/h y no define superficie por persona ni
  rendimiento de montaje; convertirlo sería inventar el rendimiento. No se toca.
* **24 recursos de maquinaria** siguen en `requiere_modelo_propio` (grúa, retro, volquete,
  extendedora, fresadora, etc.): son equipos que en obra real no se compran para una
  actuación, y el banco sí los cotiza por hora o por día con convención razonable. Ahí el
  modelo de compra no aplica y no se ha forzado.
* **No se incluye** coste de financiación ni seguro del inmovilizado (≈0,05 €/h de orden
  de magnitud). Está declarado como reserva en cada ficha.

## 6. Reserva global

El precio es una **estimación propia trazable**, no una tarifa contrastada: no existe
ficha de banco equivalente para estas 13 máquinas. La vida útil es la hipótesis que hay
que sustituir por horas reales de obra en cuanto haya partes de trabajo; cambiarla es
editar una columna y volver a ejecutar dos comandos.
