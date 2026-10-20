# Verificación SEO post-merge — 20/10/2026

Continuación de `docs/SEO_PAQUETES_HISPANOS_2026-10-19.md`. Cierra los tres
puntos que quedaron sin certificar tras fusionar el PR #133 (46 recursos
hispanos nuevos): código HTTP/cabeceras, matrices de precios y el conflicto
`www` ↔ apex.

## Resumen

| Punto pendiente | Estado tras esta sesión |
| --- | --- |
| Las 46 páginas nuevas en producción | **Confirmadas**: despliegue *Production* del merge `48a372cc` (20/10 01:14Z) y contenido real servido, tablas de mano de obra incluidas. |
| HTTP 200, canónica, hreflang, meta robots, `X-Robots-Tag` | **Certificados contra el código de `main`** (el mismo commit desplegado) con la app real: 195/195 URLs del sitemap sin fallos. Queda la confirmación con cabeceras sobre el dominio en cuanto el titular ejecute la herramienta remota (este entorno no tiene red hacia `cotizat.online`). |
| Matrices en la base de producción | Artefactos dentro de la función: **confirmados** (las guías renderizan valores del CSV). Contenido de `precios_recursos_mercado` en Supabase: herramienta lista y probada (`tools/verificar_matrices_bd.py`); su ejecución contra producción requiere las credenciales, no disponibles aquí. `/readyz` ya publica el conteo. |
| Dominio preferido | **Conflicto confirmado**: el borde redirige apex → `www`, pero canónicas, sitemap, robots, correos y Supabase usan el apex. Corrección: un ajuste en Vercel Domains (pasos abajo). Sin cambio de código. |

## Hallazgo previo: los «404» eran la caché de la herramienta de lectura

Al empezar la sesión, `/mx/guia/mano-obra-construccion-mexico` y el sitemap
sin parámetros devolvían versiones anteriores al merge («Página no
encontrada» y sitemap sin las 46), mientras que con un parámetro nunca
usado respondían el contenido nuevo. Dos guías jamás consultadas
respondieron 200 sin parámetro. Conclusión: era la caché por URL exacta de
la herramienta de lectura (había guardado las respuestas previas al
merge), **no** el borde de Vercel. Regla para próximas verificaciones con
esa herramienta: usar URLs nunca consultadas o un parámetro nuevo, y para
cabeceras, `tools/auditar_seo_produccion.py`.

## El problema real: apex ↔ www

Evidencia (20/10/2026):

- `https://cotizat.online/…` termina en `https://www.cotizat.online/…`
  (redirección del borde; la app no redirige por host).
- `COTIZAT_PUBLIC_URL = https://cotizat.online` en producción
  (`/readyz`: `recovery_redirect_url_esperada` en el apex): canónicas,
  `hreflang`, `og:url`, sitemap, línea `Sitemap:` de `robots.txt` y los
  enlaces de los correos apuntan al apex.
- Resultado para Google: cada URL del sitemap redirige una vez y la
  página destino declara canónica la URL que redirige. Lo habitual es que
  elija la URL final (`www`) ignorando la canónica declarada, marque las
  del sitemap como «Página con redirección» y desperdicie rastreo en cada
  visita. No rompe la indexación, pero invalida la arquitectura de
  canónicas construida.

Decisión: **el apex sigue siendo el canónico** (así está en Supabase,
correos y todo el código). Solo falta que el borde lo sirva:

### Pasos en Vercel (titular, ~2 minutos)

1. Vercel → proyecto `cotizat-generador` → **Settings → Domains**.
2. En `www.cotizat.online`: editar y elegir **Redirect to**
   `cotizat.online` (redirección permanente, conservar ruta).
3. Confirmar que `cotizat.online` queda como dominio servido (sin
   redirección), no al revés.
4. Verificar sin paneles:
   - `https://www.cotizat.online/mx/apu` debe terminar en
     `https://cotizat.online/mx/apu`.
   - `https://cotizat.online/readyz` debe decir
     `"host_es_canonico": "si"`.
   - Pedir `https://www.cotizat.online/readyz` ya no debe responder la
     app: debe redirigir al apex.
5. No tocar DNS (GoDaddy) ni `COTIZAT_PUBLIC_URL` ni Supabase: ya están en
   el apex. Tras el cambio, Search Console (si la propiedad es de
   dominio, nada cambia; si era de prefijo `www`, crear/usar la del apex
   y reenviar `https://cotizat.online/sitemap.xml`).

> No se añadió redirección por host en la app a propósito: con la
> configuración actual del borde (apex → www) habría creado un bucle.
> La redirección de dominio en Vercel es el mecanismo soportado, y
> `/readyz` queda como detector permanente de regresiones.

## Qué se certificó en esta sesión (código `main` = producción)

- **Auditoría HTTP local completa** con la app real (uvicorn):
  `tools/auditar_seo_produccion.py http://127.0.0.1:8017` →
  **195/195 URLs del sitemap sin fallos**: 200 directo (sin
  redirecciones), host final = loc, canónica autorreferente, `hreflang`
  del HTML idéntico al del sitemap, sin `noindex` (meta ni cabecera), un
  solo `<h1>` y JSON-LD válido. Controles: `/acceso` con `noindex` y la
  guía mexicana bajo `/es/` con 404.
- **Verificador de matrices**: contra SQLite sembrada con el importador
  real (`6208` precios = 16 países × 388), coincidencia exacta
  CSV↔BD incluidos los cinco oficios de las guías; contra BD vacía
  detecta los 6.208 faltantes. La herramienta está lista; falta correrla
  contra Supabase.
- **Regresión**: 462 tests (SEO, idioma, mercados, health, dominio
  canónico) en verde, incluidos los nuevos
  `tests/test_seo_dominio_canonico.py`.

## Instrumentación nueva en `/readyz`

Chequeos informativos (nunca tumban el readiness), en `app/health.py`:

- `dominio_canonico`, `host_recibido`, `host_es_canonico`
- `seo_sitemap_urls` (195), `seo_articulos_es` (54)
- `seo_matriz_latam` (países con filas del CSV dentro de la función),
  `seo_base_venezuela`
- `precios_bd` + `precios_bd_paises`: referencias nacionales cargadas en
  la base (esto responde el «¿están cargadas las matrices?» con solo abrir
  `/readyz`).

## Lo que queda (en orden)

1. **Vercel Domains**: invertir apex/www (pasos arriba) y verificar con
   `/readyz` por ambos hosts.
2. **Auditoría remota con cabeceras**: desde cualquier máquina con red,
   `python tools/auditar_seo_produccion.py https://cotizat.online`
   (idealmente tras el paso 1; antes reportará la redirección por URL).
3. **Matrices en Supabase**:
   `DATABASE_URL=… python tools/verificar_matrices_bd.py`.
   Si faltan o difieren, cargar con `tools/importar_precios_mercado.py
   --apply` o los SQL de `docs/cargar_precios_referencia_*.sql`
   (ojo: los SQL del 25/08 traen jornales sin coste empresa; el CSV
   vigente ya lleva la ronda 7, así que ante divergencia manda el CSV).
4. **Search Console / Bing** (Semana 1 de `HOJA_DE_RUTA_SEO.md`): enviar
   el sitemap del apex e inspeccionar las landings y 2–3 guías nuevas.

*Rama: `arena/af8c9900-generador-comercial` sobre `main` en `48a372cc`.*
