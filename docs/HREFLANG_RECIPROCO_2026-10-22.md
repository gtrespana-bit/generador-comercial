# El hreflang no era recíproco: 78 páginas con el grupo descartado

Ronda 9. Un solo valor mal puesto en una lista de 26, y el grupo entero deja
de valer.

---

## Qué pasaba

Cada página de tema declara sus 26 variantes (los 23 mercados, `es`, `en` y
`x-default`). El valor `en` apuntaba a **`/en-us/unit-price-analysis`**:

```html
<link rel="alternate" hreflang="en"    href="/en-us/unit-price-analysis">
<link rel="alternate" hreflang="en-US" href="/en-us/unit-price-analysis">
```

Dos etiquetas para la misma URL, y —lo importante— el hub inglés genérico
(`/en/unit-price-analysis`), que también declara el grupo, **no aparecía en
ningún grupo**, porque `/en-us/` no lo declaraba.

Google valida el conjunto: si A declara a B y B no declara a A, el grupo queda
incoherente y se descarta. Resultado medido sobre el sitemap:

| | Antes | Ahora |
|---|---|---|
| Páginas cuyo grupo no era recíproco | **78** | 0 |
| Destinos hreflang que redirigen | 0 | 0 |
| Páginas que no se incluyen en su propio grupo | 0 | 0 |

El efecto práctico: la versión inglesa genérica de los tres hubs —la que
compite por «estimating software», «unit price analysis» y «remodeling» sin
país— se presentaba ante Google como un documento suelto, y además obligaba a
descartar el grupo de las 25 páginas que sí la mencionaban.

## El arreglo

El inglés genérico y el mercado de Estados Unidos son **dos documentos
distintos con dos URLs distintas**:

```html
<link rel="alternate" hreflang="en"    href="/en/unit-price-analysis">
<link rel="alternate" hreflang="en-US" href="/en-us/unit-price-analysis">
```

`en` es «inglés, sin mercado»; `en-US` es el mercado estadounidense, que ya
tenía su propia entrada. La home conserva `en` → `/en-us/` porque `/en/`
responde 301 y una variante que redirige también se descarta.

El cambio está en `enlaces_hreflang()`, que es la fuente única del `<head>` y
del sitemap: no hay una segunda lista que se pueda desincronizar.

## Cobertura

`tests/test_hreflang_reciproco.py` recorre las 234 URL del sitemap y todos sus
destinos (sin repetir consultas) y falla si:

- un destino del hreflang no responde 200,
- un destino no declara hreflang,
- el destino no devuelve la página de origen,
- el conjunto de etiquetas no coincide,
- o una página no se incluye en su propio grupo.

Es la prueba que impide reintroducir el patrón: basta con devolver `en` a
`/en-us/` para que falle.

Suite completa: **2 861 pasan, 13 omitidas** (5:44).

## Lo que queda

| Idea | Nota |
|---|---|
| `/pago` por país (`/pago/mx`) | Los importes y métodos sí varían por país, pero sería contenido casi idéntico en 23 URL; hay que decidirlo como producto |
| `lastmod` por URL | Una sola fecha por mercado; inventarla por URL es peor que no tenerla |
| Apertura por ciudad en el catálogo | El catálogo no tiene datos municipales |
