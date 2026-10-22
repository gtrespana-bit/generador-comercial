# El espejo en inglés de los mercados hispanos

Ronda 7. La última pieza del mismo problema que las URL en inglés: **el mismo
documento accesible por dos direcciones, las dos indexables**.

---

## El caso

El conmutador de idioma promete «ver esta página en inglés». El resto de la
superficie pública ignora la cookie para poder cachearse en el CDN, así que la
única forma de servir la misma página en inglés es una URL propia:

```
/mx/apu                 → página de México, en español   (canónica)
/en-mx/unit-price-analysis → la misma página, en inglés
```

Ese espejo tiene sentido como utilidad. Como página indexable, no: no está en
el sitemap, no la enlaza nadie salvo el conmutador y su propio grupo de
`hreflang` apunta a **otra** URL (`en` → `/en-us/unit-price-analysis`). Es
decir, salía con `index,follow` y canónica a sí misma mientras el resto del
sitio declaraba que la versión inglesa de ese contenido vive en otro sitio.

Con 17 mercados hispanos eran 17 duplicados por cada tipo de página, generados
por el propio servidor.

## La decisión

**La URL se queda; la indexación no.**

| Señal | Antes | Ahora |
|---|---|---|
| `<meta name="robots">` | `index,follow,max-image-preview:large` | `noindex, follow` |
| `X-Robots-Tag` | ausente | `noindex, follow, noarchive` |
| `<link rel="alternate" hreflang>` | 26 entradas, ninguna hacia sí misma | ninguna |
| sitemap | ausente | ausente (igual) |

Se descartaron las otras dos salidas:

- **301 a `/mx/apu`** — rompe la función: la página destino ignora la cookie
  por diseño, así que el visitante que pidió inglés vería español. Un
  conmutador que no conmuta es peor que una URL sin indexar.
- **Canónica hacia `/mx/apu`** — legal pero frágio: Google puede desoír una
  canónica entre documentos en idiomas distintos. `noindex` no se desoye.

`follow` y no `nofollow`: los enlaces del espejo hacia el mercado sí deben
contar; el `nofollow` genérico de las páginas privadas no aplica aquí.

## Un fallo que salió al hacerlo

El conmutador a español desde un mercado inglés devolvía `/us/apu`, que desde
la ronda anterior es un **301 a `/en-us/unit-price-analysis`**: el botón «ES»
no cambiaba nada, rebotaba al inglés.

```
antes: /en-us/unit-price-analysis --(ES)--> /us/unit-price-analysis --301--> /en-us/...   ↺
ahora: /en-us/unit-price-analysis --(ES)--> /apu                                            ✓
```

Los mercados de habla inglesa no tienen versión en español: su equivalente es
la página genérica, sin país. La regla vive en `ruta_en_idioma()`, que además
ya traducía el slug del hub en los dos sentidos.

## Dónde está

| Fichero | Qué hace |
|---|---|
| `app/seo.py` | `MERCADOS_HISPANOS`, `es_espejo_de_idioma()`; el espejo deja de ser indexable |
| `app/security.py` | `X-Robots-Tag` con `follow` para el espejo |
| `app/routers/common.py` | globales `espejo_idioma()` y `robots_meta()` |
| `app/templates/_seo_head.html` | meta robots y omisión de `hreflang` |
| `app/i18n.py` | el conmutador a español sale del prefijo inglés |
| `tests/test_espejo_idioma.py` | 58 pruebas |

Suite completa: **2 809 pasan, 12 omitidas** (6:23). Sitemap: 234 URL, ninguna
del espejo.

## Lo que sigue abierto

- **IndexNow para el comparador**: `app/indexnow.py::urls_precios()` no emite
  las 34 URL del comparador internacional.
- **`lastmod` por URL en los sitemaps**: descartado mientras el catálogo tenga
  una sola fecha por mercado (una fecha falsa por URL es peor que ninguna).
