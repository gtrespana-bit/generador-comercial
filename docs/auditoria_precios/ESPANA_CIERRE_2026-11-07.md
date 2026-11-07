# Cierre de la auditoría de precios de España

**Corte: 7 de noviembre de 2026.** Documento de cierre del primer ciclo completo de la auditoría de precios de recursos de España: 388 recursos adjudicados, 18 precios nuevos aplicados y 5 referencias confirmadas. Historial previo en [CONTINUIDAD.md](CONTINUIDAD.md); guía de reanudación en [REANUDAR_AUDITORIA_ESPANA.md](REANUDAR_AUDITORIA_ESPANA.md).

## 1. Resumen

| Concepto | Recursos |
|---|---:|
| Recursos del catálogo | 388 |
| Con precio revisado trazable | 220 |
| Confirmados como referencia (`confirmado_referencia`) | 18 → **25** tras la [verificación cruzada](ESPANA_VERIFICACION_2026-11-07.md) |
| En revisión con precio revisado | 195 |
| En revisión sin precio revisado | 168 |
| Pendientes de decisión | **0** |

Decisiones registradas (375 filas, una por recurso sin confirmar previamente):

| Decisión | Recursos | Usos en partidas |
|---|---:|---:|
| `sin_equivalente_verificado` | 127 | 2.379 |
| `cierre_barrido_previo` | 96 | 1.294 |
| `agregado_heterogeneo` | 64 | 1.966 |
| `requiere_modelo_propio` | 37 | 2.907 |
| `alerta_divergencia` | 23 | 636 |
| `aplicar_mano_obra_dos_fuentes` | 8 | 1.158 |
| `aplicar_fuente_unica_coherente` | 7 | 126 |
| `mantener_sin_cambio_coherente` | 5 | 692 |
| `confirmar_referencia` | 5 | 21 |
| `aplicar_media_dos_bancos` | 3 | 238 |

**Ningún recurso queda pendiente de decisión.** «Sin equivalente verificado» no significa «sin precio en la matriz»: esos recursos conservan su referencia anterior y queda documentado por qué no se ha sustituido.

Aviso de lectura: `confirmado_referencia` significa que la referencia se acepta bajo el método y las condiciones documentadas en este informe. **No es un precio de mercado garantizado, ni una media nacional, ni el coste de una empresa o de una obra concreta.**

## 2. Método por lotes (reutilizable para los siguientes países)

El cuello de botella anterior era revisar recursos de uno en uno. Este cierre sustituye ese ritmo por una cadena de cinco pasos, cada uno reproducible y auditable:

1. **Cribado masivo contra un banco oficial completo** (`tools/cribar_precios_espana.py`). Descarga el banco, filtra moneda, ámbito y precios duplicados, y cruza los 388 recursos con los 6.131 ítems por núcleo de descripción, unidad y categoría. Produce una fila por candidato con `precision`, `cobertura`, `numeros_compatibles` y `ratio`. Resultado: 1.167 candidatos para 388 recursos, 253 recursos con algún candidato y 63 con precisión ≥ 0,70 **y** números de especificación compatibles.
2. **Adjudicación explícita por reglas publicadas** (`espana_adjudicacion_2026-11-07.csv`). Cada recurso recibe una decisión de un vocabulario cerrado, con criterio y reserva en texto. Las reglas por defecto son: descripción agregada → `agregado_heterogeneo`; maquinaria sin alcance comparable → `requiere_modelo_propio`; candidato con ratio fuera de 0,3–3 → `sin_equivalente_verificado` (producto distinto, no variación de precio); ratio 0,85–1,15 → `mantener_sin_cambio_coherente`; entre ambos → `alerta_divergencia`. Ninguna regla aplica precio: **solo aplican precio las 18 filas decididas a mano con dos fuentes o con una fuente coherente.**
3. **Aplicación validada** (`tools/cerrar_auditoria_espana.py`). Comprueba vocabulario, cobertura total, precios numéricos y positivos, exigencia de dos fuentes para las medias y banda del ±15 % para confirmar una referencia previa. Es todo o nada: si falta una fila o una cifra no cuadra, no escribe nada. Con `--aplicar` actualiza el registro y genera el libro de decisiones y la tabla de referencias aceptadas.
4. **Consumo data-driven por el generador** (`referencias_cierre_2026_11_07()`). El generador lee la tabla de referencias aceptadas y valida unidad, precio, fuente y banderas de IVA y transporte. Añadir un precio no requiere tocar código: basta una fila nueva validada.
5. **Regeneración y prueba**. Matriz, inventario, SQL local e índice público ES se regeneran; una prueba verifica que el libro, el registro, la matriz y la tabla de referencias coinciden y que la cadena es idempotente.

