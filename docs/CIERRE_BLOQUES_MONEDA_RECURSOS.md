# Cierre de bloques — moneda y recursos LatAm

## Completados

- Bloque 1: auditoría técnica.
- Bloque 2: modelo monetario ISO.
- Bloque 3: conversión y tasas.
- Bloque 4: configuración y cambio de moneda.
- Bloque 5: editor y cálculos.
- Bloque 6: plantillas y exportaciones.
- Bloque 7: recursos por mercado.
- Bloque 8: mano de obra, equipos y rendimientos.
- Bloque 9: históricos y congelación.
- Bloque 10: proyectos, cambios, pagos y facturas.
- Bloque 11: pruebas y aceptación.
- Bloque 12: documentación y cierre.

## Estado de calidad

Suite ejecutada:

```text
766 passed, 6 skipped
```

## Antes de activar en staging

- Revisar la revisión de `public.alembic_version`.
- Ejecutar únicamente los SQL Supabase posteriores a esa revisión.
- Comprobar el head final esperado: `c5d6e7f8a9b0`.
- Verificar `/readyz`.
- Ejecutar un presupuesto ficticio en CO, PE, MX y EC.
- Comprobar PDF, Excel, correo, enlace público y proyecto.
- No utilizar datos reales en la matriz de aceptación.
