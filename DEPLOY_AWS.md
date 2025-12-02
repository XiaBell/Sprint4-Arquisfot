# 🚀 Guía de Despliegue en AWS - Paso a Paso

## Información de Auth0 (Ya configurada)
- **Domain**: `dev-5i7sgc4uvmc63uai.us.auth0.com`
- **Client ID**: `8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi`
- **Audience**: `https://api.provesi.com`

---

## Paso 1: Desplegar Infraestructura con Terraform

### 1.1 Configurar terraform.tfvars

```bash
cd terraform
```

Crea `terraform/terraform.tfvars`:

```hcl
aws_region = "us-east-1"

db_username = "provesi_admin"
db_password = "TU_PASSWORD_SEGURO_AQUI"  # Mínimo 8 caracteres

# Obtener tu clave pública SSH con: cat ~/.ssh/id_rsa.pub
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."

# Variables de Auth0 (ya tienes estos valores)
auth0_domain       = "dev-5i7sgc4uvmc63uai.us.auth0.com"
auth0_audience     = "https://api.provesi.com"
auth0_client_id    = "8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi"
auth0_client_secret = "OBTENER_DE_AUTH0_DASHBOARD"  # Ver abajo cómo obtenerlo
```

**Para obtener el Client Secret:**
1. Ve a Auth0 Dashboard → Applications → Applications → Provesi Frontend
2. Click en "Settings"
3. Scroll down a "Advanced Settings" → "OAuth"
4. Copia el "Client Secret" (o genera uno nuevo si no lo ves)

### 1.2 Desplegar

```bash
terraform init
terraform plan   # Revisar qué se va a crear
terraform apply   # Confirmar con 'yes'
```

**⏱️ Esto tomará ~10-15 minutos**

### 1.3 Obtener las IPs Públicas

```bash
terraform output
```

**Anota estas IPs** (ejemplo):
```
auth_service_public_ip = "54.123.45.67"
inventory_service_public_ip = "54.123.45.68"
orders_service_public_ip = "54.123.45.69"
mongodb_private_ip = "10.0.10.50"
postgresql_endpoint = "provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com"
```

---

## Paso 2: Configurar Auth0 con URLs de AWS

### 2.1 Ir a Auth0 Dashboard

**Auth0 Dashboard → Applications → Applications → Provesi Frontend → Settings**

### 2.2 Configurar URLs (Reemplaza con tus IPs reales)

**Allowed Callback URLs:**
```
http://54.123.45.68:8000
http://54.123.45.68:8000/
http://54.123.45.68:8000/index.html
```

**Allowed Logout URLs:**
```
http://54.123.45.68:8000
http://54.123.45.68:8000/
```

**Allowed Web Origins:**
```
http://54.123.45.68:8000
```

**Allowed Origins (CORS):**
```
http://54.123.45.68:8000
```

**⚠️ IMPORTANTE:** Usa la IP de `inventory_service_public_ip` porque ahí serviremos el frontend.

**Click "Save Changes"**

---

## Paso 3: Actualizar Frontend con IPs Reales

### 3.1 Editar frontend/index.html

Busca estas líneas (alrededor de línea 320):

```javascript
// Service URLs - ACTUALIZAR CON LAS IPs PÚBLICAS DE AWS EC2
const AUTH_SERVICE_URL = 'http://<AUTH_SERVICE_IP>:3000';
const INVENTORY_SERVICE_URL = 'http://<INVENTORY_SERVICE_IP>:8000';
const ORDERS_SERVICE_URL = 'http://<ORDERS_SERVICE_IP>:8001';
```

**Reemplázalas con tus IPs reales:**

```javascript
// Service URLs - IPs de AWS EC2
const AUTH_SERVICE_URL = 'http://54.123.45.67:3000';
const INVENTORY_SERVICE_URL = 'http://54.123.45.68:8000';
const ORDERS_SERVICE_URL = 'http://54.123.45.69:8001';
```

**✅ Las configuraciones de Auth0 ya están correctas:**
```javascript
domain: 'dev-5i7sgc4uvmc63uai.us.auth0.com',
clientId: '8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi',
```

---

## Paso 4: Desplegar Microservicios

### 4.1 Desplegar Auth Service

```bash
# Desde tu máquina local
cd scripts
./deploy-aws.sh auth-service <AUTH_SERVICE_IP> ~/.ssh/tu-key.pem
```

O manualmente:

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<AUTH_SERVICE_IP>

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker.io git

# Clonar o subir código
git clone <TU_REPO> /opt/provesi
cd /opt/provesi/microservices/auth-service

# Crear .env
cat > .env << EOF
PORT=3000
AUTH0_DOMAIN=dev-5i7sgc4uvmc63uai.us.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF

# Construir y ejecutar
docker build -t auth-service .
docker run -d -p 3000:3000 --name auth-service --env-file .env --restart unless-stopped auth-service

# Verificar
curl http://localhost:3000/health
```

### 4.2 Desplegar MongoDB

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<MONGODB_PRIVATE_IP>

sudo apt-get update
sudo apt-get install -y docker.io

docker run -d -p 27017:27017 --name mongodb \
  -v mongodb_data:/data/db \
  --restart unless-stopped \
  mongo:7

docker ps
```

