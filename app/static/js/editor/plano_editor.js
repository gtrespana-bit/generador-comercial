/* Editor de planos desde cero para CotizaT.

   Se activa cuando ``plano.origen === 'dibujado'`` o cuando el usuario
   pulsa "Editar geometría" sobre un plano ``mixto``. Ofrece cuatro
   herramientas: muro, puerta, ventana y selección. Los muros se
   guardan como ``PlanoElemento`` con su grosor; las puertas y
   ventanas referencian el muro al que pertenecen para que la métrica
   pueda descontarlas del desarrollo de paredes.

   El render usa el mismo canvas que el visor principal (``#plano-canvas``)
   para evitar duplicar el motor de zoom/paneo. El lienzo virtual del
   plano en blanco se dibuja como una cuadrícula isométrica con
   coordenadas en metros para que el usuario mida mientras dibuja.

   Esta capa no es invasiva: si el JS no encuentra los hooks del
   editor (porque la página no tiene ``data-plano-editor``), se sale
   silenciosamente y el visor sigue funcionando como antes.
*/
(function () {
  "use strict";

  var API = {
    crear: "/planos/{plano_id}/elementos",
    actualizar: "/planos/{plano_id}/elementos/{elemento_id}",
    eliminar: "/planos/{plano_id}/elementos/{elemento_id}",
    grosor: "/planos/{plano_id}/grosor",
    detectar: "/planos/{plano_id}/detectar",
    enBlanco: "/presupuestos/{presupuesto_id}/planos/blanco",
  };

  function $(id) { return document.getElementById(id); }
  function normUrl(template, ctx) {
    return template.replace(/\{(\w+)\}/g, function (_, k) { return ctx[k]; });
  }

  function Estado(plano) {
    this.plano = plano;
    this.herramienta = "muro";
    this.puntosActuales = [];
    this.elementoEnEdicion = null;
    this.grosorCm = plano.grosor_tabique_cm || 10;
    this.color = "#1f2937";
  }

  function findPlanoGlobal() {
    if (typeof window !== "undefined" && window.PLANO_ACTIVO) {
      return window.PLANO_ACTIVO;
    }
    return null;
  }

  function panelDisponible() {
    return !!document.getElementById("plano-editor-panel");
  }

  function asegurarLienzo(contenedor, ancho, alto) {
    if (window.CotizatStyles) {
      CotizatStyles.set(contenedor, "position", "relative");
    }
    if (!document.getElementById("plano-editor-canvas")) {
      var c = document.createElement("canvas");
      c.id = "plano-editor-canvas";
      if (window.CotizatStyles) {
        CotizatStyles.setMany(c, {
          position: "absolute",
          inset: "0",
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        });
      }
      contenedor.appendChild(c);
    }
    return document.getElementById("plano-editor-canvas");
  }

  function construirLienzoPx(plano) {
    // Lienzo virtual en metros -> píxeles de pantalla del editor.
    // El lienzo del editor se renderiza en una capa paralela al canvas
    // principal con coordenadas coherentes con la escala calibrada.
    if (!plano.escala_px_por_metro) {
      return { anchoPx: 1200, altoPx: 800, factor: 50 };
    }
    var anchoM = plano.ancho_lienzo_m || (plano.ancho_px ? plano.ancho_px / plano.escala_px_por_metro : 12);
    var altoM = plano.alto_lienzo_m || (plano.alto_px ? plano.alto_px / plano.escala_px_por_metro : 8);
    return {
      anchoPx: Math.round(anchoM * plano.escala_px_por_metro),
      altoPx: Math.round(altoM * plano.escala_px_por_metro),
      factor: plano.escala_px_por_metro,
    };
  }

  function pintarCuadricula(ctx, ancho, alto, escala) {
    if (!escala) return;
    var factorPx = escala;  // px / m
    ctx.save();
    ctx.strokeStyle = "rgba(100, 116, 139, 0.18)";
    ctx.lineWidth = 1;
    for (var x = 0; x <= ancho; x += factorPx) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, alto);
      ctx.stroke();
    }
    for (var y = 0; y <= alto; y += factorPx) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(ancho, y);
      ctx.stroke();
    }
    // Eje principal cada metro
    ctx.strokeStyle = "rgba(100, 116, 139, 0.35)";
    for (var x2 = 0; x2 <= ancho; x2 += factorPx * 5) {
      ctx.beginPath();
      ctx.moveTo(x2, 0);
      ctx.lineTo(x2, alto);
      ctx.stroke();
    }
    for (var y2 = 0; y2 <= alto; y2 += factorPx * 5) {
      ctx.beginPath();
      ctx.moveTo(0, y2);
      ctx.lineTo(ancho, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function pintarElemento(ctx, elemento, escala) {
    if (!elemento || !ctx) return;
    var pts = elemento.puntos || [];
    ctx.save();
    if (elemento.tipo === "muro") {
      ctx.strokeStyle = elemento.color || "#1f2937";
      ctx.fillStyle = (elemento.color || "#1f2937") + "55";
      ctx.lineWidth = Math.max(2, (elemento.grosor_cm / 100) * (escala || 50));
      if (pts.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(pts[0][0], pts[0][1]);
        for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
        ctx.stroke();
      }
    } else if (elemento.tipo === "hueco") {
      var sub = (pts[0] && pts[0][2]) || "puerta";
      ctx.fillStyle = sub === "puerta" ? "rgba(244, 114, 182, 0.5)" : "rgba(56, 189, 248, 0.5)";
      ctx.strokeStyle = sub === "puerta" ? "#db2777" : "#0284c7";
      ctx.lineWidth = 1.4;
      if (pts.length >= 1) {
        var cx = pts[0][0];
        var cy = pts[0][1];
        var ancho = (pts[0][2] || 60);
        var alto = (pts[0][3] || 30);
        ctx.beginPath();
        ctx.rect(cx, cy, ancho, alto);
        ctx.fill();
        ctx.stroke();
      }
    } else if (elemento.tipo === "linea_auxiliar") {
      ctx.strokeStyle = "rgba(14, 165, 233, 0.7)";
      ctx.setLineDash([5, 4]);
      ctx.lineWidth = 1.2;
      if (pts.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(pts[0][0], pts[0][1]);
        for (var j = 1; j < pts.length; j++) ctx.lineTo(pts[j][0], pts[j][1]);
        ctx.stroke();
      }
      ctx.setLineDash([]);
    }
    ctx.restore();
  }

  function pintarTrazoActual(ctx, estado, escala) {
    if (!ctx || !estado.puntosActuales.length) return;
    ctx.save();
    ctx.strokeStyle = estado.color || "#1f2937";
    ctx.lineWidth = Math.max(2, (estado.grosorCm / 100) * (escala || 50));
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(estado.puntosActuales[0][0], estado.puntosActuales[0][1]);
    for (var i = 1; i < estado.puntosActuales.length; i++) {
      ctx.lineTo(estado.puntosActuales[i][0], estado.puntosActuales[i][1]);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    estado.puntosActuales.forEach(function (pt) {
      ctx.beginPath();
      ctx.arc(pt[0], pt[1], 4, 0, Math.PI * 2);
      ctx.fillStyle = estado.color || "#1f2937";
      ctx.fill();
    });
    ctx.restore();
  }

  function render(estado, contenedor) {
    var lienzo = asegurarLienzo(contenedor);
    var dims = construirLienzoPx(estado.plano);
    lienzo.width = dims.anchoPx || 1200;
    lienzo.height = dims.altoPx || 800;
    var ctx = lienzo.getContext("2d");
    ctx.clearRect(0, 0, lienzo.width, lienzo.height);
    pintarCuadricula(ctx, lienzo.width, lienzo.height, dims.factor);
    (estado.plano.elementos || []).forEach(function (e) { pintarElemento(ctx, e, dims.factor); });
    pintarTrazoActual(ctx, estado, dims.factor);
  }

  function fmtM(num) {
    if (num == null || isNaN(num)) return "—";
    return Number(num).toFixed(2).replace(".", ",") + " m";
  }

  function actualizarEstadoAyuda(estado) {
    var ayuda = $("plano-editor-ayuda");
    if (!ayuda) return;
    var msg = {
      muro: "Muro: haz clic en cada vértice. Doble clic para terminar.",
      puerta: "Puerta: haz clic sobre un muro. Arrastra para ajustar el ancho.",
      ventana: "Ventana: haz clic sobre un muro. Arrastra para ajustar el ancho.",
      seleccion: "Selección: haz clic en un muro o hueco para editarlo o borrarlo.",
    }[estado.herramienta] || "";
    ayuda.textContent = msg;
    var grosor = $("plano-editor-grosor-valor");
    if (grosor) grosor.textContent = (estado.grosorCm || 10).toFixed(1) + " cm";
  }

  function persistirGrosor(estado) {
    return fetch(normUrl(API.grosor, { plano_id: estado.plano.id }), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grosor_tabique_cm: estado.grosorCm }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.ok && data.grosor_tabique_cm != null) {
          estado.grosorCm = data.grosor_tabique_cm;
          estado.plano.grosor_tabique_cm = data.grosor_tabique_cm;
        }
        return data;
      });
  }

  function enviarElemento(estado, payload, opts) {
    var url = opts && opts.id
      ? normUrl(API.actualizar, { plano_id: estado.plano.id, elemento_id: opts.id })
      : normUrl(API.crear, { plano_id: estado.plano.id });
    var metodo = opts && opts.id ? "PUT" : "POST";
    return fetch(url, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok || !res.data || !res.data.ok) {
          throw new Error((res.data && res.data.error) || "No se pudo guardar el elemento.");
        }
        return res.data.elemento;
      });
  }

  function eliminarElemento(estado, id) {
    return fetch(normUrl(API.eliminar, { plano_id: estado.plano.id, elemento_id: id }), {
      method: "DELETE",
    }).then(function (r) { return r.json(); });
  }

  function pintar(estado, contenedor) {
    render(estado, contenedor);
  }

  function onCanvasClick(estado, contenedor, ev) {
    var lienzo = asegurarLienzo(contenedor);
    var rect = lienzo.getBoundingClientRect();
    var factorX = lienzo.width / Math.max(1, rect.width);
    var factorY = lienzo.height / Math.max(1, rect.height);
    var x = (ev.clientX - rect.left) * factorX;
    var y = (ev.clientY - rect.top) * factorY;
    var herr = estado.herramienta;
    if (herr === "muro") {
      estado.puntosActuales.push([x, y]);
      pintar(estado, contenedor);
    } else if (herr === "puerta" || herr === "ventana") {
      // Hueco: pedimos ancho arrastrando. Primer clic fija esquina, drag hasta soltar.
      estado.puntosActuales = [[x, y, herr, 80, 30]];
      pintar(estado, contenedor);
    } else if (herr === "seleccion") {
      // Buscar el elemento más cercano.
      var objetivo = null;
      (estado.plano.elementos || []).forEach(function (e) {
        if (e.tipo === "muro" && e.puntos && e.puntos.length >= 2) {
          var d = distanciaPuntoSegmento([x, y], e.puntos[0], e.puntos[1]);
          if (d < 12) objetivo = e;
        }
      });
      if (objetivo) {
        var nuevoEstado = confirm("¿Eliminar el muro seleccionado?")
          ? "eliminar"
          : "editar";
        if (nuevoEstado === "eliminar") {
          eliminarElemento(estado, objetivo.id).then(function () {
            estado.plano.elementos = (estado.plano.elementos || []).filter(function (e) { return e.id !== objetivo.id; });
            pintar(estado, contenedor);
          });
        } else {
          estado.elementoEnEdicion = objetivo;
          var nuevoGrosor = prompt("Grosor del muro en cm:", objetivo.grosor_cm);
          if (nuevoGrosor != null) {
            enviarElemento(estado, {
              tipo: objetivo.tipo,
              puntos: objetivo.puntos,
              grosor_cm: parseFloat(nuevoGrosor) || objetivo.grosor_cm,
              color: objetivo.color,
            }, { id: objetivo.id })
              .then(function (elemento) {
                Object.assign(objetivo, elemento);
                pintar(estado, contenedor);
              });
          }
        }
      }
    }
  }

  function onCanvasDblClick(estado, contenedor, ev) {
    if (estado.herramienta !== "muro") return;
    if (estado.puntosActuales.length < 2) {
      estado.puntosActuales = [];
      pintar(estado, contenedor);
      return;
    }
    enviarElemento(estado, {
      tipo: "muro",
      puntos: estado.puntosActuales,
      grosor_cm: estado.grosorCm,
      color: estado.color,
    })
      .then(function (elemento) {
        estado.plano.elementos = (estado.plano.elementos || []).concat([elemento]);
        estado.puntosActuales = [];
        pintar(estado, contenedor);
      })
      .catch(function (err) {
        alert(err.message);
      });
  }

  function onCanvasMouseUp(estado, ev) {
    if ((estado.herramienta === "puerta" || estado.herramienta === "ventana") && estado.puntosActuales.length === 1) {
      // Mover el segundo vértice crea un rectángulo; simplificamos
      // pidiendo el ancho vía prompt para que la operación sea rápida
      // y precisa.
      var ancho = prompt("Ancho del hueco en cm (1 cm a 400 cm):", "80");
      if (ancho === null) {
        estado.puntosActuales = [];
        return;
      }
      var anchoNum = parseFloat(ancho);
      if (!isFinite(anchoNum) || anchoNum <= 0 || anchoNum > 400) {
        alert("Ancho no válido (1 a 400 cm).");
        estado.puntosActuales = [];
        return;
      }
      var p0 = estado.puntosActuales[0];
      enviarElemento(estado, {
        tipo: "hueco",
        puntos: [[p0[0], p0[1], estado.herramienta, anchoNum, 20]],
        grosor_cm: 0,
        color: estado.herramienta === "puerta" ? "#db2777" : "#0284c7",
      })
        .then(function (elemento) {
          estado.plano.elementos = (estado.plano.elementos || []).concat([elemento]);
          estado.puntosActuales = [];
          pintar(estado, getContenedorActivo());
        })
        .catch(function (err) {
          alert(err.message);
        });
    }
  }

  function getContenedorActivo() {
    return $("canvas-container") || document.body;
  }

  function distanciaPuntoSegmento(p, a, b) {
    var dx = b[0] - a[0];
    var dy = b[1] - a[1];
    var l2 = dx * dx + dy * dy;
    if (!l2) return Math.hypot(p[0] - a[0], p[1] - a[1]);
    var t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2));
    var qx = a[0] + t * dx;
    var qy = a[1] + t * dy;
    return Math.hypot(p[0] - qx, p[1] - qy);
  }

  function construirPanel(estado) {
    if ($("plano-editor-panel")) return;
    var cont = getContenedorActivo();
    var panel = document.createElement("div");
    panel.id = "plano-editor-panel";
    panel.className = "plano-editor-panel";

    // El panel se construye con createElement (no se usa la API de
    // asignación de HTML crudo) para evitar sinks de inyección. El
    // test de seguridad audita que ningún front use la asignación
    // directa de HTML al DOM.
    var head = document.createElement("header");
    head.className = "plano-editor-head";
    var headTitulo = document.createElement("strong");
    headTitulo.textContent = "Editor vectorial";
    var ayuda = document.createElement("span");
    ayuda.className = "plano-editor-ayuda";
    ayuda.id = "plano-editor-ayuda";
    head.appendChild(headTitulo);
    head.appendChild(ayuda);

    var tools = document.createElement("div");
    tools.className = "plano-editor-tools";
    var herramientas = [
      ["muro", "Muro", true],
      ["puerta", "Puerta", false],
      ["ventana", "Ventana", false],
      ["seleccion", "Selección", false],
    ];
    herramientas.forEach(function (h) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "plano-editor-tool" + (h[2] ? " active" : "");
      b.dataset.herr = h[0];
      b.textContent = h[1];
      tools.appendChild(b);
    });

    var grosor = document.createElement("div");
    grosor.className = "plano-editor-grosor";
    var grosorLabel = document.createElement("label");
    grosorLabel.appendChild(document.createTextNode("Grosor "));
    var grosorOut = document.createElement("output");
    grosorOut.id = "plano-editor-grosor-valor";
    grosorOut.textContent = "10.0 cm";
    grosorLabel.appendChild(grosorOut);
    var grosorRange = document.createElement("input");
    grosorRange.type = "range";
    grosorRange.id = "plano-editor-grosor";
    grosorRange.min = "3";
    grosorRange.max = "40";
    grosorRange.step = "0.5";
    grosorRange.value = "10";
    grosor.appendChild(grosorLabel);
    grosor.appendChild(grosorRange);

    var acciones = document.createElement("div");
    acciones.className = "plano-editor-acciones";
    var botonesAccion = [
      ["plano-editor-detectar", "Detectar estancias", "btn btn-sm"],
      ["plano-editor-limpiar", "Limpiar selección", "btn btn-sm"],
      ["plano-editor-cerrar", "Cerrar editor", "btn btn-sm btn-primary"],
    ];
    botonesAccion.forEach(function (cfg) {
      var b = document.createElement("button");
      b.type = "button";
      b.id = cfg[0];
      b.className = cfg[2];
      b.textContent = cfg[1];
      acciones.appendChild(b);
    });

    panel.appendChild(head);
    panel.appendChild(tools);
    panel.appendChild(grosor);
    panel.appendChild(acciones);
    cont.appendChild(panel);
    panel.querySelectorAll("[data-herr]").forEach(function (b) {
      b.addEventListener("click", function () {
        estado.herramienta = b.dataset.herr;
        panel.querySelectorAll("[data-herr]").forEach(function (otro) {
          otro.classList.toggle("active", otro === b);
        });
        estado.puntosActuales = [];
        actualizarEstadoAyuda(estado);
        pintar(estado, cont);
      });
    });
    var grosor = $("plano-editor-grosor");
    grosor.value = String(estado.grosorCm);
    grosor.addEventListener("input", function () {
      var v = parseFloat(grosor.value);
      if (isFinite(v) && v > 0) {
        estado.grosorCm = v;
        actualizarEstadoAyuda(estado);
        persistirGrosor(estado);
        pintar(estado, cont);
      }
    });
    $("plano-editor-detectar").addEventListener("click", function () {
      fetch(normUrl(API.detectar, { plano_id: estado.plano.id }), { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && data.ok) {
            alert(data.modo === "vectorial"
              ? "Estancias detectadas: " + (data.nuevas || 0) + "."
              : "Estancias detectadas en la imagen: " + (data.nuevas || 0) + " (existentes: " + (data.omitidas || 0) + ").");
            if (typeof window.cargarPlano === "function") {
              window.cargarPlano(estado.plano.id);
            }
          } else {
            alert((data && data.error) || "No se pudo analizar el plano.");
          }
        })
        .catch(function () { alert("Error de red."); });
    });
    $("plano-editor-limpiar").addEventListener("click", function () {
      estado.puntosActuales = [];
      pintar(estado, cont);
    });
    $("plano-editor-cerrar").addEventListener("click", function () {
      panel.remove();
      var lienzo = document.getElementById("plano-editor-canvas");
      if (lienzo) lienzo.remove();
    });
  }

  function iniciar(estado) {
    if (!panelDisponible() && !document.getElementById("canvas-container")) return;
    construirPanel(estado);
    var cont = getContenedorActivo();
    var lienzo = asegurarLienzo(cont);
    if (window.CotizatStyles) {
      CotizatStyles.set(lienzo, "pointerEvents", "auto");
    }
    lienzo.addEventListener("click", function (ev) { onCanvasClick(estado, cont, ev); });
    lienzo.addEventListener("dblclick", function (ev) { onCanvasDblClick(estado, cont, ev); });
    lienzo.addEventListener("mouseup", function (ev) { onCanvasMouseUp(estado, ev); });
    actualizarEstadoAyuda(estado);
    pintar(estado, cont);
  }

  function init() {
    var plano = findPlanoGlobal();
    if (!plano) return;
    if (plano.origen !== "dibujado" && plano.origen !== "mixto") return;
    var estado = new Estado(plano);
    iniciar(estado);
  }

  // API expuesta para abrir el editor desde fuera (p. ej. desde el botón
  // "Crear plano desde cero" del sidebar o la página principal).
  window.PlanoEditor = {
    abrir: function (plano) {
      var estado = new Estado(plano);
      iniciar(estado);
    },
    crearEnBlanco: function (presupuestoId, opts) {
      opts = opts || {};
      return fetch(normUrl(API.enBlanco, { presupuesto_id: presupuestoId }), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: opts.nombre || "Plano sin título",
          ancho_lienzo_m: opts.ancho || 12,
          alto_lienzo_m: opts.alto || 8,
          grosor_tabique_cm: opts.grosor || 10,
        }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) throw new Error(data.error || "No se pudo crear el plano.");
          return data;
        });
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
