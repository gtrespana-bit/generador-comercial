"""Incidente del 5/11/2026 — ``ECHECKOUTTIMEOUT`` en el buscador del catálogo.

Lo que llegó al buzón y al panel del operador era un 500 en
``GET /partidas/api/buscar`` con el mensaje del pooler de Supabase:

    (psycopg.errors.InternalError) ECHECKOUTTIMEOUT: checkout timeout
    (server_id: ...) after 60000ms in Transaction mode

El diagnóstico de entonces culpaba al tamaño del pool. No era eso: en Vercel el
motor ya usa ``NullPool``. La causa real era **el coste de la consulta**.
``_aplicar_busqueda_catalogo`` traducía cada palabra a
``8 campos × N variantes`` comparaciones ``ILIKE`` sueltas —hasta 384 por
petición, medidas: 250+ en la consulta que falló— y en el catálogo real
(15.000 partidas) tardaba 11 s de media. El editor la dispara en cada pausa del
tecleo, así que las peticiones se apilaban, el pooler en modo Transaction se
quedó sin huecos y acabó devolviendo el timeout a todos.

Estas pruebas fijan las tres cosas que se arreglaron:

1. **Una sola condición por palabra** (regex en PostgreSQL, ``OR`` de ``ILIKE``
   en SQLite) sobre el texto concatenado, y un tope de variantes.
2. **Un fallo de infraestructura no se trata como bug de producto**: 503 con
   ``Retry-After``, sin correo, y el cliente del editor deja de insistir.
3. **Una transacción por petición** para latido y presencia, no tres.

El comportamiento del endpoint se cubre además en ``test_busqueda_editor.py``.
"""
from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import app.services.errores_internos as errores_module
from app import database as database_module
from app.database import Base
from app.models import ErrorInterno, Partida
from app.routers import common as common_module
from app.services.busqueda_catalogo import (
    VARIANTES_MAXIMAS_POR_GRUPO,
    grupos_sinonimos,
    variantes_consulta,
)
from app.services.errores_internos import persistir_y_avisar
from app.services.operacion import (
    RegistroErroresMiddleware,
    _respuesta_de_saturacion,
    error_de_infraestructura,
)


# ---------------------------------------------------------------------------
# 1. La condición de búsqueda
# ---------------------------------------------------------------------------


def _sql(consulta: str, dialecto) -> str:
    """SQL que se enviaría a la base para una búsqueda del editor."""
    texto = common_module._texto_buscable_catalogo()
    stmt = select(Partida.id).where(Partida.oculta.is_(False))
    for variantes in variantes_consulta(consulta):
        condicion = common_module._condicion_de_un_grupo(
            texto, variantes, dialecto=dialecto.name
        )
        if condicion is not None:
            stmt = stmt.where(condicion)
    return str(stmt.compile(dialect=dialecto, compile_kwargs={"literal_binds": True}))


def test_postgresql_recibe_una_sola_regex_por_palabra():
    """La consulta que tardaba 11 s pasa a ser una expresión por palabra.

    Se cuenta ``ILIKE``/``~~*`` porque era justo la unidad de coste: cada uno
    obligaba a rehacer la concatenación de ocho columnas por fila.
    """
    sql = _sql("cable 12", postgresql.dialect())
    assert "~*" in sql
    assert "~~*" not in sql
    # Tantos grupos como palabras escribió la persona, ni uno más.
    assert sql.count("~*") == 2


def test_las_variantes_siguen_sumando_dentro_de_la_misma_expresion():
    """Los sinónimos no se pierden: entran en la alternancia de la regex."""
    grupos = variantes_consulta("cable")
    assert len(grupos) == 1
    assert "conductor" in grupos[0], grupos[0]
    sql = _sql("cable", postgresql.dialect())
    for variante in grupos[0]:
        assert variante in sql


def test_las_variantes_salen_escapadas_hacia_la_regex():
    """El texto lo escribe la persona: no puede inyectar sintaxis de regex."""
    texto = common_module._texto_buscable_catalogo()
    condicion = common_module._condicion_de_un_grupo(
        texto, ["cable.(", "a|b"], dialecto="postgresql"
    )
    patron = condicion.right.value
    assert "\\." in patron and "\\(" in patron
    assert "\\|" in patron


def test_sqlite_conserva_el_or_de_ilike():
    """Sin ``REGEXP`` en SQLite, la semántica se mantiene con ``ILIKE``."""
    sql = _sql("cable", sqlite.dialect())
    assert "LIKE" in sql.upper()
    assert "~*" not in sql


