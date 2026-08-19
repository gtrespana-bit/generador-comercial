/* Ficha completa de Partida dentro del creador de presupuestos.
   Reutiliza PartidaCatalogoEditor y el endpoint de catálogo compartido. */
(function () {
  "use strict";

  var editor = window.EDITOR || {};
  var modal, form, root, api, wrapActual = null, fichaCatalogoActual = null;
  // Alcance elegido al aplicar cambios en una partida que ya existe en el
  // catálogo: "local" (solo este presupuesto) o "catalog" (también en BD).
  var scopeElegido = null;

  function $(id) { return document.getElementById(id); }
  function valor(name) { var el = form.elements[name]; return el ? el.value : ""; }
  function set(name, value) {
    var el = form.elements[name];
    if (!el) return;
    el.value = value == null ? "" : value;
  }
  function num(value) {
    // Mismo parseo robusto que FMT.parseNum (formato local con separador de
    // miles: «1.234,56» → 1234.56). Evita que un precio pegado desde Excel
    // se convierta en un número truncado.
    var s = String(value == null ? "" : value).trim().replace(/ /g, "").replace(/[$€Bs]/g, "");
    if (s === "") return 0;
    if (s.indexOf(",") !== -1 && s.indexOf(".") !== -1) {
      s = s.lastIndexOf(",") > s.lastIndexOf(".")
        ? s.replace(/\./g, "").replace(",", ".")
        : s.replace(/,/g, "");
    } else if (s.indexOf(",") !== -1) {
      s = s.replace(",", ".");
    }
    var n = parseFloat(s);
    return isFinite(n) ? n : 0;
  }
  function norm(value) {
    return String(value || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "");
  }
  function filasDescomposicion(datos) {
    var d = datos && datos.descomposicion;
    if (!d) return [];
    if (typeof d === "string") { try { d = JSON.parse(d); } catch (e) { return []; } }
    return Array.isArray(d) ? d : (Array.isArray(d.filas) ? d.filas : []);
  }

  function catalogoPorId(id) {
    var num = Number(id || 0);
    return num ? ((editor.CATALOGO || []).find(function (p) { return Number(p.id) === num; }) || null) : null;
  }

  function catalogoPara(datos) {
    return catalogoPorId(datos && datos.catalogo_id) || (function () {
      var nombre = norm(datos && datos.nombre);
      return nombre ? ((editor.CATALOGO || []).find(function (p) { return norm(p.nombre) === nombre; }) || null) : null;
    })();
  }

  function mostrarError(mensaje) {
    var caja = $("editor-partida-error");
    caja.textContent = mensaje || "";
    CotizatStyles.set(caja, "display", mensaje ? "" : "none");
  }

  function mostrarImagen(ruta) {
    var box = root.querySelector('[data-role="catalog-image-preview"]');
    var img = root.querySelector('[data-role="catalog-image"]');
    if (!box || !img) return;
    if (ruta) {
      img.src = window.cotizatArchivoUrl(ruta);
      CotizatStyles.set(box, "display", "flex");
    } else {
      img.removeAttribute("src");
      CotizatStyles.set(box, "display", "none");
    }
    var quitar = form.elements.quitar_imagen;
    if (quitar) quitar.checked = false;
    var archivo = form.elements.imagen;
    if (archivo) archivo.value = "";
  }

  function actualizarVistaProducto() {
    var vista = $("editor-producto-seleccionado");
    if (!vista || !form) return;
    var nombre = valor("linea_prod_nombre").trim();
    var precio = valor("linea_prod_precio");
    var unidad = valor("linea_prod_unidad").trim();
    var coste = valor("linea_prod_coste");
    var imagen = valor("linea_prod_imagen").trim();
    vista.hidden = !nombre;
    if (!nombre) return;
    var titulo = vista.querySelector("[data-producto-nombre]");
    var detalle = vista.querySelector("[data-producto-detalle]");
    var img = vista.querySelector("img");
    var icono = vista.querySelector(".editor-producto-icono");
    if (titulo) titulo.textContent = nombre;
    // Importes con código ISO: «$» a secas no distingue MXN de USD ni de COP.
    var money = function (v) {
      return window.FMT && window.FMT.fmt ? window.FMT.fmt(num(v)) : num(v).toFixed(2);
    };
    if (detalle) detalle.textContent = (precio !== "" ? "Venta " + money(precio) : "Venta sin definir") + (coste !== "" ? " · Coste " + money(coste) : "") + (unidad ? " / " + unidad : "");
    if (img) {
      var src = imagen ? (window.cotizatArchivoUrl(imagen)) : "";
      CotizatStyles.set(img, "display", src ? "" : "none");
      if (src) img.src = src; else img.removeAttribute("src");
      if (icono) CotizatStyles.set(icono, "display", src ? "none" : "grid");
    }
  }

  function cambiarTab(nombre) {
    modal.querySelectorAll("[data-partida-tab]").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.partidaTab === nombre);
    });
    modal.querySelectorAll("[data-partida-panel]").forEach(function (panel) {
      panel.classList.toggle("active", panel.dataset.partidaPanel === nombre);
    });
  }

  function addMedicion(datos) {
    datos = datos || {};
    var lista = $("editor-mediciones-list");
    var fila = document.createElement("div");
    fila.className = "editor-medicion-row";
    var concepto = document.createElement("input");
    concepto.type = "text";
    concepto.placeholder = "Concepto o zona";
    concepto.value = datos.concepto || "";
    concepto.dataset.medicion = "concepto";
    var cantidad = document.createElement("input");
    cantidad.type = "number";
    cantidad.step = "any";
    cantidad.min = "0";
    cantidad.placeholder = "Cantidad";
    cantidad.value = datos.cantidad == null ? "" : datos.cantidad;
    cantidad.dataset.medicion = "cantidad";
    var quitar = document.createElement("button");
    quitar.type = "button";
    quitar.className = "btn btn-sm btn-ghost";
    quitar.textContent = "✕";
    quitar.addEventListener("click", function () { fila.remove(); syncMedicionesEmpty(); });
    fila.appendChild(concepto);
    fila.appendChild(cantidad);
    fila.appendChild(quitar);
    lista.appendChild(fila);
    syncMedicionesEmpty();
    return fila;
  }

  function syncMedicionesEmpty() {
    CotizatStyles.set($("editor-mediciones-empty"), "display", $("editor-mediciones-list").children.length ? "none" : "flex");
  }

  function leerMediciones() {
    return Array.prototype.map.call($("editor-mediciones-list").querySelectorAll(".editor-medicion-row"), function (fila) {
      return {
        concepto: fila.querySelector('[data-medicion="concepto"]').value,
        cantidad: num(fila.querySelector('[data-medicion="cantidad"]').value)
      };
    }).filter(function (m) { return m.concepto || m.cantidad; });
  }

  function actualizarSelectorCatalogo(cat) {
    scopeElegido = null;
    var confirmScope = $("editor-save-scope-confirm");
    if (confirmScope) confirmScope.hidden = true;
    var boton = $("editor-partida-save");
    if (boton) boton.textContent = (cat && cat.id) ? "✓ Aplicar cambios" : "✓ Crear y aplicar";
  }

  function cargar(datos) {
    fichaCatalogoActual = catalogoPara(datos) || null;
    var cat = fichaCatalogoActual || {};
    var ficha = Object.assign({}, cat, {
      nombre: datos.nombre || cat.nombre || "",
      descripcion: datos.descripcion || cat.descripcion || "",
      unidad: datos.unidad || cat.unidad || "ud",
      precio: datos.precio != null ? datos.precio : (cat.precio || 0),
      categoria: datos.categoria || cat.categoria || "General",
      codigo_externo: datos.codigo_externo || cat.codigo_externo || cat.codigo || ""
    });
    set("partida_catalogo_id", datos.catalogo_id || cat.id || "");
    actualizarSelectorCatalogo(fichaCatalogoActual);
    set("nombre", ficha.nombre);
    set("categoria", ficha.categoria);
    set("subcategoria", ficha.subcategoria || "");
    set("apartado", ficha.apartado || "");
    set("unidad", ficha.unidad);
    set("codigo_externo", ficha.codigo_externo || "");
    set("descripcion", ficha.descripcion);
    // El campo «Precio de venta» es SOLO el precio de la partida (base).
    // El total de la línea = base + producto, y la línea ya trae el producto
    // sumado en `datos.precio` (p_precio). Si se cargara el total aquí, al
    // guardar se sumaría el producto dos veces y el precio se inflaría en
    // cada edición. Se resta el precio del producto para quedarse con la base.
    var precioBase = num(ficha.precio) - num(datos.prod_precio);
    set("precio_unitario", Math.max(0, precioBase).toFixed(2));
    set("codigo_interno", ficha.codigo_interno || ficha.codigo || "");
    set("proveedor", ficha.proveedor || "");
    set("tiempo_estimado_horas", ficha.tiempo_estimado_horas);
    set("rendimiento", ficha.rendimiento || "");
    set("desperdicio_recomendado_pct", ficha.desperdicio_recomendado_pct != null ? ficha.desperdicio_recomendado_pct : (datos.desperdicio_pct || 0));
    set("notas_tecnicas", ficha.notas_tecnicas || "");
    mostrarImagen(ficha.imagen || "");

    var filas = filasDescomposicion(datos);
    if (!filas.length) filas = filasDescomposicion(cat);
    api.cargar(filas);

    set("linea_cantidad", datos.cantidad == null ? 1 : datos.cantidad);
    set("linea_tipo", datos.tipo_partida || "included");
    // Las partidas incluidas / provisionales / sujetas a medición están
    // seleccionadas por defecto; solo opcionales y alternativas pueden
    // quedar sin seleccionar de forma explícita.
    var tipoLinea = datos.tipo_partida || "included";
    var seleccionada = datos.seleccionada === true ||
      (["included", "provisional", "measurement"].indexOf(tipoLinea) !== -1 && datos.seleccionada !== false);
    set("linea_seleccionada", seleccionada ? "1" : "0");
    set("linea_grupo_alternativa", datos.grupo_alternativa || "");
    set("linea_desperdicio", datos.desperdicio_pct || 0);
    set("linea_margen", datos.margen_pct || 0);
    set("linea_prod_nombre", datos.prod_nombre || "");
    set("linea_prod_precio", datos.prod_precio || "");
    set("linea_prod_coste", datos.prod_coste || "");
    set("linea_prod_unidad", datos.prod_unidad || "");
    set("linea_prod_categoria", datos.prod_categoria || "");
    set("linea_prod_imagen", datos.prod_imagen || "");
    actualizarVistaProducto();

    $("editor-mediciones-list").replaceChildren();
    (datos.mediciones || []).forEach(addMedicion);
    syncMedicionesEmpty();

    var cype = !!datos.tiene_descomposicion_cype;
    var note = $("editor-partida-cype-note");
    CotizatStyles.set(note, "display", cype ? "" : "none");
    note.textContent = cype ? "📐 Esta partida conserva su matriz original. Los recursos que edites aquí se actualizarán sin eliminar su trazabilidad técnica." : "";
    $("titulo-editor-partida").textContent = datos.nombre ? "Editar · " + datos.nombre : "Nueva partida";
    actualizarSelectorCatalogo(fichaCatalogoActual);
    mostrarError("");
    cambiarTab("ficha");
  }

  function abrir(wrap, pestañaInicial) {
    if (!wrap) return;
    wrapActual = wrap;
    cargar(editor.Partida.leerPartida(wrap));
    if (pestañaInicial) cambiarTab(pestañaInicial);
    modal.classList.add("open");
    document.body.classList.add("modal-open");
    setTimeout(function () { var el = form.elements.nombre; if (el) el.focus(); }, 80);
  }

  function cerrar() {
    modal.classList.remove("open");
    document.body.classList.remove("modal-open");
    wrapActual = null;
  }

  function costesDeFilas(filas) {
    var costes = { materiales: 0, mano_obra: 0, complementarios: 0, otros: 0 };
    filas.forEach(function (f) {
      // Cada importe de recurso se redondea a 2 decimales igual que el
      // servidor (Rendimiento × Precio unitario, ROUND_HALF_UP).
      var importe = f.importe != null && f.importe !== ""
        ? num(f.importe)
        : redondear2(num(f.rendimiento) * num(f.precio));
      var cat = costes.hasOwnProperty(f.categoria) ? f.categoria : "otros";
      costes[cat] = redondear2(costes[cat] + importe);
    });
    return costes;
  }

  function redondear2(v) {
    return Math.round((v + Number.EPSILON) * 100) / 100;
  }

  function fusionarCype(originales, editadas) {
    // Fusiona los recursos editados en el modal dentro de la matriz de descompuesto
    // original, conservando intactas las filas no editables (encabezado,
    // grupos, subtotales y total). Reglas:
    //   · Un recurso original se sustituye por su versión editada si coincide
    //     por código (o por descripción cuando no hay código).
    //   · Si un recurso original no tiene correspondencia (el usuario lo
    //     eliminó o lo renombró) se descarta, NUNCA se rellena con otra fila:
    //     rellenar con la primera pendiente duplicaba recursos y mezclaba
    //     descripciones y precios.
    //   · Los recursos nuevos (sin original) se añaden al final.
    var pendientes = editadas.slice();
    var resultado = [];
    originales.forEach(function (fila) {
      if ((fila.tipo || "") !== "recurso") {
        resultado.push(fila);
        return;
      }
      var indice = pendientes.findIndex(function (nueva) {
        return (nueva.codigo && norm(nueva.codigo) === norm(fila.codigo)) ||
          (!nueva.codigo && norm(nueva.descripcion) === norm(fila.descripcion));
      });
      if (indice < 0) return;
      var nueva = pendientes.splice(indice, 1)[0];
      resultado.push(Object.assign({}, fila, nueva, {
        numero: fila.numero,
        celdas: fila.celdas,
        formulas: fila.formulas
      }));
    });
    return resultado.concat(pendientes);
  }

  function actualizarCatalogoLocal(partida) {
    if (editor.Catalogo && editor.Catalogo.fusionarEnIndice) {
      editor.Catalogo.fusionarEnIndice(partida);
    } else {
      var indice = (editor.CATALOGO || []).findIndex(function (p) { return Number(p.id) === Number(partida.id); });
      if (indice < 0) editor.CATALOGO.push(partida);
      else Object.assign(editor.CATALOGO[indice], partida);
    }
  }

  async function guardar(event) {
    event.preventDefault();
    if (!wrapActual) return;
    if (!valor("nombre").trim()) {
      mostrarError("Escribe el nombre de la partida.");
      cambiarTab("ficha");
      return;
    }
    var boton = $("editor-partida-save");
    boton.disabled = true;
    boton.textContent = "Guardando…";
    mostrarError("");
    try {
      var actual = editor.Partida.leerPartida(wrapActual);
      var fichaGuardada = null;
      var guardarCatalogo = false;

      // Si la partida ya existe en el catálogo, preguntamos rápido al usuario
      // si aplica solo a este presupuesto o también a la base de datos.
      if (fichaCatalogoActual && fichaCatalogoActual.id) {
        if (scopeElegido == null) {
          boton.disabled = false;
          boton.textContent = "✓ Aplicar cambios";
          var confirmScope = $("editor-save-scope-confirm");
          if (confirmScope) confirmScope.hidden = false;
          return;
        }
        guardarCatalogo = scopeElegido === "catalog";
      } else {
        // Partida nueva: se guarda sola en el catálogo como partida nueva.
        guardarCatalogo = true;
      }
      if (guardarCatalogo) {
        var cuerpo = new FormData(form);
        // El formulario está en la moneda del presupuesto; el catálogo se
        // guarda en la moneda base. El servidor necesita el contexto para
        // deshacer la conversión (y devolver la ficha ya convertida).
        cuerpo.set("moneda", window.COTIZAT_MONEDA_ACTIVA || "");
        cuerpo.set("tasa", window.COTIZAT_TASA_ACTIVA || "");
        var response = await fetch("/partidas/guardar-desde-presupuesto", { method: "POST", body: cuerpo });
        var data = await response.json();
        if (!data.ok) throw new Error(data.error || "No se pudo guardar la partida en el catálogo.");
        fichaGuardada = data.partida;
        fichaCatalogoActual = fichaGuardada;
        actualizarCatalogoLocal(fichaGuardada);
      }

      var filasEditadas = fichaGuardada ? filasDescomposicion(fichaGuardada) : api.obtenerFilas();
      var filasOriginales = filasDescomposicion(actual);
      var filasFinales = actual.tiene_descomposicion_cype ? fusionarCype(filasOriginales, filasEditadas) : filasEditadas;
      var costes = fichaGuardada || costesDeFilas(filasEditadas);
      var completos = Object.assign({}, actual, {
        catalogo_id: fichaGuardada ? fichaGuardada.id : (function () {
          var nombre = norm(valor("nombre"));
          if (!nombre) return "";
          var maestra = actual.catalogo_id ? catalogoPorId(actual.catalogo_id) : null;
          if (maestra && norm(maestra.nombre) === nombre) return actual.catalogo_id;
          var porNombre = (editor.CATALOGO || []).find(function (p) { return norm(p.nombre) === nombre; });
          return porNombre ? String(porNombre.id) : "";
        })(),
        nombre: fichaGuardada ? fichaGuardada.nombre : valor("nombre"),
        descripcion: fichaGuardada ? fichaGuardada.descripcion : valor("descripcion"),
        unidad: fichaGuardada ? fichaGuardada.unidad : valor("unidad"),
        precio: num(valor("precio_unitario")) + (valor("linea_prod_nombre").trim() ? num(valor("linea_prod_precio")) : 0),
        precio_base: num(valor("precio_unitario")),
        categoria: fichaGuardada ? fichaGuardada.categoria : valor("categoria"),
        subcategoria: fichaGuardada ? fichaGuardada.subcategoria : valor("subcategoria"),
        apartado: fichaGuardada ? fichaGuardada.apartado : valor("apartado"),
        codigo_interno: fichaGuardada ? fichaGuardada.codigo_interno : valor("codigo_interno"),
        codigo_externo: fichaGuardada ? fichaGuardada.codigo_externo : valor("codigo_externo"),
        proveedor: fichaGuardada ? fichaGuardada.proveedor : valor("proveedor"),
        tiempo_estimado_horas: fichaGuardada ? fichaGuardada.tiempo_estimado_horas : num(valor("tiempo_estimado_horas")),
        rendimiento: fichaGuardada ? fichaGuardada.rendimiento : valor("rendimiento"),
        notas_tecnicas: fichaGuardada ? fichaGuardada.notas_tecnicas : valor("notas_tecnicas"),
        imagen_partida: fichaGuardada ? fichaGuardada.imagen : actual.imagen_partida,
        cantidad: num(valor("linea_cantidad")),
        tipo_partida: valor("linea_tipo"),
        seleccionada: valor("linea_seleccionada") === "1",
        grupo_alternativa: valor("linea_grupo_alternativa"),
        desperdicio_pct: num(valor("linea_desperdicio")),
        margen_pct: num(valor("linea_margen")),
        coste_materiales: num(costes.coste_materiales != null ? costes.coste_materiales : costes.materiales),
        coste_mano_obra: num(costes.coste_mano_obra != null ? costes.coste_mano_obra : costes.mano_obra),
        coste_complementarios: num(costes.coste_complementarios != null ? costes.coste_complementarios : costes.complementarios),
        coste_otros: num(costes.coste_otros != null ? costes.coste_otros : costes.otros),
        mediciones: leerMediciones(),
        prod_nombre: valor("linea_prod_nombre"),
        prod_precio: valor("linea_prod_precio"),
        prod_coste: valor("linea_prod_coste"),
        prod_unidad: valor("linea_prod_unidad"),
        prod_categoria: valor("linea_prod_categoria"),
        prod_imagen: valor("linea_prod_imagen"),
        // Las opciones de producto alternativas se conservan intactas al
        // abrir/cerrar la ficha (se editan en otra sección de los detalles).
        productos_opciones: valor("linea_prod_nombre").trim() ? (actual.productos_opciones || []) : [],
        descomposicion: { origen: actual.tiene_descomposicion_cype ? "cype" : "manual", filas: filasFinales }
      });
      var nuevo = editor.Partida.reemplazarPartida(wrapActual, completos, editor);
      cerrar();
      if (nuevo) nuevo.scrollIntoView({ behavior: "smooth", block: "center" });
      var flash = $("undo-flash");
      if (flash) {
        flash.textContent = fichaGuardada ? "✓ Partida y catálogo actualizados" : "✓ Partida actualizada en este presupuesto";
        flash.classList.add("show");
        setTimeout(function () { flash.classList.remove("show"); }, 3500);
      }
    } catch (error) {
      mostrarError(error.message || "No se pudieron aplicar los cambios.");
    } finally {
      boton.disabled = false;
      boton.textContent = "✓ Aplicar cambios";
    }
  }

  function init() {
    modal = $("modal-editor-partida");
    form = $("form-editor-partida");
    if (!modal || !form || !window.PartidaCatalogoEditor) return;
    root = form.querySelector("[data-partida-catalogo-editor]");
    api = window.PartidaCatalogoEditor.mount(root);
    // Beneficio % sobre coste <-> Precio (sincronía en modal)
    (function(){
      var ben = form.elements.linea_margen;
      var precio = form.elements.precio_unitario;
      var desperd = form.elements.linea_desperdicio;
      if (!ben || !precio || !root) return;
      var t=null;
      function costeDirecto(){
        var el = root.querySelector('[data-total="directo"]');
        var c = 0;
        if (el) {
          var txt = (el.textContent||"").replace(/\./g,"").replace(",",".");
          c = parseFloat(txt.replace(/[^0-9.-]/g,""))||0;
          if (!c) {
            // fallback parse con formato es-VE
            c = num(el.textContent);
          }
        }
        // fallback via api si no hay total
        if (!c && api && api.obtenerFilas) {
          try {
            var filas = api.obtenerFilas();
            var sum = 0;
            filas.forEach(function(f){ sum += num(f.importe != null ? f.importe : num(f.rendimiento)*num(f.precio)); });
            c = sum;
          } catch(e){}
        }
        var d = desperd ? num(desperd.value) : 0;
        return c * (1 + d/100);
      }
      ben.addEventListener('input', function(){
        clearTimeout(t);
        t=setTimeout(function(){
          var coste = costeDirecto();
          if (coste <= 0) return;
          var pct = num(ben.value);
          if (!isFinite(pct)) return;
          var nuevo = coste * (1 + pct/100);
          precio.value = nuevo.toFixed(2);
          precio.dispatchEvent(new Event('input',{bubbles:true}));
        }, 320);
      });
      // Si cambia el precio manual, el hint del catálogo ya se actualiza vía calcular()
    })();
    form.addEventListener("submit", guardar);
    $("editor-add-medicion").addEventListener("click", function () {
      var fila = addMedicion({});
      fila.querySelector("input").focus();
    });
    modal.querySelectorAll("[data-partida-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () { cambiarTab(btn.dataset.partidaTab); });
    });
    modal.querySelectorAll("[data-close]").forEach(function (btn) { btn.addEventListener("click", cerrar); });

    // Confirmación rápida de alcance para partidas ya existentes en el catálogo
    var confirmScope = $("editor-save-scope-confirm");
    if (confirmScope) {
      confirmScope.querySelectorAll("[data-scope]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          scopeElegido = btn.dataset.scope;
          confirmScope.hidden = true;
          form.requestSubmit();
        });
      });
    }

    var btnQuitarModalProd = $("editor-btn-quitar-producto");
    if (btnQuitarModalProd) {
      btnQuitarModalProd.addEventListener("click", function (evt) {
        evt.stopPropagation();
        if (confirm("¿Seguro que deseas eliminar este producto de la partida?")) {
          set("linea_prod_nombre", "");
          set("linea_prod_precio", "");
          set("linea_prod_coste", "");
          set("linea_prod_unidad", "");
          set("linea_prod_categoria", "");
          set("linea_prod_imagen", "");
          if (actual) actual.productos_opciones = [];
          actualizarVistaProducto();
          editor.marcarCambio();
        }
      });
    }

    ["linea_prod_nombre", "linea_prod_coste", "linea_prod_unidad", "linea_prod_imagen"].forEach(function (name) {
      var campo = form.elements[name];
      if (campo) campo.addEventListener("input", actualizarVistaProducto);
    });
    var prodPrecio = form.elements.linea_prod_precio;
    if (prodPrecio) {
      prodPrecio.addEventListener("input", function () {
        // El precio base de la partida no cambia al editar el producto:
        // el total de la línea se calcula al guardar como base + producto.
        actualizarVistaProducto();
        editor.marcarCambio();
      });
    }

    // Autocompletado de productos en la pestaña «Producto asociado»:
    // al escribir el nombre, muestra los productos del catálogo para elegir.
    (function initProductoAutocomplete() {
      var input = form.elements.linea_prod_nombre;
      if (!input || !editor.CATALOGO_UTILS) return;

      input.setAttribute("autocomplete", "off");
      var wrap = document.createElement("div");
      CotizatStyles.setCssText(wrap, "position:relative; display:flex; width:100%;");
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      CotizatStyles.set(input, "flex", "1");
      CotizatStyles.set(input, "minWidth", "0");

      var dropdown = null;
      function cerrar() {
        if (dropdown) { dropdown.remove(); dropdown = null; }
      }
      function posicionar() {
        if (!dropdown) return;
        var r = input.getBoundingClientRect();
        CotizatStyles.set(dropdown, "top", (r.bottom + 4) + "px");
        CotizatStyles.set(dropdown, "left", r.left + "px");
        CotizatStyles.set(dropdown, "width", r.width + "px");
      }
      function mostrar() {
        var query = input.value.trim();
        var productos = editor.PRODUCTOS || [];
        var catSug = ((form.elements.linea_prod_categoria || {}).value || "").trim();
        var campos = ["nombre", "descripcion", "marca", "modelo", "sku", "proveedor", "categoria", "color", "acabado", "formato"];
        var matches = editor.CATALOGO_UTILS.buscarEnCatalogo(productos, query, campos, catSug);
        if (!matches.length && query) {
          matches = editor.CATALOGO_UTILS.buscarEnCatalogo(productos, query, campos, "");
        }
        cerrar();
        if (!matches.length) return;

        dropdown = document.createElement("div");
        dropdown.className = "autocomplete-suggestions";
        CotizatStyles.setCssText(dropdown, "position:fixed; z-index:1300; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:240px; overflow-y:auto; box-shadow:var(--shadow-lg);");

        matches.forEach(function (item) {
          var sug = document.createElement("div");
          sug.className = "suggestion-item";
          CotizatStyles.setCssText(sug, "padding:8px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.82rem; display:flex; align-items:center; gap:9px;");
          if (item.imagen) {
            var thumb = document.createElement("img");
            thumb.className = "suggestion-thumb";
            thumb.src = window.cotizatArchivoUrl(item.imagen);
            thumb.alt = "";
            sug.appendChild(thumb);
          }
          var main = document.createElement("div");
          main.className = "suggestion-main";
          var title = document.createElement("div");
          title.className = "suggestion-title";
          CotizatStyles.set(title, "fontWeight", "600");
          title.textContent = item.nombre;
          main.appendChild(title);
          var meta = [item.marca, item.modelo, item.sku, item.categoria].filter(Boolean).join(" · ");
          var fecha = editor.FMT ? editor.FMT.fechaCorta(item.fecha_precio) : "";
          main.appendChild(editor.FMT.h("div", "suggestion-meta", meta + (fecha ? " · precio " + fecha : "")));
          sug.appendChild(main);
          var precio = document.createElement("span");
          CotizatStyles.setCssText(precio, "color:var(--accent); font-size:.78em; white-space:nowrap;");
          precio.textContent = (item.precio || 0).toFixed(2) + " $ / " + (item.unidad || "ud");
          sug.appendChild(precio);

          sug.addEventListener("mousedown", function (evt) { evt.preventDefault(); });
          sug.addEventListener("click", function (evt) {
            evt.stopPropagation();
            set("linea_prod_nombre", item.nombre);
            set("linea_prod_precio", item.precio || 0);
            set("linea_prod_coste", item.coste != null ? item.coste : "");
            set("linea_prod_unidad", item.unidad || "");
            set("linea_prod_categoria", item.categoria || "");
            set("linea_prod_imagen", item.imagen || "");
            // El precio base de la partida NO se toca: el total de la
            // línea se calcula al guardar como base + producto.
            actualizarVistaProducto();
            cerrar();
            editor.marcarCambio();
          });
          sug.addEventListener("mouseenter", function () { CotizatStyles.set(sug, "background", "var(--bg)"); });
          sug.addEventListener("mouseleave", function () { CotizatStyles.set(sug, "background", "none"); });
          dropdown.appendChild(sug);
        });

        document.body.appendChild(dropdown);
        posicionar();
      }

      input.addEventListener("input", function () {
        editor.marcarCambio();
        mostrar();
      });
      input.addEventListener("focus", mostrar);
      input.addEventListener("keydown", function (evt) {
        if (evt.key === "Escape") cerrar();
        if (evt.key === "Enter") { evt.preventDefault(); cerrar(); }
      });
      var panel = input.closest(".partida-tab-panel");
      if (panel) panel.addEventListener("scroll", posicionar);
      window.addEventListener("resize", posicionar);
      document.addEventListener("click", function (evt) {
        if (dropdown && !wrap.contains(evt.target) && !dropdown.contains(evt.target)) cerrar();
      });
    })();

    editor.abrirEditorPartida = abrir;
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
