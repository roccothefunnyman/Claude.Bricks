output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "ml_workspace_name" {
  value = azurerm_machine_learning_workspace.main.name
}

output "ml_workspace_id" {
  value = azurerm_machine_learning_workspace.main.id
}

output "storage_account_name" {
  value = azurerm_storage_account.ml.name
}

output "key_vault_name" {
  value = azurerm_key_vault.ml.name
}

output "container_registry_name" {
  value = azurerm_container_registry.ml.name
}

output "container_registry_login_server" {
  value = azurerm_container_registry.ml.login_server
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.ml.connection_string
  sensitive = true
}

output "openai_endpoint" {
  value = var.deploy_openai ? azurerm_cognitive_account.openai[0].endpoint : null
}

output "custom_vision_training_endpoint" {
  value = var.deploy_custom_vision ? azurerm_cognitive_account.custom_vision_training[0].endpoint : null
}

output "custom_vision_prediction_endpoint" {
  value = var.deploy_custom_vision ? azurerm_cognitive_account.custom_vision_prediction[0].endpoint : null
}