@description('Registry name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Regions to replicate registry to')
param replicationLocations array = []

var defaultRegions = [
  {
    location: location
  }
]

var customRegions = [for loc in replicationLocations: {
  location: loc
}]

var registryRegions = empty(replicationLocations) ? defaultRegions : customRegions

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
