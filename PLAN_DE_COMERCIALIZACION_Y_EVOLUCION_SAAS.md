# Plan de comercialización y evolución a SaaS

**Producto:** CotizaT — presupuestos y control comercial para construcción y remodelación
**Mercado inicial:** empresas pequeñas de remodelación y construcción privada en Venezuela  
**Zona inicial recomendada:** Valencia / Carabobo, con posterior expansión a Caracas y otras ciudades  
**Fecha de creación:** 13 de agosto de 2026  
**Última actualización:** 13 de agosto de 2026  
**Estado general:** Etapa 0 completada · Etapa 1 activa
**Etapa activa:** Etapa 1 — Preparación de la versión comercial local

---

## 1. Propósito de este documento

Este documento es la guía principal para convertir la aplicación privada actual en un producto comercial validado y, únicamente si el mercado responde, en un SaaS seguro y sostenible.

Sus objetivos son:

1. Evitar seguir agregando funciones sin validación comercial.
2. Mantener un orden claro de ejecución.
3. Registrar qué está pendiente, en curso, completado, bloqueado o descartado.
4. Exigir criterios objetivos antes de pasar a la siguiente etapa.
5. Conservar las decisiones comerciales, técnicas y legales importantes.
6. Diferenciar entre «software que funciona» y «producto que se puede vender y operar».

Este plan complementa, pero no reemplaza, los documentos técnicos existentes:

- `HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md`
- `ANALISIS_PRODUCTO_Y_VIABILIDAD.md`
- `docs/FASE_0_AUDITORIA_Y_DISENO.md`

La hoja técnica explica lo que se ha construido. Este documento controla el camino comercial futuro.

---

## 2. Cómo mantener este plan

### 2.1 Estados

| Marca | Estado | Uso |
|---|---|---|
| `[ ]` | Pendiente | No se ha comenzado. |
| `[~]` | En curso | Se está trabajando activamente. |
| `[x]` | Completado | Cumple su definición de terminado y tiene evidencia. |
| `[!]` | Bloqueado | No puede continuar; debe documentarse el motivo. |
| `[-]` | Descartado | Se decidió no hacerlo; debe registrarse la decisión. |

> GitHub interpreta de forma visual `[ ]` y `[x]`. Los estados `[~]`, `[!]` y `[-]` son convenciones propias de este proyecto.

### 2.2 Regla de actualización

Al trabajar en una tarea de este plan se debe:

1. Cambiar su estado.
2. Actualizar la fecha de «Última actualización».
3. Añadir evidencia cuando se complete: archivo, prueba, captura, documento, entrevista o commit.
4. Registrar decisiones que cambien alcance, precio, cliente objetivo o arquitectura.
5. No marcar una etapa como completada hasta cumplir sus criterios de salida.

### 2.3 Regla de enfoque

- Solo debe existir **una etapa principal activa**.
- Se permiten tareas preparatorias de la etapa siguiente únicamente cuando desbloqueen la etapa activa.
- No se construirán funciones de etapas avanzadas para evitar tareas comerciales incómodas de la etapa actual.
- Cada etapa tiene una puerta de decisión: **avanzar, repetir, ajustar o detener**.

---

## 3. Resumen ejecutivo de etapas

| Etapa | Objetivo | Estado | Condición principal para avanzar |
|---|---|---|---|
| 0. Diagnóstico y límites | Conocer el estado real y fijar principios | **Completada** | Auditoría y decisión de nicho documentadas |
| 1. Versión comercial local | Poder entregar e instalar un producto honesto, estable y entendible | **Activa** | Producto instalable probado fuera del equipo de desarrollo |
| 2. Validación comercial pagada | Demostrar que empresas reales pagan y continúan usándolo | Pendiente | 5 pilotos pagados y señales de uso repetido |
| 3. Piloto web de instancia individual | Validar acceso web y cobro recurrente sin riesgo multiempresa | Pendiente | 10 clientes de pago y operación estable |
| 4. SaaS multiempresa | Construir una plataforma segura, escalable y operable | Pendiente | Beta de aislamiento y seguridad aprobada |
| 5. Retención y profundidad | Convertirlo en una herramienta de uso frecuente durante la obra | Pendiente | Uso recurrente y reducción de abandono |
| 6. Expansión controlada | Crecer por gremios y países sin perder el foco vertical | Pendiente | Mercado inicial repetible y rentable |

---

# ETAPA 0 — Diagnóstico, alcance y límites

**Estado:** COMPLETADA  
**Objetivo:** comprobar qué existe, qué falta y cuál es el mercado inicial razonable.

## 0.1 Verificaciones realizadas

- [x] **E0-001 — Inventariar la arquitectura actual.**  
  Evidencia: FastAPI + Jinja2 + SQLAlchemy + SQLite + ReportLab + JavaScript modular; aplicación empaquetable para Windows.

- [x] **E0-002 — Ejecutar la suite automatizada.**  
  Evidencia actualizada: 68 pruebas superadas con `PYTHONPATH=. .venv/bin/pytest -q` el 13/08/2026.

- [x] **E0-003 — Verificar el arranque y las rutas principales.**  
  Evidencia: las pantallas principales y la generación de PDF respondieron correctamente en una base limpia.

