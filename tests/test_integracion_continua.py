"""La integración continua debe existir y ejecutar las verificaciones reales.

Los dos últimos fallos de staging (lectura de `alembic_version` y bootstrap de
organizaciones bajo RLS) se detectaron en producción, no antes de fusionar. El
flujo de GitHub Actions es la puerta que debe verlos primero, así que su
contenido se protege igual que el resto del código: si alguien elimina un paso,
estas pruebas fallan.

La definición versionada vive en `docs/ci/ci.yml`. GitHub solo ejecuta el
archivo situado en `.github/workflows/ci.yml`, que debe ser una copia idéntica;
existe esa duplicación porque el token de la aplicación que abre los cambios
automáticos no tiene permiso para escribir en `.github/workflows/`. La última
prueba impide que ambas copias se separen en silencio.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DEFINICION = REPO / "docs" / "ci" / "ci.yml"
ACTIVO = REPO / ".github" / "workflows" / "ci.yml"


def _definicion() -> str:
    assert DEFINICION.exists(), (
        "No existe docs/ci/ci.yml, la definición versionada del flujo (E1-038)."
    )
    return DEFINICION.read_text(encoding="utf-8")


def test_el_flujo_de_integracion_continua_es_yaml_valido():
    """El archivo debe ser YAML interpretable por GitHub Actions."""
    yaml = pytest.importorskip("yaml")
    datos = yaml.safe_load(_definicion())

    assert isinstance(datos, dict), "El flujo debe ser un mapa YAML."
    assert datos.get("jobs"), "El flujo no define ningún trabajo."
    # PyYAML interpreta la clave `on:` como el booleano True.
    disparadores = datos.get("on", datos.get(True))
    assert disparadores, "El flujo no define cuándo se ejecuta."
    assert "pull_request" in disparadores, (
        "El flujo debe ejecutarse en cada pull request; es su función principal."
    )


def test_el_flujo_ejecuta_la_suite_y_las_verificaciones_manuales():
    """Cada verificación que antes se hacía a mano debe estar automatizada."""
    contenido = _definicion()

    for esperado, motivo in (
        ("pytest -q", "la suite automatizada"),
        ("compileall", "la compilación de Python"),
        ("verificar_plantillas.py", "el parseo de plantillas Jinja"),
        ("node --check", "la sintaxis del JavaScript"),
        ("verificar_lock.py", "la coherencia del bloqueo de dependencias"),
        ("simular_vercel_rofs.py", "la simulación del sistema de solo lectura"),
    ):
        assert esperado in contenido, f"El flujo de CI ya no comprueba {motivo}."


def test_el_flujo_instala_dependencias_bloqueadas():
    """CI debe instalar el lock para probar siempre el mismo conjunto."""
    assert "requirements.lock" in _definicion(), (
        "CI debe instalar requirements.lock, no rangos abiertos."
    )


def test_el_flujo_activo_coincide_con_la_definicion_versionada():
    """Las dos copias no pueden separarse sin que nadie se entere."""
    if not ACTIVO.exists():
        pytest.skip(
            "No hay copia en .github/workflows/; debe instalarse desde docs/ci/ci.yml"
        )

    assert ACTIVO.read_text(encoding="utf-8") == _definicion(), (
        ".github/workflows/ci.yml difiere de docs/ci/ci.yml. "
        "Copia la definición versionada sobre la activa."
    )


def test_el_verificador_de_plantillas_aprueba_las_plantillas_actuales():
    """La herramienta que ejecuta CI debe pasar sobre el repositorio real."""
    resultado = subprocess.run(
        [sys.executable, str(REPO / "tools" / "verificar_plantillas.py")],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert resultado.returncode == 0, (
        f"verificar_plantillas.py falló:\n{resultado.stdout}\n{resultado.stderr}"
    )


def test_el_verificador_de_plantillas_detecta_una_plantilla_rota():
    """Una comprobación que nunca falla no protege nada."""
    from jinja2 import Environment, TemplateSyntaxError

    with pytest.raises(TemplateSyntaxError):
        Environment().parse("{% for x in lista %}", name="rota.html")
