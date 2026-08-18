# Cobro y licencias (E1-059 / E1-060)

Fecha: **16/08/2026**. Documento de decisión: recoge la investigación.

> **Decisión adoptada (16/08/2026): cobro manual para el piloto** (opción B).
> La vía A (autónomo en España + Stripe) queda acordada como paso previo al
> cobro recurrente. E1-060 está implementado al completo: panel de operador,
> recibo PDF, corte automático con `COTIZAT_EXIGIR_LICENCIA` y avisos de
> vencimiento por correo (ver `docs/PANEL_DE_OPERADOR.md` §6 y
> `docs/PROCESO_PILOTOS.md`).

> Aviso: esto no es asesoramiento fiscal ni legal. Antes de cobrar al primer
> cliente conviene una consulta con un asesor en España (y, si se factura desde
> Venezuela, también allí).

---

## 1. El condicionante que lo define todo

CotizaT se pensó para clientes en Latinoamérica, pero **el problema no es dónde
está el cliente, sino desde dónde se cobra**:

- **Stripe no opera en Venezuela.** No hay forma de darse de alta con una
  entidad venezolana.
- **Wise y Payoneer** imponen restricciones fuertes a residentes venezolanos
  (Wise directamente veta el país; Payoneer exige una cuenta bancaria no
  venezolana para retirar).
- **Paddle y Lemon Squeezy** (modelo *merchant of record*, que además resuelve
  los impuestos) exigen una entidad legal en un país soportado. Venezuela no lo
  es.

**Dato decisivo aportado por el titular (16/08/2026):** es de **nacionalidad
española y reside también en España**, trabajando temporalmente entre España y
Venezuela. Eso cambia el escenario por completo: la vía española está abierta.

---

## 2. Opciones reales

### Opción A — Autónomo en España + Stripe *(recomendada para cobrar en serio)*

Darse de alta como autónomo (**modelo 036** en Hacienda y **RETA** en Seguridad
Social, en ese orden) y usar Stripe con la entidad española.

**A favor**
- Stripe funciona con normalidad: cobro con tarjeta desde cualquier país,
  suscripciones, reintentos y cancelaciones ya resueltos.
- Factura española válida: desaparece la ambigüedad de «documento comercial no
  fiscal» para **la venta de CotizaT** (ojo: eso no cambia el alcance de los
  documentos que la app genera para los clientes, que siguen siendo no
  fiscales).
- Comisión baja: ~2,9 % + 0,30 € frente al ~5 % + 0,50 $ de un *merchant of
  record*.
- Da una razón social real para `COTIZAT_LEGAL_ENTITY` y para los términos.

**En contra**
- Cuota de autónomo (tarifa plana ~88 €/mes el primer año; después por tramos).
- Obligaciones trimestrales: IVA (modelo 303) e IRPF (modelo 130).
- Si se vende a **consumidores particulares de la UE** por encima de
  10.000 €/año, hay que aplicar el IVA del país del cliente y declarar por
  **ventanilla única OSS** (modelo 369). Con clientes latinoamericanos y/o
  empresas esto normalmente no aplica, pero conviene tenerlo presente.
- Requiere decidir la residencia fiscal con criterio: si se reside la mayor
  parte del año en Venezuela, la situación es mixta y **hay que consultarlo**.

### Opción B — Cobro manual *(recomendada para el piloto inmediato)*

Acordar el pago por transferencia, Zelle, Binance o Pago Móvil, y activar la
cuenta a mano.

**A favor**
- Cero integración, cero comisiones de pasarela, disponible hoy.
- Con 5–20 clientes de piloto es perfectamente operable.
- No bloquea nada: se puede empezar así y migrar a Stripe después.

**En contra**
- Sin recibo automático ni renovación automática: todo se lleva a mano.
- No escala más allá de unas pocas decenas de clientes.
- Cobrar de forma recurrente sin alta fiscal **no es sostenible**: en cuanto la
  actividad es habitual, hay que regularizarla.

### Opción C — Merchant of record (Paddle / Lemon Squeezy)

Solo viable **con la entidad española ya creada**. Cobra ~5 % + 0,50 $ pero se
encarga del IVA/OSS de todo el mundo.

Tiene sentido si la venta internacional a particulares crece y la carga fiscal
del OSS se vuelve pesada. **Hoy no compensa**: más caro y resuelve un problema
que todavía no existe.

