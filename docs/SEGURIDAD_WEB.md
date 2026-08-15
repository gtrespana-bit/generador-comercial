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
- 10 intentos cada 5 minutos en `/restablecer-clave`;
- 10 intentos cada 5 minutos en `/cuenta/clave`.

Cuando se supera el límite responde `429` y publica `Retry-After`. Las lecturas y
las rutas no incluidas no consumen intentos. Por defecto se ignora
`X-Forwarded-For`; solo
se activa con `COTIZAT_TRUST_PROXY=true` detrás de un proxy conocido que elimine
o sanee ese encabezado. Activarlo si el proceso recibe Internet directamente
permitiría falsear la IP y eludir el límite.

### Dónde se cuenta: memoria frente a contador compartido

Contar en la memoria del proceso protege un servidor único, pero **no protege
un despliegue serverless**. En Vercel cada invocación puede ejecutarse en un
proceso nuevo, de modo que el contador arranca vacío una y otra vez: bastaba
con que las peticiones cayesen en instancias distintas para que «5 intentos
cada 5 minutos» no se aplicara. `app/ratelimit.py` separa la decisión de dónde
se guarda la cuenta y ofrece dos backends:

| Backend | Cuándo se usa | Comparte estado |
| --- | --- | --- |
| `MemoryRateLimit` | Escritorio, desarrollo y respaldo ante fallos | No |
| `UpstashRateLimit` | Con `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` | Sí |

Decisiones que conviene no revertir sin motivo:

- **API REST, no cliente Redis.** Una función serverless no conserva sockets
  entre invocaciones, y usar `urllib` evita sumar una dependencia al runtime
  (mismo patrón que `app/auth.py` y `app/storage.py`).
- **Ventana fija por tramo** (`now // ventana`) en lugar de deslizante: la
  clave caduca sola, renovar el TTL es idempotente y todo cabe en un único
  viaje de ida y vuelta (`INCR` + `EXPIRE` en un pipeline, timeout de 3 s).
  Pierde precisión en la frontera entre tramos; a cambio no necesita sorted
  sets ni scripts Lua.
- **Degradación al contador local si Upstash falla.** No se falla abierto
  (sería quitar el límite justo cuando el servicio está en apuros) ni cerrado
  (dejaría a todos sin poder entrar por una caída ajena): se vuelve a la
  protección que existía antes.
- **La IP no viaja en claro.** La clave es `cotizat:rl:<sha256("ruta|ip")[:32]>
  :<índice>`, determinista entre instancias pero no reconstruible.

Una configuración incompleta o inválida no impide arrancar: se registra un
aviso y se degrada a memoria. Lo que sí hace ruido es `/readyz`, que publica
`checks.rate_limit` con `memoria`, `distribuido:upstash` o `mal-configurado`.
Con `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` el estado `memoria` pasa a ser
un error de readiness — actívalo en cualquier despliegue con más de una
instancia. En SQLite (escritorio) nunca se considera error, porque ahí un
contador por proceso es exactamente lo correcto.

## CSP estricta para scripts y estilos

Los scripts inline legítimos reciben un nonce aleatorio distinto en cada
respuesta. `script-src` acepta solo `'self'` y ese nonce, y
`script-src-attr 'none'` bloquea handlers HTML como `onclick`. Los 97 handlers
heredados se sustituyeron por acciones declarativas registradas en
`csp_events.js`; los formularios de borrado conservan su confirmación sin
reconstruir código JavaScript. El frontend ya no utiliza `innerHTML`,
`outerHTML`, `insertAdjacentHTML` ni otros parsers de fragmentos HTML: los datos
del catálogo, importaciones y editores se representan con creación explícita de
nodos y `textContent`.

La auditoría automatizada de rutas mantiene una lista cerrada de fronteras
públicas (Auth, recuperación e invitación) y exige `get_db` o
`get_authenticated_db` en el resto de endpoints comerciales. Incluso los
formularios vacíos de clientes, recursos, productos y packs requieren sesión.
Además, Storage comprueba el rol `lectura` **antes** de usar la credencial
server-side para crear o borrar un objeto; el rechazo del flush/RLS por sí solo
llegaría demasiado tarde y podría dejar un objeto huérfano o borrar uno válido.
Las transiciones de vencimiento y los hitos de onboarding/PDF ya no escriben
desde rutas `GET`: usan `POST` same-origin, y la auditoría AST impide reintroducir
mutaciones empresariales directas en endpoints de lectura. Así una membresía de
solo lectura puede abrir listados y descargar documentos sin provocar un flush
rechazado.

`style-src` tampoco admite `'unsafe-inline'` y `style-src-attr 'none'` bloquea
atributos de estilo. Los 498 atributos heredados se trasladaron a clases; los
valores Jinja variables usan clases cerradas o atributos de datos numéricos.
Las mutaciones CSSOM del editor pasan por `csp_styles.js`, que crea una hoja
autorizada con el nonce de la respuesta y modifica reglas CSS, nunca el atributo
`style` del elemento. Sus nombres de propiedad se validan y CSSOM interpreta los
valores sin construir HTML. Las etiquetas `<style>` legítimas conservan nonce y
las fuentes de Google permanecen limitadas a sus hosts oficiales.

La revisión estática de sinks HTML y estilos queda cerrada y se mantiene como
prueba de regresión. Antes de publicar todavía se debe confirmar en un navegador
del despliegue HTTPS real que no hay violaciones CSP ni regresiones visuales o de
interacción.

## Emails de invitación

Las invitaciones de equipo se envían por Resend (API REST, `urllib`) cuando
`RESEND_API_KEY` y `COTIZAT_EMAIL_FROM` están configuradas; si no, o si el
proveedor falla, el enlace se muestra una sola vez en pantalla (ver
`docs/EMAILS_INVITACION.md`). La clave `re_...` es EXCLUSIVA del backend y
nunca viaja al navegador; el token de la invitación sigue guardándose solo
como SHA-256. Las plantillas de correo se excluyen de la verificación CSP a
propósito: los clientes de email exigen estilos en línea.

## Pruebas

`tests/test_web_security.py` cubre:

- Origin exacto permitido;
- fallback a Referer same-origin;
- Origin/Fetch Metadata cross-site rechazado;
- escritura sin procedencia rechazada;
- cabeceras defensivas y HSTS;
- conservación de la CSP sandbox de archivos;
- nonce único por respuesta, ausencia de `unsafe-inline`, handlers HTML,
  atributos/style API directos, sinks de fragmentos HTML y cobertura de todas
  las acciones declarativas;
- protección declarada de todas las rutas comerciales salvo fronteras públicas
  y operaciones de backup exclusivas de SQLite local;
- ausencia de escrituras empresariales directas en rutas `GET` y sincronización
  de vencimientos/PDF/onboarding mediante `POST`;
- bloqueo del backend de objetos para membresías de solo lectura antes de
  cualquier efecto externo;
- bloqueo `429`, `Retry-After`, separación por IP y exclusión de lecturas/rutas
  no protegidas en el límite de Auth.

Este avance no sustituye una revisión independiente, la validación CSP en
navegador HTTPS, el rate limiting distribuido, ni las pruebas reales de
Auth/Storage/RLS con un rol PostgreSQL no privilegiado.
