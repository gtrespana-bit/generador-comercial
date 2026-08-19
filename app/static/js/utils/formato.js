/* ============================================================================
   Utils — formato, parseo, normalización
   ============================================================================ */

(function () {
  "use strict";

  // Exportar al scope global para que otros módulos puedan usarla
  window.FMT = window.FMT || {};

  function codigo(moneda) {
    return String(moneda || window.COTIZAT_MONEDA_ACTIVA || "USD").toUpperCase() || "USD";
  }

  function simbolo(moneda) {
    var mapa = {USD: "$", COP: "$", MXN: "$", PEN: "S/", CLP: "$", ARS: "$", UYU: "$U", PYG: "₲", BOB: "Bs", DOP: "RD$", PAB: "B/.", CRC: "₡", GTQ: "Q", HNL: "L", NIO: "C$", BRL: "R$", EUR: "€"};
    return mapa[codigo(moneda)] || codigo(moneda);
  }

  window.FMT.simbolo = simbolo;
  window.FMT.codigo = codigo;

  function decimales(moneda) {
    return ["CLP", "PYG"].indexOf(codigo(moneda)) !== -1 || codigo(moneda) === "COP" ? 0 : 2;
  }

  function fmt(valor, moneda) {
    var cod = codigo(moneda);
    var places = decimales(cod);
    if (valor == null || isNaN(valor)) return (0).toFixed(places).replace(".", ",") + " " + cod;
    var s = Math.abs(Number(valor)).toFixed(places);
    var partes = s.split(".");
    partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    var signo = valor < 0 ? "-" : "";
    return signo + partes.join(",") + " " + cod;
  }

  window.FMT.fmt = fmt;

  function fmtNum(valor) {
    if (valor == null || isNaN(valor)) return "0,00";
    return Number(valor).toLocaleString("es-VE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  window.FMT.fmtNum = fmtNum;

  function parseNum(v) {
    // Convierte texto con formato local en número de forma robusta:
    // «12,50», «1.234,56» (formato venezolano/español), «1,234.56» (inglés)
    // y «1234.56». Si hay dos separadores, el último es el decimal.
    var s = String(v == null ? "" : v).trim().replace(/ /g, "").replace(/[$€Bs]/g, "");
    if (s === "") return 0;
    if (s.indexOf(",") !== -1 && s.indexOf(".") !== -1) {
      s = s.lastIndexOf(",") > s.lastIndexOf(".")
        ? s.replace(/\./g, "").replace(",", ".")
        : s.replace(/,/g, "");
    } else if (s.indexOf(",") !== -1) {
      s = s.replace(",", ".");
    }
    var n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  window.FMT.parseNum = parseNum;

  function redondear2(v) {
    return Math.round((v + Number.EPSILON) * 100) / 100;
  }

  window.FMT.redondear2 = redondear2;

  function normalizarBusqueda(valor) {
    return String(valor || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  window.FMT.normalizarBusqueda = normalizarBusqueda;

  function fechaCorta(valor) {
    if (!valor) return "";
    var trozo = String(valor).slice(0, 10).split("-");
    return trozo.length === 3 ? trozo[2] + "/" + trozo[1] + "/" + trozo[0] : "";
  }

  window.FMT.fechaCorta = fechaCorta;

  // Formatear fecha para inputs type="date"
  function formatoFechaInput(fecha) {
    if (!fecha) return "";
    var d = new Date(fecha);
    if (isNaN(d.getTime())) return "";
    var y = d.getFullYear();
    var m = ("0" + (d.getMonth() + 1)).slice(-2);
    var day = ("0" + d.getDate()).slice(-2);
    return y + "-" + m + "-" + day;
  }

  window.FMT.formatoFechaInput = formatoFechaInput;

  // -------------------------------------------------------------------------
  // Ayudantes de creación de elementos DOM
  // -------------------------------------------------------------------------

  // Crea un elemento con clase opcional y texto opcional.
  function h(tag, cls, texto) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (texto !== undefined) el.textContent = texto;
    return el;
  }

  window.FMT.h = h;

  // Crea un <input> con tipo, valor, placeholder, campo (data-f) y atributos extra.
  function crearInput(tipo, valor, placeholder, field, extra) {
    var el = document.createElement("input");
    el.type = tipo;
    if (valor !== undefined && valor !== null && valor !== "") el.value = valor;
    if (placeholder) el.placeholder = placeholder;
    if (field) el.dataset.f = field;
    if (extra) Object.keys(extra).forEach(function (k) {
      el.setAttribute(k, extra[k]);
    });
    return el;
  }

  window.FMT.crearInput = crearInput;
})();
