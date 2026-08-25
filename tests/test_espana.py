"""España — versión de país: EUR, IVA 21 %, NIF, terminología y precios.

Regresiones de la apertura del mercado español: el país en el catálogo y el
selector, la traducción VE→ES del catálogo base (concreto→hormigón,
cielo raso→falso techo, mesón→encimera, plomero→fontanero), la tasa de
referencia USD→EUR, la landing adaptativa ``/es/`` y la matriz nacional de
precios de recursos en EUR.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import paises
from app.main import app
from app.services.tasa import factor_conversion_local, tasa_sugerida
from app.services.traduccion import codigo_desde_pais, traducir, traducir_partida

ORIGEN = "https://cotizat.test"
RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def cliente_web():
    return TestClient(app, base_url=ORIGEN)


# ---------------------------------------------------------------------------
# app/paises.py — España en el catálogo y en el selector
# ---------------------------------------------------------------------------

def test_espana_esta_en_el_selector():
    assert "ES" in paises.ORDEN_SELECTOR


def test_defaults_espana_sugieren_nif_eur_21():
    d = paises.defaults_para_pais("ES")
    assert d["codigo"] == "ES"
    assert d["nombre"] == "España"
    assert d["moneda"] == "EUR"
    assert d["iva"] == 21
    assert d["id_fiscal"] == "NIF"
    assert d["mercado"] == "español"


def test_ejemplos_de_formulario_espana():
    d = paises.defaults_para_pais("ES")
    assert d["id_fiscal_placeholder"] == "B12345678"
    assert d["telefono_ejemplo"].startswith("+34")
    assert d["razon_social_ejemplo"] == "S.L."
    assert d["ciudad_ejemplo"] == "Madrid"


def test_vocabulario_espana_terminos_locales():
    vocab = paises.defaults_para_pais("ES")["vocab"]
    # Términos de obra peninsulares, no latinos.
    for termino in ("hormigón", "pladur", "falso techo", "fontanero"):
        assert termino in vocab
    assert "concreto" not in vocab
    assert "plomero" not in vocab


# ---------------------------------------------------------------------------
# app/services/traduccion.py — terminología VE→ES al mostrar
# ---------------------------------------------------------------------------

def test_codigo_desde_nombre_espana():
    assert codigo_desde_pais("España") == "ES"
    assert codigo_desde_pais("españa") == "ES"
    assert codigo_desde_pais("Espana") == "ES"


def test_traduccion_concreto_a_hormigon():
    assert traducir("Concreto premezclado", "ES") == "Hormigón premezclado"
    assert traducir("concreto", "ES") == "hormigón"
    assert traducir("concretos", "ES") == "hormigones"


def test_traduccion_cielo_raso_a_falso_techo():
    assert traducir("Cielo raso de drywall", "ES") == "Falso techo de yeso laminado"


def test_traduccion_terminos_clave():
    assert traducir("mesón de cocina", "ES") == "encimera de cocina"
    assert traducir("plomero", "ES") == "fontanero"
    assert traducir("plomería", "ES") == "fontanería"
    assert traducir("poceta", "ES") == "inodoro"
    assert traducir("lavamanos", "ES") == "lavabo"
    assert traducir("cabilla", "ES") == "redondo"
    assert traducir("tanquilla", "ES") == "arqueta"
    assert traducir("enchapado", "ES") == "alicatado"


def test_traduccion_respeta_lo_que_ya_es_espanol():
    # Términos que ya son peninsulares no se degradan.
    assert traducir("falso techo", "ES") == "falso techo"
    assert traducir("alicatado", "ES") == "alicatado"
    assert traducir("solera", "ES") == "solera"


def test_traducir_partida_es_copia_no_mutada():
    class P:
        nombre = "Friso de mortero"
        descripcion = "Friso maestreado con concreto"
        categoria = "Revestimientos"

    p = P()
    t = traducir_partida(p, "ES")
    assert t is not p
    assert "Enfoscado" in t.nombre
    assert "hormigón" in t.descripcion
    # El original no cambia
    assert p.nombre == "Friso de mortero"


def test_traduccion_ve_sin_cambios():
    assert traducir("Friso de mortero", "VE") == "Friso de mortero"
    assert traducir("Friso de mortero", "") == "Friso de mortero"


def test_glosario_es_existe_y_es_valido():
    ruta = RAIZ / "basedatos_partidas" / "glosarios" / "ES.json"
    assert ruta.is_file(), "Falta el glosario VE→ES"
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["_origen"] == "VE"
    assert data["_destino"] == "ES"
    cambios = data["cambios"]
    assert cambios, "El glosario ES no tiene cambios"
    for c in cambios:
        assert c.get("de"), f"Cambio sin 'de': {c}"
        assert c.get("a"), f"Cambio sin 'a': {c}"


# ---------------------------------------------------------------------------
# Moneda y tasa — EUR
# ---------------------------------------------------------------------------

def test_tasa_sugerida_eur():
    tasa = tasa_sugerida("EUR")
    assert tasa is not None and tasa > 0
    # 1 USD -> EUR debe estar en el entorno de 0,8-0,95 (2026).
    assert 0.8 <= tasa <= 0.95


def test_factor_conversion_local_eur():
    tasa = tasa_sugerida("EUR")
    factor = factor_conversion_local("EUR", tasa)
    assert factor == pytest.approx(tasa)
    # Sin tasa no se inventa conversión.
    assert factor_conversion_local("EUR", None) == 1.0


def test_eur_es_moneda_soportada():
    from app.utils import SIMBOLOS, es_moneda_soportada, simbolo_moneda

    assert es_moneda_soportada("EUR")
    assert SIMBOLOS["EUR"] == "€"
    assert simbolo_moneda("EUR") == "€"


# ---------------------------------------------------------------------------
# Importador — la matriz ES es EUR
# ---------------------------------------------------------------------------

def test_importador_conoce_espana():
    from app.services.importador_precios_mercado import MONEDA_PAIS

    assert MONEDA_PAIS.get("ES") == "EUR"


# ---------------------------------------------------------------------------
# Landing adaptativa /es/ — moneda, IVA, NIF y terminología
# ---------------------------------------------------------------------------

def test_landing_es_redirige_a_slash(cliente_web):
    resp = cliente_web.get("/es", follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["location"].endswith("/es/")


def test_landing_espana_habla_de_espana(cliente_web):
    resp = cliente_web.get("/es/", follow_redirects=False)
    assert resp.status_code == 200
    assert "España" in resp.text
    assert "NIF" in resp.text
    assert "cotizat_pais=ES" in resp.headers["set-cookie"]


def test_landing_espana_muestra_ejemplo_en_eur(cliente_web):
    resp = cliente_web.get("/es/")
    assert resp.status_code == 200
    t = resp.text
    # IVA español y ciudad de ejemplo.
    assert "I.V.A. (21 %)" in t
    assert "Madrid" in t
    # La terminología del ejemplo se traduce (enfoscado, no friso).
    assert "Enfoscado" in t or "enfoscado" in t
    assert "Friso de mortero" not in t


def test_landing_espana_canonical_y_hreflang(cliente_web):
    resp = cliente_web.get("/es/")
    assert resp.status_code == 200
    assert 'rel="canonical" href="https://cotizat.test/es/"' in resp.text
    assert 'hreflang="es-ES"' in resp.text


def test_ficha_landing_espana():
    from app.seo import ficha_landing

    ficha = ficha_landing("ES")
    assert ficha["title"].startswith("CotizaT:")
    assert "España" in ficha["title"]
    assert ficha["canonical_path"] == "/es/"
    assert ficha["lang"] == "es-ES"


def test_hubs_de_intencion_espana_tienen_contenido_propio(cliente_web):
    """Las URLs /es/apu, /es/software-presupuestos y /es/remodelacion no son
    la página genérica con «España» sustituido: traen bloques y FAQ propios."""
    apu = cliente_web.get("/es/apu")
    soft = cliente_web.get("/es/software-presupuestos")
    ref = cliente_web.get("/es/remodelacion")
    for resp in (apu, soft, ref):
        assert resp.status_code == 200
        assert 'rel="canonical" href="https://cotizat.test/es/' in resp.text
    assert "mercado español" in apu.text or "euros" in apu.text.lower()
    assert "NIF" in soft.text
    assert "alicatado" in ref.text.lower()


# ---------------------------------------------------------------------------
# Matriz nacional de precios de recursos — España (EUR)
# ---------------------------------------------------------------------------

def _filas_matriz_espana():
    ruta = RAIZ / "basedatos_partidas" / "salida" / "precios_recursos_espana.csv"
    assert ruta.is_file(), "Falta la matriz de precios ES; ejecutar tools/generar_matriz_precios_espana.py"
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def test_matriz_espana_cubre_todos_los_recursos():
    filas = _filas_matriz_espana()
    # Los compuestos se abren en componentes y no son recursos físicos.
    data = json.loads((RAIZ / "basedatos_partidas" / "datos" / "recursos.json").read_text(encoding="utf-8"))
    esperados = set()
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (data.get(categoria) or {}).items():
            if isinstance(item, dict) and "descripcion" in item and not item.get("composicion"):
                esperados.add(codigo)
    cubiertos = {f["codigo_recurso"] for f in filas}
    assert cubiertos == esperados, (
        f"Faltan {sorted(esperados - cubiertos)}; sobran {sorted(cubiertos - esperados)}"
    )


def test_matriz_espana_es_eur_y_con_rangos_validos():
    filas = _filas_matriz_espana()
    assert filas, "La matriz ES está vacía"
    for f in filas:
        assert f["pais_codigo"] == "ES"
        assert f["moneda"] == "EUR"
        precio = float(f["precio_referencia"])
        minimo = float(f["precio_min"])
        maximo = float(f["precio_max"])
        assert precio > 0, f"{f['codigo_recurso']} sin precio"
        assert 0 < minimo <= precio <= maximo, f"Rango inválido en {f['codigo_recurso']}"


def test_matriz_espana_mano_obra_en_euros_de_mercado():
    filas = {f["codigo_recurso"]: f for f in _filas_matriz_espana()}
    oficial = float(filas["MO-OF1"]["precio_referencia"])
    peon = float(filas["MO-AYU"]["precio_referencia"])
    # Coste empresa España 2026 (revisión 2026-08-25): oficial ~18-25 €/h (20.50 medio), peón ~12-18 €/h (15 medio).
    # Antes era tarifa autónomo con beneficio 22-32/15-21 y daba doble margen.
    assert 17 <= oficial <= 26, f"Oficial fuera de rango coste empresa ES: {oficial}"
    assert 11 <= peon <= 19, f"Peón fuera de rango coste empresa ES: {peon}"
    assert oficial > peon


def test_matriz_espana_tiene_referencias_y_derivadas():
    filas = _filas_matriz_espana()
    confianzas = {f["confianza"] for f in filas}
    assert "referencia" in confianzas, "No hay anclas observadas"
    assert "derivado" in confianzas, "No hay canasta derivada"
    # Sin filas pendientes: la matriz es carga completa.
    assert all(f["confianza"] in ("referencia", "derivado") for f in filas)


# ---------------------------------------------------------------------------
# Configuración y onboarding de una empresa española
# ---------------------------------------------------------------------------

def test_configuracion_guarda_espana_eur_nif(entorno, cliente_web):
    from app.models import Configuracion
    from datetime import date

    Session, _ids, _rol = entorno
    resp = cliente_web.post(
        "/configuracion",
        data={
            "empresa_nombre": "Reformas Ibérica S.L.",
            "empresa_pais": "España",
            "moneda_default": "EUR",
            "etiqueta_id_fiscal": "NIF",
            "iva_default": "21",
            "tasa_cambio": "0.8564",
            "fecha_tasa": "2026-08-22",
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    with Session() as db:
        cfg = db.query(Configuracion).first()
        assert cfg.empresa_pais == "España"
        assert cfg.moneda_default == "EUR"
        assert cfg.etiqueta_id_fiscal == "NIF"
        assert cfg.iva_default == pytest.approx(21)
        assert cfg.tasa_cambio == pytest.approx(0.8564)
        assert cfg.fecha_tasa == date(2026, 8, 22)


def test_bienvenida_espana_habla_espanol(entorno, cliente_web):
    """El wizard de alta adapta NIF, teléfono +34, S.L., Madrid y EUR."""
    from app.models import Configuracion

    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "España"
        cfg.etiqueta_id_fiscal = "NIF"
        cfg.moneda_default = "EUR"
        cfg.iva_default = 21
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida")
    assert resp.status_code == 200
    assert "NIF" in resp.text
    assert "B12345678" in resp.text
    assert "+34 600 000 000" in resp.text
    assert "S.L." in resp.text
    assert "Madrid" in resp.text
    # Tasa verificada EUR del servidor, visible en el wizard
    assert "0.8564" in resp.text


def test_partidas_se_muestran_en_espanol_y_en_eur(entorno, cliente_web):
    """Con empresa_pais=España, el catálogo base VE se muestra con
    terminología peninsular (concreto→hormigón, friso→enfoscado) y los
    importes convertidos a EUR con la tasa configurada."""
    from app.models import Configuracion, Partida

    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "España"
        cfg.etiqueta_id_fiscal = "NIF"
        cfg.moneda_default = "EUR"
        cfg.iva_default = 21
        cfg.tasa_cambio = 0.8564
        p = db.query(Partida).first()
        p.nombre = "Vaciado de concreto con friso"
        p.descripcion = "Concreto premezclado y friso maestreado"
        p.categoria = "05 Estructura"
        p.subcategoria = "05.01 Concreto"
        p.apartado = "Obra"
        p.precio_unitario = 120.0
        db.commit()
        partida_id = p.id
    resp = cliente_web.get(
        "/partidas/api/filas",
        params={"categoria": "05 Estructura", "subcategoria": "05.01 Concreto"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] and data["partidas"]
    fila = next((x for x in data["partidas"] if x["id"] == partida_id), None)
    assert fila is not None
    # Terminología peninsular al mostrar, sin reescribir la base
    assert "hormigón" in fila["nombre"].lower()
    assert "enfoscado" in fila["nombre"].lower()
    assert "concreto" not in fila["nombre"].lower()
    # Importes en EUR con la tasa configurada (120 USD × 0,8564 = 102,768,
    # cuantizado a los 2 decimales del euro)
    assert fila["precio"] == pytest.approx(round(120.0 * 0.8564, 2), abs=1e-9)


def test_pais_de_nombre_espana_en_plantillas():
    """`pais_de_nombre('España')` expone EUR/21/NIF a los formularios."""
    from app.routers.common import _pais_de_nombre

    d = _pais_de_nombre("España")
    assert d["moneda"] == "EUR"
    assert d["iva"] == 21
    assert d["id_fiscal"] == "NIF"


def test_sql_de_carga_espana_generado():
    ruta = RAIZ / "docs" / "cargar_precios_referencia_espana_2026-08-25.sql"
    assert ruta.is_file(), "Falta el SQL de carga ES; ejecutar tools/generar_sql_precios_espana.py"
    texto = ruta.read_text(encoding="utf-8")
    assert "ES" in texto
    assert "EUR" in texto
    # No debe tocar referencias de otros países ni overrides de empresa.
    assert "organizacion_id IS NULL" in texto
