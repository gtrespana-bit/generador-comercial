"""Una sola moneda en toda la aplicación: recursos y agregados.

El catálogo (partidas, productos y recursos) se guarda en USD y la
organización elige su moneda con una tasa de referencia. La regla del
producto es: **el usuario nunca ve dos monedas en la misma pantalla**.

Regresiones cubiertas (reportadas por el titular):

- la pestaña Recursos mostraba el precio base en USD y, debajo, el precio de
  mercado en su moneda: dos divisas en la misma tabla;
- el formulario de recurso editaba «Precio base (USD)» aunque el resto de la
  app hablara la moneda de la organización;
- el panel y los reportes sumaban totales de presupuestos con monedas
  distintas y etiquetaban el resultado con la moneda de la organización.
"""
import pytest

from app.models import (
    Capitulo,
    Configuracion,
    Partida,
    PrecioRecursoMercado,
    Presupuesto,
    PresupuestoItem,
    Recurso,
    Cliente,
)

TASA_MXN = 17.5


def _mexico(Session, *, precio_recurso=6.5):
    """Configura la organización en México: moneda MXN con tasa 17,5."""
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "México"
        cfg.moneda_default = "MXN"
        cfg.tasa_cambio = TASA_MXN
        cfg.onboarding_completado = True
        recurso = db.query(Recurso).first()
        recurso.precio = precio_recurso
        db.commit()
        return recurso.id


def test_lista_de_recursos_habla_una_sola_moneda(entorno, cliente_web):
    """Se muestra el precio de mercado; el base convertido nunca se enseña."""
    Session, _ids, _rol = entorno
    recurso_id = _mexico(Session, precio_recurso=6.5)
    with Session() as db:
        db.add(PrecioRecursoMercado(
            recurso_id=recurso_id, pais_codigo="MX", organizacion_id=None,
            precio=100.0, moneda="MXN", confianza="confirmado",
        ))
        db.commit()

    html = cliente_web.get("/recursos").text

    # Mercado ya está en MXN (referencia nacional): se muestra tal cual
    assert "Mercado MX: 100,00 MXN" in html
    # El precio base convertido (6,5 USD × 17,5 = 113,75 MXN) no se muestra
    assert "113,75 MXN" not in html
    assert "Base catálogo" not in html
    # La moneda base del recurso ya no se muestra como USD
    assert "6,50 USD" not in html
    # El encabezado de familia también totaliza en la moneda de la organización
    assert "MXN" in html


def test_formulario_de_recurso_no_muestra_el_precio_base(entorno, cliente_web):
    Session, _ids, _rol = entorno
    recurso_id = _mexico(Session, precio_recurso=6.5)

    html = cliente_web.get(f"/recursos/{recurso_id}/editar").text

    # El precio base ya no es un campo visible: solo se conserva en un oculto
    # para no perder la plantilla interna.
    assert "Precio base (MXN)" not in html
    assert 'name="precio"' in html
    assert 'value="113.75"' in html
    # Sin referencia nacional en esta prueba, el formulario avisa de que falta
    # precio de mercado en lugar de enseñar el base convertido.
    assert "Sin precio de mercado para MX" in html


def test_guardar_recurso_ignora_el_precio_base_y_guarda_el_precio_propio(entorno, cliente_web):
    """El formulario de mercado ignora el base y persiste el precio propio."""
    Session, _ids, _rol = entorno
    recurso_id = _mexico(Session, precio_recurso=6.5)

    respuesta = cliente_web.post(
        f"/recursos/{recurso_id}/editar",
        data={"codigo": "MO001", "descripcion": "Oficial", "unidad": "hora",
              "categoria": "mano_obra", "precio": "175.0",
              "precio_mercado": "200.0"},
        follow_redirects=False,
    )
    assert respuesta.status_code in (302, 303, 307)

    with Session() as db:
        recurso = db.get(Recurso, recurso_id)
        # El precio base del catálogo no se toca desde este formulario.
        assert recurso.precio == pytest.approx(6.5)
        # El precio propio de la organización queda persistido para el futuro.
        precio_propio = db.query(PrecioRecursoMercado).filter(
            PrecioRecursoMercado.recurso_id == recurso_id,
            PrecioRecursoMercado.pais_codigo == "MX",
            PrecioRecursoMercado.organizacion_id.isnot(None),
        ).one()
        assert precio_propio.precio == pytest.approx(200.0)
        assert precio_propio.moneda == "MXN"


