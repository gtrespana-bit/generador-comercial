# Diagnóstico con datos reales de Search Console (02/11/2026)

Once CSV exportados de `cotizat.online`: rendimiento de 7 días (25–31/10),
consultas y páginas de 3 meses (muestra de 1000 filas cada una), cobertura
hasta el 22/10, problemas de indexación, países, dispositivos y apariciones
enriquecidas. Este documento sustituye a la hipótesis del 23/10
(`docs/DIAGNOSTICO_TRAFICO_CERO_2026-10-23.md`), que era razonable sin datos
pero no es lo que dicen los datos.

## 1. Lo que cambió respecto al diagnóstico anterior

| Hipótesis del 23/10 | Qué dicen los datos |
|---|---|
| «El sitio está hundido: 0 clics, posición 44» | **Ya no.** Los últimos 7 días: 49 clics, 4 975 impresiones, CTR 0,98 %, posición media 22,7 |
| «Desvalorización de sitio por el catálogo» | No hay ningún corte: las impresiones suben de ~30/día en septiembre a ~1 100/día desde el 28/10 |
| «El catálogo no se indexa y no sirve» | **El 76 % de las impresiones de los últimos 7 días viene del catálogo de precios**: 787 fichas de partida = 3 559 impresiones y 21 clics |

La serie diaria lo deja claro: 76 impresiones el 25/10 → 1 129 el 28/10 →
1 317 el 29/10. No es una caída recuperándose; es un **arranque**.

## 2. Dónde está el tráfico (7 días)

| Mercado | Impresiones | Clics | CTR | Posición media |
|---|---|---|---|---|
| España | 1 098 | 9 | 0,82 % | 24,6 |
| Reino Unido | 980 | 2 | **0,20 %** | 33,8 |
| Irlanda | 663 | 6 | 0,90 % | **16,5** |
| Australia | 526 | **0** | **0,00 %** | 27,5 |
| Estados Unidos | 351 | 1 | 0,28 % | 13,7 |
| Canadá | 252 | 1 | 0,40 % | 27,0 |
| Brasil | 68 | 0 | 0,00 % | 33,4 |
| Mercados hispanos pequeños (BO, NI, PA, DO, PY, SV, VE, CO, AR, UY) | ~430 | 12 | **2–6 %** | 4–20 |

**El patrón es nítido:** los mercados pequeños en español convierten a 2–6 % de
CTR porque están en el top 10 real. Los cinco grandes mercados ingleses +
España aportan el 79 % de las impresiones y producen 18 clics en total.

## 3. Las tres causas, por orden de impacto

### 3.1 El catálogo se indexa en fichas sueltas, no en hubs (la mayor)

| Tipo de URL | URLs | Impresiones | Clics | Posición media |
|---|---|---|---|---|
| `/{mercado}/prices/{apartado}/{partida}` (ficha) | 787 | 3 559 | 21 | 16,4 |
| `/{mercado}/prices/{apartado}` (hub) | 120 | 851 | 4 | **27,9** |
| `/{mercado}/` (landing) | 37 | 458 | 17 | 18,5 |

Las fichas rankean mejor que sus propios hubs. Eso deja al visitante en una
página de partida («Portón corredizo con automatismo — 490,78 EUR/ud en
España») sin camino claro al producto, y el sitio compite contra sí mismo.

**Y hay un dato que lo confirma**: `/en-ie/prices/lifts-and-platform-lifts` es
la segunda URL con más impresiones del sitio (63) y no tiene **ni un clic**.
Es un hub de apartado, está en posición 10,2 y su título es
«Lifts and platform lifts: unit prices in Ireland (EUR)». Un listado de precios
sin precio en el título y sin intención de compra. La consulta que la trae es
«home lift prices ireland», en posición 7,2 con 11 impresiones y cero clics.

### 3.2 Los títulos no tienen el número (CTR 0,00–0,28 %)

| Consulta | Impresiones | Posición | ¿Clic? |
|---|---|---|---|
| price of concrete per m3 ireland 2026 | 18 | **4,5** | **0** |
| home lift prices ireland | 11 | **7,2** | **0** |
| apu bolivia | 10 | **8,0** | **0** |
| linoleum flooring prices | 7 | 6,6 | 0 |
| access doors cost | 8 | 7,2 | 0 |

Hay 36 consultas en el top 10 con cero clics y 173 impresiones. No es posición:
es que el resultado no promete lo que se busca. En España el mismo tipo de
página sí gana («Portón corredizo con automatismo — 490,78 EUR/ud en España»),
porque el título **lleva el precio**. En inglés, la ficha de partida también lo
lleva («Water heater installation — 323.55 AUD/ea in Australia»), pero el hub
de apartado no.

### 3.3 Se anuncia más de lo que se indexa (cobertura)

