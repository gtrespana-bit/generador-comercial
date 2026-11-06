"""La consola de comandos de la paleta (⌘K): ejecutar, no solo buscar.

Tres cosas que no pueden fallar y que aquí quedan cerradas:

1. **Ningún comando inventa una ruta.** Cada URL del catálogo tiene que existir
   de verdad en la aplicación, con el método que declara. Un comando roto es un
   enlace muerto que el operador descubre en el peor momento.
2. **El rol filtra, y lo que cambia estado se confirma.** Un analista no ve el
   envío de avisos; ninguna acción se lanza sin `confirmacion`.
3. **La paleta envía un formulario real** (no una ruta nueva ni un `fetch` con
   permisos propios): el CSRF, el rol y el redirect con el mensaje siguen
   siendo los del servidor de siempre.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.main import app
from app.services.comandos_panel import (
    COMANDOS,
    TODOS,
    buscar_comandos,
    comandos_panel,
)

RAIZ = Path(__file__).resolve().parents[1]
JS = RAIZ / "app" / "static" / "js" / "admin-kit.js"


def _rutas_de_la_app() -> dict[str, set[str]]:
    """(ruta, métodos) registrados en la aplicación real.

    Los routers se incluyen de forma diferida, así que hay que entrar en el
    router original para ver las rutas del panel: quedarse en ``app.routes``
    solo devuelve los *wrappers* y ninguna ruta de ``/admin``.
    """
    rutas: dict[str, set[str]] = {}

    def recorrer(conjunto, prefijo: str = "") -> None:
        for ruta in conjunto:
            camino = getattr(ruta, "path", None)
            metodos = getattr(ruta, "methods", None)
            if camino and metodos:
                rutas.setdefault(prefijo + camino, set()).update(metodos)
            interno = getattr(ruta, "original_router", None)
            if interno is not None:
                recorrer(interno.routes, prefijo + (getattr(interno, "prefix", "") or ""))
            elif not camino and getattr(ruta, "routes", None):
                recorrer(ruta.routes, prefijo + (camino or ""))

    recorrer(app.routes)
    return rutas


def _coincide(url: str, metodo: str, rutas: dict[str, set[str]]) -> bool:
    """¿La URL enruta de verdad a una ruta con ese método?

    Las rutas del panel llevan parámetros (``{regla}``), así que se comparan
    como patrón: lo que se comprueba es que el navegador llegue a alguna parte.
    """
    camino = url.split("?")[0]
    for plantilla, metodos in rutas.items():
        patron = "^" + re.sub(r"\{[^/]+\}", "[^/]+", plantilla) + "$"
        if re.match(patron, camino) and metodo.upper() in metodos:
            return True
    return False


def test_todos_los_comandos_apuntan_a_rutas_que_existen():
    rutas = _rutas_de_la_app()
    fallos = [
        f"{comando.id}: {comando.url} no enruta a ninguna {comando.metodo}"
        for comando in COMANDOS
        if not _coincide(comando.url, comando.metodo, rutas)
    ]
    assert not fallos, "comandos rotos: " + "; ".join(fallos)


def test_toda_accion_dice_lo_que_va_a_pasar():
    """Un POST sin confirmación es un correo enviado por accidente."""
    for comando in COMANDOS:
        if comando.es_accion:
            assert comando.confirmacion, f"{comando.id} cambia datos sin confirmación"
            assert len(comando.confirmacion) > 30, f"{comando.id}: la confirmación no explica nada"


def test_solo_los_comandos_de_lectura_son_navegacion():
    for comando in COMANDOS:
        if comando.metodo == "GET":
            assert not comando.confirmacion, f"{comando.id} navega y pide confirmación: sobra"


def test_el_rol_filtra_la_lista():
    todos = {c["id"] for c in comandos_panel("superadmin")}
    analista = {c["id"] for c in comandos_panel("analista")}
    assert "avisos-vencimiento" in todos
    assert "avisos-vencimiento" not in analista
    assert "errores" not in analista  # Sistema es de superadmin
    assert "riesgo-baja" in analista  # la analítica la ve todo el mundo
    assert analista < todos


def test_sin_rol_declarado_no_se_esconde_nada():
    """Mismo criterio que el menú: sin rol no se filtra (y el servidor decide)."""
    assert {c["id"] for c in comandos_panel(None)} == {c.id for c in COMANDOS}


def test_los_roles_del_catalogo_son_los_del_panel():
    for comando in COMANDOS:
        assert set(comando.roles) <= set(TODOS), comando.id


def test_la_busqueda_ignora_acentos_y_encuentra_alias():
    assert [c["id"] for c in buscar_comandos("superadmin", "buzon")] == ["soporte"]
    assert [c["id"] for c in buscar_comandos("superadmin", "mrr")] == ["cobros"]
    assert [c["id"] for c in buscar_comandos("superadmin", "correo")] == ["avisos-vencimiento"]
    assert buscar_comandos("superadmin", "zzzz") == []


def test_la_paleta_arma_el_formulario_y_no_una_ruta_nueva():
    js = JS.read_text(encoding="utf-8")
    assert '"/admin/comandos"' in js
    assert 'form.method = "post"' in js
    assert "form.action = comando.url" in js
    # El primer Enter nunca ejecuta: primero se confirma.
    assert "confirmarAccion" in js
    assert "if (sel.accion) { confirmarAccion(sel); return; }" in js


def test_el_endpoint_devuelve_los_comandos_del_rol(operador, cliente_panel):
    respuesta = cliente_panel.get("/admin/comandos")
    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    datos = respuesta.json()
    assert datos["comandos"], "la consola salió vacía con sesión de operador"
    titulos = [c["titulo"] for c in datos["comandos"]]
    assert "Compras por revisar" in titulos
    # El filtro del servidor también responde por texto.
    respuesta = cliente_panel.get("/admin/comandos?q=mrr")
    assert [c["id"] for c in respuesta.json()["comandos"]] == ["cobros"]


def test_sin_sesion_la_consola_no_esta_abierta():
    from fastapi.testclient import TestClient

    anonimo = TestClient(app, base_url="https://cotizat.test", raise_server_exceptions=False)
    respuesta = anonimo.get("/admin/comandos", follow_redirects=False)
    assert respuesta.status_code in (301, 302, 303, 307, 308, 401, 403)
    assert "comandos" not in respuesta.text.lower()


def test_la_accion_termina_donde_la_paleta_dice(operador, cliente_panel):
    """Enviar desde la consola tiene que acabar en la página de la regla.

    No se comprueba el correo (en pruebas no hay servidor configurado): se
    comprueba el contrato de la paleta —POST real, redirect con el mensaje— y
    que la ruta no se caiga con un 500 cuando la lanza el operador.
    """
    comando = next(c for c in COMANDOS if c.id == "avisos-vencimiento")
    respuesta = cliente_panel.post(comando.url, follow_redirects=False)
    assert respuesta.status_code in (303, 307), respuesta.status_code
    assert respuesta.headers["location"].startswith("/admin/sistema")
