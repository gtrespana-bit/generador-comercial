/* ============================================================================
   Constructor de presupuestos — Módulos habilitados

   Este archivo es un shim que carga los módulos del editor en el orden
   correcto. Los módulos reales están en las carpetas:
     - app/static/js/utils/        (formato, catalogo)
     - app/static/js/editor/       (partida, capitulo, atajos, dragdrop, catalogo, totales)
     - app/static/js/services/     (autosave)

   El archivo principal es app/static/js/editor/main.js.
   ============================================================================ */

// Los módulos se cargan desde el HTML template.
// Este archivo se mantiene para backwards compatibility.
console.log("[Editor] Modo modular habilitado");
