#!/bin/bash

# Script de configuración inicial para AWS CloudShell
# Uso: ./cloudshell-setup.sh <GITHUB_REPO_URL>

set -e

GITHUB_REPO=$1

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Error: Debes proporcionar la URL del repositorio de GitHub"
    echo "Uso: $0 <GITHUB_REPO_URL>"
    echo "Ejemplo: $0 https://github.com/usuario/repo.git"
    exit 1
fi

echo "🚀 Configuración inicial de CloudShell para Sprint4-Arquisfot"
echo "=============================================================="
echo ""

# Verificar si estamos en CloudShell
if [ -z "$AWS_EXECUTION_ENV" ]; then
    echo "⚠️  Advertencia: No parece que estés en CloudShell"
    echo "   Continuando de todas formas..."
fi

# Paso 1: Verificar/Instalar Terraform
echo "📦 Paso 1: Verificando Terraform..."
if ! command -v terraform &> /dev/null; then
    echo "   Terraform no encontrado, instalando..."
    wget -q https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
    unzip -q terraform_1.6.0_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
    rm terraform_1.6.0_linux_amd64.zip
    echo "   ✅ Terraform instalado"
else
    echo "   ✅ Terraform ya está instalado: $(terraform version | head -n 1)"
fi

# Paso 2: Generar SSH Key si no existe
echo ""
echo "🔑 Paso 2: Verificando SSH Key..."
if [ ! -f ~/.ssh/provesi-key ]; then
    echo "   Generando nueva clave SSH..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/provesi-key -N "" -q
    echo "   ✅ Clave SSH generada"
else
    echo "   ✅ Clave SSH ya existe"
fi

# Mostrar clave pública
echo ""
echo "📋 Tu clave pública SSH (cópiala para terraform.tfvars):"
echo "========================================================="
cat ~/.ssh/provesi-key.pub
echo ""

# Paso 3: Clonar repositorio
echo ""
echo "📥 Paso 3: Clonando repositorio..."
if [ -d ~/Sprint4-Arquisfot ]; then
    echo "   El directorio ya existe, actualizando..."
    cd ~/Sprint4-Arquisfot
    git pull
else
    cd ~
    git clone "$GITHUB_REPO" Sprint4-Arquisfot
    echo "   ✅ Repositorio clonado"
fi

# Paso 4: Verificar AWS credentials
echo ""
echo "🔐 Paso 4: Verificando credenciales de AWS..."
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
AWS_REGION=$(aws configure get region)

if [ -z "$AWS_ACCOUNT" ]; then
    echo "   ❌ Error: No se pudieron obtener credenciales de AWS"
    exit 1
fi

echo "   ✅ Cuenta AWS: $AWS_ACCOUNT"
echo "   ✅ Región: ${AWS_REGION:-us-east-1}"

# Paso 5: Crear template de terraform.tfvars
echo ""
echo "📝 Paso 5: Creando template de terraform.tfvars..."
cd ~/Sprint4-Arquisfot/terraform

if [ ! -f terraform.tfvars ]; then
    SSH_PUBLIC_KEY=$(cat ~/.ssh/provesi-key.pub)
    
    cat > terraform.tfvars << EOF
aws_region = "${AWS_REGION:-us-east-1}"

db_username = "provesi_admin"
db_password = "CAMBIAR_PASSWORD_SEGURO_AQUI"

# Clave pública SSH generada automáticamente
ssh_public_key = "$SSH_PUBLIC_KEY"

# Variables de Auth0 - ACTUALIZAR CON TUS VALORES
auth0_domain       = "dev-5i7sgc4uvmc63uai.us.auth0.com"
auth0_audience     = "https://api.provesi.com"
auth0_client_id    = "8VzOmIn8oNHOtB7W9z3urBaWNV4HUkqi"
auth0_client_secret = "OBTENER_DE_AUTH0_DASHBOARD"
EOF
    
    echo "   ✅ Archivo terraform.tfvars creado"
    echo ""
    echo "   ⚠️  IMPORTANTE: Edita terraform.tfvars y actualiza:"
    echo "      - db_password: Cambia por una contraseña segura"
    echo "      - auth0_client_secret: Obtén de Auth0 Dashboard"
    echo ""
    echo "   Para editar: nano terraform.tfvars"
else
    echo "   ⚠️  terraform.tfvars ya existe, no se sobrescribió"
fi

# Resumen
echo ""
echo "✅ Configuración inicial completada!"
echo "======================================"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Editar terraform.tfvars:"
echo "   cd ~/Sprint4-Arquisfot/terraform"
echo "   nano terraform.tfvars"
echo ""
echo "2. Inicializar Terraform:"
echo "   terraform init"
echo ""
echo "3. Revisar plan:"
echo "   terraform plan"
echo ""
echo "4. Aplicar cambios:"
echo "   terraform apply"
echo ""
echo "5. Obtener IPs:"
echo "   terraform output"
echo ""
echo "📚 Para más detalles, ver: docs/DEPLOY_CLOUDSHELL.md"
echo ""

