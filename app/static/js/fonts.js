/* Carga no bloqueante de la tipografía (Inter).

 * El <link> a Google Fonts en el <head> bloqueaba el primer pintado: el
 * navegador esperaba la respuesta de fonts.googleapis.com (un tercero que
 * puede ir lento) antes de dibujar nada. Este script inyecta la hoja de
 * estilos en caliente, así el texto se pinta al instante con la fuente del
 * sistema y cambia a Inter cuando llega (la hoja usa font-display: swap).

 * El preconnect a fonts.googleapis.com / fonts.gstatic.com se conserva en el
 * <head> para que la descarga posterior sea rápida.
 */
(function () {
  "use strict";

  // Respetar a quien pide ahorrar datos.
  if (window.matchMedia && window.matchMedia("(prefers-reduced-data: reduce)").matches) {
    return;
  }
  if (document.getElementById("cotizat-fonts")) return;

  var link = document.createElement("link");
  link.id = "cotizat-fonts";
  link.rel = "stylesheet";
  link.href =
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap";
  document.head.appendChild(link);
})();
