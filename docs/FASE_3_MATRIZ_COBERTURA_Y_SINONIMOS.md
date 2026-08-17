# Fase 3 — Matriz de cobertura y sinónimos

**Estado:** completada el 16/08/2026

## Objetivo

Definir de antemano qué debe contener el catálogo general, cuánto falta en cada
familia y con qué palabras lo buscarán profesionales de distintos países y
oficios. La expansión deja de depender de solicitudes aisladas del cliente.

## Matriz exhaustiva

La matriz cubre los **18 capítulos y 172 subcapítulos** de la taxonomía v2.
Para cada familia registra:

- partidas y apartados actuales;
- objetivo mínimo y objetivo amplio;
- brecha pendiente;
- estado de cobertura;
- operaciones obligatorias;
- criterios de variación técnica.

Fuentes y salidas:

```text
basedatos_partidas/datos/objetivos_cobertura.json
basedatos_partidas/planificar_cobertura.py
basedatos_partidas/salida/matriz_cobertura.json
basedatos_partidas/salida/matriz_cobertura.csv
basedatos_partidas/salida/RESUMEN_COBERTURA.md
```

El comando reproducible es:

```bash
.venv/bin/python basedatos_partidas/planificar_cobertura.py
```

## Resultado cuantitativo

| Indicador | Resultado |
|---|---:|
| Partidas actuales | **540** |
| Objetivo mínimo | **3.000** |
| Brecha mínima | **2.460** |
| Objetivo amplio | **5.000** |
| Brecha amplia | **4.460** |
| Subcapítulos totales | **172** |
| Subcapítulos sin cobertura | **64** |
| Subcapítulos en estado crítico | **65** |

Los objetivos por capítulo suman exactamente 3.000 y 5.000; los objetivos por
subcapítulo se distribuyen de forma determinista, reservando cobertura incluso
a familias hoy vacías.

Las mayores brechas por capítulo son:

- `09 Instalaciones`: 482 partidas hasta el mínimo;
- `12 Revestimientos y acabados`: 296;
- `02 Demoliciones y desmontajes`: 157;
- `07 Carpintería, herrería, vidrios y protección solar`: 154;
- `06 Fachadas y particiones`: 142;
- `14 Obras exteriores y urbanismo`: 141.

Los capítulos 08, 16 y 18 parten completamente vacíos y quedan identificados
como lotes obligatorios, no como contenido opcional.

## Operaciones y variaciones

La matriz no mide únicamente cantidad. Según la familia exige combinaciones de:

- suministro e instalación;
- solo instalación;
- reparación y sustitución;
- desmontaje con y sin recuperación;
- demolición manual y mecánica;
- preparación, remates y protección;
- pruebas, regulación y puesta en marcha;
- mantenimiento;
- materiales, espesores, dimensiones, prestaciones y métodos de ejecución.

Una familia no se considerará cerrada mientras el ciclo normal de trabajo siga
obligando a crear conceptos manuales.

## Tesauro de búsqueda

Se creó:

```text
basedatos_partidas/datos/sinonimos_busqueda.json
app/services/busqueda_catalogo.py
```

Cobertura inicial:

| Indicador | Resultado |
|---|---:|
| Grupos bidireccionales | **146** |
| Términos y expresiones | **661** |
| Capítulos cubiertos | **18 de 18** |

Incluye terminología venezolana, peninsular, latinoamericana, inglesa de uso
comercial y vocabulario de oficio. Ejemplos:

- concreto ↔ hormigón;
- plomería ↔ fontanería;
- tomacorriente ↔ enchufe;
- cielo raso ↔ falso techo ↔ plafón;
- friso ↔ revoque ↔ repello ↔ pañete;
- afirmado ↔ contrapiso ↔ recrecido;
- drywall ↔ yeso laminado ↔ tablaroca ↔ gypsum;
- mesón ↔ encimera ↔ tope;
- closet ↔ armario ↔ ropero.

El tesauro no cambia el texto de las partidas. Solo amplía la localización:
CotizaT sigue mostrando terminología venezolana, pero entiende cómo busca cada
usuario.

## Integración en la aplicación

- El índice ligero añade sinónimos relevantes según el capítulo.
- La búsqueda remota expande cada palabra en grupos OR y mantiene AND entre
  conceptos distintos.
- `/partidas`, el árbol y Spotlight usan el mismo criterio.
- La expansión es bidireccional: buscar el término principal o cualquiera de
  sus alias devuelve la misma familia.
- El fichero es editable sin cambiar código y queda cubierto por pruebas.

## Validación

- La matriz valida 18 capítulos, 172 subcapítulos y sumas exactas 3.000/5.000.
- El tesauro valida cobertura de los 18 capítulos y bidireccionalidad de casos
  críticos.
- La búsqueda HTTP comprueba que «hormigón» encuentra partidas de concreto.
- Las salidas CSV no generan espacios finales y abren correctamente en Excel.

## Siguiente paso

Comenzar la producción por lotes de familias completas. El primer frente será
`09 Instalaciones`, priorizando las familias sin cobertura y las de mayor
brecha, seguido de `12 Revestimientos y acabados`.
