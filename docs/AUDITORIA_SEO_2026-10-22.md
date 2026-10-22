# Auditoría SEO integral — 2026-10-22

Revisión **completa** de la superficie pública: no una muestra. Se rastrearon
las **47.148 URLs** que hoy anuncian los sitemaps (200 en el sitemap principal
+ 22 sitemaps de precios), se inspeccionaron cabeceras y cuerpos reales, y se
midieron los datos diferenciales entre mercados. Este documento recoge **lo
medido**, **lo corregido en código** y **lo que queda en manos del titular**
(cuenta de Search Console/Bing, enlaces externos, contenidos editoriales).

Complementa a `AUDITORIA_SEO_2026-10-20.md`, que describía una superficie de
195 URLs. El producto creció dos órdenes de magnitud (catálogo de precios
programático por país); este documento es el que refleja ese estado.

---

## 1. Resumen ejecutivo

La base técnica estaba bien: canónicas correctas, hreflang recíproco, un solo
host, robots sano, IndexNow, caché de CDN y cero enlaces internos rotos en
47.148 URLs. Los problemas reales eran de **forma de los datos que ve el
buscador** y de **arquitectura de enlaces internos**, no de infraestructura:

| Hallazgo | Alcance medido | Estado |
|---|---|---|
| `title` > 60 caracteres | 46.773 de 47.143 URLs | **Corregido** (plantillas de precio y hubs ES/EN) |
| `meta description` > 160 caracteres | 40.356 URLs | **Corregido** (`MAX_DESCRIPCION = 155`) |
| Páginas de apartado con < 300 palabras | 1.762 URLs (239–298 palabras) | **Corregido**: 421–432 palabras con datos propios |
| Huérfanas desde `/` | 14 URLs (todo el silo inglés + `/novedades`) | **Corregido** (pie EN + enlace nuevo) |
| `hreflang` sin `x-default` | 6 guías | **Corregido** |
| `/en/guia/<artículo>` fuera del sitemap | 5 URLs | **Corregido** (y par es/en recíproco) |
| Guías y landings sin enlace al catálogo de precios | 47.148 URLs dependían del índice del país | **Corregido**: puente desde home, landings, hubs y guías |
| Sin `@id` en el grafo JSON-LD | todas las páginas | **Corregido** (Organization/WebSite/Software) |
| `areaServed: "Latinoamérica"` | home genérica | **Corregido** (23 países reales) |
| `/us`, `/gb`, `/en` con doble salto | 4 redirecciones | **Corregido** (301 directo) |
| 404 con texto plano | todos los 404 | **Corregido** (HTML 404, `noindex,follow`) |
| Imagen Open Graph de 870 KB | todas las páginas | **Corregido** (JPEG 66 KB, 1200×630) |
| Activos con hash servidos `max-age=0` | `?v=…` | **Corregido** (`immutable`, 1 año) |
| `/soporte` y `/en/soporte` en sitemap con `noindex` | 2 URLs | **Sin defecto real** (ver §5) |

Resultado del rastreo tras los cambios: **0 enlaces internos rotos**, **0
respuestas no-200 en URLs del sitemap**, hreflang recíproco en todo el grafo,
y **418 pruebas** verdes en la batería SEO/precios/caché/idioma (suite
completa: 2.359 pasan, 12 omitidas).

---

## 2. Cómo se midió

- Rastreo propio de las 47.143 URLs del sitemap contra la app real
  (`tools` + cliente HTTP): estado, `<title>`, `meta description`, canónica,
  alternates, H1, `alt`, JSON-LD, recuento de palabras del `<main>`.
- Comparación de contenido entre mercados (similitud de texto y n-gramas)
  para descartar canibalización entre los 22 catálogos.
- Verificación de redirecciones con `curl` sin seguir: código y `Location`.
- Comprobación de cabeceras de caché, compresión y tipos MIME por recurso.
- Ejecución de la suite de pruebas por área y después completa.

