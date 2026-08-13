/* ============================================================================
   Editor — Módulo Recetas de Estancia (Packs de Reforma por Estancia - Alt+R)
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR = window.EDITOR || {};
  var FMT = window.FMT || editor.FMT;

  var listaRecetasCache = null;
  var recetaSeleccionada = null;

  // Formateador de importes independiente del módulo de formato: usa FMT.fmtNum
  // si está disponible (miles con punto y decimales con coma) y si no, un
  // toFixed(2) de respaldo. Evita depender de helpers que puedan no existir.
  function money(valor) {
    if (FMT && typeof FMT.fmtNum === "function") return FMT.fmtNum(valor);
    var n = parseFloat(valor);
    return isNaN(n) ? "0,00" : n.toFixed(2);
  }

  function abrirModalRecetaEstancia() {
    var modal = document.getElementById("modal-recetas-estancia");
    if (!modal) return;

    modal.classList.add("open");
    document.body.classList.add("modal-open");

    cargarRecetasEnModal(function () {
      var inpMedida = document.getElementById("input-medida-pack");
      if (inpMedida) {
        inpMedida.focus();
        inpMedida.select();
      }
    });
  }

  function cargarRecetasEnModal(callback) {
    var select = document.getElementById("select-receta-pack");
    if (!select) return;

    select.innerHTML = '<option value="">Cargando packs disponibles...</option>';

    fetch("/recetas/api/list")
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.ok || !data.recetas) {
          console.error("La API de packs devolvió una respuesta inválida:", data);
          select.innerHTML = '<option value="">Error cargando packs</option>';
          return;
        }
        listaRecetasCache = data.recetas;
        try {
          renderOpcionesSelect(select, listaRecetasCache);
          if (listaRecetasCache.length > 0) {
            select.value = strId(listaRecetasCache[0].id);
            seleccionarRecetaPorId(listaRecetasCache[0].id);
          }
        } catch (errRender) {
          // Un error de renderizado de la vista previa NO debe ocultar la
          // lista de packs ya cargada: se registra y se continúa.
          console.error("Error al mostrar los packs cargados:", errRender);
        }
        if (callback) callback();
      })
      .catch(function (errRed) {
        console.error("Error de red cargando packs de estancia:", errRed);
        select.innerHTML = '<option value="">Error cargando packs</option>';
      });
  }

  function strId(id) {
    return String(id || "");
  }

  function renderOpcionesSelect(select, recetas) {
    select.innerHTML = "";
    var grupos = {};
    recetas.forEach(function (r) {
      var cat = r.categoria || "Otros";
      if (!grupos[cat]) grupos[cat] = [];
      grupos[cat].push(r);
    });

    Object.keys(grupos).forEach(function (cat) {
      var optgroup = document.createElement("optgroup");
      optgroup.label = cat;
      grupos[cat].forEach(function (r) {
        var opt = document.createElement("option");
        opt.value = strId(r.id);
        opt.textContent = r.nombre + " (" + (r.items ? r.items.length : 0) + " partidas · " + r.cantidad_base_default + " " + r.unidad_base + ")";
        optgroup.appendChild(opt);
      });
      select.appendChild(optgroup);
    });
  }

  function seleccionarRecetaPorId(id) {
    if (!listaRecetasCache) return;
    recetaSeleccionada = null;
    for (var i = 0; i < listaRecetasCache.length; i++) {
      if (strId(listaRecetasCache[i].id) === strId(id)) {
        recetaSeleccionada = listaRecetasCache[i];
        break;
      }
    }
    var inpMedida = document.getElementById("input-medida-pack");
    var labelMed = document.getElementById("label-medida-pack");
    var descEl = document.getElementById("receta-pack-desc");

    if (recetaSeleccionada) {
      if (inpMedida) inpMedida.value = recetaSeleccionada.cantidad_base_default || 10.0;
      if (labelMed) labelMed.textContent = "Medida de la estancia (" + (recetaSeleccionada.unidad_base || "m²") + ")";
      if (descEl) descEl.textContent = recetaSeleccionada.descripcion || "";
    }
    actualizarVistaPreviaPack();
  }

  function actualizarVistaPreviaPack() {
    var tbody = document.getElementById("tbody-preview-pack");
    var badgeTotal = document.getElementById("badge-total-pack");
    var inpMedida = document.getElementById("input-medida-pack");
    if (!tbody || !badgeTotal || !inpMedida) return;

    var medida = parseFloat(inpMedida.value) || 0;
    tbody.innerHTML = "";

    if (!recetaSeleccionada || !recetaSeleccionada.items || !recetaSeleccionada.items.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty" style="text-align:center; padding:2rem;">El pack no tiene partidas asociadas.</td></tr>';
      badgeTotal.textContent = "Total estimado: $" + money(0);
      return;
    }

    var totalEst = 0;
    recetaSeleccionada.items.forEach(function (item, idx) {
      var cant = 0;
      var tagTipo = "";
      if (item.tipo_calculo === "fijo") {
        cant = item.cantidad_fija || 1.0;
        tagTipo = "Fijo";
      } else {
        cant = Math.round((item.coeficiente || 1.0) * medida * 100) / 100;
        tagTipo = "Prop. (" + (item.coeficiente || 1.0) + "x)";
      }
      var prec = parseFloat(item.precio || 0);
      var imp = Math.round(cant * prec * 100) / 100;
      totalEst += imp;

      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td style="text-align:center; color:var(--muted);">' + (idx + 1) + '</td>' +
        '<td><strong>' + (item.nombre || "") + '</strong></td>' +
        '<td style="text-align:center;"><span class="badge" style="font-size:0.75rem;">' + tagTipo + '</span></td>' +
        '<td style="text-align:center; font-weight:600;">' + cant + '</td>' +
        '<td style="text-align:center;">' + (item.unidad || "m²") + '</td>' +
        '<td style="text-align:right;">$' + money(prec) + '</td>' +
        '<td style="text-align:right; font-weight:600;">$' + money(imp) + '</td>';
      tbody.appendChild(tr);
    });

    badgeTotal.textContent = "Total estimado: $" + money(totalEst);
  }

  function insertarPackSeleccionado() {
    if (!recetaSeleccionada) return;
    var inpMedida = document.getElementById("input-medida-pack");
    var medida = inpMedida ? (parseFloat(inpMedida.value) || 10.0) : 10.0;

    var nombreCapitulo = recetaSeleccionada.nombre + " (" + medida + " " + (recetaSeleccionada.unidad_base || "m²") + ")";
    var partidasParaCapitulo = (recetaSeleccionada.items || []).map(function (it) {
      var cant = (it.tipo_calculo === "fijo") ? (it.cantidad_fija || 1.0) : Math.round((it.coeficiente || 1.0) * medida * 100) / 100;
      return {
        nombre: it.nombre || "",
        descripcion: it.descripcion || "",
        unidad: it.unidad || "m²",
        cantidad: cant,
        precio: it.precio || 0,
        categoria: it.categoria || recetaSeleccionada.categoria || "Albañilería y Revestimientos"
      };
    });

    if (!editor.Capitulo || !editor.Capitulo.crear) {
      alert("Error en el módulo de capítulos.");
      return;
    }

    var nuevoCap = editor.Capitulo.crear({
      nombre: nombreCapitulo,
      partidas: partidasParaCapitulo
    }, editor);

    var modal = document.getElementById("modal-recetas-estancia");
    if (modal) {
      modal.classList.remove("open");
      document.body.classList.remove("modal-open");
    }

    if (editor.renumerar) editor.renumerar();
    if (editor.recalcular) editor.recalcular();
    if (editor.marcarCambio) editor.marcarCambio();

    // Flash y scroll al nuevo capítulo
    var flash = document.getElementById("undo-flash");
    if (flash) {
      flash.textContent = "⚡ Pack insertado: " + nombreCapitulo;
      flash.classList.add("show");
      setTimeout(function () { flash.classList.remove("show"); }, 2000);
    }
    if (nuevoCap && nuevoCap.scrollIntoView) {
      nuevoCap.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  // -------------------------------------------------------------------------
  // Guardar un capítulo completo del editor como un nuevo Pack de Estancia
  // -------------------------------------------------------------------------

  var capAGuardarActual = null;

  function guardarCapituloComoReceta(capEl) {
    if (!capEl) return;
    capAGuardarActual = capEl;

    var wraps = capEl.querySelectorAll(".partida-wrap");
    if (!wraps.length) {
      alert("El capítulo está vacío. Añade al menos una partida antes de guardarlo como Pack.");
      return;
    }

    var inpNombre = capEl.querySelector(".capitulo-name");
    var capTitulo = inpNombre ? inpNombre.value.trim() : "Nuevo Pack de Estancia";

    var modal = document.getElementById("modal-guardar-capitulo-receta");
    if (!modal) return;

    var inpNomPack = document.getElementById("guardar-pack-nombre");
    if (inpNomPack) inpNomPack.value = capTitulo || "Nuevo Pack de Estancia";

    modal.classList.add("open");
    document.body.classList.add("modal-open");
    if (inpNomPack) {
      inpNomPack.focus();
      inpNomPack.select();
    }
  }

  function confirmarGuardadoCapituloEnReceta() {
    if (!capAGuardarActual) return;

    var inpNomPack = document.getElementById("guardar-pack-nombre");
    var selCat = document.getElementById("guardar-pack-categoria");
    var inpUnd = document.getElementById("guardar-pack-unidad");
    var inpBase = document.getElementById("guardar-pack-base");
    var chkCoef = document.getElementById("guardar-pack-coeficientes");

    var nombrePack = inpNomPack ? inpNomPack.value.trim() : "Pack guardado";
    if (!nombrePack) {
      alert("El nombre del pack es obligatorio.");
      return;
    }

    var categoria = selCat ? selCat.value : "Otros";
    var unidadBase = inpUnd ? inpUnd.value.trim() : "m²";
    var cantidadBase = inpBase ? (parseFloat(inpBase.value) || 10.0) : 10.0;
    var calCoef = chkCoef ? chkCoef.checked : true;

    // Recolectar partidas de la cabecera / DOM
    var items = [];
    capAGuardarActual.querySelectorAll(".partida-wrap").forEach(function (w) {
      var nom = w.querySelector('[data-f="p_nombre"]');
      var und = w.querySelector('[data-f="p_und"]');
      var cant = w.querySelector('[data-f="p_cant"]');
      var prec = w.querySelector('[data-f="p_precio"]');
      var desc = w.querySelector('[data-f="p_desc"]');

      var nomVal = nom ? nom.value.trim() : "";
      if (!nomVal) return; // ignorar filas en blanco
      var cantVal = cant ? (parseFloat(cant.value) || 1.0) : 1.0;
      var precVal = prec ? (parseFloat(prec.value) || 0) : 0;
      var undVal = und ? (und.value.trim() || "und") : "und";
      var descVal = desc ? desc.value.trim() : "";

      items.push({
        nombre: nomVal,
        descripcion: descVal,
        unidad: undVal,
        cantidad: cantVal,
        precio: precVal,
        categoria: categoria
      });
    });

    if (!items.length) {
      alert("No hay partidas válidas con nombre para guardar.");
      return;
    }

    fetch("/recetas/api/guardar-desde-capitulo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre: nombrePack,
        categoria: categoria,
        unidad_base: unidadBase,
        cantidad_base_default: cantidadBase,
        calcular_coeficientes: calCoef,
        items: items
      })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (!data.ok) {
        alert(data.error || "Error guardando pack.");
        return;
      }
      var modal = document.getElementById("modal-guardar-capitulo-receta");
      if (modal) {
        modal.classList.remove("open");
        document.body.classList.remove("modal-open");
      }
      var flash = document.getElementById("undo-flash");
      if (flash) {
        flash.textContent = "💾 Pack guardado: " + data.nombre;
        flash.classList.add("show");
        setTimeout(function () { flash.classList.remove("show"); }, 3000);
      }
    })
    .catch(function () {
      alert("Error de conexión al guardar el pack de estancia.");
    });
  }

  // -------------------------------------------------------------------------
  // Event Listeners y Exposición Global
  // -------------------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", function () {
    var btnRecetaTop = document.getElementById("btn-modal-receta");
    var btnRecetaSec = document.getElementById("btn-modal-receta-seccion");
    if (btnRecetaTop) btnRecetaTop.addEventListener("click", abrirModalRecetaEstancia);
    if (btnRecetaSec) btnRecetaSec.addEventListener("click", abrirModalRecetaEstancia);

    var selPack = document.getElementById("select-receta-pack");
    var inpMedida = document.getElementById("input-medida-pack");
    var btnInsertar = document.getElementById("btn-insertar-pack-estancia");
    var btnConfirmarGuardar = document.getElementById("btn-confirmar-guardar-pack");

    if (selPack) {
      selPack.addEventListener("change", function () {
        seleccionarRecetaPorId(this.value);
      });
    }
    if (inpMedida) {
      inpMedida.addEventListener("input", actualizarVistaPreviaPack);
      inpMedida.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          insertarPackSeleccionado();
        }
      });
    }
    if (btnInsertar) {
      btnInsertar.addEventListener("click", insertarPackSeleccionado);
    }
    if (btnConfirmarGuardar) {
      btnConfirmarGuardar.addEventListener("click", confirmarGuardadoCapituloEnReceta);
    }
  });

  editor.abrirModalRecetaEstancia = abrirModalRecetaEstancia;
  editor.guardarCapituloComoReceta = guardarCapituloComoReceta;
})();
