/* ============================================================================
   Servicio — Autosave (localStorage + servidor)

   Estrategia de guardado (diseñada para que NADA se pierda):
     1) Cada vez que se marca un cambio → escritura SÍNCRONA en localStorage
        (instantánea, no puede fallar). El indicador pasa a "Guardando…".
     2) En paralelo se programa un envío al servidor con debounce
        (SERVER_DEBOUNCE_MS) para que, aunque el usuario esté tecleando sin
        parar, solo se haga UNA petición cuando se detenga.
     3) Si la página se cierra o se navega fuera con cambios sin guardar, el
        navegador pregunta antes de salir (beforeunload) Y, además, se fuerza
        un último envío al servidor con `navigator.sendBeacon` para que el
        borrador del servidor quede al día.
     4) Cada cierto tiempo (AUTOSAVE_TICK_MS), si el último guardado fue
        hace mucho, se reenvía el estado aunque no haya cambios nuevos
        (mantiene un "keepalive" del borrador en el servidor).
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  var autosave = (function () {

    // ---- Tiempos (ms) ----
    var AUTOSAVE_TICK_MS = 15000;       // cada 15 s: revalidación / keepalive
    var SERVER_DEBOUNCE_MS = 1200;      // tras el último cambio, espera 1.2 s
                                       // para enviar al servidor (agrupa ráfagas)
    var SERVER_KEEPALIVE_MS = 30000;    // reenvía aunque no haya cambios nuevos
                                       // cada 30 s (recuperación cross-device)
    var LAST_CHANGE_THRESHOLD = 600;    // tiempo mínimo desde el último cambio
                                       // para considerar que el usuario «paró»

    var state = {
      timer: null,
      lastChangeTime: 0,
      lastSavedAt: 0,
      lastServerSaveAt: 0,
      serverSaveTimer: null,
      pendingChanges: false,
      saveInProgress: false,
      hasUnsavedChanges: false,
      // Se ejecuta antes de descargar/cerrar la página: envía el borrador
      // pendiente al servidor con sendBeacon para no perder nada.
      unloadHandler: null,
    };

    // -------------------------------------------------------------------------
    // localStorage (rápido, offline, síncrono)
    // -------------------------------------------------------------------------

    function getAutosaveKey() {
      return "presup_draft_" + (editor.BUDGET_ID || "new");
    }

    function snapshotActual() {
      // Captura el estado serializado. Se hace aquí (y no dentro del setInterval)
      // para que SIEMPRE se guarde lo más reciente posible, incluso si el
      // editor muta mientras se serializa.
      try {
        return {
          capitulos: editor.serializar(),
          ts: Date.now(),
        };
      } catch (e) {
        return null;
      }
    }

    function guardarBorradorLocal(silencioso) {
      try {
        var data = snapshotActual();
        if (!data) return false;
        localStorage.setItem(getAutosaveKey(), JSON.stringify(data));
        state.lastSavedAt = Date.now();
        if (!silencioso) editor.actualizarEstadoAutosave("local", true);
        return true;
      } catch (e) {
        // localStorage lleno u otro error
        if (!silencioso) editor.actualizarEstadoAutosave("local", false);
        return false;
      }
    }

    function leerBorradorLocal() {
      try {
        var raw = localStorage.getItem(getAutosaveKey());
        if (!raw) return null;
        var data = JSON.parse(raw);
        if (data && data.capitulos && Array.isArray(data.capitulos)) {
          return data;
        }
        return null;
      } catch (e) {
        return null;
      }
    }

    function limpiarBorradorLocal() {
      try { localStorage.removeItem(getAutosaveKey()); } catch (e) {}
      editor.actualizarEstadoAutosave("local", false);
    }

    function hayBorradorLocal() {
      try { return !!localStorage.getItem(getAutosaveKey()); } catch (e) { return false; }
    }

    // -------------------------------------------------------------------------
    // Servidor (persistente, cross-device)
    // -------------------------------------------------------------------------

    function enviarServidor(usarBeacon) {
      if (state.saveInProgress) return false;
      var budgetId = Number(editor.BUDGET_ID);
      if (!Number.isInteger(budgetId) || budgetId <= 0) {
        // Nuevo presupuesto: no hay ID todavía, solo localStorage
        guardarBorradorLocal();
        return false;
      }

      var data = snapshotActual();
      if (!data) return false;

      var payload = JSON.stringify({ capitulos: data.capitulos, ts: data.ts });
      var url = "/presupuestos/" + budgetId + "/borrador";

      // Camino rápido antes de cerrar la pestaña: sendBeacon es «fire and
      // forget» y el servidor lo procesa aunque el cliente desaparezca.
      if (usarBeacon && navigator.sendBeacon) {
        try {
          var blob = new Blob([payload], { type: "application/json" });
          navigator.sendBeacon(url, blob);
          state.lastSavedAt = Date.now();
          state.lastServerSaveAt = Date.now();
          state.pendingChanges = false;
          state.hasUnsavedChanges = false;
          editor.actualizarEstadoAutosave("server", true);
          return true;
        } catch (e) {
          // Si sendBeacon falla, caemos al fetch normal
        }
      }

      state.saveInProgress = true;
      editor.actualizarEstadoAutosave("server", true);

      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: payload,
        credentials: "same-origin",
        keepalive: !!usarBeacon,
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          state.lastSavedAt = Date.now();
          state.lastServerSaveAt = Date.now();
          state.saveInProgress = false;
          editor.actualizarEstadoAutosave("server", data && data.ok);
          if (data && data.ok) {
            state.pendingChanges = false;
            state.hasUnsavedChanges = false;
          }
        })
        .catch(function () {
          state.saveInProgress = false;
          editor.actualizarEstadoAutosave("server", false);
        });
      return true;
    }

    function guardarBorradorServidor() {
      return enviarServidor(false);
    }

    function programarGuardadoServidor() {
      if (!editor.BUDGET_ID) {
        // Nuevo: solo localStorage
        guardarBorradorLocal();
        return;
      }
      if (state.serverSaveTimer) {
        clearTimeout(state.serverSaveTimer);
      }
      state.serverSaveTimer = setTimeout(function () {
        state.serverSaveTimer = null;
        // Solo envía si NO se está guardando en este momento. Si el usuario
        // está en plena ráfaga de cambios, el próximo marcarCambio() lo
        // reprograma.
        if (Date.now() - state.lastChangeTime >= LAST_CHANGE_THRESHOLD) {
          enviarServidor(false);
        }
      }, SERVER_DEBOUNCE_MS);
    }

    // -------------------------------------------------------------------------
    // Timer principal (keepalive y revalidación)
    // -------------------------------------------------------------------------

    function iniciarAutosave() {
      detenerAutosave();
      // Disparador principal: cada AUTOSAVE_TICK_MS revisamos si toca
      // reenviar al servidor. Si el usuario está activo (cambios recientes)
      // y aún no se programó un envío, lo programamos con el debounce.
      state.timer = setInterval(function () {
        var now = Date.now();
        var timeSinceLastChange = now - state.lastChangeTime;

        // (1) El usuario acaba de hacer algo: si hay cambios pendientes y
        //     ya pasó el umbral de inactividad, envía ahora mismo.
        if (state.pendingChanges && timeSinceLastChange >= LAST_CHANGE_THRESHOLD) {
          if (Date.now() - state.lastServerSaveAt >= SERVER_DEBOUNCE_MS) {
            enviarServidor(false);
          }
        }

        // (2) Keepalive: aunque no haya cambios nuevos, reenvía cada
        //     SERVER_KEEPALIVE_MS para que el borrador del servidor
        //     no quede "anticuado" y se pueda recuperar desde otro
        //     dispositivo. No machaca un envío aún en curso.
        if (!state.pendingChanges &&
            state.lastServerSaveAt > 0 &&
            (now - state.lastServerSaveAt) >= SERVER_KEEPALIVE_MS) {
          enviarServidor(false);
        }
      }, AUTOSAVE_TICK_MS);
    }

    function detenerAutosave() {
      if (state.timer) {
        clearInterval(state.timer);
        state.timer = null;
      }
      if (state.serverSaveTimer) {
        clearTimeout(state.serverSaveTimer);
        state.serverSaveTimer = null;
      }
    }

    // -------------------------------------------------------------------------
    // Integración con editor
    // -------------------------------------------------------------------------

    function marcarCambio() {
      var now = Date.now();
      var primerCambio = !state.pendingChanges;
      state.lastChangeTime = now;
      state.pendingChanges = true;
      state.hasUnsavedChanges = true;

      // 1) SIEMPRE escritura local inmediata. Es síncrona, instantánea y
      //    permite recuperar el trabajo aunque se vaya la luz o se cierre
      //    el navegador a los 3 segundos.
      guardarBorradorLocal(true);

      // 2) Programa el envío al servidor con debounce. Cada nuevo cambio
      //    reinicia el contador, así NO se envía nada mientras el usuario
      //    está tecleando: solo se envía cuando se detiene.
      programarGuardadoServidor();

      // 3) Refresca el indicador de UI.
      if (primerCambio) {
        editor.actualizarEstadoAutosave("any", true);
      }
    }

    function serializarParaGuardado() {
      return JSON.stringify(snapshotActual() || {});
    }

    function restaurarBorrador() {
      var borrador = leerBorradorLocal();
      if (!borrador) return false;

      // Verificar que no sea el estado actual
      var actual = JSON.stringify(editor.serializar());
      var borradorStr = JSON.stringify(borrador.capitulos);
      if (actual === borradorStr) {
        limpiarBorradorLocal();
        return false;
      }

      editor.construirDesde(borrador.capitulos);
      editor.marcarCambio();
      return true;
    }

    function limpiar() {
      detenerAutosave();
      limpiarBorradorLocal();
      state.pendingChanges = false;
      state.hasUnsavedChanges = false;
      state.lastServerSaveAt = 0;
      editor.actualizarEstadoAutosave("any", false);
    }

    // -------------------------------------------------------------------------
    // Cierre de pestaña: envía el último estado al servidor
    // -------------------------------------------------------------------------

  function instalarProteccionCierre() {
    if (state.unloadHandler) {
      window.removeEventListener("beforeunload", state.unloadHandler);
    }
    state.unloadHandler = function (evento) {
      // Antes de que la página se descargue, enviamos un último sendBeacon
      // para que el borrador del servidor quede actualizado. Esto cubre
      // los casos en los que el usuario cierra la pestaña sin guardar.
      if (state.pendingChanges || state.hasUnsavedChanges) {
        try { enviarServidor(true); } catch (e) {}
        // Aviso estándar del navegador para que el usuario pueda cancelar
        // el cierre si todavía no ha guardado del todo.
        evento.preventDefault();
        evento.returnValue = "Tienes cambios sin guardar. ¿Salir de todos modos?";
        return evento.returnValue;
      }
    };
    window.addEventListener("beforeunload", state.unloadHandler);

    // pagehide se dispara en móviles y en algunos navegadores al cambiar
    // de pestaña; también disparamos el último envío.
    window.addEventListener("pagehide", function () {
      if (state.pendingChanges || state.hasUnsavedChanges) {
        try { enviarServidor(true); } catch (e) {}
      }
    });
  }

  /**
   * Suspende temporalmente la protección beforeunload (p. ej. cuando el
   * usuario pulsa "Guardar presupuesto", no queremos un confirm del
   * navegador interfiriendo con el submit del formulario).
   */
  function suspenderProteccionCierre() {
    if (state.unloadHandler) {
      window.removeEventListener("beforeunload", state.unloadHandler);
      state.unloadHandler = null;
    }
    // Forzamos un envío final y limpiamos el estado para que la página
    // pueda descargarse sin pedir confirmación.
    if (state.pendingChanges || state.hasUnsavedChanges) {
      try { enviarServidor(true); } catch (e) {}
    }
    state.pendingChanges = false;
    state.hasUnsavedChanges = false;
  }

    // -------------------------------------------------------------------------
    // UI del estado de autosave
    // -------------------------------------------------------------------------

    function actualizarEstadoAutosave(tipo, ok) {
      var status = document.getElementById("autosave-status");
      if (!status) return;

      // Conservar la(s) clase(s) original(es) y solo añadir/quitar las
      // nuestras para no romper el estilo.
      var clasesBase = "autosave-status";
      var dirty = status.classList.contains("dirty");
      var nuevaClase = clasesBase + (dirty ? " dirty" : "");
      // Conservar "dirty" si hay cambios pendientes
      if (tipo === "any") {
        nuevaClase = clasesBase + (state.pendingChanges ? " dirty" : "");
      }

      var timeStr = state.lastSavedAt ? "hace " + Math.max(0, Math.round((Date.now() - state.lastSavedAt) / 1000)) + "s" : "";

      var texto = "";
      var dataState = "idle";
      if (tipo === "server" && ok) {
        texto = "✓ Guardado en servidor" + (timeStr ? " · " + timeStr : "");
        dataState = "saved";
      } else if (tipo === "server" && !ok && editor.BUDGET_ID) {
        texto = "⚠ Guardado solo en este equipo" + (timeStr ? " · " + timeStr : "");
        dataState = "error";
      } else if (tipo === "local") {
        texto = "↻ Borrador local";
        dataState = "saved";
      } else if (state.pendingChanges) {
        texto = "Guardando…";
        dataState = "saving";
      } else if (timeStr) {
        texto = "✓ Guardado · " + timeStr;
        dataState = "saved";
      } else {
        texto = "";
        dataState = "idle";
      }
      status.textContent = texto;
      status.className = nuevaClase;
      status.setAttribute("data-state", dataState);
      status.title = texto || "Autoguardado: cada cambio se guarda al instante en este equipo y se envía al servidor cuando dejas de editar.";
    }

    // -------------------------------------------------------------------------
    // API pública
    // -------------------------------------------------------------------------

    return {
      iniciar: iniciarAutosave,
      detener: detenerAutosave,
      marcarCambio: marcarCambio,
      serializar: serializarParaGuardado,
      guardarBorradorLocal: function () { return guardarBorradorLocal(false); },
      guardarBorradorLocalSilencioso: function () { return guardarBorradorLocal(true); },
      leerBorradorLocal: leerBorradorLocal,
      limpiarBorradorLocal: limpiarBorradorLocal,
      hayBorradorLocal: hayBorradorLocal,
      guardarBorradorServidor: guardarBorradorServidor,
      restaurarBorrador: restaurarBorrador,
      limpiar: limpiar,
      instalarProteccionCierre: instalarProteccionCierre,
      suspenderProteccionCierre: suspenderProteccionCierre,
      actualizarEstado: actualizarEstadoAutosave,
      estado: function () { return Object.assign({}, state); },
    };

  })();

  // Conectamos al editor y dejamos instaladas las protecciones de cierre lo
  // antes posible (incluso antes del init de main.js) para no perder los
  // primeros cambios en una sesión nueva.
  editor.autosave = autosave;
  if (typeof editor.BUDGET_ID === "number" || editor.BUDGET_ID === null) {
    try { autosave.instalarProteccionCierre(); } catch (e) {}
  }
})();
