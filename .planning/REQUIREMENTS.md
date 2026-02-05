# Requirements: Spora - Presupuestos Jerárquicos

**Defined:** 2026-02-05
**Core Value:** Conversión automática de estructura jerárquica de presupuesto a tareas de proyecto manteniendo relaciones padre-hijo

## v1 Requirements

### Hierarchical Model (HIER)

- [ ] **HIER-01**: Sistema crea modelo `sale.order.segment` con campo `parent_id` (Many2one a sí mismo)
- [ ] **HIER-02**: Modelo tiene campo `child_ids` (One2many inverso de parent_id)
- [ ] **HIER-03**: Modelo usa `_parent_store = True` para optimización de consultas jerárquicas
- [ ] **HIER-04**: Sistema calcula nivel de segmento automáticamente según profundidad (campo computed)
- [ ] **HIER-05**: Sistema previene referencias circulares al asignar parent_id
- [ ] **HIER-06**: Sistema limita jerarquía a máximo 4 niveles de profundidad
- [ ] **HIER-07**: Usuario puede asignar campo `sequence` para ordenar segmentos hermanos
- [ ] **HIER-08**: Segmento puede tener productos (via sale.order.line) sin tener sub-segmentos
- [ ] **HIER-09**: Segmento puede tener sub-segmentos sin tener productos
- [ ] **HIER-10**: Segmento puede tener productos Y sub-segmentos simultáneamente

### Sale Order Integration (SALE)

- [ ] **SALE-01**: Sale order tiene relación `segment_ids` (One2many a sale.order.segment)
- [ ] **SALE-02**: Sale order line tiene campo `segment_id` (Many2one a sale.order.segment)
- [ ] **SALE-03**: Usuario ve vista árbol expandible de segmentos en formulario de sale order
- [ ] **SALE-04**: Usuario puede crear nuevo segmento desde formulario de sale order
- [ ] **SALE-05**: Usuario puede asignar segmento padre al crear segmento
- [ ] **SALE-06**: Usuario puede asignar productos (sale.order.line) a segmento específico
- [ ] **SALE-07**: Sistema calcula subtotal de segmento (suma de productos propios)
- [ ] **SALE-08**: Sistema calcula total de segmento (subtotal propio + total de sub-segmentos)
- [ ] **SALE-09**: Usuario ve subtotales por segmento en vista árbol
- [ ] **SALE-10**: Usuario puede expandir/contraer niveles de segmentos en vista árbol
- [ ] **SALE-11**: Smart button en sale order muestra cantidad de segmentos y abre vista filtrada

### Project Integration (PROJ)

- [ ] **PROJ-01**: Project task tiene campo `segment_id` (Many2one a sale.order.segment)
- [ ] **PROJ-02**: Usuario ve referencia a segmento en formulario de project task
- [ ] **PROJ-03**: Sistema valida que segment_id pertenece al sale order vinculado al proyecto

### Automated Task Creation (AUTO)

- [ ] **AUTO-01**: Sistema crea proyecto automáticamente al confirmar sale order (si no existe)
- [ ] **AUTO-02**: Sistema crea una tarea por cada segmento al confirmar sale order
- [ ] **AUTO-03**: Tarea creada tiene `parent_id` apuntando a tarea del segmento padre (mantiene jerarquía)
- [ ] **AUTO-04**: Tarea raíz (nivel 1) no tiene parent_id
- [ ] **AUTO-05**: Sistema transfiere nombre del segmento a nombre de tarea
- [ ] **AUTO-06**: Sistema transfiere productos del segmento como descripción o campo relacionado en tarea
- [ ] **AUTO-07**: Sistema calcula horas estimadas de tarea sumando cantidades de productos del segmento
- [ ] **AUTO-08**: Sistema transfiere responsable del segmento (si existe) a assigned_user_id de tarea
- [ ] **AUTO-09**: Sistema transfiere fecha inicio/fin del segmento (si existe) a tarea
- [ ] **AUTO-10**: Sistema vincula tarea creada al segmento original via segment_id
- [ ] **AUTO-11**: Sistema usa savepoints para aislar errores en creación batch de tareas
- [ ] **AUTO-12**: Si falla creación de una tarea, no afecta a tareas ya creadas en lote

### Security & Access (SEC)

- [ ] **SEC-01**: Archivo `ir.model.access.csv` define permisos para sale.order.segment
- [ ] **SEC-02**: Usuario con rol Sales/User puede crear y leer segmentos
- [ ] **SEC-03**: Usuario con rol Sales/Manager puede crear, leer, actualizar y eliminar segmentos
- [ ] **SEC-04**: Permisos de segmento respetan permisos del sale order padre

### User Experience (UX)

