"""Capa interactiva del PDF: elegir producto y ver el precio recalculado.

Cuando una partida ofrece varios productos a elegir, el PDF deja de ser una
hoja muerta: el cliente marca la alternativa que prefiere y el precio
unitario, el importe de la partida, el subtotal del capítulo y los totales
del documento se recalculan **dentro del propio PDF**.

Cómo funciona
-------------
El documento se genera con un formulario AcroForm:

  · Cada opción de producto es un *radio button* del grupo ``sel_<pid>``.
  · Los importes que dependen de esa elección (precio unitario, importe de
    la partida y de cada medición, subtotal del capítulo, base, IVA, total…)
    son campos de texto de **solo lectura** con una acción de cálculo
    (``/AA /C``) en JavaScript.
  · Un script a nivel de documento (``/Names /JavaScript``) publica la tabla
    de datos del presupuesto y las funciones de redondeo y formato, de modo
    que las acciones de cada campo sean expresiones de una línea.
  · El array ``/CO`` fija el orden de cálculo: primero los precios
    unitarios, luego los importes, después los capítulos y por último los
    totales; así una sola pulsación propaga el cambio hasta el total.

Compatibilidad
--------------
El valor inicial de cada campo es exactamente el mismo texto que se
imprimiría en un PDF estático, así que un visor sin soporte de JavaScript
(o el propio papel) muestra el presupuesto correcto con el producto elegido
por defecto. La interactividad es un extra que aparece en Adobe Acrobat
Reader y demás visores con formularios.

Los redondeos replican `services.calculations.money` (ROUND_HALF_UP a dos
decimales) para que el PDF interactivo, la web y el CSV nunca discrepen en
un céntimo.
"""
import json

from reportlab.platypus import Flowable
from reportlab.pdfbase.pdfdoc import PDFArray, PDFDictionary, PDFName, PDFString
from reportlab.pdfbase.acroform import PDFFromString

# Los formularios PDF solo admiten las 14 fuentes estándar, así que los
# campos calculados usan Helvetica en lugar de Lato. Al mismo cuerpo la
# diferencia es prácticamente imperceptible dentro de la tabla.
FUENTE_CAMPO = "Helvetica-Bold"

# Alineaciones de /Q en el diccionario del widget.
_Q = {"left": 0, "center": 1, "right": 2}


# ---------------------------------------------------------------------------
# Flowables
# ---------------------------------------------------------------------------

class CampoCalculado(Flowable):
    """Campo de texto de solo lectura cuyo valor lo calcula el propio PDF.

    Se comporta como un `Paragraph` a efectos de maquetación (ocupa un
    rectángulo fijo dentro de la celda), pero al abrirse en un visor con
    formularios su contenido se recalcula al vuelo.
    """

    def __init__(self, ctx, nombre, valor, js, ancho, alto=11.5,
                 alineacion="center", tam=9, fuente=FUENTE_CAMPO):
        Flowable.__init__(self)
        self.ctx = ctx
        self.nombre = nombre
        self.valor = valor
        self.js = js
        self.width = ancho
        self.height = alto
        self.alineacion = alineacion
        self.tam = tam
        self.fuente = fuente
        self.hAlign = "LEFT"

    def wrap(self, ancho_disp, alto_disp):
        return (self.width, self.height)

    def draw(self):
        canv = self.canv
        form = canv.acroForm
        form.textfield(
            name=self.nombre,
            value=self.valor,
            x=0, y=0,
            width=self.width, height=self.height,
            relative=True,
            borderWidth=0,
            forceBorder=False,
            fontName=self.fuente,
            fontSize=self.tam,
            fieldFlags="readOnly",
            annotationFlags="print",
            maxlen=0,
            fillColor=None,
            borderColor=None,
            textColor=self.ctx.color_texto,
        )
        referencia = form.fields[-1]
        widget = canv._doc.idToObject[referencia.name]
        widget.dict["Q"] = _Q.get(self.alineacion, 1)
        if self.js:
            widget.dict["AA"] = PDFDictionary({
                "C": PDFDictionary({"S": PDFName("JavaScript"), "JS": PDFString(self.js)})
            })
            # El orden de /CO es el orden de cálculo: se respeta el orden en
            # que se registraron los campos en el contexto.
            self.ctx.registrar_orden_calculo(self.nombre, referencia)


