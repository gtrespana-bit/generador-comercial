"""Regresiones de rendimiento (E-PERF).

Bloquean los cuellos de botella que hacían lentas las páginas principales
del despliegue web:

1. La auditoría del catálogo propio (``asegurar_catalogo_propio``) debe
   resolver el caso normal (versión aplicada) con consultas de metadatos,
   sin hidratar partidas ni transportar sus descompuestos JSON.
2. La resolución de precios de mercado por lote debe coincidir con la
   versión individual (misma jerarquía organización → nacional → base).
3. El cliente GoTrue reutiliza la conexión (keep-alive) y la identidad
   validada se cachea por token: sin eso, cada página paginaba un viaje
   completo DNS+TCP+TLS a Supabase Auth.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import app.auth as auth_module
from app.auth import (
    AUTH_CACHE_TTL,
    SupabaseAuthClient,
    SupabaseAuthSettings,
    _reset_cache_identidades,
    identity_for_request,
)
from app.database import Base
from app.models import Configuracion, Partida, PrecioRecursoMercado, Recurso
from app.services.catalogo_propio import (
    CATALOGO_VERSION,
    asegurar_catalogo_propio,
    sembrar_catalogo_propio,
)
from app.services.precios_mercado import (
    resolver_precio,
    resolver_precios_lote,
)


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.info["organizacion_id"] = 1
    return engine, db


@pytest.fixture()
def catalogo_aplicado():
    """Catálogo oficial sembrado y marca de versión al día (caso normal)."""
    engine, db = _session()
    try:
        db.add(Configuracion(organizacion_id=1))
        db.commit()
        sembrar_catalogo_propio(db)
        cfg = db.query(Configuracion).first()
        cfg.version_catalogo = CATALOGO_VERSION
        db.commit()
        yield db
    finally:
        db.close()
        engine.dispose()


def _contar_humedecturas(funcion):
    """Ejecuta ``funcion()`` y cuenta entidades Partida hidratadas por ORM."""
    contador = {"entidades": 0, "json": 0}

    @event.listens_for(Partida, "load")
    def _carga(target, _context):
        contador["entidades"] += 1
        contador["json"] += len(target.descomposicion_json or "")

    try:
        funcion()
    finally:
        event.remove(Partida, "load", _carga)
    return contador


def test_asegurar_catalogo_aplicado_no_hidrata_partidas(catalogo_aplicado):
    """Con la versión vigente aplicada, la auditoría no toca las filas del
    catálogo: antes cada visita a /partidas hidrataba ~3.500 entidades y
    transportaba varios MiB de descompuestos."""
    db = catalogo_aplicado
    resultado = _contar_humedecturas(lambda: asegurar_catalogo_propio(db))
    assert resultado["entidades"] == 0
    assert resultado["json"] == 0
    # Y no dispara ninguna migración.
    assert asegurar_catalogo_propio(db) is None


def test_asegurar_catalogo_version_atrasada_se_repara_una_vez(catalogo_aplicado):
    """Si la marca de versión quedó atrasada (p. ej. fila de configuración
    recreada), la migración corre UNA vez y la marca persiste."""
    db = catalogo_aplicado
    db.query(Configuracion).delete()
    db.commit()

    primera = asegurar_catalogo_propio(db)
    assert primera is not None and primera.get("ok") is True

    cfg = db.query(Configuracion).first()
    assert cfg is not None
    assert cfg.version_catalogo == CATALOGO_VERSION
    # La segunda visita ya no re-migra: era el bucle que hacía eterno
    # /partidas en producción.
    assert asegurar_catalogo_propio(db) is None


def test_lote_de_precios_coincide_con_la_resolucion_individual():
    engine, db = _session()
    try:
        recursos = [
            Recurso(descripcion="Cemento", unidad="kg", categoria="materiales",
                    codigo="MAT-1", precio=1.5, moneda="USD"),
            Recurso(descripcion="Oficial", unidad="hora", categoria="mano_obra",
                    codigo="MO-1", precio=5.0, moneda="USD"),
            Recurso(descripcion="Andamio", unidad="dia", categoria="otros",
                    codigo="EQ-1", precio=20.0, moneda="USD"),
        ]
        db.add_all(recursos)
        db.flush()
        db.add_all([
            PrecioRecursoMercado(recurso_id=recursos[0].id, pais_codigo="CO",
                                 organizacion_id=None, precio=6000, moneda="COP",
                                 confianza="confirmado"),
            PrecioRecursoMercado(recurso_id=recursos[0].id, pais_codigo="CO",
                                 organizacion_id=1, precio=6100, moneda="COP",
                                 confianza="confirmado"),
            PrecioRecursoMercado(recurso_id=recursos[1].id, pais_codigo="CO",
                                 organizacion_id=None, precio=18000, moneda="COP",
                                 confianza="provisional"),
        ])
        db.commit()

        lote = resolver_precios_lote(db, recursos, "co", 1)
        assert set(lote) == {r.id for r in recursos}
        for recurso in recursos:
            individual = resolver_precio(db, recurso.id, "co", 1)
            por_lote = lote[recurso.id]
            assert por_lote.origen == individual.origen
            assert por_lote.precio == individual.precio
            assert por_lote.moneda == individual.moneda
            assert (por_lote.aviso or "") == (individual.aviso or "")
        # El override de organización gana al nacional.
        assert lote[recursos[0].id].origen == "organizacion"
        assert lote[recursos[0].id].precio == 6100
        # Sin precio de mercado y moneda USD → precio base con aviso.
        assert lote[recursos[2].id].origen == "base"
        assert lote[recursos[2].id].precio == 20.0
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Cliente GoTrue: keep-alive y caché de identidad
# ---------------------------------------------------------------------------

class _GoTrueLocal(BaseHTTPRequestHandler):
    """GoTrue de mentira: valida ``Bearer bueno`` y cuenta conexiones."""

    # HTTP/1.1 permite keep-alive; con 1.0 el servidor cierra la conexión
    # tras cada respuesta y no se puede verificar la reutilización.
    protocol_version = "HTTP/1.1"

    class _estado:
        conexiones = 0
        peticiones = 0

    def setup(self):
        super().setup()
        type(self)._estado.conexiones += 1

    def log_message(self, *args):  # noqa: N810 - silenciar la salida de pruebas
        pass

    def _responder(self, codigo, cuerpo):
        body = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self)._estado.peticiones += 1
        if self.headers.get("Authorization") == "Bearer bueno":
            self._responder(200, {
                "id": "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c",
                "email": "persona@example.com",
                "email_confirmed_at": "2026-08-13T00:00:00Z",
                "user_metadata": {"name": "Persona"},
            })
        else:
            self._responder(401, {"msg": "bad token"})

    def do_POST(self):
        longitud = int(self.headers.get("Content-Length", "0") or 0)
        self.rfile.read(longitud)
        type(self)._estado.peticiones += 1
        self._responder(200, {
            "access_token": "bueno",
            "refresh_token": "refresco",
            "expires_in": 3600,
            "user": {
                "id": "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c",
                "email": "persona@example.com",
                "user_metadata": {"name": "Persona"},
            },
        })


@pytest.fixture()
def gotrue_local():
    class _Servicio(ThreadingHTTPServer):
        daemon_threads = True

    servidor = _Servicio(("127.0.0.1", 0), _GoTrueLocal)
    _GoTrueLocal._estado.conexiones = 0
    _GoTrueLocal._estado.peticiones = 0
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    puerto = servidor.server_address[1]
    cliente = SupabaseAuthClient(SupabaseAuthSettings(
        url=f"http://127.0.0.1:{puerto}",
        publishable_key="sb_publishable_prueba",
        cookie_secure=False,
    ))
    yield cliente, _GoTrueLocal._estado
    # Se cierra ANTES la conexión keep-alive del cliente: si no, el hilo del
    # servidor se queda esperando la siguiente petición de ese socket.
    cliente._cerrar_conexion()
    servidor.shutdown()
    servidor.server_close()
    hilo.join(timeout=2)


def _peticion_con_token(token: str):
    """Request mínima con cookies y ``state`` propios (sin compartir estado)."""
    peticion = SimpleNamespace(
        cookies={"cotizat_access_token": token},
        state=SimpleNamespace(),
    )
    return peticion


def test_cliente_gotrue_reutiliza_conexion(gotrue_local):
    """Varias peticiones seguidas viajan por UNA conexión TCP (keep-alive)."""
    cliente, estado = gotrue_local
    for _ in range(3):
        identidad = cliente.get_user("bueno")
        assert identidad.email == "persona@example.com"
    assert estado.peticiones == 3
    assert estado.conexiones <= 2  # una sola, con margen para un reintento


def test_cliente_gotrue_error_401_es_credencial_invalida(gotrue_local):
    from app.auth import InvalidCredentials

    cliente, _ = gotrue_local
    with pytest.raises(InvalidCredentials):
        cliente.get_user("caducado")


def test_cliente_gotrue_refresca_y_devuelve_tokens(gotrue_local):
    cliente, _ = gotrue_local
    tokens = cliente.refresh("refresco-viejo")
    assert tokens.access_token == "bueno"
    assert tokens.identity.email == "persona@example.com"


def test_identidad_cacheada_evita_revalidar_por_red(gotrue_local, monkeypatch):
    """Con el mismo access token, la segunda petición no llama a GoTrue."""
    cliente, estado = gotrue_local
    monkeypatch.setattr(auth_module, "AUTH_CACHE_TTL", 60.0)
    monkeypatch.setattr(
        auth_module, "SupabaseAuthClient", lambda *a, **k: cliente
    )
    _reset_cache_identidades()

    primera = identity_for_request(_peticion_con_token("bueno"))
    segunda = identity_for_request(_peticion_con_token("bueno"))
    assert primera is segunda
    assert estado.peticiones == 1  # solo la validación inicial
    _reset_cache_identidades()


def test_identidad_no_se_cachea_con_ttl_cero(gotrue_local, monkeypatch):
    cliente, estado = gotrue_local
    monkeypatch.setattr(auth_module, "AUTH_CACHE_TTL", 0.0)
    monkeypatch.setattr(
        auth_module, "SupabaseAuthClient", lambda *a, **k: cliente
    )
    _reset_cache_identidades()

    identity_for_request(_peticion_con_token("bueno"))
    identity_for_request(_peticion_con_token("bueno"))
    assert estado.peticiones == 2
    _reset_cache_identidades()


def test_ttl_por_defecto_es_positivo():
    # Documenta el valor por defecto (180 s); 0 la desactiva por completo.
    assert AUTH_CACHE_TTL > 0


@pytest.fixture(autouse=True)
def _cache_limpia():
    """La caché de identidades nunca debe gotear entre pruebas."""
    _reset_cache_identidades()
    yield
    _reset_cache_identidades()
