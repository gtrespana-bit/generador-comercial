/**
 * Asistente Inteligente de CotizaT (Copilot).
 *
 * Proporciona soporte en vivo, resolución de dudas de uso, navegación y
 * redacción técnica asistida por IA (GPT OSS 120B vía Groq).
 *
 * Cumple estrictamente con las políticas de seguridad CSP:
 * - Cero uso de manipulaciones crudas de texto o sinks de inyección.
 * - Construcción segura de nodos mediante DOM nativo (document.createElement, textContent).
 * - Conexión exclusiva Same-Origin (/api/ia/*).
 */
(function () {
  "use strict";

  var chatHistorial = [];
  var estaGenerando = false;

  // -------------------------------------------------------------------------
  // Renderizador seguro de Markdown a DOM nativo
  // -------------------------------------------------------------------------

  function parsearLineaInline(texto, contenedor) {
    // Procesa tokens básicos: `codigo`, **negrita**, *cursiva*, [enlace](url)
    var regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
    var partes = texto.split(regex);

    partes.forEach(function (parte) {
      if (!parte) return;

      if (parte.charAt(0) === "`" && parte.charAt(parte.length - 1) === "`") {
        var code = document.createElement("code");
        code.className = "ia-inline-code";
        code.textContent = parte.slice(1, -1);
        contenedor.appendChild(code);
      } else if (parte.indexOf("**") === 0 && parte.lastIndexOf("**") === parte.length - 2) {
        var strong = document.createElement("strong");
        strong.textContent = parte.slice(2, -2);
        contenedor.appendChild(strong);
      } else if (parte.charAt(0) === "*" && parte.charAt(parte.length - 1) === "*") {
        var em = document.createElement("em");
        em.textContent = parte.slice(1, -1);
        contenedor.appendChild(em);
      } else if (parte.indexOf("[") === 0 && parte.indexOf("](") !== -1 && parte.charAt(parte.length - 1) === ")") {
        var sep = parte.indexOf("](");
        var etiqueta = parte.slice(1, sep);
        var enlace = parte.slice(sep + 2, -1);

        var a = document.createElement("a");
        a.className = "ia-chat-link";
        a.textContent = etiqueta;
        a.href = enlace;
        // Las acciones del asistente son declarativas: el navegador las
        // confirma y ejecuta contra los módulos ya cargados del editor.
        if (enlace.indexOf("/api/ia/accion/") === 0) {
          a.setAttribute("data-ia-action", "true");
          a.addEventListener("click", function (evento) {
            evento.preventDefault();
            ejecutarAccionAsistente(enlace, a);
          });
        }
        // Si es enlace interno, no abre pestaña nueva; si es externo, sí
        if (enlace.charAt(0) === "/") {
          a.setAttribute("data-internal", "true");
        } else {
          a.target = "_blank";
          a.rel = "noopener noreferrer";
        }
        contenedor.appendChild(a);
      } else {
        contenedor.appendChild(document.createTextNode(parte));
      }
    });
  }

  function cerrarModalAsistente(overlay) {
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    document.body.classList.remove("modal-open");
  }

  function crearModalAsistente(titulo) {
    var anterior = document.getElementById("ia-action-modal");
    if (anterior) cerrarModalAsistente(anterior);
    var overlay = document.createElement("div");
    overlay.id = "ia-action-modal";
    overlay.className = "modal-overlay open ia-action-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    var modal = document.createElement("div");
    modal.className = "modal modal-lg ia-action-modal";
    var head = document.createElement("div");
    head.className = "modal-head";
    var h3 = document.createElement("h3");
    h3.textContent = titulo;
    head.appendChild(h3);
    var cerrar = document.createElement("button");
    cerrar.type = "button";
    cerrar.className = "btn btn-ghost";
    cerrar.textContent = "✕";
    cerrar.addEventListener("click", function () { cerrarModalAsistente(overlay); });
    head.appendChild(cerrar);
    modal.appendChild(head);
    var cuerpo = document.createElement("div");
    cuerpo.className = "ia-action-modal-body";
    modal.appendChild(cuerpo);
    overlay.appendChild(modal);
    overlay.addEventListener("click", function (evento) {
      if (evento.target === overlay) cerrarModalAsistente(overlay);
    });
    document.body.appendChild(overlay);
    document.body.classList.add("modal-open");
    return { overlay: overlay, modal: modal, cuerpo: cuerpo };
  }

  function normalizarTextoEditor(texto) {
    return String(texto || "").toLowerCase().normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }

  function partidasEditor(editor) {
    var salida = [];
    if (!editor || !editor.contCapitulos) return salida;
    editor.contCapitulos.querySelectorAll(".capitulo").forEach(function (capitulo, ci) {
      var capNombre = capitulo.querySelector('[data-f="cap_nombre"]');
      capitulo.querySelectorAll(".partida-wrap").forEach(function (wrap, pi) {
        var nombre = wrap.querySelector('[data-f="p_nombre"]');
        var unidad = wrap.querySelector('[data-f="p_unidad"]');
        var catalogoId = wrap.querySelector('[data-f="p_catalogo_id"]');
        salida.push({
          capitulo: capitulo,
          capituloIndice: ci,
          capituloNombre: capNombre ? capNombre.value : "Capítulo " + (ci + 1),
          wrap: wrap,
          partidaIndice: pi,
          nombre: nombre ? nombre.value : "Partida " + (pi + 1),
          unidad: unidad ? unidad.value : "",
          catalogoId: catalogoId ? Number(catalogoId.value || 0) : 0
        });
      });
    });
    return salida;
  }

  function mostrarSelectorMedicion(editor, datos) {
    var tipo = String(datos.tipo || "");
    var unidad = normalizarTextoEditor(datos.unidad || "").replace(/\s/g, "");
    var palabras = tipo.indexOf("pared") !== -1
      ? ["pared", "muro", "paramento", "revestimiento", "enchapado"]
      : (tipo.indexOf("rodapie") !== -1
        ? ["rodapie", "zocalo", "perimetro"]
        : ["piso", "suelo", "solado", "pavimento"]);
    var todas = partidasEditor(editor);
    var compatibles = todas.filter(function (partida) {
      var unidadPartida = normalizarTextoEditor(partida.unidad).replace(/\s/g, "");
      return !unidad || unidadPartida === unidad;
    });
    var candidatas = compatibles.filter(function (partida) {
      var nombre = normalizarTextoEditor(partida.nombre);
      return palabras.some(function (palabra) { return nombre.indexOf(palabra) !== -1; });
    });
    if (!candidatas.length) candidatas = compatibles;
    if (!candidatas.length) {
      alert("No hay una partida con unidad compatible (" + datos.unidad + ") en el presupuesto.");
      return;
    }

    var vista = crearModalAsistente("Aplicar medición calculada");
    var resumen = document.createElement("p");
    resumen.className = "hint";
    resumen.textContent = datos.concepto + ": " + datos.cantidad + " " + datos.unidad + ". Elige la partida que recibirá esta medición.";
    vista.cuerpo.appendChild(resumen);
    var field = document.createElement("div");
    field.className = "field";
    var label = document.createElement("label");
    label.textContent = "Partida de destino";
    field.appendChild(label);
    var select = document.createElement("select");
    candidatas.forEach(function (partida, indice) {
      var option = document.createElement("option");
      option.value = String(indice);
      option.textContent = partida.capituloNombre + " › " + partida.nombre + " (" + partida.unidad + ")";
      select.appendChild(option);
    });
    field.appendChild(select);
    vista.cuerpo.appendChild(field);
    var acciones = document.createElement("div");
    acciones.className = "form-actions";
    var cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "btn";
    cancelar.textContent = "Cancelar";
    cancelar.addEventListener("click", function () { cerrarModalAsistente(vista.overlay); });
    acciones.appendChild(cancelar);
    var aplicar = document.createElement("button");
    aplicar.type = "button";
    aplicar.className = "btn btn-primary";
    aplicar.textContent = "Confirmar medición";
    aplicar.addEventListener("click", function () {
      var destino = candidatas[Number(select.value || 0)];
      if (!destino) return;
      editor.pushUndo();
      editor.Partida.crearMedicion(destino.wrap, {
        concepto: datos.concepto,
        cantidad: Number(datos.cantidad)
      }, editor);
      destino.capitulo.classList.remove("collapsed");
      destino.wrap.scrollIntoView({ behavior: "smooth", block: "center" });
      cerrarModalAsistente(vista.overlay);
    });
    acciones.appendChild(aplicar);
    vista.cuerpo.appendChild(acciones);
  }

  function mostrarSelectorLote(editor, ids) {
    if (!editor.Catalogo || typeof editor.Catalogo.obtenerFichasPorIds !== "function") {
      alert("El catálogo todavía no está listo para preparar el lote.");
      return;
    }
    editor.Catalogo.obtenerFichasPorIds(ids).then(function (fichas) {
      var vista = crearModalAsistente("Revisar partidas antes de añadir");
      var ayuda = document.createElement("p");
      ayuda.className = "hint";
      ayuda.textContent = "Desmarca lo que no corresponda y elige el capítulo. Nada se añadirá hasta que confirmes.";
      vista.cuerpo.appendChild(ayuda);
      var existentes = partidasEditor(editor).map(function (p) { return p.catalogoId; });
      var lista = document.createElement("div");
      lista.className = "ia-lote-lista";
      fichas.forEach(function (ficha, indice) {
        var fila = document.createElement("label");
        fila.className = "ia-lote-item";
        var check = document.createElement("input");
        check.type = "checkbox";
        check.value = String(indice);
        check.checked = existentes.indexOf(Number(ficha.id)) === -1;
        check.disabled = !check.checked;
        fila.appendChild(check);
        var texto = document.createElement("span");
        texto.textContent = (ficha.codigo_interno || ficha.codigo || "PARTIDA") + " · " + ficha.nombre +
          (check.disabled ? " · Ya está en el presupuesto" : "");
        fila.appendChild(texto);
        lista.appendChild(fila);
      });
      vista.cuerpo.appendChild(lista);

      var field = document.createElement("div");
      field.className = "field";
      var label = document.createElement("label");
      label.textContent = "Capítulo de destino";
      field.appendChild(label);
      var select = document.createElement("select");
      var capitulos = Array.prototype.slice.call(editor.contCapitulos.querySelectorAll(".capitulo"));
      capitulos.forEach(function (capitulo, indice) {
        var nombre = capitulo.querySelector('[data-f="cap_nombre"]');
        var option = document.createElement("option");
        option.value = String(indice);
        option.textContent = (nombre && nombre.value.trim()) || "Capítulo " + (indice + 1);
        select.appendChild(option);
      });
      field.appendChild(select);
      vista.cuerpo.appendChild(field);

      var acciones = document.createElement("div");
      acciones.className = "form-actions";
      var cancelar = document.createElement("button");
      cancelar.type = "button";
      cancelar.className = "btn";
      cancelar.textContent = "Cancelar";
      cancelar.addEventListener("click", function () { cerrarModalAsistente(vista.overlay); });
      acciones.appendChild(cancelar);
      var confirmar = document.createElement("button");
      confirmar.type = "button";
      confirmar.className = "btn btn-primary";
      confirmar.textContent = "Añadir seleccionadas";
      confirmar.addEventListener("click", function () {
        var seleccionadas = [];
        lista.querySelectorAll('input[type="checkbox"]:checked').forEach(function (check) {
          seleccionadas.push(fichas[Number(check.value)]);
        });
        if (!seleccionadas.length) {
          alert("Selecciona al menos una partida.");
          return;
        }
        var capitulo = capitulos[Number(select.value || 0)] || null;
        editor.Catalogo.insertarLote(seleccionadas, capitulo);
        cerrarModalAsistente(vista.overlay);
      });
      acciones.appendChild(confirmar);
      vista.cuerpo.appendChild(acciones);
    }).catch(function () {
      alert("No se pudieron cargar todas las fichas del lote.");
    });
  }

  function ejecutarAccionAsistente(enlace, control) {
    var url;
    try {
      url = new URL(enlace, window.location.origin);
    } catch (_errorUrl) {
      return;
    }
    var editor = window.EDITOR;
    if (!editor || !editor.BUDGET_ID) {
      alert("Abre primero el editor del presupuesto donde quieres aplicar esta acción.");
      return;
    }

    if (url.pathname === "/api/ia/accion/enfocar-borrador") {
      var capituloIndice = Number(url.searchParams.get("capitulo") || 0);
      var partidaParam = url.searchParams.get("partida");
      var capitulos = editor.contCapitulos.querySelectorAll(".capitulo");
      var capitulo = capitulos[capituloIndice];
      if (!capitulo) return;
      capitulo.classList.remove("collapsed");
      var destino = capitulo.querySelector('[data-f="cap_nombre"]');
      if (partidaParam !== null) {
        var partidas = capitulo.querySelectorAll(".partida-wrap");
        var partida = partidas[Number(partidaParam)];
        if (partida) {
          destino = partida.querySelector('[data-f="p_nombre"]') || partida;
          var fila = partida.querySelector(".partida-row");
          if (fila) {
            fila.classList.add("flash");
            setTimeout(function () { fila.classList.remove("flash"); }, 1400);
          }
        }
      }
      if (destino && destino.scrollIntoView) destino.scrollIntoView({ behavior: "smooth", block: "center" });
      if (destino && destino.focus) setTimeout(function () { destino.focus(); }, 350);
      alternarAsistente(false);
      return;
    }

    if (url.pathname === "/api/ia/accion/aplicar-medicion") {
      var cantidad = Number(url.searchParams.get("cantidad") || 0);
      if (!(cantidad > 0)) return;
      mostrarSelectorMedicion(editor, {
        tipo: url.searchParams.get("tipo") || "",
        cantidad: cantidad,
        concepto: url.searchParams.get("concepto") || "Medición calculada",
        unidad: url.searchParams.get("unidad") || "m2"
      });
      return;
    }

    if (url.pathname === "/api/ia/accion/agregar-lote") {
      var ids = String(url.searchParams.get("ids") || "").split(",")
        .map(function (id) { return Number(id); })
        .filter(function (id, indice, lista) { return id > 0 && lista.indexOf(id) === indice; })
        .slice(0, 12);
      if (ids.length) mostrarSelectorLote(editor, ids);
      return;
    }

    if (url.pathname === "/api/ia/accion/agregar-partida") {
      var partidaId = Number(url.searchParams.get("partida_id") || 0);
      if (!partidaId || !editor.Catalogo || typeof editor.Catalogo.insertarPorId !== "function") {
        alert("El editor todavía no está listo para añadir esta partida.");
        return;
      }
      if (!window.confirm("¿Añadir esta partida al presupuesto abierto? Podrás revisar cantidad, precio y capítulo antes de guardar.")) {
        return;
      }
      var textoOriginal = control.textContent;
      control.textContent = "Añadiendo…";
      control.setAttribute("aria-busy", "true");
      editor.Catalogo.insertarPorId(partidaId)
        .then(function (partida) {
          control.textContent = partida ? "✓ Añadida al presupuesto" : textoOriginal;
        })
        .catch(function () {
          control.textContent = textoOriginal;
          alert("No se pudo añadir la partida. Inténtalo de nuevo.");
        })
        .finally(function () {
          control.removeAttribute("aria-busy");
        });
      return;
    }

    if (url.pathname === "/api/ia/accion/abrir-pack") {
      var recetaId = Number(url.searchParams.get("receta_id") || 0);
      if (!recetaId || typeof editor.abrirModalRecetaEstancia !== "function") {
        alert("El módulo de Packs todavía no está listo.");
        return;
      }
      editor.abrirModalRecetaEstancia(recetaId);
    }
  }

  function renderizarMarkdownSeguro(textoCrudo, contenedorDestino) {
    // Vaciar contenedor de forma segura
    while (contenedorDestino.firstChild) {
      contenedorDestino.removeChild(contenedorDestino.firstChild);
    }

    var lineas = String(textoCrudo || "").split("\n");
    var listaActual = null;
    var bloqueCodigo = null;

    lineas.forEach(function (linea) {
      var lineaTrim = linea.trim();

      // Bloques de código con triple backtick
      if (lineaTrim.indexOf("```") === 0) {
        if (bloqueCodigo) {
          bloqueCodigo = null;
        } else {
          bloqueCodigo = document.createElement("pre");
          bloqueCodigo.className = "ia-code-block";
          var codeEl = document.createElement("code");
          bloqueCodigo.appendChild(codeEl);
          contenedorDestino.appendChild(bloqueCodigo);
        }
        return;
      }

      if (bloqueCodigo) {
        var targetCode = bloqueCodigo.querySelector("code");
        if (targetCode) {
          targetCode.textContent += linea + "\n";
        }
        return;
      }

      // Encabezados
      if (lineaTrim.indexOf("### ") === 0) {
        listaActual = null;
        var h3 = document.createElement("h4");
        h3.className = "ia-msg-title";
        parsearLineaInline(lineaTrim.slice(4), h3);
        contenedorDestino.appendChild(h3);
        return;
      }

      if (lineaTrim.indexOf("## ") === 0) {
        listaActual = null;
        var h2 = document.createElement("h3");
        h2.className = "ia-msg-title-lg";
        parsearLineaInline(lineaTrim.slice(3), h2);
        contenedorDestino.appendChild(h2);
        return;
      }

      // Elementos de lista
      if (/^[-*•]\s+/.test(lineaTrim) || /^\d+\.\s+/.test(lineaTrim)) {
        if (!listaActual) {
          listaActual = document.createElement("ul");
          listaActual.className = "ia-list";
          contenedorDestino.appendChild(listaActual);
        }
        var li = document.createElement("li");
        var textoItem = lineaTrim.replace(/^[-*•]\s+|\d+\.\s+/, "");
        parsearLineaInline(textoItem, li);
        listaActual.appendChild(li);
        return;
      }

      // Línea en blanco / separador
      if (!lineaTrim) {
        listaActual = null;
        return;
      }

      // Párrafo ordinario
      listaActual = null;
      var p = document.createElement("p");
      p.className = "ia-paragraph";
      parsearLineaInline(linea, p);
      contenedorDestino.appendChild(p);
    });
  }

  // -------------------------------------------------------------------------
  // Gestión de la Interfaz del Chat
  // -------------------------------------------------------------------------

  function alternarAsistente(forzarAbrir) {
    var panel = document.getElementById("cotizat-ia-panel");
    var launcher = document.getElementById("cotizat-ia-launcher");
    if (!panel) return;

    var estaAbierto = panel.classList.contains("abierto");
    var nuevoEstado = (forzarAbrir !== undefined) ? !!forzarAbrir : !estaAbierto;

    if (nuevoEstado) {
      panel.classList.add("abierto");
      if (launcher) launcher.classList.add("activo");
      var input = document.getElementById("cotizat-ia-input");
      if (input) setTimeout(function () { input.focus(); }, 150);
      scrollAlFinal();
    } else {
      panel.classList.remove("abierto");
      if (launcher) launcher.classList.remove("activo");
    }
  }

  function scrollAlFinal() {
    var body = document.getElementById("cotizat-ia-messages");
    if (body) {
      body.scrollTop = body.scrollHeight;
    }
  }

  function crearBurbujaMensaje(rol, textoInicial) {
    var messagesContainer = document.getElementById("cotizat-ia-messages");
    if (!messagesContainer) return null;

    var fila = document.createElement("div");
    fila.className = "ia-message-row " + (rol === "user" ? "ia-user-row" : "ia-bot-row");

    if (rol !== "user") {
      var avatar = document.createElement("div");
      avatar.className = "ia-avatar";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = "✨";
      fila.appendChild(avatar);
    }

    var bubble = document.createElement("div");
    bubble.className = "ia-bubble " + (rol === "user" ? "ia-user-bubble" : "ia-bot-bubble");

    var content = document.createElement("div");
    content.className = "ia-bubble-content";
    if (textoInicial) {
      if (rol === "user") {
        content.textContent = textoInicial;
      } else {
        renderizarMarkdownSeguro(textoInicial, content);
      }
    }
    bubble.appendChild(content);

    // Botón de copiar para respuestas del asistente
    if (rol !== "user") {
      var copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "ia-copy-btn";
      copyBtn.setAttribute("title", "Copiar respuesta");
      copyBtn.setAttribute("aria-label", "Copiar respuesta");
      copyBtn.textContent = "📋 Copiar";
      copyBtn.addEventListener("click", function () {
        var textoCopiar = content.textContent || "";
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(textoCopiar).then(function () {
            copyBtn.textContent = "✓ Copiado";
            setTimeout(function () { copyBtn.textContent = "📋 Copiar"; }, 2000);
          });
        }
      });
      bubble.appendChild(copyBtn);
    }

    fila.appendChild(bubble);
    messagesContainer.appendChild(fila);
    scrollAlFinal();

    return content;
  }

  function limpiarConversacion() {
    chatHistorial = [];
    var messagesContainer = document.getElementById("cotizat-ia-messages");
    if (!messagesContainer) return;

    while (messagesContainer.firstChild) {
      messagesContainer.removeChild(messagesContainer.firstChild);
    }

    // Insertar mensaje de bienvenida con sugerencias rápidas
    insertarMensajeBienvenida();
  }

  function insertarMensajeBienvenida() {
    var messagesContainer = document.getElementById("cotizat-ia-messages");
    if (!messagesContainer) return;

    var fila = document.createElement("div");
    fila.className = "ia-message-row ia-bot-row";

    var avatar = document.createElement("div");
    avatar.className = "ia-avatar";
    avatar.textContent = "✨";
    fila.appendChild(avatar);

    var bubble = document.createElement("div");
    bubble.className = "ia-bubble ia-bot-bubble ia-welcome-bubble";

    var content = document.createElement("div");
    content.className = "ia-bubble-content";

    var title = document.createElement("h4");
    title.className = "ia-welcome-title";
    title.textContent = "¡Hola! Soy tu Asistente CotizaT";
    content.appendChild(title);

    var p = document.createElement("p");
    p.className = "ia-paragraph";
    p.textContent = "Puedo buscar datos reales de tu empresa, revisar el presupuesto abierto y añadir partidas o Packs con tu confirmación.";
    content.appendChild(p);

    var chipsTitle = document.createElement("div");
    chipsTitle.className = "ia-chips-title";
    chipsTitle.textContent = "Acciones rápidas:";
    content.appendChild(chipsTitle);

    var chipsContainer = document.createElement("div");
    chipsContainer.className = "ia-suggestions-grid";

    var sugerencias = [
      { icono: "✅", texto: "Revisar el borrador visible", prompt: "Revisa este presupuesto y dime si está listo para enviar" },
      { icono: "📐", texto: "Calcular mediciones de un baño", prompt: "El baño mide 3 × 2 m, tiene 2,40 m de altura y una puerta de 0,80 × 2,10 m" },
      { icono: "🧰", texto: "Preparar demolición de porcelanato", prompt: "Prepara las partidas necesarias para demolición de porcelanato" },
      { icono: "🧭", texto: "Detectar faltantes de alcance", prompt: "¿Qué falta en el alcance de este presupuesto?" },
      { icono: "🔎", texto: "Buscar una partida", prompt: "¿Qué partida uso para demolición de porcelanato?" }
    ];

    sugerencias.forEach(function (sug) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "ia-suggestion-chip";

      var ico = document.createElement("span");
      ico.className = "ia-chip-icon";
      ico.textContent = sug.icono;
      chip.appendChild(ico);

      var txt = document.createElement("span");
      txt.textContent = sug.texto;
      chip.appendChild(txt);

      chip.addEventListener("click", function () {
        enviarConsulta(sug.prompt);
      });

      chipsContainer.appendChild(chip);
    });

    content.appendChild(chipsContainer);
    bubble.appendChild(content);
    fila.appendChild(bubble);
    messagesContainer.appendChild(fila);
  }

  // -------------------------------------------------------------------------
  // Envío y Streaming de Mensajes
  // -------------------------------------------------------------------------

  function obtenerContextoActual(consulta) {
    var contexto = { pagina: window.location.pathname || "/" };
    var presupuestoId = Number(
      window.BUDGET_ID || (window.EDITOR && window.EDITOR.BUDGET_ID) || 0
    );
    if (!presupuestoId) {
      var matchPresupuesto = String(window.location.pathname || "").match(/^\/presupuestos\/(\d+)(?:\/|$)/);
      if (matchPresupuesto) presupuestoId = Number(matchPresupuesto[1]);
    }
    if (presupuestoId > 0) contexto.presupuesto_id = presupuestoId;

    // El borrador viaja únicamente cuando una herramienta necesita analizar
    // el contenido vivo. Nunca se incorpora al prompt generativo.
    var requiereBorrador = /\b(revis|audit|falt|alcance|incomplet|duplic|prepara|anad|añad|partidas necesarias)\w*/i.test(String(consulta || ""));
    if (
      requiereBorrador && window.EDITOR &&
      typeof window.EDITOR.serializar === "function"
    ) {
      try { contexto.borrador = window.EDITOR.serializar(); } catch (_errorBorrador) {}
    }
    return contexto;
  }

  function enviarConsulta(textoManual) {
    if (estaGenerando) return;

    var input = document.getElementById("cotizat-ia-input");
    var texto = String(textoManual || (input ? input.value : "")).trim();
    if (!texto) return;

    if (input) {
      input.value = "";
      if (window.CotizatStyles) window.CotizatStyles.set(input, "height", "auto");
    }

    // Agregar mensaje del usuario en UI y en el historial
    crearBurbujaMensaje("user", texto);
    chatHistorial.push({ role: "user", content: texto });

    // Indicador de escribiendo y burbuja del asistente
    estaGenerando = true;
    var sendBtn = document.getElementById("cotizat-ia-send");
    if (sendBtn) sendBtn.disabled = true;

    var botBubbleContent = crearBurbujaMensaje("assistant", "");
    var indicadorEscribiendo = document.createElement("div");
    indicadorEscribiendo.className = "ia-typing-indicator";
    for (var i = 0; i < 3; i++) {
      var dot = document.createElement("span");
      indicadorEscribiendo.appendChild(dot);
    }
    botBubbleContent.appendChild(indicadorEscribiendo);

    var textoAcumulado = "";
    var generacionFinalizada = false;

    function finalizarUnaVez(textoFinal) {
      if (generacionFinalizada) return;
      generacionFinalizada = true;
      finalizarGeneracion(botBubbleContent, textoFinal);
    }

    fetch("/api/ia/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      },
      body: JSON.stringify({
        messages: chatHistorial,
        stream: true,
        contexto: obtenerContextoActual(texto)
      })
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Error en la respuesta del servidor (HTTP " + response.status + ")");
        }

        var reader = response.body.getReader();
        var decoder = new TextDecoder("utf-8");
        var buffer = "";

        function leerSiguienteChunk() {
          return reader.read().then(function (result) {
            if (result.done) {
              finalizarUnaVez(textoAcumulado);
              return;
            }

            buffer += decoder.decode(result.value, { stream: true });
            var lineas = buffer.split("\n");
            buffer = lineas.pop() || "";

            lineas.forEach(function (linea) {
              var lTrim = linea.trim();
              if (lTrim.indexOf("data:") === 0) {
                var jsonStr = lTrim.slice(5).trim();
                if (!jsonStr) return;
                try {
                  var data = JSON.parse(jsonStr);
                  if (data.texto) {
                    // Retirar el indicador de escribiendo si aún existe
                    if (indicadorEscribiendo && indicadorEscribiendo.parentNode) {
                      indicadorEscribiendo.parentNode.removeChild(indicadorEscribiendo);
                    }
                    textoAcumulado += data.texto;
                    renderizarMarkdownSeguro(textoAcumulado, botBubbleContent);
                    scrollAlFinal();
                  }
                  if (data.finalizado) {
                    finalizarUnaVez(textoAcumulado);
                  }
                } catch (_e) {
                  // Fragmento no JSON, ignorar
                }
              }
            });

            return leerSiguienteChunk();
          });
        }

        return leerSiguienteChunk();
      })
      .catch(function (error) {
        if (indicadorEscribiendo && indicadorEscribiendo.parentNode) {
          indicadorEscribiendo.parentNode.removeChild(indicadorEscribiendo);
        }
        var errorMsg = "⚠️ Lo sentimos, ocurrió un problema de conexión al consultar el asistente. Inténtalo de nuevo.";
        renderizarMarkdownSeguro(errorMsg, botBubbleContent);
        finalizarUnaVez(errorMsg);
      });
  }

  function finalizarGeneracion(contenedor, textoFinal) {
    estaGenerando = false;
    var sendBtn = document.getElementById("cotizat-ia-send");
    if (sendBtn) sendBtn.disabled = false;

    if (textoFinal) {
      chatHistorial.push({ role: "assistant", content: textoFinal });
    }
    scrollAlFinal();
  }

  // -------------------------------------------------------------------------
  // Integración contextual con Editor de Partidas
  // -------------------------------------------------------------------------

  function mejorarDescripcionPartida(boton) {
    var contenedor = boton.closest(".partida-editor") || boton.closest("form") || document;
    var tituloInput = contenedor.querySelector("input[name='nombre'], input[name='titulo'], #nombre, #partida_nombre");
    var descTextarea = contenedor.querySelector("textarea[name='descripcion'], #descripcion, #partida_descripcion");
    var unidadInput = contenedor.querySelector("input[name='unidad'], select[name='unidad'], #unidad");
    var catInput = contenedor.querySelector("input[name='categoria'], select[name='categoria'], #categoria");

    if (!tituloInput || !descTextarea) return;

    var titulo = String(tituloInput.value || "").trim();
    if (!titulo) {
      alert("Introduce primero el nombre o título de la partida.");
      tituloInput.focus();
      return;
    }

    var textoOriginal = boton.textContent;
    boton.textContent = "⏳ Redactando...";
    boton.disabled = true;

    fetch("/api/ia/redactar-descripcion", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({
        titulo: titulo,
        categoria: catInput ? String(catInput.value || "") : "",
        unidad: unidadInput ? String(unidadInput.value || "m2") : "m2"
      })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.ok && data.descripcion) {
          descTextarea.value = data.descripcion;
          descTextarea.dispatchEvent(new Event("input", { bubbles: true }));
          descTextarea.dispatchEvent(new Event("change", { bubbles: true }));
        } else {
          alert(data.error || "No se pudo generar la descripción.");
        }
      })
      .catch(function () {
        alert("Ocurrió un error al contactar el asistente.");
      })
      .finally(function () {
        boton.textContent = textoOriginal;
        boton.disabled = false;
      });
  }

  // -------------------------------------------------------------------------
  // Estado real del motor (el catálogo funciona incluso sin proveedor externo)
  // -------------------------------------------------------------------------

  function actualizarEstadoAsistente() {
    var estadoCabecera = document.getElementById("cotizat-ia-status");
    var estadoPie = document.getElementById("cotizat-ia-footer-status");
    fetch("/api/ia/estado", {
      method: "GET",
      headers: { "Accept": "application/json" }
    })
      .then(function (res) {
        if (!res.ok) throw new Error("Estado no disponible");
        return res.json();
      })
      .then(function (data) {
        if (data.configurado) {
          if (estadoCabecera) estadoCabecera.textContent = "● Catálogo + IA generativa";
          if (estadoPie) estadoPie.textContent = "Catálogo real · GPT OSS 120B · Enter para enviar";
        } else {
          if (estadoCabecera) estadoCabecera.textContent = "● Catálogo local activo";
          if (estadoPie) estadoPie.textContent = "Búsqueda real disponible · Enter para enviar";
        }
      })
      .catch(function () {
        if (estadoCabecera) estadoCabecera.textContent = "● Asistente disponible";
      });
  }

  // -------------------------------------------------------------------------
  // Inicialización y Registro de Acciones Declarativas
  // -------------------------------------------------------------------------

  function inicializar() {
    actualizarEstadoAsistente();

    // Registrar acciones en el despachador central de CotizaT
    if (window.CotizatActions && typeof window.CotizatActions.register === "function") {
      window.CotizatActions.register("toggle-ia-chat", function () {
        alternarAsistente();
      });
      window.CotizatActions.register("clear-ia-chat", function () {
        limpiarConversacion();
      });
      window.CotizatActions.register("send-ia-chat", function () {
        enviarConsulta();
      });
      window.CotizatActions.register("ia-redactar-partida", function (btn) {
        mejorarDescripcionPartida(btn);
      });
    }

    // Configurar textarea auto-expandible y atajo Enter
    var input = document.getElementById("cotizat-ia-input");
    if (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          enviarConsulta();
        }
      });
      input.addEventListener("input", function () {
        if (window.CotizatStyles) {
          window.CotizatStyles.set(this, "height", "auto");
          window.CotizatStyles.set(this, "height", Math.min(this.scrollHeight, 120) + "px");
        }
      });
    }

    // Insertar bienvenida inicial si la ventana está vacía
    var messagesContainer = document.getElementById("cotizat-ia-messages");
    if (messagesContainer && !messagesContainer.hasChildNodes()) {
      insertarMensajeBienvenida();
    }
  }

  window.CotizatIA = {
    abrir: function () { alternarAsistente(true); },
    cerrar: function () { alternarAsistente(false); },
    alternar: alternarAsistente,
    enviar: enviarConsulta,
    limpiar: limpiarConversacion
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar);
  } else {
    inicializar();
  }
})();
