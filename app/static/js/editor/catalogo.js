/* ============================================================================
   Editor — Catálogo inteligente

   - Autocompletado contextual con score
   - Sugerencias basadas en cliente/tipo de obra
   - Detección de patrones frecuentes
   - Indicador de diferencia vs catálogo al editar precio
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR;
  var fichasCache = Object.create(null);
  var peticionesFicha = Object.create(null);
  var peticionesBusqueda = Object.create(null);
  var busquedasVaciasRegistradas = Object.create(null);

  function fusionarEnIndice(partida) {
    var indice = (editor.CATALOGO || []).findIndex(function (p) {
      return Number(p.id) === Number(partida.id);
    });
    if (indice < 0) {
      partida._detalle_cargado = true;
      editor.CATALOGO.push(partida);
      return partida;
    }
    Object.assign(editor.CATALOGO[indice], partida, { _detalle_cargado: true });
    return editor.CATALOGO[indice];
  }

  // Contexto monetario del editor: el catálogo se guarda en la moneda base y
  // el presupuesto puede estar en otra. Se envía en cada petición para que el
  // servidor convierta en la dirección correcta (al leer y al guardar).
  function contextoMoneda() {
    var params = [];
    if (window.COTIZAT_MONEDA_ACTIVA) {
      params.push("moneda=" + encodeURIComponent(window.COTIZAT_MONEDA_ACTIVA));
    }
    if (window.COTIZAT_TASA_ACTIVA) {
      params.push("tasa=" + encodeURIComponent(window.COTIZAT_TASA_ACTIVA));
    }
    return params.join("&");
  }

  function conContexto(url) {
    var extra = contextoMoneda();
    if (!extra) return url;
    return url + (url.indexOf("?") === -1 ? "?" : "&") + extra;
  }

  window.CotizatContextoMoneda = {
    query: contextoMoneda,
    url: conContexto,
    moneda: function () { return window.COTIZAT_MONEDA_ACTIVA || "USD"; },
    tasa: function () { return window.COTIZAT_TASA_ACTIVA || ""; }
  };

  function obtenerFicha(indiceOItem) {
    var item = typeof indiceOItem === "number"
      ? (editor.CATALOGO || [])[indiceOItem]
      : indiceOItem;
    if (!item || !item.id) return Promise.reject(new Error("Partida no disponible"));
    var id = String(item.id);
    if (item._detalle_cargado || Object.prototype.hasOwnProperty.call(item, "descomposicion")) {
      item._detalle_cargado = true;
      fichasCache[id] = item;
      return Promise.resolve(item);
    }
    if (fichasCache[id]) return Promise.resolve(fichasCache[id]);
    if (peticionesFicha[id]) return peticionesFicha[id];
    peticionesFicha[id] = fetch(conContexto("/partidas/" + encodeURIComponent(id) + "/ficha"), {
      headers: { "Accept": "application/json" }
    })
      .then(function (respuesta) {
        if (!respuesta.ok) throw new Error("No se pudo cargar la partida");
        return respuesta.json();
      })
      .then(function (datos) {
        if (!datos.ok || !datos.partida) throw new Error(datos.error || "Ficha no disponible");
        var completa = fusionarEnIndice(datos.partida);
        fichasCache[id] = completa;
        delete peticionesFicha[id];
        return completa;
      })
      .catch(function (error) {
        delete peticionesFicha[id];
        throw error;
      });
    return peticionesFicha[id];
  }

  function buscarRemoto(texto, limite) {
    var consulta = String(texto || "").trim();
    if (consulta.length < 2) return Promise.resolve([]);
    var clave = consulta.toLowerCase() + "|" + String(limite || 60);
    if (peticionesBusqueda[clave]) return peticionesBusqueda[clave];
    peticionesBusqueda[clave] = fetch(
      conContexto(
        "/partidas/api/buscar?q=" + encodeURIComponent(consulta) +
        "&limite=" + encodeURIComponent(limite || 60)
      ),
      { headers: { "Accept": "application/json" } }
    )
      .then(function (respuesta) {
        if (!respuesta.ok) throw new Error("No se pudo buscar en el catálogo");
        return respuesta.json();
      })
      .then(function (datos) {
        var porId = Object.create(null);
        (editor.CATALOGO || []).forEach(function (item) { porId[String(item.id)] = item; });
        var salida = (datos.resultados || []).map(function (resultado) {
          var existente = porId[String(resultado.id)];
          if (existente) {
            Object.assign(existente, resultado);
            return existente;
          }
          editor.CATALOGO.push(resultado);
          return resultado;
        });
        return salida;
      })
      .catch(function () { return []; });
    return peticionesBusqueda[clave];
  }

  function registrarSinResultados(texto) {
    var consulta = String(texto || "").trim();
    var clave = consulta.toLowerCase();
    if (consulta.length < 2 || busquedasVaciasRegistradas[clave]) return;
    busquedasVaciasRegistradas[clave] = true;
    fetch("/partidas/api/busqueda-sin-resultados", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ q: consulta })
    }).catch(function () {});
  }

  // -------------------------------------------------------------------------
  // Catálogo de partidas — buscador
  // -------------------------------------------------------------------------

  function initCatalogo() {
    var buscador = document.getElementById("buscar-partida");
    var catalogoPanel = document.getElementById("catalogo-partidas");

    if (buscador && catalogoPanel) {
      // Abrir panel al hacer focus
      buscador.addEventListener("focus", function () {
        catalogoPanel.classList.add("open");
        // Cargar sugerencias inteligentes contextuales
        cargarSugerenciasContextuales();
      });

      buscador.addEventListener("input", function () {
        var f = buscador.value.toLowerCase().trim();
        if (!f) {
          // If empty, show suggestions
          cargarSugerenciasContextuales();
          catalogoPanel.classList.remove("open");
          return;
        }
        catalogoPanel.classList.add("open");

        // Buscar en todo el catálogo usando CATALOGO_UTILS si está disponible,
        // o filtrado manual
        var matches = [];
        if (editor.CATALOGO_UTILS && editor.CATALOGO_UTILS.buscarEnCatalogo) {
          matches = editor.CATALOGO_UTILS.buscarEnCatalogo(
            editor.CATALOGO,
            f,
            ["nombre", "buscable", "categoria", "subcategoria", "apartado", "codigo", "codigo_legacy"],
            ""
          );
        } else {
          // Fallback
          matches = editor.CATALOGO.filter(function(item) {
             var t = ((item.nombre||"") + " " + (item.categoria||"")).toLowerCase();
             return t.indexOf(f) !== -1;
          }).slice(0, 50);
        }
        
        renderizarSugerencias(matches);
      });

      // Cerrar al hacer clic fuera
      document.addEventListener("click", function (e) {
        if (!catalogoPanel.contains(e.target) && e.target !== buscador) {
          catalogoPanel.classList.remove("open");
        }
      });
    }
  }

  // -------------------------------------------------------------------------
  // Sugerencias inteligentes contextuales
  // -------------------------------------------------------------------------

  function cargarSugerenciasContextuales() {
    // Obtener contexto del cliente si existe
    var clienteId = editor.BUDGET_ID ? obtenerClienteIdDelPresupuesto() : null;
    var tipoObra = obtenerTipoObraDelPresupuesto();

    // Ordenar catálogo por relevancia contextual
    var ordenado = editor.CATALOGO.slice().sort(function (a, b) {
      var scoreA = (a.usos || 0) * 2;
      var scoreB = (b.usos || 0) * 2;

      // Bonus por última vez usado
      if (a.ultimo_uso) scoreA += 15;
      if (b.ultimo_uso) scoreB += 15;

      // Bonus por categoría contextual
      if (tipoObra && a.categoria === tipoObra) scoreA += 25;
      if (tipoObra && b.categoria === tipoObra) scoreB += 25;

      return scoreB - scoreA;
    }).slice(0, 15);

    renderizarSugerencias(ordenado);
  }

  function obtenerClienteIdDelPresupuesto() {
    var select = document.querySelector('select[name="client_id"]');
    return select ? select.value : null;
  }

  function obtenerTipoObraDelPresupuesto() {
    // Intentar inferir de los capítulos existentes
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    if (caps.length > 0) {
      var primerCap = caps[0].querySelector('[data-f="cap_nombre"]');
      if (primerCap) return primerCap.value.trim().toUpperCase();
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Renderizar sugerencias en panel
  // -------------------------------------------------------------------------

  function renderizarSugerencias(items) {
    var catalogoPanel = document.getElementById("catalogo-partidas");
    if (!catalogoPanel) return;

    catalogoPanel.replaceChildren();

    if (!items.length) {
      var empty = document.createElement("div");
      empty.className = "empty";
      CotizatStyles.setCssText(empty, "padding:1rem; color:var(--text-soft); font-size:0.85rem;");
      empty.textContent = "Sin resultados";
      catalogoPanel.appendChild(empty);
      return;
    }

    items.forEach(function (item) {
      var realIdx = editor.CATALOGO.indexOf(item);
      var div = document.createElement("div");
      div.className = "partida-catalogo";
      CotizatStyles.setCssText(div, "padding:8px 12px; cursor:pointer; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--border-subtle);");
      div.dataset.idx = realIdx;
      div.dataset.nombre = item.nombre;
      div.dataset.categoria = item.categoria;

      // Mini preview si hay imagen
      if (item.imagen) {
        var img = document.createElement("img");
        img.src = window.cotizatArchivoUrl(item.imagen);
        CotizatStyles.setCssText(img, "width:36px; height:36px; border-radius:5px; object-fit:cover;");
        div.appendChild(img);
      }

      var main = document.createElement("div");
      CotizatStyles.setCssText(main, "flex:1; min-width:0;");

      var nombre = document.createElement("div");
      nombre.textContent = item.nombre;
      CotizatStyles.setCssText(nombre, "font-weight:600; font-size:0.88rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;");
      main.appendChild(nombre);

      var meta = document.createElement("div");
      meta.textContent = [item.categoria, item.subcategoria, item.apartado, item.proveedor]
        .filter(Boolean).join(" › ");
      CotizatStyles.setCssText(meta, "font-size:0.72rem; color:var(--text-muted); margin-top:2px;");
      main.appendChild(meta);
      div.appendChild(main);

      var precio = document.createElement("span");
      // Código ISO: el catálogo se muestra en la moneda del presupuesto.
      precio.textContent = window.FMT && window.FMT.fmt
        ? window.FMT.fmt(item.precio || 0, item.moneda)
        : (item.precio || 0).toFixed(2);
      CotizatStyles.setCssText(precio, "font-weight:600; color:var(--accent); font-size:0.85rem; white-space:nowrap;");

      var badgeUso = document.createElement("span");
      badgeUso.className = "badge-categoria";
      badgeUso.textContent = "🔥 " + (item.usos || 0);
      CotizatStyles.setCssText(badgeUso, "font-size:0.65rem; padding:1px 6px; margin-left:6px;");

      var wrapper = document.createElement("div");
      CotizatStyles.setCssText(wrapper, "display:flex; align-items:center; gap:6px;");
      wrapper.appendChild(precio);
      wrapper.appendChild(badgeUso);
      div.appendChild(wrapper);

      div.addEventListener("mousedown", function (e) { e.preventDefault(); });
      div.addEventListener("click", function (e) {
        e.stopPropagation();
        agregarDesdeCatalogo(realIdx);
        catalogoPanel.classList.remove("open");
        var buscador = document.getElementById("buscar-partida");
        if (buscador) buscador.value = "";
      });

      div.addEventListener("mouseenter", function () {
        CotizatStyles.set(div, "background", "var(--surface-hover)");
      });
      div.addEventListener("mouseleave", function () {
        CotizatStyles.set(div, "background", "transparent");
      });

      catalogoPanel.appendChild(div);
    });
  }

  // -------------------------------------------------------------------------
  // Agregar partida desde catálogo
  // -------------------------------------------------------------------------

  function insertarFichaEnCapitulo(d, cap, opciones) {
    opciones = opciones || {};
    if (!cap) {
      var caps = editor.contCapitulos.querySelectorAll(".capitulo");
      cap = caps.length ? caps[caps.length - 1] : editor.Capitulo.crear({ nombre: "CAPÍTULO GENERAL" }, editor);
    }
    cap.classList.remove("collapsed");
    if (!opciones.sinUndo) editor.pushUndo();

    var partida = editor.Partida.crearPartida(cap, {
      catalogo_id: d.id || "",
      nombre: d.nombre,
      descripcion: d.descripcion,
      precio: d.precio,
      unidad: d.unidad,
      cantidad: 1,
      categoria: d.categoria || "",
      subcategoria: d.subcategoria || "",
      apartado: d.apartado || "",
      codigo_interno: d.codigo_interno || d.codigo || "",
      codigo_externo: d.codigo_externo || "",
      proveedor: d.proveedor || "",
      tiempo_estimado_horas: d.tiempo_estimado_horas,
      rendimiento: d.rendimiento || "",
      notas_tecnicas: d.notas_tecnicas || "",
      imagen_partida: d.imagen || "",
      coste_materiales: d.coste_materiales || 0,
      coste_mano_obra: d.coste_mano_obra || 0,
      coste_complementarios: d.coste_complementarios || 0,
      coste_otros: d.coste_otros || 0,
      desperdicio_pct: d.desperdicio_recomendado_pct || 0,
      descomposicion: (function () {
        try {
          return typeof d.descomposicion === "string" ? JSON.parse(d.descomposicion) : d.descomposicion;
        } catch (e) { return null; }
      })()
    }, editor);

    if (partida) {
      var row = partida.querySelector(".partida-row");
      row.classList.add("flash");
      setTimeout(function () { row.classList.remove("flash"); }, 1200);
      if (!opciones.sinScroll) {
        partida.scrollIntoView({ behavior: "smooth", block: "center" });
        var ni = partida.querySelector(".partida-nombre-input");
        if (ni) setTimeout(function () { ni.focus(); }, 200);
      }
    }
    editor.marcarCambio();
    return partida;
  }

  function insertarEnCapitulo(idx, cap) {
    var item = (editor.CATALOGO || [])[idx];
    if (!item) return Promise.resolve(null);
    return obtenerFicha(item)
      .then(function (ficha) { return insertarFichaEnCapitulo(ficha, cap); })
      .catch(function () {
        alert("No se pudo cargar la ficha de la partida. Inténtalo de nuevo.");
        return null;
      });
  }

  function insertarPorId(partidaId) {
    var item = (editor.CATALOGO || []).find(function (partida) {
      return Number(partida.id) === Number(partidaId);
    });
    // El índice ligero puede seguir cargándose de forma diferida. La API de
    // ficha solo necesita el id y fusionará el resultado al recibirlo.
    if (!item) item = { id: Number(partidaId) };
    return obtenerFicha(item)
      .then(function (ficha) { return insertarFichaEnCapitulo(ficha, null); });
  }

  function obtenerFichasPorIds(ids) {
    var unicos = [];
    (ids || []).forEach(function (id) {
      id = Number(id);
      if (id > 0 && unicos.indexOf(id) === -1) unicos.push(id);
    });
    return Promise.all(unicos.map(function (id) {
      var item = (editor.CATALOGO || []).find(function (partida) {
        return Number(partida.id) === id;
      }) || { id: id };
      return obtenerFicha(item);
    }));
  }

  function insertarLote(fichas, capitulo) {
    var validas = (fichas || []).filter(Boolean);
    if (!validas.length) return [];
    editor.pushUndo();
    var insertadas = validas.map(function (ficha, indice) {
      return insertarFichaEnCapitulo(ficha, capitulo, {
        sinUndo: true,
        sinScroll: indice < validas.length - 1
      });
    }).filter(Boolean);
    if (editor.renumerar) editor.renumerar();
    if (editor.recalcular) editor.recalcular();
    editor.marcarCambio();
    return insertadas;
  }

  function agregarDesdeCatalogo(idx) {
    var promesa = insertarEnCapitulo(idx, null);
    var cat = document.getElementById("catalogo-partidas");
    if (cat) cat.classList.remove("open");
    var buscar = document.getElementById("buscar-partida");
    if (buscar) buscar.value = "";
    return promesa;
  }

  // -------------------------------------------------------------------------
  // Comparador de precios vs catálogo (sobreescribir al editar precio)
  // -------------------------------------------------------------------------

  function partidaCatalogoPara(wrap) {
    var idInput = wrap.querySelector('[data-f="p_catalogo_id"]');
    var id = idInput ? String(idInput.value || "") : "";
    if (id) {
      var porId = (editor.CATALOGO || []).find(function (p) { return String(p.id) === id; });
      if (porId) return porId;
    }
    var nombreInput = wrap.querySelector('[data-f="p_nombre"]');
    var nombre = nombreInput ? nombreInput.value.trim().toLowerCase() : "";
    return ((editor.CATALOGO || []).find(function (p) { return p.nombre.toLowerCase() === nombre; }) || null);
  }

  function precioProducto(wrap) {
    var input = wrap.querySelector('[data-f="p_prod_precio"]');
    return input ? (parseFloat(input.value) || 0) : 0;
  }

  function actualizarIndicadorPrecio(wrap, target, match) {
    var importeCell = wrap.querySelector(".partida-importe");
    if (!importeCell) return;
    var old = importeCell.querySelector(".precio-indicator");
    if (old) old.remove();
    if (!match) return;
    var precioActual = parseFloat(target.value) || 0;
    var precioCat = Number(match.precio || match.precio_unitario || 0) + precioProducto(wrap);
    var diff = precioActual - precioCat;
    var diffPct = precioCat > 0 ? (diff / precioCat * 100) : 0;
    if (Math.abs(diffPct) < 0.1) return;
    var indicator = document.createElement("span");
    indicator.className = "precio-indicator";
    CotizatStyles.setCssText(indicator, "font-size:0.65rem; margin-left:6px; opacity:0.8;");
    if (diff > 0) { indicator.textContent = "↑ " + diffPct.toFixed(1) + "% vs catálogo"; CotizatStyles.set(indicator, "color", "var(--rose)"); }
    else { indicator.textContent = "↓ " + Math.abs(diffPct).toFixed(1) + "% vs catálogo"; CotizatStyles.set(indicator, "color", "var(--green)"); }
    importeCell.appendChild(indicator);
  }

  function cerrarPopoverPrecio() {
    var pop = document.getElementById("precio-choice-popover");
    if (pop) pop.remove();
  }

  function posicionarPopover(pop, target) {
    var r = target.getBoundingClientRect();
    CotizatStyles.set(pop, "visibility", "hidden");
    CotizatStyles.set(pop, "display", "block");
    var w = pop.offsetWidth, h = pop.offsetHeight;
    var left = Math.min(window.innerWidth - w - 12, Math.max(12, r.left));
    var top = r.bottom + 8;
    if (top + h > window.innerHeight - 12) top = Math.max(12, r.top - h - 8);
    CotizatStyles.set(pop, "left", left + "px");
    CotizatStyles.set(pop, "top", top + "px");
    CotizatStyles.set(pop, "visibility", "visible");
  }

  function actualizarPrecioCatalogoLocal(partida) {
    var actual = fusionarEnIndice(partida);
    fichasCache[String(partida.id)] = actual;
  }

  function mostrarOpcionPrecio(wrap, target, match) {
    cerrarPopoverPrecio();
    var precioNuevo = parseFloat(target.value) || 0;
    var precioCat = Number(match.precio || match.precio_unitario || 0) + precioProducto(wrap);
    if (Math.abs(precioNuevo - precioCat) < 0.005) return;

    var pop = document.createElement("div");
    pop.id = "precio-choice-popover";
    pop.className = "precio-choice-popover";
    var titulo = document.createElement("strong");
    titulo.textContent = "Cambio de precio detectado";
    pop.appendChild(titulo);
    var ayuda = document.createElement("small");
    ayuda.textContent = "Este precio puede quedarse solo en esta partida del presupuesto o actualizar la partida maestra para futuros presupuestos. Los presupuestos ya creados no se modifican.";
    pop.appendChild(ayuda);
    var acciones = document.createElement("div");
    acciones.className = "actions";
    var soloAqui = document.createElement("button");
    soloAqui.type = "button";
    soloAqui.className = "btn btn-sm";
    soloAqui.dataset.action = "local";
    soloAqui.textContent = "Solo aquí";
    acciones.appendChild(soloAqui);
    var actualizarCatalogo = document.createElement("button");
    actualizarCatalogo.type = "button";
    actualizarCatalogo.className = "btn btn-sm btn-primary";
    actualizarCatalogo.dataset.action = "catalog";
    actualizarCatalogo.textContent = "Actualizar catálogo";
    acciones.appendChild(actualizarCatalogo);
    pop.appendChild(acciones);
    document.body.appendChild(pop);
    posicionarPopover(pop, target);

    function cerrar() { cerrarPopoverPrecio(); document.removeEventListener("click", fueraClic, true); window.removeEventListener("resize", cerrar); window.removeEventListener("scroll", cerrar, true); }
    function fueraClic(e) { if (!pop.contains(e.target) && e.target !== target) cerrar(); }
    setTimeout(function () { document.addEventListener("click", fueraClic, true); }, 0);
    window.addEventListener("resize", cerrar);
    window.addEventListener("scroll", cerrar, true);

    pop.querySelector('[data-action="local"]').addEventListener("mousedown", function (e) { e.preventDefault(); });
    pop.querySelector('[data-action="catalog"]').addEventListener("mousedown", function (e) { e.preventDefault(); });
    pop.querySelector('[data-action="local"]').addEventListener("click", function (e) {
      e.stopPropagation();
      target.dataset.precioCatalogo = String(precioNuevo);
      actualizarIndicadorPrecio(wrap, target, match);
      editor.marcarCambio();
      cerrar();
    });
    pop.querySelector('[data-action="catalog"]').addEventListener("click", function (e) {
      e.stopPropagation();
      var btn = this;
      btn.disabled = true;
      btn.textContent = "Guardando…";
      fetch("/partidas/" + match.id + "/actualizar-precio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          precio: Math.max(0, precioNuevo - precioProducto(wrap)),
          // El importe va en la moneda del presupuesto: el servidor lo
          // devuelve a la moneda base antes de tocar el catálogo.
          moneda: window.COTIZAT_MONEDA_ACTIVA || "",
          tasa: window.COTIZAT_TASA_ACTIVA || ""
        })
      }).then(function (r) { return r.json(); }).then(function (data) {
        if (!data.ok) throw new Error(data.error || "No se pudo actualizar el catálogo.");
        actualizarPrecioCatalogoLocal(data.partida);
        target.dataset.precioCatalogo = String(precioNuevo);
        actualizarIndicadorPrecio(wrap, target, data.partida);
        if (editor.recalcular) editor.recalcular();
        editor.marcarCambio();
        var flash = document.getElementById("undo-flash");
        if (flash) {
          flash.textContent = "✓ Catálogo actualizado para futuros presupuestos";
          flash.classList.add("show");
          setTimeout(function () { flash.classList.remove("show"); }, 2600);
        }
        cerrar();
      }).catch(function (err) {
        btn.disabled = false;
        btn.textContent = "Actualizar catálogo";
        alert(err.message || "No se pudo actualizar el catálogo.");
      });
    });
  }

  function initComparadorPrecios() {
    editor.contCapitulos.addEventListener("input", function (e) {
      var target = e.target;
      if (!target || target.dataset.f !== "p_precio") return;
      var wrap = target.closest(".partida-wrap");
      if (!wrap) return;
      var match = partidaCatalogoPara(wrap);
      actualizarIndicadorPrecio(wrap, target, match);
    });

    editor.contCapitulos.addEventListener("change", function (e) {
      var target = e.target;
      if (!target || target.dataset.f !== "p_prod_precio") return;
      var wrap = target.closest(".partida-wrap");
      if (!wrap) return;
      var precio = wrap.querySelector('[data-f="p_precio"]');
      if (precio) actualizarIndicadorPrecio(wrap, precio, partidaCatalogoPara(wrap));
    });

    editor.contCapitulos.addEventListener("focusin", function (e) {
      var target = e.target;
      if (!target || target.dataset.f !== "p_precio") return;
      var wrap = target.closest(".partida-wrap");
      if (!wrap) return;
      var match = partidaCatalogoPara(wrap);
      if (match) target.dataset.precioCatalogo = String(Number(match.precio || match.precio_unitario || 0) + precioProducto(wrap));
    });

    editor.contCapitulos.addEventListener("change", function (e) {
      var target = e.target;
      if (!target || target.dataset.f !== "p_precio") return;
      var wrap = target.closest(".partida-wrap");
      if (!wrap) return;
      var match = partidaCatalogoPara(wrap);
      if (!match) {
        actualizarIndicadorPrecio(wrap, target, null);
        return;
      }
      var precioInicial = parseFloat(target.dataset.precioCatalogo);
      var precioNuevo = parseFloat(target.value) || 0;
      var precioCat = Number(match.precio || match.precio_unitario || 0) + precioProducto(wrap);
      if (!isFinite(precioInicial)) precioInicial = precioCat;
      if (Math.abs(precioNuevo - precioInicial) > 0.005 && Math.abs(precioNuevo - precioCat) > 0.005) {
        mostrarOpcionPrecio(wrap, target, match);
      } else {
        actualizarIndicadorPrecio(wrap, target, match);
      }
    });
  }

  // -------------------------------------------------------------------------
  // Inicialización
  // -------------------------------------------------------------------------

  function init() {
    initCatalogo();
    initComparadorPrecios();
  }

  editor.initCatalogo = init;
  editor.catalogo = { init: init };
  // Usado por la barra lateral en árbol para insertar en un capítulo concreto.
  editor.Catalogo = {
    insertarEnCapitulo: insertarEnCapitulo,
    obtenerFicha: obtenerFicha,
    buscarRemoto: buscarRemoto,
    registrarSinResultados: registrarSinResultados,
    fusionarEnIndice: fusionarEnIndice,
    insertarPorId: insertarPorId,
    obtenerFichasPorIds: obtenerFichasPorIds,
    insertarLote: insertarLote
  };

  // Exponer para las acciones declarativas del catálogo compartido.
  window.agregarDesdeCatalogo = agregarDesdeCatalogo;
})();
