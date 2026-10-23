# Diagnóstico: cero visitas tras enviar el sitemap nuevo (23/10/2026)

Contexto: entre el 19 y el 22/10 se amplió la superficie indexable (catálogo de
precios por país) y se envió el sitemap nuevo. Desde entonces Search Console
muestra 0 visitas al día. Este documento fija **qué está comprobado**, **qué
falta comprobar** y **en qué orden**, para no seguir tocando cosas a ciegas.

## 1. Lo que ya está verificado (23/10, 19:50 UTC, desde fuera)

| Comprobación | Resultado |
|---|---|
| `GET /` | 200, `x-vercel-cache: HIT`, `server: Vercel` |
| `<meta robots>` de `/` | `index,follow,max-image-preview:large` |
| Canónica de `/` | `https://cotizat.online/` (autorreferente, apex) |
| GA4 en el HTML | `gtag/js?id=G-013NT3ZTHP` presente, con `nonce` |
| `GET /es/precios` | 200, indexable, canónica autorreferente |
| Ficha de partida (`/es/precios/…/alarma-de-asistencia-de-bano`) | 200, `<title>` propio, canónica autorreferente |
| `robots.txt` | `Allow: /`, sin `Disallow: /`, anuncia índice + 23 sitemaps de precios |
| `sitemap_index.xml` | 200, 23 hijos; los hijos responden 200 |
| `/healthz` | `{"ok": true}` |
| `site:cotizat.online` en Google | **devuelve resultados y paginación** (varias páginas de resultados, mercados `en-ie`, `do`, `en-gb`…) |
| `site:cotizat.online` en DuckDuckGo | devuelve resultados (portada, `en-us`, `en-gb`, legales, planes) |

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

## 4. Hipótesis principal: desvalorización a nivel de sitio

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

### Cómo se confirma (10 minutos, sin instalar nada)

- GSC → **Rendimiento** → 28 días → gráfico de **Impresiones**: si siguen
  existiendo mientras los clics son cero, es desvalorización confirmada.
- GSC → Rendimiento → **Posición media**: un salto de, por ejemplo, 8 → 40 en
  dos días es la firma de una desvalorización, no de un bloqueo.
- GSC → **Indexación → Páginas**: cuántas URL de `/xx/precios/…` están en
  *Rastreada: actualmente no indexada*. Miles ahí = Google ha decidido que ese
  catálogo no merece índice.
- GSC → **Acciones manuales**: si aparece algo, esto deja de ser algorítmico y
  hay que pedir revisión. Si está vacío (lo habitual), es algorítmico.

### Plan si se confirma, en este orden

1. **Congelar** cualquier cambio de SEO durante 7 días y recoger datos. Cada
   cambio nuevo reinicia la lectura.
2. **Reducir la huella anunciada**: dejar en `sitemap_index.xml` solo el sitemap
   editorial y no anunciar los 23 de precios desde `robots.txt`. Las fichas
   siguen accesibles por enlazado interno, pero dejan de presentarse como un
   bloque de 47 000 URL nuevas.
3. **Diferenciar los mercados hispanos**, que es donde está el duplicado real.
   Opciones, de menos a más agresiva: ficha completa solo en España y los 3–4
   mercados con demanda demostrada; en el resto, página de **apartado** con
   tabla de precios en vez de ficha individual; o `noindex` en los mercados sin
   demanda. Los mercados de habla inglesa no sufren este problema: su texto es
   distinto de verdad.
4. **Reforzar lo que sí convierte**: landings por mercado, guías, comparador y
   calculadora —contenido escrito, no generado— para que la proporción de
   páginas de valor suba.
5. **Medir a 3–4 semanas.** Una desvalorización de sitio no se levanta en días,
   y seguir publicando páginas generadas mientras tanto la empeora.

## 5. Qué no hacer ahora

- **Congelar cambios de SEO** (canonical, hreflang, robots, sitemap, noindex)
  hasta saber la causa: un cambio más en 48 h hace imposible atribuir el efecto.
- No «reenviar» el sitemap otra vez ni borrarlo: no arregla nada y pierde la
  señal de fecha.
- No rotar URLs ni añadir redirecciones nuevas: si ya hay un problema de
  rastreo, las cadenas lo empeoran.
