targetScope = 'resourceGroup'

@description('Azure location for all resources')
param location string = resourceGroup().location

@description('Deployment environment name')
param environmentName string = 'dev'

@description('Container registry name (must be globally unique, 5-50 lowercase alphanumeric)')
param acrName string

@description('Container Apps environment name')
param containerAppsEnvironmentName string = 'cae-cloud-agent'

@description('Container app name')
param containerAppName string = 'ca-cloud-agent-ui'

@description('Log Analytics workspace name')
param logAnalyticsWorkspaceName string = 'law-cloud-agent'

@description('Azure OpenAI account name (must be globally unique, 2-64 lowercase alphanumeric or hyphen)')
param openAiAccountName string

@description('Azure location for the OpenAI account (may differ from main location for quota reasons)')
param openAiLocation string = 'eastus'

@description('Azure OpenAI deployment name consumed by the app')
param openAiDeploymentName string = 'gpt-4.1-mini'

@description('Azure OpenAI API version exposed to app config')
param openAiApiVersion string = '2024-08-01-preview'

@description('CPU allocated for container app')
param containerCpu int = 1

@description('Memory allocated for container app in Gi')
param containerMemory string = '2Gi'

@description('Container target port')
param targetPort int = 8000

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiAccountName
  location: openAiLocation
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled'
  }
}

resource openAiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: openAiDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: openAiDeploymentName
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
      }
      registries: [
        {
          server: '${acr.name}.azurecr.io'
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-pwd'
        }
      ]
      secrets: [
        {
          name: 'acr-pwd'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'openai-api-key'
          value: openAiAccount.listKeys().key1
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: containerCpu
            memory: containerMemory
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiAccount.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: openAiDeploymentName
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: openAiApiVersion
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output resourceGroupName string = resourceGroup().name
output environment string = environmentName
output containerRegistryName string = acr.name
output containerRegistryLoginServer string = '${acr.name}.azurecr.io'
output containerAppResourceName string = containerApp.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output openAiAccountResourceName string = openAiAccount.name
output openAiEndpoint string = openAiAccount.properties.endpoint
@secure()
output openAiApiKey string = openAiAccount.listKeys().key1
output openAiDeploymentNameOut string = openAiDeploymentName
output openAiApiVersionOut string = openAiApiVersion