- [x] **E0-004 — Medir el contenido inicial de una instalación nueva.**  
  Evidencia: 58 partidas, 3 productos, 6 packs de estancia, 0 recursos y 1 presupuesto de demostración.

- [x] **E0-005 — Revisar la preparación actual para SaaS.**  
  Resultado: no existen autenticación, usuarios, roles, organizaciones, aislamiento multiempresa, CSRF, cobro recurrente ni operación cloud.

- [x] **E0-006 — Definir el nicho inicial.**  
  Decisión: construcción y remodelación privada, comenzando por empresas pequeñas de remodelación residencial/comercial en Venezuela.

- [x] **E0-007 — Identificar la ventaja competitiva principal.**  
  Resultado: flujo adaptado a remodelación, presentación comercial, PDF profesional, productos con fotografías, mediciones, cambios de alcance, lenguaje venezolano y catálogo propio.

## 0.2 Decisiones de alcance ya adoptadas

- [x] Mantener el producto especializado en construcción y remodelación.
- [x] No convertirlo en un generador genérico para cualquier sector.
- [x] Mantener un modo básico simple y ocultar capacidades avanzadas cuando no sean necesarias.
- [x] No publicar la versión actual directamente en internet.
- [x] No reescribir la interfaz con React u otro framework sin una necesidad validada.
- [x] No llamar «IA» a funciones deterministas basadas en coincidencias del catálogo.
- [x] No presentar la factura actual como factura fiscal homologada.
- [x] Exigir validación pagada antes de invertir en un SaaS multiempresa completo.

## 0.3 Criterio de salida

- [x] Estado técnico conocido.
- [x] Riesgos críticos identificados.
- [x] Mercado y cliente inicial definidos.
- [x] Etapas futuras documentadas.

**Resultado de la puerta:** avanzar a Etapa 1.

---

# ETAPA 1 — Preparación de la versión comercial local

**Estado:** ACTIVA — identidad comercial aplicada; experiencia de primer inicio pendiente
**Objetivo:** transformar la aplicación privada en un producto instalable, honesto, estable y comprensible que pueda entregarse a los primeros clientes.  
**Estimación orientativa:** 4–6 semanas, ajustable después del inventario inicial.  
**Restricción:** no añadir grandes módulos funcionales durante esta etapa.

## 1.1 Identidad, alcance y presentación

- [x] **E1-001 — Elegir el nombre comercial del software.**
  Decisión aprobada por el usuario el 13/08/2026: **CotizaT**. Se eligió por su comprensión inmediata para el mercado venezolano y su relación directa con el trabajo principal. La decisión comercial no equivale a autorización registral; el riesgo de diferenciación queda controlado en E1-002.

- [~] **E1-002 — Comprobar dominio, redes y conflictos básicos de marca.**
  Evidencia acumulada (13/08/2026): no apareció una empresa exacta claramente indexada como «CotizaT» en búsquedas generales ni en Instagram, LinkedIn, TikTok o X. `cotizat.app` devolvió RDAP 404 y ninguna raíz `cotizat` resolvió por DNS en `.com`, `.app`, `.io`, `.co`, `.net` o `.software`; esto **no equivale a disponibilidad ni reserva**. El riesgo comercial sigue siendo alto por competidores directos o próximos: **Cotiza** (`getcotiza.com`), **CotiZa** (app para contratistas), Cotiza Pro, CotizApp, Cotiza Constructor, Kotiza y la página colombiana «Cotízate». WIPO y SENAPI no dieron un resultado público concluyente. Pendiente: consultar registrador, reservar los activos disponibles y obtener una revisión marcaria profesional antes del lanzamiento. **PresupuestaT queda descartado** por longitud, pronunciación y proximidad con PresupuestAPP.

- [x] **E1-003 — Definir una propuesta de valor de una frase.**
  Propuesta aplicada: «Convierte tu catálogo y tus precios en presupuestos de obra claros, editables y listos para presentar». Describe funciones existentes y evita prometer ahorro o resultados financieros no demostrados. Evidencia: `app/branding.py`, dashboard y `README.md`.

- [x] **E1-004 — Sustituir “Presupuestos Pro” y nombres genéricos por la marca elegida.**
  Evidencia: interfaz, título FastAPI, ventana de escritorio, icono provisional, ejecutable PyInstaller, instalador Inno Setup, lanzadores y documentación muestran CotizaT.

- [x] **E1-005 — Eliminar los datos predeterminados de RemodelaT.**
  Evidencia: la configuración nueva usa campos de contacto vacíos, la demo quedó anonimizada, se retiró el PDF real versionado y se eliminó el script histórico que contenía los datos privados. La actualización nunca sobrescribe una configuración ya personalizada.

- [x] **E1-006 — Eliminar o renombrar afirmaciones que no corresponden a la función real.**
  Evidencia: «Autogenerar con IA» pasó a «Sugerir desde catálogo» y explica el matching determinista local; «Gemelos Digitales 3D» pasó a «Proyectos».

- [~] **E1-007 — Revisar todo el texto visible al usuario.**
  Primera revisión completada para marca, generador por catálogo, proyectos, instalador y alcance fiscal. Pendiente una revisión integral de microcopy durante el trabajo de onboarding y pruebas de usabilidad.

## 1.2 Primer inicio y experiencia básica

