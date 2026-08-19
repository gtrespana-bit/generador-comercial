/* Selector de país para la landing adaptativa (Semana 1 — LatAm).
 *
 * Sin inyección HTML ni estilos inline: solo textContent, class y
 * atributos. El servidor ya renderiza el país correcto si viene por
 * ?pais= o por cookie; este script solo hace el cambio instantáneo en
 * cliente, persiste la elección (cookie + localStorage) y mantiene la
 * URL sincronizada sin recargar.
 */
(function () {
  var select = document.getElementById("pais-select");
  var hint = document.getElementById("pais-bar-hint");
  var dataEl = document.getElementById("paises-data");
  var actualEl = document.getElementById("pais-actual-data");
  var genericoEl = document.getElementById("pais-generico-data");

  if (!select || !dataEl) return;

  var paises = [];
  var generico = null;
  try { paises = JSON.parse(dataEl.textContent || "[]"); } catch (_) { paises = []; }
  try { generico = JSON.parse(genericoEl ? genericoEl.textContent : "null"); } catch (_) { generico = null; }
  if (!generico) generico = { codigo: "", nombre: "Latinoamérica", bandera: "🌎", moneda: "USD", simbolo_local: "$", iva: 16, id_fiscal: "ID fiscal", vocab: "concreto, friso, cielo raso, rodapié, plomero", mercado: "latinoamericano", gentilicio: "latinoamericano" };

  var mapa = {};
  for (var i = 0; i < paises.length; i++) mapa[paises[i].codigo] = paises[i];

  function aplicarPais(codigo, opts) {
    var persist = !(opts && opts.persist === false);
    var p = codigo ? mapa[codigo] : null;

    // Textos dinámicos por id
    var kicker = document.getElementById("hero-kicker");
    var bannerH2 = document.getElementById("banner-h2");
    var bannerP = document.getElementById("banner-p");
    var bannerVocab = document.getElementById("banner-vocab");
    var bannerMoneda = document.getElementById("banner-moneda");
    var fiscalH3 = document.getElementById("fiscal-h3");
    var fiscalP = document.getElementById("fiscal-p");
    var franjaH2 = document.getElementById("franja-h2");
    var franjaIntro = document.getElementById("franja-intro");
    var franjaPrecioP = document.getElementById("franja-precio-p");
    var franjaVocabP = document.getElementById("franja-vocab-p");

    if (p) {
      if (kicker) kicker.textContent = p.bandera + " Hecho para " + p.nombre + " · Construcción y remodelación";
      if (bannerH2) bannerH2.textContent = "El catálogo más completo para presupuestar en " + p.nombre + ".";
      if (bannerP) bannerP.textContent = document.querySelector("#banner-p") ? bannerP.textContent : "";
      // Reconstruir bannerP con cifras dinámicas si existen
      if (bannerP) {
        var cifrasEl = document.querySelector(".banner-cifras");
        // Mantener el formato pero actualizar mercado
        // El número de partidas viene renderizado; solo cambiamos mercado
        var txt = bannerP.textContent || "";
        // Si el texto aún es genérico, lo reescribimos completo con mercado
        if (txt.indexOf("Latinoamérica") !== -1 || txt.indexOf(p.mercado) === -1) {
          var partidasTxt = "";
          var capitulosTxt = "";
          try {
            var c1 = document.querySelector(".banner-cifras .cifra strong");
            if (c1) partidasTxt = c1.textContent.trim();
          } catch (_) {}
          // Fallback: extraer del DOM original o usar genérico
          bannerP.textContent = (partidasTxt ? partidasTxt : "3.000") + " partidas organizadas con precios en USD de referencia contrastados con el mercado " + p.mercado + " y en revisión continua. No empiezas de cero: llegas con una base de precios real y propia.";
          // Ajuste fino: si no pudimos leer, mantén el texto anterior pero reemplaza mercado
          if (!partidasTxt && txt) {
            bannerP.textContent = txt.replace("Latinoamérica", p.nombre).replace("latinoamericano", p.mercado).replace("venezolano", p.mercado).replace("mercado latinoamericano", "mercado " + p.mercado);
            if (bannerP.textContent.indexOf(p.mercado) === -1) {
              bannerP.textContent = "Más de 3.000 partidas organizadas con precios en USD de referencia contrastados con el mercado " + p.mercado + " y en revisión continua. No empiezas de cero: llegas con una base de precios real y propia.";
            }
          }
        }
      }
      if (bannerVocab) bannerVocab.textContent = "✓ Terminología de " + p.nombre + ": " + p.vocab + ".";
      // bannerMoneda contiene un span check, preservarlo
      if (bannerMoneda) {
        var monedaTxt = "✓ Precios en USD de referencia";
        if (p.moneda !== "USD") monedaTxt += " · convierte a " + p.moneda + " (" + p.simbolo_local + ") en tu presupuesto";
        else monedaTxt += ".";
        bannerMoneda.textContent = monedaTxt;
      }
      // Fiscal
      var fiscalIcon = document.querySelector("#fiscal-card .icon");
      if (fiscalIcon) fiscalIcon.textContent = p.bandera;
      if (fiscalH3) fiscalH3.textContent = "Fiscal a tu medida · " + p.nombre;
      if (fiscalP) fiscalP.textContent = "IVA " + p.iva + "%, " + p.id_fiscal + ", retención, operación exenta, número de control y cláusula cambiaria. Moneda " + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + " o USD, con tasa de referencia.";
      // Franja
      if (franjaH2) franjaH2.textContent = "Pensado para " + p.nombre + ", no adaptado después.";
      if (franjaIntro) franjaIntro.textContent = "No es una herramienta genérica traducida. CotizaT habla el idioma de la obra en " + p.nombre + ": precios, vocabulario y fiscalidad de aquí.";
      if (franjaPrecioP) franjaPrecioP.textContent = "Cotiza en " + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + " o en USD como referencia regional. Sin conversiones improvisadas: tu tasa queda guardada en cada presupuesto.";
      if (franjaVocabP) franjaVocabP.textContent = p.vocab + ", y todos los nombres que usa tu cliente y tu cuadrilla en " + p.nombre + ", no los de otro país.";
      if (hint) hint.textContent = p.bandera + " Mostrando contenido para " + p.nombre + " · " + p.id_fiscal + " · IVA " + p.iva + "%";
      // Título y meta description (opcional, sin recargar)
      try { document.title = "CotizaT — Presupuestos de construcción y remodelación para " + p.nombre; } catch (_) {}
      var meta = document.querySelector('meta[name="description"]');
      if (meta) meta.setAttribute("content", "Presupuestos de obra profesionales en minutos. Más de 3.000 partidas clasificadas con precios en USD contrastados con el mercado " + p.mercado + ". PDF con tu logo, versiones, aprobaciones y cobros.");
    } else {
      if (kicker) kicker.textContent = "🌎 Hecho para Latinoamérica · Construcción y remodelación";
      if (bannerH2) bannerH2.textContent = "El catálogo más completo para presupuestar en Latinoamérica.";
      if (bannerP) bannerP.textContent = "Más de 3.000 partidas organizadas con precios en USD de referencia para Latinoamérica y en revisión continua. No empiezas de cero: llegas con una base de precios real y propia.";
      if (bannerVocab) bannerVocab.textContent = "✓ Terminología hispana neutra con variantes locales: elige tu país y adapta los nombres.";
      if (bannerMoneda) bannerMoneda.textContent = "✓ Precios en USD de referencia · convierte a tu moneda local en cada presupuesto.";
      var fi = document.querySelector("#fiscal-card .icon");
      if (fi) fi.textContent = "🌎";
      if (fiscalH3) fiscalH3.textContent = "Fiscal a tu medida · Latinoamérica";
      if (fiscalP) fiscalP.textContent = "IVA configurable por país, tu ID fiscal (RIF, NIT, RUT, CUIT, RUC, RFC…), retención, operación exenta y cláusula cambiaria. Moneda en tu divisa local o USD, con tasa de referencia.";
      if (franjaH2) franjaH2.textContent = "Pensado para Latinoamérica, no adaptado después.";
      if (franjaIntro) franjaIntro.textContent = "No es una herramienta genérica. CotizaT nace para construir en Latinoamérica: precios en USD de referencia, vocabulario hispano y fiscalidad configurable por país.";
      if (franjaPrecioP) franjaPrecioP.textContent = "Cotiza en USD como referencia regional o en tu moneda local (COP, MXN, PEN, CLP, ARS…). Tu tasa de referencia queda guardada en cada presupuesto.";
      if (franjaVocabP) franjaVocabP.textContent = "Concreto/hormigón, friso/revoque, cielo raso/cielorraso, rodapié/zócalo, plomero/gasfíter… Elige tu país y la landing habla tu obra.";
      if (hint) hint.textContent = "Mostrando contenido genérico para toda Latinoamérica";
      try { document.title = "CotizaT — Presupuestos de construcción y remodelación para Latinoamérica"; } catch (_) {}
      var m2 = document.querySelector('meta[name="description"]');
      if (m2) m2.setAttribute("content", "Presupuestos de obra profesionales en minutos. Más de 3.000 partidas clasificadas con precios en USD de referencia para Latinoamérica. PDF con tu logo, versiones, aprobaciones y cobros.");
    }

    // Normalizar select
    if (select && select.value !== (codigo || "")) select.value = codigo || "";

    if (!persist) return;

    // Persistir cookie + localStorage + navegar al subdirectorio canónico (/co/, /mx/...)
    try {
      document.cookie = "cotizat_pais=" + encodeURIComponent(codigo || "") + "; path=/; max-age=" + (codigo ? 365 * 24 * 3600 : 0) + "; samesite=lax";
      if (codigo) localStorage.setItem("cotizat_pais", codigo);
      else localStorage.removeItem("cotizat_pais");
    } catch (_) {}

    // Navega al subdirectorio SEO (/co/, /mx/ ...) — 1 Vercel, 1 Supabase, URL canónica
    try {
      var dest = codigo ? "/" + codigo.toLowerCase() + "/" : "/";
      if (window.location.pathname !== dest) {
        window.location.href = dest;
        return;
      }
    } catch (_) {}
    // Fallback legacy ?pais= si no hay subdirectorio
    try {
      var url = new URL(window.location.href);
      if (codigo) url.searchParams.set("pais", codigo);
      else url.searchParams.delete("pais");
      history.replaceState(null, "", url.pathname + url.search + url.hash);
    } catch (_) {}
  }

  // Inicial: si hay cookie/localStorage y no hay ?pais, no forzar; el servidor ya renderizó.
  // Solo sincronizar URL si el usuario nunca eligió y no hay cookie.
  var initial = select.value || "";
  // Si el select genérico pero hay pais en URL, el servidor ya lo aplicó; no reaplicar.

  select.addEventListener("change", function () {
    var v = select.value || "";
    if (v && !mapa[v]) v = "";
    aplicarPais(v, { persist: true });
  });

  // Soporte navegación atrás/adelante con subdirectorio o ?pais=
  window.addEventListener("popstate", function () {
    try {
      var path = window.location.pathname || "";
      var m = path.match(/^\/(ve|co|mx|ec|pe)(\/|$)/i);
      if (m) {
        var c = m[1].toUpperCase();
        if (mapa[c]) { aplicarPais(c, { persist: false }); return; }
      }
      var u = new URL(window.location.href);
      var q = (u.searchParams.get("pais") || "").toUpperCase();
      if (q && !mapa[q]) q = "";
      aplicarPais(q, { persist: false });
    } catch (_) {}
  });
})();
