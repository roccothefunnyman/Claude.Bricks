# Claude.Bricks Bicep Development Plan

## Overview

This document is the detailed implementation plan for building all Bicep infrastructure-as-code for Claude.Bricks. It covers every module, parameter, output, dependency, and deployment wrapper needed to provision the complete Azure ML + Foundry environment using Bicep and Azure CLI.

This replaces Terraform as the **documented primary IaC path** for AI-300 alignment. The existing Terraform in `deploymentcode/terraform/` and `tf/` remains as an alternate implementation.

---

## Current Terraform Inventory (What We Are Replicating)

The following resources are currently provisioned by Terraform and must be replicated in Bicep:

| Terraform File | Resource(s) | Azure Resource Type |
|---------------|-------------|-------------------|
| `resource_group.tf` | Resource group | `Microsoft.Resources/resourceGroups` |
| `storage.tf` | Storage account + 4 blob containers | `Microsoft.Storage/storageAccounts` |
| `keyvault.tf` | Key Vault | `Microsoft.KeyVault/vaults` |
| `acr.tf` | Container Registry | `Microsoft.ContainerRegistry/registries` |
| `monitoring.tf` | Log Analytics workspace | `Microsoft.OperationalInsights/workspaces` |
| `monitoring.tf` | Application Insights | `Microsoft.Insights/components` |
| `ml_workspace.tf` | Azure ML workspace (Basic SKU) | `Microsoft.MachineLearningServices/workspaces` |
| `ml_compute.tf` | Compute instance | `Microsoft.MachineLearningServices/workspaces/computes` |
| `ml_compute.tf` | CPU compute cluster | `Microsoft.MachineLearningServices/workspaces/computes` |
| `ml_compute.tf` | GPU compute cluster | `Microsoft.MachineLearningServices/workspaces/computes` |
| `cognitive_services.tf` | Azure OpenAI (conditional) | `Microsoft.CognitiveServices/accounts` |
| `cognitive_services.tf` | Custom Vision Training (conditional) | `Microsoft.CognitiveServices/accounts` |
| `cognitive_services.tf` | Custom Vision Prediction (conditional) | `Microsoft.CognitiveServices/accounts` |
| `search.tf` | Azure AI Search (conditional) | `Microsoft.Search/searchServices` |

### New Resources (Not in Terraform, Added for AI-300)

| Resource | Azure Resource Type | Purpose |
|----------|-------------------|---------|
| Foundry Hub | `Microsoft.MachineLearningServices/workspaces` (kind: Hub) | GenAIOps infrastructure |
| Foundry Project | `Microsoft.MachineLearningServices/workspaces` (kind: Project) | Scenario 4 GenAI operations |
| AML Registry | `Microsoft.MachineLearningServices/registries` | Cross-workspace asset sharing |
| Private Endpoints (test/prod) | `Microsoft.Network/privateEndpoints` | Network security |
| Private DNS Zones (test/prod) | `Microsoft.Network/privateDnsZones` | Private endpoint DNS resolution |
| VNet (test/prod) | `Microsoft.Network/virtualNetworks` | Network isolation |
| Role Assignments | `Microsoft.Authorization/roleAssignments` | RBAC for managed identities |

---

## Directory Structure

```
deploymentcode/bicep/
  |-- main.bicep                          -- Orchestrator: deploys all modules
  |-- bicepconfig.json                    -- Bicep linter and experimental feature config
  |
  |-- modules/
  |   |-- storage.bicep                   -- Storage account + blob containers
  |   |-- keyvault.bicep                  -- Key Vault
  |   |-- acr.bicep                       -- Azure Container Registry
  |   |-- log-analytics.bicep             -- Log Analytics workspace
  |   |-- app-insights.bicep              -- Application Insights
  |   |-- aml-workspace.bicep             -- Azure ML workspace
  |   |-- aml-compute.bicep               -- Compute targets (instance + clusters)
  |   |-- cognitive-services.bicep         -- Azure OpenAI + Custom Vision
  |   |-- search.bicep                    -- Azure AI Search
  |   |-- foundry-hub.bicep               -- AI Foundry hub
  |   |-- foundry-project.bicep           -- AI Foundry project
  |   |-- aml-registry.bicep              -- AML shared registry
  |   |-- private-endpoint.bicep          -- Generic private endpoint module
  |   |-- vnet.bicep                      -- Virtual network + subnets
  |   |-- rbac.bicep                      -- Role assignments
  |
  |-- parameters/
  |   |-- dev.bicepparam                  -- Dev environment parameters
  |   |-- test.bicepparam                 -- Test environment parameters
  |
  |-- scripts/
  |   |-- deploy.sh                       -- Bash deployment wrapper
  |   |-- deploy.ps1                      -- PowerShell deployment wrapper
  |   |-- whatif.sh                        -- What-if preview
  |   |-- teardown.sh                     -- Resource group deletion
  |   |-- validate.sh                     -- Template validation only
```

---

## Module Specifications

### 1. `main.bicep` -- Orchestrator

**Purpose**: Top-level template that deploys all modules in dependency order.

**Target scope**: `resourceGroup` (resource group created separately by wrapper script or subscription-level deployment)

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `location` | string | Azure region | `resourceGroup().location` |
| `projectName` | string | Base name for all resources | `'claudebricks'` |
| `environment` | string | Environment identifier | `'dev'` |
| `tags` | object | Common tags applied to all resources | `{ project: 'claude-bricks', environment: environment, managedBy: 'bicep' }` |
| `deployOpenAI` | bool | Deploy Azure OpenAI resource | `true` |
| `deployCustomVision` | bool | Deploy Custom Vision resources | `false` |
| `deployAISearch` | bool | Deploy AI Search resource | `true` |
| `deployFoundry` | bool | Deploy Foundry hub and project | `true` |
| `deployRegistry` | bool | Deploy shared AML registry | `false` |
| `deployPrivateNetworking` | bool | Deploy VNet and private endpoints | `false` |
| `computeInstanceSize` | string | Compute instance VM size | `'Standard_DS2_v2'` |
| `cpuClusterMaxNodes` | int | CPU cluster max nodes | `2` |
| `gpuClusterMaxNodes` | int | GPU cluster max nodes | `1` |
| `cpuClusterVmSize` | string | CPU cluster VM size | `'Standard_DS3_v2'` |
| `gpuClusterVmSize` | string | GPU cluster VM size | `'Standard_NC4as_T4_v3'` |
| `openAIModelName` | string | OpenAI model deployment name | `'gpt-4o'` |
| `openAIModelVersion` | string | OpenAI model version | `'2024-08-06'` |
| `embeddingModelName` | string | Embedding model deployment name | `'text-embedding-3-small'` |
| `searchSku` | string | AI Search SKU | `'basic'` |
| `amlSku` | string | AML workspace SKU | `'Basic'` |

