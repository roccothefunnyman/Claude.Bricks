// ============================================================================
// Microsoft Foundry Resource (replaces standalone Azure OpenAI + AI Hub)
// Uses CognitiveServices/accounts with kind=AIServices
// ============================================================================

@description('Foundry resource name')
param foundryName string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Deploy Foundry resource')
param deployFoundry bool = true

@description('Deploy Custom Vision resources')
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

@description('AI Search resource ID (optional, for connection)')
param searchResourceId string = ''

@description('AI Search endpoint (optional, for connection)')
param searchEndpoint string = ''

// Microsoft Foundry resource (kind: AIServices with project management)
resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = if (deployFoundry) {
  name: foundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: foundryName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Model deployments (child resources of Foundry)
@batchSize(1)
resource foundryDeployments 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = [
  for deployment in openAIModelDeployments: if (deployFoundry) {
    parent: foundry
    name: deployment.name
    sku: deployment.sku
    properties: {
      model: deployment.model
    }
  }
]

// Connection to AI Search (if deployed)
resource searchConnection 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = if (deployFoundry && !empty(searchResourceId)) {
  parent: foundry
  name: 'azure-ai-search'
  properties: {
    category: 'CognitiveSearch'
    target: searchEndpoint
    authType: 'AAD'
    metadata: {
      ResourceId: searchResourceId
    }
  }
}

// Custom Vision (kept separate, these are still standalone Cognitive Services)
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

output foundryEndpoint string = deployFoundry ? foundry.properties.endpoint : ''
output foundryId string = deployFoundry ? foundry.id : ''
output foundryPrincipalId string = deployFoundry ? foundry.identity.principalId : ''
output foundryName string = deployFoundry ? foundry.name : ''
