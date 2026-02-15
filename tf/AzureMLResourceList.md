# Azure ML Resource Deployment Guide for Claude.Bricks

This document provides guidance for creating a Terraform repository to deploy Azure Machine Learning resources for the Claude.Bricks LEGO building generation project. The deployment supports four ML scenarios:

1. **Image-to-Building-Spec Model** - Analyze building photos to generate structured specs
2. **Structural Validation** - Anomaly detection for .ldr file validation
3. **Pattern Extraction** - Embeddings and clustering for reference file analysis
4. **Fine-Tuned Spec Generator** - Custom language model for building specifications

---

## Deployment Principles

### Cost Optimization (MANDATORY)

Always apply these cost-saving configurations:

- **Use public endpoints** - Avoid private endpoints, Private Link, and VNet integration (adds significant cost and complexity)
- **Set compute cluster minimum nodes to 0** - Clusters scale to zero when idle, eliminating idle costs
- **Use spot/low-priority VMs** for training workloads where interruption is acceptable
- **Use Standard tier storage** (Standard_LRS) - not Premium or GRS unless specifically required
- **Use Free tier (F0)** for Custom Vision during development, upgrade to Standard (S0) only for production
- **Deploy to a single region** - avoid multi-region replication unless required
- **Use serverless compute** where available instead of dedicated clusters
- **Delete fine-tuned model deployments** when not in active use (hourly hosting charges apply)

### Public Access Configuration (MANDATORY)

All resources must be deployed with public network access enabled:

- `public_network_access_enabled = true` on all applicable resources
- Do NOT configure private endpoints
- Do NOT configure VNet service endpoints
- Do NOT configure managed virtual networks
- Do NOT enable firewall rules that restrict access (use "Allow all networks")

---

## Resource Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Resource Group                               │
│  (rg-claudebricks-{env}-{region})                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Azure Machine Learning Workspace                │   │
│  │           (mlw-claudebricks-{env})                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │              │              │              │         │
│           ▼              ▼              ▼              ▼         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐   │
│  │   Storage   │ │  Key Vault  │ │     ACR     │ │ App      │   │
│  │   Account   │ │             │ │             │ │ Insights │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Compute Resources                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │   │
│  │  │  Compute    │  │   GPU       │  │   Serverless    │   │   │
│  │  │  Instance   │  │   Cluster   │  │   Compute       │   │   │
│  │  │  (dev)      │  │  (training) │  │   (jobs)        │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  AI Services                              │   │
│  │  ┌─────────────┐  ┌─────────────┐                        │   │
│  │  │  Custom     │  │  Azure      │                        │   │
│  │  │  Vision     │  │  OpenAI     │                        │   │
│  │  └─────────────┘  └─────────────┘                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                Managed Online Endpoints                   │   │
│  │  (Created via AzureML SDK/CLI after model training)      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Terraform Resource List

### 1. Foundation Resources

#### Resource Group
```hcl
resource "azurerm_resource_group" "main" {
  name     = "rg-claudebricks-${var.environment}-${var.location}"
  location = var.location
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_resource_group`

---

#### Storage Account
```hcl
resource "azurerm_storage_account" "ml" {
  name                     = "stclaudebricks${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"           # COST: Use Standard, not Premium
  account_replication_type = "LRS"                # COST: Use LRS, not GRS/ZRS
  account_kind             = "StorageV2"
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  allow_nested_items_to_be_public = true
  
  # Do NOT enable these:
  # shared_access_key_enabled = false  # Keep true (default)
  # network_rules { ... }              # Do not add network restrictions
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_storage_account`

**Cost settings:**
- `account_tier = "Standard"` (not Premium)
- `account_replication_type = "LRS"` (not GRS, ZRS, GZRS)
- Do NOT enable blob versioning unless required
- Do NOT enable soft delete with long retention periods

---

#### Key Vault
```hcl
resource "azurerm_key_vault" "ml" {
  name                = "kv-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"                # COST: Use standard, not premium
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  # Do NOT configure network_acls with restrictions
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }
  
  purge_protection_enabled   = false              # COST: Disable for dev environments
  soft_delete_retention_days = 7                  # COST: Minimum retention
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_key_vault`

**Cost settings:**
- `sku_name = "standard"` (not premium)
- `purge_protection_enabled = false` for dev/test
- `soft_delete_retention_days = 7` (minimum)

---

