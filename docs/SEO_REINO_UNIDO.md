# SEO de Reino Unido: qué se ha construido y cómo se explota

**Fecha:** 18 de octubre de 2026
**Ámbito:** mercado `GB` (`/en-gb/`), dentro de un producto que ya sirve 23
mercados y que hasta hoy tenía **una sola plantilla inglesa** para los cinco
mercados anglófonos.

---

## 1. El problema que había

La adaptación al inglés estaba hecha (3.006 partidas, PDF, correos), pero el
SEO no era de mercado:

| Síntoma | Consecuencia |
|---|---|
| `/en-gb/` era `landing_en.html` con `{{ país }}` sustituido | Contenido idéntico a `/en-us/`, `/en-au/`… salvo el nombre |
| El cuerpo largo solo existía para mercados hispanos (`CUERPO_PAIS`) | La landing inglesa no tenía ni un H2 propio de Reino Unido |
| Los hubs ingleses pedían la ficha **en español** | `/en-gb/apu` tenía H1 en inglés y cuerpo y FAQ en español |
| Cero artículos y cero guías de mercado | Nada que capte búsquedas de cola larga (CIS, reverse charge, plantillas) |
| El sitemap anunciaba `/gb/` y `/en/` | Ambas son 301: Search Console las marca como «página con redirección» |
| El hreflang `en` apuntaba a `/en/` | Un hreflang que redirige se descarta |
| `inLanguage` del schema decía `en` | La página se declara `en-GB` en `<html lang>` |
| `/en-gb/guia/...` no existía como ruta | Cualquier artículo de mercado habría dado 404 |
| `X-Robots-Tag: noindex` por la ruta reescrita | Una página indexable podía salir con noindex |

## 2. Qué se ha construido

### 2.1 Una URL por intención

| URL | Intención | Contenido |
|---|---|---|
| `/en-gb/` | «construction estimating software UK» | Landing + cuerpo largo británico (7 bloques) + FAQ de 9 preguntas |
| `/en-gb/software-presupuestos` | «estimating software for builders» | Hub + 3 bloques de mercado (preliminares, Excel, CIS/IVA) |
| `/en-gb/apu` | «unit price analysis construction» | Hub + coste empresa, residuos, plant |
| `/en-gb/remodelacion` | «refurbishment quote software» | Hub + strip-out, making good, snagging |
| `/en-gb/guia/construction-quote-template-uk` | «construction quote template UK» | Artículo: qué lleva una quotation británica |
| `/en-gb/guia/cis-deduction-subcontractors` | «CIS deduction 20%» | Artículo: las tres retenciones |
| `/en-gb/guia/vat-domestic-reverse-charge-construction` | «VAT domestic reverse charge» | Artículo: s. 55A y el 5 % / 0 % |
| `/en-gb/guia/unit-price-analysis-uk` | «unit price analysis UK» | Artículo: coste empresa y productividad |

Reglas que no se deben romper:

- **Una URL canónica por artículo.** `/gb/guia/x` existe solo como 301 a
  `/en-gb/guia/x`; nunca se enlaza ni se indexa.
- **El artículo de mercado no se anuncia en español.** Su hreflang es
  `en-GB` + `x-default`; no existe una versión `es`.
- **`HowTo` solo en las guías pilar**, no en artículos de fiscalidad.

### 2.2 Dónde vive el contenido

| Qué | Archivo |
|---|---|
| Cuerpo, FAQ, hubs y 4 artículos de GB | `app/seo_reino_unido.py` |
| Copy inglés genérico (otros mercados) | `app/seo_en.py` |
| Rutas canónicas, hreflang, sitemap, schemas | `app/seo.py` |
| Plantilla de landing en inglés | `app/templates/landing_en.html` |
| Plantilla de hub en inglés | `app/templates/seo_hub_en.html` |
| Plantilla de artículo en inglés | `app/templates/seo_guia_en.html` |
| Pruebas del mercado | `tests/test_seo_reino_unido.py` |

### 2.3 Cifras y fiscalidad: de dónde salen

El texto no inventa precios ni tipos. Repite lo que ya está validado en el
producto:

- **388 recursos en GBP**, 167 investigados uno a uno y 221 derivados.
- **Coste empresa/hora** con recargo del 19,8 % sobre 1.751,9 h facturables.
- **CIS** 20 / 30 / 0 % sobre la mano de obra, descontando materiales.
- **IVA** 20 % estándar, 5 % en obra residencial que cumple condiciones, 0 %
  obra nueva, e inversión del sujeto pasivo (VATA 1994 s. 55A).

Si cambia una cifra en `docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md` o en
`app/services/fiscalidad_reino_unido.py`, hay que cambiarla también aquí.

## 3. Decisiones técnicas que sostienen el SEO

1. **Indexabilidad por la ruta original.** `WebSecurityMiddleware` decide el
   `X-Robots-Tag` leyendo `scope["state"]["ruta_original"]`: el middleware de
   idioma reescribe `/en-gb/guia/x` a `/gb/guia/x` y con la ruta reescrita la
   página salía `noindex`.
2. **Sitemap sin redirecciones.** Se emite `ruta_mercado()` (la canónica) y no
   `ruta_pais()`, que en un mercado inglés devuelve el alias que redirige.
3. **hreflang `en` → `/en-us/`.** `/en/` es un 301; anunciarla es anunciar una
   redirección.
4. **`inLanguage` con locale** (`en-GB`, `es-MX`) en `WebPage`, `Article` y
   `SoftwareApplication`, y `areaServed` con el nombre del país en el idioma
   de la página.
5. **Meta description ≤ 160 caracteres.** Las guías no llevan la coletilla de
   la prueba gratuita: solo servía para que Google cortara la frase.
6. **Los hubs piden la ficha en el idioma de la petición**
   (`ficha_tema(..., lang=lang)`). Antes se pedía siempre en español.

## 4. Cómo publicarlo

1. Desplegar. Comprobar `/readyz` = `l7d0e3f6a9c4`.
2. Abrir `https://www.cotizat.online/sitemap.xml` y confirmar que aparecen las
   cuatro URLs `/en-gb/guia/...` y que **no** aparecen `/gb/` ni `/en/`.
3. Search Console → Sitemaps → reenviar `sitemap.xml`.
4. Inspeccionar URL de `/en-gb/` y de un artículo: «Página indexable», canonical
   correcta, sin `noindex`.
5. Enlazar desde fuera: directorios de oficio británicos, asociaciones
   (FMB, TrustMark), prensa del sector. El contenido ya responde a las
   consultas; los enlaces son lo que falta.

## 5. Qué medir y qué ampliar

- **Medir:** impresiones y CTR por consulta en Search Console para las cuatro
  páginas de artículo; posición de «construction quote template UK» y «CIS
  deduction».
- **Ampliar (siguiente ronda):** `day rate` / `labour rates UK`, `schedule of
  works template`, `snagging list`, `how to price a job`, `bathroom
  refurbishment cost`. Cada uno merece su artículo, no un párrafo.
- **No ampliar** hasta que estos cuatro tengan impresiones: más URLs sin
  autoridad reparten el presupuesto de rastreo sin sumar tráfico.

## 6. Lo que NO se ha hecho

- **Irlanda, Australia, Canadá y Estados Unidos** siguen con la plantilla
  genérica: no tienen estudio de precios y, por decisión del proyecto, no se
  abre un mercado sin él.
- **No hay contenido enlazado desde fuera** (backlinks): es trabajo de
  relaciones públicas y directorios, no de código.
- **No hay datos de Search Console** todavía: la medición empieza cuando el
  despliegue esté indexado.
