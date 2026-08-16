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
