# Metodología de precios referenciales nacionales LatAm

**Fecha de corte:** 20/08/2026  
**Mercados:** Venezuela, Colombia, Perú, México y Ecuador.

## Propósito

CotizaT es una herramienta de soporte para presupuestar. No promete el precio
exacto de una tienda, proveedor, ciudad o fecha futura. Entrega un **precio
referencial nacional**, su rango, fecha, fuente y nivel de confianza, para que
la empresa tenga una base inicial y pueda sustituirla por su precio propio.

En un mercado volátil no sería honesto mostrar una falsa precisión local. Por
eso el modelo no segmenta por ciudad: conserva un rango nacional y advierte al
usuario que confirme marca, proveedor, presentación, IVA, transporte, volumen
y disponibilidad.

## Evidencia disponible

Las siete rondas versionadas en el repositorio investigan las familias que
marcan el nivel de cada mercado:

1. estructura, cemento, agregados y mampostería;
2. construcción en seco y placas;
3. pintura e instalaciones;
4. impermeabilización y adhesivos;
5. mano de obra y rendimientos;
6. equipos y maquinaria;
7. transporte y fletes.

Los valores observados directamente se guardan como `referencia`. Las
especialidades o recursos sin una observación pública exactamente equivalente
se calculan con la canasta nacional y se guardan como `derivado`. Ambos son
precios referenciales; la etiqueta permite saber cómo se obtuvieron.

## Cálculo de una referencia derivada

Para cada país y familia (`materiales` o `maquinaria`):

1. Se toman únicamente los recursos con observación directa normalizada.
2. Para cada ancla se compara el precio local observado con el precio base USD
   convertido a la tasa de corte.
3. Se usa la **mediana** de esas relaciones como factor nacional. La mediana
   evita que una marca premium o una promoción puntual domine la canasta.
4. Los límites se calculan con las medianas equivalentes de los mínimos y
   máximos observados.
5. El recurso sin observación individual se obtiene así:

```text
referencia nacional = precio base USD × tasa de corte × factor de canasta
rango nacional       = precio base USD × tasa de corte × [factor mín., factor máx.]
```

No es una simple conversión monetaria: el factor refleja cuánto más alto o más
bajo está el mercado nacional frente a la canasta base investigada.

## Factores de la canasta de agosto de 2026

| País | Familia | Factor central | Rango de factor |
|---|---|---:|---:|
| Colombia | Materiales | 1,327 | 1,000–1,659 |
| Colombia | Maquinaria | 1,096 | 0,822–1,370 |
| Perú | Materiales | 0,962 | 0,674–1,102 |
| Perú | Maquinaria | 1,709 | 1,543–1,875 |
| México | Materiales | 1,163 | 0,909–1,554 |
| México | Maquinaria | 1,842 | 1,340–2,512 |
| Ecuador | Materiales | 0,817 | 0,708–0,933 |
| Ecuador | Maquinaria | 0,857 | 0,857–0,857 |

La maquinaria ecuatoriana solo tiene una ancla pública comparable; su rango
estrecho describe la evidencia encontrada, no una garantía de baja variación.
La interfaz sigue mostrando la confianza `derivado` y el aviso de verificación.

## Mano de obra

Los jornales se normalizan a una jornada de ocho horas. Cuando la ronda 5
ofrece una tarifa del oficio se usa como `referencia`; cuando solo existe el
oficial general, la especialidad hereda esa tarifa como `derivado`. Ayudante
especializado se sitúa entre ayudante y oficial. Las cargas del empleador no se
mezclan silenciosamente con el jornal y cada empresa puede introducir su coste
real.

## Reglas de presentación

Cada fila conserva:

- país y moneda;
- código y unidad del recurso;
- referencia y rango nacional;
- fecha de consulta/cálculo;
- fuente o metodología;
- confianza (`referencia` o `derivado`);
- estado de IVA y transporte;
- observaciones y aviso de comprobación.

La aplicación resuelve en este orden:

1. precio propio de la organización;
2. referencia nacional directa o derivada;
3. precio base de respaldo, únicamente si faltase una referencia.

Los presupuestos enviados o aprobados conservan el precio y la moneda con los
que fueron creados; una actualización posterior no altera documentos
históricos.

## Cobertura

La matriz resultante contiene **388 recursos físicos × 4 mercados = 1.552
referencias nacionales**. Venezuela utiliza su cuadro USD de 388 recursos, con
estado de verificación visible. Los cuatro recursos compuestos se desglosan en
sus componentes y no se duplican como filas de mercado.

## Actualización

La matriz es una fotografía fechada, no un precio eterno. Para una nueva ronda:

1. actualizar las anclas observadas;
2. conservar presentación y rango;
3. actualizar la tasa de corte;
4. regenerar la matriz;
5. revisar variaciones anómalas;
6. ejecutar la auditoría de lanzamiento y los presupuestos de aceptación.

El usuario siempre podrá reemplazar la referencia por su precio negociado sin
modificar la referencia nacional ni los presupuestos históricos.
