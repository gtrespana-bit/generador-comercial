/* Render de las filas de partidas con el DOM API (sin inyectar HTML).

 * La vista de navegación de Partidas monta el árbol completo contraído y pide
 * las filas de cada subcapítulo bajo demanda a /partidas/api/filas (JSON).
 * Aquí se construye la tabla con createElement/textContent, de acuerdo con la
 * CSP estricta del proyecto (no se usan sinks de inyección de HTML).
 *
 * Para respetar la clasificación a 3 niveles (capítulo → subcapítulo →
 * apartado), las filas se agrupan por `partida.apartado`. Cada apartado
 * genera su propio encabezado colapsable y su tabla, igual que en la vista
 * filtrada del servidor. Así “Pisos, pavimentos y sus bases” deja de mostrar
 * todas las partidas en un único bloque y pasa a desglosar
 * 01 Bases, 03 Pisos cerámicos, 04 Piedra, etc.
 */
(function () {
  "use strict";

  function crear(tag, clase, texto) {
    var el = document.createElement(tag);
    if (clase) el.className = clase;
    if (texto !== undefined && texto !== null) el.textContent = texto;
    return el;
  }

  function fmtNum(valor, decimales) {
    var dec = decimales === undefined ? 2 : decimales;
    var s = Number(valor || 0).toFixed(dec);
    var partes = s.split(".");
    var entera = partes[0];
    var frac = partes[1] || "";
    var neg = entera.indexOf("-") === 0;
    if (neg) entera = entera.slice(1);
    var out = "";
    for (var i = 0; i < entera.length; i++) {
      if (i > 0 && (entera.length - i) % 3 === 0) out += ".";
      out += entera[i];
    }
    return (neg ? "-" : "") + out + (frac ? "," + frac : "");
  }

  function monto(valor) {
    // Código ISO de la moneda de la vista (la de la organización): «$» no
    // distingue pesos mexicanos, colombianos ni dólares.
    var moneda = window.COTIZAT_MONEDA_VISTA || window.COTIZAT_MONEDA_ACTIVA || "USD";
    if (window.FMT && window.FMT.fmt) return window.FMT.fmt(valor, moneda);
    return fmtNum(valor) + " " + moneda;
  }

  function cell(tag, clase) {
    var td = crear(tag || "td", clase);
    return td;
  }

  function badgeCodigo(partida) {
    var td = cell("td", "col-code");
    if (partida.codigo) {
      var code = crear("code", "code-badge", partida.codigo.slice(0, 12));
      code.title = partida.codigo;
      td.appendChild(code);
    } else {
      td.appendChild(crear("span", "code-empty", "—"));
    }
    return td;
  }

  function cellNombre(partida) {
    var td = cell("td", "col-nombre");
    var main = crear("div", "partida-main");
    var nombre = crear("span", "partida-nombre", partida.nombre);
    nombre.title = partida.nombre;
    main.appendChild(nombre);
    if (partida.usos > 0) {
      var usosMini = crear("span", "usos-mini", "🔥" + partida.usos);
      usosMini.title = "Usada " + partida.usos + " veces";
      main.appendChild(usosMini);
    }
    td.appendChild(main);

    var sub = crear("div", "partida-sub");
    if (partida.apartado) {
      var apartado = crear("span", "apartado-mini", partida.apartado);
      apartado.title = "Ruta del catálogo";
      sub.appendChild(apartado);
    }
    if (partida.descripcion) {
      var desc = crear("span", "desc", partida.descripcion);
      desc.title = partida.descripcion;
      sub.appendChild(desc);
    } else {
      sub.appendChild(crear("span", "desc empty", "Sin descripción"));
    }
    if (partida.proveedor) {
      var prov = crear("span", "prov", "· " + partida.proveedor);
      prov.title = partida.proveedor;
      sub.appendChild(prov);
    }
    if (partida.imagen) {
      var img = crear("span", "has-img", "🖼️");
      img.title = "Con imagen";
      sub.appendChild(img);
    }
    td.appendChild(sub);
    return td;
  }

  function cellCoste(partida) {
    var coste = (partida.coste_materiales || 0) + (partida.coste_mano_obra || 0) +
      (partida.coste_complementarios || 0) + (partida.coste_otros || 0);
    var td = cell("td", "col-coste right");
    td.dataset.coste = String(coste);
    td.title = "Materiales " + monto(partida.coste_materiales) + " · Mano " + monto(partida.coste_mano_obra) +
      " · Compl. " + monto(partida.coste_complementarios) + " · Otros " + monto(partida.coste_otros);
    td.appendChild(crear("span", "coste-val", coste > 0 ? monto(coste) : "—"));
    return td;
  }

  function cellPrecio(partida) {
    var td = cell("td", "col-precio right");
    td.dataset.precio = String(partida.precio);
    td.appendChild(crear("strong", "precio-val", monto(partida.precio)));
    return td;
  }

  function cellMargen(partida) {
    var coste = (partida.coste_materiales || 0) + (partida.coste_mano_obra || 0) +
      (partida.coste_complementarios || 0) + (partida.coste_otros || 0);
    var td = cell("td", "col-margen right");
    if (coste > 0) {
      var margen = partida.precio - coste;
      var markup = (margen / coste) * 100;
      var margenPct = partida.precio ? (margen / partida.precio) * 100 : 0;
      var span;
      if (margen >= 0) {
        span = crear("span", "margen-pos", "+" + monto(margen) + " · " + markup.toFixed(1) + "%");
        span.title = "Beneficio " + monto(margen) + " · " + markup.toFixed(1) + "% s/coste, " + margenPct.toFixed(1) + "% margen";
      } else {
        span = crear("span", "margen-neg", monto(margen) + " · " + markup.toFixed(1) + "%");
        span.title = markup.toFixed(1) + "% s/coste";
      }
      td.appendChild(span);
    } else {
      td.appendChild(crear("span", "margen-na", "—"));
    }
    return td;
  }

  function cellAcciones(partida, vista) {
    var td = cell("td", "col-actions right");
    var actions = crear("div", "row-actions");
    if (vista === "ocultas") {
      var formR = crear("form");
      formR.method = "post";
      formR.action = "/partidas/" + partida.id + "/restaurar";
      var btnR = crear("button", "btn btn-sm btn-primary", "↩ Restaurar");
      btnR.type = "submit";
      btnR.title = "Restaurar en el catálogo";
      formR.appendChild(btnR);
      actions.appendChild(formR);
    } else {
      var editar = crear("a", "btn btn-sm btn-ghost", "✏️");
      editar.href = "/partidas/" + partida.id + "/editar";
      editar.title = "Editar";
      actions.appendChild(editar);

      var formD = crear("form");
      formD.method = "post";
      formD.action = "/partidas/" + partida.id + "/eliminar";
      formD.setAttribute("data-confirm", partida.es_oficial
        ? "¿Ocultar «" + partida.nombre + "» para esta organización? Podrás restaurarla después."
        : "¿Eliminar definitivamente «" + partida.nombre + "»?");
      var btnD = crear("button", "btn btn-sm btn-ghost", partida.es_oficial ? "◉" : "✕");
      btnD.type = "submit";
      btnD.title = partida.es_oficial ? "Ocultar" : "Eliminar";
      formD.appendChild(btnD);
      actions.appendChild(formD);
    }
    td.appendChild(actions);
    return td;
  }

  function fila(partida, vista) {
    var tr = crear("tr", "partida-tr");
    if (vista !== "ocultas") tr.draggable = true;
    tr.dataset.id = String(partida.id);
    tr.dataset.categoria = partida.categoria;
    tr.dataset.subcategoria = partida.subcategoria;
    tr.dataset.apartado = partida.apartado;
    tr.dataset.precio = String(partida.precio);
    tr.dataset.usos = String(partida.usos);

    var tdCheck = cell("td", "col-check");
    var chk = crear("input", "row-check");
    chk.type = "checkbox";
    chk.dataset.id = String(partida.id);
    chk.setAttribute("data-cotizat-change", "partidas-row-check");
    tdCheck.appendChild(chk);
    tr.appendChild(tdCheck);

    tr.appendChild(badgeCodigo(partida));
    tr.appendChild(cellNombre(partida));
    var tdUnd = cell("td", "col-und");
    tdUnd.appendChild(crear("span", "und-badge", partida.unidad));
    tr.appendChild(tdUnd);
    tr.appendChild(cellCoste(partida));
    tr.appendChild(cellPrecio(partida));
    tr.appendChild(cellMargen(partida));
    var tdUsos = cell("td", "col-usos right");
    tdUsos.dataset.usos = String(partida.usos);
    tdUsos.textContent = String(partida.usos);
    tr.appendChild(tdUsos);
    tr.appendChild(cellAcciones(partida, vista));

    return tr;
  }

  function filaDescomp(partida) {
    var tr = crear("tr", "descomp-row");
    tr.dataset.parent = String(partida.id);
    var td = cell("td");
    td.colSpan = 9;
    var details = crear("details", "descomp-details");
    details.dataset.descomp = String(partida.id);
    var summary = crear("summary");
    var label = crear("span", "descomp-summary-label", "▾ Descomposición (" + partida.recursos + " recursos)");
    summary.appendChild(label);
    summary.appendChild(crear("span", "hint", "Clic para ver"));
    details.appendChild(summary);
    details.appendChild(crear("div", "table-wrap descomp-holder"));
    td.appendChild(details);
    tr.appendChild(td);
    return tr;
  }

  function thead() {
    var tr = crear("tr");
    var cabeceras = [
      { clase: "col-check", titulo: "Seleccionar subcategoría", esCheck: true },
      { clase: "col-code sortable", titulo: "Código interno", texto: "Código" },
      { clase: "col-nombre sortable", titulo: "", texto: "Partida" },
      { clase: "col-und", titulo: "", texto: "Und." },
      { clase: "col-coste right sortable", titulo: "Coste directo (materiales+mano obra+complementarios+otros)", texto: "Coste" },
      { clase: "col-precio right sortable", titulo: "", texto: "Precio" },
      { clase: "col-margen right", titulo: "Beneficio = Precio - Coste · % sobre coste", texto: "Beneficio" },
      { clase: "col-usos right sortable", titulo: "", texto: "Usos" },
      { clase: "col-actions right", titulo: "", texto: "Acciones" },
    ];
    cabeceras.forEach(function (c) {
      var th = crear("th", c.clase, c.texto);
      if (c.titulo) th.title = c.titulo;
      if (c.esCheck) {
        var chk = crear("input", "subcat-master");
        chk.type = "checkbox";
        chk.setAttribute("data-cotizat-change", "partidas-select-subcategory");
        th.appendChild(chk);
      }
      tr.appendChild(th);
    });
    var theadEl = crear("thead");
    theadEl.appendChild(tr);
    return theadEl;
  }

  function crearTablaApartado(partidasGrupo, vista) {
    var tabla = crear("table", "partidas-table");
    tabla.appendChild(thead());
    var tbody = crear("tbody");
    (partidasGrupo || []).forEach(function (p) {
      tbody.appendChild(fila(p, vista));
      if (p.recursos > 0) tbody.appendChild(filaDescomp(p));
    });
    tabla.appendChild(tbody);
    return tabla;
  }

  function agruparPorApartado(partidas) {
    // Mantiene el orden numérico del código (12.05.01, 12.05.03…) y deja
    // “Sin apartado” al final para las partidas personalizadas sin clasificar.
    var mapa = {};
    var orden = [];
    (partidas || []).forEach(function (p) {
      var clave = (p.apartado || "").trim() || "Sin apartado";
      if (!Object.prototype.hasOwnProperty.call(mapa, clave)) {
        mapa[clave] = [];
        orden.push(clave);
      }
      mapa[clave].push(p);
    });
    orden.sort(function (a, b) {
      if (a === "Sin apartado") return 1;
      if (b === "Sin apartado") return -1;
      return a.localeCompare(b, "es", { numeric: true });
    });
    return orden.map(function (clave) {
      return { apartado: clave, partidas: mapa[clave] };
    });
  }

  function crearSeccionApartado(grupo, vista) {
    var sec = crear("div", "apartado-section");
    sec.dataset.apartado = grupo.apartado;
    var head = crear("header", "apartado-head");
    head.setAttribute("data-cotizat-click", "partidas-toggle-apartado");
    var toggle = crear("span", "apartado-toggle", "▼");
    var label = crear("span", "apartado-label", grupo.apartado);
    var badge = crear("span", "apartado-count-badge", String(grupo.partidas.length));
    var hint = crear("span", "apartado-hint", grupo.partidas.length + " partidas");
    head.appendChild(toggle);
    head.appendChild(label);
    head.appendChild(badge);
    head.appendChild(hint);
    sec.appendChild(head);
    var body = crear("div", "apartado-body");
    body.appendChild(crearTablaApartado(grupo.partidas, vista));
    sec.appendChild(body);
    return sec;
  }

  function render(contenedor, partidas, vista) {
    var grupos = agruparPorApartado(partidas || []);
    // Si solo hay un apartado y es “Sin apartado”, renderiza una única tabla
    // sin encabezado redundante (compatibilidad con partidas libres).
    var soloSinApartado = grupos.length === 1 && grupos[0].apartado === "Sin apartado";
    contenedor.replaceChildren();
    if (!grupos.length) {
      var empty = crear("div", "subcat-placeholder");
      empty.textContent = "No hay partidas en este subcapítulo.";
      contenedor.appendChild(empty);
      return;
    }
    if (soloSinApartado) {
      contenedor.appendChild(crearTablaApartado(grupos[0].partidas, vista));
      return;
    }
    grupos.forEach(function (g) {
      contenedor.appendChild(crearSeccionApartado(g, vista));
    });
  }

  window.CotizatRows = { render: render, agruparPorApartado: agruparPorApartado };
})();
