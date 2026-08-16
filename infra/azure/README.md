# Azure Container Apps infrastructure

This template encodes the verified existing production boundary: Azure
Container Apps Consumption in West US 2, environment
`managedEnvironment-rghoroconsult-b5b1`, `minReplicas: 0`, `maxReplicas: 1`,
0.5 vCPU, 1 GiB, port 8000, and no Log Analytics ingestion. The CI/CD workflow
updates the existing app by immutable OCI digest; it does not redeploy this
template on every release. A future region migration should create a new app
name/environment and use revision-aware cutover instead of mutating location.

Validate without changing Azure:

```bash
az bicep build --file infra/azure/main.bicep
az deployment group what-if \
  --resource-group rg-horoconsult \
  --template-file infra/azure/main.bicep \
  --parameters dockerRegistryUsername="$DOCKER_USERNAME" \
  --parameters dockerRegistryPassword="$DOCKER_PASSWORD"
```

Never place the registry token in a parameter file or commit it. Prefer a
separate Docker Hub read-only token for Azure image pulls; GitHub Actions uses
the repository secrets `DOCKER_USERNAME`, `DOCKER_PASSWORD`, and
`AZURE_CREDENTIALS`.
