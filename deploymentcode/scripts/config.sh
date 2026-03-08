#!/bin/bash
# Source this file: source deploymentcode/scripts/config.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_OUT="$SCRIPT_DIR/tf_outputs.json"

if [ ! -f "$TF_OUT" ]; then
  echo "ERROR: tf_outputs.json not found. Run 'terraform output -json > tf_outputs.json' first."
  exit 1
fi

export RESOURCE_GROUP=$(jq -r '.resource_group_name.value' "$TF_OUT")
export ML_WORKSPACE=$(jq -r '.ml_workspace_name.value' "$TF_OUT")
export STORAGE_ACCOUNT=$(jq -r '.storage_account_name.value' "$TF_OUT")
export KEY_VAULT=$(jq -r '.key_vault_name.value' "$TF_OUT")
export ACR_NAME=$(jq -r '.container_registry_name.value' "$TF_OUT")
export OPENAI_ENDPOINT=$(jq -r '.openai_endpoint.value // empty' "$TF_OUT")
export SEARCH_ENDPOINT=$(jq -r '.search_service_endpoint.value // empty' "$TF_OUT")
export SEARCH_NAME=$(jq -r '.search_service_name.value // empty' "$TF_OUT")

# Derive subscription ID from az CLI context
export SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "Configured for workspace: $ML_WORKSPACE in resource group: $RESOURCE_GROUP"
