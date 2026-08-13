/* ============================================================================
   Importador Excel embebido en el editor de presupuestos

   Analiza, valida y confirma una importación sin navegar a otra pantalla.
   En presupuestos existentes el servidor persiste las partidas al confirmar;
   en uno nuevo las guarda ya en el catálogo y las mantiene en el constructor
   hasta el guardado normal del presupuesto.
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR || {};
  var estado = {
    formato: "tabular",
    encabezados: [],
    filas: [],
    mapeo: {},
    primeraFila: 2,
    importacionId: "",
    partidasCype: []
  };

  function $(id) { return document.getElementById(id); }

  function camposImportables() {
    var nodo = $("campos-importacion-inline");
    if (!nodo) return {};
    try { return JSON.parse(nodo.textContent || "{}"); }
    catch (e) { return {}; }
  }

  function esCype() { return estado.formato === "cype_descompuesto"; }

  function normalizar(valor) {
    return String(valor || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "");
  }

  function mostrarError(mensaje) {
    var caja = $("excel-inline-error");
    if (!caja) return;
    caja.textContent = mensaje || "";
    caja.style.display = mensaje ? "" : "none";
  }

  function limpiarIssues() {
    var caja = $("excel-inline-issues");
    if (caja) caja.replaceChildren();
  }

  function mostrarIssues(errores, advertencias) {
    var caja = $("excel-inline-issues");
    if (!caja) return;
    caja.replaceChildren();
    (errores || []).forEach(function (issue) {
      var div = document.createElement("div");
      div.className = "import-issue error";
      div.textContent = (issue.fila ? "Fila " + issue.fila + ": " : "") + issue.mensaje;
      caja.appendChild(div);
    });
    (advertencias || []).slice(0, 20).forEach(function (issue) {
      var div = document.createElement("div");
      div.className = "import-issue warning";
      div.textContent = (issue.fila ? "Fila " + issue.fila + ": " : "") + issue.mensaje;
      caja.appendChild(div);
    });
  }

  function resetear() {
    estado = {
      formato: "tabular", encabezados: [], filas: [], mapeo: {},
      primeraFila: 2, importacionId: "", partidasCype: []
    };
    var file = $("excel-inline-file");
    if (file) file.value = "";
    var files = $("excel-inline-files");
    if (files) files.textContent = "Ningún archivo seleccionado";
    $("excel-inline-source").style.display = "";
    $("excel-inline-review").classList.add("import-hidden");
    $("excel-inline-mapping").classList.add("import-hidden");
    $("excel-inline-cype-chapter").classList.add("import-hidden");
    $("excel-inline-header").closest(".excel-header-check").style.display = "";
    $("excel-inline-preview").replaceChildren();
    limpiarIssues();
    mostrarError("");
  }

  function abrir() {
    resetear();
    var modal = $("modal-importar-excel");
    modal.classList.add("open");
    document.body.classList.add("modal-open");
  }

  function cerrar() {
    var modal = $("modal-importar-excel");
    modal.classList.remove("open");
    document.body.classList.remove("modal-open");
  }

  function actualizarArchivos() {
    var input = $("excel-inline-file");
    var salida = $("excel-inline-files");
    var nombres = Array.prototype.map.call(input.files || [], function (f) { return f.name; });
    salida.textContent = nombres.length ? nombres.join(" · ") : "Ningún archivo seleccionado";
    mostrarError("");
  }

  function crearCeldaTexto(tag, texto) {
    var el = document.createElement(tag);
    el.textContent = texto == null ? "" : String(texto);
    return el;
  }

  function renderMapeo() {
    var body = $("excel-inline-mapping-body");
    var campos = camposImportables();
    body.replaceChildren();
    Object.keys(campos).forEach(function (campo) {
      var tr = document.createElement("tr");
      var etiqueta = crearCeldaTexto("th", campos[campo] + (campo === "partida" ? " *" : ""));
      var td = document.createElement("td");
      var select = document.createElement("select");
      select.dataset.importField = campo;
      var vacio = document.createElement("option");
      vacio.value = "";
      vacio.textContent = "— No importar —";
      select.appendChild(vacio);
      estado.encabezados.forEach(function (encabezado, indice) {
        var opcion = document.createElement("option");
        opcion.value = String(indice);
        opcion.textContent = encabezado;
        if (estado.mapeo[campo] === indice) opcion.selected = true;
        select.appendChild(opcion);
      });
      td.appendChild(select);
      tr.appendChild(etiqueta);
      tr.appendChild(td);
      body.appendChild(tr);
    });
  }

  function renderPreviewTabular() {
    var cont = $("excel-inline-preview");
    cont.replaceChildren();
    var table = document.createElement("table");
    table.className = "table";
    var thead = document.createElement("thead");
    var hr = document.createElement("tr");
    estado.encabezados.forEach(function (h) { hr.appendChild(crearCeldaTexto("th", h)); });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tbody = document.createElement("tbody");
    estado.filas.slice(0, 6).forEach(function (fila) {
      var tr = document.createElement("tr");
      estado.encabezados.forEach(function (_, i) { tr.appendChild(crearCeldaTexto("td", fila[i] || "")); });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    cont.appendChild(table);
  }

  function renderPreviewCype() {
    var cont = $("excel-inline-preview");
    cont.replaceChildren();
    estado.partidasCype.forEach(function (partida) {
      var item = document.createElement("div");
      item.className = "excel-cype-item";
      var texto = document.createElement("div");
      var titulo = document.createElement("strong");
      titulo.textContent = (partida.codigo ? partida.codigo + " · " : "") + (partida.nombre || "Partida sin nombre");
      texto.appendChild(titulo);
      var meta = document.createElement("span");
      meta.textContent = (partida.unidad || "ud") + " · " + (partida.filas || []).length + " filas conservadas";
      texto.appendChild(meta);
      var precio = document.createElement("strong");
      precio.className = "excel-cype-price";
      precio.textContent = Number(partida.coste_directo_unitario || 0).toLocaleString("es-ES", {
        minimumFractionDigits: 2, maximumFractionDigits: 2
      });
      item.appendChild(texto);
      item.appendChild(precio);
      cont.appendChild(item);
    });
  }

  function renderAnalisis(data) {
    estado.formato = data.formato || "tabular";
    estado.importacionId = data.importacion_id || "";
    estado.partidasCype = data.partidas || [];
    estado.encabezados = data.encabezados || [];
    estado.filas = data.filas || [];
    estado.mapeo = data.mapeo_sugerido || {};
    estado.primeraFila = data.primera_fila || 2;

    $("excel-inline-source").style.display = "none";
    $("excel-inline-review").classList.remove("import-hidden");
    $("excel-inline-header").closest(".excel-header-check").style.display = esCype() ? "none" : "";
    limpiarIssues();

    if (esCype()) {
      $("excel-inline-mapping").classList.add("import-hidden");
      $("excel-inline-cype-chapter").classList.remove("import-hidden");
      $("excel-inline-result-title").textContent = estado.partidasCype.length + " partida(s) CYPE detectada(s)";
      var totalFilas = estado.partidasCype.reduce(function (n, p) { return n + (p.filas || []).length; }, 0);
      $("excel-inline-result-meta").textContent = totalFilas + " filas técnicas y fórmulas se conservarán.";
      renderPreviewCype();
    } else {
      $("excel-inline-mapping").classList.remove("import-hidden");
      $("excel-inline-cype-chapter").classList.add("import-hidden");
      $("excel-inline-result-title").textContent = estado.filas.length + " fila(s) detectada(s)";
      $("excel-inline-result-meta").textContent = "Revisa la asignación y añádelas directamente al presupuesto.";
      renderMapeo();
      renderPreviewTabular();
    }
  }

  async function analizar() {
    var input = $("excel-inline-file");
    if (!input.files || !input.files.length) {
      mostrarError("Selecciona al menos un archivo .xlsx o .csv.");
      return;
    }
    var boton = $("btn-analizar-excel-inline");
    var form = new FormData();
    Array.prototype.forEach.call(input.files, function (file) { form.append("archivo", file); });
    form.append("texto", "");
    form.append("tiene_encabezados", $("excel-inline-header").checked ? "1" : "0");
    boton.disabled = true;
    boton.textContent = "Analizando…";
    mostrarError("");
    try {
      var response = await fetch("/presupuestos/importar/analizar", { method: "POST", body: form });
      var data = await response.json();
      if (!data.ok) throw new Error(data.error || "No se pudo analizar el archivo.");
      renderAnalisis(data);
    } catch (error) {
      mostrarError(error.message || "No se pudo analizar el archivo.");
    } finally {
      boton.disabled = false;
      boton.textContent = "Analizar archivo";
    }
  }

  function payload() {
    var datos = {
      formato: estado.formato,
      modo: "editor_inline",
      presupuesto_destino_id: window.BUDGET_ID || null
    };
    if (esCype()) {
      datos.importacion_id = estado.importacionId;
      datos.capitulo_cype = $("excel-inline-chapter").value || "PARTIDAS IMPORTADAS";
      return datos;
    }
    var mapeo = {};
    $("excel-inline-mapping-body").querySelectorAll("[data-import-field]").forEach(function (select) {
      mapeo[select.dataset.importField] = select.value === "" ? null : Number(select.value);
    });
    datos.filas = estado.filas;
    datos.mapeo = mapeo;
    datos.primera_fila = estado.primeraFila;
    return datos;
  }

  function buscarCapitulo(nombre) {
    var clave = normalizar(nombre);
    var encontrado = null;
    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (cap) {
      var input = cap.querySelector('[data-f="cap_nombre"]');
      if (!encontrado && input && normalizar(input.value) === clave) encontrado = cap;
    });
    return encontrado;
  }

  function capituloVacio() {
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    for (var i = 0; i < caps.length; i++) {
      var input = caps[i].querySelector('[data-f="cap_nombre"]');
      if (input && !input.value.trim() && !caps[i].querySelector(".partida-wrap")) return caps[i];
    }
    return null;
  }

  function actualizarCatalogo(datos) {
    var indiceExistente = (editor.CATALOGO || []).findIndex(function (p) {
      return (datos.id && Number(p.id) === Number(datos.id)) || normalizar(p.nombre) === normalizar(datos.nombre);
    });
    if (indiceExistente >= 0) {
      editor.CATALOGO[indiceExistente] = Object.assign({}, editor.CATALOGO[indiceExistente], datos);
      return editor.CATALOGO[indiceExistente];
    }
    var nueva = {
      id: null,
      nombre: datos.nombre || "",
      descripcion: datos.descripcion || "",
      precio: Number(datos.precio || 0),
      unidad: datos.unidad || "ud",
      categoria: datos.categoria || "General",
      subcategoria: "",
      codigo: datos.codigo_externo || "",
      proveedor: "",
      coste_materiales: Number(datos.coste_materiales || 0),
      coste_mano_obra: Number(datos.coste_mano_obra || 0),
      coste_complementarios: Number(datos.coste_complementarios || 0),
      coste_otros: Number(datos.coste_otros || 0),
      desperdicio_recomendado_pct: Number(datos.desperdicio_pct || 0),
      descomposicion: datos.descomposicion || null,
      usos: 1
    };
    editor.CATALOGO.push(nueva);
    return nueva;
  }

  function insertarEnEditor(capitulos) {
    var primeraNueva = null;
    (capitulos || []).forEach(function (datosCapitulo) {
      var cap = buscarCapitulo(datosCapitulo.nombre);
      if (!cap) {
        cap = capituloVacio();
        if (cap) {
          cap.querySelector('[data-f="cap_nombre"]').value = datosCapitulo.nombre;
        } else {
          cap = editor.Capitulo.crear({ nombre: datosCapitulo.nombre, partidas: [] }, editor);
        }
      }
      cap.classList.remove("collapsed");
      (datosCapitulo.partidas || []).forEach(function (datosPartida) {
        var fichaCatalogo = actualizarCatalogo(datosPartida);
        if (fichaCatalogo && fichaCatalogo.id) datosPartida.catalogo_id = fichaCatalogo.id;
        var wrap = editor.Partida.crearPartida(cap, datosPartida, editor);
        if (!primeraNueva) primeraNueva = wrap;
        if (wrap) {
          var row = wrap.querySelector(".partida-row");
          if (row) {
            row.classList.add("flash");
            setTimeout(function () { row.classList.remove("flash"); }, 1400);
          }
        }
      });
    });
    editor.renumerar();
    editor.recalcular();
    editor.marcarCambio();
    if (primeraNueva) {
      setTimeout(function () { primeraNueva.scrollIntoView({ behavior: "smooth", block: "center" }); }, 150);
    }
  }

  function toast(mensaje) {
    var flash = $("undo-flash");
    if (!flash) return;
    flash.textContent = "✓ " + mensaje;
    flash.classList.add("show");
    setTimeout(function () { flash.classList.remove("show"); }, 4500);
  }

  async function confirmar() {
    var boton = $("btn-confirmar-excel-inline");
    boton.disabled = true;
    boton.textContent = "Validando…";
    mostrarError("");
    limpiarIssues();
    try {
      var datosPayload = payload();
      var validacionResponse = await fetch("/presupuestos/importar/validar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datosPayload)
      });
      var validacion = await validacionResponse.json();
      if (!validacion.ok) throw new Error(validacion.error || "No se pudo validar la importación.");
      if ((validacion.errores || []).length) {
        mostrarIssues(validacion.errores, validacion.advertencias);
        throw new Error("Corrige los errores indicados antes de importar.");
      }

      boton.textContent = "Guardando…";
      var response = await fetch("/presupuestos/importar/confirmar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datosPayload)
      });
      var data = await response.json();
      if (!data.ok) {
        mostrarIssues(data.errores || [], data.advertencias || []);
        throw new Error(data.error || "No se pudo guardar la importación.");
      }
      (data.catalogo || []).forEach(actualizarCatalogo);
      insertarEnEditor(data.capitulos || []);
      cerrar();
      toast(data.mensaje || ((data.importadas || 0) + " partida(s) importada(s)."));
    } catch (error) {
      mostrarError(error.message || "No se pudo completar la importación.");
    } finally {
      boton.disabled = false;
      boton.textContent = "✓ Añadir al presupuesto";
    }
  }

  function init() {
    if (!$("btn-subir-excel") || !editor.contCapitulos) return;
    $("btn-subir-excel").addEventListener("click", abrir);
    $("excel-inline-file").addEventListener("change", actualizarArchivos);
    $("btn-analizar-excel-inline").addEventListener("click", analizar);
    $("btn-confirmar-excel-inline").addEventListener("click", confirmar);
    $("btn-cambiar-excel-inline").addEventListener("click", resetear);

    var zona = $("excel-drop-zone");
    ["dragenter", "dragover"].forEach(function (evento) {
      zona.addEventListener(evento, function (e) { e.preventDefault(); zona.classList.add("drag-over"); });
    });
    ["dragleave", "drop"].forEach(function (evento) {
      zona.addEventListener(evento, function (e) { e.preventDefault(); zona.classList.remove("drag-over"); });
    });
    zona.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
        $("excel-inline-file").files = e.dataTransfer.files;
        actualizarArchivos();
      }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
