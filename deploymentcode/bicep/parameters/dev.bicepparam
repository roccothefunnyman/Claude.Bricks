using '../main.bicep'

param projectName = 'claudebricks'
param environment = 'dev'
param tags = {
  project: 'claude-bricks'
  environment: 'dev'
  managedBy: 'bicep'
  purpose: 'development'
}

// Feature flags
param deployOpenAI = true
param deployCustomVision = false
param deployAISearch = true
param deployFoundry = true
param deployRegistry = false
param deployPrivateNetworking = false

// Compute (smaller for dev)
param computeInstanceSize = 'Standard_DS2_v2'
param cpuClusterMaxNodes = 2
param gpuClusterMaxNodes = 1
param cpuClusterVmSize = 'Standard_DS3_v2'
param gpuClusterVmSize = 'Standard_NC4as_T4_v3'

// Models
param openAIModelName = 'gpt-4o'
param openAIModelVersion = '2024-08-06'
param embeddingModelName = 'text-embedding-3-small'

// SKUs
param searchSku = 'basic'
param amlSku = 'Basic'
