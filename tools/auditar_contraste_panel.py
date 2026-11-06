#!/usr/bin/env python3
"""Mide el contraste de texto del panel de administración sin abrir un navegador.

El panel tiene toda su piel en `app/static/css/admin.css` (desde el tramo B; las
pantallas ya no incrustan estilos). Este script lee ese CSS, resuelve las
variables `var(--token)` para el modo claro y el oscuro, y calcula el ratio de
contraste WCAG 2.1 de cada par texto/fondo que el propio CSS declara. También
mide los elementos **no textuales** de WCAG 1.4.11 (bordes de control, anillo de
foco y series de gráfico), que son justo los que un ojo cansado no ve fallar.

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

#: Umbral WCAG 1.4.11 para elementos no textuales: bordes de control, anillo
#: de foco y series de un gráfico.
MINIMO_NO_TEXTUAL = 3.0

#: (qué se mide, color del elemento, color de lo que lo rodea).
COMPONENTES_NO_TEXTUALES: tuple[tuple[str, str, str], ...] = (
    ("borde de campo sobre tarjeta", "--borde-control", "--card-bg"),
    ("borde de campo sobre el fondo", "--borde-control", "--bg-body"),
    ("anillo de foco sobre tarjeta", "--brand-color", "--card-bg"),
    ("barra de gráfico sobre tarjeta", "--brand-color", "--card-bg"),
    ("segunda serie sobre tarjeta", "--chart-2", "--card-bg"),
    ("segunda serie sobre su pista", "--chart-2", "--surface-3"),
)

BLOQUE_CSS = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
BLOQUE_EXTRA = re.compile(r"{%\s*block extra_css\s*%}(.*?){%\s*endblock\s*%}", re.S)
SELECCION_OSCURO = "html.dark-mode,\n    body.dark-mode"

HEX = re.compile(r"#([0-9a-fA-F]{3,8})\b")
RGBA = re.compile(r"rgba?\([^)]*\)")


# --------------------------------------------------------------------------- #
# Lectura del CSS del panel
# --------------------------------------------------------------------------- #
HOJA = REPO / "app" / "static" / "css" / "admin.css"


def css_del_panel() -> str:
    """Devuelve todo el CSS que el panel envía al navegador.

    Desde el tramo B la piel vive en `app/static/css/admin.css` (cacheable, con
    huella de versión). Se siguen leyendo los bloques inline por si alguna
    plantilla vuelve a incrustar estilos: así la medición no se queda ciega.
    """
    partes = []
    if HOJA.exists():
        partes.append(HOJA.read_text(encoding="utf-8"))
    partes.extend(
        m.group(1) for m in BLOQUE_CSS.finditer(BASE.read_text(encoding="utf-8"))
    )
    for ruta in sorted(ADMIN.rglob("*.html")):
        if ruta.name == "base_admin.html":
            continue
        texto = ruta.read_text(encoding="utf-8")
        partes.extend(m.group(1) for m in BLOQUE_EXTRA.finditer(texto))
        partes.extend(m.group(1) for m in BLOQUE_CSS.finditer(texto))
    return "\n".join(partes)


def paleta(css: str, selector: str) -> dict[str, str]:
    """Tokens `--x: valor` declarados en el bloque del selector indicado.

    Dos trampas que costaron caro (tramo D, 06/11/2026):

    1. **Los comentarios también contienen selectores.** El encabezado de
       `admin.css` menciona `html.dark-mode` al explicar el modo oscuro; buscar
       la primera aparición del texto encontraba ese comentario y devolvía el
       bloque `:root` siguiente. Resultado: el modo oscuro se auditaba con la
       paleta clara y salía impecable. Los comentarios se quitan antes de
       buscar.
    2. **Un selector puede ser una lista.** `html.dark-mode, body.dark-mode`
       se compara como conjunto de selectores, no como texto exacto.

    Devuelve `{}` si el selector no existe: quien llama decide si eso es un
    error (para el modo oscuro lo es).
    """
    sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    buscados = {parte.strip() for parte in selector.split(",") if parte.strip()}
    for encabezado, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", sin_comentarios):
        selectores = {parte.strip() for parte in encabezado.split(",") if parte.strip()}
        if not buscados & selectores:
            continue
        tokens = {}
        for declaracion in cuerpo.split(";"):
            if ":" not in declaracion:
                continue
            clave, valor = declaracion.split(":", 1)
            clave = clave.strip()
            if clave.startswith("--"):
                tokens[clave] = valor.strip()
        if tokens:
            return tokens
    return {}


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

    # Tokens que se usan como color de texto: si uno no tiene valor en modo
    # oscuro, hereda el claro y reaparece el problema que arregló el tramo A.
    definidos_oscuro = set(paleta(css, SELECCION_OSCURO))
    tokens_texto = set()
    for _, declaraciones in reglas:
        for nombre in re.findall(r"var\(\s*(--[\w-]+)", declaraciones.get("color", "")):
            tokens_texto.add(nombre)
    informe["tokens_texto"] = sorted(tokens_texto)
    # Un token que se apunta a sí mismo (o a otro inexistente) se queda sin
    # valor efectivo y rompe el color en silencio: el navegador lo descarta.
    todos = dict(tokens_claro)
    todos.update(paleta(css, SELECCION_OSCURO))
    rotos = sorted(
        f"{nombre}: {valor}"
        for nombre, valor in todos.items()
        if "var(" in resolver(valor, todos) or valor.strip() == f"var({nombre})"
    )
    referenciados = set()
    for _, declaraciones in reglas:
        for valor in declaraciones.values():
            referenciados.update(re.findall(r"var\(\s*(--[\w-]+)", valor))
    informe["tokens_rotos"] = rotos
    informe["tokens_inexistentes"] = sorted(referenciados - set(todos))
    informe["tokens_texto_sin_version_oscura"] = sorted(
        tokens_texto - definidos_oscuro
    )

    # Escala tipográfica: cuántos tamaños distintos se sirven al navegador.
    tamanos = {
        valor
        for _, declaraciones in reglas
        if (valor := declaraciones.get("font-size"))
    }
    informe["tamanos_fuente"] = sorted(tamanos)

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

    # Elementos no textuales (WCAG 1.4.11). El texto puede estar perfecto y aun
    # así el panel ser inusable: un campo cuyo borde no se ve, o una barra de
    # gráfico que se funde con la tarjeta, no se distinguen.
    informe["componentes"] = {}
    fallos_componentes = []
    for modo, tokens in (("claro", tokens_claro), ("oscuro", tokens_oscuro)):
        filas = []
        for nombre, frente, fondo_nombre in COMPONENTES_NO_TEXTUALES:
            if frente not in tokens or fondo_nombre not in tokens:
                continue
            rgb_frente, _ = primer_color(resolver(tokens[frente], tokens))
            rgb_fondo, _ = primer_color(resolver(tokens[fondo_nombre], tokens))
            if rgb_frente is None or rgb_fondo is None:
                continue
            ratio = round(contraste(rgb_frente, rgb_fondo), 2)
            fila = {
                "nombre": nombre,
                "frente": frente,
                "fondo": fondo_nombre,
                "ratio": ratio,
                "minimo": MINIMO_NO_TEXTUAL,
                "ok": ratio >= MINIMO_NO_TEXTUAL,
            }
            filas.append(fila)
            if not fila["ok"]:
                fallos_componentes.append({**fila, "modo": modo})
        informe["componentes"][modo] = filas
    informe["componentes_fallos"] = fallos_componentes
    return informe


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #
def imprimir(informe: dict) -> None:
    print("Panel de administración · auditoría de contraste\n")
    print(f"  reglas CSS analizadas ........ {informe['reglas']}")
    print(f"  tokens declarados (claro) .... {informe['tokens_claro']}")
    print(f"  colores literales distintos .. {len(informe['colores_literales'])}")
    print(
        "  superficies claras fijas ..... "
        f"{informe['superficies_literales']['total']}"
    )
    print(f"  tamaños de fuente distintos .. {len(informe['tamanos_fuente'])}")
    if informe["tokens_rotos"]:
        print(f"  TOKENS ROTOS ................. {informe['tokens_rotos']}")
    if informe["tokens_inexistentes"]:
        print(f"  TOKENS INEXISTENTES .......... {informe['tokens_inexistentes']}")
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
    print(f"\nElementos no textuales (WCAG 1.4.11, mínimo {MINIMO_NO_TEXTUAL}:1):")
    for modo in ("claro", "oscuro"):
        for fila in informe["componentes"].get(modo, []):
            marca = "ok" if fila["ok"] else "FALLA"
            print(
                f"  {modo:<7} {fila['ratio']:>6.2f}:1  {marca:<5} {fila['nombre']}"
            )

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

    if informe["tokens_rotos"] or informe["tokens_inexistentes"]:
        print("::warning::Hay tokens de color rotos o inexistentes en el panel.")

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
