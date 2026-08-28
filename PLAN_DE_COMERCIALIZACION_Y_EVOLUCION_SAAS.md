# Plan de comercialización y evolución a SaaS

**Producto:** CotizaT — presupuestos y control comercial para construcción y remodelación
**Mercado inicial:** empresas pequeñas de remodelación y construcción privada en Venezuela  
**Zona inicial recomendada:** Valencia / Carabobo, con posterior expansión a Caracas y otras ciudades  
**Fecha de creación:** 13 de agosto de 2026  
**Última actualización:** 28 de agosto de 2026
**Estado general:** Etapas 0 y 1 completadas · Validación comercial aplazada hasta el final
**Etapa activa:** Etapa 3 — Cierre funcional y operativo de la versión web

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
| 1. Fundamentos comerciales web | Construir una base browser-first honesta, persistente y aislada | **Completada** | Base web, licencias y usabilidad verificadas |
| 2. Validación comercial pagada | Demostrar que empresas reales pagan y continúan usándolo | **Aplazada hasta el final por decisión del titular** | Solo se abrirá cuando el producto se considere completo (D-017) |
| 3. Cierre funcional y operativo web | Terminar el ciclo comercial y la operación antes de exponerlo a clientes | **Completada (19/08/2026)** | Envío, aceptación, recuperación y operación completas y desplegadas |
| 4. Endurecimiento SaaS | Completar seguridad, escalabilidad y operación pública | **En curso** — completados el 19/08/2026: E4-030 (escaneo de dependencias/secretos en CI), **E4-021** (respaldo automático por organización), **E4-023** (verificación diaria con alerta), **E4-038** (consentimiento registrado), **E4-032** (plan de incidentes) y **E4-026/E4-027** (registro de auditoría inmutable + historial de sesiones; migración `d2a7c9e4f1b3` **ya aplicada en Supabase**); **E4-020 aplazado por decisión del titular (D-022)**; queda el simulacro E4-043 por ejecutar, pasos de panel (vigilante externo, backups Supabase Pro) y los ítems E4-039 a E4-044 (dependen de D-017) | Beta de aislamiento y seguridad aprobada |
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
- [-] Exigir validación pagada antes de completar el producto. Decisión histórica sustituida por D-017: el titular no entregará una versión que considere incompleta; la validación comercial se hará al final.

## 0.3 Criterio de salida

- [x] Estado técnico conocido.
- [x] Riesgos críticos identificados.
- [x] Mercado y cliente inicial definidos.
- [x] Etapas futuras documentadas.

**Resultado de la puerta:** avanzar a Etapa 1.

---

# ETAPA 1 — Fundamentos de la versión comercial web

**Estado:** COMPLETADA el 16/08/2026
**Objetivo cumplido:** transformar la aplicación privada en una base web honesta, persistente y aislada por empresa, con autenticación, almacenamiento, licencias y recorrido principal verificados.
**Resultado:** la siguiente etapa activa es el cierre funcional y operativo. La validación comercial pagada queda aplazada hasta que el titular declare completo el producto (D-017).

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
  Recorrido y presupuesto temporal documentados en `docs/RECORRIDO_PRIMER_PRESUPUESTO.md`: empresa → contenido inicial → catálogo → cliente → presupuesto → descarga de PDF. La meta de 20 minutos quedó validada externamente el 16/08/2026 para el público objetivo (E1-012/013).

- [x] **E1-009 — Crear asistente de primer inicio.**
  Evidencia: `/bienvenida` solicita nombre comercial, razón social, RIF, teléfono, email, país, ciudad, dirección, moneda, IVA y logo; conserva todo en la base local y solo exige el nombre para avanzar. Una base anterior migra sin mostrar el asistente ni sobrescribir su empresa.

- [x] **E1-010 — Permitir elegir entre datos de demostración o instalación limpia.**
  Evidencia: la elección explícita e idempotente carga catálogo, productos, packs, cliente y presupuesto ficticios, o deja la instalación vacía. Los registros demo se identifican en la interfaz y no completan hitos reales.

- [x] **E1-011 — Crear una lista de inicio o panel de bienvenida.**
  Evidencia: el dashboard muestra cinco pasos comprobados con datos locales: empresa, catálogo, cliente real, presupuesto real y descarga del primer PDF. Abrir una vista previa o descargar el PDF demo no completa el último paso.

- [x] **E1-012 — Ejecutar pruebas de usabilidad con al menos 3 personas ajenas al desarrollo.**
  Evidencia comunicada por el titular el 16/08/2026: varias personas externas probaron el recorrido. Las personas del ámbito de la construcción —público objetivo real— completaron el presupuesto sin ayuda. No se localizaron errores durante las sesiones.

- [x] **E1-013 — Medir el tiempo real hasta el primer PDF.**
  Resultado: varios participantes prepararon un presupuesto genérico de baño en aproximadamente **10 minutos**. El público objetivo quedó por debajo del máximo de 20 minutos. Algunas personas sin conocimientos de construcción tardaron más de 20 minutos; no se considera un fallo del recorrido para el nicho definido, pero queda como dato de segmentación.

- [x] **E1-014 — Simplificar el recorrido básico según los resultados.**
  No se observaron bloqueos, errores ni necesidad de ayuda entre profesionales de construcción, por lo que no se justifica cambiar el recorrido antes de los pilotos. Se reabrirá únicamente si el uso pagado aporta evidencia nueva.

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

## 1.5 Catálogo de ejemplo y catálogo comercial futuro

**Decisión del titular (16/08/2026, matizada el 19/08/2026):** todas las
partidas del catálogo (3.006 en `basedatos_partidas/datos/`) son **de autoría
propia** y son **el catálogo del producto**. No provienen de terceros: la
auditoría **E1-022 quedó cerrada el 19/08/2026 con evidencia** (0 coincidencias
de texto con los `.xlsx` de ejemplo, códigos CYPE ausentes, `recursos.json`
propio — detalle en `docs/DATOS_SENSIBLES.md` §6). Los archivos `DPT020.xlsx`,
`RBA010.xlsx` y `RBE030.xlsx` **no aportan contenido**: solo definen el
formato de importación que usa el usuario para subir su propio banco de
precios, y `BENEFICIO.png`/la captura de la raíz son archivos sueltos sin
referencia alguna.

El trabajo de catálogo pendiente es de **crecimiento y precio**, no de
sustitución: ampliar el catálogo propio hasta las ~5.000 partidas y cerrar los
~196 precios provisionales B2B que requieren cotización. Las tareas siguientes
se conservan reprogramadas para esa carga final de contenido, no como trabajo
activo:

- [x] **E1-022 — Aclarar la procedencia de las partidas actuales.**
  **CERRADO (19/08/2026):** auditoría de evidencia; catálogo 100 % de autoría
  propia; los ejemplos de importación no aportan contenido.
- [-] **E1-023 — Definir el esquema del catálogo maestro.** Reprogramada para el catálogo real.
- [-] **E1-024 — Separar catálogo maestro, personalización y precio congelado.** Reprogramada para el catálogo real.
- [-] **E1-025 — Curar un catálogo inicial de 200–500 partidas.** Retirada del alcance actual.
- [-] **E1-026 — Normalizar unidades y vocabulario venezolano.** Reprogramada para la revisión del contenido real.
- [-] **E1-027 — Detectar y fusionar duplicados.** Reprogramada para la revisión del contenido real.
- [-] **E1-028 — Marcar precios como referenciales.** Reprogramada para la carga del catálogo real.
- [-] **E1-029 — Añadir fecha y procedencia a cada precio.** Reprogramada para la carga del catálogo real.
- [-] **E1-030 — Documentar la actualización del catálogo.** Reprogramada para cuando exista contenido definitivo.
- [-] **E1-031 — Preparar packs comerciales iniciales.** Los packs actuales son de prueba; los comerciales se cargarán al final.

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

- [x] **E1-038 — Configurar GitHub Actions para ejecutar las pruebas.**
  CI activa en GitHub desde el 14/08/2026 y ejecutada en cada push a `main`/`arena/**` y pull request. Incluye instalación del lock, coherencia del bloqueo, `compileall`, parseo de plantillas Jinja, `node --check`, revisión de espacios, simulación del sistema de archivos de solo lectura de Vercel y `pytest -q`. `tests/test_integracion_continua.py` protege la definición. Evidencia más reciente: ejecución de `main` del PR #25 completada en verde el 16/08/2026.

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

