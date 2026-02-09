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
- **Usuario**: `admin@example.com`
- **Contraseña**: `admin`

## 📦 Módulo: spora_segment

**Estado**: ✅ Instalado y configurado

### Características

- ✅ **Segmentos jerárquicos**: Hasta 4 niveles de profundidad
- ✅ **Integración con presupuestos**: Organiza líneas de venta en segmentos
- ✅ **Creación automática de tareas**: Al confirmar presupuesto
- ✅ **Cálculo de totales**: Subtotales y totales recursivos
- ✅ **UX mejorado**: Full path, depth, product count
- ✅ **Seguridad**: Reglas para Sales User/Manager
- ✅ **98 tests**: Suite completa pasando

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
