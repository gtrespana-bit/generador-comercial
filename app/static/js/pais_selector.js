/* Selector de país para la landing adaptativa (LatAm + España, + mercados EN).
 *
 * Sin inyección HTML ni estilos inline: solo textContent, class y
 * atributos. El servidor ya renderiza el país correcto si viene por
 * subdirectorio, ?pais= o cookie —incluidos los importes del ejemplo en
 * la moneda del país—; este script hace el cambio instantáneo en cliente
 * para los textos simples, persiste la elección (cookie + localStorage)
 * y navega al subdirectorio canónico (/co/, /en-us/ ...), donde el servidor
 * re-renderiza importes, IVA y terminología del ejemplo.
 *
 * Los textos van en los dos idiomas porque el mismo script sirve la landing
 * en español y la de los mercados anglófonos: si se cambiara de país en
 * /en-gb/ y el script escribiera en español, la página se volvería bilingüe
 * a medias. El idioma se lee del <html lang> que ya renderiza el servidor.
 *
 * Dos datos vienen resueltos del servidor para no repetir reglas aquí:
 *   · p.ruta            -> subdirectorio canónico (/en-us/, /mx/)
 *   · p.impuesto_txt*   -> «21 % VAT», o «Sales tax» si no hay alícuota nacional
 */
