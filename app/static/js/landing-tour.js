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
  var pauseBtn = document.getElementById("tour-pause");

  if (!stage || slides.length === 0) {
    return;
  }

  var current = 0;
  var timer = null;
  var INTERVAL = 6000;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var paused = reduceMotion;

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
    if (paused) {
      return;
    }
    timer = window.setInterval(function () { show(current + 1); }, INTERVAL);
  }

  function updatePauseButton() {
    if (!pauseBtn) {
      return;
    }
    var label = paused ? pauseBtn.getAttribute("data-label-play") : pauseBtn.getAttribute("data-label-pause");
    if (label) {
      pauseBtn.setAttribute("aria-label", label);
      pauseBtn.setAttribute("title", label);
    }
    pauseBtn.textContent = paused ? "▶" : "❚❚";
  }

  if (pauseBtn) {
    pauseBtn.hidden = false;
    updatePauseButton();
    pauseBtn.addEventListener("click", function () {
      paused = !paused;
      updatePauseButton();
      if (paused) {
        stop();
      } else {
        restart();
      }
    });
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
