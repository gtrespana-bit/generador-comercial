/* Rescata un enlace de recuperación que aterrizó en la página equivocada.
 *
 * Supabase solo respeta `redirect_to` si la URL exacta está en su lista de
 * Redirect URLs. Si no lo está, la descarta silenciosamente y envía al Site
 * URL (normalmente `/`), que al exigir sesión acaba rebotando a `/acceso`.
 * El fragmento `#access_token=...&type=recovery` sobrevive a esos saltos
 * porque el navegador lo re-adjunta y nunca viaja al servidor.
 *
 * Sin este rescate la persona ve el login y el enlace parece roto. Aquí se
 * detecta ese fragmento y se reenvía a /restablecer-clave conservándolo, que
 * es la pantalla que sabe consumirlo.
 *
 * El token permanece siempre en el fragmento: no se escribe en la query, no
 * se registra y no se envía al servidor en esta redirección.
 */
(function () {
  "use strict";

  var DESTINO = "/restablecer-clave";

  if (window.location.pathname === DESTINO) return;

  var hash = window.location.hash || "";
  if (hash.charAt(0) !== "#") return;

  var params = new URLSearchParams(hash.slice(1));
  var tipo = params.get("type") || "";
  var token = params.get("access_token") || "";
  var error = params.get("error") || params.get("error_code") || "";

  // Un enlace caducado o ya usado llega sin token pero con error: se manda a
  // la pantalla de recuperación para pedir uno nuevo con un mensaje claro.
  if (tipo === "recovery" && !token && error) {
    window.location.replace("/recuperar-acceso?error=" + encodeURIComponent(
      "El enlace de recuperación no es válido o ya caducó. Solicita uno nuevo."
    ));
    return;
  }

  if (tipo !== "recovery" || !token) return;

  window.location.replace(DESTINO + hash);
})();