#### Resource Naming Convention

All resources follow the pattern: `{abbreviation}-{projectName}-{environment}`

| Resource | Naming Pattern | Example (dev) |
|----------|---------------|---------------|
| Storage account | `st{projectName}{env}` (no hyphens, max 24 chars) | `stclaudebricksdev` |
| Key Vault | `kv-{projectName}-{env}` | `kv-claudebricks-dev` |
| ACR | `acr{projectName}{env}` (no hyphens) | `acrclaudebricksdev` |
| Log Analytics | `law-{projectName}-{env}` | `law-claudebricks-dev` |
| App Insights | `appi-{projectName}-{env}` | `appi-claudebricks-dev` |
| AML Workspace | `mlw-{projectName}-{env}` | `mlw-claudebricks-dev` |
| OpenAI | `oai-{projectName}-{env}` | `oai-claudebricks-dev` |
| AI Search | `srch-{projectName}-{env}` | `srch-claudebricks-dev` |
| Foundry Hub | `hub-{projectName}-{env}` | `hub-claudebricks-dev` |
| Foundry Project | `proj-{projectName}-{env}` | `proj-claudebricks-dev` |
| AML Registry | `reg-{projectName}` (shared, no env suffix) | `reg-claudebricks` |
| VNet | `vnet-{projectName}-{env}` | `vnet-claudebricks-dev` |

#### Module Deployment Order (dependency chain)

```
1. storage.bicep          -- no dependencies
2. keyvault.bicep         -- no dependencies
3. acr.bicep              -- no dependencies
4. log-analytics.bicep    -- no dependencies
   |
   v
5. app-insights.bicep     -- depends on: log-analytics
   |
   v
6. aml-workspace.bicep    -- depends on: storage, keyvault, acr, app-insights
   |
   v
7. aml-compute.bicep      -- depends on: aml-workspace
8. cognitive-services.bicep -- no dependencies (conditional)
9. search.bicep            -- no dependencies (conditional)
   |
   v
10. foundry-hub.bicep     -- depends on: storage, keyvault, acr, app-insights (conditional)
    |
    v
11. foundry-project.bicep -- depends on: foundry-hub (conditional)
12. aml-registry.bicep    -- depends on: storage, acr (conditional)
13. rbac.bicep             -- depends on: all resources with managed identities
14. vnet.bicep + private-endpoint.bicep -- depends on: all resources (conditional)
```

Bicep handles dependency resolution automatically via `dependsOn` inferred from resource references. The order above is logical, not necessarily explicit.

#### Outputs

| Output | Type | Source |
|--------|------|--------|
| `workspaceName` | string | AML workspace name |
| `workspaceId` | string | AML workspace resource ID |
| `storageAccountName` | string | Storage account name |
| `storageAccountId` | string | Storage account resource ID |
| `keyVaultName` | string | Key Vault name |
| `keyVaultUri` | string | Key Vault URI |
| `acrName` | string | ACR name |
| `acrLoginServer` | string | ACR login server URL |
| `appInsightsName` | string | App Insights name |
| `appInsightsConnectionString` | string | App Insights connection string |
| `logAnalyticsWorkspaceId` | string | Log Analytics workspace ID |
| `openAIEndpoint` | string | OpenAI endpoint (conditional) |
| `searchEndpoint` | string | AI Search endpoint (conditional) |
| `foundryHubName` | string | Foundry hub name (conditional) |
| `foundryProjectName` | string | Foundry project name (conditional) |
| `registryName` | string | AML registry name (conditional) |

#### main.bicep Skeleton

```bicep
targetScope = 'resourceGroup'

// === PARAMETERS ===
param location string = resourceGroup().location
param projectName string = 'claudebricks'
param environment string = 'dev'
param tags object = {
  project: 'claude-bricks'
  environment: environment
  managedBy: 'bicep'
}

// Feature flags
param deployOpenAI bool = true
param deployCustomVision bool = false
param deployAISearch bool = true
param deployFoundry bool = true
param deployRegistry bool = false
param deployPrivateNetworking bool = false

// Compute configuration
param computeInstanceSize string = 'Standard_DS2_v2'
param cpuClusterMaxNodes int = 2
param gpuClusterMaxNodes int = 1
param cpuClusterVmSize string = 'Standard_DS3_v2'
param gpuClusterVmSize string = 'Standard_NC4as_T4_v3'

// Model configuration
param openAIModelName string = 'gpt-4o'
param openAIModelVersion string = '2024-08-06'
param embeddingModelName string = 'text-embedding-3-small'
param searchSku string = 'basic'
param amlSku string = 'Basic'

// === NAMING ===
var baseName = '${projectName}${environment}'
var storageAccountName = 'st${replace(baseName, '-', '')}'
var keyVaultName = 'kv-${projectName}-${environment}'
var acrName = 'acr${replace(baseName, '-', '')}'
var logAnalyticsName = 'law-${projectName}-${environment}'
var appInsightsName = 'appi-${projectName}-${environment}'
var workspaceName = 'mlw-${projectName}-${environment}'
var openAIName = 'oai-${projectName}-${environment}'
var searchName = 'srch-${projectName}-${environment}'
var foundryHubName = 'hub-${projectName}-${environment}'
var foundryProjectName = 'proj-${projectName}-${environment}'
var registryName = 'reg-${projectName}'

// === MODULE DEPLOYMENTS ===
module storage 'modules/storage.bicep' = { ... }
module keyVault 'modules/keyvault.bicep' = { ... }
module acr 'modules/acr.bicep' = { ... }
module logAnalytics 'modules/log-analytics.bicep' = { ... }
module appInsights 'modules/app-insights.bicep' = { ... }
module amlWorkspace 'modules/aml-workspace.bicep' = { ... }
module amlCompute 'modules/aml-compute.bicep' = { ... }
module cognitiveServices 'modules/cognitive-services.bicep' = if (deployOpenAI || deployCustomVision) { ... }
module search 'modules/search.bicep' = if (deployAISearch) { ... }
module foundryHub 'modules/foundry-hub.bicep' = if (deployFoundry) { ... }
module foundryProject 'modules/foundry-project.bicep' = if (deployFoundry) { ... }
module registry 'modules/aml-registry.bicep' = if (deployRegistry) { ... }
module rbac 'modules/rbac.bicep' = { ... }

// === OUTPUTS ===
output workspaceName string = amlWorkspace.outputs.name
output storageAccountName string = storage.outputs.name
// ... etc
```

