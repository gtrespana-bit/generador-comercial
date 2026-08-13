/* ============================================================================
   Editor — Atajos de teclado globales
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;

  function initAtajos() {
    document.addEventListener("keydown", function (e) {
      var tag = e.target.tagName;
      var inInput = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
      var mod = e.ctrlKey || e.metaKey;

      // Ctrl/Cmd+K → buscador catálogo
      if (mod && e.key.toLowerCase() === "k") {
        e.preventDefault();
        var b = document.getElementById("buscar-partida");
        if (b) {
          b.focus();
          b.select();
        }
        return;
      }

      // Ctrl/Cmd+M → cambiar moneda
      if (mod && e.key.toLowerCase() === "m") {
        e.preventDefault();
        var mon = document.getElementById("moneda-select");
        if (mon) {
          mon.value = mon.value === "USD" ? "Bs" : "USD";
          editor.renumerar();
          editor.recalcular();
          editor.marcarCambio();
        }
        return;
      }

      // / → buscador (fuera de inputs)
      if (e.key === "/" && !inInput && !mod && !e.altKey && !e.shiftKey) {
        e.preventDefault();
        var b2 = document.getElementById("buscar-partida");
        if (b2) b2.focus();
        return;
      }

      // ? → ayuda de atajos
      if ((e.key === "?" || (e.shiftKey && e.key === "/")) && !inInput && !mod && !e.altKey) {
        e.preventDefault();
        var modalAyuda = document.getElementById("modal-atajos");
        if (modalAyuda) {
          modalAyuda.classList.add("open");
          document.body.classList.add("modal-open");
        }
        return;
      }

      // Ctrl/Cmd+Enter → guardar
      if (mod && e.key === "Enter") {
        e.preventDefault();
        var form = document.getElementById("form-presupuesto");
        if (form) form.requestSubmit();
        return;
      }

      // Ctrl/Cmd+Z → deshacer (fuera de inputs)
      if (mod && e.key.toLowerCase() === "z" && !inInput) {
        e.preventDefault();
        if (editor.deshacer()) {
          var z = document.getElementById("undo-flash");
          if (z) {
            z.textContent = "↩ Deshecho";
            z.classList.add("show");
            setTimeout(function () {
              z.classList.remove("show");
            }, 1200);
          }
        }
        return;
      }

      // Alt+C → capítulo
      if (e.altKey && !e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "c") {
        e.preventDefault();
        var btnCap = document.getElementById("btn-agregar-capitulo");
        if (btnCap) btnCap.click();
        return;
      }

      // Alt+P → partida
      if (e.altKey && !e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "p") {
        e.preventDefault();
        var caps = editor.contCapitulos.querySelectorAll(".capitulo");
        var cap = caps.length ? caps[caps.length - 1] : editor.Capitulo.crear(null, editor);
        editor.nuevaPartidaEnCapitulo(cap);
        return;
      }

      // Alt+R → abrir modal Pack de Estancia
      if (e.altKey && !e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "r") {
        e.preventDefault();
        var btnRec = document.getElementById("btn-modal-receta") || document.getElementById("btn-modal-receta-seccion");
        if (btnRec) {
          btnRec.click();
        } else if (window.EDITOR && window.EDITOR.abrirModalRecetaEstancia) {
          window.EDITOR.abrirModalRecetaEstancia();
        }
        return;
      }

      // Escape → contraer partidas expandidas
      if (e.key === "Escape" && !inInput) {
        var wraps = editor.contCapitulos.querySelectorAll(".partida-wrap.expanded");
        if (wraps.length) {
          var w = wraps[wraps.length - 1];
          w.classList.remove("expanded");
          w.querySelector(".partida-row").classList.remove("expanded");
          w.querySelector(".partida-details").classList.remove("open");
        }
        // Cerrar modales
        var modales = document.querySelectorAll(".modal-overlay.open");
        modales.forEach(function (m) {
          m.classList.remove("open");
          document.body.classList.remove("modal-open");
        });
        return;
      }

      // Ctrl/Cmd+S → guardar (prevent default del browser)
      if (mod && e.key.toLowerCase() === "s") {
        e.preventDefault();
        var form = document.getElementById("form-presupuesto");
        if (form) form.requestSubmit();
        return;
      }
    });
  }

  // Exportar (compatibilidad ambas formas)
  editor.initAtajos = initAtajos;
  editor.atajos = { initAtajos: initAtajos, init: initAtajos };
})();
