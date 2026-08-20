/* Selector de país para la landing adaptativa (LatAm).
 *
 * Sin inyección HTML ni estilos inline: solo textContent, class y
 * atributos. El servidor ya renderiza el país correcto si viene por
 * subdirectorio, ?pais= o cookie —incluidos los importes del ejemplo en
 * la moneda del país—; este script hace el cambio instantáneo en cliente
 * para los textos simples, persiste la elección (cookie + localStorage)
 * y navega al subdirectorio canónico (/co/, /mx/ ...), donde el servidor
 * re-renderiza importes, IVA y terminología del ejemplo.
 */
(function () {
  var select = document.getElementById("pais-select");
  var hint = document.getElementById("pais-bar-hint");
  var dataEl = document.getElementById("paises-data");
  var genericoEl = document.getElementById("pais-generico-data");
  var monedasEl = document.getElementById("ejemplo-monedas");

  if (!select || !dataEl) return;

  var paises = [];
  var generico = null;
  var monedas = null;
  try { paises = JSON.parse(dataEl.textContent || "[]"); } catch (_) { paises = []; }
  try { generico = JSON.parse(genericoEl ? genericoEl.textContent : "null"); } catch (_) { generico = null; }
  try { monedas = JSON.parse(monedasEl ? monedasEl.textContent : "null"); } catch (_) { monedas = null; }
  if (!generico) generico = { codigo: "", nombre: "Latinoamérica", bandera: "🌎", moneda: "USD", simbolo_local: "$", iva: 16, id_fiscal: "ID fiscal", vocab: "concreto, friso, cielo raso, rodapié, plomero", mercado: "latinoamericano", gentilicio: "latinoamericano" };

  var mapa = {};
  for (var i = 0; i < paises.length; i++) mapa[paises[i].codigo] = paises[i];

  function texto(id, valor) {
    var el = document.getElementById(id);
    if (el) el.textContent = valor;
  }

  function actualizarMoneda(p) {
    // Bloque de moneda del hero-stats: coherente con el render del servidor.
    // Al navegar al subdirectorio el servidor re-renderiza; esto cubre el
    // cambio instantáneo previo a la navegación y el fallback sin recarga.
    var stat = document.getElementById("stat-moneda");
    if (!stat) return;
    var moneda = p && p.moneda && p.moneda !== "USD" ? p.moneda : "US$";
    var fuerte = stat.querySelector("strong");
    var nota = document.getElementById("stat-moneda-nota");
    if (fuerte) fuerte.textContent = moneda;
    if (nota) {
      if (p && p.moneda && p.moneda !== "USD") {
        var tasa = monedas && monedas.tasa_txt ? monedas.tasa_txt : "";
        nota.textContent = tasa
          ? "tasa de referencia " + tasa + " " + p.moneda + "/US$"
          : "moneda de " + p.nombre + ", o USD si prefieres";
      } else if (p && p.moneda_local && p.moneda_local !== "USD") {
        nota.textContent = "o " + p.simbolo_local + " (" + p.moneda_local + ") con tasa de referencia";
      } else if (p) {
        nota.textContent = "moneda de " + p.nombre + " · IVA " + p.iva + "%";
      } else {
        nota.textContent = "USD de referencia · convierte a tu moneda local";
      }
    }
  }

  function aplicarPais(codigo, opts) {
    var persist = !(opts && opts.persist === false);
    var p = codigo ? mapa[codigo] : null;

    // Textos dinámicos por id
    texto("hero-kicker", p
      ? p.bandera + " Hecho para " + p.nombre + " · Construcción y remodelación"
      : "🌎 Hecho para Latinoamérica · Construcción y remodelación");
    texto("banner-h2", p
      ? "El catálogo más completo para presupuestar en " + p.nombre + "."
      : "El catálogo más completo para presupuestar en Latinoamérica.");

    var bannerP = document.getElementById("banner-p");
    if (bannerP) {
      var txt = bannerP.textContent || "";
      // Reemplazos quirúrgicos: mercado y país, conservando las cifras
      // reales que el servidor ya renderizó.
      txt = txt.replace(/mercado [a-záéíóúñ]+/i, "mercado " + (p ? p.mercado : "latinoamericano"));
      if (!p) {
        txt = txt.replace(/para [A-ZÁÉÍÓÚÑ][\wáéíóúñ ,()]+/, "para Latinoamérica.");
      }
      bannerP.textContent = txt;
    }

    texto("banner-vocab", p
      ? "✓ Terminología de " + p.nombre + ": " + p.vocab + "."
      : "✓ Terminología hispana neutra con variantes locales: elige tu país y adapta los nombres.");

    var bannerMoneda = document.getElementById("banner-moneda");
    if (bannerMoneda) {
      if (p) {
        var m = "✓ ";
        if (p.moneda !== "USD") {
          m += "Precios convertidos a " + p.moneda + " con la tasa de referencia · o en US$ si prefieres. Cada presupuesto congela su tasa.";
        } else {
          m += "Precios en " + (p.moneda_local && p.moneda_local !== "USD" ? "USD o " + p.moneda_local : p.moneda) + " de referencia. Cada presupuesto congela su tasa si cambias de moneda.";
        }
        bannerMoneda.textContent = m;
      } else {
        bannerMoneda.textContent = "✓ Precios en USD de referencia · convierte a tu moneda local (COP, MXN, PEN, CLP, ARS…) en cada presupuesto.";
      }
    }

    // Fiscal
    var fiscalIcon = document.querySelector("#fiscal-card .icon");
    if (fiscalIcon) fiscalIcon.textContent = p ? p.bandera : "🌎";
    texto("fiscal-h3", p ? "Fiscal a tu medida · " + p.nombre : "Fiscal a tu medida · Latinoamérica");
    texto("fiscal-p", p
      ? "IVA " + p.iva + "%, " + p.id_fiscal + ", retención, operación exenta, número de control y cláusula cambiaria. Moneda " + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + " o USD, con tasa de referencia."
      : "IVA configurable por país, tu ID fiscal (RIF, NIT, RUT, CUIT, RUC, RFC…), retención, operación exenta y cláusula cambiaria. Moneda en tu divisa local o USD, con tasa de referencia.");

    // Franja país
    texto("franja-h2", p ? "Pensado para " + p.nombre + ", no adaptado después." : "Pensado para Latinoamérica, no adaptado después.");
    texto("franja-intro", p
      ? "No es una herramienta genérica traducida. CotizaT habla el idioma de la obra en " + p.nombre + ": precios, vocabulario y fiscalidad de aquí."
      : "No es una herramienta genérica. CotizaT nace para construir en Latinoamérica: precios en USD de referencia, vocabulario hispano y fiscalidad configurable por país.");
    texto("franja-precio-p", p
      ? "Cotiza en " + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + " o en USD como referencia regional. Sin conversiones improvisadas: tu tasa queda guardada en cada presupuesto."
      : "Cotiza en USD como referencia regional o en tu moneda local (COP, MXN, PEN, CLP, ARS…). Tu tasa de referencia queda guardada en cada presupuesto.");
    texto("franja-vocab-p", p
      ? p.vocab + ", y todos los nombres que usa tu cliente y tu cuadrilla en " + p.nombre + ", no los de otro país."
      : "Concreto/hormigón, friso/revoque, cielo raso/cielorraso, rodapié/zócalo, plomero/gasfíter… Elige tu país y la landing habla tu obra.");

    // Bloque de moneda (stat del hero)
    actualizarMoneda(p);

    if (hint) hint.textContent = p
      ? p.bandera + " Mostrando contenido para " + p.nombre + " · " + p.id_fiscal + " · IVA " + p.iva + "%"
      : "Mostrando contenido genérico para toda Latinoamérica";

    // Título y meta description (opcional, sin recargar)
    try {
      document.title = p
        ? "CotizaT — Presupuestos de construcción y remodelación para " + p.nombre
        : "CotizaT — Presupuestos de construcción y remodelación para Latinoamérica";
    } catch (_) {}
    var meta = document.querySelector('meta[name="description"]');
    if (meta) {
      meta.setAttribute("content", p
        ? "Presupuestos de obra profesionales en minutos. Partidas descompuestas y precios de recursos" + (p.moneda !== "USD" ? " convertidos a " + p.moneda + " con tasa de referencia" : " en USD de referencia") + " contrastados con el mercado " + p.mercado + ". PDF con tu logo, versiones, firma del cliente y cobros."
        : "Presupuestos de obra profesionales en minutos. Líneas de precio en USD de referencia convertibles a tu moneda. PDF con tu logo, versiones, firma del cliente y cobros.");
    }

    // Normalizar select
    if (select && select.value !== (codigo || "")) select.value = codigo || "";

    if (!persist) return;

    // Persistir cookie + localStorage + navegar al subdirectorio canónico (/co/, /mx/ ...)
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
