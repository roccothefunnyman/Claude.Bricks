using '../main.bicep'

param projectName = 'claudebricks'
param environment = 'test'
param tags = {
  project: 'claude-bricks'
  environment: 'test'
  managedBy: 'bicep'
  purpose: 'validation'
}

// Feature flags
param deployOpenAI = true
param deployCustomVision = false
param deployAISearch = true
param deployFoundry = true
param deployRegistry = true           // Shared registry for promotion
param deployPrivateNetworking = true   // Network isolation in test

// Compute (no dev instance, larger clusters)
param computeInstanceSize = 'Standard_DS2_v2'  // Will not deploy (handled in main)
param cpuClusterMaxNodes = 4
param gpuClusterMaxNodes = 0  // No GPU in test unless needed
param cpuClusterVmSize = 'Standard_DS3_v2'
param gpuClusterVmSize = 'Standard_NC4as_T4_v3'

// Models
param openAIModelName = 'gpt-4o'
param openAIModelVersion = '2024-08-06'
param embeddingModelName = 'text-embedding-3-small'

// SKUs
param searchSku = 'basic'
param amlSku = 'Basic'
