# Estrategia de catálogo extenso

**Decisión de producto — 16/08/2026**

## Principio no negociable

CotizaT debe llegar con un catálogo suficientemente amplio para que el cliente
pueda presupuestar sin tener que construir primero su propia base de partidas.
Es preferible que una organización oculte conceptos que no usa a que abandone
el producto porque no encuentra los que necesita.

La cobertura deja de plantearse como «catálogo mínimo útil». El producto debe
ofrecer un **catálogo general extenso de fábrica**, organizado para que el
volumen no perjudique la velocidad de búsqueda.

## Objetivo de cobertura

- **Mínimo de lanzamiento del catálogo general:** alrededor de **3.000 partidas
  base** con descomposición completa.
- **Objetivo de cobertura amplia:** **4.000–5.000 partidas base**.
- **Sin techo artificial:** se seguirán incorporando familias cuando exista una
  diferencia técnica, de medición, ejecución o coste real.
- Las variantes paramétricas y productos asociados multiplicarán las soluciones
  disponibles sin llenar el árbol de duplicados por color, marca o modelo.

Las metas intermedias de 800 y 1.200 partidas pasan a ser únicamente hitos
internos de producción. **No representan el catálogo final ni el nivel de
cobertura con el que se considera terminado el trabajo.**

## Qué significa «tenerlo todo»

Cada sistema debe cubrir, cuando corresponda:

1. suministro y colocación;
2. solo colocación cuando el producto lo aporta el cliente;
3. desmontaje con recuperación;
4. demolición y retiro;
5. reparación localizada;
6. sustitución completa;
7. preparación del soporte;
8. remates y encuentros;
9. pruebas, regulación y puesta en marcha;
10. mantenimiento preventivo y correctivo;
11. variantes por material, prestaciones y método de ejecución;
12. unidades de medición realmente utilizadas en Venezuela.

No basta con contar partidas. Una familia se considera cubierta cuando permite
presupuestar el ciclo completo del trabajo sin recurrir a una partida manual.

## Cobertura funcional prioritaria

La expansión se realizará por matrices completas, no añadiendo conceptos
sueltos:

- actuaciones previas, diagnóstico, protección y medios auxiliares;
- demoliciones de todos los sistemas constructivos;
- terreno, fundaciones, estructuras y refuerzos;
- fachadas, mampostería, tabiquería y sistemas secos;
- carpintería, herrería, vidrios, herrajes y protección solar;
- remates, ayudas, rozas, perforaciones, recibidos y sellados;
- agua, desagüe, electricidad, iluminación, datos, seguridad, domótica,
  climatización, ventilación, gas, incendios, bombeo y respaldo;
- aislamiento, impermeabilización y tratamiento de humedades;
- techos y cubiertas completas;
- frisos, enchapados, pisos, escaleras, cielos rasos, pintura y recubrimientos;
- cocinas, baños, closets, equipamiento comercial y accesibilidad;
- exteriores, drenajes, piscinas, jardinería, riego e iluminación;
- residuos, limpieza, ensayos, puesta en marcha y seguridad de obra;
- rehabilitación energética.

## Organización para miles de partidas

El código continúa siendo `CC.SS.AA.NNN` y la ruta continúa siendo:

```text
Capítulo → Subcapítulo → Apartado → Partida
```

Reglas de usabilidad:

- ningún apartado debe convertirse en una lista interminable;
- al superar unas 20–25 partidas debe evaluarse una división adicional o una
  variante paramétrica;
- búsqueda por código nuevo, código anterior, nombre, ruta y sinónimos;
- resultados con ruta completa;
- vistas de recientes, más usadas y favoritas;
- carga progresiva: el navegador no debe descargar miles de descompuestos al
  abrir un presupuesto;
- productos comerciales separados de la definición técnica del trabajo.

## Personalización por organización

Las partidas oficiales no deberían perderse mediante borrado físico. La acción
que el usuario percibe como «eliminar de mi catálogo» debe comportarse como
**ocultar/desactivar para su organización**:

- deja de aparecer en búsquedas y navegación normales;
- puede restaurarse desde «Partidas ocultas»;
- una actualización no vuelve a mostrarla por sorpresa;
- las nuevas partidas oficiales sí se incorporan automáticamente;
- las partidas creadas por la organización siguen siendo privadas y editables;
- los presupuestos históricos nunca cambian.

Esto requiere evolucionar el actual modelo de copia por organización con un
estado explícito de visibilidad y una identidad oficial estable.

## Rendimiento para 5.000 partidas — implantado

La fase 1 quedó completada el 16/08/2026:

1. índice ligero para el árbol;
2. búsqueda local y bajo demanda;
3. carga de ficha y descompuesto solo al previsualizar o insertar;
4. caché local de fichas y peticiones en curso;
5. renderizado progresivo de ramas;
6. métricas de búsquedas sin resultado;
7. pantalla de gestión paginada a 100 filas.

La prueba sintética de 5.000 partidas abrió el editor entre 1,1 y 2,1 s en
ejecuciones repetidas del sandbox y la pantalla de gestión alrededor de 0,13 s.
Detalle en `docs/FASE_1_CATALOGO_ESCALABLE.md`.

## Control de calidad y condición de salida

Cada partida oficial debe tener:

- ruta completa y código único;
- nombre y descripción propios;
- unidad correcta;
- criterio de medición;
- recursos y rendimientos;
- coste directo y precio;
- terminología venezolana;
- producto del cliente separado cuando corresponda;
- validación automática del descompuesto;
- estado del precio y fuente de contraste.

Antes de considerar completa una ronda se probarán presupuestos tipo de
viviendas, apartamentos, comercios, oficinas, condominios, exteriores y
reparaciones. Las búsquedas sin resultado detectadas por el equipo se convierten
en trabajo de catálogo antes de que las encuentre un cliente.

## Orden de ejecución

1. ✅ Preparar la aplicación para navegar 5.000 partidas sin degradación.
2. ✅ Incorporar ocultación/restauración por organización y actualización
   incremental del catálogo oficial.
3. ✅ Construir inventario de cobertura y sinónimos por cada uno de los 18
   capítulos.
4. **Siguiente:** producir familias completas, comenzando por instalaciones y acabados.
5. Validar cada lote con importador, terminología, precios y presupuestos tipo.
6. Continuar hasta superar el mínimo de 3.000 y cerrar la matriz prevista; el
   objetivo posterior es 4.000–5.000 sin sacrificar calidad.
