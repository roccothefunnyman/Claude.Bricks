# --- Custom Vision ---

resource "azurerm_cognitive_account" "custom_vision_training" {
  count = var.deploy_custom_vision ? 1 : 0

  name                = "cv-train-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "CustomVision.Training"
  sku_name            = "F0"

  public_network_access_enabled = true

  tags = var.tags
}

resource "azurerm_cognitive_account" "custom_vision_prediction" {
  count = var.deploy_custom_vision ? 1 : 0

  name                = "cv-pred-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  kind                = "CustomVision.Prediction"
  sku_name            = "F0"

  public_network_access_enabled = true

  tags = var.tags
}

# --- Azure OpenAI ---

resource "azurerm_cognitive_account" "openai" {
  count = var.deploy_openai ? 1 : 0

  name                = "oai-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.openai_location
  kind                = "OpenAI"
  sku_name            = "S0"

  public_network_access_enabled = true

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "gpt4" {
  count = var.deploy_openai ? 1 : 0

  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai[0].id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  scale {
    type     = "Standard"
    capacity = 10
  }
}