Todo lo que exige cuentas externas (impresiones, cobertura de índices,
Consultas de Search Console, backlinks) **no** se marca como hecho: se
enumera en §7 como acción del titular.

---

## 3. Correcciones aplicadas

### 3.1 Títulos y descripciones (46.773 + 40.356 URLs)

El problema no era "faltan keywords", era que el snippet se cortaba y se
perdía **el precio y el país**, que es exactamente lo que hace clic en una
página de precios.

- `app/seo_precios.py`: `MAX_TITULO = 60`, `MAX_DESCRIPCION = 155`,
  `_titulo_meta()` elige la primera variante que cabe (de la más informativa
  a la más escueta) y solo recurre a un título más largo —que Google
  recortará por su cuenta— cuando el nombre de la partida es tan largo que
  ninguna variante cabe. Nunca se recorta a mitad de palabra.
- `_recortar()` ahora cierra en el último punto completo si deja aprovechada
  al menos la mitad del espacio: las descripciones acaban en frase, no en
  «…» a mitad de palabra.
- Las descripciones de partida pasaron de nombrar la partida otra vez (ya
  está en el título y el H1) a añadir el dato que falta:
  `«1.297,50 MXN/ud en México (septiembre de 2026). Materiales 86%, mano de
  obra 12%, maquinaria 1%. Descompuesto línea a línea del catálogo CotizaT.»`
  (145 caracteres, frase completa).
- Los hubs de país en inglés (`app/seo_en.py`) tenían títulos de hasta 88
  caracteres: se acortaron por mercado (US 60/52, GB 57/50, CA 53/49,
  AU 56/48, IE 47/53) y se eliminó el título duplicado entre `/` y
  `/software-presupuestos` (y su gemelo EN).
- Efecto colateral corregido: la home de país sin mercado (`/en/`) ya no
  repite el título de la home genérica.

### 3.2 Arquitectura de enlaces: el puente que faltaba hacia el catálogo

**El hallazgo de mayor impacto.** Las 47.000 URLs de precios se descubrían
solo por (a) el sitemap y (b) el índice de su país. La home, las landings de
mercado, los hubs de intención y las guías —las páginas que primero rankean y
concentran autoridad— no enlazaban a **ninguna** de ellas.

Ahora:

- `app/seo_precios.py::enlaces_catalogo()` devuelve, para un país y una
  semilla (el slug de la guía), cinco apartados **deterministas y repartidos
  por todo el catálogo** (arranque por hash del slug + salto de
  `len/limite`). Cada guía reparte su enlace a un tramo distinto, no todas a
  los mismos cinco apartados, y el resultado es estable entre peticiones y
  despliegues (sin "enlaces aleatorios" que confundan al rastreador).
- `indices_catalogo()` enumera los 22 índices para la home genérica, que no
  tiene país propio.
- Puente insertado en: `landing.html`, `landing_en.html` (bloque «Precios
  unitarios de obra en <país>, con su descompuesto»), `seo_hub.html`,
  `seo_hub_en.html`, `seo_guia.html`, `seo_guia_en.html`.
- CSS propio en `public.css` (`.mercados-precios`), con el mismo ritmo
  visual que la tabla de mercados.

Cada página de guía/hub pasa de 0 a **6 enlaces** hacia precios del mercado;
las landings de país, de 0 a 6; la home, a los 22 índices.

### 3.3 Contenido de las páginas de apartado (1.762 URLs finas)

Un apartado era una tabla con un párrafo y dos enlaces (239–298 palabras),
justo la página que compite por «precios de X en Y». Se enriqueció con datos
que **solo esa página tiene** (nada de relleno):

1. **Rango real del apartado** en ese mercado: mínimo, máximo y media de sus
   partidas, con el mes de revisión del catálogo.
2. **«Cómo se lee este precio»**: qué incluye el descompuesto (materiales,
   mano de obra, maquinaria), qué no incluye y por qué varía por región.
