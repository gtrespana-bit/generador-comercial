/* Panel de administración premium (/admin).
 *
 * Ordena la tabla de clientes al hacer clic en las cabeceras y filtra por
 * texto y estado. Solo usa classList, addEventListener y comparadores:
 * sin inyección de HTML ni estilos en línea (cumple la CSP del proyecto).
 */
(function () {
  var tabla = document.getElementById("tabla-clientes");
  var buscar = document.getElementById("buscar");
  var filtro = document.getElementById("filtro-estado");

  if (!tabla) {
    return;
  }

  var cabeceras = tabla.querySelectorAll("thead th[data-sort]");
  var cuerpo = tabla.querySelector("tbody");
  var filas = Array.prototype.slice.call(cuerpo.querySelectorAll("tr"));
  var estadoActual = null; // {key, tipo, dir}

  function valorFila(fila, tipo) {
    // Encuentra la celda cuyo data-sort-key coincide con la columna activa.
    var celdas = fila.querySelectorAll("td");
    for (var i = 0; i < celdas.length; i++) {
      var celda = celdas[i];
      if (!estadoActual || celda.getAttribute("data-sort-key") !== estadoActual.key) {
        continue;
      }
      if (tipo === "num") {
        return parseFloat(celda.getAttribute("data-num") || "0");
      }
      if (tipo === "fecha") {
        return celda.getAttribute("data-fecha") || "";
      }
      return (celda.getAttribute("data-text") || celda.textContent || "").trim().toLowerCase();
    }
    return "";
  }

  function comparar(a, b) {
    var tipo = estadoActual.tipo;
    var va = valorFila(a, tipo);
    var vb = valorFila(b, tipo);
    if (tipo === "num") {
      return va - vb;
    }
    if (va < vb) {
      return -1;
    }
    if (va > vb) {
      return 1;
    }
    return 0;
  }

  function ordenar() {
    if (!estadoActual) {
      return;
    }
    var dir = estadoActual.dir; // 1 asc, -1 desc
    filas.sort(function (a, b) {
      return comparar(a, b) * dir;
    });
    for (var i = 0; i < filas.length; i++) {
      cuerpo.appendChild(filas[i]);
    }
    actualizarFlechas();
  }

  function actualizarFlechas() {
    for (var i = 0; i < cabeceras.length; i++) {
      var th = cabeceras[i];
      th.classList.remove("sorted-asc", "sorted-desc");
      if (estadoActual && th.getAttribute("data-key") === estadoActual.key) {
        th.classList.add(estadoActual.dir === 1 ? "sorted-asc" : "sorted-desc");
      }
    }
  }

  function aplicarFiltros() {
    var texto = (buscar ? buscar.value : "").trim().toLowerCase();
    var estado = filtro ? filtro.value : "";
    for (var i = 0; i < filas.length; i++) {
      var fila = filas[i];
      var visible = true;
      if (estado && fila.getAttribute("data-estado") !== estado) {
        visible = false;
      }
      if (visible && texto) {
        var contenido = fila.textContent.toLowerCase();
        if (contenido.indexOf(texto) === -1) {
          visible = false;
        }
      }
      fila.classList.toggle("oculta", !visible);
    }
  }

  for (var i = 0; i < cabeceras.length; i++) {
    (function (th) {
      th.addEventListener("click", function () {
        var key = th.getAttribute("data-key");
        var tipo = th.getAttribute("data-sort");
        if (estadoActual && estadoActual.key === key) {
          estadoActual.dir = -estadoActual.dir;
        } else {
          estadoActual = { key: key, tipo: tipo, dir: 1 };
        }
        ordenar();
      });
    })(cabeceras[i]);
  }

  if (buscar) {
    buscar.addEventListener("input", aplicarFiltros);
  }
  if (filtro) {
    filtro.addEventListener("change", aplicarFiltros);
  }
})();
