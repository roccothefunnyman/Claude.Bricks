# Claude.Bricks — Claude Code Configuration

## Project Overview

This repo designs **modular LEGO buildings** using the **LDraw (.ldr) file format**, rendered in **BrickLink Studio (stud.io)**. Claude Code generates buildings via PowerShell scripts that output .ldr files.

## Critical Rules

1. **NEVER write raw .ldr content directly** — always generate a PowerShell script that produces the .ldr file. Claude's 32K output token limit makes direct .ldr output impossible for real buildings.
2. **NEVER read entire large .ldr files** into the main context — use Explore subagents with chunk reading (500 lines at a time via offset/limit).
3. **Always use the standards docs** in `standards/` for part numbers, colors, and conventions before writing any generation script.
4. **Test every script** by running it after writing it. Then validate the output .ldr file.

## LDraw Quick Reference

### Coordinate System
```
1 stud  = 20 LDU (length/width)
1 brick = 24 LDU (height)
1 plate = 8 LDU  (height, 3 plates = 1 brick)
Stud top = 4 LDU above brick top surface

Y-axis is INVERTED: positive Y = downward
Ground level = Y 140 (top of baseplate)
Buildings extend upward = decreasing Y values
```

### LDraw Line Format
```
1 <color> <x> <y> <z> <a> <b> <c> <d> <e> <f> <g> <h> <i> <part.dat>

The 9 values (a through i) form a 3x3 rotation matrix:
| a b c |
| d e f |
| g h i |
```

### Rotation Matrices
```
Default (along X-axis):  1 0 0 0 1 0 0 0 1
90 deg CW (along Z):     0 0 -1 0 1 0 1 0 0
180 deg:                 -1 0 0 0 1 0 0 0 -1
270 deg CW:               0 0 1 0 1 0 -1 0 0

Angled rotations (around Y-axis, for furniture/decoration):
30 deg:   0.866025 0 0.5 0 1 0 -0.5 0 0.866025
45 deg:   0.707107 0 0.707107 0 1 0 -0.707107 0 0.707107
```

### Slope Rotations (for roofs/cornices)
```
Front-facing slope:  1 0 0 0 1 0 0 0 1    (default)
Back-facing slope:  -1 0 0 0 1 0 0 0 -1   (inverted = 180°)
```

### File Structure
```
0 FILE <modelname.ldr>     — start of file/submodel
0 <modelname.ldr>          — model name
0 Author: <name>           — author line
0 STEP                     — build step separator
1 <color> ... <part.dat>   — place a part
0 NOFILE                   — end submodel block
0 // comment               — comment
```

### Common Colors
```
Code  Color                  Code  Color
----  -----                  ----  -----
0     Black                  14    Yellow
6     Brown                  15    White
9     Light Blue             19    Tan
28    Dark Tan               47    Trans Clear
70    Reddish Brown          71    Light Bluish Gray
72    Dark Bluish Gray       84    Medium Dark Flesh
212   Bright Light Blue      378   Sand Green
462   Medium Orange          484   Dark Orange
150   Medium Nougat*

* Medium Nougat (150) may not render in all stud.io versions.
  Use Dark Tan (28) as safe fallback. Configurable via $MN in scripts.
* Bright Light Blue (212) valid in modern LDraw/stud.io.
  Use Light Blue (9) as universal fallback for older viewers.
```

### Common Parts
```
BRICKS:
  3005.dat = 1x1    3004.dat = 1x2    3622.dat = 1x3
  3010.dat = 1x4    3009.dat = 1x6    3008.dat = 1x8
  3001.dat = 2x4    3003.dat = 2x2    2456.dat = 2x6
  3002.dat = 2x3    6112.dat = 1x12

PLATES:
  3024.dat = 1x1    3023.dat = 1x2    3710.dat = 1x4
  3666.dat = 1x6    3460.dat = 1x8    3020.dat = 2x4
  3795.dat = 2x6    3034.dat = 2x8    3832.dat = 2x10
  3035.dat = 4x8    3028.dat = 6x12   3036.dat = 6x8
  3958.dat = 6x6    3031.dat = 4x4    4477.dat = 1x10

TILES (no studs):
  3070b.dat = 1x1   3069b.dat = 1x2   63864.dat = 1x3
  2431.dat  = 1x4   6636.dat  = 1x6   4162.dat  = 1x8

WINDOWS & DOORS:
  60594.dat  = Window Frame 1x4x6
  60592.dat  = Window Glass 1x4x6
  60596.dat  = Door Frame 1x4x6
  57895.dat  = Door Glass (right handle)
  57896.dat  = Door Glass (left handle)
  3853.dat   = Window 1x4x3
  3856.dat   = Window Glass 1x4x3

ARCHES:
  3659.dat   = Arch 1x4 (2 bricks tall)
  6183.dat   = Arch 1x4x3 (3 bricks tall)
  3307.dat   = Arch 1x6x2 (wide, 2 bricks tall)
  3308.dat   = Arch 1x8x2 (very wide, 2 bricks tall)

SLOPES:
  3040b.dat  = Slope 45 2x1         3037.dat  = Slope 45 2x4
  3039.dat   = Slope 45 2x2         3038.dat  = Slope 45 2x3
  85984.dat  = Slope 30 1x2x2/3     92946.dat = Slope 30 2x2x2/3
  3665.dat   = Slope Inv 45 2x1 (corbels, under-cornice)

BASEPLATES:
  3811.dat   = Baseplate 32x32 (center at 320,140,320)
  3867.dat   = Baseplate 16x32

SPECIALTY:
  87087.dat  = Brick 1x1 w/ stud on side (SNOT)
  98283.dat  = Brick 1x2 masonry profile
  15254.dat  = Round Tile 1x1 (quarter circle)
  4070.dat   = Brick 1x1 w/ headlight
  4073.dat   = Round Plate 1x1 (flowers, finials)
  2877.dat   = Brick 1x2 w/ grille
  30136.dat  = Palisade Brick 1x2
```

