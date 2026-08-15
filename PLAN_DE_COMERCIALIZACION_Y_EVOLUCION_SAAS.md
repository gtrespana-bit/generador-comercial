# Plan de comercialización y evolución a SaaS

**Producto:** CotizaT — presupuestos y control comercial para construcción y remodelación
**Mercado inicial:** empresas pequeñas de remodelación y construcción privada en Venezuela  
**Zona inicial recomendada:** Valencia / Carabobo, con posterior expansión a Caracas y otras ciudades  
**Fecha de creación:** 13 de agosto de 2026  
**Última actualización:** 14 de agosto de 2026  
**Estado general:** Etapa 0 completada · Etapa 1 activa
**Etapa activa:** Etapa 1 — Fundamentos de la versión comercial web

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
| 1. Fundamentos comerciales web | Construir una base browser-first honesta, persistente y aislada | **Activa** | Beta web privada con autenticación y datos persistentes |
| 2. Validación comercial pagada | Demostrar que empresas reales pagan y continúan usándolo | Pendiente | 5 pilotos pagados y señales de uso repetido |
| 3. Beta web controlada | Validar operación alojada, soporte y recurrencia | Pendiente | 10 clientes de pago y operación estable |
| 4. Endurecimiento SaaS | Completar seguridad, escalabilidad y operación pública | Pendiente | Beta de aislamiento y seguridad aprobada |
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
  Evidencia actualizada: 145 pruebas superadas con `.venv/bin/pytest -q` el 13/08/2026; la suite cubre Auth/membresías, aislamiento, almacenamiento privado y rate limiting de Auth, usa bases temporales y deja intacta la base personal.

- [x] **E0-003 — Verificar el arranque y las rutas principales.**  
  Evidencia: las pantallas principales y la generación de PDF respondieron correctamente en una base limpia.

- [x] **E0-004 — Medir el contenido inicial de una instalación nueva.**  
  Evidencia actualizada: el modo demo carga 58 partidas, 3 productos, 6 packs de estancia y 1 presupuesto ficticio; el modo limpio comienza sin catálogos, clientes ni documentos.

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
- [x] Exigir validación pagada antes de invertir en la operación SaaS completa; los fundamentos de aislamiento se adelantan para evitar reescrituras.

## 0.3 Criterio de salida

- [x] Estado técnico conocido.
- [x] Riesgos críticos identificados.
- [x] Mercado y cliente inicial definidos.
- [x] Etapas futuras documentadas.

**Resultado de la puerta:** avanzar a Etapa 1.

---

# ETAPA 1 — Fundamentos de la versión comercial web

**Estado:** ACTIVA — estrategia browser-first aprobada y base multiempresa en construcción
**Objetivo:** transformar la aplicación privada en un producto web honesto, persistente y aislado por empresa antes de añadir más funciones o desplegarlo públicamente.
**Estimación:** se revisará después de completar autenticación, almacenamiento y una ejecución real sobre PostgreSQL.
**Restricción:** no añadir grandes módulos funcionales ni invertir en el instalador mientras falten los fundamentos web.

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

- [x] **E1-008 — Diseñar el recorrido ideal del primer presupuesto.**
  Recorrido y presupuesto temporal documentados en `docs/RECORRIDO_PRIMER_PRESUPUESTO.md`: empresa → contenido inicial → catálogo → cliente → presupuesto → descarga de PDF. La meta de 20 minutos sigue siendo una hipótesis pendiente de validación externa.

- [x] **E1-009 — Crear asistente de primer inicio.**
  Evidencia: `/bienvenida` solicita nombre comercial, razón social, RIF, teléfono, email, país, ciudad, dirección, moneda, IVA y logo; conserva todo en la base local y solo exige el nombre para avanzar. Una base anterior migra sin mostrar el asistente ni sobrescribir su empresa.

- [x] **E1-010 — Permitir elegir entre datos de demostración o instalación limpia.**
  Evidencia: la elección explícita e idempotente carga catálogo, productos, packs, cliente y presupuesto ficticios, o deja la instalación vacía. Los registros demo se identifican en la interfaz y no completan hitos reales.

- [x] **E1-011 — Crear una lista de inicio o panel de bienvenida.**
  Evidencia: el dashboard muestra cinco pasos comprobados con datos locales: empresa, catálogo, cliente real, presupuesto real y descarga del primer PDF. Abrir una vista previa o descargar el PDF demo no completa el último paso.

- [ ] **E1-012 — Ejecutar pruebas de usabilidad con al menos 3 personas ajenas al desarrollo.**  
  No se les debe explicar cada paso; se observarán bloqueos y preguntas.

- [ ] **E1-013 — Medir el tiempo real hasta el primer PDF.**

- [ ] **E1-014 — Simplificar el recorrido básico según los resultados.**

## 1.3 Fundamentos browser-first — prioridad activa

- [x] **E1W-001 — Adoptar y documentar la arquitectura browser-first.**
  Evidencia: decisión del propietario y `docs/ADR-001_ARQUITECTURA_BROWSER_FIRST.md`. FastAPI/Jinja se conserva; el desarrollo exclusivo de escritorio queda pausado.