- [ ] **E1-008 — Diseñar el recorrido ideal del primer presupuesto.**  
  Meta: empresa → cliente → pack/capítulo → cantidades/precios → PDF en menos de 20 minutos.

- [ ] **E1-009 — Crear asistente de primer inicio.**  
  Datos mínimos: nombre comercial, razón social, RIF, teléfono, email, moneda, IVA, logo y ubicación.

- [ ] **E1-010 — Permitir elegir entre datos de demostración o instalación limpia.**

- [ ] **E1-011 — Crear una lista de inicio o panel de bienvenida.**  
  Ejemplo: configurar empresa, crear cliente, revisar catálogo, crear primer presupuesto, descargar PDF.

- [ ] **E1-012 — Ejecutar pruebas de usabilidad con al menos 3 personas ajenas al desarrollo.**  
  No se les debe explicar cada paso; se observarán bloqueos y preguntas.

- [ ] **E1-013 — Medir el tiempo real hasta el primer PDF.**

- [ ] **E1-014 — Simplificar el recorrido básico según los resultados.**

## 1.3 Honestidad funcional y límites legales

- [x] **E1-015 — Renombrar la factura actual como documento no fiscal cuando corresponda.**
  Decisión aplicada: «Documento de cobro» en interfaz y PDF; los identificadores internos y rutas históricas se conservan para no romper la base ni enlaces existentes. Los documentos nuevos usan prefijo `DC-`.

- [x] **E1-016 — Añadir aviso visible de alcance fiscal.**
  Evidencia: detalle HTML y PDF indican «Documento comercial no fiscal. No sustituye una factura fiscal emitida conforme a la normativa aplicable».

- [ ] **E1-017 — Consultar a un profesional tributario venezolano.**  
  Entregable: nota escrita sobre presupuesto, proforma, factura, IVA, número de control y retenciones.

- [ ] **E1-018 — Preparar EULA o contrato de licencia comercial.**

- [ ] **E1-019 — Preparar política de privacidad básica y condiciones de soporte.**

- [ ] **E1-020 — Crear aviso de licencias de terceros.**  
  Revisar dependencias, fuentes Lato y obligaciones de redistribución en el instalador.

- [ ] **E1-021 — Mantener el repositorio privado y revisar que no contenga datos reales sensibles.**

## 1.4 Catálogo comercial inicial

- [ ] **E1-022 — Auditar la procedencia y derechos de las partidas que se pretenden vender.**  
  Clasificar cada fuente como propia, autorizada, pública, adquirida o no redistribuible.

- [ ] **E1-023 — Definir el esquema del catálogo maestro.**  
  Debe contemplar categoría, subcategoría, unidad, ciudad/región, moneda, fecha, fuente, nivel de acabado y estado de revisión.

- [ ] **E1-024 — Separar catálogo maestro, personalización de empresa y precio congelado.**  
  Las actualizaciones futuras no deben sobrescribir silenciosamente el precio del cliente ni presupuestos históricos.

- [ ] **E1-025 — Curar un catálogo inicial de 200–500 partidas de remodelación.**  
  Prioridad: demoliciones, baños, cocinas, pisos, pintura, electricidad, plomería, cielos rasos, carpintería e impermeabilización.

- [ ] **E1-026 — Normalizar unidades y vocabulario venezolano.**

- [ ] **E1-027 — Detectar y fusionar duplicados o sinónimos innecesarios.**

- [ ] **E1-028 — Marcar claramente todos los precios como referenciales.**

- [ ] **E1-029 — Añadir fecha y procedencia a cada precio de referencia.**

- [ ] **E1-030 — Crear un proceso documentado para actualizar el catálogo.**

- [ ] **E1-031 — Preparar packs iniciales de alto valor.**  
  Mínimos sugeridos: baño, cocina, pintura integral, cambio de pisos y adecuación comercial pequeña.

## 1.5 Seguridad y funcionamiento local

- [ ] **E1-032 — Cambiar el host local predeterminado de `0.0.0.0` a `127.0.0.1`.**

- [ ] **E1-033 — Revisar acciones destructivas locales.**  
  Borrados masivos, restauración de backup, ajustes de precios y eliminación de documentos deben exigir confirmación clara.

- [ ] **E1-034 — Sustituir capturas silenciosas de errores críticos por logging útil.**

- [ ] **E1-035 — Crear una página o paquete de diagnóstico para soporte.**  
  Sin incluir información sensible sin autorización del usuario.

- [ ] **E1-036 — Embeber o servir localmente las fuentes de la interfaz.**  
  Eliminar la dependencia actual de Google Fonts para el modo offline.

- [ ] **E1-037 — Bloquear dependencias a versiones reproducibles.**

- [ ] **E1-038 — Configurar GitHub Actions para ejecutar las pruebas.**

- [ ] **E1-039 — Hacer que `pytest` funcione sin depender de configurar manualmente `PYTHONPATH`.**

- [ ] **E1-040 — Añadir pruebas de los recorridos críticos.**  
  Instalación limpia, primer inicio, presupuesto, PDF, backup, restauración y actualización.

- [ ] **E1-041 — Revisar que las pruebas no modifiquen la base de datos personal del desarrollador.**

## 1.6 Instalador, actualización y recuperación

- [ ] **E1-042 — Generar un instalador comercial con marca y versión.**

