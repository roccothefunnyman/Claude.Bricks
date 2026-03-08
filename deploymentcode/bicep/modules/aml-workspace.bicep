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

@description('Workspace description text')
param workspaceDescription string = 'Claude.Bricks ML workspace'

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
    description: workspaceDescription
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
