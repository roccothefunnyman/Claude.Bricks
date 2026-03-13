// ============================================================================
// Microsoft Foundry Project (child resource of Foundry account)
// Uses CognitiveServices/accounts/projects (replaces MachineLearningServices)
// ============================================================================

@description('Foundry project name')
param name string

@description('Azure region')
param location string

@description('Parent Foundry account name')
param foundryAccountName string

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: name
  parent: foundryAccount
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

output name string = project.name
output id string = project.id
output principalId string = project.identity.principalId
