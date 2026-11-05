"""«Revisa tus precios antes de cotizar»: el dato del que sale el importe.

El generador no inventa precios: compone el importe con las tarifas de
recursos de la empresa. Una empresa que paga 15 US$/h por un oficial y otra
que paga 25 US$/h **deben** cotizar distinto con las mismas mediciones. Lo que
no puede pasar es que una cuenta recién creada cotice con referencias de
fábrica y nadie se lo diga: el presupuesto sale, parece correcto y el margen
se lo come el cliente.

Se fija aquí el contrato, sobre todo lo que puede romperse en silencio:

1. el paso aparece **antes** del presupuesto en la guía de inicio;
2. confirmar en bloque cierra el paso y deja fecha por tarifa;
3. escribir el precio propio cuenta como revisión (no se pide dos veces);
4. el aviso del presupuesto habla de las tarifas **de ese documento**, no de
   las 300 del catálogo;
5. pasados los días de vigencia, se vuelve a pedir: una tarifa de hace un año
   no es un dato;
6. sin migración aplicada, todo se degrada en vez de romper la pantalla.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import (
    Capitulo,
    Cliente,
    DescomposicionFila,
    DescomposicionPartida,
    Configuracion,
    Organizacion,
    Partida,
    PrecioRecursoMercado,
    Presupuesto,
    PresupuestoItem,
    Recurso,
)
from app.services.revision_precios import (
    DIAS_VIGENCIA_REVISION,
    aviso_presupuesto,
    resumen_revision,
)

HOY = date.today()


def _descomposicion(codigo: str, descripcion: str, unidad: str = "h") -> str:
    return json.dumps({"filas": [{
        "tipo": "recurso",
        "codigo": codigo,
        "descripcion": descripcion,
        "unidad": unidad,
        "categoria": "mano_obra",
        "precio": 10,
    }]})


@pytest.fixture()
def entorno():
    """Dos oficiales con precios muy distintos y un presupuesto que los usa."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine)
    db = Sesion()
    org = Organizacion(nombre="Obras Norte", slug="obras-norte")
    db.add(org)
    db.flush()
    db.add(Configuracion(
        empresa_nombre="Obras Norte",
        empresa_pais="España",
        moneda_default="EUR",
        iva_default=21.0,
        # Sin onboarding completo la app redirige todo a /bienvenida y estas
        # pruebas no llegarían a las pantallas que hay que comprobar.
        onboarding_completado=True,
        onboarding_modo="demo",
    ))
    db.info["organizacion_id"] = org.id
    db.info["auth_email"] = "jefe@example.com"
    db.info["rol_membresia"] = "propietario"
    oficial = Recurso(
        codigo="MO-OF1", descripcion="Oficial de primera", unidad="h",
        categoria="mano_obra", precio=15.0, usos=12,
    )
    peon = Recurso(
        codigo="MO-PE1", descripcion="Peón ordinario", unidad="h",
        categoria="mano_obra", precio=11.0, usos=3,
    )
    arena = Recurso(
        codigo="MT-AR1", descripcion="Arena de río", unidad="m3",
        categoria="materiales", precio=18.0, usos=40,
    )
    db.add_all([oficial, peon, arena])
    db.flush()
    partida = Partida(
        organizacion_id=org.id,
        nombre="Solado de porcelanato",
        unidad="m2",
        precio_unitario=45.0,
        categoria="Albañilería",
        descomposicion_json=_descomposicion("MO-OF1", "Oficial de primera"),
    )
    db.add(partida)
    db.flush()
    cliente = Cliente(nombre="Comunidad de vecinos", es_demo=False)
    db.add(cliente)
    db.flush()
    presupuesto = Presupuesto(
        numero="P-001", year=HOY.year, es_demo=False, client_id=cliente.id
    )
    db.add(presupuesto)
    db.flush()
    capitulo = Capitulo(presupuesto_id=presupuesto.id, nombre="Albañilería")
    db.add(capitulo)
    db.flush()
    item = PresupuestoItem(
        capitulo_id=capitulo.id,
        nombre="Solado de porcelanato",
        unidad="m2",
        cantidad=10,
        precio_unitario=45.0,
    )
    db.add(item)
    db.flush()
    # El descompuesto importado de CYPE vive en su propia tabla: el aviso tiene
    # que verlo igual que el JSON del editor.
    descompuesto = DescomposicionPartida(
        partida_id=item.id,
        unidad="m2",
        filas_originales_json="[]",
    )
    db.add(descompuesto)
    db.flush()
    db.add(DescomposicionFila(
        descomposicion_id=descompuesto.id,
        tipo="recurso",
        codigo="MO-OF1",
        descripcion="Oficial de primera",
        unidad="h",
        categoria="mano_obra",
        precio_unitario=15.0,
    ))
    db.commit()
    ids = {
        "org": org.id,
        "oficial": oficial.id,
        "peon": peon.id,
        "arena": arena.id,
        "presupuesto": presupuesto.id,
    }

    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    try:
        yield TestClient(app, base_url="http://testserver"), db, ids
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# 1. Qué cuenta como «revisada»
# ---------------------------------------------------------------------------


