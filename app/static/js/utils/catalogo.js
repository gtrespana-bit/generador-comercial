/* ============================================================================
   Utils — búsqueda inteligente en catálogo
   ============================================================================ */
(function () {
  "use strict";

  window.CATALOGO_UTILS = window.CATALOGO_UTILS || {};

  function normalizarBusqueda(valor) {
    return String(valor || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function buscarEnCatalogo(items, texto, campos, categoriaPreferida) {
    var consulta = normalizarBusqueda(texto);
    var terminos = consulta ? consulta.split(/\s+/) : [];
    var categoria = normalizarBusqueda(categoriaPreferida);
    var vistos = {};

    return items
      .map(function (item, indice) {
        var valores = campos.map(function (campo) {
          return normalizarBusqueda(item[campo]);
        });
        var nombre = valores[0] || "";
        var todo = valores.join(" ");
        var categoriaItem = normalizarBusqueda(item.categoria);

        if (terminos.length && !terminos.every(function (termino) {
            return todo.indexOf(termino) !== -1;
          })) return null;
        if (!terminos.length && categoria && categoriaItem !== categoria) return null;

        var clave = nombre || "#" + indice;
        if (vistos[clave]) return null;
        vistos[clave] = true;

        var puntuacion = (item.usos || 0) / 1000;
        if (categoria && categoriaItem === categoria) puntuacion += 30;

        terminos.forEach(function (termino) {
          if (nombre.indexOf(termino) === 0) puntuacion += 20;
          else if (nombre.indexOf(termino) !== -1) puntuacion += 10;
          else puntuacion += 2;
        });

        return { item: item, puntuacion: puntuacion };
      })
      .filter(Boolean)
      .sort(function (a, b) {
        return (
          b.puntuacion - a.puntuacion ||
          String(a.item.nombre).localeCompare(String(b.item.nombre), "es")
        );
      })
      .slice(0, 12)
      .map(function (resultado) {
        return resultado.item;
      });
  }

  window.CATALOGO_UTILS.buscarEnCatalogo = buscarEnCatalogo;

  // Sugerencias inteligentes basadas en contexto de cliente
  function sugerirPartidasContextuales(items, clienteId, tipoObra) {
    // Ordenar por relevancia contextual
    return items.slice().sort(function (a, b) {
      var scoreA = (a.usos || 0) * 2;
      var scoreB = (b.usos || 0) * 2;

      // Bonus si es del tipo de obra correcto
      if (a.categoria === tipoObra) scoreA += 50;
      if (b.categoria === tipoObra) scoreB += 50;

      // Bonus por último uso reciente
      if (a.ultimo_uso) scoreA += 30;
      if (b.ultimo_uso) scoreB += 30;

      return scoreB - scoreA;
    }).slice(0, 8);
  }

  window.CATALOGO_UTILS.sugerirPartidasContextuales = sugerirPartidasContextuales;

  // Detectar patrones de uso frecuente
  function detectarPatrones(items, threshold) {
    threshold = threshold || 3;
    var patrones = {};
    items.forEach(function (item) {
      if (item.usos >= threshold) {
        var cat = item.categoria || "General";
        if (!patrones[cat]) patrones[cat] = [];
        patrones[cat].push({
          nombre: item.nombre,
          usos: item.usos,
          precio: item.precio_unitario,
        });
      }
    });
    // Ordenar cada categoría por usos
    Object.keys(patrones).forEach(function (cat) {
      patrones[cat].sort(function (a, b) {
        return b.usos - a.usos;
      });
    });
    return patrones;
  }

  window.CATALOGO_UTILS.detectarPatrones = detectarPatrones;
})();
