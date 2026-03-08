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
