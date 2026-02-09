# Testing Manual: Filtrado de Tareas Raíz

## Objetivo
Verificar que la vista de tareas del proyecto muestra solo tareas raíz por defecto.

## Pre-requisitos
- Módulo `spora_segment` actualizado
- Proyecto S00001 existente con 3 tareas raíz y 14 tareas totales
- Odoo corriendo en http://localhost:8069

## Pasos de Testing

### Test 1: Verificar Filtro por Defecto

1. **Abrir Odoo**
   - Navegar a http://localhost:8069
   - Login con credenciales (admin/admin)

2. **Navegar al Proyecto**
   - Ir a "Proyecto" en menú principal
   - Buscar y abrir proyecto "S00001"

3. **Abrir Vista de Tareas**
   - Click en botón "Tareas" (smart button en la parte superior)

4. **Verificar Estado Inicial** ✅
   - **Esperado**: Solo 3 tareas visibles en la lista
   - **Esperado**: Filtro "Root Tasks Only" está activo (resaltado) en barra superior
   - **Esperado**: Contador muestra "3" (no 14)

5. **Verificar Nombres de Tareas** ✅
   - Las 3 tareas visibles deben ser tareas raíz (sin parent_id)
   - NO deben aparecer subtareas en la lista inicial

### Test 2: Desactivar Filtro

1. **Desactivar Filtro**
   - Click en el filtro "Root Tasks Only" (en barra superior)
   - El filtro debe deseleccionarse (sin resaltar)

2. **Verificar Todas las Tareas** ✅
   - **Esperado**: Ahora aparecen las 14 tareas
   - **Esperado**: Se ven tareas raíz Y subtareas
   - **Esperado**: Contador muestra "14"

### Test 3: Expandir Tareas en Vista Árbol

1. **Reactivar Filtro**
   - Click nuevamente en "Root Tasks Only" para activarlo
   - Volver a ver solo 3 tareas

2. **Expandir Tarea Individual**
   - Click en el icono ▶ (flecha) al lado de una tarea raíz
   - **Esperado**: Se despliegan las subtareas de esa tarea
   - **Esperado**: Las subtareas son visibles dentro de su padre

### Test 4: Acceso a Subtareas desde Formulario

1. **Abrir Tarea Raíz**
   - Double-click en una de las 3 tareas raíz
   - Se abre el formulario de la tarea

2. **Verificar Subtareas**
   - Buscar campo/tab de subtareas en el formulario
   - **Esperado**: Subtareas son accesibles desde aquí
   - **Esperado**: Usuario puede navegar a subtareas sin problema

### Test 5: Crear Nueva Tarea

1. **Crear Tarea desde Vista Filtrada**
   - Con filtro "Root Tasks Only" activo
   - Click en "Crear" o "+"
   - Crear nueva tarea (sin parent_id)

2. **Verificar Nueva Tarea** ✅
   - **Esperado**: Nueva tarea aparece en la lista filtrada
   - **Esperado**: Contador ahora muestra "4"

## Resultados Esperados

| Escenario | Filtro Activo | Tareas Visibles | Contador |
|-----------|---------------|-----------------|----------|
| Default (inicial) | ✅ Sí | 3 (raíz) | 3 |
| Filtro desactivado | ❌ No | 14 (todas) | 14 |
| Filtro reactivado | ✅ Sí | 3 (raíz) | 3 |
| Expandir tarea | ✅ Sí | 3 + subtareas expandidas | 3 |

## Verificación de Integridad

### Verificar que NO se rompe funcionalidad existente:

1. **Búsquedas**: Buscar tarea específica funciona correctamente
2. **Ordenamiento**: Ordenar columnas funciona
3. **Otros filtros**: Otros filtros (estado, prioridad) funcionan
4. **Edición**: Editar tareas funciona normalmente
5. **Borrado**: Eliminar tareas funciona

## Casos Edge

### Proyecto sin Subtareas
1. Crear proyecto nuevo sin subtareas (solo tareas raíz)
2. **Esperado**: Filtro activo pero todas las tareas son visibles (porque todas son raíz)

### Proyecto sin Tareas
1. Crear proyecto vacío
2. Abrir vista de tareas
3. **Esperado**: Vista vacía con mensaje "No hay tareas"

## Rollback (si falla)

Si el filtrado causa problemas:

```bash
# Opción 1: Desactivar filtro manualmente en UI
# Click en "Root Tasks Only" para desactivar permanentemente

# Opción 2: Revertir código
git revert HEAD

# Opción 3: Actualizar módulo a versión anterior
docker compose exec odoo odoo -d spora -u spora_segment
```

## Logs y Debug

Si hay problemas, revisar logs:

```bash
# Ver logs de Odoo
docker compose logs odoo -f --tail=100

# Buscar errores relacionados con project.task
docker compose logs odoo | grep -i "project.task"

# Ver llamadas al action_view_tasks
docker compose logs odoo | grep -i "action_view_tasks"
```

## Checklist Final

- [ ] Filtro "Root Tasks Only" visible en barra de búsqueda
- [ ] Filtro activo por defecto al abrir tareas desde proyecto
- [ ] Solo tareas raíz visibles con filtro activo
- [ ] Contador muestra número correcto de tareas
- [ ] Desactivar filtro muestra todas las tareas
- [ ] Expandir tarea muestra subtareas (si aplica)
- [ ] Crear/editar/borrar tareas funciona normalmente
- [ ] Otros filtros y búsquedas funcionan correctamente

## Contacto

Si encuentras problemas:
- Revisar README.md en `addons/spora_segment/README.md`
- Ejecutar tests: `docker compose exec odoo python3 /usr/bin/odoo --test-enable --stop-after-init -d spora -u spora_segment --test-tags=spora_segment`
- Reportar a Juan Manuel con logs completos
