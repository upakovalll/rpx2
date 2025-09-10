#!/bin/bash

# Azure Resource Setup Script for RPX Backend
# This script helps set up the required Azure resources

set -e

# Configuration
SUBSCRIPTION_ID="2c9687e2-4dc8-44ae-b0c2-0ab6eea7b9e2"
RESOURCE_GROUP="rpx-dev"
LOCATION="eastus2"
ACR_NAME="rpxdevacr"
KEY_VAULT_NAME="rpx-dev-kv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "RPX Backend Azure Resource Setup"
echo "================================"

# Check if logged in to Azure
echo -n "Checking Azure login status... "
if az account show &>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Please login to Azure first:"
    az login
fi

# Set subscription
echo -n "Setting subscription... "
az account set --subscription "$SUBSCRIPTION_ID"
echo -e "${GREEN}✓${NC}"

# Check if resource group exists
echo -n "Checking resource group... "
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}Creating...${NC}"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" \
        --tags env=dev attribution=rpx
    echo -e "${GREEN}✓ Created${NC}"
fi

# Check/Create Azure Container Registry
echo -n "Checking Azure Container Registry... "
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}Creating...${NC}"
    az acr create --resource-group "$RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku Basic \
        --admin-enabled true \
        --tags env=dev attribution=rpx
    echo -e "${GREEN}✓ Created${NC}"
fi

# Get ACR credentials
echo "Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)
echo "ACR Login Server: ${ACR_NAME}.azurecr.io"
echo "ACR Username: $ACR_USERNAME"
echo -e "${YELLOW}Note: Save these credentials in Azure DevOps Variable Groups${NC}"

# Check/Create Key Vault (optional but recommended)
echo -n "Checking Azure Key Vault... "
if az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}Creating...${NC}"
    az keyvault create --resource-group "$RESOURCE_GROUP" \
        --name "$KEY_VAULT_NAME" \
        --location "$LOCATION" \
        --enabled-for-deployment true \
        --enabled-for-template-deployment true \
        --tags env=dev attribution=rpx
    echo -e "${GREEN}✓ Created${NC}"
fi

# Create sample secrets in Key Vault
echo "Setting up sample secrets in Key Vault..."
az keyvault secret set --vault-name "$KEY_VAULT_NAME" \
    --name "DATABASE-URL-DEV" \
    --value "postgresql://username:password@server:5432/rpx_engine_dev" \
    &>/dev/null
az keyvault secret set --vault-name "$KEY_VAULT_NAME" \
    --name "SECRET-KEY-DEV" \
    --value "$(openssl rand -hex 32)" \
    &>/dev/null
echo -e "${GREEN}✓ Sample secrets created${NC}"

# Display next steps
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next Steps:"
echo "1. Create Service Connections in Azure DevOps:"
echo "   - Name: rpx-azure-connection (Azure Resource Manager)"
echo "   - Name: rpx-acr-connection (Docker Registry)"
echo ""
echo "2. Create Variable Groups in Azure DevOps:"
echo "   - rpx-backend-common:"
echo "     * ACR_USERNAME = $ACR_USERNAME"
echo "     * ACR_PASSWORD = [Mark as secret]"
echo ""
echo "   - rpx-backend-dev:"
echo "     * DATABASE_URL_DEV = [Your PostgreSQL connection string]"
echo "     * SECRET_KEY_DEV = [Mark as secret]"
echo ""
echo "   - rpx-backend-prod:"
echo "     * DATABASE_URL_PROD = [Your PostgreSQL connection string]"
echo "     * SECRET_KEY_PROD = [Mark as secret]"
echo ""
echo "3. Import pipelines in Azure DevOps:"
echo "   - azure-pipelines.yml (main CI/CD)"
echo "   - azure-pipelines-deploy.yml (manual deployment)"
echo ""
echo "4. Configure branch policies for main and develop branches"
echo ""
echo "ACR Login Command:"
echo "az acr login --name $ACR_NAME"
echo ""
echo "Docker Login Command:"
echo "docker login ${ACR_NAME}.azurecr.io -u $ACR_USERNAME"