3. **«Seguir explorando»**: apartados hermanos del mismo capítulo (hasta 8),
   índice del país y guía de APU en el idioma de la página.

Medido: `/mx/precios/aislamiento-acustico` pasa de ~255 a **432 palabras**;
`/en-us/prices/acoustic-insulation`, a **421**. Las páginas de partida ya
estaban entre 627 y 880 palabras y ahora superan las 1.100 con la ficha
técnica estructurada (§3.5).

### 3.4 Huérfanas y silo inglés (14 URLs)

Desde `/` no se llegaba a: `/en/apu`, `/en/guia/*` (×3), `/en/legal/*` (×5),
`/en/novedades`, `/en/remodelacion`, `/en/software-presupuestos`,
`/en/soporte`, `/novedades`.

- `_footer_publico_en.html`: los 15 enlaces del pie pasan de rutas españolas
  a `{{ '/en/…' }}` (el logotipo apunta a `/en-us/`), más «Product updates» →
  `/en/novedades`.
- `_footer_publico.html`: se añade «Novedades del producto» → `/novedades`.
- `_nav_en.html` y `public/_nav_en.html`: el menú inglés enlazaba a
  `/como-funciona`, `/guia/presupuesto-de-obra`, `/legal/preguntas` y `/pago`
  en español. Ahora usa las rutas `/en/…` correspondientes y el logotipo va a
  `/en-us/`.
- `mapa_sitio.html` / `mapa_sitio_en.html`: el mapa en inglés enlazaba a los
  tres hubs de intención y a las guías **en español**; ahora usa `/en/apu`,
  `/en/remodelacion`, `/en/software-presupuestos` y `/en/guia/…`. Se añaden
  enlaces a novedades y al otro idioma.

Verificado: los 14 destinos responden 200 y reciben al menos un enlace desde
la home de su idioma.

### 3.5 Grafo de entidades JSON-LD

- `@id` estables: `#organization`, `#website`, `#software`. Antes cada página
  declaraba tres entidades anónimas distintas; ahora Organization, WebSite y
  SoftwareApplication se referencian entre sí (y `publisher`/`author` de los
  artículos apuntan al nodo de organización en lugar de duplicarlo).
- `logo` pasa a `ImageObject` con dimensiones (requisito de Google para el
  logotipo de marca) y se añade `image` social.
- `areaServed` de la home genérica era el literal `"Latinoamérica"`, que no
  es un país: ahora enumera los **23 mercados** como `Country`. En páginas de
  país se usa el nombre del país sin artículo («United States», no «the
  United States»).
- **Nuevo** `TechArticle` en cada página de partida: titular, descripción,
  fecha de publicación/revisión tomada del catálogo, autor y publicador por
  `@id`, idioma y `about` (el apartado). Es la descripción honesta de lo que
  la página es: una ficha técnica de precio con fecha.

**Decisión explícita: no se emite `Product`/`Offer`/`AggregateOffer` en las
páginas de precio.** El precio publicado es una referencia de catálogo, no
una oferta comprable; Google exige ofertas reales para los resultados
enriquecidos de producto y el markup que simula una oferta inexistente es
motivo de acción manual por markup engañoso. `ItemList` (ya presente en los
apartados) y `TechArticle` describen la página sin ese riesgo.

### 3.6 404 real

Antes, una URL inexistente devolvía texto plano. Ahora hay
`app/templates/404.html` (marca, `noindex,follow`, **sin** canónica, cinco
salidas útiles) servida con estado **404** desde un manejador de
`StarletteHTTPException`, con respaldo JSON para `/api/*`. Todos los
`Response("Página no encontrada", 404)` de `precios_publicos.py` y
`publico.py` pasaron a `raise HTTPException(404)`.

Matriz verificada: `/no-existe`, `/xx/precios`, `/mx/precios/no-existe`,
`/zz/` → `404 text/html`; `/api/*` → `404 application/json`.

