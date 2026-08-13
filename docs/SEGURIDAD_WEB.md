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

## Límite deliberado de CSP

La interfaz heredada contiene scripts y estilos inline. Para no romper el
constructor, la CSP transitoria permite `'unsafe-inline'` en `script-src` y
`style-src`; fuentes de Google están limitadas a sus hosts oficiales. Esto
impide plugins, objetos, framing y conexiones arbitrarias, pero **no constituye
la CSP final contra XSS**.

Antes de publicar se deben extraer handlers/scripts inline o introducir nonces,
eliminar `'unsafe-inline'`, revisar plantillas con datos del usuario y ejecutar
pruebas en el despliegue HTTPS real.

## Pruebas

`tests/test_web_security.py` cubre:

- Origin exacto permitido;
- fallback a Referer same-origin;
- Origin/Fetch Metadata cross-site rechazado;
- escritura sin procedencia rechazada;
- cabeceras defensivas y HSTS;
- conservación de la CSP sandbox de archivos.

Este avance no sustituye la auditoría pendiente de XSS, rate limiting, sesiones,
roles PostgreSQL no privilegiados ni pruebas reales de Auth/Storage.
