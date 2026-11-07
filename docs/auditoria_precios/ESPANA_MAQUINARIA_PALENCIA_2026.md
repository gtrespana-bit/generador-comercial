# España: revisión por lote de maquinaria con Palencia 2026

**Consulta:** 7 de noviembre de 2026. **Estado:** contraste preliminar, sin cambio de precios. La fuente es el [cuadro oficial de precios unitarios de la Diputación de Palencia para infraestructuras 2026](https://www.diputaciondepalencia.es/system/files/2026-01/BASE%20PRECIOS%202026.%20PRECIOS%20UNITARIOS%20DE%20MANO%20OBRA,%20MAQUINARIA%20Y%20MATERIALES.pdf), páginas 2 y 3. Es una base **provincial de infraestructuras**, no una muestra nacional ni necesariamente una tarifa de alquiler vigente. Las descripciones del cuadro no detallan en estos conceptos todas las condiciones: IVA, operador, energía, transporte y consumibles deben aclararse, no suponerse. Su edición es 2026; eso no prueba la vigencia de cada precio el día de consulta.

Se han examinado once recursos, elegidos por posible correspondencia y propagación en los descompuestos. La diferencia es `(Palencia / matriz - 1) × 100`, con precios de la matriz sin redondear. **No mide un error** cuando las prestaciones o condiciones difieren. «Usos» cuenta descompuestos que referencian el recurso, no obras ni ventas.

| Recurso CotizaT | Usos | Matriz €/h | Referencia Palencia €/h (código) | Diferencia orientativa | Por comprobar |
|---|---:|---:|---:|---:|---|
| MQ-TALADRO | 1.025 | 2,199013 | 3,11 (U02SW650) | +41,4 % | Es una categoría general de herramienta eléctrica, no necesariamente taladro percutor con brocas y consumo. |
| MQ-SIERRA | 199 | 4,251425 | 4,78 (U02SW600) | +12,4 % | Motosierra de gasolina; el recurso también admite sierra circular. Falta alcance de consumibles y operador. |
| MQ-VIBRADOR | 135 | 4,984430 | 4,42 (U02SW550) | −11,3 % | Tipo de motor, consumo y operador. |
| MQ-MART-ELEC | 110 | 5,717434 | 4,53 (U02SW615) | −20,8 % | Martillo manual eléctrico, peso y potencia no indicados; consumibles y operador. |
| MQ-MART-NEUM | 45 | 11,00 | 6,19 (U02SW610) | −43,7 % | Si incluye el compresor y sus consumos; no asumirlo. |
| MQ-GRUA | 40 | 70,00 | 51,02 (U02J040) | −27,1 % | Camión grúa hasta 10 t; operador, capacidad concreta y alcance frente al recurso genérico. |
| MQ-VOLQ | 31 | 50,00 | 51,02 (U02J030) | +2,0 % | Camión dumper de 10 m³ frente a 6 m³; conductor, distancia y tasas. |
| MQ-PLANCHA-COMP | 20 | 5,570833 | 7,73 (U02F205) | +38,8 % | Bandeja vibradora de gasolina; potencia, consumo y operador. |
| MQ-COMPACT-SALTO | 10 | 6,597039 | 5,42 (U02F200) | −17,8 % | Pisón compactador de gasolina; dimensiones, potencia, consumo y operador. |
| MQ-BOMBA-CONC | 9 | 78,00 | 125,16 (U02L010) | +60,5 % | Bombeo sobre camión: caudal, alcance y operador frente al recurso genérico. |
| MQ-BOMBA-ACHI | 7 | 3,518421 | 10,83 (U02SM005) | +207,8 % | Grupo con motobomba de hasta 10 CV; potencia, mangueras y consumo pueden ser distintos. |

El cuadro también contiene una partida separada del 6 % de costes indirectos y medios auxiliares. No se ha añadido ni deducido ese porcentaje de estos precios simples, pues no se ha verificado cómo se aplica a cada caso ni si el presupuesto propio ya incorpora conceptos similares.

## Decisiones y límites

- Los once recursos quedan `en_revision`, sin precio revisado; diez eran `pendiente` y el taladro ya estaba en revisión. No se confirma ni cambia ningún precio de la matriz o del producto.
- El taladro aparece en 1.025 descompuestos y merece prioridad, pero la diferencia con una categoría amplia no autoriza sustituir su coste. El contraste anterior de tarifas de alquiler y sus limitaciones se conserva en [materiales](ESPANA_MATERIALES_2026.md).
- Las grandes diferencias de las bombas son señales para investigar, no evidencia de sobreprecio o infravaloración: pueden corresponder a tamaños y alcances diferentes.
- Antes de calcular medias deben existir dos referencias territoriales realmente comparables, con condiciones conocidas; el documento [cruce BC3](CRUCE_MASIVO_BC3.md) explica por qué la puntuación automática tampoco garantiza equivalencia. No se ha realizado el cruce masivo real ni se ha accedido o modificado producción en esta revisión.
- La máquina de mezclado ya se contrastó con Palencia en la [revisión inicial](ESPANA_2026-11-06.md) y permanece en revisión: hormigonera 250 l frente a mezcladora de un saco, sin equivalencia demostrada.
