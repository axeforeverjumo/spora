# Spora - Presupuestos Jerárquicos con Conversión a Tareas

## What This Is

Un módulo custom de Odoo 18 que extiende el sistema de presupuestos (sale orders) para soportar segmentos jerárquicos anidables (hasta 4 niveles de profundidad) con productos del catálogo asociados. Cada segmento se convierte automáticamente en una tarea de proyecto al confirmar el presupuesto, manteniendo la jerarquía padre-hijo y asociando correctamente los productos, horas estimadas, responsables y fechas a cada tarea.

## Core Value

La conversión automática de la estructura jerárquica de presupuesto (segmentos anidados) a estructura de tareas de proyecto (parent-child tasks), permitiendo que equipos de servicios complejos (marketing, comunicación, consultoría) pasen de cotización a ejecución sin perder la organización jerárquica del trabajo.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Modelo `sale.order.segment` con relación padre-hijo (`parent_id`)
- [ ] Cálculo automático de nivel de segmento según profundidad (1-4)
- [ ] Validación de límite máximo de 4 niveles de anidación
- [ ] Cualquier segmento puede tener productos directos (vía `sale.order.line`)
- [ ] Cualquier segmento puede tener sub-segmentos hijos
- [ ] Un segmento puede tener ambos: productos Y sub-segmentos simultáneamente
- [ ] Vista árbol expandible (tree view) para navegación de jerarquía
- [ ] Cálculo automático de subtotales por segmento (suma de productos + suma de sub-segmentos)
- [ ] Conversión automática a proyecto (`project.project`) al confirmar presupuesto (sale order)
- [ ] Cada segmento genera una tarea (`project.task`) con `parent_id` respetando jerarquía
- [ ] Productos del segmento se asocian a la tarea correspondiente
- [ ] Horas estimadas de tarea = suma de cantidades de productos del segmento
- [ ] Transferencia de responsable del segmento a tarea
- [ ] Transferencia de fechas previstas del segmento a tarea
- [ ] Integración nativa con módulos `sale` y `project` de Odoo 18

### Out of Scope

- Más de 4 niveles de anidación — límite establecido para evitar complejidad excesiva
- Conversión manual de segmentos a tareas — la conversión es automática al confirmar
- Productos de texto libre — solo productos del catálogo Odoo para mantener trazabilidad
- Edición de tareas desde presupuesto — las tareas se gestionan en el módulo project
- Re-sincronización automática — si cambia presupuesto después de confirmar, no actualiza tareas

## Context

**Tipo de negocio:**
Equipos que gestionan proyectos de servicios complejos: marketing, comunicación, consultoría, ingeniería de proyectos. Los presupuestos tienen múltiples fases, áreas o categorías de trabajo que necesitan reflejarse en la estructura de tareas del proyecto.

**Ejemplo de uso real:**
Presupuesto de campaña de comunicación (ver `data4claude/2024_270_GBIPAPREC_CALONGE 1.pdf`):
- Dirección y Coordinación (segmento nivel 1)
  - Productos: dirección proyecto, coordinación ejecutiva
- Implantación PaP Doméstica (segmento nivel 1)
  - Materiales de Comunicación (segmento nivel 2)
    - Productos: cartas, magnéticos, carteles
  - Acciones de Implantación (segmento nivel 2)
    - Productos: bustiadas, xerradas, puntos informativos

**Entorno técnico:**
- Odoo 18.0 corriendo en Docker (ver `docker-compose.yml`)
- PostgreSQL 15
- Directorio addons custom: `/mnt/extra-addons`

**Motivación:**
Actualmente los presupuestos de Odoo son listas planas de líneas. Para proyectos complejos esto dificulta:
1. Organizar cotizaciones por fases/áreas
2. Ver subtotales por categoría
3. Convertir estructura de presupuesto a estructura de tareas sin trabajo manual

## Constraints

- **Tech stack**: Odoo 18.0, Python 3.10+, PostgreSQL 15 — stack ya establecido
- **Módulos base**: `sale`, `project` — debe extender sin romper funcionalidad estándar
- **Compatibilidad**: Integración nativa con vistas y workflows de Odoo (no bypass de framework)
- **Performance**: Cálculo de subtotales debe ser eficiente (campos computed con store=True)
- **UX**: Vista árbol debe seguir patrones estándar de Odoo (one2many, parent_id)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Relación padre-hijo automática vs selector manual de nivel | Usuario selecciona padre, nivel se calcula → más intuitivo y menos errores | — Pending |
| Permitir productos en segmentos con hijos | Flexibilidad real de presupuestos complejos (ej: supervisión general + sub-fases) | — Pending |
| Conversión automática al confirmar vs botón manual | Automática → menos pasos, workflow más fluido | — Pending |
| Límite 4 niveles | Balance entre flexibilidad y complejidad (casos reales raramente >3 niveles) | — Pending |

---
*Last updated: 2026-02-05 after initialization*
