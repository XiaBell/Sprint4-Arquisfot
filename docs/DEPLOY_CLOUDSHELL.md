# 🚀 Despliegue desde AWS CloudShell - Guía Completa

## Prerrequisitos

1. **Cuenta de AWS** con permisos para crear recursos (EC2, RDS, VPC, etc.)
2. **Repositorio en GitHub** con el código del proyecto
3. **Auth0 configurado** con:
   - Domain: `dev-5i7sgc4uvmc63uai.us.auth0.com`
   - Client ID: `8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi`
   - Client Secret (obtener de Auth0 Dashboard)

---

## Paso 1: Acceder a AWS CloudShell

1. Inicia sesión en la **AWS Console**
2. En la barra superior, busca **"CloudShell"** o haz clic en el ícono de terminal
3. Espera a que CloudShell se inicialice (primera vez puede tardar ~1 minuto)

**✅ CloudShell ya tiene instalado:**
- AWS CLI
- Terraform (puede que necesites instalarlo)
- Git
- Docker (no disponible directamente, pero no lo necesitamos aquí)

---

## Paso 2: Verificar/Instalar Terraform

```bash
# Verificar si Terraform está instalado
terraform version

# Si no está instalado, instalarlo
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version
```

---

## Paso 3: Clonar el Repositorio

```bash
# Navegar al directorio home
cd ~

# Clonar tu repositorio (reemplaza con tu URL de GitHub)
git clone https://github.com/TU_USUARIO/TU_REPO.git Sprint4-Arquisfot

# O si es privado, usar SSH:
# git clone git@github.com:TU_USUARIO/TU_REPO.git Sprint4-Arquisfot

# Entrar al directorio
cd Sprint4-Arquisfot
```

---

## Paso 4: Configurar Credenciales de AWS

CloudShell ya tiene credenciales configuradas automáticamente, pero verifica:

```bash
# Verificar identidad actual
aws sts get-caller-identity

# Verificar región
aws configure get region

# Si necesitas cambiar región
aws configure set region us-east-1
```

---

## Paso 5: Generar SSH Key Pair (si no tienes uno)

```bash
# Generar nueva clave SSH
ssh-keygen -t rsa -b 4096 -f ~/.ssh/provesi-key -N ""

# Ver la clave pública (la necesitarás para terraform.tfvars)
cat ~/.ssh/provesi-key.pub
```

**📋 Copia la salida completa** (empezando con `ssh-rsa...`)

---

## Paso 6: Configurar Terraform Variables

```bash
cd terraform

# Crear archivo terraform.tfvars
nano terraform.tfvars
```

**Pega esta configuración** (reemplaza los valores):

```hcl
aws_region = "us-east-1"

db_username = "provesi_admin"
db_password = "TU_PASSWORD_SEGURO_AQUI_MINIMO_8_CARACTERES"

# Pega aquí la clave pública que obtuviste en el paso anterior
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."

# Variables de Auth0
auth0_domain       = "dev-5i7sgc4uvmc63uai.us.auth0.com"
auth0_audience     = "https://api.provesi.com"
auth0_client_id    = "8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi"
auth0_client_secret = "TU_CLIENT_SECRET_DE_AUTH0"
```

**Para obtener Client Secret:**
1. Ve a Auth0 Dashboard → Applications → Applications → Provesi Frontend
2. Settings → Advanced Settings → OAuth
3. Copia el "Client Secret"

**Guardar y salir:** `Ctrl+X`, luego `Y`, luego `Enter`

---

## Paso 7: Inicializar y Desplegar con Terraform

```bash
# Inicializar Terraform
terraform init

# Ver qué se va a crear (revisar antes de aplicar)
terraform plan

# Si todo se ve bien, aplicar cambios
terraform apply

# Terraform te pedirá confirmación, escribe: yes
```

**⏱️ Esto tomará aproximadamente 10-15 minutos**

Verás el progreso de creación de recursos:
- VPC
- Subnets
- Security Groups
- RDS PostgreSQL
- Instancias EC2 (Auth, Inventory, Orders, MongoDB)

---

## Paso 8: Obtener las IPs Públicas

```bash
# Obtener todas las IPs
terraform output

# O obtener IPs individuales
terraform output auth_service_public_ip
terraform output inventory_service_public_ip
terraform output orders_service_public_ip
terraform output mongodb_private_ip
terraform output postgresql_endpoint
```

**📋 Anota estas IPs** - Las necesitarás para los siguientes pasos

**Ejemplo de salida:**
```
auth_service_public_ip = "54.123.45.67"
inventory_service_public_ip = "54.123.45.68"
orders_service_public_ip = "54.123.45.69"
mongodb_private_ip = "10.0.10.50"
postgresql_endpoint = "provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com:5432"
```

---

