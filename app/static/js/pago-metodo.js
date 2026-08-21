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

  if (!radios.length || !paneles.length) {
    return;
  }

  function mostrar(metodo) {
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

/* Evita envíos duplicados mientras se abre el checkout alojado de Stripe. */
(function () {
  var checkout = document.querySelector("[data-stripe-checkout]");
  if (!checkout) return;

  checkout.addEventListener("submit", function () {
    var boton = checkout.querySelector("button[type='submit']");
    var texto = checkout.querySelector(".compra-stripe-button-text");
    if (!boton || boton.disabled) return;

    boton.disabled = true;
    boton.classList.add("is-loading");
    if (texto) texto.textContent = "Abriendo pago seguro…";
  });
})();

/* El selector permite usar los canales del país desde el que se hará el pago. */
(function () {
  var selector = document.querySelector("[data-pais-pago-selector]");
  if (!selector || !selector.form) return;
  selector.addEventListener("change", function () {
    selector.form.submit();
  });
})();
