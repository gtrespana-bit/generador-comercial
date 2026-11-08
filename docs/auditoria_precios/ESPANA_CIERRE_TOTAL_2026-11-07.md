# Cierre total de precios de España — 7 de noviembre de 2026

Decisión del titular: **no queda ningún recurso sin precio**. «Todos, busca la mejor
manera de hacerlo». Este documento cierra los **133 recursos** que quedaban abiertos en
`espana_identidad_huecos_2026-11-07.csv` y explica, recurso a recurso y por familia, con
qué evidencia se ha valorado cada uno. La tabla de trabajo es
`espana_cierre_total_2026-11-07.csv` (133 filas: `codigo_recurso`, `metodo`, `precio`,
`referencia`, `criterio`, `confianza`).

## 1. Qué se ha cerrado

| Estado | Antes | Ahora |
|---|---|---|
| Recursos con precio revisado | 255 / 388 | **388 / 388** |
| Recursos sin precio | 133 | **0** |
| Huecos de identidad clasificados | 133 | 133 (registro histórico, todos cerrados) |
| `confirmado_referencia` | 37 | 37 |
| `en_revision` | 351 | 351 |
| Filas en la matriz ES | 388 (8 directas + 380 derivadas) | 388 (43 directas + 345 derivadas) |
| Filas en el SQL de carga | 388 | 388 (sigue **sin ejecutar**) |

No se ha confirmado ningún recurso nuevo: cerrar un precio no es confirmarlo. Los 133
entran como `en_revision` con fuente, código, criterio y reserva escritos, que es lo que
exige el contrato del registro.

## 2. La jerarquía de evidencia

Cada recurso lleva su método en la columna `metodo`. No todos valen lo mismo y el orden
de la tabla va de mayor a menor evidencia:

| Método | Recursos | Qué significa |
|---|---|---|
| `banco` | 25 | La ficha del banco **es** el artículo (identidad directa, misma unidad). |
| `modelo_propio` | 12 | Máquina valorada por **compra ÷ vida útil** + mantenimiento + energía + consumibles. |
| `compuesto` | 12 | Paquete de consumibles valorado por sus piezas, con fichas del banco cuando existen. |
| `banco_analogia` | 28 | La ficha es de la **misma familia y unidad**, con otra medida o tipo. Nivel de precio, no cotización. |
| `modelo_alquiler` | 1 | Andamio: tarifa de alquiler del banco convertida a hora con el rendimiento del catálogo. |
| `alquiler_mercado` | 1 | Baño portátil: es un servicio mensual, no una máquina que se compre. |
| `mercado_rango` | 54 | **Sin ficha de banco.** Se conserva el precio de la matriz por caer dentro de una horquilla de mercado declarada en el criterio. |

Confianza declarada: **alta 7, media 59, baja 67**. La confianza no mide el precio, mide
la fuerza de la evidencia; por eso 54 recursos quedan en `baja` aunque tengan precio.

Regla aplicada en todo el lote: **si el alcance del artículo del banco no es el del
recurso, no se sustituye el precio**. Dieciséis analogías que en una primera pasada
parecían razonables se descartaron al leer la ficha completa y pasaron a `mercado_rango`
(ver §6): el caso típico era una ficha por unidad usada para un recurso por metro
(`MT-RIEL-CORRED`), una ficha de compra para un recurso que se amortiza por uso
(`MT-LAMP-OBRA`) o un producto distinto con nombre parecido (césped artificial frente a
grama natural, lámina de PVC frente a cielo raso).

## 3. Los 25 recursos con ficha directa del banco

