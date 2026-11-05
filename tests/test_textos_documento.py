"""Textos del documento: heredar de Configuración o escribir unos propios.

Lo que se comprueba aquí es la promesa que se hizo al usuario en el editor:

1. Un presupuesto nuevo sigue saliendo con los textos de Configuración.
2. Al editarlo se ve qué es heredado y qué es propio.
3. Cambiar el texto de un presupuesto **no** toca Configuración.
4. Dejarlo igual que el general no lo congela: sigue heredando, así que un
   cambio futuro en Configuración llega también a ese presupuesto.
5. Vaciar los datos bancarios quita el bloque de pago sin tocar la empresa.

Las pruebas de integración van por HTTP porque el riesgo real no está en la
función pura sino en el camino completo: formulario → router → base → PDF.
"""
import json
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.textos_documento import (
    datos_bancarios_desde_formulario,
    datos_bancarios_documento,
    datos_bancarios_resumen,
    presupuesto_congelado,
    textos_documento,
    textos_para_formulario,
)

GENERAL = "Banco General\nCuenta 1234\nPago móvil 0414-0000000"
PROPIO = "Zelle: pagos@obra.example\nTitular: Obra del cliente"


def _cfg(datos_bancarios=GENERAL, notas="Notas de la empresa", condiciones="Condiciones de la empresa"):
    return SimpleNamespace(
        datos_bancarios=datos_bancarios,
        notas_default=notas,
        condiciones_default=condiciones,
    )


def _presupuesto(datos_bancarios="__sin_columna__", notas="", condiciones="", estado="borrador"):
    p = SimpleNamespace(notas=notas, condiciones=condiciones, estado=estado, versiones=[])
    if datos_bancarios != "__sin_columna__":
        p.__dict__["datos_bancarios"] = datos_bancarios
    return p


# ---------------------------------------------------------------------------
# Resolución del texto para el documento
# ---------------------------------------------------------------------------


def test_heredar_usa_los_datos_de_configuracion():
    """NULL es la herencia: es el valor de todas las filas anteriores."""
    p = _presupuesto(datos_bancarios=None)
    assert datos_bancarios_documento(p, _cfg()) == GENERAL


def test_un_texto_vacio_quita_el_bloque_de_pago_sin_tocar_la_empresa():
    """Vaciar el campo es una decisión, no una herencia."""
    p = _presupuesto(datos_bancarios="   ")
    assert datos_bancarios_documento(p, _cfg()) == ""
    assert datos_bancarios_resumen(p) == "sin datos de pago"


def test_datos_propios_ganan_a_los_de_configuracion():
    p = _presupuesto(datos_bancarios=PROPIO)
    assert datos_bancarios_documento(p, _cfg()) == PROPIO
    assert datos_bancarios_resumen(p) == "propios"


def test_un_presupuesto_sin_la_columna_no_se_inventa_datos_propios():
    """Base sin migrar: se leen los de la empresa, nunca un valor inventado."""
    p = _presupuesto()
    assert "datos_bancarios" not in p.__dict__
    assert datos_bancarios_documento(p, _cfg()) == GENERAL
    assert datos_bancarios_documento(None, _cfg()) == GENERAL


def test_la_version_congela_los_textos_resueltos():
    p = _presupuesto(datos_bancarios=PROPIO, notas="Alcance pactado", condiciones="Pago 50/50")
    textos = textos_documento(p, _cfg())
    assert textos == {
        "datos_bancarios": PROPIO,
        "notas": "Alcance pactado",
        "condiciones": "Pago 50/50",
    }


def test_el_estado_y_las_versiones_marcan_el_presupuesto_como_congelado():
    assert presupuesto_congelado(_presupuesto(estado="enviado")) is True
    assert presupuesto_congelado(_presupuesto(estado="aprobado")) is True
    assert presupuesto_congelado(_presupuesto(estado="borrador")) is False
    con_version = _presupuesto(estado="borrador")
    con_version.versiones = [object()]
    assert presupuesto_congelado(con_version) is True


# ---------------------------------------------------------------------------
# Los valores iniciales del editor
# ---------------------------------------------------------------------------