- [ ] **E1-043 — Probar instalación limpia en Windows 10 y Windows 11.**

- [ ] **E1-044 — Probar actualización conservando base, imágenes y configuración.**

- [ ] **E1-045 — Probar desinstalación sin pérdida accidental de datos.**

- [ ] **E1-046 — Probar backup y restauración entre dos equipos.**

- [ ] **E1-047 — Definir formato de versiones y notas de lanzamiento.**  
  Recomendación: versionado semántico `MAYOR.MENOR.PARCHE`.

- [ ] **E1-048 — Definir un canal seguro para distribuir actualizaciones.**

- [ ] **E1-049 — Investigar firma de código para reducir alertas de SmartScreen.**

## 1.7 Documentación, demostración y soporte

- [ ] **E1-050 — Crear guía de inicio rápido.**  
  Máximo recomendado: 5–8 páginas.

- [ ] **E1-051 — Grabar vídeo de demostración de 5 minutos.**

- [ ] **E1-052 — Crear un presupuesto de muestra comercial sin datos personales reales.**

- [ ] **E1-053 — Crear preguntas frecuentes.**

- [ ] **E1-054 — Definir qué incluye y qué no incluye el soporte.**

- [ ] **E1-055 — Crear procedimiento para reportar errores con evidencia.**

- [ ] **E1-056 — Preparar una landing page sencilla.**  
  Debe mostrar problema, resultado, vídeo, PDF de ejemplo, público objetivo y llamada a solicitar demostración.

## 1.8 Hipótesis comercial inicial

- [ ] **E1-057 — Definir oferta de piloto fundador.**  
  Hipótesis inicial: configuración asistida + catálogo + soporte por 99 USD/año o 10–15 USD/mes.

- [ ] **E1-058 — Definir hipótesis de licencia de escritorio.**  
  Hipótesis inicial: 79–149 USD de pago único y renovación opcional de soporte/catálogo.

- [ ] **E1-059 — Definir métodos de cobro legales y operables.**  
  Considerar cobro trimestral/anual para reducir fricción administrativa.

- [ ] **E1-060 — Preparar recibo, contrato y registro interno de licencias.**

- [ ] **E1-061 — Definir proceso manual de activación para los primeros pilotos.**

## 1.9 Criterios de salida de la Etapa 1

No se marcará esta etapa como completada hasta cumplir todos los siguientes puntos:

- [x] La aplicación no muestra datos ni marca de RemodelaT a un cliente nuevo.
- [x] No existen promesas visibles de IA, 3D o facturación fiscal no implementadas.
- [ ] Un usuario nuevo puede generar su primer PDF en menos de 20 minutos con ayuda mínima.
- [ ] El catálogo comercial tiene procedencia revisada y precios fechados.
- [ ] El instalador funciona en al menos 3 equipos externos de Windows.
- [ ] Una actualización conserva todos los datos.
- [ ] Backup y restauración fueron probados entre equipos.
- [ ] Existe guía de inicio, vídeo, oferta, contrato y canal de soporte.
- [ ] CI ejecuta las pruebas y el recorrido crítico está cubierto.
- [ ] Tres usuarios externos completaron una prueba de usabilidad.

**Puerta al terminar:** entregar la versión a prospectos y comenzar la Etapa 2. No construir todavía el SaaS multiempresa.

---

# ETAPA 2 — Validación comercial pagada

**Estado:** PENDIENTE  
**Objetivo:** demostrar que el problema es suficientemente importante para que empresas reales paguen y usen el producto repetidamente.  
**Duración orientativa:** 30–60 días.

## 2.1 Cliente inicial

Perfil prioritario:

- Empresa de 2–15 trabajadores.
- Remodelación residencial o comercial privada.
- Al menos 3 presupuestos al mes.
- Presupuestos actuales en papel, Word o Excel.
- Envío habitual por WhatsApp.
- Obras de valor suficiente para que ahorrar horas o evitar una partida olvidada tenga impacto.

## 2.2 Entrevistas y observación

- [ ] **E2-001 — Crear guion de entrevista basado en comportamiento pasado.**
- [ ] **E2-002 — Crear lista de al menos 30 prospectos.**
- [ ] **E2-003 — Entrevistar a 15–20 empresas.**
- [ ] **E2-004 — Observar al menos 5 presupuestos reales anonimizados.**
- [ ] **E2-005 — Registrar tiempo actual, herramientas, errores y frecuencia.**
- [ ] **E2-006 — No usar “¿pagarías?” como única prueba; solicitar el pago.**

Preguntas mínimas:

1. ¿Cómo preparaste tu último presupuesto?
2. ¿Cuánto tiempo tardaste?
3. ¿Cuántos preparas al mes?
4. ¿Cómo actualizas materiales y mano de obra?
5. ¿Qué ocurre cuando cambia el alcance?
6. ¿Has perdido dinero por olvidar una partida o usar un precio antiguo?
7. ¿Qué documento recibe tu cliente?
8. ¿Qué te impediría utilizar esta herramienta mañana?

## 2.3 Pilotos pagados

