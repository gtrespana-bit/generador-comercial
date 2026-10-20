"""Ejemplo de presupuesto de la landing en la moneda de cada país.

El ejemplo (remodelación de baño + APU real del catálogo) se convierte a la
moneda del visitante con la tasa de referencia verificada, se formatea con
los símbolos inequívocos (COL$, MX$, S/, US$) y usa el IVA y la ciudad del
país. Estas pruebas fijan las invariantes:

* las cifras del catálogo cuentan partidas **y** recursos (líneas de precio);
* en cualquier moneda, los totales visibles suman exactamente lo que se
  muestra (un presupuesto de ejemplo que no sumara sería demoledor);
* la terminología de las partidas se traduce al país (friso → pañete).
"""
from __future__ import annotations

import re

from app.routers.common import cifras_catalogo
from app.services.landing_ejemplo import contexto_ejemplo


# ---------------------------------------------------------------------------
# Cifras del catálogo: partidas + recursos = líneas de precio
# ---------------------------------------------------------------------------

def test_cifras_catalogo_cuentan_partidas_y_recursos():
    c = cifras_catalogo()
    assert c["partidas"] >= 3000
    assert c["recursos"] >= 300
    # La venta honesta: líneas de precio = partidas + precios de recursos
    assert c["lineas_precio"] == c["partidas"] + c["recursos"]
    assert c["lineas_precio_txt"].count(".") >= 1  # 3.398, no 3398
    # Desglose por grupos y líneas de descomposición reales
    assert c["materiales"] + c["mano_obra"] + c["equipo"] == c["recursos"]
    assert c["lineas_descomp"] >= c["partidas"] * 4  # cada partida descompuesta
    assert c["packs"] >= 1 and c["packs_partidas"] >= c["packs"]


def test_cifras_catalogo_sin_deriva():
    """El JSON precalculado coincide con el cálculo en vivo.

    ``cifras_catalogo()`` lee ``basedatos_partidas/datos/cifras_catalogo.json``
    para no recorrer miles de descompuestos en cada instancia. Si este test
    falla, se cambió el catálogo o las ``RECETAS_DEMO`` sin regenerar:
    ``python tools/generar_cifras_catalogo.py``.
    """
    import json as _json

    from app.routers.common import (
        _RUTA_CIFRAS_PRECALCULADAS,
        _calcular_cifras_catalogo,
    )

    assert _RUTA_CIFRAS_PRECALCULADAS.is_file(), (
        "Falta cifras_catalogo.json: ejecútalo con "
        "python tools/generar_cifras_catalogo.py"
    )
    en_disco = _json.loads(_RUTA_CIFRAS_PRECALCULADAS.read_text(encoding="utf-8"))
    assert en_disco == _calcular_cifras_catalogo()
    # Y es lo que sirve la app (no la red de cálculo en vivo ni las fijas).
    assert cifras_catalogo() == en_disco


# ---------------------------------------------------------------------------
# Formato por moneda
# ---------------------------------------------------------------------------

def _a_numero(texto: str, mercado: dict | None = None) -> float:
    """Invierte el formato del mercado, no un convenio fijo.

    Antes daba por hecho la coma decimal en todas partes, y eso era cierto
    solo mientras México se formateaba como España. Hoy México y Ecuador
    escriben «2,224.62» y España «2.224,62», así que hay que saber de qué
    mercado viene la cifra.
    """
    limpio = re.sub(r"[^\d,.\-]", "", texto)
    if mercado is None:
        return float(limpio.replace(".", "").replace(",", "."))
    return float(
        limpio.replace(mercado["separador_miles"], "")
        .replace(mercado["separador_decimal"], ".")
    )


def _mercado_de(codigo: str) -> dict:
    from app.paises import PAIS_GENERICO, PAISES

    return PAISES.get(str(codigo or "").strip().upper()) or PAIS_GENERICO


def test_ejemplo_colombia_usa_cop_con_iva_19_y_bogota():
    ej = contexto_ejemplo("CO")
    assert ej["moneda"] == "COP"
    assert ej["simbolo"] == "COL$"
    assert ej["decimales"] == 0
    assert ej["iva"] == 19
    assert ej["ciudad"] == "Bogotá"
    assert "S.A.S." in ej["empresa"]
    # Ningún importe del ejemplo queda en dólares crudos
    for cap in ej["caps"]:
        for p in cap["partidas"]:
            assert p["importe"].endswith("COL$")


def test_ejemplo_mexico_usa_mxn_y_rfc():
    ej = contexto_ejemplo("MX")
    assert ej["moneda"] == "MXN"
    assert ej["simbolo"] == "MX$"
    assert ej["iva"] == 16
    assert ej["tasa"] == 17.06
    assert "S.A. de C.V." in ej["empresa"]


