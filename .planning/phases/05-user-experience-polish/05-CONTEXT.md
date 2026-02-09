---
phase: 05-user-experience-polish
discussed: 2026-02-05
participants: [user, claude]
status: complete
---

# Phase 5: User Experience & Polish - Context

**Phase Goal**: Users navigate segment hierarchies efficiently with visual feedback and intuitive ordering

**Discussed**: 2026-02-05
**Language**: Spanish (user preference)

## User Decisions

### A. Vista Árbol: Estilo de Indentación (UX-01)

**Decision**: Indentación automática de Odoo + ayuda visual con colores por nivel

**Implementation**:
- Vista árbol usa atributo `recursive="1"` (Odoo nativo)
- Añadir colores diferentes según nivel de profundidad (campo `level`)
- Ejemplo: nivel 1 = azul oscuro, nivel 2 = azul medio, nivel 3 = azul claro, nivel 4 = gris

**Rationale**: Aprovechar funcionalidad nativa de Odoo + mejora visual para escaneo rápido de profundidad

---

### B. Breadcrumb Path: Visualización de Ruta Completa (UX-02)

**Decision**: Campo separado `full_path` visible como columna en vista árbol

**Implementation**:
- Campo computed `full_path` (ejemplo: "Fase 1 / Materiales / Cartas")
- Separador: "/"
- `store=True` para performance (evita recalcular en cada consulta)
- Columna visible en vista árbol (además del nombre corto)
- Permite ordenar/filtrar por ruta completa

**Rationale**:
- Más profesional para contexto ERP empresarial
- Funcional: ordenable, filtrable, exportable
- Accesible: no requiere hover del mouse
- Útil para debugging de jerarquías

**Alternatives rejected**:
- `display_name` con ruta: Muy largo, ocupa mucho espacio en selects
- Tooltip/hover: Menos funcional, no exportable, no accesible

---

### C. Drag-and-Drop: Restricciones de Movimiento (UX-03)

**Decision**: Solo permitir reordenar entre hermanos del mismo padre

**Implementation**:
- Widget `handle` en campo `sequence`
- Constraint: mismo `parent_id` para drag-and-drop
- NO permitir cambiar de padre arrastrando (sería caótico)
- Para cambiar padre, usar campo `parent_id` manualmente

**Rationale**: "sino es una locura" - mantener estructura jerárquica intacta durante reordenamiento

---

### D. Smart Buttons: Información Visible (UX-04, UX-05)

**Decision**: Mostrar cantidad de hijos Y niveles de profundidad

**Implementation**:
- Smart button muestra: "5 Sub-segmentos (2 niveles)"
- Formato: `{count} Sub-segmentos ({depth} niveles)`
- Si depth = 1: "5 Sub-segmentos (1 nivel)"
- Si count = 0: Botón deshabilitado o gris

**Rationale**: Dar contexto completo de complejidad de sub-árbol sin navegar

---

### E. Contador de Productos: Nivel de Detalle (UX-06)

**Decision**: Mostrar número de productos Y subtotal monetario

**Implementation**:
- Columna en vista árbol: "Productos: 8 (€1,245.50)"
- Formato: `{count} ({currency}{amount})`
- Suma solo productos directos del segmento (NO sub-segmentos)
- Campo computed `product_count` y `product_subtotal`

**Rationale**: Información más completa para escaneo rápido de contenido del segmento

**Note**: Ya existe campo `subtotal` (productos propios) vs `total` (propios + hijos). Reutilizar `subtotal` para el monetario.

---

### F. Performance: Strategy para Campos Computed

**Decision**: `store=True` para TODOS los campos calculados

**Implementation**:
- `full_path`: `store=True` (recalcula al cambiar parent_id o name)
- `product_count`: `store=True` (recalcula al cambiar line_ids)
- `product_subtotal`: Ya existe como `subtotal` con `store=True`
- `child_count`: `store=True` (recalcula al cambiar child_ids)
- `child_depth`: `store=True` (recalcula al cambiar child_ids recursivamente)

