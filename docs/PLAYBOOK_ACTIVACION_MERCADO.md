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

## 2. Las herramientas

```bash
# Radiografía: estado de los 22 mercados y progreso de localización
python tools/radar_activacion_mercados.py
python tools/radar_activacion_mercados.py --mercado MX --muestra 0
python tools/radar_activacion_mercados.py --json radar.json

# Preparación y progreso de un mercado, apartado a apartado
python tools/preparar_mercado.py --mercado MX --apartados
python tools/preparar_mercado.py --mercado MX --apartados 02-04-01
python tools/preparar_mercado.py --mercado MX --estado
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

### B. Subconjunto con demanda (implementado)

La unidad ya no es el mercado sino **la ficha**. Un mercado puede anunciar diez
partidas sin anunciar las dos mil, y crecer por oleadas de contenido.

Cómo funciona, en una frase: **una ficha se anuncia si tiene texto propio
validado en `basedatos_partidas/datos/localizado/<CC>.json`**; su apartado se
anuncia cuando hay al menos tres; y la portada del catálogo, si hay alguna. El
resto del mercado sigue publicado, navegable y en `noindex`.

La decisión vive en una sola función, `precios_publicos.resto_indexable()`, y
de ella salen el `<meta robots>`, el `X-Robots-Tag` y el sitemap. Es la lección
del catálogo entero: cuando el meta decía «index» y la cabecera «noindex»,
Google aplicó la más restrictiva y el catálogo se cayó del índice sin que nadie
lo pidiera.

El registro tiene una guardia real, no una promesa: una entrada sin título, con
descripción de menos de 120 caracteres o con la descripción española copiada
(comparada también contra la variante de terminología local) **no enciende
nada**. Es un borrador.

#### El flujo de trabajo, comando a comando

```bash
# 1. Ver qué apartados tiene el mercado y cuántas partidas cada uno
python tools/preparar_mercado.py --mercado MX --apartados

# 2. Crear las entradas de los apartados elegidos (no pisa lo ya escrito)
python tools/preparar_mercado.py --mercado MX --apartados 02-04-01,12-05-03

# 3. Escribir el texto de cada partida en datos/localizado/MX.json
#    (cada entrada trae el texto español en "_origen" como referencia)

# 4. Ver el progreso: cuántas válidas, qué apartados ya se anunciarían
python tools/preparar_mercado.py --mercado MX --estado

# 5. Regenerar el artefacto del mercado (obligatorio si ya estaba encendido;
#    recomendable siempre, porque es lo que se sirve)
python tools/generar_precios_publicos.py

