# Playbook: encender un mercado sin repetir el 23/10

Cómo se pasa de 6 mercados con catálogo anunciado a los 22 (Venezuela no tiene
matriz propia), **de uno en uno**, midiendo y sin volver a presentar a Google
miles de páginas que son el mismo texto con otro precio.

Origen del documento: el 21–22/10/2026 se anunciaron los 22 catálogos a la vez
(~40 000 URL) y en 48 h el sitio pasó a la 44 de posición media con 0 clics
(`docs/DIAGNOSTICO_TRAFICO_CERO_2026-10-23.md`). La medida de emergencia —dejar
el catálogo hispano en `noindex`— sigue vigente porque la causa de fondo sigue
vigente. Este playbook existe para retirarla mercado a mercado, con red.

---

## 1. El diagnóstico que faltaba: la prosa

Los precios de cada mercado son propios: `basedatos_partidas/salida/precios_recursos_<CC>.csv`
tiene matrices de coste-empresa investigadas país por país. **Lo que no es
propio es el texto**: el título, la descripción, los nombres de los recursos y
el nombre del apartado son los mismos que los de España en todos los mercados
hispanos.

Medido sobre las fichas que de verdad se publican (muestra estable de 200 por
mercado, `app/services/localizacion.py`):

| Mercado | Fichas | Jaccard vs ES | Texto idéntico | Estado |
|---|---:|---:|---:|---|
| US / GB / CA / AU / IE | 1.782–1.812 | **0,016** | 0,0 % | listo (traducido) |
| ES | 2.016 | — | — | referencia |
| MX | 1.989 | 0,978 | 53,5 % | calco |
| CO | 2.005 | 0,982 | 50,0 % | calco |
| PE | 2.001 | 0,983 | 53,0 % | calco |
| EC | 2.001 | 0,987 | 64,0 % | calco |
| CL / AR | 2.000 / 1.999 | 0,983 / 0,985 | 61,0 / 65,5 % | calco |
| DO, UY, PY, BO, PA, CR, GT, HN, SV, NI | ~2.000 | 0,975–0,988 | 51–65 % | calco |

Un `jaccard` de 0,98 significa que **el 98 % del vocabulario de la ficha es el
español**: cambia el número y la moneda, no el texto. Eso es exactamente lo que
Google evalúa como contenido a escala, y es lo que se anunció el 22/10.

Los mercados ingleses se salvan porque su prosa se traduce de verdad
(`services/traduccion.py`): 0,016 de parecido. No es que sean mejores: es que
tienen texto propio.

**Consecuencia operativa:** encender un mercado hispano no es añadir un código a
una tupla. Es escribir su prosa.

## 2. Las dos herramientas

```bash
python tools/radar_activacion_mercados.py            # radiografía de los 22
python tools/radar_activacion_mercados.py --mercado MX --muestra 0
python tools/radar_activacion_mercados.py --json radar.json
```

`tests/test_activacion_mercados.py` es la puerta: falla si un mercado de
`MERCADOS_FICHAS_INDEXABLES` está en estado `calco`. No se puede desactivar con
una variable de entorno; si alguien quiere encenderlo igualmente, tiene que
escribir el motivo en `EXCEPCIONES` dentro del test (mínimo 40 caracteres) y
pasar por revisión. La excepción caduca sola: si el mercado pasa a `listo`, el
test falla y pide borrarla.

Verificado: al añadir `MX` a `MERCADOS_FICHAS_INDEXABLES` en memoria, el test lo
rechaza con «53,5 % del texto es literalmente el español».

## 3. La unidad repetible: un mercado, siete pasos

| # | Paso | Quién | Qué significa «hecho» |
|---|---|---|---|
| 0 | **Línea base** | titular | CSV de GSC (país, páginas, consultas) de las 4 semanas previas + copia del sitemap. Sin esto no hay atribución |
| 1 | **Demanda** | titular | Las 10–15 consultas reales del país con volumen (GSC + SERP). Deciden **qué apartados** se localizan primero |
| 2 | **Prosa** | contenido | Título, descripción y recursos de esas fichas reescritos con el término, la unidad y la forma de medir del país |
| 3 | **Puerta** | código | `radar` da ese mercado en `listo` (jaccard < 0,50) o se enciende solo el subconjunto localizado (§4-B) |
| 4 | **Encendido** | código | Una línea: `MERCADOS_FICHAS_INDEXABLES` (o el registro de fichas localizadas, §4-B). Desplegar |
| 5 | **Medición** | titular | 4 semanas: *Páginas* por sitemap, posición media del país, clics. Sin cambios de SEO en paralelo |
| 6 | **Decisión** | titular | Sigue → siguiente mercado. Retrocede → revertir la línea y anotar por qué |

## 4. Dos modelos de encendido

### A. Catálogo completo del mercado (~2.000 fichas × 16 mercados = 32.000)