**Rationale**:
- Priorizar velocidad de lectura (99% de operaciones)
- Aceptar costo de write amplification (1% de operaciones)
- Jerarquías cambian poco después de setup inicial

**Trade-off accepted**: Writes más lentos (recalcular cascada) por reads instantáneos

---

## Implementation Notes

### Colores por Nivel (Opción A)

**Approach**: Usar `decoration-*` attributes en vista árbol

```xml
<tree decoration-primary="level == 1"
      decoration-info="level == 2"
      decoration-muted="level == 3"
      decoration-warning="level == 4">
```

**Odoo decoration classes**:
- `decoration-primary`: Azul (nivel 1 - epics)
- `decoration-info`: Azul claro (nivel 2 - tasks)
- `decoration-muted`: Gris (nivel 3 - subtasks)
- `decoration-warning`: Amarillo/naranja (nivel 4 - último nivel)

**Alternative**: CSS custom con `oe_read_only` classes si decorations no suficientes.

---

### Full Path Calculation (Opción B)

**Pattern**: Recursive parent traversal

```python
@api.depends('name', 'parent_id.full_path')
def _compute_full_path(self):
    for segment in self:
        if segment.parent_id:
            segment.full_path = f"{segment.parent_id.full_path} / {segment.name}"
        else:
            segment.full_path = segment.name
```

**Edge case**: Root segments (parent_id = False) → full_path = name

---

### Child Depth Calculation (Opción D)

**Pattern**: Recursive max depth of children

```python
@api.depends('child_ids', 'child_ids.child_depth')
def _compute_child_depth(self):
    for segment in self:
        if not segment.child_ids:
            segment.child_depth = 0
        else:
            segment.child_depth = max(segment.child_ids.mapped('child_depth')) + 1
```

**Example**:
- Segment with no children: depth = 0
- Segment with 1 level of children: depth = 1
- Segment with 2 levels of descendants: depth = 2

---

### Product Count & Subtotal (Opción E)

**Reuse existing fields**:
- `product_count`: New computed field (count of line_ids)
- `product_subtotal`: Reuse existing `subtotal` field (already computed, already stores sum of line_ids.price_subtotal)

```python
@api.depends('line_ids')
def _compute_product_count(self):
    for segment in self:
        segment.product_count = len(segment.line_ids)
```

**Note**: `subtotal` field already exists from Phase 2 (SALE-07).

---

### Drag-and-Drop Implementation (Opción C)

**Odoo pattern**: `handle` widget on `sequence` field

```xml
<field name="sequence" widget="handle"/>
```

**Constraint**: Odoo's drag-and-drop naturally respects parent_id grouping in tree view. No additional constraint needed if view correctly groups by parent.

**Alternative**: If cross-parent dragging possible, add constraint:

```python
@api.constrains('sequence', 'parent_id')
def _check_sequence_parent(self):
    # Validate sequence changes don't cross parent boundaries
    pass
```

---

## Requirements Coverage

| Requirement | Decision | Implementation |
|-------------|----------|----------------|
| UX-01 | Indentación automática + colores | `recursive="1"` + `decoration-*` |
| UX-02 | Campo `full_path` separado | Computed `@api.depends('parent_id.full_path')` |
| UX-03 | Drag-and-drop solo hermanos | Widget `handle` + parent_id grouping |
| UX-04 | Smart button con contador | Button con `child_ids` count + depth |
| UX-05 | Incluir niveles de profundidad | Computed `child_depth` field |
| UX-06 | Productos: número + subtotal | `product_count` + reuse `subtotal` |

**All requirements mapped**: 6/6 (100%)

---

## Open Questions

None - all gray areas resolved.

---

## Next Steps

1. Create 05-RESEARCH.md (Odoo UI patterns for tree views, widgets, smart buttons)
2. Create execution plans (05-01-PLAN.md, 05-02-PLAN.md)
3. Execute implementation
4. Verify UX improvements

---

*Context gathered: 2026-02-05*
*Ready for: Research phase*
