"""Pruebas del Asistente de Inteligencia Artificial de CotizaT (Copilot)."""

import json
from unittest.mock import MagicMock, patch
import urllib.error

from starlette.testclient import TestClient

from app.database import get_authenticated_db, get_db
from app.main import app
from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    Organizacion,
    Partida,
    Presupuesto,
    PresupuestoItem,
    Producto,
    RecetaEstancia,
    Recurso,
)
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
    assert estado["herramientas_locales_sin_consumo"] is True
    assert estado["generacion_sujeta_a_cuotas_proveedor"] is True
    assert estado["gratuito"] is None


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


def test_busqueda_funcional_partidas_consulta_natural_sin_api(monkeypatch, tmp_path):
    """La pregunta reportada debe devolver catálogo real, no instrucciones."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("COTIZAT_GROQ_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.dotenv_values", lambda *args, **kwargs: {})

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_busqueda_partidas_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1

    db.add(Organizacion(id=1, nombre="Reformas Demo", slug="reformas-demo"))
    db.add(Configuracion(
        organizacion_id=1,
        empresa_nombre="Reformas Demo",
        moneda_default="USD",
    ))
    db.add_all([
        Partida(
            organizacion_id=1,
            codigo_interno="02.10.01.010",
            nombre="Demolición de piso de baldosa cerámica o porcelanato",
            descripcion="Incluye picado, retiro del material y limpieza del soporte.",
            unidad="m2",
            precio_unitario=7.25,
            categoria="02 Demoliciones",
        ),
        Partida(
            organizacion_id=1,
            codigo_interno="12.05.03.010",
            nombre="Colocación de piso de porcelanato",
            descripcion="Suministro y colocación sobre soporte preparado.",
            unidad="m2",
            precio_unitario=12.0,
            categoria="12 Revestimientos",
        ),
    ])
    db.commit()

    consulta = "¿Qué partida es para demolicion de porcelanato?"
    assert asistente_ia.es_consulta_busqueda_partidas(consulta)
    assert asistente_ia.extraer_consulta_partidas(consulta) == "demolicion porcelanato"

    respuesta = asistente_ia.consultar_asistente_sync(
        db,
        [{"role": "user", "content": consulta}],
        {"pagina": "/presupuestos/99/editar", "presupuesto_id": 99},
    )
    assert "Partidas encontradas en tu catálogo" in respuesta
    assert "02.10.01.010" in respuesta
    assert "Demolición de piso" in respuesta
    assert "/partidas/1/editar" in respuesta
    assert "/api/ia/accion/agregar-partida?partida_id=1" in respuesta
    assert "7.25 USD" in respuesta
    assert "cómo buscar" not in respuesta.lower()


def test_busqueda_funcional_respeta_organizacion_activa(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_tenant_busqueda_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add_all([
        Organizacion(id=1, nombre="Empresa Uno", slug="empresa-uno"),
        Organizacion(id=2, nombre="Empresa Dos", slug="empresa-dos"),
        Configuracion(organizacion_id=1, empresa_nombre="Empresa Uno"),
        Configuracion(organizacion_id=2, empresa_nombre="Empresa Dos"),
        Partida(
            organizacion_id=1,
            codigo_interno="ORG1-DEM",
            nombre="Demolición de piso de porcelanato",
            unidad="m2",
        ),
        Partida(
            organizacion_id=2,
            codigo_interno="ORG2-SECRETA",
            nombre="Demolición secreta de piso de porcelanato",
            unidad="m2",
        ),
    ])
    db.commit()
    db.info["organizacion_id"] = 1

    resultado = asistente_ia.buscar_partidas_catalogo(
        db, "¿Qué partida uso para demolicion porcelanato?"
    )
    codigos = {partida["codigo"] for partida in resultado["resultados"]}
    assert "ORG1-DEM" in codigos
    assert "ORG2-SECRETA" not in codigos


def test_busqueda_funcional_no_llama_groq_aunque_haya_clave(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    monkeypatch.setenv("GROQ_API_KEY", "gsk_fake")
    engine = create_engine(f"sqlite:///{tmp_path}/test_accion_antes_groq.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa"))
    db.add(Partida(
        organizacion_id=1,
        codigo_interno="DEM-01",
        nombre="Demolición de piso de porcelanato",
    ))
    db.commit()

    with patch("urllib.request.urlopen") as urlopen:
        respuesta = asistente_ia.consultar_asistente_sync(
            db,
            [{"role": "user", "content": "Busca una partida para demoler porcelanato"}],
        )
    assert "DEM-01" in respuesta
    urlopen.assert_not_called()


def test_variantes_catalogo_reconstruyen_tilde():
    from app.services.busqueda_catalogo import variantes_consulta

    variantes = variantes_consulta("demolicion ceramica")
    assert "demolición" in variantes[0]
    assert "cerámica" in variantes[1]


def test_herramientas_buscan_clientes_productos_y_recursos(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_herramientas_busqueda.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa"))
    db.add_all([
        Cliente(
            organizacion_id=1,
            nombre="Constructora Luna",
            rif="J-123",
            email="compras@luna.test",
        ),
        Producto(
            organizacion_id=1,
            nombre="Porcelanato Luna 60x60",
            sku="POR-6060",
            precio_unitario=19.5,
            moneda="USD",
            unidad="m2",
        ),
        Recurso(
            organizacion_id=1,
            codigo="MAT-CEM",
            descripcion="Cemento gris estructural",
            categoria="materiales",
            precio=9.25,
            moneda="USD",
            unidad="saco",
        ),
    ])
    db.commit()

    cliente = asistente_ia.resolver_accion_funcional(db, "Busca el cliente Constructora Luna")
    producto = asistente_ia.resolver_accion_funcional(db, "Busca el producto POR-6060")
    recurso = asistente_ia.resolver_accion_funcional(db, "Encuentra el recurso cemento gris")

    assert "Constructora Luna" in cliente
    assert "/clientes/1/editar" in cliente
    assert "Porcelanato Luna" in producto
    assert "/productos/1/editar" in producto
    assert "MAT-CEM" in recurso
    assert "/recursos?q=" in recurso


def test_herramienta_revisa_presupuesto_abierto(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_revision_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa"))
    cliente = Cliente(organizacion_id=1, nombre="Cliente sin contacto")
    db.add(cliente)
    db.flush()
    presupuesto = Presupuesto(
        organizacion_id=1,
        numero="P-2026-001",
        year=2026,
        titulo="Baño principal",
        client_id=cliente.id,
        moneda="USD",
    )
    capitulo = Capitulo(
        organizacion_id=1,
        nombre="DEMOLICIONES",
        orden=0,
        presupuesto=presupuesto,
    )
    capitulo.partidas.append(PresupuestoItem(
        organizacion_id=1,
        nombre="Demolición de piso",
        cantidad=0,
        precio_unitario=0,
        orden=0,
    ))
    db.add(presupuesto)
    db.commit()

    respuesta = asistente_ia.resolver_accion_funcional(
        db,
        "Revisa este presupuesto y dime si está listo para enviar",
        {"pagina": f"/presupuestos/{presupuesto.id}/editar", "presupuesto_id": presupuesto.id},
    )
    assert "P-2026-001" in respuesta
    assert "Puntuación" in respuesta
    assert "Puntos críticos" in respuesta
    assert "sin precio" in respuesta.lower()
    assert f"/presupuestos/{presupuesto.id}/editar" in respuesta


def test_herramienta_propone_pack_real_y_accion_confirmable(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    engine = create_engine(f"sqlite:///{tmp_path}/test_pack_ia.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa"))
    receta = RecetaEstancia(
        organizacion_id=1,
        nombre="Baño estándar",
        categoria="Baños",
        unidad_base="m2",
        cantidad_base_default=8,
        datos=json.dumps([
            {"nombre": "Demolición de piso", "precio": 5, "unidad": "m2"},
            {"nombre": "Colocación de porcelanato", "precio": 12, "unidad": "m2"},
        ]),
    )
    db.add(receta)
    db.commit()

    respuesta = asistente_ia.resolver_accion_funcional(
        db,
        "¿Qué capítulos y partidas debo incluir para remodelar un baño?",
        {"pagina": "/presupuestos/7/editar", "presupuesto_id": 7},
    )
    assert "Estructuras disponibles" in respuesta
    assert "Baño estándar" in respuesta
    assert "Demolición de piso" in respuesta
    assert f"/api/ia/accion/abrir-pack?receta_id={receta.id}" in respuesta


def test_contexto_pagina_usa_presupuesto_verificado(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    from app.services.herramientas_ia import contexto_pagina_verificado

    engine = create_engine(f"sqlite:///{tmp_path}/test_contexto_pagina.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    cliente = Cliente(organizacion_id=1, nombre="Cliente")
    db.add(cliente)
    db.flush()
    presupuesto = Presupuesto(
        organizacion_id=1,
        numero="P-2026-009",
        year=2026,
        titulo="Cocina",
        client_id=cliente.id,
    )
    db.add(presupuesto)
    db.commit()

    contexto = contexto_pagina_verificado(db, {
        "pagina": f"/presupuestos/{presupuesto.id}/editar",
        "presupuesto_id": presupuesto.id,
    })
    assert "P-2026-009" in contexto
    assert "Proyecto: Cocina" in contexto
    assert "Ruta abierta" in contexto


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
    db.add(Partida(
        organizacion_id=1,
        codigo_interno="DEM-PORC-01",
        nombre="Demolición de piso de porcelanato",
        unidad="m2",
        precio_unitario=8.5,
    ))
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

    # 5. Búsqueda funcional contra el catálogo desde el endpoint
    res_busqueda = client.post(
        "/api/ia/chat",
        json={
            "messages": [{
                "role": "user",
                "content": "¿Qué partida uso para demolicion de porcelanato?",
            }],
            "stream": False,
            "contexto": {
                "pagina": "/presupuestos/123/editar",
                "presupuesto_id": 123,
            },
        },
    )
    assert res_busqueda.status_code == 200
    assert "DEM-PORC-01" in res_busqueda.json()["respuesta"]
    assert "/api/ia/accion/agregar-partida" in res_busqueda.json()["respuesta"]

    # 6. Revisión del borrador vivo enviado por el editor
    res_borrador = client.post(
        "/api/ia/chat",
        json={
            "messages": [{"role": "user", "content": "Revisa este presupuesto"}],
            "stream": False,
            "contexto": {
                "pagina": "/presupuestos/123/editar",
                "presupuesto_id": 123,
                "borrador": [{
                    "nombre": "CAPÍTULO",
                    "partidas": [{
                        "nombre": "Partida sin precio",
                        "unidad": "m2",
                        "cantidad": 2,
                        "precio": 0,
                    }],
                }],
            },
        },
    )
    assert res_borrador.status_code == 200
    assert "borrador visible" in res_borrador.json()["respuesta"]
    assert "sin precio" in res_borrador.json()["respuesta"].lower()

    # 7. Chat endpoint vacío
    res_chat_vacio = client.post(
        "/api/ia/chat",
        json={"messages": []},
    )
    assert res_chat_vacio.status_code == 400

    app.dependency_overrides.clear()
