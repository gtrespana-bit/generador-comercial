# Revisión comercial y conversión — 12 de noviembre de 2026

## Enfoque

Priorizar las páginas de software y generador de presupuestos de construcción; los catálogos de precios y las guías son entradas secundarias que pueden conducir al producto. No hay datos actuales de Search Console ni mediciones nuevas que permitan atribuir ventas o posiciones a estos cambios. El diagnóstico interno del 2 de noviembre es histórico, no un embudo actual.

## Correcciones realizadas en esta rama

- Los importes visibles de las portadas y planes se obtienen del mismo registro `PLANES` usado por la compra y Stripe. El cobro configurado es en USD, también en España: no se han modificado los cargos. Se han retirado las referencias al primer año y los precios tachados de estas pantallas, ya que el código de Stripe crea una suscripción al importe configurado sin cambio programado al año y la revisión no ha verificado precios anteriores. Las fichas SEO remiten a los planes para evitar cifras desactualizadas. El schema de SoftwareApplication usa la misma fuente.
- Los textos de planes dejan de prometer tarjeta cuando Stripe está desactivado; el checkout describe los métodos manuales disponibles para el país, no una lista venezolana universal. Activación por Stripe depende de la confirmación y del webhook. El titular confirma que ya se hicieron pruebas de pago y que existen usuarios de pago; esta revisión no ha verificado personalmente esos pagos ni la configuración de producción.
- El enlace móvil de «Precios y planes» ahora lleva a la página de planes existente. Se conserva la navegación del catálogo como entrada secundaria.
- Con `alta=1` el formulario de registro aparece primero y tiene la acción principal; sin ese parámetro se conserva primero el inicio de sesión. El orden está en HTML, sin depender de JavaScript. País y atribución se conservan como antes.
- Las pantallas de planes recuperan la hoja de estilo con JavaScript desactivado.

## Pendiente de validar antes de decidir inversiones

1. Probar el recorrido completo en dispositivo móvil con cuentas de prueba: búsqueda comercial → página de país → registro → confirmación de correo → empresa → primer presupuesto → compra. Medir cada transición, incluidos abandonos. El diagnóstico histórico señaló dificultades de activación, pero no permite concluir que persistan hoy.
2. El checkout usa el país explícito cuando está en la URL y, si falta, el país de la organización. La cookie de intención solo guarda el plan: al retomar la compra desde el panel tras el alta, el país de pago elegido antes puede perderse si difiere del país de la organización. La persona puede volver a elegirlo; conviene diseñar y probar la persistencia de esa elección sin confundir país de pago y de empresa.
3. Aprovechar las pruebas de pago ya realizadas: contrastar, si aún no se hizo, importe, moneda, renovación y activación con el checkout real. No es necesario repetir pagos solo por esta revisión; revisar webhook o hacer pruebas adicionales si se cambia el flujo o aparece un problema.
4. La etiqueta GA se inserta si hay ID configurado; `_ga.html` no comprueba una elección de cookies antes de cargarla. Revisar requisitos de consentimiento con asesoría y configuración real; no asumir que la aceptación de términos del registro cubre analítica. La atribución `software_comercial` indica sección, no que el origen sea orgánico ni que haya venta. Definir y validar un embudo agregado de alta, primer presupuesto, checkout y pago confirmado, sin datos personales innecesarios.
5. Contrastar consultas y páginas comerciales en Search Console con datos actuales; separar búsquedas de software de consultas informativas y seguir registros, activación y pagos mediante instrumentos apropiados. No reenviar sitemaps repetidamente ni prometer posiciones.
6. La ruta `/sitemap_index.xml` está implementada y declarada en `robots.txt`; las pruebas comprueban el dominio canónico. Vercel identifica el merge #225 como deployment productivo READY/PROMOTED. Esta revisión no ha podido comprobar directamente por HTTP el dominio público desde el entorno, así que confirmar el estado del sitemap en Search Console.
