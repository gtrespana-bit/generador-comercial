# España — inventario integral de evidencias, 7 de noviembre de 2026

Este corte responde al inventario **completo de 388 recursos**, pero **no es una validación completa de sus precios**. El [CSV integral](espana_inventario_integral_2026-11-07.csv) une el estado actual de la auditoría, el precio efectivamente en la matriz local, los usos y la disponibilidad de candidatos de la copia CERP/BCCA. Las filas se ordenan por número de partidas que usan cada recurso. La cifra de usos entre recursos se solapa y **no** indica partidas distintas.

| Estado | Recursos | Materiales | Maquinaria | Mano de obra | Con precio revisado |
|---|---:|---:|---:|---:|---:|
| Confirmado como referencia | 13 | 9 | 0 | 4 | 13 |
| En revisión | 227 | 188 | 26 | 13 | 189 |
| Pendiente | 148 | 130 | 18 | 0 | 0 |
| **Total** | **388** | **327** | **44** | **17** | **202** |

Los 202 precios revisados son 193 materiales y 9 de mano de obra; son referencias operativas, no importes garantizados para cada obra. De los 227 en revisión, 38 conservan la referencia previa sin precio revisado. Los **148 pendientes siguen sin comprobación individual suficiente**, aunque dispongan de precio en la matriz y sean importables.

## Cruce completo y límites

- La copia CERP/BCCA se cruzó con todos los 388 recursos: **359 tienen al menos una coincidencia textual y 29 no**. Los 1.637 candidatos individuales están en [candidatos BCCA](espana_candidatos_bcca_2026-11-07.csv), junto con la descripción y alertas. El CSV integral muestra solo el primero para facilitar el filtro; **primero no significa mejor técnicamente ni equivalente**. La fecha y la fuente originales deben revisarse antes de decidir.
- La copia es una fuente derivada de Andalucía, con precios mayoritariamente de 2021–2023; no es una segunda observación actual ni una media nacional. Puede contener errores de código, unidades y descripción, así como falsos positivos. Véase [procedencia y reproducción](ESPANA_CRUCE_BCCA_2026-11-07.md). El estado contenido en el archivo histórico de candidatos quedó congelado en la fecha del cruce; el **estado vigente** es el del CSV integral y la auditoría.
- La [Junta de Extremadura](https://www.juntaex.es/w/base-precios-construccion-2026) publica una base regional 2026 en BC3 y cuadros PDF; no se obtuvo el fichero íntegro por el acceso disponible en esta sesión. No se presentan sus fragmentos como un banco completo. La referencia de Palencia 2026 es igualmente provincial. **No se aplicaron candidatos BCCA automáticamente** ni se extrapoló una base autonómica como media nacional.
- Los indicadores de la columna `accion` son reglas de triaje por estado y disponibilidad, no veredictos técnicos. La validación requiere contrastar naturaleza del recurso, descripción completa, unidad, prestaciones, momento, territorio, IVA y transporte. Algunos recursos incluyen accesorios, suministro con colocación, amortización o varios productos; una oferta individual no representa todo el conjunto.

## Pendientes de mayor incidencia

El CSV contiene todos y permite filtrar; entre los primeros por usos destacan: andamio con montaje/desmontaje (190), atornilladora con consumo (162), equipo de aplicación de pintura (151), hormigón 210 kg/cm² puesto en obra (106), aspirador (91), cortadora con agua (91) y consumibles de pintura (86). Las especificaciones y los componentes incluidos son determinantes; los usos no se suman como partidas únicas.

## Avance aplicado durante este corte

Se añadieron **8 referencias provisionales con 19 componentes**: [lote de componentes](ESPANA_LOTE_COMPONENTES_2026-11-07.md).

Se añadieron **28 referencias provisionales** mediante 29 componentes por familias, con exclusiones, enlaces y condiciones: [lote ampliado](ESPANA_LOTE_FAMILIAS_2026-11-07.md).

Se añadieron cinco precios provisionales con siete componentes: [lote de alta frecuencia](ESPANA_LOTE_ALTA_FRECUENCIA_2026-11-07.md). Las cifras siguientes son históricas.

Se añadieron **18 precios provisionales** con 20 componentes: [lote priorizado](ESPANA_LOTE_PRIORIDAD_2026-11-07.md). Las cifras de los avances posteriores son históricas.

Se añadieron **20 precios provisionales** de 21 observaciones de Obramat y Leroy Merlin, con reservas y exclusiones: [barrido de cadenas](ESPANA_LOTE_CADENAS_2026-11-07.md). No son un catálogo completo ni una media nacional.


Se añadieron siete referencias provisionales individuales de Extremadura y CYPE: [lote de materiales](ESPANA_LOTE_MATERIALES_2026-11-07.md). Fechas de vigencia de CYPE, condiciones y equivalencias pendientes.

Se añadieron ocho referencias provisionales de cuadros oficiales: [lote de cuadros](ESPANA_LOTE_CUADROS_2026-11-07.md).

Se han añadido 10 referencias provisionales por descomposiciones, una sola fuente por recurso y con reservas expresas: [lote banco](ESPANA_LOTE_BANCO_2026-11-07.md). Los párrafos siguientes son avances anteriores.

Se han añadido tres referencias adicionales para pasta con cinta, cable de alarma y tornillo de cubierta: [lote posterior](ESPANA_LOTE_POSTERIOR_2026-11-07.md). En el lote anterior se añadieron cuatro referencias provisionales con dos ofertas cada una: yeso de reparación **0,16 €/kg**, esmalte sintético **9,84 €/l**, abasto flexible **2,21 €/ud** y membrana líquida de poliuretano **7,85 €/kg**. Las dos últimas tienen transporte condicionado o no confirmado. En todos los casos el precio es la media de ofertas minoristas normalizadas sin IVA y sin añadir porte; algunas ofertas podrían integrarlo, no una media estadística nacional. Fuentes, cálculos, variación y reservas: [lote tiendas](ESPANA_LOTE_TIENDAS_2026-11-07.md). La matriz, SQL local e índice público local ES se regeneraron; no se ejecutó el SQL ni se desplegó.

## Reproducir

```bash
python tools/inventario_precios_espana.py
python -m pytest -q tests/test_inventario_precios_espana.py tests/test_lote_tiendas_espana.py
python tools/verificar_matriz_importable.py ES
```

El generador integral falla si falta, sobra, se duplica o cambia de unidad/categoría un recurso entre matriz, auditoría y cruce. No modifica ninguno de ellos ni aplica importes. La comprobación de importabilidad verifica formato, no actualidad, equivalencia ni exactitud de mercado.
