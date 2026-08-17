"""Routers por dominio (E4-001).

``app/main.py`` monta la aplicación y delega las rutas de negocio en estos
módulos, agrupados por dominio: ``auth``, ``publico``, ``admin``, ``inicio``,
``clientes``, ``presupuestos``, ``configuracion``, ``partidas``, ``productos``,
``recursos``, ``plantillas`` y ``recetas``.

Los helpers y el entorno Jinja compartidos viven en ``app.routers.common``.
"""
