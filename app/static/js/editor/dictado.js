/* ============================================================================
   Editor — Dictado por voz (real, usando la Web Speech API del navegador)

   Reemplaza al antiguo botón "Dictado Asistido" que no tenía ningún código
   detrás. Esto es una funcionalidad de verdad: usa el reconocimiento de voz
   nativo del navegador (sin servidor, sin internet, sin costo) para escribir
   texto en el campo que tengas activo (nombre de partida, descripción,
   notas, etc.).

   Sólo funciona en navegadores que implementan SpeechRecognition
   (Chrome, Edge, la mayoría de Chromium). Si el navegador no lo soporta,
   se avisa claramente en vez de fingir que funciona.
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR || {};

  var SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;

  var reconocimiento = null;
  var escuchando = false;
  var campoActivo = null;

  function esCampoDeTexto(el) {
    if (!el) return false;
    var tag = el.tagName;
    if (tag === "TEXTAREA") return true;
    if (tag === "INPUT") {
      var tipo = (el.getAttribute("type") || "text").toLowerCase();
      return ["text", "search", "url", "tel"].indexOf(tipo) !== -1;
    }
    return false;
  }

  function rastrearFoco() {
    document.addEventListener(
      "focusin",
      function (e) {
        if (esCampoDeTexto(e.target)) campoActivo = e.target;
      },
      true
    );
  }

  function insertarTexto(el, texto) {
    if (!el || !texto) return;
    var inicio = el.selectionStart;
    var fin = el.selectionEnd;
    var actual = el.value || "";
    var necesitaEspacio = inicio > 0 && actual.charAt(inicio - 1) !== " " && actual.charAt(inicio - 1) !== "";
    var fragmento = (necesitaEspacio ? " " : "") + texto;

    if (typeof inicio === "number" && typeof fin === "number") {
      el.value = actual.slice(0, inicio) + fragmento + actual.slice(fin);
      var cursor = inicio + fragmento.length;
      el.setSelectionRange(cursor, cursor);
    } else {
      el.value = actual + fragmento;
    }
    // Disparar 'input' para que autosave/recalculo/undo se enteren del cambio.
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.focus();
  }

  function actualizarBoton(btn, estado) {
    if (estado === "escuchando") {
      btn.textContent = "🔴 Escuchando… (clic para detener)";
      btn.classList.add("btn-dictando");
    } else {
      btn.textContent = "🎙️ Dictado por voz";
      btn.classList.remove("btn-dictando");
    }
  }

  function initDictado() {
    var btn = document.getElementById("btn-ai-dictation");
    if (!btn) return;

    if (!SpeechRecognitionCtor) {
      btn.addEventListener("click", function () {
        alert(
          "Tu navegador no soporta dictado por voz (Web Speech API).\n" +
            "Funciona en Chrome, Edge y navegadores basados en Chromium.\n" +
            "Si estás en la app de escritorio, usa la ventana con motor Chromium disponible."
        );
      });
      btn.title = "Dictado por voz no disponible en este navegador";
      return;
    }

    rastrearFoco();

    reconocimiento = new SpeechRecognitionCtor();
    reconocimiento.lang = "es-VE";
    reconocimiento.continuous = true;
    reconocimiento.interimResults = false;

    reconocimiento.addEventListener("result", function (e) {
      var destino = campoActivo && esCampoDeTexto(campoActivo)
        ? campoActivo
        : document.querySelector('textarea[name="notas"]');
      var texto = "";
      for (var i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) texto += e.results[i][0].transcript;
      }
      texto = texto.trim();
      if (texto && destino) insertarTexto(destino, texto);
    });

    reconocimiento.addEventListener("end", function () {
      escuchando = false;
      actualizarBoton(btn, "detenido");
    });

    reconocimiento.addEventListener("error", function (e) {
      escuchando = false;
      actualizarBoton(btn, "detenido");
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        alert("No se pudo acceder al micrófono. Revisa los permisos del navegador.");
      } else if (e.error === "no-speech") {
        // Silencio: no hace falta interrumpir con una alerta.
      } else {
        alert("Error de dictado por voz: " + e.error);
      }
    });

    btn.addEventListener("click", function () {
      if (!escuchando) {
        if (!campoActivo) {
          alert("Haz clic dentro del campo donde quieres escribir (nombre, descripción o notas) y luego pulsa Dictado de nuevo.");
          return;
        }
        try {
          reconocimiento.start();
          escuchando = true;
          actualizarBoton(btn, "escuchando");
        } catch (err) {
          // start() lanza si ya estaba iniciado; lo ignoramos.
        }
      } else {
        reconocimiento.stop();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDictado);
  } else {
    initDictado();
  }

  editor.initDictado = initDictado;
  window.EDITOR = editor;
})();
