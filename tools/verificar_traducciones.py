"""Comprueba que las tablas de traducción precalculadas están completas y al día.

Las tablas de ``basedatos_partidas/salida/traducciones/`` son un artefacto
derivado: las genera ``tools/generar_traducciones.py`` recorriendo el catálogo
una vez y aplicando el glosario de cada mercado. En runtime ``traducir`` las
consulta antes de aplicar las reglas, así que son una aceleración, no un
requisito: si faltan, el programa funciona igual. Precisamente por eso pueden
quedarse viejas sin que nada falle en apariencia, que es el fallo peor de
todos: el cliente ve español en mitad de un presupuesto en inglés y no hay
ningún error en ningún log.

Reglas comprobadas:

1. **Actualizadas.** Recalcular la tabla de cada mercado reproduce exactamente
   lo que hay en disco. Si no, alguien cambió un glosario o el catálogo sin
   regenerar. Esta regla implica la completitud: el recálculo pasa por *todas*
   las cadenas del catálogo, así que una cadena que debería traducirse y no
   está en la tabla también se detecta aquí.
2. **Sin basura.** Ninguna traducción puede estar vacía, y ninguna cadena que
   traduzca a sí misma se guarda: eso solo haría el fichero más grande.
3. **Glosario sano.** JSON válido, sin claves repetidas, sin destinos vacíos y
   sin entradas que se traducen a sí mismas salvo los cognados declarados
   («sensor», «mineral», «conductor»…), que sí son legítimos.

Uso:
    python tools/verificar_traducciones.py            # falla si algo no cuadra
    python tools/verificar_traducciones.py --verbose  # detalla por mercado
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.paises import resolver_mercado                          # noqa: E402
from app.services.traduccion import (                            # noqa: E402
    BASE_GLOSARIOS,
    SALIDA_TRADUCCIONES,
    _traducir_reglas,
)

# Cognados: la palabra es correcta y exactamente igual en los dos idiomas, así
# que una entrada «de == a» es intencionada y no un error a corregir.
COGNADOS_PERMITIDOS = frozenset({
    "sensor", "mineral", "conductor", "vapor", "vertical", "flexible",
    "potable", "vehicular", "extractor", "dimensional", "detector", "bases",
    "panel", "closet", "motor", "central", "horizontal", "diesel", "carga",
    "tipo", "final", "general", "simple", "interior", "exterior", "natural",
    "marca", "cable", "parte", "receptor", "tubo", "plan", "personal",
    "metal", "principal", "total", "piso", "local", "normal", "base", "area",
    "original", "usual", "control", "formal", "manual", "granular", "audio",
    "video", "composite", "impacto", "error", "regular", "modular", "zinc",
    "orden", "individual", "industriales", "colectivas", "integral",
    "directo", "indirecta", "frecuente", "visual", "elevador", "elevado",
    "comercio", "lineal", "real", "especial", "canasta", "contenedor",
    "geotextiles", "visible", "pedestal", "parquet", "irregular",
    "tubular", "in situ",
})


def _glosarios_disponibles() -> list[str]:
    """Glosarios con fichero, ordenados con EN primero."""
    codigos = sorted(p.stem for p in BASE_GLOSARIOS.glob("*.json")
                     if not p.stem.endswith(".excepciones"))
    return (["EN"] if "EN" in codigos else []) + [c for c in codigos if c != "EN"]


def _revisar_glosarios(problemas: list[str], verboso: bool) -> None:
    for codigo in _glosarios_disponibles():
        ruta = BASE_GLOSARIOS / f"{codigo}.json"
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problemas.append(f"glosario {codigo}: JSON inválido ({exc})")
            continue
        if not isinstance(datos.get("cambios"), list):
            problemas.append(f"glosario {codigo}: no tiene la lista «cambios»")
            continue

        vistos: Counter[str] = Counter()
        for cambio in datos["cambios"]:
            de, a = cambio.get("de"), cambio.get("a")
            if not isinstance(de, str) or not de.strip():
                problemas.append(f"glosario {codigo}: entrada sin «de» válido")
                continue
            if not isinstance(a, str) or not a.strip():
                problemas.append(f"glosario {codigo}: «{de}» no tiene destino")
                continue
            vistos[de] += 1
            # La identidad solo se vigila en EN: en los glosarios de español
            # regional (ES -> CO, MX, PE...) dejar constancia de que un
            # término se dice igual en el país es documentación legítima. En
            # EN, en cambio, una identidad significa que la palabra sigue en
            # español, y que parece cubierta sin estarlo.
            if (codigo == "EN" and de.lower() == a.lower()
                    and de.lower() not in COGNADOS_PERMITIDOS):
                problemas.append(
                    f"glosario {codigo}: «{de}» se traduce a sí misma. O es un "
                    f"cognado que falta en COGNADOS_PERMITIDOS, o está tapando "
                    f"la traducción correcta."
                )
        for de, n in vistos.items():
            if n > 1:
                problemas.append(f"glosario {codigo}: «{de}» aparece {n} veces")
        if verboso:
            print(f"  glosario {codigo:3s} {len(datos['cambios']):5,d} entradas  ✓")


def _revisar_tablas(cadenas: list[str], verboso: bool,
                    problemas: list[str]) -> None:
    for glosario in _glosarios_disponibles():
        mercado = resolver_mercado("en" if glosario == "EN" else glosario)
        ruta = SALIDA_TRADUCCIONES / f"{glosario}.json"
        if not ruta.is_file():
            problemas.append(f"{glosario}: falta la tabla {ruta.name}")
            continue
        documento = json.loads(ruta.read_text(encoding="utf-8"))
        tabla = documento["cadenas"]

        vacias = [k for k, v in tabla.items() if not str(v).strip()]
        if vacias:
            problemas.append(
                f"{glosario}: {len(vacias)} traducciones vacías, "
                f"por ejemplo {vacias[0][:60]!r}"
            )

        identicas = [k for k, v in tabla.items() if k == v]
        if identicas:
            problemas.append(
                f"{glosario}: {len(identicas)} entradas que se traducen a sí "
                f"mismas (el generador no las escribe); por ejemplo "
                f"{identicas[0][:60]!r}"
            )

        # La regla que implica al resto: recalcular debe reproducir la tabla.
        desactualizadas: list[tuple[str, str, str]] = []
        for cadena in cadenas:
            esperado = _traducir_reglas(cadena, mercado, glosario)
            guardado = tabla.get(cadena, cadena)
            if guardado != esperado:
                desactualizadas.append((cadena, guardado, esperado))
                if len(desactualizadas) >= 5:
                    break
        if desactualizadas:
            cad, guardado, esperado = desactualizadas[0]
            problemas.append(
                f"{glosario}: tabla desactualizada ({len(desactualizadas)}+ "
                f"diferencias). «{cad[:50]}» está «{guardado[:50]}» y debería "
                f"estar «{esperado[:50]}». Ejecuta "
                f"tools/generar_traducciones.py"
            )

        if verboso:
            print(f"  tabla    {glosario:3s} {len(tabla):6,d} traducidas  ✓")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica las tablas de traducción precalculadas.")
    parser.add_argument("--verbose", action="store_true",
                        help="detalla el resultado por mercado")
    args = parser.parse_args()

    print("Verificando tablas de traducción…")
    cadenas = _recoger_cadenas()
    if not cadenas:
        print("No se han encontrado cadenas; ¿falta el catálogo?", file=sys.stderr)
        return 1
    print(f"  {len(cadenas):,} cadenas traducibles en el catálogo")

    problemas: list[str] = []
    _revisar_glosarios(problemas, args.verbose)
    _revisar_tablas(cadenas, args.verbose, problemas)

    if problemas:
        print(f"\n✗ {len(problemas)} problema(s):")
        for p in problemas:
            print(f"  · {p}")
        return 1
    print("\n✓ Tablas completas y al día")
    return 0


def _recoger_cadenas() -> list[str]:
    """Cadenas traducibles del catálogo, sin repeticiones y ordenadas.

    Es la misma función que usa el generador: si las dos recogieran cadenas
    distintas, este verificador podría dar por bueno un artefacto incompleto.
    """
    import importlib.util
    ruta = RAIZ / "tools" / "generar_traducciones.py"
    espec = importlib.util.spec_from_file_location("generar_traducciones", ruta)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo._recoger_cadenas()


if __name__ == "__main__":
    raise SystemExit(main())