- [x] **E1-053 — Crear preguntas frecuentes.**
  Evidencia (16/08/2026): `/legal/preguntas` (`app/templates/legal/preguntas.html`), 17 preguntas en 5 bloques (producto; datos, importación y control; facturación y alcance fiscal; precio y contratación; soporte). Enlazada desde el pie de la landing y de todas las páginas legales. Declara el acceso anticipado, repite que los documentos **no son facturas fiscales** y cierra advirtiendo que en caso de discrepancia prevalecen términos, privacidad y soporte. Cubierta por 6 pruebas en `tests/test_paginas_publicas.py`, incluida una que falla si la FAQ llegara a prometer facturación fiscal.

- [x] **E1-054 — Definir qué incluye y qué no incluye el soporte.**
  Evidencia: `/legal/soporte` §2 y §3 delimitan lo incluido (configuración, dudas de uso, errores del producto, recuperación de acceso) y lo excluido (asesoramiento fiscal/legal, carga manual del catálogo completo, desarrollos a medida, hardware/SO/red), más horario y tiempos orientativos declarados como compromisos de esfuerzo, no garantías con penalización. Protegido por `test_condiciones_de_soporte_delimitan_incluido_y_excluido`.

- [x] **E1-055 — Crear procedimiento para reportar errores con evidencia.**
  Evidencia: `/legal/soporte` §5 pide los cinco datos que hacen reproducible un fallo (qué esperabas, qué ocurrió con el mensaje exacto, pasos, captura o PDF **sin datos personales de clientes**, y fecha/hora + entorno). Protegido por `test_procedimiento_de_reporte_pide_evidencia_sin_datos_de_clientes`.

- [~] **E1-056 — Preparar una landing page sencilla.**
  Publicada en `/conocer` (15/08/2026): problema, resultado, público objetivo, precios promocionales del piloto (89 US$/año con habitual 109; 9,99 US$/mes primer año con habitual 12,99), nota de honestidad (acceso anticipado, documentos no fiscales), llamada a solicitar demostración por email y enlace al PDF de ejemplo (E1-052, añadido el 15/08/2026). Pendiente para cerrar: el vídeo de demostración (E1-051), que se enlazará cuando exista.
  **Ampliación comercial (20/08/2026): la landing vende el catálogo completo y se adapta a la moneda del país.** `app/services/landing_ejemplo.py` convierte el presupuesto de ejemplo y el APU real del catálogo (partida `14.04.01.060`) a la moneda del visitante con la tasa de referencia verificada (`app/services/tasa.py`): `/co/` muestra `COL$` con IVA 19 % y Bogotá, `/mx/` `MX$` con IVA 16 % y Ciudad de México, `/pe/` `S/` con IVA 18 %, y VE/EC/genérico quedan en `US$`; sin tasa verificada nunca se inventa conversión (degrada a USD). Las partidas del ejemplo se traducen con el servicio real de terminología (friso → pañete / aplanado) y los totales visibles suman exacto en cualquier moneda (invariantes en `tests/test_landing_ejemplo.py` + `tests/test_latam.py`). Además, las cifras de catálogo de `cifras_catalogo()` ahora cuentan las **líneas de precio completas**: 3.006 partidas + 392 precios de recursos = 3.398 líneas, más 16.127 líneas de descomposición y 6 packs de estancia; la landing añade la sección de APU (recursos, rendimientos y precio de venta reales) y una tabla comparativa de capacidades que casi ningún generador ofrece (CYPE, horas de cuadrilla, firma del cliente, versiones inmutables, moneda dual, packs, cobros).

## 1.9 Hipótesis comercial inicial

- [x] **E1-057 — Definir oferta de piloto fundador.**
  Precios decididos y publicados en la landing (15/08/2026): 89 US$/año como promoción inicial (precio habitual 109 US$/año) o 9,99 US$/mes el primer año (habitual 12,99 US$/mes), con configuración asistida y soporte incluidos. Método de cobro manual cerrado en E1-059 y contrato, recibo y registro de licencias cerrados en E1-060 el 16/08/2026.

- [-] **E1-058 — Definir hipótesis de licencia de escritorio.**
  Descartada como prioridad por la dirección browser-first; el precio se validará sobre acceso web.

- [x] **E1-059 — Definir métodos de cobro legales y operables.**
  **Decisión del titular (16/08/2026): cobro manual para el piloto.** El
  cliente paga por transferencia, Zelle, Binance o Pago Móvil y el titular
  activa la licencia a mano desde el panel. Vía «en serio» ya acordada para el
  cobro recurrente: autónomo en España (modelo 036 + RETA) + Stripe; *merchant
  of record* descartado hoy (más caro y exige la entidad ya creada). Stripe no
  opera en Venezuela y Wise/Payoneer restringen a residentes venezolanos; el
  titular es español y reside en España, así que la regularización fiscal es
  asumible cuando el volumen lo pida. Análisis en `docs/COBRO_Y_LICENCIAS.md`.

- [x] **E1-060 — Preparar recibo, contrato y registro interno de licencias.**
  **Registro interno completado (16/08/2026).** Panel de operador en `/admin/licencias` (`app/templates/admin/licencias.html`, `app/services/licencias.py`, modelo `Licencia`, migración `f4c1d8e37a95`): conceder, renovar, regalar prueba o cortesía, compensar incidencias y cancelar dejando constancia, con resumen de organizaciones sin licencia y avisos de vencimiento a 15 días. Distingue `pago` de `prueba`/`cortesia`/`compensacion` para que solo lo cobrado sume a ingresos, y encadena renovaciones sin restar días. **Aislamiento**: `licencias` es tabla **no-tenant** con RLS propia (`cotizat_licencia_*`) que exige la marca `cotizat.es_operador`; la lista de operadores vive en `COTIZAT_OPERADORES` (variable de entorno, no columna, para que no exista escalada escribiendo en la base) y se exige email verificado. Guía en `docs/PANEL_DE_OPERADOR.md`.
  **Cerrado del todo (16/08/2026, noche), migración `b7c4a9e2d31f`:**
  - **Recibo PDF** por licencia de pago (`app/services/recibo_licencia.py`,
    botón «recibo PDF» en el panel): número estable `CT-000NNN`, período
    inclusive, método y referencia; se declara **comercial sin validez fiscal**
    mientras no exista razón social registrada.
  - **Corte automático de acceso**: con `COTIZAT_EXIGIR_LICENCIA=true`, una
    organización sin licencia vigente no entra a sus pantallas (página
    «Acceso suspendido»; los datos no se tocan y vuelven al renovar). El
    corte consulta `cotizat_security.organization_has_license` (SECURITY
    DEFINER guardada por el claim de organización: la sesión del cliente no
    puede leer `licencias`). Valor por omisión: desactivado; escritorio jamás
    exige licencia.
  - **Avisos de vencimiento por correo** (Resend): botón del panel que
    escribe a propietario/administrador activos vía
    `cotizat_security.organization_admin_emails` (guardada por marca de
    operador), con constancia del envío en la propia licencia y sin reenviar
    dos veces el mismo día.
  - **Corrección de visibilidad**: la política `cotizat_org_select` solo
    mostraba organizaciones con membresía propia, así que el panel era ciego
    a las de clientes; ahora las lista también para la sesión de operador.

- [x] **E1-061 — Definir proceso manual de activación para los primeros pilotos.**
  Documentado en `docs/PROCESO_PILOTOS.md` (16/08/2026): demostración →
  registro del prospecto → cobro manual acordado → licencia y recibo desde el
  panel → seguimiento semanal de «por vencer» con avisos por correo →
  suspensión automática al vencer si no hay pago → reactivación al renovar
  sin perder datos.

- [x] **E1-062 — Prueba gratuita de 7 días como puerta de entrada.**
  **Decisión del titular (18/08/2026): 7 días, sin tarjeta.** Es la respuesta a
  la fricción del cobro manual: el prospecto no puede «pagar y probar» en un
  clic como haría con Stripe, así que se le da acceso completo primero y se
  cobra después. Publicada en `/`, `/conocer`, `/pago` y `/acceso` con el
  compromiso explícito de que no se pide tarjeta y no se cobra nada
  automáticamente.

  **La licencia se otorga a la organización, nunca al usuario.** Quien quiera
  una segunda organización paga otro plan para ella. Sin esta regla, una sola
  cuenta pagada podría dar servicio a diez organizaciones con diez personas
  dentro, que es regalar el producto.

  **Defensa anti-reciclaje** (una prueba por identidad, para siempre): el email
  se normaliza antes de registrarlo —se ignoran los puntos en Gmail y las
  subdirecciones `+etiqueta` en los proveedores que las admiten—, de modo que
  los alias de una misma cuenta cuentan como una sola identidad. Los dominios
  de correo desechable se bloquean **en el registro**, no después. La IP del
  alta se guarda **hasheada** y solo sirve para que el operador vea patrones en
  el panel: nunca bloquea a nadie automáticamente, porque una oficina entera
  comparte IP y el falso positivo costaría un cliente real.

  **Reversible sin desplegar código**: `COTIZAT_DIAS_PRUEBA=0` retira la oferta
  y el anuncio desaparece de las cuatro páginas, sustituido por «Ver planes».
  Hay un test que lo comprueba, para que la promesa pública no sobreviva a la
  retirada de la oferta. Detalle en `docs/COBRO_Y_LICENCIAS.md` §5.