| Recurso | Matriz | Adoptado | Usos | Ficha |
|---|---|---|---|---|
| MQ-BOMBA-CONC | 78.00 | 56.41 | 9 | M16A050 |
| MQ-DOBLAD-TUBO | 3.81 | 2.40 | 4 | M10A030 |
| MQ-MONTAC | 13.93 | 5.40 | 46 | M02MG030 |
| MQ-ROZAD | 6.16 | 1.93 | 30 | M11Z010 |
| MT-ANCLA-MURO | 0.74 | 0.77 | 10 | P04TW220 |
| MT-BARRA-TIERRA | 20.51 | 15.03 | 5 | P15EA010 |
| MT-BLOQUE-ALIV | 1.08 | 0.84 | 7 | P01BE010 |
| MT-BLQ-EST-15 | 1.00 | 0.60 | 5 | P01BA020 |
| MT-BLQ-EST-20 | 1.25 | 0.75 | 3 | P01BG080 |
| MT-DISOL-ADH | 5.92 | 3.46 | 4 | P01UL903 |
| MT-DOM-SENSOR-GAS | 34.18 | 106.28 | 0 | P22IO430 |
| MT-DPS-DATOS | 34.18 | 96.14 | 0 | P23PF340 |
| MT-ESTUCO-VEN | 6.84 | 9.03 | 4 | P24VE030 |
| MT-LLAVE-PROV | 6.84 | 6.69 | 5 | P41V350 |
| MT-MADERA-ENTIB | 3.87 | 6.41 | 5 | P01EB170 |
| MT-MADERA-PERGOLA | 7.75 | 1.95 | 6 | P01EW080 |
| MT-MAT-PRESTAMO | 18.23 | 9.00 | 2 | P01AD051 |
| MT-MICROCEM | 6.27 | 3.85 | 4 | P08CM030 |
| MT-PIEDRA-PIC | 30.00 | 11.99 | 10 | P01AG150 |
| MT-PIN-CAL | 2.05 | 0.50 | 1 | P24CC010 |
| MT-PLACA-FACHADA | 47.85 | 68.01 | 5 | P04FT040 |
| MT-PLANCHA-ACERO | 2.51 | 1.05 | 3 | P13TC010 |
| MT-PLO-ACC20 | 0.91 | 1.76 | 17 | P20TP050 |
| MT-PLO-ACC4 | 3.30 | 2.98 | 31 | P02TC030 |
| MT-RESINA-INYEC | 20.51 | 17.12 | 7 | P01UA010 |

Las cuatro máquinas tienen ficha horaria propia en el banco y sustituyen a precios
provisionales que estaban entre un 30 % y un 70 % por encima. `MT-DOM-SENSOR-GAS` y
`MT-DPS-DATOS` se mueven al alza porque su precio provisional (34,18) era el de relleno:
no los usa ninguna partida.

## 4. Maquinaria: 20 códigos, compra y amortización (no alquiler)

Se aplica el modelo del 7 de noviembre —`coste = compra/vida × (1+mantenimiento) +
kilovatios × 0,20 €/kWh × carga + consumibles`— con precios de compra investigados
(IVA incluido, pasado a neto dividiendo por 1,21). La vida útil y el mantenimiento son
hipótesis declaradas en cada criterio.

| Código | Matriz | Adoptado | Usos | Base del cálculo |
|---|---|---|---|---|
| MQ-ALISADORA | 7.62 | **1.92** | 9 | helicóptero 900 mm 1.400 € / 1.200 h, mant. 20 %, 5,5 kW |
| MQ-COMPACT-SALTO | 6.60 | **2.53** | 10 | canguro 1.300 € / 1.000 h, mant. 20 %, gasolina 0,8 l/h |
| MQ-ESMERIL | 3.37 | **0.40** | 40 | esmeriladora de banco 200 mm 550 W 134,90 € / 800 h |
| MQ-ESTAMP | 7.04 | **0.48** | 2 | juego de moldes 400 € / 800 h, mant. 15 % |
| MQ-HIDROLAV | 6.16 | **0.54** | 28 | hidrolimpiadora 130 bar 150 € / 600 h, 1,8 kW |
| MQ-LIJAD-PISO | 9.53 | **2.65** | 3 | lijadora de banda 1.800 € / 1.000 h, lijas 0,60 €/h |
| MQ-MART-NEUM | 11.00 | **1.83** | 45 | martillo 10,5 kg 781,66 € + compresor 700 €, cinceles 0,60 €/h |
| MQ-PLANCHA-COMP | 5.57 | **2.95** | 20 | plancha 1.100 € / 1.200 h, gasolina 1,2 l/h |
| MQ-RECUP-GAS | 9.53 | **0.77** | 7 | recuperador 900 € / 1.200 h, 0,5 kW |
| MQ-TELUROMETRO | 17.59 | **0.24** | 2 | telurómetro 400 € / 1.500 h, mant. 10 % |
| MQ-TERMOF | 2.64 | **0.29** | 23 | termofusora 120 € / 800 h, 0,8 kW |
| MQ-VENT-SUC | 4.10 | **0.30** | 3 | juego de ventosas 500 € / 1.500 h |
| MQ-ANDAMIO | 2.80 | **4.04** | 190 | alquiler 0,15 €/m²·día × 30 + montaje 6,00 €/m², entre 2,6 h/m² |
| MQ-BANO-PORT | 110.00 | **110.00** | 3 | alquiler mensual de mercado 90–130 €/mes (punto medio) |
| MQ-CIZALLA | 3.08 | **4.73** | 45 | cizalla 2,33 €/h (M10A010) + dobladora 2,40 €/h (M10A030) |
| MQ-PERF-PILOTE | 80.63 | **186.32** | 3 | M16A270 rotopercusión 6" con operador (analogía) |

