# Plan de respuesta a incidentes (E4-032)

> Documento operativo del titular. Se lee junto con
> `docs/MONITORIZACION_Y_DIAGNOSTICO.md` (qué vigila y dónde mirar),
> `docs/RESPALDO_Y_RESTAURACION_WEB.md` (cómo se restaura) y
> `docs/PENDIENTES_OPERATIVOS.md` (checklists de paneles).
>
> Estado: **definido el 19/08/2026**. El simulacro que lo ensaya es
> `docs/SIMULACRO_CAIDA_Y_RECUPERACION.md` (E4-043).

## 0. Principio rector

**Primero restaurar el servicio, después entender la causa.** Un incidente en
vivo no es el momento de diagnosticar con calma: se aplica el runbook, se
estabiliza y se documenta. El análisis profundo viene después, con calma y con
los datos del incidente ya registrados.

Segundo principio: **los datos del cliente nunca se sacrifican por restaurar
antes**. La suspensión corta el acceso pero no toca datos (E4-036); un rollback
de despliegue no borra nada; una restauración de respaldo se hace sobre una
base de pruebas o sobre producción solo tras confirmar el alcance de lo que se
pierde.

## 1. Qué cuenta como incidente

| Severidad | Definición | Ejemplo |
| --- | --- | --- |
| **S1 — Crítico** | El servicio no está disponible, o un cliente no puede acceder a sus datos, o hay sospecha de acceso no autorizado a datos de clientes. | `cotizat.online` responde 5xx o no responde; un cliente reporta que ve presupuestos de otra empresa; alerta de UptimeRobot caída. |
| **S2 — Alto** | El servicio funciona pero con degradación importante, o un proceso de pago/renovación falla, o un correo transaccional no sale. | El cron de mantenimiento falla varios días seguidos; los PDFs tardan minutos; el recordatorio de vencimiento no se envía. |
| **S3 — Medio** | Fallo acotado sin impacto en clientes, o fallo interno del operador. | `/readyz` reporta un chequeo en rojo que no afecta al uso; error al enviar el correo de alerta interno; un panel del admin falla. |
| **S4 — Bajo** | Cosmético o de proceso. | Texto mal renderizado, enlace roto en una página pública, documentación desactualizada. |

## 2. Quién y cómo se entera

- **Alerta automática interna**: el cron `/api/cron/mantenimiento` (02:00 UTC)
  ejecuta los chequeos de `/readyz` y, si fallan, envía `alerta_operador` a
  todos los correos de `COTIZAT_OPERADORES` (E4-023).
- **Vigilante externo** (pendiente de panel, recomendado): UptimeRobot sobre
  `https://cotizat.online/healthz` cada 5 minutos. Es el único que ve caer la
  app entera, porque si la app cae, el cron interno no corre.
- **El cliente**: el correo `soporte@cotizat.online` y el formulario de
  soporte. Cualquier reporte de cliente es al menos S2 hasta demostrar lo
  contrario.

## 3. Runbooks por severidad

### S1 — Crítico (objetivo: < 30 minutos hasta estabilizar)

1. **Confirmar el alcance**: abrir `https://cotizat.online/readyz` y
   `https://cotizat.online/healthz`. Anotar qué chequeos fallan.
2. **¿Es el despliegue?** → Vercel → Deployments: si el último despliegue de
   producción es reciente (última hora) y coincide con el inicio del fallo,
   hacer **rollback al despliegue anterior** (botón *Rollback*). Es reversible
   y no toca datos.
3. **¿Es la base de datos?** → Supabase → Database: estado del proyecto y de
   las consultas. Si el proyecto está en pausa por inactividad (plan free),
   reactivarlo desde el panel y avisar a los operadores. Si hay corrupción o
   pérdida, NO tocar nada más: seguir el procedimiento de restauración de
   `docs/RESPALDO_Y_RESTAURACION_WEB.md` §4 y, si aplica, el simulacro E4-043.
4. **¿Es el almacenamiento?** → Supabase → Storage: estado del bucket
   `cotizat-private`. Los PDFs y anexos se sirven por proxy desde la app; si
   el bucket responde mal, los presupuestos aparecen sin anexos pero el
   servicio sigue en pie.
5. **¿Sospecha de acceso no autorizado?** → no tocar nada, recopilar
   evidencia (logs de Vercel/Supabase del período), cortar lo que se pueda
   cortar (revocar URLs firmadas, rotar `CRON_SECRET` y claves si hubo
   exposición), y documentar. El análisis se hace con calma y con la
   evidencia guardada.
6. **Comunicar**: si el incidente dura más de 15 minutos o afecta a más de un
   cliente, avisar a los operadores (correo interno) con estado y hora
   estimada. Nunca prometer plazos que no se puedan cumplir.
7. **Registrar**: al estabilizar, escribir en `docs/INCIDENTES.md` (crear el
   archivo la primera vez) qué pasó, cuándo, qué se hizo, qué faltó y qué
   cambio evita que se repita.

### S2 — Alto (objetivo: mismo día)

1. Revisar `/readyz` y los logs de Vercel del período (Observability → Logs).
2. Si es un proceso programado: Vercel → Cron Jobs → *View Logs* y comprobar
   las últimas invocaciones de `recordatorios-vencimiento` (13:00 UTC) y
   `mantenimiento` (02:00 UTC).
3. Si es el cobro/renovación: panel `/admin` → Compras y Licencias. El cobro
   es manual: un pago puede esperar horas, pero la licencia de un cliente que
   ya pagó debe activarse el mismo día.
4. Si es un correo transaccional: panel `/admin/emails` → enviar prueba de
   los 8 correos y verificar que llegan.
5. Registrar en `docs/INCIDENTES.md` si requirió más de una hora de trabajo o
   afectó a un cliente.

### S3 / S4 — Medio/Bajo

- Se gestionan en la siguiente sesión de trabajo, salvo que se acumulen o
  afecten a más de un cliente (entonces suben a S2).
- Registrarlos en `docs/INCIDENTES.md` como «pendientes conocidos».

## 4. Contactos y accesos (rellenar por el titular)

| Recurso | Dónde está | Acceso |
| --- | --- | --- |
| Vercel | panel de Vercel, proyecto cotizat | correo del titular |
| Supabase | panel de Supabase, proyecto de producción | correo del titular |
| Zoho (correo soporte) | panel de Zoho | correo del titular |
| UptimeRobot | panel de UptimeRobot (pendiente de crear) | correo del titular |
| Operadores | `COTIZAT_OPERADORES` en Vercel → Env vars | — |

## 5. Qué NO hacer en un incidente (lecciones ya pagadas)

- **No borrar ni restaurar por encima de producción sin confirmar el
  alcance.** Un respaldo restaurado sobre producción pisa lo que haya cambiado
  después de la copia.
- **No rotar credenciales a ciegas** durante un incidente en vivo: romper el
  correo transaccional o el cron mientras se investiga agrava el problema.
- **No afirmar la causa sin evidencia.** La lección de la sesión del 18/08
  («verificar antes de afirmar») aplica doble en incidentes: comprobar el
  estado real (`/readyz`, logs, despliegues) antes de dar nada por hecho.
- **No dejar el incidente sin registro.** Un incidente sin `docs/INCIDENTES.md`
  es un incidente que se repetirá igual.

## 6. Revisión

Este plan se revisa en el simulacro E4-043 (cada vez que se ensaye la
restauración) y después de cada incidente S1/S2. La versión vigente siempre
es la de `main`.
