"""Los IDs Alembic revisados son falsos positivos, no una exclusión de archivos."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCHIVOS = (
    "app/database.py",
    "docs/staging_upgrade_a8f1c3d9e7b2.sql",
    "docs/staging_upgrade_bd832a2b009e.sql",
    "migrations/versions/a8f1c3d9e7b2_organizacion_es_test.py",
)


def _claves(datos):
    return {
        (archivo, item["hashed_secret"], item["type"])
        for archivo, hallazgos in datos["results"].items()
        for item in hallazgos
    }


def _scan(tmp_path, extra=False):
    baseline = json.loads((REPO / ".secrets.baseline").read_text())
    copia = tmp_path / "baseline.json"
    copia.write_text(json.dumps(baseline))
    for nombre in ARCHIVOS:
        destino = tmp_path / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes((REPO / nombre).read_bytes())
    # El valor sintético se genera en tiempo de ejecución y no es una credencial.
    muestra = hashlib.sha256(b"muestra sintetica para detector de secretos").hexdigest()
    if extra:
        with (tmp_path / ARCHIVOS[0]).open("a") as fichero:
            fichero.write('\nvalor_de_prueba = "' + muestra + '"\n')
    subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan", "--baseline", str(copia), *ARCHIVOS],
        cwd=tmp_path, check=True, capture_output=True, text=True,
    )
    return _claves(json.loads(copia.read_text())) - _claves(baseline), muestra


def test_ids_de_migracion_no_generan_hallazgos_nuevos(tmp_path):
    nuevas, _ = _scan(tmp_path)
    assert not nuevas


def test_se_detecta_otro_valor_en_un_archivo_con_id_aceptado(tmp_path):
    nuevas, muestra = _scan(tmp_path, extra=True)
    assert (
        ARCHIVOS[0], hashlib.sha1(muestra.encode()).hexdigest(), "Hex High Entropy String"
    ) in nuevas
