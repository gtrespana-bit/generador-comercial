"""Integración mínima y portable con Supabase Auth.

El navegador nunca recibe la clave secreta del proyecto. El backend usa la
clave publicable únicamente para hablar con GoTrue y conserva access/refresh
tokens en cookies HttpOnly. La autorización de datos sigue dependiendo de la
membresía que CotizaT guarda en PostgreSQL.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import http.client
import json
import logging
import os
import threading
import time
from typing import Any
from urllib.parse import quote, urlparse
from uuid import UUID

log = logging.getLogger("cotizat")

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

ACCESS_COOKIE = "cotizat_access_token"
REFRESH_COOKIE = "cotizat_refresh_token"
ORGANIZATION_COOKIE = "cotizat_organization_id"

#: Segundos que se reutiliza una identidad ya validada por red con el mismo
#: access token. Evita un viaje completo a GoTrue (DNS+TCP+TLS+petición) en
#: CADA página; 0 desactiva la caché. La expiración propia del JWT manda:
#: nunca se cachea más allá del 90 % de su vida útil restante.
AUTH_CACHE_TTL = float(os.environ.get("COTIZAT_AUTH_CACHE_TTL", "180"))
_AUTH_CACHE: dict[str, tuple[float, "SupabaseIdentity"]] = {}
_AUTH_CACHE_MAX = 512
_AUTH_CACHE_BLOQUEO = threading.Lock()


def _reset_cache_identidades() -> None:
    """Vacía la caché de identidades (pruebas y cambios de configuración)."""
    with _AUTH_CACHE_BLOQUEO:
        _AUTH_CACHE.clear()


def _exp_jwt(token: str) -> float | None:
    """Lee ``exp`` del payload del JWT sin verificar la firma (solo caché)."""
    try:
        segmento = token.split(".")[1]
        segmento += "=" * (-len(segmento) % 4)
        from base64 import urlsafe_b64decode

        payload = json.loads(urlsafe_b64decode(segmento.encode("ascii")))
        exp = payload.get("exp")
        return float(exp) if isinstance(exp, (int, float)) else None
    except Exception:
        return None


def _identidad_en_cache(token: str) -> "SupabaseIdentity | None":
    if AUTH_CACHE_TTL <= 0 or not token:
        return None
    clave = hashlib.sha256(token.encode("utf-8")).hexdigest()
    ahora = time.monotonic()
    with _AUTH_CACHE_BLOQUEO:
        entrada = _AUTH_CACHE.get(clave)
        if entrada is None:
            return None
        vence_cache, identidad = entrada
        if ahora >= vence_cache:
            _AUTH_CACHE.pop(clave, None)
            return None
        return identidad


def _guardar_identidad_en_cache(token: str, identidad: "SupabaseIdentity") -> None:
    if AUTH_CACHE_TTL <= 0 or not token:
        return
    ttl = AUTH_CACHE_TTL
    exp = _exp_jwt(token)
    if exp is not None:
        vida_restante = exp - time.time()
        if vida_restante <= 30:
            return  # caduca en breve: no merece caché
        ttl = min(ttl, vida_restante * 0.9)
    clave = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _AUTH_CACHE_BLOQUEO:
        if len(_AUTH_CACHE) >= _AUTH_CACHE_MAX:
            ahora = time.monotonic()
            vencidas = [k for k, (v, _i) in _AUTH_CACHE.items() if v <= ahora]
            for k in vencidas or list(_AUTH_CACHE)[: max(1, _AUTH_CACHE_MAX // 4)]:
                _AUTH_CACHE.pop(k, None)
        _AUTH_CACHE[clave] = (time.monotonic() + ttl, identidad)


def _parece_jwt(value: str) -> bool:
    """Comprobación de formato, no de firma (la valida Supabase).

    Las claves API de proyectos antiguos son JWT (``eyJ…``) con tres
    segmentos base64url. Las claves nuevas usan prefijos ``sb_*_``.
    """
    parts = value.split(".")
    if len(parts) != 3:
        return False
    return bool(
        all(parts)
        and all(ch.isascii() and (ch.isalnum() or ch in "-_.") for ch in value)
    )


def es_clave_publicable(key: str) -> bool:
    """Una clave publicable puede ser ``sb_publishable_…`` o un JWT ``anon``."""
    return key.startswith("sb_publishable_") or _parece_jwt(key)


def es_clave_secreta_servidor(key: str) -> bool:
    """Una clave secreta de servidor puede ser ``sb_secret_…`` o un JWT legacy.

    El JWT legacy ``service_role`` es secreto: nunca debe llegar al navegador.
    """
    return key.startswith("sb_secret_") or _parece_jwt(key)


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
        if not es_clave_publicable(key):
            raise AuthNotConfigured(
                "SUPABASE_PUBLISHABLE_KEY debe usar una clave sb_publishable_ "
                "o el JWT anon público del proyecto."
            )
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
            raise AuthNotConfigured("SUPABASE_URL no es una URL HTTPS válida.")
        return cls(url=url, publishable_key=key, cookie_secure=cookie_secure)


def public_app_url(path: str) -> str:
    """Construye una URL desde el origen HTTPS fijo, nunca desde ``Host``."""
    public_url = os.environ.get("COTIZAT_PUBLIC_URL", "").strip().rstrip("/")
    try:
        parsed = urlparse(public_url)
    except ValueError as exc:
        raise AuthNotConfigured("COTIZAT_PUBLIC_URL no es válida.") from exc
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise AuthNotConfigured(
            "COTIZAT_PUBLIC_URL debe ser el origen HTTPS público de CotizaT."
        )
    path = str(path or "")
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        raise AuthNotConfigured("La ruta pública de CotizaT no es válida.")
    return public_url + path


def password_reset_redirect_url() -> str:
    """URL pública fija y autorizable en Supabase para recuperar contraseña."""
    return public_app_url("/restablecer-clave")


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
    #: GoTrue devuelve un usuario "obfuscado" (sin identidades) cuando el email
    #: ya estaba registrado y la confirmación por email está activa, para no
    #: revelar qué direcciones existen. No se ha creado ninguna cuenta nueva.
    ya_registrado: bool = False


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

    #: Conexión HTTP reutilizable por hilo. ``urlopen`` abre una conexión
    #: nueva (DNS + TCP + TLS) por petición; con keep-alive, las llamadas
    #: repetidas a GoTrue dentro del mismo proceso viajan por la misma
    #: conexión y tardan milisegundos en vez de centenas de ellos.
    _conexiones = threading.local()

    def __init__(self, settings: SupabaseAuthSettings | None = None):
        self.settings = settings or SupabaseAuthSettings.from_environment()

    def _conexion(self) -> http.client.HTTPSConnection:
        destino = urlparse(self.settings.url)
        conexion = getattr(self._conexiones, "actual", None)
        marca = (destino.scheme, destino.hostname, destino.port)
        if conexion is not None and getattr(conexion, "marca", None) == marca:
            return conexion
        if conexion is not None:
            try:
                conexion.close()
            except Exception:
                pass
        if destino.scheme == "http":
            nueva = http.client.HTTPConnection(destino.hostname, destino.port or 80, timeout=12)
        else:
            nueva = http.client.HTTPSConnection(destino.hostname, destino.port or 443, timeout=12)
        nueva.marca = marca  # type: ignore[attr-defined]
        self._conexiones.actual = nueva
        return nueva

    def _cerrar_conexion(self) -> None:
        conexion = getattr(self._conexiones, "actual", None)
        self._conexiones.actual = None
        if conexion is not None:
            try:
                conexion.close()
            except Exception:
                pass

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
            "Connection": "keep-alive",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        for intento in (0, 1):
            conexion = self._conexion()
            try:
                conexion.request(method, path, body=body, headers=headers)
                respuesta = conexion.getresponse()
                estado = respuesta.status
                raw = respuesta.read(1024 * 1024)
                break
            except (http.client.HTTPException, OSError):
                # La conexión keep-alive puede estar muerta (timeout del
                # servidor o reciclaje del proceso): se descarta y se reintenta
                # UNA vez con conexión nueva antes de declarar el fallo.
                self._cerrar_conexion()
                if intento:
                    raise AuthError("No se pudo contactar con Supabase Auth.") from None
        else:  # pragma: no cover - el bucle siempre termina en break o raise
            raise AuthError("No se pudo contactar con Supabase Auth.")

        if not (200 <= estado < 300):
            # El detalle de GoTrue no contiene la contraseña ni el token en
            # claro, pero revela la causa real (otp_expired, email no
            # confirmado, credenciales inválidas…). Se registra en el log del
            # servidor para poder diagnosticar, y al usuario se le sigue
            # mostrando un mensaje propio que no filtra nada.
            log.warning(
                "Supabase Auth %s %s -> HTTP %s: %s",
                method,
                path,
                estado,
                (raw[:300].decode("utf-8", "replace") or "(sin cuerpo)"),
            )
            if estado in {400, 401, 403, 422}:
                raise InvalidCredentials("Email, contraseña o sesión no válidos.")
            raise AuthError("Supabase Auth no pudo completar la solicitud.")
        if not raw.strip():
            # ``/auth/v1/logout`` responde 204 sin cuerpo: no es un error.
            return {}
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

    def sign_up(
        self, email: str, password: str, name: str = "", redirect_to: str = ""
    ) -> SignupResult:
        """Crea la identidad en Supabase Auth.

        Igual que en ``/auth/v1/recover``, ``redirect_to`` va en la query:
        ``SignupParams`` tampoco lo declara en el cuerpo. Sin esto, el email
        de confirmación llevaría al Site URL en lugar de a la app.
        """
        email = email.strip().lower()
        if not email or "@" not in email:
            raise InvalidCredentials("Escribe un email válido.")
        if len(password) < 8:
            raise InvalidCredentials("La contraseña debe tener al menos 8 caracteres.")
        ruta = "/auth/v1/signup"
        if redirect_to:
            parsed = urlparse(redirect_to)
            if parsed.scheme != "https" or not parsed.netloc:
                raise AuthNotConfigured("La URL de confirmación no es válida.")
            ruta += f"?redirect_to={quote(redirect_to, safe='')}"
        payload = self._request_json(
            "POST",
            ruta,
            {"email": email, "password": password, "data": {"name": name.strip()[:200]}},
        )
        # ``/auth/v1/signup`` responde 200 con TRES formas distintas
        # (internal/api/signup.go), y solo una anida el usuario bajo "user":
        #
        # 1. Autoconfirm activo: ``sendJSON(w, 200, token)`` -> AccessTokenResponse
        #    con access_token, refresh_token y "user" anidado.
        # 2. Confirmación por email activa y alta nueva: ``sendJSON(w, 200, user)``
        #    -> el usuario va EN LA RAÍZ, sin envoltorio ni tokens.
        # 3. Email ya registrado sin confirmar: ``sendJSON(w, 200, sanitizedUser)``
        #    -> también en la raíz, con un id falso y "identities": [].
        #
        # Leer siempre ``payload["user"]`` rompía el registro entero en cuanto
        # el proyecto exigía confirmar el email: los casos 2 y 3 acababan en
        # "Supabase no pudo crear la cuenta" pese a ser respuestas correctas.
        user = payload.get("user")
        if not isinstance(user, dict):
            user = payload
        identity = _identity_from_payload(user)
        if payload.get("access_token") and payload.get("refresh_token"):
            return SignupResult(identity, _tokens_from_payload(payload))
        # Usuario obfuscado: GoTrue vacía "identities" para no filtrar si el
        # email existe. Se distingue del alta real, que trae su identidad.
        identities = user.get("identities")
        ya_registrado = isinstance(identities, list) and not identities
        return SignupResult(identity, None, ya_registrado=ya_registrado)

    def request_password_reset(self, email: str, redirect_to: str) -> None:
        """Pide a GoTrue el email de recuperación.

        ``redirect_to`` viaja en la QUERY STRING, no en el cuerpo JSON. El
        struct ``RecoverParams`` de GoTrue solo declara ``email``,
        ``code_challenge`` y ``code_challenge_method``: un ``redirect_to``
        dentro del JSON se descarta en silencio y el enlace del email acaba
        apuntando al Site URL, aunque la ruta esté autorizada en Supabase.
        El cliente oficial (auth-js) también lo envía como parámetro de URL.
        """
        email = email.strip().lower()
        if not email or "@" not in email:
            raise InvalidCredentials("Escribe un email válido.")
        parsed = urlparse(redirect_to)
        if parsed.scheme != "https" or not parsed.netloc:
            raise AuthNotConfigured("La URL de recuperación no es válida.")
        self._request_json(
            "POST",
            f"/auth/v1/recover?redirect_to={quote(redirect_to, safe='')}",
            {"email": email},
        )

    def update_password(self, access_token: str, password: str) -> SupabaseIdentity:
        if not access_token:
            raise AuthenticationRequired("El enlace de recuperación no es válido.")
        if len(password) < 8:
            raise InvalidCredentials("La contraseña debe tener al menos 8 caracteres.")
        payload = self._request_json(
            "PUT", "/auth/v1/user", {"password": password}, access_token=access_token
        )
        return _identity_from_payload(payload)

    def update_profile(self, access_token: str, name: str) -> SupabaseIdentity:
        """Actualiza ``user_metadata.name`` sin tocar email ni contraseña."""
        if not access_token:
            raise AuthenticationRequired("Inicia sesión para continuar.")
        payload = self._request_json(
            "PUT",
            "/auth/v1/user",
            {"data": {"name": str(name or "").strip()[:200]}},
            access_token=access_token,
        )
        return _identity_from_payload(payload)

    def change_password(
        self, access_token: str, email: str, current_password: str, new_password: str
    ) -> SupabaseIdentity:
        """Cambia la contraseña reautenticando primero con la actual.

        GoTrue permite ``PUT /auth/v1/user`` solo con el access token, así que
        una sesión robada bastaría para secuestrar la cuenta. Reautenticar con
        ``grant_type=password`` obliga a demostrar que se conoce la contraseña
        vigente antes de sustituirla.
        """
        if not access_token:
            raise AuthenticationRequired("Inicia sesión para continuar.")
        if not current_password:
            raise InvalidCredentials("Escribe tu contraseña actual.")
        if len(new_password) < 8:
            raise InvalidCredentials("La contraseña debe tener al menos 8 caracteres.")
        if new_password == current_password:
            raise InvalidCredentials("La nueva contraseña debe ser distinta de la actual.")
        # Reautenticación: falla con InvalidCredentials si la actual no coincide.
        self.sign_in(email, current_password)
        return self.update_password(access_token, new_password)

    def sign_out(self, access_token: str) -> None:
        """Revoca la sesión en Supabase; el logout local no depende de esto."""
        if not access_token:
            return
        self._request_json("POST", "/auth/v1/logout", {}, access_token=access_token)

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


def clear_auth_cookies(
    response: Response, secure: bool = True, request: Request | None = None
) -> None:
    """Borra las cookies de sesión y cancela una renovación en curso.

    Si la petición renovó el access token al validar la identidad,
    :class:`RefreshedAuthCookieMiddleware` volvería a escribir las cookies
    después de este borrado y el usuario seguiría dentro. Al descartar los
    tokens pendientes, el cierre de sesión siempre gana.
    """
    if request is not None:
        # ``State`` delega en un dict: ausente lanza KeyError, no AttributeError.
        try:
            del request.state.cotizat_refreshed_tokens
        except (AttributeError, KeyError):
            pass
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, ORGANIZATION_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )


def identity_for_request(request: Request) -> SupabaseIdentity:
    """Valida la sesión y la renueva una vez cuando el access token caducó.

    La identidad verificada por red se reutiliza durante un tiempo corto
    (:data:`AUTH_CACHE_TTL`) mientras el token no esté a punto de caducar:
    sin esta caché, cada página paginaba un viaje completo a GoTrue.
    """
    cached = getattr(request.state, "supabase_identity", None)
    if isinstance(cached, SupabaseIdentity):
        return cached
    client = SupabaseAuthClient()
    access_token = request.cookies.get(ACCESS_COOKIE, "")
    identidad_cacheada = _identidad_en_cache(access_token)
    if identidad_cacheada is not None:
        request.state.supabase_identity = identidad_cacheada
        return identidad_cacheada
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
        # La renovación entrega un access token nuevo (ya en la cookie que
        # escribirá el middleware): cachearlo evita otra validación por red
        # en la siguiente petición.
        _guardar_identidad_en_cache(tokens.access_token, tokens.identity)
    request.state.supabase_identity = identity
    _guardar_identidad_en_cache(access_token, identity)
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
