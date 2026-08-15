"""Identidad del producto y compatibilidad con instalaciones anteriores.

Este módulo concentra los nombres que se muestran al usuario y la política de
rutas de datos. Mantener la compatibilidad aquí evita que un cambio de marca
haga parecer que los presupuestos de una instalación anterior desaparecieron.
"""
from pathlib import Path

PRODUCT_NAME = "CotizaT"
PRODUCT_DESCRIPTOR = "Presupuestos y control comercial para construcción y remodelación"
VALUE_PROPOSITION = (
    "Convierte tu catálogo y tus precios en presupuestos de obra claros, "
    "editables y listos para presentar."
)

# Identidad legal publicada en términos, privacidad y landing. La razón social
# se completa con la variable de entorno COTIZAT_LEGAL_ENTITY cuando exista la
# empresa registrada; hasta entonces los documentos muestran el marcador para
# que sea imposible publicarlos por accidente como si ya estuvieran completos.
import os as _os

LEGAL_ENTITY = _os.environ.get("COTIZAT_LEGAL_ENTITY", "").strip() or (
    "[RAZÓN SOCIAL DEL TITULAR — pendiente de registro]"
)
SUPPORT_EMAIL = _os.environ.get("COTIZAT_SUPPORT_EMAIL", "").strip() or "soporte@cotizat.online"

DATA_DIRECTORY_NAME = "CotizaT"
LEGACY_DATA_DIRECTORY_NAMES = ("Presupuestos",)
DATABASE_FILENAME = "presupuestos.db"


def _has_user_data(path: Path) -> bool:
    """Indica si una carpeta parece contener datos creados por el usuario."""
    return any(
        (
            (path / DATABASE_FILENAME).is_file(),
            (path / "backups").is_dir(),
            (path / "uploads").is_dir(),
        )
    )


def resolve_data_directory(root: Path) -> Path:
    """Elige la carpeta de CotizaT sin abandonar datos de versiones previas.

    Reglas:
    1. Una carpeta nueva que ya contiene datos siempre tiene prioridad.
    2. Si solo la carpeta histórica contiene datos, se sigue usando en el
       mismo lugar; no se mueve ni borra nada automáticamente.
    3. En una instalación limpia se usa ``CotizaT``.

    La segunda regla permite instalar el ejecutable renombrado sobre una
    versión anterior y encontrar inmediatamente su base, archivos y backups.
    """
    root = Path(root)
    current = root / DATA_DIRECTORY_NAME
    if _has_user_data(current):
        return current

    for legacy_name in LEGACY_DATA_DIRECTORY_NAMES:
        legacy = root / legacy_name
        if _has_user_data(legacy):
            return legacy

    if current.exists():
        return current
    for legacy_name in LEGACY_DATA_DIRECTORY_NAMES:
        legacy = root / legacy_name
        if legacy.exists():
            return legacy
    return current
