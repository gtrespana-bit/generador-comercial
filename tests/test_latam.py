"""LatAm — país, moneda, IVA, ID fiscal y traducción (Semanas 1-2 del plan).

Regresiones del bloque de expansión regional: catálogo de países, moneda
libre con alias Bs→VES, etiqueta fiscal dinámica (RIF/NIT/RUC/RFC…),
traducción de terminología VE→CO/MX/EC/PE, tasa de referencia USD→local,
landing adaptativa con subdirectorios SEO y PDF con textos genéricos.
"""
from __future__ import annotations

import json
import re
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import paises
from app.database import Base
from app.models import (
    Capitulo,
    CategoriaPartida,
    Cliente,
    Configuracion,
    Partida,
    Presupuesto,
    PresupuestoItem,
)
from app.services.tasa import (
    factor_conversion_local,
    obtener_tasa_api,
    tasa_convertir_precio,
    tasa_sugerida,
)
from app.services.traduccion import codigo_desde_pais, traducir, traducir_partida
from app.utils import (
    MONEDAS_SOPORTADAS,
    SIMBOLOS,
    es_moneda_soportada,
    fmt_monto,
    normalizar_moneda,
)


# ---------------------------------------------------------------------------
# app/paises.py — catálogo de países
# ---------------------------------------------------------------------------

def test_selector_expone_los_5_paises_foco_en_orden():
    codigos = [p["codigo"] for p in paises.lista_paises()]
    assert codigos == ["VE", "CO", "MX", "EC", "PE"]


def test_defaults_colombia_sugieren_nit_cop_19():
    d = paises.defaults_para_pais("CO")
    assert d["moneda"] == "COP"
    assert d["iva"] == 19
    assert d["id_fiscal"] == "NIT"
    assert d["nombre"] == "Colombia"


def test_defaults_pais_invalido_cae_a_generico():
    d = paises.defaults_para_pais("ZZ")
    assert d["codigo"] == ""
    assert d["moneda"] == "USD"
    assert d["nombre"] == "Latinoamérica"


def test_obtener_pais_normaliza_minusculas():
    assert paises.obtener_pais("co")["nombre"] == "Colombia"
    assert paises.obtener_pais("") is None
    assert paises.obtener_pais(None) is None


def test_ejemplos_de_formulario_por_pais():
    """Cada país trae sus propios placeholders: ID fiscal, teléfono,
    forma legal y ciudad. Nada de ejemplos venezolanos fuera de VE."""
    d = paises.defaults_para_pais("CO")
    assert d["id_fiscal_placeholder"] == "900.123.456-7"
    assert d["telefono_ejemplo"] == "+57 300 000 0000"
    assert d["razon_social_ejemplo"] == "S.A.S."
    assert d["ciudad_ejemplo"] == "Bogotá"

    mx = paises.defaults_para_pais("MX")
    assert mx["id_fiscal_placeholder"] == "AAA010101AAA"
    assert mx["telefono_ejemplo"].startswith("+52")

    pe = paises.defaults_para_pais("PE")
    assert pe["razon_social_ejemplo"] == "S.A.C."
    assert pe["telefono_ejemplo"].startswith("+51")

    ve = paises.defaults_para_pais("VE")
    assert ve["id_fiscal_placeholder"] == "J-12345678-9"


def test_ejemplos_generico_sin_pais():
    d = paises.defaults_para_pais(None)
    assert d["id_fiscal"] == "ID fiscal"
    assert not d["ciudad_ejemplo"]


# ---------------------------------------------------------------------------
# app/utils.py — monedas libres (20 ISOs)
# ---------------------------------------------------------------------------

def test_normalizar_moneda_alias_bs_a_ves():
    assert normalizar_moneda("Bs") == "VES"
    assert normalizar_moneda("bs") == "VES"
    assert normalizar_moneda("COP") == "COP"
    assert normalizar_moneda("XXX", "USD") == "USD"
    assert normalizar_moneda(None) == "USD"


def test_catalogo_simbolos_latam():
    assert SIMBOLOS["COP"] == "$"
    assert SIMBOLOS["PEN"] == "S/"
    assert SIMBOLOS["VES"] == "Bs"
    assert SIMBOLOS["MXN"] == "$"
    assert SIMBOLOS["GTQ"] == "Q"
    assert SIMBOLOS["CRC"] == "₡"
    assert "COP" in MONEDAS_SOPORTADAS and "MXN" in MONEDAS_SOPORTADAS