#### Container Registry
```hcl
resource "azurerm_container_registry" "ml" {
  name                = "crclaudebricks${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"                   # COST: Use Basic for dev, Standard for prod
  admin_enabled       = true
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  # Do NOT configure network_rule_set with restrictions
  # Do NOT enable geo-replication (Premium only, adds cost)
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_container_registry`

**Cost settings:**
- `sku = "Basic"` for development ($0.167/day)
- `sku = "Standard"` for production ($0.667/day)
- Do NOT use Premium unless you need geo-replication or private endpoints
- `admin_enabled = true` simplifies access (no managed identity complexity)

---

#### Application Insights
```hcl
resource "azurerm_application_insights" "ml" {
  name                = "appi-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  application_type    = "web"
  
  # COST: Use workspace-based for better cost control
  workspace_id = azurerm_log_analytics_workspace.ml.id
  
  # COST: Sampling reduces ingestion costs
  sampling_percentage = 100  # Reduce to 50 or 25 for cost savings in prod
  
  retention_in_days = 30     # COST: Minimum retention (default is 90)
  
  tags = var.tags
}

resource "azurerm_log_analytics_workspace" "ml" {
  name                = "law-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"               # COST: Pay per GB ingested
  retention_in_days   = 30                        # COST: Minimum retention
  
  tags = var.tags
}
```

**Terraform resource types:** 
- `azurerm_application_insights`
- `azurerm_log_analytics_workspace`

**Cost settings:**
- `retention_in_days = 30` (minimum)
- Consider `sampling_percentage = 50` or lower for production
- Use PerGB2018 SKU (pay as you go)

---

### 2. Azure Machine Learning Workspace

```hcl
resource "azurerm_machine_learning_workspace" "main" {
  name                = "mlw-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  application_insights_id = azurerm_application_insights.ml.id
  key_vault_id            = azurerm_key_vault.ml.id
  storage_account_id      = azurerm_storage_account.ml.id
  container_registry_id   = azurerm_container_registry.ml.id
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  # Do NOT configure these (adds cost/complexity):
  # managed_network { ... }
  # primary_user_assigned_identity = ...
  # encryption { ... }
  
  identity {
    type = "SystemAssigned"   # COST: System-assigned is simpler/cheaper than user-assigned
  }
  
  # COST: Do not enable high business impact (adds restrictions)
  high_business_impact = false
  
  sku_name = "Basic"          # COST: Basic is sufficient for most workloads
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_machine_learning_workspace`

**Cost settings:**
- `sku_name = "Basic"` (not Enterprise)
- `public_network_access_enabled = true`
- `high_business_impact = false`
- Use SystemAssigned identity (simpler)

---

### 3. Compute Resources

#### Compute Instance (Development)
```hcl
resource "azurerm_machine_learning_compute_instance" "dev" {
  name                          = "ci-dev-${var.environment}"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  virtual_machine_size          = "Standard_DS3_v2"   # COST: Use smallest size that works
  
  # COST: Enable auto-shutdown
  # Note: This is configured via the AzureML SDK/CLI, not Terraform directly
  # Use azurerm_machine_learning_compute_instance schedule if available
  
  authorization_type = "personal"
  
  # Do NOT assign to subnet (keeps it public)
  # subnet_resource_id = ...
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_machine_learning_compute_instance`

**Cost settings:**
- Use smallest viable VM size (Standard_DS3_v2 or Standard_DS2_v2)
- Configure auto-shutdown schedule via AzureML portal/SDK
- Stop the instance when not in use

**Recommended VM sizes (by cost):**
- Development: `Standard_DS2_v2` (2 cores, 7GB RAM) - ~$0.146/hour
- Standard: `Standard_DS3_v2` (4 cores, 14GB RAM) - ~$0.293/hour

---

#### CPU Compute Cluster
```hcl
resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_size                       = "Standard_DS3_v2"
  vm_priority                   = "LowPriority"       # COST: Up to 80% savings
  
  scale_settings {
    min_node_count                       = 0          # COST: Scale to zero when idle
    max_node_count                       = 4
    scale_down_nodes_after_idle_duration = "PT5M"     # COST: Scale down after 5 minutes
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  # Do NOT assign to subnet (keeps it public)
  # subnet_resource_id = ...
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_machine_learning_compute_cluster`