Para el siguiente país basta sustituir el banco del paso 1 y el vocabulario del paso 2: los pasos 3 a 5 son genéricos.

## 3. Los 18 precios aplicados

| Recurso | Unidad | Matriz | Nuevo | Δ | Código fuente | Usos |
|---|---|---:|---:|---:|---|---:|
| `MO-OF1-ELE` | h | 24,00 | **23,18** | −3,4 % | BCCA `TO01800` | 405 |
| `MO-OF1-PLO` | h | 23,00 | **23,18** | +0,8 % | BCCA `TO01900` | 218 |
| `MO-OF1-PIN` | h | 20,00 | **23,18** | +15,9 % | BCCA `TO01000` | 159 |
| `MQ-VIBRADOR` | h | 4,98443 | **3,72** | −25,4 % | Palencia `U02SW550` + Extremadura `M10HV050` | 135 |
| `MO-OF1-SOLD` | h | 25,00 | **23,18** | −7,3 % | BCCA `TO01600` | 127 |
| `MO-OF1-AC` | h | 21,00 | **23,18** | +10,4 % | BCCA `TO01400` | 94 |
| `MO-OF1-VIDR` | h | 21,00 | **23,18** | +10,4 % | BCCA `TO01700` | 92 |
| `MQ-RETRO` | h | 45,00 | **38,68** | −14,0 % | Palencia `U02AA020` + Extremadura `M05RN050` | 63 |
| `MQ-OXICORTE` | h | 7,036842 | **6,90** | −1,9 % | Extremadura `M11O010` | 48 |
| `MQ-GRUA` | h | 70,00 | **50,59** | −27,7 % | Palencia `U02J040` + Extremadura `M02GE170` | 40 |
| `MO-OF1-CARP` | h | 21,00 | **23,18** | +10,4 % | BCCA `TO00400` | 39 |
| `MQ-VOLQ` | h | 50,00 | **51,02** | +2,0 % | Palencia `U02J030` | 31 |
| `MO-OF1-JARD` | h | 21,00 | **23,18** | +10,4 % | BCCA `TO00800` | 24 |
| `MT-POLIET` | m2 | 0,60 | **0,69** | +15,0 % | BCCA `XI01100` | 18 |
| `MQ-DESBROZ` | h | 3,958224 | **4,36** | +10,2 % | Extremadura `M09AD040` | 9 |
| `MQ-INYECTORA` | h | 6,157237 | **5,35** | −13,1 % | Extremadura `M10PI020` | 9 |
| `MQ-PROYECT-MORT` | h | 9,96886 | **9,14** | −8,3 % | Extremadura `M01MP010` | 9 |
| `MT-BLQ-12` | ud | 0,592405 | **0,72** | +21,5 % | BCCA `FB00500` | 2 |

Suma de usos de los recursos con precio nuevo: **1.522**.

### Mano de obra (8 recursos, 23,18 €/h)

Dos vías independientes convergen en 23,18 €/h de coste **empresarial** de oficial de 1ª:

- Modelo de coste desde tablas salariales provinciales y cuotas publicadas (Madrid y Barcelona), con horas de convenio de 1.736 h/año (VII Convenio General del Sector de la Construcción, art. 71).
- Tabla de mano de obra del banco oficial: `TO0xxxx` a 23,17 €/h para la categoría.