---

### 2. `modules/storage.bicep` -- Storage Account

**Purpose**: Storage account with blob containers for training data, models, and inference logs.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Storage account name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `sku` | string | Storage SKU (default: `'Standard_LRS'`) |
| `kind` | string | Storage kind (default: `'StorageV2'`) |
| `allowBlobPublicAccess` | bool | Allow public blob access (default: `false`) |
| `containerNames` | array | List of blob container names |

#### Resources

1. **Storage Account**
   - API version: `2023-05-01`
   - SKU: Standard_LRS (dev), Standard_GRS (test/prod)
   - Kind: StorageV2
   - TLS: 1.2 minimum
   - Public blob access: disabled
   - HTTPS only: enabled
   - System-assigned managed identity: enabled

2. **Blob Containers** (loop over `containerNames`)
   - Default containers: `facade-images`, `ldr-files`, `reference-models`, `training-data`, `inference-logs`
   - Public access: none

#### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `name` | string | Storage account name |
| `id` | string | Resource ID |
| `primaryBlobEndpoint` | string | Blob endpoint URL |
| `principalId` | string | Managed identity principal ID |

#### Full Module Code

```bicep
@description('Storage account name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Storage SKU')
param sku string = 'Standard_LRS'

@description('Blob container names')
param containerNames array = [
  'facade-images'
  'ldr-files'
  'reference-models'
  'training-data'
  'inference-logs'
]

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    accessTier: 'Hot'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for containerName in containerNames: {
    parent: blobService
    name: containerName
    properties: {
      publicAccess: 'None'
    }
  }
]

output name string = storageAccount.name
output id string = storageAccount.id
output primaryBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output principalId string = storageAccount.identity.principalId
```

---

### 3. `modules/keyvault.bicep` -- Key Vault

**Purpose**: Secrets management for API keys, connection strings, and credentials.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Key Vault name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `tenantId` | string | Azure AD tenant ID (default: `tenant().tenantId`) |
| `enableRbacAuthorization` | bool | Use RBAC instead of access policies (default: `true`) |
| `enableSoftDelete` | bool | Enable soft delete (default: `true`) |
| `softDeleteRetentionDays` | int | Soft delete retention (default: `90`) |

#### Resources

1. **Key Vault**
   - API version: `2023-07-01`
   - SKU: standard
   - RBAC authorization: enabled (AI-300 best practice over access policies)
   - Soft delete: enabled
   - Purge protection: enabled (test/prod) or disabled (dev for easy cleanup)
   - Network ACLs: allow Azure services

#### Full Module Code

```bicep
@description('Key Vault name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Azure AD tenant ID')
param tenantId string = tenant().tenantId

@description('Enable RBAC authorization (recommended over access policies)')
param enableRbacAuthorization bool = true

@description('Enable purge protection (recommended for test/prod)')
param enablePurgeProtection bool = false

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: enableRbacAuthorization
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: enablePurgeProtection ? true : null
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

output name string = keyVault.name
output id string = keyVault.id
output uri string = keyVault.properties.vaultUri
```

---

### 4. `modules/acr.bicep` -- Azure Container Registry

**Purpose**: Container image registry for training environments and scoring images.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | ACR name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `sku` | string | ACR SKU (default: `'Basic'`) |
| `adminUserEnabled` | bool | Enable admin user (default: `false`) |

#### Full Module Code

```bicep
@description('ACR name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('ACR SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output name string = containerRegistry.name
output id string = containerRegistry.id
output loginServer string = containerRegistry.properties.loginServer
```

---

### 5. `modules/log-analytics.bicep` -- Log Analytics Workspace

**Purpose**: Central log aggregation for monitoring and diagnostics.

#### Full Module Code

```bicep
@description('Log Analytics workspace name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Retention in days')
param retentionInDays int = 30

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
  }
}

output name string = logAnalytics.name
output id string = logAnalytics.id
output customerId string = logAnalytics.properties.customerId
```

---

### 6. `modules/app-insights.bicep` -- Application Insights

**Purpose**: Application telemetry, GenAI observability, endpoint monitoring.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | App Insights name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `logAnalyticsWorkspaceId` | string | Linked Log Analytics workspace resource ID |

#### Full Module Code

```bicep
@description('Application Insights name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Log Analytics workspace resource ID')
param logAnalyticsWorkspaceId string

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output name string = appInsights.name
output id string = appInsights.id
output connectionString string = appInsights.properties.ConnectionString
output instrumentationKey string = appInsights.properties.InstrumentationKey
```

---

### 7. `modules/aml-workspace.bicep` -- Azure ML Workspace

**Purpose**: Core ML workspace for training, experiment tracking, model registry, and endpoints.

This is the most important module. It wires together storage, Key Vault, ACR, and App Insights.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Workspace name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `sku` | string | Workspace SKU (default: `'Basic'`) |
| `storageAccountId` | string | Associated storage account resource ID |
| `keyVaultId` | string | Associated Key Vault resource ID |
| `containerRegistryId` | string | Associated ACR resource ID |
| `applicationInsightsId` | string | Associated App Insights resource ID |
| `publicNetworkAccess` | string | Public network access (default: `'Enabled'`) |
| `description` | string | Workspace description |

#### Full Module Code

```bicep
@description('AML workspace name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Workspace SKU tier')
@allowed(['Basic', 'Standard'])
param sku string = 'Basic'

@description('Storage account resource ID')
param storageAccountId string

@description('Key Vault resource ID')
param keyVaultId string

@description('Container Registry resource ID')
param containerRegistryId string

@description('Application Insights resource ID')
param applicationInsightsId string

@description('Public network access setting')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Workspace description')
param description string = 'Claude.Bricks ML workspace'

resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    friendlyName: name
    description: description
    storageAccount: storageAccountId
    keyVault: keyVaultId
    containerRegistry: containerRegistryId
    applicationInsights: applicationInsightsId
    publicNetworkAccess: publicNetworkAccess
    v1LegacyMode: false
  }
}

output name string = workspace.name
output id string = workspace.id
output principalId string = workspace.identity.principalId
output discoveryUrl string = workspace.properties.discoveryUrl
```