- [ ] **UX-01**: Vista árbol usa atributo `recursive="1"` para mostrar jerarquía correctamente
- [ ] **UX-02**: Usuario ve nivel de profundidad visualmente (indentación) en vista árbol
- [ ] **UX-03**: Usuario puede reordenar segmentos hermanos mediante drag & drop (handle widget)
- [ ] **UX-04**: Sistema muestra path completo del segmento (ej: "Fase 1 / Materiales / Cartas")
- [ ] **UX-05**: Formulario de segmento muestra smart button a sub-segmentos
- [ ] **UX-06**: Usuario ve cantidad de productos asignados a segmento en vista árbol

## v2 Requirements

### Advanced Hierarchy (v2)

- **HIER-V2-01**: Copy segmento con toda su jerarquía de sub-segmentos
- **HIER-V2-02**: Mover subtree completo entre diferentes segmentos padre
- **HIER-V2-03**: Exportar/importar jerarquía de segmentos con formato preservado
- **HIER-V2-04**: Templates de segmentos reutilizables

### Enhanced Automation (v2)

- **AUTO-V2-01**: Re-sincronización de tareas si cambia estructura de segmentos después de confirmar
- **AUTO-V2-02**: Creación de tareas condicional (solo ciertos tipos de segmentos)
- **AUTO-V2-03**: Mapeo personalizable de campos segmento → tarea

### Advanced UX (v2)

- **UX-V2-01**: Vista Gantt de segmentos con dependencias
- **UX-V2-02**: Filtros y búsqueda hierarchy-aware
- **UX-V2-03**: Indicadores visuales custom por nivel (colores, iconos)
- **UX-V2-04**: Dashboard de análisis de presupuestos por segmentos

## Out of Scope

| Feature | Reason |
|---------|--------|
| Más de 4 niveles de anidación | Balance complejidad/casos de uso reales (80% usan ≤3 niveles) |
| Múltiples padres (DAG) | Complejidad exponencial, casos de uso poco claros |
| Productos de texto libre | Mantener trazabilidad con catálogo Odoo |
| Conversión manual de segmentos a tareas | Automática reduce errores y pasos |
| Edición de tareas desde presupuesto | Tareas se gestionan en módulo project nativo |
| Real-time computed totals | Write amplification, usar store=True con depends |
| Modificación de core Odoo | Solo extensiones via _inherit para upgrade safety |

## Traceability

Mapeo de requisitos a fases (completado durante creación de roadmap).

| Requirement | Phase | Status |
|-------------|-------|--------|
| HIER-01 | Phase 1 | Pending |
| HIER-02 | Phase 1 | Pending |
| HIER-03 | Phase 1 | Pending |
| HIER-04 | Phase 1 | Pending |
| HIER-05 | Phase 1 | Pending |
| HIER-06 | Phase 1 | Pending |
| HIER-07 | Phase 1 | Pending |
| HIER-08 | Phase 1 | Pending |
| HIER-09 | Phase 1 | Pending |
| HIER-10 | Phase 1 | Pending |
| SALE-01 | Phase 2 | Pending |
| SALE-02 | Phase 2 | Pending |
| SALE-03 | Phase 2 | Pending |
| SALE-04 | Phase 2 | Pending |
| SALE-05 | Phase 2 | Pending |
| SALE-06 | Phase 2 | Pending |
| SALE-07 | Phase 2 | Pending |
| SALE-08 | Phase 2 | Pending |
| SALE-09 | Phase 2 | Pending |
| SALE-10 | Phase 2 | Pending |
| SALE-11 | Phase 2 | Pending |
| PROJ-01 | Phase 3 | Pending |
| PROJ-02 | Phase 3 | Pending |
| PROJ-03 | Phase 3 | Pending |
| SEC-01 | Phase 3 | Pending |
| SEC-02 | Phase 3 | Pending |
| SEC-03 | Phase 3 | Pending |
| SEC-04 | Phase 3 | Pending |
| AUTO-01 | Phase 4 | Pending |
| AUTO-02 | Phase 4 | Pending |
| AUTO-03 | Phase 4 | Pending |
| AUTO-04 | Phase 4 | Pending |
| AUTO-05 | Phase 4 | Pending |
| AUTO-06 | Phase 4 | Pending |
| AUTO-07 | Phase 4 | Pending |
| AUTO-08 | Phase 4 | Pending |
| AUTO-09 | Phase 4 | Pending |
| AUTO-10 | Phase 4 | Pending |
| AUTO-11 | Phase 4 | Pending |
| AUTO-12 | Phase 4 | Pending |
| UX-01 | Phase 5 | Pending |
| UX-02 | Phase 5 | Pending |
| UX-03 | Phase 5 | Pending |
| UX-04 | Phase 5 | Pending |
| UX-05 | Phase 5 | Pending |
| UX-06 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 46 total
- Mapped to phases: 46 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-05*
*Last updated: 2026-02-05 after roadmap creation*
