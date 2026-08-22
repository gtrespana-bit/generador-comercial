"""Pruebas del Asistente de Inteligencia Artificial de CotizaT (Copilot)."""

import json
from unittest.mock import MagicMock, patch
import urllib.error

from starlette.testclient import TestClient

from app.database import get_authenticated_db, get_db
from app.main import app
from app.models import Configuracion, Organizacion, Partida
from app.services import asistente_ia


def test_estado_asistente_sin_clave(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_GROQ_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.dotenv_values", lambda *args, **kwargs: {})

    assert not asistente_ia.asistente_configurado()
    estado = asistente_ia.estado_asistente()
    assert estado["ok"] is True
    assert estado["configurado"] is False
    assert "Groq" in estado["proveedor"]
    assert estado["modelo"] == "openai/gpt-oss-120b"


def test_estado_asistente_con_clave(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")

    assert asistente_ia.asistente_configurado()
    estado = asistente_ia.estado_asistente()
    assert estado["configurado"] is True
    assert estado["mensaje_activacion"] == ""


def test_modelo_groq_deprecado_se_migra(monkeypatch):
    monkeypatch.setenv("COTIZAT_IA_MODEL", "llama-3.3-70b-versatile")
    assert asistente_ia.obtener_modelo_ia() == "openai/gpt-oss-120b"

    monkeypatch.setenv("COTIZAT_IA_MODEL", "llama-3.1-8b-instant")
    assert asistente_ia.obtener_modelo_ia() == "openai/gpt-oss-20b"


def test_respuestas_locales_fallback():
    # Atajos
    r1 = asistente_ia.buscar_respuesta_local("¿Cuáles son los atajos de teclado?")
    assert r1 is not None
    assert "Alt + P" in r1
    assert "Alt + C" in r1
    assert "Ctrl + K" in r1

    # CYPE
    r2 = asistente_ia.buscar_respuesta_local("¿Cómo importo un archivo CYPE descompuesto?")
    assert r2 is not None
    assert "DPT020" in r2 or "CYPE" in r2

    # Monedas
    r3 = asistente_ia.buscar_respuesta_local("¿Cómo cambio la tasa de cambio o moneda?")
    assert r3 is not None
    assert "Configuración" in r3

    # Obra de baño
    r4 = asistente_ia.buscar_respuesta_local("Estructura para remodelar un baño")
    assert r4 is not None
    assert "Demoliciones" in r4 or "Fontanería" in r4

    # Consulta no coincidente
    assert asistente_ia.buscar_respuesta_local("pregunta aleatoria sin sentido") is None


def test_construir_system_prompt(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    org = Organizacion(id=1, nombre="Constructora Andina", slug="constructora-andina")
    db.add(org)
    cfg = Configuracion(organizacion_id=1, empresa_nombre="Constructora Andina", empresa_pais="Colombia", moneda_default="COP")
    db.add(cfg)
    partida = Partida(organizacion_id=1, codigo_interno="REV-01", nombre="Enchape de piso porcelanato", unidad="m2", precio_unitario=45000.0)
    db.add(partida)
    db.commit()

    prompt = asistente_ia.construir_system_prompt(db, "necesito porcelanato")
    assert "CotizaT" in prompt
    assert "Constructora Andina" in prompt
    assert "Colombia" in prompt
    assert "COP" in prompt
    assert "REV-01" in prompt or "Enchape" in prompt


def test_redaccion_tecnica_fallback():
    # Porcelanato
    r1 = asistente_ia._redaccion_tecnica_fallback("Enchapado de porcelanato 60x60", "m2")
    assert "mortero adhesivo" in r1.lower()
    assert "m2" in r1

    # Pintura
    r2 = asistente_ia._redaccion_tecnica_fallback("Pintura de caucho en paredes", "m2")
    assert "imprimación" in r2.lower() or "paramento" in r2.lower()

    # Demolición
    r3 = asistente_ia._redaccion_tecnica_fallback("Demolición de tabique de ladrillo", "m3")
    assert "escombros" in r3.lower() or "desalojo" in r3.lower()

    # Genérica
    r4 = asistente_ia._redaccion_tecnica_fallback("Instalación de cerradura de pomo", "ud")
    assert "mano de obra" in r4.lower()


def test_consultar_asistente_stream_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_GROQ_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.dotenv_values", lambda *args, **kwargs: {})

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_stream.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    mensajes = [{"role": "user", "content": "¿Cuáles son los atajos de teclado?"}]
    generador = asistente_ia.consultar_asistente_stream(db, mensajes)
    chunks = list(generador)

    assert len(chunks) >= 2
    assert "Alt + P" in "".join(chunks)


def test_consultar_asistente_stream_con_groq_mock(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_fake_mock_key")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_stream_mock.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    lineas_sse = [
        b'data: {"choices":[{"delta":{"content":"Respuesta "}}]}\n',
        b'data: {"choices":[{"delta":{"content":"desde "}}]}\n',
        b'data: {"choices":[{"delta":{"content":"Groq IA."}}]}\n',
        b'data: [DONE]\n'
    ]

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = lineas_sse

    with patch("urllib.request.urlopen", return_value=mock_resp):
        generador = asistente_ia.consultar_asistente_stream(
            db, [{"role": "user", "content": "Hola"}]
        )
        chunks = list(generador)

    texto_total = "".join(chunks)
    assert "Respuesta " in texto_total
    assert "Groq IA." in texto_total


def test_api_endpoints_ia(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_api_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    org = Organizacion(id=1, nombre="Empresa Demo", slug="empresa-demo")
    db.add(org)
    cfg = Configuracion(organizacion_id=1, empresa_nombre="Empresa Demo")
    db.add(cfg)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_authenticated_db] = override_get_db
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    # 1. Estado
    res_estado = client.get("/api/ia/estado")
    assert res_estado.status_code == 200
    data_estado = res_estado.json()
    assert data_estado["ok"] is True
    assert "Groq" in data_estado["proveedor"]

    # 2. Redacción técnica
    res_redactar = client.post(
        "/api/ia/redactar-descripcion",
        json={"titulo": "Instalación de porcelanato en piso", "categoria": "Pisos", "unidad": "m2"},
    )
    assert res_redactar.status_code == 200
    data_redactar = res_redactar.json()
    assert data_redactar["ok"] is True
    assert len(data_redactar["descripcion"]) > 10

    # 3. Validación de título vacío en redacción
    res_redactar_vacio = client.post(
        "/api/ia/redactar-descripcion",
        json={"titulo": "   "},
    )
    assert res_redactar_vacio.status_code == 400

    # 4. Chat endpoint (sync)
    res_chat = client.post(
        "/api/ia/chat",
        json={
            "messages": [{"role": "user", "content": "¿Cuáles son los atajos de teclado?"}],
            "stream": False,
        },
    )
    assert res_chat.status_code == 200
    data_chat = res_chat.json()
    assert data_chat["ok"] is True
    assert "Alt + P" in data_chat["respuesta"]

    # 5. Chat endpoint vacío
    res_chat_vacio = client.post(
        "/api/ia/chat",
        json={"messages": []},
    )
    assert res_chat_vacio.status_code == 400

    app.dependency_overrides.clear()