## Paso 9: Configurar Auth0 con las IPs

### 9.1 Ir a Auth0 Dashboard

1. Ve a **Auth0 Dashboard → Applications → Applications → Provesi Frontend → Settings**

### 9.2 Configurar URLs

Usa la IP de **inventory_service_public_ip** (donde serviremos el frontend):

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

**Click "Save Changes"**

---

## Paso 10: Actualizar Frontend con IPs Reales

```bash
# Volver al directorio raíz del proyecto
cd ~/Sprint4-Arquisfot

# Editar frontend/index.html
nano frontend/index.html
```

Busca estas líneas (alrededor de línea 320):

```javascript
const AUTH_SERVICE_URL = 'http://<AUTH_SERVICE_IP>:3000';
const INVENTORY_SERVICE_URL = 'http://<INVENTORY_SERVICE_IP>:8000';
const ORDERS_SERVICE_URL = 'http://<ORDERS_SERVICE_IP>:8001';
```

**Reemplázalas con tus IPs reales:**

```javascript
const AUTH_SERVICE_URL = 'http://54.123.45.67:3000';
const INVENTORY_SERVICE_URL = 'http://54.123.45.68:8000';
const ORDERS_SERVICE_URL = 'http://54.123.45.69:8001';
```

**Guardar:** `Ctrl+X`, `Y`, `Enter`

---

## Paso 11: Preparar Código para Desplegar en EC2

### 11.1 Crear archivo con variables de entorno

```bash
# Crear directorio para configuraciones
mkdir -p ~/configs

# Crear .env para auth-service
cat > ~/configs/auth-service.env << EOF
PORT=3000
AUTH0_DOMAIN=dev-5i7sgc4uvmc63uai.us.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF

# Crear .env para inventory-service (reemplaza con tus valores)
cat > ~/configs/inventory-service.env << EOF
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

# Crear .env para orders-service (reemplaza con tus valores)
cat > ~/configs/orders-service.env << EOF
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=TU_PASSWORD_DE_TERRAFORM
POSTGRES_HOST=provesi-postgresql.xxxxx.us-east-1.rds.amazonaws.com
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://54.123.45.67:3000
EOF
```

**⚠️ IMPORTANTE:** Reemplaza los valores con los que obtuviste de `terraform output`

---

## Paso 12: Desplegar en Instancias EC2

### 12.1 Obtener la clave SSH privada

```bash
# La clave privada está en CloudShell
cat ~/.ssh/provesi-key

# Copia todo el contenido (lo necesitarás para conectarte a EC2)
```

**📋 Copia esta clave** - La necesitarás para conectarte a las instancias EC2

### 12.2 Conectarse a cada instancia EC2

**Opción A: Desde tu máquina local** (si tienes acceso SSH)

```bash
# Desde tu máquina local (no CloudShell)
ssh -i ~/.ssh/provesi-key ubuntu@<AUTH_SERVICE_IP>
```

**Opción B: Desde CloudShell** (si tienes acceso a la VPC)

```bash
# Conectarse a auth-service
ssh -i ~/.ssh/provesi-key ubuntu@<AUTH_SERVICE_IP>
```

### 12.3 Desplegar Auth Service

```bash
# SSH a auth-service
ssh -i ~/.ssh/provesi-key ubuntu@<AUTH_SERVICE_IP>

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker.io git

# Clonar repositorio
git clone https://github.com/TU_USUARIO/TU_REPO.git /opt/provesi
cd /opt/provesi/microservices/auth-service

# Copiar .env (o crearlo manualmente)
sudo nano .env
# Pega el contenido de ~/configs/auth-service.env

# Construir y ejecutar
sudo docker build -t auth-service .
sudo docker run -d -p 3000:3000 --name auth-service --env-file .env --restart unless-stopped auth-service

# Verificar
curl http://localhost:3000/health
```

### 12.4 Desplegar MongoDB

```bash
# SSH a MongoDB (usa la IP privada desde dentro de la VPC, o pública si está configurada)
ssh -i ~/.ssh/provesi-key ubuntu@<MONGODB_IP>

sudo apt-get update
sudo apt-get install -y docker.io

sudo docker run -d -p 27017:27017 --name mongodb \
  -v mongodb_data:/data/db \
  --restart unless-stopped \
  mongo:7

sudo docker ps
```

### 12.5 Desplegar Inventory Service

```bash
ssh -i ~/.ssh/provesi-key ubuntu@<INVENTORY_SERVICE_IP>

sudo apt-get update
sudo apt-get install -y docker.io git python3-pip

git clone https://github.com/TU_USUARIO/TU_REPO.git /opt/provesi
cd /opt/provesi/microservices/inventory-service

# Crear .env con los valores correctos
sudo nano .env
# Pega el contenido de ~/configs/inventory-service.env (actualizado)

sudo docker build -t inventory-service .
sudo docker run -d -p 8000:8000 --name inventory-service --env-file .env --restart unless-stopped inventory-service

# Esperar y ejecutar migraciones
sleep 15
sudo docker exec inventory-service python manage.py migrate

curl http://localhost:8000/api/v1/health
```

