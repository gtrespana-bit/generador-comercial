"""Vigencia de los precios de referencia: ¿cuándo hay que volver a mirarlos?

Por qué existe
--------------
La tabla de precios ya guardaba ``fecha_consulta`` y ``fecha_vigencia``, y la
vista de precios por mercado las imprimía. Pero una fecha impresa no es una
señal: nadie mira 388 filas comparándolas con la de hoy. Lo que falta es la
conclusión, no el dato.

Un precio de materiales de construcción no caduca como un yogur, pero sí se
desfas: en el Reino Unido los índices de materiales se mueven todos los meses y
las tarifas de mano de obra se revisan una vez al año con los acuerdos del
sector. Un presupuesto hecho con precios de hace catorce meses no falla de
forma evidente: falla por debajo, en el margen, y se descubre cuando la obra
está empezada.

Umbrales
--------
* **≤ 180 días** — vigente. Revisión trimestral, la cadencia habitual de una
  biblioteca de precios.
* **181–365 días** — por revisar. Sigue sirviendo, pero conviene comprobarlo.
* **> 365 días** — obsoleto. Ha pasado por lo menos un ciclo entero de tarifas.

Una referencia marcada como ``provisional`` no está confirmada, así que se le
da la mitad de plazo: 90 y 180 días.

Además está **caducado**, que es distinto de obsoleto y es más grave: el propio
proveedor puso una fecha de vigencia y esa fecha ya pasó. Ahí no hay criterio
que valga, lo que se guardó dejó de ser válido por sus propios términos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: Días hasta que una referencia pasa a «por revisar» y a «obsoleta».
DIAS_POR_REVISAR = 180
DIAS_OBSOLETA = 365

#: La mitad para lo que nunca se confirmó.
DIAS_POR_REVISAR_PROVISIONAL = 90
DIAS_OBSOLETA_PROVISIONAL = 180

VIGENTE = "vigente"
POR_REVISAR = "por_revisar"
OBSOLETA = "obsoleta"
CADUCADA = "caducada"
SIN_FECHA = "sin_fecha"

_ETIQUETAS = {
    VIGENTE: "Vigente",
    POR_REVISAR: "Por revisar",
    OBSOLETA: "Obsoleto",
    CADUCADA: "Caducado",
    SIN_FECHA: "Sin fecha",
}

_ETIQUETAS_EN = {
    VIGENTE: "Current",
    POR_REVISAR: "Due for review",
    OBSOLETA: "Out of date",
    CADUCADA: "Expired",
    SIN_FECHA: "Undated",
}


@dataclass(frozen=True)
class Vigencia:
    """Conclusión sobre un precio: cuánto tiene y qué hacer con él."""

    estado: str
    #: Días desde que se consultó, o ``None`` si no hay fecha que contar.
    dias: int | None = None
    fecha_consulta: date | None = None
    #: Fecha hasta la que el proveedor garantizaba el precio.
    fecha_vigencia: date | None = None

    @property
    def requiere_revision(self) -> bool:
        """¿Hay que volver a comprobarlo?"""
        return self.estado in (POR_REVISAR, OBSOLETA, CADUCADA, SIN_FECHA)

    @property
    def presentable(self) -> bool:
        """¿Se puede usar en un presupuesto sin sonrojo?

        «Obsoleto» sigue siendo presentable —es lo que hay y se avisa—; lo
        caducado no, porque el propio proveedor dejó de sostenerlo.
        """
        return self.estado != CADUCADA

    def etiqueta(self, idioma: str = "es") -> str:
        tabla = _ETIQUETAS_EN if str(idioma or "").startswith("en") else _ETIQUETAS
        return tabla.get(self.estado, self.estado)


def evaluar_vigencia(
    fecha_consulta: date | None = None,
    fecha_vigencia: date | None = None,
    confianza: str | None = None,
    hoy: date | None = None,
) -> Vigencia:
    """Clasifica un precio de referencia según su antigüedad.

    Se mira primero la fecha de vigencia: si el proveedor dijo «hasta tal día»
    y ese día ya pasó, el precio está caducado y da igual lo reciente que sea la
    consulta. Si no hay vigencia o aún no ha vencido, manda la antigüedad de la
    consulta.

    Sin ninguna de las dos fechas no se inventa nada: se devuelve «sin fecha»,
    que cuenta como pendiente de revisión. Un precio sin datar no es un precio
    vigente, es un precio del que no se sabe.
    """
    hoy = hoy or date.today()
    consulta = _como_fecha(fecha_consulta)
    vigencia = _como_fecha(fecha_vigencia)

    if vigencia is not None and vigencia < hoy:
        return Vigencia(
            estado=CADUCADA,
            dias=(hoy - consulta).days if consulta else None,
            fecha_consulta=consulta,
            fecha_vigencia=vigencia,
        )

    if consulta is None:
        return Vigencia(
            estado=SIN_FECHA,
            dias=None,
            fecha_consulta=None,
            fecha_vigencia=vigencia,
        )

    dias = (hoy - consulta).days
    if dias < 0:
        # Fecha futura: dato mal cargado. Se trata como recién consultado en
        # lugar de romper, pero no se premia: cuenta como vigente sin más.
        dias = 0

    provisional = str(confianza or "").strip().lower() == "provisional"
    limite_revisar = DIAS_POR_REVISAR_PROVISIONAL if provisional else DIAS_POR_REVISAR
    limite_obsoleta = DIAS_OBSOLETA_PROVISIONAL if provisional else DIAS_OBSOLETA

    if dias > limite_obsoleta:
        estado = OBSOLETA
    elif dias > limite_revisar:
        estado = POR_REVISAR
    else:
        estado = VIGENTE

    return Vigencia(
        estado=estado,
        dias=dias,
        fecha_consulta=consulta,
        fecha_vigencia=vigencia,
    )


def _como_fecha(valor) -> date | None:
    """Acepta ``date``, ``datetime`` o ISO ``AAAA-MM-DD``; cualquier otra cosa
    es ``None``."""
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    texto = texto.split("T")[0].split(" ")[0]
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None
