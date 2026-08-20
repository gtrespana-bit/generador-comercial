# Guía operativa — precios por mercado LatAm

## Mercados iniciales

- Colombia — COP
- Perú — PEN
- México — MXN
- Ecuador — USD
- Venezuela — USD, catálogo existente

## Precio efectivo

Cotizat resuelve cada recurso en este orden:

1. Override de la organización.
2. Referencia nacional.
3. Respaldo base USD, claramente marcado como provisional.
4. Precio pendiente.

Los precios son orientativos. La empresa debe verificar proveedor, ciudad,
marca, calidad, volumen, IVA, transporte y fecha.

## Estado auditado (20/08/2026)

Cada mercado contiene referencias para los 388 recursos físicos: **1.552 filas
nacionales, sin huecos**. Hay 73 observaciones directas y 1.479 referencias
derivadas de las canastas nacionales investigadas.

`Derivado` no significa «precio exacto de tienda»: identifica una referencia
calculada con el nivel de mercado observado para el país y la familia. La
metodología, factores y límites están en
`docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`.

## Matriz

La matriz trazable se encuentra en:

```text
basedatos_partidas/salida/precios_recursos_latam.csv
```

La salida completa se conserva por compatibilidad en:

```text
basedatos_partidas/salida/precios_recursos_latam_completa.csv
```

Con la cobertura actual ambas contienen precio para las 1.552 filas; la
principal distingue `referencia` y `derivado`.

## Importación

Dry-run seguro:

```bash
python tools/importar_precios_mercado.py --sync-source
```

Aplicar referencias directas y derivadas:

```bash
python tools/importar_precios_mercado.py --sync-source --apply
```

`--include-fallback` se mantiene por compatibilidad con matrices antiguas; no
es necesario para la matriz actual.

## Históricos

Actualizar una referencia nacional no modifica presupuestos aprobados,
versiones, proyectos, facturas ni pagos históricos. Las filas guardan moneda,
fuente, confianza y origen.

## Añadir un país

1. Añadir el país y su moneda en `app/paises.py`.
2. Añadir la moneda ISO a `app/services/monedas.py`.
3. Añadir su tasa y política de decimales.
4. Añadir el país a la matriz.
5. Investigar recursos nacionales.
6. Ejecutar dry-run.
7. Revisar unidades, IVA y transporte.
8. Cargar referencias como `referencia` o `provisional`.
9. Añadir pruebas del país.

## Añadir una moneda

La moneda debe tener:

- Código ISO.
- Nombre.
- Decimales.
- Formato.
- Tasa o paridad.
- Regla para PDFs y Excel.
- Pruebas de conversión.

## Supabase

Las migraciones se preparan tanto como Alembic como SQL para SQL Editor.
Nunca ejecutar una migración SQL fuera del orden indicado en
`docs/MIGRACIONES_MONEDA_RECURSOS_SUPABASE.md`.
