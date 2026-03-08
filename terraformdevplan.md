# Claude.Bricks Deployment Plan

Complete instructions for deploying all Azure resources and SDK/CLI scripts needed
to run the four ML scenarios described in the DP-100 course deck.

All code (Terraform, Python scripts, YAML configs, shell scripts) lives under
`\deploymentcode` off the repo root.

---

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [Prerequisites and Manual Portal Steps](#2-prerequisites-and-manual-portal-steps)
3. [Phase 1: Shared Infrastructure (Terraform)](#3-phase-1-shared-infrastructure-terraform)
4. [Phase 2: Post-Terraform Bootstrap (CLI/SDK)](#4-phase-2-post-terraform-bootstrap-clisdk)
5. [Phase 3: Scenario 1 -- Facade Style Classification](#5-phase-3-scenario-1----facade-style-classification)
6. [Phase 4: Scenario 2 -- Structural Validation (Anomaly Detection)](#6-phase-4-scenario-2----structural-validation-anomaly-detection)
7. [Phase 5: Scenario 3 -- Pattern Extraction (Clustering)](#7-phase-5-scenario-3----pattern-extraction-clustering)
8. [Phase 6: Scenario 4 -- Fine-Tuned LLM Spec Generator](#8-phase-6-scenario-4----fine-tuned-llm-spec-generator)
9. [Teardown](#9-teardown)
10. [Cost Summary](#10-cost-summary)

---

## 1. Directory Structure

```
deploymentcode/
├── terraform/                     # All Terraform (.tf) files
│   ├── main.tf                    # Provider config, backend
│   ├── variables.tf               # Input variables
│   ├── outputs.tf                 # Output values consumed by scripts
│   ├── resource_group.tf          # azurerm_resource_group
│   ├── storage.tf                 # azurerm_storage_account + blob containers
│   ├── keyvault.tf                # azurerm_key_vault
│   ├── acr.tf                     # azurerm_container_registry
│   ├── monitoring.tf              # azurerm_log_analytics_workspace + azurerm_application_insights
│   ├── ml_workspace.tf            # azurerm_machine_learning_workspace
│   ├── ml_compute.tf              # compute instance + CPU cluster + GPU cluster
│   ├── cognitive_services.tf      # Custom Vision + Azure OpenAI + model deployment
│   ├── search.tf                  # azurerm_search_service (AI Search)
│   ├── terraform.tfvars.example   # Example variable values
│   └── .gitignore                 # Ignore .terraform/, *.tfstate*, terraform.tfvars
│
├── scripts/                       # Post-Terraform setup scripts (Python + shell)
│   ├── requirements.txt           # Python dependencies for all scripts
│   ├── config.sh                  # Reads Terraform outputs, exports as env vars
│   ├── 00_bootstrap.py            # Create datastores, upload seed data, register environments
│   │
│   ├── scenario1/                 # Facade Style Classification
│   │   ├── prepare_data.py        # Upload images, create data asset (uri_folder)
│   │   ├── train.py               # Training script (runs ON the cluster)
│   │   ├── train_job.py           # Submit command job via SDK
│   │   ├── train_job.yml          # Alternative: az ml job create YAML
│   │   ├── register_model.py      # Register best model from MLflow run
│   │   ├── deploy_endpoint.py     # Create managed online endpoint + deployment
│   │   ├── endpoint.yml           # Endpoint YAML for CLI deployment
│   │   ├── deployment.yml         # Deployment YAML for CLI deployment
│   │   └── score.py               # Scoring script for the endpoint
│   │
│   ├── scenario2/                 # Structural Validation
│   │   ├── feature_engineering.py # Parse .ldr files, extract numeric features
│   │   ├── prepare_data.py        # Upload features CSV, create data asset (uri_file)
│   │   ├── train.py               # Anomaly detection training script
│   │   ├── train_job.py           # Submit command job
│   │   ├── register_model.py      # Register trained model
│   │   ├── deploy_endpoint.py     # Deploy to managed online endpoint
│   │   └── score.py               # Scoring script
│   │
│   ├── scenario3/                 # Pattern Extraction
│   │   ├── extract_stats.py       # Extract part-usage stats from .ldr files
│   │   ├── prepare_data.py        # Upload stats, create data asset (uri_file)
│   │   ├── train.py               # Clustering/embedding training script
│   │   ├── train_job.py           # Submit command job
│   │   ├── pipeline_job.py        # Multi-step pipeline: extract -> embed -> cluster
│   │   └── register_model.py      # Register clustering model
│   │
│   ├── scenario4/                 # Fine-Tuned LLM
│   │   ├── prepare_training_data.py   # Format spec examples as JSONL
│   │   ├── upload_training_data.py    # Upload to blob, create data asset
│   │   ├── fine_tune_job.py           # Submit fine-tuning job via OpenAI SDK
│   │   ├── deploy_model.py            # Deploy fine-tuned model to endpoint
│   │   ├── rag_index_setup.py         # Create AI Search index + upload embeddings
│   │   ├── promptflow/               # Prompt flow definition files
│   │   │   ├── flow.dag.yaml         # Flow DAG definition
│   │   │   ├── retrieve.py           # Retrieval node (queries AI Search)
│   │   │   ├── generate.py           # Generation node (calls OpenAI)
│   │   │   └── requirements.txt      # Flow dependencies
│   │   └── evaluate_flow.py          # Compare prompt strategies
│   │
│   └── common/                    # Shared utilities
│       ├── ml_client.py           # MLClient factory (reads env vars from config.sh)
│       └── blob_upload.py         # Utility: upload local folder to blob container
│
└── data/                          # Seed/sample data (small files only, large data in blob)
    ├── scenario1/                 # Sample facade images (5-10 for testing)
    ├── scenario2/                 # Sample .ldr files (pass/fail labeled)
    ├── scenario3/                 # Sample reference .ldr files
    └── scenario4/                 # Sample spec JSONL training examples
```

---

## 2. Prerequisites and Manual Portal Steps

These steps MUST be completed before running Terraform or any scripts.

### 2.1 Tools to Install Locally

| Tool | Version | Install |
|------|---------|---------|
| Azure CLI | >= 2.50 | `winget install Microsoft.AzureCLI` |
| Azure CLI ML extension | v2 | `az extension add -n ml` |
| Terraform | >= 1.0 | `winget install Hashicorp.Terraform` |
| Python | >= 3.10 | `winget install Python.Python.3.12` |
| Git | any | `winget install Git.Git` |

### 2.2 Azure Subscription Access

- You need **Contributor** + **User Access Administrator** on the subscription
  (or **Owner**, which includes both).
- Run `az login` and `az account set --subscription <ID>` to confirm access.

### 2.3 Manual Portal Steps (cannot be automated)

#### GPU Quota Request (REQUIRED for Scenarios 1, 2, 4 GPU training)

1. Go to Azure Portal > **Subscriptions** > your subscription > **Usage + quotas**
2. Filter by **Machine Learning** provider
3. Search for the VM family you need (e.g., `NCasT4_v3` or `NC6s_v3`)
4. Click **Request increase** and specify the number of cores
5. Submit and wait for approval (can take minutes to days)

**If you skip this:** Terraform will deploy compute clusters but jobs targeting GPU
will fail with a quota error. CPU-only fallback is possible for Scenarios 2 and 3.

#### Azure OpenAI Access (REQUIRED for Scenario 4)

1. Check if your subscription already has Azure OpenAI access:
   `az cognitiveservices account list --query "[?kind=='OpenAI']"`
2. If not, apply at: https://aka.ms/oai/access
3. Approval is typically automatic for most enterprise subscriptions but may take
   1-2 business days for others.

**If you skip this:** The `azurerm_cognitive_account` (kind=OpenAI) resource in
Terraform will fail to create. Set `deploy_openai = false` in tfvars to skip it.

#### Custom Vision Regional Availability (Scenario 1)

Custom Vision is NOT available in all Azure regions. Confirm your region supports it:
- Supported regions (as of 2025): East US, East US 2, West US 2, West Europe,
  Southeast Asia, Australia East, North Europe, South Central US
- Check: https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/

**If your region doesn't support it:** Use Azure ML AutoML for image classification
instead (available in all regions that support Azure ML).

---

## 3. Phase 1: Shared Infrastructure (Terraform)

### 3.1 What Terraform Creates

| Resource | Terraform Type | Purpose |
|----------|---------------|---------|
| Resource Group | `azurerm_resource_group` | Container for all resources |
| Storage Account | `azurerm_storage_account` | Data, artifacts, model files |
| Key Vault | `azurerm_key_vault` | Secrets, keys, connection strings |
| Container Registry | `azurerm_container_registry` | Docker images for environments |
| Log Analytics Workspace | `azurerm_log_analytics_workspace` | Monitoring backend |
| Application Insights | `azurerm_application_insights` | ML workspace telemetry |
| ML Workspace | `azurerm_machine_learning_workspace` | Central ML hub |
| Compute Instance | `azurerm_machine_learning_compute_instance` | Dev notebooks |
| CPU Compute Cluster | `azurerm_machine_learning_compute_cluster` | Training (Scenarios 1-3) |
| GPU Compute Cluster | `azurerm_machine_learning_compute_cluster` | Training (Scenarios 1, 4) |
| Custom Vision (Training) | `azurerm_cognitive_account` (kind=CustomVision.Training) | Scenario 1 |
| Custom Vision (Prediction) | `azurerm_cognitive_account` (kind=CustomVision.Prediction) | Scenario 1 |
| Azure OpenAI | `azurerm_cognitive_account` (kind=OpenAI) | Scenario 4 |
| OpenAI Model Deployment | `azurerm_cognitive_deployment` | gpt-4o-mini for Scenario 4 |
| Azure AI Search | `azurerm_search_service` | RAG vector store for Scenario 4 |

### 3.2 New Terraform File: search.tf

The existing `tf/` folder is missing Azure AI Search. This must be added.

```hcl
# deploymentcode/terraform/search.tf

variable "deploy_ai_search" {
  description = "Whether to deploy Azure AI Search for RAG scenarios"
  type        = bool
  default     = true
}

variable "search_sku" {
  description = "SKU for Azure AI Search (free, basic, standard)"
  type        = string
  default     = "basic"
}

resource "azurerm_search_service" "main" {
  count = var.deploy_ai_search ? 1 : 0

  name                = "srch-${var.project}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku

  # PUBLIC ACCESS - Required for lab
  public_network_access_enabled = true

  # Semantic search (needed for hybrid RAG queries)
  semantic_search_sku = "free"

  # Replica and partition counts (basic tier allows 1 partition, up to 3 replicas)
  replica_count  = 1
  partition_count = 1

  tags = var.tags
}
```

**AI Search SKU guidance:**
| SKU | Price/month | Storage | Indexes | Best For |
|-----|-------------|---------|---------|----------|
| free | $0 | 50 MB | 3 | Testing only (1 per subscription) |
| basic | ~$75 | 2 GB | 15 | Labs, small datasets |
| standard | ~$250 | 50 GB | 50 | Production |

Use `basic` for lab work. The free tier is limited to 3 indexes and 50 MB.

### 3.3 New Output: search endpoint

Add to `outputs.tf`:
```hcl
output "search_service_name" {
  value = var.deploy_ai_search ? azurerm_search_service.main[0].name : null
}

output "search_service_endpoint" {
  value = var.deploy_ai_search ? "https://${azurerm_search_service.main[0].name}.search.windows.net" : null
}
```

### 3.4 Storage Account: Add Blob Containers

Add to `storage.tf` so each scenario has a dedicated container:

```hcl
resource "azurerm_storage_container" "facade_images" {
  name                  = "facade-images"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "ldr_files" {
  name                  = "ldr-files"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "reference_models" {
  name                  = "reference-models"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "training_data" {
  name                  = "training-data"
  storage_account_id    = azurerm_storage_account.ml.id
  container_access_type = "private"
}
```

### 3.5 Terraform Deployment Commands

```bash
cd deploymentcode/terraform

# 1. Copy and edit your variable values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your subscription_id, tenant_id, location, etc.

# 2. Initialize Terraform (downloads provider plugins)
terraform init

# 3. Preview what will be created
terraform plan -out=tfplan

# 4. Apply (creates all resources)
terraform apply tfplan

# 5. Export outputs for use by scripts
terraform output -json > ../scripts/tf_outputs.json
```

**Expected deployment time:** 5-15 minutes. The ML workspace and compute resources
take the longest.

### 3.6 Variables Reference (terraform.tfvars)

```hcl
subscription_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
tenant_id       = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

project     = "claudebricks"
environment = "dev"
location    = "eastus"

# OpenAI fine-tuning regions: East US, East US 2, North Central US,
# Sweden Central, Switzerland West
openai_location = "eastus"

tags = {
  Project     = "ClaudeBricks"
  Environment = "dev"
  ManagedBy   = "Terraform"
}

# Feature flags
deploy_custom_vision    = true
deploy_openai           = true
deploy_gpu_cluster      = true    # Set false if no GPU quota
deploy_compute_instance = true
deploy_ai_search        = true

# Compute sizing
compute_instance_size = "Standard_DS3_v2"
cpu_cluster_size      = "Standard_DS3_v2"
cpu_cluster_max_nodes = 4
gpu_cluster_size      = "Standard_NC4as_T4_v3"
gpu_cluster_max_nodes = 2

# AI Search
search_sku = "basic"
```

---

## 4. Phase 2: Post-Terraform Bootstrap (CLI/SDK)

After Terraform completes, run the bootstrap script to create resources that
Terraform cannot manage: datastores, data assets, and custom environments.

### 4.1 Python Dependencies

**File: `deploymentcode/scripts/requirements.txt`**

```
azure-ai-ml>=1.12.0
azure-identity>=1.15.0
azure-storage-blob>=12.19.0
azure-search-documents>=11.4.0
openai>=1.12.0
mlflow>=2.10.0,<=2.16.2
scikit-learn>=1.4.0
pandas>=2.1.0
Pillow>=10.0.0
mltable>=1.5.0
```

Install:
```bash
pip install -r deploymentcode/scripts/requirements.txt
```

### 4.2 Config Script

**File: `deploymentcode/scripts/config.sh`**

Reads Terraform outputs and exports them as environment variables that all
Python scripts consume.

```bash
#!/bin/bash
# Source this file: source deploymentcode/scripts/config.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_OUT="$SCRIPT_DIR/tf_outputs.json"

if [ ! -f "$TF_OUT" ]; then
  echo "ERROR: tf_outputs.json not found. Run 'terraform output -json > tf_outputs.json' first."
  exit 1
fi

export RESOURCE_GROUP=$(jq -r '.resource_group_name.value' "$TF_OUT")
export ML_WORKSPACE=$(jq -r '.ml_workspace_name.value' "$TF_OUT")
export STORAGE_ACCOUNT=$(jq -r '.storage_account_name.value' "$TF_OUT")
export KEY_VAULT=$(jq -r '.key_vault_name.value' "$TF_OUT")
export ACR_NAME=$(jq -r '.container_registry_name.value' "$TF_OUT")
export OPENAI_ENDPOINT=$(jq -r '.openai_endpoint.value // empty' "$TF_OUT")
export SEARCH_ENDPOINT=$(jq -r '.search_service_endpoint.value // empty' "$TF_OUT")
export SEARCH_NAME=$(jq -r '.search_service_name.value // empty' "$TF_OUT")

# Derive subscription ID from az CLI context
export SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "Configured for workspace: $ML_WORKSPACE in resource group: $RESOURCE_GROUP"
```

### 4.3 Shared MLClient Factory

**File: `deploymentcode/scripts/common/ml_client.py`**

```python
"""Shared MLClient factory. Reads config from environment variables."""
import os
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

def get_ml_client() -> MLClient:
    return MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.environ["SUBSCRIPTION_ID"],
        resource_group_name=os.environ["RESOURCE_GROUP"],
        workspace_name=os.environ["ML_WORKSPACE"],
    )
```

### 4.4 Bootstrap Script

**File: `deploymentcode/scripts/00_bootstrap.py`**

This script:
1. Creates datastores pointing to the blob containers Terraform created
2. Registers a base Python environment for training
3. Verifies compute targets exist

```python
"""
Bootstrap: create datastores, environments, and verify compute.
Run after Terraform apply and sourcing config.sh.

Usage:
  source scripts/config.sh
  python scripts/00_bootstrap.py
"""
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    AzureBlobDatastore,
    Environment,
    BuildContext,
)
from azure.identity import DefaultAzureCredential
from common.ml_client import get_ml_client


def create_datastores(ml_client: MLClient, storage_name: str):
    """Create datastores for each scenario's blob container."""
    containers = {
        "facade_images": "facade-images",
        "ldr_files": "ldr-files",
        "reference_models": "reference-models",
        "training_data": "training-data",
    }
    for ds_name, container in containers.items():
        ds = AzureBlobDatastore(
            name=ds_name,
            account_name=storage_name,
            container_name=container,
            description=f"Datastore for {container} container",
        )
        ml_client.datastores.create_or_update(ds)
        print(f"  Created/updated datastore: {ds_name} -> {container}")


def register_environments(ml_client: MLClient):
    """Register custom environments for training jobs."""

    # Scenario 1 & 2: scikit-learn + image processing
    sklearn_env = Environment(
        name="claudebricks-sklearn",
        description="scikit-learn environment for classification and anomaly detection",
        conda_file={
            "name": "claudebricks-sklearn",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.10",
                "pip",
                {
                    "pip": [
                        "azure-ai-ml>=1.12.0",
                        "mlflow>=2.10.0,<=2.16.2",
                        "scikit-learn>=1.4.0",
                        "pandas>=2.1.0",
                        "Pillow>=10.0.0",
                        "matplotlib>=3.8.0",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
        version="1",
    )
    ml_client.environments.create_or_update(sklearn_env)
    print("  Registered environment: claudebricks-sklearn:1")

    # Scenario 3: clustering + embeddings
    cluster_env = Environment(
        name="claudebricks-clustering",
        description="Environment for clustering and embedding extraction",
        conda_file={
            "name": "claudebricks-clustering",
            "channels": ["defaults", "conda-forge"],
            "dependencies": [
                "python=3.10",
                "pip",
                {
                    "pip": [
                        "azure-ai-ml>=1.12.0",
                        "mlflow>=2.10.0,<=2.16.2",
                        "scikit-learn>=1.4.0",
                        "pandas>=2.1.0",
                        "umap-learn>=0.5.5",
                        "hdbscan>=0.8.33",
                    ]
                },
            ],
        },
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
        version="1",
    )
    ml_client.environments.create_or_update(cluster_env)
    print("  Registered environment: claudebricks-clustering:1")


def verify_compute(ml_client: MLClient):
    """List compute targets to confirm they exist."""
    computes = ml_client.compute.list()
    print("  Available compute targets:")
    for c in computes:
        print(f"    - {c.name} ({c.type}, size={getattr(c, 'size', 'N/A')})")


def main():
    ml_client = get_ml_client()
    storage_name = os.environ["STORAGE_ACCOUNT"]

    print("1. Creating datastores...")
    create_datastores(ml_client, storage_name)

    print("2. Registering environments...")
    register_environments(ml_client)

    print("3. Verifying compute targets...")
    verify_compute(ml_client)

    print("\nBootstrap complete.")


if __name__ == "__main__":
    main()
```

**Run:**
```bash
source deploymentcode/scripts/config.sh
cd deploymentcode/scripts
python 00_bootstrap.py
```

---

## 5. Phase 3: Scenario 1 -- Facade Style Classification

**Goal:** Train an image classifier to map street photos to LEGO-friendly facade
styles (historic, modern, industrial, commercial, residential).

### 5.1 Azure Resources Used

| Resource | Created By | Notes |
|----------|-----------|-------|
| Blob container `facade-images` | Terraform | Stores training images |
| Datastore `facade_images` | Bootstrap script | Points to blob container |
| Data asset `facade-images-v1` | prepare_data.py | uri_folder of labeled images |
| Environment `claudebricks-sklearn` | Bootstrap script | Training environment |
| Compute: `cpu-cluster` or `gpu-cluster` | Terraform | Training compute |
| MLflow experiment | Automatic | Created on first job run |
| Registered model | register_model.py | Best model from training |
| Managed online endpoint | deploy_endpoint.py | Real-time inference |

### 5.2 Data Preparation

**File: `deploymentcode/scripts/scenario1/prepare_data.py`**

The image dataset must be organized in label subfolders:
```
data/scenario1/
├── historic/
│   ├── img001.jpg
│   └── img002.jpg
├── modern/
│   ├── img003.jpg
│   └── img004.jpg
├── industrial/
│   └── img005.jpg
├── commercial/
│   └── img006.jpg
└── residential/
    └── img007.jpg
```

Script logic:
```python
"""Upload labeled images and register as a data asset."""
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client

ml_client = get_ml_client()

# Upload local folder to the facade_images datastore
# The SDK handles the upload automatically when path is local
data_asset = Data(
    name="facade-images",
    version="1",
    description="Labeled facade images for style classification",
    path="../../data/scenario1/",  # local path; auto-uploaded to default datastore
    type=AssetTypes.URI_FOLDER,
)
ml_client.data.create_or_update(data_asset)
print(f"Created data asset: facade-images:1")
```

**CLI equivalent:**
```bash
az ml data create \
  --name facade-images \
  --version 1 \
  --type uri_folder \
  --path ../../data/scenario1/ \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $ML_WORKSPACE
```

### 5.3 Training Script

**File: `deploymentcode/scripts/scenario1/train.py`**

This runs ON the compute cluster (not locally). It receives data as a mounted path.

```python
"""
Image classification training script.
Runs as a command job on Azure ML compute.

Inputs:
  --data-path: mounted path to the image folder data asset
  --learning-rate: float
  --epochs: int

Outputs:
  MLflow-logged model to ./outputs/model/
"""
import argparse
import os
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from PIL import Image
import numpy as np

def load_images(data_path, img_size=(64, 64)):
    """Load images from label subfolders, return features and labels."""
    features, labels = [], []
    for label in os.listdir(data_path):
        label_dir = os.path.join(data_path, label)
        if not os.path.isdir(label_dir):
            continue
        for fname in os.listdir(label_dir):
            fpath = os.path.join(label_dir, fname)
            try:
                img = Image.open(fpath).convert("RGB").resize(img_size)
                features.append(np.array(img).flatten())
                labels.append(label)
            except Exception:
                continue
    return np.array(features), np.array(labels)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--n-estimators", type=int, default=100)
    args = parser.parse_args()

    mlflow.autolog()

    X, y = load_images(args.data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=args.n_estimators, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    mlflow.log_metric("test_accuracy", accuracy)
    print(f"Test accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred))

    mlflow.sklearn.log_model(model, "model")

if __name__ == "__main__":
    main()
```

### 5.4 Submit Training Job

**File: `deploymentcode/scripts/scenario1/train_job.py`**

```python
"""Submit a training job for facade classification."""
from azure.ai.ml import command, Input
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client

ml_client = get_ml_client()

job = command(
    code="./",  # current directory contains train.py
    command="python train.py --data-path ${{inputs.data}} --n-estimators 200",
    inputs={
        "data": Input(
            type=AssetTypes.URI_FOLDER,
            path="azureml:facade-images:1",
        ),
    },
    environment="azureml:claudebricks-sklearn:1",
    compute="cpu-cluster",
    experiment_name="scenario1-facade-classification",
    display_name="facade-classification-rf",
    description="Random forest classifier on facade images",
)

returned_job = ml_client.jobs.create_or_update(job)
print(f"Job submitted: {returned_job.name}")
print(f"Studio URL: {returned_job.studio_url}")
```

**CLI equivalent YAML: `deploymentcode/scripts/scenario1/train_job.yml`**
```yaml
$schema: https://azuremlschemas.azureedge.net/latest/commandJob.schema.json

code: ./
command: >-
  python train.py
  --data-path ${{inputs.data}}
  --n-estimators 200
inputs:
  data:
    type: uri_folder
    path: azureml:facade-images:1
environment: azureml:claudebricks-sklearn:1
compute: azureml:cpu-cluster
experiment_name: scenario1-facade-classification
display_name: facade-classification-rf
description: Random forest classifier on facade images
```

```bash
az ml job create -f scenario1/train_job.yml \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $ML_WORKSPACE
```

### 5.5 Register Model

**File: `deploymentcode/scripts/scenario1/register_model.py`**

```python
"""Register the best model from the training run."""
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client

ml_client = get_ml_client()

# Replace <JOB_NAME> with the job name from train_job.py output
JOB_NAME = "<JOB_NAME>"  # e.g., "brave_hat_abc123"

model = Model(
    path=f"azureml://jobs/{JOB_NAME}/outputs/artifacts/paths/model/",
    name="facade-classifier",
    description="Facade style classifier (RF on image pixels)",
    type=AssetTypes.MLFLOW_MODEL,
)

registered = ml_client.models.create_or_update(model)
print(f"Registered: {registered.name} version {registered.version}")
```

**CLI equivalent:**
```bash
az ml model create \
  --name facade-classifier \
  --version 1 \
  --path azureml://jobs/<JOB_NAME>/outputs/artifacts/paths/model/ \
  --type mlflow_model \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $ML_WORKSPACE
```

### 5.6 Deploy to Managed Online Endpoint

**File: `deploymentcode/scripts/scenario1/deploy_endpoint.py`**

```python
"""Create a managed online endpoint and deploy the facade classifier."""
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Model,
    Environment,
    CodeConfiguration,
)
from common.ml_client import get_ml_client

ml_client = get_ml_client()

# 1. Create endpoint
endpoint = ManagedOnlineEndpoint(
    name="facade-classifier-endpoint",
    description="Real-time facade style classification",
    auth_mode="key",
)
ml_client.online_endpoints.begin_create_or_update(endpoint).result()
print("Endpoint created.")

# 2. Create deployment
deployment = ManagedOnlineDeployment(
    name="blue",
    endpoint_name="facade-classifier-endpoint",
    model="azureml:facade-classifier:1",
    instance_type="Standard_DS3_v2",
    instance_count=1,
)
ml_client.online_deployments.begin_create_or_update(deployment).result()

# 3. Route 100% traffic to the deployment
endpoint.traffic = {"blue": 100}
ml_client.online_endpoints.begin_create_or_update(endpoint).result()
print("Deployment complete. 100% traffic routed to 'blue'.")
```

**CLI equivalent YAMLs:**

`endpoint.yml`:
```yaml
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineEndpoint.schema.json
name: facade-classifier-endpoint
auth_mode: key
```

`deployment.yml`:
```yaml
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineDeployment.schema.json
name: blue
endpoint_name: facade-classifier-endpoint
model: azureml:facade-classifier:1
instance_type: Standard_DS3_v2
instance_count: 1
```

```bash
az ml online-endpoint create -f scenario1/endpoint.yml
az ml online-deployment create -f scenario1/deployment.yml --all-traffic
```

### 5.7 Test the Endpoint

```bash
az ml online-endpoint invoke \
  --name facade-classifier-endpoint \
  --request-file scenario1/sample_request.json
```

---

## 6. Phase 4: Scenario 2 -- Structural Validation (Anomaly Detection)

**Goal:** Flag unsafe or unusual LEGO structures in .ldr files using anomaly
detection on engineered numeric features.

### 6.1 Feature Engineering

Extract these four features from each .ldr file (per Slide 13 of the deck):

| Feature | Description | How to Compute |
|---------|-------------|----------------|
| Overhang Ratio | Unsupported overhangs / footprint | Parse part positions, find parts with no support below |
| Collision Count | Overlapping bricks | Check for duplicate/overlapping coordinates |
| Height-to-Base Ratio | Height / base width | Max Y range / X*Z footprint |
| Layer Density | Bricks per layer distribution | Count parts per Y-coordinate, compute variance |

**File: `deploymentcode/scripts/scenario2/feature_engineering.py`**

This script parses .ldr files and outputs a CSV with one row per file and
the four numeric features plus a `label` column (pass/fail).

### 6.2 Data Preparation

```python
"""Upload engineered features and create data asset."""
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client

ml_client = get_ml_client()

data_asset = Data(
    name="ldr-validation-features",
    version="1",
    description="Engineered features from .ldr files for anomaly detection",
    path="../../data/scenario2/features.csv",
    type=AssetTypes.URI_FILE,
)
ml_client.data.create_or_update(data_asset)
```

### 6.3 Training Script

**File: `deploymentcode/scripts/scenario2/train.py`**

```python
"""Anomaly detection / classification training for .ldr validation."""
import argparse
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--model-type", type=str, default="isolation_forest",
                        choices=["isolation_forest", "random_forest"])
    args = parser.parse_args()

    mlflow.autolog()

    df = pd.read_csv(args.data_path)
    feature_cols = ["overhang_ratio", "collision_count",
                    "height_to_base_ratio", "layer_density"]
    X = df[feature_cols]

    if args.model_type == "isolation_forest":
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X)
        preds = model.predict(X)
        # IsolationForest: -1 = anomaly, 1 = normal
        mlflow.log_param("contamination", 0.1)
    else:
        y = df["label"]  # 0=pass, 1=fail
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        f1 = f1_score(y_test, preds)
        mlflow.log_metric("test_f1", f1)
        print(classification_report(y_test, preds))

    mlflow.sklearn.log_model(model, "model")

if __name__ == "__main__":
    main()
```

### 6.4 Submit Job, Register, Deploy

Follow the same pattern as Scenario 1:

1. **Submit job** using `command()` with `--data-path` pointing to
   `azureml:ldr-validation-features:1` and `compute="cpu-cluster"`
2. **Register model** as `ldr-validator` (MLflow model type)
3. **Deploy endpoint** named `ldr-validator-endpoint` with a `score.py` that:
   - Accepts JSON with the four feature values
   - Returns `{"prediction": "pass"}` or `{"prediction": "fail"}`

The endpoint is called by the Validator agent in the Claude.Bricks pipeline.

**Scoring script: `deploymentcode/scripts/scenario2/score.py`**
```python
"""Scoring script for the .ldr validator endpoint."""
import json
import mlflow
import numpy as np
import os

def init():
    global model
    model_path = os.path.join(os.environ["AZUREML_MODEL_DIR"], "model")
    model = mlflow.sklearn.load_model(model_path)

def run(raw_data):
    data = json.loads(raw_data)
    features = np.array([[
        data["overhang_ratio"],
        data["collision_count"],
        data["height_to_base_ratio"],
        data["layer_density"],
    ]])
    prediction = model.predict(features)
    result = "fail" if prediction[0] == -1 or prediction[0] == 1 else "pass"
    return json.dumps({"prediction": result})
```

---

## 7. Phase 5: Scenario 3 -- Pattern Extraction (Clustering)

**Goal:** Discover common building patterns across hundreds of .ldr reference
models using part-usage statistics, embeddings, and clustering.

### 7.1 Data Pipeline

1. **Extract part-usage stats** from each .ldr file:
   - Part counts by category (bricks, plates, slopes, windows, doors)
   - Dimensions (height, width, depth in studs)
   - Roof type indicators
   - Window-to-wall ratio

2. **Create embeddings** from the stat vectors (optional: use a pretrained
   model or just standardize the features)

3. **Run clustering** (KMeans, HDBSCAN, or similar)

### 7.2 Pipeline Job (Multi-Step)

Scenario 3 is best implemented as a pipeline with multiple steps:

**File: `deploymentcode/scripts/scenario3/pipeline_job.py`**

```python
"""Multi-step pipeline: extract features -> cluster -> evaluate."""
from azure.ai.ml import command, Input, Output, dsl
from azure.ai.ml.constants import AssetTypes
from common.ml_client import get_ml_client

ml_client = get_ml_client()

# Step 1: Feature extraction
extract_step = command(
    name="extract_features",
    code="./",
    command="python extract_stats.py --input-path ${{inputs.ldr_data}} --output-path ${{outputs.features}}",
    inputs={"ldr_data": Input(type=AssetTypes.URI_FOLDER, path="azureml:reference-models:1")},
    outputs={"features": Output(type=AssetTypes.URI_FILE)},
    environment="azureml:claudebricks-clustering:1",
    compute="cpu-cluster",
)

# Step 2: Clustering
cluster_step = command(
    name="run_clustering",
    code="./",
    command="python train.py --data-path ${{inputs.features}} --n-clusters 5",
    inputs={"features": Input(type=AssetTypes.URI_FILE)},
    environment="azureml:claudebricks-clustering:1",
    compute="cpu-cluster",
)

# Use @dsl.pipeline to chain them
@dsl.pipeline(
    compute="cpu-cluster",
    experiment_name="scenario3-pattern-extraction",
    description="Extract features from .ldr files, then cluster",
)
def pattern_extraction_pipeline(ldr_data):
    step1 = extract_step(ldr_data=ldr_data)
    step2 = cluster_step(features=step1.outputs.features)
    return {"cluster_model": step2.outputs}

pipeline = pattern_extraction_pipeline(
    ldr_data=Input(type=AssetTypes.URI_FOLDER, path="azureml:reference-models:1")
)

returned_job = ml_client.jobs.create_or_update(pipeline)
print(f"Pipeline submitted: {returned_job.name}")
print(f"Studio URL: {returned_job.studio_url}")
```

**CLI equivalent:** Use a pipeline YAML with steps referencing component YAMLs.
See: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-component-pipelines-cli

### 7.3 Register and Consume

Register the clustering model. This scenario does NOT require a real-time endpoint
(it is a batch/offline analysis tool). However, you CAN optionally deploy one
if the Spec Generator (Scenario 4) wants to query cluster labels at inference time.

---

## 8. Phase 6: Scenario 4 -- Fine-Tuned LLM Spec Generator

**Goal:** Generate detailed, consistent building specs from prompts and reference
patterns. Uses RAG with Azure AI Search and optionally fine-tuning on Azure OpenAI.

This is the most complex scenario and has the most manual steps.

### 8.1 Azure Resources Used

| Resource | Created By | Notes |
|----------|-----------|-------|
| Azure OpenAI (gpt-4o-mini) | Terraform | Base model for generation |
| Azure AI Search (basic) | Terraform | Vector store for RAG |
| Blob container `training-data` | Terraform | Fine-tuning JSONL data |
| Datastore `training_data` | Bootstrap | Points to blob |
| Prompt flow | Manual / SDK | Chains retrieval + generation |

### 8.2 RAG: Azure AI Search Index Setup

**File: `deploymentcode/scripts/scenario4/rag_index_setup.py`**

This script:
1. Creates a search index with vector fields
2. Generates embeddings from building spec documents
3. Uploads documents + embeddings to the index

```python
"""
Set up Azure AI Search index for RAG.
Requires: SEARCH_ENDPOINT and SEARCH_NAME env vars from config.sh.

References:
  https://learn.microsoft.com/en-us/azure/search/search-get-started-vector
  https://learn.microsoft.com/en-us/azure/search/search-how-to-create-search-index
"""
import os
import json
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField as VectorField,
)

SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"]
INDEX_NAME = "building-specs"

credential = DefaultAzureCredential()

# 1. Define index schema
index = SearchIndex(
    name=INDEX_NAME,
    fields=[
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="style", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="my-vector-profile",
        ),
    ],
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")],
        profiles=[
            VectorSearchProfile(
                name="my-vector-profile",
                algorithm_configuration_name="my-hnsw",
            )
        ],
    ),
)

# 2. Create the index
index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)
index_client.create_or_update_index(index)
print(f"Index '{INDEX_NAME}' created/updated.")

# 3. Upload documents (building spec descriptions)
# In production, generate embeddings via Azure OpenAI embeddings endpoint
# For now, use placeholder vectors
search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential
)

# Load spec documents from data folder
with open("../../data/scenario4/building_specs.json") as f:
    docs = json.load(f)

# Upload
result = search_client.upload_documents(documents=docs)
print(f"Uploaded {len(result)} documents to index.")
```

**MANUAL PORTAL ALTERNATIVE:**
If you prefer to create the index via the Azure Portal:
1. Go to your AI Search resource > **Indexes** > **Add index**
2. Add fields: id (string, key), title (string, searchable), content (string,
   searchable), style (string, filterable), content_vector (Collection(Single),
   1536 dimensions)
3. Under Vector Search, add an HNSW algorithm config and a profile

### 8.3 Prepare Fine-Tuning Data

**File: `deploymentcode/scripts/scenario4/prepare_training_data.py`**

Fine-tuning data must be in JSONL format with `messages` arrays:

```jsonl
{"messages": [{"role": "system", "content": "You generate LEGO building specs."}, {"role": "user", "content": "3-story historic European townhouse"}, {"role": "assistant", "content": "{\"height\": 3, \"style\": \"historic\", \"facade\": \"masonry\", \"roof\": \"peaked\", ...}"}]}
```

The script converts your spec examples into this format and saves to
`data/scenario4/training_data.jsonl`.

### 8.4 Fine-Tuning Job

**File: `deploymentcode/scripts/scenario4/fine_tune_job.py`**

```python
"""
Submit a fine-tuning job to Azure OpenAI.

References:
  https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/fine-tuning

IMPORTANT: Fine-tuning availability is region- and model-specific.
Supported regions (as of 2025): East US, East US 2, North Central US,
Sweden Central, Switzerland West.
If fine-tuning is unavailable, fall back to prompt engineering + RAG.
"""
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_ENDPOINT"],
    api_version="2024-08-01-preview",
    # Uses DefaultAzureCredential via azure-identity
    # Or set AZURE_OPENAI_API_KEY env var
)

# 1. Upload training file
with open("../../data/scenario4/training_data.jsonl", "rb") as f:
    training_file = client.files.create(file=f, purpose="fine-tune")
print(f"Uploaded training file: {training_file.id}")

# 2. Optional: upload validation file
# validation_file = client.files.create(file=open("validation.jsonl","rb"), purpose="fine-tune")

# 3. Submit fine-tuning job
ft_job = client.fine_tuning.jobs.create(
    training_file=training_file.id,
    model="gpt-4o-mini",  # base model to fine-tune
    # hyperparameters={"n_epochs": 3},  # optional
)
print(f"Fine-tuning job submitted: {ft_job.id}")
print(f"Status: {ft_job.status}")

# 4. Monitor (poll or check in Azure AI Studio)
# The job can take minutes to hours depending on data size.
# Check status:
#   status = client.fine_tuning.jobs.retrieve(ft_job.id)
#   print(status.status)  # "running", "succeeded", "failed"
```

**MANUAL PORTAL ALTERNATIVE (Azure AI Studio):**
1. Go to Azure AI Studio > your OpenAI resource > **Fine-tuning**
2. Click **Create fine-tuning job**
3. Select base model: gpt-4o-mini
4. Upload training JSONL file
5. Configure hyperparameters (epochs, batch size, learning rate multiplier)
6. Submit and monitor

**Cost warning:** Fine-tuned model hosting costs ~$1.70/hour. Delete the
deployment when not actively using it.

### 8.5 Deploy Fine-Tuned Model

After the fine-tuning job succeeds, deploy the resulting model:

```python
"""Deploy the fine-tuned model."""
# The fine-tuned model ID is in the job result:
#   ft_job = client.fine_tuning.jobs.retrieve("<JOB_ID>")
#   model_id = ft_job.fine_tuned_model  # e.g., "ft:gpt-4o-mini:...:custom"

# Deploy via Azure CLI:
# az cognitiveservices account deployment create \
#   --name <openai-resource-name> \
#   --resource-group $RESOURCE_GROUP \
#   --deployment-name ft-spec-generator \
#   --model-name <fine_tuned_model_id> \
#   --model-version 1 \
#   --model-format OpenAI \
#   --sku-capacity 10 \
#   --sku-name Standard
```

**MANUAL PORTAL ALTERNATIVE:**
1. Go to Azure AI Studio > **Deployments** > **Deploy model**
2. Select your fine-tuned model from the list
3. Set deployment name, TPM capacity
4. Deploy

### 8.6 Prompt Flow (RAG Chain)

Prompt flow chains retrieval (AI Search) with generation (OpenAI) in a single
callable flow.

**File: `deploymentcode/scripts/scenario4/promptflow/flow.dag.yaml`**

```yaml
$schema: https://azuremlschemas.azureedge.net/promptflow/latest/Flow.schema.json

inputs:
  user_prompt:
    type: string
    default: "3-story historic European townhouse with a shop on the ground floor"

outputs:
  building_spec:
    type: string
    reference: ${generate.output}

nodes:
  - name: retrieve
    type: python
    source:
      type: code
      path: retrieve.py
    inputs:
      query: ${inputs.user_prompt}
      search_endpoint: "${env:SEARCH_ENDPOINT}"
      index_name: "building-specs"
      top_k: 3

  - name: generate
    type: python
    source:
      type: code
      path: generate.py
    inputs:
      user_prompt: ${inputs.user_prompt}
      context: ${retrieve.output}
      openai_endpoint: "${env:OPENAI_ENDPOINT}"
      deployment_name: "gpt-4o-mini"  # or "ft-spec-generator" for fine-tuned

environment:
  python_requirements_txt: requirements.txt
```

**MANUAL PORTAL STEPS for Prompt Flow:**
1. Go to Azure ML Studio > **Prompt flow** > **Create**
2. Choose "Standard flow" template
3. Add a Python node for retrieval (queries AI Search)
4. Add a Python node for generation (calls OpenAI with retrieved context)
5. Connect nodes: retrieval output -> generation input
6. Test in the flow editor with sample prompts
7. Create variants for A/B testing different system prompts
8. Deploy the flow to a managed online endpoint

**References:**
- https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/overview-what-is-prompt-flow
- https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-deploy-to-code

---

## 9. Teardown

To avoid ongoing charges, tear down resources when done.

### 9.1 Delete Endpoints First (highest cost)

```bash
# Delete managed online endpoints (they charge per-hour for compute)
az ml online-endpoint delete --name facade-classifier-endpoint --yes
az ml online-endpoint delete --name ldr-validator-endpoint --yes

# Delete fine-tuned model deployment (charges ~$1.70/hr)
az cognitiveservices account deployment delete \
  --name <openai-resource-name> \
  --resource-group $RESOURCE_GROUP \
  --deployment-name ft-spec-generator
```

### 9.2 Stop Compute Instance

```bash
az ml compute stop --name ci-dev-dev --resource-group $RESOURCE_GROUP --workspace-name $ML_WORKSPACE
```

### 9.3 Full Terraform Destroy

```bash
cd deploymentcode/terraform
terraform destroy
```

This deletes ALL resources including the resource group. Use with caution.

---

## 10. Cost Summary

### Fixed Monthly Costs (always-on resources)

| Resource | Config | Est. Monthly |
|----------|--------|-------------|
| Storage Account | Standard LRS, ~50 GB | ~$1 |
| Key Vault | Standard, low usage | ~$0.10 |
| Container Registry | Basic SKU | ~$5 |
| Log Analytics | ~5 GB/month ingestion | ~$12 |
| AI Search | Basic SKU | ~$75 |
| ML Workspace | Basic SKU | $0 |
| **Subtotal** | | **~$93/month** |

### Variable Costs (usage-based)

| Resource | Config | Est. Cost |
|----------|--------|-----------|
| Compute Instance | DS3_v2, 40 hrs/month | ~$12/month |
| CPU Cluster | DS3_v2, Low Priority, 20 hrs | ~$1.20/month |
| GPU Cluster | NC4as_T4_v3, Low Priority, 10 hrs | ~$1.10/month |
| Online Endpoints | DS3_v2, 2 endpoints, 100 hrs each | ~$58/month |
| Azure OpenAI | ~500K tokens/month | ~$0.25/month |
| Fine-tuned hosting | $1.70/hr, used 10 hrs/month | ~$17/month |
| **Subtotal** | | **~$90/month** |

### Total Estimated: ~$183/month for full lab usage

**Cost reduction tips:**
- Set `deploy_ai_search = false` if not doing Scenario 4 (saves ~$75/month)
- Delete endpoints immediately after testing (saves ~$58/month)
- Use free tier AI Search if you have < 3 indexes and < 50 MB (saves ~$75/month)
- Stop compute instances when not in use
- Delete fine-tuned model deployments when not testing

---

## Appendix A: Terraform Resource Reference

| Terraform Resource Type | Azure Resource | Docs |
|------------------------|---------------|------|
| `azurerm_resource_group` | Resource Group | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/resource_group) |
| `azurerm_storage_account` | Storage Account | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/storage_account) |
| `azurerm_storage_container` | Blob Container | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/storage_container) |
| `azurerm_key_vault` | Key Vault | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/key_vault) |
| `azurerm_container_registry` | Container Registry | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_registry) |
| `azurerm_log_analytics_workspace` | Log Analytics | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/log_analytics_workspace) |
| `azurerm_application_insights` | Application Insights | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/application_insights) |
| `azurerm_machine_learning_workspace` | ML Workspace | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/machine_learning_workspace) |
| `azurerm_machine_learning_compute_instance` | Compute Instance | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/machine_learning_compute_instance) |
| `azurerm_machine_learning_compute_cluster` | Compute Cluster | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/machine_learning_compute_cluster) |
| `azurerm_cognitive_account` | Cognitive Services | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_account) |
| `azurerm_cognitive_deployment` | Model Deployment | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_deployment) |
| `azurerm_search_service` | AI Search | [Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/search_service) |