## 1.10 Criterios de salida de la Etapa 1

No se marcará esta etapa como completada hasta cumplir todos los siguientes puntos:

- [x] La aplicación no muestra datos ni marca de RemodelaT a un cliente nuevo.
- [x] No existen promesas visibles de IA, 3D o facturación fiscal no implementadas.
- [x] Un usuario nuevo puede generar su primer PDF en menos de 20 minutos con ayuda mínima.
  Evidencia (16/08/2026): profesionales de construcción lo hicieron sin ayuda; varios presupuestos genéricos de baño se completaron en unos 10 minutos.
- [x] El contenido de catálogo incluido en esta etapa tiene situación conocida.
  Decisión del titular (16/08/2026): todas las partidas actuales son propias, se conservan únicamente como datos de ejemplo para pruebas y se eliminarán al cargar las partidas reales revisadas. Por tanto no constituyen el catálogo comercial ni bloquean el cierre de la etapa.
- [x] PostgreSQL, Alembic y el aislamiento funcionan en una instancia de integración real.
  Evidencia: producción Vercel + Supabase con `/readyz` en verde (head Alembic, rol runtime limitado miembro de `cotizat_app`) y matriz de aceptación con dos organizaciones superada el 14/08/2026 (puntos 1-9, 11 y 12, incluida organización homónima sin fuga de datos); RLS de `licencias` verificado en producción el 16/08/2026.
- [x] Inicio y cierre de sesión, membresías, roles y CSRF están probados.
  Evidencia: E2E de Auth en producción el 15/08/2026 (registro, confirmación, cambio de contraseña, invitaciones con y sin cuenta previa); roles `lectura`/`miembro`, cookies HttpOnly/Secure y consola sin violaciones CSP en la matriz del 14/08/2026 (puntos 6-8, 11 y 12); CSRF same-origin cubierto por la suite (`tests/test_web_security.py`).
- [x] Imágenes y anexos usan almacenamiento persistente por organización.
  Evidencia: punto 4 de la matriz (14/08/2026) — subida y descarga de imágenes, anexos PDF y fichas técnicas a través del proxy autorizado sobre el bucket privado `cotizat-private`.
- [x] Existe una exportación y una migración controlada desde SQLite.
  Exportación: backup .zip completo desde Configuración (E1-021). Migración: importación con confirmación explícita hacia la web el 15/08/2026 (E1W-012, `/configuracion/importar-instalacion`).
- [x] Existe guía de inicio, oferta, contrato y procedimiento de soporte.
  Guía (`docs/GUIA_INICIO_RAPIDO.md`), oferta (precios en `/conocer`), términos (`/legal/terminos`) y procedimiento (`/legal/soporte`) publicados. Recibo y registro interno de licencias cerrados el 16/08/2026. La activación del buzón `soporte@cotizat.online` permanece como requisito operativo previo al lanzamiento, no como desarrollo pendiente de Etapa 1.
- [x] CI ejecuta las pruebas y el recorrido crítico está cubierto.
  CI operativo desde el 14/08/2026 (E1-038); recorrido crítico completo cubierto el 15/08/2026 (E1-040, `tests/test_recorrido_critico.py`).
- [x] Tres o más usuarios externos completaron una prueba de usabilidad.
  Evidencia comunicada por el titular el 16/08/2026: varias personas probaron el producto, sin errores observados; el público de construcción no necesitó ayuda.

**Resultado de la puerta (decisión D-017):** Etapa 1 completada. En lugar de abrir la validación pagada, se avanza al cierre funcional y operativo de la versión web. Ningún piloto comercial se iniciará hasta que el titular considere completo el producto.

---

# ETAPA 2 — Validación comercial pagada (aplazada hasta el final)

**Estado:** APLAZADA por decisión expresa del titular (16/08/2026)
**Objetivo futuro:** demostrar que empresas reales pagan y usan repetidamente el producto ya terminado.
**Condición para activarla:** el titular debe declarar cerrados los bloques funcionales y operativos del producto. No se entregará a clientes una versión considerada incompleta. Las tareas y métricas de esta sección se conservan para ejecutarlas al final, no como próximo bloque.
**Duración orientativa cuando se active:** 30–60 días.

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

# ETAPA 3 — Cierre funcional y operativo de la versión web

**Estado:** COMPLETADA (19/08/2026) — código desplegado en producción
(`cotizat.online`) y migraciones aplicadas; solo queda la validación final de
tipo prueba, agrupada en el día final de tests (D-019).
**Prerrequisito:** fundamentos web de Etapa 1 completados. Por D-017 no requiere validación comercial previa.
**Objetivo:** terminar el ciclo completo del presupuesto y la operación técnica antes de entregar CotizaT a clientes: envío, enlace seguro, aceptación trazable, recuperación, exportación y soporte operativo.

El desarrollo y las pruebas se realizan con datos ficticios o del titular. No se abre una beta comercial durante esta etapa. El primer bloque funcional es E3-016 a E3-019: llevar el presupuesto desde su generación hasta la entrega y aceptación por el cliente.

> **Numeración:** el bloque operativo E3-020 a E3-024 (respaldo, restauración,
> exportación, baja y monitorización) está descrito en el §11 y es la
> numeración usada en el resto del repositorio. Los ítems E3-025 a E3-029 de
> esta sección se renumeraron el 19/08/2026 para eliminar la colisión con ese
> bloque.

## 3.1 Fundamentos

- [ ] **E3-001 — Diseñar la operación y capacidad de la beta web controlada.**
- [x] **E3-002 — Añadir login de aplicación seguro.**
  Completado y verificado en producción con Supabase Auth.
- [x] **E3-003 — Implementar cierre de sesión y cambio de contraseña.**
  Completado en `/cuenta` y verificado end-to-end.
- [x] **E3-004 — Implementar recuperación de acceso administrada o por email.**
  Flujo Supabase sin enumeración, redirect HTTPS fijo y prueba end-to-end completada el 14/08/2026.
- [x] **E3-005 — Configurar HTTPS obligatorio.**
  Dominio `cotizat.online` desplegado por HTTPS; cookies seguras verificadas.
- [x] **E3-006 — Añadir protección CSRF.**
  Implementada por validación estricta Origin/Referer y Fetch Metadata en PostgreSQL, con pruebas same-origin/cross-site.
- [x] **E3-007 — Añadir cookies seguras y cabeceras de seguridad.**
  Cookies HttpOnly/Secure/SameSite y CSP sin `unsafe-inline` verificadas en navegador HTTPS real el 14/08/2026.
- [x] **E3-008 — Añadir límites de carga y rate limiting básico.**
  Archivos con tamaño/MIME validados y rate limiting distribuido activo con Upstash; `/readyz` confirma `distribuido:upstash`.

## 3.2 Datos y operación

- [~] **E3-009 — Crear almacenamiento persistente y backup externo cifrado.**
  Persistencia en PostgreSQL (Supabase) y **backup completo verificable** por
  organización (E3-020, manual: paquete `.zip` con manifest y SHA-256). Falta
  la **automatización y el cifrado en reposo externo** → pendiente **E4-021**
  (backups automáticos).
- [x] **E3-010 — Probar restauración completa de una instancia.**
  Restauración controlada en dos pasos ensayada (E3-021); verificación íntegra
  antes de escribir, fusión idempotente, archivos re-escritos al almacén
  privado. `docs/RESPALDO_Y_RESTAURACION_WEB.md`.
- [x] **E3-011 — Separar secretos y configuración del código.**
  Secretos en variables de entorno; repositorio e historial auditados por
  E1-021 y vigilados en CI desde el 19/08/2026 por E4-030 (detect-secrets).
- [~] **E3-012 — Añadir monitorización de disponibilidad y errores.**
  Panel `/admin/operacion` con los chequeos de `/readyz` y registro acotado de
  errores (E3-024). Falta la **vigilancia proactiva de disponibilidad**
  (alertas) → pendiente **E4-023**.
- [x] **E3-013 — Crear procedimiento de alta y baja de empresa.**
  Alta por registro autónomo (con prueba gratuita y verificación de email);
  baja por el propietario con borrado verificado y transaccional (E3-023).
  `docs/EXPORTACION_Y_BAJA_ORGANIZACION.md` y `docs/PROCESO_PILOTOS.md`.
