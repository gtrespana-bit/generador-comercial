/* ============================================================================
   Editor — Estimación de tiempo de obra (indicador profesional)

   Réplica ligera del motor de tiempos del servidor (app/services/tiempos.py)
   ahora con desglose por oficio (oficial / ayudante / capataz) y duración
   crítica (max de roles en paralelo).

   1. Descomposición de costes: filas de recursos con unidad de tiempo
      (h, día…) → horas por unidad. Las de mano de obra se clasifican por rol
      (oficial / ayudante) según su descripción; el resto con unidad de tiempo
      cuenta como equipos.
   2. Tiempo estimado del catálogo (horas por unidad) como respaldo. Si el
      catálogo tiene desglose oficial/ayudante se respeta, si no se reparte
      60/40.
   3. Estimación por coste de mano de obra ÷ tarifa media (opcional).
   4. Override manual por partida (tiempo_manual_*): si la partida tiene horas
      manuales fijadas en la página de tiempos, ese valor es prioritario.

   El detalle completo vive en /presupuestos/<id>/tiempos.
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  var FMT = window.FMT;
  var CFG = window.TIEMPOS_CFG || { jornada: 8, tarifa: 8, por_coste: true };

  var UNIDADES_HORA = { h: 1, hr: 1, hrs: 1, hs: 1, hora: 1, horas: 1 };
  var UNIDADES_DIA = { d: 1, dia: 1, dias: 1, j: 1, jornada: 1, jornadas: 1, jornal: 1 };

  function normalizarUnidad(u) {
    return String(u || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[.\\s/]+/g, "");
  }

  function factorUnidad(u) {
    var n = normalizarUnidad(u);
    if (!n) return null;
    if (UNIDADES_HORA[n]) return 1;
    if (UNIDADES_DIA[n]) return Math.max(0.1, CFG.jornada || 8);
    return null;
  }

  function normalizarTexto(t){
    return String(t||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
  }

  function derivarCategoria(grupo, codigo) {
    var t = String((grupo || "") + " " + (codigo || ""))
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "");
    if (t.indexOf("manodeobra") !== -1 || t.indexOf("personal") !== -1 || t.indexOf("mo") === 0) return "mano_obra";
    return "otros";
  }

  function categoriaFila(tr) {
    var sel = tr.querySelector('[data-f="d_categoria"]');
    var cat = sel ? sel.value : (tr.dataset.categoria || "");
    if (cat === "mano_obra" || cat === "materiales" || cat === "complementarios" || cat === "otros") return cat;
    return derivarCategoria(tr.dataset.grupo, tr.dataset.codigo);
  }

  function rolManoObra(tr){
    var txt = normalizarTexto((tr.dataset.descripcion||"") + " " + (tr.dataset.grupo||"") + " " + (tr.dataset.codigo||""));
    if(txt.indexOf("capataz")!==-1 || txt.indexOf("encargado")!==-1 || txt.indexOf("jefe")!==-1) return "capataz";
    if(txt.indexOf("oficial")!==-1 || txt.indexOf("maestro")!==-1) return "oficial";
    if(txt.indexOf("ayudante")!==-1 || txt.indexOf("ayte")!==-1 || txt.indexOf("peon")!==-1 || txt.indexOf("auxiliar")!==-1 || txt.indexOf("operario")!==-1) return "ayudante";
    // fallback: si no se reconoce, tratar como ayudante para no inflar oficial
    return "ayudante";
  }

  // -------------------------------------------------------------------------
  // Cálculo por partida (misma semántica que el servidor + manual)
  // -------------------------------------------------------------------------

  function horasPartida(wrap) {
    var cantidad = editor.cantidadDe(wrap);

    // 0) Override manual por partida (si existe en el wrap)
    // El editor puede recibir tiempo manual via hidden inputs (si se cargan desde la página de tiempos al volver)
    // Por ahora buscamos inputs manuales si existen
    var manualTotalEl = wrap.querySelector('[data-f="p_tiempo_manual_horas"]');
    var manualOfEl = wrap.querySelector('[data-f="p_tiempo_manual_oficial"]');
    var manualAyEl = wrap.querySelector('[data-f="p_tiempo_manual_ayudante"]');
    // Si el editor tiene esos hidden, usarlos
    var mTotal = manualTotalEl ? FMT.parseNum(manualTotalEl.value) : 0;
    var mOf = manualOfEl ? FMT.parseNum(manualOfEl.value) : 0;
    var mAy = manualAyEl ? FMT.parseNum(manualAyEl.value) : 0;
    var tieneManual = (manualTotalEl && manualTotalEl.value.trim()!=="") || (manualOfEl && manualOfEl.value.trim()!=="") || (manualAyEl && manualAyEl.value.trim()!=="");
    if(tieneManual){
      var horasPorUd, oficialPorUd, ayudantePorUd, equiposPorUd;
      if(mOf>0 || mAy>0){
        oficialPorUd = mOf;
        ayudantePorUd = mAy;
        horasPorUd = mOf + mAy;
        equiposPorUd = 0;
      } else if(mTotal>0){
        horasPorUd = mTotal;
        oficialPorUd = mTotal * 0.6;
        ayudantePorUd = mTotal * 0.4;
        equiposPorUd = 0;
      } else {
        horasPorUd = 0;
        oficialPorUd = 0;
        ayudantePorUd = 0;
        equiposPorUd = 0;
      }
      var duracionPorUd = Math.max(oficialPorUd, ayudantePorUd, equiposPorUd) || horasPorUd;
      return {
        cantidad: cantidad,
        horas_por_unidad: horasPorUd,
        duracion_por_unidad: duracionPorUd,
        horas: cantidad * horasPorUd,
        duracion_h: cantidad * duracionPorUd,
        mano_obra_h: cantidad * (oficialPorUd+ayudantePorUd),
        oficial_h: cantidad * oficialPorUd,
        ayudante_h: cantidad * ayudantePorUd,
        equipos_h: cantidad * equiposPorUd,
        fuente: mTotal||mOf||mAy ? "manual" : "sin_datos",
        detalle: []
      };
    }

    var horasPorUd = 0, manoObraPorUd = 0, oficialPorUd = 0, ayudantePorUd = 0, capatazPorUd = 0, equiposPorUd = 0, duracionPorUd = 0, fuente = "sin_datos", detalle = [];

    wrap.querySelectorAll(".drow").forEach(function (tr) {
      if (tr.dataset.tipo && tr.dataset.tipo !== "recurso") return;
      var unidad = String(tr.dataset.unidad || "").trim();
      if (unidad === "%") return;
      var factor = factorUnidad(unidad);
      if (factor === null) return;
      var rendEl = tr.querySelector('[data-f="d_rendimiento"]');
      if(!rendEl) return;
      var rend = FMT.parseNum(rendEl.value);
      if (rend <= 0) return;
      var horasUd = rend * factor;
      var esMO = categoriaFila(tr) === "mano_obra";
      var rol = esMO ? rolManoObra(tr) : "equipos";
      horasPorUd += horasUd;
      if (esMO){
        manoObraPorUd += horasUd;
        if(rol==="oficial") oficialPorUd += horasUd;
        else if(rol==="ayudante") ayudantePorUd += horasUd;
        else if(rol==="capataz") capatazPorUd += horasUd;
        else ayudantePorUd += horasUd;
      } else equiposPorUd += horasUd;
      detalle.push({
        descripcion: tr.dataset.descripcion || "",
        codigo: tr.dataset.codigo || "",
        grupo: tr.dataset.grupo || "",
        unidad: unidad,
        rendimiento: rend,
        horas_por_unidad: horasUd,
        mano_obra: esMO,
        rol: rol
      });
    });

    if (horasPorUd > 0) {
      fuente = "descompuesto";
      duracionPorUd = Math.max(oficialPorUd, ayudantePorUd, capatazPorUd, equiposPorUd) || manoObraPorUd;
      if(!duracionPorUd) duracionPorUd = manoObraPorUd;
    } else {
      var tCat = FMT.parseNum((wrap.querySelector('[data-f="p_tiempo_estimado_horas"]') || {}).value);
      var tCatOf = FMT.parseNum((wrap.querySelector('[data-f="p_tiempo_oficial"]') || {}).value);
      var tCatAy = FMT.parseNum((wrap.querySelector('[data-f="p_tiempo_ayudante"]') || {}).value);
      if (tCat > 0 || tCatOf >0 || tCatAy>0) {
        if(tCatOf>0 || tCatAy>0){
          oficialPorUd = tCatOf;
          ayudantePorUd = tCatAy;
          horasPorUd = tCatOf + tCatAy;
          manoObraPorUd = horasPorUd;
        } else {
          horasPorUd = tCat;
          manoObraPorUd = tCat;
          oficialPorUd = tCat * 0.6;
          ayudantePorUd = tCat * 0.4;
        }
        duracionPorUd = Math.max(oficialPorUd, ayudantePorUd) || horasPorUd;
        fuente = "catalogo";
      } else {
        var costeMO = FMT.parseNum((wrap.querySelector('[data-f="p_coste_mano_obra"]') || {}).value);
        if (CFG.por_coste && CFG.tarifa > 0 && costeMO > 0) {
          horasPorUd = costeMO / CFG.tarifa;
          manoObraPorUd = horasPorUd;
          oficialPorUd = horasPorUd * 0.6;
          ayudantePorUd = horasPorUd * 0.4;
          duracionPorUd = Math.max(oficialPorUd, ayudantePorUd);
          fuente = "coste";
        }
      }
    }

    return {
      cantidad: cantidad,
      horas_por_unidad: horasPorUd,
      duracion_por_unidad: duracionPorUd,
      horas: cantidad * horasPorUd,
      duracion_h: cantidad * duracionPorUd,
      mano_obra_h: cantidad * manoObraPorUd,
      oficial_h: cantidad * oficialPorUd,
      ayudante_h: cantidad * ayudantePorUd,
      capataz_h: cantidad * capatazPorUd,
      equipos_h: cantidad * equiposPorUd,
      fuente: fuente,
      detalle: detalle
    };
  }

  // -------------------------------------------------------------------------
  // Render del indicador en la tarjeta de totales y en la barra sticky
  // -------------------------------------------------------------------------

  function fmtHoras(v) {
    if (v == null || isNaN(v)) return "—";
    return (Math.round(v * 10) / 10).toLocaleString("es-VE", { maximumFractionDigits: 1 });
  }

  function fmtDias(v) {
    return (Math.round(v * 10) / 10).toLocaleString("es-VE", { maximumFractionDigits: 1 });
  }

  function calcularTiempos() {
    var totalHoras = 0, totalMO = 0, totalOf=0, totalAy=0, totalEq=0, totalDur=0, nPartidas = 0, nSinDatos = 0;
    var avanzado = !!(document.getElementById("usar-funciones-avanzadas") && document.getElementById("usar-funciones-avanzadas").checked);

    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (cap) {
      cap.querySelectorAll(".partida-wrap").forEach(function (wrap) {
        var tipoEl = wrap.querySelector('[data-f="p_tipo_partida"]');
        var selEl = wrap.querySelector('[data-f="p_seleccionada"]');
        var tipo = avanzado && tipoEl ? tipoEl.value : "included";
        var activa = !avanzado || !selEl || selEl.value === "1" || ["included", "provisional", "measurement"].indexOf(tipo) !== -1;
        if (!activa || tipo === "excluded") return;

        var t = horasPartida(wrap);
        nPartidas += 1;
        if (t.fuente === "sin_datos") nSinDatos += 1;
        totalHoras += t.horas;
        totalDur += t.duracion_h;
        totalMO += t.mano_obra_h;
        totalOf += t.oficial_h;
        totalAy += t.ayudante_h;
        totalEq += t.equipos_h;
      });
    });

    var jornada = Math.max(0.1, CFG.jornada || 8);
    var diasHombre = totalHoras / jornada;
    var diasDur = totalDur / jornada;

    var el = document.getElementById("ui-tiempo");
    if (el) {
      if(!nPartidas){
        el.textContent = "—";
        el.title = "";
      } else {
        el.textContent = "≈ " + fmtHoras(totalMO) + " h-h · " + fmtDias(diasDur) + " días críticos";
        el.title = `Horas-hombre: ${fmtHoras(totalMO)} h (${fmtHoras(totalOf)} h oficial + ${fmtHoras(totalAy)} h ayudante${totalEq>0?` + ${fmtHoras(totalEq)} h equipos`:""}). Duración crítica: ${fmtHoras(totalDur)} h (${fmtDias(diasDur)} días con 1 cuadrilla). Jornada ${fmtHoras(jornada)} h/día. Total horas (hombre+equipo): ${fmtHoras(totalHoras)} h.`;
      }
    }

    var nota = document.getElementById("ui-tiempo-nota");
    if (nota) {
      if (!nPartidas) {
        nota.textContent = "Añade partidas para ver la estimación de tiempo.";
      } else {
        var partes = [];
        if (nSinDatos > 0) partes.push(nSinDatos + " partida(s) sin datos de tiempo");
        partes.push(fmtHoras(totalOf) + " h oficial + " + fmtHoras(totalAy) + " h ayudante");
        partes.push(fmtDias(diasDur) + " días críticos");
        nota.textContent = partes.join(" · ") + ".";
        var link = nota.querySelector("a");
        // keep existing link handling
        var existingLink = nota.querySelector("a");
        // Remove extra a if duplicated
        // Add link
        if(!nota.querySelector("a.tiempo-link")){
          var link2 = document.createElement("a");
          link2.className="tiempo-link";
          CotizatStyles.set(link2, "marginLeft", "6px");
          nota.appendChild(link2);
          existingLink = link2;
        } else {
          existingLink = nota.querySelector("a.tiempo-link");
        }
        if (window.BUDGET_ID) {
          existingLink.href = "/presupuestos/" + window.BUDGET_ID + "/tiempos";
          existingLink.textContent = "Planificar";
        } else {
          existingLink.href = "#builder-resumen";
          existingLink.textContent = "Se guarda para planificar";
        }
      }
    }

    var badge = document.getElementById("tiempo-badge");
    if (badge) {
      badge.textContent = nPartidas ? `${fmtHoras(totalMO)} h · ${fmtDias(diasDur)} d` : "—";
      badge.title = `Tiempo: ${fmtHoras(totalOf)} h oficial + ${fmtHoras(totalAy)} h ayudante — ${fmtDias(diasDur)} días críticos`;
    }
  }

  editor.calcularTiempos = calcularTiempos;
})();
