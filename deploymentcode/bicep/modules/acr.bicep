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
