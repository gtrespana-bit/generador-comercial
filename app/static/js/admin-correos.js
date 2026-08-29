/* Sistema › Correos de prueba: un destino para todas las plantillas.
 *
 * La pantalla lista ocho correos y cada uno tenía su propia caja de destino, así
 * que probar la batería obligaba a escribir el mismo email ocho veces. El campo
 * de arriba rellena los de las tarjetas cuando se escribe en él; cada tarjeta
 * sigue siendo editable de forma independiente, y si el operador cambia una
 * después, no se le pisa: solo se actualiza al escribir en el campo común.
 *
 * Solo usa value y addEventListener: sin HTML inyectado ni estilos en línea,
 * para cumplir la CSP del despliegue. Sin este script la pantalla funciona igual
 * (cada formulario ya trae su destino en el `value` desde el servidor).
 */
(function () {
  "use strict";

  var global = document.getElementById("destino-global");
  if (!global) return;

  var destinos = document.querySelectorAll("input.correo-destino");
  if (!destinos.length) return;

  global.addEventListener("input", function () {
    var valor = global.value.trim();
    if (!valor) return;
    Array.prototype.forEach.call(destinos, function (campo) {
      campo.value = valor;
    });
  });
})();
