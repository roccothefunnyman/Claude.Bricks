# Endpoint Deployment Runbook

Operational procedures for deploying, validating, promoting, and rolling back managed online endpoints in Claude.Bricks.

Primary scenario: **Scenario 1 - Facade Classification** (`facade-classifier-endpoint`).

---

## Prerequisites

Before starting any deployment:

1. **Model registered in AML**: Verify the model version exists in the workspace model registry.
   ```bash
   az ml model show --name facade-classifier --version <version> --resource-group <rg> --workspace-name <ws>
   ```

2. **Endpoint exists**: The managed online endpoint must already be created. If not:
   ```bash
   python deploymentcode/scripts/scenario1/deploy_endpoint.py
   ```

3. **Permissions**: The deploying identity needs:
   - `AzureML Data Scientist` role on the AML workspace
   - `Contributor` role on the resource group (for endpoint operations)

4. **Scoring script tested locally**: Validate `score.py` runs against sample data before deploying.

5. **Environment image built**: The AML environment must resolve (conda/pip dependencies installable, base image pullable from ACR).

---

## Deploy a New Model Version

### Step 1: Deploy as canary (0% traffic)

```bash
python deploymentcode/scripts/scenario1/deploy_canary.py \
    --model-name facade-classifier \
    --model-version <new-version> \
    --deployment-name green \
    --instance-type Standard_DS2_v2 \
    --instance-count 1
```

This creates a new deployment on the existing endpoint with 0% traffic allocation.

### Step 2: Verify the deployment is healthy

```bash
az ml online-deployment show \
    --name green \
    --endpoint-name facade-classifier-endpoint \
    --resource-group <rg> \
    --workspace-name <ws> \
    --query "provisioning_state"
```

Expected output: `"Succeeded"`

### Step 3: Run smoke tests

```bash
python deploymentcode/scripts/scenario1/smoke_test.py \
    --endpoint-name facade-classifier-endpoint \
    --deployment-name green
```

Smoke test checks (all must pass):
- HTTP 200 response on known test inputs
- Response latency < 2 seconds (p95)
- Prediction confidence > 0.5 for known inputs
- Response JSON matches expected schema

---

## Verify Deployment Health

### Manual health check

```bash
az ml online-endpoint invoke \
    --name facade-classifier-endpoint \
    --deployment-name green \
    --request-file deploymentcode/scripts/scenario1/sample_request.json \
    --resource-group <rg> \
    --workspace-name <ws>
```

### Check deployment logs

```bash
az ml online-deployment get-logs \
    --name green \
    --endpoint-name facade-classifier-endpoint \
    --resource-group <rg> \
    --workspace-name <ws> \
    --lines 100
```

### Check metrics in Application Insights

Review the KQL dashboards:
- `monitoring/dashboards/avg-latency-by-prompt.kql` for latency
- `monitoring/dashboards/error-rate-trend.kql` for error rate

---

## Promote Traffic

### Gradual promotion (recommended)

```bash
# Step 1: 10% to new deployment
python deploymentcode/scripts/scenario1/promote_deployment.py \
    --endpoint-name facade-classifier-endpoint \
    --deployment-name green \
    --traffic 10

# Step 2: Wait 5 minutes, monitor error rate and latency

# Step 3: If healthy, promote to 50%
python deploymentcode/scripts/scenario1/promote_deployment.py \
    --endpoint-name facade-classifier-endpoint \
    --deployment-name green \
    --traffic 50

# Step 4: Wait 10 minutes, monitor

# Step 5: Full cutover
python deploymentcode/scripts/scenario1/promote_deployment.py \
    --endpoint-name facade-classifier-endpoint \
    --deployment-name green \
    --traffic 100
```

### Direct promotion (CI/CD automated path)

Used by `.github/workflows/deploy-model.yml`:
1. Deploy canary at 0%
2. Run smoke test
3. Promote to 10%
4. Wait for health check window (default 5 minutes)
5. If healthy: promote to 100%
6. If unhealthy: automatic rollback

---

## Rollback Procedure

### Immediate rollback

If the new deployment shows errors or degraded performance:

```bash
python deploymentcode/scripts/scenario1/rollback_deployment.py \
    --endpoint-name facade-classifier-endpoint \
    --rollback-to blue
```

This sets the `blue` (previous) deployment to 100% traffic and the `green` deployment to 0%.

### Manual rollback via Azure CLI

```bash
az ml online-endpoint update \
    --name facade-classifier-endpoint \
    --traffic "blue=100 green=0" \
    --resource-group <rg> \
    --workspace-name <ws>
```

### Delete failed deployment

After rollback, clean up the failed deployment:

```bash
az ml online-deployment delete \
    --name green \
    --endpoint-name facade-classifier-endpoint \
    --resource-group <rg> \
    --workspace-name <ws> \
    --yes
```

---

## Threshold Definitions

| Metric | Threshold | Action if Breached |
|--------|-----------|-------------------|
| Response latency (p95) | < 2,000 ms | Rollback |
| HTTP success rate | > 99% | Rollback |
| Prediction confidence (mean) | > 0.5 on known inputs | Rollback |
| Schema validation | 100% pass | Rollback |
| Error rate (5-minute window) | < 5% | Alert + investigate |
| Error rate (1-minute window) | < 10% | Automatic rollback |

---

## Troubleshooting

### Deployment stuck in "Updating" state

**Cause**: Image pull failure, dependency installation failure, or quota exceeded.

**Resolution**:
1. Check deployment logs for errors.
2. Verify the AML environment image builds successfully:
   ```bash
   az ml environment show --name <env-name> --version <version> --resource-group <rg> --workspace-name <ws>
   ```
3. Check ACR for the image.
4. If quota exceeded, request a quota increase or use a smaller instance type.

### Scoring errors (HTTP 500)

**Cause**: Bug in `score.py`, missing dependencies, or model file corruption.

**Resolution**:
1. Pull deployment logs.
2. Test `score.py` locally with the same model version.
3. Verify model artifacts downloaded correctly.
4. Check that all Python dependencies are in the environment definition.

### Image pull failures

**Cause**: ACR access denied or image not found.

**Resolution**:
1. Verify the AML workspace managed identity has `AcrPull` on the ACR.
2. Verify the environment image tag exists in ACR:
   ```bash
   az acr repository show-tags --name <acr-name> --repository <image-name>
   ```

### Quota exceeded

**Cause**: Insufficient compute quota for the requested instance type.

**Resolution**:
1. Check current quota usage:
   ```bash
   az ml online-deployment list --endpoint-name facade-classifier-endpoint --resource-group <rg> --workspace-name <ws>
   ```
2. Request quota increase via Azure portal.
3. Alternatively, use a smaller instance type (e.g., `Standard_DS1_v2`).

### High latency after deployment

**Cause**: Cold start, model loading time, or insufficient instance count.

**Resolution**:
1. Check if latency is only high for first requests (cold start).
2. Increase instance count if sustained high load.
3. Review model size and consider optimization.
4. Check if the scoring script does unnecessary initialization per request.
