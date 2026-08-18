/* Tour animado de la landing.
 *
 * Muestra las pantallas del producto en un carrusel con avance automático,
 * botones anterior/siguiente y puntos de progreso. Solo usa classList y
 * addEventListener, sin inyección de HTML ni estilos en línea, por lo que
 * cumple la CSP y la auditoría de inyección del proyecto.
 */
(function () {
  var stage = document.getElementById("tour-stage");
  var slides = document.querySelectorAll(".tour-slide");
  var dots = document.querySelectorAll(".tour-dot");
  var prev = document.getElementById("tour-prev");
  var next = document.getElementById("tour-next");

  if (!stage || slides.length === 0) {
    return;
  }

  var current = 0;
  var timer = null;
  var INTERVAL = 6000;

  function show(index) {
    var n = slides.length;
    current = ((index % n) + n) % n;
    for (var i = 0; i < n; i++) {
      slides[i].classList.toggle("active", i === current);
    }
    for (var j = 0; j < dots.length; j++) {
      dots[j].classList.toggle("active", j === current);
      dots[j].setAttribute("aria-selected", j === current ? "true" : "false");
    }
    restart();
  }

  function stop() {
    if (timer) {
      window.clearInterval(timer);
      timer = null;
    }
  }

  function restart() {
    stop();
    timer = window.setInterval(function () { show(current + 1); }, INTERVAL);
  }

  if (prev) {
    prev.addEventListener("click", function () { show(current - 1); });
  }
  if (next) {
    next.addEventListener("click", function () { show(current + 1); });
  }
  for (var k = 0; k < dots.length; k++) {
    (function (idx) {
      dots[idx].addEventListener("click", function () { show(idx); });
    })(k);
  }

  stage.addEventListener("mouseenter", stop);
  stage.addEventListener("mouseleave", restart);
  stage.addEventListener("focusin", stop);
  stage.addEventListener("focusout", restart);

  show(0);
})();