- [ ] **E2-007 — Cerrar al menos 5 pilotos pagados.**
- [ ] **E2-008 — Configurar personalmente cada empresa.**
- [ ] **E2-009 — Importar o adaptar una parte de su catálogo real.**
- [ ] **E2-010 — Acompañar la creación del primer presupuesto.**
- [ ] **E2-011 — Registrar incidencias y dudas sin convertir todas en nuevas funciones.**
- [ ] **E2-012 — Hacer seguimiento semanal durante 8 semanas.**
- [ ] **E2-013 — Solicitar testimonios solo después de uso real.**

## 2.4 Métricas de validación

- [ ] Primer PDF en menos de 20 minutos.
- [ ] Al menos 5 empresas pagan.
- [ ] Al menos 4 siguen usando el producto después de 8 semanas.
- [ ] Cada empresa activa crea al menos 3 presupuestos durante el piloto.
- [ ] Reducción percibida o medida de al menos 50 % en tiempo de preparación.
- [ ] Al menos 2 clientes usan catálogo o packs repetidamente.
- [ ] Al menos 1 cliente atribuye valor concreto: ahorro de tiempo, prevención de pérdida o mejora de cierre.
- [ ] Se registra el número de solicitudes de soporte por cliente y semana.

## 2.5 Experimentos de precio

- [ ] **E2-014 — Probar oferta anual de fundador.**
- [ ] **E2-015 — Probar alternativa mensual o trimestral.**
- [ ] **E2-016 — Medir rechazo por precio frente a rechazo por producto.**
- [ ] **E2-017 — Medir disposición a pagar por catálogo actualizado.**
- [ ] **E2-018 — Medir disposición a pagar por acceso web y respaldo cloud.**

## 2.6 Criterios de salida de la Etapa 2

### Avanzar

- [ ] 5 o más pilotos pagados.
- [ ] 4 o más usuarios activos tras 8 semanas.
- [ ] Uso repetido, no solamente una demostración.
- [ ] Evidencia de valor económico o ahorro de tiempo.
- [ ] Demanda clara de acceso desde varios dispositivos o fuera de la oficina.

### Ajustar y repetir

Aplicar si hay interés y uso, pero el precio, onboarding o catálogo impiden convertir.

### Detener o mantener solo como producto interno

Considerar si, después de 15–20 entrevistas y una oferta concreta:

- Nadie paga.
- El problema ocurre con muy poca frecuencia.
- El soporte requerido supera ampliamente el ingreso posible.
- Los usuarios prefieren claramente Excel incluso después de una prueba acompañada.

**Puerta al terminar:** decidir entre mantener licencia local, iniciar piloto web individual o detener inversión comercial.

---

# ETAPA 3 — Piloto web de instancia individual

**Estado:** PENDIENTE  
**Prerrequisito:** Etapa 2 validada.  
**Objetivo:** comprobar que el acceso web, el backup remoto y la recurrencia aportan valor, sin introducir todavía el riesgo de una base multiempresa compartida.

Cada empresa tendrá inicialmente:

- Instancia separada.
- Base de datos separada.
- Archivos separados.
- Credenciales propias.
- Subdominio propio.
- Backups externos.

## 3.1 Fundamentos

- [ ] **E3-001 — Diseñar arquitectura de instancia individual.**
- [ ] **E3-002 — Añadir login de aplicación seguro.**
- [ ] **E3-003 — Implementar cierre de sesión y cambio de contraseña.**
- [ ] **E3-004 — Implementar recuperación de acceso administrada o por email.**
- [ ] **E3-005 — Configurar HTTPS obligatorio.**
- [ ] **E3-006 — Añadir protección CSRF.**
- [ ] **E3-007 — Añadir cookies seguras y cabeceras de seguridad.**
- [ ] **E3-008 — Añadir límites de carga y rate limiting básico.**

## 3.2 Datos y operación

- [ ] **E3-009 — Crear almacenamiento persistente y backup externo cifrado.**
- [ ] **E3-010 — Probar restauración completa de una instancia.**
- [ ] **E3-011 — Separar secretos y configuración del código.**
- [ ] **E3-012 — Añadir monitorización de disponibilidad y errores.**
- [ ] **E3-013 — Crear procedimiento de alta y baja de empresa.**
- [ ] **E3-014 — Crear exportación completa de datos del cliente.**
- [ ] **E3-015 — Definir tiempos de retención y eliminación.**

## 3.3 Funciones comerciales web prioritarias

- [ ] **E3-016 — Envío por email del presupuesto.**
- [ ] **E3-017 — Enlace público seguro y revocable para ver una propuesta.**
- [ ] **E3-018 — Aceptación del presupuesto con trazabilidad.**
- [ ] **E3-019 — Notificación de aceptación o rechazo.**
- [ ] **E3-020 — Registro de apertura cuando sea legal y se informe adecuadamente.**

## 3.4 Operación comercial

- [ ] **E3-021 — Cobro recurrente o renovación manual documentada.**
- [ ] **E3-022 — Controlar vencimiento, gracia y suspensión sin borrar datos.**
- [ ] **E3-023 — Definir SLA y horario de soporte.**
- [ ] **E3-024 — Medir coste de infraestructura y soporte por cliente.**

## 3.5 Criterios de salida de la Etapa 3

- [ ] 10 clientes de pago.
- [ ] Operación estable durante al menos 8 semanas.
- [ ] Restauración de backup probada.
- [ ] Cero incidentes de acceso entre empresas.
- [ ] Coste de soporte e infraestructura compatible con el precio.
- [ ] Evidencia de que los clientes valoran el acceso web.
- [ ] Demanda real de varios usuarios dentro de una misma empresa.

