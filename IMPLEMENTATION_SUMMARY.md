# Implementación: Numeración Outline y Reporte Jerárquico

**Fecha:** 2025-02-09
**Versión:** 18.0.1.2.0
**Estado:** Implementado - Pendiente de validación

## Cambios Implementados

### 1. Modelo (sale_order_segment.py)

#### Campo outline_number añadido
- Campo computado y almacenado: `outline_number`
- Tipo: `Char`
- Compute: `_compute_outline_number`
- Dependencias: `parent_id`, `parent_id.outline_number`, `sequence`, `order_id`
- Store: `True`
- Recursive: `True`

#### Método _compute_outline_number
```python
@api.depends('parent_id', 'parent_id.outline_number', 'sequence', 'order_id')
def _compute_outline_number(self):
    """Calcula número outline basado en jerarquía y sequence."""
    for segment in self:
        if not segment.parent_id:
            # Segmento raíz: contar posición entre hermanos raíz
            siblings = segment.order_id.segment_ids.filtered(
                lambda s: not s.parent_id
            ).sorted('sequence')
            if segment.id in siblings.ids:
                position = siblings.ids.index(segment.id) + 1
                segment.outline_number = str(position)
            else:
                segment.outline_number = '0'
        else:
            # Hijo: padre.número + "." + posición entre hermanos
            siblings = segment.parent_id.child_ids.sorted('sequence')
            if segment.id in siblings.ids:
                position = siblings.ids.index(segment.id) + 1
                segment.outline_number = f"{segment.parent_id.outline_number}.{position}"
            else:
                segment.outline_number = '0.0'
```

#### Actualización de _compute_display_name
- Formato actualizado: `SO001 / 1.1. Segment Name`
- Incluye outline_number en el display name

#### Actualización de _order
- Anterior: `'sequence, id'`
- Nuevo: `'outline_number, sequence, id'`

### 2. Vistas (sale_order_segment_views.xml)

#### Vista Tree Actualizada
- Nueva columna "Nº" como primera columna (después de handle)
- Ancho: 80px
- Atributo `default_order="outline_number"` añadido al elemento `<list>`

### 3. Reportes de Impresión

#### Nuevos Archivos Creados

**report/sale_order_segment_report.xml**
- Definición del reporte: `action_report_sale_order_segment`
- Nombre: "Presupuesto Jerárquico"
- Modelo: `sale.order`
- Tipo: `qweb-pdf`
- Binding: Disponible en el menú Print de Sale Orders

**report/sale_order_segment_template.xml**
- Template principal: `report_saleorder_document_segment`
- Template recursivo: `segment_line_recursive`
- Características:
  - Cabecera con datos del cliente y fecha
  - Tabla con columnas: Nº, Descripción, Cant., Precio Unit., Total
  - Segmentos en negrita con fondo gris
  - Indentación proporcional al nivel (level * 15px)
  - Productos con bullet points
  - Totales destacados en negrita
  - Total general al final
  - Sección opcional de observaciones

### 4. Tests (test_outline_numbering.py)

#### 8 Tests Implementados

1. **test_outline_number_root_segments**: Verifica numeración 1, 2, 3 para segmentos raíz
2. **test_outline_number_nested**: Verifica numeración jerárquica 1.1, 1.2
3. **test_outline_number_resequence**: Verifica recálculo al cambiar sequence
4. **test_outline_number_three_levels**: Verifica jerarquía profunda 1.1.1, 1.1.2
5. **test_outline_number_multiple_trees**: Verifica múltiples árboles independientes
6. **test_outline_number_display_name**: Verifica display_name incluye número
7. **test_outline_number_ordering**: Verifica ordenamiento por outline_number
8. **test_outline_number_four_levels**: Verifica soporte hasta 4 niveles

### 5. __manifest__.py

#### Actualizado
- Versión: `18.0.1.0.0` → `18.0.1.2.0`
- Summary actualizado: incluye "outline numbering and print reports"
- Description actualizada
- Nuevos archivos de data:
  - `report/sale_order_segment_report.xml`
  - `report/sale_order_segment_template.xml`

