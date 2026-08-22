/**
 * Asistente Inteligente de CotizaT (Copilot).
 *
 * Proporciona soporte en vivo, resolución de dudas de uso, navegación y
 * redacción técnica asistida por IA (Llama 3.3 70B vía Groq).
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
    p.textContent = "Puedo responder tus dudas sobre el software, sugerirte partidas de obra, redactar especificaciones técnicas o guiarte paso a paso.";
    content.appendChild(p);

    var chipsTitle = document.createElement("div");
    chipsTitle.className = "ia-chips-title";
    chipsTitle.textContent = "Preguntas frecuentes:";
    content.appendChild(chipsTitle);

    var chipsContainer = document.createElement("div");
    chipsContainer.className = "ia-suggestions-grid";

    var sugerencias = [
      { icono: "⚡", texto: "¿Cuáles son los atajos de teclado?", prompt: "¿Cuáles son los atajos de teclado en el editor de presupuestos?" },
      { icono: "📑", texto: "¿Cómo importar un descompuesto CYPE?", prompt: "¿Cómo importar un archivo de descompuesto CYPE en Excel a CotizaT?" },
      { icono: "🛁", texto: "Presupuesto para remodelar baño", prompt: "¿Qué capítulos y partidas debo incluir para presupuestar una remodelación de baño?" },
      { icono: "💱", texto: "Configurar moneda y tasa BCV", prompt: "¿Cómo configuro la moneda principal y la tasa de cambio en CotizaT?" }
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

    fetch("/api/ia/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      },
      body: JSON.stringify({
        messages: chatHistorial,
        stream: true
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
              finalizarGeneracion(botBubbleContent, textoAcumulado);
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
                    finalizarGeneracion(botBubbleContent, textoAcumulado);
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
        finalizarGeneracion(botBubbleContent, errorMsg);
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
  // Inicialización y Registro de Acciones Declarativas
  // -------------------------------------------------------------------------

  function inicializar() {
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