**Puerta al terminar:** mantener instancias individuales o invertir en SaaS multiempresa.

---

# ETAPA 4 — SaaS multiempresa

**Estado:** PENDIENTE  
**Prerrequisitos:** validación de pago, uso recurrente y demanda multiusuario.  
**Estimación orientativa:** 12–20 semanas a tiempo completo, más beta y endurecimiento.  
**Objetivo:** operar múltiples empresas de forma segura dentro de una plataforma administrable.

## 4.1 Refactorización estructural

- [ ] **E4-001 — Dividir `app/main.py` en routers por dominio.**
- [ ] **E4-002 — Extraer servicios de aplicación y reglas de autorización.**
- [ ] **E4-003 — Crear configuración separada por entorno.**
- [ ] **E4-004 — Introducir migraciones versionadas con Alembic.**
- [ ] **E4-005 — Mantener SQLite para escritorio y PostgreSQL para SaaS, si continúa el producto híbrido.**

## 4.2 Identidad y organizaciones

- [ ] **E4-006 — Crear modelo de Organización/Empresa.**
- [ ] **E4-007 — Crear usuarios, membresías e invitaciones.**
- [ ] **E4-008 — Definir roles mínimos: propietario, administrador, presupuestador y lectura.**
- [ ] **E4-009 — Implementar autorización centralizada.**
- [ ] **E4-010 — Implementar recuperación de contraseña y verificación de email.**
- [ ] **E4-011 — Evaluar segundo factor para administradores.**

## 4.3 Aislamiento multiempresa

- [ ] **E4-012 — Añadir `organizacion_id` o estrategia equivalente a todos los datos empresariales.**
- [ ] **E4-013 — Aplicar filtrado obligatorio en la capa de datos.**
- [ ] **E4-014 — Evitar depender de que cada ruta recuerde filtrar manualmente.**
- [ ] **E4-015 — Crear pruebas automáticas de aislamiento para cada dominio.**
- [ ] **E4-016 — Auditar acceso directo por identificadores.**
- [ ] **E4-017 — Auditar archivos y URLs firmadas.**

## 4.4 Infraestructura

- [ ] **E4-018 — PostgreSQL administrado.**
- [ ] **E4-019 — Almacenamiento de objetos para imágenes, PDFs y anexos.**
- [ ] **E4-020 — Cola de trabajos para PDFs, emails e importaciones pesadas.**
- [ ] **E4-021 — Backups automáticos y restauraciones ensayadas.**
- [ ] **E4-022 — Logs estructurados sin datos sensibles innecesarios.**
- [ ] **E4-023 — Monitorización, alertas y seguimiento de errores.**
- [ ] **E4-024 — Entornos separados de desarrollo, pruebas y producción.**
- [ ] **E4-025 — Despliegues repetibles y reversibles.**

## 4.5 Auditoría y seguridad

- [ ] **E4-026 — Registro de quién cambió precios, documentos y estados.**
- [ ] **E4-027 — Historial de sesiones y acciones sensibles.**
- [ ] **E4-028 — Política de contraseñas y bloqueo de intentos.**
- [ ] **E4-029 — CSRF, XSS, CSP, validación de archivos y rate limiting revisados.**
- [ ] **E4-030 — Escaneo de dependencias y secretos en CI.**
- [ ] **E4-031 — Auditoría externa o revisión independiente antes del lanzamiento público.**
- [ ] **E4-032 — Plan de respuesta a incidentes.**

## 4.6 Suscripciones y administración

- [ ] **E4-033 — Definir planes según valor, no por acumulación arbitraria de funciones.**
- [ ] **E4-034 — Integrar un medio de cobro legalmente disponible para la empresa operadora.**
- [ ] **E4-035 — Implementar prueba, alta, renovación, gracia, suspensión y cancelación.**
- [ ] **E4-036 — No eliminar automáticamente datos al fallar un pago.**
- [ ] **E4-037 — Crear panel interno de soporte y administración.**
- [ ] **E4-038 — Registrar consentimiento de términos y privacidad.**

## 4.7 Migración y beta

- [ ] **E4-039 — Diseñar importación desde la versión de escritorio.**
- [ ] **E4-040 — Probar migraciones con copias anonimizadas de bases reales.**
- [ ] **E4-041 — Ejecutar beta cerrada con 5–10 empresas.**
- [ ] **E4-042 — Realizar prueba de carga realista.**
- [ ] **E4-043 — Realizar simulacro de caída y recuperación.**

## 4.8 Criterios de salida de la Etapa 4

- [ ] Ninguna consulta o archivo puede cruzar organizaciones en las pruebas.
- [ ] Roles y permisos están cubiertos automáticamente.
- [ ] Backups y restauración cumplen el objetivo definido.
- [ ] Monitorización y respuesta a incidentes funcionan.
- [ ] Alta, pago, gracia, cancelación y exportación fueron probados.
- [ ] La beta cerrada fue estable y aprobada.
- [ ] Existe documentación legal y operativa.

**Puerta al terminar:** lanzamiento comercial controlado del SaaS.

---

# ETAPA 5 — Retención y profundidad en obra