## Instrucciones de Actualización

### Opción 1: Actualización desde UI (Recomendado)

1. Acceder a Odoo: http://localhost:8069
2. Ir a Settings > Apps
3. Activar "Developer Mode" si no está activo
4. Buscar "Spora" en la lista de aplicaciones
5. Hacer clic en "Update" o "Upgrade"
6. Esperar a que la actualización se complete
7. Verificar que no hay errores en el log

### Opción 2: Actualización desde CLI

```bash
# Detener el servidor
docker exec spora_odoo pkill -f odoo-bin

# Esperar unos segundos
sleep 3

# Ejecutar actualización
docker exec spora_odoo odoo -d spora -r odoo -w odoo --db_host db -u spora_segment --stop-after-init

# Reiniciar servidor
docker compose restart odoo
```

### Opción 3: Ejecutar Tests

```bash
# Detener el servidor
docker exec spora_odoo pkill -f odoo-bin

# Ejecutar tests
docker exec spora_odoo odoo -d spora -r odoo -w odoo --db_host db --test-enable --stop-after-init -u spora_segment

# Reiniciar servidor
docker compose restart odoo
```

## Verificación Post-Actualización

### 1. Verificar Vista Tree

1. Ir a Sales > Quotations
2. Abrir un presupuesto existente
3. Ir a la pestaña "Segments"
4. Verificar que aparece la columna "Nº" con numeración automática (1, 1.1, 1.2, 2, 2.1, etc.)

### 2. Verificar Display Name

1. Crear o editar una tarea de proyecto
2. Seleccionar un segmento en el campo "Segment"
3. Verificar que se muestra: "SO001 / 1.1. Segment Name"

### 3. Verificar Reporte PDF

1. Ir a Sales > Quotations
2. Abrir un presupuesto con segmentos jerárquicos
3. Hacer clic en Print > Presupuesto Jerárquico
4. Verificar:
   - Columna "Nº" con numeración outline
   - Segmentos en negrita con fondo gris
   - Indentación visual proporcional al nivel
   - Productos con bullet points
   - Totales destacados
   - Total general al final

### 4. Verificar Reordenamiento

1. Editar un presupuesto con segmentos
2. Cambiar el campo "Sequence" de un segmento (ej: de 20 a 5)
3. Guardar y recargar
4. Verificar que el outline_number se recalcula automáticamente

## Casos de Prueba Sugeridos

### Test Case 1: Segmentos Raíz

**Input:**
```
Fase 1 (sequence=10)
Fase 2 (sequence=20)
Fase 3 (sequence=30)
```

**Expected Output:**
```
1. Fase 1
2. Fase 2
3. Fase 3
```

### Test Case 2: Jerarquía 2 Niveles

**Input:**
```
Proyecto Web (sequence=10)
├── Diseño (sequence=10)
└── Desarrollo (sequence=20)
```

**Expected Output:**
```
1. Proyecto Web
  1.1. Diseño
  1.2. Desarrollo
```

### Test Case 3: Jerarquía 3 Niveles

**Input:**
```
Fase 1 (sequence=10)
└── Diseño (sequence=10)
    ├── Mockups (sequence=10)
    └── Wireframes (sequence=20)
```

**Expected Output:**
```
1. Fase 1
  1.1. Diseño
    1.1.1. Mockups
    1.1.2. Wireframes
```

### Test Case 4: Reordenamiento

**Action:** Cambiar sequence de "Fase 2" de 20 a 5

**Before:**
```
1. Fase 1 (sequence=10)
2. Fase 2 (sequence=20)
3. Fase 3 (sequence=30)
```

**After:**
```
1. Fase 2 (sequence=5)
2. Fase 1 (sequence=10)
3. Fase 3 (sequence=30)
```

### Test Case 5: PDF con Jerarquía Compleja

