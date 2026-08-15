# Punto exacto de continuación

Fecha de corte: **15/08/2026, noche (cierre de sesión)** (America/Caracas).

Este documento existe para retomar el trabajo desde una conversación nueva sin
depender del historial del chat. Describe **dónde nos quedamos exactamente** y
**qué es lo siguiente**, en ese orden.

Léelo junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging y
matriz de aceptación) y `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`
(secciones 1.3, 1.4, 1.8, 1.9 y 11).

---

## 1. Lo último que se hizo: el PR #20 (tres bloques en una sesión)

La rama `arena/01a0069a-generador-comercial` entregó tres bloques que el
usuario decidió **fusionar como PR #20** al cerrar la sesión del 15/08/2026.
Si estás leyendo esto desde `main`, el merge ya ocurrió. Contenido exacto:

### 1a. E1-040 — recorrido crítico cubierto `[x]` (commit `1b4571d`)

`tests/test_recorrido_critico.py`: 4 pruebas en subproceso contra una
instalación aislada (variable nueva `COTIZAT_DATA_DIR`, solo modo
desarrollo; el .exe la ignora):

1. instalación limpia → asistente → catálogo/cliente/presupuesto reales →
   PDF → backup .zip → pérdida → restauración (con copia previa automática
   en `backups/antes_de_restaurar_*`) → reinicio sin reinyección;
2. restaurar la copia de una versión anterior re-aplica migraciones;
3. backup automático semanal sin duplicados;
4. zip malicioso (zip slip) rechazado sin tocar la base.

El criterio «CI ejecuta las pruebas y el recorrido crítico está cubierto»
pasó a `[x]` en el plan.

### 1b. E1W-012 — importación de instalaciones SQLite `[x]` (commit `11d6e50`)

Cerró la última tarea técnica de la Etapa 1 web. Regla de oro respetada:
**nunca se migran datos privados sin acción y confirmación del propietario.**

- `app/services/instalacion_sqlite.py`: la fuente (.zip de backup o .db) se
  lee con `sqlite3` crudo en **solo lectura**, tolerando bases de versiones
  anteriores (columnas/tablas ausentes → defaults del modelo). El destino se
  escribe con la **sesión ORM del usuario autenticado**: tenencia, rol y RLS
  aplican como en cualquier otra escritura.
- Asistente en `/configuracion/importar-instalacion` con **dos pasos**:
  *analizar* (resumen honesto sin escribir nada) → *confirmar* (recarga del
  MISMO archivo, verificado por SHA-256, + casilla explícita). El servidor no
  guarda el archivo entre pasos → compatible con serverless.
- No migra datos demo ni configuración de empresa; limpia referencias a
  archivos locales avisando cuántas; reimportar no duplica; conflictos de
  número se listan antes de confirmar; solo propietario/administrador.
- 12 pruebas en `tests/test_instalacion_sqlite.py`.
- El criterio «exportación y migración controlada desde SQLite» pasó a `[x]`.

### 1c. Paquete legal/comercial (commit `e496fc1`)

Páginas públicas nuevas (sin sesión, declaradas en la auditoría de rutas,
CSP estricta):

| Ruta | Tarea | Contenido |
| --- | --- | --- |
| `/conocer` | E1-056 `[~]` | Landing: problema, resultado, público, llamada a demo por email y precios |
| `/legal/terminos` | E1-018 `[x]` | EULA/términos: licencia, datos del cliente, alcance no fiscal, responsabilidad, terminación |
| `/legal/privacidad` | E1-019 `[x]` | Privacidad con los encargados reales (Supabase, Vercel, Resend, Upstash, GoDaddy) |
| `/legal/soporte` | E1-019 `[x]` | Canal soporte@cotizat.online, horario UTC−4, tiempos, cómo reportar errores |
| `/legal/licencias` | E1-020 `[x]` | 42 paquetes verificados con `importlib.metadata`; Lato OFL, psycopg LGPL, PyInstaller con excepción |

Más: `docs/GUIA_INICIO_RAPIDO.md` (E1-050 `[x]`, ~5 páginas, recorrido
<20 min) y los **precios del piloto decididos por el usuario** (E1-057 `[~]`),
publicados en la landing:

- **89 US$/año** promoción inicial (precio habitual **109 US$/año**);
- **9,99 US$/mes** el primer año (precio habitual **12,99 US$/mes**).

Decisiones de diseño que no conviene reabrir sin motivo:

