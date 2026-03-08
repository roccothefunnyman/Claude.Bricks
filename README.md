<div align="center">

# Claude.Bricks

**AI-Assisted Modular LEGO Design + Azure ML Infrastructure**

[![As-Built Docs](https://img.shields.io/badge/As--Built_Docs-Live-0078d4?style=for-the-badge&logo=microsoft-azure&logoColor=white)](https://roccothefunnyman.github.io/Claude.Bricks/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7b42bc?style=for-the-badge&logo=terraform&logoColor=white)](#azure-ml-infrastructure)
[![Azure ML](https://img.shields.io/badge/Azure_ML-SDK_v2-0078d4?style=for-the-badge&logo=microsoft-azure&logoColor=white)](#4-ml-scenarios)
[![LDraw](https://img.shields.io/badge/LDraw-BrickLink_Studio-e74c3c?style=for-the-badge)](#lego-design-workflow)

---

*A Claude Code-powered workflow for designing modular LEGO buildings, backed by an Azure ML platform for facade classification, structural validation, pattern extraction, and LLM-powered spec generation.*

</div>

---

## Azure ML Infrastructure

> **[View the full interactive As-Built Document](https://roccothefunnyman.github.io/Claude.Bricks/)** - complete with deployment phases, Terraform dependency graphs, scenario pipeline diagrams, data flow maps, and cost breakdowns.

All infrastructure is deployed via a single `terraform apply` into one Azure Resource Group, with 4 independent ML scenarios powered by Azure ML SDK v2.

<div align="center">

![Claude.Bricks - Complete Resource Map](docs/resource-map.svg)

</div>

### 4 ML Scenarios

| # | Scenario | Technique | Compute | Key Services |
|---|----------|-----------|---------|-------------|
| **1** | Facade Style Classification | Random Forest on rendered images | CPU + GPU Cluster | Custom Vision, Managed Endpoint |
| **2** | Structural Validation | Isolation Forest (anomaly detection) on .ldr features | CPU Cluster | MLflow, Online Endpoint |
| **3** | Pattern Extraction | KMeans / HDBSCAN clustering via `@dsl.pipeline` | CPU Cluster | Pipeline Jobs, MLflow |
| **4** | LLM Spec Generator | RAG with AI Search + Azure OpenAI + Prompt Flow | GPU Cluster | AI Search, OpenAI, Fine-tuning |

### Deployment Phases

```
Phase 1          Phase 2         Phase 3-6
Terraform   -->  Bootstrap  -->  ML Scenarios (independent, any order)
5-15 min         ~2 min          ~30-45 min each

15 Azure         Compute,        Train, evaluate, deploy,
resources        datastores,     score - per scenario
provisioned      environments
```

---

## LEGO Design Workflow

A Claude Code-powered workflow for designing modular LEGO buildings. You describe what you want, Claude generates a PowerShell script, the script outputs an LDraw (.ldr) file, and you open it in BrickLink Studio (stud.io) to view, render, and refine.

### Prerequisites

- **BrickLink Studio** (stud.io) - [Download here](https://www.bricklink.com/v3/studio/download.page) - for viewing and rendering .ldr files
- **PowerShell 5.1+** - included with Windows 10/11
- **Claude Code CLI** - for AI-assisted design sessions

### Quick Start

1. Open a terminal in this folder
2. Run `claude`
3. Describe the building you want:
   > "Design a 2-story Victorian townhouse, 32x16 studs, dark red and tan with white trim"
4. Claude generates a PowerShell script in `scripts/`
5. The script runs and produces an .ldr file in `output/`
6. Open the .ldr file in BrickLink Studio

### Why PowerShell Scripts?

A detailed LEGO building can be 1,000-3,000+ lines of LDraw code. Writing that directly would exceed Claude's output token limit. Instead, Claude writes a compact PowerShell script (~300-600 lines) with helper functions that procedurally generate the full .ldr file.

### Multi-Agent Workflow

For complex buildings, Claude spawns a team of specialized agents:

| Agent | Role | When Used |
|-------|------|-----------|
| **Reference Analyzer** | One agent per .ldr file, all in parallel. Reads in chunks, extracts patterns, returns structured summary. | When you provide reference files |
| **Architect** | Designs building layout, dimensions, openings, colors | Every new building |
| **Script Writer** | Writes the PowerShell generation script | After design is approved |
| **Validator** | Checks the output .ldr for structural errors | After generation |

---

## Repository Structure

```
Claude.Bricks/
├── CLAUDE.md                 # Claude Code session context
├── README.md                 # This file
├── docs/
│   └── index.html            # As-Built document (GitHub Pages)
├── deploymentcode/           # Azure ML deployment scripts
│   ├── infrastructure/       # Terraform configs
│   ├── bootstrap/            # Post-Terraform setup (SDK v2)
│   ├── scenarios/            # ML scenario implementations (1-4)
│   └── data/                 # Training data per scenario
├── standards/                # LDraw format and building conventions
│   ├── ldraw-format.md
│   ├── modular-building-spec.md
│   ├── parts-catalog.md
│   ├── color-palette.md
│   └── architectural-patterns.md
├── scripts/                  # PowerShell LEGO generation scripts
├── output/                   # Generated .ldr files
├── reference/                # Reference .ldr files for analysis
├── modules/                  # Shared PowerShell module (LDraw.psm1)
└── azure-icons/              # Azure SVG icons for documentation
```

## Adding Reference Files

Drop any well-built .ldr files into `reference/` and ask Claude to analyze them:

> "Analyze the reference files in reference/"

Claude spawns **one Explore agent per file, all running in parallel**. Each agent reads its file in 500-line chunks and returns a structured summary covering dimensions, parts, colors, construction patterns, and architectural details.

## Tips

- **Be specific about style**: "Victorian with ornate cornice" works better than "nice building"
- **Specify dimensions**: "32x16 studs, 2 stories" gives Claude clear constraints
- **Name your colors**: "Dark red primary, tan secondary, white trim" maps directly to LDraw color codes
- **Iterate**: Open the .ldr in stud.io, identify issues, then ask Claude to adjust

---

<div align="center">

**[View Full As-Built Documentation](https://roccothefunnyman.github.io/Claude.Bricks/)**

*Built with Claude Code + Terraform + Azure ML SDK v2*

</div>
