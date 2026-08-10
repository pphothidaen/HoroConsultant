targetScope = 'resourceGroup'

@description('Azure region for the Container Apps environment.')
param location string = 'westus2'

@description('Consumption-only Container Apps environment name.')
param environmentName string = 'managedEnvironment-rghoroconsult-b5b1'

@description('Existing production Container App name.')
param containerAppName string = 'horoconsult-env-new'

@description('OCI image tag or digest. Release automation deploys an immutable digest.')
param image string = 'docker.io/pansakorn/horoconsult:latest'

@description('Docker Hub user with pull access to the private repository.')
param dockerRegistryUsername string

@secure()
@description('Docker Hub token with read-only pull access when available.')
param dockerRegistryPassword string

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  tags: {
    app: 'horoconsult'
    costPolicy: 'free-grant-fail-closed'
  }
  properties: {
    zoneRedundant: false
    appLogsConfiguration: {
      destination: 'none'
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: {
    app: 'horoconsult'
    costGuardThreshold: '70-percent'
    workload: 'Consumption'
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
        {
          name: 'dockerhub-pull-token'
          value: dockerRegistryPassword
        }
      ]
      registries: [
        {
          server: 'index.docker.io'
          username: dockerRegistryUsername
          passwordSecretRef: 'dockerhub-pull-token'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'horoconsult'
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'PORT'
              value: '8000'
            }
            {
              name: 'HORO_ALLOW_PYTHON_FALLBACK'
              value: '0'
            }
          ]
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 1
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 24
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
              successThreshold: 1
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppId string = containerApp.id
output fqdn string = containerApp.properties.configuration.ingress.fqdn
