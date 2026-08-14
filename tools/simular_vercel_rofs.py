"""Simula el sistema de archivos de Vercel (solo lectura salvo /tmp) e
importa la aplicación para verificar que el arranque ya no falla.

Uso:
    python tools/simular_vercel_rofs.py [sqlite|postgres]
"""
import os
import sys
from pathlib import Path

modo = sys.argv[1] if len(sys.argv) > 1 else "postgres"

REPO = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, REPO)
ESCRIBIBLES = ("/tmp",)

real_mkdir = Path.mkdir
real_write_text = Path.write_text


def _escribible(p: Path) -> bool:
    return any(str(p).startswith(prefijo) for prefijo in ESCRIBIBLES)


def mkdir_ro(self, *args, **kwargs):
    if not _escribible(self):
        raise OSError(30, f"Read-only file system: '{self}'")
    return real_mkdir(self, *args, **kwargs)


def write_text_ro(self, *args, **kwargs):
    if not _escribible(self):
        raise OSError(30, f"Read-only file system: '{self}'")
    return real_write_text(self, *args, **kwargs)


Path.mkdir = mkdir_ro
Path.write_text = write_text_ro

if modo == "postgres":
    os.environ["DATABASE_URL"] = "postgresql://usuario:clave@localhost:5432/cotizat"
else:
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("COTIZAT_DB", None)
    os.environ.pop("PRESUPUESTOS_DB", None)

import app.database as db  # noqa: E402
import app.main  # noqa: E402

from starlette.routing import Mount, Route  # noqa: E402

print("modo:", modo)
print("DATABASE_IS_SQLITE:", db.DATABASE_IS_SQLITE)
print("DATOS_EFIMEROS:", db.DATOS_EFIMEROS)
print("DATA_DIR:", db.DATA_DIR)
print("UPLOADS_DIR:", db.UPLOADS_DIR, "existe:", db.UPLOADS_DIR.is_dir())

rutas_uploads = [r for r in app.main.app.router.routes if "/static/uploads" in getattr(r, "path", "")]
montajes = [r for r in app.main.app.router.routes if isinstance(r, Mount)]
print("rutas /static/uploads:", [type(r).__name__ for r in rutas_uploads])
print("montajes:", [getattr(r, "path", None) for r in montajes])

if modo == "postgres":
    assert not any(isinstance(r, Mount) for r in rutas_uploads), "no debe montarse uploads en PostgreSQL"
    assert any(isinstance(r, Route) for r in rutas_uploads), "debe existir la ruta 404 heredada"
else:
    assert db.DATOS_EFIMEROS, "SQLite sin DATABASE_URL en ROFS debe activar datos efímeros"
    assert str(db.DATA_DIR).startswith("/tmp"), "los datos deben reubicarse en /tmp"
    assert any(getattr(r, "path", None) == "/static/uploads" for r in montajes), "el montaje histórico debe existir en /tmp"

print("IMPORTACIÓN CORRECTA ✅")
