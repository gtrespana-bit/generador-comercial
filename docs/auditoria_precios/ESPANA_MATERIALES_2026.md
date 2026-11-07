# España: contraste operativo de materiales — 6 de noviembre de 2026

Esta revisión incorpora diecinueve precios a la matriz, en euros por unidad del catálogo. Son **puntos medios de dos ofertas minoristas puntuales**, no una media estadística de España ni un precio garantizado para una obra o empresa. Se comparan mercancías de la misma clase y formato, sin afirmar equivalencia absoluta de prestaciones. Los precios y la disponibilidad pueden cambiar.

Las treinta y ocho observaciones, fuentes, condiciones y fecha local (America/Caracas) están en [`espana_materiales_ofertas_2026.csv`](espana_materiales_ofertas_2026.csv). Se supone un IVA general del 21 % íntegramente deducible y se **excluye el transporte**, palés y otros posibles costes de suministro. Una empresa que no deduzca todo el IVA debe ajustar el coste. Los anuncios con impuestos incluidos se dividen por 1,21 y por el número de unidades o kilogramos; después se promedian sin redondear y se redondea el resultado a céntimos. Los extremos de matriz también se redondean a céntimos. El generador reproduce el cálculo sin recalibrar la canasta histórica del resto de recursos.

| Código | Ofertas con IVA y formato | Antes | Referencia actual sin IVA ni porte | Cobertura |
|---|---|---:|---:|---|
| MT-SAC-ESC | Bricosimax 4,70 € y Almacenes Iberia en Leroy Merlin 5,40 €, ambos 10 sacos 50×80 cm | 0,740506 €/ud | **0,42 €/ud** | 235 partidas; en revisión por resistencia. |
| MT-CEMENTO | Consydecor 6,29 € y Amado Salvador 5,36 €, ambos sacos de 25 kg de CEM I gris 42,5 R | 0,14 €/kg | **0,19 €/kg** | 11 partidas; referencia de producto contrastada. |
| MT-ADH-C2TE | Monomat 9,70 € y El Camarada 7,80 €, adhesivos C2 TE para porcelánico, saco de 25 kg | 0,36 €/kg | **0,29 €/kg** | 47 partidas; referencia de producto contrastada. |
| MT-PYL-PLACA125 | BigMat 4,20 €/m² y Bauhaus Placo BA 13 10,47 €/placa de 3 m² | 4,00 €/m² | **3,18 €/m²** | Referencia de placa estándar contrastada. |
| MT-PYL-MONT | Bauhaus THU 3,39 € y Obramat Placo 3,62 € por 3 m, 70 mm | 2,392405 €/m | **0,97 €/m** | En revisión por espesor. |
| MT-PYL-CANAL | Obramat Placo 3,06 € y Leroy Merlin Placo 3,49 € por 3 m, 70 mm | 1,936709 €/m | **0,90 €/m** | En revisión: espesores y comercios del mismo grupo. |
| MT-JUN-CG2 | Maperi 7,41 € y El Camarada 9,99 €, ambos 5 kg de CG2 WA | 3,20 €/kg | **1,44 €/kg** | En revisión: color y confirmación del vendedor. |
| MT-SIL-SAN | Cofan 4,24 € y Proinco Pattex 6,43 €, cartuchos sanitarios blancos 300 ml | 13,670886 €/ud | **4,41 €/ud** | Referencia de cartucho contrastada, no universal. |
| MT-ELECTRODO | Serecon 12,80 €/5 kg y Soldufer ESAB 24,16 €/3 kg, ambos E7018 3,2 mm | 4,50 €/kg | **4,39 €/kg** | En revisión: homologación, marcas y conservación difieren. |
| MT-MORT-REP-EST | Restatec 29,04 € y Pochiche 34,45 €, Morcemseal Todo1 R4 25 kg | 2.734177 €/kg | **1,05 €/kg** | Referencia de mortero estructural contrastada, sujeta a proyecto. |
| MT-MALLA-OBRA | Jardin202 16,58 € y Bricosimax 19,25 €, rollos 1 × 50 m | 1.025316 €/m² | **0,30 €/m²** | En revisión: gramaje y resistencia no especificados en una oferta. |
| MT-SELLA-ELAST | Bañón y Sánchez 6,57 € y Caberstore 12,49 €, Soudaflex 45FC blanco bolsa 600 ml | 36.455696 €/l | **13,13 €/l** | Referencia de producto contrastada; comprobar movimiento admisible. |
| MT-MORT-IMPER | Obramat 49,00 € y SLucía 56,90 €, SikaTop 107 Plus ES lote 25 kg | 1.424051 €/kg | **1,75 €/kg** | En revisión: no puentear fisuras sujetas a movimiento. |
| MT-PYL-BANDA | Obramat 8,97 € y Ferrolan 13,48 €, banda 70 mm rollo 30 m | — | **0,31 €/m** | Referencia de banda 70 mm contrastada. |
| MT-PYL-PLACA | Brico Depot 10,98 €/3,12 m² y Aislamientos González 14,77 €/3 m², placa BA 15 mm | 4,90 €/m² | **3,49 €/m²** | En revisión: stock y disponibilidad. |
| MT-PYL-PASTA-AGARRE | El món del pladur 10,48 € y Aislamientos González 11,30 €, Pladur PA 20 kg | 0,455696 €/kg | **0,45 €/kg** | Placas sin aislante incorporado. |
| MT-ELE-TUB20 | Brico Eléctrico 21,20 € y Unión Ferretera 21,55 €, PVC 20 mm rollo 100 m | 0,45 €/m | **0,18 €/m** | En revisión: reacción al fuego. |
| MT-MALLA-FACH | Prodisem 60,35 € y Ferrolan 81,10 €, mallas SATE 160 g/m² 50 m² | 2,050633 €/m² | **1,17 €/m²** | En revisión: compatibilidad de sistema y suministro. |
| MT-AUT-NIV | Bauhaus 17,99 € y Para mi reforma 17,95 €, Niveland 10 saco 25 kg | 0,44 €/kg | **0,59 €/kg** | Espesores de 2 a 10 mm; confirmar disponibilidad. |

