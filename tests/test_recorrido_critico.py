"""E1-040 — Recorrido crítico completo sobre HTTP.

Cubre, encadenados y contra una instalación aislada en un directorio
temporal (``COTIZAT_DATA_DIR`` + ``COTIZAT_DB``):

1. instalación limpia (sin datos precargados);
2. primer inicio (asistente en ``/`` y modo limpio);
3. catálogo, cliente y primer presupuesto real;
4. descarga del PDF real y cierre de la guía de primer uso;
5. backup completo desde Configuración;
6. restauración del backup tras una pérdida de datos;
7. actualización: restaurar la copia de una versión anterior deja el
   esquema al día sin impedir el arranque.

Cada prueba corre en un subproceso porque ``app.main`` fija la base y los
directorios de datos al importarse; el patrón es el mismo que en
``tests/test_onboarding.py``.
"""
import os
import subprocess
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]


def _ejecutar(script: str, datos: Path) -> subprocess.CompletedProcess:
    """Corre un guion Python contra una instalación aislada en ``datos``."""
    datos.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["COTIZAT_DATA_DIR"] = str(datos)
    env["COTIZAT_DB"] = str(datos / "presupuestos.db")
    env["PYTHONPATH"] = str(_RAIZ)
    env.pop("DATABASE_URL", None)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=_RAIZ,
        env=env,
        text=True,
        capture_output=True,
    )


