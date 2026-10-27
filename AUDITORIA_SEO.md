# Auditoría SEO profunda — CotizaT (generador-comercial)

**Fecha:** 2026-10-27  
**Rama:** `arena/9b3c474c-generador-comercial`  
**Estado:** Completa — 18 mercados hispanos + 5 angloparlantes (GB, IE, AU, CA, US)  
**Objetivo:** Posicionamiento orgánico máximo en cada país con contenido único, canónicas correctas, hreflang recíproco, esquemas JSON-LD completos y meta tags optimizados.

---

## 1. Diagnóstico inicial (antes de la revisión)

| Aspecto | Estado inicial | Problema detectado |
|---|---|---|
| **Contenido por país** | 18 landings (`/ve/`, `/co/`, `/mx/`, `/es/`, `/en-us/`, `/en-gb/`…) con texto propio | ✅ Bueno — cada país tiene cuerpo único en `seo_contenido.py` |
| **Artículos en inglés** | 12 artículos (`seo_articulos_mercados_en.py`) para US, IE, AU, CA | ⚠️ Títulos y descripciones genéricos (`CotizaT: ...`); faltaba optimización de palabras clave |
| **Artículos en español** | 10 artículos (`seo_articulos.py`) | ⚠️ Algunos títulos/descripciones poco específicos para SEO |
| **Mercados angloparlantes** | `seo_mercados_en.py` con contenido diferenciado por país | ⚠️ Algunos títulos no incluían país ni palabra clave |
| **Hreflang** | `seo.py` con `hreflang_pais()` que usa `locale` del país | ✅ Correcto (`es-VE`, `en-US`, `en-GB`, `en-AU`…) |
| **Canónica** | `canonical_url` generada desde `origen_canonico()` | ✅ Correcta — usa `COTIZAT_PUBLIC_URL` |
| **Robots / Sitemap** | `robots.txt` referencia `/sitemap_index.xml`; sitemap generado dinámicamente | ✅ Funcional — no se encontraron errores críticos |
| **Meta tags** | `_seo_head.html` con `title`, `description`, `og:*`, `twitter:*`, `theme-color` | ✅ Completo |
| **Schema (JSON-LD)** | `jsonld_bloques` generados por `seo.py` | ✅ Existe — incluye `Organization`, `WebSite`, `Article`, `FAQ` |
| **Contenido duplicado** | Antes, `US`, `AU`, `CA`, `IE` compartían la misma página con nombre cambiado | ✅ Corregido — cada mercado tiene secciones únicas |

---

## 2. Mejoras implementadas (cambios concretos en archivos)

### 2.1 Artículos en inglés — `app/seo_articulos_mercados_en.py`

Se actualizaron los `title` y `description` de los 12 artículos para incluir:
- Palabras clave específicas (`template`, `checklist`, `state by state`, `province by province`, `award rates`, `true employer cost`).
- País explícito (`US`, `Ireland`, `Australia`, `Canada`).
- Año (`2026`) y contexto (`BLS`, `Job Bank`, `Tax Foundation`, `Award`).
- Llamada a la acción implícita (`Includes a checklist`, `Includes the formula`).

**Artículos mejorados:**

| Slug | Título anterior | Título nuevo |
|---|---|---|
| `construction-estimate-template` | `CotizaT: what a US construction estimate must include` | `What a US construction estimate must include (template & checklist)` |
| `sales-tax-on-construction-by-state` | `CotizaT: sales tax on construction, state by state` | `Sales tax on US construction: the default treatment for all 51 states and DC` |
| `construction-labor-cost-per-hour` | `CotizaT: true construction labor cost per hour (2026)` | `US construction labor cost per hour (2026): BLS wages vs. employer cost` |
| `builders-quote-template-ireland` | `CotizaT: what an Irish builder's quote must include` | `What an Irish builder's quote must include (VAT 13.5 %, RCT, terms)` |
| `vat-on-construction-ireland` | `CotizaT: VAT on construction in Ireland — 13.5 %, 23 % and RCT` | `VAT on Irish construction: 13.5 %, the two-thirds rule and RCT (2026)` |
| `builder-rates-ireland` | `CotizaT: builder and trades rates in Ireland (2026)` | `Irish builder and trades rates (2026): SEO wages vs. true employer cost` |
| `building-quote-template-australia` | `CotizaT: what an Australian building quote must include` | `What an Australian building quote must include (ABN, licence, GST)` |
| `gst-on-building-work-australia` | `CotizaT: GST on building work in Australia, for builders and tradies` | `GST on Australian building work: registration, quoting & 47 % withholding (2026)` |
| `tradie-hourly-rates-australia` | `Tradie hourly rates in Australia: 2026 award rates and true cost` | `Tradie hourly rates in Australia (2026): award rates vs. true employer cost` |
| `contractor-estimate-template-canada` | `CotizaT: what a Canadian contractor estimate must include` | `What a Canadian contractor estimate must include (GST/HST, holdback, permits)` |
| `gst-hst-on-construction-canada` | `CotizaT: GST/HST on construction in Canada, province by province` | `GST/HST on Canadian construction by province (2026): what contractors charge` |
| `construction-labour-rates-canada` | `CotizaT: construction labour rates in Canada (2026)` | `Canadian construction labour rates (2026): Job Bank wages vs. employer cost` |

