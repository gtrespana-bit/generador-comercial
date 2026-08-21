# Auditoría técnica y de seguridad pre-lanzamiento — CotizaT

**Fecha:** 2026-08-21
**Alcance:** Código (`app/`), arquitectura, configuración, datos de catálogo, CI/CD y suite de pruebas.
**Método:** Revisión manual del código fuente, análisis estático dirigido (patrones de inyección, traversal, secretos, XSS, CSRF, autenticación, tenancy, rendimiento) y **ejecución completa de la suite de pruebas** (863 passed · **4 failed** · 7 skipped).

---

## 1. Nivel de Riesgo Global

> **Bajo–Medio** — el bloqueante de datos/CI detectado **ya está corregido**; quedan recomendaciones de endurecimiento y deuda técnica.

**Conclusión honesta y matizada:** este proyecto no se parece a la mayoría de los proyectos pre-lanzamiento que uno audita. La ingeniería de seguridad y arquitectónica es **excepcionalmente sólida y madura** (RLS en PostgreSQL, CSRF/CSP, tenancy, rate-limit distribuido, gestión de secretos, CI con `pip-audit` y `detect-secrets`). No encontré **ninguna vulnerabilidad de explotación trivial** (sin inyecciones SQL/NoSQL/comandos, sin secretos en repositorio, sin open-redirect, sin path traversal, sin XSS reflejado).

Durante la auditoría se encontró un **defecto de integridad de datos del catálogo** (título duplicado que hacía cargar 3005 en vez de 3006 partidas y dejaba el CI en rojo). **Este bloqueante fue corregido en esta sesión** y la suite completa vuelve a estar en verde (867 passed). Quedan recomendaciones de endurecimiento y deuda técnica descritas abajo.

---

## 2. Fallas Críticas (Bloqueantes)

### ✅ BLOQUEANTE 1 — Catálogo con integridad de datos rota y CI en rojo (4 tests) — **RESUELTO**

> **Estado: CORREGIDO en esta sesión.** Suite completa en verde (867 passed · 7 skipped). Detalle de la corrección al final de esta sección.

La suite de pruebas falla de forma **determinista** en 4 tests relacionados con el catálogo:

| Test | Falla |
|---|---|
| `test_auditoria_catalogo_lanzamiento.py::test_las_3006_partidas_y_6062_lineas_de_mano_de_obra_son_validas` | `assert resultado.errores == []` → el auditor reporta un error |
| `test_catalogo_propio.py::test_sembrar_catalogo_carga_arbol_numerico_completo` | `assert 3005 == 3006` (una partida menos) |
| `test_catalogo_propio.py::test_migrar_catalogo_prueba_elimina_antiguas_y_carga_propias` | cuenta de partidas distinta de la esperada |
| `test_catalogo_propio.py::test_modo_demo_carga_catalogo_propio` | `assert 3005 == 3006` |

**Causa raíz confirmada al ejecutar el auditor del catálogo** (`auditar_partidas()`):

```
errores: ['12.06.01.080: título vacío o duplicado']
```

La partida **`12.06.01.080` (Rodapié de piedra natural)** tiene el **campo de título vacío** en `basedatos_partidas/datos/partidas.csv` (línea 2189):

```
12.06.01.080;;Revestimientos y acabados;Rodapié de piedra natural.;...
           ^^  <- título vacío
```

Esto provoca que el sembrado de la base cargue **3005** en lugar de las **3006** partidas oficiales. Consecuencias reales de cara al lanzamiento:

- El **CI bloquea la fusión y el lanzamiento** mientras el gate esté roto.
- El **producto que se instala/despliega muestra un catálogo incompleto** (falta 1 partida del capítulo de Rodapiés), es decir, un cliente puede no encontrar una partida que el marketing anuncia.
- Existen además **avisos de calidad no bloqueantes** que el auditor ya detecta y que conviene revisar antes de publicar el número «3006/6062» en la landing: **875 partidas en 218 grupos APU exactamente duplicados**, 775 descripciones de menos de 120 caracteres, 33 recursos sin uso, y estado VE con 240 precios «provisionales».

