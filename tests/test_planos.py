from app.services.planos import calcular_valor_real, detectar_espacios_plano, metricas_estancia


def test_calcular_valor_lineal_sin_escala():
    puntos = [[0,0],[100,0]]
    valor, unidad = calcular_valor_real("lineal", puntos, None)
    assert valor == 100
    assert unidad == "px"


def test_calcular_valor_lineal_con_escala():
    puntos = [[0,0],[200,0]]
    # 100 px = 1 m
    escala = 100.0
    valor, unidad = calcular_valor_real("lineal", puntos, escala)
    assert abs(valor - 2.0) < 0.01
    assert unidad == "m"


def test_calcular_area():
    puntos = [[0,0],[100,0],[100,100],[0,100]]
    escala = 100.0  # 100 px =1m => 100px=1m => area 1m2
    valor, unidad = calcular_valor_real("area", puntos, escala)
    assert abs(valor - 1.0) < 0.01
    assert unidad == "m2"


def test_calcular_conteo():
    puntos = [[0,0],[10,10],[20,20]]
    valor, unidad = calcular_valor_real("conteo", puntos, 100.0)
    assert valor == 3
    assert unidad == "ud"


def _png_planta_sintetica(con_huecos=True):
    import io
    from PIL import Image, ImageDraw

    imagen = Image.new("RGB", (800, 600), "white")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((40, 40, 760, 560), outline="black", width=8)
    dibujo.line((400, 40, 400, 560), fill="black", width=8)
    dibujo.line((40, 300, 760, 300), fill="black", width=8)
    if con_huecos:
        # Huecos de puerta que el detector debe puentear durante la segmentación.
        dibujo.rectangle((397, 115, 403, 165), fill="white")
        dibujo.rectangle((200, 297, 250, 303), fill="white")
    salida = io.BytesIO()
    imagen.save(salida, "PNG")
    return salida.getvalue()


def test_detector_local_encuentra_estancias_y_cierra_huecos_de_puerta():
    detecciones = detectar_espacios_plano(_png_planta_sintetica(), "image/png")
    assert len(detecciones) == 4
    assert all(d["tipo"] == "area" for d in detecciones)
    assert all(len(d["puntos"]) >= 3 for d in detecciones)
    assert all(d["confianza"] >= 0.7 for d in detecciones)
    assert [d["etiqueta"] for d in detecciones] == [
        "Estancia 1",
        "Estancia 2",
        "Estancia 3",
        "Estancia 4",
    ]


def _png_planta_con_cotas_numericas():
    """Misma planta de 4 recintos, pero con cotas y números sobre los muros."""
    import io
    from PIL import Image, ImageDraw

    imagen = Image.new("RGB", (800, 600), "white")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((40, 40, 760, 560), outline="black", width=8)
    dibujo.line((400, 40, 400, 560), fill="black", width=8)
    dibujo.line((40, 300, 760, 300), fill="black", width=8)
    dibujo.rectangle((397, 115, 403, 165), fill="white")
    dibujo.rectangle((200, 297, 250, 303), fill="white")
    # Números de cota pegados a los tabiques: el detector antiguo los
    # convertía en muros y partía las estancias.
    dibujo.text((160, 48), "3.50", fill="black")
    dibujo.text((520, 48), "4.20", fill="black")
    dibujo.text((48, 160), "2.80", fill="black")
    dibujo.text((410, 320), "1.20", fill="black")
    dibujo.line((80, 28, 380, 28), fill="black", width=1)
    dibujo.line((80, 22, 80, 34), fill="black", width=1)
    dibujo.line((380, 22, 380, 34), fill="black", width=1)
    salida = io.BytesIO()
    imagen.save(salida, "PNG")
    return salida.getvalue()


def _png_planta_con_muro_diagonal():
    import io
    from PIL import Image, ImageDraw

    imagen = Image.new("RGB", (800, 600), "white")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((60, 60, 740, 540), outline="black", width=8)
    dibujo.line((60, 60, 740, 540), fill="black", width=8)
    salida = io.BytesIO()
    imagen.save(salida, "PNG")
    return salida.getvalue()


def test_detector_ignora_cotas_y_numeros_sobre_muros():
    detecciones = detectar_espacios_plano(_png_planta_con_cotas_numericas(), "image/png")
    assert len(detecciones) == 4


