/* ============================================================================
   Editor — Spotlight (⌘K / Ctrl+K)

   Buscador a pantalla completa sobre el catálogo de partidas. Sustituye el
   foco del input de la barra de herramientas: con 540 partidas conviene
   ver resultados con código, precio y capítulo de un vistazo.
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  if (!editor) return;

  var overlay = null;
  var input = null;
  var lista = null;
  var meta = null;
  var activos = [];
  var seleccionado = 0;
  var secuenciaBusqueda = 0;
  var temporizadorRemoto = null;

  function sinTildes(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function crearElemento(tag, atributos, texto) {
    var node = document.createElement(tag);
    if (atributos) {
      Object.keys(atributos).forEach(function (clave) {
        if (clave === "className") node.className = atributos[clave];
        else node.setAttribute(clave, atributos[clave]);
      });
    }
    if (texto !== undefined && texto !== null) node.textContent = texto;
    return node;
  }

  function crearIconoBusqueda() {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "spotlight-icon");
    svg.setAttribute("width", "18");
    svg.setAttribute("height", "18");
    svg.setAttribute("viewBox", "0 0 18 18");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.5");
    svg.setAttribute("aria-hidden", "true");
    var circulo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circulo.setAttribute("cx", "7.5");
    circulo.setAttribute("cy", "7.5");
    circulo.setAttribute("r", "5");
    var linea = document.createElementNS("http://www.w3.org/2000/svg", "path");
    linea.setAttribute("d", "M16 16l-4-4");
    svg.appendChild(circulo);
    svg.appendChild(linea);
    return svg;
  }

  function asegurarDOM() {
    if (overlay) return;
    overlay = document.getElementById("spotlight-catalogo");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "spotlight-catalogo";
      overlay.className = "spotlight-overlay";
      overlay.hidden = true;

      var panel = crearElemento("div", {
        className: "spotlight-panel",
        role: "dialog",
        "aria-modal": "true",
        "aria-label": "Buscar partida",
      });

      var cabecera = crearElemento("div", { className: "spotlight-head" });
      cabecera.appendChild(crearIconoBusqueda());
      cabecera.appendChild(crearElemento("input", {
        type: "search",
        id: "spotlight-input",
        className: "spotlight-input",
        placeholder: "Buscar partida por nombre, código o capítulo…",
        autocomplete: "off",
        spellcheck: "false",
      }));
      cabecera.appendChild(crearElemento("kbd", { className: "spotlight-esc" }, "Esc"));
      panel.appendChild(cabecera);

      panel.appendChild(crearElemento("div", { className: "spotlight-meta", id: "spotlight-meta" }));
      panel.appendChild(crearElemento("div", { className: "spotlight-list", id: "spotlight-list", role: "listbox" }));

      var pie = crearElemento("div", { className: "spotlight-foot" });
      pie.appendChild(crearElemento("span", null, "↑↓ navegar"));
      pie.appendChild(crearElemento("span", null, "Enter añadir"));
      pie.appendChild(crearElemento("span", null, "Esc cerrar"));
      panel.appendChild(pie);

      overlay.appendChild(panel);
      document.body.appendChild(overlay);
    }
    input = document.getElementById("spotlight-input");
    lista = document.getElementById("spotlight-list");
    meta = document.getElementById("spotlight-meta");

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) cerrar();
    });
    input.addEventListener("input", function () {
      render(input.value);
    });
    input.addEventListener("keydown", onKeydown);
  }

  function abrir() {
    asegurarDOM();
    overlay.hidden = false;
    document.body.classList.add("spotlight-open");
    input.value = "";
    render("");
    setTimeout(function () {
      input.focus();
      input.select();
    }, 10);
  }

  function cerrar() {
    if (!overlay) return;
    overlay.hidden = true;
    document.body.classList.remove("spotlight-open");
    activos = [];
    seleccionado = 0;
    clearTimeout(temporizadorRemoto);
    secuenciaBusqueda += 1;
  }

  function buscar(query, remotos) {
    var catalogo = editor.CATALOGO || [];
    var q = sinTildes(query).trim();
    if (!q) {
      // Sin query: las más usadas primero
      return catalogo
        .map(function (p, idx) {
          return { p: p, idx: idx, score: (p.usos || 0) };
        })
        .sort(function (a, b) {
          return b.score - a.score || String(a.p.nombre).localeCompare(String(b.p.nombre), "es");
        })
        .slice(0, 40);
    }
    var tokens = q.split(/\s+/).filter(Boolean);
    var out = [];
    catalogo.forEach(function (p, idx) {
      var blob = sinTildes(
        [p.nombre, p.buscable, p.codigo_interno, p.codigo_externo, p.codigo_legacy,
         p.codigo, p.categoria, p.subcategoria, p.apartado].join(" ")
      );
      var score = 0;
      var ok = true;
      for (var i = 0; i < tokens.length; i++) {
        var t = tokens[i];
        var pos = blob.indexOf(t);
        if (pos === -1) {
          ok = false;
          break;
        }
        score += 100 - Math.min(pos, 90);
        if (sinTildes(p.codigo_interno || p.codigo_externo || "").indexOf(t) === 0) score += 80;
        if (sinTildes(p.nombre || "").indexOf(t) === 0) score += 40;
      }
      if (ok) out.push({ p: p, idx: idx, score: score + (p.usos || 0) });
    });
    if (remotos && remotos.length) {
      var presentes = Object.create(null);
      out.forEach(function (r) { presentes[String(r.p.id)] = true; });
      remotos.forEach(function (p) {
        if (presentes[String(p.id)]) return;
        var idx = catalogo.findIndex(function (item) { return Number(item.id) === Number(p.id); });
        if (idx >= 0) out.push({ p: catalogo[idx], idx: idx, score: 25 + (p.usos || 0) });
      });
    }
    out.sort(function (a, b) {
      return b.score - a.score;
    });
    return out.slice(0, 60);
  }

  function programarBusquedaRemota(query) {
    clearTimeout(temporizadorRemoto);
    var consulta = String(query || "").trim();
    var secuencia = ++secuenciaBusqueda;
    if (consulta.length < 2 || !editor.Catalogo || !editor.Catalogo.buscarRemoto) return;
    temporizadorRemoto = setTimeout(function () {
      editor.Catalogo.buscarRemoto(consulta, 60).then(function (items) {
        if (secuencia !== secuenciaBusqueda || !input || input.value.trim() !== consulta) return;
        render(consulta, items, true);
        if (!activos.length && editor.Catalogo.registrarSinResultados) {
          editor.Catalogo.registrarSinResultados(consulta);
        }
      });
    }, 160);
  }

  function render(query, remotos, omitirRemoto) {
    if (!omitirRemoto) programarBusquedaRemota(query);
    activos = buscar(query, remotos);
    seleccionado = 0;
    if (meta) {
      meta.textContent = activos.length
        ? activos.length + (activos.length === 1 ? " resultado" : " resultados")
        : "Sin coincidencias";
    }
    if (!lista) return;
    lista.replaceChildren();
    if (!activos.length) {
      lista.appendChild(crearElemento(
        "div",
        { className: "spotlight-empty" },
        "No hay partidas que coincidan. Prueba otro término o un código como 09.03…"
      ));
      return;
    }
    var fragmento = document.createDocumentFragment();
    activos.forEach(function (item, i) {
      var p = item.p;
      var codigo = p.codigo_externo || p.codigo_interno || p.codigo || "";
      var ruta = [p.categoria, p.subcategoria, p.apartado].filter(Boolean).join(" › ");

      var btn = crearElemento("button", {
        type: "button",
        className: "spotlight-item" + (i === 0 ? " activo" : ""),
        role: "option",
        "data-i": String(i),
        "data-idx": String(item.idx),
      });

      var principal = crearElemento("span", { className: "spotlight-item-main" });
      if (codigo) {
        principal.appendChild(crearElemento("code", { className: "spotlight-code" }, codigo));
      }
      principal.appendChild(crearElemento("span", { className: "spotlight-nombre" }, p.nombre || ""));
      if (ruta) {
        principal.appendChild(crearElemento("span", { className: "spotlight-ruta" }, ruta));
      }
      btn.appendChild(principal);

      var metadatos = crearElemento("span", { className: "spotlight-item-meta" });
      var importe = window.FMT && window.FMT.fmt
        ? window.FMT.fmt(Number(p.precio) || 0)
        : (Number(p.precio) || 0).toFixed(2);
      metadatos.appendChild(crearElemento("strong", null, importe));
      metadatos.appendChild(crearElemento("small", null, "/" + (p.unidad || "ud")));
      btn.appendChild(metadatos);

      btn.addEventListener("mouseenter", function () {
        seleccionar(Number(btn.dataset.i) || 0);
      });
      btn.addEventListener("click", function () {
        insertar(Number(btn.dataset.idx));
      });

      fragmento.appendChild(btn);
    });
    lista.appendChild(fragmento);
  }

  function seleccionar(i) {
    if (!activos.length) return;
    seleccionado = Math.max(0, Math.min(i, activos.length - 1));
    var items = lista.querySelectorAll(".spotlight-item");
    items.forEach(function (el, idx) {
      el.classList.toggle("activo", idx === seleccionado);
    });
    var activo = items[seleccionado];
    if (activo && activo.scrollIntoView) {
      activo.scrollIntoView({ block: "nearest" });
    }
  }

  function insertar(idxCatalogo) {
    if (!editor.Catalogo || typeof editor.Catalogo.insertarEnCapitulo !== "function") return;
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    var cap = caps.length
      ? caps[caps.length - 1]
      : editor.Capitulo.crear({ nombre: "CAPÍTULO GENERAL" }, editor);
    editor.Catalogo.insertarEnCapitulo(idxCatalogo, cap);
    cerrar();
  }

  function onKeydown(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      cerrar();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      seleccionar(seleccionado + 1);
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      seleccionar(seleccionado - 1);
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      if (activos[seleccionado]) insertar(activos[seleccionado].idx);
    }
  }

  editor.abrirSpotlight = abrir;
  editor.cerrarSpotlight = cerrar;

  // El buscador de la barra de herramientas usa data-cotizat-click="open-spotlight".
  window.CotizatActions.register("open-spotlight", abrir);

  // Atajo se registra también aquí por si atajos.js se carga antes
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (overlay && !overlay.hidden) cerrar();
      else abrir();
    }
  });
})();