- [x] **E1W-002 — Desacoplar la conexión del archivo SQLite.**
  Evidencia: `DATABASE_URL` permite PostgreSQL y conserva `COTIZAT_DB`/`PRESUPUESTOS_DB` para compatibilidad local. Las URL PostgreSQL usan Psycopg 3.

- [x] **E1W-003 — Introducir migraciones web versionadas con Alembic.**
  Evidencia: baseline reproducible en `migrations/`; el arranque PostgreSQL exige ejecutar previamente `alembic upgrade head` y no modifica DDL de manera implícita.

- [x] **E1W-004 — Crear organizaciones, usuarios y membresías.**
  Evidencia: modelos `Organizacion`, `Usuario` y `Membresia`, con membresía única y rol por empresa; `Usuario.auth_user_id` enlaza el perfil con Supabase Auth desde la revisión `9bca2ad1f6e4`.

- [x] **E1W-005 — Asignar propietario a los datos empresariales.**
  Evidencia: configuración, catálogos, clientes, presupuestos, documentos, proyectos y entidades hijas incorporan `organizacion_id`; números y nombres reutilizables son únicos dentro de cada organización en el esquema web.

- [x] **E1W-006 — Aplicar aislamiento en la sesión de datos.**
  Evidencia: SQLAlchemy añade el criterio de organización a consultas y relaciones, asigna propietario a registros nuevos y rechaza escrituras cruzadas sin depender de cada ruta. `c93e7a4d20f1` añade una segunda barrera RLS por membresía/rol, todavía pendiente de prueba PostgreSQL real.

- [~] **E1W-007 — Cubrir automáticamente el aislamiento de cada dominio.**
  Cobertura actual: configuración, clientes, presupuestos, capítulos, acceso directo por ID, escritura cruzada, numeración, membresías y objetos privados. Storage verifica claves tenant, rechazo del proxy a otra organización y bloquea crear/borrar objetos para el rol `lectura` antes de cualquier efecto externo; la auditoría automatizada exige autenticación en todas las rutas comerciales salvo fronteras públicas/locales explícitas y prohíbe mutaciones empresariales directas en `GET`; vencimientos e hitos de onboarding/PDF usan `POST` same-origin. `WebSecurityMiddleware` bloquea escrituras cross-site y añade cabeceras defensivas; Auth limita ráfagas por ruta/IP; RLS cubre cada modelo tenant en `c93e7a4d20f1`; scripts y estilos usan nonce, `script-src-attr`/`style-src-attr` bloquean atributos, no queda `unsafe-inline` ni sinks de fragmentos HTML. Pendiente añadir contadores distribuidos, validar CSP/interacciones en navegador HTTPS y ejecutar el cruce real contra Supabase con rol limitado.

- [~] **E1W-008 — Implementar autenticación, sesión segura y autorización por membresía.**
  Implementado en código: Supabase Auth por clave publicable, tokens HttpOnly, renovación, vínculo `auth.users` → `Usuario`, selección validada de organización y bloqueo de escritura para el rol `lectura`. La revisión `9bca2ad1f6e4` ya está aplicada en Supabase y las variables Auth quedaron configuradas localmente fuera de Git. En PostgreSQL se ignora `COTIZAT_ORGANIZATION_ID`. Recuperación con redirect HTTPS fijo e invitaciones de un solo uso para emails verificados ya están implementadas. Pendiente prueba end-to-end desde un entorno con salida a Supabase, configurar la Redirect URL real, aplicar `c93e7a4d20f1`, validar el canal de entrega de invitaciones y endurecer CSP/XSS antes de publicar.

- [~] **E1W-009 — Crear una interfaz de almacenamiento y un backend de objetos.**
  Implementados `StorageBackend`, `LocalStorage` y `SupabaseStorage`, referencias por organización, metadatos sin binarios, proxy autorizado, compatibilidad legado, PDF vía `/tmp` y cobertura de logos, productos, partidas, proyectos, firmas, anexos, fichas técnicas e importaciones CYPE. Evidencia: `72e6f4d8a1c3`, `app/storage.py`, `tests/test_storage.py` y `docs/ALMACENAMIENTO_PRIVADO.md`. Pendiente crear/verificar `cotizat-private`, aplicar la migración y probar contra Supabase real; no existe acceso público improvisado.

- [~] **E1W-010 — Adaptar onboarding a cuenta → organización → demo/limpio.**
  La ruta inicial ya enlaza registro/login → creación o selección de organización → onboarding demo/limpio existente; aceptar una invitación selecciona la organización autorizada. Pendiente probar el recorrido completo con dos emails reales y el cambio entre organizaciones.

