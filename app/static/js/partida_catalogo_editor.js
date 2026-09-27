/* Editor compartido de la ficha de Partida.
   Lo usan tanto /partidas/.../editar como el creador de presupuestos. */
(function () {
  "use strict";

  var OPTIONS = [
    ["materiales", "Materiales"],
    ["mano_obra", "Mano de obra"],
    ["otros", "Equipos y otros"],
    ["complementarios", "Costes complementarios"]
  ];

  function numero(valor) {
    // Parseo robusto con formato local («1.234,56» → 1234.56).
    var s = String(valor == null ? "" : valor).trim().replace(/ /g, "").replace(/[$€Bs]/g, "");
    if (s === "") return 0;
    if (s.indexOf(",") !== -1 && s.indexOf(".") !== -1) {
      s = s.lastIndexOf(",") > s.lastIndexOf(".")
        ? s.replace(/\./g, "").replace(",", ".")
        : s.replace(/,/g, "");
    } else if (s.indexOf(",") !== -1) {
      s = s.replace(",", ".");
    }
    var n = parseFloat(s);
    return isFinite(n) ? n : 0;
  }

  function redondear2(v) {
    return Math.round((v + Number.EPSILON) * 100) / 100;
  }

  function formato(valor) {
    return numero(valor).toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  // Fuente de recursos para el autocompletado: el editor de presupuestos ya
  // tiene la lista en `window.EDITOR.RECURSOS` (cargada en diferido); las
  // páginas sueltas (Partidas) la consultan al servidor con
  // `window.RECURSOS_CATALOGO_URL`.
  function listaRecursosLocales() {
    try {
      if (window.EDITOR && Array.isArray(window.EDITOR.RECURSOS) && window.EDITOR.RECURSOS.length) {
        return window.EDITOR.RECURSOS;
      }
    } catch (e) { /* sin editor */ }
    return Array.isArray(window.RECURSOS_CATALOGO) ? window.RECURSOS_CATALOGO : [];
  }

  function normalizarRecurso(texto) {
    return String(texto || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function puntuarRecurso(recurso, consultaNorm) {
    var desc = normalizarRecurso(recurso.descripcion);
    var cod = normalizarRecurso(recurso.codigo);
    var grupo = normalizarRecurso(recurso.grupo);
    var prov = normalizarRecurso(recurso.proveedor);
    var score = -1;
    if (consultaNorm) {
      if (desc.indexOf(consultaNorm) === 0) score = 100;
      else if (desc.indexOf(consultaNorm) !== -1) score = 80;
      else if (cod && cod.indexOf(consultaNorm) !== -1) score = 70;
      else if (grupo && grupo.indexOf(consultaNorm) !== -1) score = 60;
      else if (prov && prov.indexOf(consultaNorm) !== -1) score = 50;
      if (score < 0) return -1;
    } else {
      score = 10;
    }
    // Bonus por uso frecuente (máx. 20): primero lo que más se repite.
    return score + Math.min(20, recurso.usos || 0);
  }

  function filasIniciales(root) {
    var nodo = root.querySelector("[data-partida-editor-inicial]");
    if (!nodo) return [];
    try {
      var valor = JSON.parse(nodo.textContent || "[]");
      if (typeof valor === "string") valor = JSON.parse(valor || "[]");
      if (valor && !Array.isArray(valor)) valor = valor.filas || [];
      return Array.isArray(valor) ? valor : [];
    } catch (e) { return []; }
  }

  function mount(root) {
    if (!root || root._partidaCatalogoEditor) return root && root._partidaCatalogoEditor;
    var body = root.querySelector('[data-role="tabla-descomposicion-catalogo"] tbody');
    var empty = root.querySelector('[data-role="breakdown-empty"]');
    if (!body) return null;

    function calcular() {
      var sums = { materiales: 0, mano_obra: 0, otros: 0, complementarios: 0 };
      var rows = Array.prototype.slice.call(body.querySelectorAll("tr"));
      var totalRend = 0;
      var totalCoste = 0;

      rows.forEach(function (tr) {
        var cat = tr.querySelector('[name="d_categoria"]').value;
        var und = tr.querySelector('[name="d_unidad"]').value.trim();
        var rend = numero(tr.querySelector('[name="d_rendimiento"]').value);
        var precio = numero(tr.querySelector('[name="d_precio"]').value);
        if (und === "%") return;
        // Mismo redondeo que el servidor: importe = ROUND_HALF_UP(rend × precio)
        var importe = redondear2(rend * precio);
        tr._importe = importe;
        tr.querySelector(".importe-cat").textContent = formato(importe);
        sums[cat] = redondear2((sums[cat] || 0) + importe);
        totalRend += rend;
        totalCoste = redondear2(totalCoste + importe);
      });

      var base = sums.materiales + sums.mano_obra + sums.otros;
      rows.forEach(function (tr) {
        var und = tr.querySelector('[name="d_unidad"]').value.trim();
        var precio = tr.querySelector('[name="d_precio"]');
        if (und !== "%") {
          precio.readOnly = false;
          precio.classList.remove("input-derivado");
          return;
        }
        precio.value = redondear2(base).toFixed(2);
        precio.readOnly = true;
        precio.classList.add("input-derivado");
        var importe = redondear2(numero(tr.querySelector('[name="d_rendimiento"]').value) * base / 100);
        tr._importe = importe;
        tr.querySelector(".importe-cat").textContent = formato(importe);
        sums.complementarios = redondear2((sums.complementarios || 0) + importe);
        totalCoste = redondear2(totalCoste + importe);
      });

      rows.forEach(function (tr) {
        var und = tr.querySelector('[name="d_unidad"]').value.trim();
        var rend = numero(tr.querySelector('[name="d_rendimiento"]').value);
        var pctRend = tr.querySelector(".pct-rend");
        pctRend.textContent = und === "%" ? "—" : ((totalRend ? rend / totalRend * 100 : 0).toFixed(1) + "%");
        tr.querySelector(".pct-coste").textContent = ((totalCoste ? (tr._importe || 0) / totalCoste * 100 : 0).toFixed(1) + "%");
      });

      Object.keys(sums).forEach(function (key) {
        var el = root.querySelector('[data-total="' + key + '"]');
        if (el) el.textContent = formato(sums[key]);
      });
      var directo = root.querySelector('[data-total="directo"]');
      if (directo) directo.textContent = formato(totalCoste);
      if (empty) CotizatStyles.set(empty, "display", rows.length ? "none" : "flex");
      root.dispatchEvent(new CustomEvent("partida-editor:recalculated", {
        bubbles: true,
        detail: { costes: sums, directo: totalCoste }
      }));
      actualizarBeneficioHint(sums, totalCoste);
    }

    function actualizarBeneficioHint(sums, totalCoste) {
      var precioInput = root.querySelector('[name="precio_unitario"]') || document.getElementById('catalog-precio-venta');
      var beneficioInput = root.querySelector('#catalog-beneficio-pct');
      if (!beneficioInput) beneficioInput = document.getElementById('catalog-beneficio-pct');
      var hint = root.querySelector('#catalog-beneficio-hint');
      if (!hint) hint = document.getElementById('catalog-beneficio-hint');
      if (!precioInput || !hint) return;
      var precio = numero(precioInput.value);
      var coste = typeof totalCoste === 'number' ? totalCoste : numero((root.querySelector('[data-total="directo"]')||{}).textContent);
      if (coste === 0) {
        // fallback: parse from totals elements if totalCoste not passed
        var directoEl = root.querySelector('[data-total="directo"]');
        if (directoEl) coste = numero(directoEl.textContent);
      }
      if (coste <= 0) {
        hint.textContent = 'Añade recursos para ver el beneficio';
        CotizatStyles.set(hint, "color", 'var(--text-muted)');
        return;
      }
      var beneficio = precio - coste;
      var markup = beneficio / coste * 100;
      var margen = precio > 0 ? beneficio / precio *100 : 0;
      hint.textContent = 'Coste: ';
      var costeStrong = document.createElement('strong');
      costeStrong.textContent = formato(coste);
      hint.appendChild(costeStrong);
      hint.appendChild(document.createTextNode(' · Beneficio: '));
      var beneficioStrong = document.createElement('strong');
      CotizatStyles.set(beneficioStrong, "color", beneficio >= 0 ? 'var(--green)' : 'var(--rose)');
      beneficioStrong.textContent = formato(beneficio) + ' (' + markup.toFixed(1).replace(".",",") + '% s/coste, ' + margen.toFixed(1).replace(".",",") + '% margen)';
      hint.appendChild(beneficioStrong);
      hint.title = 'Markup ' + markup.toFixed(2) + '% sobre coste | Margen ' + margen.toFixed(2) + '% sobre precio';
    }

    function input(nombre, tipo, valor, attrs) {
      var el = document.createElement("input");
      el.name = nombre;
      el.type = tipo || "text";
      if (valor !== undefined && valor !== null) el.value = valor;
      Object.keys(attrs || {}).forEach(function (key) { el.setAttribute(key, attrs[key]); });
      el.addEventListener("input", calcular);
      return el;
    }

    // -----------------------------------------------------------------
    // Autocompletado de recursos en la descripción de cada fila.
    // Rellena código, unidad, categoría y precio desde el catálogo de
    // recursos (o del servidor si la página no trae la lista).
    // -----------------------------------------------------------------
    function buscarRecursosServidor(consulta) {
      var url = window.RECURSOS_CATALOGO_URL;
      if (!url) return Promise.resolve([]);
      return fetch(url + "?q=" + encodeURIComponent(consulta || ""), {
        headers: { Accept: "application/json" },
        credentials: "same-origin"
      })
        .then(function (r) { return r.ok ? r.json() : { recursos: [] }; })
        .then(function (d) { return (d && d.recursos) || []; })
        .catch(function () { return []; });
    }

    function conectarAutocompleteRecursos(tr, inputDesc, wrapDesc) {
      var dropdown = null;
      var peticionId = 0;
      var temporizador = null;

      function cerrar() {
        if (dropdown) { dropdown.remove(); dropdown = null; }
      }

      function formatoImporte(item) {
        var valor = parseFloat(item.precio || 0) || 0;
        if (window.FMT && typeof window.FMT.fmt === "function") return window.FMT.fmt(valor, item.moneda);
        return valor.toFixed(2) + (item.moneda ? " " + item.moneda : "");
      }

      function aplicar(item) {
        if (!item) return;
        var set = function (nombre, valor) {
          var el = tr.querySelector('[name="' + nombre + '"]');
          if (el) el.value = valor == null ? "" : valor;
        };
        set("d_codigo", item.codigo);
        set("d_unidad", item.unidad);
        inputDesc.value = item.descripcion || "";
        set("d_descripcion", item.descripcion);
        var cat = tr.querySelector('[name="d_categoria"]');
        if (cat && item.categoria) {
          for (var i = 0; i < cat.options.length; i++) {
            if (cat.options[i].value === item.categoria) { cat.selectedIndex = i; break; }
          }
        }
        set("d_precio", item.precio != null ? item.precio : "");
        cerrar();
        calcular();
        inputDesc.dispatchEvent(new Event("input", { bubbles: true }));
      }

      function crearSugerencia(item) {
        var sug = document.createElement("div");
        sug.className = "suggestion-item";
        CotizatStyles.setCssText(sug, "padding:7px 10px; cursor:pointer; border-bottom:1px solid var(--bg); font-size:.8rem; display:flex; align-items:center; gap:9px;");
        var main = document.createElement("div");
        CotizatStyles.setCssText(main, "flex:1; min-width:0;");
        var title = document.createElement("div");
        CotizatStyles.setCssText(title, "font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;");
        title.textContent = item.descripcion || "";
        main.appendChild(title);
        var metaParts = [item.codigo, item.grupo, item.proveedor, item.unidad].filter(Boolean);
        if (metaParts.length) {
          var meta = document.createElement("div");
          CotizatStyles.setCssText(meta, "font-size:.7rem; color:var(--text-muted); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;");
          meta.textContent = metaParts.join(" · ");
          main.appendChild(meta);
        }
        sug.appendChild(main);
        var right = document.createElement("div");
        CotizatStyles.setCssText(right, "font-weight:600; color:var(--accent); font-size:.8rem; white-space:nowrap; margin-left:auto;");
        right.textContent = formatoImporte(item);
        if (item.aviso_precio) {
          right.textContent = "⚠ " + right.textContent;
          right.title = item.aviso_precio;
          sug.title = item.aviso_precio;
        } else if (item.origen_precio === "nacional" || item.origen_precio === "organizacion") {
          right.title = item.origen_precio === "organizacion"
            ? "Precio propio de tu empresa para este mercado"
            : "Precio nacional de referencia";
        }
        sug.appendChild(right);
        sug.addEventListener("mousedown", function (e) { e.preventDefault(); });
        sug.addEventListener("click", function (e) {
          e.stopPropagation();
          aplicar(item);
        });
        sug.addEventListener("mouseenter", function () { CotizatStyles.set(sug, "background", "var(--surface-hover)"); });
        sug.addEventListener("mouseleave", function () { CotizatStyles.set(sug, "background", "transparent"); });
        return sug;
      }

      function mostrar(consulta) {
        var idPeticion = ++peticionId;
        var locales = listaRecursosLocales();
        if (locales.length) {
          var qn = normalizarRecurso(consulta);
          var scored = locales
            .map(function (r) { return { item: r, score: puntuarRecurso(r, qn) }; })
            .filter(function (x) { return x.score >= 0; })
            .sort(function (a, b) { return b.score - a.score; })
            .slice(0, 12)
            .map(function (x) { return x.item; });
          pintar(scored);
          return;
        }
        if (window.RECURSOS_CATALOGO_URL) {
          // La página no trae la lista en memoria: se consulta al servidor
          // (con idPeticion se descartan respuestas viejas al seguir tecleando).
          buscarRecursosServidor(consulta).then(function (recursos) {
            if (idPeticion !== peticionId) return;
            pintar(recursos.slice(0, 12));
          });
          return;
        }
        cerrar();
      }

      function pintar(recursos) {
        cerrar();
        if (!recursos || !recursos.length) return;
        dropdown = document.createElement("div");
        dropdown.className = "autocomplete-suggestions";
        CotizatStyles.setCssText(dropdown, "position:absolute; top:100%; left:0; right:0; min-width:260px; background:var(--surface); border:1px solid var(--border-strong); border-radius:var(--radius-sm); max-height:240px; overflow-y:auto; z-index:1300; box-shadow:var(--shadow-lg); margin-top:3px;");
        recursos.forEach(function (item) {
          dropdown.appendChild(crearSugerencia(item));
        });
        wrapDesc.appendChild(dropdown);
      }

      inputDesc.addEventListener("focus", function () { mostrar(inputDesc.value.trim()); });
      inputDesc.addEventListener("input", function () {
        clearTimeout(temporizador);
        temporizador = setTimeout(function () { mostrar(inputDesc.value.trim()); }, 140);
      });
      inputDesc.addEventListener("keydown", function (evt) {
        if (evt.key === "Escape") cerrar();
        if (evt.key === "Enter") {
          // Con sugerencias abiertas, Enter elige la primera (y evita el
          // submit implícito del formulario).
          if (dropdown && dropdown.firstElementChild) {
            evt.preventDefault();
            dropdown.firstElementChild.click();
          }
        }
      });
      inputDesc.addEventListener("blur", function () { setTimeout(cerrar, 150); });
      document.addEventListener("click", function (evt) {
        if (dropdown && !wrapDesc.contains(evt.target)) cerrar();
      });
    }

    function add(datos) {
      datos = datos || {};
      var tr = document.createElement("tr");
      tr.className = "catalog-resource-row";

      var tdCat = document.createElement("td");
      var select = document.createElement("select");
      select.name = "d_categoria";
      OPTIONS.forEach(function (op) {
        var option = document.createElement("option");
        option.value = op[0];
        option.textContent = op[1];
        if (op[0] === (datos.categoria || "materiales")) option.selected = true;
        select.appendChild(option);
      });
      select.addEventListener("change", calcular);
      tdCat.appendChild(select);
      tr.appendChild(tdCat);

      var tdCodigo = document.createElement("td");
      tdCodigo.appendChild(input("d_codigo", "text", datos.codigo || "", { placeholder: "Código" }));
      tr.appendChild(tdCodigo);
      var tdUnidad = document.createElement("td");
      tdUnidad.appendChild(input("d_unidad", "text", datos.unidad || ((datos.categoria || "") === "mano_obra" ? "h" : "ud"), { placeholder: "ud" }));
      tr.appendChild(tdUnidad);
      var tdDesc = document.createElement("td");
      var descWrap = document.createElement("div");
      CotizatStyles.setCssText(descWrap, "position:relative; display:flex; width:100%; min-width:0;");
      var descInput = input("d_descripcion", "text", datos.descripcion || "", { placeholder: "Descripción del recurso (escribe para buscar en tus recursos…)" });
      CotizatStyles.set(descInput, "flex", "1");
      descInput.setAttribute("autocomplete", "off");
      descWrap.appendChild(descInput);
      tdDesc.appendChild(descWrap);
      conectarAutocompleteRecursos(tr, descInput, descWrap);
      tr.appendChild(tdDesc);
      var tdRend = document.createElement("td");
      tdRend.className = "right";
      tdRend.appendChild(input("d_rendimiento", "number", datos.rendimiento == null ? "" : datos.rendimiento, { step: "any", min: "0", placeholder: "0,00" }));
      tr.appendChild(tdRend);
      var tdPctR = document.createElement("td"); tdPctR.className = "right pct-rend"; tdPctR.textContent = "0%"; tr.appendChild(tdPctR);
      var tdPrecio = document.createElement("td");
      tdPrecio.className = "right";
      tdPrecio.appendChild(input("d_precio", "number", datos.precio == null ? (datos.precio_unitario == null ? "" : datos.precio_unitario) : datos.precio, { step: "any", min: "0", placeholder: "0,00" }));
      tr.appendChild(tdPrecio);
      var tdImporte = document.createElement("td"); tdImporte.className = "right importe-cat"; tdImporte.textContent = "0,00"; tr.appendChild(tdImporte);
      var tdPctC = document.createElement("td"); tdPctC.className = "right pct-coste"; tdPctC.textContent = "0%"; tr.appendChild(tdPctC);
      var tdAcciones = document.createElement("td");
      var quitar = document.createElement("button");
      quitar.type = "button";
      quitar.className = "btn btn-sm btn-ghost resource-remove";
      quitar.title = "Eliminar recurso";
      quitar.textContent = "✕";
      quitar.addEventListener("click", function () { tr.remove(); calcular(); });
      tdAcciones.appendChild(quitar);
      tr.appendChild(tdAcciones);
      body.appendChild(tr);
      return tr;
    }

    function cargar(filas) {
      body.replaceChildren();
      (Array.isArray(filas) ? filas : []).filter(function (fila) {
        return !fila.tipo || fila.tipo === "recurso";
      }).forEach(add);
      calcular();
    }

    function obtenerFilas() {
      return Array.prototype.map.call(body.querySelectorAll("tr"), function (tr) {
        return {
          tipo: "recurso",
          categoria: tr.querySelector('[name="d_categoria"]').value,
          codigo: tr.querySelector('[name="d_codigo"]').value,
          unidad: tr.querySelector('[name="d_unidad"]').value,
          descripcion: tr.querySelector('[name="d_descripcion"]').value,
          rendimiento: numero(tr.querySelector('[name="d_rendimiento"]').value),
          precio: numero(tr.querySelector('[name="d_precio"]').value),
          importe: numero(tr._importe)
        };
      });
    }

    root.querySelector('[data-action="add-recurso-catalogo"]').addEventListener("click", function () {
      var tr = add({});
      calcular();
      var foco = tr.querySelector('[name="d_descripcion"]');
      if (foco) foco.focus();
    });

    var api = { cargar: cargar, calcular: calcular, obtenerFilas: obtenerFilas, add: add, actualizarBeneficioHint: actualizarBeneficioHint };
    root._partidaCatalogoEditor = api;
    cargar(filasIniciales(root));
    // Conectar beneficio % <-> precio (catálogo y modal)
    (function conectarBeneficio(){
      var precioInput = root.querySelector('[name="precio_unitario"]') || document.getElementById('catalog-precio-venta');
      var beneficioInput = root.querySelector('#catalog-beneficio-pct') || document.getElementById('catalog-beneficio-pct');
      if (!precioInput) return;
      var timer = null;
      if (beneficioInput) {
        beneficioInput.addEventListener('input', function(){
          clearTimeout(timer);
          timer = setTimeout(function(){
            var costeEl = root.querySelector('[data-total="directo"]');
            var coste = costeEl ? numero(costeEl.textContent) : 0;
            if (coste <= 0) return;
            var pct = numero(beneficioInput.value);
            if (!isFinite(pct)) return;
            var precio = coste * (1 + pct/100);
            precioInput.value = precio.toFixed(2);
            precioInput.dispatchEvent(new Event('input', {bubbles:true}));
            calcular();
          }, 300);
        });
      }
      precioInput.addEventListener('input', function(){
        setTimeout(calcular, 60);
      });
      setTimeout(calcular, 180);
    })();
    return api;
  }

  function mountAll(scope) {
    (scope || document).querySelectorAll("[data-partida-catalogo-editor]").forEach(mount);
  }

  window.PartidaCatalogoEditor = { mount: mount, mountAll: mountAll };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { mountAll(document); });
  else mountAll(document);
})();