**Acción realizada (2026-08-21):**

1. **Causa raíz:** el JSON `basedatos_partidas/datos/descompuestos/12.03.02.040.json` tenía un **error de copiado** — su `titulo` repetía "Rodapié de piedra natural." (de la partida `12.06.01.080`) en lugar de "Zócalo de piedra natural.", que es el título real en el CSV `partidas.csv` (fuente de verdad). Esa partida está en la sección **Enchapados de pared** (12.03.02) y la otra en **Rodapiés y remates de piso** (12.06.01): son dos partidas legítimas y distintas (distinto oficio: alicatador vs. colocador de pisos; distinto precio: 2.67 vs. 2.04).
2. **Corrección de datos:** se alineó el JSON con el CSV — `titulo` = "Zócalo de piedra natural.", y se unificaron `descripcion` y `producto_cliente.tipo` a "zócalo" (también estaban copiados como "rodapié").
3. **Corrección de código:** se eliminó del diccionario `_RENOMBRADOS_PATRON` en `app/services/catalogo_propio.py` el mapeo `"Zócalo de piedra natural." → "Rodapié de piedra natural."` (y su rama de reescritura de descripción). Ese mapeo, pensado para normalizar terminología, colisionaba ahora las dos partidas (las volvía a unir por nombre y violaba la unicidad `(organizacion_id, nombre)`). Se dejó un comentario explicando por qué no deben colisionar.
4. **Verificación:** el auditor `auditar_lanzamiento.py` pasa con **0 errores** (3006 partidas · 6062 líneas de mano de obra), y la suite completa vuelve a estar en verde.

> Nota: no hizo falta regenerar `salida/` — `catalogo_partidas.csv`, `catalogo_partidas.json` y `arbol_catalogo.json` ya se generan desde `partidas.csv` (que siempre estuvo correcto), así que ya reflejaban "Zócalo de piedra natural.".

---

## 3. Mejoras de Código y Estructura (recomendaciones)

> Las siguientes no son vulnerabilidades explotables hoy, pero son endurecimiento de seguridad y calidad recomendable. Enumeradas de mayor a menor prioridad.

### 🔶 A. Endurecimiento de autenticación y fuerza bruta
1. **El rate-limit de Auth solo cuenta por IP+ruta** (`AuthRateLimitMiddleware.DEFAULT_LIMITS`, solo métodos `POST`). Un ataque **distribuido** (botnet, o NAT corporativo que comparte IP) no se frena. Considera añadir una **segunda clave por cuenta/email** (hash del email) además de la IP, para que un mismo login atacado quede limitado aunque venga de muchas IPs.
2. **Verifica la configuración de `COTIZAT_TRUST_PROXY` y `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT` en el despliegue.** Detrás de Vercel (serverless), si `COTIZAT_TRUST_PROXY` queda en `false`, todas las peticiones ven la IP del borde y **el límite colapsa todo el mundo en un solo cubo** (falsos bloqueos 429 = auto-DoS). Si el rate-limit distribuido (Upstash) no está activado, en serverless cada invocación arranca el contador de cero y **el límite no existe en la práctica**. Ambos son "aviso" en `/readyz`, no bloquean, así que es fácil desplegar en un estado ineficaz o autodestructivo.
3. **Inconsistencia menor:** `confia_en_proxy()` acepta `"si"/"sí"` como verdadero, pero el middleware `AuthRateLimitMiddleware` en `main.py` solo acepta `1/true/yes/on`. Si alguien escribe `COTIZAT_TRUST_PROXY=si`, la IP de rate-limit y la IP de auditoría divergen. Unificar los criterios en una sola función.

### 🔶 B. Cookie y sesión
4. **`clear_auth_cookies` no marca `max_age=0`/`expires` en el borrado** (usa `delete_cookie` con `path/secure/httponly/samesite` pero sin `max_age`). En la mayoría de navegadores basta, pero añadir `max_age=0` y `expires` al borrar evita que una cookie persistente sobreviva en navegadores/UA con semántica laxa.
5. **Caché de identidad tras el refresh:** `identity_for_request` guarda en caché también el **access token viejo (ya caducado)** (`_guardar_identidad_en_cache(access_token, identity)`). Inofensivo (el cache busca el hash del token viejo que ya no vuelve a usarse), pero es basura que ocupa entradas de la caché de 512; se puede eliminar.

