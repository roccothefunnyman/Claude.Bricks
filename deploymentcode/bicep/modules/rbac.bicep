@description('Role assignments to create')
param roleAssignments array
// Each item: { principalId, roleDefinitionId, scope, principalType, description }

// Well-known role definition IDs
var builtInRoles = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  reader: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  amlDataScientist: 'f6c7c914-8db3-469d-8ca1-694a8f32e121'
  cognitiveServicesOpenAIUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
}

resource assignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for (assignment, i) in roleAssignments: {
    name: guid(assignment.principalId, assignment.roleDefinitionId, assignment.scope)
    scope: resourceGroup()
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', assignment.roleDefinitionId)
      principalId: assignment.principalId
      principalType: assignment.?principalType ?? 'ServicePrincipal'
    }
  }
]

output assignedRoles int = length(roleAssignments)