def test_ejemplo_peru_usa_sol():
    ej = contexto_ejemplo("PE")
    assert ej["moneda"] == "PEN"
    assert ej["simbolo"] == "S/"
    assert ej["iva"] == 18


def test_ejemplo_ve_ecuador_y_generico_quedan_en_usd():
    for codigo in ("VE", "EC", "", None):
        ej = contexto_ejemplo(codigo)
        assert ej["moneda"] == "USD"
        assert ej["convierte"] is False
        # Sin moneda local no se muestra nota de conversión
        assert ej["tasa"] == 1.0


def test_ejemplo_moneda_sin_tasa_verificada_degrada_a_usd(monkeypatch):
    """Moneda local sin tasa verificada: nunca se inventa una conversión.

    CLP obtuvo tasa verificada (925,90 · 25/08/2026), así que ningún país del
    selector ejerce hoy este camino de forma natural; se simula que la
    consulta de tasas no devuelve nada y se comprueba la degradación a USD.
    """
    from app.services import landing_ejemplo

    monkeypatch.setattr(landing_ejemplo, "tasa_sugerida", lambda _moneda: None)
    landing_ejemplo.contexto_ejemplo.cache_clear()
    try:
        ej = landing_ejemplo.contexto_ejemplo("CL")
    finally:
        landing_ejemplo.contexto_ejemplo.cache_clear()
    assert ej["moneda"] == "USD"
    assert ej["convierte"] is False


# ---------------------------------------------------------------------------
# Invariantes aritméticas en cualquier moneda
# ---------------------------------------------------------------------------

def _invariantes(ej: dict, mercado: dict | None = None) -> None:
    def n(texto: str) -> float:
        return _a_numero(texto, mercado)

    for cap in ej["caps"]:
        filas = sum(n(p["importe"]) for p in cap["partidas"])
        assert abs(n(cap["importe"]) - filas) < 1.01
        ben = sum(n(p["beneficio"]) for p in cap["partidas"])
        assert abs(n(cap["beneficio"].replace("+ ", "")) - ben) < 1.01 * len(cap["partidas"])
    tot = ej["tot"]
    assert abs(
        n(tot["subtotal"])
        - n(tot["obra"])
        - n(tot["productos"])
    ) < 1.01
    assert abs(
        n(tot["total"]) - n(tot["subtotal"]) - n(tot["iva"])
    ) < 1.01
    assert abs(
        n(tot["subtotal"]) - n(tot["coste"]) - n(tot["beneficio"])
    ) < 1.01 * 20  # redondeo por fila


def test_ejemplo_suma_exacta_en_todas_las_monedas():
    """Se comprueba leyendo cada cifra en su mercado.

    México y Ecuador separan como Estados Unidos: leídos con el convenio
    europeo, «2,224.62» valdría 2.22 y las sumas no cuadrarían.
    """
    for codigo in ("", "VE", "CO", "MX", "PE", "EC"):
        _invariantes(contexto_ejemplo(codigo), _mercado_de(codigo))


def test_ejemplo_apu_real_del_catalogo():
    ej = contexto_ejemplo("CO")
    apu = ej["apu"]
    assert apu["disponible"] is True
    assert apu["codigo"] == "14.04.01.060"
    assert apu["titulo"].startswith("Muro de cerramiento")
    grupos = {f["grupo"] for f in apu["filas"]}
    assert grupos == {"Material", "Mano de obra", "Equipo"}
    # Coste directo = suma de las filas visibles (+ complementarios)
    col = _mercado_de("CO")
    filas = sum(_a_numero(f["importe"], col) for f in apu["filas"])
    assert abs(_a_numero(apu["directo"], col) - filas) < 1.01 * len(apu["filas"])
    assert abs(
        _a_numero(apu["coste"], col) - _a_numero(apu["directo"], col) - _a_numero(apu["comp"], col)
    ) < 1.01
    # Precio de venta = coste × (1 + margen 35 %, defecto del catálogo desde 2026-08-25)
    pv = _a_numero(apu["precio"].split(" COL$/")[0] + " COL$", col)
    assert abs(pv - _a_numero(apu["coste"], col) * 1.35) < max(2.0, pv * 0.002)
    assert apu["margen"] == "+35 %"


def test_ejemplo_traduce_terminologia_al_pais():
    co = contexto_ejemplo("CO")
    nombres = {p["nombre"] for cap in co["caps"] for p in cap["partidas"]}
    assert any("Pañete" in n for n in nombres), nombres
    mx = contexto_ejemplo("MX")
    nombres_mx = {p["nombre"] for cap in mx["caps"] for p in cap["partidas"]}
    assert any("Aplanado" in n for n in nombres_mx), nombres_mx
    ve = contexto_ejemplo("VE")
    nombres_ve = {p["nombre"] for cap in ve["caps"] for p in cap["partidas"]}
    assert any(n.startswith("Friso") for n in nombres_ve), nombres_ve