def test_detector_conserva_angulo_de_muro_diagonal():
    import math

    detecciones = detectar_espacios_plano(_png_planta_con_muro_diagonal(), "image/png")
    assert len(detecciones) == 2

    def _tiene_diagonal(puntos):
        n = len(puntos)
        for i in range(n):
            a, b = puntos[i], puntos[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            if math.hypot(dx, dy) < 40:
                continue
            ang = abs(math.degrees(math.atan2(dy, dx))) % 180
            if 28 < ang < 62 or 118 < ang < 152:
                return True
        return False

    assert any(_tiene_diagonal(d["puntos"]) for d in detecciones)


def test_metricas_estancia_suelo_perimetro_y_paredes():
    puntos = [[0, 0], [400, 0], [400, 300], [0, 300]]
    met = metricas_estancia(puntos, 100.0, 2.5)
    assert met["suelo"] == 12.0
    assert met["suelo_unidad"] == "m2"
    assert met["perimetro"] == 14.0
    assert met["perimetro_unidad"] == "m"
    assert met["paredes"] == 35.0
    assert met["calibrado"] is True


# ------------------------------------------------------------------
# Visor global de planos (/planos) y enlace profundo ?plano=<id>
# ------------------------------------------------------------------
from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi import Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Cliente,
    Configuracion,
    Membresia,
    Organizacion,
    Presupuesto,
    Usuario,
)
from app.services.planos import calibrar_plano, crear_medicion, crear_plano  # noqa: E402
from app.storage import reset_storage_backend_cache  # noqa: E402

# PNG 1x1 RGBA válido.
PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def entorno_planos(monkeypatch, tmp_path):
    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    reset_storage_backend_cache()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as seed:
        org = Organizacion(nombre="Constructora Planos", slug="constructora-planos")
        usuario = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000030",
            email="planos@example.com",
            nombre="Medidora",
        )
        seed.add_all([org, usuario])
        seed.flush()
        seed.info["organizacion_id"] = org.id
        seed.info["rol_membresia"] = "propietario"
        cfg = Configuracion(empresa_nombre="Constructora Planos")
        cliente = Cliente(nombre="Cliente Plano")
        seed.add_all([cfg, cliente])
        seed.flush()
        presupuesto = Presupuesto(
            numero="P-2026-031",
            year=2026,
            fecha=date(2026, 8, 20),
            titulo="Local comercial",
            estado="borrador",
            client_id=cliente.id,
        )
        seed.add(presupuesto)
        seed.flush()
        plano_a = crear_plano(seed, presupuesto.id, "Planta baja", "planta.png", PNG_1x1)
        plano_b = crear_plano(seed, presupuesto.id, "Alzado norte", "alzado.png", PNG_1x1)
        # Dimensiones estables para exportaciones: 1000x1000 px, 100 px/m.
        plano_a.ancho_px = 1000
        plano_a.alto_px = 1000
        calibrar_plano(seed, plano_a, 300.0, 3.0, "m")
        crear_medicion(
            seed, plano_a, "lineal", "Muro cocina",
            [[0, 1000], [300, 1000]], color="#ff0000",
        )
        crear_medicion(
            seed, plano_a, "area", "Suelo salón",
            [[0, 1000], [300, 1000], [300, 700], [0, 700]], color="#00aa00",
        )
        crear_medicion(
            seed, plano_a, "conteo", "Enchufes",
            [[50, 950], [150, 950]], color="#0000ff",
        )
        seed.add(Membresia(usuario_id=usuario.id, organizacion_id=org.id, rol="propietario"))
        seed.commit()
        ids = (org.id, usuario.id, presupuesto.id, plano_a.id, plano_b.id)

    rol = {"valor": "propietario"}

    def _db(request: Request):
        db = Session()
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = rol["valor"]
        request.state.organizacion = db.get(Organizacion, ids[0])
        request.state.membresia = None
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    try:
        yield Session, ids
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_storage_backend_cache()
        engine.dispose()


def test_visor_global_lista_planos_agrupados_por_presupuesto(entorno_planos):
    """La galería /planos muestra todos los planos y enlaza al área de medición."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get("/planos")
    assert resp.status_code == 200
    assert "Visor de planos" in resp.text
    assert "P-2026-031" in resp.text
    assert "Planta baja" in resp.text
    assert "Alzado norte" in resp.text
    # Enlaces profundos a cada plano del grupo.
    assert f"/presupuestos/{ids[2]}/planos?plano={ids[3]}" in resp.text
    assert f"/presupuestos/{ids[2]}/planos?plano={ids[4]}" in resp.text
    # Miniaturas servidas por el endpoint privado de archivos.
    assert f"/planos/{ids[3]}/archivo" in resp.text


def test_area_de_medicion_preselecciona_plano_por_query(entorno_planos):
    """?plano=<id> abre directamente el plano enlazado desde el visor."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano={ids[4]}")
    assert resp.status_code == 200
    assert f"planoActivoId = {ids[4]};" in resp.text