class OpcionRadio(Flowable):
    """Casilla redonda para elegir uno de los productos de una partida."""

    def __init__(self, ctx, grupo, valor, marcado, tam=9, tooltip=""):
        Flowable.__init__(self)
        self.ctx = ctx
        self.grupo = grupo
        self.valor = valor
        self.marcado = marcado
        self.width = tam
        self.height = tam
        self.tooltip = tooltip
        self.hAlign = "LEFT"

    def wrap(self, ancho_disp, alto_disp):
        return (self.width, self.height)

    def draw(self):
        self.canv.acroForm.radio(
            name=self.grupo,
            value=self.valor,
            selected=self.marcado,
            x=0, y=0,
            size=self.width,
            relative=True,
            buttonStyle="circle",
            shape="circle",
            borderWidth=0.9,
            borderColor=self.ctx.color_acento,
            fillColor=None,
            textColor=self.ctx.color_acento,
            annotationFlags="print",
            fieldFlags="radio noToggleToOff",
            tooltip=self.tooltip or "Elegir este producto",
        )


def _js_escapar(texto):
    return str(texto).replace("\\", "\\\\").replace('"', '\\"')


def _widget_de_referencia(canv, referencia):
    """Resuelve el diccionario del widget a partir de la referencia AcroForm."""
    nombre = getattr(referencia, "name", None)
    doc = getattr(canv, "_doc", None)
    if not nombre or doc is None:
        return None
    tabla = getattr(doc, "idToObject", None)
    if isinstance(tabla, dict):
        return tabla.get(nombre)
    return None


def _registrar_campo(form, widget):
    """Añade el widget al /Fields del formulario, si ReportLab lo permite."""
    try:
        if hasattr(form, "getRef"):
            form.fields.append(form.getRef(widget))
        else:
            form.fields.append(form.canv._doc.Reference(widget))
    except Exception:
        pass


def _anadir_boton_hit_nativo(canv, form, nombre, tooltip, ancho, alto, js):
    """Push-button transparente sin usar AcroForm.button (ReportLab < 4.2).

    ReportLab 4.0/4.1 ya tiene textfield/radio, pero no el método `button`.
    El widget se construye a mano: FT=Btn + Ff=pushButton, sin borde ni
    relleno, con una acción /AA /U que marca el radio de la opción.
    """
    try:
        x, y = canv.absolutePosition(0, 0)
    except Exception:
        x, y = 0.0, 0.0
    doc = canv._doc
    try:
        pagina = doc.thisPageRef()
    except Exception:
        pagina = None
    datos = {
        "FT": PDFName("Btn"),
        "Rect": PDFArray([x, y, x + ancho, y + alto]),
        "Subtype": PDFName("Widget"),
        "Type": PDFName("Annot"),
        "F": 4,            # Print
        "Ff": 1 << 16,     # pushButton
        "T": PDFString(nombre),
        "H": PDFName("N"),
        "MK": PDFDictionary({"BC": PDFArray([]), "BG": PDFArray([])}),
        "AA": PDFDictionary({
            "U": PDFDictionary({
                "S": PDFName("JavaScript"),
                "JS": PDFString(js),
            })
        }),
    }
    if pagina is not None:
        datos["P"] = pagina
    if tooltip:
        datos["TU"] = PDFString(tooltip)
    widget = PDFDictionary(datos)
    try:
        canv._addAnnotation(widget)
    except Exception:
        return False
    _registrar_campo(form, widget)
    return True


def _aplicar_apariencia_hit(widget, js):
    if widget is None or not hasattr(widget, "dict"):
        return
    widget.dict["H"] = PDFName("N")
    widget.dict["AA"] = PDFDictionary({
        "U": PDFDictionary({
            "S": PDFName("JavaScript"),
            "JS": PDFString(js),
        })
    })
    mk = widget.dict.get("MK")
    if isinstance(mk, PDFDictionary):
        mk.dict["BC"] = PDFArray([])
        mk.dict["BG"] = PDFArray([])
    else:
        widget.dict["MK"] = PDFDictionary({
            "BC": PDFArray([]),
            "BG": PDFArray([]),
        })