* Malla SATE: el producto Aisterm se anuncia para un sistema concreto y bajo pedido; verificar compatibilidad. El tubo no presupone reacción al fuego sin ficha expresa de ambas ofertas. Niveland 10 es para interiores de 2 a 10 mm y no representa espesores mayores; el envío se paga aparte.

* La banda corresponde a perfil de 70 mm, no a cualquier ancho. En la placa BA 15 la segunda tienda indica stock insuficiente; se adopta el punto medio como estimación, no como cotización firme.
* Los electrodos tienen la misma clase E7018 y diámetro, pero diferente marca y envasado, con dispersión importante; el precio no confirma la idoneidad del proceso de soldadura.
* El mortero R4 y el sellador requieren comprobar aplicación, soporte y especificación de proyecto; el 45FC es de alto módulo y no sirve indiscriminadamente para cualquier movimiento.
* La malla es de señalización, no incluye colocación, postes ni resistencia no indicada. El SikaTop 107 Plus admite cobertura pero la ficha comercial limita las fisuras puenteables a las no sujetas a movimiento; no se asume que satisfaga cualquier requisito de flexibilidad.

* Placa BA 13: la ficha técnica enlazada por Bauhaus especifica **12,5 mm**, aunque la página comercial redondea a 13 mm. BigMat ofrece recogida en tienda; Bauhaus condiciona disponibilidad a tienda. [Ficha BA](https://media.cdn.bauhaus/m/28832/BH_DOC_28832.pdf).
* Montantes: THU y Placo son para tabiques y montantes 70 mm, pero Bauhaus no indica inequívocamente el espesor de la chapa; su «34 mm» corresponde a una dimensión del perfil. Comprobar la ficha y el sistema antes de comprar. Obramat publica 0,55 mm.
* Canales: Obramat publica 0,55 mm y Leroy Merlin 0,6 mm; ambos son Placo y los comercios pertenecen al mismo grupo, por lo que no son una muestra independiente. Una obra puede exigir un espesor o sistema concreto.
* Juntas CG2 WA: el precio de Maperi requiere confirmación del vendedor y puede cambiar semanalmente; el color de ambas ofertas debe seleccionarse. Se mantiene en revisión y se ha adoptado un precio orientativo, no una cotización firme.
* Silicona: Cofan es ácida y promocional; el anuncio de Pattex es de últimas unidades y solo recogida. Es un precio por cartucho de **300 ml**, que puede no servir para soportes sensibles al curado ácido ni otras prestaciones especificadas.

* Los sacos son comparables por función y tamaño; ninguna ficha cuantifica la carga máxima o resistencia. No se garantiza que cumplan cualquier exigencia de «alta resistencia». El envío de la oferta de Leroy Merlin empieza en 4 € adicionales para el pedido. Mantener `en_revision` hasta verificar prestaciones y suministro.
* Una de las dos ofertas de cemento especifica además resistencia a sulfatos SR5; ambas se ajustan al tipo I de la descripción genérica pero no deben tratarse como intercambiables en proyectos con exigencias específicas. Consydecor pide consultar envíos fuera de Murcia o Alicante y puede exigir palé según cantidad. La antigua comparación con CEM II de Palencia **no** se utilizó para este cálculo.
* Los adhesivos cumplen la categoría C2 TE y se publicitan para porcelánico; no tienen necesariamente igual color, deformabilidad u otras prestaciones. Elegir el producto según soporte, formato y condiciones reales de aplicación.

## Otros recursos frecuentes, aún no confirmados

* `MQ-TALADRO` (1.025 partidas): se conserva 2,199013 €/h. [Máquinas-Máquinas](https://maquinas-maquinas.com/maquinaria/perforacion-demolicion-martillos/martillos/taladros/taladro-percutor-640-w/) muestra 30 €/24 h o 20 €/día con mínimo de dos días, sin IVA ni broca; [Altor](https://www.altor.ws/alquiler/productos/61/taladros/61001/taladro-electrico-normal) indica 11,10 €/día sin IVA, seguro de 0,89 €/día y canon de 1 €/contrato, con accesorios aparte. No se puede convertir esas tarifas a coste horario completo sin hipótesis de uso, duración, brocas, energía y cargos. La cifra histórica sigue sin verificar.
* `MT-CONS-DEM` (398 partidas): mezcla puntas, cinceles, discos y hojas por unidad sin identificar cuál ni consumo. No hay una compra equivalente única; requiere desglosar el recurso y revisar los rendimientos. Su precio histórico no se ha cambiado.
* `MT-ELE-CAJA` y `MT-TORN` también agrupan productos distintos y aparecen en partidas con usos heterogéneos; una única oferta barata no confirma todos esos usos.

## Alcance de publicación

La matriz y el índice público estático se regeneran localmente. El SQL generado es un archivo de carga, **no se ha ejecutado en ninguna base de datos**. La fecha máxima visible de revisión de una partida no implica que todos sus componentes estén revisados. Las referencias de mano de obra, incluidos cinco oficios aún en revisión, y sus límites figuran en [ESPANA_REFERENCIA_OPERATIVA_2026.md](ESPANA_REFERENCIA_OPERATIVA_2026.md). La copia `cargar_precios_espana_mano_obra_2026-11-06.sql` es un snapshot histórico anterior a todos estos materiales: **no utilizarla como carga actual**. El histórico del precio previo se conserva en las columnas `precio_matriz` y `fecha_matriz` del CSV de auditoría; `precio_revisado` recoge el valor actual.
