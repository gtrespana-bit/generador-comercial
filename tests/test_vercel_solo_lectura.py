"""Regresión: el arranque no debe depender de un sistema de archivos escribible.

Vercel (y otros despliegues serverless) monta el código en un sistema de
archivos de solo lectura; solo /tmp admite escritura. Antes de corregirlo, el
import de ``app.main`` fallaba al crear ``app/static/uploads`` y la página
devolvía 500 en todas las rutas.

Estas pruebas lanzan un intérprete nuevo con ese comportamiento simulado y
comprueban que la aplicación importa en ambas configuraciones:

- ``postgres``: ``DATABASE_URL`` configurado → sin escrituras locales; las
  rutas heredadas de /static/uploads quedan bloqueadas con 404.
- ``sqlite``: sin ``DATABASE_URL`` → los datos se reubican en /tmp (modo
  efímero) y el montaje histórico de subidas sigue disponible allí.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SIMULADOR = RAIZ / "tools" / "simular_vercel_rofs.py"


@pytest.mark.parametrize("modo", ["postgres", "sqlite"])
def test_arranque_en_sistema_de_solo_lectura(modo):
    entorno = os.environ.copy()
    entorno.pop("COTIZAT_DB", None)
    entorno.pop("PRESUPUESTOS_DB", None)
    resultado = subprocess.run(
        [sys.executable, str(SIMULADOR), modo],
        cwd=RAIZ,
        env=entorno,
        text=True,
        capture_output=True,
        timeout=120,
    )
    salida = resultado.stdout + resultado.stderr
    assert resultado.returncode == 0, salida
    assert "IMPORTACIÓN CORRECTA" in salida
    if modo == "sqlite":
        assert "DATOS_EFIMEROS: True" in salida
        assert "Sistema de archivos de solo lectura detectado" in resultado.stderr


def test_organizacion_por_entorno_vacia_equivale_a_no_configurada(monkeypatch):
    """Una variable presente pero vacía (Vercel la crea al pegar listas de
    variables) no debe romper get_db: antes producía ValueError en int('')."""
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("COTIZAT_ORGANIZATION_ID", "")
    with TestClient(app) as client:
        respuesta = client.get("/", follow_redirects=False)
        assert respuesta.status_code in (200, 303), (
            f"Código inesperado con COTIZAT_ORGANIZATION_ID vacía: "
            f"{respuesta.status_code}"
        )


def test_organizacion_por_entorno_no_numerica_falla_con_mensaje_claro(monkeypatch):
    """Un valor no numérico sí es un error de configuración: debe lanzar un
    ValueError descriptivo, no un 500 mudo."""
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("COTIZAT_ORGANIZATION_ID", "no-soy-un-numero")
    with TestClient(app) as client:
        with pytest.raises(ValueError, match="COTIZAT_ORGANIZATION_ID"):
            client.get("/")


def test_favicon_redirige_al_icono_estatico():
    """El navegador pide /favicon.ico por defecto; debe redirigir al icono
    real en lugar de dejar un 404 ruidoso en los logs del despliegue."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        respuesta = client.get("/favicon.ico", follow_redirects=False)
        assert respuesta.status_code == 307
        assert respuesta.headers["location"] == "/static/icono.png"

