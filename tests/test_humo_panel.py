"""Humo del panel de operador: la app arranca y ninguna página responde 500.

Motivo (05 y 06/11/2026). La suite tenía 3355 pruebas en verde y aun así se
desplegaron dos 500 seguidos:

1. ``/admin`` con ``NameError: lic_por_org`` (#189) — se arregló fuera de
   `main` y el panel se quedó sin el arreglo.
2. ``/admin/analitica`` con ``AttributeError: 'datetime.date' object has no
   attribute 'date'`` — la serie de audiencia solo se calcula cuando hay
   visitas, así que ninguna prueba con la tabla vacía la ejercitaba.

Y el apagón de #188 ni siquiera llegó a las pruebas: ``ROLES_TODOS =
ROLES_OPERADOR`` sin importar el nombre rompía ``tests/conftest.py``, de modo
que la suite no coleccionaba y todo parecía verde porque no corría nada.

Estas pruebas cubren los dos huecos con dos redes distintas:

- **Arranque real** (``test_la_app_arranca_en_un_proceso_limpio``): importa
  ``app.main`` en un intérprete nuevo, que es lo que hace el runtime al
  despertar. Un ``NameError`` de nivel de módulo no puede pasar inadvertido.
- **Humo del panel** (``test_*_del_panel_responden``): recorre todas las
  páginas del panel —las del mapa de ``app/panel_arquitectura.py`` y todas las
  rutas GET de ``app/routers``— con sesión de operador y datos sembrados, y
  exige que ninguna devuelva 500. Una página nueva queda cubierta sola.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.auth import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    SupabaseAuthSettings,
    SupabaseIdentity,
)
from app.database import get_operator_db
from app.main import app
from app.models import CompraPlan, Licencia, Organizacion, Presupuesto
from app.operadores import es_operador, rol_operador
from app.panel_arquitectura import FICHA_PESTANAS, SECCIONES, pestanas_de
from app.routers import common

RAIZ = Path(__file__).resolve().parents[1]

#: Mismo operador que usan las pruebas del panel de analítica: es la semilla
#: que deja ``init_db()`` y la que valida ``es_operador``.
EMAIL_OPERADOR = "titular@cotizat.online"
AUTH_UUID = "00000000-0000-4000-8000-000000000020"

SETTINGS = SupabaseAuthSettings(
    url="https://project.supabase.co",
    publishable_key="sb_publishable_test",
    cookie_secure=True,
)


# ---------------------------------------------------------------------------
# Red 1: la aplicación arranca
# ---------------------------------------------------------------------------


def test_la_app_arranca_en_un_proceso_limpio(tmp_path):
    """``import app.main`` en un intérprete nuevo, como el runtime real.

    Cualquier error de nivel de módulo (el caso de #188: un nombre usado y no
    importado) impide construir la aplicación y deja **todas** las rutas en
    500. Si ocurre dentro de la cadena de ``app.main``, la suite entera deja
    además de coleccionar (``conftest`` importa la app), así que se ve rojo por
    partida doble. Lo que aporta esta prueba es el arranque **en limpio**:
    intérprete nuevo, entorno sin los parches de pytest y una base recién
    creada, igual que el cold start del despliegue.
    """
    script = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "with TestClient(app) as cliente:\n"
        "    respuesta = cliente.get('/healthz')\n"
        "print('SALUD', respuesta.status_code)\n"
    )
    entorno = {
        **os.environ,
        "COTIZAT_DB": str(tmp_path / "arranque.db"),
        "PYTHONPATH": str(RAIZ),
    }
    entorno.pop("DATABASE_URL", None)

    proceso = subprocess.run(
        [sys.executable, "-c", script],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert proceso.returncode == 0, (
        "la aplicación no arranca en un proceso limpio "
        "(¿un nombre usado sin importar en el nivel de módulo?):\n"
        f"{proceso.stderr[-4000:]}"
    )
    assert "SALUD 200" in proceso.stdout, proceso.stdout + proceso.stderr[-2000:]


# ---------------------------------------------------------------------------
# Semilla y sesión de operador
# ---------------------------------------------------------------------------


@pytest.fixture
def operador(entorno, monkeypatch):
    """El entorno comercial de ``conftest`` + una sesión de operador real.

    ``entorno`` siembra la organización con presupuestos, licencia, clientes y
    facturas; aquí solo se añade la puerta de operador (``get_operator_db``)
    con la misma identidad verificada que usa el panel.
    """
    Session, ids, _rol = entorno
    monkeypatch.setattr(common, "DATABASE_IS_SQLITE", False)
    # Sin la semilla de operadores el panel responde 303 a /organizaciones y
    # el humo pasaría sin abrir ninguna página.
    monkeypatch.setenv("COTIZAT_OPERADORES", EMAIL_OPERADOR)
    monkeypatch.setattr(
        SupabaseAuthSettings, "from_environment", classmethod(lambda _cls: SETTINGS)
    )

    def _db_operador(request: Request):
        from app.auth import OrganizationAccessDenied

        db = Session()
        db.info["usuario_id"] = ids[1]
        db.info["auth_email"] = EMAIL_OPERADOR
        request.state.supabase_identity = SupabaseIdentity(
            auth_user_id=AUTH_UUID,
            email=EMAIL_OPERADOR,
            email_verified=True,
            name="Operador",
        )
        if not es_operador(EMAIL_OPERADOR, email_verificado=True):
            db.close()
            raise OrganizationAccessDenied("No tienes acceso a esta sección.")
        db.info["es_operador"] = True
        db.info["operador_rol"] = rol_operador(
            EMAIL_OPERADOR, email_verificado=True, db=db
        )
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        yield Session, ids
    finally:
        app.dependency_overrides.pop(get_operator_db, None)


def _cliente(*, con_sesion: bool = True) -> TestClient:
    # raise_server_exceptions=False: una página que revienta devuelve 500 en
    # lugar de tumbar la prueba, así se pueden listar todas las que fallan.
    cliente = TestClient(
        app, base_url="https://cotizat.test", raise_server_exceptions=False
    )
    if con_sesion:
        cliente.cookies.set(ACCESS_COOKIE, "access-token")
        cliente.cookies.set(REFRESH_COOKIE, "refresh-token")
    return cliente


def _revisar(cliente: TestClient, urls: list[str], *, permitidos=(200,)) -> list[int]:
    """Pide cada URL y falla listando todas las que se salen de lo permitido."""
    fallos = []
    codigos = []
    for url in urls:
        respuesta = cliente.get(url, follow_redirects=False)
        codigos.append(respuesta.status_code)
        if respuesta.status_code not in permitidos:
            destino = respuesta.headers.get("location", "")
            fallos.append(f"  {respuesta.status_code}  {url}  {destino}".rstrip())
    assert not fallos, (
        f"{len(fallos)} de {len(urls)} páginas del panel no responden como deben "
        f"(permitido: {sorted(permitidos)}):\n" + "\n".join(fallos)
    )
    return codigos


# ---------------------------------------------------------------------------
# Red 2: todas las páginas del panel
# ---------------------------------------------------------------------------


def test_las_paginas_del_panel_cargan_su_hoja_y_marcan_el_area(operador):
    """La piel viaja en `admin.css` y cada página declara su área en `<body>`.

    Desde el tramo B el CSS del panel ya no se incrusta en la respuesta: se
    enlaza con huella de versión y el navegador lo guarda. Y cada pantalla
    necesita `.panel-<área>` para que su CSS (que ahora vive en el mismo
    archivo) no alcance a las demás.
    """
    respuesta = _cliente().get("/admin")
    assert respuesta.status_code == 200
    html = respuesta.text
    assert "/static/css/admin.css?v=" in html, (
        "El panel tiene que enlazar la hoja cacheable con el filtro asset()."
    )
    assert '<body class="panel-hoy"' in html, (
        "El <body> del panel tiene que llevar la clase de su área."
    )
    assert "<style" not in html, (
        "El panel ha vuelto a incrustar estilos en la respuesta."
    )


def test_el_panel_no_se_abre_sin_sesion_de_operador():
    """El humo de abajo no puede pasar por una puerta abierta.

    Aquí se usa el camino real de autenticación (sin la dependencia sustituida):
    sin sesión y sin semilla de operadores, ``/admin`` no pinta el panel.
    """
    respuesta = _cliente(con_sesion=False).get("/admin", follow_redirects=False)
    assert respuesta.status_code in (301, 302, 303, 307, 308, 401, 403), (
        f"/admin sin sesión devolvió {respuesta.status_code}"
    )


def test_todas_las_pestanas_del_panel_responden(operador):
    """Área por área y pestaña por pestaña, tal como se navega de verdad."""
    Session, ids = operador
    org_id = ids[0]

    urls = []
    for seccion in SECCIONES:
        urls.append(seccion.ruta)
        for pestana in pestanas_de(seccion.id):
            urls.append(f"{seccion.ruta}?tab={pestana.id}")

    # La ficha de un cliente tiene sus propias pestañas.
    urls.append(f"/admin/clientes/{org_id}")
    for pestana in FICHA_PESTANAS:
        urls.append(f"/admin/clientes/{org_id}?tab={pestana.id}")

    # Guarda contra una lista vacía: si el mapa del panel cambiara de forma,
    # esta prueba tiene que avisar en vez de pasar por no probar nada.
    assert len(urls) >= 15, urls

    # Aquí se exige 200: son las páginas del menú, las mismas que se navegan a
    # diario. Un 303 a /organizaciones significa que el operador no entra.
    _revisar(_cliente(), urls)


def test_todas_las_rutas_get_del_panel_responden(operador):
    """Todas las rutas GET de ``app/routers`` que cuelgan de ``/admin``.

    Se leen del código fuente a propósito: las exportaciones CSV y los PDF
    están declaradas con ``include_in_schema=False`` y no aparecerían en el
    esquema OpenAPI. Así, una ruta nueva entra en el humo sin tocar la prueba.
    """
    Session, _ids = operador
    with Session() as db:
        organizacion = db.query(Organizacion).first()
        presupuesto = db.query(Presupuesto).first()
        licencia = db.query(Licencia).first()
        compra = db.query(CompraPlan).first()

    valores = {
        "organizacion_id": organizacion.id if organizacion else 1,
        "presupuesto_id": presupuesto.id if presupuesto else 1,
        "licencia_id": licencia.id if licencia else 1,
        "compra_id": compra.id if compra else 1,
        # Un chat que no existe: la página debe responder 404, no 500.
        "public_id": "no-existe",
    }

    plantillas = set()
    for archivo in (RAIZ / "app" / "routers").glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for encontrada in re.finditer(r'@router\.get\(\s*"([^"]+)"', texto):
            ruta = encontrada.group(1)
            if ruta.startswith("/admin"):
                plantillas.add(ruta)

    assert len(plantillas) >= 20, sorted(plantillas)

    urls = []
    for ruta in sorted(plantillas):
        faltan = [
            nombre
            for nombre in re.findall(r"\{(\w+)\}", ruta)
            if nombre not in valores
        ]
        assert not faltan, f"{ruta} usa parámetros que la prueba no sabe rellenar: {faltan}"
        urls.append(re.sub(r"\{(\w+)\}", lambda m: str(valores[m.group(1)]), ruta))

    # Las exportaciones y las fichas pueden redirigir con un mensaje (una
    # licencia de cortesía no tiene recibo) o responder 404 si el registro no
    # existe; lo que nunca es aceptable es un 500, un 401 o un 403.
    codigos = _revisar(_cliente(), urls, permitidos=(200, 303, 404))
    assert codigos.count(200) >= 18, (
        f"solo {codigos.count(200)} de {len(urls)} rutas responden 200: "
        "el humo estaría pasando sin abrir el panel de verdad"
    )
