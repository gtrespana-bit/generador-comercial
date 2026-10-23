# Diagnóstico: cero visitas tras enviar el sitemap nuevo (23/10/2026)

Contexto: entre el 19 y el 22/10 se amplió la superficie indexable (catálogo de
precios por país) y se envió el sitemap nuevo. Desde entonces Search Console
muestra 0 visitas al día. Este documento fija **qué está comprobado**, **qué
falta comprobar** y **en qué orden**, para no seguir tocando cosas a ciegas.

> **Veredicto (23/10 por la noche).** Con los datos de Search Console delante
> —74 impresiones en el día, posición media 44, **0 clics**, **ni una ficha de
> precios indexada** y **ninguna acción manual**— el sitio no está bloqueado:
> está **hundido**. La causa más probable es haber publicado y anunciado de
> golpe ~40 000 URL casi idénticas (los 17 mercados hispanos son el mismo
> texto con otra moneda). Medida aplicada: el catálogo solo se anuncia en
> España y los cinco mercados ingleses; el resto publica con `noindex, follow`
> pero sigue navegable. Ver **sección 5**.

## 1. Lo que ya está verificado (23/10, 19:50 UTC, desde fuera)

| Comprobación | Resultado |
|---|---|
| `GET /` | 200, `x-vercel-cache: HIT`, `server: Vercel` |
| `<meta robots>` de `/` | `index,follow,max-image-preview:large` |
| Canónica de `/` | `https://cotizat.online/` (autorreferente, apex) |
| GA4 en el HTML | `gtag/js?id=G-013NT3ZTHP` presente, con `nonce` |
| `GET /es/precios` | 200, indexable, canónica autorreferente |
| Ficha de partida (`/es/precios/…/alarma-de-asistencia-de-bano`) | 200, `<title>` propio, canónica autorreferente |
| `robots.txt` | `Allow: /`, sin `Disallow: /`, anunciaba índice + 23 sitemaps de precios (antes de la sección 5) |
| `sitemap_index.xml` | 200, 23 hijos; los hijos responden 200 (antes de la sección 5) |
| `/healthz` | `{"ok": true}` |
| `site:cotizat.online` en Google | **devuelve resultados y paginación** (varias páginas de resultados, mercados `en-ie`, `do`, `en-gb`…) |
| `site:cotizat.online` en DuckDuckGo | devuelve resultados (portada, `en-us`, `en-gb`, legales, planes) |
| GSC, día de ayer | **74 impresiones**, **posición media 44**, **0 clics** |
| GSC, indexación del catálogo | **ni una** URL de precios indexada |
| GSC, acciones manuales | **ninguna** |

**Conclusión de esta parte:** no hay `noindex` masivo, ni canónica cruzada, ni
`robots.txt` bloqueando, ni el `X-Robots-Tag` restrictivo que ya tuvo el catálogo
en el pasado. El sitio, tal como lo ve un lector de contenido, es indexable hoy.
Y, sobre todo: **Google sigue teniendo las páginas en el índice**. No hubo
eliminación del sitio ni bloqueo total del rastreo.

Con eso, el diagnóstico se estrecha: si el sitio está indexado y no recibe ni
clics ni visitas, lo que ha caído es la **posición**, no la indexación.

**Lo que no se puede ver desde fuera:** cómo responde el borde de Vercel al
`User-Agent` de Googlebot, qué dicen Search Console y Vercel, y si GA4 está
recibiendo datos. Ahí está la causa.

## 2. Orden de comprobación (de más probable a menos)

### 2.1 ¿Es medición y no tráfico? (5 minutos, primero)

Search Console publica con **2–3 días de retraso**: si el sitemap se envió el
21–22/10, los días afectados aún pueden no estar cargados.

- GSC → **Rendimiento** → rango de **28 días**. Si la línea se corta a cero los
  dos últimos días pero hay datos anteriores, es retraso, no caída.
- GSC → selector de propiedad: confirmar que se está mirando la propiedad que
  tiene histórico (`cotizat.online` apex, no `www` ni una `sc-domain:` nueva,
  que empieza vacía).
- GA4 → **Tiempo real** con una visita propia. Si apareces, el sitio recibe
  tráfico y el problema es de medición o de origen (Google), no de servidor.
  (Comprobado: **sí aparece**. Analítica, CSP y servidor están bien; lo que
  falta es el tráfico que venía de Google.)