- [x] **E3-014 — Crear exportación completa de datos del cliente.**
  `cotizat-export` v1: CSV por tabla + archivos con nombre original + respaldo
  verificable embebido (E3-022), solo propietario/administrador.
- [ ] **E3-015 — Definir tiempos de retención y eliminación.**
  Pendiente: política de retención (parcialmente cubierta en la política de
  privacidad v1; falta la declaración formal de plazos).

## 3.3 Funciones comerciales web prioritarias

- [x] **E3-016 — Envío por email del presupuesto.**
  Completado en la rama de trabajo el 16/08/2026: formulario precargado desde el cliente, PDF adjunto por Resend, `Reply-To` de la empresa, transición enviado/reenviado solo tras confirmación del proveedor, versión inmutable, copia exacta del PDF en almacenamiento privado y constancia interna. Un fallo no cambia estado ni crea versión; el rol lectura no puede provocar el efecto externo. Cobertura en `tests/test_envio_presupuesto_email.py` (6 pruebas); suite: 397 passed, 5 skipped.
- [x] **E3-017 — Enlace público seguro y revocable para ver una propuesta.**
  Completado en la rama de trabajo el 16/08/2026: cada enlace apunta a una versión y PDF congelados, guarda solo SHA-256 del secreto, caduca, puede revocarse y al crear uno nuevo revoca el anterior. La página sin sesión muestra únicamente empresa, cliente, número, título, fechas, total y el PDF exacto; no abre ninguna otra tabla del tenant. RLS se limita a una fila por claim transaccional (`c2f6e8a1d934`), con cabeceras no-store/no-referrer/noindex. Suite: 403 passed, 6 skipped.
- [x] **E3-018 — Aceptación del presupuesto con trazabilidad.**
  Completado en la rama el 16/08/2026: aceptar/rechazar una sola vez sobre la versión exacta, con nombre y email declarados, comentario opcional y fecha/hora. PostgreSQL registra la respuesta mediante una función SECURITY DEFINER limitada a cinco columnas y al hash vigente; la sesión pública no recibe UPDATE ni acceso al tenant. La interfaz declara honestamente que no es firma electrónica cualificada ni identidad certificada. Suite: 405 passed, 6 skipped.
- [x] **E3-019 — Notificación de aceptación o rechazo.**
  Completado localmente el 16/08/2026: la respuesta actualiza el presupuesto a aprobado/rechazado solo si corresponde a la última versión enviada, deja nota interna y notifica inmediatamente por Resend a propietarios/administradores con `Reply-To` del cliente. Una respuesta sobre versión antigua nunca sobrescribe el estado actual. Los fallos del proveedor no pierden la decisión: quedan visibles y admiten reintento sin repetir destinatarios ya confirmados. Suite: 409 passed, 6 skipped.
- [-] **E3-025 — Registro de apertura cuando sea legal y se informe adecuadamente.**
  **Decisión D-021 (19/08/2026): NO implementar.** Requeriría tratamiento legal
  del consentimiento y aporta poco frente al coste; la apertura no es una
  métrica de conversión crítica en el piloto manual.

## 3.4 Operación comercial

- [x] **E3-026 — Cobro recurrente o renovación manual documentada.**
  Renovación manual documentada en `docs/PROCESO_PILOTOS.md` y operativa
  (panel de operador + cron de recordatorios verificado en Vercel el
  19/08/2026); cobro recurrente (Stripe) permanece para cuando haya volumen
  (E4-034).
- [x] **E3-027 — Controlar vencimiento, gracia y suspensión sin borrar datos.**
  Corte, renovación y reactivación completados en E1-060 y verificados por el
  titular; recordatorios automáticos a 5 y 1 día operativos (cron).
- [x] **E3-028 — Definir SLA y horario de soporte.**
  Alcance, horario y tiempos orientativos publicados en `/legal/soporte`.
- [-] **E3-029 — Medir coste de infraestructura y soporte por cliente.**
  Aplazada junto con la validación comercial; no existe todavía una muestra de clientes.

## 3.5 Criterios de salida de la Etapa 3

Esta etapa se cierra con evidencia técnica, no con clientes (D-017):

- [x] El presupuesto puede enviarse por email desde CotizaT.
- [x] Existe un enlace público seguro, revocable y limitado a una propuesta.
- [x] La aceptación o rechazo queda trazada y notifica a la empresa.
- [x] La restauración completa de datos y archivos está ensayada (E3-020/E3-021).
- [x] Existe exportación completa por organización y procedimiento de baja (E3-022/E3-023).
- [x] Monitorización y diagnóstico permiten detectar fallos sin exponer datos sensibles (E3-024).
- [x] Autenticación, HTTPS, almacenamiento privado, rate limiting y licencias funcionan en producción.

Todo el bloque E3-016 a E3-024 está **completado, desplegado en producción y
verificado** (19/08/2026). Suite vigente: **672 passed, 6 skipped**. Las
migraciones del bloque están aplicadas en Supabase y `/readyz` responde
`ok: true` en `cotizat.online` con el cron de recordatorios operativo.

**Puerta al terminar:** completada — se pasó al endurecimiento técnico de la
Etapa 4, que está en curso. La validación comercial continúa aplazada (D-017)
y las comprobaciones de tipo prueba de esta etapa quedan agrupadas en el día
final de tests (D-019).

---

# ETAPA 4 — Endurecimiento y operación SaaS

**Estado:** EN CURSO — iniciada el 16/08/2026; a 19/08/2026 completados la
refactorización estructural (E4-001 a E4-005), la autorización centralizada
(E4-009), los logs estructurados (E4-022) y el escaneo de dependencias y
secretos en CI (E4-030). Pendientes recomendados: **E4-021 (backups
automáticos)** y **E4-023 (alertas de disponibilidad)**.
**Prerrequisitos:** cierre funcional de la Etapa 3. Por D-017, el endurecimiento puede completarse antes de la validación comercial.
**Estimación:** se revisará con métricas de la beta.
**Objetivo:** endurecer y operar públicamente la plataforma multiempresa iniciada en Etapa 1.

## 4.1 Refactorización estructural

- [x] **E4-001 — Dividir `app/main.py` en routers por dominio.**
  Completado el 17/08/2026: `app/main.py` (antes ~8.200 líneas) queda como
  esqueleto de montaje (middlewares, manejadores de excepción, estáticos y
  rutas de sistema) y las rutas de negocio viven en `app/routers/`, un módulo
  por dominio (`auth`, `publico`, `admin`, `inicio`, `clientes`,
  `presupuestos`, `configuracion`, `partidas`, `productos`, `recursos`,
  `plantillas`, `recetas`). Los helpers, el entorno Jinja y las constantes
  compartidas están en `app/routers/common.py`; cada router los importa con
  `from .common import *` y los nombres mutables que los tests parchean se
  leen por referencia (`common.NOMBRE`). Suite completa en verde.
- [x] **E4-002 — Extraer servicios de aplicación y reglas de autorización.**
  Los servicios viven en `app/services/` (licencias, propuestas, respaldo,
  restauración, exportación, baja, operación…) y las reglas de autorización
  quedaron centralizadas en `app/permisos.py` el 16/08/2026.
- [x] **E4-003 — Crear configuración separada por entorno.**
  Completado el 17/08/2026 con `app/config.py`: detecta el entorno
  (`COTIZAT_ENV` → `VERCEL_ENV` → pytest → desarrollo), mantiene el catálogo
  único de variables (incluida la marca de cuáles son secretas) y valida por
  entorno sin revelar valores (`validar()` / `resumen_configuracion()`). El
  entorno aparece en `/readyz` y el resumen completo en el panel del operador
  (`/admin/operacion`). Los resolvers finos existentes (`SupabaseAuthSettings`,
  `StorageSettings`, `EmailSettings`, `DatabaseSettings`) siguen siendo la capa
  de validación de formato; `app/config.py` es la fuente de verdad del
  entorno y de la superficie de configuración.
- [x] **E4-004 — Introducir migraciones versionadas con Alembic.**
  Adelantada y completada como E1W-003.
- [-] **E4-005 — Mantener SQLite para escritorio y PostgreSQL para SaaS, si continúa el producto híbrido.**
  No habrá desarrollo híbrido paralelo: SQLite queda como compatibilidad/importación y PostgreSQL es el objetivo web.

## 4.2 Identidad y organizaciones

- [x] **E4-006 — Crear modelo de Organización/Empresa.**
  Adelantada y completada como E1W-004.