def _anadir_boton_hit(canv, nombre, tooltip, ancho, alto, js):
    """Cubre la tarjeta con un botón transparente que elige la opción.

    Usa `AcroForm.button` cuando existe (ReportLab ≥ 4.2). Si no, o si
    falla la firma, crea el widget a mano. Nunca debe tumbar la generación
    del PDF: la tarjeta y el radio ya están dibujados.
    """
    form = canv.acroForm
    if hasattr(form, "button"):
        kwargs_completos = dict(
            name=nombre,
            tooltip=tooltip,
            x=0, y=0,
            width=ancho, height=alto,
            relative=True,
            borderWidth=0,
            forceBorder=False,
            fillColor=None,
            borderColor=None,
            annotationFlags="print",
            fieldFlags="",
            buttonStyle="none",
        )
        try:
            form.button(**kwargs_completos)
        except TypeError:
            try:
                form.button(
                    name=nombre,
                    tooltip=tooltip,
                    x=0, y=0,
                    width=ancho, height=alto,
                    relative=True,
                    borderWidth=0,
                    annotationFlags="print",
                )
            except Exception:
                return _anadir_boton_hit_nativo(canv, form, nombre, tooltip, ancho, alto, js)
        except Exception:
            return _anadir_boton_hit_nativo(canv, form, nombre, tooltip, ancho, alto, js)
        if form.fields:
            _aplicar_apariencia_hit(_widget_de_referencia(canv, form.fields[-1]), js)
        return True
    return _anadir_boton_hit_nativo(canv, form, nombre, tooltip, ancho, alto, js)


class TarjetaOpcionClicable(Flowable):
    """Tarjeta de producto cuya superficie entera elige la opción.

    Dibuja el contenido (foto, texto, casilla) y encima un botón
    AcroForm transparente del mismo tamaño. Pulsar la foto, el nombre
    o cualquier hueco de la tarjeta marca el radio de esa opción.
    """

    def __init__(self, interior, ctx, grupo, valor, tooltip=""):
        Flowable.__init__(self)
        self.interior = interior
        self.ctx = ctx
        self.grupo = grupo
        self.valor = str(valor)
        self.tooltip = tooltip
        self.hAlign = "LEFT"

    def wrap(self, ancho_disp, alto_disp):
        self.width, self.height = self.interior.wrap(ancho_disp, alto_disp)
        return self.width, self.height

    def draw(self):
        self.interior.drawOn(self.canv, 0, 0)
        w, h = float(self.width or 0), float(self.height or 0)
        if w < 4 or h < 4:
            return
        # La tarjeta y el radio ya están en el PDF. Si el visor o la
        # versión de ReportLab no admiten el botón transparente, el
        # documento sigue siendo válido (se elige con la casilla).
        try:
            js = 'var f=this.getField("%s"); if(f) f.value="%s";' % (
                _js_escapar(self.grupo),
                _js_escapar(self.valor),
            )
            _anadir_boton_hit(
                self.canv,
                "hit_%s_%s" % (self.grupo, self.valor),
                self.tooltip or "Elegir este producto",
                w, h, js,
            )
        except Exception:
            return


class FotoOpcionRadio(Flowable):
    """Foto de un producto enmarcada elegantemente para opciones de producto."""

    def __init__(self, ctx, grupo, valor, marcado, ruta_img, ancho=100, alto=100,
                 tooltip=""):
        Flowable.__init__(self)
        self.ctx = ctx
        self.grupo = grupo
        self.valor = valor
        self.marcado = marcado
        self.ruta_img = ruta_img
        self.width = ancho
        self.height = alto
        self.tooltip = tooltip
        self.hAlign = "LEFT"

    def wrap(self, ancho_disp, alto_disp):
        return (self.width, self.height)

    def draw(self):
        from reportlab.lib.utils import ImageReader

        canv = self.canv
        w, h = self.width, self.height
        canv.setStrokeColor(self.ctx.color_acento if self.marcado else self.ctx.color_texto)
        canv.setLineWidth(1.2 if self.marcado else 0.6)
        canv.rect(0, 0, w, h, stroke=1, fill=0)
        if self.ruta_img:
            try:
                canv.drawImage(
                    ImageReader(str(self.ruta_img)),
                    2, 2, width=w - 4, height=h - 4,
                    preserveAspectRatio=True, anchor="c", mask="auto",
                )
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Contexto: acumula datos y campos mientras se construye el documento
# ---------------------------------------------------------------------------

