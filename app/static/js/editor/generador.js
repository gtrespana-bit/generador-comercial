/* ============================================================================
   Editor — Plantillas y Autogenerar con IA (generador basado en catálogo)

   Este archivo conecta funciones que existían en el HTML pero nunca tenían
   código detrás:
     · El selector "🧩 Plantilla…" y los botones de guardar/cargar plantilla.
     · El botón "Autogenerar con IA", que antes era idéntico a "Nuevo
       presupuesto" (mismo enlace, sin generar nada).

   El generador NO usa ningún servicio de IA externo ni internet: es un
   buscador de coincidencias por palabras clave sobre tu propio catálogo de
   partidas (el mismo que ves en el buscador "🔍 Buscar en catálogo de
   partidas"), agrupado en capítulos por categoría. Es determinista y
   transparente: sólo organiza partidas que ya existen en tu base de datos.

   También arregla un bug independiente: los botones "✕"/"Cancelar"
   (data-close) de los modales no cerraban nada porque no tenían listener.
   ============================================================================ */

(function () {
  "use strict";

  var editor = window.EDITOR || {};

  // -------------------------------------------------------------------------
  // Cierre genérico de modales (✕ / Cancelar / clic en el fondo)
  // -------------------------------------------------------------------------

  function initCierreModales() {
    document.addEventListener("click", function (e) {
      var cerrar = e.target.closest("[data-close]");
      if (cerrar) {
        var overlay = cerrar.closest(".modal-overlay");
        if (overlay) {
          overlay.classList.remove("open");
          document.body.classList.remove("modal-open");
        }
        return;
      }
      // Clic directamente en el fondo oscuro (no dentro de .modal)
      if (e.target.classList && e.target.classList.contains("modal-overlay") && e.target.classList.contains("open")) {
        e.target.classList.remove("open");
        document.body.classList.remove("modal-open");
      }
    });
  }

  // -------------------------------------------------------------------------
  // Plantillas: cargar y guardar (usa los endpoints ya existentes en main.py)
  // -------------------------------------------------------------------------

  function hayContenidoEnEditor() {
    var caps = editor.contCapitulos ? editor.contCapitulos.querySelectorAll(".capitulo") : [];
    for (var i = 0; i < caps.length; i++) {
      var nombre = caps[i].querySelector('[data-f="cap_nombre"]');
      if (nombre && nombre.value.trim()) return true;
      if (caps[i].querySelectorAll(".partida-wrap").length) return true;
    }
    return false;
  }

  function cargarPlantillaPorId(id, callback) {
    fetch("/plantillas/" + id + "/datos")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) {
          alert(data.error || "No se pudo cargar la plantilla.");
          return;
        }
        editor.pushUndo();
        editor.construirDesde(data.capitulos);
        editor.marcarCambio();
        if (callback) callback(data);
      })
      .catch(function () {
        alert("No se pudo cargar la plantilla (error de conexión con el servidor local).");
      });
  }
  editor.cargarPlantillaPorId = cargarPlantillaPorId;

  function initPlantillas() {
    var select = document.getElementById("select-plantilla");
    if (select) {
      select.addEventListener("change", function () {
        var id = select.value;
        if (!id) return;
        if (hayContenidoEnEditor() && !confirm("Esto reemplazará los capítulos y partidas actuales por los de la plantilla. ¿Continuar?")) {
          select.value = "";
          return;
        }
        cargarPlantillaPorId(id);
        select.value = "";
      });
    }

    var btnAbrir = document.getElementById("btn-guardar-plantilla");
    if (btnAbrir) {
      btnAbrir.addEventListener("click", function () {
        if (!hayContenidoEnEditor()) {
          alert("Agrega al menos un capítulo con nombre o una partida antes de guardar una plantilla.");
          return;
        }
        editor.abrirModal("modal-plantilla");
        var input = document.getElementById("plantilla-nombre");
        if (input) { input.value = ""; input.focus(); }
      });
    }

    var btnGuardar = document.getElementById("btn-save-plantilla");
    if (btnGuardar) {
      btnGuardar.addEventListener("click", function () {
        var nombre = (document.getElementById("plantilla-nombre").value || "").trim();
        if (!nombre) {
          alert("Ponle un nombre a la plantilla.");
          return;
        }
        var datos = JSON.stringify(editor.serializar());
        var form = new FormData();
        form.append("nombre", nombre);
        form.append("datos", datos);

        btnGuardar.disabled = true;
        fetch("/plantillas", { method: "POST", body: form })
          .then(function (r) { return r.json(); })
          .then(function (resp) {
            btnGuardar.disabled = false;
            if (!resp.ok) {
              alert(resp.error || "No se pudo guardar la plantilla.");
              return;
            }
            if (select) {
              var yaExiste = false;
              Array.prototype.forEach.call(select.options, function (op) {
                if (op.value === String(resp.id)) yaExiste = true;
              });
              if (!yaExiste) {
                var opt = document.createElement("option");
                opt.value = resp.id;
                opt.textContent = resp.nombre;
                select.appendChild(opt);
              }
            }
            editor.cerrarModal("modal-plantilla");
          })
          .catch(function () {
            btnGuardar.disabled = false;
            alert("No se pudo guardar la plantilla (error de conexión con el servidor local).");
          });
      });
    }
  }

  // -------------------------------------------------------------------------
  // Autogenerar con IA — buscador de coincidencias sobre tu catálogo
  // -------------------------------------------------------------------------

  var PALABRAS_VACIAS = [
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
    "con", "sin", "para", "por", "en", "del", "al", "que", "su", "sus", "es",
    "son", "muy", "mas", "más", "este", "esta", "estos", "estas", "the", "and",
    "incluye", "incluir", "tambien", "también", "proyecto", "obra", "trabajo",
  ];

  function normalizar(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function tokenizar(texto) {
    return normalizar(texto)
      .split(/\s+/)
      .filter(function (p) { return p.length >= 3 && PALABRAS_VACIAS.indexOf(p) === -1; });
  }

  function buscarCoincidenciasEnCatalogo(texto) {
    var terminos = tokenizar(texto);
    if (!terminos.length || !editor.CATALOGO) return [];

    var resultados = editor.CATALOGO.map(function (item) {
      var nombre = normalizar(item.nombre);
      var resto = normalizar((item.descripcion || "") + " " + (item.categoria || "") + " " + (item.subcategoria || ""));
      var puntuacion = 0;
      var coincidencias = 0;

      terminos.forEach(function (t) {
        if (nombre.indexOf(t) !== -1) { puntuacion += 3; coincidencias++; }
        else if (resto.indexOf(t) !== -1) { puntuacion += 1; coincidencias++; }
      });
      if (coincidencias) puntuacion += Math.min(item.usos || 0, 10) * 0.2;

      return { item: item, puntuacion: puntuacion, coincidencias: coincidencias };
    })
      .filter(function (r) { return r.coincidencias > 0; })
      .sort(function (a, b) { return b.puntuacion - a.puntuacion; })
      .slice(0, 30)
      .map(function (r) { return r.item; });

    return resultados;
  }

  function agruparPorCategoria(items) {
    var grupos = {};
    var orden = [];
    items.forEach(function (item) {
      var cat = item.categoria || "General";
      if (!grupos[cat]) { grupos[cat] = []; orden.push(cat); }
      grupos[cat].push(item);
    });
    return orden.map(function (cat) {
      return {
        nombre: cat.toUpperCase(),
        partidas: grupos[cat].map(function (item) {
          return {
            partida_id: item.id,
            nombre: item.nombre,
            descripcion: item.descripcion || "",
            unidad: item.unidad || "ud",
            precio: item.precio,
            cantidad: 1,
            categoria: item.categoria || "",
          };
        }),
      };
    });
  }

  function limpiarCapituloVacioInicial() {
    if (!editor.contCapitulos) return;
    var caps = editor.contCapitulos.querySelectorAll(".capitulo");
    if (caps.length === 1) {
      var cap = caps[0];
      var nombre = cap.querySelector('[data-f="cap_nombre"]');
      var sinNombre = !nombre || !nombre.value.trim();
      var sinPartidas = cap.querySelectorAll(".partida-wrap").length === 0;
      if (sinNombre && sinPartidas) cap.remove();
    }
  }

  function generarBorrador(texto) {
    var coincidencias = buscarCoincidenciasEnCatalogo(texto);
    if (!coincidencias.length) return { total: 0, capitulos: 0 };

    var nuevosCapitulos = agruparPorCategoria(coincidencias);

    editor.pushUndo();
    limpiarCapituloVacioInicial();
    nuevosCapitulos.forEach(function (cap) {
      editor.Capitulo.crear(cap, editor);
    });
    editor.renumerar();
    editor.recalcular();
    editor.marcarCambio();

    return { total: coincidencias.length, capitulos: nuevosCapitulos.length };
  }

  function initGenerador() {
    var btnAbrir = document.getElementById("btn-abrir-generador");
    if (btnAbrir) {
      btnAbrir.addEventListener("click", function () {
        editor.abrirModal("modal-generador");
        var ta = document.getElementById("generador-texto");
        if (ta) ta.focus();
      });
    }

    var btnGenerar = document.getElementById("btn-generar");
    if (btnGenerar) {
      btnGenerar.addEventListener("click", function () {
        var ta = document.getElementById("generador-texto");
        var salida = document.getElementById("generador-resultado");
        var texto = (ta && ta.value || "").trim();
        if (!texto) {
          if (salida) {
            salida.style.display = "block";
            salida.textContent = "Escribe una breve descripción del proyecto (por ejemplo el tipo de obra y sus acabados).";
          }
          return;
        }
        var resultado = generarBorrador(texto);
        if (!resultado.total) {
          if (salida) {
            salida.style.display = "block";
            salida.textContent = "No se encontraron coincidencias en tu catálogo de partidas. Prueba con otras palabras, o agrega la partida en /partidas/nueva y vuelve a intentarlo.";
          }
          return;
        }
        if (salida) salida.style.display = "none";
        ta.value = "";
        editor.cerrarModal("modal-generador");
      });
    }

    // Si venimos del Dashboard con "Autogenerar con IA" (?autogenerar=1)
    if (location.search.indexOf("autogenerar=1") !== -1) {
      editor.abrirModal("modal-generador");
    }
  }

  function init() {
    initCierreModales();
    initPlantillas();
    initGenerador();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.EDITOR = editor;
})();