- GSC → **Rendimiento** → pestaña **Páginas**: ¿la caída es en *todas* las URL o
  solo en las nuevas `/xx/precios/...`? Son dos averías distintas:
  todas = acción o bloqueo global; solo las nuevas = las fichas no rankean.

**El discriminador que separa las dos causas grandes** (GSC → Rendimiento,
gráfico de 28 días, con el conmutador *Clics / Impresiones*):

| Lo que se ve | Qué significa | Dónde se confirma |
|---|---|---|
| Impresiones a cero | el sitio **salió del índice** | Acciones manuales, Estadísticas de rastreo, `site:cotizat.online` en Google |
| Impresiones sí, clics cero | el sitio **sigue indexado** pero hundido en posiciones | Rendimiento → Posición media (si saltó a >20, es desvalorización de calidad) |

Este segundo caso **ya está comprobado a medias**: `site:cotizat.online` en
Google devuelve resultados y paginación, así que el índice conserva las páginas.
Falta el número que lo cierra: en **Rendimiento**, ¿las impresiones siguen
existiendo mientras los clics se han ido a cero? Si sí, es una
**desvalorización a nivel de sitio** (ver sección 4).

### 2.2 ¿El borde está bloqueando a Googlebot? (la causa nº 1 de un cero seco)

Un WAF, la protección de bots de Vercel, «Attack Challenge Mode» o
«Deployment Protection» devuelven 401/403/challenge al rastreador mientras el
navegador del titular sigue viendo el sitio perfecto. Google, al no poder
rastrear, retira las páginas en días.

- Ejecutar la herramienta (sección 3): la **sonda Googlebot** compara la
  respuesta al `User-Agent` de Googlebot con la del agente propio.
- **Sin terminal:** GitHub → pestaña **Actions** → *Auditoría SEO de
  producción* → **Run workflow** → rama `arena/fbaff9ad-generador-comercial`
  → *Run*. El informe aparece en el resumen de la ejecución (sección 3.1).
- El veredicto definitivo, y el único que dice la verdad sobre Google: GSC →
  **Inspección de URLs** → pegar `https://cotizat.online/es/precios` →
  **Probar URL publicada**. Ahí se ve la respuesta HTTP *que recibe Google* y
  si la página se recupera. Un 403/challenge, o «no se pudo recuperar», es la
  causa.
- A mano, desde el portátil:

  ```bash
  curl -sI -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
       https://cotizat.online/ | head -20
  ```

  Debe dar `200` y `server: Vercel`. Un `403`, `429`, `401` o una página
  «Vercel Security Checkpoint» es la causa.
- GSC → **Inspección de URLs** → *Probar URL publicada*: mira «Respuesta HTTP»
  y «Página recuperada». Si Google no la recupera, ahí se ve.
- Vercel → **Firewall / Observability**: buscar peticiones 401/403/429 con
  `Googlebot` en el `User-Agent`, y revisar si se activó *Deployment
  Protection*, *Bot Protection* o un *challenge* al cambiar el dominio o el
  despliegue.

### 2.3 Acciones manuales y seguridad

GSC → **Acciones manuales** y **Problemas de seguridad**. Una acción por
«contenido generado a escala» o «páginas engañosas» retira el sitio entero y no
avisa por correo en todos los casos.

### 2.4 Cobertura del índice

GSC → **Indexación → Páginas**. Lo que importa es **qué categoría ha crecido**
estos días:

- *Rastreada: actualmente no indexada* en decenas de miles → expansión
  desproporcionada (ver 2.5).
- *Excluida por noindex* → un cambio de plantilla está marcando páginas.
- *Error del servidor (5xx)* o *Error de red* → el rastreo está fallando ahora.

### 2.5 La expansión del sitemap como hipótesis SEO

**No explica un cero en 48 h** (una desvalorización de calidad es gradual, no
un corte seco), pero sí es el riesgo abierto más grande del sitio:

- 23 mercados × ~3 000 partidas ≈ 47 000 URL de ficha. En los mercados
  hispanos el texto es casi idéntico (misma terminología traducida) y solo
  cambian moneda y precio: **casi duplicados a escala**, que es exactamente el
  patrón que Google llama *scaled content abuse*.
