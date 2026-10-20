# Auditoría SEO integral — Google · Bing · Yahoo (2026-10-20)

Estado SEO reconstruido **con evidencia** (código, tests, herramienta de
auditoría y respuestas reales de producción), no por suposición. Lo que
exige cuentas externas (consolas de buscadores, enlaces, contenidos
editoriales) queda como acción del titular: este documento no lo marca
como hecho.

## Resumen

La base técnica está completa y verificada: sitemap con 195 URLs,
hreflang, canonical, datos estructurados, robots sano, superficie
pública cacheada en CDN y precios con fecha honesta y vigente. La
palanca técnica que faltaba para Bing/Yahoo era **IndexNow**: queda
implementada en este PR (clave pública + ruta de verificación +
herramienta de envío). Lo que sigue ya no es código: es medir en las
consolas (Google Search Console y Bing Webmaster Tools) y decidir con
esos datos — el piloto de SEO programático de la hoja de ruta (Fase 5)
se decide ahí, no a ciegas.

## Evidencia verificada (2026-10-20)

| Qué | Cómo se verificó | Resultado |
|---|---|---|
| Sitemap | `app.seo.urls_sitemap()` ejecutado hoy | **195 URLs**, todas en `https://cotizat.online`; 18 mercados hispanos × 7, `/en` 16, `/en-gb` 8, `/en-us` `/en-au` `/en-ca` `/en-ie` × 7, resto genéricas/legales |
| hreflang | recuento sobre el sitemap | **177** URLs con alternates |
| Producción | `GET /readyz` real | `ok: true`, 195 URLs, 54 artículos ES, host canónico, `errors: []` |
| robots.txt | fetch a producción | `Allow: /`, zona privada en `Disallow`, `Sitemap:` al apex |
| Head SEO | lectura de `_seo_head.html` | canonical, hreflang + `og:locale:alternate`, Open Graph/Twitter, JSON-LD con nonce CSP |
| Auditoría local | `tools/auditar_seo_produccion.py` (corrida local, acta en `docs/SEO_VERIFICACION_PRODUCCION_2026-10-20.md`) | **195/195** sin hallazgos |
| Tests SEO + caché | pytest (8 ficheros, incl. `test_indexnow`) | **282 passed** |
| Rendimiento/rastreo | Fase 1 de la hoja de ruta (en producción) | funciones junto a la BD (`yul1`), CDN `s-maxage=300`+SWR en la superficie pública, despliegue de 27 MB |
| Frescura de contenido | Fase 2 + botón de revisión (en producción) | guías con fecha derivada de los datos; `/readyz.precios_actualizados` vigila la cadencia mensual |
| Sitemap en Google | confirmado por el titular | enviado en Search Console ✅ |

## Novedad de este PR: IndexNow

- `app/indexnow.py`: clave pública del protocolo (no es un secreto; se
  publica por diseño) y su ruta.
- Ruta de verificación servida por la app:
  `https://cotizat.online/c2ecc63e4cd4d18c77e5b5e5430d7358.txt`
  (200, solo la clave; cubierto por tests).
- `tools/indexnow.py`: construye el lote desde el sitemap real.
  **Ensayo por defecto** (no toca la red); `--enviar` hace el POST a
  `api.indexnow.org`; `--url` para avisar de una guía nueva sin
  reenviar todo. Ensayo verificado hoy: 195 URLs, 1 lote.
- El envío real lo ejecuta el titular tras el despliegue (desde el
  sandbox no hay red hacia IndexNow, y es una acción externa).

## Plan por buscador

### Google
- **Estado:** sitemap enviado en Search Console por el titular.
  Google **no** participa en IndexNow; no hay nada que enviarle por
  esa vía.
- **Repo:** nada pendiente hoy. La base (sitemap, hreflang, velocidad,
  frescura) está en producción.
- **Titular (medir):** en GSC, vigilar *Páginas* (indexadas vs.
  enviadas) y *Rendimiento* por país durante las próximas semanas.
  Esos datos deciden el piloto programático (Fase 5): sin ellos, no se
  escala ninguna superficie.

### Bing
- **Estado:** IndexNow implementado y desplegado (PR #143; clave viva
  verificada). ⏸️ **Pendiente por decisión del titular (2026-10-20):**
  el primer envío y el alta en Bing Webmaster Tools quedan aparcados;
  la infraestructura queda lista para cuando se retomen.
- **Titular:** tras el despliegue, ejecutar el envío (comandos abajo).
  Alta en BWT con su cuenta — permite importar el sitio desde GSC —
  para ver indexación y errores de rastreo.
- **Rutina:** al publicar o actualizar una guía,
  `python tools/indexnow.py --enviar --url <url>`; el resto del tiempo
  no hay que reenviar el sitemap entero.

### Yahoo
- **Estado:** cubierto por Bing — Yahoo se alimenta de su índice.
- **Acción:** ninguna separada. Lo enviado vía IndexNow/BWT es lo que
  Yahoo sirve.

## Acciones del titular (en orden)

1. ~~**Verificar la clave viva**~~ ✅ Hecho en la entrega del PR #143:
   `https://cotizat.online/c2ecc63e4cd4d18c77e5b5e5430d7358.txt`
   devuelve solo la clave.

   *⏸️ Los puntos 2 y 3 quedan aparcados por decisión del titular
   (2026-10-20). Se retoman tal cual cuando se quiera.*

2. **Primer envío IndexNow** (prudente → completo):
   ```bash
   python tools/indexnow.py                    # ensayo: ver el lote
   python tools/indexnow.py --enviar --limite 10
   python tools/indexnow.py --enviar           # si lo anterior dio 200/202
   ```
3. **Bing Webmaster Tools:** alta del sitio (importar desde GSC) y
   comprobar que el sitemap se procesa.
4. **Auditoría remota con cabeceras reales** (el sandbox no puede ver
   la CDN): `python tools/auditar_seo_produccion.py https://cotizat.online`
5. *(De la Fase 2, sigue pendiente)*
   `DATABASE_URL=… python tools/verificar_matrices_bd.py` contra
   Supabase.

## Líneas rojas (lo que este plan no hace ni afirma)

- Nada de comprar enlaces, granjas, doorway pages, reseñas o
  testimonios falsos, ni volúmenes de búsqueda inventados.
- Ningún país se declara «SEO completo» sin datos de consola que lo
  respalden.
- Los contenidos editoriales nuevos (guías, artículos) son decisión
  del titular; el repo pone la plomería (sitemap, hreflang, avisos)
  para que al publicarlos queden bien expuestos.

## Relación con la hoja de ruta

Este paquete cierra la palanca técnica de indexación multi-buscador.
No sustituye la Fase 3 (i18n) ni el piloto de SEO programático de la
Fase 5: ese piloto se lanzará — o no — con los datos que empiecen a
dar Search Console y Bing Webmaster Tools.
