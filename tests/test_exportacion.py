"""E3-022 — exportación de datos abierta y portátil por organización.

El paquete de exportación debe ser legible por cualquier herramienta (CSV con
BOM UTF-8, archivos con nombre original) y conservar dentro la copia
verificable de E3-020 para restaurar en otro CotizaT. Estas pruebas cubren el
contenido, la coherencia con el respaldo, los nombres de archivo, la
honestidad de lo omitido y las rutas HTTP con roles.
"""
import csv
import hashlib
import io
import json
import zipfile

from app.services.exportacion import (
    FORMATO_EXPORTACION,
    NOMBRE_EMBEBIDO,
    VERSION_EXPORTACION,
    generar_exportacion,
)

from tests.conftest import NOMBRE_ORG


def _exportacion(Session, org_id) -> bytes:
    with Session() as db:
        db.info["organizacion_id"] = org_id
        db.info["rol_membresia"] = "propietario"
        return generar_exportacion(db)


def test_paquete_contiene_respaldo_verificable_embebido(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _exportacion(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        nombres = paquete.namelist()
        assert NOMBRE_EMBEBIDO in nombres
        assert "manifest_exportacion.json" in nombres
        assert "LEEME_EXPORTACION.txt" in nombres
        manifest = json.loads(paquete.read("manifest_exportacion.json"))
        assert manifest["formato"] == FORMATO_EXPORTACION
        assert manifest["version"] == VERSION_EXPORTACION
        assert manifest["organizacion"]["nombre"] == NOMBRE_ORG

        # El respaldo embebido es un paquete verificable E3-020 completo
        respaldo_embebido = paquete.read(NOMBRE_EMBEBIDO)
        with zipfile.ZipFile(io.BytesIO(respaldo_embebido)) as respaldo:
            nombres_respaldo = respaldo.namelist()
            assert "manifest.json" in nombres_respaldo
            assert any(n.startswith("archivos/") for n in nombres_respaldo)
            manifest_respaldo = json.loads(respaldo.read("manifest.json"))
            assert manifest_respaldo["formato"] == "cotizat-backup"
            assert manifest_respaldo["conteos"] == manifest["conteos"]


def test_csv_por_tabla_con_bom_encabezados_y_filas_iguales_al_conteo(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _exportacion(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        manifest = json.loads(paquete.read("manifest_exportacion.json"))
        for clave, esperadas in manifest["conteos"].items():
            csv_nombre = f"csv/{clave.replace('.json', '.csv')}"
            assert csv_nombre in paquete.namelist(), csv_nombre
            crudo = paquete.read(csv_nombre)
            assert crudo.startswith(b"\xef\xbb\xbf")  # BOM para Excel/LibreOffice
            filas = list(csv.reader(io.StringIO(crudo.decode("utf-8-sig"))))
            assert filas[0] and "_id" not in filas[0]
            assert len(filas) - 1 == esperadas

        # El CSV de presupuestos es legible y no incluye los de demostración
        presupuestos = list(csv.reader(io.StringIO(
            paquete.read("csv/presupuestos.csv").decode("utf-8-sig")
        )))
        numeros = {fila[presupuestos[0].index("numero")] for fila in presupuestos[1:]}
        assert numeros == {"P-2026-020"}

        # El CSV de configuración tiene una fila sin identidad ni proceso
        configuracion = list(csv.reader(io.StringIO(
            paquete.read("csv/configuracion.csv").decode("utf-8-sig")
        )))
        encabezados = configuracion[0]
        assert "iva_default" in encabezados
        assert "empresa_nombre" not in encabezados


def test_archivos_con_nombre_original_y_prefijo_de_huella(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _exportacion(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        manifest = json.loads(paquete.read("manifest_exportacion.json"))
        assert len(manifest["archivos"]) == 1  # mismo contenido, una sola copia
        entrada = manifest["archivos"][0]
        ruta = (
            f"archivos_con_nombre/{entrada['sha256'][:12]}"
            f"_{entrada['nombre_original']}"
        )
        assert ruta in paquete.namelist()
        crudo = paquete.read(ruta)
        assert hashlib.sha256(crudo).hexdigest() == entrada["sha256"]
        assert crudo == b"PNG-logotipo-empresa"


def test_leeme_explica_como_abrir_y_que_se_omite(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _exportacion(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        leeme = paquete.read("LEEME_EXPORTACION.txt").decode("utf-8")
        assert "Excel" in leeme
        assert "cotizat-respaldo.zip" in leeme
        assert "licencias" in leeme
        assert "SHA-256" in leeme


def test_ruta_descarga_exige_rol_y_devuelve_zip(entorno, cliente_web, tmp_path):
    Session, ids, rol = entorno
    rol["valor"] = "miembro"
    respuesta = cliente_web.get("/configuracion/exportacion/descargar", follow_redirects=False)
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/configuracion")

    rol["valor"] = "propietario"
    descarga = cliente_web.get("/configuracion/exportacion/descargar")
    assert descarga.status_code == 200
    assert descarga.content.startswith(b"PK")
    assert descarga.headers["cache-control"] == "no-store"
    with zipfile.ZipFile(io.BytesIO(descarga.content)) as paquete:
        assert "csv/clientes.csv" in paquete.namelist()


def test_pantalla_respaldo_ofrece_exportacion_y_baja_al_propietario(entorno, cliente_web):
    Session, ids, rol = entorno
    rol["valor"] = "propietario"
    pagina = cliente_web.get("/configuracion/respaldo")
    assert pagina.status_code == 200
    assert "/configuracion/exportacion/descargar" in pagina.text
    assert "/configuracion/baja" in pagina.text

    rol["valor"] = "administrador"
    pagina = cliente_web.get("/configuracion/respaldo")
    assert "/configuracion/exportacion/descargar" in pagina.text
    # La baja es solo del propietario
    assert "/configuracion/baja" not in pagina.text
