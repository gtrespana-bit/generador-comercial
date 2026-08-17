/* Carga bajo demanda de la descomposición de una partida del catálogo.

 * La lista de Partidas deja vacío el cuerpo de cada <details class="descomp-details"
 * data-descomp="ID">. Al desplegarlo por primera vez se piden las filas de
 * recursos al servidor y se construye la tabla con nodos de DOM (compatible
 * con la CSP estricta). Si falla, se puede reintentar reabriendo.
 */
(function () {
  "use strict";

  var contenedor = document.getElementById("catalogMain");
  if (!contenedor) return;

  function crear(tag, clase, texto) {
    var el = document.createElement(tag);
    if (clase) el.className = clase;
    if (texto !== undefined && texto !== null) el.textContent = texto;
    return el;
  }

  function construirTabla(filas) {
    var tabla = crear("table", "table descomp-table");
    var thead = crear("thead");
    var trHead = crear("tr");
    ["Categoría", "Código", "Und.", "Descripción", "Rend.", "Precio", "Importe"].forEach(function (titulo, i) {
      trHead.appendChild(crear("th", i >= 4 ? "right" : "", titulo));
    });
    thead.appendChild(trHead);
    tabla.appendChild(thead);

    var tbody = crear("tbody");
    filas.forEach(function (r) {
      var tr = crear("tr");

      var tdCat = crear("td");
      tdCat.appendChild(crear("span", "badge", r.categoria || r.grupo || "otros"));
      tr.appendChild(tdCat);

      var tdCod = crear("td");
      tdCod.appendChild(crear("code", "", r.codigo || "—"));
      tr.appendChild(tdCod);

      tr.appendChild(crear("td", "", r.unidad || "—"));

      var tdDesc = crear("td", "", r.descripcion || "");
      if (r.descripcion) tdDesc.title = r.descripcion;
      tr.appendChild(tdDesc);

      tr.appendChild(crear("td", "right", r.rendimiento != null ? String(r.rendimiento) : ""));
      tr.appendChild(crear("td", "right", r.precio != null ? String(r.precio) : ""));
      var tdImp = crear("td", "right");
      tdImp.appendChild(crear("strong", "", r.importe != null ? String(r.importe) : ""));
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

    fetch("/partidas/" + encodeURIComponent(id) + "/descomposicion", {
      headers: { Accept: "application/json" },
    })
      .then(function (respuesta) {
        if (!respuesta.ok) throw new Error("http " + respuesta.status);
        return respuesta.json();
      })
      .then(function (datos) {
        if (!datos || datos.ok !== true) return;
        var filas = (datos.filas || []).filter(function (f) {
          return f && f.tipo === "recurso";
        });
        holder.replaceChildren();
        if (!filas.length) {
          holder.appendChild(crear("p", "hint", "Sin recursos."));
          return;
        }
        holder.appendChild(construirTabla(filas));
      })
      .catch(function () {
        details.setAttribute("data-descomp-cargado", "0");
        holder.replaceChildren();
        holder.appendChild(crear("p", "hint", "No se pudo cargar la descomposición. Cierra y vuelve a abrir para reintentar."));
      });
  }

  // Delegado: <details> dispara "toggle" al abrir/cerrar.
  contenedor.addEventListener("toggle", function (evento) {
    var objetivo = evento.target;
    if (objetivo && objetivo.classList && objetivo.classList.contains("descomp-details") && objetivo.open) {
      cargar(objetivo);
    }
  });
})();
