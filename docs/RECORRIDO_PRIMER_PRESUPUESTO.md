# Recorrido ideal hasta el primer presupuesto en PDF

**Producto:** CotizaT
**Etapa:** 1 — versión comercial local
**Tarea:** E1-008
**Fecha:** 13 de agosto de 2026

## Objetivo

Una persona que hoy trabaja con papel o Excel debe poder configurar CotizaT y descargar un primer presupuesto real en menos de 20 minutos, sin necesitar una explicación continua del desarrollador.

El recorrido básico no debe exponer costes avanzados, alternativas, facturación, proyectos ni configuraciones regionales antes de que sean necesarios.

## Punto de inicio

El cronómetro funcional comienza cuando aparece el asistente de configuración y termina con la primera descarga de un PDF real. El tiempo empleado instalando o abriendo el programa se medirá por separado en las pruebas externas.

## Secuencia principal

1. **Identificar la empresa**
   - Nombre comercial obligatorio.
   - Razón social, RIF, contacto, ubicación y logo opcionales.
   - Moneda e IVA configurados con valores editables.
2. **Elegir el catálogo inicial**
   - **Catálogo de CotizaT (recomendado):** partidas, descompuestos, recursos y referencias de precios del país elegido; además incluye productos, packs, cliente y presupuesto ficticios para explorar el flujo.
   - **Mis propias partidas / inicio en limpio:** ninguna partida, producto, pack, cliente o presupuesto precargado; está pensado para quien ya tiene una base lista para importar.
3. **Revisar o cargar el catálogo**
   - Quien eligió el catálogo de CotizaT comprueba que las referencias de precios y su alcance encajan con su trabajo.
   - Quien eligió el inicio en limpio crea una partida o importa su catálogo desde Excel o BC3.
4. **Crear un cliente real**
   - Solo nombre obligatorio; el resto puede completarse después.
5. **Crear el primer presupuesto real**
   - Elegir cliente.
   - Añadir capítulo o pack.
   - Añadir partidas desde catálogo/importación.
   - Confirmar cantidades, precios, moneda e IVA.
   - Guardar.
6. **Revisar y descargar el PDF**
   - Abrir el detalle.
   - Revisar empresa, cliente, alcance, totales y condiciones.
   - Descargar el PDF.

## Presupuesto temporal inicial

| Acción | Meta orientativa |
|---|---:|
| Asistente de empresa y modo inicial | 3 min |
| Revisión/importación mínima de catálogo | 5 min |
| Crear cliente | 2 min |
| Crear y guardar presupuesto | 7 min |
| Revisar y descargar PDF | 3 min |
| **Total** | **20 min** |

Estas cifras son hipótesis de diseño, no resultados validados. E1-012 y E1-013 deberán medirlas con usuarios externos.

## Señales registradas localmente

CotizaT conserva en la configuración local, sin telemetría externa:

- fecha de primera apertura y de finalización del asistente;
- modo elegido (`demo` o `limpio`);
- apertura del catálogo desde la guía;
- existencia de cliente y presupuesto no marcados como demo;
- primera descarga de un PDF no marcado como demo;
- fecha de esa primera descarga.

La diferencia entre primera apertura del asistente y primera descarga permitirá contrastar el tiempo total en pruebas observadas; la fecha de finalización también separa la configuración del resto del recorrido. No debe interpretarse como uso continuo si la persona cierra la aplicación entre ambos eventos: el observador anotará interrupciones.

## Reglas de honestidad

- Los datos de demostración deben estar identificados visualmente.
- Un cliente, presupuesto o PDF demo no completa los pasos reales.
- La opción limpia no debe inyectar contenido en reinicios posteriores.
- Los precios precargados no deben presentarse como vigentes para una región o fecha concreta.
- Descargar un PDF no implica que se haya enviado ni aprobado.

## Criterios de aceptación técnica

- Una instalación nueva abre el asistente desde `/`.
- Una actualización de una base anterior no abre el asistente ni altera datos.
- El modo demo crea contenido ficticio una sola vez.
- El modo limpio deja vacíos catálogos y documentos.
- El dashboard muestra cinco pasos verificables.
- El progreso distingue registros demo de registros reales.
- La primera descarga de un PDF real queda fechada localmente.
- Las migraciones y ambos modos están cubiertos por pruebas automatizadas.

## Pendiente de validación externa

- Comprensión de los términos «partida», «capítulo», «pack» y «catálogo».
- Si el usuario prefiere comenzar por el cliente o por el catálogo.
- Si 20 minutos es una meta realista con catálogos propios.
- Qué campos empresariales causan abandono.
- Si el ejemplo ayuda o distrae.
