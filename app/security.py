"""Frontera HTTP browser-first: CSRF por origen y cabeceras defensivas."""
from __future__ import annotations

from urllib.parse import urlsplit

from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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
            await response(scope, receive, self._send_with_headers(scope, headers, send))
            return

        await self.app(scope, receive, self._send_with_headers(scope, headers, send))

    def _send_with_headers(self, scope: Scope, request_headers: dict[str, str], send: Send):
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
                        b"script-src 'self' 'unsafe-inline'; "
                        b"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                        b"font-src 'self' https://fonts.gstatic.com data:; "
                        b"img-src 'self' data: blob:; connect-src 'self'; "
                        b"frame-src 'self' blob:"
                    ),
                }
                if scheme == "https":
                    additions[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                raw = list(message.get("headers", []))
                raw.extend((key, value) for key, value in additions.items() if key not in existing)
                message["headers"] = raw
            await send(message)

        return send_secure
