# Guía de Despliegue en AWS - Sprint 4 Provesi

## Paso 1: Preparar Terraform

### 1.1 Configurar variables de Terraform

Crea el archivo `terraform/terraform.tfvars`:

```hcl
aws_region = "us-east-1"

db_username = "provesi_admin"
db_password = "TU_PASSWORD_SEGURO_AQUI_MINIMO_8_CARACTERES"

# Tu clave pública SSH (obtener con: cat ~/.ssh/id_rsa.pub)
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."

# Variables de Auth0
auth0_domain       = "dev-5i7sgc4uvmc63uai.us.auth0.com"
auth0_audience     = "https://api.provesi.com"
auth0_client_id   = "8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi"
auth0_client_secret = "TU_CLIENT_SECRET_DE_AUTH0"  # Obtener de Auth0 Dashboard
```

### 1.2 Inicializar y desplegar Terraform

```bash
cd terraform
terraform init
terraform plan  # Revisar el plan
terraform apply  # Aplicar cambios (tardará ~10-15 minutos)
```

### 1.3 Obtener las IPs públicas

Después de `terraform apply`, ejecuta:

```bash
terraform output
```

Anota las siguientes IPs:
- `auth_service_public_ip` → Ejemplo: `54.123.45.67`
- `inventory_service_public_ip` → Ejemplo: `54.123.45.68`
- `orders_service_public_ip` → Ejemplo: `54.123.45.69`
- `mongodb_private_ip` → Ejemplo: `10.0.10.50`
- `postgresql_endpoint` → Ejemplo: `provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com:5432`

---

## Paso 2: Configurar Auth0 con URLs de AWS

### 2.1 Configurar Single Page Application (SPA)

Ve a **Auth0 Dashboard → Applications → Applications → Provesi Frontend → Settings**

Configura las siguientes URLs (reemplaza `X.X.X.X` con las IPs reales que obtuviste):

**Allowed Callback URLs:**
```
http://X.X.X.X:8000
http://X.X.X.X:8000/
http://X.X.X.X:8000/index.html
```

**Nota:** Si vas a servir el frontend desde una de las instancias EC2 (por ejemplo, inventory-service en puerto 8000), usa esa IP. Si lo sirves desde otra instancia o servicio, usa esa IP.

**Allowed Logout URLs:**
```
http://X.X.X.X:8000
http://X.X.X.X:8000/
```

**Allowed Web Origins:**
```
http://X.X.X.X:8000
```

**Allowed Origins (CORS):**
```
http://X.X.X.X:8000
```

**Ejemplo con IPs reales:**
```
Allowed Callback URLs:
http://54.123.45.68:8000
http://54.123.45.68:8000/
http://54.123.45.68:8000/index.html

Allowed Logout URLs:
http://54.123.45.68:8000
http://54.123.45.68:8000/

Allowed Web Origins:
http://54.123.45.68:8000

Allowed Origins (CORS):
http://54.123.45.68:8000
```

Click **"Save Changes"**

### 2.2 Verificar API Configuration

Ve a **Auth0 Dashboard → Applications → APIs → Provesi API**

Verifica que:
- **Identifier**: `https://api.provesi.com`
- **Signing Algorithm**: `RS256`

---

## Paso 3: Desplegar Microservicios en EC2

### 3.1 Preparar el código en tu máquina local

Asegúrate de tener el código listo. Luego, para cada instancia EC2:

### 3.2 Desplegar Auth Service

```bash
# SSH a la instancia
ssh -i ~/.ssh/tu-key.pem ubuntu@<AUTH_SERVICE_IP>

# Instalar dependencias
sudo apt-get update
sudo apt-get install -y git docker.io docker-compose

# Clonar repositorio (o subir código)
git clone <TU_REPO_URL> /opt/provesi
cd /opt/provesi/microservices/auth-service

# Crear .env
cat > .env << EOF
PORT=3000
AUTH0_DOMAIN=dev-5i7sgc4uvmc63uai.us.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF

# Construir y ejecutar con Docker
docker build -t auth-service .
docker run -d -p 3000:3000 --name auth-service --env-file .env auth-service

# Verificar que está corriendo
docker ps
curl http://localhost:3000/health
```

### 3.3 Desplegar Inventory Service

```bash
# SSH a la instancia
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

# Instalar dependencias
sudo apt-get update
sudo apt-get install -y git docker.io docker-compose python3-pip

# Clonar repositorio
git clone <TU_REPO_URL> /opt/provesi
cd /opt/provesi/microservices/inventory-service

# Crear .env (reemplaza con valores reales)
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=TU_PASSWORD_DE_TERRAFORM
POSTGRES_HOST=<POSTGRES_ENDPOINT_SIN_PUERTO>
POSTGRES_PORT=5432
MONGODB_HOST=<MONGODB_PRIVATE_IP>
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
EOF

# Construir y ejecutar
docker build -t inventory-service .
docker run -d -p 8000:8000 --name inventory-service --env-file .env inventory-service

# Ejecutar migraciones
docker exec inventory-service python manage.py migrate

# Verificar
curl http://localhost:8000/api/v1/health
```

### 3.4 Desplegar Orders Service

