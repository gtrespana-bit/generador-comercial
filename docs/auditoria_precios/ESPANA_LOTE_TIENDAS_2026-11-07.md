# España: lote de tiendas de construcción — 7 de noviembre de 2026

Ocho referencias **provisionales y en revisión**, media aritmética no ponderada de dos ofertas puntuales, calculada sin redondear y redondeada a céntimos. No son cotizaciones garantizadas ni medias nacionales. [CSV de observaciones](espana_fuentes_lote_tiendas_2026-11-07.csv): precios, formatos, URL y restricciones. Se supone IVA del 21 % donde no se indica el tipo; no incluye aplicación, mermas ni impuestos deducibles. Las ofertas pueden cambiar por tienda y fecha.

| Recurso (usos; pueden solaparse) | Dos ofertas sin IVA normalizadas | Anterior → provisional | Límites |
|---|---|---|---|
| Abasto flexible (22) | Illanes 2,11 €/ud y Brico Guadalupe 3,25 €/ud con IVA | 3,64557 → **2,21 €/ud** | Latiguillo M-H 3/8 de 40 cm con racores; Illanes exige 10 unidades. No representa otras longitudes, diámetros o accesorios adicionales; envío condicionado. |
| Membrana líquida de poliuretano (25) | Naminio 202,52 €/25 kg y Pinturas Proa 272,36 €/25 kg con IVA | 11,962025 → **7,85 €/kg** | Dos productos monocomponentes grises; idoneidad del sistema, soporte, uso y transporte deben comprobarse. Proa declara portes gratis desde 69 € en Península y podrían estar integrados. No incluye imprimación ni mano de obra. |
| Imprimación anticorrosiva (78) | Obramat: Rocha 27,40 € con IVA/4 l = 5,661 €/l; Pinturas Proa mediante marketplace Leroy Merlin: 47,60 €/4 l = 9,835 €/l, suponiendo 21 % IVA | 9,113924 → **7,75 €/l** | Imprimaciones sintéticas genéricas para metal, diferente color y formulación; compatibilidad de sistema y ambiente corrosivo pendientes. Proa declara entrega gratuita integrada y el IVA no está desglosado; condiciones de IVA/transporte quedan no confirmadas en matriz. |
| Banda elástica de impermeabilización (46) | Amado Salvador: Mapeband 36,60 € IVA incluido/10 m = 3,025 €/m; Lechada.es: Mapeband Easy 36,15 € IVA incluido/10 m = 2,988 €/m | 3,189873 → **3,01 €/m** | Caucho 130 mm para juntas y encuentros, variantes distintas; verificar compatibilidad con el sistema y condiciones de instalación. No incluye membrana ni accesorios. |
| Curador de hormigón (40) | Restatec: Antisol 3E 60 € sin IVA/25 kg ≈ 2,340 €/l; Mobbyplad: 67 € impuestos incluidos/25 kg ≈ 2,160 €/l | 3,873418 → **2,25 €/l** | Ambas ofertas son del mismo producto; 25 kg convertido a ≈25,641 l empleando densidad nominal 0,975 kg/l, no un volumen medido. [Ficha fabricante](https://esp.sika.com/es/construccion/construir/Aditivos-hormigon-mortero/sika-antisol-3-e.html): tolerancia ±0,020 kg/l. La densidad real cambia el resultado. Retirar membrana antes de recubrimiento, según ficha. |
| Yeso de reparación (57) | BigMat 2,95 €/17 kg y ParaTuReforma 3,45 €/17 kg, ambos con IVA | 0,56962 → **0,16 €/kg** | Yeso rápido para rozas, no todos los morteros de reparación. La oferta Jade tiene descuento temporal. |
| Esmalte sintético (14) | Obramat 27,95 €/4 l y Casado Rioja 67,28 €/4 l, ambos con IVA | 10,00 → **9,84 €/l** | Blanco brillante de dos calidades; verificar preparación y soporte. Amplia dispersión. |
| XPS 40 mm (33) | Leroy Merlin: Thermogreen 38,85 € con IVA/7,5 m² = 4,281 €/m²; Para tu Reforma: Soprema 47,24 € con IVA/7,5 m² = 5,206 €/m² | 8,544304 → **4,74 €/m²** | Dos paquetes de 10 placas; oferta Soprema −5 %. Solo espesor 40 mm; no representa otras resistencias o espesores. Verificar prestaciones y disponibilidad local. |

Las ofertas Proa con entrega gratuita pueden integrar parte del transporte; Brico Guadalupe condiciona el envío gratuito al importe. En el resto los costes de transporte no se agregan; la recogida y preparación en Obramat pueden tener cargos. El rango de cada matriz refleja solo dos observaciones. La suma de usos no es el número de partidas distintas. Los cálculos del curador usan `25 / 0,975` litros aproximados y los de IVA usan la oferta tal como fue consultada.

## Hallazgos no aplicados

- **Bloque hueco 15×20×40:** Obramat sí declara geometría hueca, y Leroy ofrece el SUBEROLITA en su categoría de bloques huecos, pero la ficha individual no precisa la estructura interna. La búsqueda indexada dio 0,65 € y la ficha directa 0,86 €: se conserva sin actualizar hasta confirmar geometría y condiciones. El bloque estructural no es equivalente automático.
- **Cable de alarma:** se encontraron mangueras apantalladas 4×0,22 + 2×0,70/0,75, pero no consta el trenzado en pares que puede requerir la descripción multipar; no se cambia el precio.
- **Yeso para rozas:** una tienda BigMat Córdoba mostraba no disponible; la ficha de BigMat nacional consultada posteriormente indica stock. Verificar disponibilidad por tienda.
- **XPS de Obramat:** la ficha del producto 25047119 menciona EPS en una característica aunque en título y texto indica XPS y muestra una conversión sin IVA por m² incorrecta. Se omitió esa oferta, no se reutilizó el precio indexado.

La matriz y SQL se regeneran localmente; el SQL no se ejecuta ni se despliega.

## Investigación adicional sin aplicación

- La silicona neutra Quilosa de Leroy (4,99 €/300 ml) es adecuada para carpintería y acristalamiento, pero `MT-SILICONA-EST` incluye **silicona estructural o neutra**: no extrapolar su precio a la estructural. El uso requiere separar la especificación. [Ficha](https://www.leroymerlin.es/productos/silicona-neutra-acristalamiento-n16-quilosa-300ml-blanco-83367792.html).
- El C1 gris de [Obramat](https://www.obramat.es/productos/cemento-cola-aplicacer-c1-25kg-gris-25119648.html) cuesta 3,30 €/25 kg con IVA; la segunda oferta consultada tiene ficha contradictoria sobre color, por lo que no se ha actualizado el C1 gris.
- La protección de obra conjunta necesita plástico, cartón y cinta; el cubretodo por sí solo no cubre el conjunto. La pasta de juntas incluye cinta y el consumo relativo depende de geometría y nivel de acabado; no se ha sumado una cinta con una proporción inventada. El cable desnudo para pararrayos incluye grapas: el precio del cable solo no cubre ese recurso.
- Un BC3 ADIF 2024 en [GitHub](https://github.com/cga-telice/bc3cat-dataset) es histórico y ferroviario; no se ha descargado, cruzado ni usado como precio actual. Tampoco se usaron alquileres diarios como precio horario sin acordar horas de utilización, transporte, seguros y amortización.