def test_el_editor_abre_con_el_texto_general_pero_marcado_como_heredado():
    """Se ve lo que va a salir en el PDF y se sabe que es prestado."""
    valores = textos_para_formulario(_presupuesto(datos_bancarios=None), _cfg())
    assert valores["datos_bancarios"] == GENERAL
    assert valores["datos_bancarios_heredados"] is True
    assert valores["datos_bancarios_eleccion"] == "heredar"
    assert valores["datos_bancarios_generales"] == GENERAL


def test_el_editor_distingue_los_tres_estados_sin_adivinar():
    """La etiqueta del campo la decide el servidor, no el navegador."""
    assert textos_para_formulario(None, _cfg())["datos_bancarios_eleccion"] == "heredar"
    assert textos_para_formulario(_presupuesto(datos_bancarios=None), _cfg())[
        "datos_bancarios_eleccion"
    ] == "heredar"
    assert textos_para_formulario(_presupuesto(datos_bancarios=PROPIO), _cfg())[
        "datos_bancarios_eleccion"
    ] == "propio"
    assert textos_para_formulario(_presupuesto(datos_bancarios="  "), _cfg())[
        "datos_bancarios_eleccion"
    ] == "vacio"


def test_unos_datos_propios_iguales_a_los_generales_siguen_siendo_propios():
    """No se convierten en herencia por parecerse: el PDF cambiaría solo."""
    valores = textos_para_formulario(_presupuesto(datos_bancarios=GENERAL), _cfg())
    assert valores["datos_bancarios_eleccion"] == "propio"
    assert valores["datos_bancarios"] == GENERAL


def test_un_presupuesto_nuevo_arranca_con_los_textos_de_la_empresa():
    valores = textos_para_formulario(None, _cfg())
    assert valores["notas"] == "Notas de la empresa"
    assert valores["condiciones"] == "Condiciones de la empresa"
    assert valores["datos_bancarios"] == GENERAL


def test_un_presupuesto_editado_muestra_sus_propios_textos_sin_los_generales():
    p = _presupuesto(datos_bancarios=PROPIO, notas="Solo esta obra", condiciones="Solo esta obra")
    valores = textos_para_formulario(p, _cfg())
    assert valores["datos_bancarios"] == PROPIO
    assert valores["datos_bancarios_heredados"] is False
    assert valores["notas"] == "Solo esta obra"
    # El botón de volver necesita el general aunque el campo tenga lo propio.
    assert valores["notas_generales"] == "Notas de la empresa"


# ---------------------------------------------------------------------------
# Interpretación del formulario
# ---------------------------------------------------------------------------


def test_la_eleccion_explicita_manda_sobre_el_texto():
    form = {"datos_bancarios_eleccion": "heredar", "datos_bancarios": PROPIO}
    assert datos_bancarios_desde_formulario(form, _cfg()) is None


def test_vaciar_el_campo_se_guarda_como_sin_datos_de_pago():
    form = {"datos_bancarios_eleccion": "propio", "datos_bancarios": "   "}
    assert datos_bancarios_desde_formulario(form, _cfg()) == ""


def test_dejar_el_texto_general_no_lo_congela_en_el_presupuesto():
    """El caso que rompía la herencia: copiar el general al guardar."""
    form = {"datos_bancarios": GENERAL}
    assert datos_bancarios_desde_formulario(form, _cfg()) is None


def test_escribir_un_texto_distinto_lo_guarda_como_propio():
    form = {"datos_bancarios": PROPIO}
    assert datos_bancarios_desde_formulario(form, _cfg()) == PROPIO


def test_repetir_lo_que_el_presupuesto_ya_tenia_no_cambia_nada():
    form = {"datos_bancarios": PROPIO}
    assert datos_bancarios_desde_formulario(form, _cfg(), actual=PROPIO) == PROPIO


def test_sin_campo_de_eleccion_y_sin_texto_conserva_lo_que_ya_habia():
    """Formulario incompleto: guardar otra cosa no borra los datos de pago."""
    assert datos_bancarios_desde_formulario({}, _cfg(), actual=None) is None
    assert datos_bancarios_desde_formulario({}, _cfg(), actual=PROPIO) == PROPIO
    assert datos_bancarios_desde_formulario({}, _cfg(), actual="") == ""


