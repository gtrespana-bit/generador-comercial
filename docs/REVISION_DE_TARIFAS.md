# Revisar tarifas: cómo se pide, cómo se pospone y cómo se quita

> Estado: implementado el 04/11/2026 (revisión de tarifas `t9b4d7e2c5f8` +
> recordatorio `u1c5e8b3d7a9`). Sustituye el comportamiento descrito en el PR
> #181, donde el aviso solo se cerraba confirmando.

## El problema de producto

El generador no inventa precios: compone el importe con las tarifas de recursos
de la empresa. Una empresa que paga **15 US$/h** por un oficial y otra que paga
**25 US$/h** deben cotizar distinto con las mismas mediciones — eso es el
producto funcionando. El fallo caro es el de al lado: una cuenta recién creada
cotiza con referencias de fábrica (de otro país, de otro convenio o de hace
meses) y nada se lo dice.

La primera versión pedía confirmar las tarifas, pero solo tenía dos desenlaces:
**confirmar** o **no hacer nada**. Eso convertía un consejo en un muro:

- quien decidía «lo miro la semana que viene» veía el mismo aviso al día
  siguiente, y al otro;
- quien ya trabajaba con sus precios no tenía forma de decir «no me lo
  repitas» sin confirmar tarifas que no había mirado;
- un aviso que no se puede quitar acaba siendo un aviso que se ignora, y con él
  se ignora el dato que decide el importe.

## Las tres decisiones

El producto separa ahora dos cosas que antes iban juntas:

| Pregunta | Dónde se responde | Qué cambia |
|---|---|---|
| ¿Esta tarifa es la mía? | botón **Confirmar** (fila, ficha, pantalla de revisión) | `recursos.precio_revisado_at` |
| ¿Cuándo quiero que me lo recuerdes? | **Ahora no** / **No volver a recordármelo** | `configuracion.tarifas_recordatorio_*` |

Ninguna de las tres rutas del recordatorio toca un precio ni una fecha de
revisión: **silenciar no es confirmar**. Al silenciar, la pantalla de revisión
sigue diciendo exactamente lo mismo que antes; lo único que desaparece es la
interrupción en el panel, en el catálogo y en la ficha del presupuesto.

### Estados del recordatorio

`app/services/revision_precios.py::estado_recordatorio` es la única fuente de
verdad; ninguna pantalla decide por su cuenta (si lo hicieran, silenciar en una
no silenciaría en las demás).

- `visible` — toca enseñarlo (o nunca se decidió nada).
- `pospuesto` — se guardó una **fecha** (`tarifas_recordatorio_pospuesto_hasta`).
  Hasta entonces no se interrumpe; después vuelve solo, aunque nadie entre a la
  aplicación. Se guarda una fecha y no un contador justo por eso.
- `silenciado` — no vuelve a interrumpir. La pantalla sigue accesible en
  *Recursos › Revisar tarifas* y ahí se reactiva.

## Recorrido del usuario

1. **Al entrar** (panel): tarjeta «Tu catálogo aún cotiza con precios de
   referencia», con el porcentaje, cuántas son de mano de obra y dos botones:
   *Revisar mis tarifas* y *Ahora no*.
2. **Pantalla de revisión** (`/recursos/revisar`): solo las pendientes, mano de
   obra primero. La selección **arranca vacía**: confirmar es una decisión, no
   el efecto de pulsar «Guardar» sin mirar. Hay *Marcar todas* y *Desmarcar
   todas* (porque si existe una, tiene que existir la otra), un contador de
   seleccionadas y un botón de confirmación que solo se activa cuando hay algo
   marcado.
3. **Una tarifa, un clic**: botón *Confirmar* en cada fila de la tabla, en la
   ficha del recurso y en el `✓` de la lista de recursos. No abre nada, no
   cambia el precio y funciona sin JavaScript.
4. **Tu precio en el mismo gesto**: desde la ficha, el campo «Tu precio» y el
   botón *Actualizar mi precio y confirmar* guardan el precio propio de la
   organización (con su propagación a las partidas) y dejan la fecha.
5. **Las salidas opcionales**, juntas y en segundo plano al pie de la pantalla:
   *¿Lo miras en otro momento?* (una semana / un mes / tres meses), *Lo hago por
   mi cuenta* (silencio) y *He revisado todas* (confirmación en bloque, que
   sigue existiendo y ahora se llama por lo que hace).

## Qué NO hace

- No bloquea nada: se puede cotizar con las referencias de mercado sin pasar
  por aquí. El aviso informa; no impide crear presupuestos.
- No cambia precios al confirmar: confirmar sin escribir un precio significa
  «la miré y es la mía», y no crea ningún override.
- No silencia la guía de inicio: el paso «Ajusta tus tarifas» sigue ahí hasta
  que se confirma; lo que se quita con el silencio es la interrupción, no el
  dato pendiente.
- No inventa: si la base no tiene las columnas del recordatorio (despliegue sin
  migración), las acciones responden con un aviso claro en vez de fingir que se
  guardaron.

## Ficheros

| Ruta | Qué contiene |
|---|---|
| `app/services/revision_precios.py` | `resumen_revision`, `estado_recordatorio`, `recordatorio_visible`, `POSPOSICIONES` |
| `app/routers/recursos.py` | `GET/POST /recursos/revisar`, `/posponer`, `/silenciar`, `/reactivar`, `/confirmar-todas`, `/recursos/{id}/revisado` |
| `app/templates/recursos/revisar.html` | la pantalla (selección vacía + confirmar por fila + tres salidas) |
| `app/templates/recursos/form.html` | estado de la tarifa y «Actualizar mi precio y confirmar» |
| `app/templates/recursos/list.html` | `✓` por fila y el contador de pendientes |
| `app/templates/_aviso_flash.html` | `?msg=` / `?error=` visibles en todas las vistas (antes se perdían) |
| `migrations/versions/u1c5e8b3d7a9_recordatorio_de_tarifas.py` | las dos columnas del recordatorio |
| `docs/staging_upgrade_u1c5e8b3d7a9.sql` | aplicación manual en Supabase |
| `tests/test_revision_de_tarifas.py` | 28 pruebas del contrato completo |

## Pruebas que fijan el contrato

- posponer silencia el aviso **sin confirmar** y el aviso vuelve solo cuando la
  fecha queda atrás;
- silenciar no cambia `precio_revisado_at` ni `onboarding_precios_revisados`, y
  se puede deshacer desde la misma pantalla;
- un plazo inventado (`plazo=siempre`) no silencia nada y devuelve error;
- confirmar una tarifa concreta (ficha, lista, fila de la tabla) deja la fecha y
  no crea overrides si no se escribió precio;
- confirmar con precio guarda el override y la fecha en un solo gesto;
- la pantalla ofrece las tres salidas y las casillas nacen sin marcar.
