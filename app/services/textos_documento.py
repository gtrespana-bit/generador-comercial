"""Textos del documento que pueden ser generales o propios de un presupuesto.

Tres bloques del PDF salen de **Configuración** y son de la empresa, no del
trabajo: los datos bancarios y métodos de pago, la información adicional
(«alcance del trabajo») y las condiciones comerciales. Eso funciona para casi
todo, pero hay presupuestos que no encajan en lo general:

- una obra que se cobra en otra cuenta (un anticipo por transferencia a nombre
  de un socio, una cuenta en otra moneda);
- un cliente extranjero que paga por Zelle o USDT y no por transferencia local;
- unas condiciones distintas porque el cliente es un particular y no una
  constructora, o porque la obra tiene un plazo de garantía pactado aparte.

Hasta ahora la única salida era cambiar los datos de la empresa —afectando a
**todos** los presupuestos— o corregir el PDF a mano.

**El modelo es «heredar o propio», y heredar es el valor por omisión.**

Para los datos bancarios el campo del presupuesto admite tres valores, y la
diferencia entre los dos últimos importa:

- ``None`` → **hereda** los de Configuración. Es lo que tienen todos los
  presupuestos guardados antes de existir esta columna, así que el documento se
  genera exactamente igual que antes.
- ``""`` → este presupuesto **no** muestra datos de pago (obra cobrada por otro
  medio). Sin esto no habría forma de quitar el bloque sin tocar la empresa.
- cualquier texto → datos **propios** de este presupuesto.

Para la información adicional y las condiciones el campo del presupuesto ya era
el documento: lo que se escribe ahí es lo que sale en el PDF, y los textos de
Configuración son el punto de partida de un presupuesto nuevo. El editor los
muestra igual —con su botón para volver a los generales— pero no hay una
segunda copia: el presupuesto manda y punto. Se documenta aquí para que la
regla viva en un solo sitio y no se reinvente tres veces.

**Lo que se congela, se congela.** Las versiones enviadas y los enlaces de
propuesta guardan el texto resuelto (:func:`textos_documento`): si mañana
cambian los datos bancarios de la empresa, una propuesta ya enviada sigue
mostrando la cuenta a la que se comprometió. Por eso los consumidores llaman a
:func:`datos_bancarios_documento` en lugar de leer la configuración por su
cuenta.
"""
from __future__ import annotations

#: Claves de los textos del documento, en el orden en que se editan.
CLAVES_TEXTO = ("datos_bancarios", "notas", "condiciones")

#: Estados en los que el presupuesto ya salió de casa y sus textos no deben
#: cambiar por detrás. Coincide con ``ESTADOS_CONGELABLES`` del router, pero se
#: declara aquí para no importar el router desde un servicio.
ESTADOS_CONGELADOS = ("enviado", "aprobado")


def datos_bancarios_documento(presupuesto, config) -> str:
    """Datos de pago que debe mostrar el documento de ``presupuesto``.

    Regla única para el PDF, la vista previa y las instantáneas de versión. Se
    lee con ``__dict__`` y no con ``getattr`` a propósito: un presupuesto cargado
    por una consulta parcial (o una fila de una base sin migrar) no debe mostrar
    los datos de la empresa como si fueran propios, y un ``getattr`` con omisión
    tampoco distingue «no preguntado» de ``None``.
    """
    if presupuesto is None:
        return str(getattr(config, "datos_bancarios", "") or "").strip()
    propios = presupuesto.__dict__.get("datos_bancarios")
    if propios is None:
        return str(getattr(config, "datos_bancarios", "") or "").strip()
    return str(propios).strip()


def textos_documento(presupuesto, config) -> dict[str, str]:
    """Los tres textos del documento, ya resueltos, para congelar en una versión.

    Se guarda el **resultado** y no la elección: una versión histórica no puede
    depender de una configuración que cambie después.
    """
    return {
        "datos_bancarios": datos_bancarios_documento(presupuesto, config),
        "notas": str(getattr(presupuesto, "notas", "") or "").strip(),
        "condiciones": str(getattr(presupuesto, "condiciones", "") or "").strip(),
    }


