# Claude.Bricks AI-300 Transformation Plan

## Executive Summary

This document is the master plan for transforming Claude.Bricks from a **DP-100 lab deployment** into an **AI-300 operations platform**. The Microsoft AI-300 exam ("Operationalizing Machine Learning and Generative AI Solutions") replaces DP-100 and shifts emphasis from "build the model" to "provision, version, promote, evaluate, monitor, optimize, and govern the system."

Claude.Bricks already has strong bones: AML workspace, 4 ML scenarios, MLflow, training/deployment scripts, RAG, Prompt Flow, Azure OpenAI, AI Search, and a full Terraform IaC story. The transformation preserves all of that while layering on the operational disciplines AI-300 demands.

---

## AI-300 Exam Domains (for reference)

| # | Domain | Weight |
|---|--------|--------|
| 1 | Design and implement an MLOps infrastructure | 15-20% |
| 2 | Implement ML model lifecycle and operations | 25-30% |
| 3 | Design and implement a GenAIOps infrastructure | 20-25% |
| 4 | Implement GenAI quality assurance and observability | 10-15% |
| 5 | Optimize GenAI systems and model performance | 10-15% |

---

## Current State Snapshot (March 2026)

### What Exists Today

| Area | Status | Location |
|------|--------|----------|
| Terraform IaC (AML, storage, KV, ACR, monitoring, OpenAI, AI Search) | Complete | `deploymentcode/terraform/` and `tf/` |
| Bootstrap script (datastores, environments, compute verification) | Complete | `deploymentcode/scripts/00_bootstrap.py` |
| Scenario 1: Facade Classification (Random Forest) | Scripts complete, not deployed | `deploymentcode/scripts/scenario1/` |
| Scenario 2: Structural Validation (Isolation Forest) | Scripts complete, feature_engineering stub | `deploymentcode/scripts/scenario2/` |
| Scenario 3: Pattern Extraction (KMeans/HDBSCAN) | Scripts complete, includes pipeline_job | `deploymentcode/scripts/scenario3/` |
| Scenario 4: LLM Spec Generator (RAG + fine-tune) | Scripts complete, Prompt Flow defined | `deploymentcode/scripts/scenario4/` |
| Shared Python utilities (ml_client, blob_upload) | Complete | `deploymentcode/scripts/common/` |
| As-built HTML documentation | Complete (DP-100 framing) | `claude-bricks-asbuilt.html` |
| PowerShell LEGO generation system | Stable (6 scripts + module) | `scripts/`, `modules/` |
| Standards documentation | Complete | `standards/` |
| GitHub Actions | **None** | - |
| Bicep templates | **None** | - |
| Dev/test environment promotion | **None** | - |
| Managed endpoint live deployment | **Not yet** | - |
| Drift detection / monitoring | **Not yet** | - |
| Foundry project | **Not yet** | - |
| Prompt versioning | **Not yet** | - |
| GenAI evaluation datasets | **Not yet** | - |
| RBAC / private networking | **Not documented** | - |

### Key Files That Will Change

| File | Change Type |
|------|-------------|
| `claude-bricks-asbuilt.html` | Major rewrite: reframe from DP-100 to AI-300 |
| `claude-bricks-asbuilt-dev.html` | Same (dev copy for iterating) |
| `README.md` | Rewrite: AI-300 framing, Bicep as primary IaC |
| `explanation.md` | Rewrite or retire |
| `CLAUDE.md` | Update file conventions, add Bicep/GHA sections |
| `deploymentcode/scripts/00_bootstrap.py` | Refactor into asset registration scripts |
| `deploymentcode/scripts/scenario4/` | Add Foundry-native variant |
| `docs/index.html` | Regenerate after as-built rewrite |
| `.gitignore` | Add Bicep-related ignores |

### New Directories to Create

```
deploymentcode/bicep/              -- Bicep modules and parameter files
deploymentcode/bicep/modules/      -- Individual resource modules
.github/workflows/                 -- GitHub Actions CI/CD
prompts/                           -- Versioned prompt templates
prompts/system/                    -- System prompts (v1, v2, ...)
prompts/rag/                       -- RAG prompt templates
eval/                              -- Evaluation datasets and configs
eval/datasets/                     -- Test sets (JSONL)
eval/configs/                      -- Evaluation run configs
eval/results/                      -- Evaluation output (gitignored)
monitoring/                        -- Drift detection and alerting
monitoring/drift/                  -- Drift detection jobs
monitoring/dashboards/             -- KQL queries and dashboard definitions
runbooks/                          -- Operational runbooks
scripts/deploy/                    -- Azure CLI deployment wrappers
```

---

## Transformation Tiers

### Tier 1: Highest Value (do first)

These changes cover the most exam weight and close the biggest gaps.

| # | Change | AI-300 Domains Covered |
|---|--------|----------------------|
| 1 | Bicep + Azure CLI deployment path | 1.3, 3.1 |
| 2 | GitHub Actions workflows (infra, train, deploy, eval) | 1.3, 2.1, 2.3, 4.1 |
| 3 | Live managed online endpoints with safe rollout/rollback | 2.3 |
| 4 | Foundry-native Scenario 4 | 3.1, 3.2 |
| 5 | Formal GenAI evaluation dataset and quality gates | 4.1 |

### Tier 2: Strong Value

| # | Change | AI-300 Domains Covered |
|---|--------|----------------------|
| 6 | Observability dashboard (latency, tokens, cost, quality) | 4.2 |
| 7 | Prompt versioning and prompt experiments | 3.3 |
| 8 | Dev/test promotion flow | 1.3, 2.2, 2.3 |
| 9 | Drift detection + retraining trigger for Scenario 1 | 2.4 |

### Tier 3: Polish

| # | Change | AI-300 Domains Covered |
|---|--------|----------------------|
| 10 | Private networking + RBAC hardening | 1.1, 3.1 |
| 11 | AML registry and shared assets across workspaces | 1.2 |
| 12 | Advanced RAG tuning matrix | 5.1 |
| 13 | Agent-like validation/regeneration loop | 3.2, 4.1 |
| 14 | Advanced fine-tuning with synthetic data | 5.2 |
| 15 | Feedback loop implementation | 4.1, 4.2 |

