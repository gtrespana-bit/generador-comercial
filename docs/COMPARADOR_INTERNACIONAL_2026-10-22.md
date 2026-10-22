# Comparador internacional de precios: la misma partida en 22 mercados

Ronda 5. Después de publicar el catálogo por mercado (47 000 fichas), la mano
de obra por oficio y la descarga JSON, quedaba la pregunta que ningún
competidor responde con datos: **¿cuánto cuesta lo mismo en cada país?**

---

## El hallazgo que lo hace posible

Los 22 catálogos no son 22 listas independientes: se construyeron sobre la
misma estructura. **1 675 partidas comparten el mismo código exacto en los 22
mercados.**

```
12.05.03.010  Piso cerámico o porcelanato de formato estándar
              (México) · Pavimento cerámico (España) · Ceramic tile flooring (US)
```

Eso permite comparar **la misma unidad de obra**, no «un m² de algo parecido».
Es la diferencia entre un dato y una anécdota.

## Cómo se compara (y por qué así)

1. **Cesta común**: solo entran los códigos presentes en los 22 mercados con la
   misma familia de unidad. Se excluyen los precios alzados (`glb`), que no se
   pueden comparar por unidad.
2. **Normalización**: unidades imperiales → métricas (`sq ft` → m², `cu yd` →
   m³) y moneda local → USD con la tasa de referencia ya congelada en
   `app/services/tasa.py`.
3. **Índice**: para cada partida se calcula la mediana de los 22 precios; el
   índice de un mercado es la **mediana de sus cocientes** frente a esas
   medianas × 100. Mediana y no media: un precio mal cargado en un mercado no
   debe mover a los otros 21.

Resultado (100 = mediana internacional, 1 675 partidas, USD):

| # | Mercado | Índice | # | Mercado | Índice |
|---|---|---|---|---|---|
| 1 | Estados Unidos | 283,2 | 12 | Panamá | 101,4 |
| 2 | Australia | 278,2 | 13 | Guatemala | 82,6 |
| 3 | Irlanda | 270,3 | 14 | Argentina | 82,1 |
| 4 | Reino Unido | 249,4 | 15 | El Salvador | 79,8 |
| 5 | Canadá | 245,6 | 16 | República Dominicana | 79,7 |
| 6 | España | 185,1 | 17 | Perú | 75,5 |
| 7 | Costa Rica | 123,0 | 18 | Honduras | 70,6 |
| 8 | Uruguay | 115,9 | 19 | Nicaragua | 70,3 |
| 9 | Chile | 107,1 | 20 | Ecuador | 65,4 |
| 10 | Colombia | 102,3 | 21 | Paraguay | 62,7 |
| 11 | México | 102,2 | 22 | Bolivia | 43,5 |

Un detalle que la página no esconde: **Australia gana más partidas sueltas que
Estados Unidos (680 frente a 474)**, pero Estados Unidos tiene el índice más
alto porque es caro en casi todas. Por eso el índice es mediana de cocientes y
no un recuento de victorias. Está en el FAQ y en las pruebas.

## Antes de construir: un arreglo silencioso

`normalizar_unidad()` no conocía `sq ft`, `cu yd`, `ea` ni `lot`. El catálogo
estadounidense escribe las unidades así, de modo que **ningún precio de EE. UU.
se podía convertir**: 951 partidas en pies cuadrados y 60 en yardas cúbicas
habrían entrado en la comparación como si fueran metros. Añadidos los alias en
`app/services/unidades_precio.py` (`sq ft`→`ft2`, `cu yd`→`yd3`, `sq yd`→`yd2`,
`cu ft`→`ft3`, `ea`→`ud`, `lot`→`glb`). Sin eso, el índice de EE. UU. habría
salido unas diez veces por debajo y el error habría sido invisible.

## Páginas publicadas (34 URL)

| Ruta ES | Ruta EN | Contenido |
|---|---|---|
| `/precios-comparados` | `/en/prices-comparison` | Ranking de los 22 mercados + 10 partidas con mayor diferencia + metodología + FAQ |
| `/precios-comparados/{capítulo}` | `/en/prices-comparison/{chapter}` | 15 capítulos con cesta común: ranking del capítulo + todas sus partidas con mediana, rango y cociente |
| `/precios-comparados.json` | `/en/prices-comparison.json` | Los datos completos (690 KB) para reutilizar |

`Gestión de residuos y limpieza` (código 15) **no** se publica: no existe en los
cinco mercados de habla inglesa, así que no hay cesta común y su tabla estaría
vacía. Sin dato diferencial no hay URL, ni entrada en el sitemap.

## Dónde se enlaza

- **1 675 fichas de partida**: bloque «El precio de esta partida en cada país»
  con los 22 precios, el precio local de cada mercado y el enlace a su catálogo.
  Es la conversión de páginas de precio en páginas comparativas sin inventar un
  dato: el precio es el de cada catálogo, normalizado.
- **Pie de página** de todo el sitio (ES/EN).
- **Índice de precios de cada mercado**: «¿Te interesa cómo queda este catálogo
  frente a los otros 21 mercados?».
- **Página de mano de obra** de cada mercado.
- **Home global y home de mercado**.
- **Sitemap editorial** (34 URL con `hreflang` es/en y `x-default`).

## Rendimiento

La cesta completa se calcula una vez por proceso: **~1,2 s** la primera vez,
con `lru_cache(maxsize=1)`. Para que la primera visita a una ficha de precios no
pague ese coste, `lifespan` lanza un hilo que la precalcula al arrancar; si
falla, la página sigue sirviendo el resto sin el bloque. En caliente, la ficha
tarda 0,01–0,04 s.

## Transparencia

El punto débil real es el tipo de cambio: la tasa está congelada
(`TASAS_ACTUALIZADAS`) y cada catálogo tiene su propia fecha de revisión. La
página publica **las dos** fechas, y el FAQ dice que un salto cambiario mueve el
índice aunque la obra no haya cambiado. No se presenta como índice de coste de
vida ni como estadística oficial.

## Cobertura

| Fichero | Qué hace |
|---|---|
| `app/comparador.py` | Cesta, índice, ranking, capítulos, comparativa por partida, exportación |
| `app/templates/comparador_precios.html` | Plantilla única bilingüe |
| `app/routers/precios_publicos.py` | Portada, capítulos y JSON (el middleware de idioma reescribe `/en/...`) |
| `app/seo.py` | Indexabilidad + 34 entradas de sitemap con `hreflang` |
| `app/seo_precios.py` | Bloque comparativo en la ficha de partida |
| `app/services/unidades_precio.py` | Alias imperiales que faltaban |
| `app/cache_publico.py` | Sellado de las rutas nuevas |
| `app/main.py` | Precalentamiento en segundo plano |
| `tests/test_comparador_precios.py` | 42 pruebas |

Suite completa: **2 704 pasan, 12 omitidas** (6:33).

## Lo que queda

| Idea | Nota |
|---|---|
| «¿Cuánto cuesta construir una casa en {país}?» | Descartada por ahora: el catálogo no tiene partidas de vivienda completa (solo «repintado integral») y cualquier sistema de pesos sería una receta inventada. El comparador responde la misma intención con datos reales. |
| Enlaces EN que faltan por mercado | `/en-us/remodeling` da 404 mientras `/mx/remodelacion` existe |
| `lastmod` por URL en los sitemaps | Descartado: el catálogo tiene una sola fecha por mercado; inventar granularidad sería mentir al rastreador |
