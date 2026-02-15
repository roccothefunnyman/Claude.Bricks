resource "azurerm_log_analytics_workspace" "ml" {
  name                = "law-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_application_insights" "ml" {
  name                = "appi-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  application_type    = "web"

  workspace_id        = azurerm_log_analytics_workspace.ml.id
  sampling_percentage = 100
  retention_in_days   = 30

  tags = var.tags
}