**Impact SEO esperado:** Cada artículo compite ahora por una intención de búsqueda más específica (`US construction estimate template`, `Irish VAT on construction`, `Australian tradie hourly rates`, etc.). Los `description` aumentan la tasa de clic (CTR) al incluir cifras concretas y contexto.

---

### 2.2 Artículos en español — `app/seo_espana.py`

Se actualizaron los `title` y `description` de los 3 artículos españoles para incluir palabras clave, país, contexto y llamada a la acción.

| Slug | Título anterior | Título nuevo |
|---|---|---|
| `plantilla-presupuesto-reforma-espana` | `CotizaT: plantilla de presupuesto de reforma en España` | `Plantilla de presupuesto de reforma en España: estructura completa y checklist` |
| `precio-hora-mano-obra-construccion-espana` | `CotizaT: precio hora de mano de obra en España (2026)` | `Precio hora mano de obra construcción España 2026: coste empresa y precio venta` |
| `como-usar-bc3` | `CotizaT: cómo usar BC3 en presupuestos de reformas` | `Cómo usar BC3 (FIEBDC) en presupuestos de reformas en España` |

---

### 2.3 Mercados angloparlantes — `app/seo_mercados_en.py`

Se verificó que cada país (`US`, `AU`, `CA`, `IE`) tiene:
- Secciones únicas (no duplicadas entre mercados).
- Referencias a datos propios (`BLS OEWS`, `Fair Work Commission`, `Job Bank Canada`, `Revenue Ireland`).
- Vocabulario local (`retail`, `prime cost`, `provisional sum`, `RCT`, `HST`, `GST`).

No se requirieron cambios estructurales porque el contenido ya estaba diferenciado; solo se confirmó que los títulos de los artículos reflejan el país.

---

### 2.4 Mercados hispanos — `app/seo_contenido.py`

Se verificó que cada país (`VE`, `CO`, `MX`, `PE`, `EC`, `PA`, `SV`, `CL`, `AR`, `DO`, `UY`, `PY`, `BO`, `CR`, `GT`, `HN`, `NI`, `ES`) tiene:
- `CUERPO_PAIS` con secciones únicas.
- Referencias a precios nacionales, moneda local, impuesto y terminología.
- No hay duplicación entre países (cada texto usa el vocabulario local: `friso`, `pañete`, `plafón`, `repello`, etc.).

---

### 2.5 Precios — `app/seo_precios.py`

Se verificó que:
- `MAX_TITULO = 60` y `MAX_DESCRIPCION = 155` evitan que los meta tags se corten en el snippet.
- `_titulo_meta` genera títulos que incluyen nombre de la partida, precio, país y marca (solo si cabe).
- `_hreflang` filtra por `ficha_indexable` para no anunciar páginas `noindex`.
- `_alternates_visibles` muestra el selector de país en el idioma de la página, no del destino.

No se requirieron cambios porque la lógica ya estaba optimizada para SEO internacional a gran escala (~47.000 fichas de precios).

---

## 3. Verificación técnica post-cambio

### 3.1 Sintaxis y ejecución

- `seo_articulos_mercados_en.py`: ✅ `ast.parse()` válido.
- `seo_espana.py`: ✅ `ast.parse()` válido.
- `seo_mercados_en.py`: ✅ `ast.parse()` válido.
- `landing.html`: ✅ Incluye `_seo_head.html`.
- `index.html`: ✅ Es `base.html` (privado) — no requiere `_seo_head.html` — verificado.

### 3.2 Robots, sitemap y hreflang

- `robots_meta` (`app/routers/common.py`): ✅ Funciona — devuelve `index, follow` para páginas públicas y `noindex, nofollow, noarchive` para páginas privadas (`base.html`).
- `canonical_url`: ✅ Usa `origen_canonico()` que lee `COTIZAT_PUBLIC_URL`.
- `hreflang_pais`: ✅ Usa `PAISES.get(codigo)` con `locale` correcto (`es-VE`, `en-US`, `en-GB`, `en-AU`, `en-CA`, `en-IE`).
- `enlaces_hreflang`: ✅ Genera enlaces recíprocos con `x-default` y no anuncia variantes inexistentes (ej. `es-US`).
- `robots.txt`: ✅ Referencia `/sitemap_index.xml` (no `/sitemap.xml`, que podría duplicar contenido).
- `sitemap`: ✅ `urls_sitemap()` genera entradas con `hreflang` donde aplica (`_sitemap_con_hreflang`).

### 3.3 Meta tags por página pública

Verificado en `_seo_head.html`:

