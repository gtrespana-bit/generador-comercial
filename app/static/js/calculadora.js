/* La demostración no guarda ni envía datos: el formulario GET es el respaldo
   para quien no ejecuta JavaScript. Los costes son por unidad, sin impuestos. */
(function () {
  'use strict';
  var form = document.getElementById('calc-demo-form');
  if (form) {
    var cantidad = document.getElementById('demo-cantidad');
    var coste = document.getElementById('demo-coste');
    var precio = document.getElementById('demo-precio');
    var horas = Number(form.dataset.hours);
    var moneda = form.dataset.currency;
    var numero = new Intl.NumberFormat(form.dataset.locale, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    function actualizar() {
      if (!cantidad.validity.valid || !coste.validity.valid || !precio.validity.valid) {
        ['demo-total-coste', 'demo-total-venta', 'demo-beneficio', 'demo-margen', 'demo-horas'].forEach(function (id) { document.getElementById(id).textContent = '—'; });
        return;
      }
      var q = Number(cantidad.value), c = Number(coste.value), p = Number(precio.value);
      if (![q, c, p].every(Number.isFinite) || q <= 0) return;
      var totalCoste = q * c, totalVenta = q * p, beneficio = totalVenta - totalCoste;
      document.getElementById('demo-total-coste').textContent = numero.format(totalCoste) + ' ' + moneda;
      document.getElementById('demo-total-venta').textContent = numero.format(totalVenta) + ' ' + moneda;
      document.getElementById('demo-beneficio').textContent = numero.format(beneficio) + ' ' + moneda;
      document.getElementById('demo-margen').textContent = totalVenta ? numero.format(beneficio / totalVenta * 100) + ' %' : form.dataset.na;
      document.getElementById('demo-horas').textContent = horas > 0 ? numero.format(horas * q) + ' h' : form.dataset.na;
    }
    [cantidad, coste, precio].forEach(function (el) { el.addEventListener('input', actualizar); });
  }
  // Los selectores dependen del país y del apartado. Actualizarlos evita
  // mostrar unidades o partidas de otro catálogo; sin JS funciona el botón.
  var pais = document.getElementById('calc-pais');
  var apartado = document.getElementById('calc-apartado');
  var unidad = document.getElementById('calc-unidad');
  if (pais && apartado && unidad) {
    pais.addEventListener('change', function () { apartado.disabled = true; unidad.disabled = true; pais.form.submit(); });
    apartado.addEventListener('change', function () { unidad.disabled = true; apartado.form.submit(); });
  }
}());
