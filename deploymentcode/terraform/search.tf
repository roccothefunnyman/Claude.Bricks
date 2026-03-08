resource "azurerm_search_service" "main" {
  count = var.deploy_ai_search ? 1 : 0

  name                = "srch-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku

  public_network_access_enabled = true
  semantic_search_sku           = "free"

  replica_count  = 1
  partition_count = 1

  tags = var.tags
}
