# Arquitectura del Sistema - Sprint 4 Provesi

## Visión General

El sistema está diseñado para cumplir con dos Atributos de Calidad (ASRs):
1. **Latencia**: Consultas de inventario en menos de 2 segundos
2. **Seguridad**: Solo GESTOR puede modificar/eliminar ítems de pedidos

## Arquitectura de Microservicios

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (HTML/JS + Auth0)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Auth0 (Identity Provider)                │
│                    Emite JWT con roles                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kong API Gateway                          │
│              (Punto de entrada único)                        │
└──────┬───────────────┬───────────────┬──────────────────────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│   Auth      │ │  Inventory   │ │   Orders     │
│  Service    │ │   Service    │ │   Service    │
│ (Node.js)   │ │ (Django)     │ │ (Django)     │
│ Port: 3000  │ │ Port: 8000   │ │ Port: 8001   │
└──────┬──────┘ └──────┬────────┘ └──────┬───────┘
       │              │                  │
       │              │                  │
       │      ┌───────┴───────┐          │
       │      │               │          │
       │      ▼               ▼          ▼
       │  ┌─────────┐   ┌─────────┐ ┌─────────┐
       │  │PostgreSQL│   │ MongoDB │ │PostgreSQL│
       │  │ (Write)  │   │ (Read)  │ │ (Orders) │
       │  └─────────┘   └─────────┘ └─────────┘
       │
       │ (Validación JWT)
       │
       └─────────────────┐
                         │
                         ▼
                   ┌─────────┐
                   │ Auth    │
                   │ Service │
                   └─────────┘
