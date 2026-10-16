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


def test_presupuesto_agrupa_por_familia_no_por_partida():
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



def _presupuesto_en(*capitulos):
    """Presupuesto redactado en inglés (rutas /en/ y presupuestos bilingües)."""
    return _presupuesto(*capitulos)


def test_todas_las_familias_tienen_traduccion():
    """Ninguna familia se queda en castellano por olvido en la tabla EN."""
    from app.services.garantias import FAMILIAS_EN, FAMILIAS_GARANTIA

    for fam in FAMILIAS_GARANTIA:
        ext = FAMILIAS_EN.get(fam["clave"])
        assert ext, f"falta FAMILIAS_EN[{fam['clave']}]"
        for campo in ("grupo", "plazo", "alcance"):
            assert ext.get(campo), f"{fam['clave']}.{campo} sin traducir"
            assert ext[campo] != fam[campo], f"{fam['clave']}.{campo} repetido"
    assert FAMILIAS_EN.get("general"), "falta la familia general en inglés"


def test_plazos_identicos_en_ambos_idiomas():
    """El plazo no cambia con el idioma: es el compromiso contractual."""
    from app.services.garantias import FAMILIAS_EN, FAMILIAS_GARANTIA

    for fam in FAMILIAS_GARANTIA:
        en = FAMILIAS_EN[fam["plazo"] and fam["clave"]]["plazo"]
        assert en == fam["plazo"].replace("años", "years").replace("año", "year"), (
            f"{fam['clave']}: {fam['plazo']} != {en}"
        )
    assert FAMILIAS_EN["general"]["plazo"] == "2 years"


def test_detecta_familias_en_presupuesto_en_ingles():
    p = _presupuesto_en(
        ("01 · Demolition and strip-out", [
            ("Hacking off wall tiling and its setting bed", "Removal of debris"),
        ]),
        ("02 · Plumbing", [("Waste pipework and tap replacement", "PPR pipework")]),
        ("03 · Electrical", [("New consumer unit and downlights", "")]),
        ("04 · Painting", [("Emulsion paint, two coats", "")]),
        ("05 · Drywall", [("Plasterboard on stud partition", "")]),
    )
    claves = [f["clave"] for f in clasificar_familias(p, "en")]
    # La demolición y el retiro de escombros nunca se garantizan.
    assert "impermeabilizacion" not in claves
    assert "fontaneria" in claves and "electricidad" in claves
    assert "pintura" in claves and "yeso" in claves
    for f in clasificar_familias(p, "en"):
        assert "año" not in f["plazo"], f"{f['clave']} sin traducir: {f['plazo']}"
        assert f["grupo"] != "Estructuras, tabiques y albañilería"


def test_mismas_familias_que_en_castellano_para_obra_equivalente():
    """El idioma no cambia qué se garantiza, solo cómo se escribe."""
    es = _presupuesto(
        ("PISOS", [("Solado de porcelanato", "Adhesivo y junta")]),
        ("FONTANERÍA", [("Puntos de agua y desagüe", "Tubería")]),
    )
    en = _presupuesto_en(
        ("FLOORING", [("Porcelain tile flooring", "Adhesive and grout")]),
        ("PLUMBING", [("Water outlets and wastes", "Pipework")]),
    )
    claves_es = [f["clave"] for f in clasificar_familias(es)]
    claves_en = [f["clave"] for f in clasificar_familias(en, "en")]
    assert claves_es and claves_es == claves_en


def test_demolicion_en_ingles_tampoco_genera_tabla():
    p = _presupuesto_en(("DEMOLITION", [("Hacking off floors and debris removal", "")]))
    assert clasificar_familias(p, "en") == []
    filas = familias_para_pdf(p, "en")
    assert filas[0]["clave"] == "general"
    assert filas[0]["grupo"] == "Remodelling work included"


def test_nota_legal_y_tabla_minima_en_ingles():
    from app.services.garantias import NOTA_LEGAL, NOTA_LEGAL_EN, nota_legal

    assert nota_legal() == NOTA_LEGAL
    assert nota_legal("es") == NOTA_LEGAL
    assert nota_legal("en") == NOTA_LEGAL_EN
    assert nota_legal("en-mx") == NOTA_LEGAL_EN
    assert NOTA_LEGAL_EN != NOTA_LEGAL
    vacio = familias_para_pdf(_presupuesto_en(("GENERAL", [("Item X", "")])), "en")
    assert vacio[0]["plazo"] == "2 years"


