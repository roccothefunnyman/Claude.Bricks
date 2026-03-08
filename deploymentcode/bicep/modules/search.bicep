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