def test_la_busqueda_no_genera_cientos_de_condiciones():
    """La consulta de seis palabras queda en decenas de condiciones, no en 384.

    Era el número que hundía el pooler: la consulta que falló en producción
    llevaba más de 250 posiciones de evaluación ``ILIKE``.
    """
    grupos = variantes_consulta("cable de cobre para acometida aerea")
    condiciones = sum(len(g) for g in grupos)
    assert condiciones <= len(grupos) * VARIANTES_MAXIMAS_POR_GRUPO
    sql = _sql("cable de cobre para acometida aerea", postgresql.dialect())
    assert sql.count("~*") <= 6
    assert sql.count("~~*") == 0


def test_el_tope_de_variantes_esta_acotado():
    """Un grupo de sinónimos grande no puede volver a explotar la consulta."""
    assert 0 < VARIANTES_MAXIMAS_POR_GRUPO <= 20
    for grupo in variantes_consulta("cable tuberia pintura ceramica"):
        assert len(grupo) <= VARIANTES_MAXIMAS_POR_GRUPO


@pytest.mark.parametrize("consulta", ["", "   ", "·-·"])
def test_sin_palabras_no_se_filtra_nada(consulta):
    """Consulta vacía o solo signos: no se añade ninguna condición."""
    sentencia = select(Partida.id)
    resultado, grupos = common_module._aplicar_busqueda_catalogo(
        _ConsultaFalsa(sentencia), consulta
    )
    assert grupos == []
    sql = str(resultado.compile(dialect=postgresql.dialect()))
    assert "~*" not in sql


class _ConsultaFalsa:
    """Lo mínimo que ``_aplicar_busqueda_catalogo`` usa de una ``Query``.

    Evita levantar la app entera para una prueba que solo mira el SQL: el filtro
    se acumula con ``.where`` sobre la sentencia y el dialecto se resuelve con
    ``session.get_bind()``.
    """

    def __init__(self, sentencia):
        self._sentencia = sentencia
        self.session = _SesionFalsa()

    def filter(self, condicion):
        return _ConsultaFalsa(self._sentencia.where(condicion))

    def __str__(self):  # pragma: no cover - comodidad al depurar
        return str(self._sentencia)

    def compile(self, **kw):
        return self._sentencia.compile(**kw)


class _SesionFalsa:
    def get_bind(self):
        return _MotorFalso()


class _MotorFalso:
    class dialect:
        name = "postgresql"


# ---------------------------------------------------------------------------
# 2. Un fallo de infraestructura no es un bug de producto
# ---------------------------------------------------------------------------


class _TimeoutDePool(Exception):
    """Imita el ``TimeoutError`` que lanza SQLAlchemy al agotarse el pool."""


def test_reconoce_el_timeout_del_pooler_de_supabase():
    exc = RuntimeError(
        "(psycopg.errors.InternalError) ECHECKOUTTIMEOUT: checkout timeout "
        "(server_id: t9b4d7e2c5f8) after 60000ms in Transaction mode"
    )
    assert error_de_infraestructura(exc) is True


def test_reconoce_el_timeout_del_pool_propio():
    assert error_de_infraestructura(TimeoutError("QueuePool limit reached")) is True


def test_reconoce_una_base_sin_huecos_de_conexion():
    exc = RuntimeError('sorry, too many clients already')
    assert error_de_infraestructura(exc) is True


def test_un_bug_de_codigo_no_se_confunde_con_saturacion():
    assert error_de_infraestructura(ValueError("la partida no existe")) is False
    assert error_de_infraestructura(None) is False


def _app_con_saturacion(exc: Exception) -> TestClient:
    """Aplicación mínima con el middleware en la posición que usa ``main``.

    Se registra con ``add_middleware`` —no envolviendo la app a mano— porque ahí
    es donde el middleware queda **por debajo** de ``ServerErrorMiddleware`` de
    Starlette, que es la capa que construye el 500. Si estuviera por encima, la
    respuesta ya habría salido y solo se podría relanzar: ese detalle costó una
    iteración y queda fijado aquí.
    """

    async def saturada(_request):
        raise exc

    app = Starlette(routes=[Route("/buscar", saturada), Route("/catalogo", saturada)])
    app.add_middleware(RegistroErroresMiddleware)
    return TestClient(app, raise_server_exceptions=False)


def test_saturacion_devuelve_503_y_no_500(entorno_errores):
    """El usuario ve «vuelve en unos segundos», no una pantalla de error rota."""
    cliente = _app_con_saturacion(
        RuntimeError(
            "ECHECKOUTTIMEOUT: checkout timeout after 60000ms in Transaction mode"
        )
    )
    respuesta = cliente.get("/buscar", headers={"Accept": "application/json"})
    assert respuesta.status_code == 503
    assert respuesta.headers["Retry-After"]
    assert respuesta.json()["reintentar"] is True


