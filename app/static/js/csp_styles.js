/* Estilos dinámicos compatibles con CSP estricta.
 *
 * Nunca escribe el atributo style de un elemento. Cada nodo recibe un selector
 * opaco y sus propiedades viven en una hoja <style> autorizada con el nonce de
 * la respuesta. Los valores pasan por CSSOM (setProperty), no por HTML.
 */
(function () {
  "use strict";

  var nonce = document.currentScript ? document.currentScript.nonce : "";
  var sheetElement = document.createElement("style");
  if (nonce) sheetElement.nonce = nonce;
  sheetElement.setAttribute("data-cotizat-dynamic-styles", "");
  document.head.appendChild(sheetElement);

  var counter = 0;
  var records = new WeakMap();

  function cssName(property) {
    var name = String(property || "").trim();
    if (name.indexOf("--") === 0) return name;
    name = name.replace(/[A-Z]/g, function (letter) {
      return "-" + letter.toLowerCase();
    });
    return /^-?[a-z][a-z0-9-]*$/.test(name) ? name : "";
  }

  function recordFor(element) {
    if (!element || !element.setAttribute) return null;
    var existing = records.get(element);
    if (existing) return existing;
    counter += 1;
    var id = "cs-" + counter.toString(36);
    element.setAttribute("data-cotizat-dynamic-style", id);
    var index = sheetElement.sheet.cssRules.length;
    sheetElement.sheet.insertRule(
      '[data-cotizat-dynamic-style="' + id + '"] {}', index
    );
    var record = { rule: sheetElement.sheet.cssRules[index], properties: new Set() };
    records.set(element, record);
    return record;
  }

  function set(element, property, value) {
    var name = cssName(property);
    if (!name || !element) return;
    var vacio = value === null || value === undefined || String(value) === "";
    // No crear una regla CSSOM para una propiedad que no va a pintar nada:
    // la primera pasada de filtrado sobre catálogos grandes (p. ej. 540
    // partidas) llamaba insertRule una vez por nodo y congelaba la pestaña.
    if (vacio && !(element.setAttribute && records.get(element))) {
      if (name === "display" && element.classList) {
        element.classList.remove("cotizat-hidden");
      }
      return;
    }
    var record = recordFor(element);
    if (!record) return;

    if (name === "display") {
      if (value === "none") {
        element.classList.add("cotizat-hidden");
        record.rule.style.removeProperty(name);
        record.properties.delete(name);
        return;
      }
      element.classList.remove("cotizat-hidden");
    }

    if (value === null || value === undefined || String(value) === "") {
      record.rule.style.removeProperty(name);
      record.properties.delete(name);
      return;
    }
    record.rule.style.setProperty(name, String(value), "important");
    record.properties.add(name);
  }

  function setMany(element, properties) {
    Object.keys(properties || {}).forEach(function (property) {
      set(element, property, properties[property]);
    });
  }

  function setCssText(element, cssText) {
    var record = recordFor(element);
    if (!record) return;
    element.classList.remove("cotizat-hidden");
    Array.from(record.properties).forEach(function (property) {
      record.rule.style.removeProperty(property);
    });
    record.properties.clear();
    String(cssText || "").split(";").forEach(function (declaration) {
      var separator = declaration.indexOf(":");
      if (separator <= 0) return;
      set(
        element,
        declaration.slice(0, separator).trim(),
        declaration.slice(separator + 1).trim()
      );
    });
  }

  function toggle(element, visible, display) {
    set(element, "display", visible ? (display || "") : "none");
  }

  function isHidden(element) {
    return !element || element.classList.contains("cotizat-hidden") ||
      window.getComputedStyle(element).display === "none";
  }

  function applyDataStyles(root) {
    (root || document).querySelectorAll("[data-cotizat-width]").forEach(function (element) {
      var value = Number(element.dataset.cotizatWidth);
      if (Number.isFinite(value)) set(element, "width", Math.max(0, Math.min(100, value)) + "%");
    });
    (root || document).querySelectorAll("[data-cotizat-flex-basis]").forEach(function (element) {
      var value = Number(element.dataset.cotizatFlexBasis);
      if (Number.isFinite(value)) set(element, "flex-basis", Math.max(0, Math.min(100, value)) + "%");
    });
  }

  window.CotizatStyles = {
    set: set,
    setMany: setMany,
    setCssText: setCssText,
    toggle: toggle,
    isHidden: isHidden,
    applyDataStyles: applyDataStyles
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { applyDataStyles(document); });
  } else {
    applyDataStyles(document);
  }
})();