```

## Componentes

### 1. Frontend Unificado

- **Tecnología**: HTML5, JavaScript, Auth0 SPA SDK
- **Funcionalidades**:
  - Autenticación con Auth0
  - Pruebas de latencia (SQL vs NoSQL)
  - Pruebas de seguridad (RBAC)
  - Visualización de resultados

### 2. Auth Service (Node.js/Express)

- **Tecnología**: Node.js 18, Express
- **Responsabilidades**:
  - Validación de tokens JWT de Auth0
  - Decodificación de tokens
  - Extracción de roles
- **Endpoints**:
  - `POST /api/v1/auth/validate`: Valida token y retorna rol
  - `POST /api/v1/auth/decode`: Decodifica token (debug)

### 3. Inventory Service (Python/Django)

- **Tecnología**: Python 3.11, Django 4.2
- **Patrón**: CQRS (Command Query Responsibility Segregation)
- **Write Model (PostgreSQL)**:
  - Productos con categorías
  - Transacciones de inventario
  - Consistencia transaccional
- **Read Model (MongoDB)**:
  - Documentos desnormalizados
  - Optimizado para consultas rápidas
  - Sincronización desde PostgreSQL
- **Endpoints**:
  - `GET /api/v1/inventory/sql-list`: Consulta lenta (PostgreSQL)
  - `GET /api/v1/inventory/nosql-list`: Consulta rápida (MongoDB)

### 4. Orders Service (Python/Django)

- **Tecnología**: Python 3.11, Django 4.2
- **Patrón**: RBAC (Role-Based Access Control)
- **Base de Datos**: PostgreSQL
- **Seguridad**:
  - Middleware `@require_gestor_role`
  - Validación de JWT vía Auth Service
  - Rechazo de OPERARIO con 403
- **Endpoints**:
  - `POST /api/v1/orders`: Crear pedido
  - `GET /api/v1/orders/{id}`: Ver pedido (lectura)
  - `PUT /api/v1/orders/{id}/items/{item_id}`: Modificar ítem (GESTOR)
  - `DELETE /api/v1/orders/{id}/items/{item_id}/delete`: Eliminar ítem (GESTOR)

## Patrones y Tácticas

### CQRS (Command Query Responsibility Segregation)

**Problema**: Consultas complejas en PostgreSQL son lentas con 100,000+ registros.

**Solución**: Separar escritura (PostgreSQL) de lectura (MongoDB).

**Beneficios**:
- Consultas rápidas en MongoDB (< 2s)
- Consistencia en PostgreSQL
- Escalabilidad independiente

**Flujo**:
1. Escritura → PostgreSQL
2. Sincronización → MongoDB (desnormalizado)
3. Lectura → MongoDB (rápida)

### RBAC (Role-Based Access Control)

**Problema**: Solo GESTOR debe poder modificar/eliminar ítems.

**Solución**: Middleware que valida JWT y extrae rol.

**Flujo**:
1. Request con JWT en header
2. Middleware llama a Auth Service
3. Auth Service valida y retorna rol
4. Si rol ≠ GESTOR → 403 Forbidden
5. Si rol = GESTOR → Ejecuta acción

### Identidad Federada (Auth0)

**Problema**: Gestión compleja de autenticación y autorización.

**Solución**: Delegar a Auth0, confiar en JWT.

**Beneficios**:
- Gestión centralizada de usuarios
- Tokens firmados criptográficamente
- Roles en claims personalizados

## Bases de Datos

### PostgreSQL

**Uso**:
- Write Model de Inventario
- Base de datos de Pedidos
- Transacciones críticas

**Esquema**:
- `products`: Productos de seguridad
- `product_categories`: Categorías
- `inventory_transactions`: Auditoría
- `orders`: Pedidos
- `order_items`: Ítems de pedidos

### MongoDB

**Uso**:
- Read Model de Inventario (CQRS)
- Documentos desnormalizados
- Consultas optimizadas

**Estructura**:
```json
{
  "_id": "GLOVE-001",
  "sku": "GLOVE-001",
  "name": "Guantes de Seguridad",
  "category": {
    "id": 1,
    "name": "Guantes de Seguridad"
  },
  "unit_price": 15.50,
  "stock_quantity": 100,
  ...
}
```

## Flujos Principales

### Flujo de Consulta de Inventario (Latencia)

1. Usuario solicita inventario
2. Frontend → Inventory Service
3. Inventory Service → MongoDB (Read Model)
4. MongoDB retorna documentos desnormalizados
5. Respuesta en < 2 segundos ✅

### Flujo de Modificación de Pedido (Seguridad)

1. Usuario (GESTOR/OPERARIO) intenta modificar ítem
2. Frontend envía JWT en header
3. Orders Service recibe request
4. Middleware extrae JWT
5. Middleware → Auth Service (validar)
6. Auth Service valida y retorna rol
7. Si OPERARIO → 403 Forbidden ❌
8. Si GESTOR → Ejecuta modificación ✅

## Infraestructura (AWS)

### Componentes

- **VPC**: Red privada aislada
- **EC2 Instances**: 3 microservicios + MongoDB
- **RDS PostgreSQL**: Base de datos relacional
- **Security Groups**: Control de acceso
- **Internet Gateway**: Acceso público

### Despliegue

- **Terraform**: Infraestructura como código
- **Docker**: Contenedores opcionales
- **Variables de entorno**: Configuración centralizada

## Seguridad

### Capas de Seguridad

1. **Auth0**: Autenticación y emisión de JWT
2. **Kong Gateway**: Validación inicial de tokens
3. **Auth Service**: Validación criptográfica de JWT
4. **RBAC Middleware**: Control de acceso por rol
5. **Security Groups**: Firewall de red

### Validación JWT

1. Verificar firma (RS256)
2. Verificar expiración
3. Verificar audience
4. Verificar issuer
5. Extraer rol de custom claim

## Escalabilidad

### Horizontal

- Microservicios independientes
- Bases de datos separadas
- Load balancers por servicio

### Vertical

- Optimización de índices
- Caché en MongoDB
- Connection pooling

## Monitoreo y Observabilidad

### Métricas Clave

- Latencia de consultas (ASR 1)
- Tasa de rechazo 403 (ASR 2)
- Tiempo de validación JWT
- Throughput por servicio

### Logs

- Requests/Responses
- Errores de validación
- Sincronización CQRS

