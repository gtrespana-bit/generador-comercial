# Auditoría del panel de administración

**Fecha:** 22/10/2026 · **Alcance:** todo el panel (`/admin`), pestaña por pestaña, más la ficha de cliente.
**Base:** código en `main` @ `2527098` (PR #154 ya fusionado). No se ha modificado nada.
**Pregunta que responde:** ¿este panel nos da información y nos deja hacer cosas, o solo nos enseña pantallas?

> **Estado de ejecución (22/10/2026).** Lo que sigue es el diagnóstico original.
> Ya está implementado:
>
> - **Fase 0 completa:** CSV de Contratos (la ruta no existía: el botón daba 404), `volver` con filtros en Soporte y Compras, badge de Soporte en el menú, estado tipado en Sistema › Estado y resultados de ⌘K que abren la compra o la ficha concretas.
> - **Fase 1 completa** en las siete listas del panel: Compras, Soporte, Renovaciones, Ventas, Cobros, Contratos y Auditoría. Todas buscan, ordenan, paginan de 25 en 25 (hasta 100), conservan los filtros en la URL y exportan un CSV con **el mismo filtro y el mismo orden** que se está viendo. Auditoría estrena además `/admin/auditoria.csv` y deja de cortar en 250 eventos a ciegas: cuenta en SQL y dice cuántos hay.
> - Suite completa en verde: **2348 tests** (5 nuevos de listas, 18 en total en `test_panel_listas.py`).
>
> El orden «en SQL» se aplica donde la fila sale de una sola tabla (Compras, Soporte, Auditoría). Renovaciones, Ventas, Cobros y Contratos siguen materializando el conjunto filtrado —sus filas se construyen cruzando licencias, compras y organizaciones— y paginan después; la paginación ya es correcta, pero mover el recorte a SQL exige antes reescribir esos servicios con agregados. Queda anotado como deuda de la Fase 4 (rendimiento).
>
> **Decisiones del titular (22/10/2026).**
> - **Responder soporte desde el panel: descartado.** Prefiere contestar desde su propio correo; es más cómodo para él y no quiere la conversación dentro del panel. Se mejora el enlace `mailto:` para que lleve el número del ticket y el mensaje citado, y la Fase 2 queda fuera del plan.
> - **Roles aplicados: aplazado sin fecha.** Solo él tiene acceso al panel y prevé que siga así; no compensa construir la tabla de permisos. `ALCANCES_ROL` sigue siendo descriptivo, no una puerta.
> - **Bandeja de Hoy con `tareas_panel`: pendiente de decidir.** Se le explicó en lenguaje llano (posponer y marcar hecho); respuesta pendiente.

---

## 1. Veredicto

El panel **está mucho mejor construido de lo que parece desde dentro**: la navegación es coherente (6 áreas, 21 pantallas, atajos, ⌘K), la ficha de cliente unificó lo que antes estaba repartido, y Analítica es una pantalla de nivel profesional. El problema no es la arquitectura: es que **la capacidad de "hacer" se quedó a medio camino y no se repite**.

Hoy el panel es bueno **para mirar** y regular **para operar**. En concreto:

1. **Solo una lista de todo el panel se puede usar de verdad.** Clientes › Directorio tiene búsqueda, chips, orden, vistas guardadas y CSV con filtros. Las otras ocho tablas no: cada una implementó un trozo distinto (unas buscan, otras filtran, otras ordenan, ninguna pagina).
2. **No se puede actuar en lote en ningún sitio.** Cero casillas de selección en todo el panel. Veinte compras pendientes = veinte clics y veinte recargas.
3. **No se puede responder a un cliente desde el panel.** El único botón de Soporte abre el cliente de correo del operador (`mailto:`). La respuesta no queda guardada, no se puede consultar después y no existe para el resto del equipo.
4. **"Hoy" informa pero no permite trabajar.** La agenda dice qué requiere atención y no deja marcarlo hecho, asignarlo ni posponerlo. Es una lista de lectura, no una bandeja.
5. **Los roles existen en el papel, no en la puerta.** `ALCANCES_ROL` describe que un `analista` es «solo lectura» y que `soporte` atiende incidencias; en la práctica **no hay ninguna comprobación de rol** salvo en cuatro acciones de equipo y tres de precios. Un operador con rol `analista` puede suspender el acceso de un cliente, apagar un flag o crear una API key.

Y por debajo de todo eso, un problema que no se ve pero se va a notar: **cada pantalla del panel recalcula todos los contadores recorriendo todas las organizaciones**. Con 30 clientes es gratis; con 300 será la razón por la que el panel "va lento".

**Resumen en una frase:** el panel ya sabe contar la verdad; lo que falta es que las listas se puedan interrogar y que las acciones estén donde está el problema.

---

## 2. El mapa actual

| Área | Pantallas | Estado general |
|---|---|---|
| **Hoy** `/admin` | 1 | Buena información, cero accionable |
| **Clientes** | Directorio · Pipeline · Soporte | Directorio excelente; Soporte cojo; Pipeline correcto |
| **Ficha de cliente** | Resumen · Presupuestos · Acceso · Cobros · Gestión · Actividad | La mejor pieza del panel; le falta historial unificado |
| **Ingresos** | Ventas · Renovaciones · Compras · Cobros · Contratos | Datos correctos, listas sin herramientas, acciones sueltas |
| **Web** | Contenido · Avisos · Versiones | Contenido es un editor de JSON; avisos y versiones están bien |
| **Analítica** | 1 (con explorador) | La pantalla más completa del panel; referencia a seguir |
| **Sistema** | Estado · Automatizaciones · Datos · Precios · Equipo · Accesos · Auditoría · Correos | Mucho poder, poca protección y poca trazabilidad |

**Navegación:** `app/panel_arquitectura.py` es la fuente única (secciones, pestañas, iconos, atajos `G+letra`, redirecciones de rutas viejas). Esto está bien y hay que conservarlo: cualquier propuesta de abajo se engancha ahí, no en cada plantilla.

---

## 3. Diagnóstico pantalla por pantalla

Formato: **qué hay** → **qué duele** → **qué necesita**. La etiqueta entre paréntesis es el impacto si se arregla: 🔴 alto, 🟠 medio, 🟢 bajo.

### 3.1 Hoy (`/admin`)

**Qué hay.** 8 KPIs, últimas 5 ventas, últimas 5 altas, buzón (3 mensajes), bloque «Requiere tu acción hoy» con las notificaciones del panel, gráfico SVG de ingresos, «Van a vencer» (6), 8 atajos y 6 acciones de auditoría. Dos botones operativos: *Conceder acceso* y *Enviar avisos de vencimiento*.

**Qué duele.**
- El bloque «Requiere tu acción hoy» **excluye** justo lo que más se acumula: ventas y registros. Es una lista de novedades, no de trabajo pendiente.
- No se puede marcar nada como hecho, asignarlo ni posponerlo. Si lo ves y no lo haces, mañana sigue igual y no hay forma de saber si alguien lo cogió.
- Los KPIs **duplican** los de las subpáginas, sin rango de fechas ni comparación (¿mejor o peor que la semana pasada? no se sabe).
- «Van a vencer» corta en 6 sin decir cuántos hay en total ni permitir ordenar por importe o por días.
- No hay forma de saber «qué pasó desde que me fui»: la auditoría reciente está al final, en formato técnico.

**Qué necesita.** 🔴 Convertirse en **bandeja de trabajo**: una sola lista de tareas del día con origen (compra por revisar, soporte nuevo, licencia que vence, error sin resolver), y tres gestos por tarea: **asignar**, **posponer**, **hecho**. KPIs con comparación contra el periodo anterior y enlace al listado ya filtrado. Ver Fase 3.

---

### 3.2 Clientes

#### Directorio (`/admin/clientes?tab=directorio`) — 🟢 la referencia

**Qué hay.** Búsqueda por nombre/slug, estado + plan + CRM, **vistas guardadas**, 5–6 cabeceras ordenables, CSV que respeta los filtros, chips con contadores, alta de cliente.

**Qué duele.**
- Busca por nombre y slug, **no por correo**. El correo se muestra en la fila, pero si el cliente escribe desde `maria@estudio.com` no hay manera de encontrarlo sin adivinar el nombre comercial.
- El orden se resuelve **en Python** (`ordenar_filas`), así que no sobrevivirá a la paginación: para ordenar por ingresos hay que traer todas las filas primero.
- La vista guardada guarda filtros, pero no el orden ni el tamaño de página.
- No hay acciones por fila (reenviar recibo, suspender, copiar enlace de la ficha). Hay que entrar a la ficha para todo.

**Qué necesita.** 🟠 Búsqueda por email y por dominio; orden y paginación en SQL; acciones rápidas en la fila (menú `⋯`); que las vistas guarden también el orden. Es la pantalla que hay que usar de molde para las demás.

#### Pipeline (`/admin/clientes?tab=pipeline`) — 🟢

**Qué hay.** Tablero por etapa, KPIs por estado, mover etapa con un `select` que hace POST, «contacto hoy o atrasado».

**Qué duele.**
- Mover una etapa **recarga la página entera**; en un tablero eso se siente roto.
- Las tarjetas no se pueden arrastrar, no se pueden filtrar y no dicen el último contacto real (solo la fecha que alguien escribió a mano).
- No hay «añadir nota rápida» desde la tarjeta: hay que abrir la ficha.

**Qué necesita.** 🟠 Actualización en sitio (fetch + reemplazo de columna), filtro por responsable/importe, y fecha de último contacto calculada desde las notas. Si no se va a hacer el fetch, al menos devolver a la misma columna y marcar la tarjeta movida.

#### Soporte (`/admin/clientes?tab=soporte`) — 🔴 el agujero más caro

**Qué hay.** KPIs, chips de estado y tipo con contadores, búsqueda, nota interna por mensaje (POST que cambia estado), marcar resuelto / reabrir, y un botón de respuesta que abre `mailto:`.

**Qué duele.**
- **No se puede responder desde el panel.** El `mailto:` depende de que el operador tenga correo configurado, no deja constancia, no lo ve el resto del equipo y no permite plantillas. Es la función más pedida y la que menos existe.
- El modelo `MensajeSoporte` no tiene campo de respuesta: guardar la contestación exige una migración (ver Fase 2). Es un cambio pequeño y acotado.
- Sin **prioridad** ni **responsable**: dos personas pueden contestar lo mismo o ninguna.
- Sin fechas ni paginación: la lista crece y solo se puede mirar hacia atrás con el filtro de estado.
- El enlace «volver» está fijo a la pestaña: al cambiar un estado **se pierden búsqueda y filtros**.
- Sin plantillas de respuesta (las 6 respuestas que se escriben siempre igual, escritas otra vez).
- Sin CSV ni exportación para reclamaciones recurrentes.

**Qué necesita.** 🔴 Responder dentro del panel (guardar respuesta + autor + fecha, enviar por Resend, cambiar estado a `en_proceso`), plantillas, prioridad y responsable, `volver` que conserva filtros, fechas y paginación. Es la Fase 2 y probablemente **el mayor retorno por día invertido de todo el documento**.

#### Ficha de cliente (`/admin/clientes/{id}`) — 🟠 buena, con dos huecos

**Qué hay.** 6 pestañas: Resumen, Presupuestos (solo superadmin, lectura auditada), Acceso (cadena de licencias, renovar, suspender), Cobros (compras + facturas), Gestión (CRM + notas internas), Actividad (eventos del cliente y acciones del panel).

**Qué duele.**
- **La cronología está partida en dos** en Actividad: eventos del cliente a un lado, acciones del panel al otro. Lo que uno quiere leer es una sola línea de tiempo: «entró, pidió presupuesto, le cancelamos una licencia, escribió a soporte».
- Las notas de soporte **no aparecen en la ficha**: si el cliente llamó por algo, eso no está en su historia.
- «Resumen» repite parte de «Acceso» y «Cobros»; no dice lo que de verdad se pregunta al abrir una ficha: *¿está al día? ¿cuándo fue el último contacto? ¿hay algo pendiente?*
- Renovar desde la ficha no deja elegir plan con un clic; hay que pasar por el formulario largo.

**Qué necesita.** 🟠 Un timeline único (auditoría + notas + soporte + licencias) y una cabecera de ficha con tres respuestas: estado de acceso, último contacto, pendientes. Es barato porque los datos ya están cargados.

---

### 3.3 Ingresos

#### Ventas (`/admin/ingresos?tab=ventas`) — 🟠

**Qué hay.** KPIs (hoy, mes, ticket medio, acumulado), chips de periodo/método/plan, búsqueda, tabla por plan, tabla por método, CSV con filtros.

**Qué duele.**
- **No se puede ordenar** ni elegir un rango de fechas libre (solo los periodos predefinidos).
- **No hay acciones por fila**: si una venta necesita un recibo o una revisión, hay que ir a Contratos o a la ficha y volver a buscar.
- Sin paginación: el «acumulado» y la tabla crecen juntos.
- Los KPIs no comparan con el periodo anterior.

**Qué necesita.** 🟠 Orden por fecha/importe/cliente, rango `desde`–`hasta`, y un menú de fila con «ver ficha», «recibo», «copiar referencia». Comparativa en los KPIs.

#### Renovaciones (`/admin/ingresos?tab=renovaciones`) — 🔴

**Qué hay.** Navegación de mes, KPIs (vencen, por renovar, importe en juego, avisados hoy), chips de estado con contadores, vistas guardadas, tabla con «Renovar 1 año» y «Ficha», CSV, y el botón global de avisos.

**Qué duele.**
- El botón de fila renueva **siempre 1 año a 89 US$**, con el importe y la duración en campos ocultos. Si el cliente paga mensual o tiene otro precio, el operador tiene que ir a la ficha, y el texto de confirmación le está mintiendo.
- No se puede **elegir a quién avisar**: el botón de avisos barre a todos los que vencen en 15 días, sin selección.
- Sin búsqueda ni orden por importe: el orden es por vencimiento, y punto.
- «Avisado» solo dice hoy; no hay historial de avisos por cliente.

**Qué necesita.** 🔴 Renovar con plan/duración/importe elegibles en la propia fila (los mismos campos del formulario de concesión, en un desplegable), selección múltiple para avisar solo a los marcados, y buscar/ordenar. Alto impacto: es dinero recurrente y hoy se trabaja a ciegas.

#### Compras (`/admin/ingresos?tab=compras`) — 🔴

**Qué hay.** Una tarjeta por compra con desplegable de verificación, dos POST (activar / rechazar) con confirmación, y recibo PDF tras activar.

**Qué duele.**
- El comprobante **se abre en otra pestaña**, dentro de un desplegable que está cerrado por defecto: revisar 15 transferencias son 15 pestañas nuevas y 15 vueltas atrás. No hay visor dentro del panel ni vista comparada de los datos de verificación.
- Sin búsqueda, sin fechas, sin lote: 15 compras pendientes son 15 pulsaciones y 15 recargas completas.
- Rechazar no pide motivo obligatorio (solo un `confirm`), y el cliente no recibe explicación.
- El enlace «volver» conserva solo el estado: se pierden los filtros que hubiera.
- No hay CSV ni forma de cuadrar contra el banco.

**Qué necesita.** 🔴 Visor de comprobante en línea (imagen/PDF en un `dialog`), selección múltiple con «activar marcadas», motivo de rechazo obligatorio que se guarde, y filtros de fecha. Es la pantalla donde cada minuto ahorrado se nota.

#### Cobros (`/admin/ingresos?tab=cobros`) — 🟠

**Qué hay.** Navegación de mes, chips por tipo, tabla, CSV.

**Qué duele.** Solo lectura en el sentido más estricto: sin búsqueda, sin orden, sin paginación, sin acciones. La columna «Pendientes» del KPI no lleva a ningún sitio: una factura vencida no tiene botón de reclamar ni enlace a su presupuesto, y una compra sin verificar no lleva a la compra.

**Qué necesita.** 🟠 Buscar por cliente, ordenar por importe/vencimiento, y acciones: «reclamar» (correo con plantilla), «ver presupuesto», «marcar cobrado» si existe el flujo.

#### Contratos (`/admin/ingresos?tab=contratos`) — 🟠

**Qué hay.** KPIs, búsqueda, filtro de estado, tabla de acceso con historial de licencias desplegable y cancelación inline, CSV.

**Qué duele.**
- **El botón de CSV daba 404**: apuntaba a `/admin/contratos.csv`, una ruta que no existía. El exportador (`/admin/ingresos.csv?tab=contratos`) sí respetaba `q` y `estado`; lo que faltaba era la puerta. Peor que ignorar los filtros: no descargaba nada y el fallo pasaba desapercibido.
- Orden fijo por vencimiento, sin poder ordenar por ingresos o nombre.
- Cancelar una licencia usa `confirm` del navegador: sin motivo, sin deshacer.

**Qué necesita.** 🟠 CSV con los filtros activos (una línea), orden por columnas, y motivo + confirmación real en la cancelación.

---

### 3.4 Web

#### Contenido (`/admin/web?tab=contenido`) — 🟠

**Qué hay.** Bloques por clave, borrador/publicado, publicar, descartar, estado por bloque.

**Qué duele.** **Se edita JSON crudo en un `<textarea>`.** El dueño del negocio no puede cambiar un titular sin saber comillas y llaves, y un error de sintaxis no se detecta hasta guardar. No hay vista previa ni diferencia entre lo publicado y el borrador (solo un badge que dice que son distintos, sin decir en qué).

**Qué necesita.** 🟠 Editor por campos, declarando el esquema de cada clave (texto, párrafo, enlace, lista), vista previa y diff publicado/borrador. Unas 2–3 jornadas bien invertidas si el contenido lo toca alguien no técnico.

#### Avisos y Versiones — 🟢

Crear, editar, activar/desactivar avisos; historial de versiones. Funcionan. Solo falta confirmación al desactivar un aviso visible y, en versiones, decir **qué cambió** (hoy es una lista de fechas).

---

### 3.5 Analítica — 🟢 la referencia

**Qué hay.** Filtros de días, organización, acción, actor, texto, rango, ruido, «mis eventos», **paginación real**, presencia en vivo, tabla por empresa, explorador de eventos, autorefresco, chats y exportación.

**Qué duele.** Es la única pantalla paginada del panel; el resto debería aprender de ella. Detalles menores: el filtro de organización es un desplegable con todas (no busca), y el explorador no enlaza a la ficha del cliente.

**Qué necesita.** 🟢 Servir de patrón (no de excepción) y añadir búsqueda en el selector de organización y enlaces a la ficha. No tocar más.

---

### 3.6 Sistema

#### Estado (`?tab=estado`) — 🟠

**Qué hay.** Badges por comprobación, errores con traza y «marcar resuelto», uptime.

**Qué duele.** El color del badge se decide con `'error' in valor`: una comprobación cuyo texto contenga «error» en otra acepción se pinta en rojo, y una que falle devolviendo «ko» se pinta en verde. La salud del sistema no debería depender de una heurística de cadenas.

**Qué necesita.** Estado **tipado** (`ok` / `aviso` / `fallo`) devuelto por cada comprobación, con mensaje aparte. Es un cambio pequeño y elimina falsos positivos de los que dependen las alertas.

#### Automatizaciones (`?tab=automatizaciones`) — 🟢

**Qué hay.** Reglas del cron visibles, «ejecutar ahora» con confirmación, qué haría hoy.

**Qué duele.** «Ejecutar ahora» no dice **a quién** va a afectar ni deja cancelar; no hay historial de ejecuciones (solo el resultado de la auditoría, en otra pantalla).

**Qué necesita.** 🟠 Previsualización («afectará a 12 clientes: …») e historial de las últimas ejecuciones con resultado.

#### Datos (`?tab=datos`) — 🟢

Salud de catálogo y de secretos definidos. Correcto. Añadiría el estado de la migración aplicada (head de Alembic) visible, porque hoy es la primera pregunta cuando algo falla.

#### Precios (`?tab=precios`) — 🟢

Carga de matriz por país con vista previa, validación y confirmación, restringido a superadmin. Bien. Falta historial de qué matriz estaba antes (hoy no hay «deshacer»).

#### Equipo (`?tab=equipo`) — 🟠

**Qué hay.** Alta, cambio de rol, suspender/activar, último superadmin protegido.

**Qué duele.** El formulario de alta tiene correo pero **no envía invitación**: el nuevo operador no sabe que existe hasta que alguien se lo dice. Y los roles se eligen desde una lista cuya descripción (`ALCANCES_ROL`) no se cumple en el resto del panel (ver §5, T5).

**Qué necesita.** 🟠 Correo de invitación con enlace, y que el rol **sirva** (T5). Mientras el rol no sirva, la pantalla está prometiendo algo que no pasa.

#### Accesos (`?tab=accesos`) — 🔴 por seguridad

**Qué hay.** Flags con alternar y claves de API con crear/revocar.

**Qué duele.** Cualquier operador, sea cual sea su rol, puede **apagar una función para todo el producto** o **crear una clave con scopes** (`licencias.escribir`). No hay confirmación en alternar un flag, ni caducidad visible en las claves, ni registro claro de quién creó qué.

**Qué necesita.** 🔴 Restringir a `admin`/`superadmin`, confirmación al apagar un flag, caducidad y último uso de cada clave.

#### Auditoría (`?tab=auditoria`) — 🟠

**Qué hay.** Filtros por actor, acción, resultado y **ID de organización escrito a mano**, 250 filas, traza técnica.

**Qué duele.**
- **Sin filtro de fechas** y sin paginación: para investigar «qué pasó el martes» hay que leer.
- **Sin CSV**: no se puede cruzar con nada.
- El ID de organización se teclea; nadie se sabe los IDs.
- Las filas no enlazan a la entidad: ves `licencia.cancelada` y no puedes saltar a la licencia ni a la ficha.

**Qué necesita.** 🟠 Fechas, paginación, CSV, buscador de organización por nombre y enlaces a la entidad. Es la pantalla que convierte el panel en auditable de verdad.

#### Correos (`?tab=correos`) — 🟢

Enviar cualquier plantilla a un buzón real, con destino global. Bien resuelto. Solo falta buscar plantilla (hoy es una cuadrícula larga) y ver la última vez que se envió cada una.

---

## 4. La matriz: el diagnóstico en una imagen

`✅` existe y funciona · `◐` existe a medias o con un fallo · `—` no existe

| Pantalla | Buscar | Filtrar | Ordenar | Paginar | CSV | Acción en fila | Lote |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Clientes › Directorio | ✅ | ✅ | ◐ (Python) | — | ✅ | — | — |
| Clientes › Pipeline | — | — | — | n/a | — | ✅ | — |
| Clientes › Soporte | ✅ | ✅ | — | — | — | ◐ | — |
| Ficha › Presupuestos | — | — | — | — | — | ◐ | — |
| Ingresos › Ventas | ✅ | ✅ | — | — | ✅ | — | — |
| Ingresos › Renovaciones | — | ✅ | — | — | ✅ | ◐ | — |
| Ingresos › Compras | — | ✅ | — | — | — | ✅ | — |
| Ingresos › Cobros | — | ◐ | — | — | ✅ | — | — |
| Ingresos › Contratos | ✅ | ✅ | — | — | ✅ (ruta añadida) | ✅ | — |
| Web › Contenido/Avisos/Versiones | — | — | — | — | — | ✅ | — |
| Analítica | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Sistema › Auditoría | ◐ (sin fechas) | ✅ | — | — | — | — | — |
| Sistema › Equipo / Accesos | — | — | — | — | — | ✅ | — |

Léase: **hay 9 listas y solo una cumple las seis columnas.** La analítica cumple todo menos acciones, y no las necesita.

---

## 5. Los ocho problemas de fondo

No son de una pestaña; son los que hacen que arreglar pestañas una por una no escale.

**T1 · No hay un patrón de lista.** Cada tabla resolvió el mismo problema a su manera. `panel_contextos` ya tiene las piezas (`chips`, `filtrar_filas`, `ordenar_filas`, `enlace_orden`, `url_panel`, `_barra_vistas`), pero cada plantilla las usa o no según quién la escribió. Mientras no haya un patrón, la lista número diez volverá a salir sin búsqueda.
*Severidad: alta. Es la causa raíz de la mitad del documento.*

**T2 · Nada está acotado.** No hay paginación en ninguna lista (salvo Analítica) y `resumen_admin` + `notificaciones_admin` + `contadores_panel` cargan organizaciones, licencias, compras, membresías y usuarios **en cada petición del panel**. El coste crece con el negocio, justo cuando el panel importa más.
*Severidad: alta (hoy invisible, mañana el problema número uno).*

**T3 · La búsqueda no llega donde duele.** ⌘K busca clientes por nombre/slug, licencias, compras, operadores y auditoría; **no busca por correo**, no busca mensajes de soporte, no busca páginas del panel y no ofrece acciones («conceder acceso a…»). Peor: un resultado de compra te lleva a la lista sin resaltar la compra, así que acabas buscando a ojo lo que el buscador ya había encontrado.
*Severidad: alta. En un panel se busca una persona, no un nombre comercial.*

**T4 · Las acciones existen, pero no donde se necesitan.** El inventario de POST es amplio (activar compra, cancelar licencia, alternar flag, crear clave, cargar matriz…). El problema es dónde están: dentro de una ficha, en otro tab, o detrás de un `confirm`. **No hay una sola acción en lote** y **no hay deshacer**: una cancelación por error se arregla concediendo otra licencia a mano.
*Severidad: alta.*

**T5 · El rol se declara pero no se aplica.** `ALCANCES_ROL` dice: *analista = solo lectura*, *soporte = ficha y acceso*, *admin = no gestiona equipo*. En código solo hay `exigir_superadmin` en 4 acciones de equipo y 3 de precios. Todo lo demás —suspender acceso, cancelar licencias, alternar flags, crear API keys, enviar correos— no comprueba rol, y **el menú muestra todas las secciones a todos**. Es a la vez un riesgo y una mala experiencia: el operador de soporte ve «Equipo» y solo descubre que no puede cuando envía el formulario.
*Severidad: alta (seguridad).*

**T6 · Confirmar no es proteger.** Todo lo delicado usa `window.confirm` con un texto. No hay motivo obligatorio, no hay papelera, no hay deshacer, y varias acciones destructivas se disparan desde un `<button class="link">` pequeño.
*Severidad: media.*

**T7 · La información está, pero no se puede leer.** KPIs sin comparativa ni rango; auditoría sin fechas; recibos y comprobantes que hay que descargar; contadores que se calculan pero no se pintan (Soporte tiene contador y no tiene badge en el menú).
*Severidad: media.*

**T8 · El contenido no es editable por quien lo posee.** JSON crudo, sin vista previa ni diff. Es el único sitio del panel donde un error de sintaxis es la forma normal de equivocarse.
*Severidad: media.*

---

## 6. Lo que ya está bien (y no hay que tocar)

- **La arquitectura de navegación.** `panel_arquitectura.py` como fuente única, pestañas por área, atajos `G+letra`, ⌘K, redirecciones de rutas antiguas y `es_destino_panel` para `volver` (anti open-redirect). Esto es criterio de producto, no accidente.
- **La ficha de cliente como centro.** Unificar licencias, cobros, CRM y notas en una ficha fue el movimiento correcto; casi todo lo que falta es *añadir* a esa ficha, no rehacerla.
- **Analítica.** Filtros combinables, paginación, exportación, presencia en vivo. Es el listón.
- **Los chips con contadores.** Ver «cuántos hay» antes de filtrar es exactamente lo que se pide a un panel. Está en varias pantallas y debería estar en todas.
- **Las vistas guardadas.** Buena idea, bien implementada; solo le falta guardar el orden y estar en más listas.
- **El comportamiento ante fallos de datos.** La ficha degrada con aviso en vez de romper (rollback explícito, lectura cerrada por RLS). Eso no se toca.

---

## 7. Lo que propongo

Cuatro fases, ordenadas por relación impacto/esfuerzo. Cada una es entregable y verificable por separado; ninguna obliga a rehacer la anterior.

### Fase 0 · Saneamiento (1–2 días) — hacer ya, sin esperar decisión

| # | Qué | Dónde | Por qué |
|---|---|---|---|
| 0.1 | CSV de Contratos con `q` y `estado` | `ingresos_contratos.html` + ruta `contratos.csv` | El botón apuntaba a una ruta inexistente (404) |
| 0.2 | `volver` de Soporte conserva filtros | `clientes_soporte.html` | Cada cambio de estado te deja en la lista completa |
| 0.3 | Badge de Soporte en el menú | `nav_panel` | El contador ya se calcula y no se pinta |
| 0.4 | Estado tipado en Sistema › Estado | `contexto_sistema` | El color no puede depender de `'error' in texto` |
| 0.5 | Resultado de ⌘K de compra/licencia resalta la fila | `panel_busqueda.py` + plantillas | Buscas una compra y te deja a mirar la lista |
| 0.6 | `volver` de Compras conserva filtros | `ingresos_compras.html` | Igual que 0.2 |

**Criterio de aceptación:** los seis son cambios de una tarde cada uno, sin migración y sin tocar el esquema. Si algo de esto rompe un test, se revierte sin afectar a lo demás.

### Fase 1 · «Listas que se pueden usar» (4–6 días) — el P0 de verdad

**Qué.** Un patrón único de lista, con una especificación por pantalla, no una plantilla copiada diez veces:

- `ListaPanel` en `panel_contextos.py`: columnas, filtros, orden permitido, tamaño de página, acciones por fila.
- **Paginación y orden en SQL** (`LIMIT/OFFSET` + `ORDER BY` con lista blanca), porque el orden en Python no sobrevive a la página 2.
- Un macro Jinja `_tabla.html` que pinta toolbar + chips + cabeceras ordenables + paginador + acciones, y que **genera el CSV con los mismos filtros** (una sola fuente para pantalla y exportación).
- Filas por página: 25 / 50 / 100, con memoria en la URL (`?pagina=2`).
- Selección múltiple con barra de acciones que aparece al marcar (la base para la Fase 2).

**Orden de migración**, por dolor (los siete hechos, en este orden):

1. ✅ **Compras** (hoy se revisa a ciegas)
2. ✅ **Soporte** (crece sin control)
3. ✅ **Renovaciones** (dinero recurrente)
4. ✅ **Ventas**
5. ✅ **Cobros**
6. ✅ **Contratos**
7. ✅ **Auditoría** (con fechas, orden y CSV)

**No migrar:** Pipeline, Hoy ni Analítica. Tienen otra forma y funcionan.

**Archivos:** `app/services/panel_contextos.py`, `app/templates/admin/partes/_tabla.html` (nuevo), los `partes/*.html` de las siete pantallas, y una función `listar()` por pantalla que devuelva `(filas, total, filtros)`.

**Criterio de aceptación:** en las siete pantallas, buscar + filtrar + ordenar + paginar + exportar dan **el mismo conjunto de filas**. Un test parametrizado por pantalla lo verifica.

**Cómo quedó (22/10/2026).** La pieza compartida no es un macro de tabla —cada pantalla tiene columnas y acciones muy distintas— sino tres piezas pequeñas que sí se repiten: `panel_listas.paginar_consulta`/`paginar_lista` (recorte y meta), `panel_listas.paginador` (URLs y números) y `partes/_paginador.html` (el marcado). Cada servicio expone su lista de columnas ordenables (`ORDENES_COMPRAS`, `ORDENES_RENOVACIONES`, `ORDENES_VENTAS`, `ORDENES_COBROS`, `ORDENES_AUDITORIA`) y su `filtrar_*`/`ordenar_*`, que comparten la pantalla y el CSV. Se descartó `_tabla.html` genérico: obligaba a meter HTML de acciones dentro de una estructura de datos y perdía la legibilidad de cada pantalla.

**Impacto:** es el cambio que hace que el panel se sienta «de verdad». Todo lo demás se apoya aquí.

### Fase 2 · «Actuar sin salir de la lista» (3–4 días) — *responder soporte, descartado*

> **Estado (22/10/2026):** la parte de responder tickets desde el panel **no se hace** por decisión del titular, que contesta desde su correo. Las acciones en lote y el menú `⋯` por fila siguen siendo válidos como Fase 2bis si algún día hacen falta; hoy no son prioritarios.

- **Acciones en lote** en Compras («activar marcadas»), Soporte («asignar a…», «marcar resueltas»), Renovaciones («avisar a las marcadas»). Con resumen previo («12 compras, 1.480 US$») y confirmación que diga el número.
- **Responder soporte desde el panel.** Requiere migración pequeña en `mensajes_soporte`: `respuesta`, `respondida_por_email`, `respondida_at`, `prioridad`, `asignado_email`. Envío por Resend con plantilla, y la respuesta visible en la ficha del cliente (pestaña Actividad). Es la función que más cambia el día a día.
- **Plantillas de respuesta** (3–5 guardadas, editables en Sistema).
- **Menú `⋯` por fila** en Directorio, Ventas, Contratos y Cobros: ver ficha, recibo, copiar referencia, suspender, reclamar.
- **Motivo obligatorio + deshacer** en las tres acciones destructivas reales (cancelar licencia, suspender acceso, rechazar compra). El «deshacer» puede ser un POST inverso desde el aviso de éxito, no un sistema de papelera.

**Criterio de aceptación:** 15 compras pendientes se resuelven en 2 acciones y sin recargar 15 veces; un ticket se responde sin abrir el correo; toda cancelación deja motivo y se puede revertir desde el propio aviso.

### Fase 3 · «Hoy como centro de mando» (3–4 días)

- **Bandeja única** con origen, cliente, importe/urgencia y tres gestos: **asignar**, **posponer**, **hecho**. Persistencia mínima: tabla `tareas_panel(clave, tipo, ref_id, asignado_email, pospuesta_hasta, resuelta_at, resuelta_por)`, sin duplicar los datos de origen.
- **KPIs con comparación** contra el periodo anterior (se calcula de `licencias`/`compras`, no hace falta histórico nuevo).
- **«Desde tu última visita»** al principio de Hoy: ventas, altas, tickets y errores nuevos desde el último acceso del operador.
- Enlaces de cada tarjeta al listado **ya filtrado** (no a la pestaña en general).

**Criterio de aceptación:** abrir el panel por la mañana contesta tres preguntas sin hacer clic: *¿qué pasó?*, *¿qué me toca?*, *¿qué está peor que la semana pasada?*.

### Fase 4 · «Sistema y contenido de verdad» (2–3 días)

- **Auditoría:** fechas, paginación, CSV y enlaces a la entidad. Buscador de organización por nombre (no por ID).
- **Contenido:** editor por campos con esquema declarado, vista previa y diff publicado/borrador.
- **Accesos:** flags y claves restringidos por rol, confirmación al apagar un flag, caducidad y último uso de cada clave.
- **Equipo:** invitación por correo al dar de alta.
- **Automatizaciones:** previsualización («afectará a N») e historial de ejecuciones.
- **Rendimiento:** contadores acotados por consulta (o cacheados 60 s) y todas las consultas del panel con `LIMIT`.

**Criterio de aceptación:** cualquier incidente se puede reconstruir en el panel con fechas y enlaces, sin leer trazas ni pedir IDs.

### Fuera de alcance (a propósito)

- Reescribir la ficha de cliente: funciona, solo se le añade.
- Un rediseño visual: la paleta, el sidebar y los componentes ya son coherentes. Esto es sobre capacidad, no sobre estética.
- Un sistema de permisos granular por campo: no hace falta; cuatro roles con límites claros bastan.

---

## 8. Definición de «panel útil» (para no discutir de gustos)

Dentro de seis meses, cualquier pantalla del panel debería cumplir:

1. Toda lista se puede **buscar**, **filtrar**, **ordenar** y **paginar**, y el CSV coincide con lo que se ve.
2. Desde cualquier aviso o KPI se llega en **un clic** al objeto concreto, no a la pestaña.
3. Cualquier dato que el panel muestra se puede encontrar **escribiendo lo que el cliente diría** (correo, nombre, referencia, número de compra).
4. Toda acción que aparece se puede ejecutar **sin salir de la pantalla** donde aparece el problema.
5. Lo que se hace en lote se hace en lote, y la confirmación dice **cuántos** y **cuánto**.
6. Toda acción destructiva pide **motivo** y se puede **deshacer**.
7. Un ticket de soporte se responde **desde el correo del operador**, con el número y el mensaje citados, sin copiar datos a mano. *(Decisión del titular: no dentro del panel.)*
8. El rol decide qué se ve **y** qué se puede hacer, en el menú y en el servidor. *(Aplazado: hoy hay un solo operador.)*
9. Los números comparan con algo (ayer, la semana pasada, el mes pasado).
10. Cualquier cambio en el panel es **rastreable**: quién, cuándo, sobre qué, con enlace.
11. Nada de la pantalla principal tarda más de lo que tarda un café, con 10 o con 500 clientes.
12. El dueño del negocio puede cambiar un texto de la web **sin escribir JSON**.

Los puntos 1, 4, 5, 7 y 8 son el 80 % del beneficio.

---

## 9. Decisiones (actualizado el 22/10/2026)

1. ✅ **Fase 0 + Fase 1 primero.** Hechas: las siete listas del panel buscan, ordenan, paginan y exportan con el mismo criterio.
2. ❌ **Responder soporte desde el panel: no.** El titular contesta desde su correo. Se deja el enlace de correo bien armado (número de ticket + mensaje citado) y no se toca `mensajes_soporte`.
3. ⏸ **Roles reales: aplazado.** Un solo operador con acceso; no hay nada que repartir todavía. Si algún día entra otra persona, la tabla de permisos por acción queda descrita en el punto 5 del veredicto y cuesta 1–2 días.
4. ❓ **Bandeja de Hoy (`tareas_panel`): sin decidir.** La pregunta es si merece la pena poder **posponer** («esto lo miro el lunes») y **marcar hecho** lo que aparece en Hoy, o si la lista actual le sirve tal cual. Con un solo operador, «asignar a alguien» no aporta; posponer y cerrar, sí.

---

## Anexo A · Acciones que hoy existen y no tienen sitio donde se necesitan

| Acción (POST) | Existe en | Se necesita también en |
|---|---|---|
| Conceder / renovar acceso | Ficha › Acceso, Contratos, Renovaciones (fijo 1 año) | Renovaciones con plan/importe; Directorio |
| Cancelar licencia | Contratos (inline) | Directorio, ficha › Resumen, menú de fila |
| Activar / rechazar compra | Compras (tarjeta) | Ficha › Cobros (hoy solo enlaza), lote |
| Cambiar estado de soporte | Soporte (nota interna) | Ficha › Actividad, bandeja de Hoy |
| Enviar avisos de vencimiento | Renovaciones (todos) | Renovaciones (solo marcados) |
| Alternar flag | Accesos | — (falta confirmación y rol) |
| Crear / revocar API key | Accesos | — (falta rol, caducidad, último uso) |
| Cargar matriz de precios | Precios | — (falta historial) |
| Suspender acceso | Ficha › Acceso | Directorio, Contratos |
| Guardar CRM / notas | Ficha › Gestión, Pipeline | Soporte (al cerrar un ticket) |

## Anexo B · Por qué el rendimiento es parte de esta auditoría

`contexto_base` llama a `contadores_panel` en **cada** petición del panel. Ese cálculo, más `resumen_admin` y `notificaciones_admin`, recorren organizaciones, licencias, compras, membresías y usuarios completos. No hay `LIMIT` que lo acote porque ninguna lista pagina.

Con el catálogo actual es imperceptible. El día que haya 300 organizaciones, el panel se sentirá lento **en todas las pantallas a la vez**, y no habrá una pestaña que arreglar: habrá que rehacer lo mismo que la Fase 1 y la Fase 3 proponen. Hacerlas ahora es más barato que hacerlas con prisa después.

---

*Documento generado a partir de la lectura del código en `main` @ `2527098`: `app/panel_arquitectura.py`, `app/routers/admin.py`, `app/routers/admin_paginas.py`, `app/services/panel_*.py`, `app/templates/admin/**`.*