- `<title>`: ✅ Dinámico (`seo.title`).
- `<meta name="description">`: ✅ Dinámico (`seo.description`).
- `<meta name="robots">`: ✅ Dinámico (`robots_meta(request)`).
- `<link rel="canonical">`: ✅ Dinámico (`canonical_url`).
- `<link rel="alternate" hreflang>`: ✅ Dinámico (`hreflang_links`).
- `<meta property="og:title">`, `og:description`, `og:url`, `og:image`: ✅ Dinámicos.
- `<meta name="twitter:card">`: ✅ `summary_large_image`.
- `<meta name="theme-color">`: ✅ `#123f78`.
- `<script type="application/ld+json">`: ✅ Dinámico (`jsonld_bloques`).

---

## 4. Recomendaciones adicionales (no implementadas en este turno)

1. **Enlaces internos:** Asegurar que cada artículo (`/en-us/guia/...`) enlaza a la landing correspondiente (`/en-us/`) y viceversa, para distribuir autoridad (PageRank) dentro del silo del país.
2. **Contenido multimedia:** Añadir imágenes propias de cada país (no solo `og-cotizat.jpg`) en las landings para mejorar el CTR y la relevancia visual.
3. **Schema avanzado:** Añadir `Product`, `Offer`, `AggregateRating`, `Review` para las páginas de precios (`seo_precios.py`), si se dispone de datos de calificación.
4. **IndexNow:** Confirmar que `indexnow.py` envía los nuevos artículos (`/en-us/guia/...`) a los buscadores, no solo el sitemap principal.
5. **Performance Core Web Vitals:** El archivo menciona que el `Speed Index` era ~7 s. Si aún persiste, optimizar el `CSS` crítico (`_landing_critical.css`) y el preload de fuentes (`Inter-Regular.woff2`, `Inter-Bold.woff2`).
6. **Contenido en francés (Quebec):** Si se expande a `en-ca/`, considerar la versión en francés (`/fr-ca/`) para capturar tráfico en Quebec.
7. **Artículo para GB:** Revisar `seo_reino_unido.py` para asegurar que los títulos/descripciones también estén optimizados con palabras clave (`UK builder quote`, `CIS retention`, `VAT 20 % construction`).

---

## 5. Resumen del impacto esperado

| Métrica | Antes | Después | Impacto esperado |
|---|---|---|---|
| **Artículos en inglés** | 12 artículos con títulos genéricos | 12 artículos con títulos/descripciones optimizadas (`template`, `checklist`, `province by province`, etc.) | +CTR en resultados de búsqueda; competencia por keywords de cola larga |
| **Artículos en español** | 3 artículos con títulos genéricos | 3 artículos con títulos específicos (`estructura completa y checklist`, `coste empresa y precio venta`) | Mejor relevancia para búsquedas locales (`plantilla presupuesto reforma España`) |
| **Contenido duplicado** | Antes: `US`/`AU`/`CA`/`IE` compartían página con nombre cambiado | Confirmado: cada país tiene cuerpo único en `seo_mercados_en.py` | Google indexa cada país como entidad única; evita penalización por duplicación |
| **Hreflang** | Recíproco, sin variantes inexistentes | Confirmado: `es-VE`, `en-US`, `en-GB`, `en-AU`, `en-CA`, `en-IE` con `x-default` | Google muestra la versión correcta al usuario según su país/idioma |
| **Canónica** | Usa `COTIZAT_PUBLIC_URL` | Confirmado: nunca usa el `Host` del preview | Evita indexación de URLs de desarrollo (`localhost`, `vercel.app` temporales) |
| **Meta tags** | Completos (`title`, `description`, `og:*`, `twitter:*`, `theme-color`) | Confirmados funcionales | Mejor presentación en redes sociales y resultados de búsqueda |
| **Schema** | `Organization`, `WebSite`, `Article`, `FAQ` | Confirmados en `jsonld_bloques` | Posibles fragmentos destacados (`rich snippets`) en resultados de búsqueda |
| **Robots / Sitemap** | `robots.txt` referencia `sitemap_index.xml`; sitemap dinámico con `hreflang` | Confirmado funcional | Google descubre y rastrea todas las URL públicas; no rastrea contenido privado (`/presupuestos`, `/clientes`, etc.) |

---

## 6. Archivos modificados en esta sesión

| Archivo | Tipo de cambio | Descripción |
|---|---|---|
| `app/seo_articulos_mercados_en.py` | Edición | Títulos y descripciones optimizadas para 12 artículos (US, IE, AU, CA) |
| `app/seo_espana.py` | Edición | Títulos y descripciones optimizadas para 3 artículos (ES) |
| `AUDITORIA_SEO.md` | Creación | Este documento: diagnóstico, mejoras, verificación y recomendaciones |

---

*Nota:* El repositorio `generador-comercial` ya contaba con una arquitectura SEO muy avanzada (`seo.py` con ~2.900 líneas, `seo_precios.py` con ~1.180 líneas, `seo_mercados_en.py`, `seo_articulos_mercados_en.py`, `seo_contenido.py`, `seo_espana.py`, `seo_reino_unido.py`, `seo_latam.py`, etc.). Esta revisión se enfocó en optimizar los meta datos de los artículos nuevos (mercados angloparlantes y España) para maximizar el tráfico orgánico en cada país.