---

### 8. `modules/aml-compute.bicep` -- Compute Targets

**Purpose**: Compute instance for development, CPU and GPU clusters for training.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `workspaceName` | string | Parent AML workspace name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `instanceSize` | string | Compute instance VM size |
| `instanceName` | string | Compute instance name (default: `'dev-instance'`) |
| `cpuClusterName` | string | CPU cluster name (default: `'cpu-cluster'`) |
| `cpuClusterVmSize` | string | CPU cluster VM size |
| `cpuClusterMinNodes` | int | CPU cluster min nodes (default: `0`) |
| `cpuClusterMaxNodes` | int | CPU cluster max nodes |
| `gpuClusterName` | string | GPU cluster name (default: `'gpu-cluster'`) |
| `gpuClusterVmSize` | string | GPU cluster VM size |
| `gpuClusterMinNodes` | int | GPU cluster min nodes (default: `0`) |
| `gpuClusterMaxNodes` | int | GPU cluster max nodes |
| `deployInstance` | bool | Deploy compute instance (default: `true`) |
| `deployGpuCluster` | bool | Deploy GPU cluster (default: `true`) |

#### Full Module Code

```bicep
@description('Parent AML workspace name')
param workspaceName string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

// Compute instance
@description('Deploy compute instance')
param deployInstance bool = true

@description('Compute instance name')
param instanceName string = 'dev-instance'

@description('Compute instance VM size')
param instanceSize string = 'Standard_DS2_v2'

// CPU cluster
@description('CPU cluster name')
param cpuClusterName string = 'cpu-cluster'

@description('CPU cluster VM size')
param cpuClusterVmSize string = 'Standard_DS3_v2'

@description('CPU cluster min nodes')
param cpuClusterMinNodes int = 0

@description('CPU cluster max nodes')
param cpuClusterMaxNodes int = 2

// GPU cluster
@description('Deploy GPU cluster')
param deployGpuCluster bool = true

@description('GPU cluster name')
param gpuClusterName string = 'gpu-cluster'

@description('GPU cluster VM size')
param gpuClusterVmSize string = 'Standard_NC4as_T4_v3'

@description('GPU cluster min nodes')
param gpuClusterMinNodes int = 0

@description('GPU cluster max nodes')
param gpuClusterMaxNodes int = 1

// Reference existing workspace
resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: workspaceName
}

resource computeInstance 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = if (deployInstance) {
  parent: workspace
  name: instanceName
  location: location
  tags: tags
  properties: {
    computeType: 'ComputeInstance'
    properties: {
      vmSize: instanceSize
      idleTimeBeforeShutdown: 'PT30M'
    }
  }
}

resource cpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: workspace
  name: cpuClusterName
  location: location
  tags: tags
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: cpuClusterVmSize
      scaleSettings: {
        minNodeCount: cpuClusterMinNodes
        maxNodeCount: cpuClusterMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT5M'
      }
    }
  }
}

resource gpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = if (deployGpuCluster) {
  parent: workspace
  name: gpuClusterName
  location: location
  tags: tags
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: gpuClusterVmSize
      scaleSettings: {
        minNodeCount: gpuClusterMinNodes
        maxNodeCount: gpuClusterMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT5M'
      }
    }
  }
}

output cpuClusterName string = cpuCluster.name
output gpuClusterName string = deployGpuCluster ? gpuCluster.name : ''
output instanceName string = deployInstance ? computeInstance.name : ''
```

---

### 9. `modules/cognitive-services.bicep` -- Azure OpenAI + Custom Vision

**Purpose**: Foundation model hosting (OpenAI) and optional Custom Vision.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `openAIName` | string | OpenAI account name |
| `location` | string | Azure region |
| `tags` | object | Resource tags |
| `deployOpenAI` | bool | Deploy OpenAI (default: `true`) |
| `deployCustomVision` | bool | Deploy Custom Vision (default: `false`) |
| `openAIModelDeployments` | array | Model deployments |
| `customVisionTrainingName` | string | Custom Vision training name |
| `customVisionPredictionName` | string | Custom Vision prediction name |

#### OpenAI Model Deployments

Default deployments:
1. **GPT-4o** -- primary LLM for Scenario 4
   - Model: `gpt-4o`, version: `2024-08-06`
   - Capacity: 10K TPM (dev), 30K TPM (test)
   - SKU: Standard
2. **text-embedding-3-small** -- embedding model for RAG
   - Model: `text-embedding-3-small`, version: `1`
   - Capacity: 10K TPM
   - SKU: Standard

#### Full Module Code

```bicep
@description('Azure OpenAI account name')
param openAIName string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Deploy Azure OpenAI')
param deployOpenAI bool = true

@description('Deploy Custom Vision')
param deployCustomVision bool = false

@description('Custom Vision training account name')
param customVisionTrainingName string = ''

@description('Custom Vision prediction account name')
param customVisionPredictionName string = ''

@description('OpenAI model deployments')
param openAIModelDeployments array = [
  {
    name: 'gpt-4o'
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
  {
    name: 'text-embedding-3-small'
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
]

resource openAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployOpenAI) {
  name: openAIName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@batchSize(1)
resource openAIDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [
  for deployment in openAIModelDeployments: if (deployOpenAI) {
    parent: openAI
    name: deployment.name
    sku: deployment.sku
    properties: {
      model: deployment.model
    }
  }
]

resource customVisionTraining 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployCustomVision) {
  name: customVisionTrainingName
  location: location
  tags: tags
  kind: 'CustomVision.Training'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customVisionTrainingName
  }
}

resource customVisionPrediction 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployCustomVision) {
  name: customVisionPredictionName
  location: location
  tags: tags
  kind: 'CustomVision.Prediction'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customVisionPredictionName
  }
}

output openAIEndpoint string = deployOpenAI ? openAI.properties.endpoint : ''
output openAIId string = deployOpenAI ? openAI.id : ''
output openAIPrincipalId string = deployOpenAI ? openAI.identity.principalId : ''
```

---

### 10. `modules/search.bicep` -- Azure AI Search

**Purpose**: Vector and hybrid search index for RAG retrieval in Scenario 4.