# ---------------------------------------------------------------------------
# Recorrido completo por HTTP
# ---------------------------------------------------------------------------


_CLIENTE = {"id": 0}

#: Un presupuesto no se guarda sin capítulo y partida con nombre; el contenido
#: del documento es lo de menos en estas pruebas.
_ESTRUCTURA = [{
    "nombre": "CAPÍTULO TEST",
    "partidas": [{
        "partida_id": "",
        "nombre": "Partida de prueba",
        "unidad": "m2",
        "cantidad": 10,
        "precio": 50.0,
        "tipo_partida": "included",
        "seleccionada": True,
    }],
}]


@pytest.fixture
def cliente():
    """Cliente HTTP con un cliente comercial ya dado de alta.

    ``/presupuestos/nuevo`` exige un ``client_id`` válido, y la base de la suite
    arranca sin clientes: se crea uno si no hay ninguno y se recuerda su id.
    """
    from app.database import SessionLocal
    from app.models import Cliente

    with TestClient(app) as c:
        with SessionLocal() as db:
            existente = db.query(Cliente).first()
            if existente is None:
                existente = Cliente(nombre="Cliente de pruebas", rif="J-00000000-0")
                db.add(existente)
                db.commit()
            _CLIENTE["id"] = existente.id
        yield c


def _crear(cliente, **extra):
    datos = {
        "client_id": str(_CLIENTE["id"]),
        "titulo": "Obra con datos de pago propios",
        "fecha": date.today().isoformat(),
        "validez_dias": "30",
        "moneda": "USD",
        "impuesto_pct": "16",
        "descuento_pct": "0",
        "estado": "borrador",
        "estructura_json": json.dumps(_ESTRUCTURA),
    }
    datos.update(extra)
    resp = cliente.post("/presupuestos/nuevo", data=datos, follow_redirects=False)
    assert resp.status_code == 303
    return int(resp.headers["location"].split("?")[0].split("/")[-1])


def _editar(cliente, pid, **extra):
    datos = {
        "client_id": str(_CLIENTE["id"]),
        "titulo": "Obra con datos de pago propios",
        "fecha": date.today().isoformat(),
        "validez_dias": "30",
        "moneda": "USD",
        "impuesto_pct": "16",
        "descuento_pct": "0",
        "estado": "borrador",
        "estructura_json": json.dumps(_ESTRUCTURA),
    }
    datos.update(extra)
    resp = cliente.post(f"/presupuestos/{pid}/editar", data=datos, follow_redirects=False)
    assert resp.status_code == 303


def _configurar_datos_bancarios(general: str) -> None:
    """Escribe el texto general directamente en la configuración de pruebas."""
    from app.database import SessionLocal
    from app.models import Configuracion

    with SessionLocal() as db:
        cfg = db.query(Configuracion).first()
        cfg.datos_bancarios = general
        db.commit()


def _leer_datos_bancarios(pid: int):
    from app.database import SessionLocal
    from app.models import Presupuesto

    with SessionLocal() as db:
        return db.get(Presupuesto, pid).datos_bancarios


def test_el_editor_muestra_los_datos_de_configuracion_y_el_boton_de_volver(cliente):
    _configurar_datos_bancarios(GENERAL)
    pid = _crear(cliente)
    html = cliente.get(f"/presupuestos/{pid}/editar").text

    assert GENERAL.splitlines()[0] in html
    assert 'name="datos_bancarios_eleccion"' in html
    assert "Volver a los datos de Configuración" in html
    assert "Usando los de Configuración" in html


def test_guardar_un_texto_propio_no_altera_configuracion(cliente):
    _configurar_datos_bancarios(GENERAL)
    pid = _crear(cliente)

    _editar(cliente, pid, datos_bancarios=PROPIO, datos_bancarios_eleccion="propio")

    assert _leer_datos_bancarios(pid) == PROPIO
    from app.database import SessionLocal
    from app.models import Configuracion

    with SessionLocal() as db:
        assert db.query(Configuracion).first().datos_bancarios == GENERAL
    html = cliente.get(f"/presupuestos/{pid}/editar").text
    assert "Propios de este presupuesto" in html


