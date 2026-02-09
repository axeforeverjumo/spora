# Diagnóstico: Presupuesto S00001 sin Proyecto/Tareas

## Fecha
2025-02-09

## Problema Reportado
El usuario confirmó el presupuesto S00001 pero NO se creó automáticamente:
- Proyecto
- Tareas jerárquicas desde segmentos

## Código Analizado

### `sale_order.py` - Método `action_confirm()` (líneas 40-50)
```python
def action_confirm(self):
    """Override to create hierarchical tasks from segments after native flow creates project."""
    # FIRST: Native Odoo flow - creates project, handles service products
    res = super().action_confirm()

    # THEN: Create segment tasks (project now guaranteed to exist)
    for order in self:
        if order.segment_ids:
            order._create_segment_tasks()

    return res
```

### `sale_order.py` - Método `_get_project()` (líneas 52-66)
El método busca el proyecto creado por Odoo nativo de 2 formas:
1. Via `project.project.sale_line_id.order_id`
2. Fallback via `project.task.sale_order_id`

### `sale_order.py` - Método `_create_segment_tasks()` (líneas 68-138)
Incluye logging y validaciones:
- Línea 80-86: Warning si no encuentra proyecto
- Línea 89-95: Warning si proyecto está archivado
- Línea 103-108: Info sobre cantidad de segmentos
- Línea 134-138: Info sobre tareas creadas exitosamente

## Causas Posibles (Orden de Probabilidad)

### CAUSA 1: Productos NO son de tipo 'service' (MÁS PROBABLE)
**Síntoma**: Odoo nativo NO crea proyecto si productos no son servicios.

**Flujo fallido**:
1. Usuario confirma S00001
2. `super().action_confirm()` ejecuta → NO crea proyecto (productos son 'product' o 'consu')
3. `_create_segment_tasks()` ejecuta
4. `_get_project()` NO encuentra proyecto
5. Línea 80-86: Genera WARNING en logs
6. `return` (sale sin crear tareas)

**Evidencia esperada en logs**:
```
WARNING: No project found for order S00001 after confirmation.
Segment tasks will not be created.
This is expected if order has no service products.
```

**Verificación necesaria**:
```python
# Via MCP, obtener líneas de pedido de S00001
mcp__odoo-factoria.search_read(
    model="sale.order.line",
    domain=[("order_id.name", "=", "S00001")],
    fields=["product_id", "product_id.type", "product_id.service_tracking"]
)
```

**Solución**:
1. Cambiar productos a tipo 'service'
2. Configurar `service_tracking` = 'task' o 'project'
3. Re-confirmar presupuesto (si es posible) o crear proyecto manualmente

---

### CAUSA 2: Presupuesto NO tiene segmentos creados
**Síntoma**: La condición `if order.segment_ids:` en línea 47 es False.

**Flujo fallido**:
1. Usuario confirma S00001
2. `super().action_confirm()` ejecuta → crea proyecto (si productos OK)
3. Línea 47: `if order.segment_ids:` → **False**
4. NO se llama a `_create_segment_tasks()`
5. Resultado: Proyecto existe pero sin tareas jerárquicas

**Verificación necesaria**:
```python
# Via MCP, verificar segmentos
mcp__odoo-factoria.get_record(
    model="sale.order",
    domain=[("name", "=", "S00001")],
    fields=["segment_ids"]
)
```

**Solución**:
1. Crear segmentos para S00001
2. Ejecutar manualmente `order._create_segment_tasks()` desde consola Python de Odoo

---

### CAUSA 3: Error durante ejecución de `_create_segment_tasks()`
**Síntoma**: Excepción no capturada o savepoint rollback.

**Posibles errores**:
- Campos requeridos faltantes en project.task
- Permisos insuficientes
- Validaciones de negocio en project.task
- Problema con `parent_id` (referencia circular, parent no existe)

**Evidencia esperada en logs**:
```
ERROR: Failed to create task for segment "...": ...
```

**Verificación necesaria**:
```python
# Buscar logs de error
mcp__odoo-factoria.search_read(
    model="ir.logging",
    domain=[
        ("name", "ilike", "spora_segment"),
        ("level", "=", "error"),
        ("create_date", ">=", "2025-02-09 00:00:00")
    ],
    fields=["message", "create_date"]
)
```

**Solución**: Depende del error específico (ver logs)

---

### CAUSA 4: Módulo `spora_segment` NO está instalado/actualizado
**Síntoma**: El override de `action_confirm()` no se ejecuta.

**Verificación necesaria**:
```python
# Via MCP, verificar estado del módulo
mcp__odoo-factoria.search_read(
    model="ir.module.module",
    domain=[("name", "=", "spora_segment")],
    fields=["name", "state"]
)
```

**Solución**:
1. Instalar módulo si `state != 'installed'`
2. Actualizar módulo si código cambió recientemente

---

## Pasos de Diagnóstico Recomendados (Orden de Ejecución)