def test_sin_revision_todas_las_tarifas_estan_por_confirmar(entorno):
    _web, db, ids = entorno
    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")

    assert resumen["total"] == 3
    assert resumen["pendientes"] == 3
    assert resumen["confirmadas"] == 0
    assert resumen["requiere_atencion"] is True
    # La mano de obra va primero: es la que cambia de empresa a empresa.
    assert [fila["descripcion"] for fila in resumen["filas"]][0] == "Oficial de primera"
    assert resumen["mano_obra_pendientes"] == 2


def test_el_precio_propio_de_la_empresa_cuenta_como_revision(entorno):
    """Quien escribe su precio ya dijo cuánto le cuesta: no se le pregunta otra vez."""
    _web, db, ids = entorno
    db.add(PrecioRecursoMercado(
        recurso_id=ids["oficial"], codigo_recurso="MO-OF1", pais_codigo="ES",
        organizacion_id=ids["org"], precio=25.0, moneda="EUR",
    ))
    db.commit()

    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert resumen["confirmadas"] == 1
    assert resumen["pendientes"] == 2
    assert "Oficial de primera" not in [f["descripcion"] for f in resumen["filas"]]


def test_una_tarifa_confirmada_caduca_y_se_vuelve_a_pedir(entorno):
    _web, db, ids = entorno
    oficial = db.get(Recurso, ids["oficial"])
    oficial.precio_revisado_at = datetime.utcnow() - timedelta(
        days=DIAS_VIGENCIA_REVISION + 1
    )
    db.commit()

    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert "Oficial de primera" in [fila["descripcion"] for fila in resumen["filas"]]

    oficial.precio_revisado_at = datetime.utcnow() - timedelta(days=10)
    db.commit()
    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert "Oficial de primera" not in [fila["descripcion"] for fila in resumen["filas"]]


# ---------------------------------------------------------------------------
# 2. El aviso dentro del presupuesto
# ---------------------------------------------------------------------------


def test_el_aviso_del_presupuesto_habla_solo_de_sus_tarifas(entorno):
    _web, db, ids = entorno
    presupuesto = db.get(Presupuesto, ids["presupuesto"])

    aviso = aviso_presupuesto(
        db, presupuesto, organizacion_id=ids["org"], pais="ES"
    )

    assert aviso is not None
    # El documento usa el oficial; el peón y la arena no aparecen en su APU.
    assert aviso["total"] == 1
    assert aviso["mano_obra"] == 1
    assert aviso["filas"][0]["descripcion"] == "Oficial de primera"


def test_el_aviso_desaparece_cuando_la_tarifa_esta_confirmada(entorno):
    _web, db, ids = entorno
    oficial = db.get(Recurso, ids["oficial"])
    oficial.precio_revisado_at = datetime.utcnow()
    db.commit()

    presupuesto = db.get(Presupuesto, ids["presupuesto"])
    assert aviso_presupuesto(
        db, presupuesto, organizacion_id=ids["org"], pais="ES"
    ) is None


def test_el_aviso_sale_en_la_ficha_del_presupuesto(entorno):
    web, _db, ids = entorno
    pagina = web.get(f"/presupuestos/{ids['presupuesto']}")

    assert pagina.status_code == 200
    assert "Este presupuesto usa precios que no has confirmado" in pagina.text
    assert "Oficial de primera" in pagina.text
    assert "/recursos/revisar" in pagina.text


