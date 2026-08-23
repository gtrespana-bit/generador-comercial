"""Gestión de planos y mediciones manuales sobre planos.

El flujo es:
1. Usuario sube imagen (PNG/JPG/WEBP) o PDF (se convierte a primera página como imagen)
2. Se guarda en storage privado organizaciones/{org}/planos/{presupuesto}/{id}.ext
3. Usuario calibra escala: dibuja línea de N px que corresponde a X metros
4. Mide líneas, áreas, conteos. Cada medición se guarda con puntos en px y valor real.

No hay IA: es medición asistida manual, sin coste por uso.
"""

from __future__ import annotations

import io
import json
import math
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..models import PlanoMedicion, PlanoObra

EXT_PLANOS_IMG = {".png", ".jpg", ".jpeg", ".webp"}
EXT_PLANOS_PDF = {".pdf"}
MAX_PLANO_BYTES = 12 * 1024 * 1024
MAX_PLANOS_POR_PRESUPUESTO = 20
MAX_MEDICIONES_POR_PLANO = 500

class ErrorPlano(ValueError):
    pass


def _validar_archivo(nombre: str, contenido: bytes) -> tuple[str, str]:
    """Valida extensión y contenido, devuelve (ext, content_type)"""
    if not contenido or len(contenido) > MAX_PLANO_BYTES:
        raise ErrorPlano("El plano supera 12 MB o está vacío.")
    ext = Path(nombre or "").suffix.lower()
    if ext not in EXT_PLANOS_IMG and ext not in EXT_PLANOS_PDF:
        raise ErrorPlano("Formato no soportado. Usa PNG, JPG, WEBP o PDF.")
    if ext in EXT_PLANOS_PDF:
        if not contenido.startswith(b"%PDF-"):
            raise ErrorPlano("El PDF no es válido.")
        return ext, "application/pdf"
    # Imagen
    try:
        from PIL import Image
        with Image.open(io.BytesIO(contenido)) as im:
            w, h = im.size
            if w <= 0 or h <= 0 or w * h > 40_000_000:
                raise ErrorPlano("Imagen demasiado grande o corrupta.")
            im.verify()
            fmt = (im.format or "").upper()
    except ErrorPlano:
        raise
    except Exception:
        raise ErrorPlano("No se pudo leer la imagen. Usa PNG/JPG válido.")
    mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(fmt, "image/png")
    return ext, mime


