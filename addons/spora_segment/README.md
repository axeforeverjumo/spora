# Módulo: spora_segment

## Descripción
Módulo para gestión de segmentos presupuestarios en proyectos y presupuestos Odoo.

## Funcionalidades

### Gestión de Segmentos
- Creación de segmentos presupuestarios vinculados a presupuestos
- Asignación de tareas a segmentos específicos
- Validación de consistencia entre proyecto y presupuesto

### Filtrado de Tareas (UX Enhancement)
Por defecto, la vista de tareas del proyecto muestra **solo tareas raíz** (parent_id = False) para evitar abrumar al usuario con subtareas en proyectos con jerarquías profundas.

#### Comportamiento
- Al abrir "Tareas" desde un proyecto, solo se muestran las tareas de nivel superior
- El filtro "Root Tasks Only" está activo por defecto (visible en la barra de búsqueda)
- Los usuarios pueden:
  - **Desactivar el filtro** haciendo clic en "Root Tasks Only" para ver todas las tareas
  - **Expandir tareas** en la vista de árbol para ver subtareas
  - **Acceder a subtareas** desde el formulario de la tarea padre

#### Justificación
En proyectos con estructura de segmentos (ej: proyecto S00001 con 3 tareas raíz pero 14 tareas totales), mostrar todas las tareas por defecto dificulta la navegación. Este filtro mejora la UX sin eliminar funcionalidad.

#### Implementación Técnica
- **Python**: Override de `project.project.action_view_tasks()` para activar filtro por defecto
- **XML**: Nuevo filtro de búsqueda `root_tasks_only` en vista de tareas
- **Context**: `search_default_root_tasks_only: 1` activa el filtro automáticamente

### Protección de Integridad
- Prevención de cambio de presupuesto cuando hay tareas con segmentos
- Validaciones al guardar proyectos

## Instalación
1. Copiar módulo a carpeta `addons/`
2. Actualizar lista de aplicaciones en Odoo
3. Buscar "spora_segment" e instalar

## Configuración
No requiere configuración adicional.

## Uso

### Filtrado de Tareas
1. Abrir un proyecto
2. Click en botón "Tareas"
3. Por defecto verás solo tareas raíz
4. Para ver todas las tareas:
   - **Opción 1**: Click en filtro "Root Tasks Only" (barra superior) para desactivarlo
   - **Opción 2**: Expandir tareas individuales en la vista de árbol

### Asignación de Segmentos
1. Abrir tarea en vista formulario
2. Campo "Budget Segment" visible solo si proyecto tiene presupuesto vinculado
3. Seleccionar segmento del presupuesto

## Dependencias
- `base`
- `project`
- `sale_project`

## Modelos

### Extendidos
- `project.project`: Validación de cambio de presupuesto, filtrado de tareas
- `project.task`: Nuevo campo `segment_id`
- `sale.order`: Gestión de segmentos
- `sale.order.segment`: Modelo de segmentos presupuestarios

## Vistas

### Vistas Principales
- **Form view** (project.task): Campo segment_id
- **Search view** (project.task): Filtro "Root Tasks Only"

### Filtros de Búsqueda
- `root_tasks_only`: Muestra solo tareas sin parent_id (activado por defecto)

## Security
- Usuarios: Lectura y escritura de tareas y segmentos
- Managers: Control completo

## Tests
Ejecutar tests:
```bash
docker compose exec odoo python3 /usr/bin/odoo --test-enable --stop-after-init -d spora -u spora_segment --test-tags=spora_segment
```

### Test Coverage
- `test_sale_order_segment.py`: Tests de modelo de segmentos
- `test_sale_order_integration.py`: Integración presupuesto-proyecto
- `test_project_task_segment.py`: Asignación de segmentos a tareas
- `test_automated_task_creation.py`: Creación automática de tareas
- `test_ux_enhancements.py`: Validaciones UX
- `test_project_task_filtering.py`: Filtrado de tareas raíz

## Troubleshooting

### No veo el filtro "Root Tasks Only"
- Verificar que el módulo esté actualizado
- Refrescar navegador (Ctrl+F5)
- Verificar logs de Odoo para errores de vista

### El filtro no se activa automáticamente
- Verificar que `action_view_tasks()` está llamando al super correctamente
- Revisar contexto del action en logs

## Changelog

### v1.1.0 (2025-02-09)
- Agregado: Filtrado automático de tareas raíz por defecto
- Mejora: UX en proyectos con jerarquías profundas
- Tests: Cobertura de filtrado de tareas

### v1.0.0 (Initial)
- Modelo de segmentos presupuestarios
- Vinculación de tareas a segmentos
- Validaciones de integridad

## Autor
JUMO Technologies - Juan Manuel Ojeda

## Licencia
LGPL-3