**Cost settings:**
- `vm_priority = "LowPriority"` (up to 80% cost reduction, but can be preempted)
- `min_node_count = 0` (CRITICAL - ensures no idle costs)
- `scale_down_nodes_after_idle_duration = "PT5M"` (aggressive scale-down)

---

#### GPU Compute Cluster (Training)
```hcl
resource "azurerm_machine_learning_compute_cluster" "gpu" {
  name                          = "gpu-cluster"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_size                       = "Standard_NC6s_v3"  # COST: Smallest GPU VM
  vm_priority                   = "LowPriority"       # COST: Up to 80% savings
  
  scale_settings {
    min_node_count                       = 0          # COST: Scale to zero when idle
    max_node_count                       = 2          # COST: Limit max nodes
    scale_down_nodes_after_idle_duration = "PT5M"     # COST: Aggressive scale-down
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_machine_learning_compute_cluster`

**GPU VM Size Options (by cost, approximate):**
| VM Size | GPUs | GPU Memory | Approx. Cost/hour | Use Case |
|---------|------|------------|-------------------|----------|
| Standard_NC6s_v3 | 1x V100 | 16 GB | ~$3.06 | Small models |
| Standard_NC12s_v3 | 2x V100 | 32 GB | ~$6.12 | Medium models |
| Standard_NC24s_v3 | 4x V100 | 64 GB | ~$12.24 | Large models |
| Standard_NC4as_T4_v3 | 1x T4 | 16 GB | ~$0.53 | Inference, small training |

**COST RECOMMENDATION:** Start with `Standard_NC4as_T4_v3` (T4 GPU) for development - it's significantly cheaper than V100-based VMs. Use V100 VMs only for production training runs.

---

### 4. AI Services

#### Custom Vision (Image-to-Spec Model)
```hcl
resource "azurerm_cognitive_account" "custom_vision_training" {
  name                = "cv-train-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  kind                = "CustomVision.Training"
  sku_name            = "F0"                      # COST: Free tier for dev
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  # Do NOT configure network_acls with restrictions
  
  tags = var.tags
}

resource "azurerm_cognitive_account" "custom_vision_prediction" {
  name                = "cv-pred-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  kind                = "CustomVision.Prediction"
  sku_name            = "F0"                      # COST: Free tier for dev
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  tags = var.tags
}
```

**Terraform resource type:** `azurerm_cognitive_account`

**Cost settings:**
- `sku_name = "F0"` for development (Free tier: 2 transactions/second, 10K predictions/month)
- `sku_name = "S0"` for production ($2/1K transactions)

**Regional availability:** Custom Vision is not available in all regions. Check Azure documentation. Common regions: East US, West US 2, West Europe, Southeast Asia.

---

#### Azure OpenAI (Fine-Tuned Spec Generator)
```hcl
resource "azurerm_cognitive_account" "openai" {
  name                = "oai-claudebricks-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.openai_location       # Limited regions available
  kind                = "OpenAI"
  sku_name            = "S0"
  
  # PUBLIC ACCESS - Required
  public_network_access_enabled = true
  
  tags = var.tags
}

# Model deployments are created via azurerm_cognitive_deployment
resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  
  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }
  
  sku {
    name     = "Standard"
    capacity = 10                                  # COST: Start with low TPM
  }
}
```

**Terraform resource types:**
- `azurerm_cognitive_account` (kind = "OpenAI")
- `azurerm_cognitive_deployment`

**Cost settings:**
- Start with low capacity (TPM - tokens per minute)
- Use `gpt-4o-mini` for fine-tuning (cheaper than gpt-4o)
- Delete fine-tuned deployments when not in use (hourly hosting charges)

**Regional availability for fine-tuning:** East US, East US 2, North Central US, Sweden Central, Switzerland West. Check current availability.

**Fine-tuning costs (approximate):**
- Training: $25/million tokens (gpt-4o-mini)
- Hosting: $1.70/hour for fine-tuned models
- Inference: $0.30/million input tokens, $1.20/million output tokens

---

### 5. Managed Online Endpoints

Managed online endpoints are typically created via the AzureML SDK/CLI after model training, not via Terraform. However, you can prepare the quota and permissions.

**Post-Terraform deployment (via AzureML CLI):**
```bash
# Create endpoint
az ml online-endpoint create --name claudebricks-validator \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $WORKSPACE_NAME

# Create deployment
az ml online-deployment create --name blue \
  --endpoint-name claudebricks-validator \
  --model azureml:validator-model@latest \
  --instance-type Standard_DS3_v2 \
  --instance-count 1
```

