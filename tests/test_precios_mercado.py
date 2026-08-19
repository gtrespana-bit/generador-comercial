from app.models import Organizacion, Recurso
from app.services.precios_mercado import guardar_precio, resolver_precio


def test_precio_organizacion_sobrescribe_nacional(entorno):
    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    org_id = ids[0]
    recurso = Recurso(organizacion_id=org_id, descripcion="Cemento", unidad="saco", precio=5, moneda="USD")
    db.add(recurso); db.flush()
    guardar_precio(db, recurso.id, "CO", 32000, "COP")
    guardar_precio(db, recurso.id, "CO", 35000, "COP", organizacion_id=org_id)
    db.flush()
    assert resolver_precio(db, recurso.id, "CO", org_id).precio == 35000
    assert resolver_precio(db, recurso.id, "CO", org_id).origen == "organizacion"


def test_precio_nacional_no_afecta_otro_pais(entorno):
    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    org_id = ids[0]
    recurso = Recurso(organizacion_id=org_id, descripcion="Cemento", unidad="saco", precio=5, moneda="USD")
    db.add(recurso); db.flush()
    guardar_precio(db, recurso.id, "CO", 32000, "COP")
    db.flush()
    assert resolver_precio(db, recurso.id, "CO", org_id).precio == 32000
    assert resolver_precio(db, recurso.id, "PE", org_id).origen == "base"


def test_no_se_puede_guardar_un_override_sin_organizacion_real(entorno):
    """`organizacion_id=0` no puede colarse como precio nacional.

    Los routers leen la organización de `db.info`; si el contexto no estuviera
    listo, un `0` se habría guardado como referencia nacional (visible para
    todas las empresas) o habría roto la clave foránea.
    """
    import pytest

    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    recurso = Recurso(organizacion_id=ids[0], descripcion="Arena", unidad="m3", precio=9, moneda="USD")
    db.add(recurso); db.flush()
    with pytest.raises(ValueError):
        guardar_precio(db, recurso.id, "CO", 100.0, "COP", organizacion_id=0)


def test_el_editor_de_presupuestos_sobrevive_a_un_fallo_de_precios(entorno, cliente_web, monkeypatch):
    """Regresión del 500 «current transaction is aborted» en /presupuestos/nuevo.

    Cuando la consulta de precios de mercado falla (en producción: la tabla
    nueva sin permisos para el rol `cotizat_app`), el editor debe seguir
    abriéndose con los precios base. Antes, el `except` que ocultaba el error
    dejaba la transacción abortada y la siguiente consulta de la página
    —`SELECT ... FROM plantillas`— tumbaba la petición entera.
    """
    from sqlalchemy.exc import ProgrammingError

    from app.services import precios_mercado

    def _falla(*_args, **_kwargs):
        raise ProgrammingError("SELECT 1", {}, Exception("permission denied"))

    monkeypatch.setattr(precios_mercado, "resolver_precio_para_presupuesto", _falla)

    respuesta = cliente_web.get("/presupuestos/nuevo")

    assert respuesta.status_code == 200
    # La página se pinta completa: las plantillas se consultan después de los
    # precios y son justo lo que fallaba.
    assert "Nuevo presupuesto" in respuesta.text or "presupuesto" in respuesta.text.lower()


def test_el_panel_de_mercado_no_muestra_precios_de_otras_empresas(entorno, cliente_web):
    """`PrecioRecursoMercado` no es TenantMixin: el filtro debe ser explícito."""
    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    otra = Organizacion(nombre="Empresa rival", slug="rival")
    db.add(otra); db.flush()
    recurso = Recurso(organizacion_id=ids[0], descripcion="Cemento gris", unidad="saco", precio=5, moneda="USD")
    db.add(recurso); db.flush()
    guardar_precio(db, recurso.id, "CO", 32000, "COP")  # referencia nacional
    guardar_precio(db, recurso.id, "CO", 41000, "COP", organizacion_id=ids[0])
    guardar_precio(db, recurso.id, "CO", 99999, "COP", organizacion_id=otra.id)
    db.commit()

    respuesta = cliente_web.get("/recursos/mercado")

    assert respuesta.status_code == 200
    assert "32000" in respuesta.text
    assert "41000" in respuesta.text
    assert "99999" not in respuesta.text


def test_solo_el_operador_edita_la_referencia_nacional(entorno, cliente_web):
    """Un cliente no puede cambiar el precio que ven todas las empresas."""
    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    recurso = Recurso(organizacion_id=ids[0], descripcion="Cabilla 3/8", unidad="ud", precio=3, moneda="USD")
    db.add(recurso); db.flush(); recurso_id = recurso.id
    db.commit()

    respuesta = cliente_web.post(
        "/recursos/mercado",
        data={"recurso_id": str(recurso_id), "pais_codigo": "CO", "precio": "1", "moneda": "COP", "organizacion": "0"},
        follow_redirects=False,
    )

    assert respuesta.status_code in (302, 303)
    assert "referencias nacionales" in respuesta.headers["location"].lower().replace("%20", " ")
    with Session() as verificacion:
        verificacion.info["organizacion_id"] = ids[0]
        assert resolver_precio(verificacion, recurso_id, "CO", ids[0]).origen == "base"


def test_actualizar_un_precio_registra_su_historico(entorno):
    """Regresión: guardar dos veces el mismo precio reventaba con TypeError.

    `guardar_precio` construía el histórico con `precio_mercado=<fila>` y el
    modelo solo tenía la clave foránea, así que **cualquier** actualización de
    un precio de mercado fallaba (formulario de recurso, panel e importador).
    """
    from app.models import HistorialPrecioRecurso

    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    recurso = Recurso(organizacion_id=ids[0], descripcion="Bloque 15", unidad="ud", precio=1, moneda="USD")
    db.add(recurso); db.flush()

    guardar_precio(db, recurso.id, "CO", 2500, "COP", organizacion_id=ids[0])
    db.flush()
    guardar_precio(db, recurso.id, "CO", 2900, "COP", organizacion_id=ids[0])
    db.commit()

    historial = db.query(HistorialPrecioRecurso).all()
    assert len(historial) == 1
    assert historial[0].precio_anterior == 2500
    assert historial[0].precio_nuevo == 2900
    assert historial[0].precio_mercado_id is not None
    assert resolver_precio(db, recurso.id, "CO", ids[0]).precio == 2900