### 4.3 Desplegar Inventory Service

```bash
./deploy-aws.sh inventory-service <INVENTORY_SERVICE_IP> ~/.ssh/tu-key.pem
```

Te pedirá:
- PostgreSQL Host: `provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com` (sin el `:5432`)
- PostgreSQL Password: La que pusiste en terraform.tfvars
- MongoDB Private IP: La IP privada que obtuviste de `terraform output`

O manualmente:

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

sudo apt-get update
sudo apt-get install -y docker.io git python3-pip

git clone <TU_REPO> /opt/provesi
cd /opt/provesi/microservices/inventory-service

# Crear .env (reemplaza con valores reales)
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=TU_PASSWORD_DE_TERRAFORM
POSTGRES_HOST=provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
MONGODB_HOST=10.0.10.50
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
EOF

docker build -t inventory-service .
docker run -d -p 8000:8000 --name inventory-service --env-file .env --restart unless-stopped inventory-service

# Esperar y ejecutar migraciones
sleep 10
docker exec inventory-service python manage.py migrate

# Verificar
curl http://localhost:8000/api/v1/health
```

### 4.4 Desplegar Orders Service

```bash
./deploy-aws.sh orders-service <ORDERS_SERVICE_IP> ~/.ssh/tu-key.pem
```

Te pedirá:
- Auth Service IP: La IP pública del auth service
- PostgreSQL Host: El mismo endpoint de RDS
- PostgreSQL Password: La misma contraseña

O manualmente:

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<ORDERS_SERVICE_IP>

sudo apt-get update
sudo apt-get install -y docker.io git python3-pip

git clone <TU_REPO> /opt/provesi
cd /opt/provesi/microservices/orders-service

# Crear .env
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=TU_PASSWORD_DE_TERRAFORM
POSTGRES_HOST=provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://54.123.45.67:3000
EOF

docker build -t orders-service .
docker run -d -p 8001:8001 --name orders-service --env-file .env --restart unless-stopped orders-service

sleep 10
docker exec orders-service python manage.py migrate

curl http://localhost:8001/api/v1/health
```

---

## Paso 5: Poblar Base de Datos

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

# Poblar con 100,000 productos
cd /opt/provesi/scripts
docker exec -it inventory-service python populate_inventory.py

# Sincronizar a MongoDB
docker exec -it inventory-service python sync_inventory.py
```

---

## Paso 6: Servir Frontend

```bash
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

# Instalar nginx
sudo apt-get install -y nginx

# Copiar frontend (actualizado con las IPs)
sudo cp -r /opt/provesi/frontend/* /var/www/html/

# Configurar nginx para puerto 8000
sudo nano /etc/nginx/sites-available/default
```

**Configuración de nginx:**
```nginx
server {
    listen 8000;
    server_name _;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo systemctl restart nginx
```

---

## Paso 7: Verificación Final

### 7.1 Health Checks

```bash
# Auth Service
curl http://<AUTH_SERVICE_IP>:3000/health

# Inventory Service
curl http://<INVENTORY_SERVICE_IP>:8000/api/v1/health

# Orders Service
curl http://<ORDERS_SERVICE_IP>:8001/api/v1/health
```

### 7.2 Probar Frontend

1. Abre en navegador: `http://<INVENTORY_SERVICE_IP>:8000`
2. Click "Iniciar Sesión"
3. Autentícate con Auth0
4. Verifica que aparezca tu rol
5. Prueba las funcionalidades

---

## 📋 Resumen de URLs Finales

Después del despliegue:

- **Frontend**: `http://<INVENTORY_SERVICE_IP>:8000`
- **Auth Service**: `http://<AUTH_SERVICE_IP>:3000`
- **Inventory Service**: `http://<INVENTORY_SERVICE_IP>:8000`
- **Orders Service**: `http://<ORDERS_SERVICE_IP>:8001`

**Configuración Auth0:**
- Callback URLs: `http://<INVENTORY_SERVICE_IP>:8000`
- Logout URLs: `http://<INVENTORY_SERVICE_IP>:8000`
- Web Origins: `http://<INVENTORY_SERVICE_IP>:8000`

---

## 🔧 Troubleshooting

### Error: "Connection refused"
- Verifica Security Groups en AWS Console
- Verifica que los puertos estén abiertos (3000, 8000, 8001)
- Verifica que los contenedores estén corriendo: `docker ps`

### Error: "Invalid token" en Auth Service
- Verifica `.env` en auth-service: `AUTH0_DOMAIN` y `AUTH0_AUDIENCE`
- Verifica que la Action/Rule esté configurada en Auth0

### Error: "403 Forbidden"
- Verifica que el usuario tenga rol asignado en Auth0
- Verifica que el token incluya el claim `https://provesi.com/rol`

### Error: No se conecta a PostgreSQL
- Verifica Security Group de RDS permite conexiones desde EC2
- Verifica que el endpoint no incluya el puerto en el host
- Verifica credenciales en `.env`

