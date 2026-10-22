# Rendimiento de rastreo y higiene del resultado de búsqueda

Ronda 8. Tres defectos medidos sobre las 234 URL del sitemap, no supuestos.

---

## 1. Las 92 URL más comerciales no se cacheaban

El sitio tiene el caché compartido bien resuelto: el idioma y el país salen de
la ruta, no de cookies, y el CDN sirve la página desde el borde. Con una
excepción que se comía justo la mitad comercial del sitemap.

El servidor aprovechaba el render para escribir la cookie de preferencia:

```python
resp.set_cookie("cotizat_pais", codigo, ...)      # landing de mercado y hubs
resp.set_cookie("cotizat_lang", lang, ...)        # cualquier URL /en-…
```

Y una respuesta con `Set-Cookie` **no se guarda en el CDN**: la regla de
`app/cache_publico.py` es explícita («si la respuesta fija cookies, no se
sella»), porque cachear una respuesta que escribe una cookie compartiría la
preferencia de un visitante con todos.

El resultado, medido:

| Superficie | Antes | Ahora |
|---|---|---|
| 23 landings de mercado (`/mx/`, `/en-gb/`…) | sin `Cache-Control` | selladas |
| 69 hubs de intención (`/mx/apu`, `/en-us/unit-price-analysis`…) | sin `Cache-Control` | selladas |
| URL del sitemap sin `Cache-Control` | **96 de 234** | **4 de 234** |

Las 4 que quedan son las dos excepciones documentadas y correctas: `/pago`
(los importes y métodos de pago dependen del país del visitante y acepta
`?msg=`) y `/soporte` (con sesión es el formulario dentro del panel).

**El arreglo** no renuncia a la preferencia: la escribe el navegador, en
`_cookies_publicas.html`, deduciendo el país de la ruta (`/en-mx/apu` → MX) y
el idioma del prefijo. El panel la lee igual, porque es una cookie normal. Con
JavaScript desactivado no se guarda la preferencia y nada más cambia: el país
sigue saliendo de la URL.

Para un buscador el efecto es directo: cada una de esas 92 URL se generaba
entera —catálogo, plantillas, JSON-LD— en **cada** petición, sin caché posible.

## 2. Enlaces internos que pasaban por una redirección

Del rastreo de 1 649 enlaces internos salieron cuatro enlaces que gastaban un
salto en cada visita, tres de ellos herencia del cambio de slugs de la ronda
anterior:

| Enlace | Dónde estaba | Destino |
|---|---|---|
| `/en-gb/apu` | guía `unit-price-analysis-uk` | `/en-gb/unit-price-analysis` |
| `/en-gb/software-presupuestos` | guía `construction-quote-template-uk` | `/en-gb/estimating-software` |
| `/en/apu/` | hub `/en-au/unit-price-analysis` | **dos** 301: slug y barra |
| `/en/` | botón «volver» de `/en/pago` | `/en-us/` |

El caso de `/en/apu/` era el peor: slug español y barra final, dos
redirecciones encadenadas en un enlace de la propia página.

## 3. Títulos y descripciones que se cortaban

- **Meta description**: `/calculadora` 171 y `/en/calculadora` 175 caracteres.
  Cortadas a 147 y 153.
- **Títulos**: 12 por encima de 70 caracteres, el peor de 82. Todos los
  «Plantilla de presupuesto de construcción en {país}, en {moneda}» pasan a
  «Plantilla de presupuesto en {país} ({moneda})»; el de República Dominicana
  pierde «de construcción» solo cuando no cabe; y la marca `| CotizaT` deja de
  añadirse cuando empuja el título por encima de 70.
- Quedan dos títulos en 71 (los capítulos más largos del comparador), que es el
  techo que fija la prueba.

## 4. Pares de idioma sin declarar

Las páginas estáticas tienen versión española e inglesa con contenido propio
(`/como-funciona` ↔ `/en/como-funciona`, `/pago` ↔ `/en/pago`, las cinco
legales). Ninguna emitía `hreflang`: para Google eran documentos sueltos. El
sitemap declaraba el par, pero sin `x-default`, y lo mismo pasaba en el
comparador y en los capítulos.

Ahora las tres superficies (HTML, sitemap de páginas estáticas, sitemap del
comparador y legales) declaran `es`, `en` y `x-default`, con el español como
predeterminado, igual que el resto del sitio.

## Cobertura

| Fichero | Qué hace |
|---|---|
| `app/templates/_cookies_publicas.html` | Escribe país e idioma desde la ruta |
| `app/routers/common.py` | Global `paises_codigos` para el script |
| `app/main.py` | No fija la cookie de idioma en la superficie cacheable |
| `app/routers/publico.py` | Landings y hubs dejan de fijar la cookie de país |
| `app/seo.py` | `hreflang` de páginas estáticas, `x-default` en sitemap y comparador |
| `app/calculadora.py` | Descripción a 158 caracteres |
| `app/seo_latam.py`, `app/seo_latam_contenido.py`, `app/seo_articulos_mercados_en.py` | Títulos largos |
| `app/templates/seo_hub_en.html`, `app/templates/pago_en.html`, `app/seo_reino_unido.py` | Enlaces a redirecciones |
| `tests/test_cache_comercial.py` | 25 pruebas |
| `tests/test_serp.py` | 20 pruebas |

Ajustadas por el cambio: `test_cache_publico.py`, `test_espana.py`,
`test_latam.py` (afirmaban que el servidor fijaba las cookies).

Suite completa: **2 854 pasan, 13 omitidas** (5:25).

## Lo que queda

| Idea | Nota |
|---|---|
| `/pago` en el caché | Depende del país del visitante; habría que mover la selección a la URL (`/pago/mx`) y eso sí crea URLs nuevas |
| Precios del catálogo por ciudad | El catálogo no tiene apertura municipal: inventarla sería contenido falso |
| `lastmod` por URL | Una sola fecha por mercado; una fecha por URL sería inventada |
