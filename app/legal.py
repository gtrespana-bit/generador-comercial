"""Versiones de los documentos legales y política de registro (E4-038).

La aceptación de los términos se registra con la **versión** que el visitante
aceptó, no con el texto actual: si mañana cambian los términos, el registro
sigue siendo fiel a lo que cada persona aceptó en su momento.

Reglas de versión:

- Bump **obligatorio** (`MAYOR`) cuando un cambio afecta a derechos u
  obligaciones ya aceptados: precios, tratamiento de datos, cancelación,
  propiedad de los datos, responsabilidad, jurisdicción.
- Bump **informativo** (`MENOR`) para redacción, ejemplos o aclaraciones que
  no cambian el alcance de lo aceptado.
- La versión vive en la base (`consentimientos.version` y
  `usuarios.acepto_terminos_version`), en el pie de la página de términos y
  en la fecha de vigencia del documento.

Al cambiar una versión MAYOR hay que decidir (y documentar) si los usuarios
existentes deben re-aceptar antes de seguir usando el servicio.
"""

#: Versión vigente de los términos del servicio. Se guarda tal cual en la
#: base y se muestra en la página /legal/terminos. Debe coincidir con la
#: línea «Versión …» del propio documento: quien acepta en el registro
#: queda anotado con esta versión, no con otra.
TERMINOS_VERSION = "1.1"

#: Fecha de vigencia de la versión vigente, legible para el documento.
TERMINOS_VERSION_FECHA = "16 de agosto de 2026"
