# Feature: Import BC3 y Medición manual sobre planos

Fecha: 2026-08-22
Rama: arena/01a02bdb-generador-comercial

## Resumen ejecutivo

Se implementan los dos puntos de mayor ROI para España sin cambiar de nicho:

1. **Import BC3 (FIEBDC-3)** - el reformista recibe el .bc3 del arquitecto y lo convierte en presupuesto CotizaT
2. **Planos manual asistido** - mide sobre PNG/JPG/PDF sin IA ni coste por uso

Ambos mantienen el posicionamiento honesto: seguimos siendo software de reforma residencial/comercial, no de licitación pública completa.

## 1. Import BC3

### Qué hace
- Acepta `.bc3` en `/presupuestos/importar` y en el importador embebido del editor (`/presupuestos/nuevo`)
- Detecta encoding: UTF-8, Windows-1252, ISO-8859-1, CP850 (BCCA Andalucía viene en ANSI)
- Parsea registros: `~V`, `~K`, `~C`, `~D`, `~T`, `~M`
- Construye árbol capítulos (`#`) -> partidas a partir de `~D`
- Extrae mediciones `~M` con desglose: comentario \ uds \ long \ lat \ alt
- Calcula costes materiales/mano obra por tipo de concepto (1=mano obra, 3=materiales)
- Guarda .bc3 original en storage privado y manifiesto JSON para auditoría

### Límites
- MAX 10.000 conceptos, 5.000 partidas, 8 MB (protección contra volcar base completa BCCA 6.600 precios)
- Si BC3 es base completa, se limita a primeras 5.000 partidas con advertencia

### Estructura devuelta
```json
{
  "formato": "bc3",
  "capitulos_detectados": 2,
  "conceptos_detectados": 120,
  "filas": [
    {
      "codigo": "02.01",
      "capitulo": "REVESTIMIENTOS",
      "nombre": "Solado porcelánico 60x60",
      "descripcion": "Texto largo ~T",
      "unidad": "m2",
      "cantidad": 84.6,
      "precio": 38.5,
      "costes": {"materiales": 1.95, "mano_obra": 4.88},
      "mediciones": [{"concepto": "Cocina", "cantidad": 50}]
    }
  ]
}
```

### Flujo de código
- `app/services/bc3.py`: parser puro, sin dependencias externas
  - `es_formato_bc3()`: heurística rápida
  - `parse_bc3()`: registros -> conceptos, textos, descomposiciones, mediciones
  - `_construir_arbol_capitulos()`: BFS desde raíces ##/#
  - `analizar_bc3()`: convierte a filas CotizaT
  - `exportar_presupuesto_bc3()`: genera BC3 básico compatible con Presto/Arquímedes/Buildgets
- `app/routers/presupuestos.py`:
  - `_guardar_importacion_bc3()` y `_cargar_importacion_bc3()` (mismo patrón que CYPE)
  - `analizar_importacion_presupuesto()` ahora acepta `.bc3` y detecta BC3 en texto pegado
  - `_datos_bc3_desde_payload()` y `_anexar_filas_bc3()` para confirmar
  - `exportar_presupuesto()` con `?formato=bc3`

### Export BC3 (extra)
Aunque la recomendación inicial era solo import, se añade export básico para cerrar el ciclo:
- ~V, ~K, ~C capítulos y partidas, ~T descripción, ~D capítulo->partida y partida->recursos, ~M mediciones
- Encoding Windows-1252 (compatible Presto)
- Sin certificaciones ni residuos ~R (licitación pública completa queda fuera)

### Tests
- `tests/test_bc3.py`: 3 tests de formato, árbol y costes

### Coste
- 0€ licencia. FIEBDC es estándar abierto.
- Solo horas dev (40-60h export, 60-80h import) + mantenimiento encoding.

## 2. Planos manual asistido

### Qué hace (sin IA)
- Subir plano: PNG, JPG, WEBP, PDF (12 MB máx, 20 planos por presupuesto)
- Si PDF, intenta convertir a PNG con PyMuPDF (opcional). Si no está instalado, guarda PDF y avisa.
- Calibrar escala: usuario dibuja línea de N px y dice "son 5 m" -> se calcula `escala_px_por_metro`
- Medir:
  - Lineal (m): distancia total
  - Área (m2): Shoelace
  - Perímetro (m): cierre automático
  - Conteo (ud): nº puntos
  - Volumen (m2 placeholder)
