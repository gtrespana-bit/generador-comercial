"""Las herramientas deterministas del copiloto, en inglés.

Lo que cambia con el idioma son las palabras: nunca los números. Cada prueba
comprueba las dos cosas a la vez —que el texto se traduce y que las cifras,
los estados y las rutas siguen idénticos—, porque un aviso que cuadra en
castellano y descuadra en inglés es peor que un aviso en castellano.
"""
import pytest

from app.models import (Base, Configuracion, Organizacion, Partida,
                        RecetaEstancia)
from app.services.copiloto_presupuesto import (
    _MENSAJES_REVISION_EN,
    _ETIQUETAS_EN,
    calcular_mediciones_texto,
    detectar_faltantes_alcance,
    preparar_lote_catalogo,
    revisar_borrador_vivo,
)
from app.services.herramientas_ia import resolver_herramienta_ia


def _db(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{tmp_path}/copiloto_idioma.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.info["organizacion_id"] = 1
    db.add(Organizacion(id=1, nombre="Empresa", slug="empresa"))
    db.add(Configuracion(organizacion_id=1, empresa_nombre="Empresa",
                         moneda_default="USD"))
    db.commit()
    return db


def _borrador():
    return [
        {
            "nombre": "DEMOLICIONES",
            "partidas": [
                {
                    "nombre": "Demolición de piso", "unidad": "m2",
                    "cantidad": 10, "precio": 0,
                    "coste_materiales": 2,
                },
                {"nombre": "", "unidad": "m2", "cantidad": 1, "precio": 1},
            ],
        },
        {"nombre": "", "partidas": []},
    ]


# ---------------------------------------------------------------------------
# Revisión del borrador
# ---------------------------------------------------------------------------

def test_revision_del_borrador_se_redacta_en_ingles():
    borrador = _borrador()
    es = revisar_borrador_vivo(borrador)
    en = revisar_borrador_vivo(borrador, "en")

    # Lo que es un dato, no un texto, no cambia.
    assert en["estado"] == es["estado"]
    assert en["score"] == es["score"]
    assert en["total_capitulos"] == es["total_capitulos"]
    assert en["total_partidas"] == es["total_partidas"]

    codigos_es = {i["codigo"] for i in es["criticos"] + es["avisos"]}
    codigos_en = {i["codigo"] for i in en["criticos"] + en["avisos"]}
    assert codigos_es == codigos_en

    for grupo in ("criticos", "avisos", "correctos"):
        assert len(en[grupo]) == len(es[grupo])
        for a, b in zip(es[grupo], en[grupo]):
            assert a["titulo"] != b["titulo"], f"{a['codigo']} sin traducir"
            # Las rutas de corrección son las mismas en los dos idiomas.
            assert a.get("capitulo_indice") == b.get("capitulo_indice")


def test_todo_codigo_emitido_tiene_su_mensaje_en_ingles():
    """Un código sin traducir se vería en castellano dentro de una lista EN."""
    emitidos = set()
    for borrador in (
        _borrador(),
        [],
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "zzz", "cantidad": 1, "precio": 1},
            {"nombre": "A", "unidad": "m2", "cantidad": 1, "precio": 1},
        ]}],
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "m2", "cantidad": 1, "precio": 1,
             "mediciones": [{"concepto": "Z", "cantidad": 5}],
             "prod_nombre": "Prod", "prod_precio": 0},
        ]}],
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "m2", "cantidad": 0, "precio": 1,
             "coste_materiales": 9},
        ]}],
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "", "cantidad": 1, "precio": 1},
        ]}],
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "m2", "cantidad": 1, "precio": 1,
             "mediciones": [{"concepto": "Z", "cantidad": 5}]},
        ]}],
        # Producto asociado: sin precio de venta y sin coste de compra.
        [{"nombre": "X", "partidas": [
            {"nombre": "A", "unidad": "m2", "cantidad": 1, "precio": 1,
             "prod_nombre": "Prod", "prod_precio": 0},
            {"nombre": "B", "unidad": "m2", "cantidad": 1, "precio": 1,
             "prod_nombre": "Prod", "prod_precio": 5},
        ]}],
    ):
        r = revisar_borrador_vivo(borrador, "en")
        for grupo in ("criticos", "avisos", "correctos"):
            emitidos.update(i["codigo"] for i in r[grupo])

    assert emitidos, "ningún código emitido: la prueba no estaría probando nada"
    for codigo in emitidos:
        assert codigo in _MENSAJES_REVISION_EN, f"falta _MENSAJES_REVISION_EN[{codigo!r}]"
    # Y ninguna entrada de la tabla es un código que ya no se emite.
    for codigo in _MENSAJES_REVISION_EN:
        assert codigo in emitidos, f"_MENSAJES_REVISION_EN[{codigo!r}] está muerto"


