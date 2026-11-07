# Agregados: qué se recompone y qué no (y por qué)

Fecha: 2026-11-07 · 19 recursos agregados que consumen 968 usos · Decisión delegada por
el titular: hacer «lo que funcione mejor y quede más profesional» · Datos:
`espana_agregados_peso_2026-11-07.csv` · Reproducible con
`tools/pesar_agregados_espana.py`.

## 1. El problema

Un recurso como `MT-CONS-DEM` («puntas, cinceles, discos y hojas de espátula») no es un
material: es un paquete de consumibles con proporciones internas desconocidas. El banco no
publica ese paquete, y su precio actual en la matriz es una cifra heredada sin
descomposición. Tiene 398 usos: es el segundo recurso más usado del catálogo.

Hay dos maneras de cerrarlo y solo una es defendible:

* **Repreciar el paquete entero** con una cifra nueva → inventar el contenido. Descartado.
* **Recomponerlo** a partir de componentes simples con precio propio, sustituyendo el
  recurso en los descompuestos → correcto, pero es cirugía de catálogo (cambia la receta de
  cientos de partidas) y exige cotizar cada componente.

## 2. El dato que decide: cuánto pesa cada agregado en su partida

Antes de tocar nada se mide el peso real de cada agregado en el coste directo de las
partidas que lo usan (rendimiento × precio / coste directo). Si el agregado pesa un 1 %, la
imprecisión de su precio es irrelevante; si pesa un 27 %, es el precio de la partida.

| Agregado | Usos | €/ud | Peso mediano | Partidas >10 % | >25 % |
|---|---:|---:|---:|---:|---:|
| `MT-HERRAJE-CLOSET` | 47 | 5,13 | **27,4 %** | 40 | 25 |
| `MQ-PERF-PILOTE` | 3 | 80,63 | 54,5 % | 1 | 1 |
| `MT-ACC-BOMBA` | 2 | 31,90 | 20,0 % | 2 | 0 |
| `MT-PLO-ACC4` | 31 | 3,30 | 15,5 % | 12 | 0 |
| `MT-PLO-DESAG` | 18 | 6,15 | 11,0 % | 5 | 0 |
| `MT-SAN-FIJA` | 13 | 5,47 | 10,6 % | 2 | 0 |
| `MT-HERRAJE-PUERTA` | 44 | 14,81 | 9,4 % | 20 | 2 |
| `MQ-RECUP-GAS` | 7 | 9,53 | 9,6 % | 0 | 0 |
| `MT-SELLA-PASE` | 17 | 5,24 | 6,5 % | 3 | 2 |
| `MT-CONS-PULIDO` | 14 | 2,73 | 5,0 % | 2 | 0 |
| `MT-PLO-ACC20` | 17 | 0,91 | 3,8 % | 0 | 0 |
| `MT-OXI-CONS` | 54 | 4,44 | 1,9 % | 0 | 0 |
| **`MT-CONS-DEM`** | **398** | 1,25 | **1,3 %** | 0 | 0 |
| `MT-CONS-LIMP` | 35 | 0,40 | 0,8 % | 0 | 0 |
| `MT-EPP` | 7 | 47,85 | 0,0 % | 0 | 0 |

## 3. La decisión

1. **No se recompone por volumen de usos, se recompone por peso en el precio.** `MT-CONS-DEM`
   es el agregado con más usos (398) y el que menos importa (1,3 % del coste directo,
   ninguna partida por encima del 10 %). Recomponerlo costaría días de cotización y movería
   el catálogo una décima. Se queda como está, documentado.
2. **Se recomponen siete, por este orden**: siete es lo que sale de aplicar la regla del
   §5 a los 19 agregados. Los cuatro primeros acumulan el 92 % de las partidas afectadas:
   `MT-HERRAJE-CLOSET` (40 partidas por encima del 10 %, 25 por encima del 25 %),
   `MT-HERRAJE-PUERTA` (20), `MT-PLO-ACC4` (12), `MT-PLO-DESAG` (5). Los otros tres son
   pequeños y de baja frecuencia: `MT-SAN-FIJA` (13 usos, 2 partidas), `MQ-PERF-PILOTE`
   (3 usos, 1 partida) y `MT-ACC-BOMBA` (2 usos, ambas partidas). En ellos el precio del
   agregado *es* el precio de la partida. Requiere cotizar cada componente (bisagra de cazoleta, tirador, soporte de
   entrepaño, tornillería; juego de bisagras de puerta; codos y yes de PVC 110; sifón y
   brida) y sustituir el agregado en los descompuestos, no solo cambiarle el precio.
3. **No se aplica nada en esta ronda.** Cambiar la receta de 200 partidas sin cotización
   componente a componente sería repetir el error que la auditoría está corrigiendo.

## 4. Impacto máximo si se hiciera al revés

Si se repreciara el paquete en bloque (lo descartado): con un contenido plausible de
1 punta SDS + 1 disco de 230 mm + 1 hoja de espátula, `MT-CONS-DEM` pasaría de 1,25 a
≈20 €/ud y las 398 partidas subirían de media un 15 %. Sería un cambio enorme apoyado en
una suposición; de ahí que se descarte explícitamente.

## 5. Criterio permanente

> Un agregado se recompone cuando su peso mediano en el coste directo llega al 10 %, o
> cuando llega al 5 % y al menos un tercio de sus partidas supera el 10 %. Por debajo de
> eso, se documenta y se deja quieto.

Siete agregados pasan el corte; doce no. `MT-CONS-DEM`, el más usado de todos (398 usos),
se queda fuera por 1,3 % de peso mediano: usarlo mucho no es lo mismo que importar mucho.

El listado completo con todos los agregados y sus pesos está en
`espana_agregados_peso_2026-11-07.csv`; el criterio se recalcula con
`tools/pesar_agregados_espana.py`, así que la decisión se puede revisar cuando el catálogo
cambie.
