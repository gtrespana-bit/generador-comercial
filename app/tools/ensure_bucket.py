"""Verifica o crea el bucket privado de Storage para staging/producción.

Se ejecuta desde un equipo con salida TLS a Supabase:

    export SUPABASE_URL=https://<proyecto>.supabase.co
    read -s SUPABASE_SECRET_KEY        # sb_secret_...; no se imprime
    export SUPABASE_SECRET_KEY
    python -m app.tools.ensure_bucket           # crea si falta
    python -m app.tools.ensure_bucket --check   # solo verifica

No imprime claves. Requiere ``SUPABASE_STORAGE_BUCKET`` (por defecto
``cotizat-private``). El bucket queda ``public=false`` y con límite de 12 MB;
el backend de CotizaT usa la clave secret y el proxy ``/archivos/...`` como
frontera de autorización, así que **no** se añaden lecturas públicas para
``anon``/``authenticated``.
"""
from __future__ import annotations

import argparse
import json
import sys

from ..storage import (
    MAX_OBJECT_SIZE,
    StorageError,
    StorageSettings,
    SupabaseStorage,
)


def _print_bucket(status: dict) -> None:
    # Solo muestra atributos no sensibles del bucket.
    visible = {
        key: status.get(key)
        for key in ("id", "name", "public", "file_size_limit", "allowed_mime_types")
    }
    print(json.dumps(visible, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aprovisiona el bucket privado de CotizaT.")
    parser.add_argument(
        "--check", action="store_true",
        help="Solo verifica que el bucket exista y sea privado; no lo crea.",
    )
    args = parser.parse_args(argv)

    settings = StorageSettings.from_environment()
    if settings.backend != "supabase":
        print(
            "COTIZAT_STORAGE_BACKEND debe ser 'supabase' para este comando.",
            file=sys.stderr,
        )
        return 2

    backend = SupabaseStorage(settings)

    try:
        status = backend.bucket_status()
    except StorageError as exc:
        print(f"No se pudo comprobar el bucket: {exc}", file=sys.stderr)
        return 1

    if status is not None:
        print(f"El bucket '{settings.bucket}' ya existe.")
        _print_bucket(status)
        if status.get("public") is not False:
            print(
                f"ERROR: el bucket '{settings.bucket}' no es privado "
                "(public debe ser false). Corrígelo en el panel de Supabase.",
                file=sys.stderr,
            )
            return 1
        limit = status.get("file_size_limit")
        if isinstance(limit, (int, float)) and int(limit) != MAX_OBJECT_SIZE:
            print(
                f"AVISO: el límite del bucket es {limit} bytes; se esperaban "
                f"{MAX_OBJECT_SIZE} bytes (12 MB).",
                file=sys.stderr,
            )
        return 0

    if args.check:
        print(f"El bucket '{settings.bucket}' no existe.", file=sys.stderr)
        return 1

    print(f"Creando el bucket privado '{settings.bucket}'...")
    try:
        backend.create_private_bucket()
    except StorageError as exc:
        print(f"No se pudo crear el bucket: {exc}", file=sys.stderr)
        return 1

    try:
        status = backend.bucket_status()
    except StorageError as exc:
        print(f"Bucket creado, pero no se pudo re-verificar: {exc}", file=sys.stderr)
        return 1

    if status is None or status.get("public") is not False:
        print(
            "El bucket se creó, pero no se confirmó que sea privado. "
            "Revisa el panel de Supabase antes de continuar.",
            file=sys.stderr,
        )
        return 1

    print("Bucket privado aprovisionado correctamente.")
    _print_bucket(status)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI manual
    raise SystemExit(main())