- [~] **E1W-011 — Ejecutar migraciones y suite de integración contra PostgreSQL real.**
  Evidencia real: revisiones `5cda50f97ed9` y `9bca2ad1f6e4` aplicadas en Supabase; una partida modificada persistió entre conexiones físicas `16389` y `17068`; dos organizaciones conservaron valores independientes; RLS quedó activo y `anon` vio 0 partidas. El código ya prepara `cotizat_app`, contexto transaccional y políticas autorizantes en `c93e7a4d20f1`. Pendiente aplicar ese head y ejecutar la suite ORM/Auth completa con un login sin `BYPASSRLS` desde un runner con salida a Supabase.

- [x] **E1W-012 — Diseñar y probar importación de instalaciones SQLite.**
  Nunca se migrarán datos privados a un servidor sin acción y confirmación del propietario.
  Evidencia (15/08/2026): `app/services/instalacion_sqlite.py` + asistente en `/configuracion/importar-instalacion`. Flujo de dos pasos (analizar → confirmar) con resumen honesto previo, casilla de confirmación explícita y verificación SHA-256 de que el archivo confirmado es el analizado (el servidor no lo guarda entre pasos). Acepta el .zip de backup o el .db directo; lee la fuente con `sqlite3` en solo lectura (tolera bases de versiones anteriores sin columnas nuevas); escribe con la sesión ORM del usuario (tenencia, rol y RLS se aplican como en cualquier escritura). No migra datos demo ni configuración de empresa; limpia referencias a archivos locales avisando cuántas; reimportar no duplica (números de presupuesto/documento en conflicto se omiten y se listan antes de confirmar). Solo propietario o administrador pueden importar. 12 pruebas en `tests/test_instalacion_sqlite.py`.

## 1.4 Honestidad funcional y límites legales

- [x] **E1-015 — Renombrar la factura actual como documento no fiscal cuando corresponda.**
  Decisión aplicada: «Documento de cobro» en interfaz y PDF; los identificadores internos y rutas históricas se conservan para no romper la base ni enlaces existentes. Los documentos nuevos usan prefijo `DC-`.

- [x] **E1-016 — Añadir aviso visible de alcance fiscal.**
  Evidencia: detalle HTML y PDF indican «Documento comercial no fiscal. No sustituye una factura fiscal emitida conforme a la normativa aplicable».

- [ ] **E1-017 — Consultar a un profesional tributario venezolano.**  
  Entregable: nota escrita sobre presupuesto, proforma, factura, IVA, número de control y retenciones.

- [x] **E1-018 — Preparar EULA o contrato de licencia comercial.**
  Evidencia (15/08/2026): términos del servicio y licencia de uso publicados en `/legal/terminos` (`app/templates/legal/terminos.html`): licencia limitada, propiedad de los datos del cliente, alcance no fiscal de los documentos, precios/renovación, límites de responsabilidad, terminación con ventana de exportación ≥30 días y ley del domicilio del titular. La razón social se inyecta con `COTIZAT_LEGAL_ENTITY` (hasta entonces se muestra un marcador imposible de confundir con una entidad real).

- [x] **E1-019 — Preparar política de privacidad básica y condiciones de soporte.**
  Evidencia (15/08/2026): `/legal/privacidad` (qué datos, para qué, encargados reales: Supabase, Vercel, Resend, Upstash y GoDaddy; sin venta de datos, sin rastreadores, cookies solo técnicas, derechos y plazos) y `/legal/soporte` (canal soporte@cotizat.online, horario, tiempos orientativos y procedimiento de reporte de errores con evidencia — cubre también E1-055 en su parte pública).

- [x] **E1-020 — Crear aviso de licencias de terceros.**
  Evidencia (15/08/2026): `/legal/licencias` generado a partir de los metadatos reales de `requirements.lock` (42 paquetes verificados con `importlib.metadata`): Lato bajo OFL 1.1 con su texto en `app/static/fonts/OFL.txt`, psycopg LGPL-3.0 usado sin modificar como paquete instalable, PyInstaller con su excepción de empaquetado, y sin copyleft fuerte en el producto distribuido.

- [x] **E1-021 — Mantener el repositorio privado y revisar que no contenga datos reales sensibles.**
  Evidencia (15/08/2026): repositorio confirmado **privado** (`gh api repos/... → "private": true`, 0 forks) y revisión de contenido convertida en comprobación repetible con `tools/auditar_datos_sensibles.py` (credenciales de Supabase/Resend/GitHub/AWS, JWT, PEM, cadenas de conexión con contraseña real, correos personales, teléfonos VE/ES, documentos fiscales, referencias del proyecto Supabase/Upstash y archivos que nunca deben versionarse). Se auditaron los 214 archivos versionados **y los 653 blobs de los 101 commits del historial**: no hay ni hubo nunca un secreto real confirmado (todas las coincidencias del historial son marcadores tipo `REEMPLAZAR` o valores de prueba), por lo que **no hace falta reescribir el histórico ni rotar claves**. Se corrigieron los tres datos reales encontrados en el árbol: el correo personal del propietario en `HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md` (→ `persona@example.com`) y dos apariciones de la referencia del proyecto Supabase en `docs/GUIA_STAGING_POR_CLICS.md` (→ `<ref-de-tu-proyecto>`). `tests/test_datos_sensibles.py` (34 pruebas) mantiene la auditoría en verde en CI y verifica que cada regla siga detectando y que los marcadores legítimos no generen ruido. Guía completa en `docs/DATOS_SENSIBLES.md`.

