from types import SimpleNamespace

from app.services.garantias import clasificar_familias, familias_para_pdf


def _presupuesto(*capitulos):
    caps = []
    for nombre, partidas in capitulos:
        items = [
            SimpleNamespace(nombre=n, descripcion=d, producto_nombre="")
            for n, d in partidas
        ]
        caps.append(SimpleNamespace(nombre=nombre, partidas=items))
    return SimpleNamespace(capitulos=caps)


def test_rusticana_agrupa_por_familia_no_por_partida():
    p = _presupuesto(
        ("DEMOLICIÓN Y PREPARACIÓN", [
            ("Picado de piso existente", "Retiro de cerámica y escombros"),
        ]),
        ("PISOS Y REVESTIMIENTOS", [
            ("Solado de porcelanato 60x120", "Incluye adhesivo y junta"),
            ("Zócalo de porcelanato", ""),
        ]),
        ("CARPINTERÍA", [
            ("Closet lacado a medida", "MDF lacado"),
        ]),
        ("FONTANERÍA", [
            ("Puntos de agua y desagüe", "Tubería PPR"),
        ]),
        ("ELECTRICIDAD", [
            ("Puntos de luz e interruptores", "Circuito nuevo"),
        ]),
        ("PINTURA", [
            ("Pintura premium sobre pañete", "Dos manos"),
        ]),
        ("ESTRUCTURAS", [
            ("Tabique de block", "Muro divisorio"),
        ]),
        ("TECHOS", [
            ("Cielo raso de drywall", ""),
        ]),
    )
    familias = clasificar_familias(p)
    claves = [f["clave"] for f in familias]
    assert "pisos" in claves
    assert "carpinteria_madera" in claves
    assert "fontaneria" in claves
    assert "electricidad" in claves
    assert "pintura" in claves
    assert "estructuras" in claves
    assert "yeso" in claves
    assert "demolicion" not in claves
    assert claves.count("pisos") == 1
    plazos = {f["clave"]: f["plazo"] for f in familias}
    assert plazos["pisos"] == "5 años"
    assert plazos["fontaneria"] == "5 años"
    assert plazos["electricidad"] == "5 años"
    assert plazos["estructuras"] == "5 años"
    assert plazos["yeso"] == "3 años"
    assert plazos["pintura"] == "2 años"
    assert "fabricante" in next(f["alcance"] for f in familias if f["clave"] == "fontaneria")
    assert "fabricante" in next(f["alcance"] for f in familias if f["clave"] == "electricidad")


def test_solo_demolicion_no_genera_tabla_de_demolicion():
    p = _presupuesto(
        ("DEMOLICIÓN", [("Picado de piso y retiro de escombros", "")]),
    )
    assert clasificar_familias(p) == []
    assert familias_para_pdf(p)[0]["clave"] == "general"


def test_sin_coincidencias_usa_tabla_minima():
    p = _presupuesto(("GENERAL", [("Partida X", "")]))
    filas = familias_para_pdf(p)
    assert len(filas) == 1
    assert filas[0]["plazo"] == "2 años"


def test_presupuesto_model_garantias_properties():
    from app.models import Presupuesto, Capitulo, PresupuestoItem
    from app.services.garantias import NOTA_LEGAL

    p = Presupuesto(numero="P-TEST-001", year=2026, mostrar_garantias=True)
    c = Capitulo(nombre="FONTANERÍA Y GRIFERÍA", orden=1)
    it = PresupuestoItem(nombre="Punto de agua", descripcion="Instalación de tubería")
    c.partidas.append(it)
    p.capitulos.append(c)

    fams = p.garantias_familias
    assert len(fams) >= 1
    assert fams[0]["clave"] == "fontaneria"
    assert p.garantias_nota_legal == NOTA_LEGAL


def test_detail_html_muestra_tabla_garantias_cuando_esta_activado():
    import uuid
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db, init_db
    from app.models import Presupuesto, Cliente, Capitulo, PresupuestoItem

    init_db()
    client = TestClient(app)
    db = next(get_db())
    cli = db.query(Cliente).first()
    if not cli:
        cli = Cliente(nombre="Cliente Test", telefono="123456")
        db.add(cli)
        db.commit()

    num = f"P-GAR-{uuid.uuid4().hex[:6].upper()}"
    p = Presupuesto(
        numero=num,
        year=2026,
        client_id=cli.id,
        mostrar_garantias=True,
        titulo="Obra con garantías",
    )
    cap = Capitulo(nombre="ALBAÑILERÍA Y PISOS", orden=1)
    it = PresupuestoItem(nombre="Solado de porcelanato", precio_unitario=50.0, cantidad=10.0)
    cap.partidas.append(it)
    p.capitulos.append(cap)
    db.add(p)
    db.commit()

    resp = client.get(f"/presupuestos/{p.id}")
    assert resp.status_code == 200
    assert "Garantías de la obra" in resp.text
    assert "descargarPDF" in resp.text
    assert "imprimirPDF" in resp.text

    pdf_resp = client.get(f"/presupuestos/{p.id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000


def test_activar_garantias_en_configuracion_actualiza_presupuestos_existentes():
    import uuid
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db, init_db
    from app.models import Presupuesto, Cliente, Configuracion

    init_db()
    client = TestClient(app)
    db = next(get_db())

    cli = db.query(Cliente).first()
    if not cli:
        cli = Cliente(nombre="Cliente Test 2", telefono="999999")
        db.add(cli)
        db.commit()

    num = f"P-CFG-{uuid.uuid4().hex[:6].upper()}"
    p = Presupuesto(
        numero=num,
        year=2026,
        client_id=cli.id,
        mostrar_garantias=False,
    )
    db.add(p)
    db.commit()

    # Guardar configuracion activando mostrar_garantias_default
    resp = client.post("/configuracion", data={
        "empresa_nombre": "Mi Empresa Test",
        "mostrar_garantias_default": "1",
        "iva_default": "16",
        "validez_default": "30",
        "moneda_default": "USD",
    }, follow_redirects=True)
    assert resp.status_code == 200

    db.refresh(p)
    assert p.mostrar_garantias is True

    # El presupuesto ahora muestra garantías en su vista detallada
    resp_detail = client.get(f"/presupuestos/{p.id}")
    assert resp_detail.status_code == 200
    assert "Garantías de la obra" in resp_detail.text

