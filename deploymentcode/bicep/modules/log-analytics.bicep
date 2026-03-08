@description('Log Analytics workspace name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Retention in days')
param retentionInDays int = 30

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
  }
}

output name string = logAnalytics.name
output id string = logAnalytics.id
output customerId string = logAnalytics.properties.customerId
