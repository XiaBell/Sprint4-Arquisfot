# Quick Start Guide - Sprint 4 Provesi

## Inicio Rápido Local

### 1. Prerrequisitos

- Docker y Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL client (opcional)
- MongoDB client (opcional)

### 2. Configurar Auth0

1. Crear cuenta en [Auth0](https://auth0.com)
2. Crear una API:
   - Name: `Provesi API`
   - Identifier: `https://api.provesi.com`
3. Crear una Single Page Application:
   - Name: `Provesi Frontend`
   - Application Type: `Single Page Application`
4. Configurar una Rule/Action para inyectar el rol:
   ```javascript
   exports.onExecutePostLogin = async (event, api) => {
     const namespace = 'https://provesi.com/';
     if (event.authorization) {
       api.idToken.setCustomClaim(namespace + 'rol', event.authorization.roles[0] || 'OPERARIO');
       api.accessToken.setCustomClaim(namespace + 'rol', event.authorization.roles[0] || 'OPERARIO');
     }
   };
   ```
5. Crear roles: `GESTOR` y `OPERARIO`
6. Asignar roles a usuarios de prueba

### 3. Configurar Variables de Entorno

Crear archivos `.env` en cada microservicio:

**microservices/auth-service/.env:**
```
PORT=3000
AUTH0_DOMAIN=tu-tenant.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
```

**microservices/inventory-service/.env:**
```
DEBUG=True
SECRET_KEY=django-insecure-dev-key
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=provesi123
POSTGRES_HOST=postgres-inventory
POSTGRES_PORT=5432
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
```

**microservices/orders-service/.env:**
```
DEBUG=True
SECRET_KEY=django-insecure-dev-key
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=provesi123
POSTGRES_HOST=postgres-orders
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://auth-service:3000
```

### 4. Iniciar Servicios

```bash
# Opción 1: Usando Make
make start-local

# Opción 2: Usando Docker Compose directamente
docker-compose -f docker-compose.local.yml up -d
```

### 5. Ejecutar Migraciones

```bash
# Inventory Service
docker-compose -f docker-compose.local.yml exec inventory-service python manage.py migrate

# Orders Service
docker-compose -f docker-compose.local.yml exec orders-service python manage.py migrate
```

### 6. Poblar Base de Datos

```bash
# Poblar con 100,000 productos
docker-compose -f docker-compose.local.yml exec inventory-service python /app/scripts/populate_inventory.py

# O desde el host (si tienes acceso)
cd scripts
pip install -r requirements.txt
python populate_inventory.py
```

### 7. Configurar Frontend

1. Editar `frontend/index.html`
2. Actualizar configuración de Auth0:
   ```javascript
   const auth0Config = {
       domain: 'tu-tenant.auth0.com',
       clientId: 'tu_client_id',
       // ...
   };
   ```
3. Abrir `frontend/index.html` en un navegador (o servir con un servidor web)

### 8. Probar Endpoints

#### Health Checks

```bash
curl http://localhost:3000/health
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
```

#### Prueba de Latencia

```bash
# Consulta SQL (lenta)
curl http://localhost:8000/api/v1/inventory/sql-list

# Consulta NoSQL (rápida)
curl http://localhost:8000/api/v1/inventory/nosql-list
```

#### Prueba de Seguridad

1. Obtener token JWT de Auth0 (usando frontend o Postman)
2. Probar con rol OPERARIO:
   ```bash
   curl -X PUT http://localhost:8001/api/v1/orders/1/items/1 \
     -H "Authorization: Bearer TOKEN_OPERARIO" \
     -H "Content-Type: application/json" \
     -d '{"status": "UNAVAILABLE"}'
   # Debe retornar 403 Forbidden
   ```

3. Probar con rol GESTOR:
   ```bash
   curl -X PUT http://localhost:8001/api/v1/orders/1/items/1 \
     -H "Authorization: Bearer TOKEN_GESTOR" \
     -H "Content-Type: application/json" \
     -d '{"status": "UNAVAILABLE"}'
   # Debe retornar 200 OK
   ```

## Comandos Útiles

```bash
# Ver logs
docker-compose -f docker-compose.local.yml logs -f

# Detener servicios
make stop-local

# Limpiar todo
make clean

# Sincronizar productos a MongoDB
make sync
```

## Troubleshooting

### Error: "Connection refused" a PostgreSQL
- Verificar que el contenedor esté corriendo: `docker ps`
- Verificar variables de entorno
- Verificar que las migraciones se hayan ejecutado

### Error: "Connection refused" a MongoDB
- Verificar que MongoDB esté corriendo
- Verificar variables de entorno
- Verificar que los productos se hayan sincronizado

### Error: "Invalid token" en Auth Service
- Verificar AUTH0_DOMAIN y AUTH0_AUDIENCE
- Verificar que el token incluya el claim `https://provesi.com/rol`
- Verificar que la Rule/Action esté configurada correctamente

### Error: "403 Forbidden" cuando debería funcionar
- Verificar que el usuario tenga el rol GESTOR asignado en Auth0
- Verificar que el token incluya el claim del rol
- Verificar logs del Auth Service

## Próximos Pasos

1. Revisar documentación completa en `docs/`
2. Ejecutar experimentos según `docs/EXPERIMENTS.md`
3. Configurar despliegue en AWS según `docs/DEPLOYMENT.md`