#### Full Module Code

```bicep
@description('AI Search service name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Search SKU')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

@description('Replica count')
param replicaCount int = 1

@description('Partition count')
param partitionCount int = 1

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: sku == 'free' ? 'disabled' : 'free'
  }
}

output name string = searchService.name
output id string = searchService.id
output endpoint string = 'https://${searchService.name}.search.windows.net'
output principalId string = searchService.identity.principalId
```

---

### 11. `modules/foundry-hub.bicep` -- AI Foundry Hub

**Purpose**: Central hub for AI Foundry, providing shared resources for projects.

#### Design Notes

AI Foundry Hub is an AML workspace of kind `Hub`. It connects to the same supporting resources (storage, Key Vault, ACR) but serves as a parent for Foundry projects.

#### Full Module Code

```bicep
@description('Foundry hub name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Storage account resource ID')
param storageAccountId string

@description('Key Vault resource ID')
param keyVaultId string

@description('Container Registry resource ID')
param containerRegistryId string

@description('Application Insights resource ID')
param applicationInsightsId string

@description('Azure OpenAI resource ID (optional, for connection)')
param openAIResourceId string = ''

@description('AI Search resource ID (optional, for connection)')
param searchResourceId string = ''

resource hub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'Hub'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    friendlyName: name
    description: 'Claude.Bricks AI Foundry Hub'
    storageAccount: storageAccountId
    keyVault: keyVaultId
    containerRegistry: containerRegistryId
    applicationInsights: applicationInsightsId
    publicNetworkAccess: 'Enabled'
    v1LegacyMode: false
  }
}

// Connection to Azure OpenAI (if deployed)
resource openAIConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = if (!empty(openAIResourceId)) {
  parent: hub
  name: 'azure-openai'
  properties: {
    category: 'AzureOpenAI'
    target: openAIResourceId
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: openAIResourceId
    }
  }
}

// Connection to AI Search (if deployed)
resource searchConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = if (!empty(searchResourceId)) {
  parent: hub
  name: 'azure-ai-search'
  properties: {
    category: 'CognitiveSearch'
    target: searchResourceId
    authType: 'AAD'
    metadata: {
      ResourceId: searchResourceId
    }
  }
}

output name string = hub.name
output id string = hub.id
output principalId string = hub.identity.principalId
```

---

### 12. `modules/foundry-project.bicep` -- AI Foundry Project

**Purpose**: Project within the Foundry hub for Scenario 4 GenAI operations.

#### Full Module Code

```bicep
@description('Foundry project name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Parent Foundry hub resource ID')
param hubId string

resource project 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    friendlyName: name
    description: 'Claude.Bricks Scenario 4 - GenAI Spec Generator'
    hubResourceId: hubId
    publicNetworkAccess: 'Enabled'
    v1LegacyMode: false
  }
}

output name string = project.name
output id string = project.id
output principalId string = project.identity.principalId
```

---

### 13. `modules/aml-registry.bicep` -- AML Shared Registry

**Purpose**: Cross-workspace asset sharing for model promotion between dev/test/prod.

#### Full Module Code

```bicep
@description('Registry name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Regions to replicate registry to')
param replicationLocations array = []

var registryRegions = empty(replicationLocations) ? [
  {
    location: location
  }
] : [for loc in replicationLocations: {
  location: loc
}]

resource registry 'Microsoft.MachineLearningServices/registries@2024-04-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    regionDetails: registryRegions
  }
}

output name string = registry.name
output id string = registry.id
output principalId string = registry.identity.principalId
```

---

### 14. `modules/rbac.bicep` -- Role Assignments

**Purpose**: RBAC role assignments for managed identities across all resources.

#### Design

This module takes arrays of role assignments and creates them. It is called after all other modules so that principal IDs are available.

#### Full Module Code

```bicep
@description('Role assignments to create')
param roleAssignments array
// Each item: { principalId, roleDefinitionId, scope, principalType, description }

// Well-known role definition IDs
var builtInRoles = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  reader: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  amlDataScientist: 'f6c7c914-8db3-469d-8ca1-694a8f32e121'
  cognitiveServicesOpenAIUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
}

resource assignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for (assignment, i) in roleAssignments: {
    name: guid(assignment.principalId, assignment.roleDefinitionId, assignment.scope)
    scope: resourceGroup()
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', assignment.roleDefinitionId)
      principalId: assignment.principalId
      principalType: assignment.?principalType ?? 'ServicePrincipal'
    }
  }
]

output assignedRoles int = length(roleAssignments)
```

---

### 15. `modules/vnet.bicep` -- Virtual Network (conditional)

**Purpose**: Network isolation for test/prod environments.

#### Full Module Code

```bicep
@description('VNet name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('VNet address prefix')
param addressPrefix string = '10.0.0.0/16'

@description('Subnet configurations')
param subnets array = [
  {
    name: 'default'
    addressPrefix: '10.0.0.0/24'
  }
  {
    name: 'ml-compute'
    addressPrefix: '10.0.1.0/24'
  }
  {
    name: 'private-endpoints'
    addressPrefix: '10.0.2.0/24'
  }
]

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [addressPrefix]
    }
    subnets: [
      for subnet in subnets: {
        name: subnet.name
        properties: {
          addressPrefix: subnet.addressPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

output name string = vnet.name
output id string = vnet.id
output subnetIds object = reduce(vnet.properties.subnets, {}, (cur, next) => union(cur, { '${next.name}': next.id }))
```

---

### 16. `modules/private-endpoint.bicep` -- Generic Private Endpoint

**Purpose**: Reusable module for creating private endpoints for any Azure resource.

#### Full Module Code

```bicep
@description('Private endpoint name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Target resource ID')
param privateLinkServiceId string

@description('Group ID for the private link (e.g., blob, vault, amlworkspace)')
param groupId string

@description('Subnet ID for the private endpoint')
param subnetId string

@description('Private DNS zone ID for DNS resolution')
param privateDnsZoneId string

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-connection'
        properties: {
          privateLinkServiceId: privateLinkServiceId
          groupIds: [groupId]
        }
      }
    ]
  }
}

resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output name string = privateEndpoint.name
output id string = privateEndpoint.id
output ipAddress string = privateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
```

---

## Parameter Files

### `parameters/dev.bicepparam`

