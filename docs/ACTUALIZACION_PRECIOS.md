# Actualización mensual de precios — proceso único

Proceso oficial para mantener frescas las referencias nacionales de
precios (Fase 2 de la hoja de ruta). Cadencia fijada por el titular:
**mensual**. `/readyz` lo vigila con la clave `precios_actualizados`: si
la última carga de cualquier país pasa de 40 días, marca `REVISAR` con
los países afectados (alarma blanda: no tumba `ok`).

Las fuentes de verdad son las 7 matrices de `basedatos_partidas/salida/`:

| Matriz | Mercados |
|---|---|
| `precios_recursos_latam.csv` | 16 países LatAm |
| `precios_recursos_espana.csv` | ES |
| `precios_recursos_estados_unidos.csv` | US (unidades de fuente imperiales) |
| `precios_recursos_reino_unido.csv` | GB |
| `precios_recursos_canada.csv` | CA |
| `precios_recursos_irlanda.csv` | IE |
| `precios_recursos_australia.csv` | AU |

## Paso 1 — Preparar la matriz con precios consultados

Consulta las fuentes de mercado y actualiza en el CSV `precio_referencia`,
`precio_min`, `precio_max` y — **imprescindible** — `fecha_consulta` con el
día de la consulta real. Esa fecha es la que las guías públicas muestran
(«Precios consultados en …», derivada de los datos desde la Fase 2): si no
la actualizas, la guía seguirá diciendo el mes antiguo aunque el precio
sea nuevo.

Notas por mercado:

- **EE. UU.**: el CSV va en unidades de fuente imperiales (sq ft, cu yd,
  lb…). El importador convierte y la BD guarda siempre métrico; no
  conviertas a mano.
- **Venezuela** no tiene CSV: sus precios salen de
  `basedatos_partidas/datos/recursos.json` (actualiza allí los precios y
  el campo `_revision`, que es la fecha que publica su guía).

## Paso 2 — Validar la matriz sin tocar la BD

```bash
python tools/verificar_matriz_importable.py basedatos_partidas/salida/precios_recursos_<mercado>.csv
```

Simula el importador completo (columnas, moneda del país, rangos,
`fecha_consulta` obligatoria, conversión imperial) sin escribir nada. Si
avisa, corrige el CSV y repite.

## Paso 3 — Cargar en la BD

Vía recomendada en producción: panel de operador
`/admin/matriz-precios` (subir el CSV; muestra el resumen antes de
aplicar).

Vía CLI (con la `DATABASE_URL` de producción en el entorno):

```bash
# primero, ensayo en seco
python tools/importar_precios_mercado.py --csv basedatos_partidas/salida/precios_recursos_<mercado>.csv
# luego, la carga real
python tools/importar_precios_mercado.py --csv basedatos_partidas/salida/precios_recursos_<mercado>.csv --apply
```

La carga es todo-o-nada (una transacción): si algo no valida, la BD
queda como estaba. Al aplicar, cada fila sella `fecha_actualizacion` a
hoy y los cambios de precio quedan en el historial.

## Paso 4 — Verificar CSV ↔ BD

```bash
DATABASE_URL=… python tools/verificar_matrices_bd.py
```

Sin argumentos verifica las 7 matrices (con la conversión imperial de
EE. UU. aplicada, igual que el importador). El resultado esperado es
`SIN DIFERENCIAS`: 22 países con 0 faltantes y 0 diferencias. Para una
sola matriz: `--csv <ruta>`.

## Paso 5 — Confirmar en producción

Abre `https://cotizat.online/readyz` y comprueba:

- `precios_actualizados: "hoy (…)"`
- `precios_bd` con el total esperado (8536 referencias en 22 países con
  las matrices actuales)

Y echa un vistazo a una guía pública del mercado actualizado: su nota
debe decir el mes de la nueva `fecha_consulta` (p. ej. «Precios
consultados en noviembre de 2026»).

## Si algo falla

- **El importador rechaza la matriz**: lee el motivo (validación dura,
  pensado para no cargar medias matrices). Corrige el CSV y vuelve al
  paso 2. La BD no ha cambiado.
- **El verificador reporta diferencias**: alguien tocó precios fuera del
  CSV (o la carga quedó a medias por otra vía). La matriz manda: repite
  el paso 3 con el CSV vigente.
- **`/readyz` sigue en REVISAR tras cargar**: cargaste contra otra base.
  Revisa la `DATABASE_URL` usada.
