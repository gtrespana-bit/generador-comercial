/* Activa la hoja completa al terminar de descargarla.
   El CSS del primer viewport está inline en _landing_critical.html, de modo
   que esta carga no bloquea First Paint. Archivo externo para cumplir CSP. */
(function () {
  var sheet = document.getElementById("landing-full-css");
  if (!sheet) return;
  function activate() {
    sheet.removeEventListener("load", activate);
    sheet.rel = "stylesheet";
  }
  sheet.addEventListener("load", activate);
  // Fallback para una respuesta desde caché que haya terminado antes de que
  // el defer registre el listener. No bloquea el primer pintado crítico.
  window.setTimeout(activate, 1500);
})();
