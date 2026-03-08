@description('Private endpoint name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Target resource ID')
param privateLinkServiceId string

@description('Group ID for the private link (e.g., blob, vault, amlworkspace)')
param groupId string

@description('Subnet ID for the private endpoint')
param subnetId string

@description('Private DNS zone ID for DNS resolution')
param privateDnsZoneId string

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-connection'
        properties: {
          privateLinkServiceId: privateLinkServiceId
          groupIds: [groupId]
        }
      }
    ]
  }
}

resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output name string = privateEndpoint.name
output id string = privateEndpoint.id
output ipAddress string = privateEndpoint.properties.customDnsConfigs[0].ipAddresses[0]