- Enviar 47 000 URL de golpe compite por un presupuesto de rastreo limitado con
  las páginas que sí convierten (landings, hubs, guías, comparador).
- Alternativas a decidir **con datos**, no ahora: mantener en el sitemap el
  índice editorial y dejar que las fichas entren por enlazado interno; o
  indexar solo los **apartados** (hubs) y las partidas con demanda demostrada;
  o dejar el catálogo completo pero sin anunciarlo en bloque. Antes de elegir,
  mirar en GSC la proporción de «Rastreada: no indexada» por carpeta.

## 3. La herramienta de auditoría (actualizada)

`tools/auditar_seo_produccion.py` ahora cubre justo lo que faltaba para este
caso. Funciona sin instalar nada (solo biblioteca estándar de Python).

### 3.1 Sin terminal: desde GitHub

`.github/workflows/auditoria-seo.yml` ejecuta la auditoría en un runner de
GitHub y deja el informe escrito en el resumen:

1. Repositorio → **Actions** → *Auditoría SEO de producción*.
2. **Run workflow** → rama `arena/fbaff9ad-generador-comercial` → *Run*.
3. Al terminar, abrir la ejecución: el bloque «Auditoría SEO de
   https://cotizat.online» es el informe completo, con una línea `FALLO …` por
   cada comprobación incumplida.

También queda programada a las 06:00 UTC de cada día (eso solo se activa
cuando el fichero está en la rama principal).

> **Nota:** el fichero del workflow no se pudo empujar al repositorio desde el
> entorno de desarrollo (la integración de GitHub de ese entorno no tiene
> permiso `workflows`). Si no aparece en la pestaña *Actions*, créalo una vez a
> mano en GitHub: **Add file → Create new file**, nombre
> `.github/workflows/auditoria-seo.yml`, pegar el contenido del fichero y
> confirmar en la rama. A partir de ahí ya se puede lanzar desde la interfaz.

### 3.2 Desde un equipo con Python

Debe ejecutarse desde una máquina con acceso al dominio (el entorno de este
repositorio no tiene salida a internet hacia `cotizat.online`):

```bash
python tools/auditar_seo_produccion.py --muestra 25
python tools/auditar_seo_produccion.py --muestra 0        # todas (lento)
python tools/auditar_seo_produccion.py --sin-googlebot    # sin la sonda
```

Qué comprueba y por qué:

| Comprobación | Qué detecta |
|---|---|
| **Sonda Googlebot** (nueva) | 401/403/429 y páginas de verificación del borde, comparadas con el agente propio |
| **Descubrimiento por índice** (nueva) | Audita también `sitemap-precios-{cc}.xml`; antes solo miraba `sitemap.xml` y dejaba fuera las 47 000 URL nuevas |
| **Muestreo repartido** (nueva) | Con 47 000 URL no se pueden pedir todas: la muestra salta de forma uniforme en vez de quedarse con las primeras N |
| **Límite de 50 000 por fichero** (nueva) | Un sitemap que lo supere lo descarta Google entero |
| **robots.txt** (corregido) | Antes exigía que el único sitemap declarado fuese `/sitemap.xml` y fallaba con la configuración real (índice + hijos); ahora acepta los del mismo origen y detecta `Disallow: /` y sitemaps de otro dominio |
| Resto (sin cambios) | Código final, redirecciones, apex↔www, `X-Robots-Tag`, canónica autorreferente, hreflang contra el sitemap, un solo `<h1>`, JSON-LD |

Sale con código 1 si algo falla, así que sirve de puerta antes de dar por bueno
un cambio de SEO.

## 4. Causa: desvalorización a nivel de sitio

Es la que encaja con todo lo comprobado: el sitio **sigue indexado** (Google lo
devuelve en `site:`), las páginas **siguen siendo indexables** (200, canónica
propia, sin `noindex`) y, aun así, no llega ni un clic ni una visita. Eso no es
un problema de rastreo ni de etiquetas: es que Google ha dejado de mostrarlo.

Qué lo habría disparado, en orden de sospecha:

1. **Publicar y anunciar de golpe ~47 000 URL generadas** cuyo texto es el
   mismo en 18 mercados (solo cambia la moneda y el precio). Es el patrón que
   Google llama *scaled content abuse* y se evalúa **a nivel de sitio**: cuando
   se activa, arrastra también las páginas buenas.
