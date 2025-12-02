#!/bin/bash

# Script de despliegue automatizado para AWS EC2
# Uso: ./deploy-aws.sh <service-name> <instance-ip> <ssh-key-path>
# Ejemplo: ./deploy-aws.sh auth-service 54.123.45.67 ~/.ssh/provesi-key.pem

set -e

SERVICE=$1
INSTANCE_IP=$2
SSH_KEY=$3

if [ -z "$SERVICE" ] || [ -z "$INSTANCE_IP" ] || [ -z "$SSH_KEY" ]; then
    echo "Uso: $0 <service-name> <instance-ip> <ssh-key-path>"
    echo "Servicios disponibles: auth-service, inventory-service, orders-service, mongodb"
    exit 1
fi

echo "🚀 Desplegando $SERVICE en $INSTANCE_IP..."

# Función para ejecutar comandos remotos
remote_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@"$INSTANCE_IP" "$@"
}

# Función para copiar archivos
remote_copy() {
    scp -i "$SSH_KEY" -r -o StrictHostKeyChecking=no "$1" ubuntu@"$INSTANCE_IP:$2"
}

case $SERVICE in
    auth-service)
        echo "📦 Desplegando Auth Service..."
        
        # Instalar dependencias
        remote_exec "sudo apt-get update && sudo apt-get install -y docker.io docker-compose git"
        
        # Copiar código
        remote_exec "mkdir -p /opt/provesi"
        remote_copy "./microservices/auth-service" "/opt/provesi/"
        
        # Crear .env
        remote_exec "cat > /opt/provesi/microservices/auth-service/.env << 'EOF'
PORT=3000
AUTH0_DOMAIN=dev-5i7sgc4uvmc63uai.us.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF"
        
        # Construir y ejecutar
        remote_exec "cd /opt/provesi/microservices/auth-service && docker build -t auth-service ."
        remote_exec "docker stop auth-service || true"
        remote_exec "docker rm auth-service || true"
        remote_exec "docker run -d -p 3000:3000 --name auth-service --env-file /opt/provesi/microservices/auth-service/.env --restart unless-stopped auth-service"
        
        echo "✅ Auth Service desplegado"
        ;;
        
    inventory-service)
        echo "📦 Desplegando Inventory Service..."
        
        # Solicitar variables
        read -p "PostgreSQL Host (endpoint sin puerto): " POSTGRES_HOST
        read -p "PostgreSQL Password: " POSTGRES_PASSWORD
        read -p "MongoDB Private IP: " MONGODB_IP
        
        # Instalar dependencias
        remote_exec "sudo apt-get update && sudo apt-get install -y docker.io docker-compose git python3-pip"
        
        # Copiar código
        remote_exec "mkdir -p /opt/provesi"
        remote_copy "./microservices/inventory-service" "/opt/provesi/"
        remote_copy "./scripts" "/opt/provesi/"
        
        # Crear .env
        SECRET_KEY=$(openssl rand -hex 32)
        remote_exec "cat > /opt/provesi/microservices/inventory-service/.env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=5432
MONGODB_HOST=$MONGODB_IP
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
EOF"
        
        # Construir y ejecutar
        remote_exec "cd /opt/provesi/microservices/inventory-service && docker build -t inventory-service ."
        remote_exec "docker stop inventory-service || true"
        remote_exec "docker rm inventory-service || true"
        remote_exec "docker run -d -p 8000:8000 --name inventory-service --env-file /opt/provesi/microservices/inventory-service/.env --restart unless-stopped inventory-service"
        
        # Ejecutar migraciones
        echo "⏳ Ejecutando migraciones..."
        sleep 10  # Esperar a que el servicio esté listo
        remote_exec "docker exec inventory-service python manage.py migrate"
        
        echo "✅ Inventory Service desplegado"
        ;;
        
    orders-service)
        read -p "Auth Service IP: " AUTH_IP
        read -p "PostgreSQL Host (endpoint sin puerto): " POSTGRES_HOST
        read -p "PostgreSQL Password: " POSTGRES_PASSWORD
        
        echo "📦 Desplegando Orders Service..."
        
        # Instalar dependencias
        remote_exec "sudo apt-get update && sudo apt-get install -y docker.io docker-compose git python3-pip"
        
        # Copiar código
        remote_exec "mkdir -p /opt/provesi"
        remote_copy "./microservices/orders-service" "/opt/provesi/"
        
        # Crear .env
        SECRET_KEY=$(openssl rand -hex 32)
        remote_exec "cat > /opt/provesi/microservices/orders-service/.env << EOF
DEBUG=False
SECRET_KEY=$SECRET_KEY
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://$AUTH_IP:3000
EOF"
        
        # Construir y ejecutar
        remote_exec "cd /opt/provesi/microservices/orders-service && docker build -t orders-service ."
        remote_exec "docker stop orders-service || true"
        remote_exec "docker rm orders-service || true"
        remote_exec "docker run -d -p 8001:8001 --name orders-service --env-file /opt/provesi/microservices/orders-service/.env --restart unless-stopped orders-service"
        
        # Ejecutar migraciones
        echo "⏳ Ejecutando migraciones..."
        sleep 10
        remote_exec "docker exec orders-service python manage.py migrate"
        
        echo "✅ Orders Service desplegado"
        ;;
        
    mongodb)
        echo "📦 Desplegando MongoDB..."
        
        # Instalar Docker
        remote_exec "sudo apt-get update && sudo apt-get install -y docker.io"
        
        # Ejecutar MongoDB
        remote_exec "docker stop mongodb || true"
        remote_exec "docker rm mongodb || true"
        remote_exec "docker run -d -p 27017:27017 --name mongodb -v mongodb_data:/data/db --restart unless-stopped mongo:7"
        
        echo "✅ MongoDB desplegado"
        ;;
        
    *)
        echo "❌ Servicio desconocido: $SERVICE"
        echo "Servicios disponibles: auth-service, inventory-service, orders-service, mongodb"
        exit 1
        ;;
esac

echo "🎉 Despliegue completado!"

