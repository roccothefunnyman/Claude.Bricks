resource "azurerm_storage_account" "ml" {
  name                     = "st${replace(var.project, "-", "")}${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  public_network_access_enabled   = true
  allow_nested_items_to_be_public = true

  tags = var.tags
}