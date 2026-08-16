# Proceso manual de activación de pilotos (E1-061)

Fecha: 16/08/2026 (America/Caracas). Complementa a `docs/PANEL_DE_OPERADOR.md`
(cómo se usa la pantalla) y a `docs/COBRO_Y_LICENCIAS.md` (por qué se cobra
así). Este documento es el **guion completo** para atender a los primeros
clientes de pago con cobro manual (E1-059).

Público: el titular operando el producto. Nada de aquí lo ejecuta un cliente.

---

## 0. Requisitos previos (una sola vez)

| Paso | Dónde | Estado |
| --- | --- | --- |
| Declarar operadores | `COTIZAT_OPERADORES` en Vercel (Production) + redeploy | ✅ hecho el 16/08/2026 |
| Correo transaccional | `RESEND_API_KEY` + `COTIZAT_EMAIL_FROM` en Vercel | ✅ hecho (SMTP de Supabase también usa Resend) |
| Migración `b7c4a9e2d31f` | Supabase → SQL Editor → `docs/staging_upgrade_b7c4a9e2d31f.sql` | ✅ aplicada el 16/08/2026 |
| **Conceder licencia de cortesía a la propia organización del titular** | Panel → «cortesia», duración larga, nota «uso del titular» | ⬜ hacerlo **antes** de activar el corte |
| Activar el corte | `COTIZAT_EXIGIR_LICENCIA=true` en Vercel + redeploy | ⬜ al empezar los pilotos de pago |
| Buzón `soporte@cotizat.online` | Reenvío en el proveedor del dominio | ⬜ cuando haga falta de verdad |

El orden importa: si el corte se activa sin licencia propia, **el titular
también se queda fuera** de su organización (el panel de operador sí seguirá
accesible, porque no depende de ninguna organización).

Tras aplicar la migración, `/readyz` debe responder
`"alembic": "head:b7c4a9e2d31f"` con `ok: true`, y muestra además
`"licencias": "exigida"` o `"no-exigida"` según el interruptor.

---

## 1. De la demostración al acceso (alta de un piloto)

1. **Demostración.** Se muestra el producto con el vídeo (E1-051) o una sesión
   guiada; la landing `/conocer` publica los precios del piloto
   (89 US$/año promocional —habitual 109— o 9,99 US$/mes el primer año
   —habitual 12,99—, configuración asistida y soporte incluidos).
2. **Registro del prospecto.** El cliente entra a `https://cotizat.online`,
   crea su cuenta, confirma su correo y crea su organización. No necesita
   nada más: con el corte activo verá la pantalla «Acceso suspendido» hasta el
   paso 4; con el corte aún apagado podrá trastear el modo demo.
3. **Cobro.** Se acuerda el método (transferencia, Zelle, Binance o Pago
   Móvil) y **solo cuando el pago está confirmado**:
4. **Licencia.** En el panel (`/admin/licencias`):
   - Tipo `pago`, duración `1 año` (o `1 mes` en plan mensual), importe y
     moneda reales, método y referencia de la operación en sus campos.
   - Nota interna con el acuerdo («piloto fundador, precio promocional»…).
5. **Recibo.** En el historial de la organización, enlace «recibo PDF»:
   se descarga y se envía al cliente por el canal acordado. El recibo declara
   que es comercial sin validez fiscal (hasta que exista razón social).
6. **Prueba gratuita opcional.** Si el prospecto quiere probar antes de pagar:
   tipo `prueba` con `7 días`. Si después paga, la licencia de pago se
   **encadena** al día siguiente del vencimiento de la prueba: nunca se
   restan días.

## 2. Seguimiento (rutina semanal, ~2 minutos)

1. Abrir `/admin/licencias` y mirar la cifra ámbar «Vencen en 15 días o
   menos».
2. Pulsar **Enviar avisos de vencimiento**: cada administrador de esas
   organizaciones recibe un correo (desde `no-responder@cotizat.online`)
   invitándole a renovar por `soporte@cotizat.online`. Cada licencia queda
   anotada con la fecha y los destinatarios; pulsar dos veces el mismo día no
   reenvía.
3. Si el aviso falla (proveedor caído), el panel lo dice y se puede reintentar
   en el momento: solo quedan anotados los envíos confirmados.

## 3. Vencimiento sin pago

- Al día siguiente del vencimiento, el corte automático deja a la organización
  en «Acceso suspendido». **Nada se borra**: presupuestos, clientes,
  catálogos y archivos siguen intactos.
- El propio mensaje de suspensión le dice al cliente cómo reactivar
  (escribir a soporte) y que sus datos siguen guardados.
- Cuando paga: nueva licencia `pago` desde el panel. El acceso vuelve solo al
  instante — el encadenado evita solapes si aún tenía días.

## 4. Gestos comerciales e incidencias

- **Compensar una caída del servicio:** tipo `compensacion` con la nota del
  motivo. No suma a ingresos.
- **Cortesía** (un mes regalado, uso del titular, familiares del proyecto):
  tipo `cortesia`, importe 0 obligatorio.
- **Cancelar:** desde el historial, con motivo obligatorio en la nota. Una
  licencia jamás se borra; la fila cancelada es la constancia.

## 5. Lo que este proceso NO hace (a propósito)

- No hay renovación automática ni cobro con tarjeta: eso llega con el alta de
  autónomo + Stripe (E1-059 ya lo deja decidido para cuando el volumen lo
  pida).
- No hay avisos programados por horario: el despliegue es serverless y no hay
  trabajos en segundo plano; el botón del panel es la cadencia. Si el número
  de pilotos crece lo bastante, se evalúa un cron externo llamando a una ruta
  protegida — hoy sería ingeniería prematura.
- El panel no muestra presupuestos, clientes ni precios de ningún cliente:
  solo licencias. Está probado en `tests/test_licencias.py`.
