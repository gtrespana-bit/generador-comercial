# ADR-002 — Los archivos privados se sirven solo por el proxy; sin URLs firmadas (por ahora)

**Estado:** propuesta (recomendación del agente, pendiente de confirmación del propietario)
**Fecha:** 17 de agosto de 2026
**Decisor:** propietario del producto

## Contexto

E4-017 pedía «auditar archivos y URLs firmadas». El estado de partida era:

- Los objetos nuevos ya pasan por el proxy privado `/archivos/...`, que
  autoriza por membresía/tenant antes de leer el objeto.
- `/static/uploads` queda bloqueado en PostgreSQL y las referencias legadas
  pasan por `/archivos-legado/...`, que exige que un registro de la
  organización activa las use.
- El bucket se aprovisiona `public: false` y ninguna plantilla enlaza a
  `supabase.co/storage`.

Quedaban dos cosas: la **auditoría externa** (manual, contra el proyecto
Supabase real) y **decidir** si se introducen URLs firmadas cortas para
descargas grandes.

## Decisión recomendada

1. **Mantener el proxy como única frontera de autorización.** No se introducen
   URLs firmadas ni públicas hacia Supabase Storage por ahora.

2. **Blindar la decisión por regresión.** `tests/test_auditoria_archivos.py`
   recorre todo `app/` (Python, plantillas, JavaScript y CSS) y prohíbe
   cualquier marcador de generación de URL pública o firmada, además de los
   enlaces directos al bucket.

3. **Posponer las URLs firmadas** hasta que exista una necesidad real (p. ej.
   descargas de planos de muchos MB que saturen el proxy serverless).

## Por qué no firmar ahora

- **Seguridad por omisión peor.** Una URL firmada traslada la autorización a
  Supabase (se genera con la `service_role`/`sb_secret_`) y añade un segundo
  camino de confianza que habría que auditar por separado: caducidad, firma
  reutilizable y visibilidad en logs/CDN.
- **No hay necesidad.** El límite de objeto es 12 MB y el proxy ya sirve con
  caché privada, `nosniff`, CSP `sandbox` y `same-origin`. El cuello de botella
  teórico (descargas muy grandes) no aparece hoy en el producto.
- **Menos superficie que revisar.** Mantener un único punto (el proxy) mantiene
  la revisión de seguridad concentrada y verificable por pruebas.

## Si en el futuro se necesitan

La vía sería, y se registraría como ADR nuevo con su propia prueba de
regresión:

1. generar URLs firmadas **cortas** (p. ej. 60 s) solo en el backend, contra el
   bucket privado;
2. servirlas únicamente desde una ruta autenticada y efímera, nunca incrustadas
   en plantillas estáticas ni en el PDF;
3. auditar que la firma use la clave de servidor y que la caducidad sea
   mínima e infalsificable.

## Consecuencias

### Se mantiene

- proxy `/archivos/...` como frontera de autorización;
- bucket privado `public: false` y ausencia de enlaces directos;
- auditoría estática completa en CI (`test_auditoria_archivos.py`).

### Queda pendiente (operativo, del titular)

- la **auditoría externa**: pegar en el navegador la URL pública de un objeto y
  confirmar que Supabase responde acceso denegado (no depende del código).

### Se evita

- un segundo mecanismo de autorización que habría que documentar, rotar y
  monitorizar sin necesidad actual.