**Setup:**
```
1. Proyecto Web (€10,000)
   • Consultoría (10h × €100) = €1,000
   1.1. Diseño (€5,000)
       • Mockups (20h × €150) = €3,000
       • Wireframes (10h × €200) = €2,000
   1.2. Desarrollo (€4,000)
       • Frontend (15h × €100) = €1,500
       • Backend (20h × €125) = €2,500
```

**Verify:**
- Indentación correcta en PDF
- Totales destacados en negrita
- Productos con bullets
- Total general €10,000 al final

## Archivos Modificados/Creados

### Modificados
- ✅ `addons/spora_segment/models/sale_order_segment.py`
- ✅ `addons/spora_segment/views/sale_order_segment_views.xml`
- ✅ `addons/spora_segment/__manifest__.py`
- ✅ `addons/spora_segment/tests/__init__.py`

### Creados
- ✅ `addons/spora_segment/report/` (directorio)
- ✅ `addons/spora_segment/report/sale_order_segment_report.xml`
- ✅ `addons/spora_segment/report/sale_order_segment_template.xml`
- ✅ `addons/spora_segment/tests/test_outline_numbering.py`

## Estado de Implementación

- ✅ Campo outline_number implementado
- ✅ Método _compute_outline_number implementado
- ✅ _compute_display_name actualizado
- ✅ _order actualizado
- ✅ Vista tree actualizada con columna "Nº"
- ✅ Reporte PDF principal creado
- ✅ Template recursivo creado
- ✅ 8 tests unitarios implementados
- ✅ __manifest__.py actualizado a v1.2.0
- ⏳ **Tests pendientes de ejecución**
- ⏳ **Actualización del módulo pendiente**
- ⏳ **Validación en presupuesto real pendiente**
- ⏳ **Generación de PDF de prueba pendiente**

## Próximos Pasos

1. Actualizar el módulo en Odoo (seguir instrucciones arriba)
2. Ejecutar tests para verificar funcionamiento
3. Validar numeración en vista tree de un presupuesto real
4. Generar y verificar PDF de ejemplo
5. Documentar cualquier issue encontrado
6. Commit y push a GitHub (opcional)

## Notas Técnicas

### Dependencias del Campo Computado

El campo `outline_number` se recalcula automáticamente cuando:
- Cambia el `parent_id` de un segmento
- Cambia el `outline_number` del padre (cascada recursiva)
- Cambia el `sequence` de un segmento
- Se añaden/eliminan segmentos en el `order_id`

Esto garantiza que la numeración siempre esté actualizada sin intervención manual.

### Recursividad en Templates QWeb

El template `segment_line_recursive` se llama a sí mismo para procesar hijos:

```xml
<t t-foreach="segment.child_ids.sorted('outline_number')" t-as="segment">
    <t t-call="spora_segment.segment_line_recursive"/>
</t>
```

Esto soporta jerarquías de hasta 4 niveles (limitado por MAX_HIERARCHY_DEPTH).

### Indentación Visual

La indentación en el PDF se calcula dinámicamente:
- Segmentos: `level * 15px`
- Productos: `(level + 1) * 15px`

Ejemplo para un producto en un segmento de nivel 2:
- Indentación = (2 + 1) * 15px = 45px

## Troubleshooting

### "outline_number no aparece en la vista"

**Causa:** Módulo no actualizado
**Solución:** Actualizar módulo desde Apps > Spora > Update

### "Los números no se recalculan al cambiar sequence"

**Causa:** Cache de computed field
**Solución:** Refrescar la página o invalidar recordset

### "El PDF no muestra jerarquía"

**Causa:** Segmentos sin parent_id definido
**Solución:** Verificar que los segmentos hijos tengan parent_id correcto

### "Tests fallan con KeyError"

**Causa:** Segment ID no existe en siblings.ids
**Solución:** Verificar que los segmentos estén guardados antes de acceder a .ids

## Referencias

- Diseño original: `docs/plans/2025-02-09-segment-outline-numbering-design.md`
- Odoo 18 Computed Fields: https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html#computed-fields
- QWeb Reports: https://www.odoo.com/documentation/18.0/developer/reference/frontend/qweb.html
