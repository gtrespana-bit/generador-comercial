"""Las dependencias deben estar fijadas y coherentes con el lock (E1-037).

Vercel instala `requirements.txt` en cada build. Con rangos abiertos
(`fastapi>=0.115`) una publicación nueva de cualquier dependencia puede romper
un despliegue estable sin que nadie cambie una línea del repositorio, y el
fallo aparece en producción sin cambio asociado que lo explique.

Estas pruebas exigen que:

1. toda dependencia directa esté fijada con `==`;
2. `requirements.lock` exista y cubra esas dependencias con la misma versión;
3. el verificador use realmente los archivos del repositorio.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO / "requirements.txt"
REQUIREMENTS_DEV = REPO / "requirements-dev.txt"
LOCK = REPO / "requirements.lock"

LINEA = re.compile(r"^(?P<nombre>[A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*(?P<resto>.*)$")


def _dependencias(ruta: Path) -> list[tuple[str, str]]:
    entradas = []
    for cruda in ruta.read_text(encoding="utf-8").splitlines():
        linea = cruda.split("#", 1)[0].strip()
        if not linea or linea.startswith("-"):
            continue
        casado = LINEA.match(linea)
        assert casado, f"No se pudo interpretar la línea: {cruda!r}"
        entradas.append((casado.group("nombre").lower(), casado.group("resto").strip()))
    return entradas


@pytest.mark.parametrize("archivo", [REQUIREMENTS, REQUIREMENTS_DEV])
def test_toda_dependencia_directa_esta_fijada(archivo):
    """Ningún requirement puede usar un rango abierto."""
    abiertas = [
        f"{nombre}{resto}"
        for nombre, resto in _dependencias(archivo)
        if not resto.startswith("==")
    ]
    assert not abiertas, (
        f"{archivo.name} tiene dependencias sin fijar: {abiertas}. "
        "Vercel resolvería una versión distinta en cada build."
    )


def test_existe_el_cierre_completo_de_dependencias():
    """El lock debe existir para que CI instale siempre lo mismo."""
    assert LOCK.exists(), "Falta requirements.lock; genéralo con tools/generar_lock.py"
    assert _dependencias(LOCK), "requirements.lock está vacío."


def test_el_lock_cubre_las_dependencias_directas_con_la_misma_version():
    """Cambiar un pin sin regenerar el lock desalinearía Vercel y CI."""
    bloqueado = dict(_dependencias(LOCK))

    for archivo in (REQUIREMENTS, REQUIREMENTS_DEV):
        for nombre, restriccion in _dependencias(archivo):
            assert nombre in bloqueado, (
                f"{archivo.name}: '{nombre}' no está en requirements.lock. "
                "Regenera el lock con tools/generar_lock.py"
            )
            assert bloqueado[nombre] == restriccion, (
                f"{archivo.name}: '{nombre}' fija {restriccion} pero el lock "
                f"tiene {bloqueado[nombre]}. Regenera el lock."
            )


def test_el_verificador_de_lock_aprueba_el_estado_actual():
    """La herramienta que ejecuta CI debe pasar sobre el repositorio real."""
    resultado = subprocess.run(
        [sys.executable, str(REPO / "tools" / "verificar_lock.py")],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert resultado.returncode == 0, (
        f"verificar_lock.py falló:\n{resultado.stdout}\n{resultado.stderr}"
    )
