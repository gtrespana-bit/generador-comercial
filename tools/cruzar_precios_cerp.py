#!/usr/bin/env python3
"""Cruce propositivo de básicos CERP/BCCA, sin modificar precios de catálogo."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
if __package__:
    from .cruzar_precios_bc3 import AUDITORIA, Precio, candidatos, unidad
else:
    from cruzar_precios_bc3 import AUDITORIA, Precio, candidatos, unidad


def leer_cerp(path: Path):
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    root = json.loads(data, parse_float=Decimal)
    if not isinstance(root, dict) or not isinstance(root.get('items'), list):
        raise ValueError('Formato CERP inválido')
    tipos = {'material': 'materiales', 'machinery': 'maquinaria', 'labor': 'mano_obra'}
    precios = []
    for item in root['items']:
        cat = tipos.get(item.get('kind'))
        un = unidad(item.get('unit') or '')
        lista = item.get('prices') or []
        if (not cat or not un or item.get('bom') or len(lista) != 1 or not item.get('summary')):
            continue
        p = lista[0]
        scope = p.get('scope') or {}
        if (p.get('source') != 'bcca' or p.get('currency') != 'EUR' or
                scope.get('country') != 'ES' or scope.get('region') != 'AND' or
                not p.get('sourceCode') or not p.get('date') or not p.get('edition')):
            continue
        try:
            val = Decimal(str(p['value']))
        except (KeyError, InvalidOperation, ValueError):
            continue
        if not val.is_finite() or val <= 0:
            continue
        precios.append(Precio(p['sourceCode'], un, item['summary'], item.get('text') or '', val, cat, p['edition'] + '|' + p['date']))
    if not precios:
        raise ValueError('No hay precios simples BCCA utilizables')
    return precios, sha, root.get('version', '')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archivo', type=Path)
    ap.add_argument('--salida', required=True, type=Path)
    ap.add_argument('--limite', type=int, default=5)
    args = ap.parse_args()
    if not 1 <= args.limite <= 50:
        ap.error('limite fuera de rango')
    precios, sha, version = leer_cerp(args.archivo)
    with AUDITORIA.open(encoding='utf-8-sig', newline='') as f:
        recursos = list(csv.DictReader(f, delimiter=';'))
    fields = ['codigo_recurso','descripcion_recurso','unidad_recurso','categoria','usos','estado_auditoria',
              'codigo_fuente','descripcion_fuente','texto_fuente','unidad_fuente','precio_fuente','edicion_fuente','fecha_precio',
              'rango','puntuacion','palabras_comunes','alerta','decision']
    counts = {'con_candidatos': 0, 'sin_candidatos': 0, 'candidatos': 0}
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=';', lineterminator='\n'); w.writeheader()
        for r, hits in candidatos(recursos, precios, args.limite):
            base = {'codigo_recurso': r['codigo_recurso'], 'descripcion_recurso': r['descripcion'],
                    'unidad_recurso': r['unidad'], 'categoria': r['categoria'], 'usos': r['partidas_que_lo_usan'],
                    'estado_auditoria': r['estado_auditoria'], 'decision': 'pendiente_revision'}
            counts['con_candidatos' if hits else 'sin_candidatos'] += 1
            if not hits:
                w.writerow(dict(base, alerta='sin_candidatos'))
            for i, (score, _, p, alerta, comunes) in enumerate(hits, 1):
                counts['candidatos'] += 1
                w.writerow(dict(base, codigo_fuente=p.codigo, descripcion_fuente=p.descripcion,
                    texto_fuente=p.texto, unidad_fuente=p.unidad, precio_fuente=str(p.importe),
                    edicion_fuente=p.fecha_fuente.split('|', 1)[0], fecha_precio=p.fecha_fuente.split('|', 1)[1], rango=i, puntuacion=f'{score:.4f}',
                    palabras_comunes=comunes, alerta=alerta))
    print(f'CERP {version}; sha256={sha}; básicos utilizables={len(precios)}; {counts}')
    print(f'Escrito {args.salida}; candidatos sin validar, no se han modificado precios.')

if __name__ == '__main__':
    main()