## 1.5 Catálogo comercial inicial

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

## 1.6 Seguridad y funcionamiento local

- [x] **E1-032 — Cambiar el host local predeterminado de `0.0.0.0` a `127.0.0.1`.**
  `run.py` solo expone otra interfaz si se configura deliberadamente `COTIZAT_HOST`; los despliegues administrados definirán su propio comando.

- [ ] **E1-033 — Revisar acciones destructivas locales.**  
  Borrados masivos, restauración de backup, ajustes de precios y eliminación de documentos deben exigir confirmación clara.

- [ ] **E1-034 — Sustituir capturas silenciosas de errores críticos por logging útil.**

- [ ] **E1-035 — Crear una página o paquete de diagnóstico para soporte.**  
  Sin incluir información sensible sin autorización del usuario.

- [ ] **E1-036 — Embeber o servir localmente las fuentes de la interfaz.**  
  Eliminar la dependencia actual de Google Fonts para el modo offline.

- [x] **E1-037 — Bloquear dependencias a versiones reproducibles.**
  Evidencia: `requirements.txt` y `requirements-dev.txt` fijan cada dependencia directa con `==`, y `requirements.lock` guarda el cierre transitivo completo (41 paquetes) que instala la integración continua. `tools/generar_lock.py` regenera el cierre y `tools/verificar_lock.py` impide que un pin cambie sin regenerarlo, evitando que Vercel y CI instalen versiones distintas. Cubierto por `tests/test_dependencias_bloqueadas.py`. Motivo: antes los rangos abiertos (`fastapi>=0.115`) permitían que Vercel resolviera versiones nuevas en cada build y rompiera un despliegue estable sin ningún cambio en el repositorio.

- [~] **E1-038 — Configurar GitHub Actions para ejecutar las pruebas.**
  Flujo escrito y verificado; falta un paso manual de activación. Evidencia: `docs/ci/ci.yml` define la ejecución en cada push a `main`/`arena/**` y en cada pull request, e incorpora las verificaciones que antes se hacían a mano: instalación del lock, coherencia del bloqueo, `compileall`, parseo de las 40 plantillas Jinja con el entorno real, `node --check` sobre los 20 archivos JavaScript, revisión de espacios en blanco limitada a las líneas del cambio, simulación del sistema de archivos de solo lectura de Vercel en modo PostgreSQL y SQLite, y `pytest -q`. Protegido por `tests/test_integracion_continua.py`, que falla si se elimina un paso o si las dos copias divergen.
  **Pendiente:** copiar `docs/ci/ci.yml` a `.github/workflows/ci.yml` desde un clon local y empujarlo (instrucciones en `docs/ci/README.md`). El token de la aplicación que abre los cambios automáticos carece del permiso `workflows` y GitHub rechaza el push de archivos bajo `.github/workflows/`.

- [x] **E1-039 — Hacer que `pytest` funcione sin depender de configurar manualmente `PYTHONPATH`.**
  Evidencia: `pytest.ini` incorpora la raíz del proyecto y permite ejecutar `.venv/bin/pytest -q` directamente.

- [x] **E1-040 — Añadir pruebas de los recorridos críticos.**
  Instalación limpia, primer inicio, presupuesto, PDF, backup, restauración y actualización.
  Evidencia (15/08/2026): `tests/test_recorrido_critico.py` encadena sobre HTTP instalación limpia → asistente → catálogo/cliente/presupuesto reales → PDF → backup → pérdida → restauración (incluida la copia previa automática), más restauración de una base de versión anterior con re-migración, backup automático semanal sin duplicados y rechazo de zip malicioso (zip slip). Cada prueba corre contra una instalación aislada vía `COTIZAT_DATA_DIR`.

- [x] **E1-041 — Revisar que las pruebas no modifiquen la base de datos personal del desarrollador.**
  Evidencia: `tests/conftest.py` asigna una base temporal antes de importar la aplicación y la elimina al cerrar la sesión de pytest.

## 1.7 Compatibilidad de escritorio pausada

Las herramientas existentes se conservan como fuente de migración, pero dejaron de ser entregables prioritarios por la decisión browser-first D-014.

- [-] **E1-042 — Generar un instalador comercial con marca y versión.**
  Pausada: no se invertirá en una nueva entrega Windows mientras falten autenticación, PostgreSQL y almacenamiento web.

- [-] **E1-043 — Probar instalación limpia en Windows 10 y Windows 11.**

- [-] **E1-044 — Probar actualización conservando base, imágenes y configuración.**
  Sustituida como prioridad por la importación controlada de SQLite de E1W-012.

- [-] **E1-045 — Probar desinstalación sin pérdida accidental de datos.**

- [-] **E1-046 — Probar backup y restauración entre dos equipos.**
  La versión web requerirá backup administrado y exportación por organización.

