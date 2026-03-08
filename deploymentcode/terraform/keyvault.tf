resource "azurerm_key_vault" "ml" {
  name                = "kv-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  public_network_access_enabled = true

  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  tags = var.tags
}