Se adopta el punto operativo 23,18 €/h para los ocho oficios de oficial de 1ª (`ELE`, `PLO`, `PIN`, `SOLD`, `AC`, `VIDR`, `CARP`, `JARD`). **Reserva:** el banco no distingue especialidades, no se acredita el convenio provincial concreto de cada oficio y las horas son de convenio, no productivas; el rendimiento de cada APU debe verificarse aparte.

### Maquinaria (7 recursos)

- `MQ-VIBRADOR`, `MQ-RETRO` y `MQ-GRUA`: media aritmética de dos referencias provinciales 2026 comparables (Palencia y Extremadura), autorizada expresamente como punto operativo.
- `MQ-OXICORTE`, `MQ-DESBROZ`, `MQ-INYECTORA` y `MQ-PROYECT-MORT`: una sola referencia provincial 2026 equivalente en alcance, aplicada por coherencia de alcance y no por coincidencia de texto.

**Reserva común:** son bancos provinciales, no una media nacional. Capacidad, potencia, consumibles, energía y alcance del operador difieren entre fuentes y deben confirmarse en el APU. Para los tres recursos con dos fuentes se conserva además la referencia del banco oficial que discrepa como alerta registrada.

### Materiales (3 recursos)

`MT-POLIET` (lámina de polietileno de 0,2 mm), `MT-BLQ-12` (bloque de hormigón hueco 40×20×12 cm, equivalencia dimensional exacta) y los cinco confirmados del apartado 4. Reserva: los precios del banco oficial están declarados en 2022 y su ámbito es andaluz; no incorporan la evolución posterior ni el porte.

## 4. Confirmaciones de referencia (±15 %)

Cinco recursos ya revisados quedan **confirmados** al encontrar una referencia oficial dentro de la banda del ±15 %:

| Recurso | Precio | Fuente | Δ |
|---|---:|---|---:|
| `MT-DIFERENCIAL` | 55,01 €/ud | BCCA `IE08600` | +12,8 % |
| `MT-VIGUETA` | 7,84 €/m | BCCA `CV00200` | −13,6 % |
| `MT-PYL-PLACA-IG` | 7,92 €/m2 | BCCA `FP80020` | −14,4 % |
| `MT-PYL-PLACA-HD` | 4,40 €/m2 | BCCA `FP01200N2` | −5,5 % |
| `MT-SELLA-FISURA` | 9,48 €/kg | BCCA `GHJFUUOIJB` | −15,0 % |

Con las 13 confirmaciones anteriores, el registro queda en **18 `confirmado_referencia`**; la verificación cruzada posterior lo eleva a **25** (ver [ESPANA_VERIFICACION_2026-11-07.md](ESPANA_VERIFICACION_2026-11-07.md)).

## 5. Lo que se ha decidido **no** aplicar

- **23 alertas de divergencia** (636 usos): hay un candidato con el mismo núcleo, pero el valor difiere entre el 15 % y el 200 %. Las de mayor uso son `MT-PYL-PASTA` (99), `MT-MADERA-LISTON` (91), `MT-ALAMBRE` (49), `MT-MORT-IMPER` (39), `MT-REJILLA-VENT` (39) y `MT-VALV-CHECK` (38). Requieren verificar especificación y presentación, no un ajuste ciego del precio.
- **127 recursos sin equivalente verificado** (2.379 usos): no hay candidato con el mismo núcleo, unidad y categoría, o el candidato difiere más de tres veces y por tanto es otro producto. Mayores usos: `MT-SAC-ESC` (235), `MT-PERNO-ANCLA` (148), `MT-ACERO-CAB` (106), `MT-ELE-CABLE` (103).
- **64 recursos agregados** (1.966 usos) que mezclan varios productos en una sola línea: `MT-CONS-DEM` (398), `MT-ELE-CAJA` (177), `MT-PLO-SOP` (169), `MT-TORN` (154), `MT-SILICONA-EST` (96). Deben desglosarse antes de tarifarse.
- **37 recursos de maquinaria** (2.907 usos) que exigen un modelo de coste horario propio (amortización, mantenimiento, energía y operador) o un alquiler 2026 con condiciones completas: `MQ-TALADRO` (1.025), `MQ-SIERRA` (199), `MQ-ANDAMIO` (190), `MQ-ATORN` (162), `MQ-RODILLO` (151). La dispersión entre bancos llega a 7× en `MQ-TALADRO` (3,11 / 0,84 / 5,81 €/h): no hay media defendible.
- **96 `cierre_barrido_previo`**: decisiones ya documentadas en los ocho barridos anteriores, no reabiertas.
- **5 `mantener_sin_cambio_coherente`** (692 usos): referencia oficial dentro del ±15 %, precio mantenido.

