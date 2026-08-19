# Investigación de precios — Ronda 7: transporte, fletes y consumibles

**Fecha:** 2026-08-19  
**Mercados:** Colombia, Perú, México y Ecuador

> El transporte no se debe modelar como un precio fijo por país. Depende de distancia, peso, volumen, vehículo, ruta, peajes, carga, descarga, operador y combustible.

| Mercado | Referencias encontradas |
|---|---|
| Colombia | Flete base de camión sencillo: 3.500–4.500 COP/km en referencias de mercado; rutas y vehículos específicos deben seguir SICE-TAC. También se encontraron servicios de retroexcavadora y transporte desde 90.000–150.000 COP/h. |
| Perú | Flete urbano Lima: 120–1.200 PEN según vehículo; interprovincial Lima: 350–2.600 PEN; retroexcavadora 150–170 PEN/h y volquete 110–140 PEN/h en referencias consultadas. |
| México | Camioneta 3,5 t: 14–20 MXN/km; rabón 10 t: 20–28 MXN/km; torton 18 t: 28–36 MXN/km; tráiler 30 t: 36–48 MXN/km, sin casetas, maniobras ni seguro. |
| Ecuador | Tarifa pública consultada: camión pesado 1,24 USD/km recorrido cargado; tarifa municipal: volquete 20 USD/viaje hasta 3 km y retroexcavadora 30 USD/h. |

## Fuentes

- Colombia: referencias de fletes por km y corredor, contrastadas con SICE-TAC y fuentes de transporte.[1](https://logitools.co/blog/tarifas-fletes-colombia-2026) [2](https://zarpe.com.co/tarifas)
- Perú: rangos urbanos e interprovinciales y tabla de valores referenciales MTC.[3](https://transportesciriacoexpress.pe/cuanto-cuesta-transporte-de-carga-peru-tarifas-2026/) [4](https://tremach.com/blog/precio-de-alquiler-de-maquinaria-pesada/)
- México: tarifas por vehículo, km, casetas, maniobras y seguro.[5](https://www.cotizadoraonline.com/cotizacion-transporte-fletes)
- Ecuador: tarifas de transporte de carga y tarifas municipales de maquinaria.[6](https://portal.compraspublicas.gob.ec/sercop/wp-content/uploads/2017/02/ficha_camion2_ejes_med_7_10.pdf) [7](https://www.gob.ec/gadmc-limon-indanza/tramites/servicio-alquiler-maquinaria)

## Modelo recomendado

Un coste de transporte debe guardar:

- origen;
- destino;
- distancia;
- tipo de vehículo;
- capacidad;
- peso o volumen;
- tarifa por km, viaje, tonelada o m³;
- peajes;
- maniobras;
- seguro;
- carga y descarga;
- combustible;
- operador;
- fecha;
- fuente;
- moneda;
- mercado.

No se debe ocultar un flete dentro del precio del cemento, arena o bloque. El recurso debe conservar su precio puesto en proveedor y el transporte debe entrar como coste separado, salvo que la fuente indique expresamente que es precio puesto en obra.

## Estado

Esta ronda cierra la investigación inicial de familias principales. Antes de cargar datos nacionales en producción falta una fase técnica de consolidación:

1. normalizar códigos y unidades;
2. vincular recursos existentes;
3. eliminar duplicados;
4. asignar precio de referencia y rango;
5. marcar confianza;
6. cargar solo precios suficientemente contrastados;
7. dejar provisionales los que necesitan proveedor adicional;
8. generar la primera matriz nacional importable.
