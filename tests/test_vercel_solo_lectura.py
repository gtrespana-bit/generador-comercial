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
