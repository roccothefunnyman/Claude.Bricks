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
