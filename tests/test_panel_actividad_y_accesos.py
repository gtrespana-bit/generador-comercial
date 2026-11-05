"""Panel: la información a un clic (contadores con lista, email y actividad).

Tres preguntas del operador que antes exigían adivinar dónde mirar:

1. «¿A quién cuenta ese 7 de “por vencer”?» → cada contador del directorio es
   un enlace a su lista, con el MISMO criterio con el que se contó.
2. «Busco por el correo del cliente y no sale nada» → el directorio y el
   buscador global encuentran empresas por el email de sus usuarios.
3. «¿Esta empresa está usando el producto y qué le molesta?» → la ficha tiene
   actividad real: cifras, qué modifica al guardar y una cronología legible.

Se comprueba sobre HTTP y sobre los servicios, no sobre el CSS: el adorno se
puede romper; lo que no puede romperse es que el enlace lleve a la lista.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_operator_db
from app.main import app
from app.models import (
    EventoAuditoria,
    Licencia,
    Membresia,
    Organizacion,
    Usuario,
)

HOY = date.today()


@pytest.fixture
def panel():
    """Dos clientes con licencia (uno por vencer) y uno sin plan ni uso."""
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
        # La membresía es lo que permite encontrar la empresa por email.
        db.add(Membresia(organizacion_id=por_vencer.id, usuario_id=usuario.id, rol="propietario"))
        db.add_all([
            Licencia(
                organizacion_id=por_vencer.id, origen="pago", importe=89.0, moneda="USD",
                inicio=HOY - timedelta(days=363), vence=HOY + timedelta(days=2),
                estado="activa", metodo_cobro="Zelle", creada_por_email="op@example.com",
            ),
            Licencia(
                organizacion_id=al_dia.id, origen="pago", importe=89.0, moneda="USD",
                inicio=HOY - timedelta(days=10), vence=HOY + timedelta(days=355),
                estado="activa", creada_por_email="op@example.com",
            ),
        ])
        db.commit()
        datos = {
            "por_vencer": por_vencer.id,
            "al_dia": al_dia.id,
            "sin_plan": sin_plan.id,
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
        yield TestClient(app, base_url="https://cotizat.test"), Session, datos
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


# ---------------------------------------------------------------------------
# 1. El aviso de la campana lleva al cliente, no a una lista parecida
# ---------------------------------------------------------------------------


def test_el_aviso_de_vencimiento_lleva_al_cliente_y_a_su_lista(panel):
    _cliente, Session, datos = panel
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        aviso = next(a for a in notificaciones_admin(db) if a["tipo"] == "renovacion")

    # El hecho: «Obras Norte vence en 2 días» abre Obras Norte.
    assert aviso["url"] == f"/admin/clientes/{datos['por_vencer']}?tab=acceso"
    # Y el resto de avisos iguales, con el MISMO umbral que anuncia el aviso.
    assert aviso["url_lista"] == "/admin/clientes?tab=directorio&dias=3"
    assert "≤3" in aviso["etiqueta_lista"]


def test_la_campana_no_corta_las_ventas_por_el_tope_de_renovaciones(panel):
    """El `break` a 8 avisos se llevaba por delante ventas y soporte."""
    _cliente, Session, _datos = panel
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        avisos = notificaciones_admin(db)

    # El aviso de «sin plan» se calcula al final: si el tope cortara antes,
    # desaparecería y el operador no vería el estado del negocio.
    assert any(a["tipo"] == "negocio" for a in avisos)
    assert len(avisos) <= 15


# ---------------------------------------------------------------------------
# 2. Cada contador del directorio abre exactamente su lista
# ---------------------------------------------------------------------------


def test_cada_contador_del_directorio_es_un_enlace_a_su_lista(panel):
    cliente, _Session, _datos = panel
    pagina = cliente.get("/admin/clientes?tab=directorio").text

    assert 'class="kpi-card enlaza info" href="/admin/clientes?tab=directorio&estado=activa"' in pagina
    assert 'href="/admin/clientes?tab=directorio&estado=por_vencer"' in pagina
    assert 'href="/admin/clientes?tab=directorio&plan=sin"' in pagina


def test_la_ventana_del_vencimiento_acota_la_lista(panel):
    """«Por vencer ≤15» y «≤3 días» son dos listas distintas y las dos existen."""
    cliente, _Session, datos = panel

    quince = cliente.get("/admin/clientes?tab=directorio&estado=por_vencer")
    tres = cliente.get("/admin/clientes?tab=directorio&dias=3")
    activos = cliente.get("/admin/clientes?tab=directorio&estado=activa")
    sin_plan = cliente.get("/admin/clientes?tab=directorio&plan=sin")

    assert "Obras Norte" in quince.text and "Reformas Sur" not in quince.text
    assert "Obras Norte" in tres.text and "Reformas Sur" not in tres.text
    # Reformas Sur vence en 355 días: no entra en ninguna ventana de aviso, ni
    # siquiera en la de 30, y por eso el contador de «por vencer» no la cuenta.
    for ventana in ("3", "7", "15", "30"):
        assert "Reformas Sur" not in cliente.get(
            f"/admin/clientes?tab=directorio&dias={ventana}"
        ).text
    # Una ventana que no está en el catálogo no filtra nada (no inventa listas).
    assert "Reformas Sur" in cliente.get("/admin/clientes?tab=directorio&dias=999").text
    assert "Reformas Sur" in activos.text and "Obras Norte" not in activos.text
    assert "Tecnicos Delta" in sin_plan.text
    assert datos["por_vencer"]  # el fixture es el que sostiene lo anterior


# ---------------------------------------------------------------------------
# 3. Buscar por email encuentra la empresa (directorio y ⌘K)
# ---------------------------------------------------------------------------


def test_el_directorio_encuentra_por_email_del_usuario(panel):
    cliente, _Session, _datos = panel
    pagina = cliente.get(
        "/admin/clientes?tab=directorio&q=cliente%40example.com"
    ).text

    assert "Obras Norte" in pagina
    assert "Reformas Sur" not in pagina
    # Y el email se ve en la fila: si no aparece, parece que la búsqueda falló.
    assert "cliente@example.com" in pagina


def test_el_buscador_global_devuelve_la_empresa_por_email_y_su_url_funciona(panel):
    cliente, Session, _datos = panel
    from app.services.panel_busqueda import buscar_global

    with Session() as db:
        resultados = buscar_global(db, "cliente@example.com")

    por_email = [r for r in resultados if r["tipo"] == "cliente"]
    assert por_email, "el email de un usuario tiene que encontrar su empresa"
    url = por_email[0]["url"]
    assert url == "/admin/clientes?tab=directorio&q=cliente%40example.com"
    assert cliente.get(url).status_code == 200


# ---------------------------------------------------------------------------
# 4. La ficha cuenta qué hace la empresa y qué modifica
# ---------------------------------------------------------------------------


def _sembrar_actividad(Session, organizacion_id: int) -> None:
    with Session() as db:
        db.add_all([
            EventoAuditoria(
                organizacion_id=organizacion_id,
                actor_email="cliente@example.com",
                accion="presupuesto.creado",
                entidad="presupuesto",
                entidad_id=1,
                detalle='{"numero": "P-1", "partidas": 12, "total": 1500.0, "moneda": "USD"}',
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
            EventoAuditoria(
                organizacion_id=organizacion_id,
                actor_email="cliente@example.com",
                accion="presupuesto.editado",
                entidad="presupuesto",
                entidad_id=1,
                # Lo que el titular corrigió al guardar: 9 precios y 2 textos.
                detalle=(
                    '{"precios": 9, "textos": 2, "partidas_total": 12,'
                    ' "resumen": "9 precios corregidos, 2 textos reescritos"}'
                ),
                created_at=datetime.utcnow() - timedelta(hours=5),
            ),
        ])
        db.commit()


def test_la_ficha_cuenta_la_actividad_en_castellano(panel):
    cliente, Session, datos = panel
    _sembrar_actividad(Session, datos["por_vencer"])

    pagina = cliente.get(f"/admin/clientes/{datos['por_vencer']}?tab=actividad").text

    assert "Presupuestos creados" in pagina
    assert "Creó un presupuesto" in pagina
    assert "Modificó un presupuesto" in pagina
    assert "9 precios corregidos, 2 textos reescritos" in pagina
    assert "Qué modifica cuando guarda" in pagina
    assert "Precios corregidos" in pagina
    # Nunca un código interno en la columna «qué».
    assert ">presupuesto.editado<" not in pagina
    # La cronología lleva a la pestaña donde el hecho se amplía.
    assert f"/admin/clientes/{datos['por_vencer']}?tab=presupuestos" in pagina


def test_la_actividad_de_una_cuenta_sin_uso_lo_dice(panel):
    cliente, _Session, datos = panel
    pagina = cliente.get(f"/admin/clientes/{datos['sin_plan']}?tab=actividad").text

    assert "Todavía no hay actividad registrada" in pagina
    assert "señal más temprana de abandono" in pagina


def test_la_pestana_de_actividad_degrada_sin_500(panel, monkeypatch):
    cliente, _Session, datos = panel
    import app.services.actividad as servicio

    def _roto(*_args, **_kwargs):
        raise RuntimeError("función sin migrar")

    monkeypatch.setattr(servicio, "actividad_organizacion", _roto)
    respuesta = cliente.get(f"/admin/clientes/{datos['por_vencer']}?tab=actividad")

    assert respuesta.status_code == 200
    assert "No se pudo leer la actividad de este cliente" in respuesta.text
    # El resto de la ficha sigue en pie.
    assert "Obras Norte" in respuesta.text


# ---------------------------------------------------------------------------
# 5. La analítica dice qué se modifica más al guardar
# ---------------------------------------------------------------------------


def test_la_analitica_ensena_que_se_modifica_mas(panel):
    cliente, Session, datos = panel
    _sembrar_actividad(Session, datos["por_vencer"])

    pagina = cliente.get("/admin/analitica?dias=30").text

    assert "Qué se modifica al guardar un presupuesto" in pagina
    assert "Precios corregidos" in pagina
    assert "Textos reescritos" in pagina


def test_la_analitica_sin_ediciones_lo_explica_en_vez_de_inventar(panel):
    cliente, _Session, _datos = panel
    pagina = cliente.get("/admin/analitica?dias=30").text

    assert "Todavía no hay ediciones medidas" in pagina


# ---------------------------------------------------------------------------
# 6. El recuento de cambios es puro: no toca la base ni guarda contenido
# ---------------------------------------------------------------------------


def test_el_resumen_de_cambios_cuenta_sin_guardar_el_texto_del_cliente():
    from app.services.actividad import resumen_cambios, texto_resumen

    antes = {
        "total": 1000.0,
        "estado": "borrador",
        "partidas": {
            "1": {"nombre": "Muro de fábrica", "precio": 10.0, "cantidad": 2.0, "unidad": "m2"},
        },
        "capitulos": {"1": "Albañilería"},
    }
    # Lo que trae el formulario: precio y nombre tocados, una partida nueva.
    partidas = [
        {"id": "1", "nombre": "Muro de ladrillo", "precio": 12.0, "cantidad": 2.0, "unidad": "m2"},
        {"nombre": "Solera", "precio": 5.0, "cantidad": 3.0, "unidad": "ml"},
    ]
    cambios = resumen_cambios(antes, partidas, [{"nombre": "Albañilería"}])

    assert cambios["precios"] == 1
    assert cambios["textos"] == 1
    assert cambios["partidas_nuevas"] == 1
    assert cambios["partidas_eliminadas"] == 0
    # El detalle del evento son cifras: ni un nombre de partida se guarda.
    assert all(isinstance(valor, (int, float, str)) for valor in cambios.values())
    assert "Muro" not in str(cambios)
    assert texto_resumen(cambios) == "1 partida nueva, 1 precio corregido, 1 texto reescrito"


# ---------------------------------------------------------------------------
# 7. «Paga y no entra» / «se registró y no probó nada»
# ---------------------------------------------------------------------------


def test_la_campana_avisa_de_quien_paga_y_no_usa_el_producto(panel):
    _cliente, Session, datos = panel
    from app.models import EventoProducto
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        # Reformas Sur paga y no ha hecho nada; Obras Norte sí trabaja.
        db.add(EventoProducto(
            organizacion_id=datos["por_vencer"],
            accion="presupuesto.creado",
            actor_email="cliente@example.com",
            detalle="{}",
            created_at=datetime.utcnow() - timedelta(hours=3),
        ))
        db.commit()
        avisos = notificaciones_admin(db)

    silencio = [a for a in avisos if a["tipo"] == "uso"]
    assert len(silencio) == 1
    assert "Reformas Sur" in silencio[0]["titulo"]
    assert silencio[0]["url"] == f"/admin/clientes/{datos['al_dia']}?tab=actividad"
    assert "Obras Norte" not in silencio[0]["titulo"]


def test_el_inicio_de_sesion_cuenta_como_dia_de_uso(panel):
    _cliente, Session, datos = panel
    from app.models import EventoAuditoria
    from app.services.actividad import actividad_organizacion

    with Session() as db:
        db.add(
            EventoAuditoria(
                organizacion_id=datos["sin_plan"],
                accion="sesion.login",
                actor_email="cliente@example.com",
                detalle="{}",
                created_at=datetime.utcnow() - timedelta(days=1),
            )
        )
        db.commit()
        datos_act = actividad_organizacion(db, datos["sin_plan"], dias=30)

    # Sin este inicio de sesión la empresa tendría 0 días de uso.
    assert datos_act["kpis"]["dias_uso"] >= 1
    assert datos_act["kpis"]["ultima_actividad"] is not None


def test_la_campana_avisa_de_un_alta_que_no_ha_probado_nada(panel):
    _cliente, Session, _datos = panel
    from app.services.panel_notificaciones import notificaciones_admin

    with Session() as db:
        tipos = {a["tipo"] for a in notificaciones_admin(db)}

    assert "activacion" in tipos


def test_si_la_telemetria_no_se_puede_leer_la_campana_sigue(panel, monkeypatch):
    """Best-effort: la tabla de uso caída no deja al operador sin campana."""
    _cliente, Session, _datos = panel
    from app.services import panel_notificaciones as servicio

    class _MotorRoto:
        def query(self, *_args, **_kwargs):
            raise RuntimeError("tabla sin migrar")

    avisos = servicio._avisos_uso(_MotorRoto(), HOY, {})
    assert avisos == []


def test_el_csv_del_directorio_exporta_la_misma_lista_que_la_pantalla(panel):
    """Si el contador lleva a una lista, el CSV de esa lista es el mismo filtro."""
    cliente, _Session, _datos = panel

    csv = cliente.get("/admin/clientes.csv?dias=3")

    assert csv.status_code == 200
    lineas = [linea for linea in csv.text.strip().splitlines() if linea.strip()]
    assert len(lineas) == 2                      # cabecera + la única empresa ≤3 días
    assert "Obras Norte" in lineas[1]
    assert "Reformas Sur" not in csv.text


def test_los_kpis_del_panel_llevan_a_la_misma_lista_que_cuentan(panel):
    """Un contador y su lista no pueden discrepar: el 3 tiene que abrir a los 3."""
    cliente, _Session, _datos = panel
    pagina = cliente.get("/admin").text

    assert 'href="/admin/clientes?tab=directorio&plan=sin"' in pagina
    assert 'href="/admin/clientes?tab=directorio&estado=por_vencer"' in pagina
    assert 'href="/admin/clientes?tab=directorio&estado=sin_licencia"' not in pagina
    # Y esa lista contiene al cliente que el contador sumó.
    assert "Tecnicos Delta" in cliente.get(
        "/admin/clientes?tab=directorio&plan=sin"
    ).text
