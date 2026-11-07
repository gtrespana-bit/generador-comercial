#!/usr/bin/env python3
"""Propone cruces entre recursos y precios simples de bases BC3, sin aplicar precios.

Ejemplo: python tools/cruzar_precios_bc3.py --fuente 'Extremadura 2026|Extremadura|https://www.juntaex.es/w/base-precios-construccion-2026|/tmp/extremadura.bc3' --salida /tmp/candidatos.csv
Los prefijos P/M/O son propios de esta base; compruebe otras bases antes de usarlos.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITORIA = ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv'
# Conservador: nunca convertir magnitudes o cantidades sin datos de la fuente.
UNIDADES = {'ud': 'ud', 'u': 'ud', 'un': 'ud', 'unidad': 'ud', 'm': 'm',
            'm2': 'm2', 'm3': 'm3', 'kg': 'kg', 'l': 'l', 'h': 'h', 'hora': 'h'}
STOP = set('de del la el los las un una y en por para con sin al a o su se sus obra obras suministro colocacion incluye incluido'.split())

@dataclass(frozen=True)
class Precio:
    codigo: str
    unidad: str
    descripcion: str
    texto: str
    importe: Decimal
    categoria: str
    fecha_fuente: str

def limpiar(texto: str) -> str:
    # Normalizar símbolos antes de quitar acentos.
    texto = texto.lower().replace('²', '2').replace('³', '3').replace(',', '.')
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))

def unidad(texto: str) -> str | None:
    return UNIDADES.get(limpiar(texto).strip().rstrip('.'))

def tokens(texto: str) -> set[str]:
    palabras = re.findall(r'[a-z]+|\d+(?:\.\d+)?', limpiar(texto))
    return {p[:-1] if len(p) > 5 and p.endswith('s') else p for p in palabras
            if p not in STOP and (len(p) >= 3 or p.isdigit())}

def leer_bc3(path: Path) -> tuple[list[Precio], str]:
    bruto = path.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    if bruto.startswith(b'\xef\xbb\xbf'):
        texto = bruto.decode('utf-8-sig')
    elif bruto.startswith((b'\xff\xfe', b'\xfe\xff')):
        texto = bruto.decode('utf-16')
    else:
        try:
            texto = bruto.decode('utf-8')
        except UnicodeDecodeError:
            # Las bases reales mezclan cp1252 con bytes sueltos (0x81, 0x8d…):
            # se sustituye el caracter dudoso en vez de abortar el archivo.
            texto = bruto.decode('cp1252', errors='replace')
    registros = re.split(r'~(?=[A-Za-z]\|)', texto)
    conceptos, descripciones, descompuestos = {}, {}, set()
    for registro in registros:
        partes = registro.split('|')
        if len(partes) < 3:
            continue
        tipo, codigo = partes[0].upper(), partes[1].strip()
        if tipo == 'D':
            # Cualquier descomposición excluye una unidad de obra o auxiliar.
            descompuestos.add(codigo)
        elif tipo == 'T':
            descripciones[codigo] = partes[2].strip()
        elif tipo == 'C' and len(partes) >= 5:
            if not codigo or '#' in codigo or codigo in conceptos:
                continue
            u = unidad(partes[2]); precio = partes[4].strip()
            # Listas de precios por zona, vacíos o signos ambiguos no se adivinan.
            if not u or not re.fullmatch(r'\d+(?:[.,]\d+)?', precio):
                continue
            try: valor = Decimal(precio.replace(',', '.'))
            except InvalidOperation: continue
            if not valor.is_finite() or valor <= 0:
                continue
            categoria = {'P': 'materiales', 'M': 'maquinaria', 'O': 'mano_obra'}.get(codigo[:1].upper())
            if categoria:
                conceptos[codigo] = (u, partes[3].strip(), valor, categoria, partes[5].strip() if len(partes) > 5 else '')
    return [Precio(c, u, d, descripciones.get(c, ''), p, cat, fecha)
            for c, (u, d, p, cat, fecha) in conceptos.items() if c not in descompuestos], sha

def candidatos(recursos, precios, limite=5):
    # El texto completo aporta términos; el resumen pesa doble en caso de empates.
    docs = [(p, tokens(p.descripcion), tokens(p.descripcion + ' ' + p.texto)) for p in precios]
    frecuencia = Counter(t for _, _, ts in docs for t in ts)
    n = len(docs)
    for r in recursos:
        rt = tokens(r['descripcion']); ru = unidad(r['unidad'])
        resultados = []
        for p, resumen, completo in docs:
            if p.categoria != r['categoria'] or p.unidad != ru:
                continue
            comunes = rt & completo
            if not comunes: continue
            peso = sum(math.log((n + 1) / (1 + frecuencia[t])) + 1 for t in comunes)
            total = sum(math.log((n + 1) / (1 + frecuencia[t])) + 1 for t in rt) or 1
            puntaje = peso / total + 0.15 * len(rt & resumen) / max(len(rt), 1)
            numeros_r = {t for t in rt if re.fullmatch(r'\d+(?:\.\d+)?', t)}
            numeros_p = {t for t in completo if re.fullmatch(r'\d+(?:\.\d+)?', t)}
            alerta = 'numeros_diferentes_o_ausentes' if numeros_r and not numeros_r <= numeros_p else ''
            resultados.append((puntaje, p.codigo, p, alerta, ', '.join(sorted(comunes))))
        resultados.sort(key=lambda x: (-x[0], x[1]))
        yield r, resultados[:limite]

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fuente', action='append', required=True, help='Nombre|ámbito|URL oficial|ruta local BC3; repetir por fuente')
    ap.add_argument('--salida', type=Path, required=True)
    ap.add_argument('--limite', type=int, default=5)
    args = ap.parse_args()
    if args.limite < 1 or args.limite > 50: ap.error('--limite debe estar entre 1 y 50')
    with AUDITORIA.open(encoding='utf-8-sig', newline='') as f:
        recursos = list(csv.DictReader(f, delimiter=';'))
    fields = ['codigo_recurso','descripcion_recurso','unidad_recurso','estado_auditoria','fuente','ambito','url','sha256_bc3','rango','codigo_fuente','descripcion_fuente','texto_fuente','unidad_fuente','precio_fuente','fecha_fuente_bc3','puntuacion','palabras_comunes','alerta','decision']
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=';'); writer.writeheader()
        for fuente in args.fuente:
            partes = fuente.split('|', 3)
            if len(partes) != 4 or not all(partes): ap.error('--fuente requiere nombre|ámbito|url|ruta')
            nombre, ambito, url, ruta = partes
            precios, sha = leer_bc3(Path(ruta))
            if not precios: raise ValueError(f'{nombre}: no se encontraron precios simples con prefijos P/M/O y unidades reconocidas')
            encontrados = 0
            for r, filas in candidatos(recursos, precios, args.limite):
                base = dict(codigo_recurso=r['codigo_recurso'], descripcion_recurso=r['descripcion'], unidad_recurso=r['unidad'], estado_auditoria=r['estado_auditoria'], fuente=nombre, ambito=ambito, url=url, sha256_bc3=sha, decision='pendiente_revision')
                if not filas:
                    writer.writerow(dict(base, alerta='sin_candidatos'))
                for pos,(score,_,p,alerta,comunes) in enumerate(filas,1):
                    encontrados += 1
                    writer.writerow(dict(base, rango=pos, codigo_fuente=p.codigo, descripcion_fuente=p.descripcion, texto_fuente=p.texto, unidad_fuente=p.unidad, precio_fuente=str(p.importe), fecha_fuente_bc3=p.fecha_fuente, puntuacion=f'{score:.4f}', palabras_comunes=comunes, alerta=alerta))
            print(f'{nombre}: {len(precios)} precios simples, {encontrados} candidatos propuestos para {len(recursos)} recursos; SHA256 {sha}')
    print(f'Escrito {args.salida}. No se ha cambiado ningún precio ni estado.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
