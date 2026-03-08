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

resource "azurerm_storage_container" "facade_images" {
  name                  = "facade-images"
  storage_account_name  = azurerm_storage_account.ml.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "ldr_files" {
  name                  = "ldr-files"
  storage_account_name  = azurerm_storage_account.ml.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "reference_models" {
  name                  = "reference-models"
  storage_account_name  = azurerm_storage_account.ml.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "training_data" {
  name                  = "training-data"
  storage_account_name  = azurerm_storage_account.ml.name
  container_access_type = "private"
}
