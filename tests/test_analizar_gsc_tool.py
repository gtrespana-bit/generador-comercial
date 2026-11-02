"""Analizador de Search Console: la lectura de los CSV que decide el plan.

Lo que se prueba aquí es lo que puede dar un diagnóstico equivocado: el
formato de la exportación (coma o punto y coma, decimales con coma, las dos
líneas de preámbulo), el reparto de impresiones entre URLs de una misma
consulta y el orden de las oportunidades. La herramienta no toca la red.
"""
from __future__ import annotations

from pathlib import Path

from tools import analizar_gsc as gsc

_CABECERA_ES = "Consultas principales;https://cotizat.online/\nÚltimos 3 meses\n"


def _csv(tmp_path: Path, nombre: str, cuerpo: str) -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(cuerpo, encoding="utf-8-sig")
    return ruta


def test_lee_el_formato_espanol_con_punto_y_coma(tmp_path):
    ruta = _csv(
        tmp_path,
        "Consultas.csv",
        _CABECERA_ES
        + "Consultas principales;Clics;Impresiones;CTR;Posición\n"
        + "software de presupuestos;3;1.412;0,21 %;41,2\n",
    )
    filas = gsc.leer_csv(ruta)
    assert len(filas) == 1
    fila = filas[0]
    assert fila["clave"] == "software de presupuestos"
    assert fila["clics"] == 3
    # El separador de miles no puede convertirse en decimal ni al revés.
    assert fila["impresiones"] == 1412
    assert fila["posicion"] == 41.2


def test_lee_el_formato_ingles_con_coma(tmp_path):
    ruta = _csv(
        tmp_path,
        "queries.csv",
        "Top queries,https://cotizat.online/\nLast 3 months\n"
        "Top queries,Clicks,Impressions,CTR,Position\n"
        '"construction estimating software",4,"1,234",0.32%,18.6\n',
    )
    fila = gsc.leer_csv(ruta)[0]
    assert fila["clics"] == 4
    assert fila["impresiones"] == 1234
    assert fila["posicion"] == 18.6


def test_la_exportacion_de_dos_dimensiones_guarda_la_url(tmp_path):
    ruta = _csv(
        tmp_path,
        "cruce.csv",
        _CABECERA_ES
        + "Consultas principales;Páginas;Clics;Impresiones;CTR;Posición\n"
        + "software de presupuestos;https://cotizat.online/es/;1;90;1,11 %;28,6\n",
    )
    fila = gsc.leer_csv(ruta)[0]
    assert fila["url"] == "https://cotizat.online/es/"
    assert gsc.tipo_de_exportacion(gsc.leer_csv(ruta)) == "cruce"


def test_detecta_canibalizacion_entre_mercados(tmp_path):
    ruta = _csv(
        tmp_path,
        "cruce.csv",
        _CABECERA_ES
        + "Consultas principales;Páginas;Clics;Impresiones;CTR;Posición\n"
        + "software de presupuestos;https://cotizat.online/;1;120;0,83 %;34,1\n"
        + "software de presupuestos;https://cotizat.online/es/;1;90;1,11 %;28,6\n"
        + "software de presupuestos;https://cotizat.online/mx/;0;70;0,00 %;39,0\n"
        + "otra consulta;https://cotizat.online/;0;5;0,00 %;60,0\n",
    )
    filas = gsc.leer_csv(ruta)
    grupos = {}
    for fila in filas:
        grupos.setdefault(fila["clave"], []).append(fila.get("url"))
    repetidas = {c: u for c, u in grupos.items() if len(set(u)) > 1}
    # La consulta con tres URLs es la señal; la de una sola URL no lo es.
    assert "software de presupuestos" in repetidas
    assert "otra consulta" not in repetidas


def test_la_franja_del_techo_es_la_que_produce_clics():
    """Una página en el puesto 3 rinde mucho más que la misma en el 40."""
    assert gsc._clics_a_posicion(1000, 3) > gsc._clics_a_posicion(1000, 40) * 10
    assert gsc._clics_a_posicion(1000, 40) < 5


def test_informe_de_consultas_marca_las_que_no_reciben_clics(tmp_path):
    filas = [
        {"clave": "cotizat", "clics": 12, "impresiones": 31, "posicion": 1.4},
        {
            "clave": "programa para hacer presupuestos",
            "clics": 0,
            "impresiones": 88,
            "posicion": 37.9,
        },
    ]
    texto = "\n".join(gsc.informe_consultas(filas, "cotizat", 10))
    assert "programa para hacer presupuestos" in texto
    assert "cero clics" in texto.lower()


def test_sin_ficheros_avisa_en_vez_de_fallar():
    assert gsc.main(["--carpeta", "/ruta/que/no/existe"]) == 2
