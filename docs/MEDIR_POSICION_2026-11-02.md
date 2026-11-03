# Medir la posición: qué mirar y qué pedir (02/11/2026)

Contexto: el 23/10 se aplicó la reducción de huella del catálogo
(`MERCADOS_FICHAS_INDEXABLES` en `app/services/precios_publicos.py`) y se
acordó congelar cambios de SEO dos semanas para poder atribuir el efecto.
Hoy es el día 10: toca **medir**, no volver a tocar.

Este documento fija qué datos hacen falta, qué significa cada uno y qué
decisión se toma con cada resultado. Sin esta lectura, cualquier cambio
posterior es otra apuesta a ciegas.

## 1. Los cinco datos que hacen falta

Todo en Search Console, propiedad `cotizat.online`, **rango de 3 meses** y
comparado con «3 meses anteriores»:

| # | Dónde | Qué se descarga | Para qué |
|---|---|---|---|
| 1 | Rendimiento → **Consultas** | CSV (botón *Exportar*) | Qué busca la gente que te ve y en qué puesto |
| 2 | Rendimiento → **Páginas** | CSV | Qué URLs gastan impresiones y en qué puesto |
| 3 | Rendimiento → **Consultas + Páginas** | CSV | Detectar canibalización y elegir la página dueña de cada consulta |
| 4 | Indexación → **Páginas** | Captura del gráfico + tabla (*No indexada* incluida) con su fecha de actualización | Si las fichas retiradas ya salieron y si el resto se indexa |
| 5 | Estadísticas de rastreo → **Descargar** | Captura de «Rastreo por respuesta» y «por tipo de archivo», 90 días | Si Googlebot sigue viniendo y si algo responde 403/5xx |

Opcional que ahorra discusión: en Rendimiento, gráfico de **16 meses** con las
casillas *Clics*, *Impresiones* y *Posición media*. La forma de la caída
distingue las dos causas: un escalón es un cambio técnico; una pendiente es
pérdida de calidad o competencia.

Con 1, 2 y 3 basta para empezar.

## 2. Cómo leerlos (herramienta lista)

```bash
python tools/analizar_gsc.py Consultas.csv Paginas.csv ConsultasPaginas.csv
python tools/analizar_gsc.py --carpeta ~/Descargas/gsc --min-impresiones 50
```

Acepta las exportaciones en español (punto y coma, decimales con coma) y en
inglés (coma), y responde:

- **Cuota de marca vs genéricas.** Si más de la mitad de las impresiones son
  de «cotizat», no hay descubrimiento: el problema no es el ranking, es que
  nadie busca lo que vendes con las palabras de la web.
- **Consultas con impresiones y cero clics.** Si están en el puesto 20+, el
  problema es el puesto; si están en el 5–10, el problema es el título y la
  descripción.
- **El techo real:** páginas en la franja 5–25 con clics potenciales
  estimados. Es donde rinde cada hora de contenido.
- **Canibalización:** la misma consulta repartida entre `/`, `/es/`, `/mx/`,
  `/es/apu`… Cada consulta debe tener una sola página dueña.

## 3. Qué decide cada resultado

| Lo que sale | Diagnóstico | Qué se hace |
|---|---|---|
| Impresiones estables, posición media 40–60, marca minoritaria | El sitio está indexado y no compite: falta contenido propio por intención | Trabajar las consultas genéricas con más impresiones: una página por intención, con dato real (precio, país, oficio) |
| La misma consulta repartida entre varias URLs | Canibalización entre mercados | Elegir dueña, enlazar las demás hacia ella, `noindex, follow` en los calcos |
| Páginas en 5–25 con muchas impresiones | Cerca del top: se gana con el contenido que ya hay | Mejorar título/H1/estructura y enlazado interno hacia esas URLs |
| Cobertura: las fichas de los 16 mercados ya como *Excluida por noindex* | El cambio del 23/10 funcionó | Esperar la siguiente ventana; no tocar nada |
| Cobertura: landings del panel de mercado también excluidas o con error | No es lo esperado: algo marcó de más | Revisar `es_indexable()` y el `X-Robots-Tag` de las landings |
| Estadísticas de rastreo con 403/429/5xx hacia Googlebot | Bloqueo de borde | Es la causa nº 1 de una caída seca: revisar firewall de Vercel antes que nada |
| Clics a cero también en marca | Posible acción manual o desindexación | GSC → Acciones manuales y Problemas de seguridad, primero de todo |

## 4. Lo que NO se hace en esta ventana

- No se reenvía el sitemap ni se cambia `robots.txt`.
- No se añaden redirecciones ni se renombran URLs.
- No se toca el `noindex` de los 16 mercados antes de tener los datos de
  cobertura: encender un mercado es una decisión medida, no una corazonada.
- No se inventan reseñas ni `aggregateRating` para limpiar el aviso de
  Fragmentos de productos (ver `docs/AUDITORIA_SEO_2026-10-22.md`, sección de
  markup honesto).

## 5. Herramientas que ya existen

| Herramienta | Qué hace |
|---|---|
| `tools/analizar_gsc.py` | Lee los CSV de Search Console (nuevo, 02/11) |
| `tools/auditar_seo_produccion.py` | Comprueba el sitio desplegado por HTTP: código, canónica, hreflang, sitemaps y sonda Googlebot |
| `tools/verificacion_seo.py` | Comprobaciones internas de la generación de SEO |
| `.github/workflows/ci.yml` | Prueba `tests/test_analizar_gsc_tool.py` en cada empujón |