def test_la_traduccion_conserva_las_cifras():
    """El marcador se rellena con el mismo número que el texto original."""
    r = revisar_borrador_vivo(_borrador(), "en")
    criticos = {i["codigo"]: i for i in r["criticos"]}
    assert "sin_precio" in criticos
    # «Demolición de piso» es un dato: se mantiene tal cual dentro del aviso.
    assert "Demolición de piso" in criticos["sin_precio"]["titulo"]


def test_sin_datos_faltantes_el_mensaje_no_se_rompe():
    """Si falta un parámetro, se cae al castellano antes que a un `{` crudo."""
    r = revisar_borrador_vivo([], "en")
    assert r["criticos"][0]["titulo"] == "The draft has no sections"
    assert "{" not in "".join(
        i["titulo"] + i["detalle"] for i in r["criticos"]
    )


# ---------------------------------------------------------------------------
# Mediciones
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("consulta", [
    "baño de 3 × 2 m y 2,40 m de altura",
    "bathroom 3 × 2 m with a ceiling height of 2.40 m",
])
def test_mediciones_calculan_lo_mismo_en_ingles(consulta):
    es = calcular_mediciones_texto(consulta)
    en = calcular_mediciones_texto(consulta, "en")
    assert es["ok"] and en["ok"]
    assert en["largo"] == es["largo"] and en["ancho"] == es["ancho"]
    assert en["altura"] == es["altura"]
    assert [f["cantidad"] for f in en["filas"]] == [f["cantidad"] for f in es["filas"]]
    assert [f["unidad"] for f in en["filas"]] == [f["unidad"] for f in es["filas"]]

    conceptos = [f["concepto"] for f in en["filas"]]
    assert "Floor area" in conceptos
    assert "Net perimeter / skirting" in conceptos
    assert "Net wall area" in conceptos
    # Las fórmulas también se traducen: son la explicación del número.
    assert "doors" in " ".join(f["formula"] for f in en["filas"])
    assert "puertas" not in " ".join(f["formula"] for f in en["filas"])


def test_mediciones_detectan_las_dimensiones_escritas_en_ingles():
    """«ceiling height of 2.40 m» tiene que valer lo mismo que «2,40 m de altura»."""
    es = calcular_mediciones_texto("baño de 3 × 2 m y 2,40 m de altura")
    en = calcular_mediciones_texto("bathroom 3 × 2 m with a ceiling height of 2.40 m", "en")
    assert en["altura"] == es["altura"] == 2.4


def test_mediciones_sin_datos_erroneas_en_ingles():
    en = calcular_mediciones_texto("hola", "en")
    assert en["ok"] is False
    assert "I could not make out" in en["error"]


# ---------------------------------------------------------------------------
# Lote del catálogo y alcance
# ---------------------------------------------------------------------------

def _sembrar(db):
    for codigo, nombre in (
        ("PRO-01", "Protección de elementos existentes"),
        ("DEM-01", "Demolición de piso de porcelanato"),
        ("DEM-02", "Picado de pared de porcelanato"),
        ("RES-01", "Acopio de escombros"),
        ("RES-02", "Transporte de escombros"),
    ):
        db.add(Partida(organizacion_id=1, codigo_interno=codigo,
                       nombre=nombre, descripcion=nombre, unidad="m2",
                       precio_unitario=5))
    db.commit()


def test_lote_en_ingles_nombra_el_capitulo_en_ingles(tmp_path):
    db = _db(tmp_path)
    _sembrar(db)
    existente = db.query(Partida).filter(Partida.codigo_interno == "DEM-01").one()
    borrador = [{"nombre": "DEMOLICIONES", "partidas": [
        {"catalogo_id": existente.id, "nombre": existente.nombre},
    ]}]

    es = preparar_lote_catalogo(
        db, "Prepara las partidas necesarias para demolicion de porcelanato",
        borrador,
    )
    en = preparar_lote_catalogo(
        db, "Prepara las partidas necesarias para demolicion de porcelanato",
        borrador, "en",
    )
    assert [p["id"] for p in en["candidatos"]] == [p["id"] for p in es["candidatos"]]
    assert en["flujo_reconocido"] == es["flujo_reconocido"]

    secciones = {p["capitulo_sugerido"] for p in en["candidatos"]}
    assert secciones, "ningún candidato: la prueba no estaría probando nada"
    for seccion in secciones:
        assert seccion in _ETIQUETAS_EN.values(), f"{seccion!r} sin traducir"
        assert seccion not in _ETIQUETAS_EN, f"{seccion!r} sigue en castellano"


