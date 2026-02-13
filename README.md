# Claude.Bricks

AI-assisted modular LEGO building design using LDraw and BrickLink Studio.

## What This Is

A Claude Code-powered workflow for designing modular LEGO buildings. You describe what you want, Claude generates a PowerShell script, the script outputs an LDraw (.ldr) file, and you open it in BrickLink Studio (stud.io) to view, render, and refine.

## Prerequisites

- **BrickLink Studio** (stud.io) — [Download here](https://www.bricklink.com/v3/studio/download.page) — for viewing and rendering .ldr files
- **PowerShell 5.1+** — included with Windows 10/11
- **Claude Code CLI** — for AI-assisted design sessions

## Quick Start

1. Open a terminal in this folder
2. Run `claude`
3. Describe the building you want:
   > "Design a 2-story Victorian townhouse, 32x16 studs, dark red and tan with white trim"
4. Claude generates a PowerShell script in `scripts/`
5. The script runs and produces an .ldr file in `output/`
6. Open the .ldr file in BrickLink Studio

## How It Works

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

This keeps the main conversation focused while heavy analysis and generation happen in parallel.

## Repository Structure

```
Claude.Bricks/
├── CLAUDE.md              # Claude Code session context (loaded automatically)
├── README.md              # This file
├── standards/             # LDraw format and building convention docs
│   ├── ldraw-format.md
│   ├── modular-building-spec.md
│   ├── parts-catalog.md
│   ├── color-palette.md
│   └── architectural-patterns.md
├── scripts/               # PowerShell generation scripts
├── output/                # Generated .ldr files
├── reference/             # Reference .ldr files for style analysis
└── oldstuff/              # Archived files from earlier work
```

## Standards Documentation

The `standards/` directory contains detailed references that Claude reads when generating buildings:

- **ldraw-format.md** — LDraw file format specification (line types, coordinates, rotations)
- **modular-building-spec.md** — Modular building conventions (dimensions, floor heights, wall patterns)
- **parts-catalog.md** — Common LEGO parts with IDs, dimensions, and usage notes
- **color-palette.md** — LDraw color codes and recommended palettes by architectural style
- **architectural-patterns.md** — Proven design patterns for facades, cornices, roofs, and details

## Adding Reference Files

Drop any well-built .ldr files into `reference/` and ask Claude to analyze them:

> "Analyze the reference files in reference/"

Claude spawns **one Explore agent per file, all running in parallel**. Each agent reads its file in 500-line chunks and returns a structured summary covering dimensions, parts, colors, construction patterns, and architectural details. After all agents complete, Claude compares the findings across files, identifies patterns that are consistent across multiple builds, and updates the standards docs.

This approach handles files of any size (5,000+ lines) without flooding the main conversation context.

## Tips

- **Be specific about style**: "Victorian with ornate cornice" works better than "nice building"
- **Specify dimensions**: "32x16 studs, 2 stories" gives Claude clear constraints
- **Name your colors**: "Dark red primary, tan secondary, white trim" maps directly to LDraw color codes
- **Iterate**: Open the .ldr in stud.io, identify issues, then ask Claude to adjust
- **Exterior first**: Start with exterior shells, add interiors later if needed
