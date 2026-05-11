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
        sharedKey: listKeys(workspace.id, workspace.apiVersion).primarySharedKey
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