## 6. Impacto en partidas

Medido, no estimado: `tools/analizar_impacto_precios_espana.py` recalcula el coste directo de las 3.006 partidas con la matriz anterior y con la actual, usando la misma cascada que la aplicación (rendimiento × precio redondeado a 2 decimales por recurso, subtotal por grupo y complementarios). Resultado en `espana_impacto_partidas_2026-11-07.csv`:

| Métrica | Valor |
|---|---|
| Partidas medidas | 3.006 |
| Con coste distinto | **1.452 (48,3 %)** |
| Delta mediano | −0,15 % |
| Delta p10 / p90 | −2,81 % / +6,00 % |
| Rango | −10,54 % … +12,75 % |

Lectura: el efecto está dominado por la mano de obra. El sesgo central es casi neutro porque los oficios suben (21 → 23,18 €/h) mientras la maquinaria baja (grúa −27,7 %, retro −14,0 %, vibrador −25,4 %). Las partidas que más suben son de pintura y acabados (`12.10.01.230` +12,75 %, `12.04.01.220` +12,24 %), donde el oficio es casi todo el coste y `MO-OF1-PIN` pasa de 20 a 23,18 €/h (+15,9 %). Las que más bajan son de desmontaje con maquinaria pesada (`02.03.01.170` −10,54 %).

La matriz del catálogo no se ha recalculado: el precio de venta de cada partida se recalcula al generar un presupuesto, no se persiste. Antes de publicar presupuestos conviene revisar los rendimientos de los APU con más peso de mano de obra, porque un precio horario más alto encarece la partida aunque la máquina abarate.

## 7. Límites de las fuentes

1. **El banco oficial disponible no es nacional ni de 2026.** Es la Base de Costes de la Construcción de Andalucía (edición 2024-01), con precios declarados en 2021–2022 y ámbito `ES/AND`. Se ha usado como referencia de contraste, no como media nacional. La copia manejada proviene del paquete de datos CERP 0.7.0, que es una redistribución de terceros: se ha verificado el contenido, no la cadena de custodia editorial.
2. **Las bases provinciales (Palencia, Extremadura) son provinciales.** Sus valores no se presentan como media nacional. La transcripción de Extremadura se ha hecho desde fichas de partida y puede contener errores de lectura; los códigos y precios usados quedan en el registro.
3. **IVA y transporte:** solo 3 de las 18 referencias aplicadas tienen condiciones documentadas de IVA y porte. Las demás quedan marcadas `no_confirmado` / `por_verificar` en la matriz y no se han corregido al alza por suposiciones.
4. **Los precios de cliente no se han tocado.** No hay escrituras en base de datos de producción, ni ejecución del SQL, ni despliegue.
5. **El cribado es una ayuda, no una prueba.** Una coincidencia de texto con precisión alta puede seguir siendo otro producto; por eso ninguna coincidencia automática ha aplicado precio.

## 8. Reproducibilidad