### 1. Verificar estado del presupuesto
```python
order = mcp__odoo-factoria.get_record(
    model="sale.order",
    domain=[("name", "=", "S00001")],
    fields=["name", "state", "project_id", "segment_ids", "segment_count"]
)
```

**Qué buscar**:
- `state` debe ser 'sale' (confirmado)
- `segment_count` > 0 (tiene segmentos)
- `project_id` puede ser False o [id, name]

### 2. Verificar segmentos
```python
segments = mcp__odoo-factoria.search_read(
    model="sale.order.segment",
    domain=[("order_id.name", "=", "S00001")],
    fields=["name", "level", "sequence", "parent_id", "line_ids"]
)
```

**Qué buscar**:
- ¿Existen segmentos? (len(segments) > 0)
- ¿Tienen líneas de pedido vinculadas? (line_ids no vacío)

### 3. Verificar productos
```python
lines = mcp__odoo-factoria.search_read(
    model="sale.order.line",
    domain=[("order_id.name", "=", "S00001")],
    fields=["product_id", "product_id.type", "product_id.service_tracking", "product_uom_qty"]
)
```

**Qué buscar**:
- `product_id.type` debe ser 'service' para al menos un producto
- `product_id.service_tracking` debe ser 'task' o 'project'

### 4. Verificar logs de Odoo
```python
logs = mcp__odoo-factoria.search_read(
    model="ir.logging",
    domain=[
        ("name", "ilike", "spora_segment"),
        ("create_date", ">=", "2025-02-09 00:00:00")
    ],
    fields=["name", "message", "level", "create_date"],
    order="create_date desc"
)
```

**Qué buscar**:
- Warnings: "No project found for order S00001"
- Errors: "Failed to create task for segment"
- Info: "Creating tasks for X segments" / "Successfully created X tasks"

### 5. Verificar tareas creadas (si existen)
```python
tasks = mcp__odoo-factoria.search_read(
    model="project.task",
    domain=[("sale_order_id.name", "=", "S00001")],
    fields=["name", "project_id", "segment_id", "parent_id", "allocated_hours"]
)
```

**Qué buscar**:
- ¿Existen tareas?
- ¿Tienen `segment_id` vinculado?
- ¿Tienen jerarquía correcta via `parent_id`?

### 6. Verificar módulo instalado
```python
module = mcp__odoo-factoria.search_read(
    model="ir.module.module",
    domain=[("name", "=", "spora_segment")],
    fields=["name", "state", "latest_version"]
)
```

**Qué buscar**:
- `state` debe ser 'installed'

---

## Soluciones por Causa

### Si CAUSA 1 (Productos no son service):
1. **Configurar productos correctamente**:
   ```python
   # Via interfaz Odoo o MCP
   for line in order.order_line:
       line.product_id.write({
           'type': 'service',
           'service_tracking': 'task'  # o 'project'
       })
   ```

2. **Re-confirmar presupuesto** (si es posible volver a borrador):
   ```python
   order.action_draft()  # Si estado lo permite
   order.action_confirm()
   ```

3. **Si NO se puede re-confirmar** (presupuesto ya confirmado):
   - Opción A: Crear proyecto manualmente y ejecutar `_create_segment_tasks()`
   - Opción B: Cancelar y crear nuevo presupuesto

### Si CAUSA 2 (Sin segmentos):
1. Crear segmentos via interfaz Odoo
2. Ejecutar manualmente desde consola Python:
   ```python
   order = env['sale.order'].search([('name', '=', 'S00001')])
   order._create_segment_tasks()
   ```

### Si CAUSA 3 (Errores durante creación):
- Revisar logs específicos
- Corregir datos o código según error

### Si CAUSA 4 (Módulo no instalado):
1. Instalar módulo: Apps → Actualizar lista de aplicaciones → Buscar "spora_segment" → Instalar
2. Actualizar módulo si ya instalado: Apps → spora_segment → Actualizar

---

## Checklist de Validación Post-Solución

Una vez aplicada la solución:

- [ ] Presupuesto S00001 tiene `state = 'sale'`
- [ ] Presupuesto tiene `segment_ids` con al menos 1 segmento
- [ ] Existe proyecto vinculado (`project_id` no False)
- [ ] Existen tareas en proyecto con `segment_id` vinculado
- [ ] Tareas tienen jerarquía correcta (parent_id según nivel de segmento)
- [ ] Tareas tienen `allocated_hours` calculado desde líneas
- [ ] Logs de Odoo muestran "Successfully created X tasks for order S00001"

---

## Próximos Pasos

1. **Ejecutar diagnóstico via MCP** (pasos 1-6 arriba)
2. **Identificar causa raíz**
3. **Aplicar solución correspondiente**
4. **Validar resultado con checklist**
5. **Documentar solución aplicada en este archivo**
6. **Crear guía de usuario** si es problema de configuración

---

## Resultado del Diagnóstico
*(Pendiente de completar después de ejecutar verificaciones MCP)*

### Causa identificada:


### Solución aplicada:


### Resultado:

