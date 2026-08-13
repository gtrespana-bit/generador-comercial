(function () {
  "use strict";

  var handlers = Object.create(null);

  function register(name, handler) {
    if (!/^[a-z0-9-]{1,80}$/.test(String(name || "")) || typeof handler !== "function") {
      throw new Error("Acción declarativa no válida");
    }
    handlers[name] = handler;
  }

  function dispatch(event, attribute) {
    var target = event.target && event.target.closest
      ? event.target.closest("[" + attribute + "]")
      : null;
    if (!target) return;
    var name = target.getAttribute(attribute) || "";
    var handler = handlers[name];
    if (typeof handler === "function") handler(target, event);
  }

  window.CotizatActions = {register: register};
  document.addEventListener("click", function (event) {
    dispatch(event, "data-cotizat-click");
  });
  document.addEventListener("change", function (event) {
    dispatch(event, "data-cotizat-change");
  });
  document.addEventListener("input", function (event) {
    dispatch(event, "data-cotizat-input");
  });
  document.addEventListener("keyup", function (event) {
    dispatch(event, "data-cotizat-keyup");
  });
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("form[data-confirm]");
    if (form && !window.confirm(form.getAttribute("data-confirm") || "¿Continuar?")) {
      event.preventDefault();
    }
  });

  register("stop-propagation", function (_element, event) {
    event.stopPropagation();
  });
  register("download-pdf", function (element, event) {
    if (typeof window.descargarPDF === "function") {
      window.descargarPDF(event, element.href, element.getAttribute("download") || "documento.pdf");
    }
  });
  register("print-pdf", function (element) {
    if (typeof window.imprimirPDF === "function") {
      window.imprimirPDF(element.dataset.url || "");
    }
  });
  register("window-print", function () {
    window.print();
  });
  register("scroll-target", function (element) {
    var target = document.getElementById(element.dataset.target || "");
    if (target) target.scrollIntoView({behavior: "smooth"});
  });
  register("submit-nearest-form", function (element) {
    var form = element.closest(".card");
    form = form && form.querySelector("form");
    if (form) form.requestSubmit();
  });
  register("show-color-value", function (element) {
    var output = element.nextElementSibling;
    if (output) output.textContent = String(element.value || "").toUpperCase();
  });
  register("show-logo-width", function (element) {
    var output = document.getElementById("logo_ancho_val");
    if (output) output.textContent = String(element.value || "") + " pt";
  });
})();
