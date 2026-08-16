(function () {
  "use strict";
  var input = document.getElementById("enlace-publico-creado");
  var button = document.getElementById("copiar-enlace-publico");
  if (!input || !button) return;

  button.addEventListener("click", function () {
    var value = input.value;
    function copied() {
      button.textContent = "Copiado";
      window.setTimeout(function () { button.textContent = "Copiar enlace"; }, 1600);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(value).then(copied, function () {
        input.focus();
        input.select();
      });
      return;
    }
    input.focus();
    input.select();
    try {
      if (document.execCommand("copy")) copied();
    } catch (_error) {
      // El enlace queda seleccionado para copiarlo manualmente.
    }
  });
})();
