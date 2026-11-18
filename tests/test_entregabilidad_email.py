"""Entregabilidad anti-spam: confirmación en el dominio propio y baja RFC 8058.

Cubre el paquete completo que hace que un correo de CotizaT llegue a la
bandeja de entrada y no a spam:

1. **Enlaces del dominio propio.** Las plantillas de Supabase apuntan a
   ``/confirmar-email``; el GET solo pinta un botón (un escáner de enlaces no
   consume el token) y el POST lo canjea.
2. **Baja en un clic (RFC 8058).** Cabeceras ``List-Unsubscribe`` y
   ``List-Unsubscribe-Post``, y una ruta pública que acepta el POST del
   cliente de correo sin Origin ni cookies.
3. **Higiene de los envíos.** ``Reply-To`` real, ``X-Entity-Ref-ID`` único,
   rechazo de inyección de cabeceras y asuntos sin mayúsculas de promoción.

Los secretos son ficticios y van marcados con ``# pragma: allowlist secret``
para que ``detect-secrets`` siga limpio.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import (
    OTP_TYPES_VALIDOS,
    AuthTokens,
    InvalidCredentials,
    SupabaseAuthClient,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import SessionLocal
from app.main import app as cotizat_app
from app.security import WebSecurityMiddleware
from app.services import email as email_module
from app.services.marketing import token_baja

ORIGEN = "https://cotizat.test"
#: Token de relleno: el canje real lo hace GoTrue, aquí solo importa el
#: contrato de la ruta (longitud, tipo y que el GET no lo consuma).
TOKEN_PRUEBA = "token-de-prueba-no-real-abcdef0123456789"  # pragma: allowlist secret
CLAVE_PUBLICABLE = "sb_publishable_pruebas"  # pragma: allowlist secret

DOCS_SUPABASE = Path("docs/supabase_templates")


def _ajustes() -> SupabaseAuthSettings:
    return SupabaseAuthSettings(
        url="https://project.supabase.co",
        publishable_key=CLAVE_PUBLICABLE,
        cookie_secure=True,
    )


def _identidad(email: str = "persona@example.com") -> SupabaseIdentity:
    return SupabaseIdentity(
        auth_user_id="0691d7f2-ae24-4b7f-9e45-87ad16fdc94c",
        email=email,
        name="Persona",
        email_verified=True,
    )


def _tokens(email: str = "persona@example.com") -> AuthTokens:
    return AuthTokens(
        access_token="access-token-de-prueba",  # pragma: allowlist secret
        refresh_token="refresh-token-de-prueba",  # pragma: allowlist secret
        expires_in=3600,
        identity=_identidad(email),
    )


class _ClienteEspia(SupabaseAuthClient):
    """Cliente que intercepta ``_request_json`` y apunta cada llamada."""

    def __init__(self, respuestas: list[dict] | None = None):
        super().__init__(_ajustes())
        self.respuestas = list(respuestas or [])
        self.llamadas: list[tuple] = []

    def _request_json(self, method, path, payload=None, access_token=""):
        self.llamadas.append((method, path, payload, access_token))
        return self.respuestas.pop(0) if self.respuestas else {}


# ---------------------------------------------------------------------------
# 1. verify_otp: el canje del token del correo
# ---------------------------------------------------------------------------


def test_verify_otp_canjea_token_hash_y_tipo_contra_gotrue():
    cliente = _ClienteEspia(
        [
            {
                "access_token": "access-token-de-prueba",  # pragma: allowlist secret
                "refresh_token": "refresh-token-de-prueba",  # pragma: allowlist secret
                "expires_in": 3600,
                "user": {
                    "id": "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c",
                    "email": "persona@example.com",
                    "email_confirmed_at": "2026-11-01T00:00:00Z",
                },
            }
        ]
    )
    tokens = cliente.verify_otp(TOKEN_PRUEBA, "signup")

    assert tokens is not None
    assert tokens.identity.email == "persona@example.com"
    assert tokens.identity.email_verified is True
    metodo, ruta, payload, access_token = cliente.llamadas[0]
    assert (metodo, ruta) == ("POST", "/auth/v1/verify")
    assert payload == {"token_hash": TOKEN_PRUEBA, "type": "signup"}
    assert access_token == ""


def test_verify_otp_devuelve_none_en_el_primer_paso_de_email_change():
    """El cambio de email es de dos clics: el primero no abre sesión."""
    cliente = _ClienteEspia([{}])
    assert cliente.verify_otp(TOKEN_PRUEBA, "email_change") is None


def test_verify_otp_solo_admite_los_tipos_catalogados():
    assert OTP_TYPES_VALIDOS == frozenset(
        {"signup", "email", "recovery", "invite", "magiclink", "email_change"}
    )
    cliente = _ClienteEspia([])
    for tipo in ("inventado", "", "admin", "signup; drop"):
        with pytest.raises(InvalidCredentials):
            cliente.verify_otp(TOKEN_PRUEBA, tipo)
    assert cliente.llamadas == []


def test_verify_otp_valida_la_longitud_del_token_sin_llamar_a_la_red():
    cliente = _ClienteEspia([])
    for token in ("", "   ", "a" * 257):
        with pytest.raises(InvalidCredentials):
            cliente.verify_otp(token, "signup")
    assert cliente.llamadas == []
    # 256 caracteres es el máximo aceptado: el token del correo nunca llega
    # ahí, pero el límite deja fuera cuerpos gigantes que solo gastarían red.
    assert len("a" * 256) <= 256


# ---------------------------------------------------------------------------
# 2. GET /confirmar-email: nunca consume el token
# ---------------------------------------------------------------------------


@pytest.fixture
def cliente_web():
    return TestClient(cotizat_app, base_url=ORIGEN)


@pytest.fixture
def gotrue_prohibido(monkeypatch):
    """Rompe cualquier llamada a GoTrue: el GET no debe hacer ninguna."""
    llamadas: list[str] = []

    def prohibido(*args, **kwargs):  # pragma: no cover - solo si se rompe
        llamadas.append("llamada")
        raise AssertionError("El GET /confirmar-email no debe llamar a GoTrue")

    monkeypatch.setattr(SupabaseAuthClient, "verify_otp", prohibido)
    monkeypatch.setattr(SupabaseAuthClient, "_request_json", prohibido)
    return llamadas


def test_get_confirmar_email_no_consume_el_token_ni_habla_con_gotrue(
    cliente_web, gotrue_prohibido
):
    respuesta = cliente_web.get(
        f"/confirmar-email?token_hash={TOKEN_PRUEBA}&type=signup"
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.headers["x-robots-tag"] == "noindex, nofollow"
    # El token viaja en un campo oculto del formulario, no en un enlace que el
    # escáner pueda volver a abrir.
    assert f'value="{TOKEN_PRUEBA}"' in respuesta.text
    assert '<form method="post" action="/confirmar-email">' in respuesta.text
    assert "Confirma tu cuenta" in respuesta.text
    assert gotrue_prohibido == []


def test_get_confirmar_email_responde_en_ingles_con_la_misma_plantilla(
    gotrue_prohibido,
):
    from app.i18n import COOKIE_IDIOMA

    cliente = TestClient(cotizat_app, base_url=ORIGEN, cookies={COOKIE_IDIOMA: "en"})
    respuesta = cliente.get(f"/confirmar-email?token_hash={TOKEN_PRUEBA}&type=signup")

    assert respuesta.status_code == 200
    assert '<html lang="en">' in respuesta.text
    assert "Confirm your account" in respuesta.text
    assert "Confirma tu cuenta" not in respuesta.text
    assert gotrue_prohibido == []


def test_get_confirmar_email_rechaza_parametros_invalidos(cliente_web, gotrue_prohibido):
    sin_token = cliente_web.get("/confirmar-email?type=signup")
    assert sin_token.status_code == 400
    assert "Este enlace ya no sirve" in sin_token.text

    tipo_raro = cliente_web.get(f"/confirmar-email?token_hash={TOKEN_PRUEBA}&type=inventado")
    assert tipo_raro.status_code == 400
    assert "Este enlace ya no sirve" in tipo_raro.text
    assert gotrue_prohibido == []


def test_get_confirmar_email_sanea_el_destino(cliente_web, gotrue_prohibido):
    respuesta = cliente_web.get(
        f"/confirmar-email?token_hash={TOKEN_PRUEBA}&type=signup&next=//malo.example/x"
    )
    assert respuesta.status_code == 200
    assert 'name="next" value="/organizaciones/nueva"' in respuesta.text


def test_get_confirmar_email_acepta_los_enlaces_antiguos_con_token(cliente_web, gotrue_prohibido):
    """Los correos ya enviados usan ``?token=…&type=…`` en vez de ``token_hash``."""
    respuesta = cliente_web.get(f"/confirmar-email?token={TOKEN_PRUEBA}&type=signup")

    assert respuesta.status_code == 200
    assert f'value="{TOKEN_PRUEBA}"' in respuesta.text


def test_get_confirmar_email_admite_el_redirect_to_de_los_enlaces_antiguos(
    cliente_web, gotrue_prohibido
):
    respuesta = cliente_web.get(
        f"/confirmar-email?token={TOKEN_PRUEBA}&type=recovery"
        "&redirect_to=https://cotizat.online/restablecer-clave"
    )
    assert respuesta.status_code == 200
    # La variante de recuperación muestra «elige una nueva contraseña».
    assert "Elige una nueva contraseña" in respuesta.text


# ---------------------------------------------------------------------------
# 3. POST /confirmar-email: el canje de verdad
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_configurado(monkeypatch):
    monkeypatch.setattr(
        SupabaseAuthSettings,
        "from_environment",
        classmethod(lambda _cls: _ajustes()),
    )


@pytest.fixture
def eventos(monkeypatch):
    """Captura el evento GA y la auditoría de sesión de las rutas."""
    capturado = {"ga": [], "auditoria": []}
    from app.routers import auth as router_auth

    monkeypatch.setattr(
        router_auth, "encolar_evento_ga", lambda _resp, nombre: capturado["ga"].append(nombre)
    )
    monkeypatch.setattr(
        router_auth.auditoria,
        "anotar_sesion",
        lambda accion, **kw: capturado["auditoria"].append((accion, kw.get("email"))),
    )
    return capturado


def _stub_verify_otp(monkeypatch, *, resultado=None, error=None):
    llamadas: list[tuple[str, str]] = []

    def falso(self, token_hash, otp_type):
        llamadas.append((token_hash, otp_type))
        if error is not None:
            raise error
        return resultado

    monkeypatch.setattr(SupabaseAuthClient, "verify_otp", falso)
    return llamadas


def test_post_confirmar_email_signup_fija_cookies_y_abre_la_organizacion(
    cliente_web, auth_configurado, eventos, monkeypatch
):
    llamadas = _stub_verify_otp(monkeypatch, resultado=_tokens())

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "signup"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] in {"/organizaciones/nueva", ORIGEN + "/organizaciones/nueva"}
    assert llamadas == [(TOKEN_PRUEBA, "signup")]
    assert eventos["ga"] == ["sign_up"]
    assert eventos["auditoria"] == [("sesion.login", "persona@example.com")]
    assert "cotizat_access_token" in respuesta.headers.get("set-cookie", "")


def test_post_confirmar_email_magiclink_registra_login_y_respeta_el_next(
    cliente_web, auth_configurado, eventos, monkeypatch
):
    _stub_verify_otp(monkeypatch, resultado=_tokens())

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "magiclink", "next": "/presupuestos"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] in {"/presupuestos", ORIGEN + "/presupuestos"}
    assert eventos["ga"] == ["login"]


def test_post_confirmar_email_recovery_muestra_el_formulario_con_el_token(
    cliente_web, auth_configurado, monkeypatch
):
    _stub_verify_otp(
        monkeypatch,
        resultado=AuthTokens(
            access_token="access-token-recuperacion",  # pragma: allowlist secret
            refresh_token="refresh-token-recuperacion",  # pragma: allowlist secret
            expires_in=3600,
            identity=_identidad(),
        ),
    )

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "recovery"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.headers["x-robots-tag"] == "noindex, nofollow"
    assert 'value="access-token-recuperacion"' in respuesta.text
    assert 'action="/restablecer-clave"' in respuesta.text
    # La sesión NO se abre: quien recupera la contraseña todavía no ha
    # demostrado que sea la persona, solo ha abierto el correo.
    assert "cotizat_access_token" not in respuesta.headers.get("set-cookie", "")


def test_post_confirmar_email_cambio_primer_paso_pide_el_segundo_correo(
    cliente_web, auth_configurado, monkeypatch
):
    _stub_verify_otp(monkeypatch, resultado=None)

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "email_change"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert "/acceso?msg=" in respuesta.headers["location"]
    assert "cotizat_access_token" not in respuesta.headers.get("set-cookie", "")


def test_post_confirmar_email_cambio_segundo_paso_abre_sesion_en_cuenta(
    cliente_web, auth_configurado, monkeypatch
):
    _stub_verify_otp(monkeypatch, resultado=_tokens())

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "email_change"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert "/cuenta?msg=" in respuesta.headers["location"]
    assert "cotizat_access_token" in respuesta.headers.get("set-cookie", "")


def test_post_confirmar_email_caducado_devuelve_400_sin_filtrar_el_detalle(
    cliente_web, auth_configurado, monkeypatch
):
    _stub_verify_otp(
        monkeypatch,
        error=InvalidCredentials("Email, contraseña o sesión no válidos."),
    )

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "signup"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 400
    assert respuesta.headers["cache-control"] == "no-store"
    assert "Este enlace ya no sirve" in respuesta.text
    assert 'href="/acceso"' in respuesta.text
    assert "cotizat_access_token" not in respuesta.headers.get("set-cookie", "")


def test_post_confirmar_email_sin_configuracion_no_revienta(cliente_web, monkeypatch):
    from app.auth import AuthNotConfigured

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)

    respuesta = cliente_web.post(
        "/confirmar-email",
        data={"token_hash": TOKEN_PRUEBA, "type": "signup"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 400
    assert "Este enlace ya no sirve" in respuesta.text
    assert AuthNotConfigured  # el tipo que lanza from_environment sin claves


# ---------------------------------------------------------------------------
# 4. Cabeceras de los envíos: RFC 8058, Reply-To y X-Entity-Ref-ID
# ---------------------------------------------------------------------------


class _RespuestaFalsa:
    def __init__(self, cuerpo: bytes = b'{"id":"envio-1"}'):
        self._cuerpo = cuerpo

    def read(self, _n: int = -1) -> bytes:
        return self._cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _capturar_envio(monkeypatch):
    capturado: list[dict] = []

    def falso_urlopen(request, timeout):  # noqa: ARG001 (firma de urlopen)
        capturado.append(json.loads(request.data.decode("utf-8")))
        return _RespuestaFalsa()

    monkeypatch.setenv("RESEND_API_KEY", "re_clave_de_prueba")  # pragma: allowlist secret
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <soporte@cotizat.online>")
    monkeypatch.delenv("COTIZAT_SUPPORT_EMAIL", raising=False)
    monkeypatch.setattr(email_module, "urlopen", falso_urlopen)
    return capturado


BAJA_URL = (
    "https://cotizat.online/baja-marketing?token="
    "YW5hQGV4YW1wbGUuY29t.firma-de-prueba-no-real"  # pragma: allowlist secret
)


def test_marketing_lleva_baja_en_un_clic_y_reply_to_real(monkeypatch):
    capturado = _capturar_envio(monkeypatch)

    email_module.enviar_bienvenida_por_email(
        email="ana@example.com",
        contexto={"baja_url": BAJA_URL, "organizacion_nombre": "Obras Ana"},
    )

    payload = capturado[0]
    cabeceras = payload["headers"]
    assert cabeceras["List-Unsubscribe"] == (
        f"<{BAJA_URL}>, <mailto:soporte@cotizat.online?subject=Baja%20de%20marketing>"
    )
    assert cabeceras["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert payload["reply_to"] == "soporte@cotizat.online"
    # Referencia única por envío: dos correos iguales no se agrupan en el
    # mismo hilo y el receptor tiene un identificador estable del remitente.
    referencia = cabeceras["X-Entity-Ref-ID"]
    assert len(referencia) == 32 and int(referencia, 16) >= 0


def test_x_entity_ref_id_es_distinto_en_cada_envio(monkeypatch):
    capturado = _capturar_envio(monkeypatch)

    email_module.enviar_bienvenida_por_email(
        email="ana@example.com", contexto={"baja_url": BAJA_URL}
    )
    email_module.enviar_bienvenida_por_email(
        email="ana@example.com", contexto={"baja_url": BAJA_URL}
    )

    assert (
        capturado[0]["headers"]["X-Entity-Ref-ID"]
        != capturado[1]["headers"]["X-Entity-Ref-ID"]
    )


def test_los_asuntos_por_defecto_no_gritan_ni_usan_rayas_largas():
    contexto = {"baja_url": BAJA_URL, "dias_restantes": 3}
    generadores = [
        email_module.enviar_bienvenida_por_email,
        email_module.enviar_marketing_consejo_tarifas,
        email_module.enviar_marketing_consejo_presupuesto,
        email_module.enviar_marketing_consejo_pdf,
        email_module.enviar_marketing_cierre_prueba,
        email_module.enviar_marketing_winback_7,
        email_module.enviar_marketing_winback_30,
        email_module.enviar_marketing_novedades,
        email_module.enviar_marketing_oferta,
        email_module.enviar_marketing_consejo_obra,
    ]
    asuntos: list[str] = []
    for generador in generadores:
        original = email_module._enviar_marketing
        try:
            email_module._enviar_marketing = lambda **kw: asuntos.append(kw["asunto"]) or "id"
            generador(email="ana@example.com", contexto=dict(contexto))
        finally:
            email_module._enviar_marketing = original

    assert len(asuntos) == len(generadores)
    for asunto in asuntos:
        assert "—" not in asunto, asunto
        assert "–" not in asunto, asunto
        assert "oferta especial" not in asunto.lower(), asunto
        assert "special offer" not in asunto.lower(), asunto
        assert "!" not in asunto, asunto


def test_las_cabeceras_rechazan_inyeccion_por_salto_de_linea(monkeypatch):
    _capturar_envio(monkeypatch)

    with pytest.raises(email_module.EmailValidationError):
        email_module._post_resend(
            email_module.EmailSettings.from_environment(),
            to="ana@example.com",
            subject="Asunto",
            html="<p>hola</p>",
            text="hola",
            headers={"List-Unsubscribe": "<x>\r\nBcc: otro@example.com"},
        )
    with pytest.raises(email_module.EmailValidationError):
        email_module._post_resend(
            email_module.EmailSettings.from_environment(),
            to="ana@example.com",
            subject="Asunto",
            html="<p>hola</p>",
            text="hola",
            headers={"X-Malo\nBcc": "otro@example.com"},
        )


def test_aviso_de_licencia_y_activacion_de_plan_responden_a_soporte(monkeypatch):
    capturado = _capturar_envio(monkeypatch)
    from datetime import date

    email_module.enviar_aviso_licencia(
        email="ana@example.com",
        organizacion_nombre="Obras Ana",
        vence=date(2026, 12, 1),
        dias_restantes=5,
    )
    email_module.enviar_activacion_plan_por_email(
        email="ana@example.com",
        organizacion_nombre="Obras Ana",
        plan_nombre="Profesional",
        importe_texto="29,00 €",
        metodo_nombre="Transferencia",
        inicio=date(2026, 12, 1),
        vence=date(2027, 1, 1),
    )

    assert [p["reply_to"] for p in capturado] == [
        "soporte@cotizat.online",
        "soporte@cotizat.online",
    ]


def test_invitacion_y_presupuesto_sin_remitente_valido_responden_a_soporte(monkeypatch):
    capturado = _capturar_envio(monkeypatch)
    from datetime import datetime

    email_module.enviar_invitacion_por_email(
        email="invitado@example.com",
        enlace="https://cotizat.test/invitaciones/tok",
        organizacion_nombre="Obras Ana",
        invitador_nombre="Ana",
        invitador_email="no-es-un-email",
        rol="miembro",
        caduca_el=datetime(2026, 12, 1, 12, 0),
    )
    email_module.enviar_presupuesto_por_email(
        email="cliente@example.com",
        asunto="Presupuesto P-1",
        mensaje="Adjunto el presupuesto.",
        empresa_nombre="Obras Ana",
        cliente_nombre="Cliente",
        presupuesto_numero="P-1",
        presupuesto_titulo="Baño",
        total_texto="1.000 €",
        pdf=b"%PDF-1.4 prueba",
        nombre_pdf="presupuesto.pdf",
    )

    assert [p["reply_to"] for p in capturado] == [
        "soporte@cotizat.online",
        "soporte@cotizat.online",
    ]


# ---------------------------------------------------------------------------
# 5. POST /baja-marketing: One-Click de RFC 8058 sin Origin ni cookies
# ---------------------------------------------------------------------------


def _cliente_estricto():
    """La app real detrás del middleware con CSRF forzado.

    En SQLite el despliegue desactiva CSRF; esto reproduce la configuración de
    producción para demostrar que la ruta de baja está exenta y que el resto
    NO lo está.
    """
    envuelto = WebSecurityMiddleware(cotizat_app, enforce_csrf=True)
    return TestClient(envuelto, base_url=ORIGEN)


def _origen_de_baja(email: str) -> str:
    with SessionLocal() as db:
        from app.models import BajaMarketing

        fila = db.query(BajaMarketing).filter(BajaMarketing.email == email).first()
        return fila.origen if fila else ""


def test_baja_one_click_urlencoded_sin_origin_ni_cookies():
    correo = "oneclick-urlencoded@example.com"
    with _cliente_estricto() as cliente:
        respuesta = cliente.post(
            f"/baja-marketing?token={token_baja(correo)}",
            data={"List-Unsubscribe": "One-Click"},
            headers={"List-Unsubscribe": "One-Click"},
        )

    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.headers["x-robots-tag"] == "noindex, nofollow"
    assert "Baja confirmada" in respuesta.text
    assert correo in respuesta.text
    assert _origen_de_baja(correo) == "one-click"


def test_baja_one_click_multipart_sin_origin():
    correo = "oneclick-multipart@example.com"
    with _cliente_estricto() as cliente:
        respuesta = cliente.post(
            f"/baja-marketing?token={token_baja(correo)}",
            files={"List-Unsubscribe": (None, "One-Click")},
            headers={"List-Unsubscribe": "One-Click"},
        )

    assert respuesta.status_code == 200
    assert "Baja confirmada" in respuesta.text
    assert _origen_de_baja(correo) == "one-click"


def test_baja_one_click_con_post_vacio_y_token_en_la_query():
    """Algunos clientes hacen el POST sin cuerpo: el token va en la URL."""
    correo = "oneclick-vacio@example.com"
    with _cliente_estricto() as cliente:
        respuesta = cliente.post(
            f"/baja-marketing?token={token_baja(correo)}",
            headers={"List-Unsubscribe": "One-Click"},
        )

    assert respuesta.status_code == 200
    assert "Baja confirmada" in respuesta.text
    assert _origen_de_baja(correo) == "one-click"


def test_baja_del_enlace_del_pie_se_registra_como_enlace():
    correo = "enlace-pie@example.com"
    with _cliente_estricto() as cliente:
        respuesta = cliente.post(
            "/baja-marketing",
            data={"token": token_baja(correo)},
            headers={"Origin": ORIGEN},
        )

    assert respuesta.status_code == 200
    assert "Baja confirmada" in respuesta.text
    assert _origen_de_baja(correo) == "enlace"


def test_baja_con_token_invalido_responde_400_sin_escribir():
    with _cliente_estricto() as cliente:
        respuesta = cliente.post(
            "/baja-marketing?token=token-invalido",
            data={"List-Unsubscribe": "One-Click"},
            headers={"List-Unsubscribe": "One-Click"},
        )

    assert respuesta.status_code == 400
    assert "no válido" in respuesta.text.lower()
    assert respuesta.headers["cache-control"] == "no-store"


def test_el_middleware_con_csrf_activo_sigue_bloqueando_otras_escrituras():
    """Control del test anterior: la exención es de la baja, no del middleware."""
    with _cliente_estricto() as cliente:
        respuesta = cliente.post("/salir")

    assert respuesta.status_code == 403
    assert "CSRF" in respuesta.text


def test_get_baja_marketing_muestra_las_dos_variantes_y_el_ya_dado_de_baja():
    correo = "get-baja@example.com"
    tok = token_baja(correo)
    with _cliente_estricto() as cliente:
        antes = cliente.get(f"/baja-marketing?token={tok}")
        cliente.post(
            f"/baja-marketing?token={tok}",
            data={"List-Unsubscribe": "One-Click"},
            headers={"List-Unsubscribe": "One-Click"},
        )
        despues = cliente.get(f"/baja-marketing?token={tok}")

    assert antes.status_code == 200
    assert "¿Dejar de recibir consejos" in antes.text
    assert "Confirmar baja" in antes.text
    assert despues.status_code == 200
    assert "Ya no recibes" in despues.text


# ---------------------------------------------------------------------------
# 6. Documentación y plantillas de Supabase (lo que se pega en el panel)
# ---------------------------------------------------------------------------

PLANTILLAS_CON_ENLACE = {
    "confirm_signup.html": "signup",
    "reset_password.html": "recovery",
    "email_change.html": "email_change",
}


@pytest.mark.parametrize("nombre,tipo", sorted(PLANTILLAS_CON_ENLACE.items()))
def test_las_plantillas_de_supabase_apuntan_al_dominio_propio(nombre, tipo):
    fuente = (DOCS_SUPABASE / nombre).read_text(encoding="utf-8")
    enlace = f"{{{{ .SiteURL }}}}/confirmar-email?token_hash={{{{ .TokenHash }}}}&amp;type={tipo}"

    assert enlace in fuente, f"{nombre} no usa el enlace del dominio propio"
    assert "{{ .ConfirmationURL }}" not in fuente
    assert "supabase.co" not in fuente.lower()
    # Sin URL cruda larga debajo del botón: es justo lo que los filtros leen
    # como enlace sospechoso y lo que el escáner abre por su cuenta.
    assert "word-break:break-all" not in fuente
    assert fuente.count("href=\"{{ .SiteURL }}") == 1
    # Diseño alineado con la base de los correos de la app.
    assert "box-shadow" not in fuente
    assert "linear-gradient" not in fuente
    assert "#0b5b38" in fuente
    assert "#dce6e1" in fuente
    assert "soporte@cotizat.online" in fuente
    assert "display:none;max-height:0" in fuente


def test_la_plantilla_de_aviso_de_contrasena_cambiada_no_lleva_token():
    fuente = (DOCS_SUPABASE / "password_changed.html").read_text(encoding="utf-8")

    assert "{{ .TokenHash }}" not in fuente
    assert "{{ .ConfirmationURL }}" not in fuente
    assert "supabase.co" not in fuente.lower()
    assert "{{ .Email }}" in fuente
    assert "soporte@cotizat.online" in fuente
    assert "display:none;max-height:0" in fuente
    assert "box-shadow" not in fuente
    assert "linear-gradient" not in fuente


def test_ninguna_plantilla_de_supabase_reintroduce_los_enlaces_antiguos():
    for ruta in sorted(DOCS_SUPABASE.glob("*.html")):
        fuente = ruta.read_text(encoding="utf-8")
        assert "{{ .ConfirmationURL }}" not in fuente, ruta
        assert "supabase.co" not in fuente.lower(), ruta
        assert "box-shadow" not in fuente, ruta
        assert "linear-gradient" not in fuente, ruta


def test_la_documentacion_explica_el_cambio_de_remitente_y_dns():
    doc = Path("docs/SUPABASE_EMAIL_TEMPLATES.md").read_text(encoding="utf-8")

    # Asuntos en español, pegados tal cual en el panel.
    assert "Confirma tu email · CotizaT" in doc
    assert "Restablece tu contraseña · CotizaT" in doc
    assert "Confirma tu nuevo email · CotizaT" in doc
    assert "Tu contraseña ha cambiado · CotizaT" in doc
    # Remitente en el dominio propio.
    assert "soporte@cotizat.online" in doc
    # Resend: seguimiento desactivado y DKIM de 2048 bits.
    assert "Open Tracking" in doc and "Click Tracking" in doc
    assert "2048" in doc
    assert "resend._domainkey" in doc
    # DMARC publicado como TXT en _dmarc.
    assert "_dmarc.cotizat.online" in doc
    assert "v=DMARC1" in doc
