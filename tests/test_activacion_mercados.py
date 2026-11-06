"""La puerta que impide repetir el 23/10: nadie enciende un catálogo calcado.

El 21–22/10/2026 se anunciaron ~40 000 URL de catálogo de golpe, casi todas el
mismo texto con otra moneda. En 48 h el sitio pasó a la página 4–5 con 0 clics
(``docs/DIAGNOSTICO_TRAFICO_CERO_2026-10-23.md``). El 23/10 se apagó el
catálogo de los 16 mercados hispanos y la superficie volvió a estabilizarse.

Lo que faltaba entonces es lo que comprueba este fichero: **que un mercado solo
se anuncie cuando su prosa no sea la española**. La medida vive en
``app/services/localizacion.py`` y el informe se saca con
``tools/radar_activacion_mercados.py``.

Regla:

* España es la referencia y no se compara consigo misma.
* Todo mercado de ``MERCADOS_FICHAS_INDEXABLES`` tiene que dar ``listo`` o
  ``parcial`` (prosa con diferencias reales respecto a España).
* Los mercados traducidos al inglés pasan por traducción: su vocabulario no se
  parece al español (jaccard ≈ 0,02) y por eso están fuera de toda duda.
* Si algún día se decide encender un mercado calcado por una razón de negocio
  —una campaña en México, por ejemplo—, se documenta en ``EXCEPCIONES`` **con
  motivo escrito**. La excepción caduca sola: si el mercado pasa a ``listo``,
  el test falla y pide borrarla.
"""
from __future__ import annotations

import pytest

from app.services import localizacion
from app.services import precios_publicos as pp

#: Muestra usada en la suite. Suficiente para que la media no se mueva y rápida
#: (≈1 s para los 22 mercados publicados).
MUESTRA = 120

#: Mercados que se anuncian aun sin prosa propia, con el motivo por escrito.
#: Vacío a propósito: hoy ningún mercado necesita esta excepción.
EXCEPCIONES: dict[str, str] = {}

_MOTIVO_MINIMO = 40


@pytest.fixture(scope="module")
def radar() -> dict[str, dict]:
    """Veredicto de cada mercado publicado, calculado una sola vez."""
    return {fila["mercado"]: fila for fila in localizacion.radar(MUESTRA)}


def test_espana_es_la_referencia(radar):
    """España no se compara consigo misma: es el patrón de la prosa."""
    assert radar["ES"]["referencia"] is True
    assert radar["ES"]["jaccard"] is None


def test_todo_mercado_publicado_se_mide(radar):
    """Si un mercado tiene catálogo, tiene que aparecer en el radar."""
    publicados = set(pp.paises_publicados())
    assert publicados <= set(radar), sorted(publicados - set(radar))
    for cc in publicados:
        fila = radar[cc]
        assert fila["publicado"] is True
        if not fila["referencia"]:
            assert fila["comparadas"] > 0
            assert fila["jaccard"] is not None


def test_ningun_mercado_anunciado_es_un_calco(radar):
    """La regla del 23/10, en una línea de código.

    Un mercado cuyo texto es el español con otro precio no puede estar en
    ``MERCADOS_FICHAS_INDEXABLES``. Si este test falla, hay dos caminos
    honestos: escribir la prosa del mercado (baja el jaccard) o documentar la
    excepción con un motivo real.
    """
    problemas = []
    for cc in pp.MERCADOS_FICHAS_INDEXABLES:
        fila = radar.get(cc)
        assert fila is not None, f"{cc} está anunciado pero no tiene catálogo medible"
        if fila["referencia"] or fila["estado"] != "calco":
            continue
        if cc in EXCEPCIONES:
            continue
        problemas.append(
            f"{cc}: {fila['porcentaje_identico']}% del texto es literalmente el "
            f"español (jaccard {fila['jaccard']:.3f}). Localiza su prosa antes de "
            "anunciarlo, o justifica la excepción en EXCEPCIONES."
        )
    assert not problemas, problemas


def test_los_mercados_traducidos_no_dependen_de_esta_puerta(radar):
    """Los mercados en inglés pasan por traducción, no por reescritura.

    Se comprueba para que nadie «arregle» la puerta subiendo el umbral: si el
    inglés dejara de parecer distinto, el problema sería la traducción.
    """
    for cc in ("US", "GB", "CA", "AU", "IE"):
        fila = radar.get(cc)
        if fila is None:
            continue
        assert fila["estado"] == "listo", (cc, fila["jaccard"], fila["estado"])
        assert fila["jaccard"] < localizacion.UMBRAL_PROPIA


def test_las_excepciones_tienen_motivo_y_no_sobran(radar):
    """Una excepción sin motivo es un umbral escondido; una caducada, deuda."""
    for cc, motivo in EXCEPCIONES.items():
        assert cc in pp.MERCADOS_FICHAS_INDEXABLES, (
            f"{cc} tiene excepción pero no está anunciado: bórrala"
        )
        assert len(motivo.strip()) >= _MOTIVO_MINIMO, (
            f"la excepción de {cc} necesita un motivo escrito (≥{_MOTIVO_MINIMO} caracteres)"
        )
        fila = radar.get(cc) or {}
        assert fila.get("estado") == "calco", (
            f"{cc} ya tiene prosa propia: borra su excepción"
        )


def test_el_radar_propone_un_orden_de_encendido(radar):
    """El orden es determinista y empieza por el mercado más preparado.

    No es una preferencia estética: localizar 2 000 fichas de un mercado que ya
    tiene guías, nota de mano de obra y problema técnico propio es mucho más
    rápido que hacerlo en uno vacío. La primera posición es la del mercado con
    más guías ya indexadas; el resto sigue el criterio de ``clave_orden``.
    """
    orden = localizacion.mercados_por_encender(MUESTRA)
    assert orden, "no hay mercados pendientes de encender"
    for cc in orden:
        assert cc not in pp.MERCADOS_FICHAS_INDEXABLES
        assert radar[cc]["publicado"] is True
        assert radar[cc]["referencia"] is False

    claves = [localizacion.clave_orden(radar[cc]) for cc in orden]
    assert claves == sorted(claves), "el orden propuesto no sigue clave_orden"

    maximo = max(radar[cc]["guias"] for cc in orden)
    assert radar[orden[0]]["guias"] == maximo
    assert orden == localizacion.mercados_por_encender(MUESTRA), "orden inestable"
