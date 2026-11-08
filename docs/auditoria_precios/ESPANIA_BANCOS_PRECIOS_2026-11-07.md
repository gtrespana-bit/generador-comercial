# Hallazgos de los dos bancos de precios — España, corte 7 de noviembre de 2026

## Decisión aplicada

El titular indicó: **«Tenemos dos bancos de precios. Usalos»** — dejar de buscar fuentes web y extraer la segunda observación independiente de los dos bancos locales:

- `bases_precios/BCCA2023_V02.bc3` — Base de Costes de la Construcción de Andalucía 2023 (FIEBDC-3/2020 RIB/Presto 22.01), 15.514 registros C, 8.426 D, 11.532 T.
- `bases_precios/BCEXTGREM_26_v1.bc3` — Base de Precios de la Construcción de Extremadura 2026, nomenclatura `P`/`M`/`O` (origen y URL en `bases_precios/LEEME.md`).

Ningún precio se aplicó por encontrar un número: solo cuando coinciden unidad, clase y alcance; y `en_revision` no se promueve a `confirmado_referencia` sin una segunda fuente independiente que **confirme** (no que diverja).

## 1. Ingestión de los bancos

**BCCA 2023.** El lector genérico `leer_bc3` solo reconoce prefijos `P`/`M`/`O` (esquema de Extremadura), así que de los 15.514 registros C de la BCCA solo veía 196 (1,3 %). Se escribió `tools/leer_bcca.py`, que reconoce la nomenclatura propia de la BCCA (`A01JF006`, `CA00220`, `IC00050`, `KA00100`, `U04AA001`…), descarta ramas del árbol (`#`), conceptos descompuestos (su precio lleva instalación), unidades no reconocidas, importes ≤ 0 y códigos de relleno sin dígito (`FJGJKL`, `JFJFGFD`, `HJJHFDF`…: descripción de una palabra y precio redondo, no son artículos). Resultado: **5.925 precios simples utilizables** (sha256 `bee06981c4447c6b…`): materiales 5.843, maquinaria 75, mano de obra 7; ud 3.485 / m2 1.054 / m 919 / kg 179 / m3 172 / h 82 / l 34.

**Extremadura 2026.** Se lee con `leer_bc3` (su esquema `P`/`M`/`O` encaja); cribado completo sobre los 388 recursos.

Ambos cribados se regeneran con:

```
python3 tools/cribar_precios_espana.py --bc3 bases_precios/BCCA2023_V02.bc3 --completo --sinonimos --banco bcca --edicion 2023 --salida docs/auditoria_precios/espana_cribado_bcca2023_2026-11-07.csv
python3 tools/cribar_precios_espana.py --bc3 bases_precios/BCEXTGREM_26_v1.bc3 --sinonimos --banco extremadura --edicion 2026 --salida docs/auditoria_precios/espana_cribado_extremadura_2026-11-07.csv
```

y el contraste se reproduce con `tools/verificar_precios_espana.py` (filtros: precisión ≥ 0,70, `numeros_compatibles == si`, código con dígito, ratio dentro del ±15 %).

## 2. Qué confirmaron los bancos

Tras el cribado contra los dos bancos y revisión caso a caso (no es un gate automático), se aplicaron **15 nuevas confirmaciones**, todas con ficha de la BCCA 2023:

