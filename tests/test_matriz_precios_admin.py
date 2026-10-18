"""Carga de la matriz nacional de precios desde el panel de operador.

Cubre las dos piezas que hacen falta para que la carga viva en el panel y no
en un SQL pegado a mano:

* el importador acepta el fichero tal cual llega (bytes) y resuelve los
  recursos **de todas** las organizaciones, no solo de la que lo sube;
* la vista previa promete exactamente lo que después se escribe, y no escribe
  nada mientras solo se está validando.

Las referencias nacionales son las de ``organizacion_id`` nulo: las que sirven
a todas las empresas de un país. RLS solo deja escribirlas a un operador, así
que el panel es su cauce natural.
"""
import csv
import io

from app.models import Organizacion, PrecioRecursoMercado, Recurso
from app.services.importador_precios_mercado import (
    COLUMNAS_MATRIZ,
    importar_matriz_csv,
    resolver_recursos,
)
from app.services.precios_mercado import resumen_matriz_por_pais

CAMPOS = list(COLUMNAS_MATRIZ)


def _matriz(filas) -> str:
    salida = io.StringIO(newline="")
    writer = csv.DictWriter(salida, fieldnames=CAMPOS, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(filas)
    return salida.getvalue()


def _fila(codigo="MT-GB", precio="24.48", **extra) -> dict:
    fila = {
        "codigo_recurso": codigo,
        "descripcion": "Material de prueba",
        "categoria": "materiales",
        "unidad_fuente": "kg",
        "pais_codigo": "GB",
        "moneda": "GBP",
        "precio_referencia": precio,
        "precio_min": "22.00",
        "precio_max": "29.00",
        "fuente": "docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md",
        "fecha_consulta": "2026-10-18",
        "confianza": "referencia",
        "incluye_iva": "no",
        "incluye_transporte": "no_confirmado",
        "origen": "nacional",
        "observaciones": "Referencia nacional de prueba.",
    }
    fila.update(extra)
    return fila


def _otra_organizacion(db) -> int:
    org = Organizacion(nombre="Otra empresa", slug="otra-empresa")
    db.add(org)
    db.flush()
    return org.id


def _recurso_de_otra_organizacion(db, org_id: int, codigo: str) -> None:
    """Crea un recurso de otra empresa saltando el guardián de tenencia.

    El guardián hace bien su trabajo: con contexto de organización puesto
    prohíbe crear registros ajenos. Para montar el escenario hay que retirar el
    contexto un momento, igual que haría una migración o una prueba unitaria.
    """
    contexto = db.info.pop("organizacion_id", None)
    try:
        db.add(Recurso(
            organizacion_id=org_id, codigo=codigo, descripcion="Solo en la otra",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        ))
        db.flush()
    finally:
        if contexto is not None:
            db.info["organizacion_id"] = contexto


# ---------------------------------------------------------------------------
# Entrada del fichero
# ---------------------------------------------------------------------------


def test_importador_acepta_bytes_igual_que_una_ruta(entorno, tmp_path):
    """El panel recibe bytes y la herramienta una ruta: mismo resultado."""
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.add(Recurso(
            organizacion_id=ids[0], codigo="MT-GB", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        ))
        db.commit()

        csv_texto = _matriz([_fila()])
        ruta = tmp_path / "matriz.csv"
        ruta.write_text(csv_texto, encoding="utf-8")

        por_ruta = importar_matriz_csv(db, ruta, aplicar=True)
        assert por_ruta["errores"] == []
        assert por_ruta["creadas_o_actualizadas"] == 1

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        por_bytes = importar_matriz_csv(db, csv_texto.encode("utf-8"), aplicar=False)
        assert por_bytes["errores"] == []
        # La referencia ya existe: la vista previa lo dice en vez de duplicarla.
        assert por_bytes["creadas"] == 0
        assert por_bytes["sin_cambios"] == 1


def test_importador_acepta_un_fichero_con_bom(entorno):
    """Un CSV guardado desde Excel llega con BOM; no puede romper la cabecera."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.add(Recurso(
            organizacion_id=ids[0], codigo="MT-GB", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        ))
        db.commit()

        contenido = "\ufeff" + _matriz([_fila()])
        resultado = importar_matriz_csv(db, contenido.encode("utf-8"), aplicar=True)
        assert resultado["errores"] == []
        assert resultado["creadas_o_actualizadas"] == 1


# ---------------------------------------------------------------------------
# Resolución de recursos en modo nacional
# ---------------------------------------------------------------------------


def test_modo_nacional_resuelve_recursos_de_otras_organizaciones(entorno):
    """La referencia sirve a todos los inquilinos: se busca por código en todos.

    Sin `nacional`, `db.query(Recurso)` solo ve la organización de la sesión y
    un código que existe en la base se rechaza como «no encontrado».
    """
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        otra = _otra_organizacion(db)
        _recurso_de_otra_organizacion(db, otra, "MT-AJENO")
        db.commit()

        # Modo organización: no lo encuentra, porque no es de esta empresa.
        assert "MT-AJENO" not in resolver_recursos(db, nacional=False)
        # Modo nacional: sí.
        assert "MT-AJENO" in resolver_recursos(db, nacional=True)


def test_modo_nacional_escribe_la_referencia_para_todos(entorno):
    """Cargada desde una organización, la referencia vale para las demás."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        otra = _otra_organizacion(db)
        _recurso_de_otra_organizacion(db, otra, "MT-AJENO")
        db.commit()

        fallido = importar_matriz_csv(
            db, _matriz([_fila("MT-AJENO")]).encode("utf-8"), aplicar=False, nacional=False
        )
        assert fallido["no_encontrados"] == 1

        valido = importar_matriz_csv(
            db, _matriz([_fila("MT-AJENO")]).encode("utf-8"), aplicar=True, nacional=True
        )
        assert valido["errores"] == []
        assert valido["creadas"] == 1

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        fila = db.query(PrecioRecursoMercado).filter_by(
            codigo_recurso="MT-AJENO", pais_codigo="GB", organizacion_id=None
        ).one()
        assert fila.activo is True
        assert fila.precio == 24.48


# ---------------------------------------------------------------------------
# Vista previa
# ---------------------------------------------------------------------------


def test_la_vista_previa_no_escribe_nada(entorno):
    """Validar es lectura: la base queda intacta aunque el fichero sea correcto."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.add(Recurso(
            organizacion_id=ids[0], codigo="MT-GB", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        ))
        db.commit()

        resultado = importar_matriz_csv(
            db, _matriz([_fila()]).encode("utf-8"), aplicar=False, nacional=True
        )
        assert resultado["errores"] == []
        assert resultado["aplicables"] == 1
        assert resultado["creadas"] == 1
        assert db.query(PrecioRecursoMercado).count() == 0


def test_la_vista_previa_clasifica_nuevas_actualizadas_e_iguales(entorno):
    """Tres recursos, tres estados distintos, contados como se van a escribir."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        for codigo in ("MT-NUEVO", "MT-CAMBIA", "MT-IGUAL"):
            db.add(Recurso(
                organizacion_id=ids[0], codigo=codigo, descripcion=codigo,
                unidad="kg", categoria="materiales", precio=1, moneda="USD",
            ))
        db.commit()

        # Carga inicial: «MT-CAMBIA» y «MT-IGUAL» entran a 10.00.
        primera = importar_matriz_csv(db, _matrix_inicial().encode("utf-8"),
                                      aplicar=True, nacional=True)
        assert primera["errores"] == []
        assert primera["creadas"] == 2

        # Segunda vuelta: una nueva, una que sube de precio, una que repite.
        segunda = importar_matriz_csv(db, _matriz([
            _fila("MT-NUEVO", "24.48"),
            _fila("MT-CAMBIA", "18.00", precio_min="16.00", precio_max="20.00"),
            _fila("MT-IGUAL", "10.00", precio_min="9.00", precio_max="11.00"),
        ]).encode("utf-8"), aplicar=False, nacional=True)

        assert segunda["errores"] == []
        assert segunda["creadas"] == 1
        assert segunda["actualizadas"] == 1
        assert segunda["sin_cambios"] == 1

        estados = {f["codigo"]: f["estado"] for f in segunda["muestra"]}
        assert estados["MT-NUEVO"] == "creada"
        assert estados["MT-CAMBIA"] == "actualizada"
        assert estados["MT-IGUAL"] == "sin_cambios"


def _matrix_inicial() -> str:
    return _matriz([
        _fila("MT-CAMBIA", "10.00", precio_min="9.00", precio_max="11.00"),
        _fila("MT-IGUAL", "10.00", precio_min="9.00", precio_max="11.00"),
    ])


def test_un_error_bloquea_toda_la_carga_y_se_ve_en_la_vista_previa(entorno):
    """Un rango corrupto no puede colarse: la carga es todo-o-nada."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        db.add(Recurso(
            organizacion_id=ids[0], codigo="MT-GB", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        ))
        db.commit()

        resultado = importar_matriz_csv(
            db,
            _matriz([_fila("MT-GB", "24.48", precio_min="99.00")]).encode("utf-8"),
            aplicar=True, nacional=True,
        )
        assert resultado["errores"]
        assert resultado["creadas_o_actualizadas"] == 0
        assert db.query(PrecioRecursoMercado).count() == 0


# ---------------------------------------------------------------------------
# Reemplazo de la matriz de un país
# ---------------------------------------------------------------------------


def test_reemplazar_desactiva_las_huerfanas_en_vez_de_borrarlas(entorno):
    """Lo que el fichero no trae se desactiva: el histórico se conserva."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        for codigo in ("MT-UNO", "MT-DOS"):
            db.add(Recurso(
                organizacion_id=ids[0], codigo=codigo, descripcion=codigo,
                unidad="kg", categoria="materiales", precio=1, moneda="USD",
            ))
        db.commit()
        importar_matriz_csv(db, _matriz([
            _fila("MT-UNO", "10.00", precio_min="9.00", precio_max="11.00"),
            _fila("MT-DOS", "10.00", precio_min="9.00", precio_max="11.00"),
        ]).encode("utf-8"), aplicar=True, nacional=True)

        # Matriz nueva que solo trae MT-UNO: MT-DOS queda fuera.
        resultado = importar_matriz_csv(
            db, _matriz([_fila("MT-UNO", "12.00", precio_min="11.00",
                               precio_max="13.00")]).encode("utf-8"),
            aplicar=True, nacional=True, reemplazar=True,
        )
        assert resultado["errores"] == []
        assert resultado["eliminadas"] == 1

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        filas = db.query(PrecioRecursoMercado).filter_by(pais_codigo="GB").all()
        assert len(filas) == 2, "no se borra: se desactiva"
        por_codigo = {f.codigo_recurso: f for f in filas}
        assert por_codigo["MT-UNO"].activo is True
        assert por_codigo["MT-UNO"].precio == 12.00
        assert por_codigo["MT-DOS"].activo is False


def test_sin_reemplazar_lo_que_existe_se_queda(entorno):
    """Cargar un fichero parcial no puede vaciar el resto del país."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        for codigo in ("MT-UNO", "MT-DOS"):
            db.add(Recurso(
                organizacion_id=ids[0], codigo=codigo, descripcion=codigo,
                unidad="kg", categoria="materiales", precio=1, moneda="USD",
            ))
        db.commit()
        importar_matriz_csv(db, _matriz([
            _fila("MT-UNO", "10.00", precio_min="9.00", precio_max="11.00"),
            _fila("MT-DOS", "10.00", precio_min="9.00", precio_max="11.00"),
        ]).encode("utf-8"), aplicar=True, nacional=True)

        resultado = importar_matriz_csv(
            db, _matriz([_fila("MT-UNO", "12.00", precio_min="11.00",
                               precio_max="13.00")]).encode("utf-8"),
            aplicar=True, nacional=True, reemplazar=False,
        )
        assert resultado["eliminadas"] == 0

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        activas = db.query(PrecioRecursoMercado).filter_by(
            pais_codigo="GB", activo=True
        ).count()
        assert activas == 2


# ---------------------------------------------------------------------------
# Resumen por país
# ---------------------------------------------------------------------------


def test_resumen_por_pais_cuenta_monedas_y_vigencia(entorno):
    """La foto de la pantalla: cuántas, de cuándo y cuántas ya caducaron."""
    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        for codigo in ("MT-RECIENTE", "MT-VIEJA"):
            db.add(Recurso(
                organizacion_id=ids[0], codigo=codigo, descripcion=codigo,
                unidad="kg", categoria="materiales", precio=1, moneda="USD",
            ))
        db.commit()
        importar_matriz_csv(db, _matriz([
            _fila("MT-RECIENTE", "10.00", precio_min="9.00", precio_max="11.00",
                  fecha_consulta="2026-10-01"),
            _fila("MT-VIEJA", "10.00", precio_min="9.00", precio_max="11.00",
                  fecha_consulta="2023-01-01"),
        ]).encode("utf-8"), aplicar=True, nacional=True)

        resumen = resumen_matriz_por_pais(db)

    assert "GB" in resumen
    gb = resumen["GB"]
    assert gb["referencias"] == 2
    assert gb["monedas"] == ["GBP"]
    # Consulta de 2023 con confianza «referencia»: pasados 365 días es obsoleta.
    # Caducada sería solo si la propia vigencia declarada ya hubiera vencido.
    assert gb["obsoletas"] == 1
    assert gb["caducadas"] == 0
    assert gb["pendientes_revision"] == 1
    assert gb["ultima_consulta"] is not None


def test_resumen_ignora_los_precios_propios_de_cada_empresa(entorno):
    """El resumen es de la matriz nacional; los overrides no cuentan."""
    from app.services.precios_mercado import guardar_precio

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        recurso = Recurso(
            organizacion_id=ids[0], codigo="MT-PROPIO", descripcion="Material",
            unidad="kg", categoria="materiales", precio=1, moneda="USD",
        )
        db.add(recurso)
        db.commit()
        guardar_precio(db, recurso.id, "GB", 99.0, "GBP", organizacion_id=ids[0])

        resumen = resumen_matriz_por_pais(db)

    assert "GB" not in resumen


# ---------------------------------------------------------------------------
# Helpers de las rutas y montaje de la pestaña
# ---------------------------------------------------------------------------


def test_el_csv_ida_y_vuelta_por_el_formulario_no_se_altera():
    """Entre «validar» y «cargar» el fichero viaja codificado: debe llegar igual."""
    from app.routers.admin import _csv_reenviable, _csv_recuperado

    original = _matriz([_fila()]).encode("utf-8")
    assert _csv_recuperado(_csv_reenviable(original)) == original


def test_un_csv_reenviado_manipulado_se_rechaza():
    """El campo es un formulario: lo que llegue roto no puede pasar por válido."""
    import pytest

    from app.routers.admin import _csv_recuperado

    with pytest.raises(ValueError):
        _csv_recuperado("no-es-base64!!!")
    with pytest.raises(ValueError):
        _csv_recuperado("")
    with pytest.raises(ValueError):
        _csv_recuperado("")


def test_solo_un_superadmin_puede_cargar_una_matriz():
    """Cargar una matriz afecta a todos los clientes del país, no a una empresa."""
    import pytest

    from app.routers.admin import _exigir_superadmin_para
    from app.services.operadores_admin import GestionEquipoError

    class _SesionFalsa:
        def __init__(self, rol):
            self.info = {"operador_rol": rol}

    _exigir_superadmin_para(_SesionFalsa("superadmin"), "cargar una matriz de precios")

    with pytest.raises(GestionEquipoError) as exc:
        _exigir_superadmin_para(_SesionFalsa("admin"), "cargar una matriz de precios")
    assert "superadmin" in str(exc.value)
    assert "cargar una matriz de precios" in str(exc.value)


def test_la_pestana_de_precios_existe_y_tiene_quien_la_rellene():
    """Sin entrada en el registro, la URL caería en otra pestaña en silencio."""
    from app.panel_arquitectura import pestanas_de
    from app.routers import admin_paginas

    ids = [p.id for p in pestanas_de("sistema")]
    assert "precios" in ids
    assert "precios" in admin_paginas._RELLENOS
    assert callable(admin_paginas._RELLENOS["precios"])


def test_las_rutas_de_carga_estan_registradas():
    from app.routers import admin

    rutas = {r.path for r in admin.router.routes if hasattr(r, "path")}
    assert "/admin/matriz-precios/validar" in rutas
    assert "/admin/matriz-precios/cargar" in rutas


def test_la_plantilla_de_precios_no_lleva_estilos_en_linea():
    """CSP del panel: nada de `style=` en el marcado."""
    from pathlib import Path

    plantilla = Path("app/templates/admin/partes/sistema_precios.html").read_text(encoding="utf-8")
    assert "style=" not in plantilla
    assert "/admin/matriz-precios/validar" in plantilla
    assert "/admin/matriz-precios/cargar" in plantilla
