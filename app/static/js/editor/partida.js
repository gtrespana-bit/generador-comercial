/* ============================================================================
   Editor — módulo de Partida

   Cada partida vive en un contenedor `.partida-wrap` con dos filas:
     · `.partida-row`     fila compacta (nombre, cantidad, unidad, precio, importe)
     · `.partida-details` panel expandible con descripción, mediciones, producto
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR = window.EDITOR || {};
  var Partida = (function () {

    // -------------------------------------------------------------------------
    // Constructores
    // -------------------------------------------------------------------------

    function crearElemento(tag, cls, texto) {
      var el = document.createElement(tag);
      if (cls) el.className = cls;
      if (texto !== undefined) el.textContent = texto;
      return el;
    }

    function crearInput(tipo, valor, placeholder, field, extra) {
      var el = document.createElement("input");
      el.type = tipo;
      if (valor !== undefined && valor !== null && valor !== "") el.value = valor;
      if (placeholder) el.placeholder = placeholder;
      if (field) el.dataset.f = field;
      if (extra) Object.keys(extra).forEach(function (k) {
        el.setAttribute(k, extra[k]);
      });
      return el;
    }

    function jsonSeguro(valor, defecto) {
      if (typeof valor === "string") {
        try { JSON.parse(valor); return valor; } catch (e) { return JSON.stringify(defecto); }
      }
      try { return JSON.stringify(valor == null ? defecto : valor); }
      catch (e) { return JSON.stringify(defecto); }
    }

    function quitarProductoDePartida(partidaWrap) {
      if (!partidaWrap) return;

      // 1. Limpiar campos primarios del producto
      ["p_prod_nombre", "p_prod_precio", "p_prod_coste", "p_prod_unidad", "p_prod_categoria", "p_prod_imagen_actual"].forEach(function (f) {
        var inp = partidaWrap.querySelector('[data-f="' + f + '"]');
        if (inp) inp.value = "";
      });
      var fileInp = partidaWrap.querySelector('input[type="file"][data-f="p_prod_imagen"]');
      if (fileInp) fileInp.value = "";

      // 2. Vaciar las opciones alternativas y su cache viva
      var jsonInp = partidaWrap.querySelector('[data-f="p_productos_opciones_json"]');
      if (jsonInp) jsonInp.value = "[]";
      partidaWrap._productosOpcionesCache = [];

      // 3. Restaurar el precio unitario total al precio base de la partida
      var baseEl = partidaWrap.querySelector('[data-f="p_precio_base"]');
      var precioInput = partidaWrap.querySelector('[data-f="p_precio"]');
      if (baseEl && precioInput) {
        var baseVal = parseFloat(baseEl.value) || 0;
        precioInput.value = baseVal.toFixed(2);
        precioInput.dispatchEvent(new Event("input", { bubbles: true }));
      }

      // 4. Actualizar componentes visuales de la partida
      var secOpciones = partidaWrap.querySelector(".productos-opciones-section");
      if (secOpciones) {
        secOpciones._opcionesCache = [];
        if (typeof secOpciones._renderOpciones === "function") {
          secOpciones._renderOpciones();
        }
      }

      // 5. Actualizar resumen de producto
      if (typeof partidaWrap._actualizarResumenProducto === "function") {
        partidaWrap._actualizarResumenProducto();
      }

      // 6. Disparar eventos globales de recalculo y guardado
      try {
        var ed = editor || window.EDITOR || {};
        if (ed.recalcular) ed.recalcular();
        if (ed.marcarCambio) ed.marcarCambio();
      } catch (e) {}
    }
    //
    // Cada partida puede tener N productos a elegir. Internamente:
    //   · El campo primario (`p_prod_nombre`, `p_prod_precio`...) sigue
    //     representando la primera opción visible en el editor y la que se
    //     muestra por defecto si no hay ninguna marcada.
    //   · Las opciones adicionales viven en un input oculto
    //     `p_productos_opciones_json` con la forma:
    //       [{ id, nombre, precio, coste, unidad, marca, sku, color,
    //          acabado, descripcion, imagen, categoria, seleccionado, orden }]
    //
    // La UI que muestra, edita y selecciona estas opciones está en
    // `crearSeccionProductosOpciones` y se actualiza con
    // `actualizarSeccionProductosOpciones` cada vez que el usuario toca
    // algo. El estado se serializa siempre a JSON dentro de la partida.

    function leerProductosOpciones(wrap) {
      var input = wrap && wrap.querySelector ? wrap.querySelector('[data-f="p_productos_opciones_json"]') : null;
      if (!input) return [];
      try {
        var lista = JSON.parse(input.value || "[]");
        if (!Array.isArray(lista)) return [];
        return lista.map(function (op, i) {
          return {
            id: op && op.id ? op.id : null,
            nombre: String((op && op.nombre) || "").trim(),
            precio: (op && typeof op.precio !== "undefined" && op.precio !== null && op.precio !== "") ? op.precio : 0,
            coste: (op && typeof op.coste !== "undefined" && op.coste !== null && op.coste !== "") ? op.coste : "",
            unidad: String((op && op.unidad) || "").trim(),
            categoria: String((op && op.categoria) || "").trim(),
            marca: String((op && op.marca) || "").trim(),
            modelo: String((op && op.modelo) || "").trim(),
            sku: String((op && op.sku) || "").trim(),
            color: String((op && op.color) || "").trim(),
            acabado: String((op && op.acabado) || "").trim(),
            descripcion: String((op && op.descripcion) || "").trim(),
            imagen: String((op && op.imagen) || "").trim(),
            seleccionado: !!(op && op.seleccionado),
            orden: (op && typeof op.orden === "number") ? op.orden : i,
          };
        });
      } catch (e) {
        return [];
      }
    }

    function sanitizarOpcionesParaGuardar(lista) {
      if (!Array.isArray(lista)) return [];
      return lista.map(function (op, i) {
        return {
          id: op && op.id ? op.id : null,
          nombre: String((op && op.nombre) || "").trim(),
          precio: (op && op.precio !== "" && op.precio != null) ? op.precio : 0,
          coste: (op && op.coste !== "" && op.coste != null) ? op.coste : "",
          unidad: String((op && op.unidad) || "").trim(),
          categoria: String((op && op.categoria) || "").trim(),
          marca: String((op && op.marca) || "").trim(),
          modelo: String((op && op.modelo) || "").trim(),
          sku: String((op && op.sku) || "").trim(),
          color: String((op && op.color) || "").trim(),
          acabado: String((op && op.acabado) || "").trim(),
          descripcion: String((op && op.descripcion) || "").trim(),
          imagen: String((op && op.imagen) || "").trim(),
          seleccionado: !!(op && op.seleccionado),
          orden: typeof (op && op.orden) === "number" ? op.orden : i,
        };
      });
    }

    function guardarProductosOpciones(wrap, lista) {
      var input = wrap && wrap.querySelector ? wrap.querySelector('[data-f="p_productos_opciones_json"]') : null;
      if (!input) return;
      try {
        input.value = JSON.stringify(sanitizarOpcionesParaGuardar(lista));
      } catch (e) {
        input.value = "[]";
      }
    }

    // Campos del catálogo de productos por los que se busca en el
    // autocompletado. Se comparten entre el producto primario de la ficha y
    // las opciones múltiples para que ambos busquen exactamente igual.
    var CAMPOS_BUSQUEDA_PRODUCTO = [
      "nombre", "descripcion", "marca", "modelo", "sku",
      "proveedor", "categoria", "color", "acabado", "formato"
    ];

    /**
     * Conecta un `input` de texto al buscador del catálogo de productos.
     *
     * Es el mismo comportamiento que ya tenía el campo «Producto
     * presupuestado» de la ficha, extraído aquí para poder reutilizarlo en
     * cada tarjeta de «Productos para elegir». Antes esas tarjetas eran
     * campos de texto en crudo, así que añadir un segundo artículo obligaba
     * a teclearlo entero en lugar de buscarlo en la base de productos.
     *
     * opciones:
     *   · contenedor      elemento posicionado donde se cuelga el desplegable
     *   · categoriaActual función que devuelve la categoría preferida
     *   · alElegir        callback(itemDelCatalogo)
     */
    function conectarBuscadorProductos(input, editorInst, opciones) {
      opciones = opciones || {};
      var ed = editorInst || editor || window.EDITOR || {};
      var FMT = (ed && ed.FMT) || editor.FMT || window.FMT;
      var utils = (ed && ed.CATALOGO_UTILS) || window.CATALOGO_UTILS;
      var contenedor = opciones.contenedor || input.parentNode;
      var dropdown = null;

      function cerrar() {
        if (dropdown) {
          dropdown.remove();
          dropdown = null;
        }
      }

      function buscar() {
        var productos = (ed && ed.PRODUCTOS) || (window.EDITOR && window.EDITOR.PRODUCTOS) || [];
        if (!utils || !utils.buscarEnCatalogo || !productos.length) return;
        var query = String(input.value || "").trim();
        var categoria = "";
        if (typeof opciones.categoriaActual === "function") {
          categoria = String(opciones.categoriaActual() || "").trim();
        }
        var matches = utils.buscarEnCatalogo(productos, query, CAMPOS_BUSQUEDA_PRODUCTO, categoria);
        // Si la categoría preferida deja la lista vacía, se repite la
        // búsqueda sobre todo el catálogo: es preferible mostrar resultados
        // de otra categoría a no mostrar nada.
        if (!matches.length) {
          matches = utils.buscarEnCatalogo(productos, query, CAMPOS_BUSQUEDA_PRODUCTO, "");
        }
        cerrar();
        if (!matches.length) return;

        dropdown = FMT.h("div", "autocomplete-suggestions");
        dropdown.style.cssText = "position:absolute; top:100%; left:0; right:0; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:240px; overflow-y:auto; z-index:1200; box-shadow:var(--shadow-lg); margin-top:4px; min-width:260px;";
        // No dejar que un clic dentro del desplegable llegue a la fila de la
        // partida (abriría la ficha y cerraría la lista sin seleccionar).
        dropdown.addEventListener("click", function (evt) { evt.stopPropagation(); });

        matches.forEach(function (item) {
          var sug = FMT.h("div", "suggestion-item");
          sug.style.cssText = "padding:8px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.82rem; display:flex; align-items:center; gap:9px;";
          if (item.imagen) {
            var thumb = FMT.h("img", "suggestion-thumb");
            thumb.src = item.imagen.indexOf("/") === 0 ? item.imagen : window.cotizatArchivoUrl(item.imagen);
            thumb.alt = "";
            sug.appendChild(thumb);
          }
          var main = FMT.h("div", "suggestion-main");
          var title = FMT.h("div", "suggestion-title", item.nombre);
          title.style.fontWeight = "600";
          main.appendChild(title);
          var meta = [item.marca, item.modelo, item.sku, item.categoria].filter(Boolean).join(" · ");
          var fecha = FMT.fechaCorta ? FMT.fechaCorta(item.fecha_precio) : "";
          main.appendChild(FMT.h("div", "suggestion-meta", meta + (fecha ? " · precio " + fecha : "")));
          sug.appendChild(main);
          var precio = FMT.h("span", null, (Number(item.precio) || 0).toFixed(2) + " $ / " + (item.unidad || "ud"));
          precio.style.cssText = "color:var(--accent); font-size:.78em; white-space:nowrap;";
          sug.appendChild(precio);

          sug.addEventListener("mousedown", function (evt) { evt.preventDefault(); });
          sug.addEventListener("click", function (evt) {
            evt.stopPropagation();
            cerrar();
            if (typeof opciones.alElegir === "function") opciones.alElegir(item);
          });
          sug.addEventListener("mouseenter", function () { sug.style.background = "var(--bg)"; });
          sug.addEventListener("mouseleave", function () { sug.style.background = "none"; });
          dropdown.appendChild(sug);
        });
        contenedor.appendChild(dropdown);
      }

      input.addEventListener("input", buscar);
      input.addEventListener("focus", buscar);
      input.addEventListener("keydown", function (evt) {
        if (evt.key === "Escape" || evt.key === "Enter") {
          if (evt.key === "Enter") evt.preventDefault();
          cerrar();
        }
      });
      document.addEventListener("click", function (evt) {
        if (dropdown && !contenedor.contains(evt.target)) cerrar();
      });

      return { cerrar: cerrar, buscar: buscar };
    }

    /**
     * Sección visible siempre (fuera del detalle oculto) que permite añadir
     * varios productos a una misma partida.
     *
     * - Siempre visible en la fila compacta de la partida.
     * - Plegable para no saturar cuando no hay opciones.
     * - Cache en memoria conserva los File de imagen sin perderlos al re-render.
     * - Cualquier cambio persiste en el input oculto p_productos_opciones_json
     *   y dispara recalcular() + marcarCambio().
     */
    function crearSeccionProductosOpciones(partidaWrap, datos, editorInstParam) {
      var ed = editorInstParam || editor || window.EDITOR || {};
      var FMT = (ed && ed.FMT) || editor.FMT || window.FMT;
      var CAT_UTILS = (ed && ed.CATALOGO_UTILS) || window.CATALOGO_UTILS;

      if (!partidaWrap._productosOpcionesGroupId) {
        partidaWrap._productosOpcionesGroupId = "grp_" + Math.random().toString(36).slice(2, 8);
      }
      var groupId = partidaWrap._productosOpcionesGroupId;

      // Cache viva: incluye _imagen_file y _objUrl que NO se serializan.
      var opcionesCache = [];
      try {
        var baseLista = leerProductosOpciones(partidaWrap);
        // Si viene de datos iniciales pero el hidden aún no tiene valor (partida nueva),
        // usamos datos.productos_opciones si existe.
        if ((!baseLista || !baseLista.length) && datos && Array.isArray(datos.productos_opciones) && datos.productos_opciones.length) {
          baseLista = datos.productos_opciones;
        }
        opcionesCache = (baseLista || []).map(function (op) {
          var c = {
            id: op.id || null,
            nombre: op.nombre || "",
            precio: op.precio != null ? op.precio : 0,
            coste: op.coste != null ? op.coste : "",
            unidad: op.unidad || "",
            categoria: op.categoria || "",
            marca: op.marca || "",
            modelo: op.modelo || "",
            sku: op.sku || "",
            color: op.color || "",
            acabado: op.acabado || "",
            descripcion: op.descripcion || "",
            imagen: op.imagen || "",
            seleccionado: !!op.seleccionado,
            orden: typeof op.orden === "number" ? op.orden : 0,
            _imagen_file: null,
            _objUrl: null
          };
          return c;
        });
      } catch (e) {
        opcionesCache = [];
      }

      // Si ya había cache en el wrap (tras duplicado/reemplazo), reutilizar archivos.
      if (partidaWrap._productosOpcionesCache && Array.isArray(partidaWrap._productosOpcionesCache)) {
        // Mezclar File preservados si coinciden por índice y nombre
        opcionesCache.forEach(function (op, i) {
          var prev = partidaWrap._productosOpcionesCache[i];
          if (prev && prev._imagen_file && !op._imagen_file) {
            op._imagen_file = prev._imagen_file;
            op._objUrl = prev._objUrl || null;
          }
        });
      }

      var sec = FMT.h("div", "productos-opciones-section");
      // Estilo para que sea visible fuera del detalle
      sec.style.cssText = "margin:0 0.65rem 0.6rem; border:1px solid var(--border); border-radius:10px; background:var(--bg); padding:10px 12px;";

      // Header
      var header = FMT.h("div", "productos-opciones-header");
      header.style.cssText = "display:flex; align-items:center; gap:8px; flex-wrap:wrap;";
      var titleLeft = FMT.h("div", "productos-opciones-title");
      titleLeft.style.cssText = "display:flex; align-items:center; gap:8px; flex:1; min-width:180px;";
      var icon = FMT.h("span", "", "🧩");
      icon.style.fontSize = "1rem";
      var label = FMT.h("div", "detail-label", "Productos para elegir");
      label.style.cssText = "margin:0; font-weight:700; color:var(--text);";
      var countBadge = FMT.h("span", "productos-opciones-count");
      countBadge.style.cssText = "display:inline-flex; align-items:center; justify-content:center; min-width:22px; height:20px; padding:0 6px; border-radius:999px; background:var(--accent-soft); color:var(--accent); border:1px solid var(--accent-light); font-size:0.72rem; font-weight:700;";
      countBadge.textContent = String(opcionesCache.length);
      titleLeft.appendChild(icon);
      titleLeft.appendChild(label);
      titleLeft.appendChild(countBadge);
      header.appendChild(titleLeft);

      var headerActions = FMT.h("div", "productos-opciones-header-actions");
      headerActions.style.cssText = "display:flex; gap:6px; align-items:center; flex-wrap:wrap;";

      var toggleBtn = FMT.h("button", "btn btn-xs", opcionesCache.length ? "▾ Ocultar" : "▸ Mostrar (" + opcionesCache.length + ")");
      toggleBtn.type = "button";
      toggleBtn.title = "Plegar/desplegar opciones";
      var btnAdd = FMT.h("button", "btn btn-xs btn-primary", "+ Añadir producto");
      btnAdd.type = "button";
      // Evitar que el clic burbujee al .partida-row (que abriría la ficha)
      [toggleBtn, btnAdd].forEach(function (b) {
        b.addEventListener("click", function (e) { e.stopPropagation(); });
      });

      headerActions.appendChild(toggleBtn);
      headerActions.appendChild(btnAdd);
      header.appendChild(headerActions);
      sec.appendChild(header);

      // Body plegable
      var body = FMT.h("div", "productos-opciones-body");
      body.style.cssText = "margin-top:10px;";

      var hint = FMT.h("p", "hint",
        "Añade varios productos candidatos para esta partida. El cliente verá las opciones en el PDF. Marca uno como elegido si ya decidió.");
      hint.style.margin = "0 0 8px 0";
      body.appendChild(hint);

      var lista = FMT.h("div", "productos-opciones-lista");
      body.appendChild(lista);

      var vacio = FMT.h("p", "hint productos-opciones-empty", "Sin opciones alternativas todavía. La partida usa solo el producto principal de arriba. Usa + Añadir producto para ofrecer alternativas.");
      vacio.style.cssText = "margin:6px 0 0 0; font-style:italic;";
      body.appendChild(vacio);
      sec.appendChild(body);

      // Estado colapsado inicial
      var collapsed = opcionesCache.length === 0;
      function aplicarColapsado(isCollapsed) {
        collapsed = !!isCollapsed;
        sec.classList.toggle("collapsed", collapsed);
        body.style.display = collapsed ? "none" : "";
        toggleBtn.textContent = collapsed ? "▸ Mostrar (" + opcionesCache.length + ")" : "▾ Ocultar";
      }
      aplicarColapsado(collapsed);

      toggleBtn.addEventListener("click", function () {
        aplicarColapsado(!collapsed);
      });

      function persistirYRecalcular() {
        guardarProductosOpciones(partidaWrap, opcionesCache);
        partidaWrap._productosOpcionesCache = opcionesCache;
        sec._opcionesCache = opcionesCache;
        countBadge.textContent = String(opcionesCache.length);
        if (!collapsed) {
          toggleBtn.textContent = "▾ Ocultar";
        } else {
          toggleBtn.textContent = "▸ Mostrar (" + opcionesCache.length + ")";
        }
        try { (ed.recalcular || editor.recalcular || function () { })(); } catch (e) {}
        try { (ed.marcarCambio || editor.marcarCambio || function () { })(); } catch (e) {}
      }

      function sincronizarPrimarioSiSeleccionada(op) {
        if (!op || !op.seleccionado) return;
        var precioInput = partidaWrap.querySelector('[data-f="p_precio"]');
        var prodNombreInput = partidaWrap.querySelector('[data-f="p_prod_nombre"]');
        var prodPrecioInput = partidaWrap.querySelector('[data-f="p_prod_precio"]');
        var prodUnidadInput = partidaWrap.querySelector('[data-f="p_prod_unidad"]');
        var prodImagenInput = partidaWrap.querySelector('[data-f="p_prod_imagen_actual"]');
        var baseEl = partidaWrap.querySelector('[data-f="p_precio_base"]');
        var base = baseEl ? parseFloat(baseEl.value) || 0 : 0;
        var nuevoPrecioProd = parseFloat(op.precio) || 0;
        if (precioInput) precioInput.value = (base + nuevoPrecioProd).toFixed(2);
        if (prodNombreInput) prodNombreInput.value = op.nombre || "";
        if (prodPrecioInput) prodPrecioInput.value = (nuevoPrecioProd || "").toString();
        if (prodUnidadInput) prodUnidadInput.value = op.unidad || "";
        if (prodImagenInput) prodImagenInput.value = op.imagen || "";
        if (partidaWrap._actualizarResumenProducto) partidaWrap._actualizarResumenProducto();
        if (precioInput) precioInput.dispatchEvent(new Event("input", { bubbles: true }));
      }

      function seleccionar(idx) {
        opcionesCache.forEach(function (o, i) { o.seleccionado = (i === idx); });
        var sel = opcionesCache[idx];
        if (sel) sincronizarPrimarioSiSeleccionada(sel);
        renderOpciones();
        persistirYRecalcular();
      }

      function eliminar(idx) {
        if (!confirm("¿Eliminar esta opción de producto?")) return;
        var op = opcionesCache[idx];
        if (op && op._objUrl) { try { URL.revokeObjectURL(op._objUrl); } catch (e) {} }
        var eraSeleccionado = op && op.seleccionado;
        opcionesCache.splice(idx, 1);
        if (opcionesCache.length === 0) {
          quitarProductoDePartida(partidaWrap);
          return;
        }
        if (eraSeleccionado && opcionesCache.length > 0) {
          opcionesCache[0].seleccionado = true;
          sincronizarPrimarioSiSeleccionada(opcionesCache[0]);
        }
        renderOpciones();
        persistirYRecalcular();
      }

      function srcImagenOpcion(op) {
        if (op._objUrl) return op._objUrl;
        if (op._imagen_file && op._imagen_file instanceof File) {
          try {
            op._objUrl = URL.createObjectURL(op._imagen_file);
            return op._objUrl;
          } catch (e) { return ""; }
        }
        if (op.imagen) {
          return window.cotizatArchivoUrl(op.imagen);
        }
        return "";
      }

      function crearTarjeta(op, idx) {
        var tarjeta = FMT.h("div", "producto-opcion-tarjeta");
        tarjeta.dataset.idx = String(idx);
        if (op.seleccionado) tarjeta.classList.add("seleccionada");
        tarjeta.style.cssText = "display:flex; gap:12px; align-items:flex-start; padding:8px; border:1px solid var(--border); border-radius:10px; margin-bottom:8px; background:var(--surface);";
        if (op.seleccionado) tarjeta.style.borderColor = "var(--accent)";

        // Foto clicable: mismo efecto que la casilla «Elegido».
        var fotoBtn = FMT.h("button", "producto-opcion-foto");
        fotoBtn.type = "button";
        fotoBtn.title = "Elegir este producto";
        fotoBtn.style.cssText = "flex:0 0 92px; width:92px; height:92px; padding:0; border:2px solid " + (op.seleccionado ? "var(--accent)" : "var(--border)") + "; border-radius:8px; overflow:hidden; background:var(--bg); cursor:pointer; display:grid; place-items:center;";
        var srcFoto = srcImagenOpcion(op);
        if (srcFoto) {
          var fotoImg = FMT.h("img", "producto-opcion-foto-img");
          fotoImg.src = srcFoto;
          fotoImg.alt = op.nombre || "Producto";
          fotoImg.style.cssText = "width:100%; height:100%; object-fit:cover; display:block;";
          fotoBtn.appendChild(fotoImg);
        } else {
          fotoBtn.appendChild(FMT.h("span", "", "▦"));
        }
        fotoBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          seleccionar(idx);
        });
        tarjeta.appendChild(fotoBtn);

        var cuerpoTarjeta = FMT.h("div", "producto-opcion-cuerpo");
        cuerpoTarjeta.style.cssText = "flex:1; min-width:0;";
        tarjeta.appendChild(cuerpoTarjeta);

        // Cabecera
        var head = FMT.h("div", "producto-opcion-head");
        head.style.cssText = "display:flex; align-items:center; gap:8px; flex-wrap:wrap;";

        var selLabel = FMT.h("label", "producto-opcion-seleccion");
        selLabel.style.cssText = "display:flex; align-items:center; gap:6px; cursor:pointer; font-size:0.78rem; font-weight:600; user-select:none;";
        var selRadio = document.createElement("input");
        selRadio.type = "radio";
        selRadio.name = "producto_opcion_sel_" + groupId;
        selRadio.checked = !!op.seleccionado;
        selRadio.title = "Marcar como producto elegido por el cliente";
        selRadio.addEventListener("change", function (e) {
          e.stopPropagation();
          seleccionar(idx);
        });
        selLabel.appendChild(selRadio);
        selLabel.appendChild(document.createTextNode("Elegido"));
        head.appendChild(selLabel);

        // Buscador del catálogo de productos. El input va dentro de un
        // contenedor posicionado para poder colgar el desplegable justo
        // debajo, igual que el campo «Producto presupuestado» de la ficha.
        var nombreWrap = FMT.h("div", "producto-opcion-buscador");
        nombreWrap.style.cssText = "position:relative; flex:1; min-width:180px; display:flex;";
        var nombreInput = FMT.crearInput("text", op.nombre || "", "Buscar producto en el catálogo…", null, { "data-opcion-campo": "nombre" });
        nombreInput.className = "producto-opcion-nombre";
        nombreInput.setAttribute("autocomplete", "off");
        nombreInput.title = "Escribe para buscar en la base de productos; también puedes teclear un producto nuevo.";
        nombreInput.style.cssText = "flex:1; min-width:0; padding:6px 8px; font-size:0.85rem;";
        nombreInput.addEventListener("click", function (e) { e.stopPropagation(); });
        nombreInput.addEventListener("input", function () {
          op.nombre = nombreInput.value;
          // Al teclear a mano se deja de estar vinculado a la ficha del
          // catálogo: es un producto nuevo hasta que se elija otro.
          op.id = null;
          persistirYRecalcular();
          if (op.seleccionado) sincronizarPrimarioSiSeleccionada(op);
        });
        nombreWrap.appendChild(nombreInput);
        head.appendChild(nombreWrap);

        // Rellena toda la tarjeta con la ficha elegida del catálogo.
        function aplicarProductoDelCatalogo(item) {
          op.id = item.id || null;
          op.nombre = item.nombre || "";
          op.precio = (item.precio != null && item.precio !== "") ? item.precio : 0;
          op.coste = (item.coste != null && item.coste !== "") ? item.coste : "";
          op.unidad = item.unidad || "";
          op.categoria = item.categoria || "";
          op.marca = item.marca || "";
          op.modelo = item.modelo || "";
          op.sku = item.sku || "";
          op.color = item.color || "";
          op.acabado = item.acabado || "";
          op.descripcion = item.descripcion || "";
          if (item.imagen) {
            op.imagen = item.imagen;
            // La imagen del catálogo sustituye a cualquier archivo suelto
            // que se hubiera cargado antes en esta tarjeta.
            if (op._objUrl) { try { URL.revokeObjectURL(op._objUrl); } catch (e) {} }
            op._objUrl = null;
            op._imagen_file = null;
          }
          // Se vuelve a pintar la tarjeta entera para reflejar todos los
          // campos (precio, marca, imagen…) de una sola vez.
          renderOpciones();
          persistirYRecalcular();
          if (op.seleccionado) sincronizarPrimarioSiSeleccionada(op);
        }

        conectarBuscadorProductos(nombreInput, ed, {
          contenedor: nombreWrap,
          categoriaActual: function () {
            var cat = partidaWrap.querySelector('[data-f="p_prod_categoria"]');
            return op.categoria || (cat ? cat.value : "");
          },
          alElegir: aplicarProductoDelCatalogo
        });

        var precioMini = FMT.crearInput("number", op.precio != null ? op.precio : "", "Precio", null, { "data-opcion-campo": "precio", step: "any", min: "0" });
        precioMini.style.cssText = "width:110px; padding:6px 8px; font-size:0.85rem;";
        precioMini.placeholder = "Precio";
        precioMini.addEventListener("click", function (e) { e.stopPropagation(); });
        precioMini.addEventListener("input", function () {
          op.precio = precioMini.value;
          persistirYRecalcular();
          if (op.seleccionado) sincronizarPrimarioSiSeleccionada(op);
        });
        head.appendChild(precioMini);

        var btnEliminar = FMT.h("button", "btn btn-xs btn-danger producto-opcion-eliminar", "✕");
        btnEliminar.type = "button";
        btnEliminar.title = "Eliminar esta opción";
        btnEliminar.addEventListener("click", function (e) {
          e.stopPropagation();
          eliminar(idx);
        });
        head.appendChild(btnEliminar);

        tarjeta.appendChild(head);

        // Grid detalles
        var grid = FMT.h("div", "producto-opcion-grid");
        grid.style.cssText = "display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:6px 10px; margin-top:8px;";

        function campo(labelTxt, key, placeholder, tipo) {
          var box = FMT.h("div", "field");
          box.style.cssText = "margin:0;";
          var l = FMT.h("label", null, labelTxt);
          l.style.cssText = "font-size:0.7rem; color:var(--text-soft); margin-bottom:2px; display:block;";
          box.appendChild(l);
          var inp = FMT.crearInput(tipo || "text", op[key] != null ? op[key] : "", placeholder || "", null, { "data-opcion-campo": key, step: "any", min: "0" });
          inp.style.cssText = "padding:5px 7px; font-size:0.82rem; width:100%;";
          inp.addEventListener("click", function (e) { e.stopPropagation(); });
          inp.addEventListener("input", function () {
            op[key] = inp.value;
            persistirYRecalcular();
            if (op.seleccionado && (key === "precio" || key === "unidad" || key === "nombre")) {
              sincronizarPrimarioSiSeleccionada(op);
            }
          });
          box.appendChild(inp);
          grid.appendChild(box);
          return inp;
        }
        campo("Coste", "coste", "0,00", "number");
        campo("Unidad", "unidad", "m2, ud…");
        campo("Marca", "marca");
        campo("Modelo", "modelo");
        campo("SKU", "sku");
        campo("Color", "color");
        campo("Acabado", "acabado");
        campo("Categoría", "categoria");

        // Descripción
        var descBox = FMT.h("div", "field");
        descBox.style.cssText = "grid-column:1 / -1; margin-top:4px;";
        var descLabel = FMT.h("label", null, "Descripción");
        descLabel.style.cssText = "font-size:0.7rem; color:var(--text-soft); margin-bottom:2px; display:block;";
        descBox.appendChild(descLabel);
        var descTA = document.createElement("textarea");
        descTA.rows = 1;
        descTA.placeholder = "Detalles del producto (acabado, dimensiones, garantía…)";
        descTA.setAttribute("data-opcion-campo", "descripcion");
        descTA.style.cssText = "width:100%; padding:5px 7px; font-size:0.82rem; resize:vertical;";
        descTA.value = op.descripcion || "";
        descTA.addEventListener("click", function (e) { e.stopPropagation(); });
        descTA.addEventListener("input", function () { op.descripcion = descTA.value; persistirYRecalcular(); });
        descBox.appendChild(descTA);
        grid.appendChild(descBox);

        // Imagen
        var imgBox = FMT.h("div", "field");
        imgBox.style.cssText = "grid-column:1 / -1; margin-top:6px;";
        var imgLabel = FMT.h("label", null, "Imagen");
        imgLabel.style.cssText = "font-size:0.7rem; color:var(--text-soft); margin-bottom:2px; display:block;";
        imgBox.appendChild(imgLabel);
        var imgRow = FMT.h("div");
        imgRow.style.cssText = "display:flex; align-items:center; gap:8px; flex-wrap:wrap;";
        var imgPrev = FMT.h("img", "producto-opcion-previa");
        imgPrev.alt = "";
        imgPrev.style.cssText = "max-height:60px; max-width:90px; border-radius:4px; border:1px solid var(--border); display:none; object-fit:cover;";
        // Prioridad: _objUrl (archivo nuevo) > imagen guardada
        if (op._objUrl) {
          imgPrev.src = op._objUrl;
          imgPrev.style.display = "";
        } else if (op._imagen_file && op._imagen_file instanceof File) {
          // Crear URL al vuelo si se perdió
          try {
            var tmpUrl = URL.createObjectURL(op._imagen_file);
            op._objUrl = tmpUrl;
            imgPrev.src = tmpUrl;
            imgPrev.style.display = "";
          } catch (e) {}
        } else if (op.imagen) {
          imgPrev.src = window.cotizatArchivoUrl(op.imagen);
          imgPrev.style.display = "";
        }
        imgRow.appendChild(imgPrev);

        var fileLbl = FMT.h("span", "hint", op.imagen || op._imagen_file ? "Sustituir imagen:" : "Imagen (opcional):");
        fileLbl.style.cssText = "font-size:0.7rem;";
        imgRow.appendChild(fileLbl);

        var fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "image/*";
        fileInput.setAttribute("data-opcion-campo", "imagen_file");
        fileInput.style.cssText = "flex:1; min-width:160px; font-size:0.75rem;";
        fileInput.addEventListener("click", function (e) { e.stopPropagation(); });
        fileInput.addEventListener("change", function () {
          if (fileInput.files && fileInput.files[0]) {
            if (op._objUrl) { try { URL.revokeObjectURL(op._objUrl); } catch (e) {} }
            var url = URL.createObjectURL(fileInput.files[0]);
            op._objUrl = url;
            op._imagen_file = fileInput.files[0];
            imgPrev.src = url;
            imgPrev.style.display = "";
            fileLbl.textContent = "Sustituir imagen:";
            btnQuitar.style.display = "";
            persistirYRecalcular();
          }
        });
        imgRow.appendChild(fileInput);

        var btnQuitar = FMT.h("button", "btn btn-xs btn-ghost", "🗑 Quitar imagen");
        btnQuitar.type = "button";
        btnQuitar.title = "Quitar la imagen de esta opción";
        btnQuitar.style.display = (op.imagen || op._imagen_file) ? "" : "none";
        btnQuitar.addEventListener("click", function (e) {
          e.stopPropagation();
          op.imagen = "";
          if (op._objUrl) { try { URL.revokeObjectURL(op._objUrl); } catch (e2) {} op._objUrl = null; }
          op._imagen_file = null;
          if (fileInput) fileInput.value = "";
          imgPrev.removeAttribute("src");
          imgPrev.style.display = "none";
          btnQuitar.style.display = "none";
          fileLbl.textContent = "Imagen (opcional):";
          persistirYRecalcular();
        });
        imgRow.appendChild(btnQuitar);
        imgBox.appendChild(imgRow);
        grid.appendChild(imgBox);

        cuerpoTarjeta.appendChild(grid);
        return tarjeta;
      }

      function renderOpciones() {
        lista.replaceChildren();
        var hay = opcionesCache.length > 0;
        vacio.style.display = hay ? "none" : "";
        countBadge.textContent = String(opcionesCache.length);
        opcionesCache.forEach(function (op, i) {
          op.orden = i;
          lista.appendChild(crearTarjeta(op, i));
        });
        // Persistir después de reordenar órdenes
        guardarProductosOpciones(partidaWrap, opcionesCache);
        partidaWrap._productosOpcionesCache = opcionesCache;
        sec._opcionesCache = opcionesCache;
      }

      btnAdd.addEventListener("click", function () {
        if (collapsed) aplicarColapsado(false);
        opcionesCache.push({
          id: null,
          nombre: "",
          precio: 0,
          coste: "",
          unidad: "",
          categoria: "",
          marca: "",
          modelo: "",
          sku: "",
          color: "",
          acabado: "",
          descripcion: "",
          imagen: "",
          seleccionado: opcionesCache.length === 0,
          orden: opcionesCache.length,
          _imagen_file: null,
          _objUrl: null
        });
        renderOpciones();
        persistirYRecalcular();
        setTimeout(function () {
          var inputs = lista.querySelectorAll('input[data-opcion-campo="nombre"]');
          if (inputs && inputs.length) inputs[inputs.length - 1].focus();
        }, 30);
      });

      // API para el exterior
      sec._renderOpciones = renderOpciones;
      sec._opcionesCache = opcionesCache;
      sec._getOpciones = function () { return opcionesCache; };
      partidaWrap._productosOpcionesCache = opcionesCache;

      // Render inicial inmediato (sin setTimeout para que sea visible)
      renderOpciones();
      // Guardar inicial para que el hidden y el cache del wrap queden sincronizados
      persistirYRecalcular();

      return sec;
    }

    // -------------------------------------------------------------------------
    // Descomposición de costes
    // -------------------------------------------------------------------------

    var CATEGORIAS_COSTE = [
      ["mano_obra", "Mano de obra"],
      ["materiales", "Materiales"],
      ["complementarios", "Directos complementarios"],
      ["otros", "Otros (maquinaria…)"]
    ];

    var ETIQUETA_CATEGORIA = {
      mano_obra: "Mano de obra",
      materiales: "Materiales",
      complementarios: "Directos complementarios",
      otros: "Otros"
    };

    function derivarCategoria(grupo, codigo) {
      var t = String((grupo || "") + " " + (codigo || ""))
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "");
      if (t.indexOf("manodeobra") !== -1 || t.indexOf("personal") !== -1 || t.indexOf("mo") === 0) return "mano_obra";
      if (t.indexOf("material") !== -1 || t.indexOf("mt") === 0) return "materiales";
      if (t.indexOf("complementario") !== -1) return "complementarios";
      return "otros";
    }

    function filasDesdeCostesPartida(datos) {
      var filas = [];
      var defs = [
        ["coste_mano_obra", "mano_obra", "h", "Mano de obra (coste actual)"],
        ["coste_materiales", "materiales", "ud", "Materiales (coste actual)"],
        ["coste_complementarios", "complementarios", "ud", "Directos complementarios (coste actual)"],
        ["coste_otros", "otros", "ud", "Otros (coste actual)"]
      ];
      defs.forEach(function (d) {
        var valor = editor.FMT.parseNum(datos[d[0]]);
        if (valor <= 0) return;
        filas.push({
          tipo: "recurso",
          grupo: ETIQUETA_CATEGORIA[d[1]],
          categoria: d[1],
          codigo: "",
          unidad: d[2],
          descripcion: d[3],
          rendimiento: 1,
          precio: valor,
          importe: "",
          numero: 0,
          celdas: "[]",
          formulas: "{}"
        });
      });
      return filas;
    }

    function crearFilaDescompuesto(partidaWrap, tbody, datos) {
      datos = datos || {};
      var tipo = datos.tipo || "recurso";
      var esPct = String(datos.unidad || "").trim() === "%";
      var editable = tipo === "recurso";
      var tr = editor.FMT.h("tr", "drow");
      tr.dataset.tipo = tipo;
      tr.dataset.grupo = datos.grupo || "";
      tr.dataset.categoria = datos.categoria || "";
      tr.dataset.codigo = datos.codigo || "";
      tr.dataset.unidad = datos.unidad || "";
      tr.dataset.descripcion = datos.descripcion || "";
      tr.dataset.numero = datos.numero || 0;
      tr.dataset.celdas = jsonSeguro(datos.celdas, []);
      tr.dataset.formulas = jsonSeguro(datos.formulas, {});
      if (esPct) tr.dataset.pct = "1";
      if (tipo !== "recurso") tr.classList.add("drow-derivada");
      if (tipo === "total") tr.classList.add("drow-total");

      if (tipo !== "recurso" && tipo !== "subtotal" && tipo !== "total") {
        tr.classList.add("drow-oculto");
        tr.style.display = "none";
      }

      var catActual = datos.categoria || derivarCategoria(datos.grupo, datos.codigo);

      // Categoría
      var tdCat = editor.FMT.h("td", "dc-cat");
      if (editable && !esPct) {
        var selCat = document.createElement("select");
        selCat.dataset.f = "d_categoria";
        selCat.title = "Categoría de coste";
        CATEGORIAS_COSTE.forEach(function (op) {
          var o = document.createElement("option");
          o.value = op[0];
          o.textContent = op[1];
          if (op[0] === catActual) o.selected = true;
          selCat.appendChild(o);
        });
        selCat.addEventListener("change", function () {
          tr.dataset.categoria = selCat.value;
          editor.recalcularDescompuesto(partidaWrap);
          editor.recalcular();
          editor.marcarCambio();
        });
        tdCat.appendChild(selCat);
      } else {
        tdCat.appendChild(editor.FMT.h("span", "dc-cat-lbl", esPct ? "Directos complementarios" : (ETIQUETA_CATEGORIA[catActual] || datos.grupo || "—")));
      }
      tr.appendChild(tdCat);

      // Código
      var tdCod = editor.FMT.h("td", "dc-cod");
      if (editable) {
        var inCod = editor.FMT.crearInput("text", datos.codigo || "", "Código", "d_codigo");
        inCod.addEventListener("input", function () {
          tr.dataset.codigo = inCod.value;
          editor.marcarCambio();
        });
        tdCod.appendChild(inCod);
      } else {
        tdCod.appendChild(editor.FMT.h("span", null, datos.codigo || ""));
      }
      tr.appendChild(tdCod);

      // Unidad
      var tdUnd = editor.FMT.h("td", "dc-und");
      if (editable) {
        var inUnd = editor.FMT.crearInput("text", datos.unidad || "", "h, kg…", "d_unidad");
        if (esPct) {
          inUnd.value = "%";
          inUnd.readOnly = true;
          inUnd.title = "Fila de porcentaje";
        }
        inUnd.addEventListener("input", function () {
          tr.dataset.unidad = inUnd.value;
          if (String(inUnd.value).trim() === "%") tr.dataset.pct = "1";
          else if (tr.dataset.pct) delete tr.dataset.pct;
          editor.recalcularDescompuesto(partidaWrap);
          editor.recalcular();
          editor.marcarCambio();
        });
        tdUnd.appendChild(inUnd);
      } else {
        tdUnd.appendChild(editor.FMT.h("span", null, datos.unidad || ""));
      }
      tr.appendChild(tdUnd);

      // Descripción con autocompletado de recursos existentes
      var tdDesc = editor.FMT.h("td", "dc-desc");
      tdDesc.style.position = "relative";
      if (editable) {
        var descWrap = editor.FMT.h("div");
        descWrap.style.cssText = "position:relative; display:flex; width:100%;";
        var inDesc = editor.FMT.crearInput("text", datos.descripcion || "", "p. ej. Peón, Mortero…", "d_descripcion");
        inDesc.style.flex = "1";
        inDesc.setAttribute("autocomplete", "off");
        // Guardar valor original para dataset
        inDesc.addEventListener("input", function () {
          tr.dataset.descripcion = inDesc.value;
          editor.marcarCambio();
          mostrarRecursosRelacionados();
        });
        descWrap.appendChild(inDesc);
        tdDesc.appendChild(descWrap);

        // --- Autocompletado de recursos ---
        var recursoDropdown = null;
        function cerrarRecursoAutocomplete() {
          if (recursoDropdown) {
            recursoDropdown.remove();
            recursoDropdown = null;
          }
        }
        function buscarRecursosMatches(query) {
          var lista = (editor.RECURSOS || window.EDITOR && window.EDITOR.RECURSOS || []);
          if (!lista || !lista.length) {
            // Fallback intentar CATALOGO_UTILS sobre RECURSOS si existe
            return [];
          }
          var q = String(query || "").trim().toLowerCase();
          if (!q) return lista.slice(0, 15);
          var norm = function(s){ return String(s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,""); };
          var qn = norm(q);
          // Filtrado simple + score por coincidencia en descripcion > codigo > grupo
          var scored = [];
          for (var i=0;i<lista.length;i++) {
            var r = lista[i];
            var desc = norm(r.descripcion);
            var cod = norm(r.codigo);
            var grupo = norm(r.grupo);
            var prov = norm(r.proveedor);
            var score = -1;
            if (desc.indexOf(qn) === 0) score = 100;
            else if (desc.indexOf(qn) !== -1) score = 80;
            else if (cod && cod.indexOf(qn) !== -1) score = 70;
            else if (grupo && grupo.indexOf(qn) !== -1) score = 60;
            else if (prov && prov.indexOf(qn) !== -1) score = 50;
            if (score >= 0) {
              // Bonus por uso frecuente
              score += Math.min(20, (r.usos||0));
              scored.push({ item: r, score: score });
            }
          }
          scored.sort(function(a,b){ return b.score - a.score; });
          return scored.slice(0, 20).map(function(s){ return s.item; });
        }
        function aplicarRecursoSeleccionado(recurso) {
          if (!recurso) return;
          // Rellenar todos los campos de la fila con el recurso existente
          // Código
          var codInput = tr.querySelector('[data-f="d_codigo"]');
          if (codInput) {
            codInput.value = recurso.codigo || "";
            tr.dataset.codigo = codInput.value;
          }
          // Unidad
          var undInput = tr.querySelector('[data-f="d_unidad"]');
          if (undInput) {
            undInput.value = recurso.unidad || "";
            tr.dataset.unidad = undInput.value;
            if (String(undInput.value).trim() === "%") tr.dataset.pct = "1";
            else if (tr.dataset.pct) delete tr.dataset.pct;
          }
          // Descripción (ya)
          inDesc.value = recurso.descripcion || "";
          tr.dataset.descripcion = inDesc.value;
          // Grupo
          tr.dataset.grupo = recurso.grupo || "";
          // Categoría
          var catSel = tr.querySelector('[data-f="d_categoria"]');
          if (catSel && recurso.categoria) {
            // Intentar seleccionar la opción correspondiente
            var encontrado = false;
            for (var ci=0; ci<catSel.options.length; ci++) {
              if (catSel.options[ci].value === recurso.categoria) {
                catSel.selectedIndex = ci;
                encontrado = true;
                break;
              }
            }
            tr.dataset.categoria = recurso.categoria;
          } else if (catSel) {
            // Si no hay select (fila % etc) guardar en dataset
            tr.dataset.categoria = recurso.categoria || tr.dataset.categoria;
          }
          // Precio unitario / hora
          var precInput = tr.querySelector('[data-f="d_precio"]');
          if (precInput) {
            precInput.value = recurso.precio != null ? recurso.precio : "";
            tr.dataset.precio = precInput.value;
          }
          // Recalcular costes e importar
          try { editor.recalcularDescompuesto(partidaWrap); } catch(e){}
          try { editor.recalcular(); } catch(e){}
          try { editor.marcarCambio(); } catch(e){}
          cerrarRecursoAutocomplete();
        }
        function mostrarRecursosRelacionados() {
          var query = inDesc.value.trim();
          var recursos = buscarRecursosMatches(query);
          cerrarRecursoAutocomplete();
          if (!recursos.length) return;
          recursoDropdown = editor.FMT.h("div", "autocomplete-suggestions");
          recursoDropdown.style.cssText = "position:absolute; top:100%; left:0; right:0; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:260px; overflow-y:auto; z-index:2000; box-shadow:var(--shadow-lg); margin-top:4px;";
          recursos.forEach(function(item){
            var sug = editor.FMT.h("div", "suggestion-item");
            sug.style.cssText = "padding:8px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.82rem; display:flex; align-items:center; gap:9px;";
            var main = editor.FMT.h("div", "suggestion-main");
            main.style.cssText = "flex:1; min-width:0;";
            var title = editor.FMT.h("div", "suggestion-title", item.descripcion || "");
            title.style.cssText = "font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";
            main.appendChild(title);
            var metaParts = [item.codigo, item.grupo, item.proveedor, item.categoria, item.unidad].filter(Boolean);
            var meta = editor.FMT.h("div", "suggestion-meta", metaParts.join(" · "));
            meta.style.cssText = "font-size:.72rem; color:var(--text-muted); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";
            main.appendChild(meta);
            sug.appendChild(main);
            var right = editor.FMT.h("div", "", (parseFloat(item.precio||0).toFixed(2) + " $"));
            right.style.cssText = "font-weight:600; color:var(--accent); font-size:0.82rem; white-space:nowrap; margin-left:auto;";
            sug.appendChild(right);
            sug.addEventListener("mousedown", function(e){ e.preventDefault(); });
            sug.addEventListener("click", function(e){
              e.stopPropagation();
              aplicarRecursoSeleccionado(item);
            });
            sug.addEventListener("mouseenter", function(){ sug.style.background = "var(--surface-hover)"; });
            sug.addEventListener("mouseleave", function(){ sug.style.background = "transparent"; });
            recursoDropdown.appendChild(sug);
          });
          descWrap.appendChild(recursoDropdown);
        }
        inDesc.addEventListener("focus", mostrarRecursosRelacionados);
        // Cerrar al hacer Escape o Enter
        inDesc.addEventListener("keydown", function(evt){
          if (evt.key === "Escape") cerrarRecursoAutocomplete();
          if (evt.key === "Enter") {
            // Si hay sugerencias y una coincide exactamente, aplicar la primera
            // Evitar submit
            if (recursoDropdown && recursoDropdown.firstChild) {
              // No cerramos con Enter para permitir escritura, pero si usuario da Enter y hay 1 sugerencia exacta, la aplicamos
              // Por ahora solo cerramos dropdown y dejamos que el input siga
            }
          }
        });
        // Cerrar al clicar fuera
        document.addEventListener("click", function(evt){
          if (recursoDropdown && !descWrap.contains(evt.target)) cerrarRecursoAutocomplete();
        });
        // También al perder foco con timeout para permitir click
        inDesc.addEventListener("blur", function(){
          setTimeout(cerrarRecursoAutocomplete, 150);
        });
      } else {
        tdDesc.appendChild(editor.FMT.h("span", null, datos.descripcion || ""));
      }
      tr.appendChild(tdDesc);

      // Rendimiento
      var tdRend = editor.FMT.h("td", "dc-rend right");
      if (editable) {
        var inRend = editor.FMT.crearInput("number",
          (datos.rendimiento !== undefined && datos.rendimiento !== null && datos.rendimiento !== "") ? datos.rendimiento : "",
          esPct ? "%" : "0,00",
          "d_rendimiento", { step: "any", min: "0" });
        inRend.addEventListener("input", function () {
          editor.recalcularDescompuesto(partidaWrap);
          editor.recalcular();
          editor.marcarCambio();
        });
        tdRend.appendChild(inRend);
      }
      tr.appendChild(tdRend);

      // Precio unitario
      var tdPre = editor.FMT.h("td", "dc-prec right");
      if (editable) {
        var precioRecurso = (datos.precio !== undefined && datos.precio !== null && datos.precio !== "")
          ? datos.precio : datos.precio_unitario;
        var inPre = editor.FMT.crearInput("number",
          (precioRecurso !== undefined && precioRecurso !== null && precioRecurso !== "") ? precioRecurso : "",
          "0,00",
          "d_precio", { step: "any", min: "0" });
        if (esPct) {
          inPre.readOnly = true;
          inPre.classList.add("input-derivado");
        }
        inPre.addEventListener("input", function () {
          editor.recalcularDescompuesto(partidaWrap);
          editor.recalcular();
          editor.marcarCambio();
        });
        tdPre.appendChild(inPre);
      }
      tr.appendChild(tdPre);

      // Importe
      var tdImp = editor.FMT.h("td", "dc-imp right");
      var spanImp = editor.FMT.h("span", null, "—");
      spanImp.dataset.campo = "d_importe";
      tdImp.appendChild(spanImp);
      tr.appendChild(tdImp);

      // Acciones
      var tdAct = editor.FMT.h("td", "dc-act");
      if (editable) {
        var btnDel = editor.FMT.h("button", "partida-icon-btn drow-del", "✕");
        btnDel.type = "button";
        btnDel.title = "Quitar recurso";
        btnDel.addEventListener("click", function () {
          editor.pushUndo();
          tr.remove();
          actualizarEstadoVacio(partidaWrap);
          editor.recalcularDescompuesto(partidaWrap);
          editor.recalcular();
          editor.marcarCambio();
        });
        tdAct.appendChild(btnDel);
      }
      tr.appendChild(tdAct);

      tbody.appendChild(tr);
      return tr;
    }

    function actualizarEstadoVacio(partidaWrap) {
      var sec = partidaWrap.querySelector(".dcost-section");
      if (!sec) return;
      var n = sec._tbody ? sec._tbody.querySelectorAll(".drow").length : 0;
      if (sec._vacio) sec._vacio.style.display = n ? "none" : "";
      if (sec._btnCostes) {
        var posibles = filasDesdeCostesPartida(sec._datos || {});
        sec._btnCostes.style.display = (!n && posibles.length) ? "" : "none";
      }
    }

    // -------------------------------------------------------------------------
    // Sección de descomposición completa
    // -------------------------------------------------------------------------

    function crearSeccionDescomposicion(partidaWrap, datos) {
      var sec = editor.FMT.h("div", "detail-section dcost-section");
      var label = editor.FMT.h("div", "detail-label");
      label.appendChild(document.createTextNode("Descomposición de costes (recursos)"));
      label.appendChild(editor.FMT.h("span", "hint", " · Rendimiento × Precio unitario por " + (datos.unidad || "ud") + " de partida"));
      sec.appendChild(label);

      var wrapTabla = editor.FMT.h("div", "table-wrap dcost-wrap");
      var tabla = editor.FMT.h("table", "table dcost-table");
      var thead = editor.FMT.h("thead");
      var trH = editor.FMT.h("tr");
      [
        ["dc-cat", "Categoría"],
        ["dc-cod", "Código"],
        ["dc-und", "Und."],
        ["dc-desc", "Descripción"],
        ["dc-rend right", "Rendimiento"],
        ["dc-prec right", "Precio unit."],
        ["dc-imp right", "Importe"],
        ["dc-act", ""]
      ].forEach(function (c) {
        trH.appendChild(editor.FMT.h("th", c[0], c[1]));
      });
      thead.appendChild(trH);
      tabla.appendChild(thead);
      var tbody = editor.FMT.h("tbody", "dcost-body");
      tabla.appendChild(tbody);
      wrapTabla.appendChild(tabla);
      sec.appendChild(wrapTabla);

      var vacio = editor.FMT.h("p", "hint dcost-empty", "Sin recursos todavía: agrega mano de obra (precio por hora), materiales (precio por kg), maquinaria…");
      sec.appendChild(vacio);

      // Resumen
      var resumen = editor.FMT.h("div", "dcost-summary");
      var sums = {};
      CATEGORIAS_COSTE.forEach(function (op) {
        var s = editor.FMT.h("span", "dcost-sum");
        s.dataset.cat = op[0];
        s.appendChild(document.createTextNode(op[1] + ": "));
        var strong = editor.FMT.h("strong", null, "0,00");
        s.appendChild(strong);
        sums[op[0]] = strong;
        resumen.appendChild(s);
      });
      var dir = editor.FMT.h("strong", "dcost-directo", "Coste directo / unidad: 0,00");
      resumen.appendChild(dir);
      sec.appendChild(resumen);

      var actions = editor.FMT.h("div", "dcost-actions");
      var btnAdd = editor.FMT.h("button", "btn btn-sm", "+ Agregar recurso");
      btnAdd.type = "button";
      btnAdd.addEventListener("click", function () {
        editor.pushUndo();
        crearFilaDescompuesto(partidaWrap, tbody, null);
        actualizarEstadoVacio(partidaWrap);
        editor.recalcularDescompuesto(partidaWrap);
        editor.recalcular();
        editor.marcarCambio();
      });
      actions.appendChild(btnAdd);

      var btnCostes = editor.FMT.h("button", "btn btn-sm", "🧮 Crear filas desde los costes actuales");
      btnCostes.type = "button";
      btnCostes.style.display = "none";
      btnCostes.title = "Convierte los costes de la partida en filas editables";
      btnCostes.addEventListener("click", function () {
        var filas = filasDesdeCostesPartida(datos);
        if (!filas.length) return;
        editor.pushUndo();
        filas.forEach(function (f) { crearFilaDescompuesto(partidaWrap, tbody, f); });
        actualizarEstadoVacio(partidaWrap);
        editor.recalcularDescompuesto(partidaWrap);
        editor.recalcular();
        editor.marcarCambio();
      });
      actions.appendChild(btnCostes);
      sec.appendChild(actions);

      sec._tbody = tbody;
      sec._vacio = vacio;
      sec._sums = sums;
      sec._dir = dir;
      sec._btnCostes = btnCostes;
      sec._datos = datos;

      // Filas iniciales
      var filasInit = [];
      if (datos.descomposicion) {
        var dDatos = datos.descomposicion;
        if (Array.isArray(dDatos)) filasInit = dDatos;
        else if (Array.isArray(dDatos.filas)) filasInit = dDatos.filas;
      }
      if (!filasInit.length && !(datos.descomposicion && datos.descomposicion.origen === "cype") && !datos.tiene_descomposicion_cype) {
        filasInit = filasDesdeCostesPartida(datos);
      }
      filasInit.forEach(function (f) { crearFilaDescompuesto(partidaWrap, tbody, f); });
      actualizarEstadoVacio(partidaWrap);
      return sec;
    }

    // -------------------------------------------------------------------------
    // Recalcular descompuesto
    // -------------------------------------------------------------------------

    function recalcularDescompuesto(wrap) {
      var sec = wrap.querySelector(".dcost-section");
      var rows = wrap.querySelectorAll(".drow");
      if (!sec && !rows.length) return;
      if (!rows.length) {
        if (sec && sec._sums) editor.CATEGORIAS_COSTE.forEach(function (op) {
          sec._sums[op[0]].textContent = "0,00";
        });
        if (sec && sec._dir) sec._dir.textContent = "Coste directo / unidad: 0,00";
        return;
      }

      var grupoSum = {};
      var catSum = { materiales: 0, mano_obra: 0, complementarios: 0, otros: 0 };
      var hayRecursos = false;

      // 1) Recursos
      rows.forEach(function (tr) {
        if (tr.dataset.tipo !== "recurso" || tr.dataset.pct === "1") return;
        var rend = editor.FMT.parseNum(tr.querySelector('[data-f="d_rendimiento"]').value);
        var precio = editor.FMT.parseNum(tr.querySelector('[data-f="d_precio"]').value);
        var importe = editor.FMT.redondear2(rend * precio);
        tr._imp = importe;
        var celda = tr.querySelector('[data-campo="d_importe"]');
        if (celda) celda.textContent = editor.FMT.fmtNum(importe);
        hayRecursos = true;
        var grupo = tr.dataset.grupo || "";
        grupoSum[grupo] = editor.FMT.redondear2((grupoSum[grupo] || 0) + importe);
        var catEl = tr.querySelector('[data-f="d_categoria"]');
        var cat = catEl ? catEl.value : (tr.dataset.categoria || derivarCategoria(tr.dataset.grupo, tr.dataset.codigo));
        if (!catSum.hasOwnProperty(cat)) cat = "otros";
        catSum[cat] = editor.FMT.redondear2((catSum[cat] || 0) + importe);
      });

      // 2) Subtotales
      var base = 0;
      rows.forEach(function (tr) {
        if (tr.dataset.tipo !== "subtotal") return;
        var valor = editor.FMT.redondear2(grupoSum[tr.dataset.grupo || ""] || 0);
        tr._imp = valor;
        var celda = tr.querySelector('[data-campo="d_importe"]');
        if (celda) celda.textContent = editor.FMT.fmtNum(valor);
        var cat = tr.dataset.categoria || derivarCategoria(tr.dataset.grupo, tr.dataset.codigo);
        if (cat !== "complementarios") base = editor.FMT.redondear2(base + valor);
      });
      if (!rows.length || !Array.prototype.some.call(rows, function (tr) { return tr.dataset.tipo === "subtotal"; })) {
        base = editor.FMT.redondear2((catSum.materiales || 0) + (catSum.mano_obra || 0) + (catSum.otros || 0));
      }

      // 3) Filas %
      rows.forEach(function (tr) {
        if (tr.dataset.tipo !== "recurso" || tr.dataset.pct !== "1") return;
        var pct = editor.FMT.parseNum(tr.querySelector('[data-f="d_rendimiento"]').value);
        var precioInput = tr.querySelector('[data-f="d_precio"]');
        if (precioInput) precioInput.value = base;
        var importe = editor.FMT.redondear2(pct * base / 100);
        tr._imp = importe;
        var celda = tr.querySelector('[data-campo="d_importe"]');
        if (celda) celda.textContent = editor.FMT.fmtNum(importe);
        hayRecursos = true;
        catSum.complementarios = editor.FMT.redondear2((catSum.complementarios || 0) + importe);
      });

      // 4) Coste directo
      var directo = 0;
      rows.forEach(function (tr) {
        if (tr.dataset.tipo === "recurso" && tr._imp !== undefined) directo = editor.FMT.redondear2(directo + tr._imp);
      });
      rows.forEach(function (tr) {
        if (tr.dataset.tipo !== "total") return;
        tr._imp = directo;
        var celda = tr.querySelector('[data-campo="d_importe"]');
        if (celda) celda.textContent = editor.FMT.fmtNum(directo);
      });

      // 5) Resumen y costes de partida
      if (sec && sec._sums) {
        editor.CATEGORIAS_COSTE.forEach(function (op) {
          sec._sums[op[0]].textContent = editor.FMT.fmtNum(catSum[op[0]] || 0);
        });
        if (sec._dir) sec._dir.textContent = "Coste directo / unidad: " + editor.FMT.fmtNum(directo);
      }

      // Sincronizar campos legacy de costes
      ["p_coste_materiales", "p_coste_mano_obra", "p_coste_complementarios", "p_coste_otros"].forEach(function (k) {
        var el = wrap.querySelector('[data-f="' + k + '"]');
        if (!el) {
          el = editor.FMT.crearInput("hidden", "0", null, k);
          wrap.appendChild(el);
        }
        el.readOnly = hayRecursos;
        el.classList.toggle("input-derivado", hayRecursos);
        if (hayRecursos) el.title = "Se calcula desde la descomposición de costes.";
      });

      var costeMap = {
        materiales: catSum.materiales || 0,
        mano_obra: catSum.mano_obra || 0,
        complementarios: catSum.complementarios || 0,
        otros: catSum.otros || 0
      };
      wrap.querySelector('[data-f="p_coste_materiales"]').value = costeMap.materiales.toFixed(2);
      wrap.querySelector('[data-f="p_coste_mano_obra"]').value = costeMap.mano_obra.toFixed(2);
      wrap.querySelector('[data-f="p_coste_complementarios"]').value = costeMap.complementarios.toFixed(2);
      wrap.querySelector('[data-f="p_coste_otros"]').value = costeMap.otros.toFixed(2);
    }

    // -------------------------------------------------------------------------
    // Lectura del modelo
    // -------------------------------------------------------------------------

    function leerPartida(wrap) {
      var meds = [];
      wrap.querySelectorAll(".medicion-row").forEach(function (m) {
        meds.push({
          concepto: m.querySelector('[data-f="m_concepto"]').value,
          cantidad: editor.FMT.parseNum(m.querySelector('[data-f="m_cantidad"]').value),
        });
      });

      var dRows = [];
      wrap.querySelectorAll(".drow").forEach(function (tr) {
        var rendEl = tr.querySelector('[data-f="d_rendimiento"]');
        var precioEl = tr.querySelector('[data-f="d_precio"]');
        var catEl = tr.querySelector('[data-f="d_categoria"]');
        dRows.push({
          tipo: tr.dataset.tipo || "recurso",
          grupo: tr.dataset.grupo || "",
          categoria: catEl ? catEl.value : (tr.dataset.categoria || ""),
          codigo: tr.dataset.codigo || "",
          unidad: tr.dataset.unidad || "",
          descripcion: tr.dataset.descripcion || "",
          rendimiento: rendEl ? rendEl.value : "",
          precio: precioEl ? precioEl.value : "",
          numero: tr.dataset.numero || 0,
          celdas: tr.dataset.celdas || "[]",
          formulas: tr.dataset.formulas || "{}"
        });
      });

      var metaDescomposicion = {};
      var metaEl = wrap.querySelector('[data-f="p_descomposicion_meta"]');
      if (metaEl && metaEl.value) {
        try { metaDescomposicion = JSON.parse(metaEl.value); } catch (e) { metaDescomposicion = {}; }
      }

      return {
        partida_id: (wrap.querySelector('[data-f="p_id"]') || {}).value || "",
        catalogo_id: String((wrap.querySelector('[data-f="p_catalogo_id"]') || {}).value || ""),
        tiempo_estimado_horas: (wrap.querySelector('[data-f="p_tiempo_estimado_horas"]') || {}).value || "",
        codigo_externo: (wrap.querySelector('[data-f="p_codigo_externo"]') || {}).value || "",
        tiene_descomposicion_cype: (wrap.querySelector('[data-f="p_tiene_descomposicion_cype"]') || {}).value === "1",
        nombre_descomposicion_cype: (wrap.querySelector('[data-f="p_nombre_descomposicion_cype"]') || {}).value || "",
        descomposicion_meta: metaDescomposicion,
        nombre: wrap.querySelector('[data-f="p_nombre"]').value,
        descripcion: wrap.querySelector('[data-f="p_descripcion"]').value,
        unidad: wrap.querySelector('[data-f="p_unidad"]').value,
        precio: editor.FMT.parseNum(wrap.querySelector('[data-f="p_precio"]').value),
        cantidad: editor.FMT.parseNum(wrap.querySelector('[data-f="p_cantidad"]').value),
        categoria: (wrap.querySelector('[data-f="p_categoria"]') || {}).value || "",
        prod_nombre: wrap.querySelector('[data-f="p_prod_nombre"]').value,
        prod_precio: wrap.querySelector('[data-f="p_prod_precio"]').value,
        precio_base: editor.FMT.parseNum(wrap.querySelector('[data-f="p_precio_base"]') ? wrap.querySelector('[data-f="p_precio_base"]').value : 0),
        prod_coste: (wrap.querySelector('[data-f="p_prod_coste"]') || {}).value || "",
        prod_unidad: wrap.querySelector('[data-f="p_prod_unidad"]').value,
        prod_categoria: (wrap.querySelector('[data-f="p_prod_categoria"]') || {}).value || "",
        prod_imagen: (wrap.querySelector('[data-f="p_prod_imagen_actual"]') || {}).value || "",
        tipo_partida: (wrap.querySelector('[data-f="p_tipo_partida"]') || {}).value || "included",
        seleccionada: (wrap.querySelector('[data-f="p_seleccionada"]') || {}).value === "1",
        coste_materiales: editor.FMT.parseNum((wrap.querySelector('[data-f="p_coste_materiales"]') || {}).value),
        coste_mano_obra: editor.FMT.parseNum((wrap.querySelector('[data-f="p_coste_mano_obra"]') || {}).value),
        coste_complementarios: editor.FMT.parseNum((wrap.querySelector('[data-f="p_coste_complementarios"]') || {}).value),
        coste_otros: editor.FMT.parseNum((wrap.querySelector('[data-f="p_coste_otros"]') || {}).value),
        desperdicio_pct: editor.FMT.parseNum((wrap.querySelector('[data-f="p_desperdicio_pct"]') || {}).value),
        margen_pct: editor.FMT.parseNum((wrap.querySelector('[data-f="p_margen_pct"]') || {}).value),
        grupo_alternativa: (wrap.querySelector('[data-f="p_grupo_alternativa"]') || {}).value || "",
        mediciones: meds,
        descomposicion: dRows,
        // Lista de productos alternativos (cada uno es un candidato para que
        // el cliente elija). Se serializa desde el input oculto
        // `p_productos_opciones_json` que la UI del constructor mantiene
        // sincronizado.
        productos_opciones: leerProductosOpciones(wrap),
      };
    }

    // -------------------------------------------------------------------------
    // Crear partida
    // -------------------------------------------------------------------------

    function crearPartida(capEl, datos, editorInst) {
      datos = datos || {};
      var cont = capEl.querySelector(".partidas-body");
      if (!cont) return null;

      var wrap = editor.FMT.h("div", "partida-wrap");
      wrap.draggable = true;

      // Campos ocultos de identidad técnica
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.partida_id || "", null, "p_id"));
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.catalogo_id || "", null, "p_catalogo_id"));
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.codigo_externo || "", null, "p_codigo_externo"));
      // Precio base de la partida sin sumar el producto asociado. El campo
      // visible p_precio es el total unitario (base + producto).
      wrap.appendChild(editor.FMT.crearInput("hidden", (datos.precio_base != null ? datos.precio_base : ((datos.precio || 0) - editor.FMT.parseNum(datos.prod_precio))), null, "p_precio_base"));
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.tiene_descomposicion_cype ? "1" : "", null, "p_tiene_descomposicion_cype"));
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.nombre_descomposicion_cype || "", null, "p_nombre_descomposicion_cype"));
      wrap.appendChild(editor.FMT.crearInput("hidden", jsonSeguro(datos.descomposicion_meta, {}), null, "p_descomposicion_meta"));
      // Horas por unidad declaradas en la ficha del catálogo; se usan solo
      // como respaldo del indicador de tiempo estimado cuando la partida no
      // tiene descomposición con rendimientos de tiempo.
      wrap.appendChild(editor.FMT.crearInput("hidden", datos.tiempo_estimado_horas || "", null, "p_tiempo_estimado_horas"));
      // Lista de productos alternativos serializada. La UI de la partida
      // lee y edita este array sin tocar los inputs primarios (que
      // mantienen la compatibilidad con versiones anteriores).
      wrap.appendChild(editor.FMT.crearInput("hidden", jsonSeguro(datos.productos_opciones || [], []), null, "p_productos_opciones_json"));
      // En modo básico no existen los selectores visibles de tipo/estado
      // (se crean solo con funciones avanzadas); se conservan como campos
      // ocultos para que la partida no pierda su tipo/estado al guardar.
      if (!window.FUNCIONES_AVANZADAS) {
        wrap.appendChild(editor.FMT.crearInput("hidden", datos.tipo_partida || "included", null, "p_tipo_partida"));
        wrap.appendChild(editor.FMT.crearInput("hidden", datos.seleccionada ? "1" : "0", null, "p_seleccionada"));
      }

      var row = editor.FMT.h("div", "partida-row");

      var drag = editor.FMT.h("div", "partida-drag", "⠿");
      drag.title = "Arrastrar para reordenar";
      row.appendChild(drag);

      var nombreWrap = editor.FMT.h("div", "partida-nombre-wrap");
      nombreWrap.style.position = "relative";
      var num = editor.FMT.h("span", "partida-num", "");
      nombreWrap.appendChild(num);
      var dot = editor.FMT.h("span", "partida-dot");
      nombreWrap.insertBefore(dot, num);
      var nombreInput = editor.FMT.crearInput("text", datos.nombre || "", "Nombre de la partida…", "p_nombre");
      nombreInput.className = "partida-nombre-input";
      nombreInput.addEventListener("input", function () {
        var catId = wrap.querySelector('[data-f="p_catalogo_id"]');
        if (!catId || !catId.value) return;
        var num = Number(catId.value || 0);
        var maestra = (editorInst.CATALOGO || []).find(function (p) { return Number(p.id) === num; });
        if (maestra && String(maestra.nombre || "").trim().toLowerCase() !== String(nombreInput.value || "").trim().toLowerCase()) {
          catId.value = "";
        }
      });
      nombreInput.addEventListener("blur", function () {
        var catId = wrap.querySelector('[data-f="p_catalogo_id"]');
        if (!catId || catId.value) return;
        var nombreActual = String(nombreInput.value || "").trim().toLowerCase();
        if (!nombreActual) return;
        var maestra = (editorInst.CATALOGO || []).find(function (p) {
          return String(p.nombre || "").trim().toLowerCase() === nombreActual;
        });
        if (maestra) catId.value = String(maestra.id);
      });
      nombreWrap.appendChild(nombreInput);
      
      // AUTOCOMPLETADO PARA NOMBRE DE PARTIDA
      var partidaDropdown = null;
      function cerrarPartidaAutocomplete() {
        if (partidaDropdown) {
          partidaDropdown.remove();
          partidaDropdown = null;
        }
      }
      function mostrarPartidasRelacionadas() {
        var query = nombreInput.value.trim();
        if (!query) {
          cerrarPartidaAutocomplete();
          return;
        }
        var matches = window.CATALOGO_UTILS.buscarEnCatalogo(
          editorInst.CATALOGO,
          query,
          ["nombre", "descripcion", "categoria", "codigo", "proveedor"],
          ""
        );
        cerrarPartidaAutocomplete();
        if (!matches.length) return;

        partidaDropdown = editorInst.FMT.h("div", "autocomplete-suggestions");
        partidaDropdown.style.cssText = "position:absolute; top:100%; left:0; right:0; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:240px; overflow-y:auto; z-index:1000; box-shadow:var(--shadow-lg); margin-top:4px;";

        matches.forEach(function (item) {
          var sug = editorInst.FMT.h("div", "suggestion-item");
          sug.style.cssText = "padding:8px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.82rem; display:flex; align-items:center; gap:9px;";
          
          var main = editorInst.FMT.h("div", "suggestion-main");
          var title = editorInst.FMT.h("div", "suggestion-title", item.nombre);
          title.style.fontWeight = "600";
          main.appendChild(title);
          
          var meta = [item.categoria, item.proveedor].filter(Boolean).join(" · ");
          if (meta) {
            var mdiv = editorInst.FMT.h("div", "suggestion-meta", meta);
            mdiv.style.cssText = "font-size:.72rem; color:var(--text-muted); margin-top:2px;";
            main.appendChild(mdiv);
          }
          sug.appendChild(main);
          
          var right = editorInst.FMT.h("div", "", (item.precio || 0).toFixed(2) + " $");
          right.style.cssText = "font-weight:600; color:var(--accent); font-size:0.85rem; white-space:nowrap; margin-left:auto;";
          sug.appendChild(right);

          sug.addEventListener("mousedown", function(e) { e.preventDefault(); });
          sug.addEventListener("click", function (e) {
            e.stopPropagation();
            // Cargar la ficha completa del catálogo, no solo nombre/precio.
            var actuales = leerPartida(wrap);
            var descomposicion = item.descomposicion;
            try {
              if (typeof descomposicion === "string") descomposicion = JSON.parse(descomposicion);
            } catch (error) { descomposicion = null; }
            var completos = Object.assign({}, actuales, {
              catalogo_id: item.id || "",
              nombre: item.nombre || "",
              descripcion: item.descripcion || "",
              unidad: item.unidad || "ud",
              // El precio del catálogo es la base de la partida; si la línea
              // ya tiene un producto asociado, el total de la línea es
              // base + producto (misma regla que en el resto del editor).
              precio: (item.precio || 0) + (String(actuales.prod_nombre || "").trim() ? editorInst.FMT.parseNum(actuales.prod_precio) : 0),
              precio_base: item.precio || 0,
              categoria: item.categoria || "",
              subcategoria: item.subcategoria || "",
              codigo_interno: item.codigo_interno || item.codigo || "",
              codigo_externo: item.codigo_externo || "",
              proveedor: item.proveedor || "",
              tiempo_estimado_horas: item.tiempo_estimado_horas,
              rendimiento: item.rendimiento || "",
              notas_tecnicas: item.notas_tecnicas || "",
              imagen_partida: item.imagen || "",
              coste_materiales: item.coste_materiales || 0,
              coste_mano_obra: item.coste_mano_obra || 0,
              coste_complementarios: item.coste_complementarios || 0,
              coste_otros: item.coste_otros || 0,
              desperdicio_pct: item.desperdicio_recomendado_pct || 0,
              descomposicion: descomposicion
            });
            cerrarPartidaAutocomplete();
            var nueva = reemplazarPartida(wrap, completos, editorInst);
            if (nueva) {
              var edit = nueva.querySelector(".partida-edit-btn");
              if (edit) edit.focus();
            }
          });
          
          sug.addEventListener("mouseenter", function () { sug.style.background = "var(--surface-hover)"; });
          sug.addEventListener("mouseleave", function () { sug.style.background = "transparent"; });

          partidaDropdown.appendChild(sug);
        });

        nombreWrap.appendChild(partidaDropdown);
      }

      nombreInput.addEventListener("input", mostrarPartidasRelacionadas);
      nombreInput.addEventListener("focus", mostrarPartidasRelacionadas);
      nombreInput.addEventListener("blur", function () {
        setTimeout(cerrarPartidaAutocomplete, 150);
      });

      var expandBtn = editor.FMT.h("button", "partida-expand-btn", "✎");
      expandBtn.type = "button";
      expandBtn.title = "Abrir ficha completa de la partida";
      nombreWrap.appendChild(expandBtn);
      row.appendChild(nombreWrap);

      var cantCell = editor.FMT.h("div", "");
      cantCell.style.textAlign = "right";
      cantCell.style.padding = "0 0.5rem";
      var cantInput = editor.FMT.crearInput("number", datos.cantidad !== undefined ? datos.cantidad : "1", "0", "p_cantidad", { step: "any", min: "0" });
      cantInput.className = "partida-cant-input";
      cantCell.appendChild(cantInput);
      row.appendChild(cantCell);

      var undCell = editor.FMT.h("div", "");
      undCell.style.textAlign = "center";
      undCell.style.padding = "0 0.3rem";
      var undSelect = document.createElement("select");
      undSelect.className = "partida-unidad-select";
      undSelect.dataset.f = "p_unidad";
      var unidades = ["ud", "m2", "m²", "m", "ml", "m3", "m³", "glb", "juego", "kg", "h", "hora"];
      var unidadActual = datos.unidad || "ud";
      if (unidades.indexOf(unidadActual) === -1) unidades.push(unidadActual);
      unidades.forEach(function (u) {
        var opt = document.createElement("option");
        opt.value = u;
        opt.textContent = u;
        if (u === unidadActual) opt.selected = true;
        undSelect.appendChild(opt);
      });
      undCell.appendChild(undSelect);
      row.appendChild(undCell);

      var precioCell = editor.FMT.h("div", "");
      precioCell.style.textAlign = "right";
      precioCell.style.padding = "0 0.5rem";
      var precioInput = editor.FMT.crearInput("number", datos.precio !== undefined ? datos.precio : "0", "0,00", "p_precio", { step: "any", min: "0" });
      precioInput.className = "partida-precio-input";
      precioInput.addEventListener("input", function () {
        var baseInput = wrap.querySelector('[data-f="p_precio_base"]');
        var prodInput = wrap.querySelector('[data-f="p_prod_precio"]');
        if (baseInput) baseInput.value = editorInst.FMT.parseNum(precioInput.value) - editorInst.FMT.parseNum(prodInput ? prodInput.value : 0);
      });
      precioCell.appendChild(precioInput);
      row.appendChild(precioCell);

      var importeCell = editor.FMT.h("div", "partida-importe", "0,00 " + editor.simbolo());
      row.appendChild(importeCell);

      // Beneficio por partida: siempre visible, muestra — si no hay coste
      var benefCell = editor.FMT.h("div", "partida-beneficio sin-datos", "—");
      benefCell.title = "Beneficio = Importe − Coste interno";
      row.appendChild(benefCell);

      // Acciones de fila
      var delCell = editor.FMT.h("div", "partida-del");
      var editBtn = editor.FMT.h("button", "partida-edit-btn", "✎ Editar");
      editBtn.type = "button";
      editBtn.title = "Abrir la ficha técnica completa";
      var dupBtn = editor.FMT.h("button", "partida-icon-btn", "⧉");
      dupBtn.type = "button";
      dupBtn.title = "Duplicar partida";
      var delBtn = editor.FMT.h("button", "partida-icon-btn", "✕");
      delBtn.type = "button";
      delBtn.title = "Eliminar partida";
      delCell.appendChild(editBtn);
      delCell.appendChild(dupBtn);
      delCell.appendChild(delBtn);
      row.appendChild(delCell);

      wrap.appendChild(row);

      // Crea primero el almacén de datos (oculto) para que el resumen pueda
      // escuchar sus cambios, y se inserta visualmente justo bajo la fila.
      var det = crearDetalles(wrap, datos, editorInst);
      // Referencia comercial visible: el producto asociado no queda escondido
      // dentro del editor. Así se ve de inmediato qué material se ha elegido.
      var productoResumen = crearResumenProducto(wrap, datos, editorInst);
      var secOpciones = crearSeccionProductosOpciones(wrap, datos, editorInst);
      wrap.appendChild(productoResumen);
      wrap.appendChild(secOpciones);
      wrap.appendChild(det);
      cont.appendChild(wrap);

      // Expandir/contraer
      function expandir() {
        wrap.classList.add("expanded");
        row.classList.add("expanded");
        det.classList.add("open");
        expandBtn.textContent = "▴";
        expandBtn.title = "Contraer partida";
      }
      function colapsar() {
        wrap.classList.remove("expanded");
        row.classList.remove("expanded");
        det.classList.remove("open");
        expandBtn.textContent = "▾";
        expandBtn.title = "Expandir partida";
      }
      function toggle() {
        if (typeof editorInst.abrirEditorPartida === "function") {
          editorInst.abrirEditorPartida(wrap);
        } else {
          det.classList.contains("open") ? colapsar() : expandir();
        }
      }

      expandBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        toggle();
      });

      row.addEventListener("click", function (e) {
        if (e.target.closest("input, select, textarea, button, .autocomplete-suggestions, .productos-opciones-section")) return;
        toggle();
      });

      var ratonDentro = false;
      wrap.addEventListener("mousedown", function () {
        ratonDentro = true;
        setTimeout(function () { ratonDentro = false; }, 0);
      });
      wrap.addEventListener("focusout", function (e) {
        if (ratonDentro || wrap.classList.contains("dragging")) return;
        if (e.relatedTarget && wrap.contains(e.relatedTarget)) return;
        colapsar();
      });

      // Flujo Enter
      nombreInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          cantInput.focus();
          cantInput.select();
        }
      });
      cantInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          precioInput.focus();
          precioInput.select();
        }
      });
      // Enter en el último campo no crea una partida nueva: solo guarda los
      // datos de esta misma partida (se abandona el foco y se confirma la fila).
      precioInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          precioInput.blur();
        }
      });

      // Editar/duplicar/eliminar
      editBtn.addEventListener("click", function () { toggle(); });
      dupBtn.addEventListener("click", function () { editorInst.duplicarPartida(wrap); });
      delBtn.addEventListener("click", function () {
        if (confirm("¿Eliminar esta partida?")) {
          editorInst.pushUndo();
          wrap.remove();
          editorInst.renumerar();
          editorInst.recalcular();
          editorInst.marcarCambio();
        }
      });

      [cantInput, precioInput].forEach(function (el) {
        el.addEventListener("input", function () {
          editorInst.renumerar();
          editorInst.recalcular();
          editorInst.marcarCambio();
        });
      });

      // Mediciones iniciales
      (datos.mediciones || []).forEach(function (m) { crearMedicion(wrap, m, editorInst); });

      editorInst.renumerar();
      editorInst.recalcular();
      return wrap;
    }

    function crearResumenProducto(partidaWrap, datos, editorInst) {
      var wrapRes = editor.FMT.h("div", "partida-producto-resumen-wrap");
      var resumen = editor.FMT.h("button", "partida-producto-resumen");
      resumen.type = "button";
      resumen.title = "Cambiar o revisar el producto asociado";
      resumen.setAttribute("aria-label", "Cambiar producto asociado");

      var imagen = editor.FMT.h("img", "partida-producto-imagen");
      imagen.alt = "";
      var sinImagen = editor.FMT.h("span", "partida-producto-icono", "▦");
      var texto = editor.FMT.h("span", "partida-producto-texto");
      var nombre = editor.FMT.h("strong", "partida-producto-nombre");
      var meta = editor.FMT.h("small", "partida-producto-meta");
      texto.appendChild(nombre);
      texto.appendChild(meta);

      var accionesWrap = editor.FMT.h("div", "partida-producto-acciones");
      accionesWrap.style.cssText = "display:flex; align-items:center; gap:8px; margin-left:auto;";

      var accion = editor.FMT.h("span", "partida-producto-accion", "Cambiar ›");
      var btnQuitarProd = editor.FMT.h("button", "btn btn-xs btn-danger", "🗑 Eliminar producto");
      btnQuitarProd.type = "button";
      btnQuitarProd.title = "Eliminar y desasociar este producto de la partida";
      btnQuitarProd.style.cssText = "font-size:0.75rem; padding:3px 8px; z-index:2;";
      btnQuitarProd.addEventListener("click", function (evt) {
        evt.stopPropagation();
        if (confirm("¿Seguro que deseas eliminar este producto de la partida?")) {
          quitarProductoDePartida(partidaWrap);
        }
      });

      accionesWrap.appendChild(accion);
      accionesWrap.appendChild(btnQuitarProd);

      resumen.appendChild(imagen);
      resumen.appendChild(sinImagen);
      resumen.appendChild(texto);
      resumen.appendChild(accionesWrap);
      wrapRes.appendChild(resumen);

      var galeria = editor.FMT.h("div", "partida-producto-galeria");
      galeria.style.cssText = "display:none; gap:6px; flex-wrap:wrap; padding:0 0.65rem 0.45rem;";
      wrapRes.appendChild(galeria);

      function rutaImagen(ruta) {
        ruta = String(ruta || "").trim();
        if (!ruta) return "";
        return window.cotizatArchivoUrl(ruta);
      }
      function actualizar() {
        var prodNombre = (partidaWrap.querySelector('[data-f="p_prod_nombre"]') || {}).value;
        var prodPrecio = (partidaWrap.querySelector('[data-f="p_prod_precio"]') || {}).value;
        var prodUnidad = (partidaWrap.querySelector('[data-f="p_prod_unidad"]') || {}).value;
        var prodImagen = (partidaWrap.querySelector('[data-f="p_prod_imagen_actual"]') || {}).value;
        var opciones = leerProductosOpciones(partidaWrap);
        var tieneProducto = String(prodNombre || "").trim().length > 0 || opciones.length > 0;
        wrapRes.hidden = !tieneProducto;
        resumen.hidden = !tieneProducto;
        if (!tieneProducto) {
          galeria.style.display = "none";
          return;
        }
        nombre.textContent = prodNombre || (opciones[0] && opciones[0].nombre) || "Producto";
        var precio = editorInst.FMT.parseNum(prodPrecio);
        var costeProducto = (partidaWrap.querySelector('[data-f="p_prod_coste"]') || {}).value;
        var coste = editorInst.FMT.parseNum(costeProducto);
        meta.textContent = (prodPrecio !== "" && isFinite(precio) ? "Venta " + editorInst.FMT.fmt(precio) : "Venta sin definir") + (costeProducto !== "" ? " · Coste " + editorInst.FMT.fmt(coste) : "") + (prodUnidad ? " / " + prodUnidad : "");
        var src = rutaImagen(prodImagen);
        imagen.style.display = src ? "" : "none";
        sinImagen.style.display = src ? "none" : "grid";
        if (src) imagen.src = src;
        else imagen.removeAttribute("src");

        galeria.replaceChildren();
        if (opciones.length > 1) {
          galeria.style.display = "flex";
          opciones.forEach(function (op, i) {
            var btn = editor.FMT.h("button", "partida-producto-mini");
            btn.type = "button";
            btn.title = "Elegir " + (op.nombre || "producto");
            btn.style.cssText = "width:56px; height:56px; padding:0; border:2px solid " + (op.seleccionado ? "var(--accent)" : "var(--border)") + "; border-radius:6px; overflow:hidden; background:var(--bg); cursor:pointer;";
            var imgSrc = rutaImagen(op.imagen);
            if (imgSrc) {
              var im = editor.FMT.h("img");
              im.src = imgSrc;
              im.alt = op.nombre || "";
              im.style.cssText = "width:100%; height:100%; object-fit:cover;";
              btn.appendChild(im);
            } else {
              btn.appendChild(editor.FMT.h("span", "", (op.nombre || "?").slice(0, 2)));
            }
            btn.addEventListener("click", function (ev) {
              ev.stopPropagation();
              opciones.forEach(function (o, j) { o.seleccionado = (j === i); });
              guardarProductosOpciones(partidaWrap, opciones);
              var precioInput = partidaWrap.querySelector('[data-f="p_precio"]');
              var prodNombreInput = partidaWrap.querySelector('[data-f="p_prod_nombre"]');
              var prodPrecioInput = partidaWrap.querySelector('[data-f="p_prod_precio"]');
              var prodUnidadInput = partidaWrap.querySelector('[data-f="p_prod_unidad"]');
              var prodImagenInput = partidaWrap.querySelector('[data-f="p_prod_imagen_actual"]');
              var baseEl = partidaWrap.querySelector('[data-f="p_precio_base"]');
              var base = baseEl ? parseFloat(baseEl.value) || 0 : 0;
              var nuevoPrecioProd = parseFloat(op.precio) || 0;
              if (precioInput) precioInput.value = (base + nuevoPrecioProd).toFixed(2);
              if (prodNombreInput) prodNombreInput.value = op.nombre || "";
              if (prodPrecioInput) prodPrecioInput.value = (nuevoPrecioProd || "").toString();
              if (prodUnidadInput) prodUnidadInput.value = op.unidad || "";
              if (prodImagenInput) prodImagenInput.value = op.imagen || "";
              if (precioInput) precioInput.dispatchEvent(new Event("input", { bubbles: true }));
              var sec = partidaWrap.querySelector(".productos-opciones-section");
              if (sec && typeof sec._renderOpciones === "function") {
                if (sec._opcionesCache) {
                  sec._opcionesCache.forEach(function (o, j) { o.seleccionado = (j === i); });
                }
                sec._renderOpciones();
              }
              actualizar();
              try { editorInst.recalcular(); } catch (e) {}
              try { editorInst.marcarCambio(); } catch (e) {}
            });
            galeria.appendChild(btn);
          });
        } else {
          galeria.style.display = "none";
        }
      }
      resumen.addEventListener("click", function (evento) {
        evento.stopPropagation();
        if (typeof editorInst.abrirEditorPartida === "function") editorInst.abrirEditorPartida(partidaWrap, "producto");
      });
      ["p_prod_nombre", "p_prod_precio", "p_prod_coste", "p_prod_unidad", "p_prod_imagen_actual"].forEach(function (campo) {
        var input = partidaWrap.querySelector('[data-f="' + campo + '"]');
        if (input) input.addEventListener("input", actualizar);
        if (input) input.addEventListener("change", actualizar);
      });
      partidaWrap._actualizarResumenProducto = actualizar;
      setTimeout(actualizar, 0);
      return wrapRes;
    }

    function crearMedicion(partidaWrap, datos, editorInst) {
      var lista = partidaWrap.querySelector(".mediciones-lista");
      if (!lista) return;
      var fila = editor.FMT.h("div", "medicion-row");
      var inConcepto = editor.FMT.crearInput("text", (datos && datos.concepto) || "", "Concepto / zona", "m_concepto");
      var inCantidad = editor.FMT.crearInput("number", datos && datos.cantidad !== undefined ? datos.cantidad : "", "Cant.", "m_cantidad", { step: "any", min: "0" });
      fila.appendChild(inConcepto);
      fila.appendChild(inCantidad);
      var btn = editor.FMT.h("button", "btn btn-sm btn-danger", "✕");
      btn.type = "button";
      btn.title = "Quitar medición";
      btn.addEventListener("click", function () {
        fila.remove();
        editorInst.renumerar();
        editorInst.recalcular();
        editorInst.marcarCambio();
      });
      fila.appendChild(btn);
      lista.appendChild(fila);
      // Editar una medición debe recalcular cantidad total, importes y
      // totales en vivo (antes solo se recalculaba al CREAR la fila, por lo
      // que el total quedaba desactualizado al cambiar la cantidad después).
      [inCantidad, inConcepto].forEach(function (input) {
        input.addEventListener("input", function () {
          editorInst.renumerar();
          editorInst.recalcular();
          editorInst.marcarCambio();
        });
      });
      editorInst.renumerar();
      editorInst.recalcular();
      editorInst.marcarCambio();
    }

    function crearDetalles(partidaWrap, datos, editorInst) {
      datos = datos || {};
      var det = editor.FMT.h("div", "partida-details partida-data-store");
      var origenDescomp = (datos.descomposicion && datos.descomposicion.origen) || "";

      if ((datos.tiene_descomposicion_cype && origenDescomp === "cype") || (datos.tiene_descomposicion_cype && !origenDescomp)) {
        var avisoCype = editor.FMT.h("div", "cype-origin-note", "📐 Esta partida conserva el descompuesto CYPE \u00ab" + (datos.nombre_descomposicion_cype || "archivo original") + "\u00bb. Edita abajo los rendimientos y precios de sus recursos; el coste directo se recalcula con las reglas del formato original.");
        det.appendChild(avisoCype);
      } else if (origenDescomp === "manual") {
        var avisoManual = editor.FMT.h("div", "cype-origin-note", "🧮 Esta partida tiene una descomposición de costes propia. El importe de cada fila se calcula como Rendimiento × Precio unitario.");
        det.appendChild(avisoManual);
      }

      // Descripción técnica
      var sec1 = editor.FMT.h("div", "detail-section");
      var headCat = editor.FMT.h("div", "detail-label");
      headCat.textContent = "Descripción técnica";
      headCat.appendChild(editor.FMT.h("span", "hint", " · Categoría para el catálogo"));
      sec1.appendChild(headCat);

      var catRow = editor.FMT.h("div");
      catRow.style.cssText = "display:flex; align-items:center; gap:0.5rem; margin-bottom:0.45rem;";
      var catLabel = editor.FMT.h("label", null, "Categoría:");
      catLabel.style.cssText = "font-size:0.8rem; font-weight:600; color:var(--text-soft); white-space:nowrap;";
      var catInput = editor.FMT.crearInput("text", datos.categoria || "", "General", "p_categoria");
      catInput.setAttribute("list", "categorias-disponibles");
      catInput.style.cssText = "flex:1; min-width:120px; padding:0.3rem 0.55rem; font-size:0.8rem;";
      catRow.appendChild(catLabel);
      catRow.appendChild(catInput);
      sec1.appendChild(catRow);

      var ta = document.createElement("textarea");
      ta.rows = 3;
      ta.placeholder = "Descripción detallada del trabajo, materiales, normativa, acabados…";
      ta.value = datos.descripcion || "";
      ta.dataset.f = "p_descripcion";
      sec1.appendChild(ta);
      det.appendChild(sec1);

      // Avanzado
      // Sección económica: siempre visible para mostrar beneficio por partida (usuario lo pide en cualquier modo)
      if (true) {
        var secAdv = editor.FMT.h("div", "detail-section advanced-item-section");
        secAdv.appendChild(editor.FMT.h("div", "detail-label", window.FUNCIONES_AVANZADAS ? "Ajustes económicos avanzados" : "Coste y beneficio"));
        var advGrid = editor.FMT.h("div", "prod-grid");

        function advField(label, type, value, key, min) {
          var box = editor.FMT.h("div", "field");
          box.appendChild(editor.FMT.h("label", null, label));
          var inp = editor.FMT.crearInput(type, value === undefined ? "" : value, "0", key, { step: "any", min: min || "0" });
          box.appendChild(inp);
          advGrid.appendChild(box);
          return inp;
        }

        // Tipo y estado solo en modo avanzado; en modo básico se ocultan pero el beneficio sigue visible
        if (window.FUNCIONES_AVANZADAS) {
        var tipoBox = editor.FMT.h("div", "field");
        tipoBox.appendChild(editor.FMT.h("label", null, "Tipo de partida"));
        var tipo = document.createElement("select");
        tipo.dataset.f = "p_tipo_partida";
        [
          ["included", "Incluida"]
        ].concat(window.MOSTRAR_ALTERNATIVAS ? [
          ["optional", "Opcional"],
          ["alternative", "Alternativa"],
          ["excluded", "No incluida"]
        ] : []).concat([
          ["provisional", "Provisional"],
          ["measurement", "Sujeta a medición"]
        ]).forEach(function (op) {
          var o = document.createElement("option");
          o.value = op[0];
          o.textContent = op[1];
          if ((datos.tipo_partida || "included") === op[0]) o.selected = true;
          tipo.appendChild(o);
        });
        tipoBox.appendChild(tipo);
        advGrid.appendChild(tipoBox);

        var selBox = editor.FMT.h("div", "field");
        selBox.appendChild(editor.FMT.h("label", null, "Estado"));
        var sel = document.createElement("select");
        sel.dataset.f = "p_seleccionada";
        [
          ["0", "No seleccionada"],
          ["1", "Seleccionada"]
        ].forEach(function (op) {
          var o = document.createElement("option");
          o.value = op[0];
          o.textContent = op[1];
          if ((datos.seleccionada ? "1" : "0") === op[0]) o.selected = true;
          sel.appendChild(o);
        });
        selBox.appendChild(sel);
        advGrid.appendChild(selBox);
        } // fin Tipo/Estado solo avanzado

        // --- Beneficio y costes: siempre visible (petición usuario 40% sobre coste) ---
        // Estos 4 costes + desperdicio + beneficio se muestran siempre, incluso en modo básico,
        // porque el beneficio por partida debe poder editarse en cualquier presupuesto/partida.
        var costeMatInput = advField("Coste materiales", "number", datos.coste_materiales || 0, "p_coste_materiales");
        var costeMOInput = advField("Coste mano de obra", "number", datos.coste_mano_obra || 0, "p_coste_mano_obra");
        var costeCompInput = advField("Directos complementarios", "number", datos.coste_complementarios || 0, "p_coste_complementarios");
        var costeOtrosInput = advField("Otros costes", "number", datos.coste_otros || 0, "p_coste_otros");
        var desperdInput = advField("Desperdicio (%)", "number", datos.desperdicio_pct || 0, "p_desperdicio_pct");

        var objetivo = advField("Beneficio deseado (%) sobre coste", "number", datos.margen_pct || datos.beneficio_pct || 0, "p_margen_pct", "0");
        objetivo.placeholder = "Ej: 40";
        objetivo.title = "Porcentaje de beneficio sobre el coste directo. Ej: 40% → Precio = Coste ×1.40";
        objetivo.removeAttribute("max");
        objetivo.step = "any";

        var margenBox = editor.FMT.h("div", "field");
        margenBox.style.gridColumn = "1 / -1";
        margenBox.appendChild(editor.FMT.h("label", null, "Beneficio real con el precio actual"));
        var margenReal = editor.FMT.h("div", "margen-real-partida", "—");
        margenReal.dataset.f = "margen_real";
        margenReal.style.cssText = "font-weight:600; padding:8px 10px; background:var(--bg); border:1px solid var(--border); border-radius:6px; font-size:.84rem; min-height:36px; display:flex; align-items:center;";
        margenBox.appendChild(margenReal);

        var btnRow = editor.FMT.h("div");
        btnRow.style.cssText = "display:flex; gap:8px; flex-wrap:wrap; margin-top:6px; align-items:center;";
        var aplicar = editor.FMT.h("button", "btn btn-sm btn-primary", "Aplicar beneficio al precio");
        aplicar.type = "button";
        aplicar.title = "Calcula el precio de venta según el beneficio deseado: Precio = Coste × (1 + Beneficio%/100)";
        var aplicarHint = editor.FMT.h("span", "hint", "Ej: coste 100 + 40% → precio 140");
        aplicarHint.style.alignSelf = "center";
        btnRow.appendChild(aplicar);
        btnRow.appendChild(aplicarHint);
        margenBox.appendChild(btnRow);
        advGrid.appendChild(margenBox);

        function costeActualConDesperdicio() {
          try { editorInst.recalcularDescompuesto(partidaWrap); } catch(e) {}
          var sum = 0;
          ["p_coste_materiales", "p_coste_mano_obra", "p_coste_complementarios", "p_coste_otros"].forEach(function(k){
            sum += editorInst.FMT.parseNum((partidaWrap.querySelector('[data-f="'+k+'"]')||{}).value);
          });
          var desp = editorInst.FMT.parseNum((partidaWrap.querySelector('[data-f="p_desperdicio_pct"]')||{}).value);
          // El producto asociado también es coste (compra real del material);
          // y en partidas con descompuesto CYPE el desperdicio no se aplica
          // (misma regla que el servidor).
          var costeProducto = editorInst.FMT.parseNum((partidaWrap.querySelector('[data-f="p_prod_coste"]')||{}).value);
          var esCype = false;
          var metaEl = partidaWrap.querySelector('[data-f="p_descomposicion_meta"]');
          if (metaEl && metaEl.value) {
            try {
              var metaDes = JSON.parse(metaEl.value);
              esCype = metaDes && (metaDes.origen === "cype" || metaDes.archivo_origen);
            } catch (e) { esCype = false; }
          }
          return esCype ? (sum + costeProducto) : (sum * (1 + desp/100) + costeProducto);
        }
        function actualizarVistaBeneficio() {
          var coste = costeActualConDesperdicio();
          var precioEl = partidaWrap.querySelector('[data-f="p_precio"]');
          var precio = editorInst.FMT.parseNum(precioEl ? precioEl.value : 0);
          if (coste <= 0) {
            margenReal.textContent = "Añade costes (o descomposición) para ver el beneficio";
            margenReal.style.color = "var(--text-muted)";
            return;
          }
          var beneficioU = precio - coste;
          var markup = (beneficioU / coste * 100);
          var margen = precio>0 ? (beneficioU / precio *100) : 0;
          margenReal.style.color = beneficioU >=0 ? "var(--green)" : "var(--rose)";
          margenReal.textContent = "Coste: ";
          var costeStrong = document.createElement("strong");
          costeStrong.textContent = editorInst.FMT.fmt(coste) + "/ud";
          margenReal.appendChild(costeStrong);
          margenReal.appendChild(document.createTextNode(" · Precio: "));
          var precioStrong = document.createElement("strong");
          precioStrong.textContent = editorInst.FMT.fmt(precio) + "/ud";
          margenReal.appendChild(precioStrong);
          margenReal.appendChild(document.createTextNode(" · Beneficio: "));
          var beneficioStrong = document.createElement("strong");
          beneficioStrong.textContent = editorInst.FMT.fmt(beneficioU) + "/ud (" + markup.toFixed(1).replace(".",",") + "% s/coste, " + margen.toFixed(1).replace(".",",") + "% margen)";
          margenReal.appendChild(beneficioStrong);
          margenReal.title = "Markup sobre coste: " + markup.toFixed(2) + "% | Margen sobre precio: " + margen.toFixed(2) + "%";
        }

        aplicar.addEventListener("click", function () {
          var coste = costeActualConDesperdicio();
          var pct = editorInst.FMT.parseNum(objetivo.value);
          if (coste <= 0) {
            margenReal.textContent = "Indica un coste directo mayor a 0";
            margenReal.style.color = "var(--rose)";
            return;
          }
          if (!isFinite(pct)) pct = 0;
          var precio = coste * (1 + pct/100);
          var precioEl = partidaWrap.querySelector('[data-f="p_precio"]');
          if (precioEl) precioEl.value = precio.toFixed(2);
          editorInst.recalcular();
          actualizarVistaBeneficio();
          editorInst.marcarCambio();
        });

        // Live: al escribir beneficio %, actualizar precio automáticamente
        var beneficioTimer = null;
        objetivo.addEventListener("input", function () {
          clearTimeout(beneficioTimer);
          beneficioTimer = setTimeout(function(){
            var coste = costeActualConDesperdicio();
            if (coste > 0) {
              var pct = editorInst.FMT.parseNum(objetivo.value);
              if (isFinite(pct) && pct >= -90) {
                var precioEl = partidaWrap.querySelector('[data-f="p_precio"]');
                if (precioEl && document.activeElement === objetivo) {
                  var precio = coste * (1 + pct/100);
                  // No pisar si el usuario está editando precio directamente
                  precioEl.value = precio.toFixed(2);
                  editorInst.recalcular();
                  actualizarVistaBeneficio();
                  editorInst.marcarCambio();
                } else {
                  actualizarVistaBeneficio();
                }
              }
            }
          }, 350);
        });

        [costeMatInput, costeMOInput, costeCompInput, costeOtrosInput, desperdInput].forEach(function(el){
          if (el) el.addEventListener("input", function(){ actualizarVistaBeneficio(); editorInst.recalcular(); });
        });
        var precioRowInput = partidaWrap.querySelector('[data-f="p_precio"]');
        if (precioRowInput) precioRowInput.addEventListener("input", actualizarVistaBeneficio);
        setTimeout(actualizarVistaBeneficio, 180);
        partidaWrap._actualizarBeneficio = actualizarVistaBeneficio;

        if (window.FUNCIONES_AVANZADAS && window.MOSTRAR_ALTERNATIVAS) {
          advField("Grupo de alternativa", "text", datos.grupo_alternativa || "", "p_grupo_alternativa");
        }

        secAdv.appendChild(advGrid);
        if (window.FUNCIONES_AVANZADAS) {
          secAdv.appendChild(editor.FMT.h("p", "hint", "💡 Beneficio siempre editable. Campos de tipo/alternativa solo en modo avanzado."));
        } else {
          secAdv.appendChild(editor.FMT.h("p", "hint", "💡 Define tus costes y el beneficio % sobre coste (ej. 40) para calcular el precio automáticamente. Activa 'Funciones avanzadas' para tipos de partida y alternativas."));
        }
        det.appendChild(secAdv);

        if (window.FUNCIONES_AVANZADAS && typeof sel !== 'undefined' && typeof tipo !== 'undefined') {
        sel.addEventListener("change", function () {
          if (tipo.value !== "alternative" || sel.value !== "1") return;
          var grupoInput = secAdv.querySelector('[data-f="p_grupo_alternativa"]');
          var grupo = grupoInput ? grupoInput.value.trim().toLowerCase() : "";
          if (!grupo) return;
          editorInst.contCapitulos.querySelectorAll('[data-f="p_seleccionada"]').forEach(function (otro) {
            if (otro === sel || otro.value !== "1") return;
            var otroWrap = otro.closest(".partida-wrap");
            var otroTipo = otroWrap && otroWrap.querySelector('[data-f="p_tipo_partida"]');
            var otroGrupo = otroWrap && otroWrap.querySelector('[data-f="p_grupo_alternativa"]');
            if (otroTipo && otroGrupo && otroTipo.value === "alternative" && otroGrupo.value.trim().toLowerCase() === grupo) {
              otro.value = "0";
            }
          });
          editorInst.recalcular();
          editorInst.marcarCambio();
        });
        }
      }

      // Descomposición de costes
      det.appendChild(crearSeccionDescomposicion(partidaWrap, datos));

      // Recuperar categoría del catálogo
      if (!(datos.categoria || "").trim() && (datos.nombre || "").trim()) {
        var nombreBuscado = datos.nombre.trim().toLowerCase();
        for (var ci = 0; ci < editorInst.CATALOGO.length; ci++) {
          if (editorInst.CATALOGO[ci].nombre.toLowerCase() === nombreBuscado) {
            catInput.value = editorInst.CATALOGO[ci].categoria || "";
            break;
          }
        }
      }

      // Mediciones
      var sec2 = editor.FMT.h("div", "detail-section");
      var medHead = editor.FMT.h("div");
      medHead.style.cssText = "display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;";
      medHead.appendChild(editor.FMT.h("div", "detail-label", "Mediciones (desglose por zonas)"));
      var btnAddMed = editor.FMT.h("button", "btn btn-sm", "+ Medición");
      btnAddMed.type = "button";
      btnAddMed.addEventListener("click", function () {
        crearMedicion(partidaWrap, null, editorInst);
      });
      medHead.appendChild(btnAddMed);
      sec2.appendChild(medHead);
      var medLista = editor.FMT.h("div", "mediciones-lista");
      sec2.appendChild(medLista);
      sec2.appendChild(editor.FMT.h("p", "hint", "Si no agregas mediciones, se usa la cantidad directa."));
      det.appendChild(sec2);

      // Producto presupuestado
      var sec3 = editor.FMT.h("div", "detail-section");
      sec3.appendChild(editor.FMT.h("div", "detail-label", "Producto presupuestado (opcional)"));
      var hintProd = editor.FMT.h("p", "hint");
      hintProd.textContent = "Elige un producto del catálogo o escribe uno nuevo: se guardará automáticamente en el catálogo al guardar el presupuesto.";
      sec3.appendChild(hintProd);

      var pgrid = editor.FMT.h("div", "prod-grid");
      var g1 = editor.FMT.h("div", "field");
      g1.appendChild(editor.FMT.h("label", null, "Nombre"));
      var prodNombreInput = editor.FMT.crearInput("text", datos.prod_nombre || "", "p. ej. Porcelanato Calacatta 60x120", "p_prod_nombre");
      g1.appendChild(prodNombreInput);
      pgrid.appendChild(g1);

      var g2 = editor.FMT.h("div", "field");
      g2.appendChild(editor.FMT.h("label", null, "Precio del producto"));
      var prodCosteInput = editor.FMT.crearInput("hidden", datos.prod_coste !== "" && datos.prod_coste !== undefined && datos.prod_coste !== null ? datos.prod_coste : "", null, "p_prod_coste");
      sec3.appendChild(prodCosteInput);
      var prodPrecioInput = editor.FMT.crearInput("number", datos.prod_precio !== "" && datos.prod_precio !== undefined && datos.prod_precio !== null ? datos.prod_precio : "", "0,00", "p_prod_precio", { step: "any", min: "0" });
      prodPrecioInput.dataset.anterior = String(editorInst.FMT.parseNum(datos.prod_precio));
      prodPrecioInput.addEventListener("input", function () {
        var baseInp = partidaWrap.querySelector('[data-f="p_precio_base"]');
        var precioInp = partidaWrap.querySelector('[data-f="p_precio"]');
        if (baseInp && precioInp) {
          var baseVal = parseFloat(baseInp.value) || 0;
          var nuevoProdVal = parseFloat(prodPrecioInput.value) || 0;
          precioInp.value = (baseVal + nuevoProdVal).toFixed(2);
          precioInp.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (typeof partidaWrap._actualizarResumenProducto === "function") {
          partidaWrap._actualizarResumenProducto();
        }
        try { editorInst.recalcular(); } catch (e) {}
        try { editorInst.marcarCambio(); } catch (e) {}
      });
      g2.appendChild(editor.FMT.h("p", "hint", "Se suma al precio base de la partida."));
      g2.appendChild(prodPrecioInput);
      pgrid.appendChild(g2);

      var g3 = editor.FMT.h("div", "field");
      g3.appendChild(editor.FMT.h("label", null, "Unidad"));
      var prodUnidadInput = editor.FMT.crearInput("text", datos.prod_unidad || "", "m2, ud…", "p_prod_unidad");
      g3.appendChild(prodUnidadInput);
      pgrid.appendChild(g3);
      sec3.appendChild(pgrid);

      // Categoría del producto
      var prodCatRow = editor.FMT.h("div");
      prodCatRow.style.cssText = "display:flex; align-items:center; gap:0.5rem; margin-top:0.4rem;";
      var prodCatLabel = editor.FMT.h("label", null, "Categoría del producto:");
      prodCatLabel.style.cssText = "font-size:0.8rem; font-weight:600; color:var(--text-soft); white-space:nowrap;";
      var prodCatInput = editor.FMT.crearInput("text", datos.prod_categoria || "", "General", "p_prod_categoria");
      prodCatInput.setAttribute("list", "categorias-disponibles");
      prodCatInput.style.cssText = "flex:1; min-width:120px; padding:0.3rem 0.55rem; font-size:0.8rem;";
      prodCatRow.appendChild(prodCatLabel);
      prodCatRow.appendChild(prodCatInput);
      sec3.appendChild(prodCatRow);

      // Foto del producto
      var imgRow = editor.FMT.h("div", "prod-img-row");
      var previa = editor.FMT.h("img", "prod-previa");
      previa.alt = "Imagen del producto";
      previa.style.display = "none";
      var hiddenProdImagen = editor.FMT.crearInput("hidden", datos.prod_imagen || "", null, "p_prod_imagen_actual");
      var fileLbl = editor.FMT.h("span", "hint", "Imagen (opcional):");
      var file = editor.FMT.crearInput("file", undefined, null, "p_prod_imagen", { accept: "image/*" });
      var btnQuitarImg = editor.FMT.h("button", "btn btn-sm btn-danger", "🗑 Eliminar");
      btnQuitarImg.type = "button";
      btnQuitarImg.title = "Quitar la foto del producto";
      btnQuitarImg.style.display = "none";

      function mostrarPrevia(src) {
        if (previa.dataset.objUrl) {
          URL.revokeObjectURL(previa.dataset.objUrl);
          delete previa.dataset.objUrl;
        }
        previa.src = src;
        previa.style.display = "";
        btnQuitarImg.style.display = "";
        fileLbl.textContent = "Sustituir imagen:";
      }

      function ocultarPrevia() {
        if (previa.dataset.objUrl) {
          URL.revokeObjectURL(previa.dataset.objUrl);
          delete previa.dataset.objUrl;
        }
        previa.removeAttribute("src");
        previa.style.display = "none";
        btnQuitarImg.style.display = "none";
        fileLbl.textContent = "Imagen (opcional):";
      }

      if (datos.prod_imagen) {
        previa.src = window.cotizatArchivoUrl(datos.prod_imagen);
        previa.style.display = "";
        btnQuitarImg.style.display = "";
        fileLbl.textContent = "Sustituir imagen:";
      }

      file.addEventListener("change", function () {
        if (file.files && file.files[0]) {
          mostrarPrevia(URL.createObjectURL(file.files[0]));
          previa.dataset.objUrl = previa.src;
        }
        editorInst.marcarCambio();
      });

      btnQuitarImg.addEventListener("click", function () {
        file.value = "";
        hiddenProdImagen.value = "";
        ocultarPrevia();
        editorInst.marcarCambio();
      });

      imgRow.appendChild(previa);
      imgRow.appendChild(hiddenProdImagen);
      imgRow.appendChild(fileLbl);
      imgRow.appendChild(file);
      imgRow.appendChild(btnQuitarImg);
      sec3.appendChild(imgRow);

      var btnQuitarProdTotal = editor.FMT.h("button", "btn btn-sm btn-danger", "🗑 Eliminar producto de esta partida");
      btnQuitarProdTotal.type = "button";
      btnQuitarProdTotal.style.cssText = "margin-top:10px;";
      btnQuitarProdTotal.addEventListener("click", function () {
        if (confirm("¿Seguro que deseas eliminar el producto de esta partida?")) {
          quitarProductoDePartida(partidaWrap);
        }
      });
      sec3.appendChild(btnQuitarProdTotal);

      det.appendChild(sec3);

      // NOTA: la sección de \"Productos para elegir\" ahora vive visible fuera
      // del detalle (en crearPartida), no duplicada dentro del panel oculto.

      // Autocompletado de productos
      (function () {
        var prodNombreWrap = editor.FMT.h("div");
        prodNombreWrap.style.cssText = "position:relative; display:flex;";
        prodNombreInput.parentNode.insertBefore(prodNombreWrap, prodNombreInput);
        prodNombreWrap.appendChild(prodNombreInput);
        prodNombreInput.style.flex = "1";
        var prodDropdown = null;

        function cerrarProdAutocomplete() {
          if (prodDropdown) {
            prodDropdown.remove();
            prodDropdown = null;
          }
        }

        function mostrarProductosRelacionados() {
          var query = prodNombreInput.value.trim();
          var categoriaSugerida = (prodCatInput.value || catInput.value || "").trim();
          var matches = editorInst.CATALOGO_UTILS.buscarEnCatalogo(
            editorInst.PRODUCTOS,
            query,
            ["nombre", "descripcion", "marca", "modelo", "sku", "proveedor", "categoria", "color", "acabado", "formato"],
            categoriaSugerida
          );
          if (!matches.length && query) {
            matches = editorInst.CATALOGO_UTILS.buscarEnCatalogo(
              editorInst.PRODUCTOS,
              query,
              ["nombre", "descripcion", "marca", "modelo", "sku", "proveedor", "categoria", "color", "acabado", "formato"],
              ""
            );
          }
          cerrarProdAutocomplete();
          if (!matches.length) return;

          prodDropdown = editor.FMT.h("div", "autocomplete-suggestions");
          prodDropdown.style.cssText = "position:absolute; top:100%; left:0; right:0; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:240px; overflow-y:auto; z-index:1000; box-shadow:var(--shadow-lg); margin-top:4px;";

          matches.forEach(function (item) {
            var sug = editor.FMT.h("div", "suggestion-item");
            sug.style.cssText = "padding:8px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.82rem; display:flex; align-items:center; gap:9px;";
            if (item.imagen) {
              var thumb = editor.FMT.h("img", "suggestion-thumb");
              thumb.src = window.cotizatArchivoUrl(item.imagen);
              thumb.alt = "";
              sug.appendChild(thumb);
            }
            var main = editor.FMT.h("div", "suggestion-main");
            var title = editor.FMT.h("div", "suggestion-title", item.nombre);
            title.style.fontWeight = "600";
            main.appendChild(title);
            var meta = [item.marca, item.modelo, item.sku, item.categoria].filter(Boolean).join(" · ");
            var fecha = editorInst.FMT.fechaCorta(item.fecha_precio);
            main.appendChild(editor.FMT.h("div", "suggestion-meta", meta + (fecha ? " · precio " + fecha : "")));
            sug.appendChild(main);
            var precio = editor.FMT.h("span", null, (item.precio || 0).toFixed(2) + " $ / " + (item.unidad || "ud"));
            precio.style.cssText = "color:var(--accent); font-size:.78em; white-space:nowrap;";
            sug.appendChild(precio);

            sug.addEventListener("mousedown", function (evt) {
              evt.preventDefault();
            });
            sug.addEventListener("click", function (evt) {
              evt.stopPropagation();
              var precioAnterior = editorInst.FMT.parseNum(prodPrecioInput.value);
              var precioNuevo = editorInst.FMT.parseNum(item.precio);
              var precioLinea = partidaWrap.querySelector('[data-f="p_precio"]');
              var base = partidaWrap.querySelector('[data-f="p_precio_base"]');
              prodNombreInput.value = item.nombre;
              prodPrecioInput.value = item.precio || 0;
              prodUnidadInput.value = item.unidad || "";
              prodCatInput.value = item.categoria || prodCatInput.value || "General";
              if (item.imagen) {
                hiddenProdImagen.value = item.imagen;
                mostrarPrevia(window.cotizatArchivoUrl(item.imagen));
              }
              if (precioLinea) {
                var total = editorInst.FMT.parseNum(precioLinea.value) - precioAnterior + precioNuevo;
                precioLinea.value = total.toFixed(2);
                if (base) base.value = (total - precioNuevo).toFixed(2);
              }
              if (partidaWrap._actualizarResumenProducto) partidaWrap._actualizarResumenProducto();
              cerrarProdAutocomplete();
              editorInst.renumerar();
              editorInst.recalcular();
              editorInst.marcarCambio();
            });
            sug.addEventListener("mouseenter", function () {
              sug.style.background = "var(--bg)";
            });
            sug.addEventListener("mouseleave", function () {
              sug.style.background = "none";
            });
            prodDropdown.appendChild(sug);
          });
          prodNombreWrap.appendChild(prodDropdown);
        }

        prodNombreInput.addEventListener("input", function () {
          if (prodPrecioInput && prodPrecioInput.value && !prodNombreInput.value.trim()) {
            var precioLinea = partidaWrap.querySelector('[data-f="p_precio"]');
            var base = partidaWrap.querySelector('[data-f="p_precio_base"]');
            if (precioLinea) {
              var total = editorInst.FMT.parseNum(precioLinea.value) - editorInst.FMT.parseNum(prodPrecioInput.value);
              precioLinea.value = total.toFixed(2);
              if (base) base.value = total.toFixed(2);
            }
            prodPrecioInput.value = "";
          }
          editorInst.marcarCambio();
          mostrarProductosRelacionados();
        });
        prodPrecioInput.addEventListener("input", function () {
          var precioAnterior = parseFloat(prodPrecioInput.dataset.anterior || prodPrecioInput.defaultValue || prodPrecioInput.value || "0") || 0;
          var precioNuevo = editorInst.FMT.parseNum(prodPrecioInput.value);
          var precioLinea = partidaWrap.querySelector('[data-f="p_precio"]');
          var base = partidaWrap.querySelector('[data-f="p_precio_base"]');
          if (precioLinea) {
            var total = editorInst.FMT.parseNum(precioLinea.value) - precioAnterior + precioNuevo;
            precioLinea.value = total.toFixed(2);
            if (base) base.value = (total - precioNuevo).toFixed(2);
          }
          prodPrecioInput.dataset.anterior = String(precioNuevo);
          if (partidaWrap._actualizarResumenProducto) partidaWrap._actualizarResumenProducto();
          editorInst.renumerar();
          editorInst.recalcular();
          editorInst.marcarCambio();
        });
        prodNombreInput.addEventListener("focus", mostrarProductosRelacionados);
        document.addEventListener("click", function (evt) {
          if (prodDropdown && !prodNombreWrap.contains(evt.target)) cerrarProdAutocomplete();
        });
        prodNombreInput.addEventListener("keydown", function (evt) {
          if (evt.key === "Escape") cerrarProdAutocomplete();
          if (evt.key === "Enter") {
            evt.preventDefault();
            cerrarProdAutocomplete();
          }
        });
      })();

      return det;
    }

    function reemplazarPartida(wrap, datos, editorInst) {
      if (!wrap || !datos) return null;
      var cap = wrap.closest(".capitulo");
      var body = cap && cap.querySelector(".partidas-body");
      if (!cap || !body) return null;
      var siguiente = wrap.nextSibling;
      var nueva = crearPartida(cap, datos, editorInst);
      if (siguiente) body.insertBefore(nueva, siguiente);
      wrap.remove();
      editorInst.renumerar();
      editorInst.recalcular();
      editorInst.marcarCambio();
      return nueva;
    }

    // -------------------------------------------------------------------------
    // API pública del módulo
    // -------------------------------------------------------------------------

    return {
      crearElemento: crearElemento,
      crearInput: crearInput,
      crearFilaDescompuesto: crearFilaDescompuesto,
      crearSeccionDescomposicion: crearSeccionDescomposicion,
      crearSeccionProductosOpciones: crearSeccionProductosOpciones,
      recalcularDescompuesto: recalcularDescompuesto,
      leerPartida: leerPartida,
      crearPartida: crearPartida,
      reemplazarPartida: reemplazarPartida,
      crearMedicion: crearMedicion,
      crearResumenProducto: crearResumenProducto,
      crearDetalles: crearDetalles,
      filasDesdeCostesPartida: filasDesdeCostesPartida,
      leerProductosOpciones: leerProductosOpciones,
      guardarProductosOpciones: guardarProductosOpciones,
      CATEGORIAS_COSTE: CATEGORIAS_COSTE,
    };

  })();

  editor.Partida = Partida;

  // Exponer también en el editor las utilidades que usan los eventos internos
  // (los handlers llaman a editor.recalcularDescompuesto y editor.CATEGORIAS_COSTE).
  editor.recalcularDescompuesto = Partida.recalcularDescompuesto;
  editor.CATEGORIAS_COSTE = Partida.CATEGORIAS_COSTE;
})();