Es el objetivo final y el más simple de operar: un mercado, una línea.
Coste real: **32.000 fichas con texto propio**. A mano no se hace; con
traducción/adaptación asistida hay que revisar el vocabulario local (block vs
ladrillo, pañete vs revoque, castillo vs castillete) o se reintroduce el mismo
problema en español neutro.

### B. Subconjunto con demanda (recomendado para empezar)

Localizar primero los apartados con demanda demostrada —10–15 por mercado, unas
150–300 fichas— y anunciar **solo esas**. Crece con cada oleada de contenido y
nunca se presenta de golpe el catálogo entero.

Requiere un cambio de código que hoy no existe: la indexabilidad es por mercado
(`ficha_indexable(cc)`), no por ficha. La forma limpia es un registro de fichas
localizadas (`basedatos_partidas/datos/localizado/<CC>/…`) del que se deriven
sitemap, `hreflang` y `X-Robots-Tag`, con la misma disciplina que hoy tiene
`MERCADOS_FICHAS_INDEXABLES`: una fuente de verdad y tests que la cubren.

**Antes de elegir B hay que decidirlo como producto**, porque toca el servicio
`precios_publicos`, la generación de sitemaps y el `hreflang` del catálogo. No
se hace por la puerta de atrás.

## 5. Protocolo de cambio seguro (aplica a todo, no solo al catálogo)

1. **Solo aditivo en el sitemap.** Se añaden URLs; no se quitan en bloque.
2. **Un cambio estructural por semana**, y de una sola plantilla. Si se apila,
   no se sabe qué funcionó (regla escrita el 23/10, sigue valiendo).
3. **Un mercado a la vez.** `MERCADOS_FICHAS_INDEXABLES` es el interruptor:
   encender y apagar es la misma línea.
4. **Nunca anunciar `noindex`, redirecciones ni 404.** Ya hay tests.
5. **Línea base antes, medición después.** 4 semanas por mercado.
6. **Reversión primero, análisis después.** Si la posición media del país cae
   más de 30 % o *Rastreada: no indexada* se multiplica por tres, se revierte
   el encendido ese mismo día y se investiga con el sitio estable.
7. **Nada de envíos manuales de sitemap como palanca.** El fichero se relee
   solo; reenviarlo no acelera ni hunde nada.

## 6. Qué se mide por mercado (y cuándo se para)

| Señal | Dónde | Umbral de alarma |
|---|---|---|
| URLs del sitemap del mercado indexadas | GSC → Páginas, filtro por sitemap | < 20 % a las 4 semanas |
| Posición media del país | GSC → Rendimiento, filtro país | Empeora > 30 % |
| Clics del país | GSC → Rendimiento | 0 clics con > 500 impresiones |
| «Rastreada: no indexada» del mercado | GSC → Páginas | Se triplica |
| Impresiones totales del sitio | GSC → Rendimiento | Caída > 20 % sostenida |

Si se dispara una alarma: revertir el encendido, esperar 2 semanas, volver a
mirar. El patrón del 23/10 fue exactamente ese, y se detectó tarde.

## 7. Estado de los 23 mercados

| Mercado | Catálogo | Estado | Qué falta |
|---|---|---|---|
| ES | 2.201 URL | referencia | — |
| US, GB, CA, AU, IE | 1.956–1.987 URL | anunciado | — |
| MX | 2.171 URL | calco | prosa propia (4 guías ya hechas) |
| CO | 2.190 URL | calco | prosa propia (4 guías ya hechas) |
| PE | 2.185 URL | calco | prosa propia (4 guías ya hechas) |
| EC | 2.185 URL | calco | prosa propia (4 guías ya hechas) |
| CL, AR, DO, UY, PY, BO, PA, CR, GT, HN, SV, NI | ~2.180 URL | calco | prosa propia (3 guías) |
| VE | — | sin catálogo | no tiene matriz de precios en el repo |

Orden propuesto por el radar (determinista, no una preferencia):
**MX → CO → PE → EC →** resto. Los cuatro primeros van delante porque ya tienen
4 guías, nota de mano de obra y problema técnico propio: son los que menos
trabajo necesitan para cruzar la puerta. Del quinto en adelante el desempate es
ruido estadístico; ese orden lo debe decidir la demanda de GSC, no este número.

## 8. Lo que no se hace

- **No** se encienden los 16 mercados hispanos de golpe «para ver qué pasa».
- **No** se baja el umbral de 0,50 para que la puerta deje pasar un mercado.
- **No** se tocan los sitemaps actuales: funcionan (7 hijos) y llevan desde el
  23/10 siendo los mismos.
- **No** se reescribe la prosa con sinónimos automáticos del español: eso sube
  el jaccard a 0,99 igual y no aporta valor al lector del país.
- **No** se mezcla un encendido de catálogo con un cambio de títulos o de
  plantilla en la misma semana.