## Appendix B: Azure ML SDK v2 Reference

| Operation | SDK Class/Method | CLI Equivalent |
|-----------|-----------------|----------------|
| Connect to workspace | `MLClient(DefaultAzureCredential(), ...)` | `az configure --defaults workspace=...` |
| Create datastore | `ml_client.datastores.create_or_update(AzureBlobDatastore(...))` | `az ml datastore create -f ds.yml` |
| Create data asset | `ml_client.data.create_or_update(Data(...))` | `az ml data create -f data.yml` |
| Register environment | `ml_client.environments.create_or_update(Environment(...))` | `az ml environment create -f env.yml` |
| Submit command job | `ml_client.jobs.create_or_update(command(...))` | `az ml job create -f job.yml` |
| Submit pipeline | `ml_client.jobs.create_or_update(pipeline(...))` | `az ml job create -f pipeline.yml` |
| Register model | `ml_client.models.create_or_update(Model(...))` | `az ml model create -n name -p path` |
| Create endpoint | `ml_client.online_endpoints.begin_create_or_update(ManagedOnlineEndpoint(...))` | `az ml online-endpoint create -f ep.yml` |
| Create deployment | `ml_client.online_deployments.begin_create_or_update(ManagedOnlineDeployment(...))` | `az ml online-deployment create -f dep.yml` |
| Log with MLflow | `mlflow.autolog()` / `mlflow.log_metric()` | Automatic in SDK jobs |

