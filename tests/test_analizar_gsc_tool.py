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


# ---------------------------------------------------------------------------
# El resto de exportaciones de Search Console: cobertura, serie diaria, países,
# dispositivos, problemas de indexación y apariciones enriquecidas. Se probaron
# con una descarga real de 11 CSV (02/11/2026): sin estas, el diagnóstico se
# queda en «consultas y páginas» y no ve el crecimiento de «sin indexar».
# ---------------------------------------------------------------------------


def _tabla_csv(tmp_path: Path, nombre: str, cuerpo: str) -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(cuerpo, encoding="utf-8-sig")
    return ruta


def test_reconoce_el_archivo_de_cobertura(tmp_path):
    ruta = _tabla_csv(
        tmp_path,
        "Gráfico.csv",
        "Fecha,Sin indexar,Indexadas,Impresiones\n"
        "2026-08-20,9,2,5\n2026-10-22,210,75,102\n",
    )
    assert gsc.tipo_de_archivo(ruta) == "cobertura"
    cabecera, filas = gsc.leer_tabla(ruta)
    texto = "\n".join(gsc.informe_cobertura(cabecera, filas))
    assert "210" in texto and "75" in texto
    # Las no indexadas suben y las indexadas no: hay que avisar.
    assert "Aviso" in texto


def test_reconoce_la_serie_diaria_y_su_pico(tmp_path):
    ruta = _tabla_csv(
        tmp_path,
        "Gráfico-2.csv",
        "Fecha,Clics,Impresiones,CTR,Posición\n"
        "2026-10-25,2,76,2.63%,39.9\n2026-10-28,10,1129,0.89%,24.4\n"
        "2026-10-31,7,1017,0.69%,25.6\n",
    )
    assert gsc.tipo_de_archivo(ruta) == "grafico"
    cabecera, filas = gsc.leer_tabla(ruta)
    texto = "\n".join(gsc.informe_grafico(cabecera, filas))
    assert "1.129" in texto
    assert "Escalón" in texto


def test_paises_y_dispositivos_salen_ordenados_por_impresiones(tmp_path):
    ruta = _tabla_csv(
        tmp_path,
        "Países.csv",
        "País,Clics,Impresiones,CTR,Posición\n"
        "España,9,1098,0.82%,24.58\nIrlanda,6,663,0.9%,16.52\n",
    )
    cabecera, filas = gsc.leer_tabla(ruta)
    texto = "\n".join(gsc.informe_dimension(cabecera, filas, "Por país", "País"))
    assert texto.index("España") < texto.index("Irlanda")
    # El CTR se escribe en formato español, no con punto decimal.
    assert "0,82 %" in texto


def test_problemas_de_indexacion_ordenados_por_paginas(tmp_path):
    ruta = _tabla_csv(
        tmp_path,
        "Problemas críticos.csv",
        "Motivo,Fuente,Validación,Páginas\n"
        "Página con redirección,Sitio web,No iniciada,10\n"
        "Descubierta: actualmente sin indexar,Sistemas de Google,Iniciada,177\n",
    )
    cabecera, filas = gsc.leer_tabla(ruta)
    texto = "\n".join(gsc.informe_problemas(cabecera, filas))
    assert texto.index("Descubierta") < texto.index("Página con redirección")


def test_una_tabla_de_problemas_vacia_no_rompe_el_informe(tmp_path):
    ruta = _tabla_csv(tmp_path, "Problemas no críticos.csv", "Motivo,Fuente,Validación,Páginas\n")
    cabecera, filas = gsc.leer_tabla(ruta)
    assert gsc.informe_problemas(cabecera, filas)


def test_mercado_e_idioma_de_una_url():
    assert gsc.mercado_de("https://cotizat.online/en-ie/prices/lifts-and-platform-lifts") == "en-ie"
    assert gsc.mercado_de("https://cotizat.online/es/precios/portones") == "es"
    assert gsc.mercado_de("https://cotizat.online/precios-comparados") == "precios-comparados"
    # Brasil paga impresiones en portugués y la web no tiene páginas en portugués.
    assert gsc.idioma_de_mercado("br") == "portugués"
    assert gsc.idioma_de_mercado("en-gb") == "inglés"
    assert gsc.idioma_de_mercado("ni") == "español"


# ---------------------------------------------------------------------------
# El embudo, que es el que decide el ingreso (no el tráfico).
# ---------------------------------------------------------------------------

from tools import analizar_embudo as emb  # noqa: E402


def test_la_conversion_cuenta_a_pago_es_la_del_titular():
    """41 cuentas y 4 pagos: 9,8 %. Es el número que ordena las prioridades."""
    datos = emb.embudo(cuentas=41, pagos=4)
    assert round(datos["conversion_cuenta_pago"], 1) == 9.8
    assert datos["sin_pagar"] == 37


def test_el_ltv_usa_los_precios_publicados():
    valor = emb.ltv(emb.PRECIO_ANUAL, emb.PRECIO_MENSUAL, meses_activo=12)
    assert valor["anual"] == 89.0
    assert valor["mensual"] > emb.PRECIO_ANUAL  # el mensual sale más caro al año


def test_el_cac_permitido_es_un_tercio_del_ltv():
    assert emb.cac_permitido(90.0) == 30.0


def test_duplicar_clientes_por_conversion_es_la_mitad_de_trabajo():
    datos = emb.embudo(cuentas=41, pagos=4, visitas=49)
    # Doblar la conversión exige el doble; doblar visitas exige el doble.
    assert round(datos["conversion_para_doblar"], 1) == 19.5
    assert datos["visitas_para_doblar"] == 98


def test_el_informe_incluye_las_preguntas_que_faltan_por_responder():
    texto = emb.informe(41, 4, None, 12)
    assert "9.8 %" in texto
    assert "crear un presupuesto" in texto
    assert "las 4 que pagan" in texto
