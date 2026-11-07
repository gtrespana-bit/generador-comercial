# España — contraste por descomposiciones, 7 de noviembre de 2026

Se han contrastado individualmente y actualizado **10 precios provisionales** en la matriz local. Para acelerar se usa una sola descomposición por recurso, no dos ofertas. Son hipótesis operativas, **no medias nacionales** ni cotizaciones garantizadas; todos permanecen `en_revision`. El [CSV de fuentes](espana_fuentes_lote_banco_2026-11-07.csv) contiene enlaces, código, precio, unidad y reservas de cada ejemplo, consultados el 7/11/2026. CYPE es una referencia técnica de costes que varía con los parámetros de la obra; fecha efectiva de edición de cada precio no acreditada. Fichas y descripciones enlazadas no confirman expresamente IVA y porte de los productos: ambos se marcan **no confirmados**. No se afirma que la fecha de consulta sea fecha de tarifa. Comprobar las condiciones y derechos antes de cualquier utilización comercial o reproducción masiva.

| Recurso | Antes €/unidad | Provisional €/unidad | Referencia y reserva principal |
|---|---:|---:|---|
| Acero corrugado elaborado | 1,15/kg | 1,60/kg | B500S de taller; más resistente que 4200 kg/cm², no equivale a proyecto. |
| Cable 12 AWG | 0,65/m | 1,06/m | H07V-K 4 mm², mayor que 12 AWG (3,31 mm²); solo aproximación económica, no sustitución técnica de THW. |
| Cable 8 AWG | 1,65/m | 2,80/m | H07V-K 10 mm², mayor que 8 AWG (8,37 mm²); misma salvedad. |
| Mecanismo y placa | 5,00/ud | 10,25/ud | Interruptor unipolar básico: cuerpo 4,62 + tecla 2,63 + marco 3,00. No caja ni instalación; tomas pueden variar. |
| Magnetotérmico | 8,50/ud | 12,66/ud | Bipolar de 16 A, curva C y 6 kA; no cubre todos los modelos. |
| Rejilla de ventilación | 10,25/ud | 9,19/ud | Plástico, diámetro 100 mm, mosquitera y fijaciones; no todos los tamaños. |
| Placa de cemento | 10,48/m² | 19,97/m² | Aquapanel Outdoor 12,5 mm; sin fijaciones ni colocación. |
| Protección compuesta | 0,40/m² | 1,32/m² | 1,5 m² plástico × 0,18 + 1,2 m² cartón × 0,75 + 1 m cinta × 0,15; por m² protegido, sin mano de obra. Los coeficientes son los de ese caso: comprobar que la partida propia no duplique mermas. |
| Plástico de protección | 0,32/m² | 0,18/m² | Polietileno 0,2 mm; sin colocación ni cinta. |
| Cartón de protección | 0,51/m² | 0,75/m² | Cartón ondulado 350 g/m²; sin colocación ni cinta. |

Los extremos mínimo/máximo iguales de la matriz identifican que **solo hay un valor de referencia, no un rango de mercado observado**. No se ha importado un precio de partida terminada ni aplicado mano de obra, maquinaria, gastos generales o beneficio a los materiales. Los consumos y precios pueden cambiar por sección, sistema y volumen. El precio propio por unidad de obra resulta de sus rendimientos; revisar la posible duplicación en protección compuesta.

## Hallazgos no aplicados

- Hormigón HA-25/F/20/XC2 fabricado en central: [94,20 €/m³ de material](https://www.generadordeprecios.info/espacios_urbanos/Estructuras/Hormigones__aceros_y_encofrados/Hormigones/Hormigon_para_armar.html); no incluye el trabajo de vertido del descompuesto. Mantener 210 y 250 kg/cm² pendientes: resistencia y condiciones de entrega deben comprobarse antes de modificar «puesto en obra».
- [Cartucho de epoxi de anclaje 400 ml](https://generadordeprecios.info/rehabilitacion/Cimentaciones/Recalces/Conexion_entre_cimientos/CZO010_Anclaje_de_barra_corrugada_de_acero.html), 22,67 €/ud (56,68 €/l): no demuestra aptitud para inyección de fisuras; no sustituye el precio del recurso mixto.
- [Vidrio doble 4/6/4](https://generadordeprecios.info/obra_nueva/L_Carpinteria__cerrajeria__vidrios_y_/Vidrios/Doble_acristalamiento/Doble_acristalamiento_estandar.html), 21,34 €/m² solo material: prestaciones y tamaño de cámara no especificados en el recurso; no extrapolar al acristalamiento térmico/acústico en general.
- Bloque hueco 40×20×15, fuente antigua CYPE 0,64 €/ud y BCCA 2023 0,79 €/ud: la primera página no acredita edición vigente; no se sustituyó el precio por estas cifras.

## Base multirregional investigada

El repositorio [OpenConstructionEstimate-DDC-CWICR](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR), commit `e9e23fbab91014c8537b054d8f625c6f390fcf08`, identifica para España BCCA **2023 de Andalucía**; sus catálogos de otros mercados usan **transformaciones PPP**, no observaciones locales directas. Según [procedencia](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR/blob/e9e23fbab91014c8537b054d8f625c6f390fcf08/Europe-Spain-BCCA/PROVENANCE.md) y [licencia](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR/blob/e9e23fbab91014c8537b054d8f625c6f390fcf08/LICENSE-DATA.txt), su compilación es CC BY-NC 4.0, con licencia comercial separada. **No se ha importado ni aplicado ningún dato de DDC**, ni se presenta el catálogo Madrid como precios observados en Madrid. Conviene buscar las fuentes oficiales originales de cada país y revisar sus licencias; no asumir que una fecha de actualización del repositorio indica vigencia de precios.

## Estado y seguridad

Tras este lote: **388 recursos, 13 confirmados como referencia, 88 en revisión, 287 pendientes; 63 precios revisados** (54 materiales y 9 de mano de obra). De los 88 en revisión, 38 no tienen precio revisado. No se ha ejecutado SQL, desplegado ni alterado precios de clientes. Importabilidad no implica validación del mercado.

Comprobación local: 39 pruebas superadas; verificador de importación en seco: 388 filas aplicables y 0 errores; `git diff --check` limpio. Estas pruebas verifican coherencia y formato, no vigencia ni equivalencia técnica.
