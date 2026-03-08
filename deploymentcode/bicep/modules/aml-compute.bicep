@description('Parent AML workspace name')
param workspaceName string

@description('Azure region')
param location string

@description('Resource tags')
param tags object

// Compute instance
@description('Deploy compute instance')
param deployInstance bool = true

@description('Compute instance name')
param instanceName string = 'dev-instance'

@description('Compute instance VM size')
param instanceSize string = 'Standard_DS2_v2'

// CPU cluster
@description('CPU cluster name')
param cpuClusterName string = 'cpu-cluster'

@description('CPU cluster VM size')
param cpuClusterVmSize string = 'Standard_DS3_v2'

@description('CPU cluster min nodes')
param cpuClusterMinNodes int = 0

@description('CPU cluster max nodes')
param cpuClusterMaxNodes int = 2

// GPU cluster
@description('Deploy GPU cluster')
param deployGpuCluster bool = true

@description('GPU cluster name')
param gpuClusterName string = 'gpu-cluster'

@description('GPU cluster VM size')
param gpuClusterVmSize string = 'Standard_NC4as_T4_v3'

@description('GPU cluster min nodes')
param gpuClusterMinNodes int = 0

@description('GPU cluster max nodes')
param gpuClusterMaxNodes int = 1

// Reference existing workspace
resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: workspaceName
}

resource computeInstance 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = if (deployInstance) {
  parent: workspace
  name: instanceName
  location: location
  tags: tags
  properties: {
    computeType: 'ComputeInstance'
    properties: {
      vmSize: instanceSize
      idleTimeBeforeShutdown: 'PT30M'
    }
  }
}

resource cpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = {
  parent: workspace
  name: cpuClusterName
  location: location
  tags: tags
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: cpuClusterVmSize
      scaleSettings: {
        minNodeCount: cpuClusterMinNodes
        maxNodeCount: cpuClusterMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT5M'
      }
    }
  }
}

resource gpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2024-04-01' = if (deployGpuCluster) {
  parent: workspace
  name: gpuClusterName
  location: location
  tags: tags
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: gpuClusterVmSize
      scaleSettings: {
        minNodeCount: gpuClusterMinNodes
        maxNodeCount: gpuClusterMaxNodes
        nodeIdleTimeBeforeScaleDown: 'PT5M'
      }
    }
  }
}

output cpuClusterName string = cpuCluster.name
output gpuClusterName string = deployGpuCluster ? gpuCluster.name : ''
output instanceName string = deployInstance ? computeInstance.name : ''