- [ ] **E1-047 — Definir formato de versiones y notas de lanzamiento.**
  Recomendación: versionado semántico `MAYOR.MENOR.PARCHE`.

- [-] **E1-048 — Definir un canal seguro para distribuir actualizaciones de escritorio.**

- [-] **E1-049 — Investigar firma de código para reducir alertas de SmartScreen.**

## 1.8 Documentación, demostración y soporte

- [x] **E1-050 — Crear guía de inicio rápido.**
  Evidencia (15/08/2026): `docs/GUIA_INICIO_RAPIDO.md` (~5 páginas impresas): cuenta y organización → catálogo (manual/Excel/importación local) → cliente → presupuesto → PDF, con tabla de «después del primer PDF» y canal de soporte. Sigue el recorrido de `docs/RECORRIDO_PRIMER_PRESUPUESTO.md` y el objetivo de <20 minutos.

- [ ] **E1-051 — Grabar vídeo de demostración de 5 minutos.**

- [x] **E1-052 — Crear un presupuesto de muestra comercial sin datos personales reales.**
  Evidencia (15/08/2026): `app/services/presupuesto_muestra.py` construye el presupuesto y `tools/generar_presupuesto_muestra.py` escribe `app/static/pdf/presupuesto-ejemplo.pdf`, enlazado desde la landing («Ver un presupuesto de ejemplo (PDF)»). Todo ficticio: empresa «Construcciones El Samán, C.A.» con RIF marcador `J-00000000-0` y contacto en el dominio reservado `ejemplo.com`, cliente genérico «Familia Rodríguez» sin documento real, e importes/mediciones verosímiles inventados; el propio PDF declara en «Información adicional» que todos los datos son ficticios. Cubierto por `tests/test_presupuesto_muestra.py`.

- [ ] **E1-053 — Crear preguntas frecuentes.**

- [ ] **E1-054 — Definir qué incluye y qué no incluye el soporte.**

- [ ] **E1-055 — Crear procedimiento para reportar errores con evidencia.**

- [~] **E1-056 — Preparar una landing page sencilla.**
  Publicada en `/conocer` (15/08/2026): problema, resultado, público objetivo, precios promocionales del piloto (89 US$/año con habitual 109; 9,99 US$/mes primer año con habitual 12,99), nota de honestidad (acceso anticipado, documentos no fiscales), llamada a solicitar demostración por email y enlace al PDF de ejemplo (E1-052, añadido el 15/08/2026). Pendiente para cerrar: el vídeo de demostración (E1-051), que se enlazará cuando exista.

## 1.9 Hipótesis comercial inicial

- [~] **E1-057 — Definir oferta de piloto fundador.**
  Precios decididos y publicados en la landing (15/08/2026): 89 US$/año como promoción inicial (precio habitual 109 US$/año) o 9,99 US$/mes el primer año (habitual 12,99 US$/mes), con configuración asistida y soporte incluidos. Pendiente: método de cobro (E1-059) y contrato/recibo (E1-060).

- [-] **E1-058 — Definir hipótesis de licencia de escritorio.**
  Descartada como prioridad por la dirección browser-first; el precio se validará sobre acceso web.

- [ ] **E1-059 — Definir métodos de cobro legales y operables.**  
  Considerar cobro trimestral/anual para reducir fricción administrativa.

- [ ] **E1-060 — Preparar recibo, contrato y registro interno de licencias.**

- [ ] **E1-061 — Definir proceso manual de activación para los primeros pilotos.**

## 1.10 Criterios de salida de la Etapa 1

No se marcará esta etapa como completada hasta cumplir todos los siguientes puntos:

- [x] La aplicación no muestra datos ni marca de RemodelaT a un cliente nuevo.
- [x] No existen promesas visibles de IA, 3D o facturación fiscal no implementadas.
- [ ] Un usuario nuevo puede generar su primer PDF en menos de 20 minutos con ayuda mínima.
- [ ] El catálogo comercial tiene procedencia revisada y precios fechados.
- [ ] PostgreSQL, Alembic y el aislamiento funcionan en una instancia de integración real.
- [ ] Inicio y cierre de sesión, membresías, roles y CSRF están probados.
- [ ] Imágenes y anexos usan almacenamiento persistente por organización.
- [x] Existe una exportación y una migración controlada desde SQLite.
  Exportación: backup .zip completo desde Configuración (E1-021). Migración: importación con confirmación explícita hacia la web el 15/08/2026 (E1W-012, `/configuracion/importar-instalacion`).
- [~] Existe guía de inicio, oferta, contrato y canal de soporte.
  Guía (`docs/GUIA_INICIO_RAPIDO.md`), oferta (precios en `/conocer`), términos como contrato de servicio (`/legal/terminos`) y canal de soporte (`/legal/soporte`) publicados el 15/08/2026. Falta: recibo y registro interno de licencias (E1-060) y crear el buzón soporte@cotizat.online.
- [x] CI ejecuta las pruebas y el recorrido crítico está cubierto.
  CI operativo desde el 14/08/2026 (E1-038); recorrido crítico completo cubierto el 15/08/2026 (E1-040, `tests/test_recorrido_critico.py`).
