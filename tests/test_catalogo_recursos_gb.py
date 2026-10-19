"""Regresiones de catálogo y Recursos en inglés británico / mercado GB."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode

import pytest

from app.models import Configuracion, Partida, PrecioRecursoMercado, Recurso
from app.paises import PAISES
from app.services.precios_mercado import guardar_precio
from app.services.traduccion import traducir

CODIGO_RECURSO = "MT-ADH-C2TE"
DESCRIPCION_RECURSO = (
    "Adhesivo cementoso mejorado tipo C2 TE, de deslizamiento reducido y "
    "tiempo abierto ampliado, para colocación de porcelanato en capa fina."
)
DESCRIPCION_PERSONALIZADA = "Adhesive selected by the client for this elevation"
TASA_USD_GBP = 0.7502
PRECIO_MERCADO_GBP = 2.50


def _preparar_gb(Session):
    """Carga una referencia GBP y una partida con APU sobre la base USD."""
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = PAISES["GB"]["nombre"]
        cfg.moneda_default = "GBP"
        cfg.tasa_cambio = TASA_USD_GBP

        recurso = Recurso(
            codigo=CODIGO_RECURSO,
            descripcion=DESCRIPCION_RECURSO,
            unidad="kg",
            categoria="materiales",
            precio=0.32,
            moneda="USD",
        )
        db.add(recurso)
        db.flush()
        guardar_precio(
            db,
            recurso.id,
            "GB",
            PRECIO_MERCADO_GBP,
            "GBP",
            fuente="Prueba GB",
            confianza="confirmado",
        )

        coste_base_usd = 0.32 * 2
        partida = Partida(
            nombre="Adhesivo cementoso de prueba",
            descripcion="Descripción técnica original de prueba",
            unidad="m²",
            categoria="Revestimientos",
            subcategoria="Adhesivos",
            apartado="Adhesivo para porcelanato",
            precio_unitario=round(coste_base_usd * 1.35, 4),
            coste_materiales=coste_base_usd,
            coste_mano_obra=0,
            coste_complementarios=0,
            coste_otros=0,
            descomposicion_json=json.dumps({
                "origen": "manual",
                "codigo": "GB-TEST-01",
                "unidad": "m²",
                "filas": [{
                    "tipo": "recurso",
                    "categoria": "materiales",
                    "grupo": "Materiales",
                    "codigo": CODIGO_RECURSO,
                    "descripcion": DESCRIPCION_PERSONALIZADA,
                    "unidad": "kg",
                    "rendimiento": 2,
                    "precio": 0.32,
                    "precio_unitario": 0.32,
                    "importe": 0.64,
                }],
            }, ensure_ascii=False),
        )
        db.add(partida)
        db.commit()
        return partida.id, recurso.id


def _filas_editor(html_form: str) -> list[dict]:
    match = re.search(
        r'<script[^>]*data-partida-editor-inicial[^>]*>(.*?)</script>',
        html_form,
        re.DOTALL,
    )
    assert match, "No se encontró el estado inicial del APU en el formulario"
    valor = json.loads(html.unescape(match.group(1)))
    if isinstance(valor, str):
        valor = json.loads(valor)
    return valor.get("filas", []) if isinstance(valor, dict) else valor


def test_recursos_en_ruta_inglesa_localiza_lista_formulario_y_categorias(
    entorno, cliente_web,
):
    Session, _ids, _rol = entorno
    _partida_id, recurso_id = _preparar_gb(Session)

    lista = cliente_web.get("/en/recursos")
    assert lista.status_code == 200
    assert "Unit Prices" in lista.text
    assert "Materials" in lista.text
    assert "Labour" in lista.text
    assert "2.50 GBP" in lista.text
    assert "Mano de obra" not in lista.text
    assert "materiales →" not in lista.text
    assert 'name="precio_mercado"' not in lista.text

    # El prefijo fija la cookie; las mismas pantallas deben seguir en inglés
    # al navegar luego por las rutas internas sin prefijo.
    for ruta in (
        "/en/recursos/nuevo",
        f"/en/recursos/{recurso_id}/editar",
        "/recursos/nuevo",
        f"/recursos/{recurso_id}/editar",
    ):
        formulario = cliente_web.get(ruta)
        assert formulario.status_code == 200
        assert "New Resource" in formulario.text or "Edit Resource" in formulario.text
        assert "Category" in formulario.text
        assert "Materials" in formulario.text
        assert "Labour" in formulario.text
        if ruta.endswith("/editar"):
            assert "2.50 GBP" in formulario.text
        assert "Categoría" not in formulario.text
        assert "Mano de obra" not in formulario.text
        assert "Code (optional) *" not in formulario.text
        assert "Code (optional)" in formulario.text


def test_catalogo_muestra_breakdown_y_lista_editor_api_coinciden_en_gbp(
    entorno, cliente_web,
):
    Session, _ids, _rol = entorno
    partida_id, _recurso_id = _preparar_gb(Session)

    lista = cliente_web.get(
        "/en/partidas",
        params={"q": "Adhesivo cementoso de prueba"},
    )
    assert lista.status_code == 200
    assert 'data-label="Catalog"' in lista.text
    assert lista.text.count("<span>Catalog</span>") >= 2
    assert 'data-label="Line Item Catalog"' not in lista.text
    assert 'class="descomp-details"' in lista.text
    assert "Breakdown (1 resources)" in lista.text
    assert "6.75 GBP" in lista.text

    editor = cliente_web.get(f"/en/partidas/{partida_id}/editar")
    assert editor.status_code == 200
    assert "Unit price analysis" in editor.text
    assert "Productivity" in editor.text
    assert "Labour" in editor.text
    assert "Descomposición" not in editor.text
    precio_editor = re.search(
        r'name="precio_unitario"[^>]*value="([^"]+)"', editor.text
    )
    assert precio_editor, "El editor no muestra el precio de venta"
    assert float(precio_editor.group(1)) == pytest.approx(6.75)

    filas_editor = _filas_editor(editor.text)
    assert len(filas_editor) == 1
    assert filas_editor[0]["descripcion"] == DESCRIPCION_PERSONALIZADA
    assert filas_editor[0]["categoria_etiqueta"] == "Materials"
    assert filas_editor[0]["precio"] == pytest.approx(PRECIO_MERCADO_GBP)
    assert filas_editor[0]["importe"] == pytest.approx(5.0)

    desglose = cliente_web.get(f"/en/partidas/{partida_id}/descomposicion")
    assert desglose.status_code == 200
    datos = desglose.json()
    assert datos["moneda"] == "GBP"
    assert len(datos["filas"]) == 1
    assert datos["filas"][0]["categoria_etiqueta"] == "Materials"
    assert datos["filas"][0]["precio"] == pytest.approx(PRECIO_MERCADO_GBP)
    assert datos["filas"][0]["importe"] == pytest.approx(5.0)
    # El endpoint del resumen puede traducir por código; la ficha editable
    # conserva la descripción particular escrita para la partida.
    assert datos["filas"][0]["descripcion"] == traducir(
        DESCRIPCION_RECURSO, "GB"
    )


def test_guardar_editor_gb_sin_cambios_no_convierte_gbp_a_usd_ni_pierde_texto(
    entorno, cliente_web,
):
    Session, _ids, _rol = entorno
    partida_id, _recurso_id = _preparar_gb(Session)
    editor = cliente_web.get(f"/en/partidas/{partida_id}/editar")
    filas = _filas_editor(editor.text)
    assert filas[0]["descripcion"] == DESCRIPCION_PERSONALIZADA

    datos = [
        ("nombre", traducir("Adhesivo cementoso de prueba", "GB")),
        ("descripcion", traducir("Descripción técnica original de prueba", "GB")),
        ("unidad", "m²"),
        ("categoria", traducir("Revestimientos", "GB")),
        ("subcategoria", traducir("Adhesivos", "GB")),
        ("apartado", traducir("Adhesivo para porcelanato", "GB")),
        ("codigo_externo", "GB-TEST-01"),
        ("codigo_interno", ""),
        ("precio_unitario", "6.75"),
        ("proveedor", ""),
        ("tiempo_estimado_horas", ""),
        ("tiempo_oficial_horas", ""),
        ("tiempo_ayudante_horas", ""),
        ("tiempo_equipo_horas", ""),
        ("rendimiento", ""),
        ("desperdicio_recomendado_pct", "0"),
        ("notas_tecnicas", ""),
        ("d_categoria", "materiales"),
        ("d_codigo", CODIGO_RECURSO),
        ("d_unidad", "kg"),
        ("d_descripcion", DESCRIPCION_PERSONALIZADA),
        ("d_rendimiento", "2"),
        ("d_precio", "2.5"),
    ]
    respuesta = cliente_web.post(
        f"/en/partidas/{partida_id}/editar",
        content=urlencode(datos).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303

    with Session() as db:
        guardada = db.get(Partida, partida_id)
        assert guardada is not None
        assert guardada.precio_unitario == pytest.approx(0.864)
        assert guardada.coste_materiales == pytest.approx(0.64)
        json_guardado = json.loads(guardada.descomposicion_json)
        fila = json_guardado["filas"][0]
        assert fila["precio"] == pytest.approx(0.32)
        assert fila["importe"] == pytest.approx(0.64)
        assert fila["descripcion"] == DESCRIPCION_PERSONALIZADA
        assert fila["categoria"] == "materiales"


def test_precio_de_recurso_gb_se_guarda_con_moneda_de_mercado(entorno):
    Session, _ids, _rol = entorno
    _partida_id, recurso_id = _preparar_gb(Session)
    with Session() as db:
        precio = db.query(PrecioRecursoMercado).filter_by(
            recurso_id=recurso_id,
            pais_codigo="GB",
            organizacion_id=None,
        ).one()
        assert precio.precio == pytest.approx(PRECIO_MERCADO_GBP)
        assert precio.moneda == "GBP"


def test_crear_recurso_en_gb_guarda_el_precio_en_gbp_y_no_en_la_base_usd(
    entorno, cliente_web,
):
    Session, ids, _rol = entorno
    _preparar_gb(Session)
    datos = [
        ("codigo", "GB-CUSTOM-01"),
        ("descripcion", "Client-selected aggregate for a UK project"),
        ("unidad", "kg"),
        ("categoria", "materiales"),
        ("grupo", "Materials"),
        ("precio", "0"),
        ("precio_mercado", "2.5"),
    ]
    respuesta = cliente_web.post(
        "/en/recursos/nuevo",
        content=urlencode(datos).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303

    with Session() as db:
        recurso = db.query(Recurso).filter_by(codigo="GB-CUSTOM-01").one()
        assert recurso.precio == pytest.approx(0.0)
        assert recurso.moneda == "USD"
        referencia = db.query(PrecioRecursoMercado).filter_by(
            recurso_id=recurso.id,
            pais_codigo="GB",
            organizacion_id=ids[0],
        ).one()
        assert referencia.precio == pytest.approx(2.5)
        assert referencia.moneda == "GBP"


def test_terminologia_britanica_en_las_partidas_del_catalogo():
    """Fija tres términos de instalaciones que no pueden volver a US English."""
    ruta_catalogo = (
        Path(__file__).resolve().parents[1]
        / "basedatos_partidas"
        / "salida"
        / "catalogo_partidas.json"
    )
    filas = json.loads(ruta_catalogo.read_text(encoding="utf-8"))
    por_codigo = {fila["codigo"]: fila for fila in filas}
    esperados = {
        "09.10.01.090": "Manual fire alarm call point installation.",
        "09.17.02.020": "Repair of a socket outlet.",
        "02.07.08.050": "Removal of a built-in cooker.",
    }
    for codigo, esperado in esperados.items():
        assert traducir(por_codigo[codigo]["nombre"], "GB") == esperado
