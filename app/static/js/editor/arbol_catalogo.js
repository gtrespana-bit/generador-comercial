/* ============================================================================
   Editor — Barra lateral con el catálogo completo en árbol

   El buscador de la barra de herramientas devuelve una lista plana. Con un
   catálogo de 540 partidas eso deja de servir: hace falta poder recorrer
   «12 Revestimientos → 12.02 Frisos → 12.02.01 Mortero» sin recordar el
   nombre exacto.

   Este panel dibuja capítulo → subcapítulo → apartado desde un índice ligero.
   Las hojas se renderizan al abrir una rama y la ficha completa se solicita
   solo al previsualizar o insertar una partida.

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
  var SIN_CAPITULO = "99 Partidas personalizadas";
  var SIN_SUBCAPITULO = "99.01 General";
  var SIN_APARTADO = "99.01.01 Trabajos diversos";
  var arrastrando = null;
  var consultaActual = "";
  var idsBusquedaRemota = null;
  var temporizadorBusqueda = null;
  var secuenciaBusqueda = 0;

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
      p.codigo_legacy, p.categoria, p.subcategoria, p.apartado, p.unidad,
      p.buscable
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
      var nombreApartado = String(p.apartado || "").trim() || SIN_APARTADO;

      var cap = indiceCap[nombreCap];
      if (!cap) {
        cap = { nombre: nombreCap, subs: [], indiceSub: Object.create(null), total: 0 };
        indiceCap[nombreCap] = cap;
        capitulos.push(cap);
      }
      var sub = cap.indiceSub[nombreSub];
      if (!sub) {
        sub = {
          nombre: nombreSub,
          apartados: [],
          indiceApartado: Object.create(null),
          total: 0
        };
        cap.indiceSub[nombreSub] = sub;
        cap.subs.push(sub);
      }
      var apartado = sub.indiceApartado[nombreApartado];
      if (!apartado) {
        apartado = { nombre: nombreApartado, hojas: [] };
        sub.indiceApartado[nombreApartado] = apartado;
        sub.apartados.push(apartado);
      }
      apartado.hojas.push({ idx: idx, dato: p, buscable: textoBusqueda(p) });
      sub.total += 1;
      cap.total += 1;
    });

    // Orden natural: «02 Demoliciones» antes que «10 Impermeabilizaciones».
    var colador = new Intl.Collator("es", { numeric: true, sensitivity: "base" });
    capitulos.sort(function (a, b) { return colador.compare(a.nombre, b.nombre); });
    capitulos.forEach(function (cap) {
      cap.subs.sort(function (a, b) { return colador.compare(a.nombre, b.nombre); });
      cap.subs.forEach(function (sub) {
        sub.apartados.sort(function (a, b) { return colador.compare(a.nombre, b.nombre); });
        sub.apartados.forEach(function (apartado) {
          apartado.hojas.sort(function (a, b) {
            return colador.compare(
              a.dato.codigo_interno || a.dato.codigo_externo || a.dato.nombre,
              b.dato.codigo_interno || b.dato.codigo_externo || b.dato.nombre
            );
          });
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

  function nodoPreview(tag, clase, texto) {
    var node = document.createElement(tag);
    if (clase) node.className = clase;
    if (texto !== undefined && texto !== null) node.textContent = texto;
    return node;
  }

  function mostrarPreview(hojaEl, d) {
    var el = asegurarPreview();
    var codigo = d.codigo_externo || d.codigo_interno || d.codigo || "";
    var filas = filasDescompuesto(d);

    el.replaceChildren();

    if (codigo) {
      el.appendChild(nodoPreview("div", "arbol-preview-code", codigo));
    }
    el.appendChild(nodoPreview("div", "arbol-preview-nombre", d.nombre || ""));
    el.appendChild(nodoPreview(
      "div",
      "arbol-preview-precio",
      num(d.precio).toFixed(2) + " $ / " + (d.unidad || "ud")
    ));
    if (d.categoria || d.subcategoria || d.apartado) {
      el.appendChild(nodoPreview(
        "div",
        "arbol-preview-ruta",
        [d.categoria, d.subcategoria, d.apartado].filter(Boolean).join(" › ")
      ));
    }
    if (d.descripcion) {
      var desc = String(d.descripcion).replace(/\s+/g, " ").trim();
      if (desc.length > 160) desc = desc.slice(0, 157) + "…";
      el.appendChild(nodoPreview("div", "arbol-preview-desc", desc));
    }
    if (filas.length) {
      var listaFilas = document.createElement("ul");
      listaFilas.className = "arbol-preview-filas";
      filas.forEach(function (f) {
        var etiqueta = f.codigo || f.descripcion || "recurso";
        var precio = f.precio != null ? f.precio : f.precio_unitario;
        var fila = document.createElement("li");
        fila.appendChild(nodoPreview("span", null, String(etiqueta).slice(0, 42)));
        fila.appendChild(nodoPreview(
          "em",
          null,
          precio != null && precio !== "" ? num(precio).toFixed(2) : "—"
        ));
        listaFilas.appendChild(fila);
      });
      el.appendChild(listaFilas);
    }
    el.appendChild(nodoPreview("div", "arbol-preview-hint", "Arrastra · doble clic · Enter"));

    el.hidden = false;
    posicionarPreview(hojaEl, el);
  }

  function cargarYMostrarPreview(hojaEl, hoja) {
    var d = hoja.dato;
    if (!editor.Catalogo || typeof editor.Catalogo.obtenerFicha !== "function") {
      mostrarPreview(hojaEl, d);
      return;
    }
    editor.Catalogo.obtenerFicha(d).then(function (ficha) {
      var sigueActivo = hojaEl.matches(":hover") || document.activeElement === hojaEl;
      if (sigueActivo) mostrarPreview(hojaEl, ficha);
    }).catch(function () {
      var sigueActivo = hojaEl.matches(":hover") || document.activeElement === hojaEl;
      if (sigueActivo) mostrarPreview(hojaEl, d);
    });
  }

  function posicionarPreview(ancla, el) {
    var r = ancla.getBoundingClientRect();
    var ancho = Math.min(320, window.innerWidth - 24);
    CotizatStyles.set(el, "width", ancho + "px");
    var left = r.right + 10;
    if (left + ancho > window.innerWidth - 12) {
      left = Math.max(12, r.left - ancho - 10);
    }
    var top = Math.max(12, Math.min(r.top, window.innerHeight - el.offsetHeight - 12));
    CotizatStyles.set(el, "left", left + "px");
    CotizatStyles.set(el, "top", top + "px");
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
        cargarYMostrarPreview(li, hoja);
      }, 280);
    });
    li.addEventListener("mouseleave", ocultarPreview);
    li.addEventListener("focus", function () {
      cargarYMostrarPreview(li, hoja);
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

        var cabSub = crearRama(sub.nombre, sub.total, "arbol-sub-head");
        var cuerpoSub = document.createElement("div");
        cuerpoSub.className = "arbol-sub-body";
        cuerpoSub.hidden = true;

        sub.apartados.forEach(function (apartado) {
          var bloqueApartado = document.createElement("div");
          bloqueApartado.className = "arbol-apartado";
          var cabApartado = crearRama(
            apartado.nombre,
            apartado.hojas.length,
            "arbol-apartado-head"
          );
          var cuerpoApartado = document.createElement("div");
          cuerpoApartado.className = "arbol-apartado-body";
          cuerpoApartado.hidden = true;
          // Las hojas se crean al abrir o buscar. Con 5.000 partidas esto
          // evita miles de nodos DOM y cientos de fichas innecesarias.
          bloqueApartado._catalogoApartado = apartado;
          bloqueApartado._claveRender = "";
          bloqueApartado.appendChild(cabApartado);
          bloqueApartado.appendChild(cuerpoApartado);
          cuerpoSub.appendChild(bloqueApartado);
        });

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

  function hojasDeApartado(bloqueApartado) {
    var apartado = bloqueApartado && bloqueApartado._catalogoApartado;
    if (!apartado) return [];
    if (!consultaActual) return apartado.hojas;
    return apartado.hojas.filter(function (hoja) {
      return hoja.buscable.indexOf(consultaActual) !== -1 ||
        (idsBusquedaRemota && idsBusquedaRemota[String(hoja.dato.id)]);
    });
  }

  function poblarApartado(bloqueApartado, forzar) {
    if (!bloqueApartado) return;
    var cuerpoApartado = bloqueApartado.querySelector(".arbol-apartado-body");
    if (!cuerpoApartado) return;
    var clave = consultaActual
      ? "q:" + consultaActual + ":" + (idsBusquedaRemota ? Object.keys(idsBusquedaRemota).length : 0)
      : "todo";
    if (!forzar && bloqueApartado._claveRender === clave) return;
    var frag = document.createDocumentFragment();
    hojasDeApartado(bloqueApartado).forEach(function (hoja) {
      frag.appendChild(crearHoja(hoja));
    });
    cuerpoApartado.replaceChildren(frag);
    bloqueApartado._claveRender = clave;
  }

  function alternar(cabecera) {
    var destino = cabecera.nextElementSibling;
    if (!destino) return;
    var abierto = !destino.hidden;
    if (abierto) {
      destino.hidden = true;
    } else {
      var bloqueApartado = cabecera.closest(".arbol-apartado");
      if (bloqueApartado) poblarApartado(bloqueApartado, false);
      destino.hidden = false;
    }
    cabecera.setAttribute("aria-expanded", abierto ? "false" : "true");
    cabecera.classList.toggle("abierto", !abierto);
  }

  // ---------------------------------------------------------------------
  // Búsqueda: filtra hojas y abre las ramas que conservan resultados
  // ---------------------------------------------------------------------

  function filtrar(texto, idsRemotos) {
    consultaActual = sinTildes(texto).trim();
    idsBusquedaRemota = idsRemotos || null;
    var visibles = 0;

    cuerpo.querySelectorAll(".arbol-capitulo").forEach(function (bloqueCap) {
      var vistasCap = 0;
      bloqueCap.querySelectorAll(".arbol-subcapitulo").forEach(function (bloqueSub) {
        var vistasSub = 0;
        bloqueSub.querySelectorAll(".arbol-apartado").forEach(function (bloqueApartado) {
          var vistasApartado = hojasDeApartado(bloqueApartado).length;
          bloqueApartado.hidden = vistasApartado === 0;
          var cabApartado = bloqueApartado.querySelector(".arbol-apartado-head");
          var cuerpoApartado = bloqueApartado.querySelector(".arbol-apartado-body");
          if (cabApartado) {
            cabApartado.querySelector(".arbol-cuenta").textContent = String(vistasApartado);
            var abrirApartado = Boolean(consultaActual) && vistasApartado > 0;
            if (abrirApartado) poblarApartado(bloqueApartado, true);
            else if (bloqueApartado._claveRender.indexOf("q:") === 0) {
              cuerpoApartado.replaceChildren();
              bloqueApartado._claveRender = "";
            }
            cuerpoApartado.hidden = !abrirApartado;
            cabApartado.classList.toggle("abierto", abrirApartado);
            cabApartado.setAttribute("aria-expanded", abrirApartado ? "true" : "false");
          }
          vistasSub += vistasApartado;
        });
        bloqueSub.hidden = vistasSub === 0;
        var cabSub = bloqueSub.querySelector(".arbol-sub-head");
        var cuerpoSub = bloqueSub.querySelector(".arbol-sub-body");
        if (cabSub) {
          cabSub.querySelector(".arbol-cuenta").textContent = String(vistasSub);
          var abrirSub = Boolean(consultaActual) && vistasSub > 0;
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
        var abrirCap = Boolean(consultaActual) && vistasCap > 0;
        cuerpoCap.hidden = !abrirCap;
        cabCap.classList.toggle("abierto", abrirCap);
        cabCap.setAttribute("aria-expanded", abrirCap ? "true" : "false");
      }
      visibles += vistasCap;
    });

    if (contador) {
      contador.textContent = consultaActual
        ? visibles + (visibles === 1 ? " partida" : " partidas")
        : (editor.CATALOGO || []).length + " partidas";
    }
    return visibles;
  }

  function buscarConServidor(texto) {
    clearTimeout(temporizadorBusqueda);
    var consulta = String(texto || "").trim();
    var secuencia = ++secuenciaBusqueda;
    filtrar(consulta, null);
    if (consulta.length < 2 || !editor.Catalogo || !editor.Catalogo.buscarRemoto) return;
    temporizadorBusqueda = setTimeout(function () {
      editor.Catalogo.buscarRemoto(consulta, 100).then(function (items) {
        if (secuencia !== secuenciaBusqueda || consulta !== String(inputBuscar.value || "").trim()) return;
        var ids = Object.create(null);
        items.forEach(function (item) { ids[String(item.id)] = true; });
        var visibles = filtrar(consulta, ids);
        if (!visibles && editor.Catalogo.registrarSinResultados) {
          editor.Catalogo.registrarSinResultados(consulta);
        }
      });
    }, 180);
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
      inputBuscar.addEventListener("input", function () { buscarConServidor(inputBuscar.value); });
      inputBuscar.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        inputBuscar.value = "";
        buscarConServidor("");
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
    // pero sigue ocupando 280–360 px y no se gana espacio de trabajo.
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
    cuerpo.querySelectorAll(".arbol-cap-head, .arbol-sub-head").forEach(function (rama) {
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