def test_recorrido_critico_de_instalacion_limpia_a_restauracion(tmp_path):
    """Instalación limpia → primer PDF real → backup → pérdida → restauración."""
    script = """
import json
import io
import zipfile
from datetime import date

from fastapi.testclient import TestClient

from app.database import BACKUPS_DIR, DATA_DIR, PRIVATE_STORAGE_DIR, UPLOADS_DIR, SessionLocal
from app.main import app
from app.models import Cliente, Partida, Presupuesto, Producto
from app.services.onboarding import estado_recorrido_inicial

# --- 1 y 2. Instalación limpia y primer inicio -----------------------------
with TestClient(app) as client:
    inicio = client.get('/inicio', follow_redirects=False)
    assert inicio.status_code == 303, inicio.status_code
    assert inicio.headers['location'] == '/bienvenida'

    fin = client.post('/bienvenida', data={
        'empresa_nombre': 'Empresa Recorrido',
        'empresa_pais': 'Venezuela',
        'empresa_ciudad': 'Valencia',
        'moneda_default': 'USD',
        'iva_default': '16',
        'modo_inicio': 'limpio',
    }, follow_redirects=False)
    assert fin.status_code == 303, fin.text

    # La instalación limpia no precarga catálogo, clientes ni documentos.
    with SessionLocal() as db:
        assert db.query(Cliente).count() == 0
        assert db.query(Partida).count() == 0
        assert db.query(Producto).count() == 0
        assert db.query(Presupuesto).count() == 0

    # --- 3. Catálogo, cliente real y primer presupuesto real ---------------
    r = client.post('/partidas/nueva', data={
        'nombre': 'Tabique de yeso laminado',
        'descripcion': 'Tabique sencillo 15+70+15',
        'unidad': 'm2',
        'categoria': 'Albañilería',
        'precio_unitario': '25',
        'coste_materiales': '10',
        'coste_mano_obra': '8',
    }, follow_redirects=False)
    assert r.status_code == 303 and 'error=' not in r.headers['location'], r.headers.get('location')

    r = client.post('/recorrido/catalogo-revisado', follow_redirects=False)
    assert r.status_code == 303

    r = client.post('/clientes/nuevo', data={'nombre': 'Cliente Real C.A.'}, follow_redirects=False)
    assert r.status_code == 303 and 'error=' not in r.headers['location'], r.headers.get('location')

    with SessionLocal() as db:
        cliente = db.query(Cliente).one()
        partida = db.query(Partida).one()
        assert cliente.es_demo is False
        cliente_id, partida_id = cliente.id, partida.id

    estructura = [{
        'nombre': 'CAPÍTULO ÚNICO',
        'partidas': [{
            'partida_id': str(partida_id),
            'nombre': 'Tabique de yeso laminado',
            'descripcion': 'Tabique sencillo 15+70+15',
            'unidad': 'm2',
            'cantidad': 12,
            'precio': 25.0,
            'tipo_partida': 'included',
            'seleccionada': True,
            'coste_materiales': 10.0,
            'coste_mano_obra': 8.0,
            'coste_complementarios': 0.0,
            'coste_otros': 0.0,
            'mediciones': [],
        }],
    }]
    r = client.post('/presupuestos/nuevo', data={
        'client_id': str(cliente_id),
        'titulo': 'Primer presupuesto real',
        'fecha': date.today().isoformat(),
        'validez_dias': '30',
        'moneda': 'USD',
        'impuesto_pct': '16',
        'descuento_pct': '0',
        'estado': 'borrador',
        'estructura_json': json.dumps(estructura),
    }, follow_redirects=False)
    assert r.status_code == 303, r.text
    pid = r.headers['location'].split('?')[0].rstrip('/').split('/')[-1]
    assert pid.isdigit(), r.headers['location']

    # --- 4. PDF real y cierre del recorrido de primer uso ------------------
    r = client.get(f'/presupuestos/{pid}/pdf')
    assert r.status_code == 200
    assert r.headers['content-type'] == 'application/pdf'
    assert r.content.startswith(b'%PDF'), r.content[:16]

    r = client.post(f'/presupuestos/{pid}/pdf-descargado')
    assert r.status_code == 200 and r.json() == {'ok': True, 'registrado': True}

    with SessionLocal() as db:
        estado = estado_recorrido_inicial(db)
        assert estado['completo'], estado

    # --- 5. Backup completo desde Configuración ----------------------------
    # Un archivo en cada almacén local debe viajar dentro del backup.
    (UPLOADS_DIR / 'products').mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / 'products' / 'recuerdo.txt').write_text('subida histórica', encoding='utf-8')
    PRIVATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    (PRIVATE_STORAGE_DIR / 'privado.txt').write_text('objeto privado', encoding='utf-8')

    r = client.get('/configuracion/backup')
    assert r.status_code == 200
    assert r.headers['content-type'] == 'application/zip'
    backup_bytes = r.content
    with zipfile.ZipFile(io.BytesIO(backup_bytes)) as z:
        nombres = set(z.namelist())
    assert 'presupuestos.db' in nombres, nombres
    assert 'LEEME_BACKUP.txt' in nombres, nombres
    assert 'uploads/products/recuerdo.txt' in nombres, nombres
    assert 'private_storage/privado.txt' in nombres, nombres

    # --- 6. Pérdida de datos y restauración ---------------------------------
    r = client.post(f'/presupuestos/{pid}/eliminar', follow_redirects=False)
    assert r.status_code in (302, 303)
    (PRIVATE_STORAGE_DIR / 'privado.txt').unlink()
    with SessionLocal() as db:
        assert db.query(Presupuesto).count() == 0

    r = client.post(
        '/configuracion/restaurar',
        files={'archivo': ('backup.zip', backup_bytes, 'application/zip')},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    assert 'error=' not in r.headers['location'], r.headers['location']

    with SessionLocal() as db:
        restaurado = db.query(Presupuesto).one()
        assert restaurado.titulo == 'Primer presupuesto real'
        assert db.query(Cliente).one().nombre == 'Cliente Real C.A.'
    assert (PRIVATE_STORAGE_DIR / 'privado.txt').read_text(encoding='utf-8') == 'objeto privado'
    assert (UPLOADS_DIR / 'products' / 'recuerdo.txt').is_file()

    # Antes de restaurar se guardó una copia de seguridad de lo anterior.
    previas = list(BACKUPS_DIR.glob('antes_de_restaurar_*'))
    assert previas, list(BACKUPS_DIR.iterdir())

    # El PDF vuelve a generarse desde la base restaurada.
    r = client.get(f'/presupuestos/{restaurado.id}/pdf')
    assert r.status_code == 200 and r.content.startswith(b'%PDF')

# --- Reinicio: la instalación limpia no reinyecta datos ni repite el asistente
with TestClient(app) as client:
    r = client.get('/inicio', follow_redirects=False)
    assert r.status_code == 200, r.status_code
    with SessionLocal() as db:
        assert db.query(Presupuesto).count() == 1
        assert db.query(Partida).count() == 1
"""
    resultado = _ejecutar(script, tmp_path / "datos")
    assert resultado.returncode == 0, resultado.stderr