El resto de la maquinaria del lote ya tiene ficha directa (§3). **El andamio es el
cambio de mayor alcance**: 190 partidas, de 2,80 a 4,04 €/h, porque el precio anterior
no cubría el montaje. Los 12 modelos propios bajan de media un 78 % respecto al precio
provisional, que estaba copiado de tarifas de alquiler con operador.

## 5. Consumibles, herrajes y equipos de protección: 12 composiciones

| Recurso | Matriz | Adoptado | Usos | Composición |
|---|---|---|---|---|
| MT-CONS-DEM | 1.25 | **2.70** | 398 | punta SDS-Max 25 €/5 usos + disco 230 mm 25 €/10 usos + hoja 6 €/10 usos |
| MT-OXI-CONS | 4.44 | **7.57** | 54 | 20 electrodos de P01US010 + disco de corte + boquilla |
| MT-HERRAJE-CLOSET | 5.13 | **8.90** | 47 | 2 bisagras + tirador + 4 soportes + tornillería |
| MT-HERRAJE-PUERTA | 14.81 | **11.70** | 44 | 3 bisagras + tope + herrajes de colgar + tornillería |
| MT-CONS-LIMP | 0.40 | **0.24** | 35 | detergente P34J020 al 5 % + paños y bolsas |
| MT-MARCO-PUERTA | 7.97 | **7.02** | 30 | 3,6 m de listón P01EW080 por metro de marco |
| MT-VIGA-APEO | 3.30 | **5.85** | 23 | 3 listones P01EW080 por metro de viga |
| MT-PLO-DESAG | 6.15 | **7.37** | 18 | sifón P17SC010 + brida y adaptadores + pegamento |
| MT-CONS-PULIDO | 2.73 | **1.50** | 14 | disco diamantado 25 €/25 m² + abrasivo + cristalizador |
| MT-PIN-LIJA | 0.97 | **1.28** | 86 | banda P11WP060 2,33 €/3 usos + cinta + plástico |
| MT-EPP | 47.85 | **29.40** | 7 | casco 2,41 + guantes 2,16 + botas 14,00 + gafas 2,41 + chaleco 8,42 |

`MT-CONS-DEM` es el recurso más usado de todo el catálogo (398 partidas): su precio pasa
de 1,25 a 2,70 €/ud porque el anterior no cubría ni la punta ni el disco. `MT-EPP` baja
porque las cinco fichas del banco suman 29,40 €, muy por debajo de los 47,85 estimados.

## 6. Los 28 de familia análoga y por qué 16 candidatos se descartaron

Las 28 analogías que se mantienen comparten **unidad y función** con la ficha: bovedilla
de poliestireno para aligerar, cantonera con malla para esquinas de friso, tubo de chapa
prelacada para panel ligero, vidrio impreso de 6 mm para vidrio de 6 mm. Las que se
movieron mucho: `MT-SUBESTRUCTURA` (20,51 → 68,00 €/m², ficha propia del banco para
fachada ventilada), `MT-MALLA-ESQ` (0,80 → 4,70 €/m), `MT-CERRADURA` (36,46 → 26,02) y
`MT-VIDRIO-6` (38,00 → 26,36).

