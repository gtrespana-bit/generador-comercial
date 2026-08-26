/* Menú móvil — hoja inferior con TODAS las secciones de la aplicación.
 *
 * El botón «Menú» de la barra inferior abre esta hoja. Las secciones NO se
 * duplican en la plantilla: se clonan del sidebar (#app-sidebar nav), que
 * sigue siendo la única fuente de verdad de la navegación (incluye los
 * condicionales de rol como «Equipo» y el estado activo de la sección).
 *
 * Compatible con la CSP estricta: sin estilos en línea (atributos hidden y
 * clases), sin manejadores inline y sin inyección de HTML dinámico.
 */
(function () {
  "use strict";

  var btn = document.getElementById("boton-menu-movil");
  var sheet = document.getElementById("menu-movil");
  if (!btn || !sheet) return;

  var backdrop = document.getElementById("menu-movil-backdrop");
  var filtro = document.getElementById("menu-movil-filtro");
  var vacio = document.getElementById("menu-movil-vacio");
  var contenedor = document.getElementById("menu-movil-nav");
  var cuerpo = sheet.querySelector(".menu-movil-cuerpo");
  var abierto = false;
  var focoPrevio = null;

  /* ── Clonar la navegación del sidebar ──────────────────────────────── */
  if (contenedor) {
    var navOriginal = document.querySelector("#app-sidebar nav");
    if (navOriginal) {
      var clon = navOriginal.cloneNode(true);
      clon.removeAttribute("id");
      // Sin ids duplicados en el documento (el clon vive en otra capa).
      Array.prototype.forEach.call(clon.querySelectorAll("[id]"), function (n) {
        n.removeAttribute("id");
      });
      contenedor.appendChild(clon);
      Array.prototype.forEach.call(clon.querySelectorAll("a"), function (a) {
        a.addEventListener("click", function () { cerrar(); });
      });
    }
  }

  // Punto dorado en «Menú»: avisa de que la sección actual no tiene pestaña
  // propia en la barra inferior (p. ej. Recursos, Cobros o Configuración) y
  // se llega a ella desde aquí.
  if (!document.querySelector(".bottom-nav a.active")) {
    btn.classList.add("menu-fuera-seccion");
  }

  /* ── Abrir / cerrar ────────────────────────────────────────────────── */
  function abrir() {
    if (abierto) return;
    abierto = true;
    focoPrevio = document.activeElement;
    document.body.classList.add("menu-movil-abierto");
    sheet.classList.add("abierto");
    sheet.setAttribute("aria-hidden", "false");
    btn.setAttribute("aria-expanded", "true");
    if (backdrop) backdrop.classList.add("abierto");
    // Llevar a la vista la sección actual dentro de la hoja.
    if (cuerpo) {
      var activo = contenedor && contenedor.querySelector("a.active");
      if (activo && activo.scrollIntoView) {
        try { activo.scrollIntoView({ block: "nearest" }); } catch (_e) { /* viejo */ }
      } else {
        cuerpo.scrollTop = 0;
      }
    }
    if (filtro) {
      filtro.value = "";
      aplicarFiltro("");
      // Tras la animación, para no partir el foco a mitad de transición.
      window.setTimeout(function () {
        if (abierto && filtro && !filtro.disabled) filtro.focus();
      }, 260);
    }
  }

  function cerrar() {
    if (!abierto) return;
    abierto = false;
    document.body.classList.remove("menu-movil-abierto");
    sheet.classList.remove("abierto");
    sheet.setAttribute("aria-hidden", "true");
    btn.setAttribute("aria-expanded", "false");
    if (backdrop) backdrop.classList.remove("abierto");
    if (focoPrevio && typeof focoPrevio.focus === "function") {
      try { focoPrevio.focus(); } catch (_e) { /* nodo fuera del DOM */ }
    }
    focoPrevio = null;
  }

  btn.addEventListener("click", function () {
    if (abierto) cerrar(); else abrir();
  });
  if (backdrop) backdrop.addEventListener("click", cerrar);
  Array.prototype.forEach.call(sheet.querySelectorAll("[data-menu-cerrar]"), function (b) {
    b.addEventListener("click", cerrar);
  });
  // Cerrar al usar cualquier acción del pie (cuenta, tema no; salir navega).
  Array.prototype.forEach.call(sheet.querySelectorAll(".menu-movil-pie a"), function (a) {
    a.addEventListener("click", cerrar);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && abierto) cerrar();
  });

  /* ── Arrastrar la hoja hacia abajo (cabecera/asidero) para cerrar ──── */
  var cabecera = sheet.querySelector(".menu-movil-head");
  if (cabecera && window.PointerEvent) {
    var arrastrando = false;
    var y0 = 0;
    var dy = 0;
    cabecera.addEventListener("pointerdown", function (e) {
      if (!abierto) return;
      arrastrando = true;
      y0 = e.clientY;
      dy = 0;
      sheet.classList.add("arrastrando");
      if (cabecera.setPointerCapture) {
        try { cabecera.setPointerCapture(e.pointerId); } catch (_e) { /* viejo */ }
      }
    });
    cabecera.addEventListener("pointermove", function (e) {
      if (!arrastrando) return;
      dy = Math.max(0, e.clientY - y0);
      // Misma vía CSP que el resto de la app: nunca el atributo style.
      if (window.CotizatStyles) {
        CotizatStyles.set(sheet, "transform", "translateY(" + dy + "px)");
      }
    });
    function soltar() {
      if (!arrastrando) return;
      arrastrando = false;
      sheet.classList.remove("arrastrando");
      if (dy > 90) {
        // Se libera el transform DESPUÉS de cerrar: la transición arranca
        // desde el punto arrastrado y la hoja sigue el dedo hasta abajo.
        cerrar();
      }
      if (window.CotizatStyles) CotizatStyles.set(sheet, "transform", "");
    }
    cabecera.addEventListener("pointerup", soltar);
    cabecera.addEventListener("pointercancel", soltar);
  }

  // Si se rota a horizontal grande o se abre en escritorio, la hoja sobra.
  var mq = window.matchMedia("(min-width: 769px)");
  var alCambiar = function (ev) { if (ev.matches) cerrar(); };
  if (mq.addEventListener) mq.addEventListener("change", alCambiar);
  else if (mq.addListener) mq.addListener(alCambiar);

  /* ── Trampa de foco dentro de la hoja ──────────────────────────────── */
  sheet.addEventListener("keydown", function (e) {
    if (e.key !== "Tab" || !abierto) return;
    var focables = sheet.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    var visibles = [];
    Array.prototype.forEach.call(focables, function (el) {
      if (el.getClientRects().length > 0) visibles.push(el);
    });
    if (!visibles.length) return;
    var primero = visibles[0];
    var ultimo = visibles[visibles.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  });

  /* ── Filtro de secciones (ignora tildes y mayúsculas) ──────────────── */
  function normalizar(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function aplicarFiltro(consulta) {
    if (!contenedor) return;
    var q = normalizar(consulta.trim());
    var enlaces = contenedor.querySelectorAll("a");
    var visibles = 0;
    Array.prototype.forEach.call(enlaces, function (a) {
      var texto = normalizar(
        (a.textContent || "") + " " + (a.getAttribute("data-label") || "")
      );
      var coincide = !q || texto.indexOf(q) !== -1;
      a.hidden = !coincide;
      if (coincide) visibles += 1;
    });
    // Un título de grupo se oculta si no queda ninguna sección visible debajo.
    Array.prototype.forEach.call(contenedor.querySelectorAll(".nav-section"), function (titulo) {
      var visiblesEnGrupo = 0;
      var nodo = titulo.nextElementSibling;
      while (nodo && !nodo.classList.contains("nav-section")) {
        if (nodo.tagName === "A" && !nodo.hidden) visiblesEnGrupo += 1;
        nodo = nodo.nextElementSibling;
      }
      titulo.hidden = visiblesEnGrupo === 0;
    });
    if (vacio) vacio.hidden = visibles > 0;
  }

  if (filtro) {
    filtro.addEventListener("input", function () {
      aplicarFiltro(filtro.value);
    });
    // «Buscar» en el teclado del móvil no debe enviar nada: solo limpiar.
    filtro.addEventListener("search", function () {
      aplicarFiltro(filtro.value);
    });
    filtro.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        var primera = contenedor && contenedor.querySelector("a:not([hidden])");
        if (primera) {
          cerrar();
          window.location.href = primera.getAttribute("href");
        }
      }
    });
  }
})();