### 12.6 Desplegar Orders Service

```bash
ssh -i ~/.ssh/provesi-key ubuntu@<ORDERS_SERVICE_IP>

sudo apt-get update
sudo apt-get install -y docker.io git python3-pip

git clone https://github.com/TU_USUARIO/TU_REPO.git /opt/provesi
cd /opt/provesi/microservices/orders-service

# Crear .env
sudo nano .env
# Pega el contenido de ~/configs/orders-service.env (actualizado)

sudo docker build -t orders-service .
sudo docker run -d -p 8001:8001 --name orders-service --env-file .env --restart unless-stopped orders-service

sleep 15
sudo docker exec orders-service python manage.py migrate

curl http://localhost:8001/api/v1/health
```

---

## Paso 13: Poblar Base de Datos

```bash
# SSH a inventory-service
ssh -i ~/.ssh/provesi-key ubuntu@<INVENTORY_SERVICE_IP>

# Poblar con 100,000 productos
cd /opt/provesi/scripts
sudo docker exec -it inventory-service python populate_inventory.py

# Sincronizar a MongoDB
sudo docker exec -it inventory-service python sync_inventory.py
```

---

## Paso 14: Servir Frontend

```bash
# SSH a inventory-service
ssh -i ~/.ssh/provesi-key ubuntu@<INVENTORY_SERVICE_IP>

# Instalar nginx
sudo apt-get install -y nginx

# Copiar frontend (ya actualizado con las IPs)
sudo cp -r /opt/provesi/frontend/* /var/www/html/

# Configurar nginx
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

# Verificar
curl http://localhost:8000
```

---

## Paso 15: Verificación Final

### 15.1 Health Checks

```bash
# Desde CloudShell o tu máquina local
curl http://<AUTH_SERVICE_IP>:3000/health
curl http://<INVENTORY_SERVICE_IP>:8000/api/v1/health
curl http://<ORDERS_SERVICE_IP>:8001/api/v1/health
```

### 15.2 Probar Frontend

1. Abre en navegador: `http://<INVENTORY_SERVICE_IP>:8000`
2. Click "Iniciar Sesión"
3. Autentícate con Auth0
4. Verifica que aparezca tu rol
5. Prueba las funcionalidades

---

## 📋 Resumen de Comandos Rápidos

```bash
# Desde CloudShell
cd ~/Sprint4-Arquisfot/terraform
terraform init
terraform apply
terraform output

# Obtener IPs
AUTH_IP=$(terraform output -raw auth_service_public_ip)
INVENTORY_IP=$(terraform output -raw inventory_service_public_ip)
ORDERS_IP=$(terraform output -raw orders_service_public_ip)

# Conectarse a instancias
ssh -i ~/.ssh/provesi-key ubuntu@$AUTH_IP
ssh -i ~/.ssh/provesi-key ubuntu@$INVENTORY_IP
ssh -i ~/.ssh/provesi-key ubuntu@$ORDERS_IP
```

---

## 🔧 Troubleshooting

### Error: "Permission denied" al hacer SSH
- Verifica que la clave privada tenga permisos correctos: `chmod 600 ~/.ssh/provesi-key`
- Verifica que la clave pública esté en `terraform.tfvars`

### Error: "Connection timeout" a EC2
- Verifica Security Groups permiten SSH desde tu IP
- Verifica que las instancias estén corriendo en AWS Console

### Error: "Terraform not found"
- Instala Terraform según el Paso 2

### Error: "Cannot connect to RDS"
- Verifica Security Group de RDS permite conexiones desde EC2
- Verifica que el endpoint no incluya el puerto en el hostname

---

## 🗑️ Limpiar Recursos (si necesitas empezar de nuevo)

```bash
cd ~/Sprint4-Arquisfot/terraform
terraform destroy
```

**⚠️ Esto eliminará TODOS los recursos creados**

---

## ✅ Checklist Final

- [ ] Terraform aplicado exitosamente
- [ ] IPs obtenidas y anotadas
- [ ] Auth0 configurado con URLs correctas
- [ ] Frontend actualizado con IPs reales
- [ ] Auth Service desplegado y funcionando
- [ ] MongoDB desplegado
- [ ] Inventory Service desplegado y migrado
- [ ] Orders Service desplegado y migrado
- [ ] Base de datos poblada
- [ ] Frontend servido con nginx
- [ ] Health checks pasando
- [ ] Frontend accesible y autenticación funcionando

