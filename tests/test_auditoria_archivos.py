"""E4-017 — auditoría de archivos y ausencia de URLs públicas/firmadas.

La frontera de autorización de los archivos privados es el proxy de CotizaT
(``/archivos/...``). Nada debe generar una URL pública ni firmada hacia
Supabase Storage, porque eso movería la autorización fuera del proxy y abriría
un segundo camino de confianza.

Las comprobaciones «de comportamiento» (el backend no expone ``public_url`` ni
``signed_url``, ``file_url`` devuelve el proxy) ya viven en
``tests/test_aislamiento_almacenamiento.py`` (punto 13). Este módulo añade la
**auditoría estática completa**: recorre todo el árbol ``app/`` (Python,
plantillas, JavaScript y CSS) y prohíbe cualquier marcador de generación de URL
pública o firmada, de modo que la decisión quede blindada por regresión y no
solo documentada.

La decisión de no usar URLs firmadas se documenta en ``docs/ADR-002_*``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1] / "app"

# Marcadores de generación de URLs públicas o firmadas hacia el almacenamiento.
# ``public_url`` a secas se excluye a propósito: en ``app/auth.py`` y
# ``app/health.py`` nombra el origen HTTPS público de la aplicación
# (``COTIZAT_PUBLIC_URL``), no una URL de un objeto de Storage.
MARCADORES_URL = (
    "create_signed_url",
    "createSignedUrl",
    "create_signed_upload_url",
    "createSignedUploadUrl",
    "get_public_url",
    "create_public_url",
    "presigned_url",
    "presign",
    "signed_url",
    "signedUrl",
    "sign_url",
    "/object/public/",
)

# Enlaces directos al almacenamiento remoto: el navegador debe pasar siempre
# por el proxy, nunca por el bucket.
MARCADORES_ENLACE_DIRECTO = (
    "supabase.co/storage",
    "/object/public/",
    "amazonaws.com/",
    "r2.dev/",
)


def _archivos_de_texto(extensiones: tuple[str, ...]):
    for archivo in sorted(RAIZ.rglob("*")):
        if archivo.suffix.lower() in extensiones and "__pycache__" not in archivo.parts:
            yield archivo


def test_ningun_python_genera_urls_publicas_o_firmadas():
    """Ningún módulo construye una URL pública/firmada hacia Storage."""
    hallazgos: list[str] = []
    for archivo in _archivos_de_texto((".py",)):
        lineas = archivo.read_text(encoding="utf-8", errors="ignore").splitlines()
        for numero, linea in enumerate(lineas, start=1):
            for marcador in MARCADORES_URL:
                if marcador in linea:
                    hallazgos.append(f"{archivo.relative_to(RAIZ)}:{numero}: {marcador}")
    assert not hallazgos, (
        "URL pública/firmada de almacenamiento detectada en Python:\n"
        + "\n".join(hallazgos)
    )


@pytest.mark.parametrize("extension", [".html", ".js", ".css"])
def test_ninguna_plantilla_ni_estatico_enlaza_al_bucket(extension):
    """Plantillas, JS y CSS no enlazan directamente al almacenamiento remoto."""
    hallazgos: list[str] = []
    for archivo in _archivos_de_texto((extension,)):
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        for marcador in MARCADORES_ENLACE_DIRECTO:
            if marcador in texto:
                hallazgos.append(f"{archivo.relative_to(RAIZ)}: {marcador}")
    assert not hallazgos, (
        "Enlace directo al almacenamiento remoto detectado:\n" + "\n".join(hallazgos)
    )


def test_file_url_siempre_pasa_por_el_proxy_para_objetos_nuevos():
    """Una referencia ``storage://`` se sirve por ``/archivos/...``, nunca en abierto."""
    from app import storage

    for referencia in (
        "storage://organizaciones/1/anexos/planos.pdf",
        "storage://organizaciones/2/productos/foto.png",
    ):
        url = storage.file_url(referencia)
        assert url.startswith("/archivos/"), url
        assert "supabase.co" not in url
        assert "/object/public/" not in url


def test_backend_supabase_no_expone_capacidad_de_url_publica(tmp_path):
    """El backend remoto no ofrece método para construir URLs públicas/firmadas."""
    from app import storage

    settings = storage.StorageSettings(
        backend="supabase",
        local_root=tmp_path,
        supabase_url="https://ejemplo.supabase.co",
        secret_key="sb_secret_prueba-no-real",
        bucket="cotizat-private",
    )
    backend = storage.SupabaseStorage(settings)
    for atributo in (
        "public_url", "signed_url", "create_signed_url",
        "get_public_url", "presigned_url",
    ):
        assert not hasattr(backend, atributo), (
            f"SupabaseStorage no debe exponer {atributo}"
        )
