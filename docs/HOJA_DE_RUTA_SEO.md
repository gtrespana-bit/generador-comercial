# Hoja de ruta SEO — CotizaT en 5 países, sin publicidad

**Fecha:** 21 de agosto de 2026  
**Dominio canónico:** `https://cotizat.online`  
**Mercados de lanzamiento:** Venezuela, Colombia, México, Ecuador, Perú  
**Objetivo:** conseguir clientes de búsqueda orgánica. Cero presupuesto en anuncios.

Esta hoja es operativa. Complementa `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` y `docs/ANALISIS_LATAM_Y_COMPETENCIA_2026-08-19.md`. No sustituye Search Console ni el día final de tests (D-019).

---

## 0. Lo que hay que oír antes de escribir una palabra más

Nadie llega a las primeras posiciones de Google en cinco países el mes del lanzamiento. Quien lo prometa miente.

Lo que sí se puede hacer, y es exactamente el trabajo de esta hoja:

1. **Que Google pueda entender y rastrear** una URL distinta por país y por intención.
2. **Que cada URL tenga texto único** (no «Venezuela» sustituido por «Colombia»).
3. **Que esas URLs coincidan con lo que un constructor busca** cuando está a punto de pagar un software.
4. **Que el resto del crecimiento orgánico** (directorios, gremios, YouTube, respuestas en foros, PDF de ejemplo) apunte a esas URLs.

Sin (1) y (2) el contenido no rankea. Sin (3) rankea para consultas que no convierten. Sin (4) un dominio nuevo no gana autoridad.

CotizaT es un dominio de semanas de vida. El horizonte realista:

| Plazo | Lo que es razonable |
| --- | --- |
| Semanas 1–4 | Indexación, rich results de FAQ, ranking en cola larga (`software presupuestos construcción venezuela`) |
| Meses 2–4 | Top 10 en 8–15 consultas de cola media por país, si el contenido se mantiene y hay enlaces naturales |
| Meses 6–12 | Top 3 en las consultas de intención comercial más débiles de cada mercado; las cabezas (`software construcción colombia`) siguen siendo de incumbentes |

La palanca de CotizaT no es «más artículos». Es **un producto que ya habla COP/MXN/PEN, NIT/RFC/RUC y pañete/aplanado/tarrajeo**, a 89 US$/año, en un mercado donde OneEstimate cobra 49 US$/mes. El SEO tiene que vender eso, no un blog genérico de «10 tips para presupuestar».

---

## 1. Auditoría del estado anterior (21/08/2026)

Qué había y por qué no bastaba.

### 1.1 Lo que ya estaba bien

- Subdirectorios `/ve/`, `/co/`, `/mx/`, `/ec/`, `/pe/` en un solo Vercel + un solo Supabase.
- Selector de país, moneda, IVA, ID fiscal y vocabulario local en la landing.
- Ejemplo de presupuesto convertido a COP / MXN / PEN.
- Canónica y `hreflang` en la landing.
- Sitemap mínimo con las 5 landings.
- Propuestas públicas y panel con `noindex` en algunos sitios.

### 1.2 Huecos que impedían rankear

| Hueco | Por qué duele | Gravedad |
| --- | --- | --- |
| **`/` cambiaba de contenido según cookie** | Google veía una URL con HTML distinto según el visitante. Riesgo de contenido duplicado / cloaking involuntario. | Crítica |
| **H1 y title genéricos** | El H1 era el mismo en los 5 países. Google no tenía señal de «Colombia» o «APU» en el encabezado. | Crítica |
| **Una sola URL por país** | Quien busca «software APU Colombia» y quien busca «presupuestos de remodelación México» aterrizaban en la misma página. Una URL no gana tres intenciones. | Alta |
| **Sin `robots.txt`** | El panel, login y presupuestos podían rastrearse. Diluye crawl budget y expone URLs privadas. | Alta |
| **Sitemap sin hreflang ni lastmod** | Google no tenía el mapa de equivalentes por país. | Alta |
| **Sin Open Graph ni JSON-LD** | Cero rich results, previews pobres al compartir en WhatsApp/LinkedIn. | Media |
| **Canónica desde `request.base_url`** | En previews de Vercel la canónica apuntaba al preview, no a `cotizat.online`. | Media |
| **`/conocer` duplicaba `/`** | Dos URLs, el mismo HTML. | Media |
| **`/co` y `/co/` ambos 200** | Canónicas duplicadas. | Baja |
| **Sin FAQPage** | Se dejaban snippets de FAQ en la mesa. | Baja |

Competencia de contenidos (no de producto): OneEstimate publica artículos de APU por país; blogs de construcción colombianos y mexicanos cubren «cómo hacer un presupuesto de obra». Un dominio nuevo no les gana con una landing sola.

