"""Genera la matriz nacional inicial de precios de recursos LatAm.

No inventa precios: crea filas pendientes para todos los recursos y rellena
solo referencias iniciales documentadas en INVESTIGACION_PRECIOS_RONDA_1 y 5.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_latam.csv"
PAISES = [("CO", "COP"), ("PE", "PEN"), ("MX", "MXN"), ("EC", "USD")]

# Referencias centrales conservadoras, basadas en las rondas documentadas.
REFERENCIAS = {
    "MT-CEMENTO": {"CO": 560, "PE": 31.0/42.5, "MX": 240.0/50, "EC": 8.5/50, "unidad": "kg"},
    "MT-ARENA": {"CO": 100000, "PE": 85, "MX": 600, "EC": 20, "unidad": "m3"},
    "MT-PIEDRA-PIC": {"CO": 115000, "PE": 100, "MX": 500, "EC": 20, "unidad": "m3"},
    "MT-ACERO-CAB": {"CO": 4000, "PE": 0.95, "MX": 22, "EC": 0.98, "unidad": "kg"},
    "MT-BLQ-15": {"CO": 2600, "PE": 1.5, "MX": 17, "EC": 0.43, "unidad": "ud"},
    "MT-LADRILLO": {"CO": 1000, "PE": 1.5, "MX": 6.4, "EC": 0.3, "unidad": "ud"},
    "MO-OF1": {"CO": 110000 / 8, "PE": 69.75 / 8, "MX": 750 / 8, "EC": 21.67 / 8, "unidad": "h"},
    "MO-AYU": {"CO": 72000 / 8, "PE": 62.80 / 8, "MX": 400 / 8, "EC": 20 / 8, "unidad": "h"},
    "MT-PYL-PLACA125": {"CO": 48900/2.9768, "PE": 28.3/2.9768, "MX": 210/2.9768, "EC": 10.67/2.9768, "unidad": "m2"},
    "MT-PYL-PLACA-RH": {"CO": 91700/2.9768, "PE": 49.9/2.9768, "MX": 289/2.9768, "EC": 17.11/2.9768, "unidad": "m2"},
    "MT-ADH-C2TE": {"CO": 3454/25, "PE": 36.9/25, "MX": 401/25, "EC": 13.43/20, "unidad": "kg"},
    "MT-ADH-C1": {"CO": 1276/25, "PE": 16.9/25, "MX": 300/25, "EC": 10/20, "unidad": "kg"},
    "MT-PIN-CAUCHO": {"CO": 60700/3.785, "PE": 55, "MX": 180, "EC": 17, "unidad": "l"},
    "MT-PLO-PVC4": {"CO": 21750, "PE": 4.1, "MX": 4.1, "EC": 4.8, "unidad": "m"},
    "MT-ELE-CABLE": {"CO": 3975, "PE": 2.86, "MX": 0.95, "EC": 0.90, "unidad": "m"},
    "MT-PIN-FONDO": {"CO": 32500/3.785, "PE": 18, "MX": 140, "EC": 16, "unidad": "l"},
    "MT-PIN-MASILLA": {"CO": 46500/14, "PE": 2.5, "MX": 12, "EC": 1.5, "unidad": "kg"},
    "MT-MANTO-ASF": {"CO": 5.6, "PE": 22, "MX": 180, "EC": 8.5, "unidad": "m2"},
    "MT-ACRIL-IMPER": {"CO": 70000/19, "PE": 12, "MX": 799/19, "EC": 4.4, "unidad": "l"},
    "MT-MALLA-ELEC": {"CO": 150000/30, "PE": 220/30, "MX": 800/30, "EC": 5.5, "unidad": "m2"},
    "MT-ELE-TUB20": {"CO": 2500, "PE": 1.2, "MX": 18, "EC": 1.2, "unidad": "m"},
    "MT-ELE-MECA": {"CO": 12000, "PE": 18, "MX": 90, "EC": 6, "unidad": "ud"},
    "MT-PYL-CANAL": {"CO": 5200, "PE": 2.2, "MX": 90, "EC": 2.0, "unidad": "m"},
}

def iter_recursos(data):
    for categoria, grupo in data.items():
        if not isinstance(grupo, dict) or categoria.startswith("_"):
            continue
        for codigo, item in grupo.items():
            if not isinstance(item, dict) or "descripcion" not in item:
                continue
            yield codigo, categoria, item

def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = []
    for codigo, categoria, item in iter_recursos(data):
        for pais, moneda in PAISES:
            ref = REFERENCIAS.get(codigo, {})
            precio = ref.get(pais, "")
            rows.append({
                "codigo_recurso": codigo,
                "descripcion": item.get("descripcion", ""),
                "categoria": categoria,
                "unidad_fuente": ref.get("unidad", item.get("unidad", "ud")),
                "pais_codigo": pais,
                "moneda": moneda,
                "precio_referencia": precio,
                "precio_min": "",
                "precio_max": "",
                "fuente": "docs/INVESTIGACION_PRECIOS_RONDA_5_MANO_OBRA.md" if categoria == "mano_obra" and precio != "" else ("docs/INVESTIGACION_PRECIOS_RONDA_1.md" if precio != "" else ""),
                "fecha_consulta": "2026-08-19" if precio != "" else "",
                "confianza": "referencia" if precio != "" else "pendiente",
                "incluye_iva": "por_verificar",
                "incluye_transporte": "no_confirmado",
                "origen": "nacional" if precio != "" else "pendiente",
                "observaciones": "Referencia central; validar presentación y proveedor." if precio != "" else "Pendiente de investigación específica.",
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter=";")
        writer.writeheader(); writer.writerows(rows)
    print(f"Generadas {len(rows)} filas en {OUT}")

if __name__ == "__main__":
    main()
