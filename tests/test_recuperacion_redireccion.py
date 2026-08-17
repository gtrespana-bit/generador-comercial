"""Rescate de enlaces de recuperación que aterrizan en la página equivocada.

Supabase solo respeta ``redirect_to`` si la URL exacta figura en su lista de
Redirect URLs. Si falta, la descarta en silencio y usa el Site URL: el enlace
del email acaba en `/` y, al exigir sesión, rebota a `/acceso`. El fragmento
`#access_token=...&type=recovery` sobrevive porque el navegador lo re-adjunta
y nunca viaja al servidor, así que la persona ve el login y el enlace parece
roto.

`recovery_redirect.js` detecta ese fragmento y reenvía a `/restablecer-clave`.
La lógica se ejercita con Node sobre un DOM mínimo: es JavaScript de navegador
y no tendría sentido reimplementarlo en Python para probarlo.
"""
from pathlib import Path
import json
import shutil
import subprocess
import textwrap

import pytest

SCRIPT = Path("app/static/js/recovery_redirect.js")
BASE = "https://cotizat-generador.vercel.app"
TOKEN = "access_token=eyJhbGciOi.PAYLOAD.SIG"

# (nombre, url de aterrizaje, destino esperado o None si no debe redirigir)
CASOS = [
    (
        "enlace mal enrutado a /acceso (caso real reportado)",
        f"{BASE}/acceso?next=/#{TOKEN}&type=recovery",
        f"/restablecer-clave#{TOKEN}&type=recovery",
    ),
    (
        "enlace mal enrutado a la raíz",
        f"{BASE}/#{TOKEN}&type=recovery",
        f"/restablecer-clave#{TOKEN}&type=recovery",
    ),
    (
        "ya está en la página correcta: no debe redirigir (evita bucle)",
        f"{BASE}/restablecer-clave#{TOKEN}&type=recovery",
        None,
    ),
    ("login normal sin fragmento", f"{BASE}/acceso", None),
    (
        "sesión de magiclink, no de recuperación",
        f"{BASE}/acceso#{TOKEN}&type=magiclink",
        None,
    ),
    ("fragmento de recuperación sin token", f"{BASE}/acceso#type=recovery", None),
    (
        "ancla corriente de la aplicación",
        f"{BASE}/presupuestos#seccion-totales",
        None,
    ),
]

RUNNER = textwrap.dedent("""
    const fs = require("node:fs");
    const src = fs.readFileSync(process.argv[1], "utf8");
    const casos = JSON.parse(process.argv[2]);

    function run(href) {
      const url = new URL(href);
      let replaced = null;
      const window = {
        location: {
          pathname: url.pathname,
          hash: url.hash,
          replace: (d) => { replaced = d; },
        },
      };
      new Function("window", "URLSearchParams", "encodeURIComponent", src)(
        window, URLSearchParams, encodeURIComponent
      );
      return replaced;
    }

    console.log(JSON.stringify(casos.map((href) => run(href))));
""")


def _ejecutar(urls: list[str]) -> list[str | None]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - depende del entorno
        pytest.skip("Node.js no está disponible para ejercitar el script.")
    salida = subprocess.run(
        [node, "-e", RUNNER, str(SCRIPT), json.dumps(urls)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(salida.stdout)


@pytest.mark.parametrize(
    "nombre,url,esperado", CASOS, ids=[caso[0] for caso in CASOS]
)
def test_rescate_de_enlace_de_recuperacion(nombre, url, esperado):
    assert _ejecutar([url])[0] == esperado, nombre


def test_enlace_caducado_lleva_a_pedir_uno_nuevo():
    """Sin token pero con error: no deja al usuario en el login sin explicación."""
    destino = _ejecutar(
        [f"{BASE}/acceso#error=access_denied&error_code=otp_expired&type=recovery"]
    )[0]
    assert destino is not None
    assert destino.startswith("/recuperar-acceso?error=")


def test_el_token_nunca_sale_del_fragmento():
    """El access token no debe acabar en la query, donde se registraría."""
    destino = _ejecutar([f"{BASE}/acceso?next=/#{TOKEN}&type=recovery"])[0]
    ruta, _, fragmento = destino.partition("#")
    assert "access_token" not in ruta
    assert "?" not in ruta
    assert "access_token" in fragmento


def test_el_script_se_carga_en_las_paginas_donde_puede_aterrizar():
    """Login y layout general: los dos destinos a los que Supabase desvía."""
    for plantilla in ("app/templates/auth/access.html", "app/templates/base.html"):
        contenido = Path(plantilla).read_text(encoding="utf-8")
        # La ruta se emite a través del filtro ``asset`` (versión cacheada), así
        # que basta con comprobar que el nombre del script está referenciado.
        assert "recovery_redirect.js" in contenido, plantilla