### 3.7 Redirecciones de un solo salto

`/us`, `/us/`, `/gb`, `/en` encadenaban dos 301 (`/us` → `/en-us` →
`/en-us/`). Ahora cada alias resuelve en **un** salto a la URL final con
barra. Matriz: `/us → /en-us/`, `/en → /en-us/`, `/gb → /en-gb/`,
`/es → /es/`, `/co → /co/`.

### 3.8 Sitemaps

- `sitemap_index.xml` (nuevo): índice de los 23 sitemaps, con `lastmod`
  **por mercado** tomado de `precios_publicos.resumen(cc)["fecha_revision"]`
  (antes era una constante única, que es una señal falsa de frescura).
  Cacheado con `s-maxage=300`. `robots.txt` lo anuncia primero.
- Los `.xml` dejan de llevar `X-Robots-Tag: noindex` (`es_ruta_indexable`
  exime `.xml`/`.txt`).
- **Cinco URLs que faltaban**: las traducciones inglesas de los artículos de
  mercado (`/en/guia/apu-panete-colombia`, `…/apu-dolares-ecuador`,
  `…/cotizar-remodelacion-mexico`, `…/metrados-peru`,
  `…/presupuesto-usd-bs-venezuela`) respondían 200 con canónica propia y solo
  se descubrían por enlace.
- El par `hreflang` de esas guías se declara ahora **en los dos sentidos**
  (la versión española vive en `/co/guia/x`, no en `/guia/x`) con
  `x-default` a la española. Una sola función, `enlaces_guia()`, alimenta el
  `<head>` y el sitemap para que no puedan divergir.

### 3.9 Rendimiento de carga (afecta a rastreo y a Core Web Vitals)

- **Imagen Open Graph**: 870 KB PNG → `og-cotizat.jpg` de **66 KB**
  (1200×630, calidad 90, progresivo). Con 870 KB, WhatsApp y LinkedIn
  descartaban la miniatura; el PNG queda eliminado del repositorio
  (`git rm`). `og:image` apunta al JPEG en `app/seo.py`.
- **Activos con hash `?v=`**: pasan de `max-age=0, must-revalidate` a
  `public, max-age=31536000, immutable`. Los no versionados mantienen
  `s-maxage=31536000, stale-while-revalidate=604800`. Verificado con `curl`:
  `cache-control: public, max-age=31536000, immutable` + `gzip` real.
- **Doble descarga de CSS**: 19 plantillas repetían la hoja en un
  `<noscript>` con URL distinta a la del `<link>` principal, así que el
  navegador descargaba y aplicaba `public.css` dos veces. Se eliminó el
  `<noscript>` redundante (la hoja ya está enlazada arriba).

### 3.10 i18n y detalles de plantilla

- Traducciones del 404 y de los bloques nuevos de precio en `es.json` /
  `en.json` (84 claves cada uno); el copy inglés usa «labor», no «labour»,
  salvo en las páginas de mercado británico.
- Se eliminaron los `style=` en línea de la 404 (la CSP los prohíbe y el test
  de plantillas lo comprueba): pasan a `.error-404` en `public.css`.

---

## 4. Lo que está bien y no se tocó (verificado, no supuesto)

- **Canónicas**: una sola URL por contenido; los alias redirigen.
- **hreflang**: recíproco en todo el grafo, con `x-default` en cada par.
- **Contenido diferencial**: los 22 catálogos no son el mismo texto con otra
  bandera. Partidas entre mercados: 48–56 % de similitud (652–877 palabras de
  texto propio); apartados: 52–77 %. Cumple la línea roja de la hoja de ruta
  («ninguna URL programática sin dato diferencial»).
- **Enlaces internos**: 264 destinos distintos comprobados, 0 rotos.
- **H1, `alt`, jerarquía de encabezados**: sin ausencias.
- **JSON-LD**: los seis bloques por página parsean sin error.
- **robots.txt**: zona privada bloqueada, `Sitemap:` al dominio canónico.
- **Compresión**: HTML y CSS/JS con gzip real (`Vary: Accept-Encoding`).