- [x] **E4-007 — Crear usuarios, membresías e invitaciones.**
  Implementados y **verificados**: perfiles Auth, membresías e invitaciones de
  un solo uso con token hasheado, caducidad, revocación y aceptación por email
  verificado; migración aplicada y prueba E2E «invitación sin cuenta previa»
  superada el 16/08/2026; canal transaccional operativo (Resend + panel
  «Correos»).
- [~] **E4-008 — Definir roles mínimos: propietario, administrador, miembro y lectura.**
  Roles persistibles, bloqueo global de escritura para `lectura` y reglas de
  administración de equipo implementados; la matriz de capacidades por rol
  vive centralizada en `app/permisos.py` (E4-009) con pruebas automáticas;
  la verificación manual de la matriz por operación de negocio en la interfaz
  queda para el **día final de tests (D-019)**.
- [x] **E4-009 — Implementar autorización centralizada.**
  Completada el 16/08/2026 con `app/permisos.py`: única fuente de verdad de los conjuntos de roles y predicados (`puede_escribir`, `puede_gestionar`, `es_propietario`, `es_lectura`) y variantes que lanzan excepción; los checks inline de las rutas migraron a los predicados y una prueba estática impide que reaparezcan. La guardia de bajo nivel de SQLAlchemy (`app/models`) permanece como defensa en profundidad.
- [x] **E4-010 — Implementar recuperación de contraseña y verificación de email.**
  Recuperación implementada sobre Supabase, **validada end-to-end el
  14/08/2026** (email recibido, enlace a `/restablecer-clave`, cambio de
  contraseña e inicio de sesión) y cambio de contraseña desde `/cuenta` con
  reautenticación previa; emails de confirmación y recuperación reestilizados
  con la identidad de CotizaT (19/08/2026).
- [~] **E4-031 — Panel de cuenta de la persona usuaria.**
  `/cuenta` reúne perfil (nombre), cambio de contraseña, listado de organizaciones con la activa marcada y cierre de sesión; `/salir` revoca además la sesión en GoTrue. Falta cambio de email con reverificación, gestión de sesiones activas por dispositivo y eliminación de cuenta.
- [ ] **E4-011 — Evaluar segundo factor para administradores.**

## 4.3 Aislamiento multiempresa

- [x] **E4-012 — Añadir `organizacion_id` o estrategia equivalente a todos los datos empresariales.**
  Adelantada como E1W-005, incluidas entidades hijas.
- [x] **E4-013 — Aplicar filtrado obligatorio en la capa de datos.**
  SQLAlchemy lo aplica por eventos y `c93e7a4d20f1` versiona RLS por
  membresía/rol; **barrera PostgreSQL real activa en producción**: el login
  runtime es miembro no privilegiado de `cotizat_app` (`/readyz` lo verifica:
  `superuser=False, bypassrls=False, inherit=True`). El cruce manual entre dos
  organizaciones queda para el día final de tests (D-019).
- [x] **E4-014 — Evitar depender de que cada ruta recuerde filtrar manualmente.**
  El criterio se aplica mediante eventos SQLAlchemy y políticas RLS sobre cada
  modelo tenant, con inventario automático de aislamiento (E4-016). La
  validación manual de integración queda para el día final de tests (D-019).
- [~] **E4-015 — Crear pruebas automáticas de aislamiento para cada dominio.**
  Cobertura en `tests/test_tenancy.py`, `tests/test_storage.py` y
  `tests/test_rls.py`, incluidos metadatos, claves, proxy, cobertura de
  tablas/políticas y contexto parametrizado, más el inventario E4-016 sobre los
  29 modelos tenant; los cruces con PostgreSQL real entre dos organizaciones
  quedan para el día final de tests (D-019).
- [x] **E4-016 — Auditar acceso directo por identificadores.**
  Completado el 17/08/2026 con `tests/test_inventario_aislamiento.py`: inventario
  auto-mantenido que construye una instancia de **cada** modelo `TenantMixin`
  (los 29) en la organización A y comprueba desde B que `db.get(Modelo, id)`
  devuelve `None` para cada uno, con sanity de que en A sí resuelve. Si se
  añade un modelo nuevo sin incluirlo en el grafo, la prueba falla nombrándolo.
- [~] **E4-017 — Auditar archivos y URLs firmadas.**
  Objetos nuevos usan proxy privado y `/static/uploads` se bloquea en
  PostgreSQL. El 17/08/2026 se añadió la auditoría estática completa
  (`tests/test_auditoria_archivos.py`): recorre todo `app/` (Python,
  plantillas, JS y CSS) prohibiendo marcadores de URLs públicas/firmadas y
  enlaces directos al bucket, con regresión sobre `file_url` y
  `SupabaseStorage`. La decisión de **no** introducir URLs firmadas cortas por
  ahora queda documentada en `docs/ADR-002_URLS_FIRMADAS_ARCHIVOS.md`
  (propuesta, pendiente de confirmación del propietario). Falta únicamente la
  auditoría externa manual (confirmar en el navegador que la URL pública del
  objeto responde acceso denegado), agrupada en el **día final de tests
  (D-019)**.

## 4.4 Infraestructura

- [x] **E4-018 — PostgreSQL administrado.**
  Elegido **Supabase** (D-016) y **en producción**: esquema migrado, RLS
  activo y rol runtime limitado verificado por `/readyz`.
- [x] **E4-019 — Almacenamiento de objetos para imágenes, PDFs y anexos.**
  Backend y metadatos implementados como E1W-009; bucket privado
  `cotizat-private` **aprovisionado y verificado** (subida/descarga por proxy
  autorizado; la auditoría externa manual queda para el día final de tests,
  D-019).
- [ ] **E4-020 — Cola de trabajos para PDFs, emails e importaciones pesadas.**
  **APLAZADO por decisión del titular (19/08/2026, D-022).** En Vercel
  serverless no hay workers persistentes: una cola real exige infraestructura
  externa (p. ej. QStash o un worker aparte). Hoy todos los envíos son
  síncronos y caben en el `maxDuration` de 60 s, y el trabajo pesado
  periódico ya corre por el cron de mantenimiento. Disparadores que
  reabrirían el ítem: PDFs que superen el timeout, importaciones de Excel que
  fallen por tiempo, o envíos masivos. No bloquea el lanzamiento.
- [x] **E4-021 — Backups automáticos y restauraciones ensayadas.**
  **Completado el 19/08/2026 (código)** con `app/services/mantenimiento.py` y
  el cron `/api/cron/mantenimiento`: respaldo automático por organización
  (mismo paquete verificable de E3-020) guardado en el bucket privado bajo
  `organizaciones/<id>/respaldo_automatico/` con retención configurable
  (`COTIZAT_RESPALDO_RETENCION`, 14 por omisión; `COTIZAT_RESPALDO_MAX_MB`),
  sin registrar los zips como archivos (evita crecimiento autorreferencial) y
  sin romper el barrido si una organización supera el límite. La restauración
  ya estaba ensayada (E3-021). **Complemento de panel pendiente**: backups
  automáticos de Supabase Pro (base + Storage) y `application/zip` en los MIME
  permitidos del bucket (`docs/PENDIENTES_OPERATIVOS.md` §11). Cubre R-011.
- [x] **E4-022 — Logs estructurados sin datos sensibles innecesarios.**
  Completado el 16/08/2026 con `app/logs.py`: modo JSON opt-in (`COTIZAT_LOG_JSON=true`, apagado por omisión), idempotente, y redacción de credenciales embebidas en URLs tanto en mensajes como en trazas de excepción.
- [x] **E4-023 — Monitorización, alertas y seguimiento de errores.**
  **Completado el 19/08/2026 (código)**: el cron `/api/cron/mantenimiento`
  ejecuta la verificación diaria de `/readyz` y, si falla, envía el correo
  interno `alerta_operador` a todos los operadores (`COTIZAT_OPERADORES`) con
  los errores y el estado de cada chequeo (sin secretos). El seguimiento de
  errores no capturados ya existía (E3-024). **Complemento de panel
  pendiente**: vigilante externo de disponibilidad (p. ej. UptimeRobot sobre
  `/healthz`, cada 5 min) — pasos en `docs/MONITORIZACION_Y_DIAGNOSTICO.md`
  §6b y `docs/PENDIENTES_OPERATIVOS.md` §11. Cubre R-009/R-011.
- [x] **E4-024 — Entornos separados de desarrollo, pruebas y producción.**
  Staging (`cotizat-generador.vercel.app`) y producción (`cotizat.online`)
  operativos, con variables por entorno en Vercel y CI como puerta.
- [x] **E4-025 — Despliegues repetibles y reversibles.**
  Vercel: cada `git push` genera despliegue; redeploy y rollback desde el
  panel; CI bloquea fusiones rotas. `docs/DESPLIEGUE_VERCEL.md`.

