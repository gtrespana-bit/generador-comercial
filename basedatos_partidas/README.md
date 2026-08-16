# Base de datos de partidas (trabajo externo)

Carpeta **independiente** del código de la aplicación. Aquí se construye y valida
el catálogo de partidas; no se toca ni un módulo del proyecto. Lo único que se
lee del proyecto es `app/services/importer.py`, y solo para **validar** que lo
generado se detecta perfectamente al subirlo.

```
basedatos_partidas/
├── datos/partidas.csv   ← FUENTE DE VERDAD (aquí van tus datos)
├── construir.py         ← genera y valida
└── salida/              ← ficheros listos para subir a la app
    ├── catalogo_partidas.csv
    ├── catalogo_partidas.xlsx
    └── catalogo_partidas.json
```

## Cómo se usa

1. Añadir/editar filas en `datos/partidas.csv` (separador `;`, UTF-8).
2. Ejecutar: `python3 basedatos_partidas/construir.py`
3. Subir `salida/catalogo_partidas.xlsx` (o el .csv) en la app:
   **Partidas → Importar** (`/presupuestos/importar?destino=catalogo`).

## Columnas del maestro (`datos/partidas.csv`)

| Columna | Obligatoria | Notas |
|---|---|---|
| `codigo` | recomendada | Código interno/externo. Se comprueba que no se repita. |
| `capitulo` | sí | Capítulo de obra (ALBAÑILERÍA, FONTANERÍA…). |
| `partida` | **sí** | Nombre. **Único** en todo el fichero: el catálogo omite duplicados (máx. 200 car.). |
| `descripcion` | sí | Texto técnico/comercial largo. |
| `unidad` | sí | `ud, m2, m, ml, m3, juego, hora, glb, kg`. `m²`→`m2` se normaliza solo. |
| `precio` | sí | Precio unitario de venta, > 0. Acepta coma o punto decimal. |
| `categoria` | no | Si se deja vacía se usa el capítulo. |
| `subcategoria` | no | Solo informativa / JSON. |
| `coste_materiales` | no | Desglose. La suma no puede superar al precio. |
| `coste_mano_obra` | no | Desglose. |
| `coste_complementarios` | no | Costes directos complementarios (estilo CYPE). |
| `coste_otros` | no | Desglose. |
| `rendimiento` | no | Texto libre (p. ej. `12 m2/jornada`). |
| `desperdicio_pct` | no | % de desperdicio recomendado. |
| `notas_tecnicas` | no | Texto libre. |

## Qué garantiza el validador

`construir.py` hace dos pasadas:

- **Calidad propia**: nombres y códigos duplicados, longitudes, precios a 0,
  desglose de costes incoherente, descripciones o capítulos vacíos, unidades raras.
- **Compatibilidad real**: pasa el CSV generado por `leer_csv` → `analizar_matriz`
  → `detectar_mapeo` → `validar_filas` del propio proyecto. El objetivo es siempre
  **8 campos detectados, 0 errores, 0 advertencias**.

## Correspondencia con el modelo `Partida`

El asistente en modo catálogo (`_importar_a_catalogo`) rellena: `nombre`,
`descripcion`, `precio_unitario`, `unidad`, `categoria`, `codigo_interno`,
`codigo_externo`, `descomposicion_json` y los cuatro `coste_*`.
El `.json` de salida conserva además `subcategoria`, `rendimiento`,
`desperdicio_recomendado_pct` y `notas_tecnicas` para una carga enriquecida futura.

---

# Descompuestos (formato hoja tipo CYPE)

`descompuestos.py` genera hojas .xlsx con **el layout exacto que ya lee
`analizar_cype_xlsx`**: cabecera con código/unidad/título, descripción larga,
fila de encabezados «Código · Unidad · Descripción · Rendimiento · Precio
unitario · Importe», grupos, subtotales, % de costes directos complementarios
y total de costes directos.

Cada partida es un JSON en `datos/descompuestos/`:

```json
{
  "codigo": "PRO-ALB-001",
  "unidad": "m²",
  "titulo": "...",
  "descripcion": "...",
  "complementarios_pct": 2,
  "recursos": [
    {"grupo": "materiales", "codigo": "...", "unidad": "m²",
     "descripcion": "...", "rendimiento": 4.2, "precio": 4.8}
  ]
}
```

`grupo` admite `materiales`, `maquinaria` y `mano_obra`; el generador los
rotula como «Materiales», «Equipo y maquinaria» y «Mano de obra», que son las
etiquetas que `_categoria_coste_cype` clasifica correctamente.

**Rendimientos**: la columna Rendimiento es la cantidad de recurso por unidad
de partida (h/m², kg/m², m/m²…). Sumando los recursos de mano de obra sale
directamente el tiempo de ejecución por unidad, que es lo que alimenta el
cálculo de horas, plazos y márgenes.

**Importante**: los importes, subtotales y el total se escriben como valores
numéricos literales, no como fórmulas. openpyxl no guarda el resultado
cacheado de una fórmula, y el lector del proyecto leería celdas vacías.

Ejecutar: `python3 basedatos_partidas/descompuestos.py [CODIGO ...]`
El script valida cada archivo con `es_formato_cype_xlsx` y `analizar_cype_xlsx`
e imprime los costes tal y como los va a leer la aplicación.

---

# Cuadro de recursos (datos/recursos.json)

**Fuente única de verdad de los precios.** Agrupa mano de obra, materiales y
maquinaria. Cada partida referencia recursos por su código:

```json
{"ref": "MO-OF1-SOL", "rendimiento": 0.400}
```

y hereda unidad, descripción y precio del cuadro. Cambiar el precio de un
recurso **recalcula automáticamente todas las partidas que lo usan**: no hay
que tocar ninguna partida para actualizar el coste de la hora de oficial o el
precio del porcelánico.

Cada recurso lleva un campo `estado`. Todo lo que ponga `provisional` está
pendiente de sustituir por el dato real de vuestros proveedores y convenio.

## Cadena completa

```
datos/recursos.json  +  datos/descompuestos/*.json
          │
          ▼   descompuestos.py
   salida/descompuestos/*.xlsx      (hoja de descompuesto, se sube una a una)
          +
   datos/partidas.csv               (maestro consolidado, regenerado)
          │
          ▼   construir.py
   salida/catalogo_partidas.{csv,xlsx,json}   (carga masiva del catálogo)
```

El precio de venta del catálogo sale de `coste directo × (1 + margen)`, con
`margen` por partida (0,30 por defecto).

## Orden de ejecución

```bash
python3 basedatos_partidas/descompuestos.py   # 1. descompuestos + maestro
python3 basedatos_partidas/construir.py       # 2. catálogo importable
```
