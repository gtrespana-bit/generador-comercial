"""Métricas financieras del negocio (B6): MRR/ARR, renovaciones y LTV.

Se calculan desde ``licencias`` (tabla sin RLS de tenant: la única fuente
fiable de ingresos del titular) y ``compras_plan``. No se leen presupuestos ni
pagos de clientes, que siguen bajo aislamiento multi-tenant.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func

from ..models import CompraPlan, Licencia, Organizacion
from .licencias import vence_cadena


def _es_mensual(licencia: Licencia) -> bool:
    """Heurística para separar planes mensuales de anuales por duración."""
    try:
        return (licencia.vence - licencia.inicio).days <= 45
    except Exception:
        return False


def _periodo_desde(mes: datetime) -> datetime:
    return mes


def _periodo_hasta(mes: datetime) -> datetime:
    if mes.month == 12:
        return mes.replace(year=mes.year + 1, month=1, day=1) - timedelta(seconds=1)
    return mes.replace(month=mes.month + 1, day=1) - timedelta(seconds=1)


def resumen_financiero(
    db,
    *,
    hoy: date | None = None,
    meses_serie: int = 6,
) -> dict:
    """Métricas para el dashboard: negocio en movimiento, no solo acumulado.

    Ahora incluye comparativas contra el mes anterior para cada KPI principal:
    MRR, ARR, ingresos del mes y clientes de pago. El operador ve de un golpe
    si el número sube o baja, no solo el valor absoluto.
    """
    hoy = hoy or date.today()
    inicio_mes = hoy.replace(day=1)
    fin_mes = (
        inicio_mes.replace(year=inicio_mes.year + 1, month=1, day=1)
        - timedelta(days=1)
        if inicio_mes.month == 12
        else inicio_mes.replace(month=inicio_mes.month + 1, day=1) - timedelta(days=1)
    )

    # Mes anterior para comparativas.
    if inicio_mes.month == 1:
        inicio_mes_anterior = inicio_mes.replace(year=inicio_mes.year - 1, month=12, day=1)
    else:
        inicio_mes_anterior = inicio_mes.replace(month=inicio_mes.month - 1, day=1)
    fin_mes_anterior = (
        inicio_mes_anterior.replace(year=inicio_mes_anterior.year + 1, month=1, day=1)
        - timedelta(days=1)
        if inicio_mes_anterior.month == 12
        else inicio_mes_anterior.replace(month=inicio_mes_anterior.month + 1, day=1)
        - timedelta(days=1)
    )

    try:
        from .organizaciones_test import ids_organizaciones_test
        ids_test = ids_organizaciones_test(db)
    except Exception:
        ids_test = set()
    licencias = [l for l in db.query(Licencia).all() if int(l.organizacion_id) not in ids_test]
    compras = [c for c in db.query(CompraPlan).all() if int(c.organizacion_id) not in ids_test]
    # Organizaciones reales = totales menos test
    total_orgs = db.query(Organizacion).count()
    organizaciones = total_orgs - len(ids_test) if ids_test else total_orgs

    # --- Ingresos por cliente (LTV real) --------------------------------
    ingresos_por_org: dict[int, float] = defaultdict(float)
    por_mes: dict[int, dict[str, float]] = defaultdict(lambda: {"ingresos": 0.0, "renovaciones": 0.0})

    activas_pago = []
    ingresos_total = 0.0
    ticket_sum = 0.0
    ticket_count = 0
    mrr_mensual = 0.0
    mrr_anual = 0.0
    renovaciones_mes = 0.0
    licencias_renovando = 0

    # MRR del mes anterior (para comparativa).
    mrr_mes_anterior = 0.0

    for lic in licencias:
        if lic.origen != "pago" or lic.importe <= 0:
            continue
        ingresos_total += lic.importe
        ingresos_por_org[lic.organizacion_id] += lic.importe
        ticket_sum += lic.importe
        ticket_count += 1

        clave_mes = (lic.created_at.year, lic.created_at.month) if lic.created_at else (hoy.year, hoy.month)
        por_mes[clave_mes]["ingresos"] = por_mes[clave_mes]["ingresos"] + lic.importe

        vigente = lic.inicio <= hoy <= lic.vence and lic.estado == "activa"
        if vigente:
            activas_pago.append(lic)
            if _es_mensual(lic):
                mrr_mensual += lic.importe
            else:
                mrr_anual += lic.importe / 12.0

        # Vigente en el mes anterior: la licencia cubría algún día de ese mes.
        vigente_mes_anterior = (
            lic.inicio <= fin_mes_anterior
            and lic.vence >= inicio_mes_anterior
            and lic.estado == "activa"
        )
        if vigente_mes_anterior:
            if _es_mensual(lic):
                mrr_mes_anterior += lic.importe
            else:
                mrr_mes_anterior += lic.importe / 12.0

        # Renovaciones: importe previsto de las que vencen este mes.
        if lic.vence and lic.vence.year == inicio_mes.year and lic.vence.month == inicio_mes.month:
            renovaciones_mes += lic.importe
            licencias_renovando += 1
            clave_ren = (lic.vence.year, lic.vence.month)
            por_mes[clave_ren]["renovaciones"] = por_mes[clave_ren]["renovaciones"] + lic.importe

    mrr = mrr_mensual + mrr_anual
    arr = mrr * 12.0
    arr_mes_anterior = mrr_mes_anterior * 12.0

    # Ingresos del mes actual y anterior.
    ingresos_mes = round(
        por_mes.get((inicio_mes.year, inicio_mes.month), {}).get("ingresos", 0.0), 2
    )
    ingresos_mes_anterior = round(
        por_mes.get((inicio_mes_anterior.year, inicio_mes_anterior.month), {}).get(
            "ingresos", 0.0
        ),
        2,
    )

    # --- Convergencia: cuántos clientes alguna vez pagaron ------------------
    clientes_con_pago = len(ingresos_por_org)
    tasa_pago = round(clientes_con_pago / organizaciones * 100.0, 1) if organizaciones else 0.0
    ticket_medio = round(ticket_sum / ticket_count, 2) if ticket_count else 0.0
    ltv_clients = list(ingresos_por_org.values())
    ltv_medio = round(sum(ltv_clients) / len(ltv_clients), 2) if ltv_clients else 0.0

    # Agrupa licencias por organización para calcular clientes activos por mes.
    lic_por_org: dict[int, list] = defaultdict(list)
    for lic in licencias:
        lic_por_org[lic.organizacion_id].append(lic)

    # Clientes con licencia de pago vigente este mes vs mes anterior.
    clientes_con_pago_mes = len(
        {
            org_id
            for org_id, cadena in lic_por_org.items()
            if any(
                l.origen == "pago"
                and l.importe > 0
                and l.inicio <= hoy
                and l.vence >= hoy
                and l.estado == "activa"
                for l in cadena
            )
        }
    )
    clientes_con_pago_mes_anterior = len(
        {
            org_id
            for org_id, cadena in lic_por_org.items()
            if any(
                l.origen == "pago"
                and l.importe > 0
                and l.inicio <= fin_mes_anterior
                and l.vence >= inicio_mes_anterior
                and l.estado == "activa"
                for l in cadena
            )
        }
    )

    # --- Serie de meses -----------------------------------------------------
    serie = []
    cursor = inicio_mes
    for _ in range(max(1, int(meses_serie))):
        cursor = _mes_anterior(cursor)
    end = inicio_mes
    for _ in range(max(1, int(meses_serie))):
        clave = (end.year, end.month)
        serie.append({
            "label": f"{_MESES[end.month]} {end.year}",
            "ingresos": round(por_mes[clave]["ingresos"], 2),
            "renovaciones": round(por_mes[clave]["renovaciones"], 2),
        })
        end = _mes_siguiente(end)

    def _variacion(actual: float, anterior: float) -> float | None:
        if anterior and anterior > 0:
            return round((actual - anterior) / anterior * 100, 1)
        if actual > 0 and anterior == 0:
            return 100.0
        return None

    return {
        "hoy": hoy,
        "mrr": round(mrr, 2),
        "mrr_mes_anterior": round(mrr_mes_anterior, 2),
        "mrr_variacion": _variacion(mrr, mrr_mes_anterior),
        "arr": round(arr, 2),
        "arr_mes_anterior": round(arr_mes_anterior, 2),
        "arr_variacion": _variacion(arr, arr_mes_anterior),
        "ingresos_total": round(ingresos_total, 2),
        "ingresos_mes": ingresos_mes,
        "ingresos_mes_anterior": ingresos_mes_anterior,
        "ingresos_variacion": _variacion(ingresos_mes, ingresos_mes_anterior),
        "renovaciones_mes": round(renovaciones_mes, 2),
        "licencias_renovando_mes": licencias_renovando,
        "ticket_medio": ticket_medio,
        "tasa_pago": tasa_pago,
        "clientes_con_pago": clientes_con_pago,
        "clientes_con_pago_mes": clientes_con_pago_mes,
        "clientes_con_pago_mes_anterior": clientes_con_pago_mes_anterior,
        "clientes_variacion": _variacion(clientes_con_pago_mes, clientes_con_pago_mes_anterior),
        "organizaciones": organizaciones,
        "ltv_medio": ltv_medio,
        "licencias_activas": len(activas_pago),
        "serie": serie,
    }


def _mes_anterior(fecha: date) -> date:
    if fecha.month == 1:
        return fecha.replace(year=fecha.year - 1, month=12, day=1)
    return fecha.replace(month=fecha.month - 1, day=1)


def _mes_siguiente(fecha: date) -> date:
    if fecha.month == 12:
        return fecha.replace(year=fecha.year + 1, month=1, day=1)
    return fecha.replace(month=fecha.month + 1, day=1)


_MESES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


# ---------------------------------------------------------------------------
# Movimiento del MRR (tramo F)
# ---------------------------------------------------------------------------
#
# `resumen_financiero` da el MRR de hoy y su variación contra el mes anterior.
# Eso responde «cuánto» pero no «por qué»: un mes puede cerrar plano con dos
# altas y dos bajas que se compensan, y esa es justo la información que dice si
# el negocio crece o se está fugando. Aquí se descompone el mes en las cuatro
# piezas estándar —nuevo, expansión, contracción y baja— y se comprueba que
# cuadren: apertura + neto = cierre, sin residuos ni «ajustes».

def _mrr_de_licencia(licencia: Licencia) -> float:
    """Ingreso mensual recurrente que aporta una licencia.

    Los planes anuales se reparten entre doce meses (misma regla que
    ``resumen_financiero``), para que el MRR no salte el día que alguien paga
    un año de golpe.
    """
    importe = float(licencia.importe or 0.0)
    return importe if _es_mensual(licencia) else importe / 12.0


def _licencia_cubre(licencia: Licencia, dia: date) -> bool:
    """¿La licencia da acceso de pago ese día?

    Se decide por fechas y no por ``estado``: una licencia vencida en octubre
    conserva ``estado="vencida"`` para siempre, así que mirar el estado haría
    desaparecer también el histórico. Solo se excluye lo cancelado a mano, que
    es una decisión, no el paso del tiempo.
    """
    if licencia.origen != "pago" or float(licencia.importe or 0.0) <= 0:
        return False
    if (licencia.estado or "") == "cancelada":
        return False
    if not licencia.inicio or not licencia.vence:
        return False
    return licencia.inicio <= dia <= licencia.vence


def _mrr_por_organizacion(licencias, dia: date) -> dict[int, float]:
    """MRR que aporta cada cliente ese día (suma de sus licencias vigentes)."""
    acumulado: dict[int, float] = defaultdict(float)
    for licencia in licencias:
        if _licencia_cubre(licencia, dia):
            acumulado[licencia.organizacion_id] += _mrr_de_licencia(licencia)
    return {org: round(monto, 2) for org, monto in acumulado.items() if monto > 0}


def _descomponer(apertura: dict[int, float], cierre: dict[int, float]) -> dict:
    """Las cuatro piezas del mes, derivadas del paso de apertura a cierre.

    Se calculan por cliente para que «expansión» y «contracción» signifiquen
    algo: un cliente que sube de plan y otro que baja no son dos altas.
    """
    nuevo = round(sum(m for org, m in cierre.items() if org not in apertura), 2)
    baja = round(sum(m for org, m in apertura.items() if org not in cierre), 2)
    expansion = round(
        sum(m - apertura[org] for org, m in cierre.items()
            if org in apertura and m > apertura[org]),
        2,
    )
    contraccion = round(
        sum(apertura[org] - m for org, m in cierre.items()
            if org in apertura and m < apertura[org]),
        2,
    )
    neto = round(nuevo + expansion - contraccion - baja, 2)
    return {
        "nuevo": nuevo,
        "expansion": expansion,
        "contraccion": contraccion,
        "baja": baja,
        "neto": neto,
        "clientes_nuevos": sum(1 for org in cierre if org not in apertura),
        "clientes_baja": sum(1 for org in apertura if org not in cierre),
        "clientes_expansion": sum(
            1 for org, m in cierre.items() if org in apertura and m > apertura[org]
        ),
        "clientes_contraccion": sum(
            1 for org, m in cierre.items() if org in apertura and m < apertura[org]
        ),
        "clientes_activos": len(cierre),
    }


def movimiento_mrr(
    db,
    *,
    hoy: date | None = None,
    meses: int = 6,
) -> dict:
    """Cómo se movió el MRR, mes a mes, y por qué.

    Devuelve el mes en curso descompuesto (apertura, nuevo, expansión,
    contracción, baja, cierre) y la serie de los ``meses`` anteriores para ver
    la tendencia. ``cuadra`` es la comprobación de que la aritmética cierra:
    apertura + neto == cierre. Si algún día deja de cuadrar, es un bug del
    cálculo y la tarjeta lo dice en vez de esconderlo.
    """
    hoy = hoy or date.today()
    try:
        from .organizaciones_test import ids_organizaciones_test
        ids_test = ids_organizaciones_test(db)
    except Exception:
        ids_test = set()
    licencias = [l for l in db.query(Licencia).all() if int(l.organizacion_id) not in ids_test]
    inicio_mes = hoy.replace(day=1)

    serie: list[dict] = []
    primero = inicio_mes
    for _ in range(max(1, int(meses)) - 1):
        primero = _mes_anterior(primero)

    cursor = primero
    while cursor.year < hoy.year or (cursor.year == hoy.year and cursor.month <= hoy.month):
        fin_mes = _mes_siguiente(cursor) - timedelta(days=1)
        apertura_dia = cursor - timedelta(days=1)
        # El mes en curso se mide hasta hoy: contar licencias que vencen el día
        # 30 como si ya estuvieran cobradas sería vender humo.
        cierre_dia = min(fin_mes, hoy)
        apertura = _mrr_por_organizacion(licencias, apertura_dia)
        cierre = _mrr_por_organizacion(licencias, cierre_dia)
        piezas = _descomponer(apertura, cierre)
        mrr_inicio = round(sum(apertura.values()), 2)
        mrr_cierre = round(sum(cierre.values()), 2)
        serie.append({
            "clave": f"{cursor.year}-{cursor.month:02d}",
            "etiqueta": f"{_MESES[cursor.month]} {cursor.year}",
            "corto": _MESES[cursor.month],
            "desde": cursor,
            "hasta": cierre_dia,
            "en_curso": cursor == inicio_mes,
            "inicio": mrr_inicio,
            "cierre": mrr_cierre,
            **piezas,
            "variacion": (
                round((mrr_cierre - mrr_inicio) / mrr_inicio * 100, 1)
                if mrr_inicio > 0
                else None
            ),
            "cuadra": round(mrr_inicio + piezas["neto"] - mrr_cierre, 2) == 0,
        })
        cursor = _mes_siguiente(cursor)

    actual = serie[-1]
    return {
        "hoy": hoy,
        "mes": actual,
        "serie": serie,
        "cuadra": all(mes["cuadra"] for mes in serie),
        "maximo": max([m["cierre"] for m in serie] + [0.0]),
        "chart": _geometria_mrr(serie),
    }


def _geometria_mrr(serie: list[dict], *, ancho: int = 300, alto: int = 90) -> dict:
    """Coordenadas de las barras de la serie, listas para un SVG.

    Se calcula aquí y no en la plantilla porque la plantilla no puede hacer
    aritmética con estilos (la CSP prohíbe `style=`), y porque así el gráfico
    se puede probar sin abrir un navegador.
    """
    if not serie:
        return {"ancho": ancho, "alto": alto, "base": alto, "puntos": [], "maximo": 0.0}
    maximo = max((mes["cierre"] for mes in serie), default=0.0) or 0.0
    hueco = 6
    ancho_barra = max(4.0, (ancho - hueco * (len(serie) - 1)) / len(serie))
    puntos = []
    for indice, mes in enumerate(serie):
        alto_barra = (mes["cierre"] / maximo * (alto - 8)) if maximo else 0.0
        puntos.append({
            "clave": mes["clave"],
            "x": round(indice * (ancho_barra + hueco), 2),
            "y": round(alto - alto_barra, 2),
            "ancho": round(ancho_barra, 2),
            "alto": round(alto_barra, 2),
            "etiqueta": mes["corto"],
            "cierre": mes["cierre"],
            "neto": mes["neto"],
            "positivo": mes["neto"] >= 0,
            "en_curso": mes["en_curso"],
        })
    return {"ancho": ancho, "alto": alto, "base": alto, "puntos": puntos, "maximo": round(maximo, 2)}
