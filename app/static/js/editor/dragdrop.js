/* ============================================================================
   Editor — Drag & Drop con línea guía visual

   Mejoras sobre el sistema anterior:
   - Línea azul de inserción entre elementos
   - Transiciones suaves
   - Feedback visual de "drop zone"
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;

  // -------------------------------------------------------------------------
  // Línea guía de inserción
  // -------------------------------------------------------------------------

  function createGuideLine() {
    var line = document.createElement("div");
    line.className = "drag-guide-line";
    CotizatStyles.setCssText(line, "position:absolute; height:2px; background:#0d9488; border-radius:2px; pointer-events:none; z-index:100; box-shadow:0 0 6px rgba(13,148,136,0.5); display:none;");
    return line;
  }

  function showGuideLine(container, element) {
    var line = container._guideLine;
    if (!line) {
      line = createGuideLine();
      container.appendChild(line);
      container._guideLine = line;
    }

    if (!element) {
      CotizatStyles.set(line, "display", "none");
      return;
    }

    var containerRect = container.getBoundingClientRect();
    var elementRect = element.getBoundingClientRect();

    // Posicionar la línea en el centro del elemento (línea horizontal)
    var top = elementRect.top - containerRect.top + elementRect.height / 2 - 1;
    CotizatStyles.set(line, "top", top + "px");
    CotizatStyles.set(line, "left", "0");
    CotizatStyles.set(line, "width", "100%");
    CotizatStyles.set(line, "display", "block");
  }

  function hideGuideLine(container) {
    if (container._guideLine) {
      CotizatStyles.set(container._guideLine, "display", "none");
    }
  }

  // -------------------------------------------------------------------------
  // Drag de partidas
  // -------------------------------------------------------------------------

  function initPartidaDragDrop() {
    var contCapitulos = editor.contCapitulos || document.getElementById("capitulos");
    if (!contCapitulos) return;

    // Asegurar posicionamiento relativo para la línea guía
    if (getComputedStyle(contCapitulos).position === "static") {
      CotizatStyles.set(contCapitulos, "position", "relative");
    }

    contCapitulos.addEventListener("dragstart", function (e) {
      // Ignorar si el arrastre viene de un control interactivo (input, botón…)
      // salvo que sea el asa de arrastre
      if (e.target.closest("input, select, textarea, button, a")) {
        // Permitir solo si el asa está siendo arrastrada directamente
        if (!e.target.closest(".partida-drag") && e.target.closest(".partida-wrap")) {
          // Si el drag se origina en un input dentro de la partida, no es un drag de partida
          // Comprobamos que el draggable real sea la partida; si el target es input, cancelar
          var isHandle = e.target.classList.contains("partida-drag") || e.target.closest(".partida-drag");
          if (!isHandle) return;
        }
      }
      var partidaWrap = e.target.closest(".partida-wrap");
      if (!partidaWrap) return;
      // Doble seguridad: si hay un capítulo siendo arrastrado, no iniciar partida
      if (contCapitulos.querySelector(".capitulo.dragging")) return;

      e.stopPropagation();
      try { e.dataTransfer.setData("text/plain", partidaWrap.querySelector('[data-f="p_nombre"]') ? partidaWrap.querySelector('[data-f="p_nombre"]').value : "partida"); } catch (err) { try { e.dataTransfer.setData("text/plain", ""); } catch (e2) {} }
      try { e.dataTransfer.effectAllowed = "move"; } catch (err2) {}
      partidaWrap.classList.add("dragging");

      // Crear línea guía si no existe
      if (!contCapitulos._guideLine) {
        contCapitulos._guideLine = createGuideLine();
        contCapitulos.appendChild(contCapitulos._guideLine);
      }

      // PUSH del estado actual para deshacer
      if (editor.pushUndo) editor.pushUndo();
    });

    contCapitulos.addEventListener("dragend", function () {
      contCapitulos.querySelectorAll(".partida-wrap").forEach(function (w) {
        w.classList.remove("dragging", "drag-over");
      });
      hideGuideLine(contCapitulos);
      if (editor.marcarCambio) editor.marcarCambio();
    });

    contCapitulos.addEventListener("dragover", function (e) {
      var dragging = contCapitulos.querySelector(".partida-wrap.dragging");
      if (!dragging) return;
      e.preventDefault();
      try { e.dataTransfer.dropEffect = "move"; } catch (err) {}

      var targetCapitulo = e.target.closest(".capitulo");
      if (!targetCapitulo) {
        hideGuideLine(contCapitulos);
        return;
      }

      var partidasBody = targetCapitulo.querySelector(".partidas-body");
      if (!partidasBody) return;

      // Encontrar elemento después del cursor dentro de este capítulo
      var after = getDragAfterElement(partidasBody, e.clientY);
      
      contCapitulos.querySelectorAll(".partida-wrap").forEach(function (w) {
        w.classList.remove("drag-over");
      });
      contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
        c.classList.remove("drag-over");
      });

      if (after) {
        after.classList.add("drag-over");
        showGuideLine(contCapitulos, after);
      } else {
        hideGuideLine(contCapitulos);
        // Si no hay after pero hay partidas, marcar la última; si no, marcar capítulo
        var existentes = partidasBody.querySelectorAll(".partida-wrap:not(.dragging)");
        if (existentes.length === 0) {
          targetCapitulo.classList.add("drag-over");
        } else {
          existentes[existentes.length - 1].classList.add("drag-over");
        }
      }
    });

    contCapitulos.addEventListener("drop", function (e) {
      var dragging = contCapitulos.querySelector(".partida-wrap.dragging");
      if (!dragging) return;
      e.preventDefault();
      e.stopPropagation();

      var targetCapitulo = e.target.closest(".capitulo");
      // Fallback: si no hay capítulo bajo el cursor, usar el más cercano o el último
      if (!targetCapitulo) {
        // Buscar capítulo más cercano al cursor
        var caps = [].slice.call(contCapitulos.querySelectorAll(".capitulo:not(.dragging)"));
        if (!caps.length) return;
        // Si suelta fuera de capítulos, mover al último capítulo
        targetCapitulo = caps[caps.length - 1];
      }
      
      var partidasBody = targetCapitulo.querySelector(".partidas-body");
      if (!partidasBody) return;

      var after = getDragAfterElement(partidasBody, e.clientY);
      if (after == null) {
        partidasBody.appendChild(dragging);
      } else {
        partidasBody.insertBefore(dragging, after);
      }

      // Limpiar drag-over
      contCapitulos.querySelectorAll(".partida-wrap").forEach(function (w) {
        w.classList.remove("drag-over");
      });
      contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
        c.classList.remove("drag-over");
      });
      hideGuideLine(contCapitulos);

      if (editor.renumerar) editor.renumerar();
      if (editor.recalcular) editor.recalcular();
      if (editor.marcarCambio) editor.marcarCambio();
    });
  }

  function getDragAfterElement(container, y) {
    var els = [].slice.call(container.querySelectorAll(".partida-wrap:not(.dragging)"));
    var closest = { offset: -Infinity, element: null };
    els.forEach(function (child) {
      var box = child.getBoundingClientRect();
      var offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) closest = { offset: offset, element: child };
    });
    return closest.element;
  }

  // -------------------------------------------------------------------------
  // Drag de capítulos
  // -------------------------------------------------------------------------

  function initCapituloDragDrop() {
    var contCapitulos = editor.contCapitulos || document.getElementById("capitulos");
    if (!contCapitulos) return;

    contCapitulos.addEventListener("dragover", function (e) {
      var draggingCap = contCapitulos.querySelector(".capitulo.dragging");
      // No interferir con arrastre de partidas
      if (!draggingCap) return;
      // Si se está arrastrando partida, no manejar como capítulo
      if (contCapitulos.querySelector(".partida-wrap.dragging")) return;
      e.preventDefault();
      try { e.dataTransfer.dropEffect = "move"; } catch (err) {}
      var after = null;
      try {
        // Intentar con 2 args primero (capitulo.js original), luego fallback
        after = Capitulo.getDragAfterElementCap(e.clientY, contCapitulos);
        if (after === undefined) after = Capitulo.getDragAfterElementCap(e.clientY);
      } catch (err2) {
        after = getDragAfterElementCapFallback(e.clientY, contCapitulos);
      }
      contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
        c.classList.remove("drag-over");
      });
      if (after) after.classList.add("drag-over");
      // Línea guía para capítulos
      if (after) {
        showGuideLine(contCapitulos, after);
      } else {
        hideGuideLine(contCapitulos);
        if (draggingCap) contCapitulos.classList.add("drag-over");
      }
    });

    contCapitulos.addEventListener("drop", function (e) {
      var draggingCap = contCapitulos.querySelector(".capitulo.dragging");
      if (!draggingCap) return;
      if (contCapitulos.querySelector(".partida-wrap.dragging")) return;
      e.preventDefault();
      e.stopPropagation();
      var after = null;
      try {
        after = Capitulo.getDragAfterElementCap(e.clientY, contCapitulos);
        if (after === undefined) after = Capitulo.getDragAfterElementCap(e.clientY);
      } catch (err2) {
        after = getDragAfterElementCapFallback(e.clientY, contCapitulos);
      }
      if (after == null) contCapitulos.appendChild(draggingCap);
      else contCapitulos.insertBefore(draggingCap, after);

      contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
        c.classList.remove("drag-over");
      });
      contCapitulos.classList.remove("drag-over");
      hideGuideLine(contCapitulos);
      if (editor.renumerar) editor.renumerar();
      if (editor.recalcular) editor.recalcular();
      if (editor.marcarCambio) editor.marcarCambio();
    });
  }

  function getDragAfterElementCapFallback(y, cont) {
    var c = cont || editor.contCapitulos || document.getElementById("capitulos");
    if (!c) return null;
    var els = [].slice.call(c.querySelectorAll(".capitulo:not(.dragging)"));
    var closest = { offset: -Infinity, element: null };
    els.forEach(function (child) {
      var box = child.getBoundingClientRect();
      var offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) closest = { offset: offset, element: child };
    });
    return closest.element;
  }

  // Configurar capítulo drag — envolver para soportar ambas firmas (y) y (y, cont)
  var Capitulo = window.EDITOR.Capitulo;
  if (Capitulo) {
    var originalCapFn = Capitulo.getDragAfterElementCap;
    Capitulo.getDragAfterElementCap = function (y, contParam) {
      var cont = contParam || editor.contCapitulos || document.getElementById("capitulos");
      if (!cont) return null;
      if (originalCapFn) {
        try {
          // Si la original espera 2 args, pasar ambos; si 1 arg, pasará y
          var res = originalCapFn.length >= 2 ? originalCapFn(y, cont) : originalCapFn(y);
          if (res !== undefined) return res;
        } catch (e) {}
      }
      return getDragAfterElementCapFallback(y, cont);
    };
  }

  // -------------------------------------------------------------------------
  // Inicialización
  // -------------------------------------------------------------------------

  function init() {
    // Evitar doble inicialización
    var cont = editor.contCapitulos || document.getElementById("capitulos");
    if (cont && cont._dragDropInit) return;
    if (cont) cont._dragDropInit = true;
    initPartidaDragDrop();
    initCapituloDragDrop();
  }

  editor.initDragDrop = init;
  // Exponer también como objeto para compatibilidad con main.js antiguo
  editor.dragDrop = { init: init };
  // Alias global por si algún script lo busca fuera de EDITOR
  window.initDragDrop = init;
})();
