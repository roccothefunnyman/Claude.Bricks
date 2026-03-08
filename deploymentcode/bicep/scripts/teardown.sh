#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"

echo "=== Teardown ==="
echo "This will DELETE resource group: ${RESOURCE_GROUP}"
echo "ALL resources in this group will be permanently destroyed."
echo ""

read -p "Type the resource group name to confirm: " CONFIRM
if [[ "${CONFIRM}" != "${RESOURCE_GROUP}" ]]; then
  echo "Name does not match. Teardown cancelled."
  exit 1
fi

echo ""
echo "Deleting resource group ${RESOURCE_GROUP}..."
az group delete --name "${RESOURCE_GROUP}" --yes --no-wait

echo "Deletion initiated (running in background)."
echo "Monitor with: az group show --name ${RESOURCE_GROUP} --query properties.provisioningState"