Se **descartaron** por diferencia de alcance, quedándose el precio de la matriz con
horquilla declarada:

| Recurso | Candidato descartado | Motivo |
|---|---|---|
| MT-GRAMA | P30PY010 césped artificial 40,04 | El recurso es grama **natural** en panes |
| MT-RIEL-CORRED | P11WH220 herrajes (ud) 41,40 | Ficha por unidad para recurso por metro |
| MT-LAMP-OBRA | P16AA010 proyector 500 W 53,00 | Precio de compra para recurso **amortizado por uso** |
| MT-TIMBRE | P15HC270 pulsador 6,42 | La ficha es solo el pulsador, no timbre + transformador |
| MT-PERFIL-ALUM | P34XA090 aluminio 6,58 €/kg | Aluminio en bruto, sin aleación, anodizado ni accesorios |
| MT-PERSIANA-ALU | P12RC060 157,66 €/m² | Ficha muy por encima del conjunto con cajón y accionamiento |
| MT-BOMBA-AGUA | P26ED010 480,40 | Sumergible, no centrífuga de superficie |
| MT-HIDRONEUMATICO | P17TO040 358,14 | Depósito de ósmosis, sin bomba ni control |
| MT-VIDRIO-DECOR | P14CL010 18,36 | Vidrio impreso, no lacado ni grabado |
| MT-VIDRIO-TEMP | P14EL356 80,82 | Laminado 10+10, no templado de 10 mm |
| MT-TEJA-ASF | P05FE020 12,60 | Placa de fibrocemento, no shingle asfáltico |
| MT-CIELO-METAL / MT-CIELO-PVC | P06SL066 8,21 | Lámina impermeabilizante de PVC, no plafón |
| MT-PARARRAYOS-PUNTA | P15AC100 133,41 | Autoválvula, no punta Franklin |
| MT-SELLA-PASE | P06SI100 4,05 | Solo el sellante, sin collarín |
| MT-FIBRA-NAT | P07AR020 22,60 | Revestimiento acústico microporoso, no fibra tejida |

**Comprobación a posteriori de un descarte**: al reejecutar la verificación cruzada,
`MT-PERSIANA-ALU` —cuyo candidato del banco (157,66 €/m²) se rechazó— aparece como
`confirmado_independiente` contra el banco de Andalucía (`KS04500`, 54,30 €/m², −13,3 %
frente a los 62,66 €/m² conservados). Es la mejor prueba de que descartar la ficha de
Extremadura era lo correcto, y la cola de verificación baja de 351 a 350 recursos.

## 7. Los 54 de contraste de mercado: el grupo débil, con nombre y apellidos

Aquí no hay ficha de banco. Se conserva el precio de la matriz porque **cae dentro de una
horquilla de mercado declarada en el criterio**, que es una prueba de cordura, no una
cotización. 39 de los 54 los usa alguna partida; 15 no los usa nadie.

