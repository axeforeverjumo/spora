# Spora - Odoo 18

Entorno de desarrollo Odoo 18 con Docker.

## Inicio rápido

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

## Acceso

- **URL**: http://localhost:8069
- **Base de datos**: crear una nueva con el wizard
- **Master password**: admin
- **Usuario por defecto**: admin
- **Contraseña**: la que definas durante la creación de la BD

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

## Base de datos

- **Host**: localhost:5432
- **Usuario**: odoo
- **Contraseña**: odoo
- **Base de datos**: postgres (por defecto)

Puedes crear múltiples bases de datos desde la interfaz de Odoo.