---

## 2. Mapa de búsquedas por país (intención comercial)

No usamos volúmenes comprados. Agrupamos por **intención** y por **vocabulario local**. La cabeza de cada cluster es la URL que debe ganar.

### 2.1 Clusters (los mismos cinco en cada país)

| Cluster | Intención | URL | Palabras típicas |
| --- | --- | --- | --- |
| **A. Software de presupuestos** | Quiero una herramienta, voy a comparar | `/co/software-presupuestos` | software presupuestos construcción, programa para cotizar obras, generador de presupuestos |
| **B. APU / precios unitarios** | Soy técnico, quiero descompuestos | `/co/apu` | APU, análisis de precios unitarios, descompuestos, metrados (PE) |
| **C. Remodelación** | Reformo viviendas, no licito obra pública | `/co/remodelacion` | presupuesto remodelación, cotizar baño, reforma cocina |
| **D. Home de país** | Marca + mercado | `/co/` | CotizaT Colombia, presupuestos construcción Colombia |
| **E. Cómo funciona / FAQ / planes** | Ya me conocen, deciden | `/como-funciona`, `/legal/preguntas`, `/pago` | precio, prueba gratis, factura fiscal |

### 2.2 Vocabulario que **debe** aparecer (y el que no)

| País | Decir | No decir en esa URL |
| --- | --- | --- |
| VE | presupuesto, concreto, friso, cielo raso, plomero, RIF, Bs, USD | pañete, aplanado, CFDI |
| CO | presupuesto, APU, pañete, andén, sardinel, NIT, COP, IVA 19 % | friso, zoclo, metrados |
| MX | presupuesto **y** cotización, aplanado, plafón, zoclo, RFC, MXN, IVA 16 % | pañete, tarrajeo, RIF |
| PE | presupuesto, metrados, APU, tarrajeo, gasfitero, RUC, IGV, S/ | pañete, plafón, RIF |
| EC | presupuesto, APU, enlucido, tumbado, gasfitero, RUC, IVA 15 %, USD | friso, zoclo |

Regla: el glosario de `app/paises.py` y `app/services/traduccion.py` es la fuente. El SEO no inventa sinónimos que el producto no usa.

### 2.3 Consultas que **no** perseguimos (aún)

- Licitación pública, BC3/FIEBDC, AIU colombiano nativo, BIM/IFC, «IA que lee planos».
- Ciudades (`software presupuestos bogotá`) hasta que las URLs de país estén indexadas y haya testimonios locales.
- España y el Cono Sur: no están en `ORDEN_SELECTOR`. Abrir Chile/Argentina es Etapa 6, no SEO de lanzamiento.

---

## 3. Qué se implantó en esta sesión (base técnica, lista para indexar)

Código en `app/seo.py`, `app/routers/publico.py`, plantillas públicas y `tests/test_seo.py`.

### 3.1 Técnico

- `robots.txt` con Allow de lo público y Disallow del panel, login, APIs y archivos.
- Sitemap con `lastmod`, prioridad, `xhtml:link` hreflang. Sin `/conocer`.
- Canónicas y Open Graph desde `COTIZAT_PUBLIC_URL` (fallback al host solo en tests).
- JSON-LD: `SoftwareApplication` (precio 89 USD), `FAQPage`, `BreadcrumbList`.
- Imagen social `/static/og-cotizat.png` (1200×630).
- `X-Robots-Tag: noindex` en todo lo que no es página de marketing (`app/seo.es_indexable`).
- `/` **siempre** genérica LatAm. La cookie ya no cambia su HTML.
- `/conocer` → 301 a `/`. `/co` → 301 a `/co/`.

### 3.2 Contenido indexable ahora

| URL | Rol |
| --- | --- |
| `/` | Hub LatAm |
| `/ve/`, `/co/`, `/mx/`, `/ec/`, `/pe/` | Home de país: H1, title, description, FAQ y vocabulario propios |
| `/software-presupuestos`, `/apu`, `/remodelacion` | Hubs de intención, genéricos |
| `/ve/software-presupuestos`, `/co/apu`, `/mx/remodelacion`… (15 URLs) | Intención × país, texto distinto |
| `/como-funciona`, `/pago`, `/legal/*` | Decisión y confianza |

Son **24 URLs de marketing** + legales. Suficiente para lanzar. No son 200 artículos delgados.

### 3.3 Cómo se añade un país o un tema después

1. El país entra en `ORDEN_SELECTOR` (`app/paises.py`).
2. Copy en `_LANDING` y `_bloques_tema` (`app/seo.py`).
3. Ruta `/xx/` (el patrón `{cc}/tema` ya cubre las intenciones).
4. Tests en `tests/test_seo.py`.

No se copia HTML. Si el texto de México es el de Colombia con el nombre cambiado, no se publica.

