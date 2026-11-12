# SEO comercial de LATAM: búsquedas que pueden llevar a una venta

## Objetivo y límites

La prioridad son personas que buscan una herramienta para crear presupuestos
comerciales de obra, no simplemente un precio unitario. La evidencia histórica
del repositorio (`DIAGNOSTICO_GSC_REAL_2026-11-02.md`) muestra 46 consultas
comerciales, 121 impresiones y ningún clic en su muestra; no demuestra el
estado actual. «Generador de construcción» es ambiguo: puede significar otros
productos. Se utiliza «generador de presupuestos de construcción/obra» para
explicar qué hace CotizaT. Las variantes son hipótesis de búsqueda, no
volúmenes ni resultados de una investigación actual de palabras clave.

## Páginas y acciones

- Conservar `/{país}/software-presupuestos` como página comercial de cada uno
  de los 17 mercados LATAM ofrecidos. El título y el encabezado apuntan al
  generador de presupuestos; el contenido explica software, programa para
  cotizar obras, APU, margen y PDF de forma natural. No se crean páginas
  separadas para sinónimos con la misma intención. La landing del país y los
  hubs de APU y remodelación permanecen en sus URLs existentes.
- CTA directo de alta cuando existe prueba, acceso a planes y PDF de ejemplo;
  sin ofrecer prueba si está desactivada. La página de planes conserva el país
  de origen y su enlace de prueba lo mantiene al pasar al alta, incluso sin
  cookie previa. El precio se consulta en la página de planes, no en cifras
  duplicadas dentro de estos hubs. Hay ejemplos locales y advertencias fiscales
  sin prometer facturación ni precios vigentes.
- Una guía visible de tres pasos explica el recorrido hasta enviar un PDF y
  se responden preguntas de compra sobre precios propios, importación y
  facturación. La muestra es un PDF ficticio venezolano en USD, no una
  cotización real ni una muestra localizada para cada país; se indica junto
  al enlace. El PDF al cliente no se presenta como un informe de margen interno.
- Los catálogos con precios enlazan a la página comercial de su país: la
  consulta informativa puede convertirse en una visita al producto. No se
  modifica la política de indexación ni se anuncian mercados no disponibles.
- El CTA de prueba comunica `software_comercial` como sección y preselecciona
  el país en el alta. La telemetría existente puede contar registros de esa
  sección; no demuestra que procedan de búsqueda orgánica. Los clics de CTA
  usan eventos existentes de GA cuando está configurado. Un clic, registro o
  prueba no es una venta.

## Medición después de desplegar

1. En Search Console, comparar periodos completos de 28 días anteriores y
   posteriores por país, consulta y página: impresiones, clics, CTR y posición
   de `/{país}/software-presupuestos`. Segmentar consultas no de marca con
   intención comercial (generador, software, programa o aplicación junto a
   presupuesto/cotización de obra). Revisar manualmente las consultas reales
   y excluir otros sentidos de «generador». No presentar hipótesis como volumen
   medido; anotar fechas, filtros y posible estacionalidad.
2. Revisar inspección de URL, canónica, indexación y qué página aparece por
   consulta. Vigilar si landing y hub de un mismo país se alternan sin mejorar;
   no hacer redirecciones o noindex masivos sin evidencia.
3. Medir clics orgánicos a la página, visitas a planes, altas atribuidas a
   `software_comercial`, primer presupuesto real y empresas pagadoras por
   país y cohorte. Conectar esos pasos solo si la analítica disponible permite
   hacerlo respetando privacidad y consentimiento; no atribuir al SEO un pago
   por el mero origen del CTA. La telemetría de sección no distingue canal.
4. Para más competitividad hace falta investigación de consultas y resultados
   reales por mercado, autoridad y menciones externas legítimas, evidencia de
   producto y revisión local. Priorizar con datos de negocio, no por cantidad
   de URLs ni impresiones de catálogo.

El despliegue, la indexación y la autoridad llevan tiempo. Estas mejoras no
garantizan aparecer en una posición concreta ni producir ventas.
