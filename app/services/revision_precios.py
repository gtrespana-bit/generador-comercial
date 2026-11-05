"""¿Puede esta empresa cotizar con sus precios, o está usando los de otro?

El generador de precios no inventa nada: compone el importe con las tarifas de
recursos de la empresa (mano de obra, materiales, equipos). Una empresa que
paga 15 US$/h por un oficial y otra que paga 25 US$/h **deben** obtener
presupuestos distintos con las mismas mediciones. Eso es el producto
funcionando.

El fallo caro es el de al lado: una cuenta recién creada cotiza con las
referencias que venían de fábrica —que pueden ser de otro país, de otro
convenio o de hace meses— y nada se lo dice. El presupuesto sale, parece
correcto y el margen se lo come el cliente.

Este servicio responde a tres preguntas y no escribe nada:

``resumen_revision``
    Cuántas tarifas hay, cuántas son «mías» (precio propio de la empresa) y
    cuántas siguen siendo referencias por confirmar. Distingue la mano de obra
    del resto porque es la que más mueve el importe y la que cada empresa
    negocia distinto.
``tarifas_a_revisar``
    Las filas que el operador de la empresa debe mirar, ordenadas como se
    revisan de verdad: primero lo que más pesa en el presupuesto (usos), luego
    la mano de obra, luego lo que nunca se tocó.
``aviso_presupuesto``
    Qué parte de un presupuesto concreto está cotizada con tarifas sin
    confirmar, para poder decirlo **donde se toma la decisión** (el editor) y
    no solo en una pantalla de ajustes que nadie abre.

Solo lee: la escritura de «confirmado» la hacen los endpoints de recursos.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func, or_

from ..models import PrecioRecursoMercado, Recurso

#: Una tarifa confirmada caduca como dato: seis meses después del «sí, es la
#: mía» se vuelve a preguntar. Es el mismo criterio con el que se revisan las
#: referencias de mercado, pero medido desde la confirmación de la empresa.
DIAS_VIGENCIA_REVISION = 180

#: Categoría que más mueve el importe y más varía entre empresas.
CATEGORIA_CLAVE = "mano_obra"


def _limite(hoy: date | None = None) -> datetime:
    return datetime.combine(
        (hoy or date.today()) - timedelta(days=DIAS_VIGENCIA_REVISION),
        datetime.min.time(),
    )


def revisada(recurso, hoy: date | None = None) -> bool:
    """¿La empresa dio esta tarifa por buena hace menos de seis meses?"""
    from .configuracion_tolerante import atributo

    marca = atributo(recurso, "precio_revisado_at")
    if marca is None:
        return False
    try:
        return marca >= _limite(hoy)
    except TypeError:  # marca sin hora (algunos backends devuelven date)
        return marca >= _limite(hoy).date()


def _con_precio_propio(db, organizacion_id: int, pais: str) -> set[int]:
    """Recursos con precio fijado por esta empresa (su override de mercado).

    Es la señal más fuerte que existe: alguien escribió el número. No hace
    falta que además pulse «confirmar», así que cuenta como revisado.
    """
    if not organizacion_id:
        return set()
    filas = (
        db.query(PrecioRecursoMercado.recurso_id, PrecioRecursoMercado.codigo_recurso)
        .filter(
            PrecioRecursoMercado.organizacion_id == organizacion_id,
            PrecioRecursoMercado.activo.is_(True),
            or_(
                PrecioRecursoMercado.pais_codigo == pais,
                PrecioRecursoMercado.pais_codigo.is_(None),
            ),
        )
        .all()
    )
    ids = {int(recurso_id) for recurso_id, _codigo in filas if recurso_id}
    codigos = {str(codigo).strip() for _id, codigo in filas if (codigo or "").strip()}
    if codigos:
        # La referencia propia puede haber llegado por código estable (misma
        # tarifa en varias copias del catálogo).
        for (recurso_id,) in (
            db.query(Recurso.id)
            .filter(Recurso.codigo.in_(codigos))
            .all()
        ):
            ids.add(int(recurso_id))
    return ids


def _consulta_recursos(db):
    """``db.query(Recurso)`` sin las columnas que la base aún no tiene.

    Si el despliegue llegó antes que la migración, ``SELECT recursos.*`` falla
    entero por ``precio_revisado_at``; esto deja leer el catálogo igual y el
    resumen cuenta esas tarifas como «sin confirmar», que es la verdad.
    """
    from .configuracion_tolerante import consulta

    return consulta(db, Recurso)


def resumen_revision(db, *, organizacion_id: int, pais: str, hoy: date | None = None) -> dict:
    """Fotografía de las tarifas: cuántas son propias y cuántas están por ver.

    No lanza si algo falla a medias: quien pinta la tarjeta del panel prefiere
    un «no lo sé» a un 500. La comprobación de la columna nueva se hace por
    ``getattr`` para sobrevivir a un despliegue sin migración.
    """
    pais = str(pais or "").strip().upper()
    propios = _con_precio_propio(db, organizacion_id, pais)
    try:
        recursos = (
            db.query(
                Recurso.id,
                Recurso.descripcion,
                Recurso.codigo,
                Recurso.unidad,
                Recurso.categoria,
                Recurso.usos,
                Recurso.precio_revisado_at,
            )
            .order_by(Recurso.categoria, Recurso.descripcion)
            .all()
        )
    except Exception:
        # Columna sin migrar: se degrada a «sin revisión registrada» en vez de
        # romper la pantalla que pide revisar.
        try:
            db.rollback()
        except Exception:
            pass
        recursos = [
            (r.id, r.descripcion, r.codigo, r.unidad, r.categoria, r.usos, None)
            for r in _consulta_recursos(db).all()
        ]

    total = len(recursos)
    por_categoria: dict[str, dict] = {}
    pendientes: list[dict] = []
    confirmadas = 0
    for recurso_id, descripcion, codigo, unidad, categoria, usos, marca in recursos:
        categoria = categoria or "otros"
        fila = por_categoria.setdefault(
            categoria, {"categoria": categoria, "total": 0, "pendientes": 0, "con_precio_propio": 0}
        )
        fila["total"] += 1
        es_propia = recurso_id in propios
        if es_propia:
            fila["con_precio_propio"] += 1
        if es_propia or _marca_vigente(marca, hoy):
            confirmadas += 1
            continue
        fila["pendientes"] += 1
        pendientes.append(
            {
                "id": recurso_id,
                "descripcion": descripcion or "",
                "codigo": codigo or "",
                "unidad": unidad or "",
                "categoria": categoria,
                "usos": int(usos or 0),
                "con_precio_propio": es_propia,
                "revisado_at": marca,
            }
        )

    # Orden de revisión: lo que más se usa primero (es lo que de verdad entra
    # en los presupuestos), después la mano de obra, que es la que cambia de
    # empresa a empresa.
    pendientes.sort(
        key=lambda fila: (
            0 if fila["categoria"] == CATEGORIA_CLAVE else 1,
            -fila["usos"],
            fila["descripcion"].lower(),
        )
    )
    mano_obra = por_categoria.get(CATEGORIA_CLAVE, {})
    return {
        "pais": pais,
        "total": total,
        "confirmadas": confirmadas,
        "pendientes": len(pendientes),
        "porcentaje": round(confirmadas * 100 / total) if total else 100,
        "mano_obra_total": int(mano_obra.get("total", 0)),
        "mano_obra_pendientes": int(mano_obra.get("pendientes", 0)),
        "por_categoria": sorted(
            por_categoria.values(),
            key=lambda fila: (-fila["pendientes"], fila["categoria"]),
        ),
        "filas": pendientes,
        "dias_vigencia": DIAS_VIGENCIA_REVISION,
        # El aviso solo tiene sentido si hay algo que revisar y hay tarifas:
        # una empresa sin catálogo tiene otro problema, no este.
        "requiere_atencion": bool(total and pendientes),
        "hoy": hoy or date.today(),
    }


def _marca_vigente(marca, hoy: date | None) -> bool:
    if marca is None:
        return False
    try:
        return marca >= _limite(hoy)
    except TypeError:
        try:
            return marca >= _limite(hoy).date()
        except TypeError:
            return False


def tarifas_a_revisar(db, *, organizacion_id: int, pais: str, hoy: date | None = None) -> list[dict]:
    """Solo las filas pendientes, ya ordenadas para revisarlas en lote."""
    return resumen_revision(
        db, organizacion_id=organizacion_id, pais=pais, hoy=hoy
    )["filas"]


def aviso_presupuesto(
    db,
    presupuesto,
    *,
    organizacion_id: int,
    pais: str,
    hoy: date | None = None,
    limite: int = 3,
) -> dict | None:
    """Qué parte de ESTE presupuesto está cotizada con tarifas sin confirmar.

    Se calcula sobre los recursos que de verdad usa el documento (líneas del
    APU), no sobre el catálogo entero: decirle a alguien «tienes 300 tarifas
    sin revisar» mientras cotiza una reforma de baño no le sirve de nada. Si
    no hay ninguna, devuelve ``None`` y el editor no enseña nada.
    """
    try:
        usados = _recursos_del_presupuesto(db, presupuesto)
    except Exception:
        return None
    if not usados:
        return None

    propios = _con_precio_propio(db, organizacion_id, pais)
    pendientes: list[dict] = []
    for recurso_id, descripcion, unidad, categoria in usados:
        if recurso_id in propios:
            continue
        marca = _marca_de(db, recurso_id)
        if _marca_vigente(marca, hoy):
            continue
        pendientes.append(
            {
                "descripcion": descripcion or "",
                "unidad": unidad or "",
                "categoria": categoria or "otros",
                "es_mano_obra": (categoria or "") == CATEGORIA_CLAVE,
            }
        )
    if not pendientes:
        return None
    pendientes.sort(key=lambda fila: (0 if fila["es_mano_obra"] else 1, fila["descripcion"].lower()))
    return {
        "total": len(pendientes),
        "mano_obra": sum(1 for fila in pendientes if fila["es_mano_obra"]),
        "filas": pendientes[: max(int(limite), 1)],
    }


def _recursos_del_presupuesto(db, presupuesto) -> list[tuple]:
    """Recursos que el documento usa de verdad, con su categoría.

    Se leen las dos formas en que un presupuesto guarda su descompuesto:

    - ``PresupuestoItem.descomposicion_json`` (lo que edita el usuario en el
      editor de partidas);
    - ``DescomposicionFila`` (el descompuesto importado de CYPE, que vive en su
      propia tabla).

    Se comparan por código cuando existe y, si no, por descripción+unidad —
    la misma clave de matching que usa el catálogo de recursos— para poder
    resolver la fila del descompuesto contra el recurso de la empresa. Una
    fila sin código se resuelve igual: es la mitad de los catálogos reales.
    """
    import json

    if presupuesto is None:
        return []
    claves: set[str] = set()

    def _anotar(codigo, descripcion, unidad) -> None:
        codigo = str(codigo or "").strip().lower()
        descripcion = str(descripcion or "").strip().lower()
        unidad = str(unidad or "").strip().lower()
        if codigo:
            claves.add(f"cod:{codigo}")
        if descripcion:
            claves.add(f"desc:{descripcion}|{unidad}")

    items = []
    for parte in getattr(presupuesto, "capitulos", None) or []:
        items.extend(list(getattr(parte, "partidas", None) or []))
    for partida in items:
        try:
            crudo = json.loads(getattr(partida, "descomposicion_json", "") or "[]")
        except (TypeError, ValueError):
            crudo = []
        filas = crudo.get("filas", []) if isinstance(crudo, dict) else crudo
        for fila in filas if isinstance(filas, list) else []:
            if isinstance(fila, dict):
                _anotar(fila.get("codigo"), fila.get("descripcion"), fila.get("unidad"))
        # ``uselist=False``: es una sola descomposición (o ninguna), no una lista.
        descompuesto = getattr(partida, "descomposicion_cype", None)
        for fila in getattr(descompuesto, "filas", None) or []:
            _anotar(fila.codigo, fila.descripcion, fila.unidad)
    if not claves:
        return []

    consulta = db.query(
        Recurso.id, Recurso.descripcion, Recurso.unidad, Recurso.categoria, Recurso.codigo
    )
    if hasattr(consulta, "filter") and hasattr(consulta, "all"):
        encontrados = consulta.all()
    else:  # dobles de prueba sin SQL
        encontrados = consulta
    vistos: dict[int, tuple] = {}
    for recurso_id, descripcion, unidad, categoria, codigo in encontrados:
        clave_cod = f"cod:{str(codigo or '').strip().lower()}"
        clave_desc = (
            f"desc:{str(descripcion or '').strip().lower()}|"
            f"{str(unidad or '').strip().lower()}"
        )
        if clave_cod in claves or clave_desc in claves:
            vistos[int(recurso_id)] = (int(recurso_id), descripcion, unidad, categoria)
    return list(vistos.values())


def _marca_de(db, recurso_id: int):
    """``precio_revisado_at`` del recurso, tolerando el despliegue sin migrar."""
    try:
        fila = (
            db.query(Recurso.precio_revisado_at)
            .filter(Recurso.id == recurso_id)
            .first()
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return None
    return fila[0] if fila else None
