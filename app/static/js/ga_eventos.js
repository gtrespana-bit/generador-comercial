/* Medición GA4: eventos de clic no intrusivos.
 *
 * Se dispara solo cuando la etiqueta está activa (ga_eventos.js se carga
 * desde _ga.html únicamente si COTIZAT_GA_ID está definida). Traduce dos
 * convenciones de atributos:
 *
 *  - data-ga-event="nombre" → gtag('event', 'nombre') directamente.
 *  - data-cotizat-click="acción" → se traduce desde POR_ACCION (la
 *    convención preexistente de clics internos), solo para las acciones
 *    con interés de negocio: descarga/impresión de PDF.
 */
(function () {
  "use strict";

  var POR_ACCION = {
    "download-pdf": "pdf_descargado",
    "print-pdf": "pdf_impreso"
  };

  function enviar(nombre) {
    if (typeof window.gtag === "function") {
      window.gtag("event", nombre);
    }
  }

  document.addEventListener(
    "click",
    function (ev) {
      var objetivo = ev.target;
      if (!objetivo || typeof objetivo.closest !== "function") return;
      var el = objetivo.closest("[data-ga-event],[data-cotizat-click]");
      if (!el) return;
      var directo = el.getAttribute("data-ga-event");
      if (directo) {
        enviar(directo);
        return;
      }
      var accion = el.getAttribute("data-cotizat-click");
      if (accion && POR_ACCION[accion]) {
        enviar(POR_ACCION[accion]);
      }
    },
    true
  );
})();