(function () {
  var select = document.getElementById("pais-select");
  var hint = document.getElementById("pais-bar-hint");
  var dataEl = document.getElementById("paises-data");
  var genericoEl = document.getElementById("pais-generico-data");
  var monedasEl = document.getElementById("ejemplo-monedas");

  if (!select || !dataEl) return;

  // «en-US», «en-GB»… también son inglés: mirar solo «en» no bastaba.
  var EN = /^en(\b|-)/i.test(document.documentElement.lang || "");

  function t(es, en) { return EN ? en : es; }

  var paises = [];
  var generico = null;
  var monedas = null;
  try { paises = JSON.parse(dataEl.textContent || "[]"); } catch (_) { paises = []; }
  try { generico = JSON.parse(genericoEl ? genericoEl.textContent : "null"); } catch (_) { generico = null; }
  try { monedas = JSON.parse(monedasEl ? monedasEl.textContent : "null"); } catch (_) { monedas = null; }
  if (!generico) generico = {
    codigo: "", bandera: "🌎", moneda: "USD", simbolo_local: "$", iva: 16,
    nombre: "España y Latinoamérica", nombre_en: "Spain and Latin America",
    id_fiscal: t("ID fiscal", "tax ID"), mercado: "iberoamericano",
    gentilicio: "iberoamericano",
    vocab: t("concreto, friso, cielo raso, rodapié, plomero",
             "concrete, plaster, suspended ceiling, baseboard, plumber"),
    ruta: t("/", "/en/"),
    impuesto_txt: "I.V.A.", impuesto_txt_en: "VAT"
  };

  var mapa = {};
  for (var i = 0; i < paises.length; i++) mapa[paises[i].codigo] = paises[i];

  function texto(id, valor) {
    var el = document.getElementById(id);
    if (el) el.textContent = valor;
  }

  /* Nombre del país en el idioma de la página.
     Venezuela, Australia, Colombia y otros once se deletrean igual. */
  function nombre(p) {
    return EN ? (p.nombre_en || p.nombre) : p.nombre;
  }

  /* Rótulo del impuesto ya resuelto por el servidor: en Estados Unidos y
     Canadá no hay alícuota nacional y viene sin cifra. */
  function impuesto(p) {
    return EN ? (p.impuesto_txt_en || p.impuesto_txt) : (p.impuesto_txt || p.impuesto_txt_en);
  }

  function vocabulario(p) {
    return EN ? (p.vocab_en || p.vocab) : p.vocab;
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
      var ref = t("tasa de referencia", "reference rate");
      var oUsd = t("o USD si prefieres", "or USD if you prefer");
      var monedaDe = t("moneda de", "currency of");
      if (p && p.moneda && p.moneda !== "USD") {
        var tasa = monedas && monedas.tasa_txt ? monedas.tasa_txt : "";
        nota.textContent = tasa
          ? ref + " " + tasa + " " + p.moneda + "/US$"
          : monedaDe + " " + nombre(p) + ", " + oUsd;
      } else if (p && p.moneda_local && p.moneda_local !== "USD") {
        nota.textContent = t("o ", "or ") + p.simbolo_local + " (" + p.moneda_local + ") " + t("con tasa de referencia", "at the reference rate");
      } else if (p) {
        nota.textContent = monedaDe + " " + nombre(p) + " · " + impuesto(p);
      } else {
        nota.textContent = t("España en EUR · Latinoamérica en su moneda",
                             "Spain in EUR · Latin America in its own currency");
      }
    }
  }

  function aplicarPais(codigo, opts) {
    var persist = !(opts && opts.persist === false);
    var p = codigo ? mapa[codigo] : null;
    var nom = p ? nombre(p) : null;

    // Textos dinámicos por id
    texto("hero-kicker", p
      ? p.bandera + " " + t("Sistema comercial para ", "Commercial system for ") + nom + " · " + t("Construcción y reformas", "Construction and remodeling") + " · " + t("catálogo de precios propio", "own price catalog")
      : t("🇪🇸 España · 🌎 Latinoamérica — Sistema comercial de obra y reformas · catálogo de precios por país",
          "🇪🇸 Spain · 🌎 Latin America — Commercial system for building and remodeling · price catalog by country"));
    texto("banner-h2", p
      ? t("El catálogo de ", "The catalog of ") + nom + t(": precios de su mercado, no de otro país.", ": prices from your market, not from another country.")
      : t("El catálogo más completo para presupuestar en España y Latinoamérica.",
          "The most complete catalog for estimating in Spain and Latin America."));

    var bannerP = document.getElementById("banner-p");
    if (bannerP) {
      var txt = bannerP.textContent || "";
      // Reemplazos quirúrgicos: mercado y país, conservando las cifras
      // reales que el servidor ya renderizó.
      txt = txt.replace(EN ? /market [a-z]+/i : /mercado [a-záéíóúñ]+/i,
                        (EN ? "market " : "mercado ") + (p ? p.mercado : t("iberoamericano", "Latin American")));
      if (!p) {
        txt = txt.replace(EN ? /for [A-Z][\w ,()]+/ : /para [A-ZÁÉÍÓÚÑ][\wáéíóúñ ,()]+/,
                          EN ? "for Spain and Latin America." : "para España y Latinoamérica.");
      }
      bannerP.textContent = txt;
    }

    texto("banner-vocab", p
      ? "✓ " + t("Catálogo y vocabulario de ", "Catalog and trade terms of ") + nom + ": " + vocabulario(p) + "."
      : "✓ " + t("España: hormigón, pladur, falso techo, alicatado, fontanería. Cada país con su vocabulario.",
                 "Spain: concrete, plasterboard, suspended ceiling, wall tiling, plumbing. Every country with its own terms."));

    var bannerMoneda = document.getElementById("banner-moneda");
    if (bannerMoneda) {
      if (p) {
        var m = "✓ ";
        if (p.codigo === "ES") {
          m += t("España en EUR con NIF e IVA 21 % · referencias de mercado espejo español. Cada presupuesto congela su tasa si trabajas en USD.",
                 "Spain in EUR with NIF and 21 % VAT · Spanish market references. Every estimate locks its rate if you work in USD.");
        } else if (p.moneda !== "USD") {
          m += t("Precios de ", "Prices for ") + nom + t(" en ", " in ") + p.moneda + t(" con la tasa de referencia · o en US$ si prefieres. Cada presupuesto congela su tasa.",
                                                                                        " at the reference rate · or in US$ if you prefer. Every estimate locks its rate.");
        } else {
          m += t("Precios de ", "Prices for ") + nom + t(" en ", " in ") + (p.moneda_local && p.moneda_local !== "USD" ? "USD " + t("o ", "or ") + p.moneda_local : p.moneda) + t(". Cada presupuesto congela su tasa si cambias de moneda.",
                                                                                                                                                                            ". Every estimate locks its rate if you switch currency.");
        }
        bannerMoneda.textContent = m;
      } else {
        bannerMoneda.textContent = "✓ " + t("España en EUR con NIF e IVA 21 % · Latinoamérica en su moneda (MXN, COP, PEN…) con tasa congelada por presupuesto.",
                                            "Spain in EUR with NIF and 21 % VAT · Latin America in its own currency (MXN, COP, PEN…) with the rate locked per estimate.");
      }
    }

    // Fiscal
    var fiscalIcon = document.querySelector("#fiscal-card .icon");
    if (fiscalIcon) fiscalIcon.textContent = p ? p.bandera : "🌎";
    texto("fiscal-h3", p
      ? t("Fiscal a tu medida · ", "Tax settings to match · ") + nom
      : t("Fiscal a tu medida · España y Latinoamérica", "Tax settings to match · Spain and Latin America"));
    texto("fiscal-p", p
      ? impuesto(p) + t(", ", ", ") + p.id_fiscal + t(", retención, operación exenta, número de control y cláusula cambiaria. Moneda ",
                                                       ", withholding, tax-exempt operation, control number and currency clause. Currency ") + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + t(" o USD, con tasa de referencia.",
 " or USD, at the reference rate.")
      : t("IVA configurable por país, tu ID fiscal (NIF, RIF, NIT, RUT, CUIT, RUC, RFC…), retención, operación exenta y cláusula cambiaria. Moneda en tu divisa local o USD, con tasa de referencia.",
          "Tax configurable per country, your tax ID (EIN, VAT number, ABN, BN, RUC…), withholding, tax-exempt operation and currency clause. Currency in your local currency or USD, at the reference rate."));

    // Franja país
    texto("franja-h2", p
      ? t("Pensado para ", "Built for ") + nom + t(", no adaptado después.", ", not adapted afterwards.")
      : t("Pensado para España y Latinoamérica, no adaptado después.", "Built for Spain and Latin America, not adapted afterwards."));
    texto("franja-intro", p
      ? t("No es una herramienta genérica traducida. CotizaT habla el idioma de la obra en ", "This is not a generic tool with a translation layer. CotizaT speaks the language of the trade in ") + nom + t(": precios, vocabulario y fiscalidad de aquí.", ": prices, terms and tax from right here.")
      : t("No es una herramienta genérica traducida. CotizaT nace para reformar en España (EUR, NIF, IVA 21 %, pladur y fontanería) y para construir en Latinoamérica. Cada país, su catálogo.",
          "This is not a generic tool with a translation layer. CotizaT was built to remodel in Spain (EUR, NIF, 21 % VAT, plasterboard and plumbing) and to build in Latin America. Each country, its own catalog."));
    texto("franja-precio-p", p
      ? (p.codigo === "ES"
        ? t("Cotiza reformas en EUR con NIF e IVA 21 %, o en USD como referencia. Referencias de mercado españolas incluidas; tu tasa queda guardada en cada presupuesto.",
            "Estimate remodeling in EUR with NIF and 21 % VAT, or in USD as a reference. Spanish market references included; your rate is saved on every estimate.")
        : t("Cotiza en ", "Estimate in ") + p.moneda + (p.moneda !== "USD" ? " (" + p.simbolo_local + ")" : "") + t(" o en USD como referencia. Sin conversiones improvisadas: tu tasa queda guardada en cada presupuesto.",
 " or in USD as a reference. No improvised conversions: your rate is saved on every estimate."))
      : t("España en euros con NIF e IVA 21 %; Latinoamérica en US$ o su moneda local (MXN, COP, PEN…). Tu tasa queda guardada en cada presupuesto.",
          "Spain in euros with NIF and 21 % VAT; Latin America in US$ or its local currency (MXN, COP, PEN…). Your rate is saved on every estimate."));
    texto("franja-vocab-p", p
      ? (p.codigo === "ES"
        ? t("Hormigón, pladur, falso techo, alicatado, fontanero. El vocabulario de tu cliente y tu cuadrilla en España, no el de otro país.",
            "Concrete, plasterboard, suspended ceiling, wall tiling, plumber. The terms your client and your crew use in Spain, not another country's.")
        : vocabulario(p) + t(", y todos los nombres que usa tu cliente y tu cuadrilla en ", ", and every name your client and your crew use in ") + nom + t(", no los de otro país.", ", not another country's."))
      : t("Hormigón, pladur, falso techo, alicatado, fontanero en España; concreto/pañete/cielo raso en LatAm. Elige tu país y la landing habla tu obra.",
          "Plasterboard, suspended ceiling, wall tiling, plumbing in Spain; concrete/render/suspended ceiling in LatAm. Pick your country and the landing speaks your trade."));

    // Bloque de moneda (stat del hero)
    actualizarMoneda(p);

    if (hint) hint.textContent = p
      ? p.bandera + " " + t("Catálogo de ", "Catalog of ") + nom + " · " + p.id_fiscal + " · " + impuesto(p)
      : t("Elige tu país para ver su catálogo de precios (España · LatAm)",
          "Choose your country to see its price catalog (Spain · Latin America)");

    // Título y meta description (opcional, sin recargar)
    try {
      document.title = p
        ? t("CotizaT: software de presupuestos de obra en ", "CotizaT: construction estimating software for ") + nom
        : t("CotizaT: software de presupuestos de obra para España y Latinoamérica",
            "CotizaT: construction estimating software for Spain and Latin America");
    } catch (_) {}
    var meta = document.querySelector('meta[name="description"]');
    if (meta) {
      meta.setAttribute("content", p
        ? t("Software para presupuestos de obra y reformas en ", "Construction and remodeling estimating software for ") + nom + t(". Catálogo de precios de su mercado, APU, PDF profesional. 7 días gratis, sin tarjeta.",
 ". Price catalog from your market, unit price analysis, professional PDF. 7 days free, no card.")
        : t("Software de presupuestos de obra para España y Latinoamérica. Catálogo de precios por país, APU, margen, tiempos y PDF profesional. 7 días gratis, sin tarjeta.",
            "Construction estimating software for Spain and Latin America. Price catalog by country, unit price analysis, margin, times and professional PDF. 7 days free, no card."));
    }

    // Normalizar select
    if (select && select.value !== (codigo || "")) select.value = codigo || "";

    if (!persist) return;

    // Persistir cookie + localStorage + navegar al subdirectorio canónico
    try {
      document.cookie = "cotizat_pais=" + encodeURIComponent(codigo || "") + "; path=/; max-age=" + (codigo ? 365 * 24 * 3600 : 0) + "; samesite=lax";
      if (codigo) localStorage.setItem("cotizat_pais", codigo);
      else localStorage.removeItem("cotizat_pais");
    } catch (_) {}

    // Navega al subdirectorio canónico (/co/, /en-us/ …). La ruta la calcula
    // el servidor: los cinco mercados anglófonos viven bajo /en-xx/ y los
    // hispanos bajo /xx/, y construirla aquí era perderse esa distinción.
    try {
      var dest = p && p.ruta ? p.ruta : (EN ? "/en/" : "/");
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
  // Reconoce tanto /co/ como /en-us/: antes solo miraba el código de país
  // al principio del path, así que volver a una landing inglesa caía al
  // genérico (y por tanto reescribía la página en español).
  function codigoDeLaRuta(path) {
    var keys = Object.keys(mapa).join("|");
    var m = path.match(new RegExp("^/(?:(en)-)?(" + keys + ")(/|$)", "i"));
    return m ? m[2].toUpperCase() : "";
  }

  window.addEventListener("popstate", function () {
    try {
      var path = window.location.pathname || "";
      var c = codigoDeLaRuta(path);
      if (c && mapa[c]) { aplicarPais(c, { persist: false }); return; }
      var u = new URL(window.location.href);
      var q = (u.searchParams.get("pais") || "").toUpperCase();
      if (q && !mapa[q]) q = "";
      aplicarPais(q, { persist: false });
    } catch (_) {}
  });
})();