| Fecha | Indexadas | Sin indexar |
|---|---|---|
| 20/09 | 51 | 104 |
| 22/10 | **75** | **210** |

En 285 URLs conocidas, solo 75 indexadas. Los motivos:

| Motivo | Páginas |
|---|---|
| Descubierta: actualmente sin indexar | 177 |
| Rastreada: actualmente sin indexar | 14 |
| Página con redirección | 10 |
| Error de redirección | 4 |
| Bloqueada por robots.txt | 3 |
| Excluida por noindex | 1 |

El sitemap declara 234 URLs no-catálogo + los sitemaps de precios de ES y los
cinco mercados ingleses. Con 177 «descubiertas sin indexar», Google sabe que
existen y no las considera prioritarias: es presupuesto de rastreo gastado en
volumen que no convierte.

## 4. La prueba del contenido duplicado

| Comparación | Similitud del texto |
|---|---|
| `/es/` vs `/mx/` | **98,1 %** |
| `/mx/` vs `/co/` | **98,6 %** |
| `/co/` vs `/ve/` | **98,4 %** |
| `/es/` vs `/ar/` | **98,4 %** |
| `/es/software-presupuestos` vs `/mx/software-presupuestos` | 87,8 % |

Cinco landings de mercado, 5 400 palabras cada una, con un 98 % de texto
idéntico. Google indexa una y descarta el resto; el resto compite entre sí por
la misma consulta.

## 5. La consulta comercial no existe

46 consultas con intención de compra («programa de presupuestos», «programa
para análisis de precios unitarios», «software de presupuestos»…): **121
impresiones y 0 clics**, en posiciones 44–87. Y la consulta de marca
(`cotizat`) trae 10 impresiones y 4 clics: el sitio no se descubre por marca,
se descubre por partidas.

**Esto no se arregla con más artículo de catálogo.** Se arregla con la página
de producto (landings) y con autoridad, que es lo que falta para competir
contra Sage, Presto, CYPE, Buildertrend…

## 6. Dos cosas que hay que mirar en Search Console

### 6.1 Brasil: 68 impresiones, 0 clics, 33,4 de posición

Se está mostrando en Brasil con **consultas en portugués** y el sitio no tiene
ni una página en portugués. Además aparece `Brasil` en `Países.csv`, lo que
sugiere que hay algún prefijo `/br` o que Google asocia las páginas hispanas a
Brasil. Revisar en Search Console → Rendimiento → filtro país Brasil → qué
páginas. Si son las hispanas, es ruido que consume rastreo.

### 6.2 `www.cotizat.online` sigue en el índice

37 URLs de la muestra son `www` con 270 impresiones y 9 clics. `vercel.json` y
`HostCanonicoMiddleware` ya hacen 301 al apex, así que es deuda antigua del
índice: se consolida sola, pero conviene comprobarla con Inspección de URLs.

## 7. Plan, por orden de rendimiento esperado

| # | Acción | Dónde | Por qué primero |
|---|---|---|---|
| 1 | **Los títulos de los hubs de apartado llevan el rango de precio** | `app/seo_precios.py` (hub) | 120 hubs, 851 impresiones, 4 clics. Hay hubs en posición 10 con cero clics; el título es la causa y se arregla sin tocar contenido |
| 2 | **Enlazar cada ficha hacia su hub y al presupuesto** | plantilla de ficha | 787 fichas reciben el 76 % de las impresiones y no llevan a ninguna parte útil |
| 3 | **Consolidar las landings de mercado duplicadas** | `app/seo.py` + política de indexación | 98 % de texto idéntico en 5 landings: una dueña por intención, el resto `noindex, follow` o contenido propio |
| 4 | **Recortar el sitemap a lo que se indexa** | sitemap | 177 «descubiertas sin indexar» es rastreo gastado |
| 5 | **Una página comercial fuerte** para «programa de presupuestos / APU» | contenido nuevo | 46 consultas, 0 clics: es donde está el cliente que paga |

Lo que **no** hay que hacer: seguir publicando mercados (el problema no es
cantidad, es que 5 landings sean la misma y que los hubs no prometan precio).

## 8. Cómo se mide el efecto

Repetir la descarga de los mismos CSV en 2–3 semanas y volver a correr:

```bash
python tools/analizar_gsc.py --carpeta ~/gsc
```

La herramienta lee los 11 tipos de archivo y responde: cobertura (indexadas vs
sin indexar), serie diaria y pico, países y dispositivos, problemas de
indexación, apariciones enriquecidas, consultas con impresiones y cero clics,
franja 5–25 y canibalización.

Criterio de éxito de las acciones 1 y 2, medido en el mismo CSV de páginas:

- los 120 hubs pasan de 4 clics a más de 15;
- el CTR de las URLs en posición ≤ 10 deja de ser 0 %;
- las fichas mantienen impresiones (no se pierden al cambiar el enlazado).
