# Bug Fix: Task Duplication on Sale Order Confirmation

## Problema Detectado

Al confirmar presupuesto S00003 con 15 segmentos y 36 líneas de producto:
- **Esperado**: 15 tareas de segmentos + 36 tareas de productos = 51 tareas
- **Resultado**: 81 tareas (exceso de 30 tareas)
- **Jerarquía rota**: productos como tareas raíz en lugar de subtareas de segmentos

## Causa Raíz

Los productos de servicio tienen `service_tracking = 'task_in_project'` configurado, lo que hace que:

1. Odoo nativo crea tareas automáticamente en `super().action_confirm()`
2. Estas tareas se crean ANTES de que nuestro módulo procese segmentos
3. Las tareas nativas son raíz (sin `parent_id`)
4. Nuestro módulo crea tareas adicionales con jerarquía correcta
5. **Resultado**: tareas duplicadas + jerarquía rota

## Solución Implementada

### 1. Modificación en `action_confirm()` (`addons/spora_segment/models/sale_order.py`)

```python
def action_confirm(self):
    """Override to create hierarchical tasks from segments.

    Para presupuestos CON segmentos:
    1. Desactiva temporalmente service_tracking='no' en productos
    2. Llama super() para confirmar orden (SIN crear tareas nativas)
    3. Crea proyecto manualmente (tracking='no' previene creación automática)
    4. Crea tareas jerárquicas (segmentos + productos)
    5. Restaura service_tracking original

    Para presupuestos SIN segmentos:
    - Flujo Odoo nativo normal (sin cambios)
    """
    # Identificar presupuestos con segmentos
    orders_with_segments = self.filtered(lambda o: o.segment_ids)

    # Guardar service_tracking original
    tracking_backup = {}
    for order in orders_with_segments:
        for line in order.order_line:
            if line.product_id.type == 'service':
                tracking_backup[line.product_id.id] = line.product_id.service_tracking
                line.product_id.service_tracking = 'no'  # Desactivar temporalmente

    try:
        # Confirmación nativa (sin crear tareas)
        res = super().action_confirm()

        # Para órdenes con segmentos: crear proyecto + tareas
        for order in orders_with_segments:
            project = order._ensure_project_exists()
            if project:
                order._create_segment_tasks()

        # Restaurar service_tracking
        for product_id, original_tracking in tracking_backup.items():
            product = self.env['product.product'].browse(product_id)
            if product.exists():
                product.service_tracking = original_tracking

    except Exception as e:
        # Restaurar tracking incluso en error
        for product_id, original_tracking in tracking_backup.items():
            product = self.env['product.product'].browse(product_id)
            if product.exists():
                product.service_tracking = original_tracking
        raise

    return res
```

### 2. Nuevo método `_ensure_project_exists()`

```python
def _ensure_project_exists(self):
    """Asegura que existe proyecto para este presupuesto. Crea si necesario.

    Retorna:
        project.project: proyecto existente o recién creado
    """
    self.ensure_one()

    # Verificar si proyecto ya existe
    project = self._get_project()
    if project:
        return project

    # Obtener primera línea de servicio para vincular
    service_line = self.order_line.filtered(
        lambda l: l.product_id.type == 'service'
    )[:1]

    # Crear proyecto
    project = self.env['project.project'].create({
        'name': self.name,
        'partner_id': self.partner_id.id,
        'company_id': self.company_id.id,
        'sale_line_id': service_line.id if service_line else False,
    })

    return project
```

### 3. Mejoras en `_create_segment_tasks()`

- **Idempotencia mejorada**: verifica tareas existentes antes de crear
- **Context flag**: previene ejecución concurrente
- **Validaciones**: proyecto activo, segmentos válidos

### 4. Tests de Regresión (`test_no_duplicate_tasks.py`)

```python
def test_no_duplicate_tasks_with_segments(self):
    """Verifica que confirmar presupuesto crea número correcto de tareas sin duplicados.

    Escenario:
    - 1 segmento raíz
    - 2 segmentos hijos
    - 2 productos asignados a hijos

    Esperado:
    - 3 tareas de segmentos (1 raíz + 2 hijos)
    - 2 tareas de productos (bajo segmentos)
    - Total: 5 tareas
    - Jerarquía correcta: productos tienen parent_id
    """
    # Crear presupuesto con segmentos y productos
    order = self.create_order_with_segments()

    # Confirmar
    order.action_confirm()

    # Verificar resultados
    tasks = self.env['project.task'].search([('sale_order_id', '=', order.id)])

    self.assertEqual(len(tasks), 5, 'Debe crear exactamente 5 tareas')

    segment_tasks = tasks.filtered(lambda t: t.segment_id)
    self.assertEqual(len(segment_tasks), 3, 'Debe crear 3 tareas de segmentos')

    product_tasks = tasks.filtered(lambda t: t.sale_line_id and not t.segment_id)
    self.assertEqual(len(product_tasks), 2, 'Debe crear 2 tareas de productos')

    orphan_products = product_tasks.filtered(lambda t: not t.parent_id)
    self.assertEqual(len(orphan_products), 0, 'Ningún producto debe ser huérfano')

    root_tasks = tasks.filtered(lambda t: not t.parent_id)
    self.assertEqual(len(root_tasks), 1, 'Solo segmento raíz debe ser raíz')
```

## Prevención Futura

### 1. Detección de Conflictos

Añadido método `check_task_creation_conflicts()` para detectar:
- Módulos conflictivos instalados
- Productos con `service_tracking` activo

### 2. Validación en Tests

Tests cubren:
- Creación correcta de tareas
- Jerarquía intacta
- Idempotencia
- Restauración de `service_tracking`

### 3. Logging Detallado

Añadidos logs en puntos clave:
- Inicio de procesamiento de presupuesto con segmentos
- Creación de proyecto
- Ejecución de `_create_segment_tasks()`
- Advertencias cuando no se encuentra proyecto

## Validación Pendiente

### Pasos para validar fix:

1. **Crear presupuesto nuevo** (NO usar S00003)
2. **Añadir estructura de segmentos**:
   - 1 segmento raíz
   - 2-3 segmentos hijos
3. **Añadir productos de servicio** asignados a segmentos hijos
4. **Confirmar presupuesto**
5. **Verificar**:
   - Número de tareas creadas = segmentos + productos
   - Jerarquía correcta (productos bajo segmentos)
   - Sin duplicados
   - Solo 1 tarea raíz (segmento raíz)

### SQL para verificar tareas:

```sql
-- Ver tareas del presupuesto
SELECT
    t.id,
    t.name,
    t.parent_id,
    t.segment_id,
    t.sale_line_id,
    CASE WHEN t.segment_id IS NOT NULL THEN 'SEGMENT' ELSE 'PRODUCT' END as type
FROM project_task t
WHERE t.sale_order_id = (SELECT id FROM sale_order WHERE name = 'S00XXX')
ORDER BY t.parent_id NULLS FIRST, t.id;
```

## Archivos Modificados

- `addons/spora_segment/models/sale_order.py`: Lógica principal
- `addons/spora_segment/tests/test_no_duplicate_tasks.py`: Tests de regresión

## Commit

```bash
git add addons/spora_segment/
git commit -m "fix(spora_segment): prevent duplicate task creation on order confirmation

PROBLEMA:
- Presupuestos con segmentos creaban tareas duplicadas (81 en lugar de 51)
- Jerarquía rota: productos como raíz en lugar de subtareas de segmentos
- Causa: service_tracking='task_in_project' hace que Odoo nativo cree tareas antes

SOLUCIÓN:
- Desactivar temporalmente service_tracking durante confirmación
- Crear proyecto manualmente (tracking='no' previene creación automática)
- Crear tareas jerárquicas (segmentos + productos)
- Restaurar service_tracking original

CAMBIOS:
- action_confirm(): filtrar presupuestos con segmentos, desactivar/restaurar tracking
- _ensure_project_exists(): crear proyecto manualmente con sale_line_id
- _create_segment_tasks(): mejor idempotencia y validaciones
- test_no_duplicate_tasks.py: tests de regresión completos

VALIDACIÓN:
- Tests unitarios implementados
- Pendiente validación manual desde UI Odoo

Refs: BUG_FIX_DOCUMENTATION.md"
```

## Próximos Pasos

1. ✅ Código implementado
2. ✅ Tests escritos
3. ⏳ **Validación manual desde UI** (pendiente)
4. ⏳ Commit del fix
5. ⏳ Actualizar CHANGELOG.md
6. ⏳ Documentar en mensaje público Odoo

## Notas Técnicas

### Por qué no modificar `service_tracking` permanentemente:

- `service_tracking` es configuración de producto (global)
- Cambiar permanentemente afectaría TODOS los presupuestos
- Solución temporal solo afecta confirmación con segmentos

### Por qué crear proyecto manualmente:

- `service_tracking='no'` previene creación automática de proyecto
- Necesitamos proyecto para crear tareas
- Creación manual con `sale_line_id` correcto permite que `_get_project()` lo encuentre

### Alternativas consideradas:

1. **Desinstalar módulo conflictivo**: No existe módulo externo
2. **Modificar productos permanentemente**: Afectaría flujo normal sin segmentos
3. **Interceptar creación de tareas nativas**: Más complejo, mayor riesgo de bugs

### Decisión final:

Desactivación temporal de `service_tracking` es:
- Menos invasiva
- Más mantenible
- No afecta flujo normal (presupuestos sin segmentos)
- Fácil de revertir si necesario