```bicep
using '../main.bicep'

param projectName = 'claudebricks'
param environment = 'dev'
param tags = {
  project: 'claude-bricks'
  environment: 'dev'
  managedBy: 'bicep'
  purpose: 'development'
}

// Feature flags
param deployOpenAI = true
param deployCustomVision = false
param deployAISearch = true
param deployFoundry = true
param deployRegistry = false
param deployPrivateNetworking = false

// Compute (smaller for dev)
param computeInstanceSize = 'Standard_DS2_v2'
param cpuClusterMaxNodes = 2
param gpuClusterMaxNodes = 1
param cpuClusterVmSize = 'Standard_DS3_v2'
param gpuClusterVmSize = 'Standard_NC4as_T4_v3'

// Models
param openAIModelName = 'gpt-4o'
param openAIModelVersion = '2024-08-06'
param embeddingModelName = 'text-embedding-3-small'

// SKUs
param searchSku = 'basic'
param amlSku = 'Basic'
```

### `parameters/test.bicepparam`

```bicep
using '../main.bicep'

param projectName = 'claudebricks'
param environment = 'test'
param tags = {
  project: 'claude-bricks'
  environment: 'test'
  managedBy: 'bicep'
  purpose: 'validation'
}

// Feature flags
param deployOpenAI = true
param deployCustomVision = false
param deployAISearch = true
param deployFoundry = true
param deployRegistry = true           // Shared registry for promotion
param deployPrivateNetworking = true   // Network isolation in test

// Compute (no dev instance, larger clusters)
param computeInstanceSize = 'Standard_DS2_v2'  // Will not deploy (handled in main)
param cpuClusterMaxNodes = 4
param gpuClusterMaxNodes = 0  // No GPU in test unless needed
param cpuClusterVmSize = 'Standard_DS3_v2'
param gpuClusterVmSize = 'Standard_NC4as_T4_v3'

// Models
param openAIModelName = 'gpt-4o'
param openAIModelVersion = '2024-08-06'
param embeddingModelName = 'text-embedding-3-small'

// SKUs
param searchSku = 'basic'
param amlSku = 'Basic'
```

---

## Deployment Wrapper Scripts

### `scripts/deploy.sh` -- Bash Deployment

```bash
#!/bin/bash
set -euo pipefail

# === Configuration ===
ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== Claude.Bricks Infrastructure Deployment ==="
echo "Environment: ${ENVIRONMENT}"
echo "Location:    ${LOCATION}"
echo "RG:          ${RESOURCE_GROUP}"
echo ""

# Verify Azure CLI login
az account show > /dev/null 2>&1 || { echo "ERROR: Not logged in. Run 'az login' first."; exit 1; }

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo "Subscription: ${SUBSCRIPTION}"
echo ""

# Create resource group if it doesn't exist
echo "--- Creating resource group ---"
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --tags project=claude-bricks environment="${ENVIRONMENT}" managedBy=bicep

# Run what-if first
echo ""
echo "--- What-If Preview ---"
az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"

# Prompt for confirmation
echo ""
read -p "Proceed with deployment? (y/N): " CONFIRM
if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
  echo "Deployment cancelled."
  exit 0
fi

# Deploy
echo ""
echo "--- Deploying ---"
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}" \
  --name "deploy-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)" \
  --verbose

echo ""
echo "=== Deployment complete ==="

# Show outputs
echo ""
echo "--- Deployment Outputs ---"
az deployment group show \
  --resource-group "${RESOURCE_GROUP}" \
  --name "$(az deployment group list --resource-group "${RESOURCE_GROUP}" --query '[0].name' -o tsv)" \
  --query properties.outputs \
  -o table
```

### `scripts/deploy.ps1` -- PowerShell Deployment

```powershell
param(
    [Parameter()]
    [ValidateSet('dev', 'test')]
    [string]$Environment = 'dev',

    [Parameter()]
    [string]$Location = 'eastus2'
)

$ErrorActionPreference = 'Stop'

# Configuration
$ProjectName = 'claudebricks'
$ResourceGroup = "rg-$ProjectName-$Environment"
$TemplateFile = Join-Path $PSScriptRoot '..\main.bicep'
$ParamsFile = Join-Path $PSScriptRoot "..\parameters\$Environment.bicepparam"

Write-Host "=== Claude.Bricks Infrastructure Deployment ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment"
Write-Host "Location:    $Location"
Write-Host "RG:          $ResourceGroup"
Write-Host ""

# Verify login
try { az account show | Out-Null } catch {
    Write-Error "Not logged in. Run 'az login' first."
    exit 1
}

$Subscription = az account show --query name -o tsv
Write-Host "Subscription: $Subscription"

# Create resource group
Write-Host "`n--- Creating resource group ---" -ForegroundColor Yellow
az group create `
    --name $ResourceGroup `
    --location $Location `
    --tags project=claude-bricks environment=$Environment managedBy=bicep

# What-if
Write-Host "`n--- What-If Preview ---" -ForegroundColor Yellow
az deployment group what-if `
    --resource-group $ResourceGroup `
    --template-file $TemplateFile `
    --parameters $ParamsFile `
    --parameters location=$Location

# Confirm
$Confirm = Read-Host "`nProceed with deployment? (y/N)"
if ($Confirm -ne 'y') {
    Write-Host "Deployment cancelled."
    exit 0
}

# Deploy
$DeploymentName = "deploy-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "`n--- Deploying ---" -ForegroundColor Yellow
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $TemplateFile `
    --parameters $ParamsFile `
    --parameters location=$Location `
    --name $DeploymentName `
    --verbose

Write-Host "`n=== Deployment complete ===" -ForegroundColor Green
```

### `scripts/whatif.sh` -- What-If Preview Only

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== What-If Preview ==="
echo "Environment: ${ENVIRONMENT}"
echo "RG:          ${RESOURCE_GROUP}"
echo ""

az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"
```

### `scripts/teardown.sh` -- Resource Cleanup

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"

echo "=== Teardown ==="
echo "This will DELETE resource group: ${RESOURCE_GROUP}"
echo "ALL resources in this group will be permanently destroyed."
echo ""

read -p "Type the resource group name to confirm: " CONFIRM
if [[ "${CONFIRM}" != "${RESOURCE_GROUP}" ]]; then
  echo "Name does not match. Teardown cancelled."
  exit 1
fi

echo ""
echo "Deleting resource group ${RESOURCE_GROUP}..."
az group delete --name "${RESOURCE_GROUP}" --yes --no-wait

