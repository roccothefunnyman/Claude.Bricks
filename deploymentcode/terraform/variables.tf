# --- Authentication ---

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

# --- Naming & Environment ---

variable "project" {
  description = "Project name used in resource naming"
  type        = string
  default     = "azureml-modularbuildings"
}

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
  description = "Azure region for OpenAI (limited region availability)"
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

# --- Feature Flags ---

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

variable "deploy_compute_instance" {
  description = "Whether to deploy dev compute instance"
  type        = bool
  default     = true
}

variable "deploy_ai_search" {
  description = "Whether to deploy Azure AI Search for RAG scenarios"
  type        = bool
  default     = true
}

# --- Compute Sizing ---

variable "compute_instance_size" {
  description = "VM size for dev compute instance"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "cpu_cluster_size" {
  description = "VM size for CPU compute cluster"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "cpu_cluster_max_nodes" {
  description = "Max nodes for CPU compute cluster"
  type        = number
  default     = 4
}

variable "gpu_cluster_size" {
  description = "VM size for GPU compute cluster"
  type        = string
  default     = "Standard_NC4as_T4_v3"
}

variable "gpu_cluster_max_nodes" {
  description = "Max nodes for GPU compute cluster"
  type        = number
  default     = 2
}

# --- AI Search ---

variable "search_sku" {
  description = "SKU for Azure AI Search (free, basic, standard)"
  type        = string
  default     = "basic"
}
