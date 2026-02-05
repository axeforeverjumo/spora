# Phase 3: Project Extension & Security - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend project.task model to trace back to originating segments and define security rules for segment access control. This phase prepares the infrastructure for automatic task creation (Phase 4) by establishing the segment_id field, validations, and permission model.

**Key clarification:** Each segment generates ONE task (not one per product). Products are grouped as description/planned_hours within the segment's task.

</domain>

<decisions>
## Implementation Decisions

### Referencia a segmento en task

- **segment_id field**: Many2one a sale.order.segment
- **Visibilidad**: Visible y editable por usuario (no readonly)
- **Ubicación UI**: En sección principal del formulario de task, cerca de project_id y parent_id
- **Formato display**: Mostrar "Nombre + orden" (ej: "SO001 / Implantación PaP")
- **Condicional**: Campo solo visible en projects que tienen sale_order_id (oculto en proyectos manuales)

### Validación de relaciones

- **Validación cross-order**: Si segment no pertenece al sale order del project → **Modal warning bloqueante** (usuario debe confirmar OK para continuar)
- **Mensaje warning**: Solo advertir, NO sugerir lista de segmentos correctos
- **Obligatoriedad**: segment_id es **opcional** (tasks pueden existir sin segment_id)
- **Mutabilidad**: segment_id **siempre editable**, puede cambiar después de crear la task
- **Project sin sale_order**: Campo segment_id invisible en esos projects (solo visible si project.sale_order_id existe)

### Reglas de seguridad

- **Herencia automática**: Si usuario no puede ver segment, tampoco puede ver la task vinculada
- **Implementación**: Herencia de permisos vía relaciones (Odoo maneja automáticamente por Many2one)
- **Restricción por ownership**: Si Sales User NO puede ver un sale order → puede **ver** segments/tasks pero **no editar** (read-only)
- **Sales User vs Sales Manager**:
  - Sales User: crear/leer segments + ver tasks de otros con read-only
  - Sales Manager: CRUD completo en segments + editar cualquier task

### Casos límite

- **Borrar segment con tasks**: **Bloquear borrado** (ValidationError si existen tasks vinculadas)
- **Cambiar sale_order_id del project**: **Bloquear cambio** si existen tasks con segment_id (ValidationError)
- **Task manual sin segment_id**: **Permitir** (usuario puede agregar tasks extra manualmente en proyectos de presupuesto)

### Claude's Discretion

- Exact warning message text (debe ser claro pero no técnico)
- Icon for segment_id field in UI
- Order of fields in form view (si hay otros campos cerca)
- Logging/audit trail for segment_id changes

</decisions>

<specifics>
## Specific Ideas

**Modelo de conversión (para contexto de Phase 4):**
```
Segmento A (nivel 1)
  ├─ Producto X → Task "Producto X" (incluido en Task A, NO tarea separada)
  ├─ Producto Y → Task "Producto Y" (incluido en Task A, NO tarea separada)
  └─ Segmento B (nivel 2) → Task "Segmento B" (hijo de Task A)
       ├─ Producto Z → (incluido en Task B)
       └─ Segmento C (nivel 3) → Task "Segmento C" (hijo de Task B)
            └─ Producto W → (incluido en Task C)
```

Cada segmento → 1 task con:
- name = segment.name
- description = lista de productos del segmento
- planned_hours = suma de cantidades de productos
- segment_id = segment original
- parent_id = task del segmento padre (si existe)

**Dos flujos de proyectos:**
1. Proyectos manuales: Usuario crea en módulo project (segment_id oculto)
2. Proyectos de presupuesto: Generados al confirmar sale order (segment_id visible)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-project-extension-security*
*Context gathered: 2026-02-05*
