# Sprint 4 - Arquitectura de Software: Latencia y Seguridad

## Descripción del Proyecto

Aplicación de gestión de inventario y pedidos para **Provesi**, empresa que vende insumos de seguridad (guantes, señalizaciones, etc.) a otras empresas.

## Arquitectura

### Microservicios

1. **Módulo Gestión de Inventario** (Python/Django)
   - Implementa CQRS para optimizar latencia
   - Write Model: PostgreSQL
   - Read Model: MongoDB

2. **Módulo Gestión de Pedidos** (Python/Django)
   - Implementa RBAC con Auth0
   - Solo GESTOR puede modificar/eliminar ítems

3. **Módulo Seguridad y Roles** (Node.js/Express)
   - Validación y decodificación de JWT de Auth0
   - Centraliza la lógica de seguridad

### Bases de Datos

- **PostgreSQL**: Datos transaccionales (pedidos, inventario write model)
- **MongoDB**: Modelo de lectura optimizado para inventario

### Infraestructura

- **AWS**: Despliegue en EC2/RDS
- **Terraform**: Infraestructura como código
- **Kong**: API Gateway

## Atributos de Calidad (ASRs)

### ASR 1: Latencia
- **Requisito**: Consultas de inventario en menos de 2 segundos
- **Táctica**: CQRS con MongoDB para lectura optimizada

### ASR 2: Seguridad
- **Requisito**: Solo GESTOR puede modificar/eliminar ítems de pedidos
- **Táctica**: RBAC con Auth0, validación JWT

## Estructura del Proyecto

```
.
├── terraform/              # Infraestructura AWS
├── microservices/
│   ├── auth-service/       # Node.js - Validación JWT
│   ├── inventory-service/  # Python/Django - CQRS
│   └── orders-service/     # Python/Django - RBAC
├── frontend/               # Frontend unificado
├── scripts/                # Scripts de población de datos
└── docs/                   # Documentación
```

## Configuración Inicial

### Auth0

1. Crear una aplicación en Auth0 (tipo API)
2. Configurar Rules/Actions para inyectar el rol en el JWT:
   - Claim: `https://provesi.com/rol`
   - Valores: `GESTOR` o `OPERARIO`

3. Obtener las siguientes variables:
   - `AUTH0_DOMAIN`
   - `AUTH0_AUDIENCE`
   - `AUTH0_CLIENT_ID`
   - `AUTH0_CLIENT_SECRET`

### Variables de Entorno

Cada microservicio requiere configuración mediante variables de entorno. Ver archivos `.env.example` en cada servicio.

## Despliegue

1. Configurar credenciales de AWS
2. Configurar variables de Auth0 en Terraform
3. Ejecutar `terraform init` y `terraform apply`
4. Esperar a que las instancias estén listas
5. Ejecutar scripts de población de datos

## Pruebas

### Prueba de Latencia

- Endpoint SQL: `GET /api/v1/inventory/sql-list`
- Endpoint NoSQL: `GET /api/v1/inventory/nosql-list`
- Medir tiempo de respuesta (objetivo: < 2s para NoSQL)

### Prueba de Seguridad

- Autenticarse como GESTOR: Debe poder modificar/eliminar ítems
- Autenticarse como OPERARIO: Debe recibir 403 Forbidden

## Tecnologías

- **Backend**: Python/Django, Node.js/Express
- **Bases de Datos**: PostgreSQL, MongoDB
- **Infraestructura**: AWS, Terraform
- **Gateway**: Kong
- **Autenticación**: Auth0

