/* ============================================================================
   Editor — Barra lateral con el catálogo completo en árbol

   El buscador de la barra de herramientas devuelve una lista plana. Con un
   catálogo de 540 partidas eso deja de servir: hace falta poder recorrer
   «Capítulo 07 → Frisos y enlucidos → los seis frisos que hay» sin recordar
   el nombre exacto.

   Este panel dibuja capítulo → subcapítulo → partida a partir de los datos
   que ya viajan en la página (window.EDITOR.CATALOGO), así que no añade
   ninguna petición al servidor.

   Formas de llevar una partida al presupuesto:
     · arrastrarla y soltarla sobre el capítulo que se quiera
     · doble clic o Enter, que la mandan al capítulo activo
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  if (!editor) return;

  var panel = document.getElementById("arbol-catalogo");
  if (!panel) return;

  var cuerpo = panel.querySelector(".arbol-body");
  var inputBuscar = document.getElementById("arbol-buscar");
  var contador = document.getElementById("arbol-contador");
  var SIN_CAPITULO = "Sin capítulo";
  var SIN_SUBCAPITULO = "General";
  var arrastrando = null;

  // ---------------------------------------------------------------------
  // Utilidades
  // ---------------------------------------------------------------------

  function sinTildes(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function num(valor) {
    var n = parseFloat(valor);
    return isFinite(n) ? n : 0;
  }

  function textoBusqueda(p) {
    return sinTildes([
      p.nombre, p.descripcion, p.codigo_interno, p.codigo_externo,
      p.categoria, p.subcategoria, p.unidad
    ].join(" "));
  }

  // ---------------------------------------------------------------------
  // Construcción del árbol a partir del catálogo plano
  // ---------------------------------------------------------------------

  function construirArbol() {
    var catalogo = editor.CATALOGO || [];
    var capitulos = [];
    var indiceCap = Object.create(null);

    catalogo.forEach(function (p, idx) {
      var nombreCap = String(p.categoria || "").trim() || SIN_CAPITULO;
      var nombreSub = String(p.subcategoria || "").trim() || SIN_SUBCAPITULO;

      var cap = indiceCap[nombreCap];
      if (!cap) {
        cap = { nombre: nombreCap, subs: [], indiceSub: Object.create(null), total: 0 };
        indiceCap[nombreCap] = cap;
        capitulos.push(cap);
      }
      var sub = cap.indiceSub[nombreSub];
      if (!sub) {
        sub = { nombre: nombreSub, hojas: [] };
        cap.indiceSub[nombreSub] = sub;
        cap.subs.push(sub);
      }
      sub.hojas.push({ idx: idx, dato: p, buscable: textoBusqueda(p) });
      cap.total += 1;
    });

    // Orden natural: «02 Demoliciones» antes que «10 Impermeabilizaciones».
    var colador = new Intl.Collator("es", { numeric: true, sensitivity: "base" });
    capitulos.sort(function (a, b) { return colador.compare(a.nombre, b.nombre); });
    capitulos.forEach(function (cap) {
      cap.subs.sort(function (a, b) { return colador.compare(a.nombre, b.nombre); });
      cap.subs.forEach(function (sub) {
        sub.hojas.sort(function (a, b) {
          return colador.compare(
            a.dato.codigo_externo || a.dato.nombre,
            b.dato.codigo_externo || b.dato.nombre
          );
        });
      });
    });
    return capitulos;
  }

  // ---------------------------------------------------------------------
  // Pintado
  // ---------------------------------------------------------------------

  // --------------------------------------------------------------------
  // Preview al pasar el ratón (precio, código, descompuesto breve)
  // --------------------------------------------------------------------

  var previewEl = null;
  var previewTimer = null;

  function asegurarPreview() {
    if (previewEl) return previewEl;
    previewEl = document.createElement("div");
    previewEl.className = "arbol-preview";
    previewEl.hidden = true;
    previewEl.setAttribute("role", "tooltip");
    document.body.appendChild(previewEl);
    return previewEl;
  }

  function filasDescompuesto(d) {
    var raw = d.descomposicion;
    if (!raw) return [];
    try {
      if (typeof raw === "string") raw = JSON.parse(raw);
    } catch (e) {
      return [];
    }
    var filas = Array.isArray(raw) ? raw : (raw && raw.filas) || [];
    return filas.filter(function (f) {
      return !f.tipo || f.tipo === "recurso";
    }).slice(0, 5);
  }

  function mostrarPreview(hojaEl, d) {
    var el = asegurarPreview();
    var codigo = d.codigo_externo || d.codigo_interno || d.codigo || "";
    var filas = filasDescompuesto(d);
    var html = "";
    if (codigo) {
      html += '<div class="arbol-preview-code">' + escapeHtml(codigo) + "</div>";
    }
    html += '<div class="arbol-preview-nombre">' + escapeHtml(d.nombre || "") + "</div>";
    html +=
      '<div class="arbol-preview-precio">' +
      num(d.precio).toFixed(2) +
      " $ / " +
      escapeHtml(d.unidad || "ud") +
      "</div>";
    if (d.categoria || d.subcategoria) {
      html +=
        '<div class="arbol-preview-ruta">' +
        escapeHtml([d.categoria, d.subcategoria].filter(Boolean).join(" · ")) +
        "</div>";
    }
    if (d.descripcion) {
      var desc = String(d.descripcion).replace(/\s+/g, " ").trim();
      if (desc.length > 160) desc = desc.slice(0, 157) + "…";
      html += '<div class="arbol-preview-desc">' + escapeHtml(desc) + "</div>";
    }
    if (filas.length) {
      html += '<ul class="arbol-preview-filas">';
      filas.forEach(function (f) {
        var etiqueta = f.codigo || f.descripcion || "recurso";
        var precio = f.precio != null ? f.precio : f.precio_unitario;
        html +=
          "<li><span>" +
          escapeHtml(String(etiqueta).slice(0, 42)) +
          "</span><em>" +
          (precio != null && precio !== "" ? num(precio).toFixed(2) : "—") +
          "</em></li>";
      });
      html += "</ul>";
    }
    html += '<div class="arbol-preview-hint">Arrastra · doble clic · Enter</div>';
    el.innerHTML = html;
    el.hidden = false;
    posicionarPreview(hojaEl, el);
  }

  function escapeHtml(texto) {
    return String(texto || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function posicionarPreview(ancla, el) {
    var r = ancla.getBoundingClientRect();
    var ancho = Math.min(320, window.innerWidth - 24);
    el.style.width = ancho + "px";
    var left = r.right + 10;
    if (left + ancho > window.innerWidth - 12) {
      left = Math.max(12, r.left - ancho - 10);
    }
    var top = Math.max(12, Math.min(r.top, window.innerHeight - el.offsetHeight - 12));
    el.style.left = left + "px";
    el.style.top = top + "px";
  }

  function ocultarPreview() {
    clearTimeout(previewTimer);
    if (previewEl) previewEl.hidden = true;
  }

  function crearHoja(hoja) {
    var d = hoja.dato;
    var li = document.createElement("div");
    li.className = "arbol-hoja";
    li.setAttribute("draggable", "true");
    li.setAttribute("tabindex", "0");
    li.setAttribute("role", "button");
    li.dataset.idx = String(hoja.idx);
    li.dataset.buscable = hoja.buscable;
    li.title = (d.codigo_externo || d.codigo_interno || "")
      ? (d.codigo_externo || d.codigo_interno) + " · " + d.nombre
      : d.nombre;

    if (d.codigo_externo || d.codigo_interno) {
      var cod = document.createElement("span");
      cod.className = "arbol-hoja-codigo";
      cod.textContent = d.codigo_externo || d.codigo_interno;
      li.appendChild(cod);
    }

    var titulo = document.createElement("span");
    titulo.className = "arbol-hoja-nombre";
    titulo.textContent = d.nombre;

    var meta = document.createElement("span");
    meta.className = "arbol-hoja-meta";
    meta.textContent = num(d.precio).toFixed(2) + " $/" + (d.unidad || "ud");

    li.appendChild(titulo);
    li.appendChild(meta);

    li.addEventListener("mouseenter", function () {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(function () {
        mostrarPreview(li, d);
      }, 280);
    });
    li.addEventListener("mouseleave", ocultarPreview);
    li.addEventListener("focus", function () {
      mostrarPreview(li, d);
    });
    li.addEventListener("blur", ocultarPreview);
    li.addEventListener("dragstart", ocultarPreview);

    return li;
  }

  function crearRama(etiqueta, cuenta, clase) {
    var cab = document.createElement("button");
    cab.type = "button";
    cab.className = clase + " arbol-rama";
    cab.setAttribute("aria-expanded", "false");

    var flecha = document.createElement("span");
    flecha.className = "arbol-flecha";
    flecha.textContent = "▸";

    var texto = document.createElement("span");
    texto.className = "arbol-rama-texto";
    texto.textContent = etiqueta;

    var badge = document.createElement("span");
    badge.className = "arbol-cuenta";
    badge.textContent = String(cuenta);

    cab.appendChild(flecha);
    cab.appendChild(texto);
    cab.appendChild(badge);
    return cab;
  }

  function pintar(capitulos) {
    var frag = document.createDocumentFragment();

    capitulos.forEach(function (cap) {
      var bloqueCap = document.createElement("div");
      bloqueCap.className = "arbol-capitulo";

      var cabCap = crearRama(cap.nombre, cap.total, "arbol-cap-head");
      var cuerpoCap = document.createElement("div");
      cuerpoCap.className = "arbol-cap-body";
      cuerpoCap.hidden = true;

      cap.subs.forEach(function (sub) {
        var bloqueSub = document.createElement("div");
        bloqueSub.className = "arbol-subcapitulo";

        var cabSub = crearRama(sub.nombre, sub.hojas.length, "arbol-sub-head");
        var cuerpoSub = document.createElement("div");
        cuerpoSub.className = "arbol-sub-body";
        cuerpoSub.hidden = true;

        sub.hojas.forEach(function (hoja) { cuerpoSub.appendChild(crearHoja(hoja)); });

        bloqueSub.appendChild(cabSub);
        bloqueSub.appendChild(cuerpoSub);
        cuerpoCap.appendChild(bloqueSub);
      });

      bloqueCap.appendChild(cabCap);
      bloqueCap.appendChild(cuerpoCap);
      frag.appendChild(bloqueCap);
    });

    cuerpo.replaceChildren(frag);
  }

  function alternar(cabecera) {
    var destino = cabecera.nextElementSibling;
    if (!destino) return;
    var abierto = !destino.hidden;
    destino.hidden = abierto;
    cabecera.setAttribute("aria-expanded", abierto ? "false" : "true");
    cabecera.classList.toggle("abierto", !abierto);
  }

  // ---------------------------------------------------------------------
  // Búsqueda: filtra hojas y abre las ramas que conservan resultados
  // ---------------------------------------------------------------------

  function filtrar(texto) {
    var aguja = sinTildes(texto).trim();
    var visibles = 0;

    cuerpo.querySelectorAll(".arbol-capitulo").forEach(function (bloqueCap) {
      var vistasCap = 0;

      bloqueCap.querySelectorAll(".arbol-subcapitulo").forEach(function (bloqueSub) {
        var vistasSub = 0;
        bloqueSub.querySelectorAll(".arbol-hoja").forEach(function (hoja) {
          var casa = !aguja || hoja.dataset.buscable.indexOf(aguja) !== -1;
          hoja.hidden = !casa;
          if (casa) vistasSub += 1;
        });
        bloqueSub.hidden = vistasSub === 0;
        var cabSub = bloqueSub.querySelector(".arbol-sub-head");
        var cuerpoSub = bloqueSub.querySelector(".arbol-sub-body");
        if (cabSub) {
          cabSub.querySelector(".arbol-cuenta").textContent = String(vistasSub);
          var abrirSub = Boolean(aguja) && vistasSub > 0;
          cuerpoSub.hidden = !abrirSub;
          cabSub.classList.toggle("abierto", abrirSub);
          cabSub.setAttribute("aria-expanded", abrirSub ? "true" : "false");
        }
        vistasCap += vistasSub;
      });

      bloqueCap.hidden = vistasCap === 0;
      var cabCap = bloqueCap.querySelector(".arbol-cap-head");
      var cuerpoCap = bloqueCap.querySelector(".arbol-cap-body");
      if (cabCap) {
        cabCap.querySelector(".arbol-cuenta").textContent = String(vistasCap);
        var abrirCap = Boolean(aguja) && vistasCap > 0;
        cuerpoCap.hidden = !abrirCap;
        cabCap.classList.toggle("abierto", abrirCap);
        cabCap.setAttribute("aria-expanded", abrirCap ? "true" : "false");
      }
      visibles += vistasCap;
    });

    if (contador) {
      contador.textContent = aguja
        ? visibles + (visibles === 1 ? " partida" : " partidas")
        : (editor.CATALOGO || []).length + " partidas";
    }
  }

  // ---------------------------------------------------------------------
  // Inserción
  // ---------------------------------------------------------------------

  function capituloDestinoPorDefecto() {
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    if (caps.length) return caps[caps.length - 1];
    return editor.Capitulo.crear({ nombre: "CAPÍTULO GENERAL" }, editor);
  }

  function insertar(idx, capDestino) {
    if (!editor.Catalogo || typeof editor.Catalogo.insertarEnCapitulo !== "function") return;
    var cap = capDestino || capituloDestinoPorDefecto();
    editor.Catalogo.insertarEnCapitulo(idx, cap);
  }

  // ---------------------------------------------------------------------
  // Arrastrar desde el árbol y soltar sobre un capítulo
  // ---------------------------------------------------------------------

  function limpiarResaltado() {
    editor.contCapitulos.querySelectorAll(".capitulo.arbol-drop-activo")
      .forEach(function (c) { c.classList.remove("arbol-drop-activo"); });
  }

  function capituloBajoElCursor(event) {
    var el = document.elementFromPoint(event.clientX, event.clientY);
    return el && el.closest ? el.closest(".capitulo") : null;
  }

  function conectarArrastre() {
    cuerpo.addEventListener("dragstart", function (event) {
      var hoja = event.target.closest && event.target.closest(".arbol-hoja");
      if (!hoja) return;
      arrastrando = hoja.dataset.idx;
      hoja.classList.add("arrastrando");
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = "copy";
        // Algunos navegadores cancelan el arrastre si no se fija nada.
        try { event.dataTransfer.setData("text/plain", String(arrastrando)); } catch (e) {}
      }
    });

    cuerpo.addEventListener("dragend", function (event) {
      var hoja = event.target.closest && event.target.closest(".arbol-hoja");
      if (hoja) hoja.classList.remove("arrastrando");
      arrastrando = null;
      limpiarResaltado();
    });

    editor.contCapitulos.addEventListener("dragover", function (event) {
      if (arrastrando === null) return;   // no interferir con el reordenado
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      var cap = capituloBajoElCursor(event);
      limpiarResaltado();
      if (cap) cap.classList.add("arbol-drop-activo");
    });

    editor.contCapitulos.addEventListener("drop", function (event) {
      if (arrastrando === null) return;
      event.preventDefault();
      event.stopPropagation();
      var cap = capituloBajoElCursor(event);
      var idx = arrastrando;
      arrastrando = null;
      limpiarResaltado();
      if (cap) cap.classList.remove("collapsed");
      insertar(idx, cap);
    });
  }

  // ---------------------------------------------------------------------
  // Arranque
  // ---------------------------------------------------------------------

  function init() {
    pintar(construirArbol());
    filtrar("");

    cuerpo.addEventListener("click", function (event) {
      var rama = event.target.closest && event.target.closest(".arbol-rama");
      if (rama) { alternar(rama); return; }
    });

    cuerpo.addEventListener("dblclick", function (event) {
      var hoja = event.target.closest && event.target.closest(".arbol-hoja");
      if (hoja) insertar(hoja.dataset.idx, null);
    });

    cuerpo.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") return;
      var hoja = event.target.closest && event.target.closest(".arbol-hoja");
      if (!hoja) return;
      event.preventDefault();
      insertar(hoja.dataset.idx, null);
    });

    if (inputBuscar) {
      inputBuscar.addEventListener("input", function () { filtrar(inputBuscar.value); });
      inputBuscar.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        inputBuscar.value = "";
        filtrar("");
      });
    }

    conectarArrastre();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  function aplicarEstadoPlegado(plegado) {
    panel.classList.toggle("plegado", plegado);
    // El contenedor grid debe soltar la columna: si no, el panel se pliega
    // pero sigue ocupando 280–320 px y no se gana espacio de trabajo.
    var layout = panel.closest(".builder-con-arbol");
    if (layout) layout.classList.toggle("arbol-plegado", plegado);
    try {
      localStorage.setItem("arbol-catalogo-plegado", plegado ? "true" : "false");
    } catch (e) {}
    var boton = document.getElementById("arbol-toggle");
    if (boton) {
      boton.setAttribute("aria-expanded", plegado ? "false" : "true");
      boton.textContent = plegado ? "›" : "‹";
      boton.title = plegado ? "Mostrar el catálogo" : "Ocultar el catálogo";
    }
  }

  window.CotizatActions.register("arbol-toggle", function () {
    aplicarEstadoPlegado(!panel.classList.contains("plegado"));
  });

  // Restaurar preferencia de panel plegado
  try {
    if (localStorage.getItem("arbol-catalogo-plegado") === "true") {
      aplicarEstadoPlegado(true);
    }
  } catch (e) {}

  window.CotizatActions.register("arbol-expandir", function () {
    cuerpo.querySelectorAll(".arbol-rama").forEach(function (rama) {
      var destino = rama.nextElementSibling;
      if (destino && destino.hidden) alternar(rama);
    });
  });

  window.CotizatActions.register("arbol-plegar", function () {
    cuerpo.querySelectorAll(".arbol-rama").forEach(function (rama) {
      var destino = rama.nextElementSibling;
      if (destino && !destino.hidden) alternar(rama);
    });
  });
})();
