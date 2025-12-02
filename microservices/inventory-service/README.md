# Inventory Service - Módulo de Gestión de Inventario

Microservicio Python/Django que implementa CQRS para optimizar la latencia de consultas de inventario.

## Arquitectura CQRS

- **Write Model (PostgreSQL)**: Datos transaccionales y consistentes
- **Read Model (MongoDB)**: Documentos desnormalizados para consultas rápidas

## Endpoints

### GET /api/v1/inventory/sql-list
Consulta compleja a PostgreSQL (Línea Base - LENTA)
- Simula JOINs costosos
- Retorna productos con información de categoría y transacciones

### GET /api/v1/inventory/nosql-list
Consulta simple a MongoDB (CQRS Optimizado - RÁPIDA)
- Documentos desnormalizados
- Sin JOINs necesarios
- Objetivo: < 2 segundos

### GET /api/v1/inventory/stats
Estadísticas del inventario desde MongoDB

### GET /api/v1/health
Health check del servicio

## Configuración

Variables de entorno:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_DB`

## Ejecución

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

O con Docker:
```bash
docker-compose up
```

## Sincronización CQRS

Los productos deben sincronizarse desde PostgreSQL a MongoDB. Ver scripts en `/scripts/sync_inventory.py`.