def test_recurso_nuevo_guarda_la_moneda_local_como_base_usd(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _mexico(Session)

    respuesta = cliente_web.post(
        "/recursos/nuevo",
        data={"codigo": "MT900", "descripcion": "Arena", "unidad": "m3",
              "categoria": "materiales", "precio": "87.5"},
        follow_redirects=False,
    )
    assert respuesta.status_code in (302, 303, 307)

    with Session() as db:
        recurso = db.query(Recurso).filter(Recurso.codigo == "MT900").one()
        assert recurso.precio == pytest.approx(5.0)  # 87,5 MXN / 17,5


def test_precio_fijo_por_lote_se_escribe_en_la_moneda_de_la_organizacion(entorno, cliente_web):
    Session, _ids, _rol = entorno
    recurso_id = _mexico(Session, precio_recurso=6.5)

    respuesta = cliente_web.post(
        "/recursos/bulk-ajustar-seleccion",
        data={"ids": str(recurso_id), "precio_fijo": "17.5"},
        follow_redirects=False,
    )
    assert respuesta.status_code in (302, 303, 307)

    with Session() as db:
        recurso = db.get(Recurso, recurso_id)
        assert recurso.precio == pytest.approx(1.0)  # 17,5 MXN / 17,5


def test_exportacion_csv_de_recursos_expresa_la_moneda_de_la_organizacion(entorno, cliente_web):
    Session, _ids, _rol = entorno
    recurso_id = _mexico(Session, precio_recurso=6.5)
    with Session() as db:
        db.add(PrecioRecursoMercado(
            recurso_id=recurso_id, pais_codigo="MX", organizacion_id=None,
            precio=100.0, moneda="MXN", confianza="confirmado",
        ))
        db.commit()

    csv = cliente_web.get("/recursos/exportar").content.decode("utf-8")

    assert "Moneda" in csv
    assert "MXN" in csv
    assert "100,00" in csv
    assert "113,75" not in csv  # el base convertido no viaja en exportaciones
    assert "6,50" not in csv  # el precio crudo en USD ya no viaja


def test_panel_agrega_presupuestos_de_monedas_distintas_en_una_sola(entorno, cliente_web):
    """Un presupuesto USD y uno MXN: el volumen aprobado se muestra en MXN."""
    Session, ids, _rol = entorno
    _mexico(Session)
    with Session() as db:
        from datetime import date as _date
        # Los presupuestos del fixture pasan a borrador para que no entren en
        # el agregado de aprobados (borrarlos rompería FKs de proyectos).
        for previa in db.query(Presupuesto).all():
            previa.estado = "borrador"
        cliente = db.query(Cliente).first()

        def _presupuesto(numero, estado, moneda, tipo_cambio, cantidad, precio):
            # impuesto 0 para que la cifra esperada sea exacta
            p = Presupuesto(
                numero=numero, year=2026, moneda=moneda,
                tipo_cambio=tipo_cambio, estado=estado, client_id=cliente.id,
                fecha=_date.today(), impuesto_pct=0.0,
                # Esta prueba inserta por ORM y se salta el guardado HTTP, que
                # es quien persiste el total cacheado usado por el panel.
                total_calculado=cantidad * precio,
            )
            cap = Capitulo(nombre="OBRA", orden=1)
            cap.partidas.append(PresupuestoItem(
                nombre="Partida", unidad="m2", cantidad=cantidad,
                precio_unitario=precio, orden=1,
            ))
            p.capitulos.append(cap)
            db.add(p)

        # 10 m2 × 20 USD = 200 USD → 3.500 MXN con la tasa de la organización
        _presupuesto("P-USD", "aprobado", "USD", 1.0, 10, 20)
        # 10 m2 × 100 MXN = 1.000 MXN (misma moneda: sin puente)
        _presupuesto("P-MXN", "aprobado", "MXN", TASA_MXN, 10, 100)
        db.commit()

    html = cliente_web.get("/inicio").text

    # 200 USD × 17,5 + 1.000 MXN = 4.500 MXN, con la etiqueta de la moneda
    assert "4.500,00 MXN" in html


def test_reportes_totalizan_en_la_moneda_de_la_organizacion(entorno, cliente_web):
    Session, ids, _rol = entorno
    _mexico(Session)
    with Session() as db:
        from datetime import date as _date
        hoy = _date.today()
        cliente = db.query(Cliente).first()
        p = Presupuesto(
            numero="P-USD", year=2026, moneda="USD", tipo_cambio=1.0,
            estado="enviado", client_id=cliente.id, fecha=hoy, impuesto_pct=0.0,
        )
        cap = Capitulo(nombre="OBRA", orden=1)
        cap.partidas.append(PresupuestoItem(
            nombre="Partida", unidad="m2", cantidad=10, precio_unitario=20, orden=1,
        ))
        p.capitulos.append(cap)
        db.add(p)
        db.commit()

    html = cliente_web.get(
        "/reportes", params={"desde": hoy.isoformat(), "hasta": hoy.isoformat()}
    ).text

    # 200 USD × 17,5 = 3.500 MXN en el importe presupuestado del período
    assert "3.500,00 MXN" in html


def test_moneda_sin_tasa_no_etiqueta_pesos_sobre_cifras_en_dolares(entorno, cliente_web):
    """Organización MXN sin tasa: sin conversión inventada no se muestra la
    base convertida como si fuera un precio de mercado."""
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "México"
        cfg.moneda_default = "MXN"
        cfg.tasa_cambio = None
        db.commit()

    html = cliente_web.get("/recursos").text

    # El precio base (Venezuela convertida) no se enseña como mercado.
    assert "6,50 USD" not in html
    assert "113,75 MXN" not in html
    assert "Sin precio de mercado para MX" in html
    assert "MXN total" not in html
    assert "Importes en <strong>USD</strong>" in html


def test_formulario_de_partida_nueva_etiqueta_la_moneda_de_la_organizacion(entorno, cliente_web):
    """La ruta nueva de partida ya no dice «USD» cuando la organización
    trabaja en otra moneda (el POST siempre convirtió desde la local)."""
    Session, _ids, _rol = entorno
    _mexico(Session)

    html = cliente_web.get("/partidas/nueva").text

    assert "Precio de venta (MXN)" in html
