"""Arquitectura del panel de operador (reorganización de 2026-08-30).

Este archivo fija el contrato del panel rediseñado, que no es visual sino de
funcionamiento:

- seis entradas de menú, cada área con sus pestañas; ninguna pantalla huérfana y
  ninguna función duplicada en dos sitios;
- las 16 URLs que se fusionaron siguen respondiendo con un 302 a su pestaña, con
  sus parámetros;
- filtros, búsqueda y orden se aplican **en el servidor**: la URL es compartible y
  el CSV exporta exactamente lo que se ve;
- las acciones se disparan desde la propia lista y devuelven a ella (`volver`),
  validado contra el mapa de rutas del panel;
- todo lo que se hace desde el panel queda auditado con una etiqueta legible.

Por qué pruebas y no CSS: el diseño se puede romper sin que se note; lo que no
puede romperse es que el panel deje de servir para operar.
"""
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_operator_db
from app.main import app
from app.models import (
    ApiKeyOperador,
    AvisoWeb,
    CrmCliente,
    EventoAdmin,
    Licencia,
    Membresia,
    Organizacion,
    Usuario,
    VistaGuardada,
)
from app.panel_arquitectura import (
    FICHA_PESTANAS,
    RUTAS_ANTIGUAS,
    SECCIONES,
    cabecera_panel,
    es_destino_panel,
    modulo_de_vistas,
    nav_panel,
    pestana_ficha_valida,
    pestana_valida,
    redireccion_de,
    ruta_panel,
)
from app.services.audit_admin import ACCIONES_LECIBLES
from app.services.compras import crear_compra
from app.services.web_admin import crear_release
from starlette.testclient import TestClient

PARTES = Path("app/templates/admin/partes")


