#!/usr/bin/env python3
"""Mide el contraste de texto del panel de administración sin abrir un navegador.

El panel tiene toda su hoja de estilos dentro de `admin/base_admin.html` (y cada
pantalla añade la suya con `{% block extra_css %}`). Este script lee ese CSS,
resuelve las variables `var(--token)` para el modo claro y el oscuro, y calcula
el ratio de contraste WCAG 2.1 de cada par texto/fondo que el propio CSS declara.

Por qué existe: la única forma de revisar el contraste a mano era mirar la
pantalla, y así se colaron pares como `--text-main` (#e2e8f0) sobre `#fff`
(1,23:1) que hacen ilegible el panel en modo oscuro.

Uso:
    python tools/auditar_contraste_panel.py                # informe legible
    python tools/auditar_contraste_panel.py --json         # volcado para pruebas
    python tools/auditar_contraste_panel.py --baseline X   # falla si hay deuda nueva

El código de salida es 1 cuando aparece una violación que no está registrada en
el baseline; con `--baseline` este script sirve como puerta de integración
continua (lo usa `tests/test_contraste_panel.py`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ADMIN = REPO / "app" / "templates" / "admin"
BASE = ADMIN / "base_admin.html"

#: Umbral WCAG 2.1 AA para texto normal.
MINIMO_NORMAL = 4.5
#: Umbral para texto grande (≥ 18,66 px o ≥ 14 px en negrita) y elementos no
#: textuales relevantes.
MINIMO_GRANDE = 3.0

BLOQUE_CSS = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
BLOQUE_EXTRA = re.compile(r"{%\s*block extra_css\s*%}(.*?){%\s*endblock\s*%}", re.S)
SELECCION_OSCURO = "html.dark-mode,\n    body.dark-mode"

HEX = re.compile(r"#([0-9a-fA-F]{3,8})\b")
RGBA = re.compile(r"rgba?\([^)]*\)")


# --------------------------------------------------------------------------- #
# Lectura del CSS del panel
# --------------------------------------------------------------------------- #
def css_del_panel() -> str:
    """Devuelve todo el CSS que el panel envía al navegador."""
    partes = [
        m.group(1) for m in BLOQUE_CSS.finditer(BASE.read_text(encoding="utf-8"))
    ]
    for ruta in sorted(ADMIN.rglob("*.html")):
        if ruta.name == "base_admin.html":
            continue
        texto = ruta.read_text(encoding="utf-8")
        partes.extend(m.group(1) for m in BLOQUE_EXTRA.finditer(texto))
        partes.extend(m.group(1) for m in BLOQUE_CSS.finditer(texto))
    return "\n".join(partes)


def paleta(css: str, selector: str) -> dict[str, str]:
    """Tokens `--x: valor` declarados en el bloque del selector indicado."""
    encontrado = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
    if encontrado is None:
        # El selector puede venir con otro espaciado (saltos de línea distintos).
        patron = re.escape(selector.split(",")[0].strip()) + r"[^{]*\{(.*?)\}"
        encontrado = re.search(patron, css, re.S)
        if encontrado is None:
            return {}
    tokens = {}
    for declaracion in encontrado.group(1).split(";"):
        if ":" not in declaracion:
            continue
        clave, valor = declaracion.split(":", 1)
        clave = clave.strip()
        if clave.startswith("--"):
            tokens[clave] = valor.strip()
    return tokens


# --------------------------------------------------------------------------- #
# Color y contraste
# --------------------------------------------------------------------------- #
def a_rgb(valor: str) -> tuple[int, int, int] | None:
    valor = valor.strip()
    corto = re.fullmatch(r"#([0-9a-fA-F]{3,8})", valor)
    if corto:
        hexa = corto.group(1)
        if len(hexa) == 3:
            hexa = "".join(c * 2 for c in hexa)
        if len(hexa) in (6, 8):
            return tuple(int(hexa[i : i + 2], 16) for i in (0, 2, 4))
        return None
    funcion = re.fullmatch(r"rgba?\(([^)]+)\)", valor)
    if funcion:
        piezas = [
            p
            for p in re.split(r"[,\s/]+", funcion.group(1).strip())
            if p.strip()
        ]
        if len(piezas) >= 3:
            return tuple(int(float(p)) for p in piezas[:3])
    return None


def alfa_de(valor: str) -> float:
    funcion = re.fullmatch(r"rgba\(([^)]+)\)", valor.strip())
    if not funcion:
        return 1.0
    piezas = [
        p for p in re.split(r"[,\s/]+", funcion.group(1).strip()) if p.strip()
    ]
    if len(piezas) >= 4:
        try:
            return float(piezas[3].rstrip("%")) / (100 if piezas[3].endswith("%") else 1)
        except ValueError:
            return 1.0
    return 1.0


def componer(frente, fondo, alfa: float):
    return tuple(round(f * alfa + b * (1 - alfa)) for f, b in zip(frente, fondo))


def luminancia(rgb) -> float:
    def canal(valor: int) -> float:
        proporcion = valor / 255
        return (
            proporcion / 12.92
            if proporcion <= 0.03928
            else ((proporcion + 0.055) / 1.055) ** 2.4
        )

    r, g, b = (canal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b) -> float:
    la, lb = luminancia(a), luminancia(b)
    alto, bajo = max(la, lb), min(la, lb)
    return (alto + 0.05) / (bajo + 0.05)


def resolver(valor: str, tokens: dict[str, str]) -> str:
    """Sustituye `var(--x)` por su valor, siguiendo hasta 6 niveles."""
    for _ in range(6):
        encontrado = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)", valor)
        if encontrado is None:
            break
        nombre, respaldo = encontrado.group(1), encontrado.group(2)
        reemplazo = tokens.get(nombre) or (respaldo or "").strip() or "#000000"
        valor = valor[: encontrado.start()] + reemplazo + valor[encontrado.end() :]
    return valor.strip()


def primer_color(valor: str):
    """Primer color de un valor CSS (gradientes incluidos)."""
    rgb = a_rgb(valor)
    if rgb:
        return rgb, valor
    encontrado = HEX.search(valor) or RGBA.search(valor)
    if encontrado is None:
        return None, None
    texto = encontrado.group(0)
    return a_rgb(texto), texto


# --------------------------------------------------------------------------- #
# Reglas
# --------------------------------------------------------------------------- #
def reglas_del_panel(css: str):
    sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    salida = []
    for encontrado in re.finditer(r"([^{}]+)\{([^{}]*)\}", sin_comentarios):
        selector = encontrado.group(1).strip()
        if selector.startswith("@") or "%" in selector:
            continue
        declaraciones: dict[str, str] = {}
        for trozo in encontrado.group(2).split(";"):
            if ":" in trozo:
                clave, valor = trozo.split(":", 1)
                declaraciones[clave.strip().lower()] = valor.strip()
        salida.append((re.sub(r"\s+", " ", selector), declaraciones))
    return salida


def violaciones(reglas, tokens: dict[str, str], fondos_base: list) -> list[dict]:
    """Pares texto/fondo declarados en una misma regla que no llegan al umbral."""
    fallos = []
    for selector, declaraciones in reglas:
        if "color" not in declaraciones:
            continue
        color = resolver(declaraciones["color"], tokens)
        if color in ("inherit", "currentColor", "unset"):
            continue
        color_rgb, color_txt = primer_color(color)
        if color_rgb is None:
            continue
        fondo = declaraciones.get("background-color") or declaraciones.get(
            "background"
        )
        if not fondo or fondo.strip() in ("none", "transparent"):
            continue
        fondo = resolver(fondo, tokens)
        fondo_rgb, fondo_txt = primer_color(fondo)
        if fondo_rgb is None:
            continue
        alfa = alfa_de(fondo)
        if alfa < 0.999:
            # Sobre qué se pinta depende del contenedor: se queda con el mejor
            # caso entre las superficies conocidas para no inventar fallos.
            ratio = max(
                contraste(color_rgb, componer(fondo_rgb, base, alfa))
                for base in fondos_base
            )
        else:
            ratio = contraste(color_rgb, fondo_rgb)
        if ratio < MINIMO_NORMAL:
            fallos.append(
                {
                    "selector": selector,
                    "texto": color_txt,
                    "fondo": fondo_txt,
                    "ratio": round(ratio, 2),
                }
            )
    fallos.sort(key=lambda f: (f["ratio"], f["selector"]))
    return fallos


def superficies_literales(reglas) -> dict[str, list[str]]:
    """Fondos claros escritos a mano: no cambian al activar el modo oscuro."""
    superficie: dict[str, list[str]] = {}
    for selector, declaraciones in reglas:
        for propiedad in ("background", "background-color"):
            valor = declaraciones.get(propiedad)
            if not valor or "var(" in valor:
                continue
            rgb, texto = primer_color(valor)
            if rgb is None or luminancia(rgb) <= 0.5:
                continue
            superficie.setdefault(texto, []).append(selector)
    return superficie


def colores_literales(reglas) -> set[str]:
    propiedades = (
        "color",
        "background",
        "background-color",
        "border",
        "border-color",
        "fill",
        "stroke",
        "box-shadow",
    )
    vistos = set()
    for _, declaraciones in reglas:
        for propiedad, valor in declaraciones.items():
            if propiedad not in propiedades or "var(" in valor:
                continue
            vistos.update(m.group(0).lower() for m in HEX.finditer(valor))
    return vistos


def claves(fallos: list[dict]) -> list[str]:
    return sorted(f"{f['selector']}|{f['texto']}|{f['fondo']}" for f in fallos)


def auditar() -> dict:
    css = css_del_panel()
    tokens_claro = paleta(css, ":root")
    tokens_oscuro = dict(tokens_claro)
    tokens_oscuro.update(paleta(css, SELECCION_OSCURO))
    reglas = reglas_del_panel(css)

    def fondo(nombre: str, tokens: dict[str, str]):
        rgb, _ = primer_color(resolver(tokens.get(nombre, "#ffffff"), tokens))
        return rgb or (255, 255, 255)

    informe = {
        "reglas": len(reglas),
        "tokens_claro": len(tokens_claro),
        "tokens_oscuro": len(
            [t for t in tokens_claro if t in paleta(css, SELECCION_OSCURO)]
        ),
        "colores_literales": sorted(colores_literales(reglas)),
    }
    for modo, tokens in (("claro", tokens_claro), ("oscuro", tokens_oscuro)):
        bases = [fondo("--bg-body", tokens), fondo("--bg-sidebar", tokens)]
        fallos = violaciones(reglas, tokens, bases)
        informe[modo] = {
            "fallos": fallos,
            "claves": claves(fallos),
        }
    superficies = superficies_literales(reglas)
    informe["superficies_literales"] = {
        "total": len(superficies),
        "detalle": {k: sorted(set(v)) for k, v in sorted(superficies.items())},
    }

    # Matriz de riesgo: tokens de texto del modo oscuro sobre esas superficies.
    tokens_texto = [
        t
        for t in (
            "--text-main",
            "--text-muted",
            "--brand-color",
            "--danger",
            "--success",
            "--warn",
            "--blue",
        )
        if t in tokens_oscuro
    ]
    matriz = {}
    for superficie in superficies:
        rgb_fondo, _ = primer_color(superficie)
        if rgb_fondo is None:
            continue
        fila = {}
        for token in tokens_texto:
            rgb_texto, _ = primer_color(resolver(tokens_oscuro[token], tokens_oscuro))
            if rgb_texto is not None:
                fila[token] = round(contraste(rgb_texto, rgb_fondo), 2)
        matriz[superficie] = fila
    informe["matriz_oscuro"] = matriz
    return informe


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #
def imprimir(informe: dict) -> None:
    print("Panel de administración · auditoría de contraste\n")
    print(f"  reglas CSS analizadas ........ {informe['reglas']}")
    print(f"  tokens de color (claro) ...... {informe['tokens_claro']}")
    print(f"  colores literales distintos .. {len(informe['colores_literales'])}")
    print(
        "  superficies claras fijas ..... "
        f"{informe['superficies_literales']['total']}"
    )
    for modo in ("claro", "oscuro"):
        fallos = informe[modo]["fallos"]
        print(f"\nMODO {modo.upper()}: {len(fallos)} par(es) por debajo de {MINIMO_NORMAL}:1")
        for fallo in fallos[:25]:
            print(
                f"  {fallo['ratio']:>6.2f}:1  {fallo['texto']:>18} sobre "
                f"{fallo['fondo']:<18} {fallo['selector'][:78]}"
            )
        if len(fallos) > 25:
            print(f"  … y {len(fallos) - 25} más")
    print("\nContraste de los tokens de texto del modo oscuro sobre superficies fijas:")
    encabezado = "  superficie".ljust(22) + "".join(
        t.replace("--", "").rjust(12) for t in ("--text-main", "--text-muted", "--brand-color")
    )
    print(encabezado)
    for superficie, fila in list(informe["matriz_oscuro"].items())[:8]:
        linea = f"  {superficie}".ljust(22)
        for token in ("--text-main", "--text-muted", "--brand-color"):
            valor = fila.get(token)
            linea += (f"{valor:>12.2f}" if valor is not None else f"{'—':>12}")
        print(linea)


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--json", action="store_true", help="volcado JSON")
    analizador.add_argument(
        "--baseline",
        type=Path,
        help="JSON con la deuda aceptada; falla si aparece una violación nueva",
    )
    argumentos = analizador.parse_args(argv)

    informe = auditar()
    if argumentos.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        imprimir(informe)

    if argumentos.baseline:
        if not argumentos.baseline.exists():
            print(
                f"::error::No existe el baseline {argumentos.baseline}",
                file=sys.stderr,
            )
            return 2
        aceptado = json.loads(argumentos.baseline.read_text(encoding="utf-8"))
        nuevas = []
        for modo in ("claro", "oscuro"):
            deuda = {
                f"{f['selector']}|{f['texto']}|{f['fondo']}"
                for f in informe[modo]["fallos"]
            }
            permitidas = set(aceptado.get(modo, []))
            nuevas.extend(sorted(deuda - permitidas))
        if nuevas:
            print("\n::error::Contraste nuevo por debajo de AA en el panel:", file=sys.stderr)
            for clave in nuevas:
                print(f"  {clave}", file=sys.stderr)
            return 1
        print("\nSin regresiones de contraste respecto al baseline ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
