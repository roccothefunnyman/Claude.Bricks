# Claude.Bricks — Repository Explanation

## What This Repo Is

Claude.Bricks is an AI-assisted system for designing modular LEGO buildings using the LDraw file format, rendered in BrickLink Studio. Claude Code writes PowerShell scripts that procedurally generate LDraw (.ldr) files, bypassing token limits while producing buildings with hundreds to thousands of lines of structured output. The repo also serves as the project backbone for an AHEAD-led DP-100 (Azure Data Scientist Associate) study group, where the LEGO building pipeline provides a concrete, end-to-end scenario for practicing Azure Machine Learning skills.

## How This Repo Is Used for the DP-100 Study Group

The Claude.Bricks project does double duty. On its own, it is a working LEGO building generator. But it is also the central scenario for a four-module DP-100 certification prep course run through AHEAD.

The course deck (Claude_Bricks_DP100_Deck_v3.pptx, 41 slides with full speaker notes) maps every lab exercise back to one of the four DP-100 exam domains:

- **Module 1 — Design and Prepare (20-25%):** Use Terraform to provision an Azure ML workspace, storage, ACR, Key Vault, Log Analytics, and compute. Register datastores and data assets. The `tf/` directory contains the actual Terraform configs for this.
- **Module 2 — Explore Data and Run Experiments (20-25%):** Run AutoML experiments, configure hyperparameter sweep jobs, track metrics with MLflow. Use the LEGO data scenarios as training inputs.
- **Module 3 — Train and Deploy Models (25-30%):** Package training code as script jobs, build Azure ML pipelines, register models, deploy to managed online and batch endpoints.
- **Module 4 — Optimize Language Models (25-30%):** Deploy models from the Azure AI model catalog, build prompt flows, implement RAG with Azure AI Search and vector stores, and discuss fine-tuning workflows.

The course defines four concrete ML scenarios that use the Claude.Bricks domain:

1. **Image classification for facade style** — classify street photos into LEGO-friendly architectural styles (historic, modern, industrial), deploy as a managed online endpoint.
2. **Anomaly detection for .ldr validation** — extract structural features from .ldr files (overhang ratios, collision counts, stability metrics) and train a model to flag unsafe builds.
3. **Pattern extraction from reference files** — vectorize part-usage statistics per building, cluster to discover recurring styles, feed insights back to the Spec Generator agent.
4. **Fine-tuned language model for spec generation** — prepare building spec examples, fine-tune a base model from the Azure AI catalog, deploy for the Spec Generator to call.

The HTML files in `output/` (dp100-domain-coverage, pipeline-flow, agent-resource-map, full-resource-architecture, lab-vs-production, rag-architecture, training-to-deployment, four-scenarios-dashboard, dp100-coverage-tracker) are interactive architecture diagrams generated for the course materials, not LEGO output. They visualize how the Claude.Bricks pipeline maps to Azure ML resources and DP-100 exam topics.

The `azure-icons/` directory contains Microsoft's official Azure icon set, used to build those diagrams.

The study group is transparent about coverage gaps. The deck explicitly calls out topics it does not fully cover (Synapse Spark, feature stores, Databricks, Responsible AI toolbox) and directs students to Microsoft Learn modules for self-study on those areas.

## Repo Structure

```
Claude.Bricks/
├── CLAUDE.md                    # Claude Code session context (loaded automatically)
├── README.md                    # Quick start and architecture overview
├── explanation.md               # This file
├── .gitignore                   # Ignores output/*.ldr, reference/*.ldr, ldraw_examples/, oldstuff/
│
├── standards/                   # LDraw and building convention references
│   ├── ldraw-format.md          #   File format spec (line types, coordinates, rotations)
│   ├── modular-building-spec.md #   Modular dimensions, floor heights, wall construction
│   ├── parts-catalog.md         #   150+ LEGO parts with LDU dimensions
│   ├── color-palette.md         #   40+ color codes and themed palettes
│   └── architectural-patterns.md#   27 proven patterns from official LEGO sets
│
├── docs/                        # Project-specific documentation and lessons learned
│   ├── part-geometry.md         #   Corrected part dimensions and pairings
│   ├── construction-patterns.md #   Patterns from 10246 Detective's Office & 10218 Pet Shop
│   ├── common-mistakes.md       #   6 critical mistakes with fixes
│   └── ldraw-format.md          #   Quick reference
│
├── modules/                     # Shared PowerShell module
│   └── LDraw.psm1              #   300+ lines: fill, wall, window, cornice, floor helpers
│
├── scripts/                     # PowerShell generation scripts
│   ├── _Template.ps1            #   448-line template for new buildings
│   ├── BasicModular.ps1         #   Georgian style, 32x32, 2 stories
│   ├── CornerBakery.ps1         #   1-story storefront, 32x16
│   ├── EuropeanTownhouse.ps1    #   v1: original dual-facade
│   ├── EuropeanTownhouse_v2.ps1 #   v2: fixed corner collisions
│   ├── EuropeanTownhouse_v3.ps1 #   v3: floor separation color fixes
│   ├── EuropeanTownhouse_v4.ps1 #   v4: corrected window parts and gaps
│   ├── GrandHotel.ps1           #   3-story Parisian colonnade, 32x32
│   ├── IceCreamShop.ps1         #   Colorful 2-story, 32x32
│   └── Validate.ps1             #   Output validator
│
├── output/                      # Generated .ldr files + DP-100 HTML diagrams
│   ├── *.ldr                    #   Generated LEGO buildings (gitignored)
│   ├── *.html                   #   DP-100 architecture diagrams for study group
│   └── connectivity-diagram.drawio  # Drawio source for connectivity diagram
│
├── reference/                   # Reference .ldr files and fix plans
│   ├── *.ldr                    #   Official LEGO set models (gitignored)
│   └── ice-cream-shop-fix-plan*.md  # Iterative fix plans for IceCreamShop
│
├── tf/                          # Terraform configs for Azure ML lab environment
│   ├── main.tf                  #   Provider config (azurerm ~> 3.80)
│   ├── resource_group.tf        #   Resource group
│   ├── ml_workspace.tf          #   Azure ML workspace
│   ├── ml_compute.tf            #   Compute clusters and instances
│   ├── storage.tf               #   Storage account
│   ├── acr.tf                   #   Azure Container Registry
│   ├── keyvault.tf              #   Key Vault
│   ├── monitoring.tf            #   Log Analytics
│   ├── cognitive_services.tf    #   Azure OpenAI / AI services
│   ├── variables.tf / outputs.tf
│   ├── terraform.tfvars.example
│   └── AzureMLResourceList.md   #   Resource inventory doc
│
├── azure-icons/                 # Microsoft Azure icon set for diagrams
│   ├── ICON-REFERENCE.md
│   └── [category subdirectories]
│
├── ldraw_examples/              # Reference LDraw files (gitignored, copyrighted)
└── oldstuff/                    # Archived earlier work (gitignored)
```