def test_fmt_monto_moneda_local():
    assert fmt_monto(4200000, "COP").endswith("$")
    assert "S/" in fmt_monto(3750, "PEN")
    assert fmt_monto(100, "Bs") == fmt_monto(100, "VES")


def test_es_moneda_soportada():
    assert es_moneda_soportada("COP")
    assert es_moneda_soportada("Bs")
    assert not es_moneda_soportada("XXX")


# ---------------------------------------------------------------------------
# app/services/traduccion.py — glosarios VE→país
# ---------------------------------------------------------------------------

def test_traduccion_friso_a_panete_colombia():
    assert traducir("Friso de mortero", "CO") == "Pañete de mortero"


def test_traduccion_categorias_y_subcategorias():
    """Las categorías del catálogo también se traducen, con plurales y
    concordancias correctas por país."""
    # Capítulos y categorías
    assert traducir("Fundaciones", "CO") == "Cimentaciones"
    assert traducir("Fundaciones", "PE") == "Cimentaciones"
    assert traducir("Techos y cubiertas", "CO") == "Cubiertas"
    assert traducir("Techos y cubiertas", "EC") == "Cubiertas"
    assert traducir("Techos y cubiertas", "MX") == "Techos y cubiertas"
    # Subcategorías con terminología local
    assert traducir("Frisos, enlucidos y revestimientos de mortero", "CO") == "Pañetes, enlucidos y revestimientos de mortero"
    assert traducir("Frisos, enlucidos y revestimientos de mortero", "EC") == "Enlucidos y revestimientos de mortero"
    assert traducir("Aceras, brocales, rampas y escaleras exteriores", "CO") == "Andenes, sardineles, rampas y escaleras exteriores"
    assert traducir("Aceras, brocales, rampas y escaleras exteriores", "MX") == "Banquetas, guarniciones, rampas y escaleras exteriores"
    assert traducir("Aceras, brocales, rampas y escaleras exteriores", "PE") == "Veredas, sardineles, rampas y escaleras exteriores"
    assert traducir("Desagüe sanitario y aguas pluviales", "MX") == "Drenaje sanitario y aguas pluviales"
    assert traducir("Desagüe sanitario y aguas pluviales", "EC") == "Desagüe sanitario y aguas lluvias"
    # Plurales con acentos y concordancias
    assert traducir("Concreto estructural vaciado en sitio", "CO") == "Concreto estructural fundido en sitio"
    assert traducir("Concreto estructural vaciado en sitio", "EC") == "Hormigón estructural fundido en sitio"
    assert traducir("Paredes de bloque de arcilla", "CO") == "Muros en bloque de arcilla"
    assert traducir("Closets, alacenas y almacenamiento fijo", "CO") == "Clósets, alacenas y almacenamiento fijo"
    assert traducir("Cielos rasos continuos", "MX") == "Plafones continuos"
    assert traducir("Particiones de yeso laminado y sistemas secos", "MX") == "Particiones de tablaroca y sistemas secos"


def test_traduccion_respeta_mayuscula_inicial():
    assert traducir("friso", "CO") == "pañete"


def test_traduccion_plural_es():
    assert traducir("Frisos", "CO") == "Pañetes"


def test_traduccion_venezuela_y_vacio_devuelven_original():
    assert traducir("Friso", "VE") == "Friso"
    assert traducir("Friso", None) == "Friso"
    assert traducir("Friso", "") == "Friso"


def test_codigo_desde_pais():
    assert codigo_desde_pais("Colombia") == "CO"
    assert codigo_desde_pais("México") == "MX"
    assert codigo_desde_pais("perú") == "PE"
    assert codigo_desde_pais("Venezuela") == "VE"
    assert codigo_desde_pais("Atlántida") == ""


def test_traducir_partida_no_muta_el_original():
    p = PresupuestoItem(nombre="Friso de mortero", descripcion="Friso fino")
    copia = traducir_partida(p, "CO")
    assert p.nombre == "Friso de mortero"
    assert copia.nombre == "Pañete de mortero"
    assert copia is not p


# ---------------------------------------------------------------------------
# app/services/tasa.py — tasa de referencia USD→local
# ---------------------------------------------------------------------------

def test_tasa_convertir_precio():
    assert tasa_convertir_precio(100, 4200) == 420000.0
    assert tasa_convertir_precio(100, None) == 100.0
    assert tasa_convertir_precio(100, 0) == 100.0


