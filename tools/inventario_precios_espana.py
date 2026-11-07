#!/usr/bin/env python3
"""Inventario integral de evidencias disponibles; no valida ni cambia precios."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITORIA = ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv'
CANDIDATOS = ROOT / 'docs/auditoria_precios/espana_candidatos_bcca_2026-11-07.csv'
MATRIZ = ROOT / 'basedatos_partidas/salida/precios_recursos_espana.csv'
SALIDA = ROOT / 'docs/auditoria_precios/espana_inventario_integral_2026-11-07.csv'


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def inventario(auditoria, candidatos, matriz):
    by_code = {}
    for row in matriz:
        if row['pais_codigo'] != 'ES':
            continue
        code = row['codigo_recurso']
        if code in by_code:
            raise ValueError(f'Matriz duplicada: {code}')
        by_code[code] = row
    grupos = defaultdict(list)
    for c in candidatos:
        grupos[c['codigo_recurso']].append(c)
    vistos, salida = set(), []
    for a in auditoria:
        code = a['codigo_recurso']
        if code in vistos or code not in by_code or code not in grupos:
            raise ValueError(f'Recurso duplicado o faltante: {code}')
        vistos.add(code)
        m, cs = by_code[code], grupos[code]
        if a['unidad'] != m['unidad_fuente'] or a['categoria'] != m['categoria']:
            raise ValueError(f'Categoría o unidad incompatible: {code}')
        hits = sorted((c for c in cs if c['codigo_fuente']), key=lambda c: int(c['rango']))
        top = hits[0] if hits else {}
        if a['estado_auditoria'] == 'confirmado_referencia':
            accion = 'mantener referencia; vigilar vigencia y alcance'
        elif a['precio_revisado']:
            accion = 'revisar reservas del precio provisional'
        elif hits:
            accion = 'contrastar candidatos antiguos con fuentes vigentes; no aplicar automáticamente'
        else:
            accion = 'buscar fuentes específicas; sin candidato BCCA textual'
        salida.append({
            'codigo_recurso': code, 'categoria': a['categoria'], 'descripcion': a['descripcion'],
            'unidad': a['unidad'], 'usos': a['partidas_que_lo_usan'],
            'estado_auditoria_actual': a['estado_auditoria'],
            'precio_matriz_actual': m['precio_referencia'], 'precio_revisado': a['precio_revisado'],
            'fuente_matriz_actual': m['fuente'], 'confianza_matriz': m['confianza'],
            'numero_candidatos_bcca': str(len(hits)), 'primer_codigo_bcca': top.get('codigo_fuente', ''),
            'primera_descripcion_bcca': top.get('descripcion_fuente', ''),
            'primer_precio_bcca': top.get('precio_fuente', ''),
            'primera_fecha_bcca': top.get('fecha_precio', ''), 'alerta_cruce': top.get('alerta', ''),
            'accion': accion,
        })
    if set(by_code) != vistos or set(grupos) != vistos:
        raise ValueError('Inventario, matriz y candidatos no cubren los mismos recursos')
    return sorted(salida, key=lambda x: (-int(x['usos']), x['codigo_recurso']))


def main():
    filas = inventario(leer(AUDITORIA), leer(CANDIDATOS), leer(MATRIZ))
    with SALIDA.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=filas[0], delimiter=';', lineterminator='\n')
        writer.writeheader(); writer.writerows(filas)
    print(f'{len(filas)} recursos en {SALIDA}; ningún candidato se ha validado ni aplicado')

if __name__ == '__main__':
    main()