## 4.5 Auditoría y seguridad

- [x] **E4-026 — Registro de quién cambió precios, documentos y estados.**
  **Completado el 19/08/2026** con la tabla inmutable `eventos_auditoria`
  (migración `d2a7c9e4f1b3`): estados de presupuestos y facturas (de → a),
  envío por email, enlaces públicos creados/revocados, precios de catálogo
  (partida/producto/recurso y ajuste masivo), configuración y renombre de la
  organización, con actor, rol y fecha. RLS: INSERT tenant, SELECT tenant u
  operador, **sin GRANT de UPDATE/DELETE** (inmutable por construcción). El
  registro es best-effort (`app/services/auditoria.py`): jamás rompe el flujo
  principal. Vista «Actividad» (`/configuracion/actividad`) para
  propietario/administrador. La misma migración corrige un bug latente de la
  baja (no borraba `compras_plan` y la FK RESTRICT la bloqueaba).
- [x] **E4-027 — Historial de sesiones y acciones sensibles.**
  **Completado el 19/08/2026** sobre la misma tabla: inicio y cierre de
  sesión y cambio de contraseña (eventos globales sin organización, vía
  función SECURITY DEFINER `registrar_evento_global` con lista cerrada de
  acciones; solo los ve el operador), gestión del equipo (invitación
  enviada/revocada, rol cambiado, miembro desactivado), respaldo descargado,
  exportación descargada, restauración ejecutada, compra registrada y
  constancia de la baja de la organización.
- [~] **E4-028 — Política de contraseñas y bloqueo de intentos.**
  Rate limiting local de intentos (10/5 min por IP) y reglas de Supabase Auth
  activas; falta formalizar la política y evaluar 2FA (E4-011).
- [x] **E4-029 — CSRF, XSS, CSP, validación de archivos y rate limiting revisados.**
  CSRF (Origin/Referer + Fetch Metadata), cabeceras defensivas, límites/MIME,
  **rate limiting distribuido activo con Upstash** (`/readyz`:
  `distribuido:upstash`) y CSP sin `unsafe-inline` implementados y con
  regresión. Validación HTTPS independiente → cubierta por E4-044/auditoría
  externa del día final de tests (D-019).
- [x] **E4-030 — Escaneo de dependencias y secretos en CI.**
  **Completado el 19/08/2026**: `pip-audit` sobre `requirements.lock`
  (dependencias vulnerables) y `detect-secrets` con baseline versionado
  `.secrets.baseline` (secretos; falla ante cualquier hallazgo nuevo) como
  pasos del flujo de CI (`docs/ci/ci.yml`, protegidos por
  `tests/test_integracion_continua.py`). Las herramientas se fijan en
  `requirements-dev.txt` (E1-037).
- [ ] **E4-044 — Auditoría externa o revisión independiente antes del lanzamiento público.**
  Pendiente (renumerado desde E4-031 el 19/08/2026 por colisión de ID con el
  panel de cuenta). Incluye la auditoría externa del bucket privado; se
  agrupa en el día final de tests (D-019).
- [x] **E4-032 — Plan de respuesta a incidentes.**
  **Completado el 19/08/2026** (documentación): `docs/PLAN_DE_RESPUESTA_A_INCIDENTES.md`
  con severidades S1–S4, canales de detección, runbooks por severidad,
  contactos y «qué no hacer». Se revisa en el simulacro E4-043 y tras cada
  incidente S1/S2; la primera revisión práctica queda agrupada en el día
  final de tests (D-019).

## 4.6 Suscripciones y administración

- [x] **E4-033 — Definir planes según valor, no por acumulación arbitraria de funciones.**
  Planes de piloto definidos y publicados (E1-057): 89 US$/año promocional
  (habitual 109) o 9,99 US$/mes el primer año (habitual 12,99), con la prueba
  gratuita de 7 días sin tarjeta (E1-062).
- [~] **E4-034 — Integrar un medio de cobro legalmente disponible para la empresa operadora.**
  **Cobro manual operativo** (transferencia, Zelle, Binance, Pago Móvil) con
  activación desde el panel. El cobro recurrente (Stripe + autónomo en España,
  modelo 036/RETA) está decidido como vía «en serio» y queda para cuando el
  volumen lo justifique (`docs/COBRO_Y_LICENCIAS.md`).
- [x] **E4-035 — Implementar prueba, alta, renovación, gracia, suspensión y cancelación.**
  Completado en E1-060/E1-062: prueba gratuita 7 días (anti-reciclaje por
  email normalizado + bloqueo de correos desechables), alta, renovación con
  encadenamiento, gracia y suspensión sin borrar datos, cancelación con
  constancia; recordatorios automáticos a 5 y 1 día operativos (cron,
  19/08/2026).
- [x] **E4-036 — No eliminar automáticamente datos al fallar un pago.**
  La suspensión corta el acceso pero **no toca datos**: al renovar todo
  vuelve. Verificado en `tests/test_licencias_acceso.py`.
- [x] **E4-037 — Crear panel interno de soporte y administración.**
  `/admin`: licencias (concesión, renovación, recibo PDF), compras (revisión y
  activación), correos (envío de prueba de los 8 correos) y operación
  (chequeos de `/readyz` + errores acotados).
- [x] **E4-038 — Registrar consentimiento de términos y privacidad.**
  **Completado el 19/08/2026 (código)**: checkbox obligatorio en el registro,
  tabla `consentimientos` (email normalizado, versión, nombre, IP con hash,
  fecha; unicidad email+versión; RLS de operador como `licencias`) con las
  funciones SECURITY DEFINER `cotizat_security.record_consent` y
  `cotizat_security.obtener_consentimiento`, y marca `usuarios.acepto_terminos_*`
  visible en `/cuenta` (con aceptación explícita para cuentas anteriores a la
  función). La versión aceptada es la declarada en `app/legal.py` (1.1) y
  mostrada en la propia página de términos, para que registro y documento no
  puedan divergir. **Pendiente de titular**: aplicar
  `docs/staging_upgrade_b6d9e4c2a8f1.sql` en Supabase (paso en
  `docs/PENDIENTES_OPERATIVOS.md` §12).

## 4.7 Migración y beta

- [ ] **E4-039 — Diseñar importación desde la versión de escritorio.**
  Pendiente; el escritorio convive en el mismo repositorio y comparte modelo,
  así que el diseño será sencillo. Se hace con el día final de tests (D-019).
- [ ] **E4-040 — Probar migraciones con copias anonimizadas de bases reales.**
  Pendiente; requiere una base real de la que tomar una copia anonimizada.
- [ ] **E4-041 — Ejecutar beta cerrada con 5–10 empresas.**
  Pendiente; depende de que el titular declare completo el producto (D-017).
- [ ] **E4-042 — Realizar prueba de carga realista.**
  Pendiente; sin tráfico aún no hay objetivo medible.
- [~] **E4-043 — Realizar simulacro de caída y recuperación.**
  Procedimiento definido el 19/08/2026 en
  `docs/SIMULACRO_CAIDA_Y_RECUPERACION.md` (escenario, pasos, criterios de
  éxito y acta). Falta la **ejecución** por el titular: primera pasada
  recomendada antes del día final de tests (D-019), con datos de la
  organización de pruebas real.

## 4.8 Criterios de salida de la Etapa 4

- [ ] Ninguna consulta o archivo puede cruzar organizaciones en las pruebas.
  Cubierto automáticamente (E4-016 + `test_rls.py`); el cruce manual entre dos
  organizaciones queda para el día final de tests (D-019).
- [ ] Roles y permisos están cubiertos automáticamente.
  Cubierto por `app/permisos.py` y sus pruebas; la verificación manual por
  operación de negocio queda para el día final de tests (D-019).
- [~] Backups y restauración cumplen el objetivo definido.
  Restauración ensayada (E3-021) y respaldo automático por organización
  (E4-021) en código; falta el simulacro E4-043 y el complemento de
  infraestructura (backups Supabase Pro — panel).
- [~] Monitorización y respuesta a incidentes funcionan.
  Verificación diaria con alerta (E4-023) en código; falta el vigilante
  externo (panel) y el plan de incidentes E4-032.
- [ ] Alta, pago, gracia, cancelación y exportación fueron probados.
  Funcionalmente completos; la prueba end-to-end real queda para el día final
  de tests (D-019).
- [ ] La beta cerrada fue estable y aprobada.
  Pendiente; depende de D-017.
