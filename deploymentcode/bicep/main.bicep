// ============================================================================
// Claude.Bricks -- Main Orchestrator
// Deploys all infrastructure modules in dependency order
// Updated: Uses Microsoft Foundry (CognitiveServices/accounts kind=AIServices)
//          instead of legacy Azure AI Hub/Project + standalone Azure OpenAI
// ============================================================================

targetScope = 'resourceGroup'

// === PARAMETERS ===

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
param projectName string = 'claudebricks'

@description('Environment identifier (dev, test, prod)')
param environment string = 'dev'

@description('Common tags applied to all resources')
param tags object = {
  project: 'claude-bricks'
  environment: environment
  managedBy: 'bicep'
}

// Feature flags
@description('Deploy Microsoft Foundry resource (includes OpenAI models)')
param deployFoundry bool = true

@description('Deploy Custom Vision resources')
param deployCustomVision bool = false

@description('Deploy AI Search resource')
param deployAISearch bool = true

@description('Deploy Foundry project')
param deployFoundryProject bool = true

@description('Deploy shared AML registry')
param deployRegistry bool = false

@description('Deploy VNet and private endpoints')
param deployPrivateNetworking bool = false

// Compute configuration
@description('Compute instance VM size')
param computeInstanceSize string = 'Standard_DS2_v2'

@description('CPU cluster max nodes')
param cpuClusterMaxNodes int = 2

@description('GPU cluster max nodes')
param gpuClusterMaxNodes int = 1

@description('CPU cluster VM size')
param cpuClusterVmSize string = 'Standard_DS3_v2'

@description('GPU cluster VM size')
param gpuClusterVmSize string = 'Standard_NC4as_T4_v3'

// Model configuration
@description('OpenAI model deployment name')
param openAIModelName string = 'gpt-4o'

@description('OpenAI model version')
param openAIModelVersion string = '2024-08-06'

@description('Embedding model deployment name')
param embeddingModelName string = 'text-embedding-3-small'

@description('AI Search SKU')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3'])
param searchSku string = 'basic'

@description('AML workspace SKU')
@allowed(['Basic', 'Standard'])
param amlSku string = 'Basic'

// === NAMING ===

var baseName = '${projectName}${environment}'
var storageAccountName = 'st${replace(baseName, '-', '')}'
var keyVaultName = 'kv-${projectName}-${environment}-v2'
var acrName = 'acr${replace(baseName, '-', '')}'
var logAnalyticsName = 'law-${projectName}-${environment}'
var appInsightsName = 'appi-${projectName}-${environment}'
var workspaceName = 'mlw-${projectName}-${environment}-v2'
var foundryName = 'foundry-${projectName}-${environment}'
var foundryProjectName = 'proj-${projectName}-${environment}'
var searchName = 'srch-${projectName}-${environment}'
var registryName = 'reg-${projectName}'
var vnetName = 'vnet-${projectName}-${environment}'

// Custom Vision naming
var customVisionTrainingName = 'cv-train-${projectName}-${environment}'
var customVisionPredictionName = 'cv-pred-${projectName}-${environment}'

// === MODULE DEPLOYMENTS ===

// 1. Storage account (no dependencies)
module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    name: storageAccountName
    location: location
    tags: tags
  }
}

// 2. Key Vault (no dependencies)
module keyVault 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  params: {
    name: keyVaultName
    location: location
    tags: tags
  }
}

// 3. Container Registry (no dependencies)
module acr 'modules/acr.bicep' = {
  name: 'deploy-acr'
  params: {
    name: acrName
    location: location
    tags: tags
  }
}

// 4. Log Analytics (no dependencies)
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'deploy-log-analytics'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
  }
}