- Guardar medición con puntos JSON, etiqueta, color, valor real
- Aplicar medición a partida: crea `Medicion` en presupuesto (concepto + cantidad)

### Modelos
- `PlanoObra`: presupuesto_id, nombre, archivo (storage://), ancho_px, alto_px, escala_px_por_metro, calibración
- `PlanoMedicion`: plano_id, tipo, etiqueta, valor, unidad, puntos_json, partida_destino_id, color

### Código
- `app/services/planos.py`: validación, conversión PDF, cálculo geométrico, recalibración en cascada
- `app/routers/planos.py`:
  - GET `/presupuestos/{id}/planos` -> template
  - GET `/planos/{id}/datos` -> JSON plano + mediciones
  - GET `/planos/{id}/archivo` -> binario privado
  - POST `/presupuestos/{id}/planos/upload`
  - POST `/planos/{id}/calibrar`
  - POST `/planos/{id}/mediciones`
  - POST `/planos/{id}/mediciones/{mid}/aplicar`
  - DELETE `/planos/{id}` y mediciones
- `app/templates/budgets/planos.html`: canvas interactivo
  - Zoom, reset, calibración, herramientas, lista mediciones, aplicar a partida
  - Sin dependencias externas, solo canvas 2D
- `migrations/versions/a1b2c3d4e5f6_add_planos_obra.py`: tablas + RLS

### Frontend detalles
- Click añade punto, clic derecho borra último, doble clic cierra polígono
- Valor actual en vivo (px o m/m2 según calibrado)
- Mediciones guardadas dibujadas con color y etiqueta
- Botón aplicar crea medición en partida destino

### Tests
- `tests/test_planos.py`: 4 tests de cálculo geométrico

### Coste
- 0€ recurrente. Sin IA, sin API externa.
- Opcional: PyMuPDF para convertir PDF a imagen (`pip install PyMuPDF`), si no, frontend muestra aviso y pide PNG/JPG.
- Si en futuro se quiere IA automática, coste sería ~0.02-0.08€/página con vision model.

## SEO / Copy

Actualizado `app/seo_contenido.py` ES:
- Antes: "CotizaT no exporta BC3 ni lee planos..."
- Ahora: "CotizaT importa BC3 de arquitectos y bases como BCCA... También mide sobre planos en modo manual asistido... Si trabajas licitación pública que exige exportar BC3 con certificaciones y residuos, aún no es tu software; si haces reforma que recibe BC3 del arquitecto, el flujo es el que ya usas."

Mantiene honestidad y convierte mejor.

## Por dónde empezar (recomendación implementada)

1. BC3 import (ya hecho): permite al reformista decir "sí, traé el BC3 del arquitecto"
2. Planos manual (ya hecho): diferenciador barato, sin coste IA
3. Próximo: pulir UX de planos (snap, ortogonal, export DXF) y si hay demanda España, mejorar export BC3 con descomposición completa y luego certificaciones.

## Checklist operación

- [x] Parser BC3 puro
- [x] Integración importador tabular + CYPE + BC3
- [x] Export BC3 básico
- [x] Modelos planos + RLS
- [x] Servicios planos
- [x] Router planos
- [x] Template canvas interactivo
- [x] Migración Alembic
- [x] Tests BC3 y planos
- [x] Botón BC3 en detalle presupuesto y botón Planos
- [x] Copy SEO actualizado
- [ ] Probar con BC3 real BCCA2023_V02.zip (descargar y probar en local)
- [ ] Instalar PyMuPDF en producción si se quieren PDFs directos

## Cómo probar

```bash
# BC3
python -m pytest tests/test_bc3.py -v
# Crear sample.bc3 y subir en /presupuestos/importar

# Planos
python -m pytest tests/test_planos.py -v
# Ir a /presupuestos/{id}/planos, subir imagen, calibrar, medir, aplicar a partida
```