## Construction Recipes (from reference analysis)

### Masonry Wall Row
```
Alternate rotation every row. Offset 20-40 LDU between rows.
Odd:  B $color $x $y $z "0 0 1 0 1 0 -1 0 0" "98283.dat"   # perpendicular
Even: B $color $x $y $z "1 0 0 0 1 0 0 0 1"  "98283.dat"   # identity
```

### Dentil Cornice
```
3794b.dat tiles every 40 LDU, perpendicular to wall:
  B $color $x $y $z "0 0 1 0 1 0 -1 0 0" "3794b.dat"
Creates 1-stud overhang from wall face.
```

### Paired Slope Ridge
```
Two slopes meeting at ridge, 20 LDU apart:
  B $Roof $x $y  $z     "1 0 0 0 1 0 0 0 1"    "3040b.dat"   # up
  B $Roof $x $y ($z+20) "-1 0 0 0 1 0 0 0 -1"  "3040b.dat"   # down
```

### Window/Door Standard
```
Frame + glass at same position. Frame in color 15, glass in color 47.
  B 15 $x $y $z $R0 "60594.dat"   # window frame
  B 47 $x $y $z $R0 "60592.dat"   # window glass
```

### SNOT Mounting
```
87087.dat stud-on-side, cardinal rotations only (studs face ±X or ±Z).
4070.dat headlight in grids every 60 LDU for detail mounting.
```

## PowerShell Generation Strategy

### Why PowerShell Scripts?
A building with proper detail = 500-3000+ lines of .ldr. A PowerShell script = ~300-600 lines.
The script approach stays within Claude's output limits while producing unlimited .ldr output.

### Required Script Structure
```powershell
# === PARAMETERS ===
$OutputFile = "output/BuildingName.ldr"
$ModelName = "Building Name"
# Colors
$Primary = 28    # Dark Tan
$Secondary = 378 # Sand Green
$Accent = 72     # Dark Bluish Gray
$Trim = 15       # White
$Window = 47     # Trans Clear
# Dimensions (in LDU)
$Width = 640     # 32 studs
$Depth = 320     # 16 studs

# === HELPER FUNCTIONS ===
# B() — place a single brick
# FillX() / FillZ() — fill a span with optimal brick sizes
# FillXPlate() / FillZPlate() — same for plates
# WallRowX() / WallRowZ() — wall row with gap support for windows/doors

# === BUILDING GENERATION ===
# Foundation plates
# Ground floor walls (row by row, bottom to top = decreasing Y)
# Floor separation (plates between stories)
# Upper floor walls
# Roof / parapet / cornice
# Details (awnings, signs, decorative elements)

# === OUTPUT ===
$lines | Out-File -FilePath $OutputFile -Encoding UTF8
```

### Key Helper Functions

Every script MUST include these core helpers:

- **`B($color, $x, $y, $z, $rot, $part)`** — emit a single part line
- **`FillX($color, $x1, $x2, $y, $z, $rot)`** — fill X span with 1x8, 1x6, 1x4, 1x2, 1x1 bricks
- **`FillZ($color, $x, $y, $z1, $z2, $rot)`** — fill Z span with bricks (rotated 90)
- **`WallRowX($color, $x1, $x2, $y, $z, $gaps)`** — wall row along X with openings
- **`WallRowZ($color, $x, $y, $z1, $z2, $gaps)`** — wall row along Z with openings
- **`FillXPlate($color, $x1, $x2, $y, $z, $depth)`** — fill floor/ceiling area with plates

`$gaps` is an array of hashtables: `@(@{s=60;e=140}, @{s=220;e=460})` where s=start, e=end in LDU.

### Y-Coordinate Cheat Sheet (32x32 modular)
```
Y=140    Ground level (top of baseplate)
Y=116    Row 1 (first brick row, since 140-24=116)
Y=92     Row 2
Y=68     Row 3
Y=44     Row 4
Y=20     Row 5
Y=-4     Floor separation plate
Y=-12    Second floor row 1
Y=-36    Row 2
Y=-60    Row 3
Y=-84    Row 4
Y=-108   Row 5
Y=-132   Roof level
```

## Multi-Agent Workflow

### When to Use Agents

Spawn agents when:
- Analyzing a reference .ldr file (always use Explore agent, never read 5000+ line files in main context)
- Building a complex structure (Architect + Script Writer)
- Validating output (Validator agent)

### Agent Roles

#### 1. Reference Analyzer (Explore subagent) — ONE PER FILE, IN PARALLEL
**Trigger**: User provides one or more reference .ldr files
**Rule**: Spawn one Explore agent per file. Run ALL agents in parallel. NEVER read large .ldr files in the main context.

```
Analyze the LDraw file at [path]. Read it in 500-line chunks using offset/limit.
Extract and return a structured summary:

1. Building dimensions (X/Y/Z ranges in LDU and studs)
2. All unique part numbers with count and common name
3. All color codes with count and descriptive name
4. Floor separation Y-coordinates
5. Window/door placements (coordinates, part numbers, which wall)
6. Roof construction (parts, Y-range, technique)
7. Submodel names (FILE/NOFILE blocks)
8. Wall construction pattern (brick sizes, staggering)
9. Architectural details (cornices, bands, SNOT, masonry, slopes)
10. Baseplate/foundation construction

Do NOT return raw file content. Return ONLY the structured analysis.
```

**After all agents complete**: Compare summaries in main context, identify patterns consistent across multiple files, and update standards docs accordingly.

#### 2. Architect (Plan subagent)
**Trigger**: New building design request
```
Read standards/modular-building-spec.md and standards/architectural-patterns.md.
Design a building spec:
- Dimensions, floor count, style
- Window/door positions as gap arrays
- Color assignments (primary, secondary, accent, trim)
- Feature list (cornice, awning, balcony, etc.)
Output a structured spec for the Script Writer.
```

#### 3. Script Writer (general-purpose subagent)
**Trigger**: Building spec is ready
```
Read the existing script template in scripts/.
Write a new PowerShell script implementing the building spec.
Use all standard helper functions.
Run the script and verify it produces valid output.
Save script to scripts/, output to output/.
```

#### 4. Validator (Bash subagent)
**Trigger**: .ldr file generated
```
Check the .ldr file for:
- Valid header (0 FILE, 0 Name)
- All part refs end in .dat
- Y coords in expected range
- Color codes are valid
- STEP markers present
- No obvious coordinate collisions
Return pass/fail with specifics.
```

### Orchestration Patterns

#### Pattern A: Analyzing Reference Files
```
User provides N reference .ldr files
    |
    +---> [Explore Agent 1] analyzes file1.ldr  ─┐
    +---> [Explore Agent 2] analyzes file2.ldr   ├── ALL in parallel
    +---> [Explore Agent 3] analyzes file3.ldr   │
    +---> [Explore Agent N] analyzes fileN.ldr  ─┘
    |
    Main context: Compare all N summaries
    |
    Identify patterns consistent across multiple files
    |
    Update standards docs with confirmed patterns
```

#### Pattern B: Designing a New Building
```
User Request
    |
    +---> [Reference Analyzer(s)] (if ref files provided)  \
    +---> [Architect]                                        }--> wait
    |                                                       /
    +---> Present spec to user for approval
    |
    +---> [Script Writer] --> generates .ldr
    |
    +---> [Validator] --> checks .ldr
    |
    +---> Report to user with file path
```

## File Conventions

- **Scripts**: `scripts/<BuildingName>.ps1` (PascalCase)
- **Output**: `output/<BuildingName>.ldr` (PascalCase)
- **Reference files**: `reference/<descriptive-name>.ldr`
- **Standards**: `standards/<topic>.md` (kebab-case)

## Standards Documentation

Detailed references are in the `standards/` directory:
- `ldraw-format.md` — Full LDraw file format specification
- `modular-building-spec.md` — Modular building dimensions and conventions
- `parts-catalog.md` — Comprehensive parts list with dimensions
- `color-palette.md` — Color codes and themed palettes
- `architectural-patterns.md` — Proven facade and detail patterns
