# Guía de Despliegue - Sprint 4 Provesi

## Prerrequisitos

1. **AWS Account** con credenciales configuradas
2. **Terraform** >= 1.0 instalado
3. **Auth0 Account** con aplicación configurada
4. **SSH Key Pair** para acceso a instancias EC2

## Configuración de Auth0

### 1. Crear API en Auth0

1. Ir a Auth0 Dashboard > Applications > APIs
2. Crear nueva API:
   - Name: `Provesi API`
   - Identifier: `https://api.provesi.com`
   - Signing Algorithm: `RS256`

### 2. Configurar Roles

1. Ir a User Management > Roles
2. Crear dos roles:
   - `GESTOR`: Gestor de bodega con permisos completos
   - `OPERARIO`: Operario con permisos de lectura

### 3. Configurar Rules/Actions para inyectar rol en JWT

Crear una Rule o Action en Auth0 que agregue el rol al token:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://provesi.com/';
  
  if (event.authorization) {
    api.idToken.setCustomClaim(namespace + 'rol', event.authorization.roles[0] || 'OPERARIO');
    api.accessToken.setCustomClaim(namespace + 'rol', event.authorization.roles[0] || 'OPERARIO');
  }
};
```

### 4. Obtener Variables de Auth0

- `AUTH0_DOMAIN`: Tu dominio de Auth0 (ej: `tu-tenant.auth0.com`)
- `AUTH0_AUDIENCE`: `https://api.provesi.com`
- `AUTH0_CLIENT_ID`: Client ID de tu aplicación
- `AUTH0_CLIENT_SECRET`: Client Secret de tu aplicación

## Configuración de Terraform

### 1. Configurar Variables

Copiar `terraform/terraform.tfvars.example` a `terraform/terraform.tfvars` y completar:

```hcl
aws_region = "us-east-1"

db_username = "provesi_admin"
db_password = "TU_PASSWORD_SEGURO_AQUI"

ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."

auth0_domain       = "tu-tenant.auth0.com"
auth0_audience     = "https://api.provesi.com"
auth0_client_id    = "tu_client_id"
auth0_client_secret = "tu_client_secret"
```

### 2. Desplegar Infraestructura

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Obtener IPs de las Instancias

```bash
terraform output
```

Anotar las IPs públicas de los servicios y la IP privada de MongoDB.

## Configuración de Microservicios

### 1. Auth Service (Node.js)

SSH a la instancia:
```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<AUTH_SERVICE_IP>
```

Clonar código y configurar:
```bash
cd /opt
git clone <repo-url> provesi
cd provesi/microservices/auth-service

# Crear .env
cat > .env << EOF
PORT=3000
AUTH0_DOMAIN=tu-tenant.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF

# Instalar y ejecutar
npm install
npm start
```

O usar Docker:
```bash
docker build -t auth-service .
docker run -d -p 3000:3000 --env-file .env auth-service
```

### 2. Inventory Service (Python/Django)

SSH a la instancia:
```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>
```

Configurar:
```bash
cd /opt/provesi/microservices/inventory-service

# Crear .env
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=<DB_PASSWORD>
POSTGRES_HOST=<POSTGRES_ENDPOINT>
POSTGRES_PORT=5432
MONGODB_HOST=<MONGODB_PRIVATE_IP>
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
EOF

# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Poblar datos
cd ../../scripts
pip install -r requirements.txt
python populate_inventory.py

# Ejecutar
python manage.py runserver 0.0.0.0:8000
```

### 3. Orders Service (Python/Django)

SSH a la instancia:
```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<ORDERS_SERVICE_IP>
```

Configurar:
```bash
cd /opt/provesi/microservices/orders-service

# Crear .env
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=<DB_PASSWORD>
POSTGRES_HOST=<POSTGRES_ENDPOINT>
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://<AUTH_SERVICE_IP>:3000
EOF

# Instalar y ejecutar
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

## Configuración del Frontend

1. Editar `frontend/index.html`
2. Actualizar configuración de Auth0:
   ```javascript
   const auth0Config = {
       domain: 'tu-tenant.auth0.com',
       clientId: 'tu_client_id',
       // ...
   };
   ```
3. Actualizar URLs de servicios:
   ```javascript
   const AUTH_SERVICE_URL = 'http://<AUTH_SERVICE_IP>:3000';
   const INVENTORY_SERVICE_URL = 'http://<INVENTORY_SERVICE_IP>:8000';
   const ORDERS_SERVICE_URL = 'http://<ORDERS_SERVICE_IP>:8001';
   ```
4. Servir el frontend (puede usar un servidor web simple o S3 + CloudFront)

## Verificación

1. Verificar health checks:
   - `http://<AUTH_SERVICE_IP>:3000/health`
   - `http://<INVENTORY_SERVICE_IP>:8000/api/v1/health`
   - `http://<ORDERS_SERVICE_IP>:8001/api/v1/health`

2. Probar endpoints:
   - Inventario SQL: `GET /api/v1/inventory/sql-list`
   - Inventario NoSQL: `GET /api/v1/inventory/nosql-list`
   - Crear pedido: `POST /api/v1/orders`
   - Modificar ítem (requiere GESTOR): `PUT /api/v1/orders/{id}/items/{item_id}`

## Troubleshooting

### Error de conexión a PostgreSQL
- Verificar Security Groups
- Verificar que RDS esté en subnets privadas
- Verificar credenciales

### Error de conexión a MongoDB
- Verificar Security Groups
- Verificar que MongoDB esté ejecutándose
- Verificar IP privada

### Error de validación JWT
- Verificar configuración de Auth0
- Verificar que el rol esté en el token
- Verificar AUTH0_DOMAIN y AUTH0_AUDIENCE

### Error 403 en modificación de pedidos
- Verificar que el usuario tenga rol GESTOR en Auth0
- Verificar que el token incluya el claim `https://provesi.com/rol`

