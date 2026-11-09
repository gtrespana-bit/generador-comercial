-- CotizaT — cotizaciones reales de España (2026-11-08).
-- Cubre todas las decisiones cerradas en el registro de esa fecha (todos los lotes);
-- repetir los UPDATE de un lote ya cargado es idempotente.
-- Generado por tools/aplicar_cotizaciones_espana.py desde
-- docs/auditoria_precios/espana_decision_cotizaciones_2026-11-08.csv y la matriz
-- basedatos_partidas/salida/precios_recursos_espana.csv.
--
-- ALCANCE: solo las referencias nacionales ES (sin organizacion_id) de los
-- 12 recursos cotizados. NO TOCA precios propios de empresas ni otros países.
-- MONEDA: EUR, precios sin IVA (la tabla guarda la moneda de cada mercado).

BEGIN;

-- MT-AISL-REFLECT: cotizacion_directa · adopta 3.6 EUR (Leroy Merlin mantas reflectivas OPTIMER RF1 y BLH y rollo multicapa (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 3.6,
       precio_min = 2.32,
       precio_max = 4.25,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin mantas reflectivas OPTIMER RF1 y BLH y rollo multicapa (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 2.32-4.25 EUR/m2, precio adoptado 3.60 EUR/m2 sin IVA. Tres rollos con foil de aluminio y burbuja de polietileno: RF1 de 4 mm y 42 m2 a 118 EUR (2,32 EUR/m2 sin IVA), BLH de 8 mm y 36 m2 a 185 EUR (4,25 EUR/m2 sin IVA) y el multicapa de doble burbuja de 48 m2 a 209 EUR (3,60 EUR/m2 sin IVA). Se adopta 3,60 porque es el único cuya ficha declara doble capa de burbuja, que es lo que pide el recurso. Banda 2,32-4,25 medida sobre precios de venta por m2 que publica la propia tienda.'
 WHERE codigo_recurso = 'MT-AISL-REFLECT'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-CIELO-PVC: cotizacion_directa · adopta 18.01 EUR (Leroy Merlin, lámina alveolar Renolam y panel alero de 10 mm (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 18.01,
       precio_min = 16.74,
       precio_max = 18.01,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin, lámina alveolar Renolam y panel alero de 10 mm (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 16.74-18.01 EUR/m2, precio adoptado 18.01 EUR/m2 sin IVA. Dos láminas de PVC de techo: alveolar blanco brillo a 20,25 €/m² y panel rígido de 10 mm a 21,79 €/m² IVA incluido, que son 16,74 y 18,01 €/m² sin IVA. Se adopta la mayor por ser el panel de 10 mm, más próximo al cielo raso. Falta la perfilería de remate que la ficha del recurso incluye y que el catálogo valora aparte como MT-PERFIL-REMATE: por eso el precio se queda en el extremo alto de lo medido en lugar de bajar al alveolar.'
 WHERE codigo_recurso = 'MT-CIELO-PVC'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-PERFIL-ALUM: cotizacion_directa · adopta 10.82 EUR (Arialpro perfiles 3030P 4040P y 6060P y Proycsa perfil 40x40 (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 10.82,
       precio_min = 7.54,
       precio_max = 14.46,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Arialpro perfiles 3030P 4040P y 6060P y Proycsa perfil 40x40 (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 7.54-14.46 EUR/kg, precio adoptado 10.82 EUR/kg sin IVA. Perfiles de aluminio 6063 T6 anodizado vendidos por metro con su peso declarado: Arialpro da 10,75 EUR por 0,932 kg (3030P), 17,95 EUR por 1,508 kg (4040P) y 23,99 EUR por 2,63 kg (6060P) con IVA, que son 9,53 / 9,84 y 7,54 EUR por kg sin IVA, y Proycsa da 26,41 EUR por metro del perfil 40x40 de 1,51 kg/m con IVA, 14,46 EUR/kg sin IVA. Banda medida 7,54-14,46 EUR/kg. Se mantiene el precio de la matriz porque cae dentro de la banda y el recurso ampara además herrajes y accesorios que el perfil desnudo no incluye. El banco BCCA no sirve de contraste: sus tres candidatos son perfiles de acero.'
 WHERE codigo_recurso = 'MT-PERFIL-ALUM'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-PERSIANA-ALU: cotizacion_directa · adopta 56.19 EUR (Avosdim, persiana enrollable de aluminio aislado con cinta (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 56.19,
       precio_min = 53.27,
       precio_max = 67.99,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Avosdim, persiana enrollable de aluminio aislado con cinta (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 53.27-67.99 EUR/m2, precio adoptado 56.19 EUR/m2 sin IVA. Persianas manuales con cajón, guías y cinta: 97,90 € una unidad de 1,44 m² y 119,90 € una de 1,86 m², que dan 67,99 y 64,46 €/m² con IVA y 56,19 y 53,27 €/m² sin IVA. El alcance coincide con el recurso, que también incluye cajón y accionamiento. Se adopta 56,19 porque es la unidad pequeña, la que peor precio por metro tiene.'
 WHERE codigo_recurso = 'MT-PERSIANA-ALU'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-REGUL-GAS: banco_y_minorista · adopta 15.69 EUR (Bauhaus regulador con llave de corte y banco BCCA IG03300 e IG03400 (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 15.69,
       precio_min = 11.36,
       precio_max = 15.69,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Bauhaus regulador con llave de corte y banco BCCA IG03300 e IG03400 (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (banco_y_minorista). Banda medida: 11.36-15.69 EUR/ud, precio adoptado 15.69 EUR/ud sin IVA. El banco BCCA de 2024-01 valora el regulador de butano en 11,36 EUR y el de propano de 1/2 pulgada en 14,64 EUR por unidad. El minorista de 2026 lo confirma: 18,99 EUR con IVA en Bauhaus con llave de corte (15,69 sin IVA) y 13,99 EUR el conjunto regulador con tubo y abrazadera de Leroy Merlin (11,56 sin IVA). Banda 11,36-15,69. Se adopta 15,69 porque es el único que declara llave de corte incluida y 30 mbar con 2,5 kg por hora. Desmiente la horquilla declarada 15-40 al alza.'
 WHERE codigo_recurso = 'MT-REGUL-GAS'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-RIEL-CORRED: cotizacion_directa · adopta 15.95 EUR (Leroy Merlin kits de herrajes INDAUX JUNIOR-1 y EVOTRADE y kit Tourly completo (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 15.95,
       precio_min = 5.12,
       precio_max = 20.62,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin kits de herrajes INDAUX JUNIOR-1 y EVOTRADE y kit Tourly completo (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 5.12-20.62 EUR/m, precio adoptado 15.95 EUR/m sin IVA. El recurso no distingue armario de puerta pesada y el mercado sí: el kit INDAUX JUNIOR-1 trae dos rieles de 2 m con carros y ruedas por 24,80 EUR con IVA (5,12 EUR por metro de riel), el kit de dos puertas con perfil de 2 m y topes cuesta 49,90 EUR (20,62 EUR/m) y el kit completo Tourly de 183 cm cuesta 41,99 EUR (18,96 EUR/m). Se mantiene 15,95 porque cae dentro de una banda que va del herraje de armario al kit de puerta corredera pesada, y el recurso no permite elegir sin cambiar su alcance.'
 WHERE codigo_recurso = 'MT-RIEL-CORRED'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-SAN-FIJA: banco_y_minorista · adopta 8.9 EUR (Bricosanitarios anillo de cera OATEY y banco BCCA IF17200 juego de tornillos (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 8.9,
       precio_min = 5.65,
       precio_max = 8.9,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Bricosanitarios anillo de cera OATEY y banco BCCA IF17200 juego de tornillos (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (banco_y_minorista). Banda medida: 5.65-8.90 EUR/ud, precio adoptado 8.90 EUR/ud sin IVA. El kit son dos piezas con precio propio: el anillo de cera OATEY cuesta 6,83 EUR con IVA (5,65 sin IVA) en Bricosanitarios y el juego de tornillos de fijación cromados está en 3,25 EUR sin IVA en el banco BCCA IF17200. La suma da 8,90 EUR por aparato. El anillo solo ya cuesta más que el precio derivado 5,47, así que la horquilla era baja. Banda 5,65-8,90 formada por las dos piezas que el recurso nombra.'
 WHERE codigo_recurso = 'MT-SAN-FIJA'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-SELLA-PASE: cotizacion_directa · adopta 9.96 EUR (Tienda Reco collares de sellado Tyvek-EPDM para penetraciones y masilla LAP-SEALANT (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 9.96,
       precio_min = 4.5,
       precio_max = 17.2,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Tienda Reco collares de sellado Tyvek-EPDM para penetraciones y masilla LAP-SEALANT (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 4.50-17.20 EUR/ud, precio adoptado 9.96 EUR/ud sin IVA. Collares de sellado de aire Tyvek-EPDM por diámetro: 5,45 EUR con IVA el de 4-8 mm (4,50 sin IVA), 12,05 EUR el de 40-55 mm (9,96 sin IVA) y 20,81 EUR el de 100-110 mm (17,20 sin IVA). Se adopta el de 40-55 mm, que es el diámetro habitual de los pases de fontanería y saneamiento que valoran las partidas. La masilla LAP-SEALANT cuesta 15,95 EUR sin IVA el cartucho y rinde 8 m de junta, así que por pase aporta menos de 1 EUR y no desplaza el precio. Banda 4,50-17,20 según diámetro.'
 WHERE codigo_recurso = 'MT-SELLA-PASE'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-SENAL-OBRA: cotizacion_directa · adopta 9.9 EUR (Atproteccion Lopez Parra y Leroy Merlin conos de 75 cm con banda reflectante (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 9.9,
       precio_min = 6.53,
       precio_max = 10.74,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Atproteccion Lopez Parra y Leroy Merlin conos de 75 cm con banda reflectante (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 6.53-10.74 EUR/ud, precio adoptado 9.90 EUR/ud sin IVA. Tres conos de 75 cm con banda reflectante: 7,90 EUR con IVA en Lopez Parra (Coysa), 11,98 EUR en Atproteccion (9,90 sin IVA) y 12,99 EUR en Leroy Merlin (lastrado), que son 6,53 / 9,90 y 10,74 EUR por unidad sin IVA. Se adopta 9,90. La horquilla declarada 3-10 queda desmentida por abajo: el cono más barato localizado ya cuesta 6,53. El banco BCCA solo ofrece señales de peligro tipo A de 48 a 219 EUR, que no son el cono que mide este recurso. La cinta de balizamiento tiene recurso propio (MT-CINTA-ENM), así que la unidad se valora como cono.'
 WHERE codigo_recurso = 'MT-SENAL-OBRA'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-SOPORTE-AC: cotizacion_directa · adopta 10.98 EUR (Leroy Merlin, soportes STAG 50x45 y 50x50 (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 10.98,
       precio_min = 7.68,
       precio_max = 10.98,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin, soportes STAG 50x45 y 50x50 (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 7.68-10.98 EUR/ud, precio adoptado 10.98 EUR/ud sin IVA. Dos escuadras galvanizadas de la misma familia y unidad: 9,29 € (50x45) y 13,29 € (50x50) IVA incluido, que son 7,68 y 10,98 € sin IVA. Se adopta la de 50x50 porque el recurso ampara equipos de mayor tamaño. Ninguna incluye tacos ni antivibratorios: el catálogo los valora aparte como MT-PERNO-ANCLA y MT-SOPORTE-ANTIVIB. Sustituye el valor derivado 18,23 y desmiente la horquilla declarada 15-60, que estaba por encima del mercado.'
 WHERE codigo_recurso = 'MT-SOPORTE-AC'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-TRAMPA-GRASA: cotizacion_directa · adopta 169 EUR (Bomdesa, separador de grasas ECO 72 l, y Eurosur, separador de 55 l (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 169,
       precio_min = 169,
       precio_max = 439.32,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Bomdesa, separador de grasas ECO 72 l, y Eurosur, separador de 55 l (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 169.00-439.32 EUR/ud, precio adoptado 169.00 EUR/ud sin IVA. La horquilla declarada 60-150 €/ud queda desmentida por el mercado: el separador de grasas prefabricado más barato localizado, ECO UNE-EN 1825 de 72 l con tapa, cuesta 204,49 € con IVA, es decir 169,00 € sin IVA, y el modelo de 55 l bajo fregadero sube a 531,58 €. Se adopta el mínimo real. El recurso no declara capacidad, así que si la partida exige un separador de cocina de mayor caudal este precio se queda corto.'
 WHERE codigo_recurso = 'MT-TRAMPA-GRASA'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-VIDRIO-TEMP: banco_y_minorista · adopta 77.47 EUR (CYPE LVT010 (mt21vtt010e) y Plakglass, vidrio templado de 10 mm (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 77.47,
       precio_min = 59.13,
       precio_max = 125.95,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'CYPE LVT010 (mt21vtt010e) y Plakglass, vidrio templado de 10 mm (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (banco_y_minorista). Banda medida: 59.13-125.95 EUR/m2, precio adoptado 77.47 EUR/m2 sin IVA. Se conserva el precio de la matriz porque las dos evidencias lo acotan por abajo y por arriba: el banco CYPE da 59,13 €/m² de material de 10 mm con canteado pero sin taladros, y la cristalería minorista da 125,95 €/m² sin IVA con mecanizado a medida. El recurso incluye perforaciones, que el banco no valora, de modo que el precio de la matriz cae entre ambos y no se sustituye: lo que cambia es la evidencia, que pasa de «sin ficha de banco» a dos fuentes reales que enmarcan el valor.'
 WHERE codigo_recurso = 'MT-VIDRIO-TEMP'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;

-- Comprobación: debe devolver 12 filas con la banda coherente.
SELECT codigo_recurso, precio, precio_min, precio_max, moneda, confianza,
       incluye_iva, fecha_consulta
  FROM public.precios_recursos_mercado
 WHERE codigo_recurso IN ('MT-AISL-REFLECT', 'MT-CIELO-PVC', 'MT-PERFIL-ALUM', 'MT-PERSIANA-ALU', 'MT-REGUL-GAS', 'MT-RIEL-CORRED', 'MT-SAN-FIJA', 'MT-SELLA-PASE', 'MT-SENAL-OBRA', 'MT-SOPORTE-AC', 'MT-TRAMPA-GRASA', 'MT-VIDRIO-TEMP')
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL
 ORDER BY codigo_recurso;

COMMIT;