### Recomendación

1. **Ahora, para el piloto**: opción B (manual). No frena el desarrollo.
2. **Antes de cobrar de forma recurrente**: opción A (autónomo en España +
   Stripe), que es la única que sostiene el cobro habitual con factura válida.
3. **Más adelante, si hace falta**: reevaluar la opción C.

---

## 3. E1-060 — Registro interno de licencias

**Decisión del titular (16/08/2026): debe vivir _dentro_ de la aplicación**, en
un panel de administración propio.

### Qué implica (y por qué no es trivial)

Hoy **no existe** ningún concepto de superadministrador: toda la autorización
de CotizaT se apoya en la **membresía de una organización**, y todas las tablas
de negocio son *tenant* (llevan `organizacion_id` y están protegidas por RLS).
Una licencia **no pertenece a ninguna organización**: es un dato del negocio del
titular *sobre* una organización. No encaja en el modelo actual, así que hay que
diseñarlo con cuidado:

1. **Tabla no-tenant** (p. ej. `licencias`), fuera de `TenantMixin`, con su
   propia política RLS: legible **solo** por el rol operador, nunca por el rol
   de aplicación de un cliente. Es el punto delicado: una licencia mal expuesta
   filtraría a un cliente cuánto paga otro.
2. **Rol de operador del producto**, distinto de los roles de organización, con
   una lista explícita de cuentas autorizadas por variable de entorno (no una
   columna que pueda modificarse desde la propia aplicación).
3. **Panel `/admin/licencias`**: alta, renovación, estado (activa, vencida,
   cancelada), importe, método de cobro y notas. Protegido igual que el resto:
   CSRF, CSP con nonce, sin datos en GET.
4. **Recibo en PDF** con los datos del cliente y el período pagado, reutilizando
   el generador existente (`app/services/pdf.py`).
5. **Auditoría**: quién creó o modificó cada licencia y cuándo.

### Riesgo principal a vigilar

El panel de operador es, por definición, **una excepción al aislamiento
multi-tenant** que el resto del sistema defiende. Debe:

- no permitir **leer datos de negocio** de ninguna organización (solo el hecho
  de la licencia: quién, cuánto, hasta cuándo);
- estar cubierto por pruebas que fallen si un usuario normal alcanza la ruta;
- quedar fuera del alcance de las políticas de tenant, sin debilitarlas.

Por eso conviene abordarlo **como su propio bloque**, no de pasada.

---

## 4. Estado y siguiente paso

| Pieza | Estado |
| --- | --- |
| E1-053 Preguntas frecuentes | ✅ `/legal/preguntas` |
| E1-054 Alcance del soporte | ✅ `/legal/soporte` §2–§3 |
| E1-055 Reporte de errores | ✅ `/legal/soporte` §5 |
| E1-059 Método de cobro | ✅ **decidido (16/08/2026): cobro manual para el piloto**; Stripe+autónomo antes del cobro recurrente |
| E1-060 Registro de licencias | ✅ panel `/admin/licencias` desplegado en producción el 16/08/2026; recibo PDF, corte automático y avisos de vencimiento implementados el 16/08/2026 noche (migración `b7c4a9e2d31f`) |
| E1-061 Activación manual de pilotos | ✅ proceso documentado en `docs/PROCESO_PILOTOS.md` (16/08/2026) |

El registro interno hacía falta se cobrase como se cobrase; con la decisión de
cobro manual tomada, las tres piezas que esperaban (recibo, corte y avisos)
quedaron construidas en la misma sesión.

**Actualización 18/08/2026.** El titular ensayó el circuito completo en staging
(compra con comprobante → activación desde `/admin/compras` → plan visible) y lo
dio por bueno. Se cerró después el lado del comprador, que era lo único
realmente «manual» que quedaba: al activar la compra el cliente **recibe un
correo** con la fecha de vencimiento y el **recibo PDF adjunto**, y puede
volver a descargarlo cuando quiera desde `/configuracion`
(`GET /pago/recibo/{compra_id}.pdf`, migración `c7f1a3b9d425`). Detalles en
`docs/PANEL_DE_OPERADOR.md` §7. Sigue sin haber renovación automática: eso llega
con Stripe.
