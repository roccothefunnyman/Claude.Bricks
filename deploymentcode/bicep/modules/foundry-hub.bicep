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