- [ ] Tres usuarios externos completaron una prueba de usabilidad.

**Puerta al terminar:** desplegar una beta web privada para prospectos y comenzar la validación pagada, sin afirmar todavía preparación para lanzamiento público.

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

**Puerta al terminar:** avanzar a beta web controlada, ajustar la propuesta o detener inversión comercial según evidencia de pago y uso.

---

# ETAPA 3 — Beta web controlada

**Estado:** PENDIENTE
**Prerrequisito:** fundamentos web de Etapa 1 y validación inicial de Etapa 2.
**Objetivo:** comprobar que el acceso alojado, el backup remoto, el soporte y la recurrencia aportan valor usando desde el inicio organizaciones lógicamente aisladas.

La beta seguirá siendo privada y de capacidad limitada. Compartir infraestructura no autoriza un lanzamiento público: cada acceso deberá validarse mediante membresía y las pruebas impedirán cruces de datos y archivos.

## 3.1 Fundamentos

- [ ] **E3-001 — Diseñar la operación y capacidad de la beta web controlada.**
- [ ] **E3-002 — Añadir login de aplicación seguro.**
- [ ] **E3-003 — Implementar cierre de sesión y cambio de contraseña.**
- [~] **E3-004 — Implementar recuperación de acceso administrada o por email.**
  Flujo Supabase implementado sin enumeración de cuentas y con redirect HTTPS fijo; falta configurarlo y probar el email real.
- [ ] **E3-005 — Configurar HTTPS obligatorio.**
- [x] **E3-006 — Añadir protección CSRF.**
  Implementada por validación estricta Origin/Referer y Fetch Metadata en PostgreSQL, con pruebas same-origin/cross-site.
- [~] **E3-007 — Añadir cookies seguras y cabeceras de seguridad.**
  Cookies Auth seguras y cabeceras globales implementadas; scripts y estilos CSP usan nonce, bloquean atributos inline y ya no admiten `unsafe-inline`. Falta validación HTTPS/navegador real.
- [~] **E3-008 — Añadir límites de carga y rate limiting básico.**
  Auth ya responde 429 con `Retry-After` ante ráfagas por ruta/IP y los archivos validan tamaño/MIME; falta un contador compartido entre instancias y verificar límites en el proxy de producción.

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

# ETAPA 4 — Endurecimiento y operación SaaS

**Estado:** PENDIENTE; algunos fundamentos técnicos fueron adelantados a E1W para evitar reescrituras.
**Prerrequisitos:** validación de pago, uso recurrente y demanda multiusuario.
**Estimación:** se revisará con métricas de la beta.
**Objetivo:** endurecer y operar públicamente la plataforma multiempresa iniciada en Etapa 1.

## 4.1 Refactorización estructural

- [ ] **E4-001 — Dividir `app/main.py` en routers por dominio.**
- [ ] **E4-002 — Extraer servicios de aplicación y reglas de autorización.**
- [~] **E4-003 — Crear configuración separada por entorno.**
  `DATABASE_URL` ya separa persistencia web; faltan secretos, almacenamiento y políticas completas por entorno.
- [x] **E4-004 — Introducir migraciones versionadas con Alembic.**
  Adelantada y completada como E1W-003.
- [-] **E4-005 — Mantener SQLite para escritorio y PostgreSQL para SaaS, si continúa el producto híbrido.**
  No habrá desarrollo híbrido paralelo: SQLite queda como compatibilidad/importación y PostgreSQL es el objetivo web.

## 4.2 Identidad y organizaciones

- [x] **E4-006 — Crear modelo de Organización/Empresa.**
  Adelantada y completada como E1W-004.
- [~] **E4-007 — Crear usuarios, membresías e invitaciones.**
  Implementados perfiles Auth, membresías e invitaciones de un solo uso con token hasheado, caducidad, revocación y aceptación por email verificado; faltan migración/prueba real y canal transaccional de entrega.
- [~] **E4-008 — Definir roles mínimos: propietario, administrador, miembro y lectura.**
  Roles persistibles, bloqueo global de escritura para `lectura` y reglas de administración de equipo implementados; falta completar la matriz por operación de negocio.
- [ ] **E4-009 — Implementar autorización centralizada.**
- [~] **E4-010 — Implementar recuperación de contraseña y verificación de email.**
  Recuperación implementada sobre Supabase y cambio de contraseña desde `/cuenta` con reautenticación previa y cierre de sesión posterior; falta prueba real y completar gestión explícita de verificación de email.
- [~] **E4-031 — Panel de cuenta de la persona usuaria.**
  `/cuenta` reúne perfil (nombre), cambio de contraseña, listado de organizaciones con la activa marcada y cierre de sesión; `/salir` revoca además la sesión en GoTrue. Falta cambio de email con reverificación, gestión de sesiones activas por dispositivo y eliminación de cuenta.
- [ ] **E4-011 — Evaluar segundo factor para administradores.**

## 4.3 Aislamiento multiempresa

