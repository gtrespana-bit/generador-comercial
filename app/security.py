"""Frontera HTTP browser-first: CSRF por origen y cabeceras defensivas."""
from __future__ import annotations

from collections import deque
import ipaddress
import secrets
from threading import Lock
import time
from urllib.parse import urlsplit

from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuthRateLimitMiddleware:
    """Límite básico por IP para endpoints de credenciales y recuperación.

    Es deliberadamente local al proceso. Reduce abuso accidental y ráfagas,
    pero un despliegue con varias instancias necesitará Redis/Upstash o el
    rate limiter equivalente del proveedor.
    """

    DEFAULT_LIMITS = {
        "/acceso": 10,
        "/registro": 5,
        "/recuperar-acceso": 5,
        "/restablecer-clave": 10,
        # Verifica la contraseña actual: sin límite, una sesión robada podría
        # usarse para adivinarla por fuerza bruta desde el propio panel.
        "/cuenta/clave": 10,
    }

    def __init__(
        self,
        app: ASGIApp,
        limits: dict[str, int] | None = None,
        window_seconds: int = 300,
        trust_forwarded_for: bool = False,
        max_buckets: int = 10_000,
    ):
        self.app = app
        self.limits = dict(limits or self.DEFAULT_LIMITS)
        self.window_seconds = max(1, int(window_seconds))
        self.trust_forwarded_for = trust_forwarded_for
        self.max_buckets = max(1, int(max_buckets))
        self._attempts: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    def _client_ip(self, scope: Scope, headers: dict[str, str]) -> str:
        forwarded = headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        try:
            if self.trust_forwarded_for and forwarded:
                return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass
        client = scope.get("client")
        return str(client[0]) if client else "unknown"

    def _permitido(self, key: tuple[str, str], limit: int) -> tuple[bool, int]:
        now = time.monotonic()
        threshold = now - self.window_seconds
        with self._lock:
            if key not in self._attempts and len(self._attempts) >= self.max_buckets:
                stale = [
                    stored_key
                    for stored_key, values in self._attempts.items()
                    if not values or values[-1] <= threshold
                ]
                for stored_key in stale:
                    self._attempts.pop(stored_key, None)
                if len(self._attempts) >= self.max_buckets:
                    self._attempts.pop(next(iter(self._attempts)))
            attempts = self._attempts.setdefault(key, deque())
            while attempts and attempts[0] <= threshold:
                attempts.popleft()
            if len(attempts) >= limit:
                retry = max(1, int(self.window_seconds - (now - attempts[0])))
                return False, retry
            attempts.append(now)
            return True, 0

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
        if self.enforce_csrf and method in _UNSAFE_METHODS and not self._csrf_valido(scope, headers):
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
                additions = {
                    b"x-content-type-options": b"nosniff",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"x-frame-options": b"DENY",
                    b"cross-origin-opener-policy": b"same-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"content-security-policy": (
                        b"default-src 'self'; base-uri 'self'; object-src 'none'; "
                        b"frame-ancestors 'none'; form-action 'self'; "
                        + f"script-src 'self' 'nonce-{nonce}'; ".encode("ascii")
                        + b"script-src-attr 'none'; "
                        + f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com; ".encode("ascii")
                        + b"style-src-attr 'none'; "
                        + b"font-src 'self' https://fonts.gstatic.com data:; "
                        + b"img-src 'self' data: blob:; connect-src 'self'; "
                        + b"frame-src 'self' blob:"
                    ),
                }
                if scheme == "https":
                    additions[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                raw = list(message.get("headers", []))
                raw.extend((key, value) for key, value in additions.items() if key not in existing)
                message["headers"] = raw
            await send(message)

        return send_secure
