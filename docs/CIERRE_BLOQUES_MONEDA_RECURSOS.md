# Cierre de bloques — moneda y recursos LatAm

**Reauditado: 20/08/2026.**

## Estado de lanzamiento

La implementación técnica y la cobertura referencial están completas para los
cinco países. CotizaT se lanza como **generador de soporte y ayuda**, no como
cotizador de una tienda local: cada valor conserva rango, fecha, fuente y
confianza y puede ser reemplazado por el precio propio de la empresa.

| Bloque | Estado |
|---|---|
| Modelo monetario, conversión y documentos | Completo |
| Editor, históricos, proyectos, pagos y facturas | Completo |
| Mano de obra explícita | 3.006 / 3.006 partidas |
| Integridad de APUs y recursos | 0 errores estructurales |
| Venezuela | 388 / 388 precios base referenciales USD |
| Colombia | 388 / 388 referencias nacionales COP |
| Perú | 388 / 388 referencias nacionales PEN |
| México | 388 / 388 referencias nacionales MXN |
| Ecuador | 388 / 388 referencias nacionales USD |
| Matriz CO/PE/MX/EC | 73 observaciones directas + 1.479 derivadas |

Las derivaciones no son una simple conversión monetaria. Se calibran con la
mediana de la canasta investigada para cada país y familia según
[`METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`](METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md).

## Controles implantados

- Cada partida declara oficio, nivel profesional y horas por unidad.
- La aplicación conserva horas de oficial, ayudante y equipo, sin inventar un
  reparto 60/40.
- Cada precio nacional conserva rango, unidad, fecha, IVA, transporte,
  observaciones y confianza.
- El importador valida toda la matriz antes de escribir y es atómico.
- La referencia nacional se localiza por código estable, no solo por el ID
  privado del recurso de una organización.
- Los recursos compuestos se abren en componentes y no generan filas
  nacionales duplicadas.
- El precio propio de la empresa tiene prioridad sobre la referencia nacional.
- Los documentos históricos no cambian al actualizar la matriz.

## Calidad progresiva

La auditoría detecta 218 grupos (875 partidas) con APUs idénticos. Esto no es
por sí solo un defecto: distintas variantes pueden compartir el mismo trabajo
de instalación. Los grupos permanecen visibles en
`basedatos_partidas/salida/auditoria_partidas.csv` para revisión técnica y
mejora continua, sin bloquear el lanzamiento si su estructura, recursos,
mano de obra y rendimientos son válidos.

## Antes de staging

1. Aplicar migraciones en orden y comprobar el head final
   `a4c8e2f7b1d6`.
2. Verificar `/readyz`.
3. Importar `precios_recursos_latam.csv`.
4. Ejecutar `python3 basedatos_partidas/auditar_lanzamiento.py --strict` y
   exigir código de salida 0.
5. Crear un presupuesto ficticio en VE, CO, PE, MX y EC.
6. Comprobar moneda, PDF, Excel, correo, enlace público e históricos.
7. Confirmar que la interfaz muestra el aviso de precio referencial y permite
   introducir el precio propio.

## Mantenimiento

Latinoamérica es un mercado volátil. La referencia es una fotografía fechada,
no una garantía de permanencia. Cada nueva ronda actualiza anclas, rangos y
tasa de corte; después se regenera la matriz y se repite la aceptación. No se
segmenta artificialmente por ciudad ni se promete precisión de tienda.