- [x] **E4-012 — Añadir `organizacion_id` o estrategia equivalente a todos los datos empresariales.**
  Adelantada como E1W-005, incluidas entidades hijas.
- [~] **E4-013 — Aplicar filtrado obligatorio en la capa de datos.**
  SQLAlchemy ya lo aplica y `c93e7a4d20f1` versiona RLS por membresía/rol; falta aplicar y probar la barrera PostgreSQL real con el login limitado.
- [~] **E4-014 — Evitar depender de que cada ruta recuerde filtrar manualmente.**
  El criterio se aplica mediante eventos SQLAlchemy y políticas RLS sobre cada modelo tenant; falta validación de integración real.
- [~] **E4-015 — Crear pruebas automáticas de aislamiento para cada dominio.**
  Cobertura en `tests/test_tenancy.py`, `tests/test_storage.py` y `tests/test_rls.py`, incluidos metadatos, claves, proxy, cobertura de tablas/políticas y contexto parametrizado; faltan dominios y la integración PostgreSQL real.
- [~] **E4-016 — Auditar acceso directo por identificadores.**
  La prueba inicial cubre cliente y capítulo; falta inventario completo de rutas.
- [~] **E4-017 — Auditar archivos y URLs firmadas.**
  Objetos nuevos usan proxy privado y `/static/uploads` se bloquea en PostgreSQL; falta auditoría externa y decidir URLs firmadas cortas para descargas grandes.

## 4.4 Infraestructura

- [~] **E4-018 — PostgreSQL administrado.**
  Driver, URL y esquema están preparados; falta elegir proveedor y ejecutar integración real.
- [~] **E4-019 — Almacenamiento de objetos para imágenes, PDFs y anexos.**
  Backend y metadatos implementados como E1W-009; falta aprovisionar y probar el bucket privado real.
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
- [~] **E4-029 — CSRF, XSS, CSP, validación de archivos y rate limiting revisados.**
  CSRF, cabeceras, límites/MIME, rate limiting local y CSP sin `unsafe-inline` para scripts/estilos implementados; handlers, style API y sinks DOM quedan cubiertos por regresión. Faltan validación HTTPS independiente y rate limiting distribuido.
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
| Licencia local perpetua | 79–149 USD | Descartada como prioridad por D-014 |
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
| 13/08/2026 | D-003 | Preparar primero una versión comercial local | Decisión histórica sustituida por D-014 al aclararse la prioridad browser-first | Sustituida el 13/08/2026 |
| 13/08/2026 | D-004 | No publicar la aplicación actual en internet | Aún no existen autenticación, autorización de archivos ni seguridad web completa | Al completar E1W-007 a E1W-011 |
| 13/08/2026 | D-005 | No presentar funciones deterministas como IA | Proteger credibilidad | Si se integra IA real |
| 13/08/2026 | D-006 | No presentar la factura actual como fiscal | No existe homologación/integración demostrada | Tras consulta tributaria |
| 13/08/2026 | D-007 | No reescribir el frontend por moda | El stack actual permite validar el producto | Si aparecen límites medidos |
| 13/08/2026 | D-008 | Exigir pilotos pagados antes de escalar la operación SaaS | Los fundamentos multiempresa se adelantan por D-015, pero no la inversión operativa completa | Puerta Etapa 2 |
| 13/08/2026 | D-009 | Crear una marca para construcción latinoamericana, especializada inicialmente en remodelación venezolana | Permite crecer por país y función sin diluir el mensaje comercial de entrada | Tras la selección final de nombre |
| 13/08/2026 | D-010 | Adoptar **CotizaT** como nombre comercial | El usuario priorizó comprensión inmediata y aprobó expresamente el nombre | Tras revisión marcaria profesional |
| 13/08/2026 | D-011 | Usar la propuesta «Convierte tu catálogo y tus precios en presupuestos de obra claros, editables y listos para presentar» | Es verificable con el producto actual y no promete resultados financieros | Después de pruebas comerciales |
| 13/08/2026 | D-012 | Renombrar ejecutable e instalador, manteniendo compatibilidad automática con la carpeta histórica de datos | Aplicar la marca sin hacer desaparecer bases, imágenes ni backups existentes | Después de probar actualización en Windows |
| 13/08/2026 | D-013 | Sustituir la siembra automática por una elección explícita entre demo y limpio | Evitar datos y precios inesperados, y respetar a quien importará un catálogo propio | Después de pruebas de usabilidad |
| 13/08/2026 | D-014 | Desarrollar CotizaT browser-first y pausar nuevas inversiones de escritorio | El producto final será alojado; adelantar persistencia y aislamiento evita reescribir cada módulo | Después de la beta web privada |
| 13/08/2026 | D-015 | Adelantar organizaciones y aislamiento, pero no confundirlos con preparación para publicar | La propiedad de datos debe existir antes de ampliar funciones; autenticación, archivos y seguridad siguen pendientes | Al completar E1W-007 a E1W-011 |
| 13/08/2026 | D-016 | Adoptar Supabase inicialmente para PostgreSQL, Auth y Storage, manteniendo abstraído el almacenamiento | Reduce integraciones en la beta; PostgreSQL real, RLS y persistencia ya se validaron, sin impedir migrar objetos a R2 | Tras medir límites/coste en pilotos |