def _pdf_a_imagen(contenido_pdf: bytes) -> tuple[bytes, int, int]:
    """
    Convierte primera página de PDF a PNG usando PyMuPDF si está disponible,
    si no, devuelve el PDF tal cual y dimensiones None (el frontend usará pdf.js).
    Para MVP, si no hay librería, guardamos PDF y el frontend lo renderiza.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=contenido_pdf, filetype="pdf")
        if len(doc) == 0:
            raise ErrorPlano("PDF vacío.")
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x para calidad
        img_bytes = pix.tobytes("png")
        w, h = pix.width, pix.height
        doc.close()
        return img_bytes, w, h
    except ImportError:
        # Sin PyMuPDF, devolver PDF y dejar que frontend use pdf.js
        return contenido_pdf, 0, 0
    except ErrorPlano:
        raise
    except Exception as e:
        # Fallback: guardar PDF
        return contenido_pdf, 0, 0


def _distancia_px(puntos: list[list[float]]) -> float:
    """Suma distancia euclídea entre puntos consecutivos"""
    if len(puntos) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(puntos)):
        x0, y0 = puntos[i-1]
        x1, y1 = puntos[i]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _area_px(puntos: list[list[float]]) -> float:
    """Área polígono por Shoelace, en px²"""
    if len(puntos) < 3:
        return 0.0
    s = 0.0
    n = len(puntos)
    for i in range(n):
        x0, y0 = puntos[i]
        x1, y1 = puntos[(i+1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def calcular_valor_real(tipo: str, puntos: list[list[float]], escala_px_por_m: float | None) -> tuple[float, str]:
    """
    Calcula valor real a partir de puntos y escala.
    Devuelve (valor, unidad)
    """
    if not escala_px_por_m or escala_px_por_m <= 0:
        # Sin calibrar, devolver valor en px
        if tipo == "lineal":
            return _distancia_px(puntos), "px"
        elif tipo in ("area",):
            return _area_px(puntos), "px2"
        elif tipo == "perimetro":
            return _distancia_px(puntos), "px"
        elif tipo == "conteo":
            return float(len(puntos)), "ud"
        else:
            return 0.0, "px"

    # Con escala: 1 m = escala_px_por_m px
    factor = 1.0 / escala_px_por_m  # m por px
    if tipo == "lineal":
        px = _distancia_px(puntos)
        return px * factor, "m"
    elif tipo == "area":
        px2 = _area_px(puntos)
        return px2 * (factor ** 2), "m2"
    elif tipo == "perimetro":
        px = _distancia_px(puntos)
        # Si polígono cerrado, añadir cierre
        if len(puntos) >= 3:
            x0, y0 = puntos[0]
            x1, y1 = puntos[-1]
            if math.hypot(x1-x0, y1-y0) > 1e-6:
                px += math.hypot(x1-x0, y1-y0)
        return px * factor, "m"
    elif tipo == "conteo":
        return float(len(puntos)), "ud"
    elif tipo == "volumen":
        # Volumen no directo, por ahora área * altura? devolver área
        px2 = _area_px(puntos)
        return px2 * (factor ** 2), "m2"
    return 0.0, "m"


def crear_plano(
    db: Session,
    presupuesto_id: int,
    nombre: str,
    archivo_nombre: str,
    contenido: bytes,
) -> PlanoObra:
    from ..storage import save_object

    # Contar planos existentes
    existentes = db.query(PlanoObra).filter(PlanoObra.presupuesto_id == presupuesto_id).count()
    if existentes >= MAX_PLANOS_POR_PRESUPUESTO:
        raise ErrorPlano(f"Máximo {MAX_PLANOS_POR_PRESUPUESTO} planos por presupuesto.")

    ext, mime = _validar_archivo(archivo_nombre, contenido)

    # Si PDF, intentar convertir a imagen
    ancho = alto = None
    contenido_guardar = contenido
    content_type_guardar = mime
    if ext == ".pdf":
        img_bytes, w, h = _pdf_a_imagen(contenido)
        if w and h:
            contenido_guardar = img_bytes
            content_type_guardar = "image/png"
            ancho, alto = w, h
            ext = ".png"
        else:
            # Guardar PDF tal cual, frontend lo renderizará
            ancho = alto = None

    if ext in EXT_PLANOS_IMG and (ancho is None or alto is None):
        try:
            from PIL import Image
            with Image.open(io.BytesIO(contenido_guardar)) as im:
                ancho, alto = im.size
        except Exception:
            ancho = alto = None

    plano = PlanoObra(
        presupuesto_id=presupuesto_id,
        nombre=(nombre or Path(archivo_nombre).stem)[:250] or "Plano",
        archivo="",  # se rellena tras save_object
        content_type=content_type_guardar,
        ancho_px=ancho,
        alto_px=alto,
    )
    db.add(plano)
    db.flush()  # para tener id

    # Guardar archivo
    try:
        guardado = save_object(
            db,
            contenido_guardar,
            "planos",
            f"{plano.id}{ext}",
            content_type_guardar,
            prefix=f"presupuesto-{presupuesto_id}/plano-{plano.id}",
        )
        plano.archivo = guardado.reference
    except Exception as exc:
        db.rollback()
        raise ErrorPlano(f"No se pudo guardar el plano: {exc}") from exc

    db.commit()
    return plano


def calibrar_plano(
    db: Session,
    plano: PlanoObra,
    distancia_px: float,
    distancia_real: float,
    unidad: str = "m",
) -> PlanoObra:
    if distancia_px <= 0 or distancia_real <= 0:
        raise ErrorPlano("Distancias de calibración deben ser positivas.")
    if distancia_px > 10000 or distancia_real > 10000:
        raise ErrorPlano("Calibración fuera de rango.")

    unidad = (unidad or "m").strip().lower()
    # Convertir a metros
    factor_unidad = {"m": 1.0, "cm": 0.01, "mm": 0.001, "km": 1000.0}.get(unidad, 1.0)
    distancia_real_m = distancia_real * factor_unidad

    escala = distancia_px / distancia_real_m  # px por metro

    plano.escala_px_por_metro = escala
    plano.calibracion_px = distancia_px
    plano.calibracion_real = distancia_real_m
    plano.unidad_calibracion = unidad

    # Recalcular mediciones existentes
    for med in plano.mediciones:
        pts = med.puntos()
        valor, uni = calcular_valor_real(med.tipo, pts, escala)
        med.valor = valor
        med.unidad = uni

    db.commit()
    return plano


def crear_medicion(
    db: Session,
    plano: PlanoObra,
    tipo: str,
    etiqueta: str,
    puntos: list[list[float]],
    color: str = "#ff0000",
    partida_destino_id: int | None = None,
) -> PlanoMedicion:
    tipo = (tipo or "lineal").strip().lower()
    if tipo not in ("lineal", "area", "perimetro", "conteo", "volumen"):
        raise ErrorPlano("Tipo de medición no válido.")

    if len(puntos) == 0:
        raise ErrorPlano("La medición debe tener puntos.")

    if len(puntos) > 100:
        raise ErrorPlano("Demasiados puntos (máx 100).")

    existentes = db.query(PlanoMedicion).filter(PlanoMedicion.plano_id == plano.id).count()
    if existentes >= MAX_MEDICIONES_POR_PLANO:
        raise ErrorPlano(f"Máximo {MAX_MEDICIONES_POR_PLANO} mediciones por plano.")

    # Validar puntos
    puntos_limpios = []
    for p in puntos:
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            continue
        try:
            x = float(p[0]); y = float(p[1])
            if not (math.isfinite(x) and math.isfinite(y)):
                continue
            puntos_limpios.append([x, y])
        except (TypeError, ValueError):
            continue

    if not puntos_limpios:
        raise ErrorPlano("Puntos no válidos.")

    valor, unidad = calcular_valor_real(tipo, puntos_limpios, plano.escala_px_por_metro)

    med = PlanoMedicion(
        plano_id=plano.id,
        presupuesto_id=plano.presupuesto_id,
        tipo=tipo,
        etiqueta=(etiqueta or "")[:250],
        valor=valor,
        unidad=unidad,
        puntos_json=json.dumps(puntos_limpios, ensure_ascii=False),
        partida_destino_id=partida_destino_id,
        color=color[:20] if color else "#ff0000",
    )
    db.add(med)
    db.commit()
    return med


def eliminar_plano(db: Session, plano: PlanoObra):
    from ..storage import delete_object
    ref = plano.archivo
    db.delete(plano)
    db.flush()
    if ref:
        try:
            delete_object(db, ref)
        except Exception:
            pass
    db.commit()


def eliminar_medicion(db: Session, medicion: PlanoMedicion):
    db.delete(medicion)
    db.commit()


def aplicar_medicion_a_partida(
    db: Session,
    medicion: PlanoMedicion,
    partida_id: int,
) -> dict:
    """Crea una Medicion (del presupuesto) a partir de una PlanoMedicion."""
    from ..models import Medicion, PresupuestoItem

    partida = db.query(PresupuestoItem).filter(PresupuestoItem.id == partida_id).first()
    if not partida:
        raise ErrorPlano("Partida destino no encontrada.")

    # Verificar que partida pertenece al mismo presupuesto que el plano
    if partida.capitulo and partida.capitulo.presupuesto_id != medicion.presupuesto_id:
        raise ErrorPlano("La partida no pertenece al mismo presupuesto que el plano.")

    # Crear medición de presupuesto
    # Si es conteo, valor es uds; si lineal, m; si área, m2
    concepto = medicion.etiqueta or f"Plano {medicion.plano.nombre} - {medicion.tipo}"
    # Si ya hay mediciones, añadir, si no, cantidad directa se reemplaza por suma
    from sqlalchemy import func
    max_orden = db.query(func.max(Medicion.orden)).filter(Medicion.partida_id == partida.id).scalar() or 0
    nueva = Medicion(
        partida_id=partida.id,
        concepto=concepto[:250],
        cantidad=float(medicion.valor or 0),
        orden=max_orden + 1,
    )
    db.add(nueva)
    # Vincular
    medicion.partida_destino_id = partida.id
    db.commit()
    return {"ok": True, "medicion_id": nueva.id, "cantidad": nueva.cantidad}
