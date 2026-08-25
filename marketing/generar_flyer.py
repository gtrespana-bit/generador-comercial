"""Genera los flyers publicitarios de CotizaT para Facebook.

Piezas (ambas en marketing/, PNG listos para Meta Ads):
- cotizat-flyer-facebook-1080x1080.png  → feed 1:1 (universal)
- cotizat-flyer-facebook-1080x1350.png  → feed 4:5 (recomendado móvil)

El mensaje deja claro que CotizaT es un producto de software (generador de
presupuestos + gestión comercial) que usa la propia empresa, no un servicio
de remodelación ni de redacción de presupuestos.

Se compone a 2x y se reduce con LANCZOS para máxima nitidez del texto.
La fotografía y la tarjeta de ejemplo se pegan ya a resolución final.
Los rellenos semitransparentes se hacen por overlay + alpha_composite
(ImageDraw reemplazaría el canal alfa y aclararía la imagen final).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "app" / "static" / "fonts"
OUT = ROOT / "marketing"
LOGO = ROOT / "app" / "static" / "icono.png"
FOTO = OUT / "assets" / "foto-obrera.jpg"

NAVY_TOP = (11, 34, 68)       # #0b2244
NAVY_BOT = (18, 63, 120)      # #123f78 (navy de marca)
GOLD = (229, 174, 60)         # #e5ae3c (dorado de marca)
GOLD_DARK = (180, 128, 26)
LIGHT = (185, 204, 231)       # #b9cce7
WHITE = (255, 255, 255)
S = 2                          # factor de supermuestreo

BLACK = "Lato-Black.ttf"
BOLD = "Lato-Bold.ttf"
REG = "Lato-Regular.ttf"

LOGO_IMG = Image.open(LOGO).convert("RGBA")


# ── utilidades base ──────────────────────────────────────────────────────────

def font(name, size):
    return ImageFont.truetype(str(FONTS / name), int(size * S))


def fit_font(texts, name, start, minimum, max_w, draw):
    size = start
    while size > minimum:
        f = font(name, size)
        if all(draw.textlength(t, font=f) <= max_w * S for t in texts):
            return f
        size -= 1
    return font(name, minimum)


def gradient(w, h, top, bot):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def add_texture(base):
    w, h = base.size
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    step = 64 * S
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(255, 255, 255, 7), width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(255, 255, 255, 7), width=1)
    cx, cy = -150 * S, -150 * S
    for r, a in ((380, 10), (470, 9), (560, 8)):
        d.ellipse([cx - r * S, cy - r * S, cx + r * S, cy + r * S],
                  outline=(*GOLD, a), width=3 * S)
    base.alpha_composite(ov)


def new_base(W, H):
    base = gradient(W * S, H * S, NAVY_TOP, NAVY_BOT).convert("RGBA")
    add_texture(base)
    return base, ImageDraw.Draw(base)


def glass(base, rect, radius, fill, outline=None, width=2):
    """Redondeado con relleno/contorno que respeta el alfa (overlay)."""
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    box = [rect[0] * S, rect[1] * S, rect[2] * S, rect[3] * S]
    d.rounded_rectangle(box, radius=radius * S, fill=fill,
                        outline=outline,
                        width=width * S if outline else 1)
    base.alpha_composite(ov)


def dot_alpha(base, cx, cy, r, fill):
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
    d.ellipse(box, fill=fill)
    base.alpha_composite(ov)


def draw_tracked(draw, x, y, text, fnt, fill, tracking):
    cx = x * S
    for ch in text:
        draw.text((cx, y * S), ch, font=fnt, fill=fill)
        cx += draw.textlength(ch, font=fnt) + tracking
    return cx


def paste_logo(base, pos, size):
    logo = LOGO_IMG.resize((size * S, size * S), Image.Resampling.LANCZOS)
    base.alpha_composite(logo, (pos[0] * S, pos[1] * S))
    glass(base, (pos[0], pos[1], pos[0] + size, pos[1] + size),
          size * 0.185, (0, 0, 0, 0), outline=GOLD, width=3)


def header(base, d, logo_size, wordmark, tagline=None, x=64, y=60):
    paste_logo(base, (x, y), logo_size)
    f_mark = font(BLACK, wordmark)
    mx = (x + logo_size + 20) * S
    my = (y + (logo_size - wordmark) / 2 - 2) * S
    d.text((mx, my), "Cotiza", font=f_mark, fill=WHITE)
    d.text((mx + d.textlength("Cotiza", font=f_mark), my), "T",
           font=f_mark, fill=GOLD)
    if tagline:
        f_tag = font(REG, 22)
        d.text((mx, my + wordmark * S + 6 * S), tagline, font=f_tag,
               fill=LIGHT)


def draw_check(base, cx, cy, r):
    dot_alpha(base, cx, cy, r, (*GOLD, 255))
    d = ImageDraw.Draw(base)
    w = int(r * 0.30 * S)
    pts = [(cx - 0.42 * r) * S, (cy + 0.02 * r) * S,
           (cx - 0.10 * r) * S, (cy + 0.34 * r) * S,
           (cx + 0.48 * r) * S, (cy - 0.30 * r) * S]
    d.line([pts[0:2], pts[2:4], pts[4:6]], fill=WHITE, width=w,
           joint="curve")
    for px, py in (pts[0:2], pts[2:4], pts[4:6]):
        d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2],
                  fill=WHITE)


def chip(base, d, x, y, text, h=44, fsize=20, fg=WHITE, outline=None,
         fill=(255, 255, 255, 18), pad=16, bold=True):
    f = font(BOLD if bold else REG, fsize)
    tw = d.textlength(text, font=f) / S
    w = tw + pad * 2
    glass(base, (x, y, x + w, y + h), h / 2, fill,
          outline=outline, width=2)
    d.text(((x + pad) * S, (y + (h - fsize) / 2 - fsize * 0.18) * S), text,
           font=f, fill=fg)
    return x + w


def headline(d, x, y, lines, size, max_w):
    full = ["".join(seg[0] for seg in segs) for segs in lines]
    f = fit_font(full, BLACK, size, 30, max_w, d)
    for segs in lines:
        cx = x * S
        for t, c in segs:
            d.text((cx, y * S), t, font=f, fill=c)
            cx += d.textlength(t, font=f)
        y += int(size * 1.14)
    return y


def cta_block(base, d, x, y, pill_h, cta_size, label):
    f_lab = font(BOLD, 22)
    draw_tracked(d, x, y, label, f_lab, GOLD, 6 * S)
    y += 42
    f_cta = font(BLACK, cta_size)
    txt = "cotizat.online"
    tw = d.textlength(txt, font=f_cta)
    pw = tw / S + 100
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x * S, (y + 8) * S, (x + pw) * S, (y + pill_h + 8) * S],
        radius=pill_h * S // 2, fill=(0, 0, 0, 110))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9 * S)))
    glass(base, (x, y, x + pw, y + pill_h), pill_h / 2, (*GOLD, 255))
    d.text((x * S + (pw * S - tw) / 2,
            y * S + (pill_h * S - cta_size * S) / 2 - cta_size * S * 0.16),
           txt, font=f_cta, fill=(11, 34, 68))
    return y + pill_h


def paste_photo(base, W, H, width_px, cx_frac=0.60, feather=140):
    foto = Image.open(FOTO).convert("RGB")
    scale = H / foto.height
    fh = round(foto.width * scale)
    foto = foto.resize((fh, H), Image.Resampling.LANCZOS)
    cx = int(fh * cx_frac)
    x0s = min(max(cx - width_px // 2, 0), fh - width_px)
    foto = foto.crop((x0s, 0, x0s + width_px, H))
    tint = Image.new("RGB", foto.size, NAVY_BOT)
    foto = Image.blend(foto, tint, 0.16)
    mask = Image.new("L", (width_px, H), 255)
    mp = mask.load()
    for xx in range(feather):
        t = xx / feather
        val = int(255 * (t * t * (3 - 2 * t)))
        for yy in range(H):
            mp[xx, yy] = val
    base.paste(foto, (W - width_px, 0), mask)


def downscale(base, W, H):
    return base.resize((W, H), Image.Resampling.LANCZOS)


def benefit_float_1x(final, bx, by, bw, bh):
    """Tarjeta blanca con los números reales del ejemplo de la app."""
    sh = Image.new("RGBA", final.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([bx + 6, by + 8, bx + bw, by + bh],
                                         radius=14, fill=(0, 0, 0, 110))
    base = Image.alpha_composite(final.convert("RGBA"),
                                 sh.filter(ImageFilter.GaussianBlur(10)))
    ov = Image.new("RGBA", final.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14,
                        fill=(255, 255, 255, 244))
    f_cap = ImageFont.truetype(str(FONTS / BOLD), 14)
    d.text((bx + 22, by + 14), "EJEMPLO DESDE LA PROPIA APP", font=f_cap,
           fill=(*NAVY_BOT, 150))
    f_big = ImageFont.truetype(str(FONTS / BLACK), 30)
    d.text((bx + 22, by + 36), "+651,47 US$", font=f_big, fill=GOLD_DARK)
    f_sm = ImageFont.truetype(str(FONTS / REG), 16)
    d.text((bx + 22, by + 78), "de beneficio (+35 %) en una remodelación",
           font=f_sm, fill=NAVY_TOP)
    d.text((bx + 22, by + 102), "98 h-hombre · ≈ 6 días de obra",
           font=f_sm, fill=(*NAVY_TOP, 210))
    return Image.alpha_composite(base, ov).convert("RGB")


# ── flyer de feed ────────────────────────────────────────────────────────────

ADV_STANDALONE = [
    ("Genera presupuestos en minutos",
     "catálogo propio, plantillas y PDF profesional"),
    ("Gestiona y controla cada venta",
     "estados, cambios de alcance, cobros y WhatsApp"),
    ("Precios de mercado de tu país",
     "388 recursos verificados, con fuente y fecha"),
    ("Tu moneda y tu normativa local",
     "17 monedas · IVA e ID fiscal propios"),
    ("Beneficio y horas a la vista",
     "margen por partida · horas-hombre de la obra"),
    ("APU, CYPE, BC3 y planos",
     "edita rendimientos · mide m² · exporta DXF"),
]

LABEL_TXT = "GENERADOR DE PRESUPUESTOS"   # etiqueta: qué es el producto
SUB_TXT = "de obra, en tu moneda y con tu normativa"


def build_standalone(W, H, cfg, out_name):
    base, d = new_base(W, H)
    x = 64
    header(base, d, 92, 54, cfg["tagline"])

    # Etiqueta de producto: deja claro lo que es CotizaT
    draw_tracked(d, x, cfg["label_y"], LABEL_TXT, font(BOLD, 22),
                 GOLD, 6 * S)

    y = headline(d, x, cfg["head_y"], [
        [("Genera y gestiona", WHITE)],
        [("tus presupuestos", GOLD)],
    ], cfg["head"], cfg["text_w"])

    f_sub = font(REG, cfg["sub"])
    d.text((x * S, (y + 4) * S), SUB_TXT, font=f_sub, fill=LIGHT)
    y += int(cfg["sub"] * 1.9)

    f_adv = font(BOLD, cfg["adv"])
    f_adv_sub = font(REG, cfg["adv_sub"])
    for title, sub in ADV_STANDALONE:
        draw_check(base, x + 21, y + cfg["adv"] // 2 + 2, 21)
        d.text(((x + 58) * S, y * S), title, font=f_adv, fill=WHITE)
        d.text(((x + 58) * S, (y + cfg["adv"] + 4) * S), sub,
               font=f_adv_sub, fill=LIGHT)
        y += cfg["adv_row"]

    cta_block(base, d, x, y + cfg["gap_cta"], cfg["cta_h"], cfg["cta"],
              "PRUÉBALO HOY EN TU PAÍS")

    final = downscale(base, W, H).convert("RGB")
    paste_photo(final, W, H, cfg["photo_w"], cx_frac=0.60)
    final = benefit_float_1x(final, *cfg["bene"])

    out = OUT / out_name
    final.save(out, "PNG", optimize=True)
    print("OK", out)


CFG_STANDALONE_11 = dict(
    text_w=536, tagline="Para construcción y remodelación · 18 países",
    label_y=202, head=54, head_y=238, sub=27,
    adv=28, adv_sub=21, adv_row=74,
    gap_cta=22, cta=40, cta_h=76,
    photo_w=396, bene=(706, 1080 - 200 - 34, 310, 148))

CFG_STANDALONE_45 = dict(
    text_w=536, tagline="Para construcción y remodelación · 18 países",
    label_y=262, head=60, head_y=300, sub=28,
    adv=29, adv_sub=22, adv_row=92,
    gap_cta=30, cta=42, cta_h=84,
    photo_w=396, bene=(706, 1350 - 200 - 40, 310, 160))


# ── página de Facebook: perfil y portada ─────────────────────────────────────

def build_profile():
    """Foto de perfil de la página: el ícono oficial de la app (512×512).

    Facebook lo muestra a 170 px (página) y en círculo a 40 px (comentarios);
    usar el ícono de marca tal cual da máxima nitidez y reconocimiento.
    """
    logo = LOGO_IMG.resize((512, 512), Image.Resampling.LANCZOS)
    out = OUT / "cotizat-perfil-facebook-512x512.png"
    logo.save(out, "PNG", optimize=True)
    print("OK", out)


def build_cover():
    """Portada 1640×624: Facebook la muestra a 820×312 (escritorio) y
    640×360 (móvil, recortando laterales). Todo el contenido de marca va en
    la zona segura central; la esquina inferior izquierda queda libre porque
    allí es donde Facebook superpone la foto de perfil.
    """
    W, H = 1640, 624
    base, d = new_base(W, H)
    x = 200

    paste_logo(base, (x, 82), 92)
    f_mark = font(BLACK, 58)
    mx = (x + 92 + 22) * S
    my = (82 + (92 - 58) / 2 - 2) * S
    d.text((mx, my), "Cotiza", font=f_mark, fill=WHITE)
    d.text((mx + d.textlength("Cotiza", font=f_mark), my), "T",
           font=f_mark, fill=GOLD)

    tag = font(REG, 26)
    d.text((mx, my + 58 * S + 10 * S),
           "Generador de presupuestos y gestión comercial", font=tag,
           fill=LIGHT)

    y = headline(d, x, 250, [
        [("Genera y gestiona", WHITE)],
        [("tus presupuestos de obra", GOLD)],
    ], 54, 900)

    f_sub = font(REG, 27)
    d.text((x * S, (y + 12) * S),
           "con los precios, la moneda y la normativa de tu país",
           font=f_sub, fill=LIGHT)

    # chips de credibilidad + CTA (la 4ª es el botón dorado)
    cy = y + 70
    cx = x
    for t in ["18 países", "17 monedas", "IVA e ID fiscal propios"]:
        cx = chip(base, d, cx, cy, t, h=48, fsize=22, fg=WHITE,
                  outline=(*GOLD, 160), pad=20) + 14
    chip(base, d, cx, cy, "cotizat.online", h=48, fsize=23, fg=NAVY_TOP,
         fill=(*GOLD, 255), pad=22)

    final = downscale(base, W, H).convert("RGB")
    paste_photo(final, W, H, 520, cx_frac=0.60, feather=160)

    out = OUT / "cotizat-portada-facebook-1640x624.png"
    final.save(out, "PNG", optimize=True)
    print("OK", out)


if __name__ == "__main__":
    build_standalone(1080, 1080, CFG_STANDALONE_11,
                     "cotizat-flyer-facebook-1080x1080.png")
    build_standalone(1080, 1350, CFG_STANDALONE_45,
                     "cotizat-flyer-facebook-1080x1350.png")
    build_profile()
    build_cover()
