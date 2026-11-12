# Visibilidad orgánica en Latinoamérica — 12/11/2026

## Alcance y diagnóstico

El selector ofrece 17 mercados hispanos de LATAM: México, Colombia, Perú,
Chile, Argentina, Venezuela, Ecuador, República Dominicana, Panamá, Costa
Rica, Guatemala, Honduras, El Salvador, Nicaragua, Uruguay, Paraguay y Bolivia.
Brasil no está en el selector ni hay versión portuguesa; no se ha creado una
página para él ni se presume cobertura de toda Latinoamérica.

La última evidencia de Search Console guardada en el repositorio corresponde
al 25–31/10, no a la situación actual. `DIAGNOSTICO_GSC_REAL_2026-11-02.md`
reporta landings muy parecidas entre sí y pocas impresiones para consultas
comerciales. Es una referencia histórica, no una atribución causal ni una
medición del efecto de estos cambios. No hay datos actuales de GSC/SERP en este
entorno para afirmar posiciones o volúmenes por país.

## Cambios en esta entrega

- Los 17 hubs `/{país}/software-presupuestos` responden a un escenario local
  de obra y delimitan el documento comercial; se retiran de esos hubs dos
  bloques genéricos, incluida una afirmación no sustentada sobre el uso de
  Excel. Se conserva la URL, canónica, hreflang y enlaces editoriales.
- La descripción comercial usa el nombre del impuesto del mercado, no siempre
  «IVA». Un impuesto de referencia no determina el tratamiento de la obra.
- Los puentes desde landings, hubs y guías priorizan apartados indexables en
  mercados parcialmente localizados. Si no hay ninguno, siguen mostrando el
  catálogo navegable al visitante. El índice enlaza directamente las fichas
  indexables cuyo apartado aún no cumple el umbral de indexación.
- No se habilita la indexación masiva de fichas que carecen de texto local ni
  se crean cifras, casos de clientes o promesas de funciones fiscales.

La diferenciación añadida es un primer paso, no prueba de relevancia local ni
un sustituto de entrevistas, enlaces y revisión por profesionales del país.

## Después del despliegue

1. En Search Console, comprobar la propiedad del dominio canónico y enviar
   `https://cotizat.online/sitemap_index.xml`. Inspeccionar una landing y un hub
   comercial por mercado y, donde existan, fichas localizadas: respuesta 200,
   canónica, contenido renderizado, indexabilidad y fecha del último rastreo.
   Revisar también que el dominio `www` redirige al canónico. No solicitar
   indexación de forma masiva.
2. Exportar rendimiento de búsqueda web por **país**, página y consulta con
   periodos completos de 28 días antes y después; excluir búsquedas de marca
   cuando se analicen consultas comerciales. Registrar impresiones, clics,
   CTR y posición media, junto con las consultas y URLs, sin confundir país
   del usuario con prefijo de la URL. Los datos antiguos de noviembre son solo
   contexto; la línea base debe ser el periodo previo real al despliegue.
3. Contrastar indexación y consultas de las 17 URLs comerciales, las guías y
   los catálogos parciales; investigar páginas excluidas y consultas reales de
   cada país antes de ampliar textos. Comparar por separado URLs con pocos
   datos: una variación pequeña no demuestra mejora. Usar
   `python tools/analizar_gsc.py --carpeta <exportaciones>` para los CSV
   compatibles y conservar periodos y filtros de cada exportación.
4. Medir registros, primer presupuesto y pagos por país y fuente orgánica
   únicamente si la analítica existente lo permite y con consentimiento;
   GSC no mide conversiones. Buscar colaboradores y fuentes locales reales,
   y revisar precios, terminología y condiciones legales con profesionales.

Los cambios necesitan despliegue, rastreo e indexación. Ni un sitemap ni
hreflang ni estas mejoras garantizan posiciones, clics o plazos de Google.
