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
