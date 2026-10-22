# Mano de obra por país, catálogo JSON y el noindex que bloqueaba 47 000 URLs

Ronda 4 del trabajo de tráfico orgánico. Tres entregas, y un hallazgo que
estaba por encima de las tres.

---

## 0. El hallazgo: el catálogo estaba en `noindex` por cabecera

Mientras verificaba que las páginas nuevas fueran indexables encontré que
**todo el catálogo de precios** —`/mx/precios`, los 180 apartados y las 1 989
partidas de cada mercado— servía dos instrucciones contradictorias:

| Dónde | Qué decía |
|---|---|
| `<meta name="robots">` del HTML | `index,follow,max-image-preview:large` |
| Cabecera HTTP `X-Robots-Tag` | `noindex, nofollow, noarchive` |

Cuando las dos se contradicen, Google aplica la más restrictiva: la cabecera.
La causa era `app/seo.py`: `es_indexable()` tiene una lista blanca de rutas y
`/{cc}/precios…` nunca estuvo en ella. El sitemap anunciaba las 47 000 URL, el
canonical era correcto, el `Dataset` estaba bien… y todas estaban fuera del
índice.

Arreglado en `app/seo.py` con `_es_indexable_precios()`, que reconoce solo las
formas canónicas:

- `/{cc}/precios` y `/en-xx/prices`
- `/{cc}/precios/{apartado}` y `/{cc}/precios/{apartado}/{partida}`
- `/{cc}/mano-de-obra` y `/en-xx/labour-rates`
- `/{cc}/precios.json` y `/en-xx/prices.json`

Cualquier otra forma (un slug inventado, una ruta de cuatro segmentos) sigue
fuera de la lista, y de todos modos el router devuelve 404. Lo cubre
`tests/test_indexabilidad_catalogo.py`, que comprueba la **cabecera** en los 22
mercados y en las tres profundidades del catálogo, no el meta.

Este solo cambio vale más que las dos páginas nuevas: es la diferencia entre
47 000 URL indexables y 47 000 URL invisibles.

---

## 1. Coste horario de la mano de obra: `/{cc}/mano-de-obra`

**URL**: `/mx/mano-de-obra`, `/en-us/labour-rates` (canónica por idioma del
mercado, con 301 desde el alias cruzado).

**Qué dato aporta que no exista ya**. El descompuesto de cada partida lleva sus
líneas de mano de obra con nombre, unidad, rendimiento y precio. Agregando las
1 989 partidas del catálogo salen los 16 oficios del mercado con su coste
horario real, en la moneda del país, y en cuántas partidas aparece cada uno.
No es una encuesta ni una tabla salarial copiada: es el coste de cuadrilla que
el propio catálogo usa para construir sus precios.

Rendimiento: agregar el catálogo completo cuesta 0,1–0,4 s por país, con
`lru_cache`. La página no necesita materialización previa.

### Lo que la página dice (y lo que no)

| Mercado | Tarifas distintas |
|---|---|
| US | 16 |
| CA | 14 |
| GB | 11 |
| AU | 9 |
| ES | 8 |
| CO / MX | 7 |
| IE | 5 |
| GT / NI | 4 |
| AR, BO, CL, CR, DO, EC, HN, PA, PE, PY, SV, UY | 3 |

En 12 de los 22 mercados casi todos los oficios comparten tarifa (en DO,
albañil = electricista = pintor = 325,00 DOP/h). Por eso la página **no** se
vende como tabla salarial: el FAQ lo dice con todas las letras
(`«no es una tabla salarial»`, «no incluye impuestos», «no incluye tu
beneficio»), y hay un párrafo específico —`mo.lectura3`— que explica que donde
los oficios se separan de verdad es en el **rendimiento**, no en la hora.

El valor diferencial es otro: **cuánto cuesta la hora de cuadrilla en tu país y
en qué partidas pesa cada oficio**. Eso no lo publica nadie con datos de
catálogo y moneda local para 22 mercados.

### Contenido y datos estructurados

- Tabla completa de oficios con coste/hora, peso en el catálogo y capítulos en
  los que aparece.