2. Los `lastmod` de los sitemaps de precios son del 25/08 y 08/09, mientras el
   índice se regeneró el 19/10: se envió como «nuevo» un catálogo que en su
   mayoría llevaba semanas publicado. Para Google, una subida repentina de
   volumen sin cambios reales de contenido es una señal más de generación
   masiva, no de frescura.

### Confirmado con los datos del 23/10

| Dato de Search Console | Lectura |
|---|---|
| 74 impresiones en el día | Google **sigue mostrando** el sitio: no hay eliminación ni bloqueo |
| Posición media 44 | Está en la página 4–5: por eso 74 impresiones no producen ni un clic |
| Posición bajó | Es una **pérdida de posiciones**, no de indexación |
| **Ni una** URL de precios indexada | Google rastreó el catálogo y decidió no indexarlo: la huella de contenido masivo, sin valor añadido por mercado |
| Acciones manuales vacías | Es **algorítmico**, no una penalización manual: no hay nada que apelar |

Ese cuadro descarta las otras dos explicaciones que quedaban (bloqueo de
rastreo del borde y acción manual) y deja la desvalorización por contenido
generado a escala como la única que encaja con todo.

## 5. Cambio aplicado: reducir la huella a lo que tiene valor propio

Implementado el 23/10/2026. La política vive en **una constante** de
`app/services/precios_publicos.py`:

```python
MERCADOS_FICHAS_INDEXABLES: tuple[str, ...] = ("ES", "US", "GB", "CA", "AU", "IE")
```

| Qué | Antes | Ahora |
|---|---|---|
| Catálogo de precios en los 22 mercados | indexable en todos | indexable solo en ES y los 5 ingleses |
| 16 mercados hispanos restantes (MX, CO, AR, CL, PE, EC, DO, UY, PY, BO, PA, CR, GT, HN, SV, NI) | `index,follow` + sitemap + hreflang | `noindex, follow` en **meta y cabecera**, sin sitemap, sin hreflang; la página **sigue funcionando** para quien navega |
| Landings de mercado (`/mx/`, `/mx/apu`, guías) | indexables | **sin cambios**: son las páginas que rankean |
| `sitemap_index.xml` | 24 hijos (todos los mercados) | 7 hijos (principal + 6 mercados anunciados) |
| `robots.txt` | anunciaba además los 23 sitemaps hijos | solo índice y principal (el índice ya los contiene) |
| hreflang del catálogo | 22 mercados entre sí | solo mercados anunciados (un hreflang a `noindex` invalida el grupo) |
| `<meta robots>` vs `X-Robots-Tag` | dos listas distintas que podían divergir | el meta se deriva de la **misma** función que la cabecera |

**No se pierde tráfico con esto**: hoy esas páginas tienen cero URL indexadas y
cero clics. Lo que se gana es dejar de presentar a Google 40 000 páginas que
son el mismo texto con otra moneda.

### Cómo se revierte o se amplía

Añadir un mercado a `MERCADOS_FICHAS_INDEXABLES` (una línea) y desplegar. Todo
lo demás —sitemap, índice, `robots.txt`, hreflang, meta y cabecera— se recoge
solo. Condición antes de añadirlo: que su ficha **no** sea un calco de la
española (texto propio, unidades propias, contenido local real).

### Qué esperar, y cuándo

| Cuándo | Qué mirar |
|---|---|
| 24–72 h | Search Console → **Estadísticas de rastreo**: que Google vuelva a pedir las páginas clave. `site:cotizat.online` sigue devolviendo resultados |
| 1 semana | **Cobertura**: las URL de precios de los 16 mercados pasan a «Excluida por noindex». Es lo esperado: están saliendo del índice |
| 2–4 semanas | **Rendimiento**: la posición media de las landings y las guías debe empezar a recuperarse. Una desvalorización de sitio no se levanta en días |
| Si a las 4 semanas no hay mejora | El disparador no era solo el catálogo: toca revisar la calidad del contenido de las landings por mercado (títulos y textos clonados entre países) |

### Qué no tocar mientras tanto

- **Nada más de SEO** durante 2 semanas (títulos, canónicas, hreflang, sitemaps,
  redirecciones). Cada cambio reinicia la lectura y hace imposible saber qué
  funcionó.
