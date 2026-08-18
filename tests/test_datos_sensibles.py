"""E1-021 — el repositorio no debe contener datos reales sensibles.

La revisión manual de E1-021 no sirve de nada si el siguiente commit vuelve a
pegar una clave o un correo real. Estas pruebas ejecutan
``tools/auditar_datos_sensibles.py`` sobre lo que Git publicaría y verifican,
además, que el propio auditor sigue detectando lo que dice detectar (una regla
rota es peor que no tener regla: da confianza falsa).

El requisito de que el repositorio sea **privado** es operativo y se comprueba
en GitHub; aquí se cubre la otra mitad del enunciado: su contenido.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.auditar_datos_sensibles import (  # noqa: E402
    PATRONES_DE_ARCHIVO_PROHIBIDO,
    archivos_versionados,
    auditar,
)

REPO = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# El repositorio real
# ---------------------------------------------------------------------------


def test_el_repositorio_no_contiene_datos_sensibles():
    """Ningún archivo versionado expone credenciales ni datos personales."""
    hallazgos = auditar(REPO)

    assert not hallazgos, "Datos sensibles en el repositorio:\n" + "\n".join(
        f"  {h}" for h in hallazgos
    )


def test_la_herramienta_de_auditoria_se_ejecuta_y_devuelve_cero():
    """El comando documentado funciona tal cual y sale con estado 0."""
    resultado = subprocess.run(
        [sys.executable, "tools/auditar_datos_sensibles.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "Sin hallazgos" in resultado.stdout


def test_no_hay_archivos_prohibidos_versionados():
    """`.env`, bases de datos, volcados y claves no pueden estar en Git."""
    prohibidos = [
        ruta
        for ruta in archivos_versionados(REPO)
        for patron, _ in PATRONES_DE_ARCHIVO_PROHIBIDO
        if patron.search(ruta)
    ]

    assert not prohibidos, f"Archivos que no deben versionarse: {prohibidos}"


def test_gitignore_cubre_los_artefactos_con_datos_reales():
    """La primera barrera es .gitignore; debe seguir listando lo esencial."""
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")

    for entrada in (".env", "*.db", "backups/", "app/static/uploads/", "private_storage/"):
        assert entrada in gitignore, f"{entrada} ya no está en .gitignore"


# ---------------------------------------------------------------------------
# El auditor detecta de verdad (pruebas sobre archivos sintéticos)
# ---------------------------------------------------------------------------


CASOS_QUE_DEBEN_DETECTARSE = (
    ("clave-secreta-supabase", "SUPABASE_SECRET_KEY=sb_secret_A1b2C3d4E5f6G7h8I9j0K1l2"),
    ("api-key-resend", "RESEND_API_KEY=re_A1b2C3d4E5f6G7h8I9j0K1l2M3"),
    (
        "jwt",
        "token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjAwMDAwMDAwfQ."
        "dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXkw",
    ),
    ("token-github", "GH_TOKEN=ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"),
    # No se usa la clave canónica AKIAIOSFODNN7EXAMPLE de la documentación de
    # AWS: contiene «EXAMPLE» y el auditor la trata, con razón, como marcador.
    ("clave-aws", "aws_access_key_id = AKIAQ7R3TZ5MWN2LD8HC"),
    ("clave-privada-pem", "-----BEGIN RSA PRIVATE KEY-----"),
    (
        "cadena-de-conexion-con-contrasena",
        "DATABASE_URL=postgresql://cotizat_runtime:Tr0ub4dor&3@db.host.com:5432/cotizat",
    ),
    ("correo-personal", "Escribe a juan.perez.rodriguez@gmail.com para la prueba."),
    # El nombre de fantasía solo exime a la parte local: un nombre verosímil
    # sobre un dominio de consumo se sigue marcando aunque lleve subdirección.
    ("correo-personal", "alias de pruebas: j.perez+uno@gmail.com"),
    ("correo-personal", "contacto: no-soy-fulano@gmail.com"),
    ("telefono-venezolano", "Teléfono de contacto: +58 412 5837291"),
    ("telefono-espanol", "Llamar al +34 655 384 217"),
    ("documento-fiscal", "RIF de la empresa: J-30845217-4"),
    (
        "referencia-proyecto-supabase",
        "postgresql://cotizat_runtime.abcdefghijklmnopqrst:x@aws-0-eu-west-1.pooler.supabase.com:6543/postgres",
    ),
)


@pytest.mark.parametrize("regla_esperada,contenido", CASOS_QUE_DEBEN_DETECTARSE)
def test_el_auditor_detecta_cada_tipo_de_dato_sensible(
    tmp_path, regla_esperada, contenido
):
    """Cada regla debe seguir disparándose ante un ejemplo representativo."""
    archivo = tmp_path / "filtracion.txt"
    archivo.write_text(contenido, encoding="utf-8")

    hallazgos = auditar(tmp_path, rutas=["filtracion.txt"])

    reglas = {h.regla for h in hallazgos}
    assert regla_esperada in reglas, (
        f"El auditor ya no detecta '{regla_esperada}' en: {contenido!r}"
    )


CASOS_LEGITIMOS = (
    "SUPABASE_SECRET_KEY=REEMPLAZAR_CON_SB_SECRET_SOLO_EN_EL_BACKEND",
    "RESEND_API_KEY=re_REEMPLAZAR_SOLO_EN_EL_BACKEND",
    "DATABASE_URL=postgresql://cotizat_runtime:REEMPLAZAR@localhost:5432/cotizat",
    "Escribe a persona@example.com o a soporte@cotizat.online.",
    # Los ejemplos de normalización de identidad necesitan el dominio real
    # (los puntos que Gmail ignora no se pueden demostrar con example.com),
    # así que se admiten con un nombre de fantasía en la parte local.
    "normalizar_email('Fulano.Detal+cotizat@GMail.com') == 'fulanodetal@gmail.com'",
    "assert normalizar_email('mengana+x@proton.me') == 'mengana@proton.me'",
    "El buzón f.u.l.a.n.o@gmail.com recibe lo enviado a fulano@gmail.com.",
    "Casos degenerados: +etiqueta@gmail.com y .@gmail.com no dejan usuario.",
    "Teléfono de ejemplo: +58 412 000 0000",
    "RIF de ejemplo: J-00000000-0",
    "El formulario sugiere J-12345678-9 como formato.",
    "Conéctate a https://tu-proyecto.supabase.co con tu clave.",
    'jwt = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.signature-part-123"',
)


@pytest.mark.parametrize("contenido", CASOS_LEGITIMOS)
def test_el_auditor_no_marca_marcadores_ni_datos_ficticios(tmp_path, contenido):
    """Los marcadores documentados no pueden generar ruido: si el auditor
    grita en falso, se acaba ignorando y deja de proteger."""
    archivo = tmp_path / "documentacion.md"
    archivo.write_text(contenido, encoding="utf-8")

    hallazgos = auditar(tmp_path, rutas=["documentacion.md"])

    assert not hallazgos, f"Falso positivo en {contenido!r}: {hallazgos}"


@pytest.mark.parametrize(
    "ruta",
    (
        ".env",
        ".env.production",
        "presupuestos.db",
        "datos.sqlite3",
        "clave.pem",
        "backups/copia.zip",
        "app/static/uploads/logo.png",
        ".vercel/project.json",
    ),
)
def test_el_auditor_rechaza_los_archivos_que_nunca_deben_versionarse(ruta):
    """Se comprueba por nombre, sin necesidad de que el archivo exista."""
    hallazgos = auditar(REPO, rutas=[ruta])

    assert any(h.regla == "archivo-prohibido" for h in hallazgos), (
        f"El auditor permitiría versionar {ruta}"
    )


def test_env_example_sigue_permitido():
    """La plantilla de variables es documentación y debe seguir versionada."""
    hallazgos = auditar(REPO, rutas=[".env.example"])

    assert not hallazgos, f".env.example marcado por error: {hallazgos}"
