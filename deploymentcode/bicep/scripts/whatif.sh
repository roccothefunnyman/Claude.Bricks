#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== What-If Preview ==="
echo "Environment: ${ENVIRONMENT}"
echo "RG:          ${RESOURCE_GROUP}"
echo ""

az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"
