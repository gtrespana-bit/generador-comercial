"""Frontera HTTP browser-first: CSRF por origen y cabeceras defensivas."""
from __future__ import annotations

import ipaddress
import os
import secrets
from urllib.parse import urlsplit

from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .ratelimit import MemoryRateLimit, RateLimitBackend, build_rate_limiter

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

#: Valores que se interpretan como «confiar en el proxy» para
#: ``COTIZAT_TRUST_PROXY``. Es la ÚNICA fuente de verdad: tanto
#: ``confia_en_proxy()`` (auditoría/IP del registro) como el middleware de
#: rate-limit resuelven aquí, para que ambas decisiones nunca divergan.
_VALORES_VERDADEROS_PROXY = frozenset({"1", "true", "yes", "on", "si", "sí"})

#: Escrituras que no vienen del navegador. El webhook de Stripe firma el
#: cuerpo con ``Stripe-Signature``; exigirle Origin same-origin lo rompería.
_CSRF_EXENTAS = frozenset({"/pago/stripe/webhook"})


def _antecesores_permitidos() -> tuple[bytes, bytes | None]:
    """Quién puede embeber la aplicación en un iframe.

    Por defecto, nadie: `frame-ancestors 'none'` y `X-Frame-Options: DENY`,
    que es lo correcto en producción para cerrar el clickjacking.

    `COTIZAT_FRAME_ANCESTORS` permite abrir una excepción concreta cuando la
    aplicación se sirve dentro de un panel de vista previa o de una demo
    embebida. Se indica la lista de orígenes tal cual la espera CSP, por
    ejemplo `https://*.e2b.app`. Nunca se acepta un comodín total.
    """
    valor = (os.environ.get("COTIZAT_FRAME_ANCESTORS") or "").strip()
    if not valor or valor == "*":
        return b"'none'", b"DENY"
    origenes = " ".join(valor.split())
    # Con una excepción activa, X-Frame-Options sobra: es más restrictivo que
    # CSP y no entiende comodines, así que bloquearía igualmente.
    return origenes.encode("ascii", "ignore"), None


def _destinos_formulario() -> bytes:
    """A dónde pueden enviarse los formularios (directiva ``form-action``).

    La base es ``'self'``, pero Chrome aplica ``form-action`` también a cada
    redirección de la cadena de envío, no solo al destino inicial. Eso obliga
    a dos excepciones:

    - ``checkout.stripe.com``: el POST de "Pagar con tarjeta" responde 303
      hacia la página de Checkout de Stripe. Sin este origen, Chrome bloquea
      el pago con "violates form-action 'self'". Solo se añade con Stripe
      configurado; sin clave no existe esa redirección.
    - El origen canónico (``COTIZAT_PUBLIC_URL``): si el usuario navega por un
      alias del dominio (p. ej. sin ``www``) y el hosting redirige el POST al
      dominio canónico, esa redirección cruza de origen y caería en el mismo
      bloqueo.
    """
    destinos = ["'self'"]
    publico = (os.environ.get("COTIZAT_PUBLIC_URL") or "").strip().rstrip("/")
    if publico:
        try:
            parsed = urlsplit(publico)
        except ValueError:
            parsed = None
        if (
            parsed
            and parsed.scheme == "https"
            and parsed.netloc
            and not parsed.username
            and not parsed.password
        ):
            destinos.append(f"https://{parsed.netloc}")
    if (os.environ.get("STRIPE_SECRET_KEY") or "").strip():
        destinos.append("https://checkout.stripe.com")
    return " ".join(destinos).encode("ascii", "ignore")


def confia_en_proxy() -> bool:
    """¿Se puede creer la cabecera ``X-Forwarded-For``?

    Solo detrás de un proxy propio que la reescriba (Vercel). Expuesto
    directamente a internet, cualquiera la falsifica y la IP deja de valer
    nada.

    Usa la misma lista de valores que el middleware de rate-limit
    (``_VALORES_VERDADEROS_PROXY``), de modo que la IP de auditoría y la de
    limitación nunca diverjan por interpretar distinto el mismo flag.
    """
    return (
        os.environ.get("COTIZAT_TRUST_PROXY", "").strip().lower()
        in _VALORES_VERDADEROS_PROXY
    )


