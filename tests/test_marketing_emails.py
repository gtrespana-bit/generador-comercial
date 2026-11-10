"""Sistema de marketing por email: secuencia, baja y campañas.

Cubre lo nuevo de E1: bienvenida inmediata, consejos por días de prueba,
win-back y campañas manuales. Cada plantilla se envía una vez por
organización y respeta la baja con un clic.
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Configuracion, Licencia, Membresia, Organizacion, PruebaConcedida, Usuario
from app.services.marketing import (
    PLANTILLAS_SECUENCIA,
    enviar_bienvenida,
    enviar_campana,
    enviar_secuencia_marketing,
    es_baja,
    historial_enviado,
    quitar_baja,
    registrar_baja,
    token_baja,
    verificar_token_baja,
)


# ---------- Helpers ----------

def _engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    return eng


def _org_con_prueba(db, nombre="Org", dias_desde_alta=0, vencimiento_dias=6):
    """Crea org + usuario propietario + licencia de prueba desde hace N días."""
    hoy = date.today()
    org = Organizacion(nombre=nombre, slug=f"slug-{nombre.lower().replace(' ', '-')}-{dias_desde_alta}-{vencimiento_dias}", activa=True)
    db.add(org); db.flush()
    u = db.query(Usuario).filter(Usuario.email == "ana@example.com").first()
    if not u:
        u = Usuario(email="ana@example.com", nombre="Ana", auth_user_id="auth-ana", activo=True)
        db.add(u); db.flush()
    m = Membresia(usuario_id=u.id, organizacion_id=org.id, rol="propietario", activa=True)
    db.add(m)
    inicio = hoy - timedelta(days=dias_desde_alta)
    vence = hoy + timedelta(days=vencimiento_dias - dias_desde_alta) if vencimiento_dias else inicio + timedelta(days=7)
    lic = Licencia(organizacion_id=org.id, estado="activa", origen="prueba", inicio=inicio, vence=vence, importe=0, creada_por_email="ana@example.com")
    db.add(lic)
    pc = PruebaConcedida(email_normalizado=f"ana-{org.id}@example.com", email_original=f"ana-{org.id}@example.com", organizacion_id=org.id, ip_hash="x", dias=7)
    pc.created_at = datetime.combine(inicio, datetime.min.time())
    db.add(pc)
    cfg = Configuracion(organizacion_id=org.id, empresa_nombre=nombre, empresa_pais="Venezuela", moneda_default="USD", iva_default=16)
    db.add(cfg)
    db.commit()
    return org


# ---------- Token de baja ----------

def test_token_baja_es_firmado_y_verificable(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    monkeypatch.setenv("CRON_SECRET", "testsecret123")
    tok = token_baja("ana@example.com")
    assert "." in tok
    assert verificar_token_baja(tok) == "ana@example.com"
    assert verificar_token_baja(tok + "x") is None
    assert verificar_token_baja("") is None
    assert verificar_token_baja("sinpunto") is None


def test_url_baja_contiene_token(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    monkeypatch.setenv("CRON_SECRET", "testsecret123")
    from app.services.marketing import url_baja
    url = url_baja("ana@example.com")
    assert "/baja-marketing?token=" in url
    assert "cotizat.online" in url


# ---------- Baja ----------

def test_baja_se_registra_y_se_respeta():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    assert not es_baja(db, "ana@example.com")
    assert registrar_baja(db, "ana@example.com")
    db.commit()
    assert es_baja(db, "ana@example.com")
    assert es_baja(db, "ANA@EXAMPLE.COM")  # normaliza
    assert not registrar_baja(db, "ana@example.com")  # ya estaba
    assert quitar_baja(db, "ana@example.com")
    db.commit()
    assert not es_baja(db, "ana@example.com")
    db.close(); eng.dispose()


# ---------- Bienvenida ----------

def test_bienvenida_se_envia_una_sola_vez_por_org():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    org = _org_con_prueba(db, nombre="Bienv")
    llamadas = []
    def fake(email, plantilla=None, contexto=None, **kw):
        llamadas.append((email, plantilla or kw.get("plantilla")))
        return "id123"
    res = enviar_bienvenida(db, organizacion_id=org.id, organizacion_nombre=org.nombre, email="ana@example.com", remitente=fake)
    assert len(res["enviadas"]) == 1
    assert historial_enviado(db, org.id, "bienvenida")
    # segunda vez idempotente
    llamadas.clear()
    res2 = enviar_bienvenida(db, organizacion_id=org.id, organizacion_nombre=org.nombre, email="ana@example.com", remitente=fake)
    assert not res2["enviadas"]
    assert res2["omitidas_ya_enviada"]
    db.close(); eng.dispose()


def test_bienvenida_respeta_baja():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    org = _org_con_prueba(db, nombre="BajaBienv")
    registrar_baja(db, "ana@example.com"); db.commit()
    def fake(email, plantilla=None, contexto=None, **kw):
        return "id"
    res = enviar_bienvenida(db, organizacion_id=org.id, organizacion_nombre=org.nombre, email="ana@example.com", remitente=fake)
    assert not res["enviadas"]
    assert res["omitidas_baja"]
    db.close(); eng.dispose()


# ---------- Secuencia ----------

def test_secuencia_envia_plantilla_del_dia():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    hoy = date.today()
    # Dia 0 -> bienvenida, dia 1 -> consejo_tarifas, dia 2 -> consejo_presupuesto, etc.
    # Creamos orgs con distintas antiguedades
    org0 = _org_con_prueba(db, nombre="Dia0", dias_desde_alta=0)
    # Para que consejo_tarifas no se salte por paso completo, necesitamos simular catálogo con tarifas pendientes.
    # Truco: el progreso se mockea haciendo que _progreso devuelva no completado.
    import app.services.marketing as mkt
    orig_prog = mkt._progreso_para_personalizar
    mkt._progreso_para_personalizar = lambda db, oid: {"paso_tarifas_completo": False, "paso_presupuesto_completo": False, "paso_pdf_completo": False, "total_tarifas": 10}

    llamadas = []
    def fake(email, plantilla=None, contexto=None, **kw):
        llamadas.append(plantilla or kw.get("plantilla"))
        return "id"

    res = enviar_secuencia_marketing(db, remitente=fake, hoy=hoy)
    # Dia0 deberia disparar bienvenida
    assert any("bienvenida" in c for c in llamadas), llamadas

    # Idempotencia: re-ejecutar mismo día no reenvía
    llamadas.clear()
    res2 = enviar_secuencia_marketing(db, remitente=fake, hoy=hoy)
    assert not res2["enviadas"]

    mkt._progreso_para_personalizar = orig_prog
    db.close(); eng.dispose()


def test_secuencia_winback_a_los_7_dias():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    hoy = date.today()
    # Org vencida hace 7 días (alta hace 14 días, prueba 7d)
    org = Organizacion(nombre="Vencida", slug="vencida-1", activa=True)
    db.add(org); db.flush()
    u = Usuario(email="bob@example.com", nombre="Bob", auth_user_id="auth-bob", activo=True)
    db.add(u); db.flush()
    db.add(Membresia(usuario_id=u.id, organizacion_id=org.id, rol="propietario", activa=True))
    lic = Licencia(organizacion_id=org.id, estado="activa", origen="prueba", inicio=hoy - timedelta(days=14), vence=hoy - timedelta(days=7), importe=0, creada_por_email="bob@example.com")
    db.add(lic)
    pc = PruebaConcedida(email_normalizado="bob@example.com", email_original="bob@example.com", organizacion_id=org.id, ip_hash="x", dias=7)
    pc.created_at = datetime.combine(hoy - timedelta(days=14), datetime.min.time())
    db.add(pc)
    db.add(Configuracion(organizacion_id=org.id, empresa_nombre="Vencida", empresa_pais="Venezuela", moneda_default="USD", iva_default=16))
    db.commit()

    llamadas=[]
    def fake(email, plantilla=None, contexto=None, **kw):
        llamadas.append(plantilla or kw.get("plantilla"))
        return "id"

    res = enviar_secuencia_marketing(db, remitente=fake, hoy=hoy)
    assert any("winback_7" in c for c in llamadas), f"esperaba winback_7, llamadas={llamadas} res={res}"
    db.close(); eng.dispose()


# ---------- Campañas ----------

def test_campana_a_segmento():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    org = _org_con_prueba(db, nombre="CampTest")
    llamadas=[]
    def fake(email, plantilla=None, contexto=None, **kw):
        llamadas.append((email, plantilla or kw.get("plantilla")))
        return "id"
    res = enviar_campana(db, plantilla="novedades", segmento="prueba", remitente=fake, titulo_campana="Nov Oct", cuerpo_campana="Hola", cta_url="https://cotizat.online/novedades", cta_label="Ver")
    assert res["enviadas"]
    # reenviar misma campaña idempotente
    llamadas.clear()
    res2 = enviar_campana(db, plantilla="novedades", segmento="prueba", remitente=fake)
    assert not res2["enviadas"]
    assert res2["omitidas_ya_enviada"]
    db.close(); eng.dispose()


def test_campana_plantilla_desconocida_falla():
    eng = _engine()
    Session = sessionmaker(bind=eng)
    db = Session()
    with pytest.raises(ValueError):
        enviar_campana(db, plantilla="noexiste", segmento="prueba", remitente=lambda **kw: "id")
    db.close(); eng.dispose()


# ---------- Ruta pública de baja ----------

def test_ruta_publica_baja_get_y_post(monkeypatch):
    monkeypatch.setenv("COTIZAT_PUBLIC_URL", "https://cotizat.online")
    monkeypatch.setenv("CRON_SECRET", "testsecret123")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_mkt_baja.db")
    import pathlib
    pathlib.Path("test_mkt_baja.db").unlink(missing_ok=True)
    from app.models import Base as BM
    from app.database import engine as eng_main
    BM.metadata.create_all(bind=eng_main)

    tok = token_baja("carla@example.com")
    client = TestClient(app)
    # GET con token válido muestra form
    resp = client.get(f"/baja-marketing?token={tok}")
    assert resp.status_code == 200
    assert "carla@example.com" in resp.text

    # POST confirma baja
    resp = client.post("/baja-marketing", data={"token": tok})
    assert resp.status_code == 200
    assert "Baja confirmada" in resp.text

    # GET posterior muestra ya dada de baja
    resp = client.get(f"/baja-marketing?token={tok}")
    assert "Ya no recibes" in resp.text

    # Token inválido 400-ish page
    resp = client.get("/baja-marketing?token=malo")
    assert resp.status_code in (200, 400)
    assert "no válido" in resp.text.lower()

    pathlib.Path("test_mkt_baja.db").unlink(missing_ok=True)
