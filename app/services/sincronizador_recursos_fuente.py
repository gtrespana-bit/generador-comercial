"""Sincroniza recursos base desde basedatos_partidas/datos/recursos.json."""
from __future__ import annotations
import json
from pathlib import Path
from sqlalchemy.orm import Session
from ..models import Recurso

CATEGORIAS = {"mano_obra": "mano_obra", "materiales": "materiales", "maquinaria": "otros"}

def sincronizar_desde_json(db: Session, ruta: str | Path, organizacion_id: int) -> dict:
    data = json.loads(Path(ruta).read_text(encoding="utf-8"))
    existentes = {r.codigo: r for r in db.query(Recurso).filter(Recurso.organizacion_id == organizacion_id).all() if r.codigo}
    creados = actualizados = 0
    for familia, grupo in data.items():
        if familia.startswith("_") or not isinstance(grupo, dict):
            continue
        categoria = CATEGORIAS.get(familia, "otros")
        for codigo, item in grupo.items():
            if not isinstance(item, dict) or not item.get("descripcion"):
                continue
            r = existentes.get(codigo)
            if r is None:
                r = Recurso(organizacion_id=organizacion_id, codigo=codigo)
                db.add(r); existentes[codigo] = r; creados += 1
            # La sincronización actualiza identidad, nunca pisa el precio local.
            r.descripcion = str(item.get("descripcion") or "").strip()[:250]
            r.unidad = str(item.get("unidad") or "ud").strip()[:30] or "ud"
            r.categoria = categoria
            if not r.moneda:
                r.moneda = "USD"
            actualizados += 1
    db.commit()
    return {"creados": creados, "actualizados": actualizados, "total": len(existentes)}