class ContextoInteractivo:
    """Estado compartido durante la generación del PDF interactivo.

    Guarda la tabla de datos que consumirá el JavaScript del documento
    (cantidades, precios base y precios de cada producto) y la lista
    ordenada de campos calculados.
    """

    def __init__(self, presupuesto, moneda, color_texto, color_acento,
                 etiqueta_total="PRESUPUESTO TOTAL"):
        self.presupuesto = presupuesto
        self.moneda = moneda
        self.simbolo = str(moneda or "USD").upper()
        self.color_texto = color_texto
        self.color_acento = color_acento
        self.etiqueta_total = etiqueta_total

        # partidas: id → {cantidad, base, precios[], capitulo, cuenta}
        self.partidas = {}
        # capitulos: id → {constante, partidas[]}
        self.capitulos = {}
        self._orden_calculo = []
        self._nombres_orden = []
        self._ids_partida = {}
        self._ids_capitulo = {}

        # Constantes económicas del documento (no dependen de la elección).
        self.parametros = {
            "iva": float(getattr(presupuesto, "impuesto_pct", 0) or 0),
            "descuento": float(getattr(presupuesto, "descuento_pct", 0) or 0),
            "indirectos": float(getattr(presupuesto, "gastos_indirectos_pct", 0) or 0),
            "imprevistos": float(getattr(presupuesto, "imprevistos_pct", 0) or 0),
            "transporte": float(getattr(presupuesto, "transporte_monto", 0) or 0),
            "otros": float(getattr(presupuesto, "otros_cargos_monto", 0) or 0),
        }
        # Importes fijos: partidas sin opciones múltiples. Se rellenan en
        # `preparar()` y se suman como constante en cada fórmula.
        self.fijos = {"incluido": 0.0, "opcional": 0.0, "alternativas": 0.0}

    # -- identificadores estables -----------------------------------------
    def id_partida(self, partida):
        clave = id(partida)
        if clave not in self._ids_partida:
            self._ids_partida[clave] = "p%d" % (len(self._ids_partida) + 1)
        return self._ids_partida[clave]

    def id_capitulo(self, capitulo):
        clave = id(capitulo)
        if clave not in self._ids_capitulo:
            self._ids_capitulo[clave] = "c%d" % (len(self._ids_capitulo) + 1)
        return self._ids_capitulo[clave]

    # -- registro ----------------------------------------------------------
    def registrar_orden_calculo(self, nombre, referencia):
        if nombre in self._nombres_orden:
            return
        self._nombres_orden.append(nombre)
        self._orden_calculo.append(referencia)

    def es_interactiva(self, partida):
        return self.id_partida(partida) in self.partidas

    # -- preparación -------------------------------------------------------
    def preparar(self):
        """Recorre el presupuesto y decide qué partidas son interactivas.

        Devuelve True si hay al menos una partida con varios productos a
        elegir (única situación en la que merece la pena montar el
        formulario).
        """
        from .calculations import (
            importe_partida, partida_activa, tipo_partida,
        )

        presupuesto = self.presupuesto
        avanzadas = bool(getattr(presupuesto, "usar_funciones_avanzadas", False))

        for capitulo in presupuesto.capitulos:
            cid = self.id_capitulo(capitulo)
            datos_cap = {"constante": 0.0, "partidas": []}
            for partida in capitulo.partidas:
                tipo = tipo_partida(partida) if avanzadas else "included"
                activa = partida_activa(partida) if avanzadas else True
                # El subtotal del capítulo del PDF omite las partidas no
                # seleccionadas de tipo excluida/opcional/alternativa.
                cuenta_en_capitulo = not (
                    avanzadas
                    and tipo in {"excluded", "optional", "alternative"}
                    and not getattr(partida, "seleccionada", False)
                )
                opciones = self._opciones_de(partida)
                if len(opciones) < 2:
                    importe = float(importe_partida(partida))
                    if cuenta_en_capitulo:
                        datos_cap["constante"] += importe
                    self._acumular_fijo(tipo, activa, importe)
                    continue

                pid = self.id_partida(partida)
                self.partidas[pid] = {
                    "cantidad": float(getattr(partida, "cantidad_total", 0) or 0),
                    "base": float(getattr(partida, "precio_base_sin_producto", 0) or 0),
                    "precios": [self._precio_de(op) for op in opciones],
                    "nombres": [self._nombre_de(op) for op in opciones],
                    "unidades": [self._unidad_de(op, partida) for op in opciones],
                    "elegido": int(getattr(partida, "indice_producto_elegido", 0) or 0),
                    "mediciones": [float(m.cantidad or 0) for m in (partida.mediciones or [])],
                    "capitulo": cid,
                    "cuenta_capitulo": bool(cuenta_en_capitulo),
                    "tipo": tipo,
                    "activa": bool(activa),
                }
                if cuenta_en_capitulo:
                    datos_cap["partidas"].append(pid)
            self.capitulos[cid] = datos_cap

        return bool(self.partidas)

    def _acumular_fijo(self, tipo, activa, importe):
        if tipo == "optional":
            self.fijos["opcional"] += importe
            if activa:
                self.fijos["incluido"] += importe
        elif tipo == "alternative":
            self.fijos["alternativas"] += importe
            if activa:
                self.fijos["incluido"] += importe
        elif activa:
            self.fijos["incluido"] += importe

    @staticmethod
    def _opciones_de(partida):
        if not getattr(partida, "tiene_producto", False):
            return []
        return list(getattr(partida, "productos_multiples", None) or [])

    @staticmethod
    def _precio_de(opcion):
        precio = getattr(opcion, "precio", None)
        if precio is None:
            precio = getattr(opcion, "producto_precio", None)
        try:
            return float(precio or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _nombre_de(opcion):
        return str(
            getattr(opcion, "nombre", "") or getattr(opcion, "producto_nombre", "") or ""
        )

    @staticmethod
    def _unidad_de(opcion, partida):
        return str(
            getattr(opcion, "unidad", "") or getattr(opcion, "producto_unidad", "")
            or getattr(partida, "unidad", "") or "ud"
        )

    # -- espejo en Python de las fórmulas del JavaScript -------------------
    #
    # El texto inicial de cada campo se calcula con estas funciones, no con
    # los valores del ORM. Así el primer pintado del PDF y el resultado de
    # recalcular tras pulsar una opción son idénticos por construcción,
    # incluso con precios de más de dos decimales guardados en la base.
    @staticmethod
    def _r2(valor):
        from .calculations import money
        return float(money(valor))

    def _sel(self, pid):
        return int(self.partidas[pid]["elegido"])

    def pu(self, pid):
        datos = self.partidas[pid]
        return self._r2(datos["base"] + datos["precios"][self._sel(pid)])

    def imp(self, pid):
        return self._r2(self.partidas[pid]["cantidad"] * self.pu(pid))

    def imp_medicion(self, pid, indice):
        return self._r2(self.partidas[pid]["mediciones"][indice] * self.pu(pid))

    def cap(self, cid):
        datos = self.capitulos[cid]
        total = datos["constante"]
        for pid in datos["partidas"]:
            total += self.imp(pid)
        return self._r2(total)

    def totales(self):
        p = self.parametros
        incluido = self.fijos["incluido"]
        opcional = self.fijos["opcional"]
        alternativas = self.fijos["alternativas"]
        for pid, datos in self.partidas.items():
            importe = self.imp(pid)
            if datos["tipo"] == "optional":
                opcional += importe
                if datos["activa"]:
                    incluido += importe
            elif datos["tipo"] == "alternative":
                alternativas += importe
                if datos["activa"]:
                    incluido += importe
            elif datos["activa"]:
                incluido += importe
        incluido = self._r2(incluido)
        adicionales = self._r2(
            self._r2(p["transporte"]) + self._r2(p["otros"])
            + self._r2(incluido * p["indirectos"] / 100)
            + self._r2(incluido * p["imprevistos"] / 100)
        )
        bruto = self._r2(incluido + adicionales)
        descuento = self._r2(bruto * p["descuento"] / 100)
        base = self._r2(bruto - descuento)
        impuesto = self._r2(base * p["iva"] / 100)
        return {
            "subtotal": incluido,
            "opcional": self._r2(opcional),
            "alternativas": self._r2(alternativas),
            "adicionales": adicionales,
            "descuento": descuento,
            "base": base,
            "impuesto": impuesto,
            "total": self._r2(base + impuesto),
        }

    # -- textos iniciales (idénticos a los que produce el JavaScript) -----
    def _monto(self, valor):
        from ..utils import fmt_num
        return "%s %s" % (fmt_num(valor), self.simbolo)

    def txt_precio_unitario(self, partida):
        from ..utils import fmt_num
        pid = self.id_partida(partida)
        unidad = self.partidas[pid]["unidades"][self._sel(pid)]
        return "%s %s%s" % (fmt_num(self.pu(pid)), self.simbolo,
                            ("/" + unidad) if unidad else "")

    def txt_importe(self, partida):
        return self._monto(self.imp(self.id_partida(partida)))

    def txt_importe_medicion(self, partida, indice):
        return self._monto(self.imp_medicion(self.id_partida(partida), indice))

    def txt_capitulo(self, capitulo):
        return self._monto(self.cap(self.id_capitulo(capitulo)))

    def txt_peso_capitulo(self, capitulo):
        total = self.totales()["subtotal"]
        if not total:
            return "0,0 %"
        pct = self.cap(self.id_capitulo(capitulo)) * 100 / total
        return ("%.1f %%" % pct).replace(".", ",")

    def txt_total(self, clave):
        valor = self.totales()[clave]
        if clave == "descuento":
            return "- " + self._monto(valor)
        return self._monto(valor)

    # -- fábricas de campos ------------------------------------------------
    def campo(self, nombre, valor, js, ancho, **kw):
        return CampoCalculado(self, nombre, valor, js, ancho, **kw)

    def radio(self, partida, indice, marcado, tooltip=""):
        return OpcionRadio(self, "sel_" + self.id_partida(partida), str(indice),
                           marcado, tam=12, tooltip=tooltip)

    def tarjeta_clicable(self, interior, partida, indice, tooltip=""):
        return TarjetaOpcionClicable(
            interior, self, "sel_" + self.id_partida(partida), indice,
            tooltip=tooltip,
        )

    def radio_foto(self, partida, indice, marcado, ruta_img, ancho=104, alto=104,
                   tooltip=""):
        return FotoOpcionRadio(
            self, "sel_" + self.id_partida(partida), str(indice),
            marcado, ruta_img, ancho=ancho, alto=alto, tooltip=tooltip,
        )

    # -- JavaScript del documento -----------------------------------------
    def script_documento(self):
        datos = {
            "partidas": self.partidas,
            "capitulos": self.capitulos,
            "parametros": self.parametros,
            "fijos": self.fijos,
            "simbolo": self.simbolo,
        }
        return _PLANTILLA_JS.replace("__DATOS__", json.dumps(datos, ensure_ascii=True))

    # -- fórmulas listas para cada campo ----------------------------------
    def js_precio_unitario(self, partida):
        return 'event.value = PU_TXT("%s");' % self.id_partida(partida)

    def js_importe(self, partida):
        return 'event.value = IMP_TXT("%s");' % self.id_partida(partida)

    def js_importe_medicion(self, partida, indice):
        return 'event.value = MED_TXT("%s", %d);' % (self.id_partida(partida), indice)

    def js_nombre_producto(self, partida):
        return 'event.value = NOMBRE("%s");' % self.id_partida(partida)

    def js_capitulo(self, capitulo):
        return 'event.value = CAP_TXT("%s");' % self.id_capitulo(capitulo)

    def js_peso_capitulo(self, capitulo):
        return 'event.value = PESO_TXT("%s");' % self.id_capitulo(capitulo)

    def js_total(self, clave):
        return 'event.value = TOT_TXT("%s");' % clave

    # -- integración con el canvas ----------------------------------------
    def aplicar_al_canvas(self, canv):
        """Cierra el formulario: orden de cálculo y script del documento."""
        form = getattr(canv, "AcroForm", None)
        if form is None:
            return
        # NeedAppearances hace que el visor regenere el texto de los campos
        # con el valor recalculado (si no, mostraría la apariencia inicial).
        form.extras["NeedAppearances"] = PDFFromString("true")
        if self._orden_calculo:
            form.extras["CO"] = PDFArray(list(self._orden_calculo))
        script = PDFDictionary({
            "S": PDFName("JavaScript"),
            "JS": PDFString(self.script_documento()),
        })
        referencia = canv._doc.Reference(script)
        canv._doc._catalog.Names = PDFDictionary({
            "JavaScript": PDFDictionary({
                "Names": PDFArray([PDFString("presupuesto_calculo"), referencia])
            })
        })


# ---------------------------------------------------------------------------
# JavaScript embebido en el documento
# ---------------------------------------------------------------------------
# Se escribe en ES3 (sin let/const/arrow) porque el motor de Acrobat es
# antiguo. `__DATOS__` se sustituye por el JSON del presupuesto.
_PLANTILLA_JS = r"""
var PRESU = __DATOS__;

/* Redondeo monetario idéntico a ROUND_HALF_UP de la aplicación. */
function R2(x) {
  if (!isFinite(x)) return 0;
  var s = x < 0 ? -1 : 1;
  return s * Math.floor(Math.abs(x) * 100 + 0.5 + 1e-9) / 100;
}

/* 1234567.89 -> "1.234.567,89" (mismo formato que utils.fmt_num). */
function NUM(x) {
  x = R2(x);
  var neg = x < 0;
  var s = Math.abs(x).toFixed(2);
  var p = s.split(".");
  var ent = p[0], out = "";
  while (ent.length > 3) {
    out = "." + ent.substring(ent.length - 3) + out;
    ent = ent.substring(0, ent.length - 3);
  }
  return (neg ? "-" : "") + ent + out + "," + p[1];
}

function MONTO(x) { return NUM(x) + " " + PRESU.simbolo; }

/* Índice del producto marcado en la partida. */
function SEL(pid) {
  var d = PRESU.partidas[pid];
  if (!d) return 0;
  var campo = this.getField("sel_" + pid);
  var i = campo ? parseInt(campo.value, 10) : NaN;
  if (isNaN(i) || i < 0 || i >= d.precios.length) i = d.elegido;
  return i;
}

/* Precio unitario de la partida = obra + producto elegido. */
function PU(pid) {
  var d = PRESU.partidas[pid];
  if (!d) return 0;
  return R2(d.base + d.precios[SEL(pid)]);
}

function PU_TXT(pid) {
  var d = PRESU.partidas[pid];
  var u = d ? d.unidades[SEL(pid)] : "";
  return NUM(PU(pid)) + " " + PRESU.simbolo + (u ? "/" + u : "");
}

function IMP(pid) {
  var d = PRESU.partidas[pid];
  if (!d) return 0;
  return R2(d.cantidad * PU(pid));
}

function IMP_TXT(pid) { return MONTO(IMP(pid)); }

function MED_TXT(pid, k) {
  var d = PRESU.partidas[pid];
  if (!d || !d.mediciones || k >= d.mediciones.length) return "";
  return MONTO(R2(d.mediciones[k] * PU(pid)));
}

function NOMBRE(pid) {
  var d = PRESU.partidas[pid];
  if (!d) return "";
  return d.nombres[SEL(pid)];
}

function CAP(cid) {
  var c = PRESU.capitulos[cid];
  if (!c) return 0;
  var t = c.constante, i;
  for (i = 0; i < c.partidas.length; i++) t += IMP(c.partidas[i]);
  return R2(t);
}

function CAP_TXT(cid) { return MONTO(CAP(cid)); }

/* Peso del capítulo sobre el subtotal incluido, en tanto por ciento. */
function PESO_TXT(cid) {
  var total = TOTALES().subtotal;
  if (!total) return "0,0 %";
  var pct = CAP(cid) * 100 / total;
  return (Math.round(pct * 10) / 10).toFixed(1).replace(".", ",") + " %";
}

/* Totales del documento, replicando services/calculations.py. */
function TOTALES() {
  var f = PRESU.fijos, p = PRESU.parametros;
  var incluido = f.incluido, opcional = f.opcional, alternativas = f.alternativas;
  for (var pid in PRESU.partidas) {
    if (!PRESU.partidas.hasOwnProperty(pid)) continue;
    var d = PRESU.partidas[pid];
    var imp = IMP(pid);
    if (d.tipo == "optional") {
      opcional += imp;
      if (d.activa) incluido += imp;
    } else if (d.tipo == "alternative") {
      alternativas += imp;
      if (d.activa) incluido += imp;
    } else if (d.activa) {
      incluido += imp;
    }
  }
  incluido = R2(incluido);
  var basePartidas = incluido;
  var adicionales = R2(
    R2(p.transporte) + R2(p.otros)
    + R2(basePartidas * p.indirectos / 100)
    + R2(basePartidas * p.imprevistos / 100)
  );
  var bruto = R2(basePartidas + adicionales);
  var descuento = R2(bruto * p.descuento / 100);
  var base = R2(bruto - descuento);
  var impuesto = R2(base * p.iva / 100);
  return {
    subtotal: incluido,
    opcional: R2(opcional),
    alternativas: R2(alternativas),
    adicionales: adicionales,
    descuento: descuento,
    base: base,
    impuesto: impuesto,
    total: R2(base + impuesto)
  };
}

function TOT_TXT(clave) {
  var t = TOTALES();
  if (clave == "descuento") return "- " + MONTO(t.descuento);
  return MONTO(t[clave]);
}
"""
