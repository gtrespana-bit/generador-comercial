/* ============================================================================
   Editor — Totales y barra sticky mejorada

   - Barra de total fijo con indicadores visuales
   - Progress bar del descuento
   - Indicador de margen (semáforo)
   - Sparkline simple del coste vs precio por capítulo
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;

  // -------------------------------------------------------------------------
  // Barra sticky de totales
  // -------------------------------------------------------------------------

  function renderStickyTotal() {
    var existing = document.getElementById("sticky-total-bar");
    if (existing) existing.remove();

    var bar = document.createElement("div");
    bar.className = "sticky-total";
    bar.id = "sticky-total-bar";
    CotizatStyles.setCssText(bar, editor.stickyTotalStyles || "");

    // Contenedor izquierdo: total grande
    var left = document.createElement("div");
    CotizatStyles.setCssText(left, "display:flex; align-items:center; gap:12px;");

    var label = document.createElement("span");
    label.textContent = "TOTAL";
    CotizatStyles.setCssText(label, "font-size:0.75rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em;");
    left.appendChild(label);

    var totalVal = document.createElement("strong");
    totalVal.id = "sticky-total-val";
    CotizatStyles.setCssText(totalVal, "font-size:1.4rem; color:var(--accent); font-weight:700;");
    left.appendChild(totalVal);

    bar.appendChild(left);

    // Indicadores de margen + descuento
    var indicators = document.createElement("div");
    CotizatStyles.setCssText(indicators, "display:flex; align-items:center; gap:16px;");

    // Indicador de margen (semáforo)
    var margenIndicator = document.createElement("div");
    margenIndicator.id = "margen-indicator";
    CotizatStyles.setCssText(margenIndicator, "display:flex; align-items:center; gap:6px; font-size:0.8rem;");

    var margenDot = document.createElement("span");
    margenDot.className = "margen-dot";
    CotizatStyles.setCssText(margenDot, "width:10px; height:10px; border-radius:50%; background:var(--border-strong);");
    margenIndicator.appendChild(margenDot);

    var margenText = document.createElement("span");
    margenText.id = "margen-text";
    CotizatStyles.setCssText(margenText, "color:var(--text-soft);");
    margenIndicator.appendChild(margenText);

    indicators.appendChild(margenIndicator);

    // Barra de progreso del descuento
    var descuentoBar = document.createElement("div");
    descuentoBar.className = "descuento-bar";
    CotizatStyles.setCssText(descuentoBar, "display:flex; align-items:center; gap:6px; font-size:0.72rem; color:var(--text-muted);");

    var descuentoTrack = document.createElement("div");
    CotizatStyles.setCssText(descuentoTrack, "width:60px; height:4px; background:var(--border); border-radius:2px; overflow:hidden;");

    var descuentoFill = document.createElement("div");
    descuentoFill.id = "descuento-fill";
    CotizatStyles.setCssText(descuentoFill, "height:100%; background:var(--accent); width:0%; border-radius:2px; transition: width 0.3s ease, background 0.3s ease;");

    descuentoTrack.appendChild(descuentoFill);
    descuentoBar.appendChild(descuentoTrack);

    var descuentoText = document.createElement("span");
    descuentoText.id = "descuento-text";
    descuentoBar.appendChild(descuentoText);

    indicators.appendChild(descuentoBar);

    // Coste vs precio (mini gráfico)
    var costoBadge = document.createElement("div");
    costoBadge.id = "costo-badge";
    CotizatStyles.setCssText(costoBadge, "display:flex; align-items:center; gap:4px; font-size:0.72rem; color:var(--text-muted);");
    costoBadge.textContent = "Costo: --";
    indicators.appendChild(costoBadge);

    // Tiempo estimado de obra (lo actualiza editor/tiempos.js)
    var tiempoBadge = document.createElement("div");
    tiempoBadge.id = "tiempo-badge";
    CotizatStyles.setCssText(tiempoBadge, "display:flex; align-items:center; gap:4px; font-size:0.72rem; color:var(--text-muted); white-space:nowrap;");
    tiempoBadge.textContent = "⏱ —";
    indicators.appendChild(tiempoBadge);

    bar.appendChild(indicators);

    // Pegar al contenedor correcto
    var toolbar = document.querySelector(".constructor-toolbar");
    if (toolbar) {
      toolbar.parentNode.insertBefore(bar, toolbar.nextSibling);
    } else {
      var cont = document.querySelector(".content") || document.body;
      cont.insertBefore(bar, cont.firstChild);
    }
  }

  // -------------------------------------------------------------------------
  // Actualizar totales en sticky
  // -------------------------------------------------------------------------

  function actualizarStickyTotal(totals) {
    var totalEl = document.getElementById("sticky-total-val");
    var margenEl = document.getElementById("margen-text");
    var margenDot = document.querySelector("#margen-indicator .margen-dot");
    var descuentoFill = document.getElementById("descuento-fill");
    var descuentoText = document.getElementById("descuento-text");
    var costoBadge = document.getElementById("costo-badge");

    if (totalEl) {
      totalEl.textContent = editor.FMT.fmt(totals.total, totals.moneda);
    }

    if (margenEl) {
      // El semáforo de la barra debe medir la obra, no los productos de paso
      // (cerámica, calentadores, electrodomésticos) que apenas dejan margen.
      var conProductos = (totals.total_productos || 0) > 0;
      var margenPct = conProductos ? (totals.margen_obra_pct || 0) : (totals.margen_pct || 0);
      var margenAbs = conProductos ? (totals.margen_obra || 0) : (totals.margen || 0);
      var etiqueta = conProductos ? "Margen obra " : "Margen ";

      if (margenPct >= 20) {
        margenEl.textContent = "✅ " + etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) CotizatStyles.set(margenDot, "background", "#10b981");
      } else if (margenPct >= 10) {
        margenEl.textContent = "⚠ " + etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) CotizatStyles.set(margenDot, "background", "#f59e0b");
      } else if (margenPct > 0) {
        margenEl.textContent = "📉 " + etiqueta + margenPct.toFixed(1) + "%";
        if (margenDot) CotizatStyles.set(margenDot, "background", "#e11d48");
      } else if (margenAbs < 0) {
        margenEl.textContent = "❌ Pérdida obra -" + Math.abs(margenPct).toFixed(1) + "%";
        if (margenDot) CotizatStyles.set(margenDot, "background", "#e11d48");
      } else {
        margenEl.textContent = "—";
        if (margenDot) CotizatStyles.set(margenDot, "background", "var(--border-strong)");
      }
      margenEl.title = conProductos
        ? "Margen real de la obra sin contar productos comerciales. Total: " + (totals.margen_pct || 0).toFixed(1) + "%"
        : "Margen total del presupuesto";
    }

    if (descuentoFill && descuentoText) {
      var descuentoPct = totals.descuento_pct || 0;
      var maxDescuento = 50; // referencia visual
      var pctVisual = Math.min((descuentoPct / maxDescuento) * 100, 100);
      CotizatStyles.set(descuentoFill, "width", pctVisual + "%");

      if (descuentoPct > 15) {
        CotizatStyles.set(descuentoFill, "background", "#e11d48");
      } else if (descuentoPct > 10) {
        CotizatStyles.set(descuentoFill, "background", "#f59e0b");
      } else {
        CotizatStyles.set(descuentoFill, "background", "var(--accent)");
      }

      descuentoText.textContent = descuentoPct > 0 ? "−" + descuentoPct.toFixed(1) + "%" : "";
    }

    if (costoBadge) {
      var costeTotal = totals.coste_interno || 0;
      var totalVenta = totals.total || 0;
      if (costeTotal > 0) {
        var costoPct = totalVenta > 0 ? (costeTotal / totalVenta * 100) : 0;
        costoBadge.textContent = "Costo: " + editor.FMT.fmt(costeTotal, totals.moneda) + " (" + costoPct.toFixed(1) + "%)";
      } else {
        costoBadge.textContent = "Costo: —";
      }
    }
  }

  // -------------------------------------------------------------------------
  // Sparkline simple para capítulo (costo vs precio)
  // -------------------------------------------------------------------------

  function crearSparkline(canvas, datos) {
    if (!canvas || !datos || datos.length < 2) return;

    var ctx = canvas.getContext("2d");
    var rect = canvas.parentElement.getBoundingClientRect();
    var width = Math.min(rect.width || 200, 120);
    var height = 24;

    canvas.width = width * 2;
    canvas.height = height * 2;
    CotizatStyles.set(canvas, "width", width + "px");
    CotizatStyles.set(canvas, "height", height + "px");
    ctx.scale(2, 2);

    ctx.clearRect(0, 0, width, height);

    var max = Math.max.apply(null, datos.map(function (d) { return Math.max(d.precio, d.costo); }));
    var min = Math.min.apply(null, datos.map(function (d) { return Math.min(d.precio, d.costo); }));
    var range = max - min || 1;

    // Dibujar precio
    ctx.beginPath();
    ctx.strokeStyle = "#0d9488";
    ctx.lineWidth = 2;
    datos.forEach(function (d, i) {
      var x = (i / (datos.length - 1)) * width;
      var y = height - ((d.precio - min) / range) * (height - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dibujar costo
    ctx.beginPath();
    ctx.strokeStyle = "#e11d48";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([2, 2]);
    datos.forEach(function (d, i) {
      var x = (i / (datos.length - 1)) * width;
      var y = height - ((d.costo - min) / range) * (height - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // -------------------------------------------------------------------------
  // Inicialización
  // -------------------------------------------------------------------------

  function init() {
    // Crear tabla de estilos CSS para la barra sticky
    if (!document.getElementById("sticky-total-styles")) {
      var style = document.createElement("style");
      style.id = "sticky-total-styles";
      style.textContent = `
        .sticky-total {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: 0.6rem 1rem;
          background: var(--surface);
          border: 1px solid var(--border-strong);
          border-radius: var(--radius);
          margin-bottom: 1rem;
          box-shadow: var(--shadow);
          font-size: 0.85rem;
        }
        .margen-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          transition: background 0.3s ease;
        }
        .descuento-bar {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .descuento-bar > div {
          width: 50px;
          height: 4px;
          background: var(--border);
          border-radius: 2px;
          overflow: hidden;
        }
        .descuento-bar > div > div {
          height: 100%;
          border-radius: 2px;
          transition: width 0.3s ease, background 0.3s ease;
        }
        .costo-badge {
          font-size: 0.72rem;
          color: var(--text-muted);
        }
        .precio-indicator {
          font-size: 0.65rem;
          margin-left: 6px;
          opacity: 0.8;
        }
      `;
      document.head.appendChild(style);
    }

    renderStickyTotal();
  }

  editor.initStickyTotal = init;
  editor.initTotales = init;
  editor.totales = { init: init };
  editor.actualizarStickyTotal = actualizarStickyTotal;
})();