def textos_para_formulario(presupuesto, config) -> dict[str, object]:
    """Valores iniciales de los tres campos en el editor.

    ``datos_bancarios`` devuelve el texto **general** cuando el presupuesto
    hereda: el campo se pinta relleno para que se vea lo que va a salir en el
    documento. Así se cumple lo pedido: ver los datos generales y tener la
    opción de mantenerlos o cambiarlos sin adivinar qué hay configurado.
    """
    heredado = presupuesto is not None and presupuesto.__dict__.get("datos_bancarios") is None
    propios = presupuesto.__dict__.get("datos_bancarios") if presupuesto is not None else None
    if heredado or presupuesto is None:
        eleccion = "heredar"
    elif not str(propios or "").strip():
        eleccion = "vacio"
    else:
        eleccion = "propio"
    notas_generales = str(getattr(config, "notas_default", "") or "").strip()
    condiciones_generales = str(getattr(config, "condiciones_default", "") or "").strip()
    if presupuesto is None:
        # Presupuesto nuevo: el editor arranca con los textos de la empresa, que
        # es lo que se venía haciendo. Sigue siendo una copia editable, no una
        # herencia: en cuanto se guarda, el presupuesto tiene los suyos.
        notas = notas_generales
        condiciones = condiciones_generales
    else:
        notas = str(getattr(presupuesto, "notas", "") or "").strip()
        condiciones = str(getattr(presupuesto, "condiciones", "") or "").strip()
    return {
        "datos_bancarios": datos_bancarios_documento(presupuesto, config),
        "notas": notas,
        "condiciones": condiciones,
        # El editor necesita saber si lo que hay en el campo es suyo o prestado:
        # para rotular «usando los datos de Configuración» y para que el botón de
        # volver sepa qué tiene que reponer.
        "datos_bancarios_heredados": heredado,
        # Lo que el editor debe marcar ya al abrir: «heredar», «vacio» o
        # «propio». Se calcula aquí para que la etiqueta del formulario no
        # tenga que adivinar y para que el campo oculto llegue coherente.
        "datos_bancarios_eleccion": eleccion,
        "datos_bancarios_generales": str(getattr(config, "datos_bancarios", "") or "").strip(),
        "notas_generales": notas_generales,
        "condiciones_generales": condiciones_generales,
    }


def datos_bancarios_resumen(presupuesto) -> str:
    """Etiqueta corta del panel plegado del editor («heredados» / «propios»)."""
    if presupuesto is None:
        return "heredados"
    propios = presupuesto.__dict__.get("datos_bancarios")
    if propios is None:
        return "heredados"
    if not str(propios).strip():
        return "sin datos de pago"
    return "propios"


def datos_bancarios_desde_formulario(form, config, *, actual=None) -> str | None:
    """Interpreta el campo del editor y devuelve lo que se guarda.

    El campo llega relleno con los datos generales, así que el texto solo no
    basta para saber qué quiso la persona. Hay tres intenciones que en el
    formulario se parecen:

    1. **Mantener los generales** (el campo no se tocó, o se pulsó «volver a los
       datos de Configuración»): se guarda ``None`` para que el presupuesto siga
       heredando. Copiar el texto congelaría hoy lo que mañana cambie en
       Configuración, que es justo lo que hay que evitar.
    2. **Quitarlos** (el campo se vació a mano): se guarda ``""``.
    3. **Usar unos propios**: se guarda el texto.

    La intención explícita viaja en ``datos_bancarios_eleccion``. Sin ella
    (petición de un cliente antiguo o formulario incompleto) se deduce del
    texto: coincidir con el general significa que no se tocó, y un campo
    **ausente** conserva lo que el presupuesto ya tenía —borrar datos de pago
    tiene que ser una decisión explícita, no el efecto de guardar otra cosa—.
    ``actual`` es el valor que el presupuesto tenía guardado; si el texto es
    igual a lo que él mismo tenía, se devuelve tal cual.
    """
    eleccion = str(form.get("datos_bancarios_eleccion", "") or "").strip().lower()
    texto = str(form.get("datos_bancarios", "") or "").strip()
    general = str(getattr(config, "datos_bancarios", "") or "").strip()

    if eleccion == "heredar":
        return None
    if eleccion == "propio":
        # Un campo vacío con intención de «propio» es un documento sin bloque de
        # pago; es lo que el editor marca como ``vacio``, pero llega aquí si el
        # navegador no ejecutó el JS.
        return texto
    if eleccion == "vacio":
        return ""

    # Sin intención explícita: formulario incompleto, cliente antiguo o una
    # petición que no pasó por el editor. Se deduce del texto.
    if texto and texto == general:
        return None
    if not texto:
        # Ausencia de texto **no** significa «vacíalo»: se conserva lo que el
        # presupuesto ya tenía. Escribir ``""`` aquí borraría los datos de pago
        # de un presupuesto por el simple hecho de guardar otra cosa.
        return None if actual is None else actual
    if actual is not None and str(actual).strip() == texto:
        return actual
    return texto


def presupuesto_congelado(presupuesto) -> bool:
    """¿Los textos ya salieron de casa y no deben cambiar solos?"""
    estado = str(getattr(presupuesto, "estado", "") or "").lower()
    if estado in ESTADOS_CONGELADOS:
        return True
    versiones = getattr(presupuesto, "versiones", None)
    return bool(versiones)
