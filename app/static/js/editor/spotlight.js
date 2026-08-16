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

  function sinTildes(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function asegurarDOM() {
    if (overlay) return;
    overlay = document.getElementById("spotlight-catalogo");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "spotlight-catalogo";
      overlay.className = "spotlight-overlay";
      overlay.hidden = true;
      overlay.innerHTML =
        '<div class="spotlight-panel" role="dialog" aria-modal="true" aria-label="Buscar partida">' +
        '<div class="spotlight-head">' +
        '<svg class="spotlight-icon" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="7.5" cy="7.5" r="5"/><path d="M16 16l-4-4"/></svg>' +
        '<input type="search" id="spotlight-input" class="spotlight-input" placeholder="Buscar partida por nombre, código o capítulo…" autocomplete="off" spellcheck="false">' +
        '<kbd class="spotlight-esc">Esc</kbd>' +
        "</div>" +
        '<div class="spotlight-meta" id="spotlight-meta"></div>' +
        '<div class="spotlight-list" id="spotlight-list" role="listbox"></div>' +
        '<div class="spotlight-foot"><span>↑↓ navegar</span><span>Enter añadir</span><span>Esc cerrar</span></div>' +
        "</div>";
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
  }

  function buscar(query) {
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
        [p.nombre, p.descripcion, p.codigo_interno, p.codigo_externo, p.codigo, p.categoria, p.subcategoria].join(" ")
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
    out.sort(function (a, b) {
      return b.score - a.score;
    });
    return out.slice(0, 60);
  }

  function escapeHtml(texto) {
    return String(texto || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function render(query) {
    activos = buscar(query);
    seleccionado = 0;
    if (meta) {
      meta.textContent = activos.length
        ? activos.length + (activos.length === 1 ? " resultado" : " resultados")
        : "Sin coincidencias";
    }
    if (!lista) return;
    if (!activos.length) {
      lista.innerHTML =
        '<div class="spotlight-empty">No hay partidas que coincidan. Prueba otro término o el código CT-…</div>';
      return;
    }
    var html = "";
    activos.forEach(function (item, i) {
      var p = item.p;
      var codigo = p.codigo_externo || p.codigo_interno || p.codigo || "";
      var ruta = [p.categoria, p.subcategoria].filter(Boolean).join(" · ");
      html +=
        '<button type="button" class="spotlight-item' +
        (i === 0 ? " activo" : "") +
        '" role="option" data-i="' +
        i +
        '" data-idx="' +
        item.idx +
        '">' +
        '<span class="spotlight-item-main">' +
        (codigo ? '<code class="spotlight-code">' + escapeHtml(codigo) + "</code>" : "") +
        '<span class="spotlight-nombre">' +
        escapeHtml(p.nombre || "") +
        "</span>" +
        (ruta ? '<span class="spotlight-ruta">' + escapeHtml(ruta) + "</span>" : "") +
        "</span>" +
        '<span class="spotlight-item-meta">' +
        '<strong>' +
        (Number(p.precio) || 0).toFixed(2) +
        "</strong>" +
        "<small>/$" +
        escapeHtml(p.unidad || "ud") +
        "</small>" +
        "</span>" +
        "</button>";
    });
    lista.innerHTML = html;
    lista.querySelectorAll(".spotlight-item").forEach(function (btn) {
      btn.addEventListener("mouseenter", function () {
        seleccionar(Number(btn.dataset.i) || 0);
      });
      btn.addEventListener("click", function () {
        insertar(Number(btn.dataset.idx));
      });
    });
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

  // Atajo se registra también aquí por si atajos.js se carga antes
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (overlay && !overlay.hidden) cerrar();
      else abrir();
    }
  });
})();
