/* Landing «Impulso»: microcompromisos, valor antes del alta y medición.
 *
 * Reglas deliberadas:
 * - Solo textContent / classList / atributos: nunca se inyecta marcado ni
 *   se escriben estilos en línea. La CSP del proyecto prohíbe ambos.
 * - La calculadora usa exclusivamente los números que escribe el visitante.
 *   No inventa ahorros, no envía nada a ningún servidor y no promete un
 *   porcentaje de mejora.
 * - Los eventos GA4 son opcionales: si no hay gtag configurado, no pasa nada.
 * - La intención y la variante viajan en la URL del CTA, no en cookies: la
 *   landing se sirve desde CDN y debe seguir siendo idéntica por visita.
 */
(function () {
  "use strict";

  function ga(nombre, params) {
    if (typeof window.gtag === "function") {
      window.gtag("event", nombre, params || {});
    }
  }

  function texto(id, valor) {
    var el = document.getElementById(id);
    if (el) el.textContent = valor;
  }

  /* ── 1. Autosegmentación: el CTA habla el idioma del problema elegido ─── */
  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-lp2-intent]"));
  var etiquetas = Array.prototype.slice.call(document.querySelectorAll("[data-lp2-cta-label]"));
  var enlaces = Array.prototype.slice.call(document.querySelectorAll("a[data-lp2-cta]"));

  function aplicarIntencion(chip) {
    var valor = chip.getAttribute("data-lp2-intent") || "";
    var copia = chip.getAttribute("data-lp2-copy") || "";
    var cta = chip.getAttribute("data-lp2-cta") || "";
    for (var i = 0; i < chips.length; i++) {
      chips[i].classList.toggle("is-active", chips[i] === chip);
      chips[i].setAttribute("aria-pressed", chips[i] === chip ? "true" : "false");
    }
    texto("lp2-intent-copy", copia);
    for (var j = 0; j < etiquetas.length; j++) {
      if (cta) etiquetas[j].textContent = cta;
    }
    for (var k = 0; k < enlaces.length; k++) {
      var a = enlaces[k];
      try {
        var url = new URL(a.getAttribute("href"), window.location.origin);
        if (valor) url.searchParams.set("intencion", valor);
        else url.searchParams.delete("intencion");
        a.setAttribute("href", url.pathname + url.search + url.hash);
      } catch (_) {
        /* Un href relativo sencillo no debería fallar; si lo hace, se deja
           tal cual antes que romper la navegación del CTA. */
      }
    }
    ga("landing_intencion", {intencion: valor});
  }

  for (var c = 0; c < chips.length; c++) {
    chips[c].setAttribute("aria-pressed", chips[c].classList.contains("is-active") ? "true" : "false");
    chips[c].addEventListener("click", function () { aplicarIntencion(this); });
  }

  /* ── 2. Valor antes del registro: coste de oportunidad con datos propios ─ */
  var presupuestos = document.getElementById("lp2-presupuestos");
  var horas = document.getElementById("lp2-horas");
  var calculado = false;

  function numero(input, minimo, maximo) {
    var n = parseFloat(String((input && input.value) || "").replace(",", "."));
    if (!isFinite(n)) return minimo;
    return Math.min(maximo, Math.max(minimo, n));
  }

  function calcular() {
    if (!presupuestos || !horas) return;
    var porSemana = numero(presupuestos, 0, 200);
    var porPresupuesto = numero(horas, 0, 40);
    var alMes = Math.round(porSemana * porPresupuesto * 4.33);
    var formato = new Intl.NumberFormat("es", {maximumFractionDigits: 0});
    texto("lp2-horas-perdidas", formato.format(alMes) + " h/mes");
    texto(
      "lp2-calc-frase",
      alMes === 0
        ? "Ajusta los datos para ver el tamaño real del problema."
        : "Son tus números, no una promesa nuestra: tiempo que hoy se va en armar, revisar y rehacer presupuestos."
    );
    var boton = document.getElementById("lp2-calc-cta-label");
    if (boton) boton.textContent = alMes > 0 ? "Quiero recuperar esas horas" : "Quiero preparar mi próximo presupuesto";
    if (!calculado && alMes > 0) {
      calculado = true;
      ga("landing_calculo_tiempo", {horas_mes: alMes});
    }
  }

  if (presupuestos && horas) {
    ["input", "change"].forEach(function (evento) {
      presupuestos.addEventListener(evento, calcular);
      horas.addEventListener(evento, calcular);
    });
    calcular();
  }

  /* ── 3. CTA persistente: aparece solo cuando el hero ya no está visible ─ */
  var hero = document.getElementById("lp2-hero");
  var sticky = document.getElementById("lp2-sticky");
  if (hero && sticky && "IntersectionObserver" in window) {
    var observador = new IntersectionObserver(function (entradas) {
      var visible = entradas.some(function (entrada) { return entrada.isIntersecting; });
      sticky.classList.toggle("is-visible", !visible);
      sticky.setAttribute("aria-hidden", visible ? "true" : "false");
      var enlace = sticky.querySelector("a");
      if (enlace) enlace.setAttribute("tabindex", visible ? "-1" : "0");
    }, {threshold: 0.08});
    observador.observe(hero);
  }

  /* ── 4. Profundidad de lectura: una señal por tramo, sin identificadores ─ */
  var tramos = [25, 50, 75, 90];
  var enviados = Object.create(null);
  window.addEventListener("scroll", function () {
    var doc = document.documentElement;
    var total = doc.scrollHeight - window.innerHeight;
    if (total <= 0) return;
    var porcentaje = Math.round((window.scrollY / total) * 100);
    for (var i = 0; i < tramos.length; i++) {
      if (porcentaje >= tramos[i] && !enviados[tramos[i]]) {
        enviados[tramos[i]] = true;
        ga("landing_scroll", {profundidad: tramos[i]});
      }
    }
  }, {passive: true});
})();
