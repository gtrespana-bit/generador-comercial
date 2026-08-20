# Moneda única en toda la aplicación (2026-08-19)

## Regla de producto

**El usuario nunca ve dos divisas en la misma pantalla.** El catálogo
(partidas, productos, recursos) se guarda internamente en USD —la base— y
cada pantalla lo muestra convertido a la moneda de la organización
(`configuracion.moneda_default` + `configuracion.tasa_cambio`), con su
código ISO siempre visible. Los presupuestos y facturas conservan su propia
moneda congelada (la del documento), que es la correcta para el cliente.

## Problemas corregidos

| Pantalla | Antes | Ahora |
|---|---|---|
| `/recursos` | Precio base en **USD** y, debajo, el de mercado en su divisa: dos monedas en la misma tabla; el total por familia sumaba USD crudo. | Base y mercado en la moneda de la organización; totales por familia y exportaciones (CSV/Excel) igual. |
| Formulario de recurso (nuevo/editar) | «Precio base (USD)»: se editaba en dólares aunque el resto hablara la moneda local; el precio fijado por lote también. | Todo el formulario y el precio fijo por lote en la moneda de la organización; el POST revierte a USD base antes de guardar (y la propagación a partidas sigue siendo en USD). |
| Panel `/inicio` y `/reportes` | Sumaban totales de presupuestos con monedas distintas y etiquetaban el resultado con la moneda de la organización. | Cada total se convierte por USD con la tasa congelada del propio presupuesto; sin tasa para el puente queda fuera del agregado (nunca se inventa). |
| Formulario de partida nueva | Etiqueta «USD» aunque el POST ya convertía desde la moneda local. | Etiqueta y símbolo de la moneda de la organización. |
| Moneda local elegida **sin tasa** | Las páginas etiquetaban «MXN» cifras que seguían en dólares. | Sin tasa válida la vista confiesa la base: muestra y etiqueta **USD** hasta que se configure la tasa (jamás inventa la conversión). |

## Superficies verificadas (ya eran correctas)

- `/partidas` (lista, filas por subcapítulo, ficha, buscador): convierte
  precio y costes con el mismo factor.
- `/productos` (lista y formularios): convierte y revierte al guardar.
- Presupuestos (lista, ficha, versiones, comparador, PDF), facturas,
  proyectos y propuestas públicas: moneda congelada del documento, etiquetada.
- Panel de precios de mercado (`/recursos/mercado`): cada referencia nacional
  con su moneda explícita (es un panel de datos de referencia por país).

## Implementación

- `app/routers/recursos.py` + `app/templates/recursos/*`: vista unificada
  con `resolver_precios_para_presupuesto_lote` (una consulta) y conversión
  de base/mercado; POSTs con `_a_moneda_base`.
- `app/routers/common.py`: `_contexto_moneda` nunca devuelve una moneda
  local con factor 1 (sin tasa ⇒ USD honesto) y añade
  `_importe_en_moneda_vista` (presupuesto → USD → moneda de la vista).
- `app/routers/inicio.py` y `reportes`: agregados convertidos.
- Regresiones: `tests/test_moneda_recursos.py` (10 pruebas).
