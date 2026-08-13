# ADR-001 — CotizaT se desarrolla browser-first

**Estado:** aceptada
**Fecha:** 13 de agosto de 2026
**Decisor:** propietario del producto

## Contexto

CotizaT nació como una aplicación FastAPI servida localmente y envuelta en una ventana de escritorio. El objetivo comercial final es una aplicación alojada, accesible desde el navegador y capaz de separar de forma segura los datos de diferentes empresas.

Continuar ampliando una configuración global, SQLite y archivos locales obligaría a revisar posteriormente cada consulta, documento y módulo. La interfaz FastAPI/Jinja ya es web y no necesita ser reescrita para tomar esta dirección.

## Decisión

CotizaT se desarrollará desde ahora con una arquitectura **browser-first**, aunque durante el desarrollo siga ejecutándose en un navegador local.

1. FastAPI, Jinja y JavaScript continúan como stack principal.
2. PostgreSQL es la base objetivo de la versión alojada.
3. Alembic versiona el esquema web; las migraciones SQLite manuales se conservan solo para importar y proteger instalaciones anteriores.
4. Cada dato empresarial debe pertenecer explícitamente a una organización.
5. El aislamiento se aplica en la sesión de SQLAlchemy, no mediante la disciplina de recordar un filtro en cada ruta.
6. Logos, imágenes, anexos e importaciones deberán pasar por una interfaz de almacenamiento antes de desplegarse públicamente.
7. La autenticación determinará la organización activa mediante una membresía; el identificador local fijo es únicamente una transición y no autoriza un despliegue público.
8. La arquitectura será portable. Vercel es una opción de despliegue, no una dependencia de diseño.

## Consecuencias

### Se mantiene

- lógica de presupuestos, catálogos y proyectos;
- generación de PDF;
- importadores;
- plantillas y editor web;
- recorrido hasta el primer PDF;
- posibilidad de ejecutar la aplicación localmente mientras se desarrolla.

### Se pausa

- nuevas inversiones en PyInstaller, pywebview e Inno Setup;
- pruebas comerciales del instalador de Windows;
- nuevas funciones que dependan de reemplazar o copiar directamente el archivo SQLite.

Los componentes existentes no se eliminan todavía: sirven como fuente para migrar bases y catálogos anteriores.

## Primera implementación

La primera entrega de esta decisión incorpora:

- resolución de `DATABASE_URL` con compatibilidad para `COTIZAT_DB` y `PRESUPUESTOS_DB`;
- driver PostgreSQL `psycopg`;
- esquema inicial versionado con Alembic;
- modelos `Organizacion`, `Usuario` y `Membresia`;
- `organizacion_id` en entidades empresariales;
- asignación y filtrado automático por organización;
- unicidad de números de documento y nombres de catálogo por organización;
- pruebas de aislamiento de lectura, acceso directo por ID y escritura;
- aislamiento de la base utilizada por pytest.

## Trabajo todavía obligatorio

Esta decisión y su primera implementación **no vuelven pública ni segura** la aplicación. Antes de un despliegue externo faltan:

- autenticación y selección de organización desde membresías;
- autorización por rol;
- CSRF, cookies seguras y cabeceras;
- almacenamiento de objetos;
- secretos y entornos separados;
- ejecución real de pruebas contra PostgreSQL;
- auditoría de todas las rutas y archivos;
- estrategia de backup y restauración administrada;
- migrador probado desde bases SQLite existentes.