```bash
python3 tools/cribar_precios_espana.py            # cribado (requiere el banco en la ruta documentada)
python3 tools/cerrar_auditoria_espana.py          # valida la adjudicación sin escribir
python3 tools/cerrar_auditoria_espana.py --aplicar  # registro + referencias + libro de decisiones
python3 tools/generar_matriz_precios_espana.py    # matriz de recursos
python3 tools/inventario_precios_espana.py        # inventario integral
python3 tools/generar_sql_precios_espana.py       # SQL local (no ejecutado)
python3 tools/generar_precios_publicos.py         # índice público por país
git show HEAD:basedatos_partidas/salida/precios_recursos_espana.csv > /tmp/antes.csv
python3 tools/analizar_impacto_precios_espana.py --anterior /tmp/antes.csv
.venv/bin/python -m pytest -q -n 4                # suite completa
```

Artefactos de este cierre:

| Archivo | Contenido |
|---|---|
| `espana_adjudicacion_2026-11-07.csv` | 375 decisiones, una por recurso, con precio, fuente, desviación, criterio y reserva |
| `espana_referencias_cierre_2026-11-07.csv` | 18 referencias aceptadas que consume el generador |
| `espana_cierre_decisiones_2026-11-07.csv` | libro de 375 filas: estado final, precio final, fuente y decisión |
| `espana_2026-11-06.csv` | registro maestro: 18 confirmados, 370 en revisión, 220 con precio revisado |
| `espana_cribado_bcca_2026-11-07.csv` | 1.167 candidatos del banco oficial con métricas de cruce |
| `espana_inventario_integral_2026-11-07.csv` | inventario de los 388 recursos con estado y candidatos |
| `espana_impacto_partidas_2026-11-07.csv` | 3.006 partidas con coste anterior, actual, delta y recursos responsables |

Pruebas nuevas: `tests/test_cierre_auditoria_espana.py` (10 pruebas: validación, coherencia libro/registro/matriz, idempotencia, cribado, cascada de coste e impacto publicado) y `tests/apoyo_cierre_espana.py`. Las pruebas de lotes anteriores se han adaptado para admitir el estado de cierre sin relajar lo que verificaban (precio del lote, trazabilidad de la fuente, coherencia con la matriz).

## 9. Siguientes pasos, por orden de impacto

1. **Desglosar los 64 agregados** con más usos (`MT-CONS-DEM`, `MT-ELE-CAJA`, `MT-PLO-SOP`, `MT-TORN`): desbloquea 1.966 usos y es trabajo de descripción, no de búsqueda de precios.
2. **Modelo de coste horario propio** para la maquinaria de mayor uso (`MQ-TALADRO`, `MQ-SIERRA`, `MQ-ANDAMIO`, `MQ-ATORN`): 2.907 usos esperando un método, no un número.
3. **Resolver las 23 alertas** con especificación y oferta 2026, empezando por `MT-PYL-PASTA`, `MT-MADERA-LISTON` y `MT-ALAMBRE`.
4. **Conseguir un banco nacional y vigente** (o una suscripción con licencia de uso) para sustituir el contraste andaluz de 2022; mientras no exista, toda cifra nueva debe seguir declarando su ámbito provincial.
5. **Repetir la cadena en el siguiente país** con el método del apartado 2.

## 10. Anexo: maquinaria cerrada por modelo propio (7 de noviembre de 2026)

El paso 2 de la lista anterior (modelo de coste horario para la maquinaria) está hecho: **13
recursos de maquinaria (2.185 usos)** tienen ya precio propio calculado como compra dividida
por vida útil, con energía a 0,20 €/kWh y consumibles incluidos. Siguen en revisión, porque un
modelo propio no es una tarifa contrastada. `MQ-ANDAMIO` y los 24 recursos de maquinaria
pesada quedan fuera del modelo con motivo escrito.

* Detalle, fuentes de adquisición y sensibilidad: [decisión de maquinaria](ESPANA_MAQUINARIA_DECISION_2026-11-07.md).
* Impacto en el catálogo: `espana_impacto_maquinaria_2026-11-07.csv` (1.511 partidas, mediana
  −0,5 %, máximo −10,8 %).
* Agregados, con criterio medido en lugar de intuición: [decisión de agregados](ESPANA_AGREGADOS_DECISION_2026-11-07.md).
