"""E4-003 — configuración centralizada por entorno.

Cubre la detección de entorno, el catálogo de secretos y la validación por
entorno, asegurando además que ningún resumen filtre el valor de una
credencial.
"""
from __future__ import annotations

import pytest

from app.config import (
    DEFINICIONES,
    Entorno,
    entorno_actual,
    resumen_configuracion,
    secretos_configurados,
    validar,
    variables_secretas,
)


# ---------------------------------------------------------------------------
# Detección de entorno
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("production", Entorno.PRODUCCION),
        ("prod", Entorno.PRODUCCION),
        ("produccion", Entorno.PRODUCCION),
        ("test", Entorno.PRUEBAS),
        ("pruebas", Entorno.PRUEBAS),
        ("development", Entorno.DESARROLLO),
        ("dev", Entorno.DESARROLLO),
        ("desarrollo", Entorno.DESARROLLO),
    ],
)
def test_cotizat_env_explicito_gobierna(monkeypatch, valor, esperado):
    monkeypatch.setenv("COTIZAT_ENV", valor)
    assert entorno_actual() is esperado


def test_vercel_env_production_detecta_produccion(monkeypatch):
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert entorno_actual() is Entorno.PRODUCCION


def test_vercel_env_preview_no_es_produccion(monkeypatch):
    """Un preview de Vercel no debe activar las exigencias duras de producción."""
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    monkeypatch.setenv("VERCEL_ENV", "preview")
    assert entorno_actual() is not Entorno.PRODUCCION


def test_bajo_pytest_sin_senales_es_entorno_de_pruebas(monkeypatch):
    monkeypatch.delenv("COTIZAT_ENV", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    assert entorno_actual() is Entorno.PRUEBAS


def test_etiquetas_y_propiedades():
    assert Entorno.DESARROLLO.etiqueta == "desarrollo"
    assert Entorno.PRUEBAS.etiqueta == "pruebas"
    assert Entorno.PRODUCCION.etiqueta == "producción"
    assert Entorno.PRODUCCION.es_produccion
    assert not Entorno.PRUEBAS.es_produccion
    assert not Entorno.DESARROLLO.es_produccion


# ---------------------------------------------------------------------------
# Catálogo de secretos
# ---------------------------------------------------------------------------

def test_variables_secretas_son_las_esperadas():
    assert variables_secretas() == frozenset({
        "DATABASE_URL",
        "MIGRATION_DATABASE_URL",
        "SUPABASE_SECRET_KEY",
        "UPSTASH_REDIS_REST_TOKEN",
        "RESEND_API_KEY",
    })


def test_la_clave_publicable_de_supabase_no_es_secreta():
    """sb_publishable_ es pública por diseño: marcarla secreta sería un error."""
    assert "SUPABASE_PUBLISHABLE_KEY" not in variables_secretas()


def test_todas_las_definiciones_estan_documentadas():
    for variable in DEFINICIONES:
        assert variable.nombre, "nombre vacío en el catálogo"
        assert variable.descripcion.strip(), f"{variable.nombre} sin descripción"
    # No puede haber dos variables con el mismo nombre.
    nombres = [v.nombre for v in DEFINICIONES]
    assert len(nombres) == len(set(nombres))


def test_secretos_configurados_devuelve_booleanos(monkeypatch):
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_valor_de_prueba")
    estado = secretos_configurados()
    assert estado["SUPABASE_SECRET_KEY"] is True
    assert estado["RESEND_API_KEY"] is False
    assert all(isinstance(v, bool) for v in estado.values())


# ---------------------------------------------------------------------------
# Validación por entorno
# ---------------------------------------------------------------------------

def test_validar_en_desarrollo_y_pruebas_no_exige_nada():
    for entorno in (Entorno.DESARROLLO, Entorno.PRUEBAS):
        resultado = validar(entorno)
        assert resultado.ok
        assert resultado.problemas == ()


def test_validar_en_produccion_exige_las_requeridas(monkeypatch):
    for nombre in (
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_SECRET_KEY",
        "COTIZAT_PUBLIC_URL",
        "RESEND_API_KEY",
        "COTIZAT_EMAIL_FROM",
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
    ):
        monkeypatch.delenv(nombre, raising=False)

    resultado = validar(Entorno.PRODUCCION)

    errores = {p.mensaje for p in resultado.errores}
    avisos = {p.mensaje for p in resultado.avisos}

    # Exigidas (error).
    for nombre in (
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_SECRET_KEY",
        "COTIZAT_PUBLIC_URL",
    ):
        assert any(nombre in m for m in errores), f"{nombre} debería ser un error"

    # Recomendadas (aviso).
    for nombre in ("RESEND_API_KEY", "COTIZAT_EMAIL_FROM", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"):
        assert any(nombre in m for m in avisos), f"{nombre} debería ser un aviso"

    assert not resultado.ok


def test_validar_en_produccion_con_todo_configurado_ok(monkeypatch):
    for nombre in (
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_STORAGE_BUCKET",
        "COTIZAT_PUBLIC_URL",
        "RESEND_API_KEY",
        "COTIZAT_EMAIL_FROM",
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
    ):
        monkeypatch.setenv(nombre, "valor-de-prueba")

    resultado = validar(Entorno.PRODUCCION)
    assert resultado.ok
    assert resultado.problemas == ()


def test_validar_no_revela_el_valor_de_las_credenciales(monkeypatch):
    """Aunque falte o sobre una credencial, el mensaje nunca lleva su valor."""
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_abcdefghijklmnopqrstuvwxyz")
    resultado = validar(Entorno.PRODUCCION)
    texto = " ".join(p.mensaje for p in resultado.problemas)
    assert "sb_secret_abcdefghijklmnopqrstuvwxyz" not in texto


# ---------------------------------------------------------------------------
# Resumen seguro para el panel del operador
# ---------------------------------------------------------------------------

def test_resumen_no_filtra_valores_de_secretos(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_secreto_inventado_para_la_prueba")
    resumen = resumen_configuracion()
    serializado = str(resumen)
    assert "re_secreto_inventado_para_la_prueba" not in serializado
    # Los secretos se exponen solo como booleanos.
    assert all(isinstance(v, bool) for v in resumen["secretos"].values())


def test_resumen_incluye_entorno_y_problemas(monkeypatch):
    monkeypatch.setenv("COTIZAT_ENV", "production")
    resumen = resumen_configuracion()
    assert resumen["entorno"] == "production"
    assert resumen["entorno_etiqueta"] == "producción"
    assert isinstance(resumen["problemas"], list)
    assert all("gravedad" in p and "mensaje" in p for p in resumen["problemas"])


# ---------------------------------------------------------------------------
# Integración con /readyz y el panel de operador
# ---------------------------------------------------------------------------

def test_readiness_incluye_el_entorno_detectado():
    from app.health import readiness

    estado = readiness()
    assert "entorno" in estado.checks
    assert estado.checks["entorno"] in {"desarrollo", "pruebas", "producción"}


def test_diagnostico_operacion_incluye_la_configuracion():
    from app.services.operacion import diagnostico_operacion

    configuracion = diagnostico_operacion()["hechos"]["configuracion"]
    assert configuracion["entorno"] in {"development", "test", "production"}
    assert set(configuracion["secretos"]) == variables_secretas()
    assert all(isinstance(v, bool) for v in configuracion["secretos"].values())