- La razón social se inyecta con `COTIZAT_LEGAL_ENTITY` (y el correo con
  `COTIZAT_SUPPORT_EMAIL`, por defecto `soporte@cotizat.online`) desde
  `app/branding.py`. Sin definir, los documentos muestran el marcador
  `[RAZÓN SOCIAL DEL TITULAR — pendiente de registro]`: es **a propósito**,
  imposible de publicar por accidente como entidad real.
- Jurisdicción neutral («ley del domicilio del titular»), elegida por el
  usuario mientras decide la entidad legal.
- `tests/test_paginas_publicas.py` (6 pruebas) incluye una de **honestidad
  publicitaria**: el precio promocional siempre aparece junto al habitual.
- La pantalla de acceso enlaza términos y privacidad al crear cuenta.

### Validación del usuario (15/08/2026, noche)

El usuario **probó las páginas nuevas y el resto de lo entregado y confirmó
que todo funciona correctamente**. Su valoración textual: necesita mejoras
claramente, pero está bien para ser la primera versión. Es decir: **v1
aceptada; iterar diseño/contenido después, sin rehacer la base.**

### Estado final de la sesión

- Suite: **284 passed, 5 skipped** (262 → 266 → 278 → 284).
- La rama incluye un merge de `origin/main` (`e1b0444`) que resolvió el
  conflicto de docs creado por el PR #21 (docs viejos de la rama anterior
  fusionados por el usuario); se conservó la versión más reciente.
- PR #20 `MERGEABLE` al cierre; **el usuario lo fusiona él mismo**.

---

## 2. Cerrado antes (no rehacer)

