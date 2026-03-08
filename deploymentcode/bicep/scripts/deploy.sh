#!/bin/bash
set -euo pipefail

# === Configuration ===
ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== Claude.Bricks Infrastructure Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Location:    ${LOCATION}"
echo "RG:          ${RESOURCE_GROUP}"
echo ""

# Verify Azure CLI login
az account show > /dev/null 2>&1 || { echo "ERROR: Not logged in. Run 'az login' first."; exit 1; }

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo "Subscription: ${SUBSCRIPTION}"
echo ""

# Create resource group if it doesn't exist
echo "--- Creating resource group ---"
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --tags project=claude-bricks environment="${ENVIRONMENT}" managedBy=bicep

# Run what-if first
echo ""
echo "--- What-If Preview ---"
az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"

# Prompt for confirmation
echo ""
read -p "Proceed with deployment? (y/N): " CONFIRM
if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
  echo "Deployment cancelled."
  exit 0
fi

# Deploy
echo ""
echo "--- Deploying ---"
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}" \
  --name "deploy-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)" \
  --verbose

echo ""
echo "=== Deployment complete ==="

# Show outputs
echo ""
echo "--- Deployment Outputs ---"
az deployment group show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "$(az deployment group list --resource-group "${RESOURCE_GROUP}" --query '[0].name' -o tsv)" \
  --query properties.outputs \
  -o table
