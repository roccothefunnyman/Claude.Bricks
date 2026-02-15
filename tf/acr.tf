resource "azurerm_container_registry" "ml" {
  name                = "cr${replace(var.project, "-", "")}${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  public_network_access_enabled = true

  tags = var.tags
}