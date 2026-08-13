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
      if (empty) empty.style.display = rows.length ? "none" : "flex";
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
        hint.style.color = 'var(--text-muted)';
        return;
      }
      var beneficio = precio - coste;
      var markup = beneficio / coste * 100;
      var margen = precio > 0 ? beneficio / precio *100 : 0;
      hint.innerHTML = 'Coste: <strong>' + formato(coste) + '</strong> · Beneficio: <strong style="color:'+(beneficio>=0?'var(--green)':'var(--rose)')+'">' + formato(beneficio) + ' (' + markup.toFixed(1).replace(".",",") + '% s/coste, ' + margen.toFixed(1).replace(".",",") + '% margen)</strong>';
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
      tdDesc.appendChild(input("d_descripcion", "text", datos.descripcion || "", { placeholder: "Descripción del recurso" }));
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
      body.innerHTML = "";
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