def _resolver_ip(cabecera: str, host: str, confiar: bool, defecto: str) -> str:
    """Criterio único para decidir la IP de origen de una petición.

    Es una función suelta, y no un método, porque tiene dos llamantes con
    formas muy distintas: el middleware de rate limit trabaja sobre el `scope`
    ASGI crudo y con una bandera de confianza inyectada, mientras que
    `ip_de_request` recibe un `Request` ya construido y lee el entorno. Lo que
    no puede divergir entre ambos es la decisión: si se cree o no la cabecera
    reenviada, y qué se hace cuando trae basura.

    La cabecera solo se acepta si además parsea como IP. Un `X-Forwarded-For`
    con texto arbitrario cae al cliente directo en lugar de convertirse en una
    clave de contador inventada por el atacante.
    """
    cabecera = (cabecera or "").split(",", 1)[0].strip()
    if confiar and cabecera:
        try:
            return str(ipaddress.ip_address(cabecera))
        except ValueError:
            pass
    return str(host or "") or defecto


def ip_de_request(request) -> str:
    """IP de quien hace la petición, con el mismo criterio que el rate limit.

    Vive fuera del middleware porque hay más sitios que necesitan la IP —el
    registro de pruebas gratuitas la guarda hasheada— y duplicar la lógica de
    confianza en el proxy sería la forma segura de que un día divergieran.

    Devuelve cadena vacía si no se puede determinar: quien la use debe tratar
    la ausencia como un dato normal, no como un error.
    """
    try:
        cabecera = request.headers.get("x-forwarded-for", "")
    except Exception:
        cabecera = ""
    cliente = getattr(request, "client", None)
    return _resolver_ip(
        cabecera,
        str(getattr(cliente, "host", "") or ""),
        confia_en_proxy(),
        defecto="",
    )


class AuthRateLimitMiddleware:
    """Límite por IP y ruta para endpoints de credenciales y recuperación.

    El contador vive en un backend intercambiable (`app/ratelimit.py`). Con
    `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` configuradas se
    comparte entre instancias, que es lo que exige un despliegue serverless
    como Vercel: allí cada invocación puede usar un proceso nuevo, y un
    contador en memoria se reinicia constantemente sin llegar a limitar nada.

    Sin esas variables se usa el contador en memoria de siempre, adecuado para
    el modo escritorio y para desarrollo local.
    """

    DEFAULT_LIMITS = {
        "/acceso": 10,
        "/registro": 5,
        "/recuperar-acceso": 5,
        "/restablecer-clave": 10,
        # Verifica la contraseña actual: sin límite, una sesión robada podría
        # usarse para adivinarla por fuerza bruta desde el propio panel.
        "/cuenta/clave": 10,
        # Formulario público de demo: evita que un bot inunde el buzón de
        # soporte con solicitudes falsas.
        "/demo": 3,
        # Crear sesiones de Stripe: evita que un bot abra cientos de checkouts.
        "/pago/stripe/checkout": 10,
    }

    def __init__(
        self,
        app: ASGIApp,
        limits: dict[str, int] | None = None,
        window_seconds: int = 300,
        trust_forwarded_for: bool = False,
        max_buckets: int = 10_000,
        backend: RateLimitBackend | None = None,
    ):
        self.app = app
        self.limits = dict(limits or self.DEFAULT_LIMITS)
        self.window_seconds = max(1, int(window_seconds))
        self.trust_forwarded_for = trust_forwarded_for
        self.max_buckets = max(1, int(max_buckets))
        # `build_rate_limiter()` decide según el entorno; se puede inyectar un
        # backend concreto en pruebas o en el modo escritorio.
        self.backend = backend or build_rate_limiter()
        if isinstance(self.backend, MemoryRateLimit):
            self.backend.max_buckets = self.max_buckets

    def _client_ip(self, scope: Scope, headers: dict[str, str]) -> str:
        """Clave de contador para esta petición.

        Comparte criterio con `ip_de_request` a través de `_resolver_ip`. El
        defecto es "unknown" y no cadena vacía porque aquí la IP se usa como
        clave: todas las peticiones sin cliente identificable deben caer en el
        mismo cubo y limitarse juntas, en vez de repartirse por una clave vacía
        que se confundiría con otra ruta.
        """
        client = scope.get("client")
        return _resolver_ip(
            headers.get("x-forwarded-for", ""),
            str(client[0]) if client else "",
            self.trust_forwarded_for,
            defecto="unknown",
        )

    def _permitido(self, key: tuple[str, str], limit: int) -> tuple[bool, int]:
        path, ip = key
        decision = self.backend.hit(f"{path}|{ip}", limit, self.window_seconds)
        return decision.permitido, decision.reintentar_en

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or str(scope.get("method", "GET")).upper() != "POST":
            await self.app(scope, receive, send)
            return
        path = str(scope.get("path", ""))
        limit = self.limits.get(path)
        if not limit:
            await self.app(scope, receive, send)
            return
        headers = WebSecurityMiddleware._headers(scope)
        allowed, retry = self._permitido((path, self._client_ip(scope, headers)), limit)
        if allowed:
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            {"ok": False, "error": "Demasiados intentos. Espera antes de volver a intentarlo."},
            status_code=429,
            headers={"Retry-After": str(retry)},
        )
        await response(scope, receive, send)