- Tres párrafos de lectura (caro vs. barato, peso, tarifa común).
- «De dónde salen estas cifras»: metodología, qué incluye y qué no.
- 4 preguntas frecuentes + `FAQPage`, `BreadcrumbList`, `Organization`,
  `WebSite`.
- `hreflang` de los 22 mercados + `x-default`, canonical propio.
- Enlaces internos: catálogo, calculadora, 5 apartados del mercado, descarga
  JSON y selector de países.

### Dónde se enlaza

| Página | Enlace |
|---|---|
| Home de cada mercado (`/mx/`, `/en-us/`) | «Coste horario de la mano de obra de México» |
| Home global `/` | listado de los 22 mercados con su enlace de mano de obra |
| Índice de precios del país | bloque «Coste horario de los oficios de este mercado» |
| Cada apartado | enlace en la lista de enlaces del apartado |
| Cada partida | bloque nuevo «La mano de obra de esta partida», con el coste por hora de **cada** oficio que usa esa partida y enlace a la tabla del país |
| Sitemap del país | entrada propia, `priority 0.8`, `changefreq monthly` |

El bloque de la ficha de partida es el que más rinde: mete el nombre del oficio
y su precio por hora en la página que ya recibe búsquedas del tipo «precio de
la hora de albañil», con el dato exacto del catálogo.

---

## 2. Catálogo descargable: `/{cc}/precios.json`

`GET /mx/precios.json` (y `/en-us/prices.json`) sirve el catálogo completo del
mercado en JSON: capítulos → apartados → partidas, cada partida con unidad,
precio unitario redondeado y URL absoluta a su ficha. 535 KB para México,
0,26 s de generación, orden estable.

Sirve para tres cosas:

1. **Google Dataset Search** exigía una descarga real para el `Dataset`. Hasta
   ahora el `Dataset` se declaraba sin `distribution` «para no inventar una
   descarga que no existía». Ya existe: `jsonld_dataset()` apunta a ella.
2. **Citas**: quien reutilice el catálogo enlaza a la fuente.
3. **Tráfico de uso**: es el único contenido del sitio que una herramienta
   ajena puede necesitar de verdad.

Cabeceras: `application/json`, `Access-Control-Allow-Origin: *`,
`Cache-Control: public, max-age=3600, s-maxage=86400, stale-while-revalidate` y
un `Content-Disposition` con nombre de fichero. Está enlazado desde el índice
de precios de cada país y desde la página de mano de obra.

---

## 3. Cobertura

| Fichero | Qué cubre |
|---|---|
| `app/mano_obra.py` | Agregación, rutas, SEO, FAQ y contexto de la página |
| `app/templates/pais_mano_obra.html` | Plantilla única bilingüe (sin gemela `_en`) |
| `app/services/precios_publicos.py` | `exportar()`, `ruta_mano_obra()`, `ruta_json()`, `oficios_disponibles()` y la entrada del sitemap |
| `app/routers/precios_publicos.py` | Rutas de mano de obra y de la descarga JSON |
| `app/seo.py` | `_es_indexable_precios()` (el arreglo del noindex) |
| `app/seo_precios.py` | `distribution` del `Dataset`, `mano_obra_url` y `json_url` en los contextos |
| `app/cache_publico.py` | Sellado de las rutas nuevas |
| `app/locales/es.json` / `en.json` | 24 claves `mo.*` + 4 de enlaces cruzados (148 por idioma) |
| `tests/test_mano_obra.py` | 149 pruebas |
| `tests/test_indexabilidad_catalogo.py` | 31 pruebas |

Pruebas nuevas: **180**. Suite completa: **2 631 pasan, 12 omitidas** (6:00).

---

## 4. Lo que queda del backlog

| # | Idea | Estado |
|---|---|---|
| 3 | `lastmod` real por URL en los sitemaps | Pendiente |
| 5 | `/mx/precios.json` con `Dataset` | **Hecho** |
| 6 | «¿Cuánto cuesta construir una casa en {país}?» | Siguiente |
| — | Enlaces EN que faltan por mercado (`/en-us/remodeling` da 404) | Pendiente |
| — | `tools/indexnow.py` no envía los sitemaps de precios | Pendiente |