---

## 4. Hoja de ruta a 90 días (sin anuncios)

Una sola persona puede ejecutar esto. El cuello de botella es constancia, no código.

### Semana 0 — ya hecha en código

- [x] Canónicas, hreflang, robots, sitemap, schema, OG.
- [x] URLs de país e intención con copy propio.
- [x] `/` genérica; 301 de duplicados.

### Semana 1 — indexación (titular, 2–3 horas)

Trabajo de panel, no de repositorio:

1. **Google Search Console** en `https://cotizat.online` (prefijo de dominio, no solo URL). Verificar DNS.
2. Enviar `https://cotizat.online/sitemap.xml`.
3. Inspeccionar `/`, `/co/`, `/mx/`, `/co/apu`. Pedir indexación.
4. **Bing Webmaster Tools** (mismo sitemap). Es gratis y alimenta Copilot/DuckDuckGo.
5. Comprobar que `www.cotizat.online` redirige al apex (ya documentado en `docs/DOMINIO_COTIZAT_ONLINE.md`).
6. En Search Console → Recurso internacional: revisar que los `hreflang` se leen.

Criterio de hecho: las 5 homes de país aparecen como «Detectada» o «Indexada» en 14 días.

### Semanas 2–3 — confianza y CTR (código ligero + un vídeo)

- [ ] **E1-051 — vídeo de 5 minutos.** Es el activo SEO más barato que falta: se incrusta en `/como-funciona` y se sube a YouTube con título por país («Cómo hacer un presupuesto de obra en Colombia con CotizaT»). YouTube rankea en Google.
- [ ] PDF de ejemplo enlazado con `rel` interno desde cada hub (ya existe el archivo).
- [ ] Completar `og:locale` alternates si GSC marca avisos.
- [ ] Página `/legal/preguntas`: añadir 3 preguntas por país (NIT, RFC, RUC, factura DIAN/CFDI/SUNAT/SRI) sin prometer fiscalidad. Enlazar a `/co/`, `/mx/`, etc.

Criterio de hecho: el vídeo indexado y la FAQ de legales enlaza a las 5 homes.

### Semanas 4–6 — autoridad sin pagar

Nada de comprar enlaces. Nada de PBNs. Nada de «guest posts» en granjas.

Lista de **enlaces que un constructor sí haría clic**, todos gratis:

| Canal | Qué hacer | A qué URL |
| --- | --- | --- |
| **Capterra / GetApp / Software Advice** | Ficha gratuita «construction estimating – Latin America» | Home del país del revisor |
| **Product Hunt / BetaList** | Un lanzamiento, no cinco | `/` |
| **Cámaras y gremios** | Cámara de la Construcción (VE), CAMACOL (CO), CMIC (MX), CAPECO (PE), Cámara de la Construcción (EC): directorio de proveedores o nota de prensa de 400 palabras | Home de país |
| **Perfiles de empresa** | Google Business Profile si hay domicilio fiscal; LinkedIn Company | `/` |
| **Comunidades** | Responder (no spamear) en grupos de maestros de obra, Reddit r/Colombia, foros de CYPE en español. Enlace solo si aporta. | `/co/apu` o equivalente |
| **PDF viajero** | Cada presupuesto de piloto que salga al mundo lleva `cotizat.online` en el pie. Es el backlink más natural del producto. | Home |

Criterio de hecho: 8–12 enlaces de dominio distintos, ninguno pagado, ninguno recíproco masivo.

### Semanas 6–10 — un artículo realmente útil por país (no un blog)

Cinco URLs nuevas, **una por país**, de 1.200–1.800 palabras, con datos del producto (cifras reales del catálogo, APU de ejemplo, moneda). Temas que nadie más cubre bien a este precio:

| País | Artículo (slug tentativo) | Por qué convierte |
| --- | --- | --- |
| CO | `/co/apu-vs-excel` — «Cómo armar un APU de pañete en Colombia sin Excel» | Intención alta, vocabulario local |
| MX | `/mx/cotizar-remodelacion` — «De la visita a la cotización en MXN» | «Cotización» es la palabra de México |
| PE | `/pe/metrados` — «Metrados y APU en soles, congelando el IGV» | Palabra que solo se busca en Perú |
| VE | `/ve/presupuesto-usd-bs` — «Presupuesto en USD con equivalente en Bs, tasa congelada» | Dolor único venezolano |
| EC | `/ec/apu-en-dolares` — «APU en Ecuador, en USD, con RUC» | Mercado dolarizado, poco contenido |

Reglas del artículo:

- Lo escribe alguien que ha usado el producto, no un generador suelto.
- Incluye captura o cifra del catálogo real (partidas, no «miles de»).
- Enlaza a la home de país, a `/como-funciona` y a `/pago`.
- Declara que no es factura fiscal.
- No ataca a competidores por nombre salvo comparación factual de precio público.

