/* Panel de administración premium (/admin).
 *
 * Tres cosas: ordena la tabla de clientes al pulsar las cabeceras, filtra por
 * texto y estado, y despliega la ficha de acciones de un cliente al pulsar su
 * fila (conceder, renovar, suspender e historial, sin salir de la fila).
 *
 * Solo usa classList, addEventListener y comparadores: sin inyección de HTML
 * ni estilos en línea (cumple la CSP del proyecto). Las acciones son
 * formularios POST normales, así que el panel sigue funcionando sin este
 * script: sin él la ficha queda visible en vez de plegada, nunca inaccesible.
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
  // Solo las filas de cliente entran en el orden y el filtro; las fichas de
  // acciones viajan pegadas a su fila (ver moverFicha).
  var filas = Array.prototype.slice.call(
    cuerpo.querySelectorAll("tr.fila-cliente")
  );
  if (!filas.length) {
    filas = Array.prototype.slice.call(cuerpo.querySelectorAll("tr"));
  }
  var estadoActual = null; // {key, tipo, dir}

  function fichaDe(fila) {
    var id = fila.getAttribute("data-org");
    return id ? cuerpo.querySelector('tr.fila-acciones[data-de="' + id + '"]') : null;
  }

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
      // La ficha se reinserta justo detrás de su fila: al reordenar no puede
      // quedarse colgando bajo el cliente equivocado.
      var ficha = fichaDe(filas[i]);
      if (ficha) {
        cuerpo.appendChild(ficha);
      }
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
      var ficha = fichaDe(fila);
      if (ficha) {
        // Una ficha abierta cuyo cliente deja de encajar en el filtro se
        // esconde con él; si no, quedaría suelta sin dueño visible.
        ficha.classList.toggle(
          "oculta",
          !visible || !fila.classList.contains("abierta")
        );
      }
    }
  }

  function alternarFicha(fila) {
    var ficha = fichaDe(fila);
    if (!ficha) {
      return;
    }
    var abierta = fila.classList.toggle("abierta");
    ficha.classList.toggle("oculta", !abierta);
    fila.setAttribute("aria-expanded", abierta ? "true" : "false");
  }

  for (var f = 0; f < filas.length; f++) {
    (function (fila) {
      if (!fichaDe(fila)) {
        return;
      }
      fila.addEventListener("click", function () {
        alternarFicha(fila);
      });
      fila.addEventListener("keydown", function (evento) {
        // Teclado: la fila es un control, así que responde a Enter y espacio.
        if (evento.key === "Enter" || evento.key === " " || evento.key === "Spacebar") {
          evento.preventDefault();
          alternarFicha(fila);
        }
      });
    })(filas[f]);
  }

  // Confirmación de lo irreversible (suspender, cancelar). Se hace aquí y no
  // con un onsubmit en el HTML porque la CSP prohíbe el script en línea.
  var arriesgados = document.querySelectorAll("form[data-confirmar]");
  for (var c = 0; c < arriesgados.length; c++) {
    (function (formulario) {
      formulario.addEventListener("submit", function (evento) {
        if (!window.confirm(formulario.getAttribute("data-confirmar"))) {
          evento.preventDefault();
        }
      });
    })(arriesgados[c]);
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