---

## Change 1: Bicep + Azure CLI Deployment Path

**Priority**: Tier 1
**AI-300 Coverage**: Domain 1.3 (Implement IaC for ML), Domain 3.1 (Deploy infrastructure using Bicep)
**Detailed plan**: See `bicepdevplan.md`

### Summary

Create a complete Bicep IaC path parallel to the existing Terraform. Bicep becomes the **documented primary path**; Terraform becomes the "alternate implementation" kept for learning purposes.

### Deliverables

- `deploymentcode/bicep/main.bicep` -- orchestrator
- `deploymentcode/bicep/modules/*.bicep` -- 10+ resource modules
- `deploymentcode/bicep/parameters/dev.bicepparam` -- dev environment
- `deploymentcode/bicep/parameters/test.bicepparam` -- test environment
- `scripts/deploy/deploy-infra.sh` -- Azure CLI deployment wrapper (bash)
- `scripts/deploy/deploy-infra.ps1` -- Azure CLI deployment wrapper (PowerShell)
- `scripts/deploy/whatif.sh` -- what-if preview
- `scripts/deploy/teardown.sh` -- resource cleanup

### Key Design Decisions

1. **Module-per-resource pattern** matching current Terraform structure for easy mental mapping
2. **Parameter files per environment** (dev, test) enabling multi-environment promotion
3. **Conditional deployment flags** matching current Terraform feature flags (`deploy_openai`, `deploy_ai_search`, `deploy_custom_vision`)
4. **Azure CLI wrappers** that handle login, subscription selection, resource group creation, and Bicep deployment in one command
5. **What-if support** for safe preview before deployment

### Terraform Disposition

- Keep `deploymentcode/terraform/` as-is
- Keep `tf/` directory but add a README noting it is the legacy/alternate path
- Update all documentation to reference Bicep as primary
- Update CLAUDE.md to mention Bicep conventions

---

## Change 2: GitHub Actions Workflows

**Priority**: Tier 1
**AI-300 Coverage**: Domain 1.3 (Automate resource provisioning with GitHub Actions), Domain 2.1 (Implement training pipelines), Domain 2.3 (Deploy models), Domain 4.1 (Automated evaluation workflows)

### Workflow A: Infrastructure Deployment

**File**: `.github/workflows/infra.yml`

**Trigger**: Push to `deploymentcode/bicep/**` or manual dispatch

**Steps**:
1. Checkout code
2. Azure login via OIDC (federated identity, no secrets stored)
3. Bicep lint (`az bicep build`)
4. Bicep validate (`az deployment group validate`)
5. What-if preview (`az deployment group what-if`)
6. Deploy to dev (`az deployment group create` with dev parameters)
7. Manual approval gate (GitHub environment protection rule)
8. Deploy to test (with test parameters)

