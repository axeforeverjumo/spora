# Phase 4: Automated Task Creation - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement automatic conversion of hierarchical segment structure to hierarchical project tasks when sale order is confirmed. This phase extends native Odoo sale order confirmation workflow to create tasks that mirror the segment tree structure, maintaining parent-child relationships and transferring product information.

**Core principle:** Extend native Odoo flow, don't replace it. Odoo already creates projects and tasks on confirmation; we add hierarchical segment-to-task conversion on top.

</domain>

<decisions>
## Implementation Decisions

### Trigger timing & project creation

**Momento de ejecución:**
- Ejecutar conversión en confirmación del presupuesto (sale.order action_confirm)
- Ejecutar **ANTES** del flujo nativo de Odoo (para tener control total)
- Método: Extender `sale.order.action_confirm()` vía `_inherit`

**Control del flujo:**
- **Nosotros controlamos la creación de tareas** (no dejar que Odoo cree tareas por su cuenta de forma no controlada)
- Prevenir que Odoo haga creaciones duplicadas o extrañas
- Implementar lógica de control explícita antes de que el flujo nativo actúe

**Productos sin segment_id:**
- Productos que NO tienen segment_id asignado → **Odoo los maneja** (crea tareas normales)
- Contexto: Lo más normal es que todos los productos estén dentro de un segmento (90%+ casos)
- No interferir con el flujo nativo de Odoo para productos sueltos

**Idempotencia:**
- Re-confirmar un presupuesto → **NO crear tareas duplicadas**
- Verificar si ya existen tareas vinculadas a los segmentos antes de crear
- Lógica: Si `self.env['project.task'].search([('segment_id', '=', segment.id)])` → skip

**Creación de proyecto:**
- Si proyecto no existe al confirmar → **dejar que Odoo lo cree** (flujo nativo)
- Odoo crea proyecto automáticamente si hay productos tipo servicio
- Nosotros solo creamos las tareas jerárquicas después

**Orden de ejecución:**
```python
def action_confirm(self):
    # 1. Nuestro código: crear tareas de segmentos (ANTES)
    self._create_segment_tasks()

    # 2. Flujo nativo Odoo: crear proyecto + tareas de productos sueltos
    res = super().action_confirm()

    return res
```

### Product-to-description conversion

**Campo description de la tarea:**
- Si segmento tiene productos → description = **descripción de cada producto** (listado)
- Si segmento NO tiene productos → description = vacío o solo título del segmento
- Formato sugerido:
  ```
  Productos incluidos:
  - Producto X: [descripción del producto]
  - Producto Y: [descripción del producto]
  ```

**Campo name de la tarea:**
- `task.name = segment.name` (título del segmento, NO descripción de productos)

**Visualización en presupuesto:**
- Los productos se muestran dentro del segmento en el presupuesto
- En la tarea, se replica esta información en el campo description

### Data inheritance & defaults

**Campos a transferir del segmento a la tarea:**
- `name` → `task.name` (título del segmento)
- `sequence` → `task.sequence` (ordenamiento de hermanos)
- `parent_id` → `task.parent_id` (jerarquía: apuntar a tarea del segmento padre)
- Productos del segmento → `task.description` (listado formateado)
- Suma de cantidades de productos → `task.planned_hours` (horas estimadas)
- Segmento original → `task.segment_id` (trazabilidad)

**Campos NO transferidos inicialmente (v1):**
- Responsable del segmento (AUTO-08) - requiere campo adicional en segment
- Fecha inicio/fin del segmento (AUTO-09) - requiere campos adicionales en segment
- Estos campos pueden agregarse en Phase 5 (UX) si se requieren

**Valores por defecto:**
- `task.project_id` = proyecto vinculado al sale order (ya creado por Odoo)
- `task.partner_id` = cliente del sale order
- `task.company_id` = compañía del sale order

### Error handling & partial failures

**Savepoints para aislamiento (AUTO-11, AUTO-12):**
- Usar savepoints de Odoo para aislar errores en creación batch
- Pattern:
  ```python
  for segment in segments:
      try:
          with self.env.cr.savepoint():
              self._create_task_for_segment(segment)
      except Exception as e:
          _logger.error(f"Failed to create task for segment {segment.id}: {e}")
          continue
  ```

