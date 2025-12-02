#!/bin/bash

# Script para generar configuración después de terraform apply
# Uso: ./generate-config.sh

echo "🔧 Generador de Configuración para AWS"
echo "========================================"
echo ""

# Obtener outputs de Terraform
cd ../terraform 2>/dev/null || cd terraform

if [ ! -f terraform.tfstate ]; then
    echo "❌ Error: No se encontró terraform.tfstate"
    echo "   Ejecuta 'terraform apply' primero"
    exit 1
fi

echo "📋 Obteniendo IPs de Terraform..."
AUTH_IP=$(terraform output -raw auth_service_public_ip 2>/dev/null)
INVENTORY_IP=$(terraform output -raw inventory_service_public_ip 2>/dev/null)
ORDERS_IP=$(terraform output -raw orders_service_public_ip 2>/dev/null)
MONGODB_IP=$(terraform output -raw mongodb_private_ip 2>/dev/null)
POSTGRES_ENDPOINT=$(terraform output -raw postgresql_endpoint 2>/dev/null)

if [ -z "$AUTH_IP" ]; then
    echo "❌ Error: No se pudieron obtener las IPs"
    echo "   Verifica que terraform apply se haya ejecutado correctamente"
    exit 1
fi

echo ""
echo "✅ IPs obtenidas:"
echo "   Auth Service:      $AUTH_IP"
echo "   Inventory Service:  $INVENTORY_IP"
echo "   Orders Service:     $ORDERS_IP"
echo "   MongoDB (Private):  $MONGODB_IP"
echo "   PostgreSQL:         $POSTGRES_ENDPOINT"
echo ""

# Generar configuración de Auth0
echo "📝 Configuración para Auth0 Dashboard:"
echo "========================================"
echo ""
echo "Ve a: Applications → Applications → Provesi Frontend → Settings"
echo ""
echo "Allowed Callback URLs:"
echo "http://$INVENTORY_IP:8000"
echo "http://$INVENTORY_IP:8000/"
echo "http://$INVENTORY_IP:8000/index.html"
echo ""
echo "Allowed Logout URLs:"
echo "http://$INVENTORY_IP:8000"
echo "http://$INVENTORY_IP:8000/"
echo ""
echo "Allowed Web Origins:"
echo "http://$INVENTORY_IP:8000"
echo ""
echo "Allowed Origins (CORS):"
echo "http://$INVENTORY_IP:8000"
echo ""

# Generar código JavaScript para frontend
echo "📝 Código para frontend/index.html:"
echo "========================================"
echo ""
echo "Reemplaza estas líneas en frontend/index.html:"
echo ""
cat << EOF
        // Service URLs - IPs de AWS EC2
        const AUTH_SERVICE_URL = 'http://$AUTH_IP:3000';
        const INVENTORY_SERVICE_URL = 'http://$INVENTORY_IP:8000';
        const ORDERS_SERVICE_URL = 'http://$ORDERS_IP:8001';
EOF
echo ""

# Generar archivos .env de ejemplo
echo "📝 Variables de entorno para microservicios:"
echo "========================================"
echo ""

echo "microservices/auth-service/.env:"
cat << EOF
PORT=3000
AUTH0_DOMAIN=dev-5i7sgc4uvmc63uai.us.auth0.com
AUTH0_AUDIENCE=https://api.provesi.com
EOF
echo ""

echo "microservices/inventory-service/.env:"
cat << EOF
DEBUG=False
SECRET_KEY=<GENERAR_CON_openssl_rand_-hex_32>
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=<TU_PASSWORD_DE_TERRAFORM>
POSTGRES_HOST=${POSTGRES_ENDPOINT%:*}
POSTGRES_PORT=5432
MONGODB_HOST=$MONGODB_IP
MONGODB_PORT=27017
MONGODB_DB=provesi_inventory
EOF
echo ""

echo "microservices/orders-service/.env:"
cat << EOF
DEBUG=False
SECRET_KEY=<GENERAR_CON_openssl_rand_-hex_32>
POSTGRES_DB=provesi
POSTGRES_USER=provesi_admin
POSTGRES_PASSWORD=<TU_PASSWORD_DE_TERRAFORM>
POSTGRES_HOST=${POSTGRES_ENDPOINT%:*}
POSTGRES_PORT=5432
AUTH_SERVICE_URL=http://$AUTH_IP:3000
EOF
echo ""

echo "✅ Configuración generada!"
echo ""
echo "📚 Siguiente paso: Ver DEPLOY_AWS.md para instrucciones completas"

