from app.models import Organizacion, Recurso
from app.services.precios_mercado import guardar_precio, resolver_precio


def test_precio_organizacion_sobrescribe_nacional(db):
    org = Organizacion(nombre="Org", slug="org-precios")
    db.add(org); db.flush()
    recurso = Recurso(organizacion_id=org.id, descripcion="Cemento", unidad="saco", precio=5, moneda="USD")
    db.add(recurso); db.flush()
    guardar_precio(db, recurso.id, "CO", 32000, "COP")
    guardar_precio(db, recurso.id, "CO", 35000, "COP", organizacion_id=org.id)
    db.flush()
    assert resolver_precio(db, recurso.id, "CO", org.id).precio == 35000
    assert resolver_precio(db, recurso.id, "CO", org.id).origen == "organizacion"


def test_precio_nacional_no_afecta_otro_pais(db):
    org = Organizacion(nombre="Org2", slug="org-precios-2")
    db.add(org); db.flush()
    recurso = Recurso(organizacion_id=org.id, descripcion="Cemento", unidad="saco", precio=5, moneda="USD")
    db.add(recurso); db.flush()
    guardar_precio(db, recurso.id, "CO", 32000, "COP")
    db.flush()
    assert resolver_precio(db, recurso.id, "CO", org.id).precio == 32000
    assert resolver_precio(db, recurso.id, "PE", org.id).origen == "base"