| Recurso | Precio revisado | Ficha BCCA | Precio banco | Desvío | Usos |
|---|---|---|---:|---:|---:|
| MO-OF1-ELE | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 405 |
| MO-OF1-PLO | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 218 |
| MO-OF1-PIN | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 159 |
| MO-OF1-SOLD | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 127 |
| MO-OF1-AC | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 94 |
| MO-OF1-VIDR | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 92 |
| MO-OF1-CARP | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 39 |
| MO-OF1-JARD | 23,18 €/h | TO02100 Oficial 1ª | 23,17 | −0,0 % | 24 |
| MT-BLQ-12 | 0,72 €/ud | FB00500 bloque 40×20×12 | 0,72 | 0,0 % | 2 |
| MT-ARENA | 16,50 €/m3 | U04AA001 arena de río 0–5 mm | 18,48 | +12,0 % | 13 |
| MT-CINTA-ANTIDES | 0,44 €/m | RS00050 cinta 40 mm base aluminio | 0,43 | −2,3 % | 5 |
| MT-EPOXI-ANCLA | 24,23 €/l | GR00200 resina epoxi | 21,45 | −11,5 % | 27 |
| MT-LANA-ROCA | 6,16 €/m2 | XT11200 panel lana mineral 40 mm | 5,46 | −11,4 % | 15 |
| MT-CANON-TIERRA | 2,14 €/m3 | ET00200 canon gestión tierras | 2,42 | +13,1 % | 4 |
| MT-PERSIANA-ALU | 62,66 €/m2 | KS04500 persiana enrollable Al lacado | 54,30 | −13,3 % | 4 |

Total en el registro: **52 `confirmado_referencia` (2.346 usos)** y **336 `en_revision`**; 1 más está `confirmado_independiente` (MT-PERSIANA-ALU ya lo estaba desde el ciclo anterior contra KS04500). Reserva escrita en cada confirmación: referencia operativa contrastada, no media nacional ni coste de proveedor concreto; IVA y transporte sin confirmar.

Nota: Extremadura 2026 cotiza exactamente lo mismo que la matriz para `MQ-OXICORTE` (6,90 €/h, M11O010) y `MQ-DESBROZ` (4,51 €/h vs 4,36 revisado), pero esos precios **vienen de ese mismo banco** (la matriz ya los adoptó de Extremadura 2026), así que no son una segunda fuente independiente: siguen `en_revision` con la reserva escrita.

## 3. Qué divergen — se conserva el precio de matriz con horquilla declarada

Cuando el banco tiene ficha pero el precio está fuera del ±15 % (o el alcance no coincide), el precio de la matriz **no se sustituye**; se documenta la divergencia y el recurso sigue `en_revision`. 66 divergencias verificadas (1.447 usos), 38 contra Extremadura 2026, 25 contra BCCA 2023, 3 contra ofertas comerciales. Las de mayor uso:

| Recurso | Usos | Matriz | Banco | Δ | Ficha |
|---|---:|---:|---:|---:|---|
| MT-PERNO-ANCLA | 148 | 1,55 €/ud | 1,80 €/ud | +16,1 % | Extremadura P01UT100 |
| MT-PYL-PASTA | 99 | 1,01 €/ud | 1,00 €/ud | −1,0 % | Extremadura P39E010 |
| MT-PINT-ANTICORR | 78 | 7,75 €/ud | 29,24 €/ud | +277,3 % | Extremadura P19GTW280 |
| MT-PUENTE-ADH | 76 | 23,91 €/ud | 5,56 €/ud | −76,7 % | Extremadura P06SI120 |
| MT-PERFIL-REMATE | 68 | 2,85 €/m | 9,30 €/m | +226,3 % | Extremadura P08WP300 |
| MT-PYL-MONT | 61 | 0,97 €/ud | 2,07 €/ud | +113,4 % | Extremadura P04PW170 |
| MT-APEO | 54 | 1,04 €/ud | 13,55 €/ud | +1202,9 % | Extremadura P31CB010 (puntal telescópico, distinto artículo) |
| MT-BANDA-REF | 46 | 3,01 €/ud | 0,15 €/ud | −95,0 % | Extremadura P01LW083 |
| MT-PLO-PVC4 | 32 | 1,41 €/m | 9,94 €/m | +605 % | BCCA SC01100 (Ø250 mm vs 4″ del recurso) |
| MT-MORT-IMPER | 39 | 1,75 €/kg | 0,42 €/kg | −76,0 % | BCCA IS031 (mortero genérico vs bicomponente flexible) |
| MT-GRAVILLA | 21 | 38,97 €/m3 | 14,82 €/m3 | −62,0 % | BCCA AG00500 (grava sin puesta en obra) |
| MT-ELE-CABLE | — | 0,65 €/m | 3,91–17,19 €/m | fuera de banda | BCCA secciones 10–50 mm² vs 12 AWG del recurso |
| MT-PERSIANA-ALU (Extremadura) | 4 | 62,66 €/m2 | 157,66 €/m2 | +151,6 % | P12RC060 descartada: alcance distinto (cajón+accesorios) |

