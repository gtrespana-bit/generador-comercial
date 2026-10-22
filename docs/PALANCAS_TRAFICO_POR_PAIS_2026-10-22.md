# Palancas de tráfico orgánico por país — 2026-10-22 (ronda 2)

Continuación de `docs/AUDITORIA_SEO_2026-10-22.md`. Aquí va lo aplicado en esta
ronda y, sobre todo, **el inventario de lo que queda**, separando lo que se
resuelve con código de lo que exige contenido o datos nuevos.

Contexto: 22 mercados publicados, 47.148 URLs, 200 en el sitemap principal.

---

## 1. Lo aplicado en esta ronda

### 1.1 Alias de país (`/colombia` → `/co/`)

Un 404 no transfiere autoridad; un 301 sí. Y la gente —y los enlaces viejos,
los correos y los documentos— escribe `/colombia`, `/mexico`, `/reino-unido`,
`/estados-unidos`. Todas devolvían 404.

- `app/alias_paises.py`: nombre de país (con y sin acento, en los dos idiomas)
  → código ISO. 41 alias sobre los 22 mercados.
- Un solo salto garantizado: `/colombia` → 301 → `/co/` → 200, sin escala
  intermedia.
- Con sección: `/mexico/precios` → `/mx/precios`,
  `/estados-unidos/precios` → `/en-us/prices`. Si la sección no existe en ese
  mercado (`/mexico/blog`), cae a la portada del mercado, **nunca** a un 404.
- No se anuncian en el sitemap ni se enlazan desde el sitio: son una red de
  recuperación para tráfico que llega de fuera.

### 1.2 Barra final: de 307 a 301

`/mx/precios/` respondía **307** (temporal) porque era Starlette quien
resolvía. Un 307 le dice a Google «esto es provisional», así que conserva las
dos URLs compitiendo entre sí. Ahora el middleware responde 301 a la forma que
declaran la canónica y el sitemap. Afecta a cualquier enlace externo con
barra final, en los 47.148 precios y en todo lo demás.

### 1.3 El catálogo de cada país como `Dataset`

Canal gratuito que el sector de la construcción casi no usa: **Google Dataset
Search**. La página cumple los requisitos de verdad (datos publicados,
cobertura geográfica, fecha de revisión, autor identificable, acceso libre),
así que se declara como `Dataset` con `spatialCoverage`, `temporalCoverage`,
`variableMeasured` y licencia. **No** se declara `distribution` porque no hay
fichero de descarga: sería inventar una descarga que no existe.

### 1.4 FAQ local real en los 22 índices de precios

Las cinco preguntas que de verdad se hace quien busca «precios de construcción
en X», respondidas con datos que cambian de un mercado a otro:

| Dato que diferencia la respuesta | Ejemplo |
|---|---|
| Nombre legal del impuesto | IVA (MX, CO, ES, AR…), ITBIS (DO), ISV (HN), ITBMS (PA), IGV (PE), GST/HST (CA), Sales tax (US) |
| Tipo aplicable | 16 % MX · 18 % DO · 7 % PA · 13,5 % IE · 5 % CA |
| Número de partidas, apartados y capítulos | 1.989 / 180 / 16 en México |
| Moneda y mes de revisión | MXN, septiembre de 2026 |

Son ~520 palabras de texto **único por país** (y no relleno: es la ficha
técnica del catálogo), visibles en `<details>` y declaradas en `FAQPage`. El
texto visible importa: un schema sin su texto en la página es markup huérfano.

### 1.5 `/pago`: oferta comprable real

Es la única página del sitio con algo que comprar, y no lo declaraba como
producto. Ahora lleva `Product` + `AggregateOffer` con los importes reales de
los planes (9,99 US$ mensual / 89 US$ anual, USD, `InStock`). Eso habilita el
precio en el resultado de búsqueda, que es la diferencia entre un clic y un
salto a la competencia.

Se mantiene la decisión de la ronda anterior: **el catálogo de precios no
declara `Product`/`Offer`**, porque el precio publicado es una referencia, no
una oferta comprable. Hay un test que lo fija en ambas direcciones.

### 1.6 `og:locale:alternate` sin el idioma propio

Cada página repetía su propio idioma como «alternativo» (23 entradas donde
debían ser 22). Corregido: ahora son 22 y sin duplicados.

---

## 2. Lo que queda, por orden de retorno esperado

### Con código, sin contenido nuevo (se puede hacer ya)

| # | Palanca | Por qué mueve tráfico | Coste |
|---|---|---|---|
| 1 | **`/precios` genérico** y `/calcular`/`/calculadora` como puertas de entrada | Son las dos consultas más tecleadas del sector; hoy dan 404. Requieren decidir el destino (¿selector de país? ¿calculadora real?) | 1–2 días |
| 2 | **Enlaces contextuales entre apartados de la misma obra** («quien presupuesta aislamiento también necesita tabiquería») | Hoy los enlaces entre apartados son solo por capítulo. Un grafo por afinidad de obra reparte autoridad entre los 2.000 apartados de cada país | 2–3 días |
| 3 | **`lastmod` real por URL** en el sitemap principal | Hoy las 200 URLs comparten una fecha; Google usa `lastmod` para decidir recrawl. Necesita una fuente de fecha por guía (hoy no existe) | 1 día |
| 4 | **Página por oficio y país desde el catálogo** (`/mx/precios/oficios/electricista`) | Cruza el catálogo con la demanda de oficio; saldría de los capítulos reales, sin inventar | 3–5 días |
| 5 | **Versión JSON del catálogo** (`/mx/precios.json`) | Abre la puerta a Dataset Search de verdad, a agentes/LLM y a que otros sitios te citen como fuente | 2 días |
| 6 | **`BreadcrumbList` visible** en precios ya existe en schema; falta el mismo en las guías de mercado | Coherencia con el schema y mejor CTR en SERP | 0,5 días |

### Con contenido nuevo (código + redacción; aquí está el techo)

| # | Palanca | Por qué es la que más mueve | Coste |
|---|---|---|---|
| 7 | **«¿Cuánto cuesta construir una casa en {país}?»** | Es *la* consulta del sector y hoy no hay ninguna página que la responda por país. Requiere un modelo de coste por m² defendible (partidas reales del catálogo + supuestos explícitos) | 1 semana de redacción + datos |
| 8 | **Comparativas entre mercados** («mismo trabajo en México y en Colombia») | Dato que solo tú tienes (dos catálogos con la misma clave). Riesgo: puede leerse como contenido generado si no se cuida | 1 semana |
| 9 | **Guías de oficio por país** (fontanería, electricidad, albañilería) | Long-tail de altísima intención y poca competencia en LatAm | 1 semana por país |
| 10 | **Casos de obra reales con números** | Es lo que enlazan los medios y los colegios profesionales; sin esto, el punto 4 de la ronda anterior sigue siendo el límite | continuo |

### Fuera del código (no se resuelve programando)

- **Backlinks temáticos.** Sigue siendo el techo real. Un 301 recupera
  autoridad que ya existía; no la crea.
- **Search Console / Bing.** Sin medir, las decisiones de las filas 7–10 son
  apuestas.
- **Reseñas y perfiles** (Google Business Profile si hay trato local, directorios
  de software de construcción).

---

## 3. Regla que se mantiene

Ninguna URL nueva sin un dato que no exista ya en otra página. Los 22
catálogos lo cumplen (48–77 % de texto propio entre mercados). Las filas 4, 7,
8 y 9 de arriba solo se implementan si aportan ese diferencial; si no, se
quedan fuera aunque el volumen de búsqueda parezca tentador.