echo "Deletion initiated (running in background)."
echo "Monitor with: az group show --name ${RESOURCE_GROUP} --query properties.provisioningState"
```

### `scripts/validate.sh` -- Template Validation

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
LOCATION="${2:-eastus2}"
PROJECT_NAME="claudebricks"
RESOURCE_GROUP="rg-${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="$(dirname "$0")/../main.bicep"
PARAMS_FILE="$(dirname "$0")/../parameters/${ENVIRONMENT}.bicepparam"

echo "=== Bicep Validation ==="

# Lint (compile to ARM)
echo "--- Linting (bicep build) ---"
az bicep build --file "${TEMPLATE_FILE}" --stdout > /dev/null
echo "Lint: PASSED"

# Validate against Azure
echo ""
echo "--- Validating against Azure ---"
az deployment group validate \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "${TEMPLATE_FILE}" \
  --parameters "${PARAMS_FILE}" \
  --parameters location="${LOCATION}"

echo ""
echo "Validation: PASSED"
```

---

## `bicepconfig.json` -- Linter Configuration

```json
{
  "analyzers": {
    "core": {
      "enabled": true,
      "rules": {
        "no-unused-params": {
          "level": "warning"
        },
        "no-unused-vars": {
          "level": "warning"
        },
        "prefer-interpolation": {
          "level": "warning"
        },
        "secure-parameter-default": {
          "level": "error"
        },
        "simplify-interpolation": {
          "level": "warning"
        },
        "use-stable-resource-identifiers": {
          "level": "warning"
        },
        "explicit-values-for-loc-params": {
          "level": "warning"
        },
        "no-hardcoded-location": {
          "level": "warning"
        }
      }
    }
  }
}
```

---

## Mapping to Existing Terraform

This table maps every Terraform resource to its Bicep equivalent for verification:

| Terraform Resource | Terraform File | Bicep Module | Status |
|-------------------|---------------|-------------|--------|
| `azurerm_resource_group` | `resource_group.tf` | Created by wrapper script | Equivalent |
| `azurerm_storage_account` | `storage.tf` | `storage.bicep` | Equivalent |
| `azurerm_storage_container` (x4) | `storage.tf` | `storage.bicep` (loop) | Equivalent (+1 new container) |
| `azurerm_key_vault` | `keyvault.tf` | `keyvault.bicep` | Equivalent (upgraded to RBAC) |
| `azurerm_container_registry` | `acr.tf` | `acr.bicep` | Equivalent |
| `azurerm_log_analytics_workspace` | `monitoring.tf` | `log-analytics.bicep` | Equivalent |
| `azurerm_application_insights` | `monitoring.tf` | `app-insights.bicep` | Equivalent |
| `azurerm_machine_learning_workspace` | `ml_workspace.tf` | `aml-workspace.bicep` | Equivalent |
| `azurerm_machine_learning_compute_instance` | `ml_compute.tf` | `aml-compute.bicep` | Equivalent |
| `azurerm_machine_learning_compute_cluster` (CPU) | `ml_compute.tf` | `aml-compute.bicep` | Equivalent |
| `azurerm_machine_learning_compute_cluster` (GPU) | `ml_compute.tf` | `aml-compute.bicep` | Equivalent |
| `azurerm_cognitive_account` (OpenAI) | `cognitive_services.tf` | `cognitive-services.bicep` | Equivalent |
| `azurerm_cognitive_account` (CV Train) | `cognitive_services.tf` | `cognitive-services.bicep` | Equivalent |
| `azurerm_cognitive_account` (CV Predict) | `cognitive_services.tf` | `cognitive-services.bicep` | Equivalent |
| `azurerm_search_service` | `search.tf` | `search.bicep` | Equivalent |
| -- | -- | `foundry-hub.bicep` | **NEW** |
| -- | -- | `foundry-project.bicep` | **NEW** |
| -- | -- | `aml-registry.bicep` | **NEW** |
| -- | -- | `rbac.bicep` | **NEW** |
| -- | -- | `vnet.bicep` | **NEW** |
| -- | -- | `private-endpoint.bicep` | **NEW** |

---

## Terraform Feature Flag Mapping

| Terraform Variable | Bicep Parameter | Default |
|-------------------|----------------|---------|
| `deploy_openai` | `deployOpenAI` | `true` |
| `deploy_custom_vision` | `deployCustomVision` | `false` |
| `deploy_ai_search` | `deployAISearch` | `true` |
| -- | `deployFoundry` | `true` (NEW) |
| -- | `deployRegistry` | `false` (NEW) |
| -- | `deployPrivateNetworking` | `false` (NEW) |

---

## Estimated Azure Monthly Cost (Dev Environment)

| Resource | SKU/Tier | Estimated Monthly Cost |
|----------|---------|----------------------|
| Storage Account | Standard LRS | ~$2 |
| Key Vault | Standard | ~$0.50 |
| ACR | Basic | ~$5 |
| Log Analytics | Per-GB (30 day retention) | ~$5 |
| Application Insights | Included with Log Analytics | $0 |
| AML Workspace | Basic | $0 (no workspace charge for Basic) |
| Compute Instance (DS2_v2) | Pay-as-you-go, auto-shutdown | ~$30-60 (depends on hours) |
| CPU Cluster (DS3_v2, 0-2 nodes) | Scale-to-zero | ~$0-20 (depends on jobs) |
| GPU Cluster (NC4as_T4_v3, 0-1 node) | Scale-to-zero | ~$0-50 (depends on jobs) |
| Azure OpenAI (S0) | Standard, 10K TPM | ~$5-20 (depends on usage) |
| AI Search (Basic) | Basic tier | ~$75 |
| Foundry Hub | Basic (same as AML workspace) | $0 |
| Foundry Project | Basic (same as AML workspace) | $0 |
| **Total (dev, moderate use)** | | **~$120-240/month** |

---

## GitHub Actions Integration

### Infrastructure Workflow Integration Points

The Bicep deployment integrates with `.github/workflows/infra.yml`:

```yaml
# Key steps that reference Bicep:
- name: Lint Bicep
  run: az bicep build --file deploymentcode/bicep/main.bicep --stdout > /dev/null

- name: Validate
  run: |
    az deployment group validate \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --template-file deploymentcode/bicep/main.bicep \
      --parameters deploymentcode/bicep/parameters/${{ env.ENVIRONMENT }}.bicepparam

- name: What-If
  run: |
    az deployment group what-if \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --template-file deploymentcode/bicep/main.bicep \
      --parameters deploymentcode/bicep/parameters/${{ env.ENVIRONMENT }}.bicepparam

- name: Deploy
  run: |
    az deployment group create \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --template-file deploymentcode/bicep/main.bicep \
      --parameters deploymentcode/bicep/parameters/${{ env.ENVIRONMENT }}.bicepparam \
      --name deploy-${{ env.ENVIRONMENT }}-${{ github.run_number }}
```

### OIDC Authentication Setup

For GitHub Actions to deploy without storing secrets:

1. Create Azure AD App Registration
2. Add federated credential for GitHub Actions
3. Assign Contributor role on subscription or resource group
4. Configure GitHub environment secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`

Bicep module for the federated credential is out of scope (it is a one-time Azure AD setup, not a resource group deployment).

---

## Testing Strategy

### Local Testing

1. **Lint**: `az bicep build --file main.bicep --stdout > /dev/null`
2. **Compile to ARM**: `az bicep build --file main.bicep --outfile main.json` (inspect generated ARM template)
3. **Validate**: `./scripts/validate.sh dev`
4. **What-if**: `./scripts/whatif.sh dev`
5. **Deploy dev**: `./scripts/deploy.sh dev eastus2`

### Automated Testing (GitHub Actions)

1. On every PR touching `deploymentcode/bicep/**`: lint + validate
2. On merge to main: lint + validate + what-if + deploy dev
3. Manual approval: deploy test

### Validation Checklist

After deployment, verify:

- [ ] Resource group exists with correct tags
- [ ] Storage account accessible, containers created
- [ ] Key Vault accessible, RBAC authorization enabled
- [ ] ACR accessible, admin disabled
- [ ] Log Analytics workspace collecting data
- [ ] App Insights connected to Log Analytics
- [ ] AML workspace linked to storage, KV, ACR, App Insights
- [ ] Compute instance running (or startable)
- [ ] CPU cluster scales from 0 on job submission
- [ ] GPU cluster scales from 0 on job submission (if deployed)
- [ ] OpenAI endpoint responds (if deployed)
- [ ] AI Search endpoint responds (if deployed)
- [ ] Foundry hub created, connections to OpenAI and Search working (if deployed)
- [ ] Foundry project created under hub (if deployed)
- [ ] All managed identities have correct RBAC assignments

---

## Implementation Sequence

### Step 1: Core Modules (estimated: first session)

Write these modules first; they have no dependencies on each other:
1. `storage.bicep`
2. `keyvault.bicep`
3. `acr.bicep`
4. `log-analytics.bicep`
5. `bicepconfig.json`

### Step 2: Dependent Modules (estimated: second session)

These depend on Step 1 outputs:
6. `app-insights.bicep` (needs log-analytics)
7. `aml-workspace.bicep` (needs storage, KV, ACR, app-insights)
8. `aml-compute.bicep` (needs workspace)

### Step 3: Optional Service Modules (estimated: third session)

9. `cognitive-services.bicep`
10. `search.bicep`

### Step 4: AI-300 New Modules (estimated: fourth session)

11. `foundry-hub.bicep`
12. `foundry-project.bicep`
13. `aml-registry.bicep`

### Step 5: Orchestrator and Parameters (estimated: fifth session)

14. `main.bicep` (wire everything together)
15. `parameters/dev.bicepparam`
16. `parameters/test.bicepparam`

### Step 6: Wrapper Scripts (estimated: sixth session)

17. `scripts/deploy.sh`
18. `scripts/deploy.ps1`
19. `scripts/whatif.sh`
20. `scripts/teardown.sh`
21. `scripts/validate.sh`

### Step 7: Security Modules (estimated: seventh session, Tier 3)

22. `rbac.bicep`
23. `vnet.bicep`
24. `private-endpoint.bicep`

### Step 8: Testing and Validation

25. Local lint and compile
26. Deploy to dev
27. Verify all resources
28. Run what-if for test
29. Deploy to test (if desired)

---

## API Versions Reference

All modules use these API versions (current as of March 2026):

| Resource Provider | API Version |
|-------------------|------------|
| `Microsoft.Storage/storageAccounts` | `2023-05-01` |
| `Microsoft.KeyVault/vaults` | `2023-07-01` |
| `Microsoft.ContainerRegistry/registries` | `2023-07-01` |
| `Microsoft.OperationalInsights/workspaces` | `2023-09-01` |
| `Microsoft.Insights/components` | `2020-02-02` |
| `Microsoft.MachineLearningServices/workspaces` | `2024-04-01` |
| `Microsoft.MachineLearningServices/workspaces/computes` | `2024-04-01` |
| `Microsoft.MachineLearningServices/registries` | `2024-04-01` |
| `Microsoft.CognitiveServices/accounts` | `2024-04-01-preview` |
| `Microsoft.Search/searchServices` | `2024-03-01-preview` |
| `Microsoft.Network/virtualNetworks` | `2024-01-01` |
| `Microsoft.Network/privateEndpoints` | `2024-01-01` |
| `Microsoft.Authorization/roleAssignments` | `2022-04-01` |

---

## Notes and Caveats

### Foundry API Stability
Microsoft Foundry is evolving. The `kind: 'Hub'` and `kind: 'Project'` on `Microsoft.MachineLearningServices/workspaces` may change. Check the latest API docs before implementing.

### OpenAI Model Availability
Model availability varies by region. `gpt-4o` and `text-embedding-3-small` should be available in `eastus2` but verify before deployment. The Bicep template will fail if a model is not available in the selected region.

### Naming Constraints
- Storage accounts: 3-24 chars, lowercase alphanumeric only
- Key Vault: 3-24 chars, alphanumeric and hyphens
- ACR: 5-50 chars, alphanumeric only
- AML workspace: 1-260 chars, alphanumeric, hyphens, underscores

The naming convention in `main.bicep` handles these constraints.

### Existing Terraform Resources
If you have already deployed resources via Terraform and want to switch to Bicep management, you have two options:
1. **Clean slate**: Tear down Terraform resources, deploy via Bicep (recommended for study project)
2. **Import**: Use `az resource` commands to import existing resources into Bicep state (complex, not recommended unless production)

For Claude.Bricks, option 1 is recommended. Run `terraform destroy`, then `./scripts/deploy.sh dev`.
