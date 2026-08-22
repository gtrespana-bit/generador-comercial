# Asistente CotizaT: copiloto funcional y herramientas deterministas

**Estado:** implementado  
**Última actualización:** 22 de agosto de 2026

## 1. Objetivo

El Asistente CotizaT no se limita a generar explicaciones. Antes de recurrir a
un modelo de lenguaje, identifica solicitudes que puede resolver con datos y
reglas de CotizaT, ejecuta la herramienta correspondiente en el servidor y
presenta resultados verificables y acciones confirmables.

Principios de diseño:

1. **Resolver antes de explicar.** Una petición de búsqueda consulta la base de
   datos; no responde únicamente cómo usar el buscador.
2. **Datos reales antes que texto generado.** Códigos, precios, clientes,
   presupuestos y recursos proceden de la organización activa.
3. **Sin escrituras silenciosas.** Toda acción que modifica el borrador exige
   selección o confirmación explícita.
4. **Cálculos en servidor.** Las mediciones y revisiones deterministas no se
   delegan al modelo generativo.
5. **IA externa opcional.** Las herramientas locales funcionan sin Groq.

## 2. Arquitectura de resolución

El flujo de `/api/ia/chat` sigue este orden:

1. Recibe los mensajes y un contexto mínimo de pantalla.
2. Verifica la organización mediante la sesión autenticada y el filtro tenant.
3. Intenta resolver una herramienta determinista:
   - revisión del borrador;
   - mediciones;
   - preparación de lotes;
   - detección de alcance;
   - búsquedas internas;
   - revisión del presupuesto guardado;
   - Packs de estancia.
4. Si no corresponde ninguna herramienta, consulta el índice local de ayuda.
5. Solo entonces, si existe `GROQ_API_KEY`, utiliza GPT OSS mediante Groq para
   conversación o redacción generativa.

Módulos principales:

- `app/services/asistente_ia.py`: orquestación, prompt, streaming y búsqueda de
  partidas.
- `app/services/herramientas_ia.py`: enrutamiento de intenciones y presentación
  de herramientas deterministas.
- `app/services/copiloto_presupuesto.py`: revisión viva, mediciones, lotes y
  reglas de alcance.
- `app/services/busqueda_catalogo.py`: normalización, sinónimos y variantes sin
  tildes.
- `app/static/js/asistente_ia.js`: chat, contexto de pantalla, acciones y
  confirmaciones.
- `app/static/js/editor/catalogo.js`: carga e inserción individual o múltiple de
  fichas del catálogo.

## 3. Contexto de pantalla y privacidad

El navegador puede enviar:

```json
{
  "pagina": "/presupuestos/42/editar",
  "presupuesto_id": 42,
  "borrador": [
    {
      "nombre": "DEMOLICIONES",
      "partidas": []
    }
  ]
}
```

Reglas:

- La ruta se reduce a un formato interno válido.
- El `presupuesto_id` se vuelve a consultar dentro del tenant activo; no se
  confía en nombres o estados enviados por el navegador.
- El borrador solo viaja para herramientas que necesitan analizarlo.
- El borrador **no se incorpora al prompt de Groq**.
- El servidor limita el análisis a 100 capítulos y 600 partidas.
- Ningún resultado puede atravesar el filtro de organización del ORM/RLS.

## 4. Búsquedas funcionales

El asistente busca directamente:

- partidas;
- clientes;
- presupuestos;
- productos;
- recursos.

Ejemplos:

- `¿Qué partida uso para demolición de porcelanato?`
- `Busca el cliente Constructora Luna.`
- `Encuentra el producto POR-6060.`
- `Busca el recurso cemento gris.`
- `Busca el presupuesto P-2026-001.`

Las partidas muestran código, nombre, unidad, precio, moneda, ruta de catálogo
y enlace a la ficha. Desde el editor también ofrecen la acción de añadirlas al
borrador.

La búsqueda tolera expresiones conversacionales, omisión de tildes y sinónimos
de oficio. Por ejemplo, `demolicion`, `demoler`, `quitar`, `picar`, `ceramica`
y `porcelanato` pueden conducir a los conceptos técnicos relacionados.

Si no existe una coincidencia suficientemente fiable, el asistente lo indica y
no inventa códigos ni precios. La consulta sin resultado queda registrada en
logs con organización, tipo y texto para mejorar catálogo y sinónimos.

## 5. Revisión del borrador visible

Consulta recomendada:

```text
Revisa este presupuesto y dime si está listo para enviar.
```

Cuando el editor está abierto, la revisión utiliza su serialización actual y
comprueba:

- capítulos vacíos o sin nombre;
- partidas sin nombre;
- precio o cantidad efectiva en cero;
- partidas duplicadas;
- unidades vacías o inusuales;
- diferencia entre cantidad directa y suma de mediciones;
- costes internos superiores al precio de venta;
- productos sin precio de venta o sin coste de compra.

Devuelve puntuación estructural, puntos críticos, avisos y enlaces declarativos
`Ir al campo`. Estos enlaces despliegan el capítulo, resaltan la partida y
colocan el foco sin guardar ni modificar datos.

Si no se recibe un borrador vivo, la revisión usa el presupuesto guardado y el
servicio `revision_presupuesto.py`, que además analiza cliente, contacto,
margen, tiempos, logo, validez, moneda y versiones.

## 6. Asistente de mediciones

Ejemplo:

```text
El baño mide 3 × 2 m, tiene 2,40 m de altura, una puerta de
0,80 × 2,10 m y 10 % de desperdicio.
```

El servidor calcula con `Decimal` y redondeo comercial:

- superficie de piso;
- perímetro;
- rodapié, descontando anchos de puertas;
- superficie bruta y neta de paredes;
- descuento de puertas, ventanas y huecos;
- cantidades con desperdicio o merma.

Cada resultado puede aplicarse como medición. Antes de hacerlo, CotizaT abre un
selector de partidas compatibles por unidad y nombre; el usuario elige destino
y pulsa `Confirmar medición`.

Limitación actual: el reconocimiento geométrico está orientado a estancias
rectangulares con dimensiones explícitas. Las plantas irregulares deben
separarse en varios rectángulos o cargarse manualmente.

## 7. Preparación e inserción múltiple de partidas

Ejemplo:

```text
Prepara las partidas necesarias para demolición de porcelanato.
```

El servidor reconoce flujos iniciales de:

- demolición de porcelanato o cerámica;
- pintura;
- remodelación de baño.

Cada flujo se resuelve contra el catálogo activo. No se crean partidas
inexistentes y se excluyen conceptos que ya estén vinculados en el borrador.

La acción `Revisar selección y añadir` abre un modal que permite:

1. revisar códigos y nombres;
2. desmarcar conceptos;
3. identificar partidas ya presentes;
4. elegir el capítulo de destino;
5. cancelar o confirmar.

El lote confirmado se incorpora como una sola operación lógica de deshacer. El
borrador continúa siendo editable y se guarda mediante el autosave normal.

## 8. Detector de posibles faltantes de alcance

Ejemplo:

```text
¿Qué falta en el alcance de este presupuesto?
```

Cobertura inicial:

| Disparador | Complementos revisados |
| --- | --- |
| Demolición o desmontaje | protecciones; gestión/transporte de escombros |
| Porcelanato, cerámica o enchapado | preparación, regularización o nivelación del soporte |
| Baño, ducha, lavadero o terraza con revestimientos | impermeabilización |
| Pintura | preparación de superficies; imprimación o fondo |

El detector consulta nombres, capítulos y descripciones. Si una descripción ya
incluye el complemento, intenta no proponer una partida separada. Cada aviso se
presenta como **posible faltante**, nunca como obligación contractual.

Las soluciones sugeridas se vinculan a partidas reales del catálogo. El usuario
puede revisar y añadir una selección mediante el mismo modal de lotes.

## 9. Acciones declarativas y confirmación

Las respuestas pueden contener enlaces internos bajo `/api/ia/accion/...`.
No son endpoints de escritura. El renderizador seguro del navegador los
intercepta y ejecuta contra el editor abierto:

- `agregar-partida`;
- `agregar-lote`;
- `aplicar-medicion`;
- `enfocar-borrador`;
- `abrir-pack`.

Las acciones que cambian el borrador muestran confirmación o un modal de
selección. La ficha completa vuelve a cargarse desde un endpoint autenticado y
filtrado por tenant antes de insertarse.

## 10. Coste y configuración

No requieren IA generativa ni consumen tokens:

- búsquedas internas;
- revisión guardada o viva;
- mediciones;
- lotes;
- detector de alcance;
- acciones del editor;
- Packs y navegación.

Groq es opcional para redacción y conversación abierta:

```env
GROQ_API_KEY=gsk_REEMPLAZAR_SOLO_EN_EL_BACKEND
COTIZAT_IA_MODEL=openai/gpt-oss-120b
```

La capa gratuita de Groq está sujeta a cuotas y condiciones del proveedor; no
se presenta como uso ilimitado garantizado. El alojamiento de CotizaT y su base
de datos también pueden tener costes independientes del asistente.

## 11. Seguridad

- Todos los endpoints de IA utilizan `get_authenticated_db`.
- Las consultas heredan el filtro obligatorio de `organizacion_id`.
- Los roles de solo lectura siguen protegidos al intentar guardar.
- El navegador no recibe credenciales de Groq.
- El Markdown se convierte con DOM seguro; no se inyecta HTML de respuestas.
- Los datos editables del catálogo se limpian antes de incorporarse al
  Markdown.
- IDs y precios sugeridos proceden de consultas verificadas.
- El asistente no confirma escrituras destructivas ni guarda el presupuesto por
  sí solo.

## 12. Operación y diagnóstico

Estado del asistente:

```text
GET /api/ia/estado
```

Campos relevantes:

- `configurado`: existe una clave de Groq;
- `herramientas_locales_sin_consumo`: siempre `true`;
- `generacion_sujeta_a_cuotas_proveedor`: siempre `true`;
- `modelo`: modelo generativo configurado.

Cuando no existe Groq, la interfaz muestra `Catálogo local activo` y conserva
todas las herramientas deterministas.

## 13. Pruebas

Cobertura principal:

- `tests/test_asistente_ia.py`
- `tests/test_copiloto_presupuesto.py`
- `tests/test_revision_presupuesto.py`

Verificación recomendada:

```bash
pytest -q
python tools/verificar_plantillas.py
python -m compileall -q app tools run.py desktop.py
find app/static/js -name '*.js' -exec node --check {} \;
```

La implementación se validó con la suite completa y comprobaciones de sintaxis
de Python, JavaScript y plantillas Jinja.

## 14. Extensión

Para añadir una herramienta nueva:

1. Implementar la lógica determinista en un servicio de dominio.
2. Añadir un detector de intención preciso en `herramientas_ia.py`.
3. Devolver resultados verificables y no texto inventado.
4. Si modifica el borrador, usar una acción declarativa con confirmación.
5. Revalidar IDs, tenant y permisos en servidor.
6. Añadir pruebas de éxito, ausencia de resultados y aislamiento.
7. Documentar límites y procedencia de los datos.

Las reglas de alcance deben crecer de forma conservadora: una sugerencia útil y
explicable es preferible a una lista extensa de falsos positivos.
