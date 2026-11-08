# Convención de medida: qué se hace cuando el recurso no dice la medida

Fecha: 2026-11-07 · Política fijada por el titular: *«si no tiene medida usa algo medio:
bloque exterior 20 o 25, interior 15, la pasta algo medio, igual con todo lo demás»* ·
Tabla: `espana_convenciones_medida_2026-11-07.csv` (56 recursos) · Resultado:
`espana_impacto_convenciones_2026-11-07.csv` · Reproducible con
`tools/adjudicar_convenciones_espana.py` y `tools/impacto_recursos_espana.py`.

## 1. La regla

Antes, un recurso sin medida se quedaba bloqueado con la nota «el banco tiene la familia,
pero la ficha no fija la medida». Eso dejaba 56 recursos parados y 924 usos sin precio.
A partir de hoy:

1. **Se adopta la medida media de la práctica española** y se escribe en el criterio, para
   que cualquiera pueda discutirla.
2. **Se busca la ficha del banco con esa medida exacta**. Si existe, se aplica su precio y
   el recurso queda con precio trazado.
3. **Si el banco no tiene la ficha con esa medida**, el recurso queda
   `pendiente_cotizacion` **con la convención ya escrita**: la siguiente ronda solo tiene
   que buscar el precio, no volver a decidir la especificación.
4. **La convención nunca rebaja una exigencia física**: un vidrio templado de 10 mm para
   mampara no se sustituye por uno de 6 mm aunque sea lo único que hay en el banco.

## 2. Las convenciones, familia por familia

| Familia | Medida o clase convencional | Por qué |
|---|---|---|
| Bloque de hormigón | 20×20×40 exterior, 15×20×40 tabique | La fábrica exterior de vivienda se ejecuta en 20 cm; el tabique resistente, en 15 |
| Bloque de arcilla | 15×20×30 en fachada, 10×20×30 en tabique | Igual criterio, con el hueco de arcilla habitual |
| Caja eléctrica | 100×100 mm empotrada | La caja de registro y la de mecanismo comparten módulo |
| Tornillería de placa | 3,5×25 autotaladrante a perfil | Es la fijación que el recurso describe (placa a estructura metálica) |
| Tubo de acero | Estructural rectangular, 2-3 mm | La herrería de rejas y barandas se hace con tubo conformado |
| Acero inoxidable | AISI 304 en perfil conformado | El 304 es el grado de interior; el 316 se reserva a ambiente agresivo |
| Llave de paso | Esfera 1/2" (PPR 20 mm) | 20 mm y 1/2" son la misma boca de instalación |
| Árido | Arena de río 0/5 lavada | Árido de referencia para camas y rellenos |
| Resina epoxi | Bicomponente base, con árido para autonivelante | El autonivelante es la misma resina más carga |
| Celosía | Fija de aluminio con marco | El recurso dice aluminio; el precio anterior era de PVC |
| Adoquín | Rectangular 20×10×8 gris | El más frecuente en pavimento exterior de vivienda |
| Encofrado | Madera en muros, con puntales, amortizada | El recurso ya dice «amortizado por número de usos» |
| Vidrio | Templado 10 mm en mampara, flotado 6 mm en paño | La resistencia exigible manda sobre la disponibilidad del banco |

## 3. Lo aplicado: 18 recursos, 621 usos

