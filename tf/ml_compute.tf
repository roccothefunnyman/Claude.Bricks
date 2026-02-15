# --- Dev Compute Instance ---

resource "azurerm_machine_learning_compute_instance" "dev" {
  count = var.deploy_compute_instance ? 1 : 0

  name                          = "ci-dev-${var.environment}"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  virtual_machine_size          = var.compute_instance_size
  authorization_type            = "personal"

  tags = var.tags
}

# --- CPU Compute Cluster ---

resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  location                      = azurerm_resource_group.main.location
  vm_size                       = var.cpu_cluster_size
  vm_priority                   = "LowPriority"

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.cpu_cluster_max_nodes
    scale_down_nodes_after_idle_duration = "PT5M"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# --- GPU Compute Cluster ---

resource "azurerm_machine_learning_compute_cluster" "gpu" {
  count = var.deploy_gpu_cluster ? 1 : 0

  name                          = "gpu-cluster"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  location                      = azurerm_resource_group.main.location
  vm_size                       = var.gpu_cluster_size
  vm_priority                   = "LowPriority"

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.gpu_cluster_max_nodes
    scale_down_nodes_after_idle_duration = "PT5M"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}