**Estado:** PENDIENTE  
**Objetivo:** pasar de una herramienta que se abre al presupuestar a una herramienta que aporta valor durante toda la obra.

Prioridades sujetas a evidencia de clientes:

- [ ] **E5-001 — Coste presupuestado frente a coste real incurrido.**
- [ ] **E5-002 — Registro de compras y facturas de proveedores.**
- [ ] **E5-003 — Jornales y mano de obra real.**
- [ ] **E5-004 — Certificaciones o avances parciales.**
- [ ] **E5-005 — Facturación desde avances mediante integración fiscal válida o exportación a un sistema homologado.**
- [ ] **E5-006 — Portal del cliente con avance, fotos, pagos y cambios.**
- [ ] **E5-007 — Aprobación digital de cambios de alcance.**
- [ ] **E5-008 — Planificación sencilla por capítulos y dependencias.**
- [ ] **E5-009 — PWA/móvil para visitas y trabajo en obra.**
- [ ] **E5-010 — Modo offline selectivo, solo después de definir sincronización y conflictos.**
- [ ] **E5-011 — Actualización versionada de catálogos y precios.**
- [ ] **E5-012 — Telemetría mínima, agregada y voluntaria para conocer uso de funciones.**

## Métricas de esta etapa

- Retención a 3, 6 y 12 meses.
- Presupuestos creados por empresa y mes.
- Proyectos activos gestionados.
- Cambios de alcance aprobados.
- Tiempo hasta primer valor.
- Solicitudes de soporte por empresa.
- Ingreso mensual por cliente.
- Abandono y motivo de cancelación.

---

# ETAPA 6 — Expansión controlada

**Estado:** PENDIENTE  
**Objetivo:** crecer sin abandonar la especialización que diferencia al producto.

## 6.1 Gremios adyacentes

- [ ] Electricistas.
- [ ] Plomeros.
- [ ] Instaladores de aire acondicionado.
- [ ] Carpinteros y fabricantes de mobiliario.
- [ ] Herreros.
- [ ] Pintores.
- [ ] Impermeabilizadores.

La expansión debe realizarse principalmente mediante catálogos, packs y lenguaje especializado, no mediante productos de software independientes.

## 6.2 Otros países

- [ ] Investigar un segundo país solo después de consolidar Venezuela.
- [ ] Priorizar inicialmente mercados dolarizados o con problemas similares.
- [ ] Separar reglas fiscales, moneda, vocabulario y catálogo por país.
- [ ] Consultar especialistas fiscales locales antes de anunciar facturación.
- [ ] Ejecutar una validación comercial nueva; no asumir que Venezuela se replica automáticamente.

## 6.3 Límites

- [ ] No perseguir sectores genéricos como eventos, agencias, medicina o comercio minorista.
- [ ] No añadir una función para otro sector por una única venta aislada.
- [ ] Sí se puede vender la herramienta existente a otro sector si no exige desviar el producto.

---

# 7. Registro de riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación principal | Estado |
|---|---|---:|---:|---|---|
| R-001 | Los elogios no se convierten en pagos | Alta | Alta | Pilotos pagados antes del SaaS | Abierto |
| R-002 | El producto abruma al usuario de papel/Excel | Alta | Alta | Onboarding y pruebas observadas | Abierto |
| R-003 | Partidas sin derechos de redistribución | Media | Crítico | Auditoría de procedencia | Abierto |
| R-004 | Precios desactualizados causan pérdidas | Alta | Crítico | Fecha, fuente, región y aviso referencial | Abierto |
| R-005 | Confusión entre documento de cobro y factura fiscal | Media | Crítico | Aviso no fiscal aplicado; consultar especialista | Mitigado parcialmente |
| R-006 | Fuga de datos entre empresas | Alta en la arquitectura actual | Crítico | No publicar; aislamiento y pruebas | Abierto |
| R-007 | Precio demasiado bajo frente al soporte | Alta | Alta | Medir soporte y cobrar onboarding/anualidad | Abierto |
| R-008 | Dificultad para cobrar recurrencia en Venezuela | Alta | Alta | Métodos legales alternativos y cobro trimestral/anual | Abierto |
| R-009 | Dependencia de una sola persona | Alta | Alta | Documentación, tests, logs y procesos | Abierto |
| R-010 | Seguir agregando funciones sin mercado | Alta | Alta | Puertas de decisión por etapa | Abierto |
| R-011 | Pérdida o corrupción de datos | Media | Crítico | Backups probados y recuperación | Abierto |
| R-012 | Instalador bloqueado por SmartScreen/antivirus | Media | Alta | Firma de código y pruebas externas | Abierto |
| R-013 | CotizaT se confunde o colisiona con marcas del territorio «Cotiza» | Alta | Alta | Revisión profesional, registro urgente y validación oral antes del lanzamiento | Abierto |

---

# 8. Registro de hipótesis comerciales

Estas cifras no son precios definitivos; deben probarse en la Etapa 2.

| Hipótesis | Valor inicial | Estado |
|---|---:|---|
| Piloto fundador anual | 99 USD/año | Sin validar |
| Piloto mensual | 10–15 USD/mes | Sin validar |
| Licencia local perpetua | 79–149 USD | Sin validar |
| Renovación de soporte/catálogo | 30–60 USD/año | Sin validar |
| Futuro plan web profesional | 19–29 USD/mes | Sin validar |
| Tiempo máximo al primer PDF | 20 minutos | Sin validar externamente |
| Reducción esperada de tiempo | 50 % | Sin validar |

