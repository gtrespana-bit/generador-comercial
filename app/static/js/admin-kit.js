/* Kit del panel de administración (A3/A4): buscador ⌘K y centro de notificaciones.
 * Vanilla JS, sin dependencias externas y compatible con CSP del despliegue.
 * Renderiza con nodos DOM y clases, nunca con fragmentos ni estilos inline. */
(function () {
  "use strict";

  /* ---------- Menú móvil del panel ----------
   *
   * El botón ya está en la plantilla porque el sidebar se convierte en un
   * cajón en pantallas pequeñas. Este controlador mantiene la clase que usa
   * la hoja de estilos y cierra el cajón al navegar, al pulsar Escape o al
   * tocar el fondo. También devuelve el foco al botón para que el menú sea
   * utilizable sin ratón.
   */
  var menuToggle = document.querySelector("[data-menu-toggle]");
  var menuSidebar = document.getElementById("sidebar");
  var menuBackdrop = document.querySelector("[data-menu-fondo]");
  var menuOpen = false;
  var menuFocusPrevious = null;

  function menuEsMovil() {
    if (window.matchMedia) return window.matchMedia("(max-width: 860px)").matches;
    return window.innerWidth <= 860;
  }

  function menuActualizarAccesibilidad() {
    if (!menuSidebar) return;
    // El sidebar sigue siendo la navegación normal en escritorio, pero está
    // fuera del árbol accesible mientras permanece cerrado en móvil.
    menuSidebar.setAttribute("aria-hidden", menuEsMovil() && !menuOpen ? "true" : "false");
    if (menuBackdrop) menuBackdrop.setAttribute("aria-hidden", menuOpen ? "false" : "true");
  }

  function menuCerrar() {
    if (!menuOpen) {
      menuActualizarAccesibilidad();
      return;
    }
    menuOpen = false;
    document.body.classList.remove("menu-abierto");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "Abrir el menú de secciones");
    }
    menuActualizarAccesibilidad();
    if (menuFocusPrevious && typeof menuFocusPrevious.focus === "function") {
      try { menuFocusPrevious.focus(); } catch (_e) { /* nodo fuera del DOM */ }
    }
    menuFocusPrevious = null;
  }

  function menuAbrir() {
    if (menuOpen) return;
    menuOpen = true;
    menuFocusPrevious = document.activeElement;
    document.body.classList.add("menu-abierto");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "true");
      menuToggle.setAttribute("aria-label", "Cerrar el menú de secciones");
    }
    menuActualizarAccesibilidad();

    // El foco entra en el cajón después de aplicar la transición. Si se cierra
    // antes de que termine, no robamos el foco de vuelta al sidebar oculto.
    var primero = menuSidebar && menuSidebar.querySelector("a[href]");
    window.setTimeout(function () {
      if (menuOpen && primero && typeof primero.focus === "function") primero.focus();
    }, 0);
  }

  if (menuToggle && menuSidebar) {
    menuToggle.addEventListener("click", function () {
      if (menuOpen) menuCerrar(); else menuAbrir();
    });
    if (menuBackdrop) menuBackdrop.addEventListener("click", menuCerrar);
    Array.prototype.forEach.call(menuSidebar.querySelectorAll("a[href]"), function (enlace) {
      enlace.addEventListener("click", menuCerrar);
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && menuOpen) menuCerrar();
    });
    window.addEventListener("resize", function () {
      if (!menuEsMovil()) menuCerrar();
      else menuActualizarAccesibilidad();
    });
    menuActualizarAccesibilidad();
  }

  /* ---------- Buscador global ---------- */
  var overlay = document.querySelector("[data-admin-search-overlay]");
  var searchBtn = document.querySelector("[data-admin-search]");
  var input = document.querySelector("[data-admin-search-input]");
  var results = document.querySelector("[data-admin-search-results]");
  var items = [];
  var selIndex = -1;

  function tipoIcono(tipo) {
    switch (tipo) {
      case "cliente": return "🏢";
      case "licencia": return "🔑";
      case "compra": return "💳";
      case "operador": return "👥";
      case "auditoria": return "📜";
      default: return "⋅";
    }
  }

  function vaciar(nodo) {
    while (nodo.firstChild) nodo.removeChild(nodo.firstChild);
  }

  function crearVacio(contenedor, texto) {
    vaciar(contenedor);
    var div = document.createElement("div");
    div.className = "admin-kit-empty";
    div.textContent = texto;
    contenedor.appendChild(div);
  }

  function crearItemBusqueda(r, i) {
    var a = document.createElement("a");
    a.className = "admin-kit-item";
    a.setAttribute("data-i", String(i));
    a.setAttribute("href", r.url || "#");
    a.setAttribute("title", r.subtitulo || r.titulo || "");

    var ico = document.createElement("span");
    ico.className = "ico";
    ico.textContent = tipoIcono(r.tipo);

    var wrapper = document.createElement("span");
    var titulo = document.createElement("b");
    titulo.textContent = r.titulo || "";
    var sub = document.createElement("small");
    sub.textContent = r.subtitulo || "";
    wrapper.appendChild(titulo);
    wrapper.appendChild(sub);

    a.appendChild(ico);
    a.appendChild(wrapper);
    return a;
  }

  function renderItems(lista) {
    if (!results) return;
    items = lista || [];
    selIndex = -1;
    if (!items.length) {
      crearVacio(results, "Sin resultados.");
      return;
    }
    vaciar(results);
    items.forEach(function (r, i) {
      results.appendChild(crearItemBusqueda(r, i));
    });
  }

  function abrirBusqueda() {
    if (!overlay) return;
    overlay.classList.add("open");
    document.body.classList.add("admin-kit-abierto");
    setTimeout(function () { if (input) input.focus(); }, 30);
  }

  function cerrarBusqueda() {
    if (!overlay) return;
    overlay.classList.remove("open");
    document.body.classList.remove("admin-kit-abierto");
    if (input) input.value = "";
    renderItems([]);
  }

  function buscar(q) {
    fetch("/admin/buscar?q=" + encodeURIComponent(q), { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) { renderItems(data.resultados || []); })
      .catch(function () { renderItems([]); });
  }

  var debounce;
  if (searchBtn) searchBtn.addEventListener("click", abrirBusqueda);
  if (overlay && input) {
    input.addEventListener("input", function () {
      clearTimeout(debounce);
      var q = input.value.trim();
      if (!q) { renderItems([]); return; }
      debounce = setTimeout(function () { buscar(q); }, 200);
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown") {
        ev.preventDefault();
        if (selIndex < items.length - 1) selIndex++;
        marcarSeleccion();
      } else if (ev.key === "ArrowUp") {
        ev.preventDefault();
        if (selIndex > 0) selIndex--;
        marcarSeleccion();
      } else if (ev.key === "Enter") {
        var sel = items[selIndex] || items[0];
        if (sel && sel.url) window.location.href = sel.url;
      }
    });
    overlay.addEventListener("click", function (ev) { if (ev.target === overlay) cerrarBusqueda(); });
  }

  function marcarSeleccion() {
    var nodos = results.querySelectorAll(".admin-kit-item");
    Array.prototype.forEach.call(nodos, function (n, i) {
      n.classList.toggle("sel", i === selIndex);
      if (i === selIndex) n.scrollIntoView({ block: "nearest" });
    });
  }

  /* ---------- Navegación por teclado ---------- *
   * Un operador recorre el panel con las manos en el teclado: `/` busca y
   * `g` + letra salta a un área. Las letras salen del `data-atajo` del menú,
   * declarado en app/panel_arquitectura.py: si mañana hay una séptima área, su
   * atajo existe sin tocar este archivo. */
  var atajos = {};
  Array.prototype.forEach.call(document.querySelectorAll("[data-atajo]"), function (enlace) {
    atajos[(enlace.getAttribute("data-atajo") || "").toLowerCase()] = enlace.getAttribute("href");
  });
  var esperandoG = false;
  var temporizadorG;

  function seEstaEscribiendo(ev) {
    var nodo = ev.target;
    if (!nodo || !nodo.tagName) return false;
    var nombre = nodo.tagName.toLowerCase();
    return nombre === "input" || nombre === "textarea" || nombre === "select" || nodo.isContentEditable;
  }

  document.addEventListener("keydown", function (ev) {
    var mod = ev.metaKey || ev.ctrlKey;
    if (mod && (ev.key === "k" || ev.key === "K")) {
      ev.preventDefault();
      overlay && overlay.classList.contains("open") ? cerrarBusqueda() : abrirBusqueda();
      return;
    }
    if (ev.key === "Escape" && overlay && overlay.classList.contains("open")) {
      cerrarBusqueda();
      return;
    }
    if (mod || ev.altKey || seEstaEscribiendo(ev)) return;
    if (ev.key === "/" && overlay) {
      ev.preventDefault();
      abrirBusqueda();
      return;
    }
    if (ev.key === "g" || ev.key === "G") {
      esperandoG = true;
      clearTimeout(temporizadorG);
      temporizadorG = setTimeout(function () { esperandoG = false; }, 1200);
      return;
    }
    if (esperandoG) {
      var destino = atajos[(ev.key || "").toLowerCase()];
      esperandoG = false;
      if (destino) {
        ev.preventDefault();
        window.location.href = destino;
      }
    }
  });

  /* ---------- Centro de notificaciones ---------- */
  var bell = document.querySelector("[data-admin-bell]");
  var bellCount = document.querySelector("[data-admin-bell-count]");
  var bellPop = document.querySelector("[data-admin-bell-pop]");
  var bellList = document.querySelector("[data-admin-bell-list]");

  function crearNotificacion(a) {
    var enlace = document.createElement("a");
    enlace.className = "admin-notify-item";
    enlace.setAttribute("href", a.url || "#");
    enlace.setAttribute("title", a.detalle || a.titulo || "");

    var titulo = document.createElement("b");
    titulo.textContent = a.titulo || "";
    var detalle = document.createElement("small");
    detalle.textContent = a.detalle || "";

    enlace.appendChild(titulo);
    enlace.appendChild(detalle);
    return enlace;
  }

  function renderNotif(avisos) {
    if (!bellList) return;
    if (!avisos || !avisos.length) {
      vaciar(bellList);
      var div = document.createElement("div");
      div.className = "admin-notify-empty";
      div.textContent = "Todo al día. No hay pendientes.";
      bellList.appendChild(div);
      return;
    }
    vaciar(bellList);
    avisos.forEach(function (a) {
      bellList.appendChild(crearNotificacion(a));
    });
  }

  function actualizarContador(avisos) {
    if (!bellCount) return;
    bellCount.textContent = avisos.length;
    if (avisos.length) bellCount.removeAttribute("hidden");
    else bellCount.setAttribute("hidden", "");
  }

  function cargarNotif() {
    fetch("/admin/notificaciones", { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var avisos = data.avisos || [];
        renderNotif(avisos);
        actualizarContador(avisos);
      })
      .catch(function () {});
  }

  if (bell) bell.addEventListener("click", function () {
    /* Solo alterna cuando un clic cierra: la campana siempre recarga al abrir. */
    var abierto = bellPop && bellPop.classList.contains("open");
    if (bellPop) bellPop.classList.toggle("open", !abierto);
    if (!abierto) cargarNotif();
  });

  if (bellList) cargarNotif();

  /* ---------- Confirmación de lo irreversible ---------- *
   * Suspenden, cancelan, revocan o borran: hay que decirlo antes, y se hace aquí
   * y no con un `onsubmit` en el HTML porque la CSP prohíbe el script en línea.
   * Sin JavaScript el formulario sigue enviándose: la confirmación es un extra,
   * nunca un requisito para que la pantalla funcione. */
  var arriesgados = document.querySelectorAll("form[data-confirmar]");
  Array.prototype.forEach.call(arriesgados, function (formulario) {
    formulario.addEventListener("submit", function (ev) {
      var aviso = formulario.getAttribute("data-confirmar");
      if (aviso && !window.confirm(aviso)) ev.preventDefault();
    });
  });
})();
