/* Panel de analítica (/admin/analitica).
 *
 * Solo una cosa: filtrar la tabla de eventos recientes por texto y acción.
 * Sigue las reglas del proyecto: classList/addEventListener, sin nodos HTML
 * dinámicos ni estilos en línea (CSP estricta). Sin este script la tabla se ve
 * completa, nunca inaccesible.
 */
(function () {
  "use strict";

  var tabla = document.getElementById("tabla-eventos");
  var buscar = document.getElementById("buscar-evento");
  var filtro = document.getElementById("filtro-accion");

  if (!tabla || !buscar || !filtro) {
    return;
  }

  var filas = Array.prototype.slice.call(
    tabla.querySelectorAll("tbody tr[data-accion]")
  );

  function aplicar() {
    var texto = buscar.value.trim().toLowerCase();
    var accion = filtro.value;
    filas.forEach(function (fila) {
      var visible =
        (!accion || fila.getAttribute("data-accion") === accion) &&
        (!texto || (fila.getAttribute("data-texto") || "").indexOf(texto) !== -1);
      fila.classList.toggle("oculta", !visible);
    });
  }

  buscar.addEventListener("input", aplicar);
  filtro.addEventListener("change", aplicar);
})();
