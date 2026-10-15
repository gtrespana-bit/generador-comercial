"""Genera la vista previa de la firma de correo de CotizaT (reproducible).

Produce **``vista-previa.png``**: una recreación a escala de cómo se ve la firma
en un cliente de correo (mismos colores, mismos saltos de línea y misma
jerarquía que el HTML). Sirve para revisarla sin abrir el archivo en el
navegador y para compartirla en una conversación.

El logotipo **no se genera aquí**: la firma apunta al icono que la web ya
publica (``/static/icono-192.png``, con ``/static/icono-512.png`` para pantallas
retina). Son los mismos archivos del favicon y del manifiesto PWA, así que
están en producción desde antes y la firma no depende de publicar nada nuevo.
La imagen no se incrusta en el HTML a base64 porque Outlook de escritorio
ignora las imágenes embebidas.

Uso:

    python3 -m venv .venv-firma
    .venv-firma/bin/pip install pillow
    .venv-firma/bin/python marketing/firma_correo/generar_assets.py

Los textos de la firma (nombre, cargo, descriptor y contacto) viven en
``firma.html``: si cambian, cambia también ``DATOS`` aquí para que la vista
previa siga contando lo mismo.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
#: Icono oficial que la web ya publica (favicon y manifiesto PWA).
LOGO_ORIGEN = RAIZ / "app" / "static" / "icono-512.png"
FUENTES = RAIZ / "app" / "static" / "fonts"
VISTA_PREVIA = Path(__file__).resolve().parent / "vista-previa.png"

#: Tamaño visible del logotipo dentro de la firma (px CSS) y su versión retina.
LADO_VISIBLE = 72

NAVY = "#123f78"
GRIS = "#5b6b7c"
GRIS_TEXTO = "#3d4c5c"
ORO = "#e5ae3c"

DATOS = {
    "nombre": "Ruben Romero",
    "cargo": "Fundador · CotizaT",
    "descriptor": "Presupuestos y control comercial para construcción y remodelación",
    "email": "soporte@cotizat.online",
    "web": "cotizat.online",
    "cta": "Prueba gratis 7 días, sin tarjeta",
}

#: Se dibuja al doble y se reduce: los bordes del texto quedan suaves.
ESCALA = 2


def _fuente(nombre: str, tamano: float) -> ImageFont.FreeTypeFont:
    """Lato del propio proyecto: la vista previa no depende de fuentes del SO."""
    return ImageFont.truetype(str(FUENTES / nombre), int(round(tamano * ESCALA)))


def _medir(dibujo: ImageDraw.ImageDraw, texto: str, fuente) -> float:
    return dibujo.textlength(texto, font=fuente) / ESCALA


def _partir(dibujo, texto: str, fuente, limite: float) -> list[str]:
    """Corta el descriptor por palabras, como haría el ancho de la celda."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        candidata = f"{actual} {palabra}".strip()
        if _medir(dibujo, candidata, fuente) > limite and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = candidata
    if actual:
        lineas.append(actual)
    return lineas


def _vista_previa() -> Path:
    """Recrea la firma con la misma jerarquía visual que el HTML."""
    margen_x, margen_y = 44, 40
    separacion = 18
    lado = LADO_VISIBLE
    ancho_texto = 430

    # Lienzo de trabajo al doble de resolución.
    ancho = margen_x * 2 + lado + separacion + ancho_texto
    lienzo = Image.new("RGBA", (ancho * ESCALA, 300 * ESCALA), "white")
    dibujo = ImageDraw.Draw(lienzo)

    f_nombre = _fuente("Lato-Bold.ttf", 17)
    f_cargo = _fuente("Lato-Regular.ttf", 12)
    f_texto = _fuente("Lato-Regular.ttf", 11)
    f_contacto = _fuente("Lato-Bold.ttf", 11.5)
    f_cta = _fuente("Lato-Regular.ttf", 10)

    x = margen_x
    y = margen_y

    # Logotipo (con su transparencia, como en el correo). Se reduce el icono
    # oficial —el mismo que sirve la firma por URL— al tamaño visible.
    logo = Image.open(LOGO_ORIGEN).convert("RGBA").resize((lado, lado), Image.LANCZOS)
    lienzo.alpha_composite(logo, (x * ESCALA, y * ESCALA))

    x_texto = x + lado + separacion
    cursor = y + 1

    def linea(texto: str, fuente, color: str, avance: float) -> None:
        nonlocal cursor
        dibujo.text(
            (x_texto * ESCALA, cursor * ESCALA),
            texto,
            font=fuente,
            fill=color,
        )
        cursor += avance

    linea(DATOS["nombre"], f_nombre, NAVY, 20)
    linea(DATOS["cargo"], f_cargo, GRIS, 14)
    # Filete dorado
    dibujo.rectangle(
        [x_texto * ESCALA, (cursor + 2) * ESCALA,
         (x_texto + 52) * ESCALA, (cursor + 4) * ESCALA],
        fill=ORO,
    )
    cursor += 16

    for parte in _partir(dibujo, DATOS["descriptor"], f_texto, ancho_texto):
        linea(parte, f_texto, GRIS_TEXTO, 14)

    cursor += 6
    dibujo.text((x_texto * ESCALA, cursor * ESCALA), DATOS["email"],
                font=f_contacto, fill=NAVY)
    corrido = _medir(dibujo, DATOS["email"], f_contacto)
    dibujo.text(((x_texto + corrido + 9) * ESCALA, cursor * ESCALA), "·",
                font=f_texto, fill=GRIS)
    dibujo.text(((x_texto + corrido + 22) * ESCALA, cursor * ESCALA), DATOS["web"],
                font=f_contacto, fill=NAVY)
    cursor += 20

    dibujo.ellipse(
        [(x_texto + 2) * ESCALA, (cursor + 4) * ESCALA,
         (x_texto + 8) * ESCALA, (cursor + 10) * ESCALA],
        fill=ORO,
    )
    dibujo.text(((x_texto + 14) * ESCALA, cursor * ESCALA), DATOS["cta"],
                font=f_cta, fill=GRIS_TEXTO)

    alto_final = int((cursor + 32) * ESCALA)
    lienzo = lienzo.crop((0, 0, ancho * ESCALA, alto_final))
    lienzo.convert("RGB").resize((ancho, alto_final // ESCALA), Image.LANCZOS).save(
        VISTA_PREVIA, format="PNG", optimize=True
    )
    return VISTA_PREVIA


def main() -> int:
    print(f"Escrita {_vista_previa().relative_to(RAIZ)} ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
