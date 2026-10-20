"""Avisos del negocio y buzón de soporte (petición del titular, 2026-10).

Tres huecos que esta suite fija como contrato:

1. **Una venta no puede descubrirse por el banco.** Cuando una compra queda
   activa —webhook de Stripe o comprobante activado a mano— sale un aviso al
   buzón del titular con plan, importe, método y período, y el panel lo pinta
   en «Hoy» y en el libro de ventas.
2. **Un alta tampoco.** El registro y la empresa nueva (con su prueba) avisan
   al mismo buzón.
3. **El cliente tiene un botón de soporte.** ``/soporte`` guarda el mensaje en
   ``mensajes_soporte`` con un único INSERT (el correo se intenta primero y
   su marca viaja en la fila: el UPDATE está reservado al operador por RLS y
   marcar después tiraba el registro en PostgreSQL, 2026-10-20), funciona sin
   sesión y el panel lo lee, lo marca y lo audita.

Los envíos de correo se prueban con el mismo doble que el resto de la suite:
se sustituye ``urlopen`` de ``app.services.email`` y se inspecciona el JSON
que habría ido a Resend.
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_operator_db
from app.main import app
from app.models import (
    CompraPlan,
    EventoAdmin,
    EventoProducto,
    Licencia,
    Membresia,
    MensajeSoporte,
    Organizacion,
    Usuario,
)
from app.security import AuthRateLimitMiddleware
from starlette.testclient import TestClient

#: El límite real del formulario público, comprobado abajo antes de ampliarlo
#: para que las pruebas no tropiecen con él (mismo criterio que ``/demo`` en
#: ``conftest.py``).
LIMITE_SOPORTE = AuthRateLimitMiddleware.DEFAULT_LIMITS.get("/soporte")
AuthRateLimitMiddleware.DEFAULT_LIMITS["/soporte"] = 999


# ---------------------------------------------------------------------------
# Doble de Resend
# ---------------------------------------------------------------------------


class ResendDoble:
    """Captura lo que se habría enviado a la API de Resend."""

    def __init__(self):
        self.envios = []

    class _Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size=-1):
            return b'{"id":"aviso-1"}'

    def __call__(self, request, timeout):  # noqa: ARG002
        self.envios.append(json.loads(request.data.decode("utf-8")))
        return self._Respuesta()

    @property
    def ultimo(self) -> dict:
        assert self.envios, "No se envió ningún correo."
        return self.envios[-1]


@pytest.fixture
def resend(monkeypatch):
    from app.services import email as email_module

    doble = ResendDoble()
    monkeypatch.setenv("RESEND_API_KEY", "re_prueba")
    monkeypatch.setenv("COTIZAT_EMAIL_FROM", "CotizaT <no-responder@cotizat.test>")
    monkeypatch.delenv("COTIZAT_AVISOS_EMAIL", raising=False)
    monkeypatch.setattr(email_module, "urlopen", doble)
    return doble


# ---------------------------------------------------------------------------
# Base del panel: una venta reciente, un mensaje de soporte y un alta
# ---------------------------------------------------------------------------


@pytest.fixture
def panel():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        cliente = Organizacion(nombre="Obras Norte", slug="obras-norte")
        db.add(cliente)
        db.flush()
        hoy = date.today()
        compra = CompraPlan(
            organizacion_id=cliente.id,
            plan="mensual",
            metodo_pago="stripe",
            importe=9.99,
            moneda="USD",
            estado="activa",
            creada_por_email="compras@example.com",
            created_at=datetime.utcnow() - timedelta(hours=3),
            revisado_at=datetime.utcnow() - timedelta(hours=3),
            revisado_por_email="op@example.com",
            stripe_checkout_session_id="cs_test_venta_1",
            licencia_inicio=hoy,
            licencia_vence=hoy + timedelta(days=30),
        )
        db.add(compra)
        db.flush()
        db.add(Licencia(
            organizacion_id=cliente.id,
            origen="pago",
            importe=9.99,
            moneda="USD",
            inicio=hoy,
            vence=hoy + timedelta(days=30),
            estado="activa",
            metodo_cobro="Stripe",
            creada_por_email="op@example.com",
        ))
        mensaje = MensajeSoporte(
            nombre="Ana Cliente",
            email="ana@example.com",
            organizacion_id=cliente.id,
            tipo="problema",
            asunto="El PDF no lleva el logo",
            mensaje="Hola: al exportar el presupuesto el logo sale en blanco.",
            pagina="/presupuestos/12",
            estado="nuevo",
        )
        db.add(mensaje)
        db.add(EventoProducto(
            organizacion_id=None,
            actor_email="nueva@example.com",
            accion="cuenta.registrada",
            detalle=json.dumps({"pais": "ES"}),
        ))
        db.commit()
        datos = {"org": cliente.id, "compra": compra.id, "mensaje": mensaje.id}

    def _db_operador():
        db = Session()
        db.info["es_operador"] = True
        db.info["auth_email"] = "titular@example.com"
        db.info["operador_rol"] = "superadmin"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        cliente_http = TestClient(app, base_url="https://cotizat.test")
        yield cliente_http, Session, datos
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


# ---------------------------------------------------------------------------
# 1. Aviso de venta
# ---------------------------------------------------------------------------


def test_el_formulario_publico_tiene_rate_limit():
    """El botón de soporte es público: sin límite, un bot llena el buzón."""
    assert LIMITE_SOPORTE == 5


def test_una_venta_avisa_al_buzon_del_titular(panel, resend):
    """El correo que evita enterarse de un cobro por el banco."""
    _cliente, Session, datos = panel
    from app.services.avisos_negocio import avisar_venta

    with Session() as db:
        compra = db.get(CompraPlan, datos["compra"])
        licencia = db.query(Licencia).filter_by(organizacion_id=datos["org"]).one()
        envio_id = avisar_venta(db, compra=compra, licencia=licencia, origen="stripe")

    assert envio_id == "aviso-1"
    correo = resend.ultimo
    assert correo["to"] == ["soporte@cotizat.online"]
    assert "Venta" in correo["subject"]
    assert "9,99" in correo["subject"] or "9.99" in correo["subject"]
    assert "Obras Norte" in correo["subject"]
    # Responder al aviso escribe al comprador, no a uno mismo.
    assert correo["reply_to"] == "compras@example.com"
    assert "Obras Norte" in correo["html"]
    assert "mensual" in correo["text"].lower() or "Mensual" in correo["text"]
    assert "/admin/ingresos?tab=ventas" in correo["text"]


def test_el_aviso_de_venta_distingue_una_renovacion(panel, resend):
    """Un alta y una renovación no se leen igual en el buzón."""
    _cliente, Session, datos = panel
    from app.services.avisos_negocio import avisar_venta

    with Session() as db:
        compra = db.get(CompraPlan, datos["compra"])
        avisar_venta(db, compra=compra, renovacion=True, origen="stripe")

    correo = resend.ultimo
    assert "Renovación" in correo["subject"]


def test_sin_correo_configurado_la_venta_no_se_rompe(panel, monkeypatch):
    """Un aviso nunca puede deshacer la venta: sin Resend, solo se registra."""
    _cliente, Session, datos = panel
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_EMAIL_FROM", raising=False)
    from app.services.avisos_negocio import avisar_venta

    with Session() as db:
        compra = db.get(CompraPlan, datos["compra"])
        assert avisar_venta(db, compra=compra) == ""


def test_activar_una_compra_a_mano_avisa_de_la_venta(panel, resend, monkeypatch):
    """El cobro manual es una venta igual que la que cierra Stripe."""
    _cliente, Session, datos = panel
    monkeypatch.setenv("COTIZAT_SUPPORT_EMAIL", "soporte@cotizat.online")

    with Session() as db:
        # Compra pendiente con comprobante: el caso real del panel.
        org = db.get(Organizacion, datos["org"])
        pendiente = CompraPlan(
            organizacion_id=org.id,
            plan="anual",
            metodo_pago="usdt",
            importe=89.0,
            moneda="USD",
            estado="pendiente",
            datos_verificacion=json.dumps({"hash_transaccion": "TX-1"}),
            comprobante_reference="storage://x/comprobante.png",
            comprobante_nombre="comprobante.png",
            comprobante_mime="image/png",
            creada_por_email="compras@example.com",
        )
        db.add(pendiente)
        db.commit()
        compra_id = pendiente.id

    _cliente, Session, _datos = panel
    respuesta = _cliente.post(
        f"/admin/compras/{compra_id}/activar",
        data={"volver": "/admin/ingresos?tab=compras", "metodo_cobro": "USDT"},
        follow_redirects=False,
        headers={"origin": "https://cotizat.test"},
    )
    assert respuesta.status_code in {302, 303}, respuesta.text

    assert resend.envios, "La activación manual debe avisar de la venta"
    destinos = {correo["to"][0] for correo in resend.envios}
    assert "soporte@cotizat.online" in destinos
    cuerpos = " ".join(correo["subject"] for correo in resend.envios)
    assert "Obras Norte" in cuerpos or "Compras" in cuerpos or "Venta" in cuerpos

    with Session() as db:
        compra = db.get(CompraPlan, compra_id)
        assert compra.estado == "activa"


# ---------------------------------------------------------------------------
# 2. Aviso de alta
# ---------------------------------------------------------------------------


def test_un_alta_avisa_al_buzon_del_titular(resend):
    from app.services.avisos_negocio import avisar_registro

    envio_id = avisar_registro(
        email="nueva@example.com",
        nombre="Nueva Persona",
        pais="ES",
        origen="registro",
    )

    assert envio_id == "aviso-1"
    correo = resend.ultimo
    assert correo["to"] == ["soporte@cotizat.online"]
    assert "Nueva Persona" in correo["subject"]
    assert correo["reply_to"] == "nueva@example.com"
    assert "Nueva Persona" in correo["html"]
    assert "ES" in correo["text"]


def test_el_aviso_de_prueba_lleva_la_empresa_y_el_plazo(resend):
    from app.services.avisos_negocio import avisar_registro

    avisar_registro(
        email="dueno@example.com",
        nombre="Dueño",
        pais="VE",
        origen="prueba",
        organizacion_nombre="Reformas del Sur",
        prueba_texto="Prueba de 7 días",
    )

    correo = resend.ultimo
    assert "prueba" in correo["subject"].lower()
    assert "Reformas del Sur" in correo["subject"]
    assert "7 días" in correo["text"]


def test_el_destino_de_los_avisos_se_puede_desviar(resend, monkeypatch):
    """``COTIZAT_AVISOS_EMAIL`` permite separar avisos del buzón de clientes."""
    monkeypatch.setenv("COTIZAT_AVISOS_EMAIL", "titular@example.com")
    from app.services.avisos_negocio import avisar_registro

    avisar_registro(email="otra@example.com", nombre="Otra")

    assert resend.ultimo["to"] == ["titular@example.com"]


# ---------------------------------------------------------------------------
# 3. Botón de soporte: formulario público, buzón y panel
# ---------------------------------------------------------------------------


def _limpiar_mensajes(*emails):
    from app.database import SessionLocal

    with SessionLocal() as db:
        db.query(MensajeSoporte).filter(MensajeSoporte.email.in_(emails)).delete(
            synchronize_session=False
        )
        db.commit()


def test_la_pagina_de_soporte_ofrece_el_formulario():
    with TestClient(app, base_url="https://cotizat.test") as client:
        respuesta = client.get("/soporte?desde=/presupuestos")

    assert respuesta.status_code == 200
    assert "Soporte" in respuesta.text
    for campo in ("nombre", "email", "tipo", "asunto", "mensaje", "desde"):
        assert f'name="{campo}"' in respuesta.text
    assert "soporte@cotizat.online" in respuesta.text
    # El motivo se elige de la lista cerrada del modelo.
    assert "Queja o reclamación" in respuesta.text


def test_la_pagina_de_soporte_figura_en_el_mapa_y_en_el_sitemap():
    from app.seo import urls_sitemap

    assert "/soporte" in {entrada["loc"].split("https://cotizat.online")[-1] for entrada in urls_sitemap()}
    with TestClient(app, base_url="https://cotizat.test") as client:
        mapa = client.get("/mapa-del-sitio")
    assert "/soporte" in mapa.text


def test_el_mensaje_del_formulario_queda_guardado_y_avisa(resend):
    """El correo se intenta primero y su marca viaja en el INSERT único
    (contrato desde 2026-10-20: sin UPDATE posterior, vedado por RLS)."""
    email = "boton-soporte@example.com"
    _limpiar_mensajes(email)
    try:
        with TestClient(app, base_url="https://cotizat.test") as client:
            respuesta = client.post(
                "/soporte",
                data={
                    "nombre": "Cliente del botón",
                    "email": email,
                    "tipo": "queja",
                    "asunto": "Cobro duplicado",
                    "mensaje": "Me habéis cobrado dos veces el mes pasado.",
                    "desde": "/configuracion",
                },
                headers={"origin": "https://cotizat.test"},
                follow_redirects=False,
            )

        assert respuesta.status_code == 303
        assert respuesta.headers["location"].startswith("/soporte?enviado=1")

        from app.database import SessionLocal

        with SessionLocal() as db:
            fila = (
                db.query(MensajeSoporte)
                .filter(MensajeSoporte.email == email)
                .one()
            )
            assert fila.estado == "nuevo"
            assert fila.tipo == "queja"
            assert fila.pagina == "/configuracion"
            assert fila.aviso_enviado is True

        correo = resend.ultimo
        assert correo["to"] == ["soporte@cotizat.online"]
        assert correo["reply_to"] == email
        assert "Queja o reclamación" in correo["subject"]
        assert "Cobro duplicado" in correo["html"]
    finally:
        _limpiar_mensajes(email)


def test_el_formulario_rechaza_un_correo_invalido_sin_guardar():
    email = "sin-arroba"
    with TestClient(app, base_url="https://cotizat.test") as client:
        respuesta = client.post(
            "/soporte",
            data={"nombre": "X", "email": email, "tipo": "consulta", "mensaje": "Hola"},
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert "/soporte?error=" in respuesta.headers["location"]
    from app.database import SessionLocal

    with SessionLocal() as db:
        assert db.query(MensajeSoporte).filter(MensajeSoporte.email == email).count() == 0


def test_el_cebo_para_bots_no_guarda_nada(resend):
    """Un rellenacampos automático se va con la misma respuesta que una persona."""
    email = "bot@example.com"
    _limpiar_mensajes(email)
    with TestClient(app, base_url="https://cotizat.test") as client:
        respuesta = client.post(
            "/soporte",
            data={
                "nombre": "Bot",
                "email": email,
                "tipo": "consulta",
                "mensaje": "compra barata aquí",
                "web": "http://spam.example",
            },
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303
    assert "enviado=1" in respuesta.headers["location"]
    from app.database import SessionLocal

    with SessionLocal() as db:
        assert db.query(MensajeSoporte).filter(MensajeSoporte.email == email).count() == 0
    assert not resend.envios


def test_una_cookie_de_organizacion_caducada_no_rompe_el_formulario(resend):
    """Una sesión vieja no puede impedir enviar la queja.

    La cookie ``cotizat_organization_id`` viaja en el navegador aunque la base
    se haya restaurado o la empresa se haya dado de baja: si el mensaje se
    guardara «con» esa organización, el FK fallaría y la persona vería un
    error. Se guarda sin ella.
    """
    email = "cookie-vieja@example.com"
    _limpiar_mensajes(email)
    try:
        with TestClient(app, base_url="https://cotizat.test") as client:
            client.cookies.set("cotizat_organization_id", "999999")
            respuesta = client.post(
                "/soporte",
                data={
                    "nombre": "Cliente",
                    "email": email,
                    "tipo": "consulta",
                    "mensaje": "Sigo sin poder entrar.",
                },
                headers={"origin": "https://cotizat.test"},
                follow_redirects=False,
            )

        assert respuesta.status_code == 303
        assert "enviado=1" in respuesta.headers["location"]

        from app.database import SessionLocal

        with SessionLocal() as db:
            fila = db.query(MensajeSoporte).filter(MensajeSoporte.email == email).one()
            assert fila.organizacion_id is None
    finally:
        _limpiar_mensajes(email)


def test_la_bandeja_del_panel_muestra_y_atiende_los_mensajes(panel):
    cliente, Session, datos = panel
    pagina = cliente.get("/admin/clientes?tab=soporte")
    assert pagina.status_code == 200
    assert "Bandeja de soporte" in pagina.text
    assert "El PDF no lleva el logo" in pagina.text
    assert "ana@example.com" in pagina.text
    assert "Sin atender" in pagina.text

    respuesta = cliente.post(
        f"/admin/soporte/{datos['mensaje']}/estado",
        data={
            "estado": "resuelto",
            "nota": "Se regeneró el PDF con el logo.",
            "volver": "/admin/clientes?tab=soporte",
        },
        follow_redirects=False,
        headers={"origin": "https://cotizat.test"},
    )
    assert respuesta.status_code in {302, 303}

    with Session() as db:
        mensaje = db.get(MensajeSoporte, datos["mensaje"])
        assert mensaje.estado == "resuelto"
        assert "logo" in mensaje.nota_interna
        assert mensaje.atendido_por_email == "titular@example.com"
        evento = (
            db.query(EventoAdmin)
            .filter(EventoAdmin.accion == "soporte.mensaje_estado")
            .one_or_none()
        )
        assert evento is not None, "Toda acción del panel queda auditada"


def test_la_etiqueta_de_la_auditoria_del_soporte_es_legible():
    from app.services.audit_admin import ACCIONES_LECIBLES

    assert ACCIONES_LECIBLES["soporte.mensaje_estado"] == "Estado de mensaje de soporte"


def test_el_contador_de_soporte_alimenta_la_pestana(panel):
    _cliente, Session, _datos = panel
    from app.panel_arquitectura import pestanas_panel
    from app.services.panel_contextos import contadores_panel

    with Session() as db:
        contadores = contadores_panel(db)

    assert contadores["soporte"] == 1
    pestanas = {p["id"]: p["contador"] for p in pestanas_panel("clientes", "soporte", contadores)}
    assert pestanas["soporte"] == 1


def test_la_campana_anuncia_ventas_y_soporte(panel):
    _cliente, Session, _datos = panel
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        avisos = notificaciones_admin(db)

    tipos = {aviso["tipo"] for aviso in avisos}
    assert "venta" in tipos
    assert "soporte" in tipos
    venta = next(aviso for aviso in avisos if aviso["tipo"] == "venta")
    assert "/admin/ingresos?tab=ventas" in venta["url"]
    soporte = next(aviso for aviso in avisos if aviso["tipo"] == "soporte")
    assert "/admin/clientes?tab=soporte" in soporte["url"]


def test_el_panel_hoy_ensena_la_venta_y_el_buzon(panel):
    cliente, _Session, _datos = panel
    pagina = cliente.get("/admin")
    assert pagina.status_code == 200
    assert "Últimas ventas" in pagina.text
    assert "Obras Norte" in pagina.text
    assert "Buzón de soporte" in pagina.text
    assert "Ventas del mes" in pagina.text
    # La campana del panel expone los mismos avisos por JSON.
    campana = cliente.get("/admin/notificaciones")
    assert campana.status_code == 200
    assert any(a["tipo"] == "venta" for a in campana.json()["avisos"])


def test_el_libro_de_ventas_lista_y_exporta(panel):
    cliente, _Session, _datos = panel
    pagina = cliente.get("/admin/ingresos?tab=ventas")
    assert pagina.status_code == 200
    assert "Libro de ventas" in pagina.text
    assert "Obras Norte" in pagina.text
    assert "9.99" in pagina.text or "9,99" in pagina.text
    assert "Automático" in pagina.text

    csv = cliente.get("/admin/ingresos.csv?tab=ventas")
    assert csv.status_code == 200
    assert "Obras Norte" in csv.text
    assert "Automática" in csv.text


def test_la_fila_de_venta_marca_la_novedad(panel):
    _cliente, Session, _datos = panel
    from app.services.panel_ventas import ultimas_ventas

    with Session() as db:
        ventas = ultimas_ventas(db, limite=5)

    assert ventas and ventas[0]["es_novedad"] is True
    assert ventas[0]["automatica"] is True
    assert ventas[0]["renovacion"] is False
    assert ventas[0]["url_cliente"].startswith("/admin/clientes/")


def test_las_altas_recientes_salen_de_la_telemetria(panel):
    _cliente, Session, _datos = panel
    from app.services.panel_ventas import registros_recientes, resumen_registros

    with Session() as db:
        registros = registros_recientes(db, limite=5, dias=30)
        resumen = resumen_registros(db)

    assert [r["email"] for r in registros] == ["nueva@example.com"]
    assert registros[0]["tipo"] == "cuenta"
    assert resumen["hoy"] >= 1


def test_el_boton_de_soporte_esta_donde_esta_el_cliente():
    """Un botón que no se ve no sirve: va en la barra lateral y flotante.

    Se comprueba sobre la plantilla porque el cliente que escribe puede estar
    en cualquier pantalla de la aplicación (el que paga y el que solo prueba).
    """
    base = Path("app/templates/base.html").read_text(encoding="utf-8")
    assert 'href="/soporte"' in base
    assert "soporte-flotante" in base
    assert "/soporte?desde=" in base, "el formulario quiere saber desde dónde se escribe"
    css = Path("app/static/css/style.css").read_text(encoding="utf-8")
    assert ".soporte-flotante" in css


# ---------------------------------------------------------------------------
# El registro de verdad (ruta HTTP) avisa al buzón del titular
# ---------------------------------------------------------------------------


class _ClienteAuthDoble:
    """Doble de Supabase Auth: registra la llamada y devuelve tokens."""

    def __init__(self, _settings=None):
        self.calls = []

    def sign_up(self, email, password, name="", redirect_to=""):  # noqa: ARG002
        from app.auth import AuthTokens, SignupResult, SupabaseIdentity

        self.calls.append(email)
        identidad = SupabaseIdentity(
            auth_user_id="7c1d4f3e-9a52-4a1f-8d33-0b6e2c5a91d4",
            email=email,
            name=name,
            email_verified=True,
        )
        return SignupResult(
            identity=identidad,
            tokens=AuthTokens(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_in=3600,
                identity=identidad,
            ),
            ya_registrado=False,
        )


def test_el_registro_avisa_al_buzon_del_titular(resend, monkeypatch):
    """Un alta tiene que sonar en el buzón, con prueba o sin ella."""
    from app.auth import SupabaseAuthSettings
    from app.routers import common

    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    monkeypatch.setattr(
        SupabaseAuthSettings,
        "from_environment",
        classmethod(
            lambda _cls: SupabaseAuthSettings(
                url="https://project.supabase.co",
                publishable_key="sb_publishable_test",
                cookie_secure=True,
            )
        ),
    )
    monkeypatch.setattr(common, "SupabaseAuthClient", _ClienteAuthDoble)

    email = "alta-avisada@example.com"
    with TestClient(app, base_url="https://cotizat.test", client=("192.0.2.77", 50000)) as client:
        respuesta = client.post(
            "/registro",
            data={
                "email": email,
                "password": "clave-larga-segura",
                "password_confirmation": "clave-larga-segura",
                "nombre": "Persona Nueva",
                "acepto_terminos": "1",
                "pais": "ES",
            },
            headers={"origin": "https://cotizat.test"},
            follow_redirects=False,
        )

    assert respuesta.status_code == 303, respuesta.text
    avisos = [correo for correo in resend.envios if correo["to"] == ["soporte@cotizat.online"]]
    assert avisos, "El alta tiene que avisar al buzón del titular"
    aviso = avisos[-1]
    assert email in aviso["subject"] or "Persona Nueva" in aviso["subject"]
    assert aviso["reply_to"] == email
    assert "ES" in aviso["text"]


# ---------------------------------------------------------------------------
# 2026-10-20: el registro no puede emitir UPDATE ni la página «expulsa».
# ---------------------------------------------------------------------------


def test_registrar_mensaje_no_emite_ningun_update(resend):
    """El registro público es un único INSERT, sin UPDATE posterior.

    La política RLS de ``mensajes_soporte`` solo permite el INSERT público;
    con FORCE RLS, marcar ``aviso_enviado`` tras enviar el correo emitía un
    UPDATE que PostgreSQL reducía a 0 filas → ``StaleDataError`` → rollback
    del mensaje y banner de error (producción, 2026-10-20). Los tests corren
    en SQLite sin RLS, así que el contrato se fija contando las sentencias.
    """
    from sqlalchemy import event

    from app.database import SessionLocal
    from app.services import soporte as soporte_service

    sentencias = []

    def _contar(_conn, _cursor, sentencia, _params, _context, _executemany):
        sentencias.append(sentencia.strip().upper())

    email = "sin-update@example.com"
    _limpiar_mensajes(email)
    try:
        with SessionLocal() as db:
            motor = db.get_bind()
            event.listen(motor, "before_cursor_execute", _contar)
            try:
                fila, aviso_id = soporte_service.registrar_mensaje(
                    db,
                    nombre="Sin Update",
                    email=email,
                    tipo="consulta",
                    mensaje="¿Funciona sin UPDATE?",
                    pagina="/inicio",
                )
            finally:
                event.remove(motor, "before_cursor_execute", _contar)

        assert aviso_id, "El doble de Resend devuelve un identificador: el aviso «salió»"
        assert fila.aviso_enviado is True
        actualizaciones = [s for s in sentencias if s.startswith("UPDATE")]
        assert not actualizaciones, actualizaciones
        inserciones = [s for s in sentencias if s.startswith("INSERT INTO MENSAJES_SOPORTE")]
        assert len(inserciones) == 1
    finally:
        _limpiar_mensajes(email)


def test_soporte_con_sesion_se_ve_dentro_de_la_aplicacion():
    """Quien está dentro no cae en la página de marketing con «Acceder».

    En SQLite (escritorio y tests) siempre hay sesión: ``/soporte`` se pinta
    con la estructura del panel. Sin sesión (forzado aquí) sigue la pública
    indexable, que es la que enlaza el sitemap.
    """
    with TestClient(app, base_url="https://cotizat.test") as client:
        respuesta = client.get("/soporte")

    assert respuesta.status_code == 200
    assert 'href="/inicio"' in respuesta.text  # barra lateral de la aplicación
    assert "hub-hero-int" not in respuesta.text  # nada de marco público


def test_soporte_sin_sesion_sigue_siendo_la_publica(monkeypatch):
    from app.routers import publico

    monkeypatch.setattr(publico, "_soporte_con_sesion", lambda _request: False)
    with TestClient(app, base_url="https://cotizat.test") as client:
        respuesta = client.get("/soporte")

    assert respuesta.status_code == 200
    assert "hub-hero-int soporte-main" in respuesta.text
    assert 'rel="canonical"' in respuesta.text
