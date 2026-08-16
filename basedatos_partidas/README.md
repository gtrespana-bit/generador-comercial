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


---

# Clasificación jerárquica (datos/clasificacion.json)

Tres niveles, pensados para alimentar el árbol de la barra lateral del presupuestador:

```
Capítulo (1 letra)  →  Subcapítulo (2 letras)  →  Grupo (3 letras)  →  Partida (grupo + 3 dígitos)

R  Revestimientos y trasdosados
└─ RS  Pavimentos
   └─ RSG  Cerámicos y porcelánicos
      ├─ RSG010  Pavimento formato estándar
      └─ RSG020  Pavimento gran formato
```

Cada partida declara `capitulo`, `subcapitulo` y `grupo`. El generador **valida** que los
tres existan en `clasificacion.json` y que el código empiece por el grupo; si no, falla.
Así es imposible que se cuele una partida descolgada del árbol.

Hay **18 capítulos** declarados desde el principio, aunque estén vacíos: el árbol se
construye completo y las ramas se van llenando.

## Salida para el front

`salida/arbol_catalogo.json` contiene el árbol ya montado, con el contador de partidas de
cada rama y, en las hojas, código, título, unidad, precio, horas y si requiere producto de
cliente. Es lo que consumirá la barra lateral arrastrable.

---

# Productos de elección del cliente

Una partida **no incluye el material de acabado que elige el cliente**. El solado incluye
adhesivo, junta, crucetas, corte y mano de obra — pero **no la cerámica**, porque esa
depende de lo que escoja cada cliente y vive en el catálogo de productos.

Cada partida afectada declara:

```json
"producto_cliente": {
  "tipo": "Pieza cerámica o porcelanato para pavimento, formato hasta 60x60 cm",
  "unidad": "m2",
  "consumo": 1.06,
  "nota": "Consumo con 6 % de desperdicio por cortes y roturas."
}
```

El `consumo` es el factor de conversión: por cada m² de partida hacen falta 1,06 m² de
producto. Al presupuestar, se elige el producto, se multiplica por el consumo y se suma.
El precio de la partida es **solo de ejecución**, y así se puede ofrecer el mismo trabajo
con tres cerámicas distintas sin recalcular nada.

La nota se arrastra al campo `notas_tecnicas` del catálogo, dejando constancia explícita
de qué NO está incluido.

---

# Actualización de precios en bloque (precios.py)

Los precios viven **solo** en `datos/recursos.json`. Las partidas guardan
rendimientos y referencian recursos por código, así que **actualizar precios
nunca obliga a tocar una partida**.

```bash
python3 basedatos_partidas/precios.py exportar
# -> salida/precios_para_revisar.csv, ordenado POR IMPACTO
#    (los recursos que más pesan en el coste del catálogo, primero)

# rellenar la columna «precio_nuevo» y:
python3 basedatos_partidas/precios.py aplicar
# -> actualiza recursos.json, marca los recursos como «confirmado»
#    y deja copia de seguridad con fecha

python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py
```

El CSV incluye `partidas_que_lo_usan` y `peso_en_catalogo_usd` para saber
dónde merece la pena invertir el tiempo de buscar precios.

**Conclusión práctica**: no hay que tener los precios antes de escribir
partidas. Lo único que sí conviene fijar desde el principio es la **unidad de
compra** de cada recurso (kg o saco, m o rollo), porque cambiar la unidad sí
obliga a revisar los rendimientos.

---

# Cobertura (cobertura.py)

Informe del avance del catálogo sobre la taxonomía, para trabajar **capítulo a
capítulo y grupo a grupo** sin dejar huecos:

```bash
python3 basedatos_partidas/cobertura.py              # resumen por capítulo
python3 basedatos_partidas/cobertura.py D            # detalle del capítulo D
python3 basedatos_partidas/cobertura.py --pendientes # grupos declarados y vacíos
```

## Criterio de trabajo

1. Se elige un **grupo** (tercer nivel, p. ej. `DRS`).
2. Se completa **entero**, con todas las variantes de material y sus remates.
3. Se pasa al siguiente grupo del mismo subcapítulo.

Un grupo se considera cerrado cuando cubre las tipologías que realmente se
encuentran en obra en Venezuela, no cuando iguala a ninguna base ajena.

## Terminología

El catálogo usa vocabulario de obra venezolano:

| No usar | Usar |
|---|---|
| hormigón | concreto |
| pavimento / solado | piso |
| enfoscado / guarnecido | friso |
| falso techo | cielo raso |
| terrazo (continuo) | granito vaciado en sitio |
| escayola | yeso |
| fontanero | plomero |
| bote de escombro | bote de escombro / retiro a vertedero |
