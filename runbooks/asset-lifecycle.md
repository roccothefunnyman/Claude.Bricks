# Asset Lifecycle Runbook

Procedures for versioning, publishing, promoting, and archiving ML assets in Claude.Bricks. Covers models, environments, components, and data assets across dev/test workspaces and the shared AML registry.

---

## Model Versioning

### Versioning Scheme: Semantic Versioning

Models use **semantic versioning** (`MAJOR.MINOR.PATCH`):

| Version Part | When to Increment | Example |
|-------------|-------------------|---------|
| MAJOR | Breaking change in input/output schema, different algorithm | `1.0.0` to `2.0.0` |
| MINOR | Retrained on new data, hyperparameter tuning, improved accuracy | `1.0.0` to `1.1.0` |
| PATCH | Bug fix in scoring script, no model weight changes | `1.1.0` to `1.1.1` |

### Model Naming Convention

```
<scenario>-<model-type>:<major>.<minor>.<patch>
```

Examples:
- `facade-classifier:1.0.0` - Scenario 1, Random Forest
- `structural-validator:1.2.0` - Scenario 2, Isolation Forest
- `pattern-extractor:2.0.0` - Scenario 3, HDBSCAN
- `lego-spec-generator:1.0.0` - Scenario 4, Fine-tuned LLM

### Registering a New Model Version

```bash
# In the dev workspace after training
python deploymentcode/scripts/scenario1/register_model.py \
    --model-name facade-classifier \
    --model-path outputs/model/ \
    --version 1.1.0 \
    --description "Retrained on expanded facade dataset (2026-03)"
```

### Model Metadata

Every registered model must include:
- **Description**: What changed in this version
- **Tags**: `scenario`, `algorithm`, `trained_on` (date), `accuracy`, `dataset_version`
- **Properties**: Training job ID, experiment name, MLflow run ID

---

## Environment Versioning

### Versioning Scheme: Major.Minor

```
<environment-name>:<major>.<minor>
```

| Version Part | When to Increment |
|-------------|-------------------|
| MAJOR | Base image change, Python version change, major dependency upgrade |
| MINOR | Dependency version bump, new optional dependency added |

### Environment Names

| Environment | Purpose | Base Image |
|-------------|---------|-----------|
| `claudebricks-sklearn` | Scenarios 1-3 (scikit-learn, pandas, numpy) | `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04` |
| `claudebricks-genai` | Scenario 4 (openai, azure-search, langchain) | `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04` |
| `claudebricks-drift` | Drift detection (scipy, pandas, mlflow) | `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04` |

### Registering an Environment

```bash
python deploymentcode/scripts/register_envs.py \
    --name claudebricks-sklearn \
    --version 1.3 \
    --conda-file deploymentcode/environments/sklearn-conda.yml
```

---

## Component Versioning

### Versioning Scheme: Major.Minor

Pipeline components use `MAJOR.MINOR`:

| Version Part | When to Increment |
|-------------|-------------------|
| MAJOR | Input/output interface change, new required parameters |
| MINOR | Internal logic change, same interface |

### Component Names

| Component | Purpose |
|-----------|---------|
| `prepare-data` | Load and preprocess training data |
| `train-model` | Train and log model with MLflow |
| `evaluate-model` | Score model on test set, log metrics |
| `register-model` | Register model if metrics pass threshold |

### Registering Components

```bash
python deploymentcode/scripts/register_components.py \
    --component-dir deploymentcode/components/ \
    --version 1.0
```

---

## Data Asset Versioning

### Versioning Scheme: Integer

Data assets use simple integer versions that auto-increment:

```
<asset-name>:<version>
```

Examples:
- `facade-images:1` - Initial training dataset
- `facade-images:2` - Expanded dataset with new facade styles
- `inference-logs-scenario1:1` - Captured inference data for drift analysis

### Registering Data Assets

```bash
python deploymentcode/scripts/register_data_assets.py \
    --name facade-images \
    --path azureml://datastores/workspaceblobstore/paths/scenario1/images/ \
    --type uri_folder
```

