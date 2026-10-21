/* Panel de analítica (/admin/analitica).
 *
 * Dos mejoras de lectura, ninguna imprescindible: el panel se ve completo sin
 * este archivo (los filtros son del servidor y funcionan con GET).
 *
 * 1. «Actualizar solo»: recarga la página cada minuto para que la presencia
 *    en vivo no envejezca mientras el operador la mira.
 * 2. «hace N min»: avanza el contador de las empresas en línea sin recargar,
 *    para no depender de que la página se refresque.
 *
 * Reglas del proyecto: classList/addEventListener, sin nodos HTML dinámicos
 * ni estilos en línea (CSP estricta).
 */
(function () {
  "use strict";

  var CLAVE = "cotizat.analitica.auto";

  /* ---------- 1. Recarga automática ---------- */

  var casilla = document.getElementById("auto-refresh");

  function recordar(activo) {
    try {
      window.localStorage.setItem(CLAVE, activo ? "1" : "0");
    } catch (error) {
      /* modo privado sin almacenamiento: la preferencia dura la visita */
    }
  }

  function recordado() {
    try {
      return window.localStorage.getItem(CLAVE) === "1";
    } catch (error) {
      return false;
    }
  }

  if (casilla) {
    casilla.checked = recordado();
    casilla.addEventListener("change", function () {
      recordar(casilla.checked);
      if (casilla.checked) {
        window.setTimeout(function () {
          window.location.reload();
        }, 60000);
      }
    });
    if (casilla.checked) {
      window.setTimeout(function () {
        window.location.reload();
      }, 60000);
    }
  }

  /* ---------- 2. Contador «hace N min» ---------- */

  var marcas = Array.prototype.slice.call(
    document.querySelectorAll("[data-hace]")
  );

  if (!marcas.length) {
    return;
  }

  function pintar() {
    marcas.forEach(function (nodo) {
      var base = parseInt(nodo.getAttribute("data-hace"), 10);
      if (isNaN(base)) {
        return;
      }
      var minutos = base + Math.floor((Date.now() - inicio) / 60000);
      if (minutos < 1) {
        nodo.textContent = "ahora mismo";
      } else if (minutos === 1) {
        nodo.textContent = "hace 1 min";
      } else {
        nodo.textContent = "hace " + minutos + " min";
      }
    });
  }

  var inicio = Date.now();
  window.setInterval(pintar, 30000);
})();