# ---------------------------------------------------------------------------
# 3. La página de revisión y la confirmación en bloque
# ---------------------------------------------------------------------------


def test_la_pagina_de_revision_ensena_las_tarifas_por_confirmar(entorno):
    web, _db, _ids = entorno
    pagina = web.get("/recursos/revisar")

    assert pagina.status_code == 200
    assert "Revisa tus tarifas antes de cotizar" in pagina.text
    assert "Oficial de primera" in pagina.text
    assert "3 de 3" in pagina.text
    # Y explica el porqué con el ejemplo de los dos precios por hora.
    assert "15" in pagina.text and "25" in pagina.text


def test_confirmar_en_bloque_cierra_el_paso_y_deja_fecha(entorno):
    web, db, ids = entorno
    respuesta = web.post("/recursos/revisar/confirmar-todas", follow_redirects=False)

    assert respuesta.status_code in (303, 307)
    db.expire_all()
    for recurso_id in (ids["oficial"], ids["peon"], ids["arena"]):
        assert db.get(Recurso, recurso_id).precio_revisado_at is not None
    assert db.query(Configuracion).one().onboarding_precios_revisados is True

    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert resumen["pendientes"] == 0
    assert resumen["requiere_atencion"] is False


def test_escribir_el_precio_en_la_revision_lo_guarda_como_propio(entorno):
    """El gesto real: mirar la lista, corregir dos precios y confirmar el resto."""
    web, db, ids = entorno
    respuesta = web.post(
        "/recursos/revisar",
        data={
            "revisar": [str(ids["oficial"]), str(ids["peon"])],
            f"precio_{ids['oficial']}": "25",
        },
        follow_redirects=False,
    )

    assert respuesta.status_code in (303, 307)
    db.expire_all()
    propio = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.organizacion_id == ids["org"],
        PrecioRecursoMercado.recurso_id == ids["oficial"],
    ).one()
    assert propio.precio == 25.0
    # El que se confirmó sin escribir precio no genera override: se da por bueno.
    assert db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.organizacion_id == ids["org"],
        PrecioRecursoMercado.recurso_id == ids["peon"],
    ).first() is None
    assert db.get(Recurso, ids["peon"]).precio_revisado_at is not None


def test_confirmar_sin_marcar_nada_no_rompe_y_lo_dice(entorno):
    web, _db, _ids = entorno
    respuesta = web.post("/recursos/revisar", data={}, follow_redirects=False)

    assert respuesta.status_code in (303, 307)
    assert "error=" in respuesta.headers["location"]


# ---------------------------------------------------------------------------
# 4. La guía de inicio y el panel
# ---------------------------------------------------------------------------


def test_la_guia_pone_las_tarifas_antes_del_presupuesto(entorno):
    _web, db, _ids = entorno
    from app.services.onboarding import estado_recorrido_inicial

    estado = estado_recorrido_inicial(db)
    claves = [paso["clave"] for paso in estado["pasos"]]

    assert claves[0] == "tarifas"
    assert claves.index("tarifas") < claves.index("presupuesto")
    paso = next(p for p in estado["pasos"] if p["clave"] == "tarifas")
    assert paso["completo"] is False
    assert paso["url"] == "/recursos/revisar"
    # Y el detalle dice cuántas son de mano de obra, que es la pregunta real.
    assert "mano de obra" in paso["detalle"]
    assert estado["tarifas"]["pendientes"] == 3


def test_el_panel_avisa_de_las_tarifas_sin_confirmar(entorno):
    web, _db, _ids = entorno
    pagina = web.get("/inicio")

    assert pagina.status_code == 200
    assert "Tu catálogo aún cotiza con precios de referencia" in pagina.text
    assert "/recursos/revisar" in pagina.text


def test_el_panel_deja_de_avisar_cuando_estan_confirmadas(entorno):
    web, db, ids = entorno
    oficial = db.get(Recurso, ids["oficial"])
    peon = db.get(Recurso, ids["peon"])
    arena = db.get(Recurso, ids["arena"])
    for recurso in (oficial, peon, arena):
        recurso.precio_revisado_at = datetime.utcnow()
    db.commit()

    pagina = web.get("/inicio").text
    assert "Tu catálogo aún cotiza con precios de referencia" not in pagina


