# Seguridad HTTP y protección CSRF

## Implementado

`app/security.py` incorpora una frontera ASGI aplicada globalmente:

- En PostgreSQL, toda petición `POST`, `PUT`, `PATCH` o `DELETE` debe aportar
  `Origin` o `Referer` del mismo origen exacto (esquema + host).
- `Sec-Fetch-Site: cross-site` y `none` se rechazan para escrituras.
- Las peticiones JSON reciben un error 403 en JSON; el resto, texto 403.
- SQLite local desactiva esta comprobación porque no expone sesiones
  multiempresa; el destino web la habilita obligatoriamente.

Esta defensa no depende de que cada formulario recuerde añadir un token. Es
adecuada para la aplicación browser-first same-origin actual. Si en el futuro
se admiten clientes API, webhooks o formularios embebidos, tendrán que usar una
ruta autenticada separada o añadirse un token CSRF firmado; no se debe relajar
la validación global de forma genérica.

Todas las respuestas incorporan:

- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- `X-Frame-Options: DENY`;
- `Cross-Origin-Opener-Policy: same-origin`;
- `Permissions-Policy` sin cámara, micrófono ni geolocalización;
- Content Security Policy con `default-src 'self'`, `object-src 'none'`,
  `base-uri 'self'`, `frame-ancestors 'none'` y `form-action 'self'`;
- HSTS durante respuestas HTTPS.

Las respuestas de archivos que ya declaran `Content-Security-Policy: sandbox`
conservan esa política más restrictiva.

## Límite de frecuencia de Auth

`AuthRateLimitMiddleware` limita por ruta e IP las escrituras sensibles:

- 10 intentos cada 5 minutos en `/acceso`;
- 5 intentos cada 5 minutos en `/registro`;
- 5 intentos cada 5 minutos en `/recuperar-acceso`;
- 10 intentos cada 5 minutos en `/restablecer-clave`.

Cuando se supera el límite responde `429` y publica `Retry-After`. Las lecturas y
las rutas no incluidas no consumen intentos. El número de contadores se acota
para que las IP nuevas no hagan crecer la memoria indefinidamente. Esta primera
barrera vive en la memoria de cada proceso: no comparte contadores entre
instancias y se reinicia
con el servidor. Por tanto **no sustituye un límite distribuido** (Redis,
Upstash o el servicio equivalente del proveedor) antes de una exposición
pública con escalado horizontal. Por defecto se ignora `X-Forwarded-For`; solo
se activa con `COTIZAT_TRUST_PROXY=true` detrás de un proxy conocido que elimine
o sanee ese encabezado. Activarlo si el proceso recibe Internet directamente
permitiría falsear la IP y eludir el límite.

## CSP y límite todavía pendiente

Los scripts inline legítimos reciben un nonce aleatorio distinto en cada
respuesta. `script-src` acepta solo `'self'` y ese nonce, y
`script-src-attr 'none'` bloquea handlers HTML como `onclick`. Los 97 handlers
heredados se sustituyeron por acciones declarativas registradas en
`csp_events.js`; los formularios de borrado conservan su confirmación sin
reconstruir código JavaScript. También se eliminó un `innerHTML` que incorporaba
nombres/unidades editables de packs y ahora esos nodos usan `textContent`.

Los estilos siguen siendo la excepción transitoria: hay cientos de atributos
`style` y cambios CSSOM del editor heredado, por lo que `style-src` aún incluye
`'unsafe-inline'`. Las etiquetas `<style>` ya reciben nonce, pero todavía falta
extraer atributos y mutaciones de estilo antes de retirar esa última concesión.
Fuentes de Google permanecen limitadas a sus hosts oficiales. Por tanto la
protección XSS mejoró de forma material, pero **la CSP todavía no es final**.

Antes de publicar se debe eliminar `'unsafe-inline'` también de estilos,
terminar la revisión de sinks DOM y ejecutar pruebas en el despliegue HTTPS real.

## Pruebas

`tests/test_web_security.py` cubre:

- Origin exacto permitido;
- fallback a Referer same-origin;
- Origin/Fetch Metadata cross-site rechazado;
- escritura sin procedencia rechazada;
- cabeceras defensivas y HSTS;
- conservación de la CSP sandbox de archivos;
- nonce único por respuesta, ausencia de handlers HTML y cobertura de todas las
  acciones declarativas;
- bloqueo `429`, `Retry-After`, separación por IP y exclusión de lecturas/rutas
  no protegidas en el límite de Auth.

Este avance no sustituye la auditoría pendiente de XSS, el rate limiting
distribuido, sesiones, roles PostgreSQL no privilegiados ni pruebas reales de
Auth/Storage.