// 5. Application Insights (depends on Log Analytics)
module appInsights 'modules/app-insights.bicep' = {
  name: 'deploy-app-insights'
  params: {
    name: appInsightsName
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// 6. AML Workspace (depends on storage, keyvault, acr, app-insights)
module amlWorkspace 'modules/aml-workspace.bicep' = {
  name: 'deploy-aml-workspace'
  params: {
    name: workspaceName
    location: location
    tags: tags
    sku: amlSku
    storageAccountId: storage.outputs.id
    keyVaultId: keyVault.outputs.id
    containerRegistryId: acr.outputs.id
    applicationInsightsId: appInsights.outputs.id
  }
}

// 7. AML Compute (depends on AML workspace)
module amlCompute 'modules/aml-compute.bicep' = {
  name: 'deploy-aml-compute'
  params: {
    workspaceName: amlWorkspace.outputs.name
    location: location
    tags: tags
    deployInstance: environment == 'dev'
    instanceName: 'dev-instance-v2'
    instanceSize: computeInstanceSize
    cpuClusterName: 'cpu-cluster'
    cpuClusterVmSize: cpuClusterVmSize
    cpuClusterMaxNodes: cpuClusterMaxNodes
    deployGpuCluster: gpuClusterMaxNodes > 0
    gpuClusterName: 'gpu-cluster'
    gpuClusterVmSize: gpuClusterVmSize
    gpuClusterMaxNodes: gpuClusterMaxNodes
  }
}

// 8. AI Search (conditional, no dependencies -- deployed before Foundry so we can connect)
module search 'modules/search.bicep' = if (deployAISearch) {
  name: 'deploy-search'
  params: {
    name: searchName
    location: location
    tags: tags
    sku: searchSku
  }
}

// 9. Microsoft Foundry + model deployments + connections
//    Replaces: standalone Azure OpenAI (kind=OpenAI) + Azure AI Hub (MachineLearningServices kind=Hub)
//    New: single CognitiveServices/accounts resource with kind=AIServices and allowProjectManagement=true
module foundry 'modules/cognitive-services.bicep' = if (deployFoundry || deployCustomVision) {
  name: 'deploy-foundry'
  params: {
    foundryName: foundryName
    location: location
    tags: tags
    deployFoundry: deployFoundry
    deployCustomVision: deployCustomVision
    customVisionTrainingName: customVisionTrainingName
    customVisionPredictionName: customVisionPredictionName
    openAIModelDeployments: [
      {
        name: openAIModelName
        model: {
          format: 'OpenAI'
          name: openAIModelName
          version: openAIModelVersion
        }
        sku: {
          name: 'Standard'
          capacity: 10
        }
      }
      {
        name: embeddingModelName
        model: {
          format: 'OpenAI'
          name: embeddingModelName
          version: '1'
        }
        sku: {
          name: 'Standard'
          capacity: 10
        }
      }
    ]
    searchResourceId: deployAISearch ? search.outputs.id : ''
    searchEndpoint: deployAISearch ? search.outputs.endpoint : ''
  }
}

// 10. Foundry Project (child resource of Foundry account)
//     Replaces: MachineLearningServices/workspaces kind=Project
//     New: CognitiveServices/accounts/projects (child of the Foundry account)
module foundryProject 'modules/foundry-project.bicep' = if (deployFoundry && deployFoundryProject) {
  name: 'deploy-foundry-project'
  params: {
    name: foundryProjectName
    location: location
    foundryAccountName: foundry.outputs.foundryName
  }
}

// 11. AML Registry (conditional)
module registry 'modules/aml-registry.bicep' = if (deployRegistry) {
  name: 'deploy-aml-registry'
  params: {
    name: registryName
    location: location
    tags: tags
  }
}

// 12. VNet (conditional, for private networking)
module vnet 'modules/vnet.bicep' = if (deployPrivateNetworking) {
  name: 'deploy-vnet'
  params: {
    name: vnetName
    location: location
    tags: tags
  }
}

// 13. RBAC role assignments (depends on all resources with managed identities)
var storageBlobDataContributorId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var keyVaultSecretsUserId = '4633458b-17de-408a-b874-0445c86b69e6'
var acrPullId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// AML workspace needs access to storage, key vault, and ACR
var workspaceRoleAssignments = [
  {
    principalId: amlWorkspace.outputs.principalId
    roleDefinitionId: storageBlobDataContributorId
    scope: storage.outputs.id
    description: 'AML workspace -> Storage Blob Data Contributor'
  }
  {
    principalId: amlWorkspace.outputs.principalId
    roleDefinitionId: keyVaultSecretsUserId
    scope: keyVault.outputs.id
    description: 'AML workspace -> Key Vault Secrets User'
  }
  {
    principalId: amlWorkspace.outputs.principalId
    roleDefinitionId: acrPullId
    scope: acr.outputs.id
    description: 'AML workspace -> ACR Pull'
  }
]

// Storage account managed identity needs Key Vault access
var storageRoleAssignments = [
  {
    principalId: storage.outputs.principalId
    roleDefinitionId: keyVaultSecretsUserId
    scope: keyVault.outputs.id
    description: 'Storage -> Key Vault Secrets User'
  }
]

// Foundry managed identity needs access to storage, key vault, and ACR
var foundryRoleAssignments = deployFoundry ? [
  {
    principalId: foundry.outputs.foundryPrincipalId
    roleDefinitionId: storageBlobDataContributorId
    scope: storage.outputs.id
    description: 'Foundry -> Storage Blob Data Contributor'
  }
  {
    principalId: foundry.outputs.foundryPrincipalId
    roleDefinitionId: keyVaultSecretsUserId
    scope: keyVault.outputs.id
    description: 'Foundry -> Key Vault Secrets User'
  }
  {
    principalId: foundry.outputs.foundryPrincipalId
    roleDefinitionId: acrPullId
    scope: acr.outputs.id
    description: 'Foundry -> ACR Pull'
  }
] : []

// Foundry project role assignments (conditional)
var projectRoleAssignments = (deployFoundry && deployFoundryProject) ? [
  {
    principalId: foundryProject.outputs.principalId
    roleDefinitionId: storageBlobDataContributorId
    scope: storage.outputs.id
    description: 'Foundry Project -> Storage Blob Data Contributor'
  }
] : []

// Combine all role assignments
var allRoleAssignments = concat(
  workspaceRoleAssignments,
  storageRoleAssignments,
  foundryRoleAssignments,
  projectRoleAssignments
)

module rbac 'modules/rbac.bicep' = {
  name: 'deploy-rbac'
  params: {
    roleAssignments: allRoleAssignments
  }
}

// === OUTPUTS ===

output workspaceName string = amlWorkspace.outputs.name
output workspaceId string = amlWorkspace.outputs.id
output storageAccountName string = storage.outputs.name
output storageAccountId string = storage.outputs.id
output keyVaultName string = keyVault.outputs.name
output keyVaultUri string = keyVault.outputs.uri
output acrName string = acr.outputs.name
output acrLoginServer string = acr.outputs.loginServer
output appInsightsName string = appInsights.outputs.name
output appInsightsConnectionString string = appInsights.outputs.connectionString
output logAnalyticsWorkspaceId string = logAnalytics.outputs.id
output foundryEndpoint string = deployFoundry ? foundry.outputs.foundryEndpoint : ''
output foundryName string = deployFoundry ? foundry.outputs.foundryName : ''
output foundryProjectName string = (deployFoundry && deployFoundryProject) ? foundryProject.outputs.name : ''
output searchEndpoint string = deployAISearch ? search.outputs.endpoint : ''
output registryName string = deployRegistry ? registry.outputs.name : ''