Regla aplicada a todas: la ficha del banco sirve de **nivel de precio**, no de cotización del artículo; cuando descripción, unidad o alcance no coinciden (césped artificial por grama natural, riel por metro por herraje por unidad, compra por alquiler, bomba sumergible por centrífuga…), no se cierra con ella.

## 4. Grupo débil: sin ficha de banco

**54 recursos (393 usos) no tienen ficha en ninguno de los dos bancos** y conservan el precio de la matriz dentro de una horquilla de mercado declarada. Es el grupo con menor evidencia: ningún banco regional ni oferta puntual demuestra una media nacional. Los de más uso:

- MT-PERFIL-ALUM 74 usos · MT-SENAL-OBRA 73 · MT-REGUL-GAS 37 · MT-SOPORTE-AC 36 · MT-VIDRIO-TEMP 35 · MT-RIEL-CORRED 17 · MT-SELLA-PASE 17 · MT-SAN-FIJA 13 · MT-AISL-REFLECT 9 · MT-GRAMA 4 · MT-PERSIANA-ALU 4 · MT-TOLDO 4.

39 de los 54 los usa al menos una partida. Excepción declarada y marcada para revisión: `MT-PLANTA-ELEC` 1.367,09 €/ud, fuera de su propia horquilla 6.000–12.000 €/ud y sin uso en el catálogo.

## 5. Qué no se pudo cerrar con los bancos

- 263 recursos siguen de **fuente única** (su precio viene de un lote concreto: convenios, modelo de compra y amortización, composición de consumibles, contraste de mercado…). Ninguna segunda fuente independiente los corrobora ni los contradice: siguen `en_revision` y no se promocionan.
- 32 recursos sin usos (`MT-DOM-*` completos, `MT-DPS-*`, `MT-PANEL-SOLAR`, `MT-INVERSOR`, `MT-PARARRAYOS-*`, `MT-PLANTA-ELEC`, `MT-CAMARA-CCTV`, `MT-ALARMA`, `MT-BATERIA`, `MT-BOMBA-AGUA`, `MT-HIDRONEUMATICO`, `MT-CONT-DESCARGAS`, `MT-AUTOM-PORTON`) tienen precio por cierre total, pero sin partida que lo valide; mantener como catálogo o dar de baja es una decisión de producto, no de precios.

## 6. Reproducibilidad

Cadena completa, sin ejecutar SQL ni desplegar:

```
python3 tools/leer_bcca.py bases_precios/BCCA2023_V02.bc3          # 5.925 precios, sha256 bee06981…
python3 tools/cribar_precios_espana.py --bc3 bases_precios/BCCA2023_V02.bc3 --completo --sinonimos --banco bcca --edicion 2023
python3 tools/cribar_precios_espana.py --bc3 bases_precios/BCEXTGREM_26_v1.bc3 --sinonimos --banco extremadura --edicion 2026
python3 tools/verificar_precios_espana.py                          # 52 confirmados / 66 divergencias / 263 única fuente
python3 tools/confirmar_precios_espana.py --aplicar                # idempotente; nada se sobrescribe
python3 tools/generar_matriz_precios_espana.py                     # 388 filas: 43 directas + 345 derivadas
python3 tools/inventario_precios_espana.py
python3 tools/generar_precios_publicos.py                          # ES.json, 2.016 partidas
python3 tools/generar_sql_precios_espana.py                        # 388 filas, NO ejecutado
```

Suite: `python3 -m pytest -n 2` → 3651 passed, 13 skipped. `bases_precios/` no está versionada (git-ignorado); los CSV de cribado y verificación en `docs/auditoria_precios/` son los artefactos trazables de esta ronda.