Hasta que estos cinco existan, **no se abre un blog**. Un blog vacío es peor que no tenerlo.

### Semanas 10–12 — medir y podar

- Consultas reales de GSC: qué impresiona, qué no clicó, qué posicionó en 20–40.
- Si una URL de intención tiene impresiones y CTR < 2 %: reescribir title/H1, no añadir otra URL.
- Si una URL no tiene impresiones a 45 días: comprobar indexación; si está indexada y a cero, el cluster estaba mal elegido — no se insiste.
- No se crean URLs de ciudad todavía.

---

## 5. Operación continua (el trabajo que no se ve)

Cada mes, 60 minutos:

1. GSC: cobertura, páginas excluidas, hreflang, consultas nuevas.
2. `sitemap.xml` se regenera solo; no hace falta reenviarlo salvo error.
3. Un enlace natural (directorio, gremio, respuesta útil).
4. Una mejora de snippet (title o FAQ) en la URL que más impresiones tenga y peor CTR.

Cada trimestre:

- Revisar que el copy de `app/seo.py` sigue siendo verdad (precio, IVA, número de partidas). Un title que miente se hunde.
- Si se abre Chile o Argentina: copy nuevo, no clonar Perú.

---

## 6. Métricas (las que importan, no las vanidosas)

| Métrica | Dónde | Meta 90 días | Meta 12 meses |
| --- | --- | --- | --- |
| URLs indexadas de marketing | GSC | 20 de 24 | todas las publicadas |
| Clics orgánicos / semana | GSC | 30–80 | 300–800 |
| Consultas en top 10 | GSC | 10 | 40 |
| Registros con `utm` orgánico o `referrer` Google | panel interno (cuando exista telemetría E5-012) | 5–15 | 40–80 |
| Enlaces de dominios distintos | GSC / Ahrefs gratuito a ratos | 8 | 30 |
| Pruebas gratuitas que llegan de orgánico | cruce manual email × fecha × GSC | 3 | 20 |

No se optimiza para «tráfico». Se optimiza para **pruebas empezadas**. Un millar de visitas de «qué es un APU» que no llegan a `/acceso` no pagan el servidor.

Cuando exista E5-012 (telemetría voluntaria), añadir `utm_source=google` en los CTAs no hace falta: el referrer basta. No se instala Google Analytics ahora: la política de privacidad dice «sin rastreadores». GSC no usa cookies en la web. Si un día se quiere Analytics, hay que cambiar privacidad **antes**.

---

## 7. Lo que no se hará (y por qué)

- **No se compran enlaces ni se publican en granjas.** Un penalización en un dominio nuevo es irreversible para el lanzamiento.
- **No se cloakea por IP de país.** Los subdirectorios ya resuelven el geotargeting. Un HTML distinto según IP es el error que Google más castiga.
- **No se generan 200 páginas de ciudad** (`/co/bogota`, `/co/medellin`…) hasta tener testimonios locales. Son doorway pages.
- **No se llama «IA» al matching del catálogo.** Ya es decisión D-005 y además es SEO negativo: la query «IA presupuestos» la ganan otros y el anuncio sería falso.
- **No se promete factura DIAN / CFDI / SUNAT / SRI.** El snippet que mienta se denuncia y se pierde la cuenta.
- **No se abre el blog** hasta los cinco artículos de la sección 4.
- **No se traduce a portugués ni a inglés** en este ciclo.

---

## 8. Responsables y orden

| Quién | Qué |
| --- | --- |
| Código (esta rama) | Base técnica y URLs de intención. Hecho. |
| Titular | GSC, Bing, vídeo E1-051, fichas Capterra, gremios, los cinco artículos. |
| Nadie más | Enlaces pagados, agencias «garantizamos el nº 1». |

El siguiente commit de producto **no** debería ser más SEO. Debería ser el vídeo y el alta en Search Console. El código ya no es el cuello de botella.

---

## 9. Archivos de referencia

- `app/seo.py` — copy, canónicas, sitemap, robots, schema.
- `app/routers/publico.py` — rutas `/co/`, `/co/apu`, 301, robots, sitemap.
- `app/templates/_seo_head.html`, `landing.html`, `seo_hub.html`.
- `app/static/og-cotizat.png`.
- `tests/test_seo.py`.
- `docs/DOMINIO_COTIZAT_ONLINE.md` — DNS y canónico apex.
- `docs/ANALISIS_LATAM_Y_COMPETENCIA_2026-08-19.md` — por qué el precio y el APU son el mensaje.

---

*Auditoría y primera implantación: 21/08/2026, rama `arena/01a0257a-generador-comercial`.*