---

# 9. Registro de decisiones

| Fecha | ID | Decisión | Motivo | Revisión futura |
|---|---|---|---|---|
| 13/08/2026 | D-001 | Mantener foco en construcción y remodelación | Es donde existe conocimiento, código y catálogo diferencial | Tras validar Venezuela |
| 13/08/2026 | D-002 | Comenzar por empresas pequeñas de remodelación privada | Ciclo de venta más corto y mejor encaje con el PDF comercial | Después de 20 entrevistas |
| 13/08/2026 | D-003 | Preparar primero una versión comercial local | Menor coste y riesgo que un SaaS completo | Al cerrar Etapa 2 |
| 13/08/2026 | D-004 | No publicar la aplicación actual en internet | No existen autenticación ni aislamiento | Etapa 3 |
| 13/08/2026 | D-005 | No presentar funciones deterministas como IA | Proteger credibilidad | Si se integra IA real |
| 13/08/2026 | D-006 | No presentar la factura actual como fiscal | No existe homologación/integración demostrada | Tras consulta tributaria |
| 13/08/2026 | D-007 | No reescribir el frontend por moda | El stack actual permite validar el producto | Si aparecen límites medidos |
| 13/08/2026 | D-008 | Exigir pilotos pagados antes del multi-tenant | Reducir riesgo de construir sin demanda | Puerta Etapa 2 |
| 13/08/2026 | D-009 | Crear una marca para construcción latinoamericana, especializada inicialmente en remodelación venezolana | Permite crecer por país y función sin diluir el mensaje comercial de entrada | Tras la selección final de nombre |
| 13/08/2026 | D-010 | Adoptar **CotizaT** como nombre comercial | El usuario priorizó comprensión inmediata y aprobó expresamente el nombre | Tras revisión marcaria profesional |
| 13/08/2026 | D-011 | Usar la propuesta «Convierte tu catálogo y tus precios en presupuestos de obra claros, editables y listos para presentar» | Es verificable con el producto actual y no promete resultados financieros | Después de pruebas comerciales |
| 13/08/2026 | D-012 | Renombrar ejecutable e instalador, manteniendo compatibilidad automática con la carpeta histórica de datos | Aplicar la marca sin hacer desaparecer bases, imágenes ni backups existentes | Después de probar actualización en Windows |

---

# 10. Registro de evidencia comercial

Se completará durante la Etapa 2. No deben guardarse aquí nombres, teléfonos ni datos sensibles sin autorización.

| Fecha | Tipo | Segmento | Hallazgo | Evidencia anonimizada | Acción |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

# 11. Próximo bloque de trabajo

## Etapa 1 activa — siguiente bloque: primer inicio y recorrido básico

La entrega de identidad y honestidad quedó aplicada en código. El siguiente trabajo, en este orden, es:

1. **E1-002:** completar reserva de activos y revisión marcaria profesional de CotizaT; el riesgo no se considera cerrado por ausencia DNS o RDAP.
2. **E1-008:** definir el recorrido ideal empresa → cliente → catálogo/pack → presupuesto → PDF.
3. **E1-009 a E1-011:** crear asistente de primer inicio, elección demo/limpio y lista de bienvenida.
4. **E1-007:** terminar la revisión integral de microcopy dentro del nuevo onboarding.
5. **E1-012 a E1-014:** probar el recorrido con usuarios ajenos, medir el primer PDF y simplificar con evidencia.
6. **E1-042 a E1-045:** compilar y probar en Windows la actualización de marca, la conservación de datos y el instalador en equipos externos antes de cerrar la entrega comercial.

Evidencia de la entrega de identidad (13/08/2026):

- Marca, descriptor y propuesta centralizados en `app/branding.py`.
- Configuración y demo sin datos personales reales en `app/models.py` y `app/seeds.py`.
- Claims de IA/3D sustituidos por nombres que describen la función real.
- «Factura» visible sustituida por «Documento de cobro» con aviso no fiscal.
- Ejecutable e instalador renombrados como CotizaT.
- Migración no destructiva: una instalación nueva usa `%LOCALAPPDATA%\CotizaT`; una actualización sigue usando `%LOCALAPPDATA%\Presupuestos` si allí encuentra datos previos. Los aliases técnicos anteriores continúan aceptándose.
- El PDF real versionado y el script histórico con datos privados fueron retirados del árbol actual.
- Pruebas de regresión de branding, privacidad, alcance fiscal y compatibilidad añadidas en `tests/test_branding.py`; suite completa: **68 aprobadas**.

---

## Declaración final de enfoque

El objetivo inmediato no es construir la mayor cantidad posible de funciones. El objetivo es comprobar que una empresa venezolana de remodelación puede:

1. Entender el producto.
2. Crear un presupuesto profesional rápidamente.
3. Confiar en sus datos y cálculos.
4. Mantener sus precios y documentos seguros.
5. Obtener suficiente valor como para pagar y seguir utilizándolo.

Solo cuando esto esté demostrado se justificará convertir la aplicación en un SaaS multiempresa completo.
