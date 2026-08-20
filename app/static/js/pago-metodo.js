/* Selector de método de pago en /pago/comprar.
 *
 * Al elegir un método (radio), muestra su panel con los datos para pagar y
 * el formulario de verificación. Solo usa classList y addEventListener, sin
 * inyección de HTML ni estilos en línea: cumple la CSP y la auditoría.
 */
(function () {
  var radios = document.querySelectorAll("input[name='metodo_pago']");
  var paneles = document.querySelectorAll(".metodo-panel");
  var campos = document.querySelectorAll("[data-campo]");
  var btnRegistrar = document.getElementById("btn-registrar");

  if (!radios.length || !paneles.length) {
    return;
  }

  function esOnline(metodo) {
    var panel = document.querySelector(
      ".metodo-panel[data-metodo='" + metodo + "']"
    );
    return panel ? panel.getAttribute("data-online") === "1" : false;
  }

  function mostrar(metodo) {
    var online = esOnline(metodo);
    for (var i = 0; i < paneles.length; i++) {
      var activo = paneles[i].getAttribute("data-metodo") === metodo;
      paneles[i].classList.toggle("activo", activo);
      paneles[i].setAttribute("aria-hidden", activo ? "false" : "true");
      var inputs = paneles[i].querySelectorAll("input, select, textarea");
      for (var j = 0; j < inputs.length; j++) {
        if (activo) {
          // Reactiva los campos del método elegido.
          inputs[j].disabled = false;
        } else {
          // Desactiva los campos de los métodos no elegidos: un input
          // `disabled` no se envía con el formulario. Sin esto, cada panel
          // mandaba su propio campo de archivo (y sus campos de verificación
          // con nombres repetidos) y el servidor recibía partes vacías que
          // competían con el archivo elegido.
          inputs[j].disabled = true;
          inputs[j].removeAttribute("required");
        }
      }
    }
    // Marcar como obligatorios los campos del método activo.
    for (var k = 0; k < campos.length; k++) {
      var requiere = campos[k].getAttribute("data-metodo") === metodo;
      if (requiere) {
        campos[k].setAttribute("required", "required");
      } else {
        campos[k].removeAttribute("required");
      }
    }
    // El botón «Registrar mi compra» (con comprobante) solo aplica a métodos
    // manuales; para la tarjeta, el propio panel tiene su botón de pago.
    if (btnRegistrar) {
      btnRegistrar.hidden = online;
    }
  }

  for (var r = 0; r < radios.length; r++) {
    radios[r].addEventListener("change", function () {
      if (this.checked) {
        mostrar(this.value);
      }
    });
    // Primer método marcado por defecto en el HTML: activa su panel al cargar.
    if (radios[r].checked) {
      mostrar(radios[r].value);
    }
  }
})();
