# Auditoría externa (SEO Ninja, 22-10-2026): qué era real y qué no

Informe sobre `https://cotizat.online/`: **95/100, nota A**. 31 comprobaciones
pasadas, 10 avisos, 0 errores.

> El informe no se podía leer directamente: se carga por JavaScript. Se revisó
> con un renderizador y se contrastó cada aviso contra el código y contra las
> cabeceras reales de producción (petición HEAD externa a `cotizat.online` y
> `www.cotizat.online`), no contra lo que dice el informe.

---

## Los cinco avisos que eran falsos positivos

El escáner aseguraba que faltaban estas cinco cosas. Las cinco están en
producción, y así se ve en la respuesta real del servidor:

| Aviso del informe | Realidad (cabeceras de `https://cotizat.online/`) |
|---|---|
| Content Security Policy Missing | `Content-Security-Policy: default-src 'self'; base-uri 'self'; …` |
| X-Frame-Options Missing | `X-Frame-Options: DENY` |
| HSTS Header Missing | `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` |
| Browser Caching: No Cache-Control | `Cache-Control: public, max-age=0` |
| Server Compression Not detected | `Content-Encoding: gzip` |

No hay nada que arreglar ahí. Queda una prueba (`test_auditoria_externa.py`)
que comprueba las cinco cabeceras en las 234 URL del sitemap, para que no se
pierdan de verdad en el futuro.

**Por qué falló el escáner**: analizó el documento, pero no las cabeceras de
su propia petición; los cinco avisos son la firma típica de eso. Los informes
automáticos sirven para descubrir cosas, no para creérselos sin comprobarlos.

---

## Los cinco avisos que sí eran reales

### 1. www devolvía 307, no 301 (el único de peso técnico)

```
HTTP/1.1 307 Temporary Redirect
Location: https://cotizat.online/
Server: Vercel
```

Lo emite Vercel en el borde, antes de llegar a la aplicación: es la
redirección automática del dominio y es **temporal**. Un 307 no consolida
señales; Google lo trata como salto provisional y puede mantener las dos
direcciones como candidatas.

Arreglado en dos capas:

- `vercel.json` declara la regla con `"permanent": true` (308 en el borde).
- Un middleware (`HostCanonicoMiddleware`) devuelve 301 en cualquier otro
  despliegue, conservando ruta y query.

### 2. Cero enlaces externos

La portada no citaba ninguna fuente. Se añadió un bloque **«De dónde salen
las reglas que aplica CotizaT»** con dos organismos oficiales, elegidos porque
sostienen afirmaciones que el copy ya hace:

- **CTE** (`codigotecnico.org`) — normativa de edificación española.
- **BOE** (`boe.es`) — tipos de IVA y obligaciones de facturación.

Ambos comprobados con una petición real (200). Se descartaron otros
candidatos: `fiebdc.es` responde 302→404 y `iso.org` devuelve 403 a los
rastreadores, así que enlazarlos habría sido peor que no enlazar nada.

### 3. «1 párrafo de 747 palabras»

Es el mock decorativo del hero (`aria-hidden="true"`): una maqueta del panel
con decenas de etiquetas cortas. No es prosa y no se toca: es el elemento que
explica el producto en el primer scroll.

### 4. Sin `llms.txt`

Añadido `https://cotizat.online/llms.txt`, generado del mismo sitio que el
sitemap: portada, producto, comparador con sus 14 capítulos, los 23 mercados,
los tres hubs en sus dos idiomas, las guías y una nota de qué no se indexa. 80
líneas, sin HTML, cacheable.

### 5. «Answer-Ready Headings: None detected»

Las preguntas frecuentes existían (y su `FAQPage` pasaba la validación), pero
iban dentro de `<summary>`, que es interactivo y **no** es un encabezado: ni
Google ni un asistente de IA las ven como pregunta. Ahora cada una lleva un
`<h3>` dentro del `<summary>`, en las nueve plantillas que tienen preguntas, y
el CSS lo neutraliza para que el acordeón se vea igual.

Además, bajo el H1 de la portada hay una **respuesta autocontenida de ~40
palabras** («CotizaT es un software de presupuestos de construcción: …»), que
varía por mercado porque incluye su moneda, impuesto y terminología. Es la
frase que un buscador puede citar sin el resto de la página.

---

## Lo que el informe no vio y sigue abierto

| Tema | Estado |
|---|---|
| Reduce unused CSS (~1 oportunidad) | La portada ya pinta el primer viewport con CSS crítico inline y carga `public.css` sin bloquear. Partir esa hoja más es un trabajo de diseño, no un cambio seguro de una tarde |
| `sameAs` de la organización | El escáner lo echaba en falta; ya estaba resuelto en el PR #167 (perfil de Facebook). Aparece en las 234 URL del sitemap |
| `lastmod` por URL | Una sola fecha por mercado; inventarla por URL es peor que no tenerla |
| `/pago` por país | Sus importes sí varían por mercado, pero serían 23 URL casi idénticas: decisión de producto |

---

## Cobertura

`tests/test_auditoria_externa.py` (**28 pruebas**): redirección de www con 301
(con y sin `COTIZAT_PUBLIC_URL`, y la regla de `vercel.json`), fuentes
oficiales con `rel="noopener"`, preguntas como encabezados en seis
plantillas, respuesta citable de 30-60 palabras, `llms.txt` (estructura,
formato, que todas sus URL respondan 200 y que no liste páginas privadas) y
las seis cabeceras que el informe daba por ausentes en las 234 URL.

Suite completa: **2 909 pasan, 13 omitidas** (5:52).
