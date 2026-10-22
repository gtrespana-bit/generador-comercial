# URLs en inglés: slugs ingleses y el prefijo interno que duplicaba el sitio

Ronda 6. Dos defectos que se tapaban entre sí, y los dos en los cinco mercados
de habla inglesa, que son los de mayor valor del sitio.

---

## 1. Una página en inglés con URL en español

Hasta esta ronda:

```
/en-us/apu              → página en inglés, slug en español
/en-gb/remodelacion     → página en inglés, slug en español
/en/software-presupuestos
```

El slug se ve en el resultado de búsqueda y en cada enlace que alguien comparte
por WhatsApp o LinkedIn. Una página que compite por «unit price analysis» no
puede llamarse `apu`: pierde relevancia en la URL y confunde a quien la lee.

Ahora el slug va en el idioma del mercado:

| Tema | Español | Inglés |
|---|---|---|
| software-presupuestos | `/mx/software-presupuestos` | `/en-us/estimating-software` |
| apu | `/mx/apu` | `/en-us/unit-price-analysis` |
| remodelacion | `/mx/remodelacion` | `/en-us/remodeling` |

Las URL antiguas **redirigen con 301**, no se apagan: el enlace entrante, el
histórico de cada página y lo ya indexado llegan igual. El mapa vive en
`TEMAS_EN` (`app/seo.py`) y de ahí salen la canónica, el sitemap, el `hreflang`,
el pie, el mapa del sitio y el conmutador de idioma. No hay una segunda lista.

El conmutador también traduce el slug en los dos sentidos (`/apu` →
`/en/unit-price-analysis` y de vuelta), así que cambiar de idioma es **un**
salto y no dos.

## 2. El prefijo interno era una URL pública

El middleware reescribe `/en-us/apu` a `/us/apu` para enrutar. El problema es
que `/us/apu` **también respondía 200 con su propia canónica**:

| URL | Antes | Ahora |
|---|---|---|
| `/us/apu` | 200, `canonical: /us/apu` | 301 → `/en-us/unit-price-analysis` |
| `/us/` | 301 → `/en-us/` | 301 → `/en-us/` |
| `/gb/remodelacion` | 200, canónica propia | 301 → `/en-gb/remodeling` |

Es decir: el mismo documento en dos URL, las dos indexables, sin `hreflang` que
las uniera. Contenido duplicado generado por el propio servidor, en el mercado
más competido. Ahora todo lo que cuelga de un prefijo interno (`us`, `gb`, `ca`,
`au`, `ie`) redirige en un solo salto a la URL pública, ya con el slug traducido
y conservando la query.

Los prefijos de los mercados de habla española (`/mx/`, `/co/`, `/es/`…) **no se
tocan**: ahí el prefijo sí es la URL pública.

## 3. Detalles que había que ajustar para que no quedara a medias

- **Caché compartida**: `_patrones()` construye la lista blanca desde
  `TEMAS`; al añadir slugs ingleses, su ruta interna (`/us/estimating-software`)
  quedaba fuera y el idioma pasaba a depender de la cookie. Añadidos.
- **Indexabilidad**: `es_indexable()` acepta los slugs nuevos y **rechaza** el
  prefijo interno, para que el diagnóstico no diga que hay dos páginas donde
  solo hay una.
- **Enlaces internos**: el pie y el mapa del sitio en inglés escribían
  `/en/apu` a mano; ahora usan `ruta_tema_en()` y no gastan un salto en cada
  rastreo.
- **Sitemap**: 76 URL de tema, todas canónicas, ninguna con slug español en
  mercado inglés.

## Cobertura

| Fichero | Qué hace |
|---|---|
| `app/seo.py` | `TEMAS_EN`, `slug_tema()`, `tema_desde_slug()`, `ruta_mercado()`, sitemap e indexabilidad |
| `app/seo_en.py` | `_ruta_en()` con el slug inglés |
| `app/routers/publico.py` | 6 rutas nuevas (genérica + por mercado) y el 301 a la canónica |
| `app/main.py` | 301 del prefijo interno, con traducción de slug en el mismo salto |
| `app/i18n.py` | El conmutador traduce el slug en los dos sentidos |
| `app/routers/common.py` | `ruta_tema_en()` para las plantillas |
| `app/cache_publico.py` | Los slugs ingleses entran en la caché compartida |
| `tests/test_urls_ingles.py` | 47 pruebas |

Ajustadas por el cambio: `tests/test_idioma.py` y `tests/test_mercados.py`
(esperaban las URL antiguas).

Suite completa: **2 751 pasan, 12 omitidas** (6:28).

## Lo que queda

| Idea | Nota |
|---|---|
| `hreflang` de `/en-mx/…` | Existe una variante de interfaz en inglés para mercados hispanos (`/en-mx/`), indexable y sin pareja declarada. O se le pone `hreflang` o se marca `noindex`; hay que decidir producto antes que SEO |
| `lastmod` por URL en los sitemaps | Descartado: el catálogo tiene una sola fecha por mercado |
| «¿Cuánto cuesta construir una casa en {país}?» | Descartado: el catálogo no tiene partidas de vivienda completa y cualquier reparto de pesos sería una receta inventada |
