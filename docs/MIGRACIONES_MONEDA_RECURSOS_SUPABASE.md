# Migraciones Supabase — Moneda y recursos LatAm

Estas migraciones son la versión SQL para el flujo actual de Supabase SQL Editor.

## Orden obligatorio

Antes de ejecutar, consultar:

```sql
SELECT version_num FROM public.alembic_version;
```

La cadena debe avanzar así:

| Orden | Archivo | Revisión previa | Nueva revisión |
|---:|---|---|---|
| 1 | `docs/staging_upgrade_a7b8c9d0e1f2.sql` | `f9d4c2a7e5b3` | `a7b8c9d0e1f2` |
| 2 | `docs/staging_upgrade_b8c9d0e1f2a3.sql` | `a7b8c9d0e1f2` | `b8c9d0e1f2a3` |
| 3 | `docs/staging_upgrade_c9d0e1f2a3b4.sql` | `b8c9d0e1f2a3` | `c9d0e1f2a3b4` |
| 4 | `docs/staging_upgrade_d0e1f2a3b4c5.sql` | `c9d0e1f2a3b4` | `d0e1f2a3b4c5` |
| 5 | `docs/staging_upgrade_e1f2a3b4c5d6.sql` | `d0e1f2a3b4c5` | `e1f2a3b4c5d6` |
| 6 | `docs/staging_upgrade_f2a3b4c5d6e7.sql` | `e1f2a3b4c5d6` | `f2a3b4c5d6e7` |
| 7 | `docs/staging_upgrade_a3b4c5d6e7f8.sql` | `f2a3b4c5d6e7` | `a3b4c5d6e7f8` |
| 8 | `docs/staging_upgrade_b4c5d6e7f8a9.sql` | `a3b4c5d6e7f8` | `b4c5d6e7f8a9` |
| 9 | `docs/staging_upgrade_c5d6e7f8a9b0.sql` | `b4c5d6e7f8a9` | `c5d6e7f8a9b0` |
| 10 | `docs/staging_upgrade_e7b3c1d5a204.sql` | `c5d6e7f8a9b0` | `e7b3c1d5a204` |
| 11 | `docs/staging_upgrade_b9f4d8a2c6e1.sql` | `e7b3c1d5a204` | `b9f4d8a2c6e1` |
| 12 | `docs/staging_upgrade_a4c8e2f7b1d6.sql` | `b9f4d8a2c6e1` | `a4c8e2f7b1d6` |

Cada script tiene una guarda y aborta si la revisión previa no coincide.

## Aplicación

En Supabase:

1. Abrir SQL Editor.
2. Crear una consulta nueva.
3. Pegar el primer archivo cuyo `revision_num` coincida con la consulta.
4. Ejecutar el script completo.
5. Consultar de nuevo `public.alembic_version`.
6. Continuar con el siguiente archivo.

El paso 10 es **obligatorio**: sin él, `precios_recursos_mercado` e
`historial_precios_recursos` quedan sin `GRANT` ni políticas para el rol
`cotizat_app` y la aplicación responde 500 al abrir «Nuevo presupuesto»
(`permission denied for table precios_recursos_mercado` → la transacción queda
abortada y la consulta siguiente falla con `InFailedSqlTransaction`).

No ejecutar los archivos juntos si la base no está exactamente en `f9d4c2a7e5b3`; la guarda existe para impedir errores de orden.

## Verificación final

```sql
SELECT version_num FROM public.alembic_version;

SELECT column_name FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('configuracion','presupuestos','proyectos','presupuesto_versiones','facturas','presupuesto_items','productos','recursos','cambios_alcance','cambio_alcance_items')
  AND column_name IN ('moneda_base','moneda_base_catalogo','moneda_contractual','fuente_tipo_cambio','moneda');

SELECT to_regclass('public.precios_recursos_mercado');
```

Comprobación de que el paso 10 se aplicó (deben salir 6 políticas y los
permisos en `true`):

```sql
SELECT policyname FROM pg_policies
WHERE tablename IN ('precios_recursos_mercado','historial_precios_recursos');

SELECT has_table_privilege('cotizat_app','public.precios_recursos_mercado','SELECT') AS lee_precios,
       has_table_privilege('cotizat_app','public.historial_precios_recursos','SELECT') AS lee_historial;
```

La revisión final esperada es:

```text
a4c8e2f7b1d6
```

## Alternativa Alembic

Si existe una `MIGRATION_DATABASE_URL` administrativa configurada y el flujo de despliegue la utiliza, el equivalente es:

```bash
alembic upgrade head
```

En ese caso no se deben ejecutar además los scripts SQL manuales: se aplicaría dos veces el mismo cambio.
