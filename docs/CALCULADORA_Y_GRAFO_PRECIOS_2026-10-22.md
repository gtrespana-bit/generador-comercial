# Calculadora pública y grafo de afinidad — 2026-10-22 (ronda 3)

Tercera ronda sobre la auditoría. Aquí van las dos palancas que quedaban
marcadas como «con código, sin contenido nuevo» y de mayor retorno:

1. **Calculadora pública** (`/calculadora` · `/en/calculadora`): la puerta de
   entrada de mayor intención del sector, gratis y sin registro.
2. **Grafo de afinidad entre apartados**: 47.000 páginas que dejan de vivir en
   16 islas por país.

---

## 1. Por qué una calculadora (y por qué esta y no otra)

La consulta «cuánto cuesta X m² de Y» y «calculadora de presupuesto de obra»
son las de mayor intención del sitio. Hasta hoy, quien la tecleaba llegaba a
la landing (que vende el producto) o a una ficha de precio (que da el precio
unitario), pero no podía decir «tengo 20 m²» y obtener un número.

**Lo que se hizo:**

- `/calculadora` (ES) y `/en/calculadora` (EN), una sola plantilla bilingüe con
  el catálogo i18n (`t()`), como exige la convención del repositorio.
- Formulario GET sin JavaScript: país (22 mercados), tipo de trabajo
  (capítulos reales del catálogo del país, agrupados), cantidad y unidad.
- Resultado: mínimo, media y máximo del apartado para esa cantidad, más el
  reparto de materiales / mano de obra / maquinaria y la tabla de partidas con
  su precio unitario, su importe y su enlace a la ficha.

**Las cuatro decisiones que importan:**

1. **No hay recetas inventadas.** No se estima «una reforma de baño» con
   coeficientes que nadie puede comprobar. Se parte de un apartado real del
   catálogo del país y se multiplica su precio unitario por la cantidad. Si el
   dato no existe, no se inventa.
2. **Rango, no cifra única.** Un apartado agrupa partidas de precio distinto
   (azulejo estándar frente a porcelanato de gran formato). Se enseñan las tres
   cifras reales y la tabla que las produce: el mínimo es la partida más barata
   y el máximo la más cara, no un ±20 % decorativo.
3. **Funciona en los 22 mercados sin curación.** Los apartados, las unidades y
   los slugs salen del catálogo publicado de cada país. Estados Unidos y Reino
   Unido muestran pies cuadrados y slugs traducidos sin ninguna tabla de
   equivalencias. Hay un test por mercado que lo comprueba: un mercado nuevo no
   puede estrenar una calculadora rota.
4. **La canónica no lleva parámetros.** País, apartado, cantidad y unidad van
   en la query; la canónica es siempre `/calculadora` (o `/en/calculadora`). Un
   formulario no debe generar miles de URLs equivalentes.

**Ida y vuelta con el catálogo** (esto es lo que lo convierte en palanca SEO y
no solo en una herramienta): la calculadora enlaza a cada ficha de partida y
cada índice, apartado y partida enlazan a la calculadora con su país y su
apartado ya rellenados. La herramienta reparte autoridad a las 47.000 páginas
y las 47.000 páginas le dan autoridad a ella.

**Datos estructurados**: `WebApplication` con `isAccessibleForFree` y oferta a
0. Es honesto (la herramienta es gratis y no pide registro) y es lo que permite
que Google la trate como aplicación y no como una página de texto más.

---

## 2. Grafo de afinidad: de 16 islas a un silo

Cada apartado enlazaba solo con los de su propio capítulo. La autoridad de
47.000 páginas se quedaba repartida en 16 islas por país y «impermeabilizar»
nunca conectaba con «alicatar», que es como se piensa una obra de verdad.

**Cómo funciona:**

- `_AFINIDAD_CAPITULOS` (en `app/seo_precios.py`) declara qué capítulos
  acompañan a cada uno en una obra real: cimentación ↔ estructura ↔ fábricas,
  aislamiento ↔ cubiertas ↔ revestimientos, instalaciones ↔ equipamiento,
  demoliciones ↔ residuos. Los códigos 01–18 significan lo mismo en los 22
  mercados, así que el mapa es único (no 22 tablas que se desincronizan).
- Cada apartado recibe **3 enlaces a otros capítulos**, elegidos de forma
  determinista por el hash de su slug: cada apartado reparte su enlace a un
  tramo distinto del capítulo afín en vez de que los 2.000 apunten a los mismos
  tres. Estable entre peticiones y despliegues: nada de enlaces aleatorios que
  confundan al rastreador.
- Bloque visible «Obras que van con esta», con el nombre del capítulo de cada
  destino.

**Verificado con tests** (`tests/test_grafos_precios.py`, 32 pruebas): los
capítulos afines existen en los 22 mercados, ningún enlace vuelve al propio
capítulo, la selección es determinista, se reparte entre hermanos y todos los
destinos responden 200.

---

## 3. Efecto sobre la estructura del sitio

| Antes | Ahora |
|---|---|
| 0 enlaces de la home al catálogo | 22 índices enlazados |
| Guías y hubs sin enlace a precios | 6 enlaces por página |
| 16 islas por país en los apartados | 16 capítulos conectados por afinidad |
| Ninguna forma de usar un precio sin registrarse | Calculadora con resultado real |
| `/colombia`, `/calculo`… 404 | 41 alias 301 + calculadora |

---

## 4. Lo que sigue

Del backlog de `docs/PALANCAS_TRAFICO_POR_PAIS_2026-10-22.md` ya están hechas
las filas 1 (puerta de entrada), 2 (grafo) y parte de la 6 (breadcrumb en
precios vía calculadora). Quedan:

| # | Palanca | Nota |
|---|---|---|
| 3 | `lastmod` real por URL en el sitemap | Necesita una fuente de fecha por guía; hoy no existe |
| 4 | Página por oficio y país | `/mx/precios/oficios/electricista`, desde los capítulos reales |
| 5 | Versión JSON del catálogo | `/mx/precios.json` — Dataset Search de verdad y que otros te citen |
| 7 | «¿Cuánto cuesta construir una casa en {país}?» | La consulta grande del sector; exige modelo por m² con supuestos explícitos |

Y lo que no se resuelve con código: enlaces externos, Search Console y una
línea base de medición por clúster antes de crear más superficie.

---

## 5. Archivos

```
app/calculadora.py            lógica, contexto, JSON-LD (nuevo)
app/templates/calculadora.html  herramienta bilingüe (nueva)
app/routers/publico.py        ruta /calculadora
app/seo.py                    indexable + sitemap (0.8, weekly)
app/seo_precios.py            grafo de afinidad, ruta_calculadora(), calc_url
app/cache_publico.py          /calculadora y /en/calculadora en la lista blanca
app/templates/_nav*.html      enlace en el menú (ES y EN)
app/templates/_footer_publico*.html, mapa_sitio*.html   enlaces
app/templates/pais_precio{s,_apartado,_partida}.html     CTA a la calculadora
app/locales/{es,en}.json      cls. calc.* (36) y precios.relacionadas.* (2)
app/static/css/public.css     estilos de la herramienta
tests/test_calculadora.py     32 pruebas
tests/test_grafos_precios.py  32 pruebas
```