Naming conventions: scripts use PascalCase (`CornerBakery.ps1`), standards docs use kebab-case (`parts-catalog.md`), output files match their script names. The European Townhouse has four versioned scripts tracking its iterative refinement.

## Key Technologies and Tools

- **PowerShell 5.1+** — all building generation logic. Scripts import a shared module (`LDraw.psm1`) and output UTF-8 text files.
- **LDraw file format** — open standard for describing LEGO models. Line type 1 places parts with position, rotation matrix, and part ID.
- **BrickLink Studio (stud.io)** — desktop app for viewing, rendering, and refining .ldr files. The visual feedback loop.
- **Claude Code CLI** — AI-assisted design sessions. Reads CLAUDE.md and standards docs for context, generates PowerShell scripts, spawns subagents for analysis.
- **Terraform (>= 1.0, azurerm ~> 3.80)** — provisions the Azure ML lab environment. Local backend for development, with remote state config commented out for production.
- **Azure Machine Learning** — workspace, compute clusters/instances, datastores, data assets, managed online endpoints, batch endpoints, MLflow tracking.
- **Azure AI services** — Azure OpenAI, Azure AI Search (vector store for RAG), prompt flow.
- **Git / GitHub** — version control, hosted at `github.com/roccothefunnyman/Claude.Bricks`.

## Architecture and Design Patterns

### Code generation as an output multiplier

The core design decision: Claude cannot emit 2000 lines of LDraw directly (token limits), but it can write a 400-line PowerShell script that generates 2000 lines. The script approach is a compression strategy — loops, helper functions, and parameterized dimensions produce far more output than input.

### Shared module with fill algorithms

`LDraw.psm1` provides `Fill-BricksX`, `Fill-BricksZ`, `Fill-PlatesX`, and similar functions that take a span in LDU and greedily fill it with the largest available parts (1x8, 1x6, 1x4, 1x2, 1x1). Wall functions (`Add-WallRowX`, `Add-WallRowZ`) accept gap arrays for window and door openings. This prevents every script from reinventing brick-filling logic.

### Standards as structured context

The `standards/` directory is not documentation for humans — it is context for Claude. When Claude generates a building, it reads `parts-catalog.md` for valid part IDs, `color-palette.md` for color codes, `architectural-patterns.md` for proven construction techniques. This is prompt engineering expressed as markdown files checked into the repo.

### Multi-agent workflow

CLAUDE.md defines four specialized agent roles: Reference Analyzer (reads .ldr files in 500-line chunks), Architect (designs building specs), Script Writer (writes the PowerShell), and Validator (checks output). Reference analysis agents run in parallel — one per file — to avoid flooding the main context window.

### Iterative correction loop

The European Townhouse went through four versions (v1 through v4), each fixing specific structural issues discovered in stud.io: corner wall collisions, floor separation thickness, window part mismatches. The `docs/common-mistakes.md` file captures these as a checklist. The `reference/ice-cream-shop-fix-plan*.md` files show the same pattern for the Ice Cream Shop — three iterations of increasingly precise fix plans, each correcting assumptions from the previous plan.

### Infrastructure as code for the study group

The `tf/` directory provisions a complete Azure ML lab environment: resource group, workspace, storage, ACR, Key Vault, Log Analytics, compute clusters, and cognitive services. It is split into one file per resource type. The course deck shows students how this maps to DP-100 exam topics.