# 6. Comprobar la prosa y la puerta
python tools/radar_activacion_mercados.py --mercado MX
python -m pytest tests/test_mercados_incrementales.py tests/test_activacion_mercados.py
```

#### Cómo se escribe una entrada

La referencia es el vocabulario del país, no un sinónimo del español. Ejemplo
del patrón (México; el dato de precio no se toca, eso lo pone el catálogo):

```json
{
  "partidas": {
    "02.04.01.010": {
      "titulo": "Muro de block de concreto 15x20x40 asentado con mortero",
      "descripcion": "Suministro y colocación de muro de block hueco de concreto de 15x20x40 cm, asentado con mortero cemento-arena en proporción 1:5, incluyendo castillos y dalas de desplante y cerramiento, refuerzo horizontal, andamio, plomeo y limpieza del área. La cantidad se mide por metro cuadrado de muro terminado, descontando vanos mayores a 1 m². No incluye aplanado ni pintura.",
      "recursos": {
        "MT-BLOCK-15": "Block hueco de concreto 15x20x40 cm"
      },
      "revisado": "2026-11-06"
    }
  }
}
```

Reglas de estilo que se comprueban solas: el título describe el trabajo (no el
material), la descripción dice **qué incluye y cómo se mide**, y los nombres de
los recursos usan el término del país (block, castillo, dala, plafón, losa,
impermeabilizante acrílico).

Una regla que no comprueba ningún test y hay que respetar a mano: **en
`recursos` se renombran materiales y equipo (`MT-*`, `MQ-*`), no mano de obra
(`MO-*`)**. La tabla de tarifas horarias del mercado se construye agrupando los
recursos `MO-*` por nombre; si una ficha suelta llama «losetero» al oficial de
piso y otra sigue llamándolo «oficial de 1ª», el mismo oficio aparece dos veces
con medias tarifas y el mercado pasa de 16 oficios a 22. Los nombres de mano de
obra se cambian de una vez para todo el mercado, cuando se encienda entero.

#### Qué NO es localizar

- Cambiar «hormigón» por «concreto» en las 2.000 fichas con un buscar y
  reemplazar. Sube la similitud a 0,99 otra vez y no aporta nada al lector.
- Rellenar con sinónimos automáticos o traducción de máquina sin revisar.
- Encender un apartado con una sola ficha: por eso el mínimo es tres.

#### Estado de partida (06/11/2026)

México es el primer mercado con registro y va por su segunda oleada. **146 fichas
y 7 apartados completos**, escritos a mano uno por uno:

| Apartado | Fichas |
|---|---|
| `02-04-01` Paredes, muros y apertura de vanos | 20 / 20 |
| `02-01-01` Cimentaciones | 18 / 18 |
| `05-06-01` Losas y entrepiso | 21 / 21 |
| `10-05-01` Impermeabilización de áreas húmedas | 26 / 26 |
| `12-05-03` Pisos cerámicos y porcelanato | 6 / 6 |
| `12-08-01` Plafones continuos de tablaroca | 26 / 26 |
| `12-10-01` Pintura interior | 29 / 29 |

Son **154 URL anunciadas** (portada del catálogo + 7 apartados + 146 fichas) y
1.843 páginas que siguen en `noindex`. El mercado entero sigue apagado: crece
por oleadas y cada oleada se mide antes de la siguiente.

**Desplegado el 06/11/2026**: la oleada 0 (26 fichas, 2 apartados) en el PR #203 y
la oleada 1 (120 fichas, 5 apartados) en el PR siguiente. Verificado en
producción: `sitemap-precios-mx.xml` sirve exactamente las 154 URL,
`sitemap_index.xml` lista 8 hijos y las fichas localizadas responden 200 con la
prosa mexicana.

El `lastmod` del hijo de México ya usa la fecha más reciente entre el lote de
precios y el registro de texto propio (`precios_publicos.revision_de_mercado`),
así que un mercado que estrena prosa no sigue declarando la fecha del catálogo.

Queda un detalle conocido, para cuando se encienda el mercado entero: la mano de
obra se sigue llamando «Oficial de 1ª colocador de pisos» y «Ayudante», el nombre
base del catálogo. Se renombra de una vez para todo el mercado (ver la regla de
`MO-*` arriba), no ficha a ficha.

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
| MX | 2.171 URL | **a medio localizar** | 146 fichas / 7 apartados anunciados (154 URL); faltan 1.843 fichas |
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
- **No** se tocan los sitemaps ya enviados: funcionan y llevan desde el 23/10
  siendo los mismos. El de México es un hijo nuevo, no un cambio de los otros.
- **No** se reescribe la prosa con sinónimos automáticos del español: eso sube
  el jaccard a 0,99 igual y no aporta valor al lector del país.
- **No** se mezcla un encendido de catálogo con un cambio de títulos o de
  plantilla en la misma semana.

## 9. El título del hub de apartado (06/11/2026)

El 02/11 el hub con la segunda cifra de impresiones del sitio,
`/en-ie/prices/lifts-and-platform-lifts`, tenía 63 impresiones, posición 10,2 y
**cero clics**. Su título era «Lifts and platform lifts: unit prices in Ireland
(EUR)»: un listado que no promete ninguna cifra, compitiendo por «home lift
prices ireland» contra páginas que sí la dan.

La cifra ya estaba en el código, pero casi nunca llegaba al título: se escribía
con céntimos y con la moneda dos veces («40,00 EUR–264,00 EUR»), así que no cabía
en los 60 caracteres del resultado y se caía a la variante sin precio. El
resultado era que **solo el 22 % de los hubs de apartado llevaba un número en el
título**; hoy lo llevan el **88 %**.

Tres reglas, y las tres tienen test en `tests/test_titulos_apartado.py`:

1. **La cifra va sin céntimos y con la moneda una sola vez**: «40–264 MXN/m²»,
   no «40,00 MXN–264,00 MXN». `_numero_corto` redondea **hacia arriba**, para no
   prometer un precio más bajo del que hay en la ficha.
2. **El rango doble solo si el apartado es homogéneo** (≥70 % de las partidas en
   la misma unidad): sumar precios de m² y de unidad no da un rango, da un
   número inventado. Si no lo es, se anuncia el mínimo con «desde» y sin unidad.
3. **Si la dispersión pasa de 40 a 1, no hay rango**: «0,48–63,68 EUR» no
   informa de nada. Se anuncia el precio típico (la mediana) con «de media».

El orden de las variantes importa y es la mitad del arreglo: primero el nombre
completo con el país completo, después el mismo título con el país corto («the
US»), después con la primera cláusula del apartado, y solo al final la versión
sin cifra. Antes se saltaba de la variante completa a la que no da precio, que
es exactamente cómo se quedaron 1.200 hubs sin número.

Queda un detalle estético menor: la ficha del hub sigue mostrando su rango con
céntimos («de 22,18 EUR a 38,21 EUR»). Son dos redondeos del mismo dato y los
dos son ciertos, pero convendría unificarlos cuando se toque esa plantilla.

## 10. La línea base real y el título de la ficha (06/11/2026)

El informe de Search Console de 28 días (08/10 → 04/11) cambia el punto de
partida de todo lo anterior. No es un sitio estable: es un sitio en curva.

| | Primeros 7 días | Últimos 7 días | 28 días |
|---|---|---|---|
| Clics | 15 | 105 | 167 |
| Impresiones | 237 | 13.062 | 15.530 |
| Posición media | 36,5 | 25,0 | 25,7 |

El 84 % de las impresiones del periodo llegó en sus últimos siete días, y el
salto se ve el 28/10 (187 → 1.129 impresiones en un día). **La caída del CTR no
es un problema de títulos: es aritmética de ganar impresiones en posiciones
20-40.** Lo que hay que leer es por tramos y por tipo de página.

### Dónde están las impresiones y dónde los clics

| Tipo de página | Páginas | Impresiones | Clics | CTR | Posición |
|---|---|---|---|---|---|
| Ficha de partida | 746 | 9.504 (64 %) | 75 | 0,79 % | 22,5 |
| Hub de apartado | 169 | 2.927 (19 %) | 10 | 0,34 % | 31,9 |
| Landing de país | 46 | 1.708 (11 %) | 50 | **2,93 %** | 17,6 |
| Portada | 1 | 96 | 23 | 24,0 % | 5,0 |

| Posición | Impresiones | CTR |
|---|---|---|
| 1–3 | 105 | 4,76 % |
| 4–10 | 3.838 | 2,79 % |
| 11–20 | 2.956 | 0,98 % |
| 21–40 | 3.551 | 0,51 % |
| > 40 | 4.378 | 0,27 % |

Hay **6.500 impresiones en posiciones 11-40**. Ahí no hay que subir de posición:
hay que dejar de perder el clic que Google ya está sirviendo.

### Los mercados pequeños convierten, los grandes rankean

| Grupo | Impresiones | Clics | CTR |
|---|---|---|---|
| España + 5 angloparlantes | 12.460 (87 %) | 73 (48 %) | 0,59 % |
| 16 mercados hispanos | 1.787 (13 %) | **79 (52 %)** | **4,42 %** |

Ecuador: 12 clics con 54 impresiones (22 % CTR, posición 6). Los clics de esos
mercados vienen de las **landings de país** —que sí son indexables y rankean en
4-11—, no del catálogo. Dos casos sueltos: Chile rankea en 62 con 383
impresiones, y las URL `www.cotizat.online` del informe (1.418 impresiones, 35
clics) son residuo anterior al 301 de www al ápice, ya corregido en el borde y
en `HostCanonicoMiddleware`.

### El arreglo: la cifra en el título de la ficha

Mismo diagnóstico que en los hubs y misma solución. Antes del cambio,
**167 de 42.978 fichas (0,4 %) llevaban cifra en el título**; después,
**42.278 (98,4 %)**. Mediana 66 caracteres, ninguna por encima de 72, y en el
93-96 % de ellas (según el mercado) el precio entero entra antes del corte de
Google, que llega hacia los 60. El título se corta por el final, y el final es
el país: el número queda siempre a la vista.

Reglas, todas con test en `tests/test_titulos_ficha.py`:

1. `titulo_partida()` es pura: `(cc, título, unidad, pu, país, idioma) → título`.
2. La cifra va sin céntimos, moneda una vez y **redondeo hacia arriba**.
3. La unidad se escribe como se lee: «m²», no «m2» (la descripción también).
4. Orden de sacrificio: primero el país, después la unidad, después la primera
   cláusula del nombre («…, con pendiente hacia la coladera»), y **solo al
   final** el precio. El nombre de la partida es lo último que se toca porque es
   lo que coincide con la consulta.
5. La marca (`| CotizaT`) solo si el título resultante no pasa de 72 caracteres.

Un detalle que no es cosmético: las variantes con precio **no** se eligen con
`_titulo_meta`, porque ese ayudante prefiere lo que cabe en 60 caracteres y en
una ficha eso significa tirar el país teniendo sitio hasta 72. El país es lo que
distingue la misma partida en veintidós mercados, así que se conserva hasta 72 y
lo que Google recorta, si recorta, es la cola.

Lo que **no** se tocó, a propósito: el H1, el precio con céntimos del cuerpo y la
descripción larga. El cuerpo sigue dando la cifra exacta del descompuesto; el
título y la meta description dan la cifra redondeada, que es la que se compara.

## 11. El panel de los 14 días (Search Console)

Cada 14 días, tres números y nada más:

1. **Cobertura del sitemap de México** — «Rastreada: no indexada» por sitemap. Por
   debajo del 20 % indexado a las cuatro semanas, alarma.
2. **CTR de fichas y de hubs, por mercado.** Línea divisoria: fichas 0,79 %,
   hubs 0,34 %, landings 2,93 % (28 días hasta el 04/11).
3. **Posición media de los tramos 11-20 y 21-40**: si suben sin que suba el CTR,
   el problema es el título, no el ranking.

Línea base para comparar: **167 clics · 15.530 impresiones · CTR 1,08 % ·
posición 25,7**, con 12.460 impresiones en los seis mercados grandes y 1.787 en
los dieciséis hispanos.
