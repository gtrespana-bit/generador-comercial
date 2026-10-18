# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (20 de n): resinas y
recubrimientos finales.

Vocabulario aplicado:

· «Pintura de demarcación» es line marking paint y la de tráfico es
  traffic paint, la misma que se usa en los estacionamientos.
· «Escamas de color» son colored flakes y el «espolvoreo» del árido es
  broadcasting.
· «Autodrenante» es self-draining y la «pendiente de evacuación» es
  drainage fall.
· «Poliuretano cementoso» es polyurethane concrete, el que aguanta la
  abrasión y el choque térmico de la industria alimentaria.
· «Cámara frigorífica» es cold room, y el recubrimiento tiene que ser
  apto para frío, apto para dilatar con el sustrato.
· «Resalte sanitario» es coved skirting: la media caña de resina que
  sustituye al rodapié y deja el rincón lavable.
· «Mortero acrílico» de fachada es acrylic render, y el reflectivo de
  cubierta es reflective coating, el que baja la carga térmica.
· «Vaciado de las juntas» es raking out of the joints, y rejuntar es
  re-grouting.
"""

LOTE = {
    "Aplicación de revestimiento epóxico de alta resistencia química sobre piso o paramento de laboratorio o industria. Incluye la preparación, la imprimación y las capas de acabado resistentes a productos químicos. Medido por metro cuadrado recubierto.":
        "Application of a high chemical resistance epoxy coating on a floor or substrate in a laboratory or industrial premises. Includes the preparation, the primer and the chemical resistant finish coats. Measured per square meter coated.",

    "Aplicación de pintura de demarcación sobre pisos industriales y estacionamientos, para delimitación de zonas y circulaciones. Incluye el replanteo de las líneas y la aplicación de la pintura de tráfico. Medido por metro cuadrado demarcado.":
        "Application of line marking paint on industrial floors and parking lots, for the delimitation of zones and circulation routes. Includes setting out the lines and applying the traffic paint. Measured per square meter marked.",

    "Aplicación de microcemento en techo, con malla y acabado sellado. Incluye la preparación del soporte y la aplicación del microcemento. Medido por metro cuadrado aplicado.":
        "Application of microcement on a ceiling, with mesh and a sealed finish. Includes preparing the substrate and applying the microcement. Measured per square meter applied.",

    "Aplicación de membrana de poliurea sobre cubierta o superficie expuesta, en capa continua. Incluye la preparación del soporte y la aplicación de la poliurea. Medido por metro cuadrado aplicado.":
        "Application of a polyurea membrane on a roof or exposed surface, in a continuous coat. Includes preparing the substrate and applying the polyurea. Measured per square meter applied.",

    "Aplicación de recubrimiento epóxico decorativo con escamas de color sobre piso o paramento. Incluye la preparación, la imprimación y la aplicación con escamas. Medido por metro cuadrado recubierto.":
        "Application of a decorative epoxy coating with colored flakes on a floor or substrate. Includes the preparation, the primer and the application with flakes. Measured per square meter coated.",

    "Aplicación de recubrimiento de resina con árido de cuarzo coloreado antideslizante sobre piso. Incluye la preparación, la resina y el espolvoreo del cuarzo. Medido por metro cuadrado recubierto.":
        "Application of a resin coating with anti-slip colored quartz aggregate on a floor. Includes the preparation, the resin and the broadcasting of the quartz. Measured per square meter coated.",

    "Aplicación de recubrimiento antiderrapante de resina sobre rampa, para circulación segura. Incluye la preparación y la aplicación del recubrimiento. Medido por metro cuadrado recubierto.":
        "Application of an anti-slip resin coating on a ramp, for safe circulation. Includes the preparation and the application of the coating. Measured per square meter coated.",

    "Aplicación de recubrimiento de resina acrílica decorativa sobre piso o paramento. Incluye la preparación y la aplicación de la resina. Medido por metro cuadrado recubierto.":
        "Application of a decorative acrylic resin coating on a floor or substrate. Includes the preparation and the application of the resin. Measured per square meter coated.",

    "Aplicación de recubrimiento epóxico autodrenante sobre piso industrial, con pendiente de evacuación. Incluye la preparación, la imprimación y el acabado autodrenante. Medido por metro cuadrado recubierto.":
        "Application of a self-draining epoxy coating on an industrial floor, with a drainage fall. Includes the preparation, the primer and the self-draining finish. Measured per square meter coated.",

    "Aplicación de recubrimiento de poliuretano cementoso sobre piso, resistente a la abrasión. Incluye la preparación y la aplicación del recubrimiento. Medido por metro cuadrado recubierto.":
        "Application of an abrasion resistant polyurethane concrete coating on a floor. Includes the preparation and the application of the coating. Measured per square meter coated.",

    "Aplicación de recubrimiento de resina en cámara frigorífica o local frío. Incluye la preparación y la aplicación del recubrimiento apto para frío. Medido por metro cuadrado recubierto.":
        "Application of a resin coating in a cold room or cold store. Includes the preparation and the application of the coating suitable for cold. Measured per square meter coated.",

    "Ejecución de resalte sanitario de resina en el encuentro piso-pared, para limpieza e higiene. Incluye la preparación y la formación del resalte. Medido por metro lineal ejecutado.":
        "Formation of a resin coved baseboard at the floor to wall junction, for cleaning and hygiene. Includes the preparation and the formation of the coving. Measured per meter completed.",

    "Aplicación de recubrimiento epóxico conductor antiestático sobre piso de laboratorio o industria electrónica. Incluye la preparación y la aplicación del recubrimiento conductor. Medido por metro cuadrado recubierto.":
        "Application of an anti-static conductive epoxy coating on a laboratory or electronics industry floor. Includes the preparation and the application of the conductive coating. Measured per square meter coated.",

    "Aplicación de recubrimiento de fachada con mortero acrílico decorativo e impermeable. Incluye la preparación del soporte y la aplicación del mortero acrílico. Medido por metro cuadrado recubierto.":
        "Application of a facade coating with a decorative and waterproof acrylic stucco. Includes preparing the substrate and applying the acrylic stucco. Measured per square meter coated.",

    "Aplicación de recubrimiento reflectivo sobre cubierta, para reducir la carga térmica. Incluye la limpieza y la aplicación del recubrimiento reflectivo. Medido por metro cuadrado recubierto.":
        "Application of a reflective coating on a roof, to reduce the thermal load. Includes the cleaning and the application of the reflective coating. Measured per square meter coated.",

    "Aplicación de recubrimiento decorativo texturado sobre paramento, con acabado a elección. Incluye la preparación del soporte y la aplicación del texturado. Medido por metro cuadrado recubierto.":
        "Application of a textured decorative coating on a substrate, with the finish of the client's choice. Includes preparing the substrate and applying the textured coating. Measured per square meter coated.",

    "Limpieza de fachada con hidrolavadora de presión para eliminar suciedad, contaminación y eflorescencias sin dañar el soporte. Incluye la protección de carpintería y accesos y la limpieza por franjas. Medido por metro cuadrado limpiado.":
        "Cleaning of a facade with a pressure washer to remove dirt, pollution and efflorescence without damaging the substrate. Includes protecting the joinery and the accesses and the cleaning in bands. Measured per square meter cleaned.",

    "Restauración de enchapado existente con retirada del mortero de juntas deteriorado y rejuntado con mortero nuevo. Incluye el vaciado de las juntas, la limpieza y el relleno con el mortero adecuado. Medido por metro cuadrado restaurado.":
        "Restoration of existing tiling with the removal of the deteriorated grout and re-grouting with new mortar. Includes the raking out of the joints, the cleaning and the filling with the appropriate mortar. Measured per square meter restored.",
}