def test_castellano_no_cambia_al_añadir_ingles():
    """Las rutas en castellano siguen recibiendo exactamente lo de antes."""
    p = _presupuesto(
        ("PISOS", [("Solado de porcelanato", "")]),
        ("CARPINTERÍA", [("Closet lacado a medida", "")]),
    )
    claves = [f["clave"] for f in clasificar_familias(p)]
    assert claves == ["pisos", "carpinteria_madera"]
    assert claves == [f["clave"] for f in clasificar_familias(p, "es")]
    # Un presupuesto en castellano se lee igual en modo bilingüe.
    assert claves == [f["clave"] for f in clasificar_familias(p, "en")]


def test_modelo_expone_variante_inglesa():
    from app.models import Presupuesto, Capitulo, PresupuestoItem
    from app.services.garantias import NOTA_LEGAL_EN

    p = Presupuesto(numero="P-TEST-002", year=2026, mostrar_garantias=True)
    c = Capitulo(nombre="FONTANERÍA Y GRIFERÍA", orden=1)
    c.partidas.append(PresupuestoItem(
        nombre="Punto de agua", descripcion="Instalación de tubería",
    ))
    p.capitulos.append(c)

    assert [f["clave"] for f in p.garantias_familias_en] == ["fontaneria"]
    assert p.garantias_familias_en[0]["plazo"] == "5 years"
    assert p.garantias_nota_legal_en == NOTA_LEGAL_EN
    # La versión en castellano sigue disponible para el PDF en castellano.
    assert [f["clave"] for f in p.garantias_familias] == ["fontaneria"]
    assert p.garantias_familias[0]["plazo"] == "5 años"

    # Un presupuesto redactado en inglés solo se clasifica en modo inglés:
    # por eso la variante en inglés se guarda aparte en la instantánea.
    c.nombre = "PLUMBING AND SANITARY"
    c.partidas[0].nombre = "Pipework and water outlets"
    c.partidas[0].descripcion = "Waste installation"
    assert [f["clave"] for f in p.garantias_familias] == ["general"]
    assert [f["clave"] for f in p.garantias_familias_en] == ["fontaneria"]


def test_version_guarda_las_dos_variantes():
    from app.services.versions import serializar_presupuesto
    from app.models import Presupuesto, Capitulo, PresupuestoItem, Cliente

    p = Presupuesto(numero="P-TEST-003", year=2026, mostrar_garantias=True,
                    titulo="T", moneda="USD")
    c = Capitulo(nombre="PISOS", orden=1)
    c.partidas.append(PresupuestoItem(
        nombre="Solado de porcelanato", descripcion="",
        cantidad=1.0, precio_unitario=10.0,
    ))
    p.capitulos.append(c)
    p.cliente = Cliente(nombre="ACME", rif="J-1")

    snap = serializar_presupuesto(p)
    assert snap["garantias_familias"] == p.garantias_familias
    assert snap["garantias_familias_en"] == p.garantias_familias_en
    assert "años" not in snap["garantias_familias_en"][0]["plazo"]
    assert snap["garantias_nota_legal_en"].startswith("The warranty covers")
    # Sin garantías activadas no se guarda nada.
    p.mostrar_garantias = False
    snap2 = serializar_presupuesto(p)
    assert snap2["garantias_familias_en"] == [] and snap2["garantias_nota_legal_en"] == ""


def test_pdf_en_ingles_incluye_la_tabla_de_garantias_traducida():
    """El PDF que se envía desde /en/ no puede llevar la tabla en castellano."""
    import io
    from datetime import date

    from pypdf import PdfReader

    from app.models import (Capitulo, Cliente, Configuracion, Presupuesto,
                            PresupuestoItem)
    from app.services.pdf import generar_pdf

    cfg = Configuracion(empresa_nombre="ACME")
    p = Presupuesto(numero="P-EN-001", year=2026, moneda="USD",
                    fecha=date(2026, 10, 16), validez_dias=30,
                    impuesto_pct=0.0, descuento_pct=0.0, tipo_cambio=1.0,
                    mostrar_garantias=True, titulo="Bathroom refurbishment")
    p.cliente = Cliente(nombre="John Doe", rif="J-1")
    c = Capitulo(nombre="PLUMBING AND SANITARY", orden=1)
    c.partidas.append(PresupuestoItem(
        nombre="Pipework and water outlets", descripcion="Waste installation",
        cantidad=2.0, precio_unitario=100.0, unidad="ud",
    ))
    p.capitulos.append(c)

    datos = generar_pdf(p, cfg, lang="en").getvalue()
    texto = "\n".join(
        (pag.extract_text() or "") for pag in PdfReader(io.BytesIO(datos)).pages
    )
    assert "PROJECT WARRANTIES" in texto
    assert "PLUMBING AND SANITARY INSTALLATIONS" in texto.upper()
    assert "5 years" in texto
    assert "The warranty covers defects in the execution" in texto
    assert "GARANT" not in texto.upper().replace("WARRANT", "")
    assert "años" not in texto