### No CI/CD, no tests, no automation pipeline

This is a design-time tool, not a production system. There is no CI pipeline, no automated test suite, no deployment workflow. The feedback loop is: write script, run script, open .ldr in stud.io, look at it, iterate.

## How Claude Code Is Being Used Here

Claude Code is not a helper tool in this repo. It is the primary design engine.

**CLAUDE.md** (383 lines) is the session context file, loaded automatically when Claude Code opens this repo. It contains:
- The LDraw coordinate system, rotation matrices, and part reference tables
- Construction recipes (masonry walls, dentil cornices, window assemblies)
- The complete PowerShell generation strategy with required script structure
- Multi-agent orchestration patterns with prompts for each agent role
- File naming conventions and output paths

**Auto-memory** (`.claude/` project directory) preserves critical corrections across sessions — window part pairings, floor plate construction rules, Fill function safety guards. This prevents Claude from repeating mistakes it has already fixed.

**Standards docs as agent context**: The five files in `standards/` exist primarily to be read by Claude during generation. They are structured for machine consumption: tables of part IDs with dimensions, rotation matrices in copyable format, color codes with hex values.

**Iterative refinement artifacts**: The fix plan files in `reference/` show Claude Code's planning process — analyzing reference images, identifying specific coordinate and part corrections, then implementing targeted changes. Each plan version corrects the previous one based on visual feedback from stud.io renders.

**Subagent delegation**: The CLAUDE.md file explicitly defines when to spawn agents, what prompts to use, and how to manage parallel analysis of large files. This is formalized agent orchestration, not ad-hoc tool use.

## What Makes This Repo Interesting as a Demo

**Claude Code as a domain-specific design tool.** This repo shows what happens when you take an AI coding assistant and point it at a problem that is not software engineering in the traditional sense. LDraw is a declarative 3D format with precise coordinate math, strict part IDs, and physical constraints. Claude Code is being used as a CAD system, not a code editor.

**The compression pattern.** The PowerShell-as-intermediate-representation approach is a genuine engineering solution to a real constraint (output token limits). It is generalizable: any time an AI needs to produce output larger than its context window, generating a program that produces the output is a viable strategy.

**Standards docs as prompt engineering.** Instead of cramming domain knowledge into a system prompt, this repo externalizes it as version-controlled markdown files that Claude reads on demand. The standards are the prompt. This is a repeatable pattern for giving AI tools deep domain knowledge without bloating context.

**The correction loop is visible.** Four versions of the European Townhouse, three versions of the Ice Cream Shop fix plan, and a `common-mistakes.md` file that reads like a post-mortem log. You can trace every mistake Claude made, how it was discovered (stud.io rendering), and how it was corrected. This is honest documentation of how AI-assisted design actually works — it is iterative, it makes mistakes, and the human-in-the-loop (opening the file in stud.io and looking at it) is essential.

**Dual-purpose project.** Using a LEGO building generator as the scenario for an Azure ML certification course is a deliberate choice. It gives students a single coherent project instead of disconnected demos. Image classification, anomaly detection, clustering, and LLM fine-tuning all have natural homes in the LEGO domain. The four DP-100 exam domains map to four course modules, each with hands-on labs tied to this project.

**Multi-agent orchestration in practice.** The CLAUDE.md file is a working specification for agent-based workflows: parallel reference analysis, specialized roles (Architect, Script Writer, Validator), and explicit prompts for each. This is not theoretical — it is how the buildings get made.

## Current State

**Working and stable:**
- Six building scripts produce valid .ldr files that render in stud.io
- The shared module (`LDraw.psm1`) provides reusable fill, wall, and assembly functions
- Standards documentation is thorough and cross-referenced
- The template script (`_Template.ps1`) provides a solid starting point for new buildings
- Terraform configs provision a complete Azure ML lab environment

**Actively being worked on:**
- `IceCreamShop.ps1` is modified (uncommitted changes) with three fix plan iterations in reference/
- The `GrandHotel.ps1` script is untracked (not yet committed)
- Output HTML diagrams for the DP-100 course exist in v1 and v2 variants, suggesting active refinement

**Incomplete or experimental:**
- The `tf/` directory has a `.terraform` directory (initialized) but no evidence of a completed deployment
- Azure-related HTML diagrams and `azure-icons/` are in the repo but not gitignored, suggesting they may be in transition
- The `output/` directory mixes LEGO .ldr files with DP-100 HTML diagrams — these serve different purposes and could be separated
- No interiors in any building — all scripts generate exterior shells only
- The connection between the LEGO generation pipeline and the Azure ML scenarios described in the deck is conceptual. The ML training code, datasets, and endpoint configurations for the four scenarios do not exist in the repo yet.

**Known debt:**
- CLAUDE.md still has incorrect window part descriptions (documented in memory and docs/common-mistakes.md but not fixed in the main config)
- Some documentation overlap between `standards/` and `docs/` (two ldraw-format.md files)
- The `oldstuff/` directory contains archived work from earlier sessions that has not been cleaned up