def test_saturacion_en_navegacion_devuelve_texto_legible(entorno_errores):
    cliente = _app_con_saturacion(
        TimeoutError("QueuePool limit of size 5 overflow 10 reached")
    )
    respuesta = cliente.get("/catalogo", headers={"Accept": "text/html"})
    assert respuesta.status_code == 503
    assert "vuelve" in respuesta.text.lower()


def test_un_bug_de_codigo_conserva_el_500(entorno_errores):
    """Solo la saturación se convierte en 503: un bug real sigue siendo un 500."""
    cliente = _app_con_saturacion(ValueError("la partida no existe"))
    respuesta = cliente.get("/catalogo", headers={"Accept": "text/html"})
    assert respuesta.status_code == 500


def test_la_saturacion_no_manda_correo(entorno_errores):
    """Un incidente de infraestructura no puede inundar el buzón del titular."""
    Sesiones, enviados = entorno_errores
    persistir_y_avisar(
        {
            "metodo": "GET",
            "ruta": "/partidas/api/buscar",
            "tipo": "InternalError",
            "mensaje": "ECHECKOUTTIMEOUT ... after 60000ms in Transaction mode",
            "traza": "Traceback...",
            "ahora": datetime(2026, 11, 5, 1, 3),
            "transitorio": True,
        }
    )
    assert enviados == []
    # Pero queda constancia para el panel.
    with Sesiones() as db:
        assert db.query(ErrorInterno).count() == 1


def test_un_error_de_codigo_sigue_avisando(entorno_errores):
    Sesiones, enviados = entorno_errores
    persistir_y_avisar(
        {
            "metodo": "POST",
            "ruta": "/presupuestos/nuevo",
            "tipo": "DataError",
            "mensaje": "value too long for type character varying(200)",
            "traza": "Traceback...",
            "ahora": datetime(2026, 11, 5, 1, 4),
            "transitorio": False,
        }
    )
    assert len(enviados) == 1


# ---------------------------------------------------------------------------
# 3. Una transacción por petición
# ---------------------------------------------------------------------------


def test_latido_y_presencia_se_confirman_una_sola_vez(monkeypatch):
    """Anotar telemetría no puede costar tres transacciones por petición.

    Cada ``commit`` cerraba la transacción de la petición; la lectura siguiente
    abría otra, el listener ``after_begin`` reinstalaba los seis claims de RLS y
    el pool entregaba conexión de nuevo. En una petición de solo lectura eso era
    el triple de checkouts, justo lo que no sobra cuando el pooler está al
    límite.
    """
    from app.services import telemetria

    confirmaciones: list[str] = []

    class _Sesion:
        info = {"organizacion_id": 43, "auth_email": "titular@example.com"}

        def __init__(self) -> None:
            self.pendientes: list[object] = []

        def query(self, *_a, **_k):  # noqa: D401 - doble mínimo del ORM
            class _Consulta:
                def filter(self, *_a, **_k):
                    return self

                def first(self):
                    return None  # ni latido ni presencia de hoy

            return _Consulta()

        def add(self, objeto):
            self.pendientes.append(objeto)

        def flush(self):
            confirmaciones.append("flush")

        def commit(self):
            confirmaciones.append("commit")

        def rollback(self):
            confirmaciones.append("rollback")

    telemetria._PRESENCIA.clear()
    sesion = _Sesion()
    assert telemetria.latido_diario(sesion, confirmar=False) is True
    assert telemetria.marcar_presencia(sesion, confirmar=False) is True
    assert confirmaciones.count("commit") == 0
    assert confirmaciones.count("flush") == 2


def test_el_contrato_publico_sigue_confirmando(monkeypatch):
    """Quien llama a estas funciones por su cuenta obtiene la fila guardada."""
    from app.services import telemetria

    confirmaciones: list[str] = []

    class _Sesion:
        info = {"organizacion_id": 7}

        def query(self, *_a, **_k):
            class _Consulta:
                def filter(self, *_a, **_k):
                    return self

                def first(self):
                    return None

            return _Consulta()

        def add(self, _objeto):
            pass

        def flush(self):
            confirmaciones.append("flush")

        def commit(self):
            confirmaciones.append("commit")

        def rollback(self):
            confirmaciones.append("rollback")

    telemetria._PRESENCIA.clear()
    assert telemetria.latido_diario(_Sesion()) is True
    assert confirmaciones == ["commit"]


# ---------------------------------------------------------------------------
# 4. Espera máxima por conexión
# ---------------------------------------------------------------------------