```bash
# SSH a la instancia
ssh -i ~/.ssh/tu-key.pem ubuntu@<ORDERS_SERVICE_IP>

# Instalar dependencias
sudo apt-get update
sudo apt-get install -y git docker.io docker-compose python3-pip

# Clonar repositorio
git clone <TU_REPO_URL> /opt/provesi
cd /opt/provesi/microservices/orders-service

# Crear .env (reemplaza con valores reales)
cat > .env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=TU_PASSWORD_DE_TERRAFORM
POSTGRES_HOST=<POSTGRES_ENDPOINT_SIN_PUERTO>
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://<AUTH_SERVICE_IP>:3000
EOF

# Construir y ejecutar
docker build -t orders-service .
docker run -d -p 8001:8001 --name orders-service --env-file .env orders-service

# Ejecutar migraciones
docker exec orders-service python manage.py migrate

# Verificar
curl http://localhost:8001/api/v1/health
```

### 3.5 Desplegar MongoDB

```bash
# SSH a la instancia MongoDB
ssh -i ~/.ssh/tu-key.pem ubuntu@<MONGODB_PRIVATE_IP>

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Ejecutar MongoDB
docker run -d -p 27017:27017 --name mongodb \
  -v mongodb_data:/data/db \
  mongo:7

# Verificar
docker ps
```

---

## Paso 4: Poblar Base de Datos

### 4.1 Poblar PostgreSQL con productos

```bash
# SSH a inventory-service
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

# Ejecutar script de población
cd /opt/provesi/scripts
docker exec -it inventory-service python populate_inventory.py
```

### 4.2 Sincronizar a MongoDB

```bash
# Desde inventory-service
docker exec -it inventory-service python sync_inventory.py
```

---

## Paso 5: Configurar Frontend

### 5.1 Actualizar frontend/index.html

Edita `frontend/index.html` y actualiza estas líneas (alrededor de la línea 400):

```javascript
// Auth0 Configuration
const auth0Config = {
    domain: 'dev-5i7sgc4uvmc63uai.us.auth0.com',
    clientId: '8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi',
    authorizationParams: {
        audience: 'https://api.provesi.com',
        redirect_uri: window.location.origin
    }
};

// Service URLs (reemplaza con las IPs reales)
const AUTH_SERVICE_URL = 'http://<AUTH_SERVICE_IP>:3000';
const INVENTORY_SERVICE_URL = 'http://<INVENTORY_SERVICE_IP>:8000';
const ORDERS_SERVICE_URL = 'http://<ORDERS_SERVICE_IP>:8001';
```

**Ejemplo con IPs reales:**
```javascript
const AUTH_SERVICE_URL = 'http://54.123.45.67:3000';
const INVENTORY_SERVICE_URL = 'http://54.123.45.68:8000';
const ORDERS_SERVICE_URL = 'http://54.123.45.69:8001';
```

### 5.2 Servir el Frontend

Opción A: Desde Inventory Service (recomendado para simplicidad)

```bash
# SSH a inventory-service
ssh -i ~/.ssh/tu-key.pem ubuntu@<INVENTORY_SERVICE_IP>

# Instalar nginx
sudo apt-get install -y nginx

# Copiar frontend
sudo cp -r /opt/provesi/frontend/* /var/www/html/

# Configurar nginx para servir en puerto 8000
sudo nano /etc/nginx/sites-available/default
```

Configuración de nginx:
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

Opción B: Servir desde una instancia EC2 separada (más complejo)

---

## Paso 6: Verificación Final

### 6.1 Health Checks

```bash
# Auth Service
curl http://<AUTH_SERVICE_IP>:3000/health

# Inventory Service
curl http://<INVENTORY_SERVICE_IP>:8000/api/v1/health

# Orders Service
curl http://<ORDERS_SERVICE_IP>:8001/api/v1/health
```

### 6.2 Probar Endpoints

```bash
# Prueba de latencia - SQL
curl http://<INVENTORY_SERVICE_IP>:8000/api/v1/inventory/sql-list

# Prueba de latencia - NoSQL
curl http://<INVENTORY_SERVICE_IP>:8000/api/v1/inventory/nosql-list
```

### 6.3 Probar Frontend

1. Abre en navegador: `http://<INVENTORY_SERVICE_IP>:8000`
2. Click en "Iniciar Sesión"
3. Autentícate con Auth0
4. Verifica que aparezca tu rol (GESTOR u OPERARIO)
5. Prueba las funcionalidades de latencia y seguridad

---

## Resumen de URLs Finales

Después del despliegue, tendrás:

- **Frontend**: `http://<INVENTORY_SERVICE_IP>:8000`
- **Auth Service**: `http://<AUTH_SERVICE_IP>:3000`
- **Inventory Service**: `http://<INVENTORY_SERVICE_IP>:8000`
- **Orders Service**: `http://<ORDERS_SERVICE_IP>:8001`

**Configuración de Auth0:**
- Domain: `dev-5i7sgc4uvmc63uai.us.auth0.com`
- Client ID: `8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi`
- Audience: `https://api.provesi.com`
- Callback URLs: `http://<INVENTORY_SERVICE_IP>:8000`

---

## Troubleshooting

### Error: "Connection refused" a servicios
- Verifica Security Groups en AWS
- Verifica que los puertos estén abiertos
- Verifica que los contenedores estén corriendo: `docker ps`

### Error: "Invalid token" en Auth Service
- Verifica AUTH0_DOMAIN y AUTH0_AUDIENCE en .env
- Verifica que el token incluya el claim `https://provesi.com/rol`
- Verifica que la Action/Rule esté configurada en Auth0

### Error: "403 Forbidden" cuando debería funcionar
- Verifica que el usuario tenga rol GESTOR asignado en Auth0
- Verifica que el token incluya el claim del rol
- Verifica logs: `docker logs auth-service`

### Error: No se puede conectar a PostgreSQL
- Verifica que el Security Group de RDS permita conexiones desde las instancias EC2
- Verifica el endpoint de PostgreSQL (sin el puerto en el host)
- Verifica credenciales en .env

