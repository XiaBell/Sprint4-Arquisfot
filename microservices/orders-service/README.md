# Orders Service - Módulo de Gestión de Pedidos

Microservicio Python/Django que implementa RBAC para controlar el acceso a operaciones de modificación/eliminación de ítems de pedidos.

## Seguridad (RBAC)

- **GESTOR**: Puede modificar y eliminar ítems de pedidos
- **OPERARIO**: Solo puede leer pedidos, recibe 403 Forbidden al intentar modificar/eliminar

## Endpoints

### POST /api/v1/orders
Crear un nuevo pedido (cualquier usuario autenticado)

### GET /api/v1/orders/list
Listar pedidos (lectura, ambos roles)

### GET /api/v1/orders/{order_id}
Obtener detalles de un pedido con sus ítems (lectura, ambos roles)

### PUT /api/v1/orders/{order_id}/items/{item_id}
Marcar ítem como no disponible o cambiar estado
**REQUIERE ROL: GESTOR**
- Si OPERARIO intenta: 403 Forbidden
- Si GESTOR: 200 OK

### DELETE /api/v1/orders/{order_id}/items/{item_id}/delete
Eliminar ítem de un pedido
**REQUIERE ROL: GESTOR**
- Si OPERARIO intenta: 403 Forbidden
- Si GESTOR: 204 No Content

### GET /api/v1/health
Health check del servicio

## Middleware de Seguridad

El decorator `@require_gestor_role`:
1. Extrae el JWT del header `Authorization: Bearer <token>`
2. Llama al Auth Service para validar el token
3. Extrae el rol del usuario
4. Si el rol no es GESTOR, devuelve 403 Forbidden
5. Si es GESTOR, permite la ejecución

## Configuración

Variables de entorno:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `AUTH_SERVICE_URL`: URL del Auth Service (default: http://localhost:3000)

## Ejecución

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

O con Docker:
```bash
docker-compose up
```

## Trade-off de Seguridad

El middleware mide el tiempo de validación del JWT para analizar el trade-off entre seguridad y latencia.