def test_tasa_sugerida_solo_valores_verificados():
    # Tasas verificadas el día de la actualización (TASAS_ACTUALIZADAS)
    assert tasa_sugerida("COP") == pytest.approx(3128.65)  # TRM oficial 19/08/2026
    assert tasa_sugerida("VES") == pytest.approx(773.31)   # BCV oficial 18/08/2026
    assert tasa_sugerida("MXN") == pytest.approx(17.06)    # mercado 18/08/2026
    assert tasa_sugerida("PEN") == pytest.approx(3.37)     # SUNAT 12/08/2026
    assert tasa_sugerida("USD") == 1.0
    assert tasa_sugerida("PAB") == 1.0
    assert tasa_sugerida("Bs") == tasa_sugerida("VES")


def test_tasa_sugerida_sin_verificacion_devuelve_none():
    """Nunca se pre-rellena una tasa no verificada: el usuario consulta
    «Tasa de hoy» o escribe la oficial."""
    assert tasa_sugerida("CLP") is None
    assert tasa_sugerida("ARS") is None
    assert tasa_sugerida("XXX") is None


def test_obtener_tasa_api_usd_no_requiere_red():
    tasa, error = obtener_tasa_api("USD")
    assert tasa == 1.0
    assert error is None


def test_factor_conversion_local():
    assert factor_conversion_local("COP", 3128.65) == pytest.approx(3128.65)
    assert factor_conversion_local("Bs", 773.31) == pytest.approx(773.31)
    assert factor_conversion_local("USD", 4200) == 1.0
    assert factor_conversion_local("PAB", 3.0) == 1.0
    assert factor_conversion_local("", 3.0) == 1.0
    assert factor_conversion_local("COP", None) == 1.0
    assert factor_conversion_local("COP", 0) == 1.0


# ---------------------------------------------------------------------------
# Landing adaptativa (público)
# ---------------------------------------------------------------------------

def test_landing_generica_habla_de_latinoamerica(cliente_web):
    resp = cliente_web.get("/")
    assert resp.status_code == 200
    assert "Latinoamérica" in resp.text
    assert 'id="pais-select"' in resp.text
    assert 'rel="canonical" href="https://cotizat.test/"' in resp.text


def test_landing_subdirectorio_colombia(cliente_web):
    resp = cliente_web.get("/co/", follow_redirects=False)
    assert resp.status_code == 200
    assert "Colombia" in resp.text
    assert "NIT" in resp.text
    assert "cotizat_pais=CO" in resp.headers["set-cookie"]


def test_landing_query_pais_redirige_al_subdirectorio(cliente_web):
    resp = cliente_web.get("/?pais=MX", follow_redirects=False)
    assert resp.status_code == 301
    assert resp.headers["location"] == "/mx/"


def test_landing_pais_invalido_ignora_el_parametro(cliente_web):
    resp = cliente_web.get("/?pais=ZZ", follow_redirects=False)
    assert resp.status_code == 200
    assert "Latinoamérica" in resp.text


def test_sitemap_incluye_subdirectorios_de_pais(cliente_web):
    resp = cliente_web.get("/sitemap.xml")
    assert resp.status_code == 200
    for u in ("/ve/", "/co/", "/mx/", "/ec/", "/pe/"):
        assert u in resp.text


# ---------------------------------------------------------------------------
# Configuración por tenant: moneda, IVA, etiqueta fiscal y tasa
# ---------------------------------------------------------------------------