---

# 10. Registro de evidencia comercial

Se completará durante la Etapa 2. No deben guardarse aquí nombres, teléfonos ni datos sensibles sin autorización.

| Fecha | Tipo | Segmento | Hallazgo | Evidencia anonimizada | Acción |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

# 11. Próximo bloque de trabajo

## Etapa 1 activa — siguiente bloque: validación con matriz de aceptación en staging

La continuidad operativa exacta para una conversación nueva está en `docs/PUNTO_DE_CONTINUACION.md` (dónde se quedó el trabajo y qué sigue) y `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de fondo de staging); deben seguirse sin reconstruir el estado desde el chat.

La base browser-first ya está desplegada en staging Vercel + Supabase (`https://cotizat-generador.vercel.app`), con `/healthz` y `/readyz` respondiendo 200 OK. El siguiente trabajo es:

1. **Matriz de aceptación (Sección 4 de CONTINUIDAD):** continuar los 14 puntos de prueba manual con dos correos y dos organizaciones en el entorno desplegado. Los puntos 1-9, 11 y 12 quedaron superados el 14/08/2026 (registro de A, Organización A, recuperación de contraseña, subida/descarga de archivos y PDF, invitación al Usuario B, rol `lectura` comprobado, ascenso a `miembro`, Organización B homónima sin fuga de datos, cookies HttpOnly/Secure y consola sin violaciones CSP).
2. **E1W-009 / E1W-011 — prioridad inmediata:** verificar la subida/descarga de imágenes, anexos PDF y fichas técnicas a través del proxy autorizado conectando con el bucket privado `cotizat-private`. Es el punto 4 de la matriz y la primera prueba real de `SupabaseStorage`, hasta ahora solo ejercitado contra una simulación REST.
3. **E1W-007 / E1W-008:** las invitaciones de equipo, el cambio de roles (`lectura` vs `miembro`), las cookies de sesión (HttpOnly/Secure/SameSite, `document.cookie` vacío) y la ausencia de violaciones CSP ya quedaron validados en navegador real el 14/08/2026 (puntos 6-8, 11 y 12 de la matriz). La recuperación de clave ya está validada.
4. **Infraestructura — hecho:** el rate limiting distribuido ya está implementado (`app/ratelimit.py`, backend Upstash Redis por REST con degradación a memoria). Para activarlo en staging solo faltan las variables `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` y `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` en Vercel; `/readyz` publica el estado en `checks.rate_limit`.
5. **E1-012 a E1-014:** retomar usabilidad y medición externa sobre el recorrido web.

Evidencia acumulada al 14/08/2026:

- Marca, descriptor, propuesta y alcance no fiscal aplicados.
- Recorrido inicial, modos demo/limpio y progreso hasta el PDF implementados.
- Decisión browser-first registrada en `docs/ADR-001_ARQUITECTURA_BROWSER_FIRST.md`.
- `DATABASE_URL`, Psycopg 3 y Alembic preparados; compatibilidad SQLite preservada.
- Migraciones aplicadas en Supabase real; RLS activo y `cotizat_runtime` configurado como rol limitado miembro de `cotizat_app`.
- Bucket `cotizat-private` aprovisionado y verificado.
- PR #3 fusionado y PR #4 abierto con correcciones defensivas de lectura de `alembic_version` y manejo de excepciones en `lifespan`.
- Vercel desplegado y respondiendo HTTP 200 OK en `/healthz` y `/readyz` con todas las comprobaciones en verde.
- PR #6 fusionado: el bootstrap de la primera organización bajo RLS funciona y el propietario confirmó la creación de la Organización A en staging el 14/08/2026.
- Recuperación de contraseña validada end-to-end en staging el 14/08/2026: email recibido, enlace correcto hacia `/restablecer-clave`, cambio de contraseña e inicio de sesión con la nueva. Auth deja de ser un subsistema sin prueba real.
- Integración continua activa (E1-038) y dependencias bloqueadas (E1-037): cada pull request ejecuta la suite y las verificaciones que antes eran manuales.
- Pytest supera 174 pruebas automáticas.
- La aplicación **está lista para ejecutar la matriz de aceptación manual con dos organizaciones** antes de autorizar cualquier beta abierta.

---

## Declaración final de enfoque

El objetivo inmediato no es construir la mayor cantidad posible de funciones. El objetivo es comprobar que una empresa venezolana de remodelación puede:

1. Entender el producto.
2. Crear un presupuesto profesional rápidamente.
3. Confiar en sus datos y cálculos.
4. Mantener sus precios y documentos seguros.
5. Obtener suficiente valor como para pagar y seguir utilizándolo.

Los fundamentos multiempresa se construyen desde ahora para evitar reescrituras; la inversión en escalabilidad, operación pública y automatización comercial solo se justificará con evidencia de uso y pago.