**Environment secrets**:
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` (OIDC)
- No client secrets -- managed identity / federated credential only

### Workflow B: ML Training Pipeline

**File**: `.github/workflows/train.yml`

**Trigger**: Push to `deploymentcode/scripts/scenario1/**` or `deploymentcode/scripts/scenario2/**` or `deploymentcode/scripts/scenario3/**`, or manual dispatch with scenario selector

**Steps**:
1. Checkout code
2. Azure login
3. Install Python dependencies
4. Submit AML training job via SDK
5. Wait for job completion (poll or use AML CLI)
6. Pull MLflow metrics from completed job
7. Compare metrics against threshold (accuracy >= 0.85, or scenario-specific)
8. Fail workflow if metrics below threshold
9. Register model if metrics pass
10. Post metrics as PR comment (if triggered by PR)

**Inputs** (for manual dispatch):
- Scenario (1, 2, or 3)
- Compute target override
- Experiment name override

### Workflow C: Model Deployment

**File**: `.github/workflows/deploy-model.yml`

**Trigger**: Manual dispatch only (requires approval)

**Steps**:
1. Checkout code
2. Azure login
3. Select model version from registry
4. Deploy as new deployment on existing endpoint (blue/green)
5. Run smoke test against new deployment
6. If smoke test passes: shift 10% traffic to new deployment
7. Wait for health check window (configurable, default 5 minutes)
8. If healthy: promote to 100% traffic
9. If unhealthy: rollback to previous deployment, fail workflow
10. Archive old deployment after successful cutover

**Inputs**:
- Model name and version
- Target endpoint name
- Initial traffic percentage (default 10)
- Health check duration (default 5m)

### Workflow D: GenAI Evaluation

**File**: `.github/workflows/eval-rag.yml`

**Trigger**: Push to `prompts/**`, `eval/**`, `deploymentcode/scripts/scenario4/**`, or manual dispatch

**Steps**:
1. Checkout code
2. Azure login
3. Load evaluation dataset from `eval/datasets/`
4. Run prompt/RAG test set against deployed model
5. Calculate quality metrics (groundedness, relevance, coherence, fluency)
6. Compare against baseline thresholds
7. Generate evaluation report
8. If any metric below threshold: fail workflow, block deployment
9. Store results in `eval/results/` (gitignored) and as workflow artifact
10. Post summary as PR comment (if triggered by PR)

**Thresholds** (configurable in `eval/configs/thresholds.json`):
```json
{
  "groundedness": 0.7,
  "relevance": 0.75,
  "coherence": 0.8,
  "fluency": 0.85,
  "safety_pass_rate": 1.0
}
```

### Workflow E: Drift Detection (Tier 2, added later)

**File**: `.github/workflows/drift-check.yml`

**Trigger**: Scheduled (weekly cron) or manual dispatch

**Steps**:
1. Azure login
2. Submit drift detection AML job
3. Pull drift metrics
4. If drift exceeds threshold: trigger `train.yml` workflow via repository dispatch
5. Post alert to configured channel

---

## Change 3: Live Managed Online Endpoints with Safe Rollout/Rollback

**Priority**: Tier 1
**AI-300 Coverage**: Domain 2.3 (Deploy models, progressive rollout, safe rollback)

### Current State

- `deploy_endpoint.py` exists for Scenarios 1 and 2 but endpoints are not yet serving live models
- Endpoint definitions exist but no blue/green or canary strategy

### Target State

For **Scenario 1** (Facade Classification) as the primary demonstration:

#### Endpoint Architecture

```
facade-classifier-endpoint
  |-- deployment-blue  (model v1, 100% traffic initially)
  |-- deployment-green (model v2, 0% traffic initially)
```

#### New/Modified Files

| File | Purpose |
|------|---------|
| `deploymentcode/scripts/scenario1/deploy_endpoint.py` | Refactor: create endpoint + initial deployment |
| `deploymentcode/scripts/scenario1/deploy_canary.py` | **New**: deploy new model version as canary |
| `deploymentcode/scripts/scenario1/promote_deployment.py` | **New**: shift traffic to new deployment |
| `deploymentcode/scripts/scenario1/rollback_deployment.py` | **New**: revert traffic to previous deployment |
| `deploymentcode/scripts/scenario1/smoke_test.py` | **New**: health check against endpoint |
| `runbooks/endpoint-deployment.md` | **New**: operational runbook |

#### Deployment Flow

1. `deploy_endpoint.py` -- create endpoint, deploy model-v1 as "blue" with 100% traffic
2. Train new model, register as model-v2
3. `deploy_canary.py` -- deploy model-v2 as "green" with 0% traffic
4. `promote_deployment.py --traffic 10` -- shift 10% to green
5. `smoke_test.py` -- validate green is healthy (latency, accuracy, error rate)
6. `promote_deployment.py --traffic 100` -- full cutover
7. If problems at any step: `rollback_deployment.py` -- revert to blue at 100%

#### Smoke Test Criteria

- Response latency < 2 seconds (p95)
- HTTP 200 success rate > 99%
- Prediction confidence > threshold for known test inputs
- Schema validation (response matches expected JSON structure)

#### Operational Runbook (`runbooks/endpoint-deployment.md`)

Sections:
1. Prerequisites (model registered, endpoint exists, permissions)
2. How to deploy a new model version
3. How to verify deployment health
4. How to promote traffic
5. How to rollback
6. Threshold definitions and what triggers rollback
7. Troubleshooting common failures (quota, image pull, scoring errors)

---

## Change 4: Foundry-Native Scenario 4

**Priority**: Tier 1
**AI-300 Coverage**: Domain 3.1 (Foundry environments), Domain 3.2 (Deploy foundation models)

### Current State

Scenario 4 uses:
- Azure OpenAI for LLM (fine-tuning + inference)
- AI Search for RAG retrieval
- Prompt Flow for orchestration (`flow.dag.yaml`, `retrieve.py`, `generate.py`)
- `evaluate_flow.py` for prompt strategy comparison

### Target State

Add a **Foundry-native variant** alongside the existing implementation.

#### New Directory Structure

```
deploymentcode/scripts/scenario4/
  |-- (existing files remain)
  |-- foundry/
  |   |-- create_project.py          -- Create Foundry hub + project
  |   |-- deploy_model.py            -- Deploy foundation model via Foundry
  |   |-- configure_index.py         -- Wire AI Search index to Foundry project
  |   |-- run_evaluation.py          -- Run Foundry evaluation pipeline
  |   |-- configure_monitoring.py    -- Set up Foundry continuous monitoring
  |   |-- trace_analysis.py          -- Analyze traces from Foundry tracing
```

#### What Changes

| Aspect | Current (OpenAI + Prompt Flow) | New (Foundry-native) |
|--------|-------------------------------|---------------------|
| Model deployment | Azure OpenAI resource directly | Foundry model catalog / serverless API |
| Orchestration | Prompt Flow DAG | Foundry SDK / project assets |
| Evaluation | `evaluate_flow.py` (custom) | Foundry built-in evaluators |
| Monitoring | Application Insights (manual) | Foundry continuous monitoring |
| Tracing | Not implemented | Foundry tracing (tool calls, latency, tokens) |

#### Foundry Hub/Project Provisioning

Add to Bicep modules:
- `deploymentcode/bicep/modules/foundry-hub.bicep` -- Foundry hub resource
- `deploymentcode/bicep/modules/foundry-project.bicep` -- Foundry project linked to hub

Wire into `main.bicep` with conditional deployment flag (`deploy_foundry`).

#### Scenario 4 Flow (Foundry version)

1. User provides LEGO building description
2. Retrieve relevant reference content from AI Search index
3. LLM generates building specification via Foundry-managed deployment
4. Foundry tracing captures: prompt version, retrieval latency, generation latency, token counts
5. Foundry evaluation pipeline scores output (groundedness, relevance, coherence)
6. Foundry monitoring dashboard tracks metrics over time

---

## Change 5: Formal GenAI Evaluation Dataset and Quality Gates

**Priority**: Tier 1
**AI-300 Coverage**: Domain 4.1 (Test datasets, quality metrics, safety evaluation, automated workflows)

### Evaluation Dataset

**File**: `eval/datasets/lego-spec-generator.jsonl`

Each row contains:
```json
{
  "id": "eval-001",
  "prompt": "Generate a building specification for a 2-story corner bakery with Art Deco styling",
  "context_docs": ["reference/corner-bakery-patterns.md"],
  "expected_traits": {
    "has_dimensions": true,
    "has_color_palette": true,
    "has_brick_references": true,
    "has_floor_plan": true,
    "style_matches": "Art Deco",
    "story_count": 2,
    "building_type": "commercial"
  },
  "golden_answer_keywords": ["arch", "pilaster", "geometric", "facade", "storefront"],
  "known_bad_patterns": ["impossible cantilever", "unsupported overhang > 2 studs"],
  "difficulty": "medium"
}
```

**Target**: 30-50 evaluation rows covering:
- Different building types (residential, commercial, mixed-use)
- Different architectural styles (Victorian, Art Deco, Modern, Georgian, Parisian)
- Different complexity levels (simple 1-story to complex 3-story)
- Edge cases (unusual dimensions, conflicting requirements)
- Known failure modes (structurally impossible requests)

### Quality Metrics

| Metric | Description | Threshold | Source |
|--------|-------------|-----------|--------|
| Groundedness | Output grounded in retrieved context | >= 0.70 | Foundry evaluator |
| Relevance | Output addresses the prompt | >= 0.75 | Foundry evaluator |
| Coherence | Output is internally consistent | >= 0.80 | Foundry evaluator |
| Fluency | Output is well-written | >= 0.85 | Foundry evaluator |
| Safety | No harmful content | 100% pass | Foundry safety evaluator |
| Buildability | Domain-specific: can the spec be built? | >= 0.70 | Custom evaluator |

### Custom "Buildability" Evaluator

**File**: `eval/evaluators/buildability.py`

Checks:
1. Does the output include physical dimensions (width, depth, height)?
2. Does it reference plausible brick/part names or categories?
3. Does it specify a color palette?
4. Are structural elements physically possible (no floating elements, reasonable cantilevers)?
5. Does the generated spec (if .ldr) parse cleanly?
6. Are referenced part numbers valid (cross-check against `standards/parts-catalog.md`)?

### Evaluation Pipeline

**File**: `eval/run_evaluation.py`

Steps:
1. Load test dataset from `eval/datasets/`
2. For each test case:
   a. Format prompt with system prompt version
   b. Retrieve context from AI Search
   c. Generate response via Foundry deployment
   d. Score with built-in metrics (groundedness, relevance, coherence, fluency)
   e. Score with safety evaluator
   f. Score with custom buildability evaluator
3. Aggregate results
4. Compare against thresholds in `eval/configs/thresholds.json`
5. Output report to `eval/results/` and stdout
6. Exit with non-zero code if any metric below threshold (for CI/CD gating)

### Automated Quality Gate

Integrated into `.github/workflows/eval-rag.yml` (see Change 2, Workflow D).

Any push to `prompts/**` or `eval/**` triggers evaluation. Deployment is blocked if metrics fall below thresholds.

---

## Change 6: Observability Dashboard

**Priority**: Tier 2
**AI-300 Coverage**: Domain 4.2 (Monitor performance, track cost, configure logging/tracing)

### What to Capture (Scenario 4 GenAI path)

| Metric | Source | Storage |
|--------|--------|---------|
| Prompt version | Application code | App Insights custom dimensions |
| Model name/version | Foundry deployment | App Insights custom dimensions |
| Retrieval latency (ms) | AI Search call timing | App Insights dependency tracking |
| Generation latency (ms) | LLM call timing | App Insights dependency tracking |
| Total response latency (ms) | End-to-end | App Insights request tracking |
| Input token count | LLM response metadata | App Insights custom metrics |
| Output token count | LLM response metadata | App Insights custom metrics |
| Estimated cost ($) | Token counts * pricing | App Insights custom metrics |
| Evaluation score | Evaluation pipeline | App Insights custom metrics |
| Trace ID | Foundry tracing | Foundry + App Insights |
| Error type/reason | Exception handling | App Insights exceptions |

### Implementation

#### Telemetry Client

**File**: `deploymentcode/scripts/common/telemetry.py`

```python
# Wraps Application Insights SDK
# Provides: track_request, track_dependency, track_metric, track_exception
# Auto-attaches: prompt_version, model_version, trace_id as custom dimensions
```

#### Instrument Scenario 4

Modify these files to emit telemetry:
- `scenario4/foundry/deploy_model.py` -- track model deployment events
- `scenario4/promptflow/retrieve.py` -- track retrieval latency
- `scenario4/promptflow/generate.py` -- track generation latency, tokens, cost
- `scenario4/evaluate_flow.py` -- track evaluation scores

#### KQL Queries

**Directory**: `monitoring/dashboards/`

| File | Purpose |
|------|---------|
| `avg-latency-by-prompt.kql` | Average latency grouped by prompt version |
| `token-cost-by-day.kql` | Daily token consumption and estimated cost |
| `groundedness-pass-rate.kql` | Evaluation pass rate over time |
| `error-rate-trend.kql` | Error rate by day, grouped by error type |
| `top-failure-modes.kql` | Top 10 failure reasons by frequency |

#### Dashboard

Azure Workbook or Grafana dashboard JSON exported to `monitoring/dashboards/genai-ops.json`.

Shows:
- Average latency by prompt version (line chart)
- Token cost by day (bar chart)
- Groundedness pass rate (gauge)
- Error rate trend (line chart)
- Top failure modes (table)

---

## Change 7: Prompt Versioning and Experiments

**Priority**: Tier 2
**AI-300 Coverage**: Domain 3.3 (Design prompts, create variants, compare performance, version in Git)

### Directory Structure

```
prompts/
  |-- system/
  |   |-- v1.txt       -- Original system prompt
  |   |-- v2.txt       -- Refined system prompt (more structured output)
  |   |-- v3.txt       -- Concise system prompt (fewer tokens)
  |-- rag/
  |   |-- v1.jinja2    -- Original RAG template
  |   |-- v2.jinja2    -- Template with explicit grounding instructions
  |-- few-shot/
  |   |-- v1.jsonl     -- Few-shot examples set A
  |   |-- v2.jsonl     -- Few-shot examples set B (more diverse)
  |-- CHANGELOG.md     -- Prompt version history with rationale for each change
```

### Prompt Experiment Runner

**File**: `eval/run_prompt_experiment.py`

**Inputs**:
- System prompt version(s) to test
- RAG template version(s) to test
- Evaluation dataset
- Model deployment name

**Outputs**:
- Per-version scores (all quality metrics)
- Side-by-side comparison table
- Statistical significance indicator (if sample size sufficient)
- Winner recommendation

**Example invocation**:
```bash
python eval/run_prompt_experiment.py \
  --system-prompts v1,v2,v3 \
  --rag-templates v1,v2 \
  --dataset eval/datasets/lego-spec-generator.jsonl \
  --output eval/results/experiment-2026-03-10.json
```

This creates a matrix of 6 combinations (3 system x 2 RAG) and evaluates each.

### What to Measure Per Combination

- Groundedness, relevance, coherence, fluency (Foundry evaluators)
- Buildability (custom evaluator)
- Average token consumption (input + output)
- Average latency
- Estimated cost per request

---

## Change 8: Dev/Test Promotion Flow

**Priority**: Tier 2
**AI-300 Coverage**: Domain 1.3 (repeatable environments), Domain 2.2 (model lifecycle), Domain 2.3 (production deployment)

### Current State

Single resource group, single workspace, lab-style deployment.

### Target State

| Environment | Resource Group | AML Workspace | Purpose |
|-------------|---------------|---------------|---------|
| dev | `rg-claudebricks-dev` | `mlw-claudebricks-dev` | Experimentation, training |
| test | `rg-claudebricks-test` | `mlw-claudebricks-test` | Validation, pre-prod |
| (optional) prod | `rg-claudebricks-prod` | `mlw-claudebricks-prod` | Production serving |

### Shared AML Registry

**Name**: `reg-claudebricks`

Purpose: Share models, environments, and components across dev/test/prod workspaces without re-registering.

**Provisioned via Bicep**: `deploymentcode/bicep/modules/aml-registry.bicep`

### Promotion Flow

```
dev workspace                    test workspace
  |                                |
  Train model                      |
  |                                |
  Register in dev                  |
  |                                |
  Publish to shared registry  --> Import from registry
  |                                |
  [GitHub Actions gate]            Deploy to test endpoint
  |                                |
                                   Run smoke tests
                                   |
                                   Run evaluation suite
                                   |
                                   [Manual approval gate]
                                   |
                                   Promote to prod (if applicable)
```

### New Scripts

| File | Purpose |
|------|---------|
| `deploymentcode/scripts/publish_to_registry.py` | Publish model + environment to shared registry |
| `deploymentcode/scripts/import_from_registry.py` | Import assets from registry into target workspace |
| `deploymentcode/scripts/promote_model.py` | Orchestrate promotion: publish, import, deploy, test |

### Bicep Parameter Differences

| Parameter | dev | test |
|-----------|-----|------|
| `sku` | Basic | Basic |
| `compute_instance_size` | Standard_DS2_v2 | (none) |
| `cpu_cluster_max_nodes` | 2 | 4 |
| `gpu_cluster_max_nodes` | 1 | 0 |
| `deploy_openai` | true | true |
| `deploy_ai_search` | true | true |
| `public_network_access` | Enabled | Disabled |

---

## Change 9: Drift Detection and Retraining Triggers

**Priority**: Tier 2
**AI-300 Coverage**: Domain 2.4 (Detect drift, monitor performance, configure retraining triggers)

### Target Scenario

**Scenario 1: Facade Classification** -- chosen because it has the clearest feature distribution to monitor.

### Implementation

#### Baseline Dataset Profile

**File**: `monitoring/drift/create_baseline.py`

- After initial training, capture feature distributions of training data
- Store as baseline profile in AML data asset (versioned)
- Features to profile: pixel intensity distributions, image dimensions, class balance

#### Inference Capture

**File**: `deploymentcode/scripts/scenario1/score.py` (modify)

- On each inference request, log:
  - Input features (or feature hash)
  - Prediction
  - Confidence score
  - Timestamp
- Store in Blob container `inference-logs/scenario1/`

#### Drift Detection Job

**File**: `monitoring/drift/detect_drift.py`

- AML scheduled job (daily or weekly)
- Compare recent inference feature distributions against baseline
- Calculate drift metrics:
  - Population Stability Index (PSI) per feature
  - Kolmogorov-Smirnov test statistic
  - Jensen-Shannon divergence
- Log metrics to MLflow experiment `drift-monitoring-scenario1`
- Post custom metric to Application Insights

#### Alert and Retrain Trigger

**File**: `monitoring/drift/alert_config.py`

Thresholds:
- PSI > 0.2 on any feature: warning alert
- PSI > 0.4 on any feature: critical alert, trigger retraining
- Accuracy on labeled holdout < 0.80: trigger retraining

Action on critical alert:
- Post to Application Insights
- Trigger GitHub Actions `train.yml` via repository dispatch event

#### Retraining Flow

```
Drift detected (PSI > 0.4)
  |
  GitHub Actions repository_dispatch event
  |
  train.yml workflow runs
  |
  New model trained on updated data
  |
  Metrics compared against previous model
  |
  If improved: register new version
  |
  deploy-model.yml triggered for canary deployment
```

---

## Change 10: Private Networking and RBAC Hardening

**Priority**: Tier 3
**AI-300 Coverage**: Domain 1.1 (identity and access), Domain 3.1 (network security, private networking, RBAC)

### RBAC Role Assignments (in Bicep)

| Principal | Role | Scope |
|-----------|------|-------|
| GitHub Actions SP (OIDC) | Contributor | Resource group |
| GitHub Actions SP (OIDC) | AzureML Data Scientist | AML workspace |
| AML workspace managed identity | Storage Blob Data Contributor | Storage account |
| AML workspace managed identity | Key Vault Secrets User | Key Vault |
| AML workspace managed identity | AcrPull | ACR |
| AML compute managed identity | Storage Blob Data Reader | Storage account |
| Foundry project managed identity | Cognitive Services OpenAI User | OpenAI resource |
| Foundry project managed identity | Search Index Data Reader | AI Search |

**Implementation**: Add `roleAssignments` array to each Bicep module or create a dedicated `deploymentcode/bicep/modules/rbac.bicep`.

### Managed Identities

| Resource | Identity Type | Used For |
|----------|--------------|----------|
| AML workspace | System-assigned | Access storage, KV, ACR |
| AML compute cluster | System-assigned | Access storage during training |
| Managed endpoint | System-assigned | Access model artifacts, KV secrets |
| Foundry project | System-assigned | Access OpenAI, AI Search |
| GitHub Actions | Federated (OIDC) | Deploy infrastructure and submit jobs |

### Private Networking (test/prod only)

| Resource | Private Endpoint | DNS Zone |
|----------|-----------------|----------|
| Storage account | Yes | `privatelink.blob.core.windows.net` |
| Key Vault | Yes | `privatelink.vaultcore.azure.net` |
| AML workspace | Yes | `privatelink.api.azureml.ms` |
| ACR | Yes | `privatelink.azurecr.io` |
| AI Search | Yes | `privatelink.search.windows.net` |
| OpenAI / Foundry | Yes | `privatelink.openai.azure.com` |

**Implementation**: Add private endpoint modules to Bicep, conditional on environment (disabled for dev, enabled for test/prod).

### Bicep Module

**File**: `deploymentcode/bicep/modules/private-endpoint.bicep`

Generic module that takes:
- Target resource ID
- Subnet ID
- Group ID (e.g., `blob`, `vault`, `amlworkspace`)
- Private DNS zone ID

---

## Change 11: AML Registry and Shared Assets

**Priority**: Tier 3
**AI-300 Coverage**: Domain 1.2 (Share assets across workspaces using registries)

### Registry Contents

| Asset Type | Example | Versioning |
|------------|---------|-----------|
| Model | `facade-classifier:1.0.0` | Semantic versioning |
| Environment | `claudebricks-sklearn:1.2` | Major.minor |
| Component | `prepare-data:1.0` | Major.minor |
| Data asset | `facade-images:2` | Integer version |

### Scripts

| File | Purpose |
|------|---------|
| `deploymentcode/scripts/register_components.py` | Register pipeline components to workspace |
| `deploymentcode/scripts/register_envs.py` | Register environments to workspace |
| `deploymentcode/scripts/register_data_assets.py` | Register data assets to workspace |
| `deploymentcode/scripts/publish_to_registry.py` | Publish assets from workspace to shared registry |

### Lifecycle Rules

- Models: archive after 3 newer versions registered (keep metadata, remove artifacts)
- Environments: archive when no active deployments reference them
- Components: archive when replaced by newer major version
- Document archival policy in `runbooks/asset-lifecycle.md`

---

## Change 12: Advanced RAG Tuning Matrix

**Priority**: Tier 3
**AI-300 Coverage**: Domain 5.1 (Optimize RAG: similarity thresholds, chunk sizes, retrieval strategies, embedding models, hybrid search, A/B testing)

### Tuning Parameters

| Parameter | Values to Test |
|-----------|---------------|
| Chunk size | 300, 600, 1000 tokens |
| Chunk overlap | 0, 50, 100 tokens |
| Search mode | vector, hybrid, keyword+semantic |
| Top-k results | 3, 5, 8 |
| Embedding model | text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large |
| Similarity threshold | 0.5, 0.7, 0.85 |

### Implementation

**File**: `eval/run_rag_tuning.py`

1. For each combination in the matrix (or a subset):
   a. Configure AI Search index with chunk size/overlap
   b. Re-index reference content with selected embedding model
   c. Run evaluation dataset through RAG pipeline
   d. Measure: groundedness, relevance, latency, token cost
2. Output comparison table to `eval/results/rag-tuning-matrix.json`
3. Identify Pareto-optimal configurations (best quality vs. cost tradeoff)

### Practical Scope

Full matrix is 3 x 3 x 3 x 3 x 3 x 3 = 729 combinations. Not practical.

Recommended approach:
1. Fix embedding model, test chunk size x overlap x search mode (27 runs)
2. Take best config, test embedding models (3 runs)
3. Take best config, test top-k x similarity threshold (9 runs)
4. Total: ~39 evaluation runs

---

## Change 13: Agent-Like Validation/Regeneration Loop

**Priority**: Tier 3
**AI-300 Coverage**: Domain 3.2 (model deployment strategies), Domain 4.1 (evaluation)

### Flow

```
User prompt
  |
  v
Retrieve examples from AI Search
  |
  v
Generate spec via Foundry LLM
  |
  v
Validate spec (rules-based)
  |-- PASS --> Return to user
  |-- FAIL --> Extract failure reasons
                |
                v
              Regenerate with corrective prompt
                (include failure reasons + original prompt)
                |
                v
              Validate again
                |-- PASS --> Return to user
                |-- FAIL --> Return with warnings
                             (max 2 retries)
```

### Implementation

**File**: `deploymentcode/scripts/scenario4/foundry/agent_loop.py`

- Max retries: 2 (3 total attempts)
- Each attempt logged with: attempt number, prompt used, validation result, latency, tokens
- All attempts stored for evaluation analysis
- Foundry tracing captures full chain

### Validation Rules

1. Output contains dimensions (width, depth, height)
2. Referenced parts exist in `standards/parts-catalog.md`
3. Color codes are valid LDraw colors
4. No structural impossibilities (floating unsupported elements)
5. Output follows expected format (sections for dimensions, palette, features, construction notes)

---

## Change 14: Advanced Fine-Tuning with Synthetic Data

**Priority**: Tier 3
**AI-300 Coverage**: Domain 5.2 (Advanced fine-tuning, synthetic data, monitor fine-tuned model, manage through production)

### Synthetic Data Generation

**File**: `deploymentcode/scripts/scenario4/generate_synthetic_data.py`

Use a strong base model to generate training examples:
1. Generate diverse building prompts programmatically (vary style, size, features)
2. For each prompt, generate a high-quality spec using GPT-4 with detailed system prompt
3. Validate generated specs against rules
4. Filter to only high-quality examples
5. Format as JSONL for fine-tuning

**Target**: 200-500 synthetic training examples

### Fine-Tuning Pipeline

```
Generate synthetic data
  |
  v
Quality filter (rules + LLM-as-judge)
  |
  v
Format as training JSONL
  |
  v
Upload to Azure OpenAI
  |
  v
Submit fine-tuning job
  |
  v
Evaluate fine-tuned model against base model
  |
  v
If improved: register and deploy
If worse: analyze failure modes, iterate on data
```

### Monitoring Fine-Tuned Model

- Track: training loss curve, validation loss, evaluation metrics post-training
- Compare against base model on same evaluation dataset
- Monitor production performance (latency, quality, cost) after deployment
- Set retraining trigger if quality degrades below threshold

---

## Change 15: Feedback Loop Implementation

**Priority**: Tier 3
**AI-300 Coverage**: Domain 4.1 (evaluation), Domain 4.2 (monitoring)

### Current State

Feedback loop is **planned** in the as-built but not implemented.

### Implementation

**File**: `deploymentcode/scripts/scenario4/foundry/feedback_loop.py`

1. Generate spec from user prompt
2. Run rules-based validator
3. Run LLM-as-judge evaluator (Foundry or custom)
4. If fail:
   a. Extract specific failure reasons
   b. Construct corrective prompt (original prompt + failure reasons + "fix these issues")
   c. Regenerate
   d. Re-evaluate
5. Store both attempts and results in structured log
6. Trend failure causes over time (weekly aggregation job)

### Failure Cause Taxonomy

| Category | Examples |
|----------|---------|
| Missing dimensions | No width/depth/height specified |
| Invalid parts | Referenced non-existent brick types |
| Structural issues | Floating elements, impossible overhangs |
| Style mismatch | Requested Victorian, got Modern |
| Format violations | Missing required sections |
| Safety | Inappropriate content |

### Trending Job

**File**: `monitoring/feedback/trend_failures.py`

- Weekly scheduled job
- Aggregates failure causes from log
- Posts summary to Application Insights
- Surfaces top 5 recurring issues
- Informs prompt iteration (if "missing dimensions" is #1 failure, update system prompt to emphasize dimensions)

---

## As-Built HTML Transformation

The as-built document needs a comprehensive rewrite to reframe from DP-100 to AI-300. This is a separate work item that should happen **after** the code changes are implemented.

### Sections to Rewrite

| Current Section | AI-300 Version |
|----------------|----------------|
| "What is Claude.Bricks" (DP-100 framing) | Reframe around AI-300 domains and operational platform |
| "DP-100 Domain Coverage" | Replace with AI-300 domain coverage mapping |
| Architecture Overview | Add Foundry, Bicep, GitHub Actions, dev/test/prod |
| Deployment Phases | Rewrite: Bicep as primary, add promotion flow |
| Phase 1: Terraform | Phase 1: Bicep (Terraform as alternate) |
| Phase 2: Bootstrap | Phase 2: Asset Registration (components, environments, data assets) |
| Scenarios 1-3 | Add endpoint deployment, drift monitoring, retraining |
| Scenario 4 | Add Foundry variant, evaluation, observability |
| Data Flow | Add evaluation and monitoring feedback loops |
| Cost Breakdown | Update for Foundry, additional environments |
| New: GitHub Actions CI/CD | Document all workflows |
| New: Prompt Engineering | Versioning, experiments, results |
| New: Evaluation and Quality Gates | Datasets, metrics, automation |
| New: Observability | Dashboard, tracing, cost tracking |
| New: Security and Networking | RBAC, managed identities, private endpoints |

### New Visuals Needed

| Visual | Type | Content |
|--------|------|---------|
| AI-300 Domain Coverage | Grid/tracker | Map repo features to exam domains |
| Bicep Module Dependency Graph | Flow diagram | Module relationships |
| GitHub Actions Pipeline Flow | Pipeline diagram | All 4-5 workflows |
| Dev/Test Promotion Flow | Flow diagram | Environment promotion |
| Endpoint Rollout Strategy | Sequence diagram | Blue/green deployment |
| Drift Detection Flow | Flow diagram | Monitor -> detect -> retrain |
| Foundry Architecture | Architecture diagram | Hub/project/model/evaluation |
| RAG Pipeline with Evaluation | Flow diagram | Retrieve -> generate -> evaluate |
| Observability Dashboard Mockup | Dashboard layout | Metrics and charts |

---

## README.md Transformation

### Current Structure (DP-100 focused)

- Why This Exists (DP-100 study group)
- Azure ML Infrastructure (4 scenarios)
- LEGO Design Workflow
- Repository Structure

### New Structure (AI-300 focused)

1. **What is Claude.Bricks** -- AI-300 operations platform + LEGO design system
2. **AI-300 Exam Coverage** -- domain mapping table
3. **Architecture** -- Bicep-provisioned, multi-environment, with Foundry
4. **Quick Start**
   a. Deploy infrastructure (Bicep + Azure CLI)
   b. Register assets
   c. Run training scenario
   d. Deploy model with safe rollout
   e. Run GenAI evaluation
5. **CI/CD with GitHub Actions** -- workflow descriptions
6. **ML Scenarios** (1-3) -- with operational lifecycle
7. **GenAI Scenario** (4) -- Foundry-native with evaluation
8. **LEGO Design System** -- (keep, it is the domain)
9. **Repository Structure** -- updated tree
10. **Full Documentation** -- link to as-built

---

## CLAUDE.md Updates

### Add Sections

- Bicep file conventions (`deploymentcode/bicep/`)
- GitHub Actions conventions (`.github/workflows/`)
- Prompt file conventions (`prompts/`)
- Evaluation file conventions (`eval/`)
- Monitoring file conventions (`monitoring/`)

### Update Sections

- File Conventions: add new directories
- PowerShell Generation Strategy: no changes (LEGO side untouched)

---

## Implementation Order

### Phase 1: Infrastructure Foundation (Tier 1, items 1-2)

1. Write all Bicep modules and parameter files
2. Write Azure CLI deployment wrapper scripts
3. Create GitHub Actions infrastructure workflow
4. Test: deploy dev environment via Bicep
5. Create GitHub Actions training workflow (Scenario 1)
6. Create GitHub Actions deployment workflow
7. Create GitHub Actions evaluation workflow

### Phase 2: ML Operations (Tier 1, items 3 + Tier 2, items 8-9)

8. Implement live endpoint deployment for Scenario 1
9. Implement blue/green deployment scripts
10. Implement smoke tests
11. Write endpoint deployment runbook
12. Implement dev/test promotion flow
13. Implement drift detection for Scenario 1
14. Connect drift alerts to retraining workflow

### Phase 3: GenAI Operations (Tier 1, items 4-5 + Tier 2, items 6-7)

15. Create Foundry hub/project via Bicep
16. Implement Foundry-native Scenario 4
17. Create evaluation dataset (30-50 rows)
18. Implement evaluation pipeline with quality gates
19. Implement prompt versioning structure
20. Implement prompt experiment runner
21. Implement observability telemetry
22. Create KQL queries and dashboard

### Phase 4: Hardening and Polish (Tier 3, items 10-15)

23. Add RBAC role assignments to Bicep
24. Add managed identity configuration
25. Add private endpoint modules (conditional)
26. Implement AML registry and asset sharing
27. Implement RAG tuning matrix
28. Implement agent validation loop
29. Implement synthetic data generation
30. Implement feedback loop

### Phase 5: Documentation

31. Rewrite as-built HTML for AI-300
32. Create new visuals (v2 HTML/CSS style)
33. Rewrite README.md
34. Update CLAUDE.md
35. Update `docs/index.html` for GitHub Pages

---

## File Inventory: All New Files

### Bicep (see bicepdevplan.md for details)
```
deploymentcode/bicep/main.bicep
deploymentcode/bicep/modules/resource-group.bicep
deploymentcode/bicep/modules/storage.bicep
deploymentcode/bicep/modules/keyvault.bicep
deploymentcode/bicep/modules/acr.bicep
deploymentcode/bicep/modules/log-analytics.bicep
deploymentcode/bicep/modules/app-insights.bicep
deploymentcode/bicep/modules/aml-workspace.bicep
deploymentcode/bicep/modules/aml-compute.bicep
deploymentcode/bicep/modules/cognitive-services.bicep
deploymentcode/bicep/modules/search.bicep
deploymentcode/bicep/modules/foundry-hub.bicep
deploymentcode/bicep/modules/foundry-project.bicep
deploymentcode/bicep/modules/aml-registry.bicep
deploymentcode/bicep/modules/private-endpoint.bicep
deploymentcode/bicep/modules/rbac.bicep
deploymentcode/bicep/parameters/dev.bicepparam
deploymentcode/bicep/parameters/test.bicepparam
```

### GitHub Actions
```
.github/workflows/infra.yml
.github/workflows/train.yml
.github/workflows/deploy-model.yml
.github/workflows/eval-rag.yml
.github/workflows/drift-check.yml
```

### Deployment Scripts
```
scripts/deploy/deploy-infra.sh
scripts/deploy/deploy-infra.ps1
scripts/deploy/whatif.sh
scripts/deploy/teardown.sh
```

### Asset Registration
```
deploymentcode/scripts/register_data_assets.py
deploymentcode/scripts/register_components.py
deploymentcode/scripts/register_envs.py
deploymentcode/scripts/publish_to_registry.py
deploymentcode/scripts/import_from_registry.py
deploymentcode/scripts/promote_model.py
```

### Foundry (Scenario 4)
```
deploymentcode/scripts/scenario4/foundry/create_project.py
deploymentcode/scripts/scenario4/foundry/deploy_model.py
deploymentcode/scripts/scenario4/foundry/configure_index.py
deploymentcode/scripts/scenario4/foundry/run_evaluation.py
deploymentcode/scripts/scenario4/foundry/configure_monitoring.py
deploymentcode/scripts/scenario4/foundry/trace_analysis.py
deploymentcode/scripts/scenario4/foundry/agent_loop.py
deploymentcode/scripts/scenario4/foundry/feedback_loop.py
deploymentcode/scripts/scenario4/generate_synthetic_data.py
```

### Endpoint Operations
```
deploymentcode/scripts/scenario1/deploy_canary.py
deploymentcode/scripts/scenario1/promote_deployment.py
deploymentcode/scripts/scenario1/rollback_deployment.py
deploymentcode/scripts/scenario1/smoke_test.py
```

### Prompts
```
prompts/system/v1.txt
prompts/system/v2.txt
prompts/rag/v1.jinja2
prompts/rag/v2.jinja2
prompts/few-shot/v1.jsonl
prompts/few-shot/v2.jsonl
prompts/CHANGELOG.md
```

### Evaluation
```
eval/datasets/lego-spec-generator.jsonl
eval/configs/thresholds.json
eval/evaluators/buildability.py
eval/run_evaluation.py
eval/run_prompt_experiment.py
eval/run_rag_tuning.py
```

### Monitoring
```
monitoring/drift/create_baseline.py
monitoring/drift/detect_drift.py
monitoring/drift/alert_config.py
monitoring/feedback/trend_failures.py
monitoring/dashboards/avg-latency-by-prompt.kql
monitoring/dashboards/token-cost-by-day.kql
monitoring/dashboards/groundedness-pass-rate.kql
monitoring/dashboards/error-rate-trend.kql
monitoring/dashboards/top-failure-modes.kql
monitoring/dashboards/genai-ops.json
```

### Runbooks
```
runbooks/endpoint-deployment.md
runbooks/asset-lifecycle.md
```

### Telemetry
```
deploymentcode/scripts/common/telemetry.py
```

---

## Risk and Scope Notes

### Scope Control
- The LEGO generation side (PowerShell scripts, LDraw module, standards) is **untouched** by this transformation. It remains the domain that makes Claude.Bricks unique.
- Terraform is preserved as alternate IaC, not deleted.
- Existing Python scripts in `deploymentcode/scripts/` are extended, not rewritten from scratch.

### Potential Risks
- **Foundry API stability**: Microsoft Foundry is evolving rapidly. API surface may change before AI-300 goes live.
- **Cost**: Running dev + test environments doubles Azure spend. Use dev primarily; deploy test only when validating promotion flow.
- **Complexity creep**: Not everything in Tier 3 needs to be implemented. Tiers 1 and 2 provide strong AI-300 coverage on their own.

### Definition of Done (per change)
1. Code written and committed
2. Script tested (runs without errors)
3. Output validated (resources deploy, pipelines run, metrics generated)
4. As-built section written or updated
5. README updated if externally visible