**Required pip packages:**
```
azure-ai-ml          # ML workspace SDK
azure-identity       # Authentication
azure-search-documents  # AI Search SDK
openai               # Azure OpenAI SDK
mlflow               # Experiment tracking
```

## Appendix C: Microsoft Learn Documentation Links

### Terraform & Infrastructure
- [Manage Azure ML workspace with Terraform](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-workspace-terraform)
- [Azure ML compute clusters](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-attach-compute-cluster)
- [GPU VM sizes](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes-gpu)

### Data & Environments
- [Create data assets](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-data-assets)
- [Manage environments v2](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-environments-v2)
- [Access data during training](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-read-write-data-v2)

### Training & Pipelines
- [Train models with SDK v2](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-train-model)
- [Create ML pipelines (CLI)](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-create-component-pipelines-cli)
- [AutoML for image models](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-auto-train-image-models-v2)
- [MLflow tracking in Azure ML](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models)

### Deployment
- [Deploy to managed online endpoints](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-online-endpoints)
- [Online endpoint concepts](https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online)
- [Blue-green deployment](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints)

### Azure OpenAI & RAG
- [Azure OpenAI fine-tuning](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/fine-tuning)
- [Azure AI Search vector search quickstart](https://learn.microsoft.com/en-us/azure/search/search-get-started-vector)
- [Create a search index](https://learn.microsoft.com/en-us/azure/search/search-how-to-create-search-index)

### Prompt Flow
- [Prompt flow overview](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/overview-what-is-prompt-flow)
- [Deploy prompt flow to endpoint](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/how-to-deploy-to-code)

### Cost & Quotas
- [Azure ML pricing](https://azure.microsoft.com/en-us/pricing/details/machine-learning/)
- [Manage quotas](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-quotas)
- [Azure OpenAI pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Azure AI Search pricing](https://azure.microsoft.com/en-us/pricing/details/search/)