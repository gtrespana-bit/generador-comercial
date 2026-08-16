"""E3-023 — baja de organización con borrado verificado.

La baja es irreversible y solo del propietario: exige escribir el nombre
exacto de la organización y marcar una casilla explícita. Estas pruebas
cubren el resumen, los rechazos sin efectos, el borrado completo (datos,
archivos del almacenamiento privado, licencias, membresías y organización),
el aislamiento entre organizaciones, el fallo de almacenamiento sin borrado
parcial, la respuesta post-baja sin cookie de organización y la definición de
la función PostgreSQL (guardias de claim y de rol).
"""
from types import SimpleNamespace
from datetime import date
from urllib.parse import unquote

import pytest

from app.models import (
    ArchivoAlmacenado,
    Cliente,
    Configuracion,
    Licencia,
    Membresia,
    Organizacion,
    PermisoOrganizacionError,
    Presupuesto,
    Usuario,
)
from app.services.baja import BajaError, ejecutar_baja, resumen_baja
from app.storage import get_storage_backend

from migrations.versions import a3d7e9c1b5f2_baja_organizacion_function as migration

from tests.conftest import NOMBRE_ORG


class _FakeBind:
    dialect = SimpleNamespace(name="postgresql")


def _post_baja(cliente, nombre=None, confirmar="si"):
    return cliente.post(
        "/configuracion/baja/confirmar",
        data={
            "nombre_confirmado": nombre if nombre is not None else NOMBRE_ORG,
            "confirmar": confirmar,
        },
        headers={"Origin": "https://cotizat.test"},
        follow_redirects=False,
    )


def _tablas_con_datos(Session, org_id):
    """Conteos de negocio visibles desde la organización activa."""
    with Session() as db:
        db.info["organizacion_id"] = org_id
        db.info["rol_membresia"] = "propietario"
        return {
            "presupuestos": db.query(Presupuesto).count(),
            "clientes": db.query(Cliente).count(),
            "configuracion": db.query(Configuracion).count(),
            "archivos": db.query(ArchivoAlmacenado).count(),
        }


# ---------------------------------------------------------------------------
# Pantalla y guardias
# ---------------------------------------------------------------------------

def test_pantalla_muestra_resumen_y_exige_rol_propietario(entorno, cliente_web):
    Session, ids, rol = entorno

    rol["valor"] = "administrador"
    respuesta = cliente_web.get("/configuracion/baja", follow_redirects=False)
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/configuracion")

    rol["valor"] = "propietario"
    pagina = cliente_web.get("/configuracion/baja")
    assert pagina.status_code == 200
    assert NOMBRE_ORG in pagina.text
    assert "/configuracion/exportacion/descargar" in pagina.text
    assert "irreversible" in pagina.text


def test_nombre_incorrecto_no_borra_nada(entorno, cliente_web):
    Session, ids, rol = entorno
    antes = _tablas_con_datos(Session, ids[0])
    respuesta = _post_baja(cliente_web, nombre="Nombre Incorrecto")
    assert respuesta.status_code == 303
    assert "no coincide" in unquote(respuesta.headers["location"])
    assert _tablas_con_datos(Session, ids[0]) == antes


def test_sin_casilla_no_borra_nada(entorno, cliente_web):
    Session, ids, rol = entorno
    antes = _tablas_con_datos(Session, ids[0])
    respuesta = _post_baja(cliente_web, confirmar="")
    assert respuesta.status_code == 303
    assert "casilla" in unquote(respuesta.headers["location"])
    assert _tablas_con_datos(Session, ids[0]) == antes


def test_solo_el_propietario_puede_ejecutar_la_baja(entorno, cliente_web):
    Session, ids, rol = entorno
    rol["valor"] = "miembro"
    respuesta = _post_baja(cliente_web)
    assert respuesta.status_code == 303
    assert _tablas_con_datos(Session, ids[0])["presupuestos"] == 2


# ---------------------------------------------------------------------------
# Borrado completo y verificable
# ---------------------------------------------------------------------------

def test_baja_borra_datos_archivos_licencias_membresias_y_organizacion(entorno, cliente_web):
    Session, ids, rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        objeto = db.query(ArchivoAlmacenado).first()
        clave = objeto.object_key
        backend = get_storage_backend()
        assert backend.read(clave) == b"PNG-logotipo-empresa"

    respuesta = _post_baja(cliente_web)
    assert respuesta.status_code == 200
    assert "fue dada de baja" in respuesta.text
    assert "no-store" in respuesta.headers.get("cache-control", "")
    # La cookie de organización se retira para no apuntar a una org borrada
    assert "cotizat_organization_id=" in respuesta.headers.get("set-cookie", "")
    assert "Max-Age=0" in respuesta.headers.get("set-cookie", "")

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["rol_membresia"] = "propietario"
        for modelo in (Presupuesto, Cliente, Configuracion, ArchivoAlmacenado):
            assert db.query(modelo).count() == 0
        assert db.query(Licencia).filter(Licencia.organizacion_id == ids[0]).count() == 0
        assert db.query(Membresia).filter(Membresia.organizacion_id == ids[0]).count() == 0
        assert db.get(Organizacion, ids[0]) is None
        # La cuenta de usuario NO se borra (identidad de Auth)
        assert db.get(Usuario, ids[1]) is not None
    # El objeto del almacenamiento privado desapareció
    from app.storage import StorageError
    with pytest.raises(StorageError):
        backend.read(clave)