def test_la_lista_de_recursos_ensena_el_contador_y_el_acceso(entorno):
    web, _db, _ids = entorno
    pagina = web.get("/recursos")

    assert pagina.status_code == 200
    assert "/recursos/revisar" in pagina.text
    assert "siguen siendo referencia de" in pagina.text


# ---------------------------------------------------------------------------
# 5. Lo que no puede romperse
# ---------------------------------------------------------------------------


def test_sin_la_columna_de_revision_no_se_rompe_la_pantalla(entorno, monkeypatch):
    """Despliegue sin migración: se degrada a «sin revisión», no a un 500."""
    web, db, ids = entorno
    import app.services.revision_precios as servicio

    original = servicio.resumen_revision

    def _sin_columna(db_, **kwargs):
        try:
            raise RuntimeError('no such column: recursos.precio_revisado_at')
        finally:
            pass

    monkeypatch.setattr(servicio, "resumen_revision", _sin_columna)
    monkeypatch.setattr(
        "app.services.onboarding._estado_tarifas",
        lambda _db, _cfg: {"completo": False, "pendientes": 0, "mano_obra": 0,
                           "total": 0, "detalle": ""},
    )
    pagina = web.get("/inicio")
    assert pagina.status_code == 200
    monkeypatch.setattr(servicio, "resumen_revision", original)
    assert ids["org"]


# ---------------------------------------------------------------------------
# Despliegue sin migración: el 500 real del 04/11/2026
# ---------------------------------------------------------------------------


def _sin_migrar(db):
    """Deja la base como estaba producción: en s8a3c6d1f7b9.

    Es el estado del 04/11/2026: el código ya leía ``Configuracion`` entera y
    la base no tenía ``onboarding_precios_revisados``, así que cualquier
    pantalla respondía 500 con ``UndefinedColumn``.
    """
    from sqlalchemy import text

    from app.services.configuracion_tolerante import olvidar_columnas

    db.execute(text("ALTER TABLE recursos DROP COLUMN precio_revisado_at"))
    db.execute(text("ALTER TABLE configuracion DROP COLUMN onboarding_precios_revisados"))
    db.commit()
    olvidar_columnas("configuracion")


def _migrar(db):
    from sqlalchemy import text

    from app.services.configuracion_tolerante import olvidar_columnas

    db.execute(text(
        "ALTER TABLE configuracion ADD COLUMN onboarding_precios_revisados BOOLEAN DEFAULT false"
    ))
    db.execute(text("ALTER TABLE recursos ADD COLUMN precio_revisado_at DATETIME"))
    db.commit()
    olvidar_columnas("configuracion")


def test_sin_la_columna_nueva_el_panel_no_devuelve_500(entorno):
    """El error reportado: «column configuracion.onboarding_precios_revisados
    does not exist» en ``GET /inicio``.

    El código se publicó antes de pegar el SQL de la migración, así que el
    ``SELECT`` con todas las columnas del modelo fallaba. La lectura tolerante
    pide solo las columnas que existen: el panel se pinta con los datos reales.
    """
    web, db, _ids = entorno
    _sin_migrar(db)
    try:
        respuesta = web.get("/inicio", follow_redirects=False)
        assert respuesta.status_code == 200, respuesta.text[:400]
        # El panel se pinta entero: si la lectura de configuración hubiera
        # seguido pidiendo la columna ausente, esta respuesta sería un 500.
        assert "text/html" in respuesta.headers.get("content-type", "")
    finally:
        _migrar(db)


def test_sin_la_columna_nueva_las_pantallas_de_tarifas_siguen_abriendo(entorno):
    """Sin migración, ni /recursos ni /recursos/revisar pueden reventar."""
    web, db, _ids = entorno
    _sin_migrar(db)
    try:
        for ruta in ("/recursos", "/recursos/revisar"):
            respuesta = web.get(ruta, follow_redirects=False)
            assert respuesta.status_code == 200, (ruta, respuesta.text[:400])
    finally:
        _migrar(db)