---

## Publishing to Shared Registry

The shared AML registry (`reg-claudebricks`) enables asset sharing across dev and test workspaces without re-registration.

### Publish a Model

```bash
python deploymentcode/scripts/publish_to_registry.py \
    --asset-type model \
    --name facade-classifier \
    --version 1.1.0 \
    --registry-name reg-claudebricks
```

### Publish an Environment

```bash
python deploymentcode/scripts/publish_to_registry.py \
    --asset-type environment \
    --name claudebricks-sklearn \
    --version 1.3 \
    --registry-name reg-claudebricks
```

### Import from Registry to Workspace

```bash
python deploymentcode/scripts/import_from_registry.py \
    --asset-type model \
    --name facade-classifier \
    --version 1.1.0 \
    --registry-name reg-claudebricks \
    --target-workspace mlw-claudebricks-test
```

---

## Promotion Flow

### Dev to Test

1. **Train and validate in dev workspace**
   - Training job completes, metrics logged to MLflow
   - Model passes accuracy threshold (>= 0.85)
   - Model registered in dev workspace

2. **Publish to shared registry**
   ```bash
   python deploymentcode/scripts/publish_to_registry.py \
       --asset-type model --name facade-classifier --version 1.1.0
   ```

3. **Import into test workspace**
   ```bash
   python deploymentcode/scripts/import_from_registry.py \
       --asset-type model --name facade-classifier --version 1.1.0 \
       --target-workspace mlw-claudebricks-test
   ```

4. **Deploy to test endpoint** (see `runbooks/endpoint-deployment.md`)

5. **Run evaluation suite in test**
   ```bash
   python eval/run_evaluation.py --workspace mlw-claudebricks-test
   ```

6. **Manual approval gate** (via GitHub Actions environment protection rule)

### Automated Promotion (CI/CD)

The full promotion is orchestrated by:
- `.github/workflows/deploy-model.yml` for model deployment
- `.github/workflows/eval-rag.yml` for GenAI evaluation gates

---

## Archival Policies

### Models

| Rule | Action |
|------|--------|
| 3 newer versions registered for the same model name | Archive older versions |
| No active deployment references the model version | Eligible for archival |
| Model archived | Metadata retained, artifacts deleted from blob storage |

**Archive a model**:
```bash
az ml model archive \
    --name facade-classifier \
    --version 1.0.0 \
    --resource-group <rg> \
    --workspace-name <ws>
```

**Restore an archived model** (if needed):
```bash
az ml model restore \
    --name facade-classifier \
    --version 1.0.0 \
    --resource-group <rg> \
    --workspace-name <ws>
```

### Environments

| Rule | Action |
|------|--------|
| No active deployment or training job references the environment version | Eligible for archival |
| Newer major version exists and is in use | Archive older major versions |

**Archive an environment**:
```bash
az ml environment archive \
    --name claudebricks-sklearn \
    --version 1.2 \
    --resource-group <rg> \
    --workspace-name <ws>
```

### Components

| Rule | Action |
|------|--------|
| Replaced by newer major version | Archive older major versions |
| No pipeline references the component version | Eligible for archival |

### Data Assets

| Rule | Action |
|------|--------|
| Superseded by newer version with same schema | Keep for 90 days, then archive |
| Referenced by a registered model's training metadata | Never archive |

### Registry Assets

Assets in the shared registry (`reg-claudebricks`) follow the same rules but require verification across all workspaces before archival:

```bash
# Check if any workspace references the model
az ml model list --registry-name reg-claudebricks --name facade-classifier
```

---

## Audit Trail

All asset lifecycle events are tracked via:

1. **AML workspace activity logs**: Registration, archival, deployment events
2. **MLflow experiment tracking**: Training runs, metrics, parameters
3. **GitHub Actions workflow logs**: CI/CD promotion steps
4. **Application Insights**: Runtime telemetry with model_version dimension
5. **Git history**: Version-controlled scripts, prompts, and configurations
