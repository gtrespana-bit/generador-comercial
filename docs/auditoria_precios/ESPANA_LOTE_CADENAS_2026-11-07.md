# España — barrido de cadenas, 7 de noviembre de 2026

**20 recursos con precio provisional**, a partir de 21 observaciones de Obramat y Leroy Merlin, sobre productos y variantes concretas; las 21 filas, URL, formato, normalización y reservas están en el [CSV](espana_fuentes_cadenas_2026-11-07.csv). No es un catálogo completo, ni un muestreo representativo nacional. Son referencias minoristas no garantizadas, pendientes de contrastar condiciones profesionales y zona. La consulta no certifica vigencia ni disponibilidad futura; IVA y precios pueden variar por tienda y promociones. No se consulta producción.

Para Obramat se usa el **precio sin IVA del envase** mostrado para la variante, dividido por kg, litros, unidades, longitud o superficie. Cuando únicamente se vio PVP, se estimó IVA general peninsular del 21%: las filas correspondientes lo indican. Para Leroy Merlin se usó PVP de la página y se estimó IVA 21% (sin comprobación de ticket ni ubicación fiscal); el campo vendedor de la tabla identifica el canal; el vendedor real de la masilla Leroy no se ha confirmado y el precio de marketplace no se atribuye automáticamente a la cadena. El transporte es no confirmado y no se añade de forma inventada. Los rótulos web de Obramat que repiten el precio del envase como €/kg, €/l o €/m² no se toman como precio unitario. En las superficies se usan dimensiones del producto, sin fijaciones ni mermas salvo indicación expresa. En una referencia con dos observaciones, el precio es el punto medio aritmético, no media estadística. Los extremos de matriz iguales no representan rango de mercado.

| Recurso | €/unidad | Fuente(s) | Alcance / reservas |
|---|---:|---|---|
| MT-SILICONA-EST | 11.17 / l | Obramat | Sellado neutro, no acredita uso como silicona estructural; confirmar compatibilidad con vidrio y carpintería. |
| MT-PIN-MASILLA | 1.23 / kg | Obramat + Leroy Merlin | Lista al uso para interior; soportes y reparación concretos por verificar. Precio sin IVA calculado con IVA general supuesto del 21%; no incluye envío. |
| MT-LASUR | 12.40 / l | Obramat | Acabado incoloro; protección UV y compatibilidad exterior concreta por confirmar. |
| MT-DECAP | 12.89 / l | Obramat | Quitapinturas de consistencia viscosa; no se acredita formulación gel exacta; validar soporte y seguridad. |
| MT-PRESERV-MAD | 13.17 / l | Obramat | Protección preventiva frente a insectos y hongos para interior y contracubiertas; no acredita todas las clases de servicio estructural. |
| MT-PINT-TRAFICO | 7.03 / l | Obramat | Pintura blanca acrílica para señalización; prestaciones viales o reflectantes por proyecto. |
| MT-ESMALTE-AGUA | 8.04 / l | Obramat | Base agua para madera y metal preparados; condiciones de acabado y soporte por verificar. |
| MT-PIN-TIZA | 18.51 / l | Obramat | Producto interior para escritura con tiza; no incluye imprimación ni garantías de cualquier soporte. |
| MT-SELLA-PIEDRA | 22.27 / l | Obramat | Hidro-oleorrepelente para piedra natural no pulida y materiales absorbentes; probar en el porcelánico específico. |
| MT-BLQ-10 | 0.47 / ud | Obramat | Bloque para particiones; confirmar resistencia, huecos y disponibilidad por tienda. |
| MT-BLQ-15 | 0.54 / ud | Obramat | Producto hueco; transporte, resistencia y alcance de precio por cantidad por confirmar. |
| MT-BLQ-20 | 0.68 / ud | Obramat | Producto hueco; transporte, resistencia y alcance de precio por cantidad por confirmar. |
| MT-PYL-PLACA-HD | 4.40 / m2 | Obramat | Placa de 3 m²: 15,97 € con IVA, neto calculado al 21%; 13 mm nominales frente a 12,5 solicitados; no acreditar prestaciones de sistema. |
| MT-MOSQUITERO | 14.26 / m2 | Leroy Merlin | Área nominal 1,68 m²; neto calculado IVA general supuesto 21%; sin montaje; tamaños distintos no escalan linealmente. |
| MT-ASPERSOR | 5.45 / ud | Obramat | Rosca macho incorporada; adaptador a la red y condiciones hidráulicas pueden precisar coste adicional. |
| MT-DETECT-HUMO | 5.73 / ud | Obramat | Solo detector autónomo, no direccionable; base y cumplimiento normativo del proyecto por verificar. |
| MT-ESPEJO | 29.52 / m2 | Obramat | Canto pulido; protección del respaldo y fijaciones por verificar; formato comercial no escala linealmente. |
| MT-PERFIL-REMATE | 2.85 / m | Obramat | Perfil de esquina negro, no representa toda transición o material; sin merma ni colocación. |
| MT-BARNIZ-PISO | 11.57 / l | Obramat | Barniz interior para tarima, resistencia a abrasión indicada; clase específica de alto tránsito por verificar. |
| MT-PIN-ANTIMOHO | 5.06 / l | Obramat | Pintura de interiores húmedos con conservante antimoho; efecto y adecuación a condiciones concretas por confirmar. |

## Productos revisados pero sin trasladar como precio completo

Las [exclusiones trazadas](espana_exclusiones_cadenas_2026-11-07.csv) conservan los motivos y enlaces cuando existe ficha identificada; los conjuntos sin producto concreto son advertencias, no ofertas observadas.

- Encofrados, señalización, apoyos, fijaciones de fontanería, accesorios de desagüe y cerrojos son **conjuntos**: una abrazadera, un cono, un sifón o una cerradura sin cilindro no representan el conjunto. Se seguirá componiendo cada uno con cantidades explícitas.
- La silicona adoptada es **neutra**, no prueba validez para acristalamiento estructural. Para el antimoho, detección y barniz se conservan reservas sobre la prestación exigida; no son certificados de un sistema.
- No se aplican un adhesivo de piedra sin acreditar protección frente a manchas, una tubería 110 mm con junta elástica como junta cementada, ni una imprimación epoxi distinta de puente entre hormigones; tampoco se extrapolan kg a litros sin densidad.
- Leroy Merlin y Obramat muestran precios que cambian con tienda, fecha, cantidad y vendedores. Para la masilla, la distancia entre 0,78 y 1,67 €/kg refleja dos productos y canales, no una distribución nacional.

Matriz, inventario, SQL local e índice público ES regenerados; 61 pruebas superadas y 388 filas importables sin errores. La importabilidad solo valida formato. Se actualizan únicamente los artefactos locales; no se ha ejecutado SQL, desplegado ni cambiado precios de clientes.
