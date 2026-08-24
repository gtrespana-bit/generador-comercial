/* Editor vectorial de planos desde cero para CotizaT (v2).

   Es un editor de muros libre y profesional:

   * Lienzo infinito con cuadrícula en metros y regla. No se pide largo por
     ancho: el lienzo crece solo cuando dibujas cerca del borde.
   * Grosor de tabique ajustable (10 cm por defecto). Cada tramo de muro se
     guarda como elemento independiente para poder tocarlo luego.
   * Trazas las líneas tú: clic para empezar, clic en cada vértice, doble clic
     / Esc / Enter para terminar. Snap a vértices, ortogonal (Mayús para libre)
     y a cuadrícula, con la medida en metros en vivo.
   * Haz clic sobre un muro y cambia su medida al momento (p. ej. 2,00 → 2,50)
     y el plano se ajusta moviendo los muros conectados.

   Se activa cuando ``window.PLANO_ACTIVO.origen`` es ``dibujado`` (o
   ``mixto``) y existe el contenedor ``#canvas-container``. Renderiza sobre su
   propio lienzo superpuesto y se comunica con el visor principal a través de
   ``window.PlanosAPI`` (lista de mediciones, selección de estancia, análisis).
*/
(function () {
  "use strict";

  var ESCALA_PX_M = 100.0;   // 1 px = 1 cm
  var EPS = 1.5;             // tolerancia (px) para unir vértices
  var API = {
    crear: "/planos/{plano_id}/elementos",
    actualizar: "/planos/{plano_id}/elementos/{elemento_id}",
    eliminar: "/planos/{plano_id}/elementos/{elemento_id}",
    grosor: "/planos/{plano_id}/grosor",
    lienzo: "/planos/{plano_id}/lienzo",
    detectar: "/planos/{plano_id}/detectar",
  };

  function $(id) { return document.getElementById(id); }
  function normUrl(tpl, ctx) {
    return tpl.replace(/\{(\w+)\}/g, function (_, k) { return ctx[k]; });
  }
  function dist(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1]); }
  function cerca(a, b, tol) { return dist(a, b) <= (tol == null ? EPS : tol); }
  function fmt(n, dec) {
    if (n == null || !isFinite(n)) return "—";
    return Number(n).toFixed(dec == null ? 2 : dec).replace(".", ",");
  }

  function Estado(plano) {
    this.plano = plano;
    this.herramienta = "muro";
    this.zoom = 1;
    this.panX = -40;
    this.panY = -40;
    this.grosorCm = plano.grosor_tabique_cm || 10;
    this.elementos = (plano.elementos || []).slice();
    this.mediciones = [];
    this.puntoInicio = null;   // ancla del tramo en curso
    this.primerPunto = null;   // primer punto de la cadena (para cerrar)
    this.cursor = null;        // posición actual en mundo
    this.seleccionado = null;  // id del muro seleccionado
    this.pan = null;           // arrastre de paneo
    this.snap = null;          // {x, y} vértice de snap activo
    this.escala = plano.escala_px_por_metro || ESCALA_PX_M;
  }

  function contenedor() { return $("canvas-container"); }
  function lienzo() {
    var c = document.getElementById("plano-editor-canvas");
    if (!c) {
      c = document.createElement("canvas");
      c.id = "plano-editor-canvas";
      CotizatStyles.setMany(c, {
        position: "absolute", inset: "0", width: "100%", height: "100%",
        pointerEvents: "auto", display: "block",
      });
      var cont = contenedor();
      if (cont) cont.appendChild(c);
    }
    return c;
  }

  function lienzoPx(estado) {
    var anchoM = estado.plano.ancho_lienzo_m || 30;
    var altoM = estado.plano.alto_lienzo_m || 20;
    return { ancho: Math.round(anchoM * estado.escala), alto: Math.round(altoM * estado.escala) };
  }

  // ---------- utilidades de geometría ----------

  function mundoDesdePantalla(estado, cx, cy) {
    return [cx / estado.zoom + estado.panX, cy / estado.zoom + estado.panY];
  }

  function verticesExistentes(estado) {
    var out = [];
    estado.elementos.forEach(function (e) {
      if (e.tipo !== "muro" || !e.puntos) return;
      e.puntos.forEach(function (p) { out.push([p[0], p[1]]); });
    });
    return out;
  }

  function snapPunto(estado, p, fuerzaLibre) {
    var tol = 10 / estado.zoom;
    // 1) Snap a vértices existentes.
    var mejor = null, mejorD = tol;
    verticesExistentes(estado).forEach(function (v) {
      var d = dist(p, v);
      if (d < mejorD) { mejorD = d; mejor = v; }
    });
    if (mejor) return { p: mejor, snap: true };

    // 2) Ortogonal desde el punto anterior (si estamos trazando y no se pide libre).
    if (estado.puntoInicio && !fuerzaLibre) {
      var a = estado.puntoInicio;
      var dx = Math.abs(p[0] - a[0]), dy = Math.abs(p[1] - a[1]);
      if (dx >= dy) p = [p[0], a[1]];
      else p = [a[0], p[1]];
    }

    // 3) Cuadrícula de 5 cm.
    var paso = estado.escala * 0.05;
    var q = [Math.round(p[0] / paso) * paso, Math.round(p[1] / paso) * paso];
    if (dist(p, q) <= (6 / estado.zoom) + 1) return { p: q, snap: false };
    return { p: [p[0], p[1]], snap: false };
  }

  // ---------- render ----------

  function pintarFondo(estado, ctx) {
    var c = lienzo();
    var dpr = window.devicePixelRatio || 1;
    var w = c.clientWidth, h = c.clientHeight;
    if (w <= 0 || h <= 0) return;
    if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) {
      c.width = Math.round(w * dpr);
      c.height = Math.round(h * dpr);
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.setTransform(
      estado.zoom * dpr, 0, 0, estado.zoom * dpr,
      -estado.panX * estado.zoom * dpr, -estado.panY * estado.zoom * dpr
    );

    // Límites visibles en mundo.
    var x0 = estado.panX, y0 = estado.panY;
    var x1 = x0 + w / estado.zoom, y1 = y0 + h / estado.zoom;

    // En un plano dibujado desde cero el lienzo es propio y se pinta la
    // cuadrícula; en uno mixto (imagen + muros) dejamos el lienzo
    // transparente para que se vea la imagen de fondo.
    var esDibujo = estado.plano.origen === "dibujado";
    if (esDibujo) {
      ctx.fillStyle = "#f5f7fa";
      ctx.fillRect(x0 - 2, y0 - 2, (x1 - x0) + 4, (y1 - y0) + 4);
    }

    // Cuadrícula fina (0,1 m) y gruesa (1 m).
    var fino = estado.escala * 0.1, grueso = estado.escala;
    if (esDibujo && fino * estado.zoom >= 6) {
      ctx.strokeStyle = "rgba(148,163,184,0.14)";
      ctx.lineWidth = 1 / estado.zoom;
      ctx.beginPath();
      for (var gx = Math.floor(x0 / fino) * fino; gx <= x1; gx += fino) {
        ctx.moveTo(gx, y0); ctx.lineTo(gx, y1);
      }
      for (var gy = Math.floor(y0 / fino) * fino; gy <= y1; gy += fino) {
        ctx.moveTo(x0, gy); ctx.lineTo(x1, gy);
      }
      ctx.stroke();
    }
    if (esDibujo) {
      ctx.strokeStyle = "rgba(100,116,139,0.30)";
      ctx.lineWidth = 1 / estado.zoom;
      ctx.beginPath();
      for (var gx2 = Math.floor(x0 / grueso) * grueso; gx2 <= x1; gx2 += grueso) {
        ctx.moveTo(gx2, y0); ctx.lineTo(gx2, y1);
      }
      for (var gy2 = Math.floor(y0 / grueso) * grueso; gy2 <= y1; gy2 += grueso) {
        ctx.moveTo(x0, gy2); ctx.lineTo(x1, gy2);
      }
      ctx.stroke();
    }

    // Etiquetas de la regla (cada 1 m), fijas al borde.
    if (esDibujo && grueso * estado.zoom >= 34) {
      ctx.fillStyle = "#64748b";
      ctx.font = (10 / estado.zoom) + "px sans-serif";
      ctx.textBaseline = "top";
      var pista = 12 / estado.zoom;
      for (var rx = Math.max(0, Math.floor(x0 / grueso)) * grueso; rx <= x1; rx += grueso) {
        var met = (rx / estado.escala).toFixed(0);
        ctx.fillText(met, rx + 2 / estado.zoom, y0 + pista);
      }
      ctx.textBaseline = "alphabetic";
      for (var ry = Math.max(0, Math.floor(y0 / grueso)) * grueso; ry <= y1; ry += grueso) {
        var met2 = (ry / estado.escala).toFixed(0);
        ctx.fillText(met2, x0 + pista, ry - 2 / estado.zoom);
      }
    }
  }

  function grosorPx(e, estado) {
    return Math.max(1.5, (e.grosor_cm || estado.grosorCm) / 100.0 * estado.escala);
  }

  function pintarElemento(ctx, e, estado) {
    var pts = e.puntos || [];
    ctx.save();
    if (e.tipo === "muro") {
      if (pts.length < 2) return ctx.restore();
      ctx.strokeStyle = e.color || "#1f2937";
      ctx.lineCap = "butt";
      ctx.lineJoin = "miter";
      ctx.lineWidth = grosorPx(e, estado);
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
      // Medida del tramo (en m).
      if (estado.zoom >= 0.35) {
        var mx = (pts[0][0] + pts[pts.length - 1][0]) / 2;
        var my = (pts[0][1] + pts[pts.length - 1][1]) / 2;
        var dx = pts[pts.length - 1][0] - pts[0][0];
        var dy = pts[pts.length - 1][1] - pts[0][1];
        var largo = Math.hypot(dx, dy) / estado.escala;
        var nx = -dy, ny = dx;
        var nl = Math.hypot(nx, ny) || 1;
        var off = Math.max(14 / estado.zoom, grosorPx(e, estado) / 2 + 5 / estado.zoom);
        var lx = mx + (nx / nl) * off, ly = my + (ny / nl) * off;
        ctx.fillStyle = "#0f172a";
        ctx.font = "500 " + (11 / estado.zoom) + "px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(fmt(largo) + " m", lx, ly);
        ctx.textAlign = "start";
        ctx.textBaseline = "alphabetic";
      }
    } else if (e.tipo === "hueco") {
      var sub = (pts[0] && pts[0][2]) || "puerta";
      var cxp = pts[0][0], cyp = pts[0][1];
      var an = (pts[0][3] || 90) / 100 * estado.escala;
      var al = (pts[0][4] || 20) / 100 * estado.escala;
      ctx.fillStyle = sub === "puerta" ? "rgba(244,114,182,0.55)" : "rgba(56,189,248,0.55)";
      ctx.strokeStyle = sub === "puerta" ? "#db2777" : "#0284c7";
      ctx.lineWidth = 1.4 / estado.zoom;
      ctx.beginPath();
      ctx.rect(cxp - an / 2, cyp - al / 2, an, al);
      ctx.fill();
      ctx.stroke();
    }
    ctx.restore();
  }

  function pintarMedicion(ctx, m, estado) {
    var pts = m.puntos || [];
    if (pts.length < 3) return;
    var color = m.color || "#2563eb";
    ctx.save();
    ctx.fillStyle = color + "2e";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2 / estado.zoom;
    ctx.beginPath();
    pts.forEach(function (p, i) { if (i === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]); });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    if (pts[0] && m.metricas && m.metricas.calibrado) {
      var label = (m.etiqueta || "Estancia") + " · " + fmt(m.metricas.suelo) + " m²";
      ctx.fillStyle = "#0f172a";
      ctx.font = "600 " + (12 / estado.zoom) + "px Inter, sans-serif";
      ctx.fillText(label, pts[0][0] + 6 / estado.zoom, pts[0][1] - 6 / estado.zoom);
    }
    ctx.restore();
  }

  function pintarTrazo(estado, ctx) {
    var e = estado;
    if (e.snap) {
      ctx.save();
      ctx.strokeStyle = "#2563eb";
      ctx.lineWidth = 2 / e.zoom;
      ctx.beginPath();
      ctx.arc(e.snap[0], e.snap[1], 7 / e.zoom, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
    if (!e.puntoInicio || !e.cursor) return;
    var a = e.puntoInicio;
    var b = e.cursor;
    if (e.snap) b = e.snap;
    ctx.save();
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = grosorPx({ grosor_cm: e.grosorCm }, e);
    ctx.setLineDash([6 / e.zoom, 4 / e.zoom]);
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0], b[1]);
    ctx.stroke();
    ctx.setLineDash([]);
    // Medida en vivo.
    var largo = dist(a, b) / e.escala;
    ctx.fillStyle = "#0f172a";
    ctx.font = "600 " + (12 / e.zoom) + "px Inter, sans-serif";
    var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    ctx.fillText(fmt(largo) + " m", mx + 8 / e.zoom, my - 8 / e.zoom);
    ctx.beginPath();
    ctx.arc(a[0], a[1], 4 / e.zoom, 0, Math.PI * 2);
    ctx.fillStyle = "#2563eb";
    ctx.fill();
    ctx.restore();
  }

  function pintarSeleccion(estado, ctx) {
    var sel = null;
    estado.elementos.forEach(function (e) {
      if (e.id === estado.seleccionado && e.tipo === "muro") sel = e;
    });
    if (!sel || sel.puntos.length < 2) return;
    ctx.save();
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 3 / estado.zoom;
    ctx.beginPath();
    ctx.moveTo(sel.puntos[0][0], sel.puntos[0][1]);
    ctx.lineTo(sel.puntos[1][0], sel.puntos[1][1]);
    ctx.stroke();
    // Asas en los extremos.
    ctx.fillStyle = "#fff";
    ctx.lineWidth = 2 / estado.zoom;
    sel.puntos.forEach(function (p) {
      ctx.beginPath();
      ctx.arc(p[0], p[1], 6 / estado.zoom, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });
    ctx.restore();
  }

  function render(estado) {
    var c = lienzo();
    var ctx = c.getContext("2d");
    pintarFondo(estado, ctx);
    estado.elementos.forEach(function (e) { pintarElemento(ctx, e, estado); });
    estado.mediciones.forEach(function (m) { pintarMedicion(ctx, m, estado); });
    pintarSeleccion(estado, ctx);
    pintarTrazo(estado, ctx);
  }

  // ---------- persistencia ----------

  function pedirJson(url, metodo, body) {
    return fetch(url, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); });
  }

  function persistirGrosor(estado) {
    return pedirJson(normUrl(API.grosor, { plano_id: estado.plano.id }), "POST", {
      grosor_tabique_cm: estado.grosorCm,
    }).then(function (res) {
      if (res.ok && res.data && res.data.ok) {
        estado.grosorCm = res.data.grosor_tabique_cm;
        estado.plano.grosor_tabique_cm = res.data.grosor_tabique_cm;
      }
    }).catch(function () {});
  }

  function guardarMuro(estado, pts, grosorCm) {
    return pedirJson(normUrl(API.crear, { plano_id: estado.plano.id }), "POST", {
      tipo: "muro", puntos: pts, grosor_cm: grosorCm, color: "#1f2937",
    }).then(function (res) {
      if (!res.ok || !res.data || !res.data.ok) {
        throw new Error((res.data && res.data.error) || "No se pudo guardar el muro.");
      }
      return res.data.elemento;
    });
  }

  function guardarHueco(estado, pts, sub) {
    return pedirJson(normUrl(API.crear, { plano_id: estado.plano.id }), "POST", {
      tipo: "hueco", puntos: pts, grosor_cm: 0,
      color: sub === "puerta" ? "#db2777" : "#0284c7",
    }).then(function (res) {
      if (!res.ok || !res.data || !res.data.ok) {
        throw new Error((res.data && res.data.error) || "No se pudo guardar el hueco.");
      }
      return res.data.elemento;
    });
  }

  function actualizarElemento(estado, id, pts, grosorCm) {
    return pedirJson(normUrl(API.actualizar, { plano_id: estado.plano.id, elemento_id: id }), "PUT", {
      puntos: pts, grosor_cm: grosorCm,
    }).then(function (res) {
      if (!res.ok || !res.data || !res.data.ok) {
        throw new Error((res.data && res.data.error) || "No se pudo actualizar.");
      }
      return res.data.elemento;
    });
  }

  function eliminarElemento(estado, id) {
    return pedirJson(normUrl(API.eliminar, { plano_id: estado.plano.id, elemento_id: id }), "DELETE")
      .catch(function () {});
  }

  function ampliarLienzo(estado) {
    var dims = lienzoPx(estado);
    var anchoM = estado.plano.ancho_lienzo_m || 30;
    var altoM = estado.plano.alto_lienzo_m || 20;
    var margen = 2.0; // crece cuando dibujas a menos de 2 m del borde
    var crecio = false;
    if (estado.cursor && estado.cursor[0] > dims.ancho - margen * estado.escala) {
      anchoM += 10; crecio = true;
    }
    if (estado.cursor && estado.cursor[1] > dims.alto - margen * estado.escala) {
      altoM += 10; crecio = true;
    }
    if (estado.cursor && estado.cursor[0] < margen * estado.escala) {
      // no encogemos por la izquierda; el usuario puede mover el paneo
    }
    if (!crecio) return;
    estado.plano.ancho_lienzo_m = anchoM;
    estado.plano.alto_lienzo_m = altoM;
    pedirJson(normUrl(API.lienzo, { plano_id: estado.plano.id }), "POST", {
      ancho_lienzo_m: anchoM, alto_lienzo_m: altoM,
    }).catch(function () {});
  }

  // ---------- redimensionar un muro (y ajustar el plano) ----------

  function muroPorId(estado, id) {
    for (var i = 0; i < estado.elementos.length; i++) {
      if (estado.elementos[i].id === id) return estado.elementos[i];
    }
    return null;
  }

  function propagarCambio(estado, verticeOld, delta, u, ancla, origenId, cambios) {
    estado.elementos.forEach(function (w) {
      if (w.id === origenId || w.tipo !== "muro" || w.puntos.length < 2) return;
      if (cambios.some(function (c) { return c.id === w.id; })) return;
      var pa = [w.puntos[0][0], w.puntos[0][1]];
      var pb = [w.puntos[1][0], w.puntos[1][1]];
      var enA = cerca(pa, verticeOld), enB = cerca(pb, verticeOld);
      if (!enA && !enB) return;

      var wdx = pb[0] - pa[0], wdy = pb[1] - pa[1];
      var wl = Math.hypot(wdx, wdy) || 1;
      var dot = Math.abs((wdx / wl) * u[0] + (wdy / wl) * u[1]);
      var perpendicular = dot < 0.3;

      function mover(p) {
        var q = [p[0] + delta[0], p[1] + delta[1]];
        if (cerca(q, ancla, EPS)) return [ancla[0], ancla[1]]; // no mover el ancla
        return q;
      }

      var npa, npb;
      if (enA) {
        npa = mover(pa);
        npb = perpendicular ? mover(pb) : [pb[0], pb[1]];
      } else {
        npb = mover(pb);
        npa = perpendicular ? mover(pa) : [pa[0], pa[1]];
      }
      cambios.push({ id: w.id, puntos: [npa, npb] });
      if (perpendicular) {
        var far = enA ? pb : pa;
        if (!cerca(far, ancla, EPS)) propagarCambio(estado, far, delta, u, ancla, w.id, cambios);
      }
    });
  }

  function redimensionarMuro(estado, muro, nuevaLongitudM) {
    var pts = muro.puntos;
    var a = [pts[0][0], pts[0][1]];
    var b = [pts[1][0], pts[1][1]];
    var dx = b[0] - a[0], dy = b[1] - a[1];
    var lenPx = Math.hypot(dx, dy) || 1;
    var nuevaLenPx = nuevaLongitudM * estado.escala;
    var delta = nuevaLenPx - lenPx;
    if (Math.abs(delta) < 0.5) return [];
    var u = [dx / lenPx, dy / lenPx];
    var dd = [u[0] * delta, u[1] * delta];
    var nuevoB = [b[0] + dd[0], b[1] + dd[1]];
    var cambios = [{ id: muro.id, puntos: [[a[0], a[1]], nuevoB] }];
    propagarCambio(estado, b, dd, u, a, muro.id, cambios);
    return cambios;
  }

  function aplicarRedimension(estado, muro, nuevaLongitudM) {
    var cambios = redimensionarMuro(estado, muro, nuevaLongitudM);
    var promesas = cambios.map(function (c) {
      var grosor = muroPorId(estado, c.id) ? muroPorId(estado, c.id).grosor_cm : estado.grosorCm;
      return actualizarElemento(estado, c.id, c.puntos, grosor).then(function (elem) {
        var local = muroPorId(estado, c.id);
        if (local) {
          local.puntos = elem.puntos;
          local.grosor_cm = elem.grosor_cm;
        }
        return elem;
      });
    });
    return Promise.all(promesas).then(function () {
      render(estado);
      actualizarCarta(estado);
    });
  }

  // ---------- UI flotante ----------

  function construirUI(estado) {
    if ($("plano-editor-panel")) return;
    var cont = contenedor();
    if (!cont) return;

    var panel = document.createElement("div");
    panel.id = "plano-editor-panel";
    panel.className = "plano-editor-panel";

    var head = document.createElement("header");
    head.className = "plano-editor-head";
    var t = document.createElement("strong");
    t.textContent = "Editor de planos";
    var ayuda = document.createElement("span");
    ayuda.id = "plano-editor-ayuda";
    ayuda.className = "plano-editor-ayuda";
    head.appendChild(t);
    head.appendChild(ayuda);

    var tools = document.createElement("div");
    tools.className = "plano-editor-tools";
    [
      ["muro", "＋ Muro", true],
      ["seleccionar", "↖ Seleccionar", false],
      ["puerta", "Puerta", false],
      ["ventana", "Ventana", false],
    ].forEach(function (h) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "plano-editor-tool" + (h[2] ? " active" : "");
      b.dataset.herr = h[0];
      b.textContent = h[1];
      tools.appendChild(b);
    });

    var grosor = document.createElement("div");
    grosor.className = "plano-editor-grosor";
    var gl = document.createElement("label");
    gl.textContent = "Grosor del tabique ";
    var go = document.createElement("output");
    go.id = "plano-editor-grosor-valor";
    go.textContent = "10 cm";
    gl.appendChild(go);
    var gr = document.createElement("input");
    gr.type = "range";
    gr.id = "plano-editor-grosor";
    gr.min = "3"; gr.max = "40"; gr.step = "0.5"; gr.value = "10";
    grosor.appendChild(gl);
    grosor.appendChild(gr);

    var acciones = document.createElement("div");
    acciones.className = "plano-editor-acciones";
    [
      ["plano-editor-detectar", "✨ Detectar estancias"],
      ["plano-editor-ayuda-boton", "¿Cómo se usa?"],
    ].forEach(function (cfg) {
      var b = document.createElement("button");
      b.type = "button";
      b.id = cfg[0];
      b.className = "btn btn-sm";
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
        panel.querySelectorAll("[data-herr]").forEach(function (o) {
          o.classList.toggle("active", o === b);
        });
        if (estado.herramienta !== "muro") estado.puntoInicio = estado.primerPunto = null;
        if (estado.herramienta !== "seleccionar") {
          estado.seleccionado = null;
          ocultarCarta();
        }
        actualizarAyuda(estado);
        render(estado);
      });
    });

    var grosorRange = $("plano-editor-grosor");
    grosorRange.value = String(estado.grosorCm);
    grosorRange.addEventListener("input", function () {
      var v = parseFloat(grosorRange.value);
      if (isFinite(v) && v > 0) {
        estado.grosorCm = v;
        actualizarAyuda(estado);
        persistirGrosor(estado);
        render(estado);
      }
    });

    $("plano-editor-detectar").addEventListener("click", function () {
      detectarEstancias(estado);
    });
    $("plano-editor-ayuda-boton").addEventListener("click", function () {
      alert(
        "Muro: clic para empezar, clic en cada vértice, doble clic / Enter / Esc para terminar.\n" +
        "Mayús + clic: línea libre (sin ortogonal).\n" +
        "Seleccionar: clic sobre un muro para cambiar su medida o su grosor; Supr para borrarlo.\n" +
        "Rueda: zoom. Arrastra con el botón central o la barra espaciadora: mover el lienzo."
      );
    });

    // Carta flotante de edición de medida.
    var carta = document.createElement("div");
    carta.id = "plano-editor-carta";
    carta.className = "plano-editor-carta cotizat-hidden";
    var cl = document.createElement("label");
    cl.textContent = "Longitud (m)";
    var ci = document.createElement("input");
    ci.type = "number";
    ci.id = "plano-editor-carta-long";
    ci.step = "0.01";
    ci.min = "0.1";
    var cg = document.createElement("label");
    cg.textContent = "Grosor (cm)";
    var cgi = document.createElement("input");
    cgi.type = "number";
    cgi.id = "plano-editor-carta-grosor";
    cgi.step = "0.5";
    cgi.min = "3";
    cgi.max = "40";
    var cbotones = document.createElement("div");
    cbotones.className = "plano-editor-carta-botones";
    var bAplicar = document.createElement("button");
    bAplicar.type = "button";
    bAplicar.id = "plano-editor-carta-aplicar";
    bAplicar.className = "btn btn-sm btn-primary";
    bAplicar.textContent = "Aplicar";
    var bBorrar = document.createElement("button");
    bBorrar.type = "button";
    bBorrar.id = "plano-editor-carta-borrar";
    bBorrar.className = "btn btn-sm btn-danger";
    bBorrar.textContent = "Borrar";
    var bCerrar = document.createElement("button");
    bCerrar.type = "button";
    bCerrar.id = "plano-editor-carta-cerrar";
    bCerrar.className = "btn btn-sm";
    bCerrar.textContent = "✕";
    cbotones.appendChild(bAplicar);
    cbotones.appendChild(bBorrar);
    cbotones.appendChild(bCerrar);
    carta.appendChild(cl);
    carta.appendChild(ci);
    carta.appendChild(cg);
    carta.appendChild(cgi);
    carta.appendChild(cbotones);
    cont.appendChild(carta);

    ci.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); bAplicar.click(); }
    });
    bAplicar.addEventListener("click", function () {
      var muro = estado.seleccionado != null ? muroPorId(estado, estado.seleccionado) : null;
      if (!muro) return;
      var largo = parseFloat(ci.value);
      if (!isFinite(largo) || largo <= 0) { alert("Medida no válida."); return; }
      aplicarRedimension(estado, muro, largo).catch(function (err) { alert(err.message); });
    });
    bBorrar.addEventListener("click", function () {
      var id = estado.seleccionado;
      if (id == null) return;
      if (!confirm("¿Borrar este muro?")) return;
      eliminarElemento(estado, id).then(function () {
        estado.elementos = estado.elementos.filter(function (e) { return e.id !== id; });
        estado.seleccionado = null;
        ocultarCarta();
        render(estado);
      });
    });
    bCerrar.addEventListener("click", function () {
      estado.seleccionado = null;
      ocultarCarta();
      render(estado);
    });
  }

  function actualizarAyuda(estado) {
    var ayuda = $("plano-editor-ayuda");
    if (!ayuda) return;
    var msg = {
      muro: "Muro: clic para empezar · clic en cada vértice · doble clic para terminar · Mayús = línea libre",
      seleccionar: "Seleccionar: clic en un muro para cambiar su medida o grosor · Supr borra",
      puerta: "Puerta: clic sobre un muro para colocar un hueco de 90 cm",
      ventana: "Ventana: clic sobre un muro para colocar un hueco de 120 cm",
    }[estado.herramienta] || "";
    ayuda.textContent = msg;
    var go = $("plano-editor-grosor-valor");
    if (go) go.textContent = (estado.grosorCm || 10).toFixed(1).replace(".", ",") + " cm";
  }

  function mostrarCarta(estado, muro) {
    var carta = $("plano-editor-carta");
    if (!carta) return;
    CotizatStyles.set(carta, "display", "block");
    var ci = $("plano-editor-carta-long");
    var cgi = $("plano-editor-carta-grosor");
    if (ci) {
      var p0 = muro.puntos[0], p1 = muro.puntos[1];
      var largo = dist(p0, p1) / estado.escala;
      ci.value = largo.toFixed(2);
    }
    if (cgi) cgi.value = String(muro.grosor_cm || estado.grosorCm);

    // Posiciona la carta junto al punto medio del muro (en pantalla).
    var c = lienzo();
    var mx = (muro.puntos[0][0] + muro.puntos[1][0]) / 2;
    var my = (muro.puntos[0][1] + muro.puntos[1][1]) / 2;
    var sx = (mx - estado.panX) * estado.zoom;
    var sy = (my - estado.panY) * estado.zoom;
    CotizatStyles.set(carta, "left", Math.max(6, Math.min(sx, c.clientWidth - 240)) + "px");
    CotizatStyles.set(carta, "top", Math.max(6, Math.min(sy + 18, c.clientHeight - 200)) + "px");

    $("plano-editor-carta-grosor").oninput = function () {
      var v = parseFloat(cgi.value);
      if (!isFinite(v) || v < 3 || v > 40) return;
      actualizarElemento(estado, muro.id, muro.puntos, v).then(function (elem) {
        muro.grosor_cm = elem.grosor_cm;
        render(estado);
      }).catch(function () {});
    };
  }

  function ocultarCarta() {
    var carta = $("plano-editor-carta");
    if (carta) CotizatStyles.set(carta, "display", "none");
  }

  function actualizarCarta(estado) {
    if (estado.seleccionado == null) return;
    var muro = muroPorId(estado, estado.seleccionado);
    if (muro) mostrarCarta(estado, muro);
  }

  // ---------- detección de estancias ----------

  function detectarEstancias(estado) {
    var btn = $("plano-editor-detectar");
    if (btn) { btn.disabled = true; btn.textContent = "Detectando…"; }
    pedirJson(normUrl(API.detectar, { plano_id: estado.plano.id }), "POST")
      .then(function (res) {
        if (!res.ok || !res.data || !res.data.ok) {
          throw new Error((res.data && res.data.error) || "No se pudo analizar el plano.");
        }
        return res.data;
      })
      .then(function (data) {
        return refrescarMediciones(estado).then(function (meds) {
          var msg;
          if ((data.nuevas || 0) === 0 && (data.omitidas || 0) > 0) {
            msg = "Las estancias ya estaban detectadas.";
          } else {
            msg = (data.nuevas || 0) + " estancia(s) detectada(s).";
          }
          if (btn) btn.textContent = "✨ Detectar estancias";
          return { meds: meds, msg: msg };
        });
      })
      .then(function (r) {
        if (window.PlanosAPI && window.PlanosAPI.aviso) window.PlanosAPI.aviso(r.msg, "ok");
        var primera = r.meds.find(function (m) { return m.tipo === "area"; });
        if (primera && window.PlanosAPI && window.PlanosAPI.seleccionarEstancia) {
          window.PlanosAPI.seleccionarEstancia(primera);
        }
      })
      .catch(function (err) {
        if (window.PlanosAPI && window.PlanosAPI.aviso) window.PlanosAPI.aviso(err.message, "error");
      })
      .finally(function () {
        if (btn) { btn.disabled = false; if (btn.textContent === "Detectando…") btn.textContent = "✨ Detectar estancias"; }
      });
  }

  function refrescarMediciones(estado) {
    if (window.PlanosAPI && window.PlanosAPI.refrescar) {
      return window.PlanosAPI.refrescar().then(function (meds) {
        estado.mediciones = meds || [];
        render(estado);
        return estado.mediciones;
      });
    }
    return Promise.resolve(estado.mediciones || []);
  }

  // ---------- eventos ----------

  function muroEnPunto(estado, p) {
    var tol = 12 / estado.zoom;
    var mejor = null, mejorD = tol;
    estado.elementos.forEach(function (e) {
      if (e.tipo !== "muro" || e.puntos.length < 2) return;
      var a = e.puntos[0], b = e.puntos[1];
      var dx = b[0] - a[0], dy = b[1] - a[1];
      var l2 = dx * dx + dy * dy;
      var t = l2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2)) : 0;
      var qx = a[0] + t * dx, qy = a[1] + t * dy;
      var d = dist(p, [qx, qy]);
      if (d < mejorD) { mejorD = d; mejor = e; }
    });
    return mejor;
  }

  function medicionEnPunto(estado, p) {
    var areas = estado.mediciones.filter(function (m) {
      return m.tipo === "area" && (m.puntos || []).length >= 3;
    });
    areas.sort(function (a, b) { return areaPx(a) - areaPx(b); });
    for (var i = 0; i < areas.length; i++) {
      if (puntoEnPoligono(p, areas[i].puntos)) return areas[i];
    }
    return null;
  }

  function areaPx(m) {
    var pts = m.puntos || [];
    if (pts.length < 3) return 0;
    var s = 0;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i], q = pts[(i + 1) % pts.length];
      s += p[0] * q[1] - q[0] * p[1];
    }
    return Math.abs(s) / 2;
  }

  function puntoEnPoligono(p, poly) {
    var inside = false;
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      var xi = poly[i][0], yi = poly[i][1], xj = poly[j][0], yj = poly[j][1];
      if (((yi > p[1]) !== (yj > p[1])) && (p[0] < (xj - xi) * (p[1] - yi) / ((yj - yi) || 1e-12) + xi)) {
        inside = !inside;
      }
    }
    return inside;
  }

  function onClick(estado, ev) {
    var c = lienzo();
    var rect = c.getBoundingClientRect();
    var cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
    var mundo = mundoDesdePantalla(estado, cx, cy);
    var herr = estado.herramienta;

    if (herr === "muro") {
      var r = snapPunto(estado, mundo, ev.shiftKey);
      var p = r.p;
      if (!estado.puntoInicio) {
        estado.puntoInicio = p;
        estado.primerPunto = p.slice();
      } else {
        // cierre de cadena: si cae sobre el primer punto, cierra.
        if (cerca(p, estado.primerPunto, 10 / estado.zoom)) {
          guardarMuro(estado, [estado.puntoInicio.slice(), estado.primerPunto.slice()], estado.grosorCm)
            .then(function (elem) { estado.elementos.push(elem); render(estado); })
            .catch(function (err) { alert(err.message); });
          estado.puntoInicio = estado.primerPunto = null;
        } else if (dist(p, estado.puntoInicio) > 1) {
          var ini = estado.puntoInicio.slice();
          var destino = p.slice();
          estado.puntoInicio = destino; // continúa la cadena sin esperar a la red
          guardarMuro(estado, [ini, destino], estado.grosorCm)
            .then(function (elem) {
              estado.elementos.push(elem);
              ampliarLienzo(estado);
              render(estado);
            })
            .catch(function (err) { alert(err.message); });
        }
      }
      return;
    }

    if (herr === "seleccionar") {
      var muro = muroEnPunto(estado, mundo);
      if (muro) {
        estado.seleccionado = muro.id;
        mostrarCarta(estado, muro);
      } else {
        var med = medicionEnPunto(estado, mundo);
        if (med && window.PlanosAPI && window.PlanosAPI.seleccionarEstancia) {
          window.PlanosAPI.seleccionarEstancia(med);
        }
        estado.seleccionado = null;
        ocultarCarta();
      }
      render(estado);
      return;
    }

    if (herr === "puerta" || herr === "ventana") {
      var m = muroEnPunto(estado, mundo);
      if (!m || m.puntos.length < 2) return;
      var sub = herr;
      var anchoCm = herr === "puerta" ? 90 : 120;
      guardarHueco(estado, [[mundo[0], mundo[1], sub, anchoCm, 20]], sub)
        .then(function (elem) { estado.elementos.push(elem); render(estado); })
        .catch(function (err) { alert(err.message); });
      return;
    }
  }

  function onDblClick(estado) {
    if (estado.herramienta === "muro") {
      estado.puntoInicio = estado.primerPunto = null;
      render(estado);
    }
  }

  function onKeyDown(estado, ev) {
    if (ev.key === "Escape") {
      estado.puntoInicio = estado.primerPunto = null;
      estado.seleccionado = null;
      ocultarCarta();
      render(estado);
      return;
    }
    if (ev.key === "Enter") {
      estado.puntoInicio = estado.primerPunto = null;
      render(estado);
      return;
    }
    if ((ev.key === "Delete" || ev.key === "Backspace") && estado.seleccionado != null) {
      var id = estado.seleccionado;
      if (!confirm("¿Borrar este muro?")) return;
      eliminarElemento(estado, id).then(function () {
        estado.elementos = estado.elementos.filter(function (e) { return e.id !== id; });
        estado.seleccionado = null;
        ocultarCarta();
        render(estado);
      });
      return;
    }
    if (ev.key.toLowerCase() === "m") { cambiarHerramienta(estado, "muro"); }
    if (ev.key.toLowerCase() === "s") { cambiarHerramienta(estado, "seleccionar"); }
  }

  function cambiarHerramienta(estado, h) {
    estado.herramienta = h;
    var panel = $("plano-editor-panel");
    if (panel) {
      panel.querySelectorAll("[data-herr]").forEach(function (b) {
        b.classList.toggle("active", b.dataset.herr === h);
      });
    }
    if (h !== "muro") estado.puntoInicio = estado.primerPunto = null;
    if (h !== "seleccionar") { estado.seleccionado = null; ocultarCarta(); }
    actualizarAyuda(estado);
    render(estado);
  }

  function iniciar(estado) {
    construirUI(estado);
    var c = lienzo();
    var cont = contenedor();

    c.addEventListener("click", function (ev) { onClick(estado, ev); });
    c.addEventListener("dblclick", function (ev) { ev.preventDefault(); onDblClick(estado); });
    c.addEventListener("contextmenu", function (ev) {
      ev.preventDefault();
      estado.puntoInicio = estado.primerPunto = null;
      render(estado);
    });

    c.addEventListener("mousemove", function (ev) {
      var rect = c.getBoundingClientRect();
      var cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
      estado.cursor = mundoDesdePantalla(estado, cx, cy);
      if (estado.pan) {
        estado.panX = estado.pan.mundoX0 - cx / estado.zoom;
        estado.panY = estado.pan.mundoY0 - cy / estado.zoom;
        render(estado);
        return;
      }
      // snap visual
      if (estado.herramienta === "muro" && estado.puntoInicio) {
        var r = snapPunto(estado, estado.cursor, ev.shiftKey);
        estado.snap = r.snap ? r.p : null;
      } else {
        estado.snap = null;
      }
      render(estado);
    });
    c.addEventListener("mouseleave", function () {
      estado.cursor = null;
      estado.snap = null;
      render(estado);
    });

    c.addEventListener("mousedown", function (ev) {
      if (ev.button === 1 || (ev.button === 0 && (ev.shiftKey && estado.herramienta !== "muro"))) {
        ev.preventDefault();
        var rect = c.getBoundingClientRect();
        estado.pan = {
          mundoX0: estado.panX + (ev.clientX - rect.left) / estado.zoom,
          mundoY0: estado.panY + (ev.clientY - rect.top) / estado.zoom,
        };
      }
    });
    window.addEventListener("mouseup", function () { estado.pan = null; });

    c.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      var rect = c.getBoundingClientRect();
      var cx = ev.clientX - rect.left, cy = ev.clientY - rect.top;
      var mundoAntes = mundoDesdePantalla(estado, cx, cy);
      var factor = ev.deltaY < 0 ? 1.15 : 1 / 1.15;
      var nuevoZoom = Math.min(10, Math.max(0.15, estado.zoom * factor));
      estado.zoom = nuevoZoom;
      estado.panX = mundoAntes[0] - cx / estado.zoom;
      estado.panY = mundoAntes[1] - cy / estado.zoom;
      render(estado);
    }, { passive: false });

    document.addEventListener("keydown", function (ev) {
      var t = (ev.target && ev.target.tagName) || "";
      if (["INPUT", "SELECT", "TEXTAREA"].includes(t)) return;
      onKeyDown(estado, ev);
    });

    window.addEventListener("resize", function () { render(estado); });

    // Mediciones iniciales desde el puente.
    refrescarMediciones(estado);
    actualizarAyuda(estado);
    render(estado);
  }

  function init() {
    if (typeof window === "undefined" || !window.PLANO_ACTIVO) return;
    var plano = window.PLANO_ACTIVO;
    if (plano.origen !== "dibujado" && plano.origen !== "mixto") return;
    if (!document.getElementById("canvas-container")) return;
    var estado = new Estado(plano);
    iniciar(estado);
    window.PlanoEditor = { estado: estado };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