- [ ] Existe documentación legal y operativa.
  Mayormente sí (términos, privacidad, soporte, guías); falta E4-038
  (consentimiento registrado) y E4-032 (plan de incidentes).

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
- [~] **E5-012 — Telemetría mínima, agregada y voluntaria para conocer uso de funciones.**
  En curso (28/08/2026, decisión D-023): implementada la **parte de servidor** — tabla
  `eventos_producto` (migración `e3a5c7d9b1f4`, hermana de `eventos_auditoria`:
  inmutable, sin IP, detalle sin datos sensibles), servicio
  `app/services/telemetria.py` (catálogo cerrado de 12 acciones, best-effort),
  latido diario por organización en `get_db`, eventos en los momentos del
  embudo (registro, alta de empresa, presupuesto creado/aprobado/enviado, PDF,
  importación CYPE/BC3, compra, checkout Stripe, licencia activada, invitación)
  y panel de operador `/admin/analitica` (KPIs, embudo, series diarias,
  cohortes de retención, uso de funciones, riesgo de churn, eventos recientes).
  Cubierto por `tests/test_telemetria.py` y `tests/test_panel_analitica.py`.
  Complementa a GA4 (que sigue midiendo la capa pública); no usa cookies ni
  terceros, por lo que no exige consentimiento adicional al registrado (E4-038).
  Pendiente de E5-012: revisar las métricas con datos reales de la beta y
  decidir si alguna función necesita eventos más finos.

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
| R-002 | El producto abruma al usuario de papel/Excel | Alta | Alta | Onboarding y pruebas observadas | Mitigado inicialmente en público de construcción; reevaluar en pilotos |
| R-003 | Partidas sin derechos de redistribución | Media | Crítico | Auditoría de procedencia | **Cerrado (19/08/2026): E1-022 — catálogo 100 % de autoría propia, con auditoría de evidencia** |
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
| Piloto fundador anual | **89 US$/año promocional (habitual 109)** — publicado (E1-057) | Publicado, sin validar (Etapa 2) |
| Piloto mensual | **9,99 US$/mes el primer año (habitual 12,99)** — publicado (E1-057) | Publicado, sin validar (Etapa 2) |
| Licencia local perpetua | 79–149 USD | Descartada como prioridad por D-014 |
| Renovación de soporte/catálogo | 30–60 USD/año | Sin validar |
| Futuro plan web profesional | 19–29 USD/mes | Sin validar |
| Tiempo máximo al primer PDF | 20 minutos | Validado inicialmente: público de construcción ≈10 min y sin ayuda (16/08/2026) |
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
| 13/08/2026 | D-008 | Exigir pilotos pagados antes de escalar la operación SaaS | Decisión histórica sustituida por D-017 | Sustituida el 16/08/2026 |
| 13/08/2026 | D-009 | Crear una marca para construcción latinoamericana, especializada inicialmente en remodelación venezolana | Permite crecer por país y función sin diluir el mensaje comercial de entrada | Tras la selección final de nombre |
| 13/08/2026 | D-010 | Adoptar **CotizaT** como nombre comercial | El usuario priorizó comprensión inmediata y aprobó expresamente el nombre | Tras revisión marcaria profesional |
| 13/08/2026 | D-011 | Usar la propuesta «Convierte tu catálogo y tus precios en presupuestos de obra claros, editables y listos para presentar» | Es verificable con el producto actual y no promete resultados financieros | Después de pruebas comerciales |
| 13/08/2026 | D-012 | Renombrar ejecutable e instalador, manteniendo compatibilidad automática con la carpeta histórica de datos | Aplicar la marca sin hacer desaparecer bases, imágenes ni backups existentes | Después de probar actualización en Windows |
| 13/08/2026 | D-013 | Sustituir la siembra automática por una elección explícita entre demo y limpio | Evitar datos y precios inesperados, y respetar a quien importará un catálogo propio | Después de pruebas de usabilidad |
| 13/08/2026 | D-014 | Desarrollar CotizaT browser-first y pausar nuevas inversiones de escritorio | El producto final será alojado; adelantar persistencia y aislamiento evita reescribir cada módulo | Después de la beta web privada |
| 13/08/2026 | D-015 | Adelantar organizaciones y aislamiento, pero no confundirlos con preparación para publicar | La propiedad de datos debe existir antes de ampliar funciones; autenticación, archivos y seguridad siguen pendientes | Al completar E1W-007 a E1W-011 |
| 13/08/2026 | D-016 | Adoptar Supabase inicialmente para PostgreSQL, Auth y Storage, manteniendo abstraído el almacenamiento | Reduce integraciones en la beta; PostgreSQL real, RLS y persistencia ya se validaron, sin impedir migrar objetos a R2 | Tras medir límites/coste en pilotos |
| 16/08/2026 | D-017 | Completar el producto antes de ejecutar validación comercial pagada | El titular no considera útil entregar a terceros un generador que aún perciba incompleto; catálogo comercial y pilotos se dejan para el final | Cuando el titular declare cerrado el producto |
| 19/08/2026 | D-018 | La estimación de tiempos (horas, días, plazos) **nunca se imprime en el PDF del cliente** | El desglose de horas es información interna con ventaja comercial; exponerlo invita a reclamaciones («el papel dice 5 h y se hizo en 2»). Solo vive en la app; si algún día se imprime, sería una versión interna para la empresa | Si el titular decide publicar plazos comerciales |
| 19/08/2026 | D-019 | Agrupar **toda** la validación de tipo prueba en un día final único de solo tests | Hacer las pruebas por etapas y repetirlas al cierre sería trabajo doble. Incluye: matriz de aceptación manual, cruces con dos correos y dos organizaciones, primer alta real con el corte, auditoría externa del bucket, invitación sin cuenta previa y recordatorio real | Cuando el titular lo indique |
| 19/08/2026 | D-020 | El catálogo de partidas propio (3.006) **es el catálogo del producto**; los `.xlsx` de ejemplo no aportan contenido | E1-022 cerrado con evidencia: autoría 100 % propia; el trabajo pendiente es crecimiento (≈5.000 partidas) y precios B2B, no sustitución | En la carga final de contenido |
| 19/08/2026 | D-021 | **No implementar** el registro de apertura de correos/enlaces (E3-025) | Requeriría tratamiento legal del consentimiento y aporta poco frente al coste en el piloto manual | Si se abre beta automatizada con métricas de conversión |
| 28/08/2026 | D-023 | Adelantar la **telemetría interna de producto** (E5-012) en su variante de servidor, a petición del titular | GA4 solo ve la capa pública y pierde conversiones por bloqueadores; el plan necesita retención y activación medidas con dato propio. Se implementó como eventos agregados sin IP ni cookies (no amplía el tratamiento registrado en E4-038) | Con los primeros datos de la beta se revisan las métricas y se decide si hacen falta eventos más finos |

---

# 10. Registro de evidencia comercial

Se completará durante la Etapa 2. No deben guardarse aquí nombres, teléfonos ni datos sensibles sin autorización.

| Fecha | Tipo | Segmento | Hallazgo | Evidencia anonimizada | Acción |
|---|---|---|---|---|---|
| 16/08/2026 | Prueba de usabilidad | Profesionales de construcción y personas externas | El público objetivo completó presupuestos sin ayuda; varios baños genéricos en ≈10 min; sin errores observados. Personas sin conocimientos de construcción tardaron más, fuera del nicho prioritario. | Informe verbal anonimizado del titular | Mantener el recorrido; continuar la terminación técnica y dejar la validación comercial para el final (D-017) |
| 18/08/2026 | Lanzamiento público de la prueba gratuita | Público general (landing) | Se anuncia la prueba de 7 días sin tarjeta en `/`, `/conocer`, `/pago` y `/acceso` y se enciende el corte por licencia; el circuito de cobro completo queda operativo (registro → prueba → recordatorio → pago → renovación). | Verificado en producción vía `/readyz` | Esperar el primer alta real para la validación comercial (D-017); pruebas E2E agrupadas en el día final (D-019) |
| 19/08/2026 | Auditoría técnica | Repositorio | E1-022 cerrado: catálogo 100 % de autoría propia (0 coincidencias con los `.xlsx` de ejemplo); E4-030 implantado (escaneo de dependencias y secretos en CI). | `docs/DATOS_SENSIBLES.md` §6; `docs/ci/ci.yml` | Reducen R-003 y añaden guardas de regresión para R-009/R-011 |

---

# 11. Próximo bloque de trabajo

## Estado actual (19/08/2026): Etapa 3 cerrada y Etapa 4 en curso

La continuidad operativa exacta está en `docs/PUNTO_DE_CONTINUACION.md` y el
estado de infraestructura en `docs/CONTINUIDAD_STAGING_SUPABASE.md`.

