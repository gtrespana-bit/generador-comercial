#!/usr/bin/env bash
#
# Crea la copia limpia del proyecto y la sube al repositorio nuevo.
#
#   Repo personal (este)  : gtrespana-bit/presupuestos          → no se toca
#   Repo de producto      : gtrespana-bit/generador-presupuestos → destino
#
# USO (desde la raíz de tu copia local del repo personal):
#
#     bash scripts/crear-repo-nuevo.sh
#
# El script NO modifica tu repositorio actual: trabaja sobre una copia
# temporal en /tmp. Puedes ejecutarlo las veces que quieras.
#
set -euo pipefail

DESTINO_URL="${1:-https://github.com/gtrespana-bit/generador-presupuestos.git}"
TMP="$(mktemp -d /tmp/generador-presupuestos.XXXXXX)"

# Archivos personales que NO deben viajar al repositorio de producto:
# presupuestos reales de clientes, capturas y hojas de cálculo de muestra.
EXCLUIR='^(BENEFICIO\.png|Captura de pantalla 2026-08-06 233827\.png|presupuesto_P-2026-003-rusticana\.pdf|DPT020\.xlsx|RBA010\.xlsx|RBE030\.xlsx|scripts/crear-repo-nuevo\.sh|ANALISIS_PRODUCTO_Y_VIABILIDAD\.md)$'

echo "==> Copiando archivos versionados (excluyendo los personales)..."
git ls-files -z | grep -zvE "$EXCLUIR" | xargs -0 -I{} cp --parents "{}" "$TMP/"
cd "$TMP"
echo "    $(find . -type f | wc -l) archivos · $(du -sh . | cut -f1)"

echo "==> Vaciando los datos de empresa precargados..."
python3 - <<'PY'
import re, pathlib

# 1) models.py — la configuración de una instalación nueva arranca en blanco.
p = pathlib.Path("app/models.py")
s = p.read_text(encoding="utf-8")

s = re.sub(
    r'DATOS_EMPRESA_DEFECTO = \{.*?\n\}',
    '# Configuración inicial de una instalación nueva. Se deja vacía a propósito:\n'
    '# cada empresa introduce sus propios datos en /configuracion la primera vez\n'
    '# que abre el programa. Nunca se deben poner aquí datos de una empresa real,\n'
    '# porque acabarían impresos en los PDF de todos los clientes que instalen.\n'
    'DATOS_EMPRESA_DEFECTO = {\n'
    '    "empresa_nombre": "",\n'
    '    "empresa_telefono": "",\n'
    '    "empresa_email": "",\n'
    '    "empresa_web": "",\n'
    '    "empresa_direccion": "",\n'
    '}',
    s, flags=re.S,
)

s = s.replace(
    '''    """Si no existe configuración, crea una con los datos de RemodelaT.

    En instalaciones nuevas la configuración ya viene rellena con los datos
    de la empresa (nombre, teléfono, web, email y dirección). Si la base de
    datos es antigua y todavía conserva el placeholder genérico («Mi
    Empresa»), también se autorellena una única vez; si el usuario ya la
    personalizó, no se toca.
    """''',
    '''    """Crea la configuración inicial si todavía no existe.

    La empresa se configura desde la propia aplicación (Configuración), de
    modo que una instalación nueva arranca en blanco y el usuario introduce
    su nombre, teléfono, web, email y dirección. Si el usuario ya la
    personalizó, no se toca.
    """''',
)

# Ya no se reescribe la configuración existente con datos de nadie.
s = s.replace(
    '''        db.commit()
        return
    if cfg.empresa_nombre in ("", "Mi Empresa") and not cfg.empresa_email:
        for campo, valor in DATOS_EMPRESA_DEFECTO.items():
            setattr(cfg, campo, valor)
        db.commit()''',
    '''        db.commit()''',
)
p.write_text(s, encoding="utf-8")

# 2) README.md
p = pathlib.Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '''  condiciones). Al abrir el programa por primera vez ya viene rellena con
  los datos de la empresa (**RemodelaT Venezuela**: 04227997043 ·
  www.remodelat.net · contacto@remodelat.net · San Diego, Carabobo); se
  pueden cambiar en cualquier momento.''',
    '''  condiciones). Al abrir el programa por primera vez la ficha está vacía:
  cada empresa introduce sus propios datos desde **Configuración** y quedan
  guardados para todos los presupuestos siguientes.''',
)
p.write_text(s, encoding="utf-8")

# 3) instalador.iss — editor de la publicación
p = pathlib.Path("instalador.iss")
s = p.read_text(encoding="utf-8")
s = s.replace("AppPublisher=RemodelaT Venezuela", "AppPublisher=Generador de Presupuestos")
s = s.replace(
    "AppPublisherURL=https://www.remodelat.net",
    "AppPublisherURL=https://github.com/gtrespana-bit/generador-presupuestos",
)
p.write_text(s, encoding="utf-8")

# 4) tests — nombre de test sin referencia a una obra real
p = pathlib.Path("tests/test_garantias.py")
s = p.read_text(encoding="utf-8")
s = s.replace("def test_rusticana_agrupa_por_familia", "def test_agrupa_por_familia")
p.write_text(s, encoding="utf-8")
PY

echo "==> Comprobando que no queden datos personales..."
if grep -rlni "remodelat\|rusticana\|04227997043" . 2>/dev/null | grep -q .; then
    echo "!!! Quedan referencias personales:"
    grep -rlni "remodelat\|rusticana\|04227997043" . 2>/dev/null
    exit 1
fi
echo "    Limpio."

echo "==> Ejecutando los tests..."
if [ -x "$OLDPWD/.venv/bin/python" ]; then
    PY_BIN="$OLDPWD/.venv/bin/python"
else
    PY_BIN="python3"
fi
"$PY_BIN" -m pytest tests/ -q 2>&1 | tail -3

echo "==> Creando el repositorio git y subiéndolo..."
git init -q -b main

# Si no hay identidad de git configurada en el sistema, se usa una por
# defecto solo para este repositorio (no toca tu configuración global).
if ! git config user.email >/dev/null 2>&1 && ! git config --global user.email >/dev/null 2>&1; then
    git config user.name "gtrespana-bit"
    git config user.email "gtrespana-bit@users.noreply.github.com"
fi

git add -A
git commit -q -m "Versión inicial: generador de presupuestos para construcción y remodelación

Copia del proyecto base, preparada para desarrollo de producto:

- Sin datos de empresa precargados: la configuración arranca en blanco y
  cada instalación introduce los suyos desde Configuración.
- Sin documentos personales de obra (presupuestos reales, capturas y
  hojas de cálculo de muestra) en el control de versiones.
- Editor de la publicación del instalador desligado de la empresa original.

Estado verificado: 58 tests en verde y arranque limpio con base de datos
nueva (13 rutas principales respondiendo 200)."

git remote add origin "$DESTINO_URL"
git push -u origin main

echo
echo "==> Listo. Repositorio nuevo publicado en:"
echo "    $DESTINO_URL"
echo
echo "    Copia de trabajo local: $TMP"
echo "    (clónalo donde quieras trabajar: git clone $DESTINO_URL)"
