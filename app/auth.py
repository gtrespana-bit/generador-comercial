"""Integración mínima y portable con Supabase Auth.

El navegador nunca recibe la clave secreta del proyecto. El backend usa la
clave publicable únicamente para hablar con GoTrue y conserva access/refresh
tokens en cookies HttpOnly. La autorización de datos sigue dependiendo de la
membresía que CotizaT guarda en PostgreSQL.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest, urlopen
from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

ACCESS_COOKIE = "cotizat_access_token"
REFRESH_COOKIE = "cotizat_refresh_token"
ORGANIZATION_COOKIE = "cotizat_organization_id"


class AuthError(RuntimeError):
    """Error de autenticación que se puede mostrar sin filtrar secretos."""


class AuthNotConfigured(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class AuthenticationRequired(AuthError):
    pass


class OrganizationRequired(AuthError):
    pass


class OrganizationAccessDenied(AuthError):
    pass


@dataclass(frozen=True)
class SupabaseAuthSettings:
    url: str
    publishable_key: str
    cookie_secure: bool

    @classmethod
    def from_environment(cls) -> "SupabaseAuthSettings":
        url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
        key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        secure_raw = os.environ.get("COTIZAT_COOKIE_SECURE", "").strip().lower()
        cookie_secure = secure_raw not in {"0", "false", "no"}
        if not url or not key:
            raise AuthNotConfigured(
                "Supabase Auth todavía no está configurado en el servidor."
            )
        if not key.startswith("sb_publishable_"):
            raise AuthNotConfigured(
                "SUPABASE_PUBLISHABLE_KEY debe usar una clave sb_publishable_."
            )
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
            raise AuthNotConfigured("SUPABASE_URL no es una URL HTTPS válida.")
        return cls(url=url, publishable_key=key, cookie_secure=cookie_secure)


@dataclass(frozen=True)
class SupabaseIdentity:
    auth_user_id: str
    email: str
    name: str = ""
    email_verified: bool = False


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    identity: SupabaseIdentity


@dataclass(frozen=True)
class SignupResult:
    identity: SupabaseIdentity
    tokens: AuthTokens | None


def _identity_from_payload(payload: dict[str, Any]) -> SupabaseIdentity:
    raw_id = str(payload.get("id") or "").strip()
    try:
        auth_user_id = str(UUID(raw_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise InvalidCredentials("Supabase devolvió una identidad no válida.") from exc
    email = str(payload.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise InvalidCredentials("La cuenta autenticada no tiene un email válido.")
    metadata = payload.get("user_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    name = str(
        metadata.get("name")
        or metadata.get("full_name")
        or metadata.get("nombre")
        or ""
    ).strip()[:200]
    verified = bool(payload.get("email_confirmed_at") or payload.get("confirmed_at"))
    return SupabaseIdentity(auth_user_id, email, name, verified)


def _tokens_from_payload(payload: dict[str, Any]) -> AuthTokens:
    access_token = str(payload.get("access_token") or "").strip()
    refresh_token = str(payload.get("refresh_token") or "").strip()
    user = payload.get("user")
    if not access_token or not refresh_token or not isinstance(user, dict):
        raise InvalidCredentials("Supabase no devolvió una sesión válida.")
    try:
        expires_in = max(60, int(payload.get("expires_in") or 3600))
    except (TypeError, ValueError):
        expires_in = 3600
    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        identity=_identity_from_payload(user),
    )


class SupabaseAuthClient:
    """Cliente pequeño para GoTrue sin incorporar el SDK completo al runtime."""

    def __init__(self, settings: SupabaseAuthSettings | None = None):
        self.settings = settings or SupabaseAuthSettings.from_environment()

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        access_token: str = "",
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "apikey": self.settings.publishable_key,
            "Accept": "application/json",
            "User-Agent": "CotizaT/1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        request = UrlRequest(
            f"{self.settings.url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=12) as response:  # noqa: S310 (URL validada)
                raw = response.read(1024 * 1024)
        except HTTPError as exc:
            # El detalle de GoTrue no contiene la contraseña, pero se reduce a
            # mensajes propios para no depender de su respuesta interna.
            if exc.code in {400, 401, 403, 422}:
                raise InvalidCredentials("Email, contraseña o sesión no válidos.") from exc
            raise AuthError("Supabase Auth no pudo completar la solicitud.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AuthError("No se pudo contactar con Supabase Auth.") from exc
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise AuthError("Supabase Auth devolvió una respuesta no válida.") from exc
        if not isinstance(result, dict):
            raise AuthError("Supabase Auth devolvió una respuesta no válida.")
        return result

    def sign_in(self, email: str, password: str) -> AuthTokens:
        email = email.strip().lower()
        if not email or not password:
            raise InvalidCredentials("Escribe tu email y contraseña.")
        payload = self._request_json(
            "POST",
            "/auth/v1/token?grant_type=password",
            {"email": email, "password": password},
        )
        return _tokens_from_payload(payload)

    def sign_up(self, email: str, password: str, name: str = "") -> SignupResult:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise InvalidCredentials("Escribe un email válido.")
        if len(password) < 8:
            raise InvalidCredentials("La contraseña debe tener al menos 8 caracteres.")
        payload = self._request_json(
            "POST",
            "/auth/v1/signup",
            {"email": email, "password": password, "data": {"name": name.strip()[:200]}},
        )
        user = payload.get("user")
        if not isinstance(user, dict):
            raise InvalidCredentials("Supabase no pudo crear la cuenta.")
        identity = _identity_from_payload(user)
        if payload.get("access_token") and payload.get("refresh_token"):
            return SignupResult(identity, _tokens_from_payload(payload))
        return SignupResult(identity, None)

    def get_user(self, access_token: str) -> SupabaseIdentity:
        if not access_token:
            raise AuthenticationRequired("Inicia sesión para continuar.")
        payload = self._request_json("GET", "/auth/v1/user", access_token=access_token)
        return _identity_from_payload(payload)

    def refresh(self, refresh_token: str) -> AuthTokens:
        if not refresh_token:
            raise AuthenticationRequired("Inicia sesión para continuar.")
        payload = self._request_json(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )
        return _tokens_from_payload(payload)


def set_auth_cookies(response: Response, tokens: AuthTokens, secure: bool) -> None:
    common = {
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        ACCESS_COOKIE,
        tokens.access_token,
        max_age=tokens.expires_in,
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=60 * 60 * 24 * 30,
        **common,
    )


def clear_auth_cookies(response: Response, secure: bool = True) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, ORGANIZATION_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )


def identity_for_request(request: Request) -> SupabaseIdentity:
    """Valida la sesión y la renueva una vez cuando el access token caducó."""
    cached = getattr(request.state, "supabase_identity", None)
    if isinstance(cached, SupabaseIdentity):
        return cached
    client = SupabaseAuthClient()
    access_token = request.cookies.get(ACCESS_COOKIE, "")
    try:
        identity = client.get_user(access_token)
    except (InvalidCredentials, AuthenticationRequired):
        refresh_token = request.cookies.get(REFRESH_COOKIE, "")
        if not refresh_token:
            raise AuthenticationRequired("Inicia sesión para continuar.")
        try:
            tokens = client.refresh(refresh_token)
        except AuthError as exc:
            raise AuthenticationRequired("Tu sesión terminó. Vuelve a iniciar sesión.") from exc
        request.state.cotizat_refreshed_tokens = tokens
        identity = tokens.identity
    request.state.supabase_identity = identity
    return identity


class RefreshedAuthCookieMiddleware(BaseHTTPMiddleware):
    """Escribe los tokens renovados después de resolver las dependencias."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        tokens = getattr(request.state, "cotizat_refreshed_tokens", None)
        if isinstance(tokens, AuthTokens):
            try:
                secure = SupabaseAuthSettings.from_environment().cookie_secure
            except AuthNotConfigured:
                secure = True
            set_auth_cookies(response, tokens, secure)
        return response