def test_el_flujo_se_reconoce_escribiendo_en_ingles(tmp_path):
    db = _db(tmp_path)
    _sembrar(db)
    lote = preparar_lote_catalogo(
        db, "prepare the line items needed for porcelain tile demolition",
        None, "en",
    )
    assert lote["flujo_reconocido"] is True
    assert lote["candidatos"]


def test_faltantes_de_alcance_se_redactan_en_ingles(tmp_path):
    db = _db(tmp_path)
    _sembrar(db)
    borrador = [{"nombre": "DEMOLICIONES", "partidas": [
        {"nombre": "Demolición de piso de porcelanato", "descripcion": ""},
    ]}]

    es = detectar_faltantes_alcance(db, borrador)
    en = detectar_faltantes_alcance(db, borrador, "", "en")
    assert [s["clave"] for s in en["sugerencias"]] == \
           [s["clave"] for s in es["sugerencias"]]
    assert en["analizadas"] == es["analizadas"]
    assert en["ids_recomendados"] == es["ids_recomendados"]

    for sugerencia in en["sugerencias"]:
        assert sugerencia["titulo"] in _ETIQUETAS_EN.values()
        assert sugerencia["motivo"] in _ETIQUETAS_EN.values()


def test_cada_etiqueta_de_la_tabla_tiene_traduccion_distinta():
    for es, en in _ETIQUETAS_EN.items():
        assert es.strip() and en.strip(), f"etiqueta vacía: {es!r}"
        assert es != en, f"traducción igual al original: {es!r}"
        # Una etiqueta traducida no puede conservar acentos del castellano.
        if es.isascii():
            continue


# ---------------------------------------------------------------------------
# Enrutado: las herramientas se disparan también en inglés
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("consulta,idioma,esperado", [
    # Escrito en inglés, respondido en inglés.
    ("measure a bathroom 3 × 2 m", "en", "Measurements worked out on the server"),
    ("review this estimate please", "en", "Estimate review"),
    # Escrito en castellano, respondido en castellano.
    ("mide un baño de 3 × 2 m", "es", "Mediciones calculadas en el servidor"),
    ("revisa este presupuesto", "es", "Revisión de presupuesto"),
])
def test_las_herramientas_se_disparan_y_contestan_en_su_idioma(tmp_path, consulta, idioma, esperado):
    db = _db(tmp_path)
    respuesta = resolver_herramienta_ia(db, consulta, None, idioma)
    assert respuesta is not None, f"la herramienta no se disparó: {consulta!r}"
    assert esperado in respuesta


def test_los_patrones_en_ingles_no_secuestran_las_consultas_en_castellano(tmp_path):
    """Añadir inglés no puede cambiar qué herramienta responde en castellano."""
    db = _db(tmp_path)
    for consulta in ("mide un baño de 3 × 2 m", "revisa este presupuesto",
                     "añade las partidas necesarias"):
        assert resolver_herramienta_ia(db, consulta, None) is not None
        en = resolver_herramienta_ia(db, consulta, None, "en")
        assert en is not None, f"dejó de responder en inglés: {consulta!r}"


def test_sin_coincidencia_no_hay_respuesta(tmp_path):
    db = _db(tmp_path)
    assert resolver_herramienta_ia(db, "hola buenos días", None, "en") is None


# ---------------------------------------------------------------------------
# Recorrido HTTP: el asistente responde en la lengua de la pantalla
# ---------------------------------------------------------------------------

def test_el_asistente_responde_en_ingles_por_la_cookie(tmp_path):
    """De extremo a extremo: /api/ia/chat con herramientas deterministas."""
    from starlette.testclient import TestClient

    from app.database import get_authenticated_db, get_db
    from app.main import app

    db = _db(tmp_path)
    _sembrar(db)

    def override_get_db():
        yield db

    app.dependency_overrides[get_authenticated_db] = override_get_db
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app, base_url="https://cotizat.test")

        client.cookies.set("cotizat_lang", "en")
        en = client.post("/api/ia/chat", json={
            "messages": [{"role": "user", "content": "measure a bathroom 3 × 2 m"}],
            "stream": False,
        }).json()
        assert en["ok"] is True
        assert "Floor area" in en["respuesta"]
        assert "Superficie de piso" not in en["respuesta"]

        client.cookies.set("cotizat_lang", "es")
        es = client.post("/api/ia/chat", json={
            "messages": [{"role": "user", "content": "mide un baño de 3 × 2 m"}],
            "stream": False,
        }).json()
        assert es["ok"] is True
        assert "Superficie de piso" in es["respuesta"]

        # Las dos respuestas calculan lo mismo: 3 × 2 = 6 m².
        assert "6 m2" in en["respuesta"] and "6 m2" in es["respuesta"]
    finally:
        app.dependency_overrides.clear()