def test_area_de_medicion_ignora_plano_inexistente(entorno_planos):
    """Un ?plano ajeno al presupuesto cae en el plano más reciente."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano=999999")
    assert resp.status_code == 200
    assert f"planoActivoId = {ids[4]};" in resp.text


def test_workspace_planos_es_compacto_y_solo_hace_zoom_con_lupas(entorno_planos):
    """El visor evita el zoom accidental de rueda y mantiene el plano a mano."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano={ids[3]}")
    assert resp.status_code == 200
    html = resp.text
    assert 'class="planos-layout"' in html
    assert 'data-inspector-tab="estancia"' in html
    assert 'data-inspector-tab="medir"' in html
    assert 'data-inspector-tab="resultados"' in html
    assert 'id="btn-zoom-in"' in html
    assert 'id="btn-zoom-out"' in html
    assert "Zoom únicamente con las lupas" in html
    assert "addEventListener('wheel'" not in html
    assert 'id="btn-fit-view"' not in html
    assert 'id="btn-reset-view"' not in html


def test_workspace_no_presenta_pixeles_como_medida_al_usuario(entorno_planos):
    """Píxeles quedan como dato técnico interno; la interfaz habla en m y m²."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos?plano={ids[3]}")
    assert resp.status_code == 200
    assert "Medidas reales en metros" in resp.text
    assert "metros cuadrados" in resp.text
    assert "px/m" not in resp.text

    galeria = client.get("/planos")
    assert galeria.status_code == 200
    assert "Escala real lista" in galeria.text
    assert "px/m" not in galeria.text


def test_subida_activa_analisis_y_detecciones_persisten_sin_duplicarse(entorno_planos):
    Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    subida = client.post(
        f"/presupuestos/{ids[2]}/planos/upload",
        data={"nombre": "Planta automática"},
        files={"archivo": ("planta-auto.png", _png_planta_sintetica(), "image/png")},
    )
    assert subida.status_code == 200
    datos_subida = subida.json()
    plano_id = datos_subida["plano_id"]
    assert datos_subida["deteccion_automatica"] is False
    assert datos_subida["requiere_calibracion"] is True
    assert datos_subida["url"].endswith(f"?plano={plano_id}")

    primera = client.post(f"/planos/{plano_id}/detectar")
    assert primera.status_code == 200
    assert primera.json()["nuevas"] == 4

    segunda = client.post(f"/planos/{plano_id}/detectar")
    assert segunda.status_code == 200
    assert segunda.json()["analizadas"] == 4
    assert segunda.json()["nuevas"] == 0
    assert segunda.json()["omitidas"] == 4

    # Una recarga obtiene exactamente las geometrías confirmadas en la base de datos.
    recarga = client.get(f"/planos/{plano_id}/datos").json()
    assert recarga["ok"] is True
    assert len(recarga["mediciones"]) == 4
    with Session() as db:
        from app.models import PlanoMedicion
        assert db.query(PlanoMedicion).filter(PlanoMedicion.plano_id == plano_id).count() == 4


def test_post_y_put_medicion_guardan_geometria_recalculada(entorno_planos):
    Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    creada = client.post(
        f"/planos/{ids[3]}/mediciones",
        json={"tipo": "lineal", "etiqueta": "Tramo editable", "puntos": [[0, 0], [100, 0]], "color": "#123456"},
    )
    assert creada.status_code == 200
    med_id = creada.json()["medicion"]["id"]
    assert creada.json()["medicion"]["valor"] == pytest.approx(1.0)

    actualizada = client.put(
        f"/planos/{ids[3]}/mediciones/{med_id}",
        json={"tipo": "lineal", "etiqueta": "Tramo corregido", "puntos": [[0, 0], [250, 0]], "color": "#654321"},
    )
    assert actualizada.status_code == 200
    assert actualizada.json()["medicion"]["valor"] == pytest.approx(2.5)
    assert actualizada.json()["medicion"]["puntos"] == [[0.0, 0.0], [250.0, 0.0]]

    with Session() as db:
        from app.models import PlanoMedicion
        med = db.get(PlanoMedicion, med_id)
        assert med.etiqueta == "Tramo corregido"
        assert med.color == "#654321"
        assert med.valor == pytest.approx(2.5)
        assert med.puntos() == [[0.0, 0.0], [250.0, 0.0]]


def test_medicion_incompleta_no_se_confirma_en_servidor(entorno_planos):
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.post(
        f"/planos/{ids[3]}/mediciones",
        json={"tipo": "area", "etiqueta": "Incompleta", "puntos": [[0, 0], [10, 0]]},
    )
    assert resp.status_code == 400
    assert "al menos 3" in resp.json()["error"]


# ------------------------------------------------------------------
# Exportaciones premium: CSV, DXF, renombrado y anexo PDF
# ------------------------------------------------------------------
def test_exportar_csv_mediciones_del_presupuesto(entorno_planos):
    """El CSV recoge todas las mediciones de todos los planos."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos/exportar?formato=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Planta baja" in resp.text
    assert "Muro cocina" in resp.text
    assert "Suelo salón" in resp.text
    assert "Enchufes" in resp.text
    assert "Lineal" in resp.text and "Área" in resp.text and "Conteo" in resp.text
    assert "3,00" in resp.text   # muro: 300 px a 100 px/m = 3 m
    assert "9,00" in resp.text   # área: 300x300 px = 9 m2


