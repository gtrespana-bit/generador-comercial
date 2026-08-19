"""Completa una matriz de respaldo desde el precio base USD.

Los valores completados quedan claramente marcados como `base`/`provisional`.
Nunca sustituyen los 92 precios investigados ni se importan por defecto.
"""
from pathlib import Path
import csv, json
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'basedatos_partidas/datos/recursos.json'
IN=ROOT/'basedatos_partidas/salida/precios_recursos_latam.csv'
OUT=ROOT/'basedatos_partidas/salida/precios_recursos_latam_completa.csv'
RATES={'CO':3128.65,'PE':3.37,'MX':17.06,'EC':1.0}
CURRENCY={'CO':'COP','PE':'PEN','MX':'MXN','EC':'USD'}

def main():
 data=json.loads(SRC.read_text(encoding='utf8'))
 base={}
 for fam,items in data.items():
  if isinstance(items,dict):
   for code,item in items.items():
    if isinstance(item,dict) and item.get('precio') is not None:
     try: base[code]=float(item['precio'])
     except (TypeError,ValueError): pass
 rows=[]
 with IN.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f,delimiter=';'))
 for r in rows:
  if str(r.get('precio_referencia') or '').strip(): continue
  code=r['codigo_recurso']; usd=base.get(code)
  if usd is None: continue
  pais=r['pais_codigo']; r['precio_referencia']=f'{usd*RATES[pais]:.6f}'.rstrip('0').rstrip('.')
  r['fuente']='Precio base USD convertido; respaldo provisional, revisar con proveedor'
  r['fecha_consulta']='2026-08-19'; r['confianza']='provisional'; r['origen']='base'; r['incluye_iva']='por_verificar'; r['incluye_transporte']='no'; r['observaciones']='Respaldo convertido desde el precio base USD; no es precio local confirmado.'
 with OUT.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';'); w.writeheader(); w.writerows(rows)
 print('filas',len(rows),'con precio',sum(bool(str(r.get('precio_referencia') or '').strip()) for r in rows),'investigadas',sum(r.get('origen')=='nacional' for r in rows),'respaldo',sum(r.get('origen')=='base' for r in rows))
if __name__=='__main__': main()
