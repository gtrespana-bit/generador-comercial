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


def test_precio_nacional_se_resuelve_por_codigo_estable_no_por_id_tenant(entorno):
    """Cada organización tiene su copia de Recurso y, por tanto, otro ID.

    La referencia nacional debe seguir al código del recurso; ligarla solo al
    ID hacía que funcionase únicamente para la organización usada al importar.
    """
    Session, ids, _ = entorno
    db = Session(); db.info["organizacion_id"] = ids[0]
    original = Recurso(
        organizacion_id=ids[0], codigo="MT-COMUN", descripcion="Cemento A",
        unidad="kg", precio=1, moneda="USD",
    )
    copia = Recurso(
        organizacion_id=ids[0], codigo="MT-COMUN", descripcion="Cemento B",
        unidad="kg", precio=2, moneda="USD",
    )
    db.add_all([original, copia]); db.flush()
    guardar_precio(db, original.id, "CO", 2500, "COP")
    db.flush()

    resuelto = resolver_precio(db, copia.id, "CO", ids[0])
    assert resuelto.origen == "nacional"
    assert resuelto.precio == 2500


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


def _matriz_csv(filas):
    import csv
    import io

    campos = [
        "codigo_recurso", "descripcion", "categoria", "unidad_fuente",
        "pais_codigo", "moneda", "precio_referencia", "precio_min",
        "precio_max", "fuente", "fecha_consulta", "confianza",
        "incluye_iva", "incluye_transporte", "origen", "observaciones",
    ]
    salida = io.StringIO(newline="")
    writer = csv.DictWriter(salida, fieldnames=campos, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(filas)
    return salida.getvalue()


def test_importador_conserva_toda_la_evidencia_del_precio(entorno, tmp_path):
    from datetime import date
    from app.models import PrecioRecursoMercado
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        recurso = Recurso(
            organizacion_id=ids[0], codigo="MT-AUDIT", descripcion="Material auditado",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        )
        db.add(recurso)
        db.commit()
        ruta = tmp_path / "matriz.csv"
        ruta.write_text(_matriz_csv([{
            "codigo_recurso": "MT-AUDIT", "descripcion": "Material auditado",
            "categoria": "materiales", "unidad_fuente": "kg", "pais_codigo": "CO",
            "moneda": "COP", "precio_referencia": "2500", "precio_min": "2200",
            "precio_max": "2900", "fuente": "Proveedor nacional", "fecha_consulta": "2026-08-20",
            "confianza": "referencia", "incluye_iva": "si",
            "incluye_transporte": "no", "origen": "nacional",
            "observaciones": "Bogotá, venta minorista",
        }]), encoding="utf-8")

        resultado = importar_matriz_csv(db, ruta, aplicar=True)
        assert resultado["errores"] == []
        assert resultado["creadas_o_actualizadas"] == 1
        precio = db.query(PrecioRecursoMercado).filter_by(
            recurso_id=recurso.id, pais_codigo="CO", organizacion_id=None
        ).one()
        assert precio.precio == 2500
        assert precio.codigo_recurso == "MT-AUDIT"
        assert precio.precio_min == 2200
        assert precio.precio_max == 2900
        assert precio.unidad_referencia == "kg"
        assert precio.fecha_consulta == date(2026, 8, 20)
        assert precio.incluye_iva == "si"
        assert precio.incluye_transporte == "no"
        assert precio.observaciones == "Bogotá, venta minorista"


def test_importador_no_escribe_parcialmente_si_un_rango_es_invalido(entorno, tmp_path):
    from app.models import PrecioRecursoMercado
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        recurso = Recurso(
            organizacion_id=ids[0], codigo="MT-ATOMIC", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        )
        db.add(recurso)
        db.commit()
        base = {
            "codigo_recurso": "MT-ATOMIC", "descripcion": "Material",
            "categoria": "materiales", "unidad_fuente": "kg", "pais_codigo": "CO",
            "moneda": "COP", "precio_referencia": "2500", "precio_min": "2200",
            "precio_max": "2900", "fuente": "Proveedor", "fecha_consulta": "2026-08-20",
            "confianza": "referencia", "incluye_iva": "si",
            "incluye_transporte": "no", "origen": "nacional", "observaciones": "",
        }
        invalida = {**base, "pais_codigo": "MX", "moneda": "MXN", "precio_min": "3000"}
        ruta = tmp_path / "matriz_invalida.csv"
        ruta.write_text(_matriz_csv([base, invalida]), encoding="utf-8")

        resultado = importar_matriz_csv(db, ruta, aplicar=True)
        assert resultado["errores"]
        assert resultado["creadas_o_actualizadas"] == 0
        assert db.query(PrecioRecursoMercado).filter_by(recurso_id=recurso.id).count() == 0