1. **Rate limiting distribuido** (PR #18, merge `7940ce9`): Upstash activo,
   `/readyz` → `"rate_limit": "distribuido:upstash"`.
2. **Dominio propio** `cotizat.online` (GoDaddy → Vercel; Supabase y
   `COTIZAT_PUBLIC_URL` apuntando al dominio). Guía en
   `docs/DOMINIO_COTIZAT_ONLINE.md`.
3. **Emails de invitación** (PR #19, merge `f686e80`): Resend con dominio
   verificado; producción confirma `"email": "configurado"` en `/readyz`.
4. **E1-040, E1W-012 y paquete legal/comercial** (PR #20, esta sesión).

---

## 3. Pendientes del usuario (operativos, sin código)

1. **Prueba E2E de invitaciones** (la hará él): `/equipo` → invitación real →
   correo desde `no-responder@cotizat.online` → aceptar y ver que se consume.
   Preguntarle si ya la hizo antes de dar el bloque de emails por cerrado
   del todo.
2. **Crear el buzón/redirección `soporte@cotizat.online`** (lo más simple:
   redirección en GoDaddy hacia su correo real). La landing y los legales ya
   lo publican.
3. **Definir la razón social** → añadir `COTIZAT_LEGAL_ENTITY` en Vercel
   (Production) y redeploy; el marcador desaparece solo.
4. Tras fusionar el PR #20: verificar en producción que
   `https://cotizat.online/conocer` y las 4 páginas `/legal/*` responden 200.

## 4. Aparcado por decisión del usuario

**Puntos 13-manual y 14 de la matriz de aceptación** — no pedirlos hasta que
el desarrollo esté cerrado (guía en `docs/MATRIZ_PASOS_MANUALES.md`).

---

## 5. Qué es lo siguiente

En orden recomendado:

1. **E1-052 — presupuesto de muestra comercial** sin datos personales reales
   (alimenta la landing con el «PDF de ejemplo» que le falta a E1-056).
2. **E1-051 — vídeo de demostración de 5 minutos** (operativo del usuario;
   la landing lo enlazará donde corresponda).
3. **E1-021 — revisar que el repositorio no contenga datos reales sensibles.**
4. **E1-059/E1-060 — método de cobro + recibo/contrato firmable y registro
   interno de licencias** (cierra E1-057 y el criterio «guía, oferta,
   contrato y soporte»).
5. Iterar diseño/contenido de landing y legales (v1 aceptada con mejoras
   pendientes declaradas por el usuario).

Criterios de salida de Etapa 1 aún abiertos: primer PDF en <20 min por usuario
nuevo, catálogo con procedencia y precios fechados, recibo/registro de
licencias, tres pruebas de usabilidad externas.

## 6. Aviso de plan que conviene tener presente

El plan **Hobby de Vercel prohíbe el uso comercial**. La landing ya publica
precios: antes de **cobrar** al primer cliente hay que pasar a **Pro
(20 $/mes)**. Al cerrar la matriz completa: retirar del `README.md` (línea 14)
el aviso de «todavía no debe publicarse».

---

## 7. Reglas invariables (no negociables)

- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue;
- si staging falla, corregir el problema observado **sin relajar** CSRF, CSP,
  RLS, bucket privado ni la exigencia del rol limitado;
- usar solo datos ficticios en las pruebas de la matriz;
- toda dependencia nueva exige pin `==` en `requirements.txt` más
  `python tools/generar_lock.py`, o falla `tests/test_dependencias_bloqueadas.py`.

Nota operativa: el token de la app que abre cambios automáticos carece del
permiso `workflows`; `docs/ci/ci.yml` existe como copia y el workflow se
instaló manualmente.

Nota de entorno: el `.venv` no persiste entre sesiones (recrearlo es normal) y
el HEAD local puede aparecer retrocedido al inicio de una sesión nueva; si los
archivos están intactos, basta `git fetch origin <rama>` + `git reset --mixed
FETCH_HEAD` para realinear sin perder nada.

---

## 8. Mensaje para iniciar la conversación nueva

Copiar tal cual, sin añadir secretos ni tokens:

---

Continúa el proyecto CotizaT. Antes de proponer nada, lee
`docs/PUNTO_DE_CONTINUACION.md` y luego `docs/CONTINUIDAD_STAGING_SUPABASE.md`.
No repitas trabajo ya hecho y no me pidas secretos.

**Dónde quedó todo (15/08/2026, cierre de sesión).**

- **Fusioné yo mismo el PR #20** («docs + E1-040 + E1W-012 + paquete
  legal/comercial», rama `arena/01a0069a-generador-comercial`, HEAD
  `e1b0444`). Con él quedan en `main`: el recorrido crítico cubierto
  (E1-040 `[x]`), la importación de instalaciones SQLite hacia la web
  (E1W-012 `[x]`, asistente en `/configuracion/importar-instalacion`) y el
  paquete legal/comercial: landing `/conocer` con mis precios (89 US$/año
  promo, habitual 109; 9,99 US$/mes primer año, habitual 12,99), páginas
  `/legal/terminos`, `/legal/privacidad`, `/legal/soporte`,
  `/legal/licencias` y `docs/GUIA_INICIO_RAPIDO.md`.
- **Ya probé las páginas nuevas y lo demás: todo funciona.** Necesita mejoras
  claramente, pero está bien como primera versión. No rehacer nada; las
  mejoras de diseño/contenido se iteran después.
- Bloques cerrados antes y verificados en producción: rate limiting
  distribuido (Upstash), dominio `cotizat.online`, emails de invitación por
  Resend (`/readyz` con `"email": "configurado"`).
- Suite al cierre: **284 passed, 5 skipped**.

**Empieza por verificar el estado real, no te fíes de este resumen:**

1. `git log --oneline -5` y `git status --short` — el merge del PR #20 debe
   estar en `main`. (Si el HEAD local aparece retrocedido con archivos
   intactos: `git fetch` + `git reset --mixed FETCH_HEAD`, es un artefacto
   conocido del entorno.)
2. Recrea el entorno y corre la suite: `python3 -m venv .venv`,
   `.venv/bin/pip install -r requirements-dev.txt`, `.venv/bin/pytest -q`.
   Deben salir **284 passed, 5 skipped**.
3. Abre `https://cotizat.online/readyz` (debe seguir 200 con `"email":
   "configurado"` y `"rate_limit": "distribuido:upstash"`) y comprueba que
   `https://cotizat.online/conocer` y las 4 páginas `/legal/*` responden 200
   tras el despliegue del merge.

**Mis pendientes operativos (recuérdamelos, pero no los bloquees):** la
prueba E2E de invitaciones en `/equipo`; crear la redirección
`soporte@cotizat.online` en GoDaddy; definir la razón social y añadir
`COTIZAT_LEGAL_ENTITY` en Vercel.

**Aparcado por decisión mía:** los puntos 13-manual y 14 de la matriz, hasta
que el desarrollo esté cerrado. No pedirlos todavía.

**Siguiente bloque:** E1-052 (presupuesto de muestra comercial sin datos
reales, que además dará el «PDF de ejemplo» a la landing); después E1-021
(revisión de datos sensibles del repo) y E1-059/E1-060 (cobro + recibo/
contrato). Recordar: Vercel Hobby prohíbe uso comercial → pasar a Pro antes
de cobrar.

---