def test_el_pool_propio_no_espera_mas_que_el_pooler(monkeypatch):
    """Un tope menor que los 60 s del pooler convierte la espera en un 503."""
    monkeypatch.delenv("COTIZAT_DB_POOL_TIMEOUT", raising=False)
    assert database_module._pool_timeout_configurado(usa_pool_propio=True) == (
        database_module.POOL_TIMEOUT_POR_DEFECTO
    )
    assert database_module.POOL_TIMEOUT_POR_DEFECTO < 60


def test_el_timeout_se_configura_y_se_puede_desactivar(monkeypatch):
    monkeypatch.setenv("COTIZAT_DB_POOL_TIMEOUT", "4")
    assert database_module._pool_timeout_configurado(usa_pool_propio=True) == 4
    monkeypatch.setenv("COTIZAT_DB_POOL_TIMEOUT", "0")
    assert database_module._pool_timeout_configurado(usa_pool_propio=True) == 0
    monkeypatch.setenv("COTIZAT_DB_POOL_TIMEOUT", "no-es-un-numero")
    assert database_module._pool_timeout_configurado(usa_pool_propio=True) == (
        database_module.POOL_TIMEOUT_POR_DEFECTO
    )


def test_con_nullpool_no_hay_cola_propia_que_limitar(monkeypatch):
    """En Vercel (``NullPool``) el límite lo pone el pooler, no SQLAlchemy."""
    assert database_module._pool_timeout_configurado(usa_pool_propio=False) == 0
    monkeypatch.setenv("COTIZAT_DB_POOL_TIMEOUT", "8")
    assert database_module._pool_timeout_configurado(usa_pool_propio=False) == 0


# ---------------------------------------------------------------------------
# 5. El cliente del editor deja de insistir
# ---------------------------------------------------------------------------


def test_el_buscador_respeta_el_retry_after_del_503():
    """Con el servidor saturado, el rebote de 140 ms no puede seguir martillando."""
    from pathlib import Path

    js = (
        Path(__file__).resolve().parents[1]
        / "app/static/js/editor/catalogo.js"
    ).read_text(encoding="utf-8")
    assert "Retry-After" in js
    assert "pausarBusquedaRemota" in js
    assert "busquedaRemotaPausada" in js


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


@pytest.fixture
def entorno_errores(monkeypatch):
    """BD SQLite con el esquema completo y el correo capturado."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sesiones = sessionmaker(bind=engine)
    monkeypatch.setattr(errores_module, "SessionLocal", Sesiones)
    enviados: list[dict] = []
    monkeypatch.setattr(
        "app.services.email.enviar_aviso_error_interno_por_email",
        lambda **kw: enviados.append(kw) or "id-de-prueba",
    )
    with errores_module._avisos_lock:
        errores_module._avisos_enviados.clear()
    yield Sesiones, enviados
    engine.dispose()


def test_el_diccionario_de_sinonimos_sigue_cargando():
    """Guardia: la composición nueva no puede vaciar los sinónimos."""
    assert grupos_sinonimos()


# ---------------------------------------------------------------------------
# 6. Un fallo de base no puede disfrazarse de «licencia vencida»
# ---------------------------------------------------------------------------


def test_un_timeout_al_comprobar_la_licencia_no_suspende_la_cuenta(monkeypatch):
    """El 5/11/2026 esto habría dicho «tu plan venció» a quien lo tiene pagado.

    ``organizacion_tiene_acceso`` devolvía ``False`` ante **cualquier**
    excepción. Con el pooler devolviendo ``ECHECKOUTTIMEOUT``, ese ``False`` se
    convertía en ``LicenciaSuspendidaError``: la persona veía la pantalla de
    suspensión con su licencia de pago vigente. No poder preguntar no es lo
    mismo que la respuesta sea «no».
    """
    from app.services.licencias import organizacion_tiene_acceso

    class _Sesion:
        def get_bind(self):
            class _Motor:
                class dialect:
                    name = "postgresql"

            return _Motor()

        def execute(self, *_a, **_k):
            raise RuntimeError(
                "ECHECKOUTTIMEOUT: checkout timeout after 60000ms in Transaction mode"
            )

        def rollback(self):
            pass

    with pytest.raises(RuntimeError, match="ECHECKOUTTIMEOUT"):
        organizacion_tiene_acceso(_Sesion(), 43)


def test_un_fallo_de_permisos_sigue_cerrando_el_paso():
    """El criterio fail-closed se mantiene para lo que **no** es infraestructura."""
    from app.services.licencias import organizacion_tiene_acceso

    class _Sesion:
        def get_bind(self):
            class _Motor:
                class dialect:
                    name = "postgresql"

            return _Motor()

        def execute(self, *_a, **_k):
            raise RuntimeError("permission denied for function organization_has_license")

        def rollback(self):
            pass

    assert organizacion_tiene_acceso(_Sesion(), 43) is False
