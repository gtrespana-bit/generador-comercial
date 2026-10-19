/* Lazy-load the resource breakdown when a catalogue row is expanded.
   The parent listens in capture: the native <details> toggle event does not
   bubble, so a normal delegated listener silently misses it. */
(function () {
  "use strict";

  var contenedor = document.getElementById("catalogMain");
  if (!contenedor) return;
  var ENGLISH = String(document.documentElement.lang || "").toLowerCase().indexOf("en") === 0;

  function crear(tag, clase, texto) {
    var el = document.createElement(tag);
    if (clase) el.className = clase;
    if (texto !== undefined && texto !== null) el.textContent = texto;
    return el;
  }

  function numero(valor) {
    var n = Number(valor);
    return isFinite(n) ? n : 0;
  }

  function formatoNumero(valor) {
    return numero(valor).toLocaleString(ENGLISH ? "en-GB" : "es-VE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatoMoneda(valor, moneda) {
    if (window.FMT && typeof window.FMT.fmt === "function") {
      return window.FMT.fmt(numero(valor), moneda);
    }
    return formatoNumero(valor) + " " + String(moneda || "USD").toUpperCase();
  }

  function esqueleto(holder) {
    holder.replaceChildren();
    var anchos = ["wide", "med", "small", "med"];
    for (var f = 0; f < 3; f++) {
      var fila = crear("div", "skeleton-row");
      anchos.forEach(function (clase) {
        fila.appendChild(crear("div", "skeleton skeleton-cell " + clase));
      });
      holder.appendChild(fila);
    }
  }

  function construirTabla(filas, moneda) {
    var tabla = crear("table", "table descomp-table");
    var thead = crear("thead");
    var trHead = crear("tr");
    var codigoMoneda = String(moneda || "USD").toUpperCase();
    var titulos = ENGLISH
      ? ["Category", "Code", "Unit", "Description", "Output", "Unit price (" + codigoMoneda + ")", "Amount (" + codigoMoneda + ")"]
      : ["Categoría", "Código", "Unidad", "Descripción", "Rendimiento", "Precio (" + codigoMoneda + ")", "Importe (" + codigoMoneda + ")"];
    titulos.forEach(function (titulo, i) {
      trHead.appendChild(crear("th", i >= 4 ? "right" : "", titulo));
    });
    thead.appendChild(trHead);
    tabla.appendChild(thead);

    var tbody = crear("tbody");
    filas.forEach(function (r) {
      var tr = crear("tr");

      var tdCat = crear("td");
      tdCat.appendChild(crear("span", "badge", r.categoria_etiqueta || r.grupo || r.categoria || (ENGLISH ? "Other" : "Otros")));
      tr.appendChild(tdCat);

      var tdCod = crear("td");
      tdCod.appendChild(crear("code", "", r.codigo || "—"));
      tr.appendChild(tdCod);

      tr.appendChild(crear("td", "", r.unidad || "—"));

      var tdDesc = crear("td", "", r.descripcion || "");
      if (r.descripcion) tdDesc.title = r.descripcion;
      tr.appendChild(tdDesc);

      tr.appendChild(crear("td", "right", r.rendimiento != null ? formatoNumero(r.rendimiento) : ""));
      tr.appendChild(crear("td", "right", r.precio != null ? formatoMoneda(r.precio, moneda) : ""));
      var tdImp = crear("td", "right");
      tdImp.appendChild(crear("strong", "", r.importe != null ? formatoMoneda(r.importe, moneda) : ""));
      tr.appendChild(tdImp);

      tbody.appendChild(tr);
    });
    tabla.appendChild(tbody);
    return tabla;
  }

  function cargar(details) {
    var id = details.getAttribute("data-descomp");
    if (!id || details.getAttribute("data-descomp-cargado") === "1") return;
    var holder = details.querySelector(".descomp-holder");
    if (!holder) return;
    details.setAttribute("data-descomp-cargado", "1");
    esqueleto(holder);

    var contexto = window.CotizatContextoMoneda && window.CotizatContextoMoneda.query
      ? window.CotizatContextoMoneda.query()
      : "";
    fetch("/partidas/" + encodeURIComponent(id) + "/descomposicion" + (contexto ? "?" + contexto : ""), {
      headers: { Accept: "application/json" },
    })
      .then(function (respuesta) {
        if (!respuesta.ok) throw new Error("http " + respuesta.status);
        return respuesta.json();
      })
      .then(function (datos) {
        if (!datos || datos.ok !== true) throw new Error("breakdown unavailable");
        var filas = (datos.filas || []).filter(function (f) {
          return f && f.tipo === "recurso";
        });
        holder.replaceChildren();
        if (!filas.length) {
          holder.appendChild(crear("p", "hint", ENGLISH ? "No resources." : "Sin recursos."));
          return;
        }
        holder.appendChild(construirTabla(filas, datos.moneda));
      })
      .catch(function () {
        details.setAttribute("data-descomp-cargado", "0");
        holder.replaceChildren();
        holder.appendChild(crear("p", "hint", ENGLISH
          ? "Could not load the breakdown. Close and reopen to try again."
          : "No se pudo cargar la descomposición. Cierra y vuelve a abrir para reintentar."));
      });
  }

  contenedor.addEventListener("toggle", function (evento) {
    var objetivo = evento.target;
    if (objetivo && objetivo.classList && objetivo.classList.contains("descomp-details") && objetivo.open) {
      cargar(objetivo);
    }
  }, true);

  // Click fallback for browsers/webviews that fail to deliver toggle through
  // the ancestor capture path; keyboard activation is still covered by toggle.
  contenedor.addEventListener("click", function (evento) {
    var summary = evento.target && evento.target.closest ? evento.target.closest(".descomp-details > summary") : null;
    var details = summary && summary.parentElement;
    if (details && details.classList.contains("descomp-details")) {
      window.setTimeout(function () {
        if (details.open) cargar(details);
      }, 0);
    }
  }, true);
})();
