"""Comprueba que `requirements.lock` cubre y respeta los requirements fijados.

Sin esta verificación se puede cambiar una versión en `requirements.txt` y
olvidar regenerar el lock. El resultado sería que Vercel (que instala
`requirements.txt`) y la integración continua (que instala el lock) ejecuten
versiones distintas: justo el fallo que el bloqueo pretende evitar.

Reglas comprobadas:

1. Todas las dependencias directas usan `==` (nada de rangos abiertos).
2. Cada dependencia directa aparece en el lock.
3. La versión fijada coincide exactamente con la del lock.

Uso:
    python tools/verificar_lock.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIRECTOS = (REPO / "requirements.txt", REPO / "requirements-dev.txt")
LOCK = REPO / "requirements.lock"

# Nombre del paquete, extras opcionales y versión: p. ej. `uvicorn[standard]==0.52.3`
LINEA = re.compile(r"^(?P<nombre>[A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*(?P<op>[=<>!~]+)?\s*(?P<version>.*)$")


def _normalizar(nombre: str) -> str:
    """Normaliza el nombre según PEP 503 (guiones bajos, puntos y mayúsculas)."""
    return re.sub(r"[-_.]+", "-", nombre).lower()


def _leer(ruta: Path) -> list[tuple[str, str]]:
    """Devuelve los pares (paquete, version) declarados en un archivo."""
    entradas: list[tuple[str, str]] = []
    for cruda in ruta.read_text(encoding="utf-8").splitlines():
        linea = cruda.split("#", 1)[0].strip()
        if not linea or linea.startswith("-"):
            continue
        casado = LINEA.match(linea)
        if not casado:
            continue
        entradas.append(
            (
                _normalizar(casado.group("nombre")),
                f"{casado.group('op') or ''}{casado.group('version') or ''}".strip(),
            )
        )
    return entradas


def main() -> int:
    if not LOCK.exists():
        print(f"Falta {LOCK.name}. Genéralo con: python tools/generar_lock.py")
        return 1

    bloqueado = dict(_leer(LOCK))
    errores: list[str] = []

    for archivo in DIRECTOS:
        for paquete, restriccion in _leer(archivo):
            if not restriccion.startswith("=="):
                errores.append(
                    f"{archivo.name}: '{paquete}' no está fijado con '==' "
                    f"(encontrado: '{restriccion or 'sin versión'}')."
                )
                continue

            version = restriccion[2:]
            if paquete not in bloqueado:
                errores.append(
                    f"{archivo.name}: '{paquete}' no aparece en {LOCK.name}. "
                    "Regenera el lock."
                )
            elif bloqueado[paquete] != restriccion:
                errores.append(
                    f"{archivo.name}: '{paquete}' fija {version} pero "
                    f"{LOCK.name} tiene {bloqueado[paquete].lstrip('=')}. "
                    "Regenera el lock."
                )

    for error in errores:
        print(f"ERROR {error}")

    if errores:
        print(f"\n{len(errores)} incoherencia(s). Ejecuta: python tools/generar_lock.py")
        return 1

    print(f"Dependencias directas coherentes con {LOCK.name} ({len(bloqueado)} paquetes) ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