### 🔶 C. Privacidad / datos sensibles
6. **El email aparece en el resumen del recordatorio del cron** (`_resumen_recordatorios` incluye `organizaciones` por nombre, pero `resultado` internamente maneja emails; el resumen ya los filtra — bien). Revisar que **los logs de error** (`traceback.format_exc()`) nunca capturen cuerpos de formulario con comprobantes/emails en producciones con `COTIZAT_LOG_JSON`.
7. **`COTIZAT_HASH_SALT` por defecto = `SUPABASE_SECRET_KEY`.** Es un compromiso razonable (la IP del alta se guarda hasheada), pero el `.env.example` ya lo documenta. Asegurar que en prod la sal sea **una variable independiente** y no se reutilice la misma clave para dos propósitos.

### 🔶 D. Robustez de archivos
8. **`descargar_archivo_legado_privado`** valida bien traversal (`..`, `//`, fuera de `UPLOADS_DIR`), pero normaliza `\` → `/`. Es correcto y no explotable; mantener esa validación tal cual al añadir cualquier nueva ruta de archivo.
9. **El montaje `StaticFiles` de `/static/uploads` solo existe en SQLite** (web devuelve 404 y usa el proxy `/archivos/...`). Correcto; no regresar a servir subidas por estático en el despliegue web.

### 🔶 E. Arquitectura y deuda técnica
10. **`desktop.py` y el flujo SQLite conviven con la web.** El feature-flag por `DATABASE_IS_SQLITE` está bien aislado, pero genera ramas en casi todos los routers (`if postgresql ... else ...`). Es la mayor deuda de mantenibilidad: conviene encapsular esas bifurcaciones en servicios (`SECURITY DEFINER` vs objeto directo) ya hecho en `propuestas.py`, y replicar ese patrón en el resto.
11. **Falta un linter/type-check en CI.** El CI cubre pruebas, lock, secretos, plantillas, JS y compilación, pero **no corre `ruff` ni `mypy`/`pyright`**. Hay `noqa` dispersos y comentarios `# type: ignore`. Añadir `ruff check` y un type-check suave detectaría clases de bugs antes de mergear.
12. **`form-action` y CSP con nonce por petición** están muy bien. Único matiz: CSP se emite para **toda** la app (incluida la API JSON). Es aceptable, pero si el volumen crece, considera aplicar CSP fuerte solo a las respuestas HTML y dejar cabeceras más laxas en la API interna (reduciría CPU sin riesgo).

### 🔶 F. Rendimiento / escalabilidad
13. La arquitectura ya aborda los cuellos de botella típicos: **caché de identidad por token** (`COTIZAT_AUTH_CACHE_TTL`), **TTL de sincronización de `/recursos`**, GZip con exclusión de binarios, `pool_pre_ping`, `s-maxage`/`stale-while-revalidate` en estáticos. Bien.
14. **Observación de escalabilidad:** en serverless, la caché de identidad es **por invocación/proceso**, así que con TTL alto solo acelera dentro de un proceso cálido; con TTL `0` cada página paga un viaje a GoTrue. Mantener TTL entre 60–180 s es el equilibrio correcto (el valor por defecto 180 es razonable).
15. **El catálogo se lee como estático** (`cifras_catalogo()` cacheado) y no desde la DB — buena decisión de rendimiento para la landing.

---

## 4. Plan de Acción (ordenado del 1 al 5)

