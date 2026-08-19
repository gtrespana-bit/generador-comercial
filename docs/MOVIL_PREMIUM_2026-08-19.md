# Capa móvil premium (2026-08-19)

## Qué se corrigió

El diseño de escritorio no se toca: todo vive en media queries nuevas al
final de `app/static/css/style.css` (sección «MÓVIL PREMIUM») y en pequeños
ajustes de plantilla.

| Problema en teléfono | Solución |
|---|---|
| **La página «se ajusta mal»**: iOS acerca el zoom al tocar un campo | Todos los `input/select/textarea` usan **16 px reales** en ≤768 px (Safari hace zoom con menos) |
| Tablas de listado aplastadas (6 columnas en 390 px) con fila de acciones amontonada | Las listas principales (presupuestos, clientes, cobros, proyectos, recientes del panel) se convierten en **tarjetas** con etiqueta–valor (`table-mobile-cards` + `data-label`) y los botones en cuadrícula táctil |
| Otras tablas anchas (reportes, mercado) desalineaban el documento | La tarjeta desplaza en horizontal con la **primera columna fija** y sombra de profundidad |
| El árbol de capítulos del catálogo ocupaba media pantalla encima de la tabla | Se convierte en un **riel de chips horizontal pegajoso**; los subcapítulos del capítulo abierto se despliegan como chips en la fila inferior |
| La barra de acciones en lote aparecía en medio del contenido | **Bandeja flotante inferior** (con blur y safe-area) sobre la navegación, al alcance del pulgar |
| Modales pequeños y difíciles de usar | **Hoja completa** en ≤640 px con safe-area |
| Botones diminutos | Targets táctiles **≥42 px** (38 px los compactos) |
| Contenido cortado por el notch / indicador de inicio | `viewport-fit=cover` + `env(safe-area-inset-bottom)` en barras fijas |
| KPIs del panel en columna única larguísima | Rejilla de **2 columnas compactas** hasta 400 px |
| Formularios con botones chicos dispersos | Acciones en cuadrícula, botón principal a todo el ancho |
| Scroll horizontal accidental del documento | `overflow-x: clip` en `html/body`; cada tabla desplaza dentro de su contenedor con momentum nativo |

## Dónde

- CSS: `app/static/css/style.css` → sección final «MÓVIL PREMIUM»
  (validada con `tinycss2`, sin errores de sintaxis).
- Plantillas: `data-label` y `table-mobile-cards` en `budgets/list.html`,
  `clients/list.html`, `facturas/list.html`, `projects/list.html`,
  `index.html`; `viewport-fit=cover` en `base.html`.
- La caché de estáticos se rompe sola: la URL lleva `?v=<commit>`.

## Pruebas

`tests/test_movil.py` (7 regresiones): viewport con safe-area, tablas-tarjeta
presentes en las plantillas, regla de 16 px, riel de chips, bandeza inferior,
modal completo y CSS sin errores de sintaxis.
