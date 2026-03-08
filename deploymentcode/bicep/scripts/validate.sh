#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== Bicep Validation ==="

# Lint (compile to ARM)
echo "--- Linting (bicep build) ---"
az bicep build --file "${TEMPLATE_FILE}" --stdout > /dev/null
echo "Lint: PASSED"

# Validate against Azure
echo ""
echo "--- Validating against Azure ---"
az deployment group validate \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"

echo ""
echo "Validation: PASSED"
