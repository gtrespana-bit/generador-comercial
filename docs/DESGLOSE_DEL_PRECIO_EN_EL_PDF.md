# Desglose del precio en el PDF

Qué enseña, de dónde salen las cifras y qué se hizo para que la descarga deje
de tardar. Escrito para poder explicárselo a un cliente sin tecnicismos.

## Qué ve el cliente

En el bloque de totales del presupuesto, justo debajo del descuento, el
documento añade dos filas:

```
BASE IMPONIBLE                                    475,00 USD
DESCUENTO (5.0 %)                                 - 25,50 USD
  •  Productos y materiales seleccionados               114,00 USD  (24,0 %)
  •  Mano de obra, recursos y ejecución de los trabajos 361,00 USD  (76,0 %)
I.V.A. (16.0 %)                                    76,00 USD
PRESUPUESTO TOTAL                                 551,00 USD
```

Con una nota al pie del bloque: el desglose reparte la base imponible entre los
productos y materiales elegidos y el resto de la obra, y los porcentajes se
calculan sobre esa misma base.

* **Las dos cifras suman exactamente la base imponible.** El céntimo de
  redondeo lo absorbe la parte de obra, así que el cliente nunca tiene que
  sumar nada ni encuentra un importe suelto.
* **Es un reparto del precio de venta, no el coste de la empresa.** No aparece
  el margen ni el coste de compra: eso sigue viviendo solo en «Configuración →
  Mostrar costes internos», para el uso interno.
* Tiene sentido sobre todo en presupuestos con **productos elegidos** (solados,
  sanitarios, electrodomésticos…): enseña que buena parte del importe es
  material visible. En obra sin producto seleccionado la fila de productos sale
  a cero y todo el precio es mano de obra y ejecución.
* Si el presupuesto tiene productos alternativos, las dos filas se **recalculan
  dentro del propio PDF** al cambiar de producto, igual que el resto de
  importes.

## Cómo se activa

Casilla por presupuesto, en «Opciones de maquetación del PDF» del formulario
(alta y edición):

> ☑ Desglose del precio: productos elegidos y mano de obra

Nace **apagada**: ningún presupuesto ya emitido cambia de aspecto. Los
presupuestos duplicados heredan la elección del original. El PDF del ejemplo
público (`/conocer`) la lleva activada para enseñar la función.

## De dónde salen las cifras

`app/services/calculations.py` (el motor único de totales) calcula el importe de
venta de los productos asociados a las partidas y lo reparte con el descuento
comercial en la misma proporción que la obra:

```
descuento_productos = descuento × (productos / bruto)
descuento_obra      = descuento - descuento_productos   (absorbe el redondeo)
precio_productos    = productos  - descuento_productos
precio_obra         = base       - precio_productos
```

`Presupuesto.desglose_precio` expone las dos cifras y `_filas_desglose` del PDF
las imprime. El PDF interactivo replica la misma fórmula en JavaScript
(`DESG_TXT`), y una prueba (`tests/test_desglose_precio.py`) compara ambos
resultados ejecutando el propio JavaScript, para que el primer pintado y el
recálculo del visor digan exactamente lo mismo.

## Por qué antes tardaba tanto la descarga

La generación era correcta, pero pagaba trabajo repetido cuatro veces:

1. **Consultas perezosas por partida.** Generar el PDF de 50 partidas lanzaba
   **209 consultas** (una por partida y relación: productos, mediciones,
   descompuesto y sus filas). Con la base de datos en la nube, cada consulta
   añade su ida y vuelta: se medía ~4,5 s de espera con 20 ms de latencia por
   consulta. Ahora el documento carga su grafo completo en **9 consultas
   fijas** (`_opciones_pdf_presupuesto` en `app/routers/common.py`).
2. **El motor de totales se ejecutaba ocho veces** por documento (una por cada
   cifra del bloque). Ahora hay una sola pasada (`_LecturaTotales`) y el
   recálculo del descompuesto CYPE está memorizado por contenido de las filas.
3. **Las imágenes se descargaban en serie.** Cada foto de producto, plano o
   anexo esperaba su turno (hasta 20 s de tiempo de espera por archivo) antes de
   empezar a maquetar, y el contenedor en la nube arranca con la caché temporal
   vacía. Ahora se descargan **en paralelo** antes de maquetar
   (`precargar_referencias`) y cada archivo se lee una sola vez: medido con 12
   imágenes y 300 ms de latencia, 3,67 s → 0,70 s.
4. **La descarga no daba señales de vida.** El botón ahora muestra «Generando el
   PDF…» mientras el servidor trabaja, así que ya no parece que se haya quedado
   colgada.

Además, el registro de la aplicación anota cuánto tarda cada documento
(`Presupuesto X: PDF maquetado en … s`) para poder diagnosticar en producción.

## Archivos que cambian

| Archivo | Qué hace |
| --- | --- |
| `app/services/calculations.py` | Reparto del descuento y `base_productos` del reparto. |
| `app/models.py` | Columna `mostrar_desglose_precio` y `Presupuesto.desglose_precio`. |
| `app/services/pdf.py` | Filas del desglose en el bloque de totales, una sola pasada de totales y precarga de archivos. |
| `app/services/pdf_interactivo.py` | `DESG_TXT`/`TOTALES()` en el JavaScript del PDF y espejo en Python. |
| `app/routers/presupuestos.py` | Casilla en alta/edición/duplicado y carga del grafo completo para los PDF. |
| `app/routers/common.py` | `_opciones_pdf_presupuesto`, `_presupuesto_para_pdf`, `_factura_para_pdf`. |
| `app/storage.py` | `precargar_referencias` y lectura con caché temporal. |
| `app/templates/budgets/form.html`, `app/templates/base.html` | Casilla y estado «Generando el PDF…». |
| `migrations/versions/h1c4b7e9a3d2_mostrar_desglose_precio.py` | Columna nueva (head vigente). |