**Decisiones del titular (16/08/2026, matizadas el 19/08/2026):**

1. **Etapa 1 completada.** PR #25 fusionado, licencias funcionando, usabilidad
   superada por profesionales de construcción y presupuestos de baño en unos
   10 minutos sin errores observados.
2. **Catálogo propio como producto (D-020).** El catálogo (3.006 partidas) es
   100 % de autoría propia (E1-022 cerrado con evidencia) y es el catálogo del
   producto; los `.xlsx` de ejemplo solo definen el formato de importación.
   El trabajo pendiente es crecimiento (≈5.000 partidas) y precios B2B.
3. **Validación comercial aplazada hasta el final (D-017).** No se harán
   pilotos ni se entregará a clientes una versión que el titular considere
   incompleta.
4. **Toda la validación de tipo prueba se agrupa en un día final único**
   **(D-019, 19/08/2026):** matriz de aceptación manual, cruces con dos
   correos y dos organizaciones, primer alta real con el corte, auditoría
   externa del bucket, invitación sin cuenta previa y recordatorio real.

**Siguiente bloque recomendado (Etapa 4):**

1. ✅ **E4-021 — Backups automáticos** y ✅ **E4-023 — Alertas**: completados en
   código el 19/08/2026 (cron `/api/cron/mantenimiento`: respaldo por
   organización + verificación diaria con correo). Quedan los **pasos de
   panel** (`docs/PENDIENTES_OPERATIVOS.md` §11): `application/zip` en el
   bucket, vigilante externo de disponibilidad (UptimeRobot) y backups de
   Supabase Pro.
2. **E4-030 — Escaneo de dependencias y secretos en CI**: completado el
   19/08/2026 (pip-audit + detect-secrets en `docs/ci/ci.yml`).
3. Con eso, el **día final de tests (D-019)** cuando el titular lo indique.

Histórico de bloques ya completados (se conserva como registro):

### Bloque completado: ciclo completo del presupuesto

El generador ya crea un PDF profesional. El salto funcional fue que CotizaT
gestionara también su entrega y cierre, en este orden (todo completado):

1. ~~**E3-016 — Envío por email del presupuesto.**~~ Completado el 16/08/2026
   con PDF adjunto, versión congelada y constancia; suite en verde.
2. ~~**E3-017 — Enlace público seguro y revocable.**~~ Completado el
   16/08/2026 con versión/PDF congelados, caducidad, revocación y RLS por hash.
3. ~~**E3-018 — Aceptación o rechazo con trazabilidad.**~~ Completado el
   16/08/2026, una sola respuesta con identidad declarada, fecha/hora y versión.
4. ~~**E3-019 — Notificación inmediata y estado controlado.**~~ Completado el
   16/08/2026 con aviso a administradores, transición solo de la última versión
   y reintento seguro ante fallos.

El ciclo completo del presupuesto E3-016 a E3-019 quedó terminado, y a
continuación se cerró la operación técnica (bloque siguiente, también
completado). Solo cuando el titular declare terminado el producto se retomará
la Etapa 2 de validación comercial.

### Bloque completado: restauración, exportación, baja y operación (16/08/2026)

1. ~~**E3-020 — Copia de seguridad web completa y verificable.**~~ Completado el
   16/08/2026: paquete `.zip` `cotizat-backup` v1 con manifest, conteos,
   omisiones declaradas y cada archivo bajo su SHA-256; funciona en PostgreSQL
   y SQLite; descarga solo para propietario/administrador.
2. ~~**E3-021 — Restauración controlada en dos pasos.**~~ Completado el
   16/08/2026: mismo archivo re-subido (SHA-256) + confirmación explícita;
   verificación íntegra antes de escribir; fusión idempotente por claves
   naturales (nada se borra ni se duplica); archivos re-escritos al almacén
   privado del destino con reutilización por huella; historial de propuestas
   conservado como notas; licencias, cuentas, invitaciones y enlaces quedan
   fuera con motivo declarado. Detalle operativo en
   `docs/RESPALDO_Y_RESTAURACION_WEB.md`. Suite: **423 passed, 6 skipped**.
3. ~~**E3-022 — Exportación por organización.**~~ Completado el 16/08/2026:
   paquete `cotizat-export` v1 con CSV por tabla (BOM UTF-8), archivos con
   nombre original y el respaldo verificable embebido; solo
   propietario/administrador; funciona en PostgreSQL y SQLite.
4. ~~**E3-023 — Baja por organización.**~~ Completado el 16/08/2026: solo el
   propietario, nombre exacto escrito + casilla explícita, archivos borrados
   antes de la base, borrado transaccional completo (datos, licencias,
   membresías y organización) con aislamiento entre tenants; función
   SECURITY DEFINER `cotizat_security.baja_organizacion` en PostgreSQL
   (migración `a3d7e9c1b5f2`, sin aplicar hasta el despliegue). Detalle en
   `docs/EXPORTACION_Y_BAJA_ORGANIZACION.md`. Suite: **441 passed, 6 skipped**.
5. ~~**E3-024 — Monitorización y diagnóstico.**~~ Completado el 16/08/2026:
   panel de operación `/admin/operacion` con los chequeos de `/readyz`,
   hechos operativos (backend, modo efímero, head de Alembic, almacenamiento,
   rate limit, licencias, operadores) y registro acotado en memoria de
   errores no capturados (sin query strings ni tokens, con agregación de
   ocurrencias); middleware que captura y relanza sin cambiar la semántica
   HTTP. Detalle en `docs/MONITORIZACION_Y_DIAGNOSTICO.md`. Suite:
   **453 passed, 6 skipped**.

Con E3-024 quedó terminado el cierre funcional y operativo de la Etapa 3
(envío, aceptación, recuperación, exportación/baja y operación), con sus
migraciones **aplicadas y verificadas en Supabase el 16/08/2026**. El código
**se desplegó en producción** (la Etapa 3 quedó cerrada el 19/08/2026;
`/readyz` responde `ok: true`) y se pasó al **endurecimiento técnico de la
Etapa 4**, que está en curso.

<details><summary>Histórico: bloque previo — validación con matriz de aceptación en staging (superado el 14-16/08/2026)</summary>

La base browser-first ya está desplegada en staging Vercel + Supabase (`https://cotizat-generador.vercel.app`), con `/healthz` y `/readyz` respondiendo 200 OK. El siguiente trabajo es:

1. **Matriz de aceptación (Sección 4 de CONTINUIDAD):** continuar los 14 puntos de prueba manual con dos correos y dos organizaciones en el entorno desplegado. Los puntos 1-9, 11 y 12 quedaron superados el 14/08/2026 (registro de A, Organización A, recuperación de contraseña, subida/descarga de archivos y PDF, invitación al Usuario B, rol `lectura` comprobado, ascenso a `miembro`, Organización B homónima sin fuga de datos, cookies HttpOnly/Secure y consola sin violaciones CSP).
2. **E1W-009 / E1W-011 — prioridad inmediata:** verificar la subida/descarga de imágenes, anexos PDF y fichas técnicas a través del proxy autorizado conectando con el bucket privado `cotizat-private`. Es el punto 4 de la matriz y la primera prueba real de `SupabaseStorage`, hasta ahora solo ejercitado contra una simulación REST.
3. **E1W-007 / E1W-008:** las invitaciones de equipo, el cambio de roles (`lectura` vs `miembro`), las cookies de sesión (HttpOnly/Secure/SameSite, `document.cookie` vacío) y la ausencia de violaciones CSP ya quedaron validados en navegador real el 14/08/2026 (puntos 6-8, 11 y 12 de la matriz). La recuperación de clave ya está validada.
4. **Infraestructura — hecho:** el rate limiting distribuido ya está implementado (`app/ratelimit.py`, backend Upstash Redis por REST con degradación a memoria). Para activarlo en staging solo faltan las variables `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` y `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` en Vercel; `/readyz` publica el estado en `checks.rate_limit`.
5. **E1-012 a E1-014:** este pendiente histórico fue superado posteriormente el 16/08/2026; la evidencia actual está en §1.2 y §10.

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

</details>

---

## Declaración final de enfoque

El objetivo inmediato no es construir la mayor cantidad posible de funciones. El objetivo es comprobar que una empresa venezolana de remodelación puede:

1. Entender el producto.
2. Crear un presupuesto profesional rápidamente.
3. Confiar en sus datos y cálculos.
4. Mantener sus precios y documentos seguros.
5. Obtener suficiente valor como para pagar y seguir utilizándolo.

Los fundamentos multiempresa se construyen desde ahora para evitar reescrituras; la inversión en escalabilidad, operación pública y automatización comercial solo se justificará con evidencia de uso y pago.