- No «reenviar» el sitemap: ya está enviado y ahora es más pequeño; reenviarlo
  no acelera nada.
- No pedir indexación de las fichas retiradas: es lo contrario de lo que toca.

## 6. Qué no hacer ahora

- **Congelar cambios de SEO** (canonical, hreflang, robots, sitemap, noindex)
  hasta saber la causa: un cambio más en 48 h hace imposible atribuir el efecto.
- No «reenviar» el sitemap otra vez ni borrarlo: no arregla nada y pierde la
  señal de fecha.
- No rotar URLs ni añadir redirecciones nuevas: si ya hay un problema de
  rastreo, las cadenas lo empeoran.
- No volver a publicar mercados por volumen. Si algún día se enciende otro, que
  sea con contenido propio del país, de uno en uno y midiendo entre uno y otro.

## 7. GA4: por qué el informe «Tiempo real» puede salir vacío

Comprobado desde fuera el 23/10/2026, 20:36 UTC:

| Comprobación | Resultado |
|---|---|
| Etiqueta en el HTML servido | presente: `googletagmanager.com/gtag/js?id=G-013NT3ZTHP` |
| CSP de la respuesta | `script-src` incluye `www.googletagmanager.com` y `*.googletagmanager.com`; `connect-src` y `img-src` incluyen los recolectores de Google |
| Coherencia nonce ↔ CSP | el `nonce` del HTML coincide con el de la cabecera **también en respuestas servidas desde caché** (dos peticiones con `x-vercel-cache: HIT` y `age` idéntico devuelven el mismo nonce): no hay desajuste que bloquee el script de configuración |
| Caché | `/` se sirve con `public, max-age=0, must-revalidate` (MISS/HIT alternos), no desde una copia vieja sin etiqueta |

Es decir: **el servidor entrega la etiqueta correcta y deja pasar todo lo que
gtag.js necesita**. Lo que ya no se puede comprobar desde fuera es si *tu
navegador* la ejecuta. Las causas posibles, por frecuencia:

1. **Bloqueador o privacidad del navegador.** uBlock Origin, Brave Shields,
   AdGuard, Ghostery, Safari/Firefox con protección antitracking, o un DNS
   privado (NextDNS, Pi-hole, AdGuard DNS) cortan `googletagmanager.com`. La
   etiqueta sigue en el HTML: simplemente nunca se descarga.
2. **Vista equivocada en GA4.** El ID que sirve el sitio es `G-013NT3ZTHP`. Si
   la propiedad que miras tiene otro ID (o es una propiedad nueva), su
   «Tiempo real» estará siempre vacío aunque el sitio envíe datos a la otra.
3. **Retraso del informe.** «Tiempo real» suele pintar en 10–30 s; abrirlo
   después de navegar a veces muestra la visita ya cerrada.

### Cómo se resuelve en 1 minuto, sin instalar nada

Con el despliegue hecho, abre **`https://cotizat.online/comprobar-analitica`**.

La página (nueva, no indexable) ejecuta la misma etiqueta del sitio y, a los
4 segundos, informa en castellano de:

- si el script de configuración se ejecutó (`gtag` definido);
- si `gtag.js` se **descargó** de verdad (entradas de `performance`);
- cuántos eventos hay en `dataLayer` y si se creó la cookie `_ga`;
- si hubo **violaciones de CSP** (escuchando `securitypolicyviolation`);
- y envía un evento de prueba `ga_diagnostico` que debe aparecer en
  **GA4 → Informes → Tiempo real** en menos de un minuto.

Interpretación directa:

| Lo que muestra | Qué significa |
|---|---|
| Todo en verde y el evento no aparece en GA4 | el sitio funciona: el problema es la **propiedad/vista** que estás mirando |
| «gtag.js descargado: no» | un **bloqueador o DNS** corta Google: no es el sitio |
| «Bloqueos de la política de seguridad» con contenido | bug real de CSP/nonce: avísame con el texto y lo corrijo |
| «GA está apagado» | el despliegue no tiene ID: revisa `COTIZAT_GA_ID` en Vercel |

Además, `GET /readyz` incluye ahora la clave `analitica_ga` con el ID en uso y
los hosts abiertos en la CSP, para no tener que mirar el HTML.