def test_exportar_dxf_con_mediciones_en_metros(entorno_planos):
    """DXF ASCII con entidades por tipo, Y invertida y metros reales."""
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/planos/{ids[3]}/exportar?formato=dxf")
    assert resp.status_code == 200
    assert "application/dxf" in resp.headers["content-type"]
    cuerpo = resp.text
    assert "ENTITIES" in cuerpo
    # Capas por tipo de medición + capa de etiquetas.
    assert "MED_LINEAL_M" in cuerpo
    assert "MED_AREA_M" in cuerpo
    assert "MED_CONTEO_M" in cuerpo
    assert "MED_ETIQUETAS" in cuerpo
    # Muro cocina: (0,1000)->(300,1000) px => (0,0)->(3,0) m con Y invertida.
    assert "10\n0.0000" in cuerpo
    assert "20\n0.0000" in cuerpo
    assert "11\n3.0000" in cuerpo
    # Lineal = 1 segmento; área cerrada de 4 vértices = 4 segmentos.
    assert cuerpo.count("\nLINE\n") == 5
    # El conteo dibuja círculos y las etiquetas van como TEXT.
    assert "\nCIRCLE\n" in cuerpo
    assert "\nTEXT\n" in cuerpo
    assert "Muro cocina" in cuerpo


def test_exportar_dxf_sin_mediciones_avisa(entorno_planos):
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/planos/{ids[4]}/exportar?formato=dxf")
    assert resp.status_code == 400
    assert "no tiene mediciones" in resp.json()["error"]