def test_restaurar_backup_de_version_anterior_actualiza_el_esquema(tmp_path):
    """Actualización: una copia de una versión vieja queda al día al restaurarla."""
    script = """
import io
import shutil
import sqlite3
import zipfile

from fastapi.testclient import TestClient

from app.database import DB_PATH, DATA_DIR, SessionLocal
from app.main import app
from app.models import Configuracion

with TestClient(app) as client:
    client.post('/bienvenida', data={
        'empresa_nombre': 'Empresa Anterior',
        'empresa_pais': 'Venezuela',
        'empresa_ciudad': 'Valencia',
        'moneda_default': 'USD',
        'iva_default': '16',
        'modo_inicio': 'limpio',
    }, follow_redirects=False)

    # Se fabrica la base de una «versión anterior»: la actual sin columnas
    # añadidas después (el caso real de mostrar_garantias_default).
    vieja = DATA_DIR / 'version_anterior.db'
    shutil.copy2(DB_PATH, vieja)
    con = sqlite3.connect(str(vieja))
    try:
        con.execute('ALTER TABLE configuracion DROP COLUMN mostrar_garantias_default')
        con.execute('ALTER TABLE presupuestos DROP COLUMN mostrar_garantias')
        con.commit()
    finally:
        con.close()
    columnas = {
        fila[1]
        for fila in sqlite3.connect(str(vieja)).execute('PRAGMA table_info(configuracion)')
    }
    assert 'mostrar_garantias_default' not in columnas

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(vieja, 'presupuestos.db')
    buf.seek(0)

    r = client.post(
        '/configuracion/restaurar',
        files={'archivo': ('backup_viejo.zip', buf.getvalue(), 'application/zip')},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    assert 'error=' not in r.headers['location'], r.headers['location']

    # La restauración reaplicó las migraciones: columnas nuevas presentes y
    # la aplicación sigue funcionando sin reinstalar nada.
    columnas = {
        fila[1]
        for fila in sqlite3.connect(str(DB_PATH)).execute('PRAGMA table_info(configuracion)')
    }
    assert 'mostrar_garantias_default' in columnas, columnas
    with SessionLocal() as db:
        cfg = db.query(Configuracion).one()
        assert cfg.empresa_nombre == 'Empresa Anterior'
        assert cfg.onboarding_completado is True
    r = client.get('/inicio', follow_redirects=False)
    assert r.status_code == 200, r.status_code
"""
    resultado = _ejecutar(script, tmp_path / "datos")
    assert resultado.returncode == 0, resultado.stderr


def test_backup_automatico_semanal_se_crea_una_sola_vez(tmp_path):
    """El arranque local crea la copia automática y no la duplica en la semana."""
    script = """
from fastapi.testclient import TestClient

from app.database import BACKUPS_DIR
from app.main import app

with TestClient(app) as client:
    client.get('/healthz')
autos = list(BACKUPS_DIR.glob('auto_*.zip'))
assert len(autos) == 1, autos

# Un segundo arranque dentro de la misma semana no genera otra copia.
with TestClient(app) as client:
    client.get('/healthz')
autos = list(BACKUPS_DIR.glob('auto_*.zip'))
assert len(autos) == 1, autos
"""
    resultado = _ejecutar(script, tmp_path / "datos")
    assert resultado.returncode == 0, resultado.stderr


def test_restaurar_zip_malicioso_es_rechazado(tmp_path):
    """Un zip con rutas fuera del directorio (zip slip) no debe restaurarse."""
    script = """
import io
import zipfile

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Configuracion

with TestClient(app) as client:
    client.post('/bienvenida', data={
        'empresa_nombre': 'Empresa Segura',
        'empresa_pais': 'Venezuela',
        'empresa_ciudad': 'Valencia',
        'moneda_default': 'USD',
        'iva_default': '16',
        'modo_inicio': 'limpio',
    }, follow_redirects=False)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('../fuera.txt', 'no debería escribirse')
        z.writestr('presupuestos.db', 'no es una base real')
    buf.seek(0)

    r = client.post(
        '/configuracion/restaurar',
        files={'archivo': ('malo.zip', buf.getvalue(), 'application/zip')},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert 'error=' in r.headers['location'], r.headers['location']

    # La base actual quedó intacta.
    with SessionLocal() as db:
        assert db.query(Configuracion).one().empresa_nombre == 'Empresa Segura'
"""
    resultado = _ejecutar(script, tmp_path / "datos")
    assert resultado.returncode == 0, resultado.stderr