class WebSecurityMiddleware:
    """Bloquea escrituras cross-site y añade cabeceras a toda respuesta.

    En el despliegue PostgreSQL todas las escrituras son browser-first. Se
    exige Origin/Referer same-origin y se rechaza explícitamente Fetch Metadata
    cross-site. SQLite local puede desactivar CSRF porque no expone cuentas web.
    """

    def __init__(self, app: ASGIApp, enforce_csrf: bool = True):
        self.app = app
        self.enforce_csrf = enforce_csrf

    @staticmethod
    def _headers(scope: Scope) -> dict[str, str]:
        return {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

    @staticmethod
    def _scheme(scope: Scope, headers: dict[str, str]) -> str:
        forwarded = headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
        return forwarded if forwarded in {"http", "https"} else str(scope.get("scheme", "http"))

    @classmethod
    def _same_origin(cls, value: str, scope: Scope, headers: dict[str, str]) -> bool:
        try:
            parsed = urlsplit(value)
        except ValueError:
            return False
        host = headers.get("host", "").strip().lower()
        return bool(
            parsed.scheme in {"http", "https"}
            and parsed.scheme == cls._scheme(scope, headers)
            and parsed.netloc.lower() == host
            and not parsed.username
            and not parsed.password
        )

    @classmethod
    def _csrf_valido(cls, scope: Scope, headers: dict[str, str]) -> bool:
        fetch_site = headers.get("sec-fetch-site", "").strip().lower()
        if fetch_site in {"cross-site", "none"}:
            return False
        origin = headers.get("origin", "").strip()
        if origin:
            return cls._same_origin(origin, scope, headers)
        referer = headers.get("referer", "").strip()
        return bool(referer and cls._same_origin(referer, scope, headers))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = self._headers(scope)
        nonce = secrets.token_urlsafe(18)
        scope.setdefault("state", {})["csp_nonce"] = nonce
        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", ""))
        if (
            self.enforce_csrf
            and method in _UNSAFE_METHODS
            and path not in _CSRF_EXENTAS
            and not self._csrf_valido(scope, headers)
        ):
            accept = headers.get("accept", "")
            if "application/json" in accept or headers.get("content-type", "").startswith("application/json"):
                response = JSONResponse(
                    {"ok": False, "error": "La solicitud fue bloqueada por protección CSRF."},
                    status_code=403,
                )
            else:
                response = PlainTextResponse(
                    "Solicitud bloqueada por protección CSRF.", status_code=403
                )
            await response(
                scope, receive, self._send_with_headers(scope, headers, nonce, send)
            )
            return

        await self.app(
            scope, receive, self._send_with_headers(scope, headers, nonce, send)
        )

    def _send_with_headers(
        self,
        scope: Scope,
        request_headers: dict[str, str],
        nonce: str,
        send: Send,
    ):
        scheme = self._scheme(scope, request_headers)

        async def send_secure(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {key.lower() for key, _value in message.get("headers", [])}
                antecesores, x_frame = _antecesores_permitidos()
                additions = {
                    b"x-content-type-options": b"nosniff",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"cross-origin-opener-policy": b"same-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"content-security-policy": (
                        b"default-src 'self'; base-uri 'self'; object-src 'none'; "
                        + b"frame-ancestors " + antecesores + b"; "
                        + b"form-action " + _destinos_formulario() + b"; "
                        + f"script-src 'self' 'nonce-{nonce}'; ".encode("ascii")
                        + b"script-src-attr 'none'; "
                        + f"style-src 'self' 'nonce-{nonce}'; ".encode("ascii")
                        + b"style-src-attr 'none'; "
                        + b"font-src 'self' data:; "
                        + b"img-src 'self' data: blob:; connect-src 'self'; "
                        + b"frame-src 'self' blob:"
                    ),
                }
                if x_frame:
                    additions[b"x-frame-options"] = x_frame
                if scheme == "https":
                    additions[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                path = str(scope.get("path") or "")
                try:
                    from .seo import es_indexable

                    if not es_indexable(path):
                        additions[b"x-robots-tag"] = b"noindex, nofollow, noarchive"
                except Exception:
                    pass
                raw = list(message.get("headers", []))
                raw.extend((key, value) for key, value in additions.items() if key not in existing)
                message["headers"] = raw
            await send(message)

        return send_secure