def test_sin_la_columna_no_se_confirma_nada_por_accidente(entorno):
    """La lectura tolerante no puede inventar «revisado».

    La columna ausente se completa con su valor por defecto (False). Si eso se
    interpretara como «esta empresa ya revisó», el consejo de revisar precios
    desaparecería justo cuando la base ni siquiera puede guardar la fecha.
    """
    from app.services.configuracion_tolerante import leer_configuracion

    _web, db, _ids = entorno
    _sin_migrar(db)
    try:
        cfg = leer_configuracion(db)
        assert cfg is not None
        assert cfg.empresa_nombre == "Obras Norte"
        assert cfg.onboarding_precios_revisados is False
    finally:
        _migrar(db)


# ---------------------------------------------------------------------------
# 6. El recordatorio se puede posponer y silenciar (u1c5e8b3d7a9)
# ---------------------------------------------------------------------------
#
# La revisión de tarifas decide el importe entero, así que tiene que poder
# pedirse; pero un aviso que no se puede quitar deja de ser un consejo. Estas
# pruebas fijan el contrato de las dos salidas: no confirman precios, solo
# deciden cuándo se enseña el aviso — y se pueden deshacer.


def _cfg(db):
    db.expire_all()
    return db.query(Configuracion).one()


def test_posponer_silencia_el_aviso_hasta_la_fecha_elegida(entorno):
    web, db, ids = entorno
    respuesta = web.post(
        "/recursos/revisar/posponer", data={"plazo": "semana"}, follow_redirects=False
    )

    assert respuesta.status_code in (303, 307)
    cfg = _cfg(db)
    assert cfg.tarifas_recordatorio_pospuesto_hasta == date.today() + timedelta(days=7)
    assert not cfg.tarifas_recordatorio_silenciado

    # No confirma nada: las tres tarifas siguen pendientes.
    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert resumen["pendientes"] == 3
    assert db.get(Recurso, ids["oficial"]).precio_revisado_at is None

    # Y el aviso deja de interrumpir en el panel, en el catálogo y en la ficha.
    inicio = web.get("/inicio").text
    assert "Tu catálogo aún cotiza con precios de referencia" not in inicio
    assert "siguen siendo referencia de" not in web.get("/recursos").text
    ficha = web.get(f"/presupuestos/{ids['presupuesto']}").text
    assert "Este presupuesto usa precios que no has confirmado" not in ficha


def test_el_aviso_vuelve_solo_cuando_pasa_la_fecha(entorno):
    """Se guarda una fecha, no un contador: sin volver a entrar, el aviso vuelve."""
    web, db, _ids = entorno
    web.post("/recursos/revisar/posponer", data={"plazo": "semana"}, follow_redirects=False)

    cfg = _cfg(db)
    # Se simula el paso del tiempo dejando la fecha en el pasado.
    cfg.tarifas_recordatorio_pospuesto_hasta = date.today() - timedelta(days=1)
    db.commit()

    assert "Tu catálogo aún cotiza con precios de referencia" in web.get("/inicio").text


def test_silenciar_no_confirma_tarifas_y_se_puede_deshacer(entorno):
    web, db, ids = entorno
    respuesta = web.post("/recursos/revisar/silenciar", follow_redirects=False)

    assert respuesta.status_code in (303, 307)
    cfg = _cfg(db)
    assert cfg.tarifas_recordatorio_silenciado is True
    assert cfg.onboarding_precios_revisados in (False, None)

    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert resumen["pendientes"] == 3
    assert db.get(Recurso, ids["oficial"]).precio_revisado_at is None
    assert "Tu catálogo aún cotiza con precios de referencia" not in web.get("/inicio").text

    # La pantalla de revisión sigue disponible y es donde se reactiva.
    revisar = web.get("/recursos/revisar")
    assert revisar.status_code == 200
    assert "Recordatorio desactivado" in revisar.text

    assert web.post("/recursos/revisar/reactivar", follow_redirects=False).status_code in (303, 307)
    assert _cfg(db).tarifas_recordatorio_silenciado is False
    assert "Tu catálogo aún cotiza con precios de referencia" in web.get("/inicio").text


