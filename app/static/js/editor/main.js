/* ============================================================================
   Editor — Módulo principal

   Orquesta todos los sub-módulos del editor de presupuestos.
   ============================================================================ */

(function () {
  "use strict";

  // Exportar al scope global
  window.EDITOR = window.EDITOR || {};

  var editor = window.EDITOR;

  // Importar dependencias
  var FMT = window.FMT;
  var CATALOGO_UTILS = window.CATALOGO_UTILS;
  var Partida = window.EDITOR.Partida;
  var Capitulo = window.EDITOR.Capitulo;
  var autosave = window.EDITOR.autosave;
  var atajos = window.EDITOR.atajos || window.EDITOR.initAtajos;
  var dragDrop = window.EDITOR.dragDrop || window.EDITOR.initDragDrop;
  var catalogo = window.EDITOR.catalogo || window.EDITOR.initCatalogo;
  var totales = window.EDITOR.totales || window.EDITOR.initStickyTotal;

  // -------------------------------------------------------------------------
  // Estado inicial del editor
  // -------------------------------------------------------------------------

  var DATOS = JSON.parse(document.getElementById("datos-iniciales").textContent || "{}");
  var CATALOGO = JSON.parse(document.getElementById("datos-catalogo").textContent || "[]");
  var PRODUCTOS = JSON.parse(document.getElementById("datos-productos").textContent || "[]");
  var RECURSOS = [];
  try {
    var elRec = document.getElementById("datos-recursos");
    RECURSOS = elRec ? JSON.parse(elRec.textContent || "[]") : [];
  } catch (e) { RECURSOS = []; }

  var BUDGET_ID = (function (valor) {
    var n = Number(valor);
    return Number.isInteger(n) && n > 0 ? n : null;
  })(window.BUDGET_ID);
  window.BUDGET_ID = BUDGET_ID;
  var contCapitulos = document.getElementById("capitulos");

  function fusionarIndiceCatalogo(nuevas) {
    var previas = editor.CATALOGO || [];
    var indice = nuevas || [];
    var ids = Object.create(null);
    indice.forEach(function (p) { ids[String(p.id)] = true; });
    previas.forEach(function (p) {
      if (p && p.id && !ids[String(p.id)]) indice.push(p);
    });
    editor.CATALOGO = indice;
    if (typeof editor.reconstruirArbolCatalogo === "function") {
      editor.reconstruirArbolCatalogo();
    }
  }

  function urlDatosConFase(url, fase) {
    if (!fase) return url;
    return url + (url.indexOf("?") === -1 ? "?" : "&") + "fase=" + encodeURIComponent(fase);
  }

  function cargarCatalogoDiferido() {
    var url = window.CATALOGO_DATOS_URL;
    if (!url) return;
    var contador = document.getElementById("arbol-contador");

    function fallarCarga() {
      if (contador) contador.textContent = "No se pudo cargar el catálogo";
      var cuerpo = document.querySelector("#arbol-catalogo .arbol-body");
      if (cuerpo && !(editor.CATALOGO || []).length) {
        cuerpo.replaceChildren();
        var p = document.createElement("p");
        p.className = "hint";
        p.textContent = "No se pudo cargar el catálogo. Recarga la página.";
        cuerpo.appendChild(p);
      }
    }

    // Primero solo partidas: la barra lateral no necesita productos ni
    // precios de mercado (eso era lo que dejaba el árbol en «Cargando…»).
    fetch(urlDatosConFase(url, "indice"), {
      headers: { Accept: "application/json" },
      credentials: "same-origin"
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (datos) {
        if (!datos || !datos.ok) throw new Error("catalogo");
        if (datos.arbol && datos.arbol.capitulos) {
          editor.ARBOL_CATALOGO = datos.arbol;
          if (typeof editor.reconstruirArbolCatalogo === "function") {
            editor.reconstruirArbolCatalogo();
          }
        }
        if ((datos.partidas || []).length) fusionarIndiceCatalogo(datos.partidas);
        return fetch(urlDatosConFase(url, "resto"), {
          headers: { Accept: "application/json" },
          credentials: "same-origin"
        });
      })
      .then(function (r) {
        if (!r || !r.ok) return null;
        return r.json();
      })
      .then(function (datos) {
        if (!datos || !datos.ok) return;
        editor.PRODUCTOS = datos.productos || editor.PRODUCTOS || [];
        editor.RECURSOS = datos.recursos || editor.RECURSOS || [];
      })
      .catch(fallarCarga);
  }

  // Pila de deshacer (usada por pushUndo/deshacer)
  editor.undoStack = [];

  editor.DATOS = DATOS;
  editor.CATALOGO = CATALOGO;
  editor.PRODUCTOS = PRODUCTOS;
  editor.RECURSOS = RECURSOS;
  editor.BUDGET_ID = BUDGET_ID;
  editor.contCapitulos = contCapitulos;
  editor.FMT = FMT;
  editor.CATALOGO_UTILS = CATALOGO_UTILS;
  editor.Partida = Partida;
  editor.Capitulo = Capitulo;
  editor.autosave = autosave;

  // -------------------------------------------------------------------------
  // Funciones globales usadas por otros módulos
  // -------------------------------------------------------------------------

  function simbolo() {
    var sel = document.querySelector('select[name="moneda"]');
    var cod = sel && sel.value ? String(sel.value).trim() : "USD";
    if (cod === "Bs") cod = "VES";
    var mapa = {};
    var el = document.getElementById("simbolos-moneda");
    if (el) {
      try { mapa = JSON.parse(el.textContent || "{}"); } catch (_) {}
    }
    return cod.toUpperCase();
  }
  editor.simbolo = simbolo;

  function nuevaPartidaEnCapitulo(capEl) {
    capEl.classList.remove("collapsed");
    // La nueva partida debe poder deshacerse con Ctrl+Z (como duplicar).
    editor.pushUndo();
    var p = Partida.crearPartida(capEl, null, editor);
    if (p) {
      var ni = p.querySelector(".partida-nombre-input");
      if (ni) ni.focus();
    }
    return p;
  }
  editor.nuevaPartidaEnCapitulo = nuevaPartidaEnCapitulo;

  function duplicarPartida(wrap) {
    var cap = wrap.closest(".capitulo");
    var body = cap.querySelector(".partidas-body");
    var datos = Partida.leerPartida(wrap);

    // Una copia es una partida nueva: no comparte ni mueve la trazabilidad
    datos.partida_id = "";
    datos.codigo_externo = "";
    datos.tiene_descomposicion_cype = false;
    datos.nombre_descomposicion_cype = "";
    datos.descomposicion_meta = {};

    editor.pushUndo();
    var nuevo = Partida.crearPartida(cap, datos, editor);
    if (nuevo) {
      body.insertBefore(nuevo, wrap.nextSibling);
      editor.renumerar();
      editor.recalcular();
      var ni = nuevo.querySelector(".partida-nombre-input");
      if (ni) ni.focus();
    }
    editor.marcarCambio();
  }
  editor.duplicarPartida = duplicarPartida;

  function duplicarCapitulo(capEl) {
    var datos = leerCapitulo(capEl);
    editor.pushUndo();
    var nuevo = Capitulo.crear(datos, editor);
    editor.contCapitulos.insertBefore(nuevo, capEl.nextSibling);
    editor.renumerar();
    editor.recalcular();
    editor.marcarCambio();
  }
  editor.duplicarCapitulo = duplicarCapitulo;

  function leerCapitulo(capEl) {
    var partidas = [];
    capEl.querySelectorAll(".partida-wrap").forEach(function (w) {
      partidas.push(Partida.leerPartida(w));
    });
    return {
      nombre: capEl.querySelector('[data-f="cap_nombre"]').value,
      partidas: partidas
    };
  }

  function serializar() {
    var caps = [];
    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
      caps.push(leerCapitulo(c));
    });
    return caps;
  }
  editor.serializar = serializar;

  function construirDesde(lista) {
    editor.contCapitulos.replaceChildren();
    (lista || []).forEach(function (c) { Capitulo.crear(c, editor); });
    if (!editor.contCapitulos.querySelectorAll(".capitulo").length) {
      Capitulo.crear(null, editor);
    }
    editor.renumerar();
    editor.recalcular();
  }
  editor.construirDesde = construirDesde;

  function pushUndo() {
    editor.undoStack.push(serializar());
    if (editor.undoStack.length > 60) editor.undoStack.shift();
  }
  editor.pushUndo = pushUndo;

  function deshacer() {
    if (!editor.undoStack.length) return false;
    construirDesde(editor.undoStack.pop());
    editor.marcarCambio();
    return true;
  }
  editor.deshacer = deshacer;

  function renumerar() {
    var totalPartidas = 0;
    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (cap, ci) {
      cap.querySelectorAll(".partida-wrap").forEach(function (wrap, pi) {
        totalPartidas += 1;
        var num = wrap.querySelector(".partida-num");
        if (num) num.textContent = (ci + 1) + "." + (pi + 1);
      });
    });
    var contador = document.getElementById("builder-item-count");
    if (contador) contador.textContent = totalPartidas;
    actualizarEstadoVacioEditor(totalPartidas);
  }
  editor.renumerar = renumerar;

  function actualizarEstadoVacioEditor(totalPartidas) {
    var empty = document.getElementById("builder-empty-state");
    if (empty) empty.hidden = totalPartidas > 0;
  }
  editor.actualizarEstadoVacioEditor = actualizarEstadoVacioEditor;

  function pintarAvisosPartida(wrap, avisos) {
    var cont = wrap && wrap.querySelector(".partida-alerts");
    if (!cont) return;
    cont.textContent = "";
    avisos = avisos || [];
    cont.hidden = !avisos.length;
    avisos.slice(0, 4).forEach(function (aviso) {
      var chip = document.createElement("span");
      chip.className = "partida-alert-chip " + (aviso.tipo || "warn");
      chip.textContent = aviso.texto;
      if (aviso.titulo) chip.title = aviso.titulo;
      cont.appendChild(chip);
    });
  }

  // -------------------------------------------------------------------------
  // Cálculo de totales (versión simplificada que delega al servidor)
  // -------------------------------------------------------------------------

  function recalcular() {
    // Réplica exacta del motor de cálculo del servidor (calculations.py):
    // cada importe, coste y paso intermedio se redondea a 2 decimales con la
    // misma regla, para que el editor, el PDF y el CSV coincidan al céntimo.
    var totalGral = 0, totalOpcional = 0, totalAlternativas = 0;
    var costeTotal = 0, hayCostes = false;
    var totalProductos = 0, costeProductos = 0, subtotalObra = 0, costeObra = 0;

    var avanzado = !!(document.getElementById("usar-funciones-avanzadas") && document.getElementById("usar-funciones-avanzadas").checked);

    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (cap) {
      var subt = 0;

      cap.querySelectorAll(".partida-row").forEach(function (row) {
        var wrap = row.closest(".partida-wrap");

        // Recalcular descomposición si existe
        if (wrap.querySelectorAll(".drow").length) {
          Partida.recalcularDescompuesto(wrap);
        }

        var cant = cantidadDe(wrap);
        var precio = FMT.parseNum(row.querySelector('input[data-f="p_precio"]').value);
        var importe = FMT.redondear2(cant * precio);

        // Desglose de mediciones visible bajo la fila: el campo de cantidad
        // refleja la SUMA de las mediciones (y pasa a solo lectura) cuando
        // existe desglose; los importes de cada medición y el total del
        // bloque se mantienen sincronizados en vivo.
        var cantInput = row.querySelector('input[data-f="p_cantidad"]');
        var medCantidadEls = wrap.querySelectorAll('.medicion-row input[data-f="m_cantidad"]');
        var hayMediciones = false;
        medCantidadEls.forEach(function (i) {
          if (String(i.value || "").trim() !== "") hayMediciones = true;
        });
        var cantRedondeada = FMT.redondear2(cant);
        if (cantInput) {
          if (hayMediciones) {
            if (String(cantInput.value) !== String(cantRedondeada)) cantInput.value = String(cantRedondeada);
            cantInput.readOnly = true;
            cantInput.title = "Total calculado a partir de las mediciones (edítalas en el desglose de abajo)";
            cantInput.classList.add("partida-cant-calculada");
          } else {
            cantInput.readOnly = false;
            cantInput.removeAttribute("title");
            cantInput.classList.remove("partida-cant-calculada");
          }
        }
        wrap.querySelectorAll(".medicion-row").forEach(function (m) {
          var cantMed = FMT.parseNum((m.querySelector('[data-f="m_cantidad"]') || {}).value);
          var importeMed = m.querySelector(".partida-medicion-importe");
          if (importeMed) importeMed.textContent = FMT.fmtNum(FMT.redondear2(cantMed * precio));
        });
        var medTotalEl = wrap.querySelector(".partida-mediciones-total");
        if (medTotalEl) {
          var unidadEl = wrap.querySelector('[data-f="p_unidad"]');
          medTotalEl.textContent = "Σ " + FMT.fmtNum(cantRedondeada) + (unidadEl ? " " + unidadEl.value : "");
        }

        var tipoEl = wrap && wrap.querySelector('[data-f="p_tipo_partida"]');
        var selEl = wrap && wrap.querySelector('[data-f="p_seleccionada"]');
        var tipo = avanzado && tipoEl ? tipoEl.value : "included";
        var activa = !avanzado || !selEl || selEl.value === "1" || ["included", "provisional", "measurement"].indexOf(tipo) !== -1;

        if (tipo === "optional") totalOpcional += importe;
        if (tipo === "alternative") totalAlternativas += importe;
        if (activa && tipo !== "excluded") subt += importe;

        var impCell = row.querySelector(".partida-importe");
        if (impCell) {
          impCell.textContent = FMT.fmt(importe);
        }

        // Beneficio por partida
        var costeMat = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_coste_materiales"]') || {}).value);
        var costeMO = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_coste_mano_obra"]') || {}).value);
        var costeComp = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_coste_complementarios"]') || {}).value);
        var costeOtros = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_coste_otros"]') || {}).value);
        var desperd = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_desperdicio_pct"]') || {}).value);
        // El coste del producto se conserva separado de la descomposición: es
        // la compra real del material comercial asociado a esta partida.
        var costeProducto = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_prod_coste"]') || {}).value);
        var precioProducto = FMT.parseNum((wrap && wrap.querySelector('[data-f="p_prod_precio"]') || {}).value);
        var nombreProducto = String((wrap && wrap.querySelector('[data-f="p_prod_nombre"]') || {}).value || "").trim();
        var imagenProducto = String((wrap && wrap.querySelector('[data-f="p_prod_imagen_actual"]') || {}).value || "").trim();
        var hayProducto = !!(nombreProducto || imagenProducto || (wrap && wrap.querySelector('[data-f="p_prod_precio"]') && precioProducto !== 0));
        var importeProducto = hayProducto ? FMT.redondear2(cant * precioProducto) : 0;
        var importeObraLinea = FMT.redondear2(importe - importeProducto);
        var costeProductoLinea = hayProducto ? FMT.redondear2(cant * costeProducto) : 0;

        // En las partidas con descompuesto importado el coste directo ya incluye
        // sus propios redondeos y NO se le aplica el desperdicio de la
        // partida (misma regla que el servidor). En el resto (descompuesto
        // manual o solo campos de coste) el desperdicio sí se aplica.
        var esCype = false;
        var metaEl = wrap && wrap.querySelector('[data-f="p_descomposicion_meta"]');
        if (metaEl && metaEl.value) {
          try {
            var metaDes = JSON.parse(metaEl.value);
            esCype = metaDes && (metaDes.origen === "cype" || metaDes.archivo_origen);
          } catch (e) { esCype = false; }
        }
        var cypeFlag = wrap && wrap.querySelector('[data-f="p_tiene_descomposicion_cype"]');
        if (!esCype && cypeFlag && cypeFlag.value === "1") {
          var origenDes = (wrap && wrap.dataset && wrap.dataset.origenDescomposicion) || "";
          esCype = origenDes !== "manual";
        }
        var sumCostes = costeMat + costeMO + costeComp + costeOtros;
        var costeUnidadObra = esCype
          ? sumCostes
          : sumCostes * (1 + desperd / 100);
        var costeUnidad = costeUnidadObra + costeProducto;
        var costeObraLinea = FMT.redondear2(cant * costeUnidadObra);
        var coste = FMT.redondear2(cant * costeUnidad);
        var hayCostesPartida = (sumCostes + costeProducto) > 0;

        if (hayCostesPartida) hayCostes = true;

        var beneficio = FMT.redondear2(importe - coste);
        var markupFila = hayCostesPartida && coste > 0 ? (beneficio / coste * 100) : 0;
        var margenFilaPct = hayCostesPartida && importe > 0 ? (beneficio / importe * 100) : 0;
        var avisosPartida = [];
        var nombrePartida = String((wrap && wrap.querySelector('[data-f="p_nombre"]') || {}).value || "").trim();
        if (!nombrePartida) avisosPartida.push({ tipo: "danger", texto: "Sin nombre", titulo: "Añade un nombre a la partida" });
        if (cant <= 0) avisosPartida.push({ tipo: "danger", texto: "Cantidad 0", titulo: "Esta partida no suma porque la cantidad es 0" });
        if (precio <= 0) avisosPartida.push({ tipo: "danger", texto: "Precio 0", titulo: "Indica precio unitario antes de enviar" });
        if (!hayCostesPartida) avisosPartida.push({ tipo: "muted", texto: "Sin coste", titulo: "Sin coste interno no se calcula margen real" });
        else if (beneficio < 0) avisosPartida.push({ tipo: "danger", texto: "Pérdida", titulo: "El coste supera el precio de venta" });
        else if (margenFilaPct > 0 && margenFilaPct < 20) avisosPartida.push({ tipo: "warn", texto: "Margen bajo", titulo: "Margen por debajo del 20%" });
        pintarAvisosPartida(wrap, avisosPartida);
        var margenReal = wrap.querySelector('[data-f="margen_real"]');
        if (margenReal) {
          if (hayCostesPartida) {
            var markupUnidad = costeUnidad > 0 ? ((precio - costeUnidad) / costeUnidad * 100) : 0;
            var margenUnidad = precio > 0 ? ((precio - costeUnidad) / precio * 100) : 0;
            margenReal.textContent = markupUnidad.toFixed(1).replace(".", ",") + " % s/coste · " + margenUnidad.toFixed(1).replace(".", ",") + " % margen";
            margenReal.title = "Beneficio sobre coste: " + markupUnidad.toFixed(2) + "% | Margen sobre precio: " + margenUnidad.toFixed(2) + "%";
          } else {
            margenReal.textContent = "—";
          }
        }

        var benefCell = row.querySelector(".partida-beneficio");
        if (benefCell) {
          if (!hayCostesPartida) {
            benefCell.textContent = "—";
            benefCell.classList.add("sin-datos");
            benefCell.classList.remove("negativo");
            benefCell.title = "Sin datos de coste: añade descomposición o costes para ver beneficio";
          } else {
            // Mostrar beneficio importe + % sobre coste (lo que pide el usuario) y margen en tooltip
            benefCell.textContent = FMT.fmt(beneficio) + " · " + markupFila.toFixed(1).replace(".", ",") + "%";
            benefCell.title = "Beneficio " + FMT.fmt(beneficio) + " | " + markupFila.toFixed(2).replace(".", ",") + "% sobre coste | " + margenFilaPct.toFixed(2).replace(".", ",") + "% margen s/precio · Coste: " + FMT.fmt(coste);
            benefCell.classList.remove("sin-datos");
            benefCell.classList.toggle("negativo", beneficio < 0);
          }
        }

        if (activa && tipo !== "excluded") {
          totalProductos += importeProducto;
          subtotalObra += importeObraLinea;
          if (hayCostesPartida) {
            costeTotal += coste;
            costeObra += costeObraLinea;
            // No considerar 0 como coste real del producto cuando el campo
            // está vacío; así su venta no aparece como beneficio íntegro.
            if (hayProducto && costeProducto > 0) costeProductos += costeProductoLinea;
          }
        }
      });

      var chip = cap.querySelector(".capitulo-subtotal");
      if (chip) chip.textContent = FMT.fmt(FMT.redondear2(subt));

      totalGral += subt;
    });

    // Cargar valores del formulario
    var dto = FMT.parseNum(document.querySelector('input[name="descuento_pct"]').value);
    var ivaPct = FMT.parseNum(document.querySelector('input[name="impuesto_pct"]').value);
    var moneda = (document.querySelector('select[name="moneda"]') || {}).value || "USD";

    // Cada paso económico se redondea igual que en el servidor:
    //  base_partidas = money(subtotal) · adicionales = money(cada uno) ·
    //  bruto = money(base + adicionales) · descuento = money(bruto × %/100) ·
    //  base = money(bruto - descuento) · iva = money(base × %/100) ·
    //  total = money(base + iva)
    var basePartidas = FMT.redondear2(totalGral);
    totalProductos = FMT.redondear2(totalProductos);
    subtotalObra = FMT.redondear2(subtotalObra);
    costeProductos = FMT.redondear2(costeProductos);
    costeObra = FMT.redondear2(costeObra);
    var indirectos = avanzado ? FMT.redondear2(basePartidas * FMT.parseNum((document.querySelector('input[name="gastos_indirectos_pct"]') || {}).value) / 100) : 0;
    var imprevistos = avanzado ? FMT.redondear2(basePartidas * FMT.parseNum((document.querySelector('input[name="imprevistos_pct"]') || {}).value) / 100) : 0;
    var transporte = avanzado ? FMT.redondear2(FMT.parseNum((document.querySelector('input[name="transporte_monto"]') || {}).value)) : 0;
    var otros = avanzado ? FMT.redondear2(FMT.parseNum((document.querySelector('input[name="otros_cargos_monto"]') || {}).value)) : 0;

    var adicionales = FMT.redondear2(indirectos + imprevistos + transporte + otros);
    var bruto = FMT.redondear2(basePartidas + adicionales);
    var descuento = FMT.redondear2(bruto * dto / 100);
    var base = FMT.redondear2(bruto - descuento);
    var iva = FMT.redondear2(base * ivaPct / 100);
    var totalFinal = FMT.redondear2(base + iva);
    // Beneficio real de la obra = lo que queda para la empresa después de
    // descontar TODOS los gastos (materiales, mano de obra, complementarios,
    // otros, imprevistos, transporte…). El IVA NO es beneficio: es un impuesto
    // que se recauda y se entrega al Estado, por eso el ingreso real es la
    // base imponible (sin IVA). Los productos comerciales se separan para que
    // no distorsionen el margen de la obra.
    var brutoObra = FMT.redondear2(subtotalObra + adicionales);
    var brutoProductos = totalProductos;
    var descuentoObra = bruto > 0 ? FMT.redondear2(descuento * brutoObra / bruto) : descuento;
    var descuentoProductos = bruto > 0 ? FMT.redondear2(descuento * brutoProductos / bruto) : 0;
    var diferenciaDescuento = FMT.redondear2(descuento - descuentoObra - descuentoProductos);
    descuentoObra = FMT.redondear2(descuentoObra + diferenciaDescuento);
    var baseObra = FMT.redondear2(brutoObra - descuentoObra);
    var baseProductos = FMT.redondear2(brutoProductos - descuentoProductos);
    var beneficioObra = FMT.redondear2(baseObra - costeObra - adicionales);
    var beneficioProductos = costeProductos > 0 ? FMT.redondear2(baseProductos - costeProductos) : 0;
    var beneficioTotal = FMT.redondear2(beneficioObra + beneficioProductos);
    var margenPct = base > 0 ? FMT.redondear2(beneficioTotal / base * 100) : 0;
    var margenObraPct = baseObra > 0 ? FMT.redondear2(beneficioObra / baseObra * 100) : 0;
    var margenProductosPct = baseProductos > 0 ? FMT.redondear2(beneficioProductos / baseProductos * 100) : 0;
    var hayCostesProductos = costeProductos > 0;

    var set = function (id, v) {
      var e = document.getElementById(id);
      if (e) e.textContent = v;
    };

    set("ui-subtotal", FMT.fmt(basePartidas, moneda));
    set("ui-opcional", FMT.fmt(totalOpcional, moneda));
    set("ui-alternativas", FMT.fmt(totalAlternativas, moneda));
    set("ui-productos", FMT.fmt(totalProductos, moneda));
    set("ui-obra", FMT.fmt(subtotalObra, moneda));
    set("ui-adicionales", FMT.fmt(adicionales, moneda));
    set("ui-descuento", "- " + FMT.fmt(descuento, moneda));
    set("ui-iva", FMT.fmt(iva, moneda));
    set("ui-total", FMT.fmt(totalFinal, moneda));
    set("sticky-total-val", FMT.fmt(totalFinal, moneda));
    set("ui-beneficio-obra", FMT.fmt(beneficioObra, moneda));
    set("ui-margen-obra", margenObraPct.toFixed(2).replace(".", ",") + " %");
    set("ui-beneficio-productos", FMT.fmt(beneficioProductos, moneda));
    set("ui-margen-productos", margenProductosPct.toFixed(2).replace(".", ",") + " %");
    set("ui-beneficio", FMT.fmt(beneficioTotal, moneda));
    set("ui-margen", margenPct.toFixed(2).replace(".", ",") + " %");

    // Ocultar/mostrar filas según configuración
    var filaDesc = document.getElementById("ui-fila-desc");
    if (filaDesc) CotizatStyles.set(filaDesc, "display", dto > 0 ? "" : "none");

    ["ui-fila-opcional", "ui-fila-alternativas", "ui-fila-adicionales"].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) CotizatStyles.set(e, "display", avanzado ? "" : "none");
    });
    ["ui-fila-productos", "ui-fila-obra"].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) CotizatStyles.set(e, "display", totalProductos > 0 ? "" : "none");
    });

    ["ui-fila-beneficio-obra", "ui-fila-margen-obra"].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) CotizatStyles.set(e, "display", hayCostes ? "" : "none");
    });
    ["ui-fila-beneficio-productos", "ui-fila-margen-productos"].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) CotizatStyles.set(e, "display", hayCostes && hayCostesProductos ? "" : "none");
    });
    ["ui-fila-beneficio", "ui-fila-margen"].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) CotizatStyles.set(e, "display", hayCostes ? "" : "none");
    });

    // Actualizar barra sticky con datos completos
    var totalsData = {
      total: totalFinal,
      moneda: moneda,
      descuento_pct: dto,
      total_productos: totalProductos,
      margen_pct: margenPct,
      margen: beneficioTotal,
      margen_obra: beneficioObra,
      margen_obra_pct: margenObraPct,
      margen_productos: beneficioProductos,
      margen_productos_pct: margenProductosPct,
      coste_interno: FMT.redondear2(costeTotal),
    };
    editor.actualizarStickyTotal(totalsData);
    if (editor.calcularTiempos) editor.calcularTiempos();
  }
  editor.recalcular = recalcular;

  function cantidadDe(wrapEl) {
    // Misma semántica que el servidor: si hay mediciones con valor (aunque
    // sea 0), la cantidad total es la SUMA de todas ellas; si no, se usa la
    // cantidad directa. Una medición en 0 NO debe caer a la cantidad directa.
    // Las mediciones viven en `.partida-mediciones-inline`, hermano de
    // `.partida-row`, por eso la búsqueda parte del contenedor `.partida-wrap`.
    var filas = wrapEl.querySelectorAll('.medicion-row input[data-f="m_cantidad"]');
    var hayValor = false;
    var sum = 0;
    filas.forEach(function (i) {
      if (String(i.value || "").trim() !== "") hayValor = true;
      sum += FMT.parseNum(i.value);
    });
    if (hayValor) return sum;
    return FMT.parseNum(wrapEl.querySelector('input[data-f="p_cantidad"]').value);
  }
  editor.cantidadDe = cantidadDe;

  // -------------------------------------------------------------------------
  // Marcar cambio y autosave
  // -------------------------------------------------------------------------

  var autosaveTimer = null;

  function marcarCambio() {
    if (autosave) {
      autosave.marcarCambio();
    } else {
      var status = document.getElementById("autosave-status");
      if (status) {
        status.textContent = "Guardando…";
        status.classList.add("dirty");
      }
      clearTimeout(autosaveTimer);
      autosaveTimer = setTimeout(function () {
        if (editor.BUDGET_ID) {
          // Guardar en servidor
          fetch("/presupuestos/" + editor.BUDGET_ID + "/borrador", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ capitulos: serializar(), ts: Date.now() })
          }).then(function (r) { return r.json(); }).then(function (data) {
            var status = document.getElementById("autosave-status");
            if (status) {
              status.textContent = data && data.ok ? "✓ Guardado" : "⚠ Solo local";
              status.classList.remove("dirty");
            }
          });
        }
      }, 8000);
    }
  }
  editor.marcarCambio = marcarCambio;

  function actualizarEstadoAutosave(tipo, ok) {
    // Esta función se mantiene por compatibilidad (autosave.js y los
    // módulos externos la invocan). La presentación real vive en
    // autosave.js, que ya actualiza el indicador con detalle. Aquí
    // simplemente reenviamos a la implementación canónica.
    if (editor.autosave && editor.autosave.actualizarEstado) {
      try { editor.autosave.actualizarEstado(tipo, ok); return; } catch (e) {}
    }
    var status = document.getElementById("autosave-status");
    if (!status) return;
    // Conserva la clase base "autosave-status"; añade o quita "dirty" según
    // el estado sin destruir el resto de la cadena de clases (estilo CSS).
    var pending = editor.autosave && editor.autosave.estado
      ? !!editor.autosave.estado().pendingChanges
      : false;
    if (pending) {
      status.classList.add("dirty");
    } else {
      status.classList.remove("dirty");
    }
    if (tipo === "any" && pending) {
      status.textContent = "Guardando…";
    } else if (tipo === "server" && ok) {
      status.textContent = "✓ Guardado";
    } else if (tipo === "server" && !ok && editor.BUDGET_ID) {
      status.textContent = "⚠ Solo local";
    } else if (tipo === "local") {
      status.textContent = "↻ Borrador local";
    } else if (!pending) {
      status.textContent = "";
    }
  }
  editor.actualizarEstadoAutosave = actualizarEstadoAutosave;

  // -------------------------------------------------------------------------
  // Pegar desde Excel (TSV)
  // -------------------------------------------------------------------------

  function parseExcel(texto) {
    var filas = [];
    texto.split(/\r?\n/).forEach(function (linea) {
      if (!linea.trim()) return;
      var celdas = linea.split(/\t|;/).map(function (c) { return c.trim(); }).filter(function (c) { return c !== ""; });
      if (celdas.length === 0) return;
      filas.push(celdas);
    });

    // Quitar cabecera si el primer campo es "nombre"
    if (filas.length && filas[0][0].toLowerCase() === "nombre") filas.shift();

    var partidas = [];
    filas.forEach(function (c) {
      var p = { nombre: c[0], unidad: "ud", cantidad: 1, precio: 0, descripcion: "" };
      if (c.length >= 4) {
        p.unidad = c[1];
        p.cantidad = FMT.parseNum(c[2]);
        p.precio = FMT.parseNum(c[3]);
      } else if (c.length === 3) {
        p.cantidad = FMT.parseNum(c[1]);
        p.precio = FMT.parseNum(c[2]);
      } else if (c.length === 2) {
        p.precio = FMT.parseNum(c[1]);
      }
      partidas.push(p);
    });
    return partidas;
  }

  function importarPegado(texto) {
    var partidas = parseExcel(texto);
    if (!partidas.length) return;

    editor.pushUndo();
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    var cap = caps.length ? caps[caps.length - 1] : Capitulo.crear({ nombre: "CAPÍTULO GENERAL" }, editor);
    cap.classList.remove("collapsed");

    partidas.forEach(function (p) { Partida.crearPartida(cap, p, editor); });
    editor.renumerar();
    editor.recalcular();
    editor.marcarCambio();
  }

  function initPegarExcel() {
    var btnPegar = document.getElementById("btn-pegar-excel");
    if (btnPegar) {
      btnPegar.addEventListener("click", function () {
        abrirModal("modal-pegar");
      });

      var btnImportar = document.getElementById("btn-importar-excel");
      if (btnImportar) {
        btnImportar.addEventListener("click", function () {
          var ta = document.getElementById("paste-input");
          if (ta && ta.value.trim()) {
            importarPegado(ta.value);
            ta.value = "";
            cerrarModal("modal-pegar");
          }
        });
      }
    }
  }
  editor.initPegarExcel = initPegarExcel;

  function initEmptyStateActions() {
    var empty = document.getElementById("builder-empty-state");
    if (!empty) return;
    var add = document.getElementById("empty-add-first-partida");
    var pack = document.getElementById("empty-open-pack-modal");
    var paste = document.getElementById("empty-paste-excel");
    if (add) add.addEventListener("click", function () {
      var cap = editor.contCapitulos.querySelector(".capitulo") || Capitulo.crear({ nombre: "CAPÍTULO GENERAL" }, editor);
      nuevaPartidaEnCapitulo(cap);
      editor.renumerar();
      editor.recalcular();
    });
    if (pack) pack.addEventListener("click", function () {
      var b = document.getElementById("btn-modal-receta-seccion") || document.getElementById("btn-modal-receta");
      if (b) b.click();
    });
    if (paste) paste.addEventListener("click", function () {
      var b = document.getElementById("btn-pegar-excel");
      if (b) b.click();
    });
  }
  editor.initEmptyStateActions = initEmptyStateActions;

  // -------------------------------------------------------------------------
  // Serialización del formulario
  // -------------------------------------------------------------------------

  function initSerializacionFormulario() {
    var form = document.getElementById("form-presupuesto");
    var estructura = document.getElementById("estructura-json");
    if (!form || !estructura) return;
    form.addEventListener("submit", function () {
      // Los elementos del constructor son dinámicos y se representan como un
      // único JSON para no desalinearlos después de una importación inline.
      editor.contCapitulos.querySelectorAll(".partida-wrap").forEach(function (wrap) {
        Partida.recalcularDescompuesto(wrap);
      });
      estructura.value = JSON.stringify(serializar());

      // Los archivos sí necesitan viajar como multipart; todos comparten el
      // nombre y conservan el mismo orden que las partidas serializadas.
      editor.contCapitulos.querySelectorAll('input[type="file"][data-f="p_prod_imagen"]').forEach(function (file) {
        file.name = "p_prod_imagen";
      });

      // Imágenes nuevas de las opciones múltiples: cada opción guarda el
      // File en su cache viva `wrap._productosOpcionesCache[idx]._imagen_file`
      // (o `section._opcionesCache`). Al enviar el formulario convertimos
      // esos File en inputs `p_opcion_imagen` para que viajen como multipart,
      // con un hidden paralelo `p_opcion_imagen_idx` con formato
      // "<partidaIdx>:<opcionIdx>" para que el servidor los asocie.
      editor.contCapitulos.querySelectorAll(".partida-wrap").forEach(function (wrap, partidaIdx) {
        var cache = wrap._productosOpcionesCache;
        if (!cache || !cache.length) {
          var sec = wrap.querySelector(".productos-opciones-section");
          if (sec && sec._opcionesCache) cache = sec._opcionesCache;
        }
        if (!cache || !cache.length) return;
        cache.forEach(function (op, opIdx) {
          var file = op && op._imagen_file;
          if (!(file instanceof File)) {
            var existingInput = wrap.querySelector('.producto-opcion-tarjeta[data-idx="' + opIdx + '"] input[type="file"][data-opcion-campo="imagen_file"]');
            if (existingInput && existingInput.files && existingInput.files[0]) file = existingInput.files[0];
          }
          if (!(file instanceof File)) return;
          var input = wrap.querySelector('.producto-opcion-tarjeta[data-idx="' + opIdx + '"] input[type="file"][data-opcion-campo="imagen_file"]');
          var createdTemp = false;
          if (!input) {
            input = document.createElement("input");
            input.type = "file";
            CotizatStyles.set(input, "display", "none");
            form.appendChild(input);
            createdTemp = true;
          }
          try {
            var dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
          } catch (e) {
            try { input.files = [file]; } catch (e2) {}
          }
          input.name = "p_opcion_imagen";
          input.setAttribute("data-opcion-partida", String(partidaIdx));
          input.setAttribute("data-opcion-indice", String(opIdx));
          if (!createdTemp) input.setAttribute("data-temp-marker", "1");
          var idxInput = document.createElement("input");
          idxInput.type = "hidden";
          idxInput.name = "p_opcion_imagen_idx";
          idxInput.value = String(partidaIdx) + ":" + String(opIdx);
          form.appendChild(idxInput);
        });
      });

      // Al guardar el formulario el servidor borrará el borrador, así que
      // desactivamos la protección beforeunload y vaciamos el estado de
      // "cambios sin guardar" para que el submit no muestre un confirm
      // y para que el próximo load arranque limpio.
      if (editor.autosave && editor.autosave.suspenderProteccionCierre) {
        try { editor.autosave.suspenderProteccionCierre(); } catch (e) {}
      }
    });
  }
  editor.initSerializacionFormulario = initSerializacionFormulario;

  function initNavegacionCreador() {
    document.querySelectorAll("[data-scroll-builder]").forEach(function (button) {
      button.addEventListener("click", function () {
        var destino = document.getElementById(button.dataset.scrollBuilder);
        if (destino) destino.scrollIntoView({ behavior: "smooth", block: "start" });
        document.querySelectorAll("[data-scroll-builder]").forEach(function (b) { b.classList.remove("active"); });
        button.classList.add("active");
      });
    });
    var previewTop = document.getElementById("btn-preview-pdf-top");
    var preview = document.getElementById("btn-preview-pdf");
    if (previewTop && preview) {
      previewTop.addEventListener("click", function () { preview.click(); });
    }
    if (preview) {
      preview.addEventListener("click", function () {
        if (editor.BUDGET_ID) {
          var frame = document.getElementById("preview-frame");
          if (frame) {
            frame.src = "/presupuestos/" + editor.BUDGET_ID + "/pdf?inline=1&t=" + Date.now();
          }
          abrirModal("modal-preview");
        } else {
          alert("Para previsualizar el PDF, primero guarda el presupuesto.");
        }
      });
    }
    var refreshPreview = document.getElementById("btn-refresh-preview");
    if (refreshPreview) {
      refreshPreview.addEventListener("click", function () {
        var frame = document.getElementById("preview-frame");
        if (frame && editor.BUDGET_ID) {
          frame.src = "/presupuestos/" + editor.BUDGET_ID + "/pdf?inline=1&t=" + Date.now();
        }
      });
    }
  }
  editor.initNavegacionCreador = initNavegacionCreador;

  // -------------------------------------------------------------------------
  // Modales genéricos
  // -------------------------------------------------------------------------

  function abrirModal(id) {
    var m = document.getElementById(id);
    if (m) {
      m.classList.add("open");
      document.body.classList.add("modal-open");
    }
  }
  editor.abrirModal = abrirModal;

  function cerrarModal(id) {
    var m = document.getElementById(id);
    if (m) {
      m.classList.remove("open");
      document.body.classList.remove("modal-open");
    }
  }
  editor.cerrarModal = cerrarModal;

  // -------------------------------------------------------------------------
  // Toggle de IVA
  // -------------------------------------------------------------------------

  function syncIvaToggle() {
    var on = editor.ivaActivo;
    var impInput = document.querySelector('input[name="impuesto_pct"]');
    var pct = on
      ? (impInput ? FMT.parseNum(impInput.value) : 0)
      : (editor.ivaGuardado != null ? editor.ivaGuardado : 0);
    document.querySelectorAll(".iva-toggle-btn").forEach(function (b) {
      b.textContent = on ? "IVA ON" : "IVA OFF";
      b.classList.toggle("active", !on);
      b.title = on ? ("Desactivar IVA (" + pct + " %)") : ("Activar IVA (" + pct + " %)");
    });
  }
  editor.syncIvaToggle = syncIvaToggle;

  function toggleIVA() {
    var impInput = document.querySelector('input[name="impuesto_pct"]');
    if (!impInput) return;
    if (editor.ivaActivo) {
      // Guardamos el % real y lo dejamos en 0 para que se guarde sin IVA.
      editor.ivaGuardado = FMT.parseNum(impInput.value);
      impInput.value = 0;
      editor.ivaActivo = false;
    } else {
      // Restauramos el % real.
      impInput.value = editor.ivaGuardado != null ? editor.ivaGuardado : FMT.parseNum(impInput.value);
      editor.ivaActivo = true;
    }
    syncIvaToggle();
    recalcular();
    marcarCambio();
  }
  editor.toggleIVA = toggleIVA;

  // -------------------------------------------------------------------------
  // Inicialización del editor
  // -------------------------------------------------------------------------

  function init() {
    if (!contCapitulos) return;

    // Variables globales de configuración. La plantilla ya las define con el
    // valor real de la configuración (window.FUNCIONES_AVANZADAS = true/false
    // antes de cargar estos módulos); aquí solo se calculan si por cualquier
    // motivo no llegaron definidas. Sobrescribirlas a false rompía el modo
    // avanzado aunque estuviera activado en Configuración.
    if (typeof window.FUNCIONES_AVANZADAS !== "boolean") {
      window.FUNCIONES_AVANZADAS = !!document.getElementById("funciones-avanzadas-activas");
    }
    if (typeof window.MOSTRAR_ALTERNATIVAS !== "boolean") {
      window.MOSTRAR_ALTERNATIVAS = !!document.getElementById("mostrar-alternativas");
    }
    if (typeof window.MOSTRAR_COSTES_INTERNOS !== "boolean") {
      window.MOSTRAR_COSTES_INTERNOS = !!document.getElementById("mostrar-costes-internos");
    }
    // Beneficio por partida siempre visible (petición usuario: ver beneficio en la fila)
    document.body.classList.add('beneficio-on');

    // Inicializar módulos (soporta tanto objeto.* como init*)
    if (autosave && autosave.iniciar) autosave.iniciar();

    // Atajos
    if (window.EDITOR.initAtajos) window.EDITOR.initAtajos();
    else if (atajos && atajos.initAtajos) atajos.initAtajos();
    else if (typeof atajos === "function") atajos();

    // Drag & Drop — nombre canónico initDragDrop
    if (window.EDITOR.initDragDrop) window.EDITOR.initDragDrop();
    else if (dragDrop && dragDrop.init) dragDrop.init();
    else if (typeof dragDrop === "function") dragDrop();
    else if (window.EDITOR.dragDrop && window.EDITOR.dragDrop.init) window.EDITOR.dragDrop.init();

    // Totales / sticky (antes "totales")
    if (window.EDITOR.initStickyTotal) window.EDITOR.initStickyTotal();
    else if (window.EDITOR.initTotales) window.EDITOR.initTotales();
    else if (totales && totales.init) totales.init();
    else if (typeof totales === "function") totales();

    initPegarExcel();
    initEmptyStateActions();
    initSerializacionFormulario();
    initNavegacionCreador();

    // IVA: estado inicial y botones de activar/desactivar
    editor.ivaActivo = true;
    var impInput = document.querySelector('input[name="impuesto_pct"]');
    editor.ivaGuardado = impInput ? FMT.parseNum(impInput.value) : 0;
    if (impInput) {
      impInput.addEventListener("input", function () {
        if (editor.ivaActivo) editor.ivaGuardado = FMT.parseNum(impInput.value);
      });
    }
    document.querySelectorAll(".iva-toggle-btn").forEach(function (b) {
      b.addEventListener("click", toggleIVA);
    });
    syncIvaToggle();

    // Botón "Agregar otro capítulo"
    var btnAgregarCap = document.getElementById("btn-agregar-capitulo");
    if (btnAgregarCap) {
      btnAgregarCap.addEventListener("click", function () {
        editor.pushUndo();
        var nuevo = Capitulo.crear(null, editor);
        editor.renumerar();
        editor.recalcular();
        editor.marcarCambio();
        var nombre = nuevo.querySelector('[data-f="cap_nombre"]');
        if (nombre) {
          nombre.focus();
          nombre.select();
        }
        nuevo.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    }

    // Inicializar catálogo
    if (window.EDITOR.initCatalogo) window.EDITOR.initCatalogo();
    else if (catalogo && catalogo.init) catalogo.init();
    else if (typeof catalogo === "function") catalogo();

    // Cargar estado inicial
    (DATOS.capitulos || []).forEach(function (c) { Capitulo.crear(c, editor); });
    if (!editor.contCapitulos.querySelectorAll(".capitulo").length) {
      Capitulo.crear(null, editor);
    }
    renumerar();
    recalcular();

    // Restaurar borrador local si existe
    if (autosave && autosave.hayBorradorLocal()) {
      var draftBanner = document.getElementById("draft-banner");
      var btnRestore = document.getElementById("btn-restore-draft");
      var btnDiscard = document.getElementById("btn-discard-draft");

      if (draftBanner) CotizatStyles.set(draftBanner, "display", "flex");

      if (btnRestore) {
        btnRestore.addEventListener("click", function () {
          if (autosave) autosave.restaurarBorrador();
          if (draftBanner) CotizatStyles.set(draftBanner, "display", "none");
        });
      }

      if (btnDiscard) {
        btnDiscard.addEventListener("click", function () {
          if (autosave) autosave.limpiarBorradorLocal();
          if (draftBanner) CotizatStyles.set(draftBanner, "display", "none");
        });
      }
    } else if (window.BORRADOR_SERVIDOR && window.BORRADOR_SERVIDOR.capitulos && window.BORRADOR_SERVIDOR.capitulos.length) {
      // Borrador persistido por el autoguardado del servidor (más reciente
      // que el último guardado del presupuesto). Mismo banner que el local.
      var draftBannerS = document.getElementById("draft-banner");
      var draftTexto = document.getElementById("draft-banner-text");
      if (draftBannerS) {
        CotizatStyles.set(draftBannerS, "display", "flex");
        if (draftTexto) draftTexto.textContent = "El autoguardado tiene cambios sin guardar de esta sesión.";
        var btnRestoreS = document.getElementById("btn-restore-draft");
        if (btnRestoreS) {
          btnRestoreS.addEventListener("click", function () {
            editor.construirDesde(window.BORRADOR_SERVIDOR.capitulos);
            editor.marcarCambio();
            CotizatStyles.set(draftBannerS, "display", "none");
          });
        }
        var btnDiscardS = document.getElementById("btn-discard-draft");
        if (btnDiscardS) {
          btnDiscardS.addEventListener("click", function () {
            try {
              fetch("/presupuestos/" + editor.BUDGET_ID + "/borrador", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ capitulos: null, ts: Date.now() })
              }).catch(function () {});
            } catch (e) {}
            CotizatStyles.set(draftBannerS, "display", "none");
          });
        }
      }
    }

    // Listener para campos de totales
    document.addEventListener("input", function (e) {
      if (["impuesto_pct", "descuento_pct", "gastos_indirectos_pct", "imprevistos_pct", "transporte_monto", "otros_cargos_monto"].indexOf(e.target.name) !== -1) {
        recalcular();
        marcarCambio();
      }
      if (e.target.matches('[data-f="p_tipo_partida"], [data-f="p_seleccionada"], [data-f="p_coste_materiales"], [data-f="p_coste_mano_obra"], [data-f="p_coste_complementarios"], [data-f="p_coste_otros"], [data-f="p_desperdicio_pct"], [data-f="p_margen_pct"], [data-f="margen_real"]')) {
        recalcular();
        marcarCambio();
      }
      // Cuando se modifica el beneficio deseado, recalcular también actualiza el display en tiempo real
      if (e.target.matches('[data-f="p_margen_pct"]')) {
        // No recalcular precio automáticamente aquí; el usuario puede pulsar "Aplicar"
        // Pero si quiere efecto inmediato, lo manejamos en partida.js directamente
      }
    });

    // Listener para cambiar moneda
    var selMoneda = document.querySelector('select[name="moneda"]');
    if (selMoneda) {
      selMoneda.addEventListener("change", function () {
        window.COTIZAT_MONEDA_ACTIVA = selMoneda.value || "USD";
        renumerar();
        recalcular();
      });
    }

    cargarCatalogoDiferido();

    // Botón "Guardar ahora" del autosave: fuerza un envío inmediato al
    // servidor sin necesidad de pulsar el botón principal del formulario.
    var btnSaveNow = document.getElementById("btn-autosave-save-now");
    if (btnSaveNow && autosave) {
      btnSaveNow.addEventListener("click", function () {
        if (!editor.BUDGET_ID) {
          // Sin id de presupuesto: solo guardamos local
          autosave.guardarBorradorLocal();
          return;
        }
        btnSaveNow.disabled = true;
        var textoOriginal = btnSaveNow.textContent;
        btnSaveNow.textContent = "⏳ Guardando…";
        try { autosave.guardarBorradorServidor(); } catch (e) {}
        setTimeout(function () {
          btnSaveNow.disabled = false;
          btnSaveNow.textContent = textoOriginal;
        }, 1200);
      });
    }
  }

  // Esperar a que el DOM esté listo
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
