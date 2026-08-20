# Auditoría integral del catálogo antes de lanzamiento

**Fecha de corte:** 20/08/2026  
**Alcance:** 3.006 partidas, cuadro base Venezuela y matrices CO/PE/MX/EC.

> Esta auditoría distingue tres cosas: que el APU sea calculable, que la mano de obra esté explícita y que exista una referencia nacional trazable. Una conversión de divisa aislada no basta; una derivación calibrada con la canasta investigada se identifica como `derivado`.

## Veredicto

**APTO para lanzamiento en los cinco países como generador de soporte con precios referenciales nacionales.** Las 3.006 partidas son calculables, todas tienen mano de obra explícita y los 388 recursos físicos tienen referencia en CO/PE/MX/EC. La aplicación debe mantener visibles fecha, rango, confianza y el aviso de comprobación: no son cotizaciones exactas de una tienda.

## 1. Partidas y mano de obra

| Comprobación | Resultado |
|---|---:|
| Partidas JSON revisadas | 3006 |
| Partidas con al menos una línea de mano de obra | 3006 / 3006 |
| Líneas de mano de obra revisadas | 6062 |
| Horas-persona por unidad acumuladas (indicador, no duración de una obra) | 3952.7 h |
| Errores estructurales | 0 |

Cada rol declara ahora `oficio`, `nivel_profesional`, jornada de 8 h, tipo de tarifa y mercado base. El catálogo de la aplicación recibe `tiempo_oficial_horas`, `tiempo_ayudante_horas` y `tiempo_equipo_horas`; ya no inventa el reparto 60/40 para estas partidas. El detalle partida por partida está en `basedatos_partidas/salida/auditoria_partidas.csv`.

## 2. Calidad semántica de los APUs

- **218 grupos / 875 partidas** comparten exactamente unidad, recursos y rendimientos con otra partida.
- **775 descripciones** tienen menos de 120 caracteres.
- Repetir un APU puede ser legítimo cuando varias variantes comparten el mismo trabajo de instalación. Las coincidencias quedan identificadas para revisión técnica progresiva; no son por sí solas un error ni bloquean el lanzamiento mientras recursos, mano de obra y rendimientos sean válidos.

## 3. Venezuela — cuadro base USD

| Estado del recurso físico | Cantidad | Cobertura |
|---|---:|---:|
| Material/equipo verificado en mercado | 131 | 33.8% |
| Tarifa interna confirmada | 17 | 4.4% |
| Provisional | 240 | 61.9% |

Los 388 recursos físicos tienen precio base referencial. `Provisional` expresa menor evidencia pública o mayor volatilidad, no ausencia de precio. Los cuatro recursos compuestos se abren en cemento, arena, agua y componentes al calcular la partida.

## 4. Precios país por país

| País | Recursos | Referencia directa | Derivados | Pendientes | Cobertura trazable |
|---|---:|---:|---:|---:|---:|
| Colombia (COP) | 388 | 22 | 366 | 0 | 100.0% |
| Perú (PEN) | 388 | 14 | 374 | 0 | 100.0% |
| México (MXN) | 388 | 18 | 370 | 0 | 100.0% |
| Ecuador (USD) | 388 | 19 | 369 | 0 | 100.0% |

La matriz contiene referencias nacionales directas y derivadas. Las derivadas se calibran con la canasta investigada de cada país y se identifican como tales; no se presentan como una cotización local exacta. `precios_recursos_latam_completa.csv` se conserva por compatibilidad y actualmente coincide en cobertura con la matriz principal.

### Correcciones críticas aplicadas

- Los valores que la documentación dejaba sin observación individual (por ejemplo PVC y cable en México) se calculan ahora con la canasta nacional y quedan explícitamente como `derivado`.
- Se corrigió la doble división por 25 del adhesivo C2 en Colombia: el valor anterior estaba 25 veces por debajo de su presentación documentada.
- Se añadieron rangos normalizados y se exige que la referencia quede dentro de ellos.
- Se excluyeron 4 recursos compuestos que no existen como filas físicas en la aplicación (16 filas huérfanas país/recurso).
- Las 17 categorías de mano de obra tienen referencia por país; las especialidades sin jornal propio quedan visibles como `derivado`, nunca como observación directa.
- La metodología nacional completa 1.552 referencias con factores de canasta por país y familia, sin segmentación artificial por ciudad.
- El importador es atómico y conserva rango, unidad, fecha, IVA, transporte y observaciones en base de datos.
- La referencia nacional se resuelve por código estable de recurso; ya no queda ligada al ID privado de la organización usada para importarla.

## 5. Condiciones de lanzamiento y mantenimiento

1. Mostrar siempre que el valor es referencial y puede variar por proveedor, marca, disponibilidad, IVA y transporte.
2. Mostrar rango, fecha y confianza; no convertir `derivado` en `referencia` sin una observación directa.
3. Permitir que cada empresa sustituya el valor nacional por su precio propio.
4. Ejecutar un presupuesto representativo por país como prueba funcional de moneda, PDF, Excel e históricos.
5. Revisar progresivamente los grupos de APUs coincidentes y renovar la canasta de mercado en cada ronda de actualización.

## 6. Reproducción

```bash
python3 tools/generar_matriz_precios_latam.py
python3 tools/completar_matriz_referencias.py
python3 basedatos_partidas/auditar_lanzamiento.py
python3 basedatos_partidas/auditar_lanzamiento.py --strict  # debe terminar en 0 antes de publicar
```

**Errores de integridad de matriz:** 0.  
**Recursos físicos sin uso:** 33 (MO-OF1, MT-ALARMA, MT-AUTOM-PORTON, MT-BATERIA, MT-BOMBA-AGUA, MT-CAMARA-CCTV, MT-CONT-DESCARGAS, MT-DOM-ACTUADOR, MT-DOM-CENTRAL, MT-DOM-DIMMER, MT-DOM-ENCHUFE, MT-DOM-PANEL, MT-DOM-PASARELA, MT-DOM-PERSIANA, MT-DOM-REPETIDOR, MT-DOM-SENSOR-GAS, MT-DOM-SENSOR-INUND, MT-DOM-SENSOR-LUZ, MT-DOM-SENSOR-MOV, MT-DOM-SENSOR-PUERTA, MT-DOM-SENSOR-TEMP, MT-DOM-TECLADO, MT-DOM-TERMOSTATO, MT-DPS-1, MT-DPS-2, MT-DPS-3, MT-DPS-DATOS, MT-HIDRONEUMATICO, MT-INVERSOR, MT-PANEL-SOLAR, MT-PARARRAYOS-PDA, MT-PARARRAYOS-PUNTA, MT-PLANTA-ELEC).