| Recurso | Precio ud | Usos | Horquilla declarada |
|---|---|---|---|
| MT-PERFIL-ALUM | 10.82 | 74 | 8-14 EUR/kg |
| MT-SENAL-OBRA | 6.27 | 73 | 3-10 EUR/ud |
| MT-REGUL-GAS | 27.34 | 37 | 15-40 EUR/ud |
| MT-SOPORTE-AC | 18.23 | 36 | 15-60 EUR/ud |
| MT-VIDRIO-TEMP | 77.47 | 35 | 60-110 EUR/m2 |
| MT-RIEL-CORRED | 15.95 | 17 | 12-30 EUR/m |
| MT-SELLA-PASE | 5.24 | 17 | 4-8 EUR/ud |
| MT-SAN-FIJA | 5.47 | 13 | 4-8 EUR/ud |
| MT-AISL-REFLECT | 3.65 | 9 | 2-5 EUR/m2 |
| MT-CONTENEDOR | 74.05 | 5 | 60-90 EUR/mes |
| MT-PASIVANTE | 11.16 | 5 | 8-15 EUR/l |
| MT-QUIMICO-LIMP-AC | 9.68 | 5 | 6-15 EUR/ud |
| MT-CANON | 7.00 | 4 | 5-12 EUR/m3 |
| MT-CIELO-METAL | 15.95 | 4 | 12-30 EUR/m2 |
| MT-CIELO-PVC | 18.23 | 4 | 10-22 EUR/m2 |
| MT-ESTRUCT-MESON | 13.67 | 4 | 10-18 EUR/m |
| MT-GRAMA | 3.65 | 4 | 2-6 EUR/m2 |
| MT-LAMP-OBRA | 10.82 | 4 | 8-15 EUR/ud |
| MT-PERSIANA-ALU | 62.66 | 4 | 40-90 EUR/m2 |
| MT-TOLDO | 54.68 | 4 | 45-90 EUR/m2 |
| MT-CASETA-BIEN | 136.71 | 3 | 100-200 EUR/mes |
| MT-CINTA-LED | 7.06 | 3 | 6-12 EUR/m |
| MT-LINEA-VIDA | 7.06 | 3 | 5-12 EUR/m |
| MT-TABLERO-DIST | 54.68 | 3 | 40-90 EUR/ud |
| MT-BLQ-VIDRIO | 7.86 | 2 | 5-9 EUR/ud |
| MT-GAS-REFRIG | 20.51 | 2 | 15-30 EUR/kg |
| MT-PERFIL-CORTINERO | 8.43 | 2 | 5-12 EUR/m |
| MT-TABLERO-PROV | 51.27 | 2 | 40-80 EUR/ud |
| MT-TEJA-ASF | 11.96 | 2 | 8-20 EUR/m2 |
| MT-TIMBRE | 15.95 | 2 | 12-25 EUR/ud |
| MT-VAPOR | 2.73 | 2 | 2-5 EUR/l |
| MT-ZIPPER | 4.33 | 2 | 3-6 EUR/ud |
| MT-FIBRA-NAT | 25.06 | 1 | 15-40 EUR/m2 |
| MT-GABINETE-MANG | 227.85 | 1 | 150-300 EUR/ud |
| MT-PIEDRA-FACHADA | 43.29 | 1 | 35-70 EUR/m2 |
| MT-PLATINA-DIV | 2.39 | 1 | 1,5-4 EUR/m |
| MT-SOPORTE-ANTIVIB | 5.70 | 1 | 3-8 EUR/ud |
| MT-TRAMPA-GRASA | 88.86 | 1 | 60-150 EUR/ud |
| MT-VIDRIO-DECOR | 51.27 | 1 | 35-70 EUR/m2 |
| MT-AUTOM-PORTON | 205.06 | 0 | 150-300 EUR/ud |
| MT-BOMBA-AGUA | 182.28 | 0 | 150-400 EUR/ud |
| MT-CAMARA-CCTV | 96.84 | 0 | 60-140 EUR/ud |
| MT-CONT-DESCARGAS | 51.27 | 0 | 40-90 EUR/ud |
| MT-DOM-PANEL | 102.53 | 0 | 70-150 EUR/ud |
| MT-DOM-REPETIDOR | 51.27 | 0 | 30-70 EUR/ud |
| MT-DOM-SENSOR-TEMP | 25.06 | 0 | 15-35 EUR/ud |
| MT-DOM-TECLADO | 39.87 | 0 | 25-60 EUR/ud |
| MT-DPS-3 | 28.48 | 0 | 18-40 EUR/ud |
| MT-HIDRONEUMATICO | 273.42 | 0 | 200-500 EUR/ud |
| MT-INVERSOR | 318.99 | 0 | 200-450 EUR/ud |
| MT-PANEL-SOLAR | 205.06 | 0 | 150-300 EUR/ud |
| MT-PARARRAYOS-PDA | 432.91 | 0 | 300-600 EUR/ud |
| MT-PARARRAYOS-PUNTA | 74.05 | 0 | 60-150 EUR/ud |
| MT-PLANTA-ELEC | 1367.09 | 0 | 6000-12000 EUR/ud (**por debajo: revisar antes de usar**) |