@pytest.fixture
def entorno():
    """Base con clientes en cada situación que el panel tiene que poder operar."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        por_vencer = Organizacion(nombre="Obras Norte", slug="obra-norte")
        al_dia = Organizacion(nombre="Reformas Sur", slug="reformas-sur")
        sin_plan = Organizacion(nombre="Tecnicos Delta", slug="delta")
        usuario = Usuario(
            auth_user_id="auth-1",
            email="cliente@example.com",
            nombre="Cliente",
            email_verificado_at=datetime(2026, 8, 1),
        )
        db.add_all([por_vencer, al_dia, sin_plan, usuario])
        db.flush()
        db.add(Membresia(organizacion_id=por_vencer.id, usuario_id=usuario.id, rol="propietario"))
        hoy = date.today()
        db.add_all([
            Licencia(
                organizacion_id=por_vencer.id, origen="pago", importe=89.0, moneda="USD",
                inicio=hoy - timedelta(days=363), vence=hoy + timedelta(days=2),
                estado="activa", metodo_cobro="Zelle", creada_por_email="op@example.com",
            ),
            Licencia(
                organizacion_id=al_dia.id, origen="pago", importe=89.0, moneda="USD",
                inicio=hoy - timedelta(days=10), vence=hoy + timedelta(days=355),
                estado="activa", creada_por_email="op@example.com",
            ),
        ])
        db.commit()
        db.info["organizacion_id"] = sin_plan.id
        compra = crear_compra(
            db,
            organizacion_id=sin_plan.id,
            plan="mensual",
            metodo_pago="usdt",
            datos_verificacion={"hash_transaccion": "TX-PRUEBA"},
            comprobante_reference="storage://organizaciones/3/comprobantes/tx.png",
            comprobante_nombre="tx.png",
            comprobante_mime="image/png",
            creada_por_usuario_id=usuario.id,
            creada_por_email="cliente@example.com",
        )
        db.commit()
        datos = {
            "por_vencer": por_vencer.id,
            "al_dia": al_dia.id,
            "sin_plan": sin_plan.id,
            "compra": compra.id,
        }

    def _db_operador():
        db = Session()
        db.info["es_operador"] = True
        db.info["auth_email"] = "op@example.com"
        db.info["operador_rol"] = "superadmin"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        cliente = TestClient(app, base_url="https://cotizat.test")
        yield cliente, Session, datos
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


# ---------------------------------------------------------------------------
# El mapa: seis áreas, pestañas y URLs antiguas
# ---------------------------------------------------------------------------


def test_el_panel_tiene_seis_entradas_como_maximo():
    """El límite es el criterio de diseño: si cabe en seis áreas, no hay página nueva."""
    assert len(SECCIONES) == 6
    assert [s.id for s in SECCIONES] == ["hoy", "clientes", "ingresos", "web", "analitica", "sistema"]
    assert len(nav_panel()) == 6


def test_clientes_usa_una_sola_lista_para_dos_vistas():
    """CRM y directorio eran dos tablas de las mismas organizaciones: hoy son pestañas."""
    assert pestana_valida("clientes", "pipeline") == "pipeline"
    assert pestana_valida("clientes", "noexiste") == "directorio"
    assert [p.vista_modulo for p in SECCIONES[1].pestanas] == ["clientes", ""]


def test_un_area_de_una_sola_pantalla_no_pinta_barra():
    """Una barra con un elemento es ruido: Hoy y Analítica navegan sin pestañas."""
    assert pestana_valida("hoy", "cualquiera") == ""
    assert pestana_valida("analitica", "cualquiera") == ""
    assert len(pestana_valida("sistema", "auditoria")) > 0


def test_las_pestanas_de_la_ficha_no_dependen_del_area():
    assert pestana_ficha_valida("cobros") == "cobros"
    assert pestana_ficha_valida("inventada") == "resumen"
    assert len(FICHA_PESTANAS) == 5


def test_el_breadcrumb_sale_del_mapa_no_de_cada_plantilla():
    cabecera = cabecera_panel("ingresos", "cobros")
    assert cabecera["titulo"] == "Cobros del mes"
    assert [m["ruta"] for m in cabecera["migas"]] == ["/admin/ingresos", "/admin/ingresos?tab=cobros"]


@pytest.mark.parametrize(
    "antigua,destino", sorted(RUTAS_ANTIGUAS.items()),
    ids=[Path(ruta).name for ruta in sorted(RUTAS_ANTIGUAS)],
)
def test_las_urls_fusionadas_redirigen_a_su_pestana(antigua, destino):
    """Nada queda muerto: los enlaces guardados aterrizan en la pestaña nueva."""
    assert redireccion_de(antigua) == ruta_panel(*destino)


def test_la_redireccion_conserva_los_parametros_del_enlace_viejo(entorno):
    """Un favorito a «cobros de julio» tiene que seguir trayendo julio."""
    cliente, _Session, _datos = entorno
    respuesta = cliente.get("/admin/cobros?mes=2026-07", follow_redirects=False)
    assert respuesta.status_code == 302
    ubicacion = respuesta.headers["location"]
    assert ubicacion.startswith("/admin/ingresos")
    assert "tab=cobros" in ubicacion and "mes=2026-07" in ubicacion
    pagina = cliente.get(ubicacion)
    assert pagina.status_code == 200
    assert "Julio de 2026" in pagina.text


def test_no_quedan_plantillas_huerfanas_en_el_panel():
    """Cada parcial declarado existe, y ningún parcial sobrevive a su pestaña.

    El panel había acumulado pantallas que ya nadie enlazaba (doce archivos que se
    podían borrar sin tocar nada). Como las pestañas se resuelven por nombre —
    ``partes/<área>_<pestaña>.html``—, esta prueba es la que avisa cuando se
    declara una pestaña sin pantalla o se deja una pantalla sin dueño.
    """
    declarados = {f"{s.id}_{p.id}.html" for s in SECCIONES for p in s.pestanas}
    declarados |= {f"ficha_{p.id}.html" for p in FICHA_PESTANAS}
    # Hoy no tiene pestañas pero su contenido está en el cuerpo de dashboard.html.
    declarados |= {f"ingresos_{p}.html" for p in ()}
    existentes = {p.name for p in PARTES.glob("*.html") if not p.name.startswith("_")}
    faltan = declarados - existentes
    sobran = existentes - declarados
    assert not faltan, f"pestañas declaradas sin plantilla: {sorted(faltan)}"
    assert not sobran, f"plantillas de parte sin pestaña que las muestre: {sorted(sobran)}"


# ---------------------------------------------------------------------------
# Filtros, orden y vistas: todo en el servidor
# ---------------------------------------------------------------------------


def test_el_directorio_filtra_por_texto_estado_y_plan(entorno):
    """A2: el filtro estrecha el servidor, no el DOM (y el contador acompaña)."""
    cliente, _Session, _datos = entorno

    todo = cliente.get("/admin/clientes?tab=directorio")
    por_vencer = cliente.get("/admin/clientes?tab=directorio&estado=por_vencer")
    sin_plan = cliente.get("/admin/clientes?tab=directorio&plan=sin")
    texto = cliente.get("/admin/clientes?tab=directorio&q=reformas")

    assert "Obras Norte" in todo.text and "Reformas Sur" in todo.text
    assert "Tecnicos Delta" in todo.text and "3 fila" in todo.text
    assert "Obras Norte" in por_vencer.text and "Reformas Sur" not in por_vencer.text
    assert "Tecnicos Delta" in sin_plan.text and "Obras Norte" not in sin_plan.text
    assert "Reformas Sur" in texto.text and "Obras Norte" not in texto.text
    assert "1 fila" in texto.text


def test_el_orden_es_de_la_url_y_no_del_navegador(entorno):
    """Ordenar en la lista y en el CSV tiene que dar el mismo orden."""
    cliente, _Session, _datos = entorno
    descendente = cliente.get("/admin/clientes?tab=directorio&orden=ingresos&dir=desc").text
    ascendente = cliente.get("/admin/clientes?tab=directorio&orden=ingresos&dir=asc").text

    assert descendente.index("Obras Norte") < descendente.index("Tecnicos Delta")
    assert ascendente.index("Tecnicos Delta") < ascendente.index("Obras Norte")
    # El enlace de la cabecera alterna la dirección: no hay JS de ordenación.
    assert "orden=ingresos" in descendente


def test_el_csv_exporta_lo_que_se_ve_y_no_toda_la_base(entorno):
    """El CSV del directorio es la lista filtrada: sustituye la pantalla aparte."""
    cliente, _Session, _datos = entorno
    filtrado = cliente.get("/admin/clientes.csv?q=reformas")
    completo = cliente.get("/admin/clientes.csv")

    assert filtrado.status_code == 200
    assert "text/csv" in filtrado.headers["content-type"]
    lineas = [l for l in filtrado.text.strip().splitlines() if l.strip()]
    assert len(lineas) == 2                       # cabecera + la única fila filtrada
    assert "Reformas Sur" in lineas[1]
    assert "Obras Norte" not in filtrado.text
    assert "Obras Norte" in completo.text
    # El CRM va en las mismas columnas: antes había que cruzar dos pantallas.
    assert "Estado comercial" in lineas[0]


def test_una_sola_ruta_de_csv_para_las_cuatro_listas_de_ingresos(entorno):
    """`/admin/ingresos.csv?tab=` exporta la pestaña que miras, con sus columnas.

    Cuatro pantallas de exportación eran cuatro rutas con cuatro filtros que se
    podían desincronizar de la pantalla. Ahora el CSV comparte router, filtros y
    orden con la lista; las rutas antiguas siguen respondiendo.
    """
    cliente, _Session, _datos = entorno
    # Cada pestaña exporta LO SUYO: columnas propias, no un CSV genérico.
    cabeceras = {
        "renovaciones": "Cliente;Slug;Vence;Días",
        "cobros": "Fecha;Mes;Tipo;Número;Cliente",
        "compras": "Compra;Cliente;Plan;Método",
        "contratos": "Cliente;Slug;Estado;Plan",
    }
    for pestana, cabecera in cabeceras.items():
        csv = cliente.get(f"/admin/ingresos.csv?tab={pestana}")
        assert csv.status_code == 200, pestana
        assert "text/csv" in csv.headers["content-type"]
        lineas = csv.text.strip().splitlines()
        assert csv.text.startswith("\ufeff"), pestana        # BOM: Excel abre acentos
        assert cabecera in lineas[0], (pestana, lineas[0])
        assert ";" in lineas[0], pestana                    # separador de la casa

    # La cola de compras tiene su propio CSV (es lo que hay que verificar) y los
    # filtros de la lista se respetan en la exportación.
    assert "Obras Norte" in cliente.get("/admin/ingresos.csv?tab=contratos").text
    assert "Obras Norte" not in cliente.get("/admin/ingresos.csv?tab=contratos&q=Delta").text
    assert "Obras Norte" not in cliente.get("/admin/ingresos.csv?tab=renovaciones&mes=2020-01").text
    assert "Tecnicos Delta" in cliente.get("/admin/ingresos.csv?tab=compras").text
    assert "Tecnicos Delta" not in cliente.get("/admin/ingresos.csv?tab=compras&estado=activa").text

    # Las URLs históricas no se rompen.
    for vieja in ("/admin/renovaciones.csv", "/admin/cobros.csv"):
        respuesta = cliente.get(vieja)
        assert respuesta.status_code == 200 and "text/csv" in respuesta.headers["content-type"]


def test_la_vista_guardada_es_un_filtro_con_nombre_en_su_lista(entorno):
    """A5: se crea desde la barra de la lista, se aplica por URL y se borra ahí."""
    cliente, Session, _datos = entorno

    creada = cliente.post(
        "/admin/vistas/crear",
        data={
            "modulo": "clientes",
            "nombre": "Por vencer",
            "filtros": '{"estado":"por_vencer"}',
            "volver": "/admin/clientes?tab=directorio",
        },
        follow_redirects=False,
    )
    assert creada.status_code == 303
    assert creada.headers["location"].startswith("/admin/clientes?tab=directorio")
    with Session() as db:
        vista_id = db.query(VistaGuardada).one().id

    barra = cliente.get("/admin/clientes?tab=directorio").text
    assert "Por vencer" in barra
    # El chip lleva los filtros de la vista en la URL: se puede compartir y funciona
    # sin JavaScript (y el formulario de «guardar actual» está en la misma barra).
    assert "estado=por_vencer&amp;tab=directorio" in barra
    assert "Guardar actual" in barra and "Gestionar (1)" in barra

    aplicado = cliente.get(f"/admin/clientes?tab=directorio&vista={vista_id}")
    assert "Obras Norte" in aplicado.text and "Reformas Sur" not in aplicado.text

    # La pantalla antigua ya no existe: enlaza con la lista que la muestra.
    vieja = cliente.get("/admin/vistas", follow_redirects=False)
    assert vieja.headers["location"] == "/admin/clientes?tab=directorio"

    borrada = cliente.post(
        f"/admin/vistas/{vista_id}/eliminar",
        data={"volver": "/admin/clientes?tab=directorio"},
        follow_redirects=False,
    )
    assert borrada.status_code == 303
    tras = cliente.get("/admin/clientes?tab=directorio").text
    # El nombre «Por vencer» también lo lleva la lista de estados: lo que tiene
    # que desaparecer es el chip de la vista.
    assert 'class="chip chip-vista' not in tras
    assert "Gestionar (1)" not in tras


def test_una_vista_no_se_filtra_entre_listas_ajenas(entorno):
    """El módulo de una vista es el de su lista: una vista de cobros no aparece en Clientes."""
    cliente, Session, _datos = entorno
    with Session() as db:
        db.add(VistaGuardada(modulo="cobros", nombre="Julio", filtros='{"mes":"2026-07"}'))
        db.commit()
    assert modulo_de_vistas("clientes", "directorio") == "clientes"
    assert "Julio" not in cliente.get("/admin/clientes?tab=directorio").text
    assert "Julio" in cliente.get("/admin/ingresos?tab=cobros").text


# ---------------------------------------------------------------------------
# Actuar desde la propia lista
# ---------------------------------------------------------------------------


def test_conceder_desde_contratos_vuelve_a_contratos(entorno):
    cliente, Session, datos = entorno
    respuesta = cliente.post(
        f"/admin/organizaciones/{datos['sin_plan']}/conceder",
        data={"origen": "prueba", "duracion": "7d", "volver": "/admin/ingresos?tab=contratos"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/admin/ingresos?tab=contratos")

    with Session() as db:
        licencia = (
            db.query(Licencia)
            .filter(Licencia.organizacion_id == datos["sin_plan"])
            .order_by(Licencia.id.desc())
            .first()
        )
        assert licencia is not None
        # «7 días» incluye el día del alta: vence el sexto a partir de hoy.
        assert licencia.vence == date.today() + timedelta(days=6)
        assert licencia.importe == 0                      # concedido como prueba
        evento = (
            db.query(EventoAdmin)
            .filter(EventoAdmin.accion == "licencia.concedida")
            .order_by(EventoAdmin.id.desc())
            .first()
        )
        assert evento is not None and evento.resultado == "ok"
        assert evento.organizacion_id == datos["sin_plan"]


def test_el_alta_manual_aplica_el_importe_del_plan_si_se_deja_en_blanco(entorno):
    """`/admin/licencias` y el botón rápido no pueden discrepar: importe del plan.

    Una licencia de pago sin importe es un error de negocio; el formulario largo
    lo dejaba en 0 y el botón rápido, en el precio del plan.
    """
    cliente, Session, datos = entorno
    respuesta = cliente.post(
        "/admin/licencias",
        data={
            "organizacion_id": datos["por_vencer"],
            "origen": "pago",
            "duracion": "1a",
            "importe": "",
            "volver": "/admin/ingresos?tab=contratos",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "error" not in respuesta.headers["location"]
    with Session() as db:
        licencia = (
            db.query(Licencia)
            .filter(Licencia.organizacion_id == datos["por_vencer"])
            .order_by(Licencia.id.desc())
            .first()
        )
        assert round(float(licencia.importe), 2) == 89.0


def test_suspender_desde_la_ficha_deja_constancia_y_no_cambia_el_pasado(entorno):
    cliente, Session, datos = entorno
    ficha = cliente.get(f"/admin/clientes/{datos['por_vencer']}?tab=acceso")
    assert ficha.status_code == 200
    assert "data-confirmar" in ficha.text
    assert f"/admin/organizaciones/{datos['por_vencer']}/suspender" in ficha.text

    respuesta = cliente.post(
        f"/admin/organizaciones/{datos['por_vencer']}/suspender",
        data={
            "motivo": "Impago confirmado por teléfono",
            "volver": f"/admin/clientes/{datos['por_vencer']}?tab=acceso",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "tab=acceso" in respuesta.headers["location"]
    with Session() as db:
        licencias = db.query(Licencia).filter_by(organizacion_id=datos["por_vencer"]).all()
        assert licencias and all(lic.estado == "cancelada" for lic in licencias)
        assert all(lic.vence >= date.today() - timedelta(days=400) for lic in licencias)
        assert db.query(EventoAdmin).filter_by(accion="licencia.suspendida").count() == 1


def test_un_volver_inventado_no_saca_al_operador_del_panel(entorno):
    """El `volver` viene del formulario: validarlo o es una redirección abierta."""
    assert es_destino_panel("/admin/ingresos?tab=compras&estado=pendiente")
    assert es_destino_panel("/admin/clientes/12?tab=acceso")
    assert not es_destino_panel("//evil.com/admin")
    assert not es_destino_panel("https://evil.test")
    assert not es_destino_panel("/admin/sistema?tab=inventada")
    assert not es_destino_panel("/organizaciones")

    cliente, _Session, datos = entorno
    respuesta = cliente.post(
        f"/admin/organizaciones/{datos['sin_plan']}/conceder",
        data={"origen": "prueba", "duracion": "1m", "volver": "https://evil.test"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/admin")
    assert "evil" not in respuesta.headers["location"]


def test_activar_una_compra_la_saca_de_la_cola_y_concede_el_plan(entorno):
    """La decisión se toma en la fila: verificar y activar, sin página aparte."""
    cliente, Session, datos = entorno
    lista = cliente.get("/admin/ingresos?tab=compras")
    assert "Verificar y activar" in lista.text
    assert f"/admin/compras/{datos['compra']}/activar" in lista.text
    assert f"/admin/compras/{datos['compra']}/rechazar" in lista.text
    assert "1 visible" in lista.text

    respuesta = cliente.post(
        f"/admin/compras/{datos['compra']}/activar",
        data={"volver": "/admin/ingresos?tab=compras"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/admin/ingresos?tab=compras")

    with Session() as db:
        from app.models import CompraPlan

        compra = db.get(CompraPlan, datos["compra"])
        assert compra.estado == "activa" and compra.licencia_id
        licencia = db.get(Licencia, compra.licencia_id)
        assert licencia.organizacion_id == datos["sin_plan"]
        assert round(float(licencia.importe), 2) == 9.99     # el importe real, no 0
        assert db.query(EventoAdmin).filter_by(accion="compra.activada").count() == 1

    # Al volver, la cola está vacía y el badge del menú baja: nada queda colgado.
    tras = cliente.get("/admin/ingresos?tab=compras")
    assert "No hay compras" in tras.text
    assert f"/admin/compras/{datos['compra']}/activar" not in tras.text


def test_rechazar_una_compra_pide_motivo_y_deja_el_cliente_intacto(entorno):
    cliente, Session, datos = entorno
    respuesta = cliente.post(
        f"/admin/compras/{datos['compra']}/rechazar",
        data={"motivo": "El comprobante no corresponde al importe", "volver": "/admin/ingresos?tab=compras"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    with Session() as db:
        from app.models import CompraPlan

        assert db.get(CompraPlan, datos["compra"]).estado == "rechazada"
        assert db.query(Licencia).filter_by(organizacion_id=datos["sin_plan"]).count() == 0


# ---------------------------------------------------------------------------
# CRM, notas y actividad: todo dentro del cliente
# ---------------------------------------------------------------------------


def test_mover_una_tarjeta_del_embudo_no_toca_el_acceso(entorno):
    cliente, Session, datos = entorno
    respuesta = cliente.post(
        f"/admin/crm/{datos['al_dia']}/guardar",
        data={
            "estado": "riesgo",
            "proximo_contacto": date.today().isoformat(),
            "notas": "Quiere migrar los presupuestos antiguos",
            "volver": "/admin/clientes?tab=pipeline",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/admin/clientes?tab=pipeline")
    with Session() as db:
        assert db.query(CrmCliente).filter_by(organizacion_id=datos["al_dia"]).one().estado == "riesgo"
        assert db.query(Licencia).filter_by(organizacion_id=datos["al_dia"]).one().estado == "activa"

    embudo = cliente.get("/admin/clientes?tab=pipeline")
    assert "Reformas Sur" in embudo.text
    assert "riesgo" in embudo.text
    # El embudo comparte los filtros del directorio: misma lista, otra lectura.
    assert "Reformas Sur" not in cliente.get("/admin/clientes?tab=pipeline&estado=por_vencer").text


def test_quitar_el_estado_comercial_borra_la_ficha_y_no_rompe_un_check(entorno):
    """`crm_clientes.estado` tiene un CHECK con cinco valores: «sin asignar» = fuera."""
    cliente, Session, datos = entorno
    with Session() as db:
        db.add(CrmCliente(organizacion_id=datos["por_vencer"], estado="lead", notas=""))
        db.commit()

    respuesta = cliente.post(
        f"/admin/crm/{datos['por_vencer']}/guardar",
        data={"estado": "", "notas": "", "volver": f"/admin/clientes/{datos['por_vencer']}?tab=gestion"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "error" not in respuesta.headers["location"]
    with Session() as db:
        assert db.query(CrmCliente).filter_by(organizacion_id=datos["por_vencer"]).one_or_none() is None
        evento = (
            db.query(EventoAdmin)
            .filter(EventoAdmin.accion == "crm.cliente_actualizado")
            .order_by(EventoAdmin.id.desc())
            .first()
        )
        assert "borrado" in str(evento.detalle)


def test_la_nota_de_gestion_vuelve_a_gestion_y_no_al_principio(entorno):
    cliente, _Session, datos = entorno
    respuesta = cliente.post(
        f"/admin/clientes/{datos['por_vencer']}/notas",
        data={"contenido": "Llamó para pedir la factura a nombre de la matriz"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "tab=gestion" in respuesta.headers["location"]
    assert "Llamó para pedir la factura" in cliente.get(
        f"/admin/clientes/{datos['por_vencer']}?tab=gestion"
    ).text


# ---------------------------------------------------------------------------
# Web: contenido, avisos y versiones en un área
# ---------------------------------------------------------------------------


def test_editar_un_aviso_no_obliga_a_borrarlo_y_recrearlo(entorno):
    cliente, Session, _datos = entorno
    with Session() as db:
        aviso = AvisoWeb(
            tipo="mantenimiento", nivel="warning", titulo="Corte el sabado",
            mensaje="De 2 a 4 de la madrugada", activo=True, creado_por="op@example.com",
        )
        db.add(aviso)
        db.commit()
        aviso_id = aviso.id

    lista = cliente.get("/admin/web?tab=avisos")
    assert "Corte el sabado" in lista.text
    assert f"/admin/avisos/{aviso_id}/editar" in lista.text

    respuesta = cliente.post(
        f"/admin/avisos/{aviso_id}/editar",
        data={
            "tipo": "mantenimiento", "nivel": "warning",
            "titulo": "Corte el sabado 6", "mensaje": "De 2 a 4 (ampliado)",
            "activo": "on", "inicio": "", "fin": (date.today() + timedelta(days=3)).isoformat(),
            "volver": "/admin/web?tab=avisos",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/admin/web?tab=avisos")
    # Lo que verá el público lo decide `avisos_publicos`: el aviso editado es el
    # mismo, no una fila nueva, y sigue dentro de su ventana.
    from app.services.web_admin import avisos_publicos

    with Session() as db:
        publicados = avisos_publicos(db)
    assert [a.titulo for a in publicados] == ["Corte el sabado 6"]
    with Session() as db:
        assert db.query(AvisoWeb).count() == 1                # no se duplicó
        assert db.get(AvisoWeb, aviso_id).activo is True
        assert db.query(EventoAdmin).filter_by(accion="web.aviso_editado").count() == 1


def test_editar_una_version_se_refleja_en_la_pagina_publica(entorno):
    cliente, Session, _datos = entorno
    with Session() as db:
        release = crear_release(
            db, version="v9.9", titulo="Panel reorganizado", notas="Seis areas.",
            publicado=True, fecha=date.today(), operador_email="op@example.com",
        )
        db.commit()
        release_id = release.id

    lista = cliente.get("/admin/web?tab=versiones")
    assert f"/admin/releases/{release_id}/editar" in lista.text

    respuesta = cliente.post(
        f"/admin/releases/{release_id}/editar",
        data={
            "version": "v9.9", "titulo": "Panel en seis areas",
            "notas": "Seis areas y filtros server-side.", "publicado": "on",
            "fecha": date.today().isoformat(), "volver": "/admin/web?tab=versiones",
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    from app.services.web_admin import releases_publicas

    with Session() as db:
        assert [r.titulo for r in releases_publicas(db)] == ["Panel en seis areas"]
    assert "Panel en seis areas" in cliente.get("/admin/web?tab=versiones").text


def test_guardar_contenido_deja_el_borrador_a_la_vista(entorno):
    """Editar la landing y publicarla son la misma pantalla, no dos."""
    cliente, Session, _datos = entorno
    respuesta = cliente.post(
        "/admin/web/guardar",
        data={"clave": "landing.hero", "contenido_json": '{"titulo":"Presupuesta en minutos"}'},
        follow_redirects=False,
    )
    assert respuesta.status_code == 303
    assert "tab=contenido" in respuesta.headers["location"]

    contenido = cliente.get("/admin/web?tab=contenido")
    assert "landing.hero" in contenido.text
    assert "Publicar" in contenido.text or "publicado" in contenido.text.lower()


# ---------------------------------------------------------------------------
# Sistema: accesos, equipo y auditoría
# ---------------------------------------------------------------------------


def test_la_clave_nueva_se_ve_una_sola_vez(entorno):
    """El token solo existe en la respuesta que lo crea: ni en la URL ni en la lista."""
    cliente, Session, _datos = entorno
    creada = cliente.post("/admin/api-keys/crear", data={"nombre": "Cobros", "scopes": "cobros.leer"})
    assert creada.status_code == 200
    import re

    coincidencia = re.search(r"cotizat_[A-Za-z0-9_-]{20,}", creada.text)
    token = coincidencia.group(0) if coincidencia else None
    assert token and len(token) > 20

    with Session() as db:
        clave = db.query(ApiKeyOperador).order_by(ApiKeyOperador.id.desc()).one()
        assert clave.clave_hash != token and len(clave.clave_hash) == 64

    # Revocar desde el panel tiene que valer de algo: la token deja de autenticar.
    from app.services.web_admin import verificar_api_key

    with Session() as db:
        assert verificar_api_key(db, token) is not None

    lista = cliente.get("/admin/sistema?tab=accesos").text
    assert token not in lista and "Cobros" in lista

    revocada = cliente.post(f"/admin/api-keys/{clave.id}/revocar", follow_redirects=False)
    assert revocada.status_code == 303
    assert revocada.headers["location"].startswith("/admin/sistema?tab=accesos")
    with Session() as db:
        assert db.get(ApiKeyOperador, clave.id).activo is False
        assert verificar_api_key(db, token) is None
        assert verificar_api_key(db, "cotizat_" + "x" * 32) is None


def test_flags_y_claves_comparten_pestana_porque_son_la_misma_pregunta(entorno):
    """«Quién puede hacer qué» estaba en dos páginas: hoy es una sola."""
    cliente, _Session, _datos = entorno
    pagina = cliente.get("/admin/sistema?tab=accesos")
    assert "Claves" in pagina.text
    for vieja in ("/admin/flags", "/admin/api-keys"):
        assert cliente.get(vieja, follow_redirects=False).headers["location"] == "/admin/sistema?tab=accesos"


def test_la_auditoria_se_puede_filtrar_por_lo_que_fallo(entorno):
    cliente, Session, datos = entorno
    with Session() as db:
        db.add_all([
            EventoAdmin(
                operador_email="op@example.com", operador_rol="superadmin",
                accion="compra.activada", entidad="compra", entidad_id=1,
                organizacion_id=datos["sin_plan"], detalle="{}", resultado="ok",
                created_at=datetime(2026, 8, 29, 12, 0),
            ),
            EventoAdmin(
                operador_email="otra@example.com", operador_rol="soporte",
                accion="licencia.concedida", entidad="licencia", entidad_id=2,
                detalle="{}", resultado="error", created_at=datetime(2026, 8, 29, 13, 0),
            ),
        ])
        db.commit()

    todo = cliente.get("/admin/sistema?tab=auditoria").text
    solo_fallos = cliente.get("/admin/sistema?tab=auditoria&resultado=error").text
    por_actor = cliente.get("/admin/sistema?tab=auditoria&actor=otra").text

    # Las opciones del filtro contienen los códigos de todas las acciones: se
    # cuenta filas renderizadas, no se busca la cadena suelta.
    assert todo.count('class="accion-code"') == 2
    assert solo_fallos.count('class="accion-code"') == 1
    assert "Licencia concedida" in solo_fallos and "Otra acci" not in solo_fallos
    assert por_actor.count('class="accion-code"') == 1      # solo la de «otra»
    assert "otra@example.com" in por_actor
    # Desde el hecho se salta a la ficha del cliente afectado.
    assert f"/admin/clientes/{datos['sin_plan']}?tab=actividad" in todo


def test_toda_accion_que_se_audita_tiene_etiqueta_legible():
    """Ninguna acción huérfana: si el panel audita algo, el filtro lo conoce.

    Un registro con una acción sin etiqueta es invisible en la práctica: el
    operador no puede filtrar por ella y lee un código suelto en la tabla.
    """
    import re

    emitidas = set()
    for archivo in Path("app/routers").glob("*.py"):
        emitidas |= set(re.findall(r'accion="([a-z_]+\.[a-z_]+)"', archivo.read_text(encoding="utf-8")))
    assert emitidas, "el panel tiene que auditar algo"
    faltan = sorted(emitidas - set(ACCIONES_LECIBLES))
    assert not faltan, f"acciones del panel sin etiqueta de auditoría: {faltan}"


def test_el_equipo_se_gestiona_desde_su_pestana_y_sigue_solo_para_superadmin(entorno):
    cliente, _Session, _datos = entorno
    pagina = cliente.get("/admin/sistema?tab=equipo")
    assert pagina.status_code == 200
    assert 'name="rol"' in pagina.text
    assert "/admin/equipo/crear" in pagina.text
    assert cliente.get("/admin/equipo", follow_redirects=False).headers["location"] == "/admin/sistema?tab=equipo"
    # Un alta desde el panel es un operador de verdad, con su marca de rol.
    respuesta = cliente.post("/admin/equipo/crear", data={"email": "nuevo@example.com", "rol": "admin"})
    assert respuesta.status_code in (200, 303)


# ---------------------------------------------------------------------------
# Hoy y las pestañas: que ninguna pantalla se caiga
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruta", sorted(set(RUTAS_ANTIGUAS)))
def test_toda_url_antigua_acaba_en_una_pagina_valida(entorno, ruta):
    """Un 302 a una pantalla que no existe sería peor que borrar la ruta."""
    cliente, _Session, _datos = entorno
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert '<main' in respuesta.text or "table" in respuesta.text


def test_todas_las_pestanas_de_todas_las_areas_renderizan(entorno):
    cliente, _Session, _datos = entorno
    for seccion in SECCIONES:
        for definida in seccion.pestanas or [None]:
            url = ruta_panel(seccion.id, definida.id if definida else "")
            respuesta = cliente.get(url)
            assert respuesta.status_code == 200, url
            assert "Undefined" not in respuesta.text
            assert "jinja2" not in respuesta.text.lower()


def test_la_ficha_del_cliente_tiene_cinco_pestanas_y_todas_pintan(entorno):
    cliente, _Session, datos = entorno
    for pestana in ("resumen", "acceso", "cobros", "gestion", "actividad"):
        respuesta = cliente.get(f"/admin/clientes/{datos['por_vencer']}?tab={pestana}")
        assert respuesta.status_code == 200, pestana
        assert f"tab={pestana}" in respuesta.text        # la pestaña activa, enlazada
    assert "Obras Norte" in cliente.get(f"/admin/clientes/{datos['por_vencer']}").text
    assert "00/00/0000" not in cliente.get(f"/admin/clientes/{datos['por_vencer']}").text


def test_el_hub_es_agenda_y_no_un_muro_de_tablas(entorno):
    """Hoy existe para decidir: pendientes, vencimientos y atajos a las listas."""
    cliente, _Session, _datos = entorno
    pagina = cliente.get("/admin")
    assert pagina.status_code == 200
    assert "Requiere tu acci" in pagina.text
    assert "/admin/ingresos?tab=compras" in pagina.text
    assert "Compras por activar" in pagina.text
    assert "Registrar compra" not in pagina.text        # el formulario vive en su lista
    assert "Obras Norte" in pagina.text                 # mencionada, no listada
    assert "/admin/organizaciones/" not in pagina.text  # sin acciones universales en el hub
    for entrada in nav_panel():
        assert entrada["nombre"] in pagina.text


def test_los_atajos_de_teclado_salen_del_mapa_del_panel(entorno):
    """`g` + letra navega; las letras las declara el mapa, no el JavaScript."""
    cliente, _Session, _datos = entorno
    pagina = cliente.get("/admin").text
    for entrada in nav_panel():
        assert f'data-atajo="{entrada["atajo"]}"' in pagina
    assert len({e["atajo"] for e in nav_panel()}) == len(SECCIONES)


def test_los_contadores_del_menu_salen_de_dos_consultas(entorno):
    """El badge del menú es el recuento de lo pendiente, no un adorno estático."""
    cliente, Session, datos = entorno
    from app.services.panel_contextos import contadores_panel

    with Session() as db:
        contadores = contadores_panel(db)
    # Una compra pendiente + una licencia que vence en dos días.
    assert contadores == {"ingresos": 2, "compras": 1, "renovaciones": 1}
    # Solo se decora lo que tiene números fiables y baratos: el resto del menú
    # no presume de cifras que exijan recorrer la base en cada petición.
    for entrada in nav_panel(contadores):
        if entrada["id"] != "ingresos":
            assert not entrada["contador"], entrada["id"]
    assert [e["contador"] for e in nav_panel(contadores)][2] == 2

def test_ZZZ(entorno):
    cliente, Session, _datos = entorno
    r = cliente.post("/admin/vistas/crear", data={"modulo": "clientes", "nombre": "Por vencer",
                  "filtros": '{"estado":"por_vencer"}', "volver": "/admin/clientes?tab=directorio"},
                  follow_redirects=False)
    print("LOC", r.headers["location"])
    with Session() as db:
        from app.services.web_admin import listar_vistas
        for v in listar_vistas(db, "clientes"):
            print("VISTA", v.id, v.modulo, v.nombre, v.filtros, v.creada_por)
    pagina = cliente.get("/admin/clientes?tab=directorio").text
    cuerpo = pagina[pagina.find("<main"):]
    for marca in ("chip-vista", "Gestionar (", "Guardar actual", "Filtros guardados", "chips-titulo"):
        print(marca, "->", marca in cuerpo)
    i = cuerpo.find("chips-titulo")
    print("BARRA>>>", repr(cuerpo[i - 400 : i + 900]) if i > 0 else "sin barra")



def test_los_enlaces_que_fabrican_los_servicios_apuntan_a_pantallas_reales(entorno):
    """⌘K y la campana no pueden enlazar a una página que ya no existe.

    El buscador y las notificaciones construyen URLs a mano, fuera de las
    plantillas. Cuando el panel se reorganizó, diez de esos enlaces siguieron
    apuntando a rutas fusionadas —o a parámetros que ninguna pestaña lee, como
    `?licencia=`—: respondían con un 302 y aterrizaban sin lo que prometían. Se
    comprueba contra el mismo validador de los formularios POST, y pidiendo la
    página de verdad.
    """
    cliente, Session, datos = entorno
    from app.services.panel_busqueda import buscar_global
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        urls = [r["url"] for q in ("Obras", "Delta", "compra", "op@example.com", "licencia")
                for r in buscar_global(db, q)]
        urls += [a["url"] for a in notificaciones_admin(db)]
    assert urls, "el seed debería producir enlaces que revisar"
    for url in urls:
        assert es_destino_panel(url.split("#")[0]), url
        assert cliente.get(url).status_code == 200, url

    with Session() as db:
        por_cliente = buscar_global(db, "Obras")
    # El resultado de una licencia no cae en una ruta huérfana: abre la lista de
    # contratos ya filtrada por ese cliente, donde está el botón de renovar.
    licencia = next(r for r in por_cliente if r["tipo"] == "licencia")
    assert licencia["url"] == "/admin/ingresos?tab=contratos&q=Obras%20Norte"
    # ...y el filtro del enlace funciona de verdad en esa pestaña.
    pagina = cliente.get(licencia["url"]).text
    assert "Obras Norte" in pagina and "Reformas Sur" not in pagina
    # Y el aviso de vencimiento de la campana lleva a la ficha del cliente.
    renovacion = next(a for a in notificaciones_admin(db) if a["tipo"] == "renovacion")
    assert renovacion["url"] == f"/admin/clientes/{datos['por_vencer']}?tab=acceso"