---

## 5. Falsos positivos descartados (para no volver a "arreglarlos")

1. **`/soporte` con `noindex` en el sitemap.** En el entorno de desarrollo la
   sesión de prueba hace que se sirva el panel de soporte (que es
   `noindex` por diseño). Sin sesión —como rastrea Google— se sirve
   `soporte.html`, que lleva `_seo_head.html`, canónica y un título de 46
   caracteres («Soporte de CotizaT: escríbenos y te contestamos»). No hay
   defecto que corregir.
2. **404 en `/es/precios/<slug>` de partidas inexistentes.** Es el
   comportamiento correcto.
3. **Páginas de precio "finas" o duplicadas.** Medido: 48–77 % de texto
   propio entre mercados y ≥ 1.100 palabras por partida. No son duplicados.

---

## 6. Pruebas

- Nueva batería `tests/test_seo_grafo_y_puentes.py` (6 pruebas) que fija lo
  que se rompió sin avisar: par `es/en` en el sitemap, puente a precios desde
  home/landing/guía, `@id` del grafo, `areaServed` por país y 404 HTML.
- Batería SEO/precios/caché/idioma/plantillas: **418 pruebas verdes**.
- Suite completa: **2.359 pasan, 12 omitidas, 0 fallos**.

---

## 7. Lo que queda en manos del titular (no es código)

1. **Search Console**: enviar `sitemap_index.xml` (sustituye a los envíos
   sueltos), revisar «Páginas» tras 2–4 semanas y vigilar el informe de
   *Mejoras → Artículos* (nuevo `TechArticle`).
2. **Bing Webmaster Tools**: reenviar el índice con el helper de IndexNow
   (`tools/indexnow.py --enviar`) tras el despliegue.
3. **Rich Results Test** sobre una muestra: una guía, un apartado, una
   partida y la home.
4. **Enlaces externos**: el sitio sigue dependiendo de autoridad prestada.
   Sin backlinks temáticos (colegios profesionales, portales de construcción,
   prensa sectorial), el techo del SEO programático son las long-tail de baja
   competencia. Es la palanca que ningún cambio de código sustituye.
5. **Medición**: definir una línea base de consultas/impresiones por clúster
   (precios por país, guías por oficio, software) antes de crear más
   superficie. Crecer en URLs sin medir es la forma más rápida de repartir
   autoridad sin retorno.

---

## 8. Archivos tocados

```
app/seo.py                 títulos/descripciones, enlaces_guia(), @id, areaServed,
                           TechArticle de precios, robots, sitemap, og:image
app/seo_precios.py         MAX_TITULO/MAX_DESCRIPCION, _titulo_meta, _recortar,
                           enlaces_catalogo(), indices_catalogo(), jsonld_ficha_precio(),
                           enriquecimiento de apartados
app/seo_en.py              títulos por mercado (US/GB/CA/AU/IE), sin duplicados
app/routers/publico.py     puente de catálogos, HTTPException(404), sitemap_index
app/routers/precios_publicos.py  404 reales
app/main.py                _quiere_html, manejador de 404, caché immutable
app/cache_publico.py       /sitemap_index.xml
app/locales/{es,en}.json   error404.*, precios.rango.*
app/templates/404.html     (nuevo)
app/templates/landing*.html, seo_hub*.html, seo_guia*.html   puente a precios
app/templates/_footer_publico*.html, _nav_en.html, public/_nav_en.html,
  mapa_sitio*.html         silo inglés y huérfanas
app/templates/pais_precio_apartado.html                     bloques nuevos
app/static/og-cotizat.jpg  (nuevo, 66 KB) · og-cotizat.png (eliminado)
app/static/css/public.css  .mercados-precios, .error-404
tests/test_seo_grafo_y_puentes.py                           (nuevo)
```
