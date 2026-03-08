resource "azurerm_machine_learning_workspace" "main" {
  name                = "mlw-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  application_insights_id = azurerm_application_insights.ml.id
  key_vault_id            = azurerm_key_vault.ml.id
  storage_account_id      = azurerm_storage_account.ml.id
  container_registry_id   = azurerm_container_registry.ml.id

  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  high_business_impact = false
  sku_name             = "Basic"

  tags = var.tags
}
