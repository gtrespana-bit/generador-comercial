/* ============================================================================
   Editor — módulo de Capítulo
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  var Partida = editor.Partida;

  var Capitulo = (function () {

    function crearCapitulo(datos, editorInst) {
      datos = datos || {};
      var cap = Partida.crearElemento("div", "capitulo");

      var head = Partida.crearElemento("div", "capitulo-head");
      var chevron = Partida.crearElemento("span", "cap-chevron", "⌄");
      head.appendChild(chevron);

      var nombreInput = Partida.crearInput("text", datos.nombre || "", "NOMBRE DEL CAPÍTULO", "cap_nombre");
      nombreInput.className = "capitulo-name";
      head.appendChild(nombreInput);

      var subtotal = Partida.crearElemento("span", "capitulo-subtotal", "");
      head.appendChild(subtotal);

      var actions = Partida.crearElemento("div", "cap-actions");
      var btnAddP = Partida.crearElemento("button", "btn btn-sm", "+ Partida");
      btnAddP.type = "button";
      btnAddP.title = "Añadir partida (Alt+P)";
      btnAddP.addEventListener("click", function (e) {
        e.stopPropagation();
        editorInst.nuevaPartidaEnCapitulo(cap);
      });
      actions.appendChild(btnAddP);

      var btnDupCap = Partida.crearElemento("button", "btn btn-sm", "⧉");
      btnDupCap.type = "button";
      btnDupCap.title = "Duplicar capítulo";
      btnDupCap.addEventListener("click", function (e) {
        e.stopPropagation();
        editorInst.duplicarCapitulo(cap);
      });
      actions.appendChild(btnDupCap);

      var btnSavePack = Partida.crearElemento("button", "btn btn-sm", "💾 Guardar pack");
      btnSavePack.type = "button";
      btnSavePack.title = "Guardar este capítulo como un nuevo Pack de Estancia en tu librería";
      btnSavePack.addEventListener("click", function (e) {
        e.stopPropagation();
        if (window.EDITOR && window.EDITOR.guardarCapituloComoReceta) {
          window.EDITOR.guardarCapituloComoReceta(cap);
        }
      });
      actions.appendChild(btnSavePack);

      var btnDelCap = Partida.crearElemento("button", "btn btn-sm btn-danger", "✕");
      btnDelCap.type = "button";
      btnDelCap.title = "Eliminar capítulo";
      btnDelCap.addEventListener("click", function (e) {
        e.stopPropagation();
        var partCount = cap.querySelectorAll(".partida-row").length;
        if (partCount && !confirm("El capítulo tiene partidas. ¿Eliminar todo el capítulo?")) return;
        editorInst.pushUndo();
        cap.remove();
        editorInst.renumerar();
        editorInst.recalcular();
        editorInst.marcarCambio();
      });
      actions.appendChild(btnDelCap);
      head.appendChild(actions);

      head.addEventListener("click", function (e) {
        if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") return;
        if (cap.classList.contains("collapsed")) {
          cap.classList.remove("collapsed");
          chevron.style.transform = "rotate(0deg)";
        } else {
          cap.classList.add("collapsed");
          chevron.style.transform = "rotate(-90deg)";
        }
      });
      cap.appendChild(head);

      var body = Partida.crearElemento("div", "capitulo-body");
      var pHead = Partida.crearElemento("div", "partidas-head");
      pHead.appendChild(Partida.crearElemento("span", "", ""));
      pHead.appendChild(Partida.crearElemento("span", "", "Partida"));
      pHead.appendChild(Partida.crearElemento("span", "", "Cant."));
      pHead.appendChild(Partida.crearElemento("span", "", "Und."));
      pHead.appendChild(Partida.crearElemento("span", "", "Precio"));
      pHead.appendChild(Partida.crearElemento("span", "", "Importe"));
      pHead.appendChild(Partida.crearElemento("span", "", "Benef."));
      pHead.appendChild(Partida.crearElemento("span", "", ""));
      body.appendChild(pHead);

      var partidasBody = Partida.crearElemento("div", "partidas-body");
      body.appendChild(partidasBody);
      cap._partidasBody = partidasBody;

      var addRow = Partida.crearElemento("div", "add-partida-row");
      var btnAddPartida = Partida.crearElemento("button", "btn-add-partida", "+ Añadir nueva partida");
      btnAddPartida.type = "button";
      btnAddPartida.addEventListener("click", function () {
        editorInst.nuevaPartidaEnCapitulo(cap);
      });
      addRow.appendChild(btnAddPartida);
      body.appendChild(addRow);

      cap.appendChild(body);
      editorInst.contCapitulos.appendChild(cap);

      // Drag & drop capítulo
      cap.draggable = true;
      // El handle es la cabecera para evitar conflictos con inputs
      var capituloHandle = head;
      capituloHandle.style.cursor = "grab";
      cap.addEventListener("dragstart", function (e) {
        // Solo permitir arrastre desde la cabecera o si el target es el propio capítulo
        if (e.target.closest(".partida-wrap, input, select, textarea, button, a") && !e.target.closest(".capitulo-head")) {
          // Si arrastra una partida interna, no iniciar drag de capítulo
          if (e.target.closest(".partida-wrap")) return;
          // Si es un control dentro de la cabecera (input nombre, botones), ignorar
          if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") {
            e.preventDefault();
            return;
          }
        }
        // Solo permitir si el drag viene de la cabecera o del capítulo mismo
        var fromHead = e.target.closest(".capitulo-head") || e.target === cap;
        var isPartida = !!e.target.closest(".partida-wrap");
        if (isPartida) return;
        if (!fromHead && e.target !== cap) {
          // Fallback: comprobar que no sea un drag interno de partida
          var partWrap = editorInst.contCapitulos.querySelector(".partida-wrap.dragging");
          if (partWrap) return;
        }
        try { e.dataTransfer.setData("text/plain", cap.querySelector('[data-f=\"cap_nombre\"]') ? cap.querySelector('[data-f=\"cap_nombre\"]').value : "capitulo"); } catch (err) { try { e.dataTransfer.setData("text/plain", ""); } catch (e2) {} }
        try { e.dataTransfer.effectAllowed = "move"; } catch (err2) {}
        cap.classList.add("dragging");
        if (editorInst.pushUndo) editorInst.pushUndo();
      });
      cap.addEventListener("dragend", function () {
        cap.classList.remove("dragging");
        editorInst.contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
          c.classList.remove("drag-over");
        });
        if (editorInst.marcarCambio) editorInst.marcarCambio();
      });
      cap.addEventListener("dragover", function (e) { 
        // Solo prevenir si hay un capítulo siendo arrastrado
        if (editorInst.contCapitulos.querySelector(".capitulo.dragging")) e.preventDefault(); 
      });

      (datos.partidas || []).forEach(function (p) {
        Partida.crearPartida(cap, p, editorInst);
      });

      editorInst.renumerar();
      editorInst.recalcular();
      return cap;
    }

    function getDragAfterElementCap(y, contCapitulos) {
      var cont = contCapitulos || editor.contCapitulos || document.getElementById("capitulos");
      if (!cont) return null;
      var els = [].slice.call(cont.querySelectorAll(".capitulo:not(.dragging)"));
      var closest = { offset: -Infinity, element: null };
      els.forEach(function (child) {
        var box = child.getBoundingClientRect();
        var offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) closest = { offset: offset, element: child };
      });
      return closest.element;
    }

    function setupDragDropCapitulos(contCapitulos, editorInst) {
      contCapitulos.addEventListener("dragover", function (e) {
        e.preventDefault();
        var dragging = contCapitulos.querySelector(".capitulo.dragging");
        if (!dragging) return;
        var after = getDragAfterElementCap(e.clientY, contCapitulos);
        contCapitulos.querySelectorAll(".capitulo").forEach(function (c) {
          c.classList.remove("drag-over");
        });
        if (after) after.classList.add("drag-over");
      });

      contCapitulos.addEventListener("drop", function (e) {
        e.preventDefault();
        var dragging = contCapitulos.querySelector(".capitulo.dragging");
        if (!dragging) return;
        var after = getDragAfterElementCap(e.clientY, contCapitulos);
        if (after == null) contCapitulos.appendChild(dragging);
        else contCapitulos.insertBefore(dragging, after);
        editorInst.renumerar();
        editorInst.recalcular();
        editorInst.marcarCambio();
      });
    }

    return {
      crear: crearCapitulo,
      setupDragDrop: setupDragDropCapitulos,
      getDragAfterElementCap: getDragAfterElementCap,
    };

  })();

  editor.Capitulo = Capitulo;
})();