def test_la_pantalla_ofrece_las_tres_salidas_y_ninguna_obliga(entorno):
    """Sin muro: posponer, silenciar y «he revisado todas» conviven.

    Además, la selección arranca vacía: confirmar es una decisión del usuario,
    no el efecto de pulsar «Guardar» sin mirar.
    """
    web, _db, _ids = entorno
    pagina = web.get("/recursos/revisar")

    assert pagina.status_code == 200
    assert 'action="/recursos/revisar/posponer"' in pagina.text
    assert 'action="/recursos/revisar/silenciar"' in pagina.text
    assert 'action="/recursos/revisar/confirmar-todas"' in pagina.text
    assert "Marcar todas" in pagina.text
    assert "Desmarcar todas" in pagina.text
    # Las casillas nacen sin marcar: el único «checked» del HTML es el selector
    # ``:checked`` del contador en JavaScript.
    assert 'type="checkbox" name="revisar"' in pagina.text
    assert 'value="' in pagina.text and 'checked>' not in pagina.text


def test_posponer_con_un_plazo_inventado_no_cambia_nada(entorno):
    web, db, _ids = entorno
    respuesta = web.post(
        "/recursos/revisar/posponer", data={"plazo": "siempre"}, follow_redirects=False
    )

    assert respuesta.status_code in (303, 307)
    assert "error=" in respuesta.headers["location"]
    assert _cfg(db).tarifas_recordatorio_pospuesto_hasta is None


def test_confirmar_una_tarifa_desde_su_ficha(entorno):
    """El gesto mínimo: un botón en la ficha, sin formulario ni pantalla aparte."""
    web, db, ids = entorno

    respuesta = web.post(f"/recursos/{ids['oficial']}/revisado", follow_redirects=False)

    assert respuesta.status_code in (303, 307)
    assert f"/recursos/{ids['oficial']}/editar" in respuesta.headers["location"]
    db.expire_all()
    assert db.get(Recurso, ids["oficial"]).precio_revisado_at is not None
    # Y no se inventó ningún precio propio: solo se dio por buena.
    assert db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.organizacion_id == ids["org"]
    ).first() is None


def test_confirmar_desde_la_lista_devuelve_a_la_lista(entorno):
    web, db, ids = entorno

    respuesta = web.post(
        f"/recursos/{ids['peon']}/revisado", data={"volver": "lista"},
        follow_redirects=False,
    )

    assert respuesta.status_code in (303, 307)
    assert respuesta.headers["location"].startswith("/recursos?")
    db.expire_all()
    assert db.get(Recurso, ids["peon"]).precio_revisado_at is not None


def test_confirmar_una_tarifa_con_tu_precio_guarda_el_override(entorno):
    """Un clic en la ficha: guardar mi precio y darlo por bueno, sin dos pasos."""
    web, db, ids = entorno

    respuesta = web.post(
        f"/recursos/{ids['oficial']}/revisado",
        data={"precio_propio": "25", "volver": "revisar"},
        follow_redirects=False,
    )

    assert respuesta.status_code in (303, 307)
    assert respuesta.headers["location"].startswith("/recursos/revisar?")
    db.expire_all()
    propio = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.organizacion_id == ids["org"],
        PrecioRecursoMercado.recurso_id == ids["oficial"],
    ).one()
    assert propio.precio == 25.0
    assert db.get(Recurso, ids["oficial"]).precio_revisado_at is not None


def test_una_tarifa_confirmada_ya_no_aparece_en_la_pantalla(entorno):
    web, db, ids = entorno
    web.post(f"/recursos/{ids['oficial']}/revisado", follow_redirects=False)
    db.expire_all()

    resumen = resumen_revision(db, organizacion_id=ids["org"], pais="ES")
    assert resumen["pendientes"] == 2
    assert "Oficial de primera" not in [f["descripcion"] for f in resumen["filas"]]
    assert "2 de 3" in web.get("/recursos/revisar").text


def test_la_ficha_del_recurso_ofrece_confirmar_y_dice_si_ya_lo_esta(entorno):
    web, db, ids = entorno

    sin_confirmar = web.get(f"/recursos/{ids['oficial']}/editar").text
    assert "Sin confirmar" in sin_confirmar
    assert f'formaction="/recursos/{ids["oficial"]}/revisado"' in sin_confirmar

    web.post(f"/recursos/{ids['oficial']}/revisado", follow_redirects=False)
    db.expire_all()
    confirmada = web.get(f"/recursos/{ids['oficial']}/editar").text
    assert "Confirmada el" in confirmada
    assert "Sin confirmar" not in confirmada
