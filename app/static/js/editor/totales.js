/* ============================================================================
   Editor — Indicadores de la command bar (margen, descuento, coste, tiempo)

   La barra de comando vive en el HTML del editor (form.html). Este módulo
   solo actualiza los chips de margen / descuento / coste / tiempo. Ya no
   crea una segunda barra sticky (antes se duplicaba con la del template).
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;

  function ensureMetaChips() {
    var meta = document.getElementById("editor-command-meta");
    if (!meta) return;

    // Descuento (se crea bajo demanda si no existe)
    if (!document.getElementById("descuento-text")) {
      var descuentoChip = document.createElement("span");
      descuentoChip.className = "ecb-chip muted";
      descuentoChip.id = "descuento-chip";
      descuentoChip.innerHTML =
        '<span id="descuento-fill" class="ecb-descuento-fill" hidden></span>' +
        '<span id="descuento-text"></span>';
      meta.appendChild(descuentoChip);
    }

    if (!document.getElementById("costo-badge")) {
      var costo = document.createElement("span");
      costo.id = "costo-badge";
      costo.className = "ecb-chip muted";
      costo.textContent = "Costo: —";
      meta.appendChild(costo);
    }

    if (!document.getElementById("tiempo-badge")) {
      var tiempo = document.createElement("span");
      tiempo.id = "tiempo-badge";
      tiempo.className = "ecb-chip muted";
      tiempo.textContent = "—";
      meta.appendChild(tiempo);
    }
  }

  function actualizarStickyTotal(totals) {
    ensureMetaChips();

    var totalEl = document.getElementById("sticky-total-val");
    var margenEl = document.getElementById("margen-text");
    var margenDot = document.querySelector("#margen-indicator .margen-dot");
    var descuentoFill = document.getElementById("descuento-fill");
    var descuentoText = document.getElementById("descuento-text");
    var descuentoChip = document.getElementById("descuento-chip");
    var costoBadge = document.getElementById("costo-badge");

    if (totalEl && editor.FMT) {
      totalEl.textContent = editor.FMT.fmt(totals.total, totals.moneda);
    }

    if (margenEl) {
      // El semáforo mide la obra, no los productos de paso.
      var conProductos = (totals.total_productos || 0) > 0;
      var margenPct = conProductos ? (totals.margen_obra_pct || 0) : (totals.margen_pct || 0);
      var margenAbs = conProductos ? (totals.margen_obra || 0) : (totals.margen || 0);
      var etiqueta = conProductos ? "Obra " : "Margen ";

      if (margenPct >= 20) {
        margenEl.textContent = etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) {
          margenDot.className = "margen-dot ok";
          CotizatStyles.set(margenDot, "background", "");
        }
      } else if (margenPct >= 10) {
        margenEl.textContent = etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) {
          margenDot.className = "margen-dot warn";
          CotizatStyles.set(margenDot, "background", "");
        }
      } else if (margenPct > 0) {
        margenEl.textContent = etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) {
          margenDot.className = "margen-dot bad";
          CotizatStyles.set(margenDot, "background", "");
        }
      } else if (margenAbs < 0) {
        margenEl.textContent = "Pérdida " + Math.abs(margenPct).toFixed(1) + "%";
        if (margenDot) {
          margenDot.className = "margen-dot bad";
          CotizatStyles.set(margenDot, "background", "");
        }
      } else {
        margenEl.textContent = "—";
        if (margenDot) {
          margenDot.className = "margen-dot";
          CotizatStyles.set(margenDot, "background", "");
        }
      }
      margenEl.title = conProductos
        ? "Margen real de la obra sin productos. Total: " + (totals.margen_pct || 0).toFixed(1) + "%"
        : "Margen total del presupuesto";
    }

    if (descuentoText) {
      var descuentoPct = totals.descuento_pct || 0;
      if (descuentoPct > 0) {
        descuentoText.textContent = "−" + descuentoPct.toFixed(1) + "%";
        if (descuentoChip) descuentoChip.hidden = false;
        if (descuentoFill) {
          var pctVisual = Math.min((descuentoPct / 50) * 100, 100);
          CotizatStyles.set(descuentoFill, "width", pctVisual + "%");
          descuentoFill.hidden = false;
          if (descuentoPct > 15) descuentoFill.className = "ecb-descuento-fill bad";
          else if (descuentoPct > 10) descuentoFill.className = "ecb-descuento-fill warn";
          else descuentoFill.className = "ecb-descuento-fill";
        }
      } else {
        descuentoText.textContent = "";
        if (descuentoChip) descuentoChip.hidden = true;
      }
    }

    if (costoBadge) {
      var costeTotal = totals.coste_interno || 0;
      var totalVenta = totals.total || 0;
      if (costeTotal > 0 && editor.FMT) {
        var costoPct = totalVenta > 0 ? (costeTotal / totalVenta * 100) : 0;
        costoBadge.textContent =
          "Costo " + editor.FMT.fmt(costeTotal, totals.moneda) +
          " · " + costoPct.toFixed(0) + "%";
        costoBadge.hidden = false;
      } else {
        costoBadge.textContent = "";
        costoBadge.hidden = true;
      }
    }
  }

  function init() {
    ensureMetaChips();
  }

  editor.initStickyTotal = init;
  editor.initTotales = init;
  editor.totales = { init: init };
  editor.actualizarStickyTotal = actualizarStickyTotal;
})();