def test_mantener_el_texto_general_deja_el_presupuesto_heredando(cliente):
    _configurar_datos_bancarios(GENERAL)
    pid = _crear(cliente)

    _editar(cliente, pid, datos_bancarios=GENERAL, datos_bancarios_eleccion="heredar")

    assert _leer_datos_bancarios(pid) is None


def test_vaciar_los_datos_de_pago_quita_el_bloque_solo_en_ese_presupuesto(cliente):
    _configurar_datos_bancarios(GENERAL)
    pid = _crear(cliente)
    otro = _crear(cliente)

    _editar(cliente, pid, datos_bancarios="", datos_bancarios_eleccion="vacio")

    assert _leer_datos_bancarios(pid) == ""
    assert _leer_datos_bancarios(otro) is None
    html = cliente.get(f"/presupuestos/{pid}/editar").text
    assert "Sin datos de pago en este presupuesto" in html


def test_el_pdf_no_revienta_con_datos_propios_ni_vacios(cliente):
    """El PDF es el único consumidor que ya existía: la regla no lo rompe."""
    _configurar_datos_bancarios(GENERAL)
    pid = _crear(cliente)
    for eleccion, texto in (("propio", PROPIO), ("vacio", ""), ("heredar", GENERAL)):
        _editar(cliente, pid, datos_bancarios=texto, datos_bancarios_eleccion=eleccion)
        assert cliente.get(f"/presupuestos/{pid}/pdf").status_code == 200


# ---------------------------------------------------------------------------
# Interfaz del editor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ["form.html", "form_en.html"])
def test_el_bloque_de_pago_declara_sus_acciones_y_el_js_las_registra(nombre):
    """Una acción `data-cotizat-click` sin registrar es un botón que no hace nada.

    El despachador (``csp_events.js``) falla en silencio cuando el nombre no
    existe, así que el error sería invisible: el botón se pulsa y no pasa nada.
    """
    import re
    from pathlib import Path

    html = (Path(__file__).resolve().parent.parent / "app/templates/budgets" / nombre).read_text(
        encoding="utf-8"
    )
    # Las acciones del editor se registran en esta plantilla; las del resto de
    # la aplicación viven en ``app/static/js`` y no se comprueban aquí.
    registradas = set(re.findall(r'CotizatActions\.register\("([a-z0-9-]+)"', html))
    usadas = set(re.findall(r'data-cotizat-click="([a-z0-9-]+)"', html))

    assert {"budget-payment-reset", "budget-text-default"} <= usadas
    assert {"budget-payment-reset", "budget-text-default"} <= registradas

    # Los tres estados que el servidor sabe guardar tienen que existir en el
    # editor, o la intención no puede viajar.
    for eleccion in ("heredar", "propio", "vacio"):
        assert f'"{eleccion}"' in html
    # La etiqueta del estado y el campo oculto usan el vocabulario exacto del
    # servicio: un valor de más (o de menos) dejaría el estado sin color o
    # guardaría «propio» en silencio.
    assert "data-estado=\"{{ textos_doc.datos_bancarios_eleccion }}\"" in html
    assert 'value="{{ textos_doc.datos_bancarios_eleccion }}"' in html
    assert 'name="datos_bancarios_eleccion"' in html
    assert 'id="campo-datos-bancarios"' in html


@pytest.mark.parametrize("nombre", ["version.html", "version_en.html"])
def test_la_version_congelada_ensena_los_textos_que_llevaba_el_documento(nombre):
    """Es donde el usuario comprueba qué condiciones envió.

    Sin este bloque, un presupuesto con datos propios y otro que hereda se ven
    idénticos en el histórico de versiones.
    """
    from pathlib import Path

    html = (Path(__file__).resolve().parent.parent / "app/templates/budgets" / nombre).read_text(
        encoding="utf-8"
    )
    assert "snapshot.datos_bancarios" in html
    assert "snapshot.notas" in html
    assert "snapshot.condiciones" in html
    # Los tres estados se explican: propios, heredados (None) y sin datos ("").
    assert "snapshot.datos_bancarios is sameas none" in html
    assert 'snapshot.datos_bancarios == ""' in html