def test_baja_no_toca_otra_organizacion(entorno, cliente_web):
    Session, ids, rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["rol_membresia"] = "propietario"
        otra = Organizacion(nombre="Otra Constructora", slug="otra")
        db.add(otra)
        db.flush()
        db.info["organizacion_id"] = otra.id
        cliente_b = Cliente(nombre="Cliente de Otra")
        db.add(cliente_b)
        db.flush()
        otro_presupuesto = Presupuesto(
            numero="P-OTRA-001", year=2026,
            fecha=date(2026, 8, 16),
            titulo="Obra de otra", client_id=cliente_b.id,
        )
        db.add(otro_presupuesto)
        db.commit()
        otra_id = otra.id

    respuesta = _post_baja(cliente_web)
    assert respuesta.status_code == 200

    with Session() as db:
        assert db.get(Organizacion, otra_id) is not None
        db.info["organizacion_id"] = otra_id
        assert db.query(Presupuesto).count() == 1
        assert db.query(Cliente).count() == 1


def test_fallo_de_almacenamiento_aborta_sin_borrar_nada(entorno, cliente_web, monkeypatch):
    Session, ids, rol = entorno
    antes = _tablas_con_datos(Session, ids[0])

    def _delete_roto(clave):
        raise RuntimeError("bucket no disponible")

    backend = get_storage_backend()
    monkeypatch.setattr(backend, "delete", _delete_roto)

    respuesta = _post_baja(cliente_web)
    assert respuesta.status_code == 303
    assert "almacenamiento" in unquote(respuesta.headers["location"])
    assert _tablas_con_datos(Session, ids[0]) == antes
    with Session() as db:
        assert db.get(Organizacion, ids[0]) is not None


def test_servicio_rechaza_sin_contexto_o_sin_rol(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["rol_membresia"] = "propietario"
        with pytest.raises(BajaError, match="organización activa"):
            ejecutar_baja(db, nombre_confirmado=NOMBRE_ORG, confirmar=True)

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["rol_membresia"] = "lectura"
        with pytest.raises(PermisoOrganizacionError):
            ejecutar_baja(db, nombre_confirmado=NOMBRE_ORG, confirmar=True)


def test_resumen_baja_lista_conteos_y_archivos(entorno):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.info["rol_membresia"] = "propietario"
        resumen = resumen_baja(db)
        assert resumen["nombre"] == NOMBRE_ORG
        assert resumen["conteos"]["presupuestos"] == 2  # incluye el de demostración
        assert resumen["conteos"]["licencias"] == 1
        assert resumen["conteos"]["membresias"] == 2
        assert resumen["archivos"] == 2


# ---------------------------------------------------------------------------
# Definición PostgreSQL: guardias de claim y de rol, y permisos de ejecución
# ---------------------------------------------------------------------------

def test_funcion_postgresql_borra_en_orden_y_con_guardias(monkeypatch):
    statements = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: _FakeBind())
    monkeypatch.setattr(migration.op, "execute", lambda statement: statements.append(str(statement)))
    migration.upgrade()
    sql = "\n".join(statements)
    upper = sql.upper()

    assert "CREATE OR REPLACE FUNCTION COTIZAT_SECURITY.BAJA_ORGANIZACION" in upper
    assert "SECURITY DEFINER" in upper
    assert "CURRENT_SETTING('COTIZAT.ORGANIZATION_ID', TRUE)" in upper
    assert "MEMBERSHIP_ROLE(P_ORGANIZATION_ID)" in upper
    assert "'PROPIETARIO'" in upper
    assert "DELETE FROM PUBLIC.ORGANIZACIONES" in upper
    assert "DELETE FROM PUBLIC.ARCHIVOS_ALMACENADOS" in upper
    assert "DELETE FROM PUBLIC.LICENCIAS" in upper
    assert "DELETE FROM PUBLIC.MEMBRESIAS" in upper
    # Ejecución solo para el rol de aplicación, nunca pública
    assert "REVOKE ALL ON FUNCTION COTIZAT_SECURITY.BAJA_ORGANIZACION(INTEGER) FROM PUBLIC" in upper
    assert "GRANT EXECUTE ON FUNCTION COTIZAT_SECURITY.BAJA_ORGANIZACION(INTEGER) TO COTIZAT_APP" in upper


def test_migracion_baja_no_hace_nada_en_sqlite(monkeypatch):
    statements = []
    monkeypatch.setattr(
        migration.op, "get_bind", lambda: SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    )
    monkeypatch.setattr(migration.op, "execute", lambda statement: statements.append(str(statement)))
    migration.upgrade()
    assert statements == []


def test_migracion_baja_cuelga_del_head_anterior():
    assert migration.down_revision == "c2f6e8a1d934"
    assert migration.revision == "a3d7e9c1b5f2"
