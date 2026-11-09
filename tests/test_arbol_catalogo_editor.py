"""La barra lateral del catálogo tiene que servir para mirar, no solo para buscar.

Fallo reportado: en el editor de presupuesto la barra decía «3006 partidas» y no
mostraba ninguna. El árbol se construye con el esqueleto que sirve el servidor
(capítulos, subcapítulos y apartados con su recuento, sin las ~3.000 hojas: se
piden al abrir cada apartado). Al filtrar sin texto de búsqueda se contaban las
hojas **ya cargadas**, que son cero, así que los dieciocho capítulos quedaban
ocultos y solo quedaba el buscador.

Estas pruebas atan las dos mitades del contrato: el esqueleto declara totales
que la interfaz puede enseñar, y la interfaz los usa en vez de contar lo que
aún no ha llegado. Además cubren el ancho ajustable del panel, que antes solo
se podía plegar.

El comportamiento en tiempo de ejecución (recorrido capítulo → partida y
arrastre del asa) se ha verificado con jsdom; aquí se fija el contrato que
puede romperse sin que nadie se dé cuenta en una revisión.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARBOL_JS = (RAIZ / "app/static/js/editor/arbol_catalogo.js").read_text(encoding="utf-8")
CSS = (RAIZ / "app/static/css/style.css").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# El esqueleto del servidor: recuentos sí, hojas no
# ---------------------------------------------------------------------------

def test_el_esqueleto_declara_totales_y_no_manda_las_hojas(entorno, cliente_web):
    datos = cliente_web.get("/presupuestos/editor/datos", params={"fase": "indice"}).json()

    assert datos["ok"] is True
    assert datos["partidas"] == [], "la fase índice no debe arrastrar las 3.000 partidas"
    arbol = datos["arbol"]
    assert arbol["capitulos"], "el árbol necesita al menos un capítulo"
    assert arbol["total"] > 0

    total = 0
    for capitulo in arbol["capitulos"]:
        assert capitulo["nombre"].strip()
        assert capitulo["total"] == sum(sub["total"] for sub in capitulo["subs"])
        for sub in capitulo["subs"]:
            assert sub["total"] == sum(apt["total"] for apt in sub["apartados"])
            for apartado in sub["apartados"]:
                # La hoja se pide apartado a apartado; aquí no viaja ninguna.
                assert "hojas" not in apartado
                assert apartado["total"] >= 1
        total += capitulo["total"]
    assert total == arbol["total"]


def test_las_hojas_llegan_solo_al_pedirlas_y_con_su_precio(entorno, cliente_web):
    esqueleto = cliente_web.get("/presupuestos/editor/datos", params={"fase": "indice"}).json()
    capitulo = next(c for c in esqueleto["arbol"]["capitulos"] if c["total"] > 0)
    sub = next(s for s in capitulo["subs"] if s["total"] > 0)
    apartado = next(a for a in sub["apartados"] if a["total"] > 0)

    datos = cliente_web.get("/presupuestos/editor/hojas", params={
        "categoria": capitulo["clave"],
        "subcategoria": sub["clave"],
        "apartado": apartado["clave"],
    }).json()

    assert datos["ok"] is True
    assert datos["partidas"], "el apartado debe devolver sus partidas"
    assert len(datos["partidas"]) == apartado["total"]
    for partida in datos["partidas"]:
        assert partida["nombre"].strip()
        assert "precio" in partida


# ---------------------------------------------------------------------------
# El árbol se pinta con lo que el servidor declara
# ---------------------------------------------------------------------------

def test_el_recuento_sin_busqueda_sale_del_total_declarado():
    assert "function contarApartado(bloqueApartado)" in ARBOL_JS
    # El total del servidor manda mientras no haya consulta…
    assert 'typeof apartado.total === "number" && apartado.total > 0' in ARBOL_JS
    # …y con consulta se cuenta lo que de verdad coincide.
    assert "var vistasApartado = contarApartado(bloqueApartado);" in ARBOL_JS
    # Contar las hojas cargadas fue exactamente el fallo: cero y a ocultar.
    assert "var vistasApartado = hojasDeApartado(bloqueApartado).length;" not in ARBOL_JS


def test_los_capitulos_se_abren_solos_para_poder_explorar_el_catalogo():
    assert "var abrirCap = vistasCap > 0;" in ARBOL_JS
    # Los subcapítulos siguen plegados: abrirlos todos llenaría la barra.
    assert "var abrirSub = Boolean(consultaActual) && vistasSub > 0;" in ARBOL_JS
    # Buscar sigue abriendo lo que conserva resultados, y solo eso.
    assert "var abrirApartado = Boolean(consultaActual) && vistasApartado > 0;" in ARBOL_JS


# ---------------------------------------------------------------------------
# Ancho del panel: arrastrar, teclado y memoria
# ---------------------------------------------------------------------------

def test_el_panel_tiene_un_asa_de_ancho_accesible():
    assert 'separador.className = "arbol-resize";' in ARBOL_JS
    assert '"role", "separator"' in ARBOL_JS
    assert '"aria-orientation", "vertical"' in ARBOL_JS
    assert "pointerdown" in ARBOL_JS and "pointermove" in ARBOL_JS
    assert "ArrowRight" in ARBOL_JS and "ArrowLeft" in ARBOL_JS
    assert "dblclick" in ARBOL_JS, "doble clic debe restablecer el ancho"


def test_el_ancho_se_recuerda_y_respeta_limites():
    assert '"arbol-catalogo-ancho"' in ARBOL_JS
    assert "localStorage.setItem(CLAVE_ANCHO" in ARBOL_JS
    assert "restaurarAncho()" in ARBOL_JS
    assert "var ANCHO_MIN = 260;" in ARBOL_JS
    assert "var ANCHO_MAX = 720;" in ARBOL_JS
    assert "var ANCHO_POR_DEFECTO = 340;" in ARBOL_JS


def test_el_ancho_se_aplica_a_la_columna_del_grid_no_solo_al_panel():
    # La CSP no permite escribir `.style` desde JS: se usa la hoja con nonce.
    assert 'window.CotizatStyles.set(layout, "--arbol-ancho"' in ARBOL_JS
    assert ".style." not in ARBOL_JS
    assert "--arbol-ancho: 340px;" in CSS
    assert "grid-template-columns: minmax(260px, var(--arbol-ancho)) minmax(0, 1fr);" in CSS
    # El modo foco ya no vuelve a fijar 280 px: respeta lo que elija el usuario.
    assert "minmax(220px, 280px)" not in CSS
    assert "--arbol-ancho: 300px;" in CSS


def test_el_asa_se_oculta_donde_no_cabe():
    assert ".arbol-resize" in CSS
    assert ".arbol-catalogo.plegado .arbol-resize { display: none; }" in CSS
    # En hoja inferior (móvil y tablet) el ancho es el de la pantalla.
    assert "  .arbol-resize { display: none; }" in CSS


def test_hay_un_boton_explicito_para_ensanchar_que_cicla_anchos():
    """El asa se descubre tarde: el botón de la cabecera lo hace evidente."""
    assert 'ensanchar.id = "arbol-ancho-toggle"' in ARBOL_JS
    assert "var ANCHOS_COMODOS = [340, 460, 580, 700];" in ARBOL_JS
    assert "siguienteAncho(anchoActual())" in ARBOL_JS
    # Al llegar al ancho más cómodo que cabe, vuelve al de partida.
    assert "return ANCHOS_COMODOS[0];" in ARBOL_JS
    assert ".arbol-ancho-toggle" in CSS
