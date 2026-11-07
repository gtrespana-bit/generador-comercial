# España — lote de materiales de alto uso, 7 de noviembre de 2026

Se seleccionaron recursos con muchos usos. La matriz aplica **referencias provisionales**, no cotizaciones ni medias estadísticas españolas. Se comparan dos ofertas comerciales por recurso: precio con IVA / 1,21 / cantidad física, media aritmética sin redondeo intermedio y redondeo final a céntimos. Sin portes ni IVA deducible; descuentos, existencias y condiciones de entrega son variables. La evidencia y las condiciones se conservan en [`espana_materiales_ofertas_2026-11-07.csv`](espana_materiales_ofertas_2026-11-07.csv).

| Recurso | Usos en inventario | Precio anterior | Dos observaciones normalizadas, sin redondeo intermedio | Precio provisional | Limitaciones |
|---|---:|---:|---|---:|---|
| MT-CABLE-DATOS | 47 | 0,341772 €/m | Ilumitec 161,31 €/305 m y Sonicolor 145,33 €/305 m, ambos con IVA | 0,42 €/m | Cat6 UTP rígido cobre 100 %, AWG24, Dca, libre de halógenos; caja/bobina completa. Sonicolor indica porte especial; verificar condiciones de proyecto y envío. |
| MT-DESMOLD | 45 | 3,189873 €/l | SLucía 176,90 €/25 l y Aislamientos González 182,04 €/25 l, ambos con IVA | 5,93 €/l | Mismo Sika LN listo al uso, principalmente para encofrados metálicos, también protege madera. No es representativo de productos diluibles u otros desencofrantes. Disponibilidad de González por confirmar. |
| MT-ALAMBRE | 49 | 2,10 €/kg | Ferrovicmar 5,95 €/1 kg y Ferretería Esteve 5,95 €/1 kg, ambos con IVA | 4,92 €/kg | Mismo Nivel 1,3 mm, misma referencia; posible proveedor común. Dos precios idénticos no prueban estabilidad ni independencia de mercado. El formato minorista de 1 kg puede costar mucho más que una compra de obra a granel. Verificar stock de Esteve. |

Los usos no se suman como partidas únicas: pueden coincidir en un mismo descompuesto. Los tres recursos permanecen `en_revision`, incluso cuando se emplea el precio provisional. Cada referencia guarda mínimo y máximo observados normalizados, no un intervalo estadístico ni costes de entrega. Las páginas pueden cambiar: se anotó lo observado en la fecha, no un precio permanente.

## Descartes de esta ronda

- **Lana mineral de 60 mm:** la ficha de Restatec aparece como artículo no disponible y la otra fuente no pudo abrirse. La ficha Sasmak Knauf contiene contradicciones entre 60 mm en título/características y 50 mm en descripción; la oferta Volcalis requiere un mínimo de 48 paquetes. No se ha aplicado ningún precio para este recurso.
- **Fondo fijador:** una oferta indica simultáneamente no disponible y últimas unidades y su rendimiento difiere de la otra; no se promediaron. Iplisa muestra un rango para dos variantes, sin asociar inequívocamente cada importe al tamaño en la página leída. No se aplica precio.
- **Desencofrante Gasca:** la oferta indica sin existencias; se han usado otras dos fuentes en su lugar. Se privilegió la ficha actual sobre cifras antiguas indexadas, que diferían.

## Regeneración y límites

El generador conserva congelada la canasta histórica utilizada para los recursos aún pendientes y superpone solo los tres precios de este lote. Se regeneran la matriz, `basedatos_partidas/datos/precios_publicos/ES.json` y `docs/cargar_precios_referencia_espana_2026-11-06.sql`. El nombre de este último se mantiene por compatibilidad; sus filas contienen sus propias fechas de consulta. No se ejecutó el SQL ni se desplegó. El fichero de carga abarca 388 recursos: revisar su alcance antes de una eventual aplicación; no presupone autorización para modificar producción o precios de clientes.
