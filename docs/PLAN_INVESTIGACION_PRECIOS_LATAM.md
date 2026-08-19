# Plan de investigación de precios nacionales — Bloque 7

**Fecha:** 2026-08-19

## Mercados activos para la investigación

- Colombia — COP
- Perú — PEN
- México — MXN
- Ecuador — USD
- Venezuela — USD, ya existente y fuera de esta primera ronda de investigación

> Venezuela no se cuenta como uno de los cuatro mercados nuevos: su catálogo USD ya existe.

## Alcance técnico

El catálogo contiene aproximadamente 3.006 partidas, pero no se investigará un precio independiente para cada partida. Las partidas se calculan a partir de un cuadro de recursos compartidos. La primera ronda investigará y normalizará todos los recursos materiales, mano de obra y maquinaria existentes en `basedatos_partidas/datos/recursos.json`, que es la fuente actual del catálogo.

Los productos elegidos por el cliente —porcelanatos, sanitarios, griferías, puertas y similares— se tratarán como productos comerciales y no se mezclarán con los recursos técnicos de las descomposiciones.

## Método

Para cada recurso y país se guardará:

- código estable del recurso;
- descripción normalizada;
- unidad exacta;
- país;
- moneda;
- precio mínimo observado;
- precio máximo observado;
- precio de referencia seleccionado;
- fecha de consulta;
- fuente;
- proveedor o canal;
- nivel de confianza;
- observaciones de presentación, transporte o región.

## Jerarquía de fuentes

1. Fabricantes y distribuidores nacionales.
2. Grandes cadenas y ferreterías con precio público.
3. Cámaras, índices oficiales y bases sectoriales.
4. Proveedores especializados.
5. Fuentes de mercado secundarias, solo como contraste.

Las fuentes secundarias no se marcarán como precio confirmado sin contraste. Cuando solo exista un rango, se almacenará el rango y se elegirá un valor de referencia documentado.

## Normalización

Antes de cargar un precio se comprobará:

- presentación: saco, bulto, rollo, varilla, m3, kg, litro, m2 o unidad;
- si incluye IVA;
- si incluye transporte;
- ciudad o región de referencia;
- equivalencia entre unidades;
- marca y calidad;
- fecha de vigencia;
- si el precio corresponde a venta minorista o mayorista.

## Política de confianza

- `confirmado`: contrastado con dos o más fuentes fiables o una fuente primaria clara;
- `referencia`: dato útil de mercado con una fuente razonable, pendiente de validación adicional;
- `provisional`: estimación o única fuente débil;
- `derivado`: calculado desde otros recursos;
- `desactualizado`: fuera de la vigencia definida.

## Ronda de trabajo

1. Materiales estructurales y agregados.
2. Mampostería, morteros y placas.
3. Instalaciones eléctricas, hidrosanitarias y climatización.
4. Cubiertas, impermeabilización y acabados técnicos.
5. Mano de obra nacional por categoría.
6. Equipos, alquileres y transporte.
7. Contraste, normalización y carga en la tabla de precios por mercado.
8. Prueba de una partida representativa por país.

## Regla de no impacto histórico

La carga o actualización de precios nacionales solo afectará:

- nuevas partidas;
- nuevas descomposiciones;
- borradores cuando el usuario confirme la actualización.

No modificará automáticamente presupuestos enviados, aprobados, proyectos, facturas ni cambios de alcance históricos.
