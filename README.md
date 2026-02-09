# Spora - Odoo 18 Module

Módulo Odoo 18 para gestión de presupuestos jerárquicos con creación automática de tareas de proyecto.

## 🚀 Inicio rápido

```bash
# Levantar los contenedores
docker-compose up -d

# Ver logs
docker-compose logs -f odoo

# Parar los contenedores
docker-compose down

# Reiniciar Odoo
docker-compose restart odoo
```

## 🔐 Acceso

- **URL**: http://localhost:8069
- **Base de datos**: `odoo` (ya creada y configurada)
- **Usuario**: `admin`
- **Contraseña**: `admin`

## 📦 Módulo: spora_segment

**Estado**: ✅ Instalado y configurado
**Versión**: 1.2.0 (2026-02-09)

### Características Principales

#### 🏗️ Estructura Jerárquica
- ✅ **Segmentos jerárquicos**: Hasta 4 niveles de profundidad
- ✅ **Integración con presupuestos**: Organiza líneas de venta en segmentos
- ✅ **Cálculo de totales**: Subtotales y totales recursivos
- ✅ **Vista jerárquica visual**: Smart button "Vista Jerárquica" con badge de conteo

#### 🤖 Creación Automática de Tareas
- ✅ **Tareas por segmento**: Un task por cada segmento (jerárquico)
- ✅ **Tareas por producto**: Un task individual por cada producto (NEW v1.1.0)
  - Horas asignadas desde cantidad de producto
  - Descripción incluida en task
  - Vinculado a sale.order.line
- ✅ **Algoritmo DFS recursivo**: Procesamiento en profundidad
- ✅ **Idempotencia**: Detecta y omite tareas duplicadas
- ✅ **Isolation por savepoint**: Previene fallos en cascada

#### 🎨 UX Mejorado
- ✅ **Numeración outline automática**: Sistema de numeración jerárquica (1, 1.1, 1.2, etc.) (NEW v1.2.0)
  - Visible en todas las vistas (columna "Nº")
  - Diferencia segmentos con mismo nombre en padres distintos
  - Actualización automática al reordenar
- ✅ **Full path**: Navegación breadcrumb (ej. "Root / Child / Grandchild")
- ✅ **Indicadores de nivel**: Decoraciones visuales (primario/info/muted/warning)
- ✅ **Product count badge**: Muestra cantidad de productos en segmento
- ✅ **Products Detail column**: Vista previa de productos con cantidades (NEW v1.1.0)
- ✅ **Smart buttons**:
  - Segmentos en presupuesto
  - Sub-segmentos en formulario de segmento
  - Profundidad del árbol (child_depth)

#### 🔒 Seguridad
- ✅ **Reglas de acceso**: Sales User (lectura) / Sales Manager (CRUD)
- ✅ **Record rules**: Aislamiento por orden de venta
- ✅ **Constraints**:
  - C1: Segmento debe pertenecer a misma orden
  - C2: Profundidad máxima (4 niveles)
  - C3: Relación task-segment-order consistente

#### 🧪 Calidad de Código
- ✅ **106 tests**: Suite completa pasando (+8 tests en v1.2.0)
- ✅ **2123 líneas de código de tests**: Cobertura exhaustiva
- ✅ **28 productos de ejemplo**: Datos demo para validación completa

#### 📄 Reportes (NEW v1.2.0)
- ✅ **Presupuesto Jerárquico PDF**: Impresión profesional con jerarquía visual
  - Tabla con indentación proporcional al nivel
  - Totales de segmentos destacados en negrita
  - Productos con bullet points (•)
  - Total general al final
  - Soporta hasta 4 niveles de jerarquía

### Novedades v1.2.0 (2026-02-09)

- **Numeración outline automática**: Sistema 1, 1.1, 1.2, 2, 2.1, etc. visible en todas las vistas
- **Reporte PDF jerárquico**: Impresión profesional con indentación y totales destacados
- **Ordenamiento automático**: Por número outline para navegación lógica
- **8 nuevos tests**: Validación completa del sistema de numeración
- **Display name mejorado**: "S00001 / 1.1. Diseño" en selects y referencias

### Novedades v1.1.0 (2026-02-09)

- **Productos como tareas individuales**: Cada producto ahora genera su propio task (antes era texto en descripción)
- **Vista jerárquica mejorada**: Botón "Vista Jerárquica" con acceso directo
- **Columna Products Detail**: Muestra productos inline en vista de lista
- **Algoritmo optimizado**: DFS recursivo reemplaza BFS iterativo

## Estructura

```
spora/
├── addons/          # Módulos custom (vacío inicialmente)
├── config/          # Configuración de Odoo
├── odoo-data/       # Datos de Odoo (generado automáticamente)
├── postgresql/      # Datos de PostgreSQL (generado automáticamente)
└── docker-compose.yml
```

## Desarrollo

Los módulos custom se colocan en `./addons/` y se cargan automáticamente.

Para actualizar módulos después de cambios:

```bash
docker-compose restart odoo
```

O desde la interfaz: Apps > Update Apps List

## 🗄️ Base de datos

- **Host**: localhost:5432
- **Usuario**: odoo
- **Contraseña**: odoo
- **Base de datos activa**: `odoo`

### Actualizar módulo después de cambios

```bash
# Opción 1: Desde línea de comandos
docker compose exec odoo odoo -d odoo -u spora_segment --stop-after-init -c /etc/odoo/odoo.conf

# Opción 2: Desde interfaz
# Apps > spora_segment > Upgrade

# Opción 3: Ejecutar tests
docker compose exec odoo odoo -d odoo --test-tags=spora_segment --stop-after-init -c /etc/odoo/odoo.conf
```

## 📝 Documentación técnica

Ver `.planning/` para documentación completa del desarrollo:
- Requirements (REQUIREMENTS.md)
- Roadmap (ROADMAP.md)
- Planes de implementación por fase
- Reportes de verificación