def test_renombrar_medicion_guardada(entorno_planos):
    Session, ids = entorno_planos
    with Session() as db:
        from app.models import PlanoMedicion
        med = db.query(PlanoMedicion).filter(PlanoMedicion.plano_id == ids[3]).first()
        med_id = med.id
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.post(
        f"/planos/{ids[3]}/mediciones/{med_id}/renombrar",
        json={"etiqueta": "Muro salón norte"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "etiqueta": "Muro salón norte"}


def test_datos_de_area_incluyen_metricas_de_estancia(entorno_planos):
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    recarga = client.get(f"/planos/{ids[3]}/datos").json()
    suelo = next(m for m in recarga["mediciones"] if m["tipo"] == "area")
    assert suelo["metricas"]["suelo"] == pytest.approx(9.0)
    assert suelo["metricas"]["perimetro"] == pytest.approx(12.0)
    assert suelo["metricas"]["paredes"] == pytest.approx(30.0)
    assert recarga["plano"]["altura_libre_m"] == pytest.approx(2.5)


def test_cambiar_altura_recalcula_paredes(entorno_planos):
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.post(f"/planos/{ids[3]}/altura", json={"altura_libre_m": 3.0})
    assert resp.status_code == 200
    suelo = next(m for m in resp.json()["mediciones"] if m["tipo"] == "area")
    assert suelo["metricas"]["paredes"] == pytest.approx(36.0)


def test_renombrar_medicion_rechaza_etiqueta_vacia(entorno_planos):
    _Session, ids = entorno_planos
    with _Session() as db:
        from app.models import PlanoMedicion
        med = db.query(PlanoMedicion).filter(PlanoMedicion.plano_id == ids[3]).first()
        med_id = med.id
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.post(
        f"/planos/{ids[3]}/mediciones/{med_id}/renombrar",
        json={"etiqueta": "   "},
    )
    assert resp.status_code == 400


def test_pdf_del_presupuesto_incluye_anexo_de_planos(monkeypatch):
    """Con «incluir anexos», el PDF final lleva el plano con sus mediciones."""
    import io
    import json as _json

    from PIL import Image
    from pypdf import PdfReader

    from app.models import (
        Capitulo,
        Cliente,
        Configuracion,
        PlanoMedicion,
        PlanoObra,
        Presupuesto,
        PresupuestoItem,
    )
    from app.services import pdf as pdf_service
    from app.services import pdf_planos

    buf = io.BytesIO()
    Image.new("RGB", (400, 300), (248, 250, 252)).save(buf, "PNG")
    almacen = {"storage://a/planta.png": buf.getvalue()}
    monkeypatch.setattr(pdf_planos, "read_reference", lambda ref: almacen[ref])

    plano = PlanoObra(
        nombre="Planta baja",
        archivo="storage://a/planta.png",
        content_type="image/png",
        ancho_px=400,
        alto_px=300,
        escala_px_por_metro=100.0,
    )
    plano.mediciones = [
        PlanoMedicion(
            tipo="lineal", etiqueta="Muro cocina", valor=3.0, unidad="m",
            puntos_json=_json.dumps([[0, 300], [300, 300]]), color="#ff0000",
        ),
    ]
    cliente = Cliente(nombre="Cliente de prueba", rif="J-12345678")
    presupuesto = Presupuesto(
        numero="P-2026-050",
        titulo="Reforma con planos",
        fecha=date(2026, 8, 22),
        moneda="USD",
        estado="borrador",
        impuesto_pct=16.0,
        cliente=cliente,
        incluir_anexos=True,
    )
    cap = Capitulo(nombre="ALBAÑILERÍA", orden=1)
    cap.partidas = [PresupuestoItem(nombre="Tabique", unidad="m2", cantidad=10.0, precio_unitario=40.0)]
    presupuesto.capitulos = [cap]
    presupuesto.planos = [plano]

    cfg = Configuracion(empresa_nombre="Constructora de prueba", pdf_color="#0F4C81")
    datos = pdf_service.generar_pdf(presupuesto, cfg).getvalue()
    texto = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(datos)).pages)
    assert "Plano: Planta baja" in texto
    assert "Muro cocina" in texto
    assert "Planos y mediciones" in texto  # citado en el índice de anexos


def test_detector_reutiliza_el_eje_central_de_tabiques_compartidos():
    """Dos recintos colindantes no dejan un hueco equivalente al espesor del muro."""
    detecciones = detectar_espacios_plano(_png_planta_sintetica())
    assert len(detecciones) == 4
    izquierda = [d for d in detecciones if d["bbox"][2] < 500]
    derecha = [d for d in detecciones if d["bbox"][0] >= 390]
    assert izquierda and derecha
    assert {round(d["bbox"][2], 2) for d in izquierda} == {round(d["bbox"][0], 2) for d in derecha}
    arriba = [d for d in detecciones if d["bbox"][3] < 400]
    abajo = [d for d in detecciones if d["bbox"][1] >= 250]
    assert {round(d["bbox"][3], 2) for d in arriba} == {round(d["bbox"][1], 2) for d in abajo}


def test_selector_de_presupuesto_expone_perimetro_suelo_y_paredes(entorno_planos):
    _Session, ids = entorno_planos
    client = TestClient(app, base_url="https://cotizat.test")
    resp = client.get(f"/presupuestos/{ids[2]}/planos/mediciones-selector")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    planta = next(p for p in data["planos"] if p["id"] == ids[3])
    estancia = next(m for m in planta["mediciones"] if m["tipo"] == "area")
    opciones = {op["clave"]: op for op in estancia["opciones"]}
    assert opciones["perimetro"]["unidad"] == "m"
    assert opciones["perimetro"]["cantidad"] == pytest.approx(12.0)
    assert opciones["suelo"]["unidad"] == "m2"
    assert opciones["suelo"]["cantidad"] == pytest.approx(9.0)
    assert opciones["paredes"]["cantidad"] == pytest.approx(30.0)