### Paso 1 — Arreglar la integridad del catálogo y dejar el CI en verde (URGENTE) — ✅ HECHO
- [x] Corregir el **título duplicado** de la partida `12.03.02.040` (JSON alineado con `partidas.csv`: "Zócalo de piedra natural.") y eliminar el mapeo `_RENOMBRADOS_PATRON` que colisionaba ambas partidas.
- [x] Re-auditar (`auditar_lanzamiento.py`) → **0 errores** (3006 partidas · 6062 líneas de mano de obra).
- [x] Ejecutar `pytest -q` → **867 passed, 7 skipped, 0 failed**.
- [ ] Revisar los avisos de calidad (875 duplicados en APU, 775 descripciones cortas, 33 recursos sin uso, 240 precios VE «provisionales») y decidir si se publican los números exactos «3006/6062/388» en la landing.

### Paso 2 — Verificar la configuración de seguridad del despliegue de producción
- [ ] Confirmar en el panel del despliegue: `COTIZAT_ENV=production`, `COTIZAT_TRUST_PROXY=true` (detrás de Vercel), `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` **con** `UPSTASH_REDIS_REST_URL/TOKEN` reales.
- [ ] Confirmar que `/readyz` responde 200 en producción y que `rate_limit=distribuido:upstash`, `rol_runtime` sin `SUPERUSER/BYPASSRLS`.
- [ ] Confirmar cookies `Secure` (`COTIZAT_COOKIE_SECURE=true`) y `CRON_SECRET`/`STRIPE_WEBHOOK_SECRET` generados y distintos.

### Paso 3 — Endurecer la autenticación
- [ ] Añadir una **clave de rate-limit por email normalizado** además de por IP (mitiga fuerza bruta distribuida/NAT).
- [ ] Unificar `confia_en_proxy()` con la bandera del middleware de rate-limit (eliminar la divergencia `si/sí`).
- [ ] Añadir `max_age=0`/`expires` en `clear_auth_cookies` y limpiar la caché del token viejo tras el refresh.

### Paso 4 — Cerrar la deuda de calidad de código
- [ ] Añadir **`ruff` y un type-check (pyright/mypy)** al pipeline de CI.
- [ ] Reducir las bifurcaciones `if sqlite/postgres` moviéndolas a servicios (patrón ya usado en `propuestas.py`).
- [ ] Revisar que los logs de error en producción (`traceback.format_exc()`) no capturen datos personales/comprobantes.

### Paso 5 — Pruebas de aceptación y monitoreo pre-lanzamiento
- [ ] Ejecutar el recorrido crítico completo (registro → alta de empresa → crear presupuesto → importar CYPE → compartir propuesta pública → pago) en **staging** con la misma configuración que prod.
- [ ] Verificar el funcionamiento del **webhook de Stripe** y los **2 crons de Vercel** (recordatorios + mantenimiento/respaldo) con logs en verde.
- [ ] Dejar activo el monitoreo de `/healthz` y `/readyz` con alerta al operador antes del primer día de lanzamiento.

---

## Resumen ejecutivo

| Criterio | Veredicto |
|---|---|
| **Vulnerabilidades OWASP / inyección** | ✅ Sin hallazgos explotables (SQL/NoSQL/comandos/XXE/XSS reflejado/open-redirect/traversal) |
| **Autenticación / autorización / tenancy** | ✅ Muy fuerte (Supabase Auth, RLS + SECURITY DEFINER, cookies HttpOnly, CSRF, rate-limit distribuido) |
| **Gestión de secretos** | ✅ Sin secretos reales en repo; baseline `detect-secrets` + `pip-audit` en CI |
| **Integridad de datos de catálogo** | ✅ **CORREGIDO:** partida `12.03.02.040` con título corregido (Zócalo de piedra natural.); catálogo carga 3006/3006 y **CI en verde** |
| **Rendimiento / escalabilidad** | ✅ Buenas prácticas ya aplicadas (caché, TTL, GZip, pool); verificar rate-limit distribuido en serverless |
| **Calidad / deuda técnica** | 🟡 Bifurcaciones sqlite/postgres; falta linter+type-check en CI |

**El proyecto está notablemente bien construido desde el punto de vista de seguridad.** El único obstáculo real para el lanzamiento es la **falla de integridad del catálogo** que deja el CI en rojo y un catálogo incompleto; es de resolución rápida y es **lo primero** a corregir antes de salir al mercado. Las demás recomendaciones son endurecimiento incremental y control de deuda técnica.