**Única excepción declarada**: `MT-PLANTA-ELEC` vale 1.367,09 €/ud en la matriz y un
grupo electrógeno de 20 kVA cuesta entre 6.000 y 12.000 €. Se deja el precio porque
**ninguna partida lo usa** y no se sustituye por una cifra sin fuente; queda marcado como
pendiente de revisión obligatoria en su criterio.

Los 54 son el grupo que hay que atacar en la siguiente vuelta con cotización de tienda
con URL y fecha. Ya hay precedente en el repositorio: las fichas de maquinaria se
cerraron así.

## 8. Efecto sobre el catálogo: 1.076 partidas

`espana_impacto_lote_2026-11-07.csv` propaga el cambio de cada recurso a las partidas que
lo consumen con el rendimiento del descompuesto:

- 1.076 partidas afectadas (549 suben, 330 bajan, el resto sin cambio neto).
- Variación por partida: **mínima −77,8 %, mediana +0,1 %, máxima +36,9 %**.
- Efecto medio por partida tipo: +125,20 €/ud.

Las partidas que más bajan son las de piedra picada y plancha compactadora, donde la
ficha del banco sustituye a estimaciones altas: `03.04.01.140` −77,8 %,
`03.06.01.100` y `03.06.01.140` −65,5 %, `03.04.01.040` −56,7 % y `09.13.03.050`
(telurómetro) −38,2 %. Las que más suben son de subestructura de fachada ventilada
(`06.07.01.050` +36,9 %, `06.07.01.020` +33,5 %, `06.07.01.010` y `06.07.01.040`
+31,3 %) y de malla de esquina (`12.01.01.190` +24,8 %).

## 9. Reservas

1. **Cerrar no es confirmar.** Los 133 siguen `en_revision`; ninguno pasa a
   `confirmado_referencia`, que exige una segunda fuente independiente.
2. **54 recursos no tienen ficha de banco.** Su precio es una banda de cordura. En 39
   casos hay partidas detrás, así que conviene priorizarlos en la próxima cotización.
3. **28 analogías dan nivel de precio, no cotización del artículo.** El criterio dice
   siempre qué ficha se usó y en qué se diferencia.
4. **La maquinaria depende de hipótesis declaradas**: vida útil, mantenimiento y precio
   de compra. Cambiar una hipótesis cambia el precio, y así está escrito.
5. **El SQL ya está cargado** (8 de noviembre de 2026): 390 referencias nacionales ES,
   selladas a 2026-11-07, con los dos recursos que faltaban creados para no dejar fuera
   `MT-BLQ-17` ni `MT-BLQ-25`. Ver
   [carga en producción](ESPANA_CARGA_PRODUCCION_2026-11-08.md). Cargar no es verificar:
   la carga no cambia los estados de auditoría ni convierte las estimaciones en cotizaciones.

## 10. Reproducibilidad

```bash
python3 tools/cerrar_huecos_espana.py --aplicar     # reescribe la adjudicación (idempotente)
python3 tools/cerrar_auditoria_espana.py --aplicar  # lleva la decisión al registro
python3 tools/verificar_precios_espana.py           # cola de verificación
python3 tools/generar_matriz_precios_espana.py      # matriz ES
python3 tools/inventario_precios_espana.py          # inventario integral
python3 tools/generar_sql_precios_espana.py         # SQL de carga
python3 tools/generar_precios_publicos.py           # ES.json
python3 tools/impacto_recursos_espana.py --antes <matriz_anterior.csv>
```

`cerrar_huecos_espana.py` **falla** si falta una decisión, si sobra una para un recurso
que ya tenía precio, si el método no está en la jerarquía o si el criterio está vacío.
`tests/test_cierre_total_espana.py` comprueba además que las fichas citadas existen
literalmente en el `.bc3`, que el precio de `mercado_rango` cae dentro de su horquilla y
que la maquinaria se valora por compra y amortización.
