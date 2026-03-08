@description('Azure OpenAI account name')
param openAIName string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

@description('Deploy Azure OpenAI')
param deployOpenAI bool = true

@description('Deploy Custom Vision')
param deployCustomVision bool = false

@description('Custom Vision training account name')
param customVisionTrainingName string = ''

@description('Custom Vision prediction account name')
param customVisionPredictionName string = ''

@description('OpenAI model deployments')
param openAIModelDeployments array = [
  {
    name: 'gpt-4o'
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
  {
    name: 'text-embedding-3-small'
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
]

resource openAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployOpenAI) {
  name: openAIName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@batchSize(1)
resource openAIDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [
  for deployment in openAIModelDeployments: if (deployOpenAI) {
    parent: openAI
    name: deployment.name
    sku: deployment.sku
    properties: {
      model: deployment.model
    }
  }
]

resource customVisionTraining 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployCustomVision) {
  name: customVisionTrainingName
  location: location
  tags: tags
  kind: 'CustomVision.Training'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customVisionTrainingName
  }
}

resource customVisionPrediction 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = if (deployCustomVision) {
  name: customVisionPredictionName
  location: location
  tags: tags
  kind: 'CustomVision.Prediction'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: customVisionPredictionName
  }
}

output openAIEndpoint string = deployOpenAI ? openAI.properties.endpoint : ''
output openAIId string = deployOpenAI ? openAI.id : ''
output openAIPrincipalId string = deployOpenAI ? openAI.identity.principalId : ''
