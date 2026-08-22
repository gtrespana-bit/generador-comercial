"""Buscar y añadir partidas tiene que funcionar desde el primer segundo.

Fallo reportado: al crear un presupuesto nuevo había alrededor de un minuto en
el que escribir en el buscador —o en el nombre de una partida— no encontraba
nada; pasado ese rato empezaba a funcionar. La causa es que el editor solo
miraba el índice del catálogo que se descarga de forma DIFERIDA
(``/presupuestos/editor/datos``, varios MB con miles de partidas): hasta que no
llegaba, no había nada donde buscar.

La corrección es que todas las búsquedas del editor consulten además
``/partidas/api/buscar``, que responde en milisegundos contra la base de datos.
Estas pruebas cubren el endpoint y el cableado del editor.
"""
from pathlib import Path

from app.models import Configuracion, Partida

RAIZ = Path(__file__).resolve().parents[1]
CATALOGO_JS = (RAIZ / "app/static/js/editor/catalogo.js").read_text(encoding="utf-8")
PARTIDA_JS = (RAIZ / "app/static/js/editor/partida.js").read_text(encoding="utf-8")
ARBOL_JS = (RAIZ / "app/static/js/editor/arbol_catalogo.js").read_text(encoding="utf-8")
MAIN_JS = (RAIZ / "app/static/js/editor/main.js").read_text(encoding="utf-8")


def test_la_busqueda_del_catalogo_responde_sin_el_indice_diferido(entorno, cliente_web):
    """El endpoint encuentra la partida aunque el editor no haya cargado nada."""
    Session, _ids, _rol = entorno
    with Session() as db:
        partida = db.query(Partida).first()
        partida.nombre = "Enchapado de pared con cerámica esmaltada"
        db.commit()

    datos = cliente_web.get("/partidas/api/buscar", params={"q": "enchapado"}).json()

    assert datos["ok"] is True
    assert any("Enchapado" in r["nombre"] for r in datos["resultados"])


def test_sin_texto_devuelve_sugerencias_inmediatas(entorno, cliente_web):
    """Al enfocar el buscador ya hay algo que insertar, sin esperar al índice."""
    Session, _ids, _rol = entorno

    datos = cliente_web.get("/partidas/api/buscar", params={"q": "", "limite": 5}).json()

    assert datos["ok"] is True
    assert datos["resultados"], "el buscador vacío debe sugerir lo más usado"
    assert len(datos["resultados"]) <= 5


def test_las_sugerencias_llegan_en_la_moneda_del_presupuesto(entorno, cliente_web):
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        cfg.moneda_default = "COP"
        cfg.tasa_cambio = 3128.65
        db.commit()

    datos = cliente_web.get(
        "/partidas/api/buscar", params={"q": "", "limite": 3, "moneda": "COP", "tasa": 3128.65}
    ).json()

    assert datos["moneda"] == "COP"
    assert all(r["moneda"] == "COP" for r in datos["resultados"])


def test_el_buscador_superior_consulta_al_servidor():
    """El panel del editor no puede depender solo del índice local."""
    assert "function ejecutarBusqueda" in CATALOGO_JS
    assert "buscarRemoto(filtro, 60)" in CATALOGO_JS
    # Rebote: se acompaña al tecleo sin lanzar una petición por letra.
    assert "setTimeout(function () { ejecutarBusqueda(valor); }, 140)" in CATALOGO_JS
    # Y con el campo vacío se piden sugerencias al servidor.
    assert "sugerenciasRemotas(15)" in CATALOGO_JS


def test_el_autocompletado_de_la_fila_consulta_al_servidor():
    assert "function buscarSugerenciasPartida" in PARTIDA_JS
    assert "catalogo.buscarRemoto(query, 25)" in PARTIDA_JS
    assert "programarSugerenciasPartida" in PARTIDA_JS


def test_al_elegir_una_sugerencia_se_carga_la_ficha_completa():
    """Un resultado de búsqueda es un índice ligero: falta su descomposición."""
    assert "catalogoApi.obtenerFicha(item)" in PARTIDA_JS
