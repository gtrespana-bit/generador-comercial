# España: lote adicional priorizado — 7 de noviembre de 2026

Se añaden **18 referencias provisionales**, calculadas a partir de 20 componentes de fuentes puntuales. El orden prioriza recursos usados en muchas partidas. Permanecen **en revisión** y no son precios comerciales confirmados ni medias nacionales. Las cantidades de uso se solapan; no se pueden sumar como partidas únicas.

## Resultados y cálculos

| Código | Usos | Cálculo de componentes (EUR) | Referencia | Reserva principal |
| --- | ---: | --- | ---: | --- |
| MT-PERNO-ANCLA | 148 | 0.81 / 1 × 0.44375 + 1.19 / 1 × 1 | 1.55 €/ud | Descomposición CYPE: 4 barras B500S Ø12 y 50 cm; dividir 1,775 kg entre cuatro, más un juego de tuerca, contratuerca y arandelas por barra. No incluye placa, instalación ni coste de roscado no acreditado; verificar dimensiones, resistencia y conformidad estructural. Edición, IVA y portes no confirmados. |
| MT-PERFIL-ACERO | 79 | 1.54 / 1 × 1 | 1.54 €/kg | Perfil trabajado y montado en taller e imprimado, alcance superior o diferente al corte a medida solicitado; confirmar sección, tratamiento, fecha de edición, IVA y portes. |
| MT-PUENTE-ADH | 76 | 15.942148760 / 1 × 1.5 | 23.91 €/l | Kit bicomponente; se usa densidad nominal de mezcla 1,5 ± 0,1 kg/l, no densidad de envase. IVA 21% supuesto. Asegurar compatibilidad con hormigón y condiciones de aplicación. |
| MT-CINTA-ENM | 57 | 17.78 / 30 × 1 + 1.24 / 1 × 1 | 1.83 €/ud | Hipótesis de un rollo de pintor 29 mm × 45 m y un rollo de embalaje 48 mm × 66 m por unidad; verificar la composición efectiva, cantidad y alcance del conjunto. |
| MT-MANTA-ACUS | 7 | 3.36 / 1 × 1 | 3.36 €/m2 | Polietileno reticulado 10 mm; no incluye instalación, cinta ni solapes. Confirmar espesor, vigencia, IVA y porte. |
| MT-HIDROFUGO | 14 | 9.57 / 5 × 1 | 1.91 €/l | Densidad nominal aproximada del fabricante 1,0 kg/l; precio publicado para 5 kg, no extrapolar otras formulaciones. Confirmar dosis y obra. |
| MT-SILOXANO | 2 | 31.40 / 5 × 1 | 6.28 €/l | Misma oferta de Sikagard-711 ES empleada también para la otra categoría de hidrofugante: no son dos observaciones independientes. Comprobar soporte, permeabilidad y ficha específica; precio unitario web mal etiquetado, se usa envase de 5 l. |
| MT-HIDROFUG-FACH | 4 | 31.40 / 5 × 1 | 6.28 €/l | Misma oferta de Sikagard-711 ES empleada también para la otra categoría de hidrofugante: no son dos observaciones independientes. Comprobar soporte, permeabilidad y ficha específica; precio unitario web mal etiquetado, se usa envase de 5 l. |
| MT-LIMP-QUIM | 10 | 3.14 / 1 × 1 | 3.14 €/l | Ejemplo para cemento, cal y óxido sobre soportes descritos; no sirve para toda mancha o fachada. Comprobar compatibilidad, dilución y ficha de seguridad. |
| MT-IMPRIM-ASF | 18 | 26.528925620 / 5 × 1 | 5.31 €/l | Precio impuestos incluidos; se supone IVA general peninsular 21%, pendiente de confirmar fiscalidad y disponibilidad. Validar compatibilidad con manto. |
| MT-CIELO-DESM | 6 | 1.75 / .36 × 1 | 4.86 €/m2 | Precio por pieza dividido entre 0,36 m²; el €/m² neto de la web repite erróneamente el precio por pieza. Sin perfilería ni instalación; revisar prestaciones acústicas. |
| MT-LACA-MADERA | 7 | 11.98 / 1 × 1 | 11.98 €/l | Acrílica para madera interior, limpieza al agua; base acuosa no explicitada en la ficha comercial. Verificar ficha técnica y compatibilidad con acabado. |
| MT-BARNIZ-MARINO | 2 | 7.83 / .75 × 1 | 10.44 €/l | Barniz de exterior castaño resistente a intemperie; confirmar prestaciones marinas y color requerido; solo un formato. |
| MT-PEGA-MURAL | 4 | 8.18 / .5 × 1 | 16.36 €/kg | Precio del concentrado, no de mezcla preparada; confirmar si el rendimiento de la partida mide kg de concentrado y compatibilidad con revestimientos textiles. |
| MT-TINTE-MAD | 1 | 8.22 / .75 × 1 | 10.96 €/l | Tinte interior al disolvente color roble; no representa otras bases o colores. La web etiqueta el importe neto de envase como €/l; dividir por 0,75 l. |
| MT-CERRADURA-MULTI | 9 | 81.82 / 1 × 1 | 81.82 €/ud | Modelo de embutir para puerta de madera, 3 puntos, cilindro y cerradero; comprobar mano, dimensiones y seguridad del proyecto. |
| MT-PIN-MAGNETICA | 1 | 10.983471074 / .5 × 1 | 21.97 €/l | Base agua color gris para paredes, precio de una oferta. IVA 21% supuesto; comprobar número de manos y efecto magnético requerido. |
| MT-SELLA-CONC | 4 | 90.91 / 15 × 1 | 6.06 €/l | Precio observado en producto relacionado, no directamente en la ficha principal. Apto para hormigón impreso; confirmar disponibilidad, transparencia, acabado y condición de compra. |

