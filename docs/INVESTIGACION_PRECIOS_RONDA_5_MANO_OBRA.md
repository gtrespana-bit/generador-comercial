# Investigación de precios — Ronda 5: mano de obra y rendimientos

**Fecha:** 2026-08-19  
**Mercados:** Colombia, Perú, México y Ecuador

> Los jornales de fuentes de mercado no equivalen automáticamente al coste laboral total. Se separan jornal base, cargas/beneficios y tarifa interna de la empresa.

| Categoría | Colombia / día | Perú / día | México / día | Ecuador / día |
|---|---:|---:|---:|---:|
| Oficial / albañil | 90.000–130.000 COP | 69,75 PEN oficial básico 2026 | 650–850 MXN | 21,67 USD referencia sectorial |
| Ayudante / peón | 60.000–85.000 COP | 62,80 PEN peón básico 2026 | 350–450 MXN | 20,00–20,63 USD |
| Maestro de obra | 120.000–180.000 COP | pendiente de fuente comparable | 1.200–1.800 MXN | 23,33–25,83 USD |
| Electricista oficial | 100.000–150.000 COP | pendiente | 950–1.300 MXN | 22,71 USD |
| Plomero oficial | 95.000–145.000 COP | pendiente | 900–1.200 MXN | 22,29 USD |
| Pintor | 65.000–110.000 COP | pendiente | 600–800 MXN | 20,83 USD |
| Soldador | 110.000–165.000 COP | pendiente | 1.100–1.600 MXN | 27,08 USD |

## Fuentes

- Colombia: rangos de jornal por oficio y rendimientos de mampostería, pintura, drywall e instalaciones.[1](https://oneestimate.ai/en/blog/costos-construccion-por-m2-colombia-2026) [2](https://oneestimate.ai/en/blog/lista-precios-mano-obra-construccion-colombia-2026) [3](https://co.computrabajo.com/salarios/ayudante-de-construccion)
- Perú: el convenio colectivo de construcción civil 2026 fija jornal básico de S/ 89,30 para operario, S/ 69,75 para oficial y S/ 62,80 para peón.[4](https://www.ftccp.com/index.php/es/component/content/article/negociacion-colectiva-construccion-civil-2026-aumento-salarial-peru?catid=24&Itemid=122) [5](https://elperuano.pe/noticia/286045-construccion-civil-2026-revisa-si-te-corresponde-el-nuevo-aumento-del-jornal)
- México: se contrastaron rangos por oficio, jornal y mano de obra por m²; también se comprobó que el salario mínimo profesional de albañilería es distinto del salario general.[6](https://oneestimate.ai/en/blog/precios-mano-obra-construccion-2026) [7](https://www.telediario.mx/comunidad/salario-minimo-albanil-cuanto-debe-ganar-2026) [8](https://mx.computrabajo.com/salarios/albanil)
- Ecuador: referencias sectoriales separan jornal básico y coste real con beneficios sociales; se observaron oficiales alrededor de 21,67 USD/día y peones alrededor de 20 USD/día.[9](https://oneestimate.ai/es/blog/precios-mano-obra-construccion-ecuador-2026) [10](https://oneestimate.ai/en/blog/rendimientos-mano-obra-construccion-ecuador)

## Reglas para el modelo

- La tarifa se guardará por país y categoría.
- Debe distinguir jornal, hora y coste empresa.
- El usuario podrá definir su tarifa propia.
- La tarifa nacional de referencia no sustituye automáticamente la tarifa de una empresa.
- Los beneficios legales no se mezclarán con el precio neto del trabajador.
- Los rendimientos se guardarán como producción por jornada o horas por unidad.
- El precio de mano de obra de una partida se calculará como:

```text
coste de cuadrilla por jornada / producción de la cuadrilla por jornada
```

- Un rendimiento por m² no se convertirá directamente a tarifa/h sin conservar la jornada y la composición de cuadrilla.

## Observaciones

- Perú es el país con mejor referencia normativa localizada en esta ronda porque existe convenio colectivo 2026 publicado por la federación sectorial.
- Ecuador debe separar salario sectorial y coste real del empleador, especialmente por IESS, décimos, vacaciones y fondos de reserva.
- Colombia y México requieren continuar contrastando fuentes oficiales y regionales antes de marcar tarifas como confirmadas.
- Los rendimientos nacionales deben mantenerse como referencia: una empresa puede sobrescribirlos por ciudad, cuadrilla o experiencia propia.
