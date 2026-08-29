"""Routers por dominio (E4-001).

``app/main.py`` monta la aplicación y delega las rutas en estos módulos, uno por
dominio. Seis cosas se reparten el panel y la aplicación:

- ``publico`` y ``inicio`` — landing, páginas estáticas, blog y lo que ve quien
  no ha entrado.
- ``auth`` — alta, entrada y verificación del usuario.
- ``clientes`` — el workspace de organización (equipo y ajustes de la empresa).
- ``presupuestos``, ``partidas``, ``recursos``, ``plantillas``, ``productos``,
  ``recetas``, ``configuracion``, ``planos``, ``ia`` — el negocio del generador:
  cotizar y mantener el catálogo propio.
- ``pagos`` — compras de plan y cobros desde la pasarela.
- ``admin`` — **solo** las acciones del panel de operador (POST, API de búsqueda,
  campana y endpoints del cron).
- ``admin_paginas`` — las pantallas del panel: seis áreas con sus pestañas, los
  CSV y las redirecciones de las páginas que se fusionaron. El mapa que las
  describe está en ``app.panel_arquitectura``.

Los helpers y el entorno Jinja compartidos viven en ``app.routers.common``:
sesión, ``_redirect`` (303 para que un F5 no repita un cobro), el CSV con ``;`` y
BOM, y el ``context_processors`` que añade las cifras de la barra superior.
"""
