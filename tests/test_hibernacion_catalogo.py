"""Pruebas de regresión para la hibernación y siembra bajo demanda del catálogo."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    EventoAuditoria,
    Licencia,
    Organizacion,
    Partida,
    Presupuesto,
    PresupuestoItem,
    Producto,
    RecetaEstancia,
    Recurso,
)
from app.services.catalogo_propio import (
    CATALOGO_HIBERNADO,
    CATALOGO_VERSION,
    asegurar_catalogo_propio,
    reactivar_si_hibernado,
    total_partidas_fuente,
)
from app.services.hibernacion_catalogo import (
    HIBERNAR_CATALOGOS_FUNCTION_SQL,
    PREFIJO_ORIGEN_OFICIAL,
    catalogo_bajo_demanda_activado,
    dias_hibernacion_catalogo,
    hibernar_catalogos_inactivos,
    limite_orgs_hibernacion,
)
from app.services.onboarding import completar_onboarding, estado_recorrido_inicial

HOY = date(2026, 11, 17)
AHORA = datetime(2026, 11, 17, 12, 0, 0)
TS_ANTIGUO = datetime(2026, 10, 1, 10, 0, 0)


def _crear_sesion():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _crear_org(
    db,
    nombre: str,
    *,
    created_at: datetime = TS_ANTIGUO,
    version_catalogo: int = CATALOGO_VERSION,
    modo: str = "demo",
    semilla: bool = True,
) -> tuple[Organizacion, Configuracion]:
    org = Organizacion(
        nombre=nombre,
        slug=nombre.lower().replace(" ", "-"),
        activa=True,
        created_at=created_at,
    )
    db.add(org)
    db.flush()
    cfg = Configuracion(
        organizacion_id=org.id,
        empresa_nombre=nombre,
        onboarding_completado=True,
        onboarding_modo=modo,
        semilla_catalogo_aplicada=semilla,
        version_catalogo=version_catalogo,
    )
    db.add(cfg)
    db.flush()
    return org, cfg


def _partida_oficial_intacta(
    org_id: int,
    codigo: str,
    nombre: str,
    *,
    precio: float = 25.0,
    created_at: datetime = TS_ANTIGUO,
    fap: datetime | None = None,
    uid: str | None = None,
) -> Partida:
    return Partida(
        organizacion_id=org_id,
        nombre=nombre,
        descripcion="Descripción oficial",
        precio_unitario=precio,
        unidad="m2",
        categoria="06 Albañilería",
        subcategoria="06.01 Muros",
        apartado="06.01.01 Bloque",
        codigo_interno=codigo,
        codigo_externo=codigo,
        catalogo_uid=uid or f"cp:{codigo}",
        es_oficial=True,
        oculta=False,
        usos=0,
        ultimo_uso=None,
        imagen="",
        version_catalogo=CATALOGO_VERSION,
        version_alta_catalogo=2,
        descomposicion_json=json.dumps(
            {
                "origen": "catalogo_propio",
                "version_catalogo": CATALOGO_VERSION,
                "codigo": codigo,
                "unidad": "m2",
                "filas": [],
            }
        ),
        created_at=created_at,
        fecha_actualizacion_precio=fap or created_at,
    )


def test_configuracion_por_omision_y_variables(monkeypatch):
    monkeypatch.delenv("COTIZAT_CATALOGO_BAJO_DEMANDA", raising=False)
    monkeypatch.delenv("COTIZAT_CATALOGO_HIBERNAR_DIAS", raising=False)
    monkeypatch.delenv("COTIZAT_CATALOGO_HIBERNAR_LIMITE", raising=False)

    assert catalogo_bajo_demanda_activado(es_sqlite=False) is True
    assert catalogo_bajo_demanda_activado(es_sqlite=True) is False
    assert dias_hibernacion_catalogo() == 7
    assert limite_orgs_hibernacion() == 10

    monkeypatch.setenv("COTIZAT_CATALOGO_BAJO_DEMANDA", "true")
    assert catalogo_bajo_demanda_activado(es_sqlite=True) is True
    monkeypatch.setenv("COTIZAT_CATALOGO_BAJO_DEMANDA", "false")
    assert catalogo_bajo_demanda_activado(es_sqlite=False) is False

    monkeypatch.setenv("COTIZAT_CATALOGO_HIBERNAR_DIAS", "0")
    assert dias_hibernacion_catalogo() == 0
    monkeypatch.setenv("COTIZAT_CATALOGO_HIBERNAR_LIMITE", "999")
    assert limite_orgs_hibernacion() == 100


def test_hibernacion_protege_licencias_vigentes_gracia_y_pago():
    db = _crear_sesion()
    try:
        # 1. Licencia vigente -> intacta
        org_activa, cfg_activa = _crear_org(db, "Org Activa")
        db.add(
            Licencia(
                organizacion_id=org_activa.id,
                estado="activa",
                origen="prueba",
                inicio=HOY - timedelta(days=2),
                vence=HOY + timedelta(days=5),
            )
        )
        db.add(_partida_oficial_intacta(org_activa.id, "01.01", "Partida activa"))

        # 2. Prueba vencida hace 3 días (dentro de gracia de 7) -> intacta
        org_gracia, cfg_gracia = _crear_org(db, "Org Gracia")
        db.add(
            Licencia(
                organizacion_id=org_gracia.id,
                estado="activa",
                origen="prueba",
                inicio=HOY - timedelta(days=10),
                vence=HOY - timedelta(days=3),
            )
        )
        db.add(_partida_oficial_intacta(org_gracia.id, "01.01", "Partida gracia"))

        # 3. Cliente de pago/cortesía/compensación vencido hace 60 días -> intacto
        for origen in ("pago", "cortesia", "compensacion"):
            org_p, _ = _crear_org(db, f"Org {origen}")
            db.add(
                Licencia(
                    organizacion_id=org_p.id,
                    estado="activa",
                    origen=origen,
                    inicio=HOY - timedelta(days=90),
                    vence=HOY - timedelta(days=60),
                )
            )
            db.add(_partida_oficial_intacta(org_p.id, "01.01", f"Partida {origen}"))

        # 4. Organización sin licencia pero recién creada (hace 2 días) -> intacta
        org_nueva, _ = _crear_org(
            db, "Org Nueva", created_at=AHORA - timedelta(days=2)
        )
        db.add(_partida_oficial_intacta(org_nueva.id, "01.01", "Partida nueva"))

        # 5. Organización con ajuste masivo auditado -> intacta
        org_ajuste, _ = _crear_org(db, "Org Ajuste")
        db.add(_partida_oficial_intacta(org_ajuste.id, "01.01", "Partida ajustada"))
        db.add(
            EventoAuditoria(
                organizacion_id=org_ajuste.id,
                accion="catalogo.precios_ajustados",
                entidad="partida",
            )
        )

        # 6. Prueba vencida hace 15 días sin pago -> SÍ se hiberna
        org_vencida, cfg_vencida = _crear_org(db, "Org Vencida")
        db.add(
            Licencia(
                organizacion_id=org_vencida.id,
                estado="activa",
                origen="prueba",
                inicio=HOY - timedelta(days=22),
                vence=HOY - timedelta(days=15),
            )
        )
        db.add(_partida_oficial_intacta(org_vencida.id, "01.01", "Partida 1"))
        db.add(_partida_oficial_intacta(org_vencida.id, "01.02", "Partida 2"))
        db.commit()

        res = hibernar_catalogos_inactivos(db, dias=7, hoy=HOY, ahora=AHORA)
        assert res == {
            "activado": True,
            "organizaciones": 1,
            "partidas": 2,
            "dias": 7,
        }

        db.refresh(cfg_activa)
        db.refresh(cfg_gracia)
        db.refresh(cfg_vencida)
        assert cfg_activa.version_catalogo == CATALOGO_VERSION
        assert cfg_gracia.version_catalogo == CATALOGO_VERSION
        assert cfg_vencida.version_catalogo == CATALOGO_HIBERNADO
        assert (
            db.query(Partida)
            .filter(Partida.organizacion_id == org_vencida.id)
            .count()
            == 0
        )
        # Las 7 organizaciones protegidas conservan su partida oficial.
        assert db.query(Partida).count() == 7

        # Segundo barrido: idempotente, no vuelve a tocar nada.
        res2 = hibernar_catalogos_inactivos(db, dias=7, hoy=HOY, ahora=AHORA)
        assert res2["organizaciones"] == 0
        assert res2["partidas"] == 0
    finally:
        db.close()


def test_hibernacion_conserva_todo_dato_tocado_por_el_usuario():
    db = _crear_sesion()
    try:
        org, cfg = _crear_org(db, "Prueba Con Trabajo")
        db.add(
            Licencia(
                organizacion_id=org.id,
                estado="activa",
                origen="prueba",
                inicio=HOY - timedelta(days=30),
                vence=HOY - timedelta(days=20),
            )
        )

        # Filas que DEBEN conservarse intactas:
        p_propia = Partida(
            organizacion_id=org.id,
            nombre="Partida propia del cliente",
            precio_unitario=120.0,
            es_oficial=False,
            version_catalogo=0,
            descomposicion_json='{"origen": "manual", "filas": []}',
            created_at=TS_ANTIGUO,
            fecha_actualizacion_precio=TS_ANTIGUO,
        )
        p_usada = _partida_oficial_intacta(org.id, "02.01", "Oficial usada")
        p_usada.usos = 1
        p_usada.ultimo_uso = TS_ANTIGUO + timedelta(days=1)

        p_oculta = _partida_oficial_intacta(org.id, "02.02", "Oficial oculta")
        p_oculta.oculta = True

        p_imagen = _partida_oficial_intacta(org.id, "02.03", "Oficial con foto")
        p_imagen.imagen = "partidas/cat_1.jpg"

        p_editada = _partida_oficial_intacta(org.id, "02.04", "Oficial editada")
        p_editada.precio_unitario = 999.0
        p_editada.descomposicion_json = '{"origen": "manual", "filas": []}'

        p_precio_inline = _partida_oficial_intacta(
            org.id,
            "02.05",
            "Oficial con precio inline",
            created_at=TS_ANTIGUO,
            fap=TS_ANTIGUO + timedelta(minutes=10),
        )
        p_precio_inline.precio_unitario = 88.5

        p_enlazada = _partida_oficial_intacta(
            org.id, "02.06", "Oficial enlazada en presupuesto"
        )
        p_auditada = _partida_oficial_intacta(
            org.id, "02.07", "Oficial con auditoría"
        )

        # Filas 100 % de fábrica que SÍ deben hibernarse:
        p_intacta_1 = _partida_oficial_intacta(org.id, "03.01", "Intacta 1")
        p_intacta_2 = _partida_oficial_intacta(org.id, "03.02", "Intacta 2")
        p_intacta_3 = _partida_oficial_intacta(org.id, "03.03", "Intacta 3")

        db.add_all(
            [
                p_propia,
                p_usada,
                p_oculta,
                p_imagen,
                p_editada,
                p_precio_inline,
                p_enlazada,
                p_auditada,
                p_intacta_1,
                p_intacta_2,
                p_intacta_3,
            ]
        )
        db.flush()

        cli = Cliente(organizacion_id=org.id, nombre="Cliente Real")
        db.add(cli)
        db.flush()
        pres = Presupuesto(
            organizacion_id=org.id,
            numero="P-001",
            year=2026,
            fecha=HOY - timedelta(days=25),
            titulo="Reforma real",
            client_id=cli.id,
        )
        db.add(pres)
        db.flush()
        cap = Capitulo(
            organizacion_id=org.id, presupuesto_id=pres.id, nombre="Cap 1", orden=1
        )
        db.add(cap)
        db.flush()
        item = PresupuestoItem(
            organizacion_id=org.id,
            capitulo_id=cap.id,
            nombre=p_enlazada.nombre,
            cantidad=10,
            precio_unitario=25.0,
            partida_catalogo_id=p_enlazada.id,
        )
        db.add(item)
        db.add(
            EventoAuditoria(
                organizacion_id=org.id,
                accion="catalogo.precio_partida",
                entidad="partida",
                entidad_id=p_auditada.id,
            )
        )
        db.commit()

        res = hibernar_catalogos_inactivos(db, dias=7, hoy=HOY, ahora=AHORA)
        assert res["organizaciones"] == 1
        assert res["partidas"] == 3

        restantes = {
            p.nombre for p in db.query(Partida).filter_by(organizacion_id=org.id).all()
        }
        assert restantes == {
            "Partida propia del cliente",
            "Oficial usada",
            "Oficial oculta",
            "Oficial con foto",
            "Oficial editada",
            "Oficial con precio inline",
            "Oficial enlazada en presupuesto",
            "Oficial con auditoría",
        }
        db.refresh(cfg)
        db.refresh(item)
        assert cfg.version_catalogo == CATALOGO_HIBERNADO
        assert item.partida_catalogo_id == p_enlazada.id
    finally:
        db.close()


def test_reactivacion_transparente_y_siembra_bajo_demanda(monkeypatch):
    monkeypatch.setenv("COTIZAT_CATALOGO_BAJO_DEMANDA", "true")
    db = _crear_sesion()
    try:
        cfg = completar_onboarding(
            db,
            {
                "empresa_nombre": "Reformas Bolívar",
                "empresa_pais": "España",
                "moneda_default": "EUR",
                "iva_default": 21.0,
            },
            "demo",
        )
        # En modo bajo demanda se siembran recursos, productos, recetas y
        # presupuesto de ejemplo, pero 0 partidas hasta abrir el catálogo.
        assert cfg.semilla_catalogo_aplicada is True
        assert cfg.version_catalogo == CATALOGO_HIBERNADO
        assert db.query(Partida).count() == 0
        assert db.query(Recurso).count() > 100
        assert db.query(Producto).count() > 0
        assert db.query(RecetaEstancia).count() > 0
        assert db.query(Presupuesto).count() == 1

        # /inicio (estado_recorrido_inicial) informa del catálogo disponible
        # sin forzar la siembra de las ~3.000 filas.
        recorrido = estado_recorrido_inicial(db, cfg)
        paso_cat = next(p for p in recorrido["pasos"] if p["clave"] == "catalogo")
        assert str(total_partidas_fuente()) in paso_cat["detalle"]
        assert db.query(Partida).count() == 0

        # El usuario personaliza una tarifa antes de abrir /partidas.
        recurso = db.query(Recurso).filter(Recurso.precio > 0).first()
        assert recurso is not None
        recurso.precio = round(float(recurso.precio) * 2.0, 2)
        recurso.precio_revisado_at = AHORA
        db.commit()

        # Al abrir el buscador/editor/catálogo se materializan las partidas.
        res = reactivar_si_hibernado(db)
        assert res is not None and res.get("ok") is True
        total_sembrado = db.query(Partida).count()
        assert total_sembrado >= 500
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_VERSION

        # Personalizamos: 1 propia, 1 oficial editada/renombrada (mismo uid) y
        # 1 oficial oculta. Luego simulamos vencimiento, hibernamos y volvemos
        # a despertar para comprobar pérdida cero y ausencia de colisiones.
        oficiales = (
            db.query(Partida)
            .filter(Partida.es_oficial.is_(True))
            .order_by(Partida.id)
            .limit(2)
            .all()
        )
        p_renombrada, p_oculta = oficiales[0], oficiales[1]
        uid_renombrada = p_renombrada.catalogo_uid
        p_renombrada.nombre = "Título personalizado por el cliente"
        p_renombrada.precio_unitario = 777.77
        p_renombrada.descomposicion_json = '{"origen": "manual", "filas": []}'
        p_oculta.oculta = True
        p_propia = Partida(
            organizacion_id=cfg.organizacion_id,
            nombre="Servicio exclusivo de la empresa",
            precio_unitario=450.0,
            es_oficial=False,
            version_catalogo=0,
            descomposicion_json='{"origen": "manual", "filas": []}',
        )
        db.add(p_propia)
        # Aseguramos que la org de SQLite exista y sea antigua sin licencia.
        org = db.get(Organizacion, cfg.organizacion_id)
        if org is None:
            org = Organizacion(
                id=cfg.organizacion_id,
                nombre="Reformas Bolívar",
                slug="reformas-bolivar",
                activa=True,
                created_at=TS_ANTIGUO,
            )
            db.add(org)
        else:
            org.created_at = TS_ANTIGUO
        for p in db.query(Partida).all():
            p.created_at = TS_ANTIGUO
            p.fecha_actualizacion_precio = TS_ANTIGUO
        db.commit()

        hib = hibernar_catalogos_inactivos(db, dias=7, hoy=HOY, ahora=AHORA)
        assert hib["organizaciones"] == 1
        assert hib["partidas"] == total_sembrado - 2
        # Solo quedan las 3 tocadas (propia + renombrada + oculta).
        assert db.query(Partida).count() == 3
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_HIBERNADO

        # El cliente renueva y abre /partidas -> todo vuelve intacto.
        db.info.pop("_catalogo_no_hibernado", None)
        despertar = asegurar_catalogo_propio(db)
        assert despertar is not None and despertar.get("ok") is True
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_VERSION
        # total_sembrado oficiales (incluida la renombrada por catalogo_uid y
        # la oculta) + 1 propia = total_sembrado + 1, sin duplicados.
        assert db.query(Partida).count() == total_sembrado + 1

        ren = db.query(Partida).filter_by(catalogo_uid=uid_renombrada).one()
        assert ren.nombre == "Título personalizado por el cliente"
        assert ren.precio_unitario == pytest.approx(777.77)
        assert db.get(Partida, p_oculta.id).oculta is True
        assert db.get(Partida, p_propia.id).precio_unitario == pytest.approx(450.0)

        # Una partida borrada después con catálogo activo no reaparece.
        victima = (
            db.query(Partida)
            .filter(Partida.es_oficial.is_(True), Partida.oculta.is_(False))
            .first()
        )
        db.delete(victima)
        db.commit()
        conteo_tras_borrado = db.query(Partida).count()
        assert asegurar_catalogo_propio(db) is None
        assert db.query(Partida).count() == conteo_tras_borrado
    finally:
        db.close()


def test_interruptor_cero_desactiva_hibernacion():
    db = _crear_sesion()
    try:
        org, cfg = _crear_org(db, "Org Vencida")
        db.add(_partida_oficial_intacta(org.id, "01.01", "Partida 1"))
        db.commit()

        res = hibernar_catalogos_inactivos(db, dias=0, hoy=HOY, ahora=AHORA)
        assert res == {
            "activado": False,
            "organizaciones": 0,
            "partidas": 0,
            "dias": 0,
        }
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_VERSION
        assert db.query(Partida).count() == 1
    finally:
        db.close()


def test_contrato_funcion_security_definer_postgres():
    """La función PostgreSQL exige sesión de operador y privilegios mínimos."""
    assert "SECURITY DEFINER" in HIBERNAR_CATALOGOS_FUNCTION_SQL
    assert "SET search_path = pg_catalog, public" in HIBERNAR_CATALOGOS_FUNCTION_SQL
    assert "cotizat.es_operador" in HIBERNAR_CATALOGOS_FUNCTION_SQL
    assert "'pago', 'cortesia', 'compensacion'" in HIBERNAR_CATALOGOS_FUNCTION_SQL
    assert PREFIJO_ORIGEN_OFICIAL in HIBERNAR_CATALOGOS_FUNCTION_SQL
    assert "catalogo.precios_ajustados" in HIBERNAR_CATALOGOS_FUNCTION_SQL

    raiz = Path(__file__).resolve().parents[1]
    helper = (raiz / "app" / "services" / "hibernacion_catalogo.py").read_text(
        encoding="utf-8"
    )
    database_py = (raiz / "app" / "database.py").read_text(encoding="utf-8")
    assert "REVOKE ALL ON FUNCTION" in helper
    assert "GRANT EXECUTE ON FUNCTION" in helper
    assert "_asegurar_funcion_hibernacion_postgres(eng)" in database_py


def test_ayudantes_editor_y_asistente_despiertan_catalogo_hibernado():
    """Abrir el árbol del editor o buscar en el asistente repone el catálogo."""
    from app.routers.common import _arbol_catalogo_editor
    from app.services.asistente_ia import buscar_partidas_catalogo

    db = _crear_sesion()
    try:
        _, cfg = _crear_org(
            db,
            "Org Hibernada Editor",
            version_catalogo=CATALOGO_HIBERNADO,
            modo="demo",
            semilla=True,
        )
        db.commit()
        assert db.query(Partida).count() == 0

        arbol = _arbol_catalogo_editor(db)
        assert arbol["total"] >= 500
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_VERSION

        # Volvemos a hibernar para probar también la ruta del asistente.
        db.query(Partida).delete()
        cfg.version_catalogo = CATALOGO_HIBERNADO
        db.commit()
        db.info.pop("_catalogo_no_hibernado", None)

        busqueda = buscar_partidas_catalogo(db, "pintura", limite=5)
        assert len(busqueda["resultados"]) > 0
        db.refresh(cfg)
        assert cfg.version_catalogo == CATALOGO_VERSION
    finally:
        db.close()