**Manejo de errores:**
- Si falla creación de UNA tarea → continuar con las demás (no rollback total)
- Loggear errores específicos para debugging
- No bloquear confirmación del presupuesto por fallo en una tarea

**Validaciones pre-creación:**
- Verificar que proyecto existe antes de crear tareas
- Verificar que no existan tareas duplicadas (idempotencia)
- Validar estructura jerárquica (parent_id válido)

### Jerarquía y dependencias

**Orden de creación:**
- Crear tareas de arriba hacia abajo (nivel 1 → nivel 2 → nivel 3 → nivel 4)
- Asegurar que parent_id apunta a tarea ya creada
- Algoritmo: BFS o DFS del árbol de segmentos

**Root tasks (nivel 1):**
- Segmentos sin parent_id → tareas sin parent_id (raíz del proyecto)

**Child tasks (niveles 2-4):**
- `task.parent_id` = tarea del `segment.parent_id`
- Mantener jerarquía de 3 niveles en tasks (constraint de Odoo)

### Claude's Discretion

- Formato exacto del listado de productos en description
- Orden de procesamiento de segmentos (BFS vs DFS)
- Logging level y mensajes de error específicos
- Manejo de segmentos vacíos (ni productos ni hijos)
- Opción de configuración para deshabilitar conversión automática

</decisions>

<specifics>
## Specific Ideas

**Modelo de conversión detallado:**
```
Sale Order: SO001
  Segmento A (nivel 1) → Task "Segmento A" (root, project_id=P1)
    Producto X (qty=2) ─┐
    Producto Y (qty=3) ─┤→ description + planned_hours=5
    Segmento B (nivel 2) → Task "Segmento B" (parent_id=Task A)
      Producto Z (qty=1) → description + planned_hours=1
      Segmento C (nivel 3) → Task "Segmento C" (parent_id=Task B)
        Producto W (qty=4) → description + planned_hours=4
```

**Método de conversión (pseudocódigo):**
```python
def _create_segment_tasks(self):
    """Crear tareas jerárquicas desde segmentos al confirmar SO."""
    if not self.segment_ids:
        return

    project = self._get_or_create_project()
    segment_to_task = {}

    # Recorrer segmentos por nivel
    for level in range(1, 5):  # 4 niveles máximo
        segments_at_level = self.segment_ids.filtered(lambda s: s.level == level)

        for segment in segments_at_level:
            # Skip si ya existe tarea para este segmento
            if self.env['project.task'].search([('segment_id', '=', segment.id)]):
                continue

            # Preparar valores
            vals = {
                'name': segment.name,
                'project_id': project.id,
                'segment_id': segment.id,
                'description': self._format_products_description(segment.line_ids),
                'planned_hours': sum(segment.line_ids.mapped('product_uom_qty')),
                'partner_id': self.partner_id.id,
                'sequence': segment.sequence,
            }

            # Asignar parent_id si es hijo
            if segment.parent_id and segment.parent_id.id in segment_to_task:
                vals['parent_id'] = segment_to_task[segment.parent_id.id]

            # Crear tarea con savepoint
            try:
                with self.env.cr.savepoint():
                    task = self.env['project.task'].create(vals)
                    segment_to_task[segment.id] = task.id
            except Exception as e:
                _logger.error(f"Error creating task for segment {segment.id}: {e}")
                continue
```

**Formato sugerido para description:**
```markdown
Productos incluidos:
• Implantación PaP (2.00 unidades)
  Configuración inicial del sistema PaP
• Formación usuarios (3.00 horas)
  Sesión de formación para usuarios finales
```

</specifics>

<deferred>
## Deferred Ideas

**Áreas no discutidas (por falta de contexto/tiempo):**
- Campos adicionales en segment (responsable, fechas) para AUTO-08, AUTO-09
- Configuración de formato de description personalizable
- Sincronización bidireccional segment ↔ task (fuera de scope v1)
- Conversión manual de segmentos a tareas (OUT_OF_SCOPE según requirements)

**Para Phase 5 (UX):**
- Vista Gantt de segmentos → tareas
- Indicadores visuales de estado de conversión
- Smart button en segment para ver tarea generada

</deferred>

---

*Phase: 04-automated-task-creation*
*Context gathered: 2026-02-05*
*Discussed areas: 2/4 (Trigger timing, Product conversion — Data inheritance/Error handling based on requirements)*
