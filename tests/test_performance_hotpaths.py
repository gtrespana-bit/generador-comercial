"""Regresiones de rendimiento de las rutas comerciales de mayor uso."""
from __future__ import annotations

from datetime import date

from sqlalchemy import event


def test_listado_presupuestos_evitar_n_mas_uno_con_totales_legacy(entorno, cliente_web):
    from app.models import Capitulo, Presupuesto, PresupuestoItem

    Session, ids, _ = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        base = db.get(Presupuesto, ids[2])
        client_id = base.client_id
        # El fixture incluye un presupuesto de demostración sin total congelado;
        # se separa de los casos legacy que queremos medir aquí.
        for existente in db.query(Presupuesto).filter_by(organizacion_id=ids[0]):
            existente.total_calculado = 200.0

        legacy = []
        for indice in range(15):
            presupuesto = Presupuesto(
                organizacion_id=ids[0],
                numero=f"PERF-{indice:03d}",
                year=2026,
                fecha=date(2026, 1, 1),
                titulo=f"Presupuesto de rendimiento {indice}",
                estado="borrador",
                client_id=client_id,
                impuesto_pct=0.0,
                total_calculado=None,
            )
            presupuesto.capitulos.append(Capitulo(
                organizacion_id=ids[0],
                nombre=f"Capítulo {indice}",
                orden=1,
                partidas=[PresupuestoItem(
                    organizacion_id=ids[0],
                    nombre="Partida de prueba",
                    cantidad=1,
                    precio_unitario=123.45,
                    orden=1,
                )],
            ))
            legacy.append(presupuesto)
        db.add_all(legacy)
        db.commit()
        bind = db.get_bind()

    tablas_detalle = (
        "capitulos",
        "presupuesto_items",
        "mediciones",
        "presupuesto_item_productos",
        "descomposiciones_partida",
        "descomposicion_filas",
    )
    consultas_por_tabla = {tabla: [] for tabla in tablas_detalle}

    def contar_detalle(_conn, _cursor, statement, _params, _context, _many):
        sql = " ".join(statement.lower().split())
        if not sql.startswith("select"):
            return
        for tabla in tablas_detalle:
            if f"from {tabla} " in sql or f"from {tabla}\n" in sql:
                consultas_por_tabla[tabla].append(statement)
                break

    event.listen(bind, "before_cursor_execute", contar_detalle)
    try:
        for ruta in ("/presupuestos", "/en/presupuestos"):
            antes = {tabla: len(consultas) for tabla, consultas in consultas_por_tabla.items()}
            respuesta = cliente_web.get(ruta)
            assert respuesta.status_code == 200
            assert "123,45" in respuesta.text or "123.45" in respuesta.text
            for tabla, consultas in consultas_por_tabla.items():
                # Una carga select-in por tabla, no una consulta por cada fila.
                assert len(consultas) - antes[tabla] <= 1, (ruta, tabla, consultas)
    finally:
        event.remove(bind, "before_cursor_execute", contar_detalle)