## Fuentes y reproducibilidad

El [CSV de componentes](espana_fuentes_prioridad_2026-11-07.csv) conserva enlaces de producto, enlace exacto del precio cuando es distinto, enlaces técnicos, importe bruto, base, formato, cantidades y reservas. La función `referencias_lote_prioridad()` valida códigos, unidades, componentes, fecha, IVA, cantidades y cálculo con `Decimal`, redondeando solamente el resultado final.

- Obramat: importe neto publicado por envase; sus etiquetas netas por litro o metro cuadrado pueden repetir el importe del envase. Se divide por la cantidad real. El precio del sellador se vio en una ficha relacionada, lo cual se explicita en el CSV.
- Leroy Merlin y BigMat: IVA general peninsular **21 % supuesto** al desglosar PVP; sujeto a comprobación fiscal y territorial. No se usa una base fiscal supuesta para Canarias.
- CYPE: se toman precios unitarios de materiales de ejemplos públicos, no el coste de la partida completa. **Fecha de edición, IVA y portes no confirmados**; se conserva IVA `por_verificar`. No se afirma vigencia comercial. La ferralla y el juego del perno proceden del mismo ejemplo, no son dos ofertas independientes.
- Sikadur 32 EF usa densidad nominal de mezcla **1,5 ± 0,1 kg/l**; Sika-1 usa aproximadamente **1,0 kg/l**. La densidad depende de ficha y condiciones; no es una conversión universal.
- Las dos categorías de hidrofugante comparten exactamente una sola oferta Sikagard-711; no son observaciones independientes. La cinta usa la hipótesis explícita de un rollo de cada tipo. La cola es concentrada, no mezcla preparada.
- El coste del perno no demuestra que se incluya el roscado; no incluye placa ni instalación. Una referencia de material no acredita seguridad estructural ni sustituye proyecto.

## Candidatos no aplicados

- `MT-MALLA-JUNTA`: el rollo de 1 m de ancho exige decidir un ancho de corte para convertir €/m² a €/m; 20 cm es solo una hipótesis, no especificación general.
- `MT-PER-BANDA`: la cinta localizada es de **8 mm**, frente a 10 mm exigidos; se mantiene pendiente.
- Válvula PPR empotrada: la ficha no confirma que sea de esfera. El producto para quitar papel está expresado en gramos y no se dispone de densidad fiable para convertir a litros. No se les asigna precio.
- Otros conjuntos incompletos o perfiles sin equivalencia suficiente también se mantienen pendientes.

## Alcance del corte

- Inventario: **13 confirmados como referencia, 141 en revisión y 234 pendientes**, de 388; **116 precios revisados**.
- Se regeneran matriz, inventario, SQL y precálculo público ES en el repositorio; el SQL es un archivo local, **no se ha ejecutado**.
- Los extremos iguales de la matriz son el mismo punto, no una horquilla de mercado. El precio y la disponibilidad pueden variar por centro, fecha y transporte.
- La importabilidad técnica no valida las especificaciones, la cobertura comercial ni el mercado. No se despliega ni se modifican precios de clientes.

## Comprobaciones

Se ejecutaron 61 pruebas de auditoría, lotes, inventario y precios públicos; todas pasaron. El verificador de importación ES encontró 388 filas importables y 0 errores. La importabilidad es solo un control técnico, no una validación comercial.
