"""Activación incremental: un mercado anuncia solo lo que ha localizado.

Contexto: el 22/10/2026 se anunciaron los 22 catálogos a la vez y el sitio pasó
a la 44 de posición media con 0 clics. El catálogo hispano quedó en ``noindex``
entero. Levantarlo entero otra vez sería repetir el incidente.

Desde esta ronda la unidad ya no es el mercado sino la ficha
(``datos/localizado/<CC>.json``):

* una partida con texto propio validado se anuncia;
* su apartado se anuncia cuando hay al menos tres;
* la portada del catálogo, si hay alguna;
* y el hreflang solo enlaza destinos que se anuncian, uno a uno.

Estas pruebas fijan ese contrato en la única función que decide
(``resto_indexable``), en el sitemap y en lo que viaja al navegador
(``<meta robots>`` + ``X-Robots-Tag``), que nacen de la misma fuente.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import precios_publicos as pp

BASE = "https://cotizat.online"
CC = "MX"


@pytest.fixture(autouse=True)
def _sin_cache_contaminada():
    """Aísla el registro y el índice en vivo entre pruebas.

    ``_indice_en_vivo`` está cacheado con ``lru_cache`` en producción (cuesta
    segundos por país). Una prueba que lo construya con un registro falso
    dejaría ese resultado envenenado para la siguiente —y para la prueba de
    deriva del artefacto, que compara el JSON servido con el cálculo en vivo—.
    Se limpia antes y después, no solo después: una prueba que falle a mitad
    tampoco debe arrastrar estado.
    """
    pp._localizado.cache_clear()
    pp._indice_en_vivo.cache_clear()
    yield
    pp._localizado.cache_clear()
    pp._indice_en_vivo.cache_clear()


def _indice(cc: str = CC) -> dict:
    indice = pp._indice(cc)
    assert indice is not None, f"{cc} debería tener catálogo"
    return indice


def _apartado_con_partidas(n: int = 3, cc: str = CC) -> tuple[str, list[dict]]:
    indice = _indice(cc)
    for slug_ap in sorted(indice["apartados"]):
        fichas = [
            indice["partidas"][(slug_ap, resumen["slug"])]
            for resumen in indice["apartados"][slug_ap]["partidas"]
        ]
        if len(fichas) >= n:
            return slug_ap, fichas[:n]
    raise AssertionError("ningún apartado con partidas suficientes")


def _registro(fichas: list[dict]) -> dict[str, dict]:
    return {
        ficha["codigo"]: {
            "titulo": f"{ficha['titulo']} (edición del mercado)",
            "descripcion": " ".join(f"Texto propio del mercado {i}." for i in range(20)),
            "recursos": {},
            "revisado": "2026-11-06",
        }
        for ficha in fichas
    }


@pytest.fixture
def un_solo_apartado(monkeypatch):
    """Un apartado con tres fichas localizadas y el resto del mercado vacío."""
    slug_ap, fichas = _apartado_con_partidas(3)
    registro = _registro(fichas)
    monkeypatch.setattr(
        pp, "_localizado", lambda cc: registro if str(cc).upper() == CC else {}
    )
    return slug_ap, fichas


def test_sin_texto_propio_el_mercado_sigue_apagado():
    """El estado de hoy: México existe, se navega y no se anuncia."""
    slug_ap, fichas = _apartado_con_partidas(1)
    ficha = fichas[0]
    assert pp.ficha_indexable(CC) is False
    assert pp.partida_indexable(CC, slug_ap, ficha["slug"]) is False
    assert pp.apartado_indexable(CC, slug_ap) is False
    assert pp.indice_indexable(CC) is False
    assert pp.urls_sitemap(CC, BASE) == []


def test_una_ficha_localizada_se_anuncia_sola(un_solo_apartado):
    """Con texto propio, la ficha entra en el índice y en el sitemap."""
    slug_ap, fichas = un_solo_apartado
    ficha = fichas[0]
    assert pp.partida_localizada(CC, ficha["codigo"]) is True
    assert pp.partida_indexable(CC, slug_ap, ficha["slug"]) is True
    assert pp.indice_indexable(CC) is True
    # La portada del mercado, sí: es la que reparte autoridad a la ficha.
    assert pp.resto_indexable("precios", CC) is True
    assert pp.resto_indexable(f"precios/{slug_ap}/{ficha['slug']}", CC) is True

    locs = [entrada["loc"] for entrada in pp.urls_sitemap(CC, BASE)]
    assert f"{BASE}/mx/precios" in locs
    # Exactamente las fichas localizadas, ni una más: las hermanas del
    # apartado que no tienen texto propio siguen fuera del sitemap.
    anunciadas = {
        loc
        for loc in locs
        if loc.startswith(f"{BASE}/mx/precios/") and loc.count("/") == 6
    }
    assert anunciadas == {
        f"{BASE}/mx/precios/{slug_ap}/{f['slug']}" for f in fichas
    }


def test_el_apartado_necesita_tres_fichas(monkeypatch):
    """Un listado con una o dos fichas no lleva a ninguna parte."""
    slug_ap, fichas = _apartado_con_partidas(3)
    for cuantas, esperado in ((2, False), (3, True)):
        registro = _registro(fichas[:cuantas])
        monkeypatch.setattr(
            pp, "_localizado", lambda cc, r=registro: r if str(cc).upper() == CC else {}
        )
        assert pp.apartado_indexable(CC, slug_ap) is esperado
        locs = [entrada["loc"] for entrada in pp.urls_sitemap(CC, BASE)]
        assert (f"{BASE}/mx/precios/{slug_ap}" in locs) is esperado


def test_una_ficha_sin_localizar_sigue_en_noindex(un_solo_apartado):
    """La hermana no localizada no se cuela por estar en un apartado anunciado."""
    slug_ap, fichas = un_solo_apartado
    indice = _indice()
    otra = next(
        ficha
        for (ap, _slug), ficha in sorted(indice["partidas"].items())
        if ap != slug_ap
    )
    assert pp.partida_indexable(CC, otra["slug_apartado"], otra["slug"]) is False
    assert pp.resto_indexable(
        f"precios/{otra['slug_apartado']}/{otra['slug']}", CC
    ) is False


def test_las_descargas_y_la_mano_de_obra_van_con_el_mercado(un_solo_apartado):
    """El JSON y la tabla de tarifas no se anuncian por una ficha suelta."""
    assert pp.resto_indexable("precios.json", CC) is False
    assert pp.resto_indexable("mano-de-obra", CC) is False


def test_el_hreflang_no_apunta_a_paginas_noindex(un_solo_apartado):
    """Un solo destino noindex invalida el grupo: se filtran uno a uno."""
    from app.seo_precios import _hreflang

    slug_ap, fichas = un_solo_apartado
    ficha = fichas[0]
    rutas = [
        {
            "hreflang": "es",
            "cc": "ES",
            "path": f"/es/precios/{ficha['slug_apartado']}/{ficha['slug']}",
        },
        {"hreflang": "es-MX", "cc": "MX", "path": f"/mx/precios/{slug_ap}/{ficha['slug']}"},
        {"hreflang": "es-CO", "cc": "CO", "path": f"/co/precios/{slug_ap}/{ficha['slug']}"},
    ]
    etiquetas = [enlace["hreflang"] for enlace in _hreflang(BASE, rutas)]
    assert etiquetas == ["es", "es-MX", "x-default"]


def test_el_texto_propio_llega_a_la_ficha(monkeypatch):
    """En el índice en vivo manda el texto del mercado, y el slug lo sigue."""
    slug_ap, fichas = _apartado_con_partidas(1)
    ficha = fichas[0]
    registro = {
        ficha["codigo"]: {
            "titulo": "Suministro y colocación de block de concreto 15x20x40",
            "descripcion": " ".join(["Muro de block de concreto en México."] * 8),
            "recursos": {},
            "revisado": "2026-11-06",
        }
    }
    monkeypatch.setattr(
        pp, "_localizado", lambda cc: registro if str(cc).upper() == CC else {}
    )
    indice = pp._indice_en_vivo(CC)
    assert indice is not None
    destino = indice["por_codigo"][ficha["codigo"]]
    publicada = indice["partidas"][destino]
    assert publicada["titulo"].startswith("Suministro y colocación de block")
    assert publicada["slug"] != ficha["slug"], "el slug tiene que nacer del texto nuevo"


def test_el_registro_no_acepta_el_texto_español(monkeypatch, tmp_path):
    """Copiar la descripción española no localiza nada: es el mismo contenido."""
    slug_ap, fichas = _apartado_con_partidas(2)
    ficha = fichas[0]
    monkeypatch.setattr(pp, "_DIR_LOCALIZADO", tmp_path)
    pp._localizado.cache_clear()
    ruta = tmp_path / f"{CC}.json"

    def escribir(**cambios):
        entrada = {
            "titulo": "Block de concreto 15x20x40 puesto en obra",
            "descripcion": " ".join(["Muro de block en México."] * 10),
            "revisado": "2026-11-06",
        }
        entrada.update(cambios)
        ruta.write_text(
            json.dumps({"partidas": {ficha["codigo"]: entrada}}, ensure_ascii=False),
            encoding="utf-8",
        )
        pp._localizado.cache_clear()
        return pp._localizado(CC)

    try:
        assert ficha["codigo"] in escribir(), "un texto propio válido debe contar"
        assert escribir(descripcion=ficha["descripcion"]) == {}, "texto español copiado"
        assert escribir(descripcion="Corto.") == {}, "descripción por debajo del mínimo"
        assert escribir(titulo="") == {}, "sin título no hay ficha"
        assert escribir(descripcion="") == {}
    finally:
        pp._localizado.cache_clear()


def test_el_mercado_completo_no_cambia():
    """España y los cinco traducidos conservan su política exacta."""
    for cc in pp.MERCADOS_FICHAS_INDEXABLES:
        assert pp.resto_indexable("precios.json", cc) is True
        assert pp.resto_indexable("mano-de-obra", cc) is True
        assert pp.resto_indexable("precios", cc) is True
        assert pp.indice_indexable(cc) is True
    # Las 2.201 URL del catálogo español siguen siendo 2.201.
    assert len(pp.urls_sitemap("ES", BASE)) == 2201


def test_la_cabecera_y_el_meta_coinciden_en_la_ficha(monkeypatch):
    """Lo que ve Google en el HTML y en la cabecera sale de la misma función."""
    slug_ap, fichas = _apartado_con_partidas(3)
    localizada, otra = fichas[0], None
    indice = _indice()
    otra = next(
        ficha
        for (ap, _slug), ficha in sorted(indice["partidas"].items())
        if ap != slug_ap
    )
    registro = _registro([localizada])
    monkeypatch.setattr(
        pp, "_localizado", lambda cc: registro if str(cc).upper() == CC else {}
    )
    with TestClient(app, base_url=BASE) as cliente:
        buena = cliente.get(f"/mx/precios/{slug_ap}/{localizada['slug']}")
        mala = cliente.get(
            f"/mx/precios/{otra['slug_apartado']}/{otra['slug']}"
        )
    assert buena.status_code == 200 and mala.status_code == 200
    assert "noindex" not in buena.headers.get("x-robots-tag", "")
    assert "noindex" not in buena.text.split("</head>")[0]
    assert "noindex" in mala.headers.get("x-robots-tag", "")
    assert "noindex" in mala.text.split("</head>")[0]


def test_todo_registro_esta_en_el_artefacto():
    """El artefacto es lo que se sirve: si el registro cambia, se regenera.

    ``_indice`` lee ``datos/precios_publicos/<CC>.json`` (milisegundos) y no el
    cálculo en vivo (segundos). Si alguien escribe texto propio y no ejecuta
    ``tools/generar_precios_publicos.py``, la ficha se anunciaría con el texto
    español y el slug viejo: justo el error que hay que evitar. La prueba de
    deriva de ``test_precios_publicos`` también lo caza; esta lo dice con el
    mensaje exacto.
    """
    for cc in pp.PAISES_PRECIOS_PUBLICOS:
        registro = pp._localizado(cc)
        if not registro:
            continue
        indice = pp._indice(cc) or {}
        for codigo, texto in registro.items():
            destino = (indice.get("por_codigo") or {}).get(codigo)
            if not destino:
                continue
            servida = indice["partidas"][destino]
            assert servida["titulo"] == texto["titulo"], (
                f"{cc}: el registro tiene texto propio y el artefacto no. "
                "Ejecuta python tools/generar_precios_publicos.py"
            )
