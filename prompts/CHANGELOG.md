# Prompt Version Changelog

All notable changes to prompt templates are documented here. Each version change should include the rationale and any evaluation results that motivated the change.

## System Prompts (`system/`)

### v2.txt (2026-03-08)

**Rationale**: v1 produced unstructured free-text output that was difficult to parse programmatically and inconsistent across runs. v2 enforces a fixed section structure (Dimensions, Color Palette, Architectural Features, Floor Plans, Construction Notes, Structural Validation) so downstream scripts can reliably extract fields.

**Changes from v1**:
- Added explicit output section headings with required format
- Added table format for color palette
- Added structural validation section requiring the model to self-check
- Added grounding instruction: "Ground every decision in the provided context"
- Specified gap array format for window/door placements

**Expected impact**: More consistent output format, fewer missing fields, better parseability for automated evaluation.

### v1.txt (2026-03-08)

**Rationale**: Initial system prompt establishing the core task definition for LEGO building specification generation.

**Content summary**: Instructs the model to generate specs with dimensions, colors, architectural features, floor plans, and construction notes using LDraw conventions. Straightforward, minimal structure requirements.

---

## RAG Templates (`rag/`)

### v2.jinja2 (2026-03-08)

**Rationale**: v1 provided context without explicit instructions on how to use it, leading to outputs that sometimes ignored retrieved materials or hallucinated part numbers not present in the references.

**Changes from v1**:
- Added numbered reference headers with relevance scores
- Added explicit grounding instructions (5 rules)
- Required inline citations `[Ref N]` for major design decisions
- Required the model to flag ungrounded decisions
- Added prompt_version metadata for telemetry tracking

**Expected impact**: Higher groundedness scores, fewer hallucinated part numbers, traceable design decisions.

### v1.jinja2 (2026-03-08)

**Rationale**: Initial RAG template providing simple context injection. Concatenates retrieved documents and appends the user query.

**Content summary**: "Based on the following reference materials: [context]. Generate a building specification for: [query]." Minimal structure.

---

## Versioning Policy

- System prompts use integer versions: `v1.txt`, `v2.txt`, etc.
- RAG templates use integer versions: `v1.jinja2`, `v2.jinja2`, etc.
- Every version is kept in the repository (never delete old versions).
- Version changes are evaluated using `eval/run_prompt_experiment.py` before promotion.
- The active version in production is tracked via the `PROMPT_VERSION` environment variable and logged as a custom dimension in Application Insights telemetry.
