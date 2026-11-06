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
  /* Consola de comandos (tramo F). `comandos` se pide una vez al abrir la
     paleta y se filtra en memoria: escribir no dispara una petición por tecla.
     `pendiente` guarda el comando de acción que está esperando el segundo
     Enter; sin él, nada que cambie estado sale de aquí. */
  var comandos = [];
  var comandosPedidos = false;
  var pendiente = null;

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

  function iconoComando(c) {
    return c.accion ? "⚡" : "→";
  }

  function crearItemComando(c, i) {
    var a = document.createElement("a");
    a.className = "admin-kit-item comando" + (c.accion ? " accion" : "");
    a.setAttribute("data-i", String(i));
    a.setAttribute("href", c.accion ? "#" : (c.url || "#"));
    a.setAttribute("title", c.descripcion || c.titulo || "");

    var ico = document.createElement("span");
    ico.className = "ico";
    ico.textContent = iconoComando(c);

    var wrapper = document.createElement("span");
    var titulo = document.createElement("b");
    titulo.textContent = c.titulo || "";
    var sub = document.createElement("small");
    sub.textContent = c.descripcion || "";
    wrapper.appendChild(titulo);
    wrapper.appendChild(sub);

    if (c.accion) {
      var etiqueta = document.createElement("kbd");
      etiqueta.className = "admin-kit-accion";
      etiqueta.textContent = "Enter";
      a.appendChild(ico);
      a.appendChild(wrapper);
      a.appendChild(etiqueta);
    } else {
      a.appendChild(ico);
      a.appendChild(wrapper);
    }
    return a;
  }

  function crearGrupo(texto) {
    var h = document.createElement("div");
    h.className = "admin-kit-grupo";
    h.textContent = texto;
    return h;
  }

  function normalizar(texto) {
    return (texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function comandosQueEncajan(q) {
    if (!q) return comandos.slice(0, 6);
    var busca = normalizar(q);
    return comandos.filter(function (c) {
      var pajar = normalizar([c.titulo, c.descripcion, c.grupo].join(" "));
      return pajar.indexOf(busca) !== -1;
    }).slice(0, 6);
  }

  function renderItems(lista, q) {
    if (!results) return;
    var resultados = lista || [];
    var acciones = comandosQueEncajan(q || "");
    // El índice de teclado recorre lo pintado: primero comandos, luego datos.
    items = acciones.concat(resultados);
    selIndex = -1;
    vaciar(results);

    if (!items.length) {
      crearVacio(results, q
        ? "Sin resultados. Prueba con un cliente, una licencia o un comando."
        : "Escribe para buscar, o lanza una acción con ↑↓ y Enter.");
      return;
    }
    if (acciones.length) {
      results.appendChild(crearGrupo("Comandos"));
      acciones.forEach(function (c, i) {
        results.appendChild(crearItemComando(c, i));
      });
    }
    if (resultados.length) {
      results.appendChild(crearGrupo("Resultados"));
      var base = acciones.length;
      resultados.forEach(function (r, i) {
        results.appendChild(crearItemBusqueda(r, base + i));
      });
    }
  }

  function abrirBusqueda() {
    if (!overlay) return;
    overlay.classList.add("open");
    document.body.classList.add("admin-kit-abierto");
    pendiente = null;
    cargarComandos();
    setTimeout(function () { if (input) input.focus(); }, 30);
  }

  function cerrarBusqueda() {
    if (!overlay) return;
    overlay.classList.remove("open");
    document.body.classList.remove("admin-kit-abierto");
    if (input) input.value = "";
    pendiente = null;
    renderItems([]);
  }

  function cargarComandos() {
    if (comandosPedidos) { renderItems([], input ? input.value.trim() : ""); return; }
    comandosPedidos = true;
    fetch("/admin/comandos", { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        comandos = data.comandos || [];
        renderItems([], input ? input.value.trim() : "");
      })
      .catch(function () { comandos = []; });
  }

  function buscar(q) {
    fetch("/admin/buscar?q=" + encodeURIComponent(q), { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) { renderItems(data.resultados || [], q); })
      .catch(function () { renderItems([], q); });
  }

  /* Una acción no se ejecuta con el primer Enter: se pide confirmación y se
     envía un formulario real, para que el servidor haga lo de siempre (CSRF
     por origen, redirect con el mensaje). Nada de rutas nuevas ni de fetch. */
  function confirmarAccion(comando) {
    pendiente = comando;
    vaciar(results);
    var caja = document.createElement("div");
    caja.className = "admin-kit-confirmar";
    var titulo = document.createElement("b");
    titulo.textContent = comando.titulo;
    var texto = document.createElement("p");
    texto.textContent = comando.confirmacion || "Esta acción cambia datos.";
    var pie = document.createElement("div");
    pie.className = "admin-kit-confirmar-pie";
    var si = document.createElement("button");
    si.type = "button";
    si.className = "btn btn-sm btn-primary";
    si.textContent = "Enviar (Enter)";
    si.addEventListener("click", ejecutarPendiente);
    var no = document.createElement("button");
    no.type = "button";
    no.className = "btn btn-sm";
    no.textContent = "Cancelar (Esc)";
    no.addEventListener("click", function () {
      pendiente = null;
      renderItems([], input ? input.value.trim() : "");
    });
    pie.appendChild(si);
    pie.appendChild(no);
    caja.appendChild(titulo);
    caja.appendChild(texto);
    caja.appendChild(pie);
    results.appendChild(caja);
  }

  function ejecutarPendiente() {
    if (!pendiente) return;
    var comando = pendiente;
    pendiente = null;
    var form = document.createElement("form");
    form.method = "post";
    form.action = comando.url;
    form.className = "visualmente-oculto";
    document.body.appendChild(form);
    form.submit();
  }

  var debounce;
  if (searchBtn) searchBtn.addEventListener("click", abrirBusqueda);
  if (overlay && input) {
    input.addEventListener("input", function () {
      clearTimeout(debounce);
      pendiente = null;
      var q = input.value.trim();
      if (!q) { renderItems([], ""); return; }
      debounce = setTimeout(function () { buscar(q); }, 200);
    });
    input.addEventListener("keydown", function (ev) {
      if (pendiente && ev.key === "Enter") {
        ev.preventDefault();
        ejecutarPendiente();
        return;
      }
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
        if (!sel) return;
        if (sel.accion) { confirmarAccion(sel); return; }
        if (sel.url) window.location.href = sel.url;
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
      // Con una acción a medio confirmar, Escape cancela la acción (no la
      // paleta): cerrar de golpe dejaría el «¿envío?» en el aire.
      if (pendiente) {
        pendiente = null;
        renderItems([], input ? input.value.trim() : "");
        return;
      }
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
    /* Un aviso tiene dos destinos posibles: el hecho concreto (este cliente,
       esta compra) y la lista con el mismo criterio. El primero es el enlace
       del aviso; el segundo, un botón pequeño al lado. */
    var fila = document.createElement("div");
    fila.className = "admin-notify-item";

    var enlace = document.createElement("a");
    enlace.className = "admin-notify-destino";
    enlace.setAttribute("href", a.url || "#");
    enlace.setAttribute("title", a.detalle || a.titulo || "");

    var titulo = document.createElement("b");
    titulo.textContent = a.titulo || "";
    var detalle = document.createElement("small");
    detalle.textContent = a.detalle || "";

    enlace.appendChild(titulo);
    enlace.appendChild(detalle);
    fila.appendChild(enlace);

    if (a.url_lista) {
      var lista = document.createElement("a");
      lista.className = "admin-notify-mas";
      lista.setAttribute("href", a.url_lista);
      lista.textContent = a.etiqueta_lista || "Ver la lista";
      fila.appendChild(lista);
    }
    return fila;
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
    if (bellList && !bellList.getAttribute("data-cargado")) {
      vaciar(bellList);
      var espera = document.createElement("div");
      espera.className = "admin-notify-empty";
      espera.textContent = "Leyendo los pendientes…";
      bellList.appendChild(espera);
    }
    fetch("/admin/notificaciones", { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var avisos = data.avisos || [];
        if (bellList) bellList.setAttribute("data-cargado", "1");
        renderNotif(avisos);
        actualizarContador(avisos);
      })
      .catch(function () {
        if (!bellList) return;
        vaciar(bellList);
        var error = document.createElement("div");
        error.className = "admin-notify-empty";
        error.textContent = "No se pudieron leer los avisos. Recarga la página.";
        bellList.appendChild(error);
      });
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

  /* ---------- Modo oscuro ---------- *
   * La preferencia se guarda en localStorage y se aplica como clase
   * .dark-mode en <html>. Sin JS, el panel se ve en modo claro siempre.
   * Solo se activa si el operador lo pide con el botón: el panel ya no sigue
   * `prefers-color-scheme` (lo hacía y dejaba el panel en un modo oscuro a
   * medio hacer, con texto casi invisible; ver la auditoría de 2026-11-06). */
  var darkBtn = document.querySelector("[data-admin-dark]");
  var htmlRoot = document.documentElement;

  function modoOscuroActivo() {
    return htmlRoot.classList.contains("dark-mode");
  }

  function aplicarModoOscuro(activar) {
    if (activar) htmlRoot.classList.add("dark-mode");
    else htmlRoot.classList.remove("dark-mode");
    try {
      localStorage.setItem("cotizat_dark", activar ? "1" : "0");
    } catch (_e) { /* localStorage no disponible */ }
  }

  function cargarModoOscuro() {
    try {
      // Sin preferencia guardada el panel se queda en claro: es el tema que
      // está revisado y el que se ve igual en cualquier equipo del equipo.
      var guardado = localStorage.getItem("cotizat_dark");
      if (guardado === "1") aplicarModoOscuro(true);
    } catch (_e) { /* sin localStorage: modo claro */ }
  }

  if (darkBtn) {
    darkBtn.addEventListener("click", function () {
      aplicarModoOscuro(!modoOscuroActivo());
    });
  }
  cargarModoOscuro();

  /* ---------- Cheatsheet de teclado ---------- *
   * Se abre con `?` y se cierra con Esc, clic fuera o el botón Cerrar. */
  var modal = document.querySelector("[data-admin-cheatsheet-modal]");
  var modalBtn = document.querySelector("[data-admin-cheatsheet]");
  var modalCerrar = document.querySelector("[data-admin-cheatsheet-cerrar]");

  function cheatsheetAbrir() {
    if (!modal) return;
    modal.classList.add("open");
    document.body.classList.add("admin-kit-abierto");
  }

  function cheatsheetCerrar() {
    if (!modal) return;
    modal.classList.remove("open");
    document.body.classList.remove("admin-kit-abierto");
  }

  if (modalBtn) modalBtn.addEventListener("click", cheatsheetAbrir);
  if (modalCerrar) modalCerrar.addEventListener("click", cheatsheetCerrar);
  if (modal) modal.addEventListener("click", function (ev) {
    if (ev.target === modal) cheatsheetCerrar();
  });
  document.addEventListener("keydown", function (ev) {
    if (!modal) return;
    if (ev.key === "?" && !seEstaEscribiendo(ev)) {
      ev.preventDefault();
      modal.classList.contains("open") ? cheatsheetCerrar() : cheatsheetAbrir();
    }
    if (ev.key === "Escape" && modal && modal.classList.contains("open")) {
      cheatsheetCerrar();
    }
  });
})();

/* ------------------------------------------------------------------------- *
 * Barra de progreso de navegación.
 *
 * El panel se pinta en el servidor: al pulsar un enlace, el navegador se queda
 * en la página anterior hasta que llega la siguiente. En un panel con tablas
 * pesadas eso son varios cientos de milisegundos sin ninguna señal, y el
 * operador vuelve a pulsar. Tres píxeles arriba bastan para que sepa que el
 * clic contó.
 *
 * No es un «esqueleto» de tarjetas grises a propósito: aquí no llegan datos
 * después del HTML, así que un esqueleto sería decorado que miente.
 * ------------------------------------------------------------------------- */
(function () {
  "use strict";

  var barra = null;

  function crear() {
    if (barra) return barra;
    barra = document.createElement("div");
    barra.className = "barra-carga";
    barra.setAttribute("data-estado", "listo");
    barra.setAttribute("aria-hidden", "true");
    document.body.appendChild(barra);
    return barra;
  }

  function marcar(estado) {
    crear().setAttribute("data-estado", estado);
  }

  function contenido() {
    return document.getElementById("contenido");
  }

  function ocupado(activo) {
    var main = contenido();
    if (!main) return;
    if (activo) main.setAttribute("aria-busy", "true");
    else main.removeAttribute("aria-busy");
  }

  function esNavegacion(ev, enlace) {
    if (!enlace || !enlace.getAttribute) return false;
    if (ev.defaultPrevented || ev.button !== 0) return false;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return false;
    if (enlace.target && enlace.target !== "_self") return false;
    if (enlace.hasAttribute("download")) return false;
    var destino = enlace.getAttribute("href") || "";
    if (!destino || destino.charAt(0) === "#") return false;
    if (/^(mailto|tel|javascript):/i.test(destino)) return false;
    var url;
    try {
      url = new URL(enlace.href, window.location.href);
    } catch (error) {
      return false;
    }
    if (url.origin !== window.location.origin) return false;
    // Misma página, solo otro hash: no hay recarga.
    if (url.pathname === window.location.pathname && url.search === window.location.search) {
      return false;
    }
    return true;
  }

  document.addEventListener("click", function (ev) {
    var enlace = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!esNavegacion(ev, enlace)) return;
    marcar("cargando");
    ocupado(true);
  });

  function terminar() {
    if (!barra) return;
    marcar("listo");
    ocupado(false);
    window.setTimeout(function () {
      if (barra) barra.setAttribute("data-estado", "");
    }, 260);
  }

  window.addEventListener("pageshow", terminar);
  window.addEventListener("beforeunload", function () {
    if (barra) barra.setAttribute("data-estado", "listo");
  });
})();