**Cost settings for endpoints:**
- Use smallest instance type that meets latency requirements
- Start with `instance_count = 1`
- Enable autoscaling with `min_instances = 0` if your endpoint supports scale-to-zero
- Use `Standard_DS2_v2` or `Standard_DS3_v2` for CPU inference
- Use `Standard_NC4as_T4_v3` for GPU inference (cheapest GPU option)

---

## Variables File Structure

```hcl
# variables.tf

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for deployment"
  type        = string
  default     = "eastus"
}

variable "openai_location" {
  description = "Azure region for OpenAI (limited availability)"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "ClaudeBricks"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

variable "deploy_custom_vision" {
  description = "Whether to deploy Custom Vision resources"
  type        = bool
  default     = true
}

variable "deploy_openai" {
  description = "Whether to deploy Azure OpenAI resources"
  type        = bool
  default     = true
}

variable "deploy_gpu_cluster" {
  description = "Whether to deploy GPU compute cluster"
  type        = bool
  default     = true
}
```

---

## Terraform File Structure

```
terraform/
├── main.tf                 # Provider configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── resource_group.tf       # Resource group
├── storage.tf              # Storage account
├── keyvault.tf             # Key Vault
├── acr.tf                  # Container Registry
├── monitoring.tf           # App Insights + Log Analytics
├── ml_workspace.tf         # AzureML Workspace
├── ml_compute.tf           # Compute instances and clusters
├── cognitive_services.tf   # Custom Vision + OpenAI
├── terraform.tfvars        # Variable values (gitignored)
└── terraform.tfvars.example # Example variable values
```

---

## Provider Configuration

```hcl
# main.tf

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
  
  # COST: Use local backend for dev, remote for prod
  # backend "azurerm" {
  #   resource_group_name  = "rg-terraform-state"
  #   storage_account_name = "stterraformstate"
  #   container_name       = "tfstate"
  #   key                  = "claudebricks.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true         # COST: Clean up for dev
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

data "azurerm_client_config" "current" {}
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Azure subscription with sufficient quota for GPU VMs (request if needed)
- [ ] Service principal or user with Contributor + User Access Administrator roles
- [ ] Azure OpenAI access approved (requires application)
- [ ] Custom Vision available in target region

### Post-Deployment
- [ ] Configure compute instance auto-shutdown schedule
- [ ] Verify compute clusters scale to zero when idle
- [ ] Test connectivity to all endpoints
- [ ] Configure RBAC roles for team members
- [ ] Create initial model deployments via AzureML CLI

### Cost Monitoring
- [ ] Set up Azure Cost Management budget alerts
- [ ] Tag all resources for cost allocation
- [ ] Review compute cluster utilization weekly
- [ ] Delete unused endpoints and models

---

## Estimated Monthly Costs (Development Environment)

| Resource | Configuration | Est. Monthly Cost |
|----------|--------------|-------------------|
| Storage Account | Standard LRS, 50GB | ~$1 |
| Key Vault | Standard | ~$0.03/10K operations |
| Container Registry | Basic | ~$5 |
| Log Analytics | 5GB ingestion | ~$12 |
| Application Insights | Included with LA | $0 |
| ML Workspace | Basic SKU | $0 (no charge for workspace itself) |
| Compute Instance | DS3_v2, 40 hrs/month | ~$12 |
| CPU Cluster | DS3_v2, Low Priority, 20 hrs/month | ~$1.20 |
| GPU Cluster | NC4as_T4_v3, Low Priority, 10 hrs/month | ~$1.10 |
| Custom Vision | Free tier | $0 |
| Azure OpenAI | 100K tokens/month | ~$0.05 |
| **TOTAL (Dev)** | | **~$35/month** |

**Note:** Actual costs depend heavily on usage. GPU training and fine-tuned model hosting are the primary cost drivers in production.

---

## References

- [Azure Machine Learning workspace Terraform](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-workspace-terraform)
- [Create compute clusters](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-compute-cluster)
- [GPU VM sizes](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes-gpu)
- [Custom Vision quickstart](https://learn.microsoft.com/en-us/azure/ai-services/custom-vision-service/quickstarts/image-classification)
- [Azure OpenAI fine-tuning](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/fine-tuning)
- [Managed online endpoints](https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online)
- [Azure ML pricing](https://azure.microsoft.com/en-us/pricing/details/machine-learning/)