def test_configuracion_guarda_moneda_cop_etiqueta_nit_y_tasa(entorno, cliente_web):
    Session, _ids, _rol = entorno
    resp = cliente_web.post(
        "/configuracion",
        data={
            "empresa_nombre": "Constructora Restaurada",
            "empresa_pais": "Colombia",
            "moneda_default": "COP",
            "etiqueta_id_fiscal": "NIT",
            "iva_default": "19",
            "tasa_cambio": "4200",
            "fecha_tasa": "2026-08-19",
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    with Session() as db:
        cfg = db.query(Configuracion).first()
        assert cfg.moneda_default == "COP"
        assert cfg.etiqueta_id_fiscal == "NIT"
        assert cfg.iva_default == pytest.approx(19)
        assert cfg.tasa_cambio == pytest.approx(4200)
        assert cfg.fecha_tasa == date(2026, 8, 19)


def test_configuracion_rechaza_moneda_desconocida(entorno, cliente_web):
    Session, _ids, _rol = entorno
    cliente_web.post(
        "/configuracion",
        data={"empresa_nombre": "X", "moneda_default": "XXX"},
        follow_redirects=False,
    )
    with Session() as db:
        cfg = db.query(Configuracion).first()
        assert cfg.moneda_default == "USD"


# ---------------------------------------------------------------------------
# Formularios adaptados al país: onboarding y configuración
# ---------------------------------------------------------------------------

def test_bienvenida_colombia_habla_colombiano(entorno, cliente_web):
    """El wizard de alta de empresa adapta etiqueta, teléfono, forma legal
    y tasa al país configurado — sin ejemplos venezolanos."""
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        cfg.etiqueta_id_fiscal = "NIT"
        cfg.moneda_default = "COP"
        cfg.iva_default = 19
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida")
    assert resp.status_code == 200
    # Etiqueta del ID fiscal colombiano y su formato de ejemplo
    assert "NIT" in resp.text
    assert "900.123.456-7" in resp.text
    # Ejemplos locales: teléfono +57, forma legal S.A.S., ciudad Bogotá
    assert "+57 300 000 0000" in resp.text
    assert "S.A.S." in resp.text
    assert "Bogotá" in resp.text
    # Tasa verificada del servidor (TRM oficial), no la antigua de 4200
    assert "3128.65" in resp.text
    # Ningún placeholder venezolano renderizado (el JSON del selector sí
    # incluye los datos de VE para poder volver a elegirlo)
    assert 'placeholder="+58 412 000 0000"' not in resp.text
    assert 'placeholder="J-12345678-9"' not in resp.text


def test_bienvenida_venezuela_conserva_sus_ejemplos(entorno, cliente_web):
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Venezuela"
        cfg.etiqueta_id_fiscal = "RIF"
        cfg.moneda_default = "USD"
        cfg.onboarding_completado = False
        db.commit()
    resp = cliente_web.get("/bienvenida")
    assert resp.status_code == 200
    assert "RIF" in resp.text
    assert "+58 412 000 0000" in resp.text


def test_configuracion_colombia_adapta_los_campos(entorno, cliente_web):
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        cfg.etiqueta_id_fiscal = "NIT"
        cfg.moneda_default = "COP"
        db.commit()
    resp = cliente_web.get("/configuracion")
    assert resp.status_code == 200
    assert "900.123.456-7" in resp.text          # placeholder del NIT
    assert "+57 300 000 0000" in resp.text       # teléfono colombiano
    assert "S.A.S." in resp.text                 # forma legal colombiana
    assert "3128.65" in resp.text                # TRM verificada en el JSON
    assert 'placeholder="+58' not in resp.text   # sin teléfono venezolano renderizado
    assert 'placeholder="J-XXXXXXXX-X"' not in resp.text


# ---------------------------------------------------------------------------
# Detalle del presupuesto: etiqueta y tasa genéricas
# ---------------------------------------------------------------------------

def test_detalle_presupuesto_muestra_etiqueta_y_tasa_genericas(entorno, cliente_web):
    Session, ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.etiqueta_id_fiscal = "NIT"
        cfg.moneda_default = "COP"
        cfg.tasa_cambio = 4200.0
        presupuesto = db.get(Presupuesto, ids[2])
        presupuesto.tipo_cambio = 4200.0
        db.commit()
    resp = cliente_web.get(f"/presupuestos/{ids[2]}")
    assert resp.status_code == 200
    assert "NIT:" in resp.text
    assert "RIF/C.I." not in resp.text
    assert "(1 USD = 4.200,00 COP)" in resp.text


# ---------------------------------------------------------------------------
# PDF: etiqueta fiscal dinámica, tasa genérica y terminología traducida
# ---------------------------------------------------------------------------

def test_pdf_latam_usa_etiqueta_tasa_y_terminologia_del_pais():
    import io

    from pypdf import PdfReader

    from app.services import pdf as pdf_service

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        cfg = Configuracion(
            empresa_nombre="Andina SAS",
            empresa_rif="900123456-7",
            etiqueta_id_fiscal="NIT",
            empresa_pais="Colombia",
            moneda_default="COP",
            tasa_cambio=4200.0,
            fecha_tasa=date(2026, 8, 19),
            mostrar_tasa_cambio=True,
            mostrar_total_bs=True,
        )
        cliente = Cliente(nombre="Cliente CO", rif="901000222-3")
        db.add_all([cfg, cliente])
        db.flush()
        presu = Presupuesto(
            numero="P-CO-1",
            year=2026,
            fecha=date.today(),
            client_id=cliente.id,
            impuesto_pct=19,
            moneda="COP",
            tipo_cambio=4200.0,
            fecha_tipo_cambio=date(2026, 8, 19),
        )
        cap = Capitulo(nombre="Friso de muros", orden=1)
        cap.partidas.append(
            PresupuestoItem(
                nombre="Friso de mortero",
                unidad="m2",
                cantidad=10,
                precio_unitario=4200,
                orden=1,
            )
        )
        presu.capitulos.append(cap)
        db.add(presu)
        db.commit()
        db.refresh(presu)

        data = pdf_service.generar_pdf(presu, cfg).getvalue()
        assert data.startswith(b"%PDF")
        texto = "\n".join(
            (pagina.extract_text() or "") for pagina in PdfReader(io.BytesIO(data)).pages
        )
        # Etiqueta fiscal dinámica (empresa y cliente) — nada de RIF hardcodeado
        assert "NIT: 900123456-7" in texto
        assert "NIT: 901000222-3" in texto
        assert "RIF" not in texto
        # Tasa genérica sin BCV ni Bs
        assert "Tasa de referencia: 1 USD = 4.200,00 COP" in texto
        assert "BCV" not in texto
        # Terminología traducida al vuelo (VE friso → CO pañete)
        assert "PAÑETE DE MUROS" in texto
        assert "Pañete de mortero" in texto
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Catálogo: categorías traducidas y beneficio SIEMPRE en la misma moneda
# ---------------------------------------------------------------------------

TASA_COP = 3128.65


def _poner_org_colombia_y_partida(Session, *, precio=12.0, costes=(8.0, 2.0, 0.0, 0.0)):
    """Configura la organización del fixture en COP/Colombia y deja la
    partida de prueba con categoría venezolana y costes conocidos (USD)."""
    from app.models import Partida as _Partida

    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        cfg.etiqueta_id_fiscal = "NIT"
        cfg.moneda_default = "COP"
        cfg.iva_default = 19
        cfg.tasa_cambio = TASA_COP
        p = db.query(_Partida).first()
        p.nombre = "Friso de mortero"
        p.descripcion = "Friso fino sobre muro"
        p.categoria = "04 Fundaciones"
        p.subcategoria = "04.04 Losas de fundación"
        p.apartado = "Obra"
        p.precio_unitario = precio
        p.coste_materiales, p.coste_mano_obra, p.coste_complementarios, p.coste_otros = costes
        db.commit()
        return p.id


def test_filas_api_convierte_precio_y_costes_con_el_mismo_factor(entorno, cliente_web):
    """El JSON de las filas no puede traer precio en COP y costes en USD:
    el margen se calcularía mezclando monedas."""
    Session, _ids, _rol = entorno
    partida_id = _poner_org_colombia_y_partida(Session)
    resp = cliente_web.get(
        "/partidas/api/filas",
        params={"categoria": "04 Fundaciones", "subcategoria": "04.04 Losas de fundación"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] and data["partidas"]
    fila = next((p for p in data["partidas"] if p["id"] == partida_id), None)
    assert fila is not None
    # Todo convertido con el MISMO factor 3128.65
    assert fila["precio"] == pytest.approx(12.0 * TASA_COP, rel=1e-6)
    assert fila["coste_materiales"] == pytest.approx(8.0 * TASA_COP, rel=1e-6)
    assert fila["coste_mano_obra"] == pytest.approx(2.0 * TASA_COP, rel=1e-6)
    # Margen coherente: (12-10)*3128.65 = 6.257,30 COP -> +20% s/coste
    coste_total = fila["coste_materiales"] + fila["coste_mano_obra"]
    margen = fila["precio"] - coste_total
    assert margen == pytest.approx(2.0 * TASA_COP, rel=1e-6)
    assert margen / coste_total == pytest.approx(0.20, rel=1e-6)
    # Categorías traducidas
    assert fila["nombre"] == "Pañete de mortero"
    assert fila["categoria"] == "04 Cimentaciones"
    assert fila["subcategoria"] == "04.04 Placas de cimentación"


def test_listado_partidas_busqueda_muestra_margen_coherente_y_categorias_traducidas(entorno, cliente_web):
    """La búsqueda renderiza las filas en el servidor: precio y costes deben
    estar en COP (margen 50% -> +6.257,30, no cientos de miles), y los
    encabezados de grupo traducidos (Cimentaciones, no Fundaciones)."""
    Session, _ids, _rol = entorno
    _poner_org_colombia_y_partida(Session)
    resp = cliente_web.get("/partidas?q=friso")
    assert resp.status_code == 200
    texto = resp.text
    # Precio 12 USD -> 37.543,80 COP; coste 10 USD -> 31.286,50; margen 6.257,30 (+20%)
    assert "37.543,80" in texto
    assert "31.286,50" in texto
    assert "6.257,30" in texto
    assert "20.0%" in texto
    # Nunca el absurdo de COP - USD (~37.512,30 con markup del 119.800%)
    assert "119" not in texto
    # Encabezado de grupo traducido
    assert "Cimentaciones" in texto
    assert "Pañete de mortero" in texto


def test_arbol_categorias_traduce_etiquetas_sin_romper_claves(entorno, cliente_web):
    """El árbol lateral muestra la etiqueta traducida pero conserva la clave
    cruda en data-cat/enlaces para que los filtros sigan funcionando."""
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        db.add(CategoriaPartida(
            categoria="11 Techos y cubiertas", subcategoria="", nivel=1,
            oficial=True, activa=True, codigo_completo="11",
        ))
        db.flush()
        padre_id = db.query(CategoriaPartida).filter(
            CategoriaPartida.categoria == "11 Techos y cubiertas",
            CategoriaPartida.nivel == 1,
        ).first().id
        db.add(CategoriaPartida(
            categoria="11 Techos y cubiertas",
            subcategoria="11.02 Cubiertas planas transitables y no transitables",
            nivel=2, parent_id=padre_id, oficial=True, activa=True,
            codigo_completo="11.02",
        ))
        db.commit()
    resp = cliente_web.get("/partidas")
    assert resp.status_code == 200
    texto = resp.text
    # Etiqueta visible traducida (techo->cubierta hace «Cubiertas», no duplicado)
    assert "Cubiertas" in texto
    # La clave cruda se conserva para los filtros/enlaces
    assert 'data-cat="11 Techos y cubiertas"' in texto
    assert "/partidas?categoria=11%20Techos%20y%20cubiertas" in texto


def test_editor_indice_en_moneda_y_terminologia_del_presupuesto(entorno, cliente_web):
    """El catálogo embebido del editor de presupuestos llega en la moneda del
    presupuesto (COP) con costes convertidos y categorías traducidas, para
    que el beneficio por partida sea coherente."""
    Session, _ids, _rol = entorno
    partida_id = _poner_org_colombia_y_partida(Session)
    resp = cliente_web.get("/presupuestos/nuevo")
    assert resp.status_code == 200
    m = re.search(
        r'<script nonce="[^"]*" id="datos-catalogo" type="application/json">(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    assert m is not None
    catalogo = json.loads(m.group(1))
    item = next((p for p in catalogo if p["id"] == partida_id), None)
    assert item is not None
    assert item["precio"] == pytest.approx(12.0 * TASA_COP, rel=1e-6)
    assert item["coste_materiales"] == pytest.approx(8.0 * TASA_COP, rel=1e-6)
    assert item["coste_mano_obra"] == pytest.approx(2.0 * TASA_COP, rel=1e-6)
    assert item["categoria"] == "04 Cimentaciones"
    assert item["nombre"] == "Pañete de mortero"


def test_editor_indice_presupuesto_usd_no_convierte(entorno, cliente_web):
    """Un presupuesto en USD recibe el catálogo en USD aunque la org tenga
    COP configurado por defecto."""
    Session, ids, _rol = entorno
    partida_id = _poner_org_colombia_y_partida(Session)
    with Session() as db:
        presupuesto = db.get(Presupuesto, ids[2])
        presupuesto.moneda = "USD"
        presupuesto.tipo_cambio = None
        db.commit()
    resp = cliente_web.get(f"/presupuestos/{ids[2]}/editar")
    assert resp.status_code == 200
    m = re.search(
        r'<script nonce="[^"]*" id="datos-catalogo" type="application/json">(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    assert m is not None
    catalogo = json.loads(m.group(1))
    item = next((p for p in catalogo if p["id"] == partida_id), None)
    assert item is not None
    assert item["precio"] == pytest.approx(12.0, rel=1e-6)
    assert item["coste_materiales"] == pytest.approx(8.0, rel=1e-6)
    # La terminología sí se traduce (país de la organización)
    assert item["nombre"] == "Pañete de mortero"