| Recurso | Usos | Antes | Ahora | Ficha |
|---|---:|---:|---:|---|
| `MT-ELE-CAJA` | 177 | 1,253 | **1,02** | P15GK010 caja registro empotrar 100×100 |
| `MT-TORN` | 154 | 0,034 | **0,03** | P04CA080 tornillo PYL-perfil 3,5×25 |
| `MT-FORM-MADERA` | 73 | 10,00 | **25,56** | P30IG040 encofrado madera en muros |
| `MQ-NIVEL-LASER` | 41 | 3,225 | **1,00** | M11L040 nivel láser |
| `MT-TUBO-ACERO` | 36 | 2,222 | **1,71** | P03AT010 acero en tubo rectangular |
| `MT-CABLE-COBRE-DESN` | 23 | 5,127 | **7,22** | P15EB010 cobre desnudo 35 mm² |
| `MT-ACERO-INOX` | 17 | 15,949 | **5,15** | P39DBA020 inox austenítico conformado |
| `MT-PLO-LLAVE` | 17 | 5,127 | **6,69** | P41V350 llave de paso 1/2" |
| `MQ-PULIDORA` | 16 | 6,597 | **4,69** | M10HP010 pulidora mecánica |
| `MT-ARENA` | 13 | 28,00 | **16,50** | P01AA030 arena de río 0/5 |
| `MT-EPOXI-PISO` | 13 | 17,089 | **17,12** | P01UA010 resina epoxi |
| `MT-CELOSIA` | 10 | 29,620 | **106,31** | P12RC020 celosía fija de aluminio |
| `MQ-BOMBA-ACHI` | 7 | 3,518 | **2,32** | M01DS010 bomba sumergible 1,1 kW |
| `MT-BARANDA-PROV` | 6 | 5,127 | **6,68** | P31CB310 barandilla de huecos |
| `MT-BOTIQUIN` | 6 | 39,873 | **40,32** | P31BM160 botiquín portátil de obra |
| `MT-RED-SEG` | 5 | 3,190 | **1,91** | P31CR030 red poliamida 7×7 D=3 |
| `MT-ADOQUIN` | 3 | 17,658 | **12,71** | P08CA010 adoquín 20×10×8 gris |
| `MT-PIN-IGNFUGA` | 3 | 13,671 | **9,89** | P24PF020 pintura intumescente |

## 4. Los cuatro cambios que suben mucho, explicados

* `MT-CELOSIA` **+259 %**: el precio anterior era de PVC (28,10 €/m² es la celosía fija de
  PVC del propio banco). El recurso dice *aluminio*, y la celosía fija de aluminio está a
  106,31 €/m². Se corrige el material, no el criterio.
* `MT-FORM-MADERA` **+156 %**: 10,00 €/m² no cubría un encofrado con puntales y
  arriostramiento; la ficha del banco, que es exactamente ese concepto, está a 25,56.
* `MT-ACERO-INOX` **−68 %**: 5,15 €/kg es el precio del perfil conformado AISI 304 como
  material. El precio anterior mezclaba material y fabricación; la fabricación ya está en
  la mano de obra de las partidas.
* `MQ-NIVEL-LASER` **−69 %**: el banco cotiza la hora de nivel láser a 1,00 €, muy por
  debajo de las tarifas de mercado que se venían usando.

## 5. Lo que sigue pendiente, con la convención ya decidida

38 recursos (304 usos) quedan `pendiente_cotizacion` porque el banco no tiene la ficha con
la medida convencional. **No hay que volver a decidir la especificación**, solo buscar el
precio:

* **Compra de máquina** (`MQ-MART-NEUM` 45, `MQ-ROZAD` 30, `MQ-LIJAD-PISO` 3): entran en el
  modelo de compra y amortización que ya está en producción para las otras 13 máquinas.
* **Producto sin ficha en el banco** (`MT-VIDRIO-TEMP` 35, `MT-VIDRIO-6` 23, `MT-SOPORTE-AC`
  36, `MT-REGUL-GAS` 37, `MT-AISL-REFLECT` 9, `MT-SUBESTRUCTURA` 7, `MT-PERSIANA-ALU` 4,
  `MT-BARRA-APOYO`…): cotización de tienda, con la convención del §2 como referencia de
  búsqueda.
* **Compuestos que exigen desglose** (`MT-BARRA-TIERRA`, `MT-LLAVE-PROV`): el banco cotiza
  una parte del conjunto.
* **Sin uso actual** (domótica, CCTV, planta eléctrica): 0 usos, se abordan al final.

## 6. Reserva

La convención es una **decisión de ingeniería declarada**, no un dato del proveedor. Cada
precio nuevo lleva en el registro la frase «Convención de medida 2026-11-07: el recurso no
fija medida o clase y se adopta…» y la ficha exacta usada. Si un proyecto fija otra medida,
el precio se recalcula con la ficha de esa medida: la tabla de convenciones es el punto de
partida de esa búsqueda, no una excusa para no hacerla.
