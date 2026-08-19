"""LatAm — país, moneda, IVA, ID fiscal y traducción (Semanas 1-2 del plan).

Regresiones del bloque de expansión regional: catálogo de países, moneda
libre con alias Bs→VES, etiqueta fiscal dinámica (RIF/NIT/RUC/RFC…),
traducción de terminología VE→CO/MX/EC/PE, tasa de referencia USD→local,
landing adaptativa con subdirectorios SEO y PDF con textos genéricos.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import paises
from app.database import Base
from app.models import Capitulo, Cliente, Configuracion, Presupuesto, PresupuestoItem
from app.services.tasa import obtener_tasa_api, tasa_convertir_precio, tasa_sugerida
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


def test_tasa_sugerida():
    assert tasa_sugerida("COP") == 4200.0
    assert tasa_sugerida("USD") == 1.0
    assert tasa_sugerida("Bs") == tasa_sugerida("VES")


def test_obtener_tasa_api_usd_no_requiere_red():
    tasa, error = obtener_tasa_api("USD")
    assert tasa == 1.0
    assert error is None


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
