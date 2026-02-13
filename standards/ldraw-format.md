# LDraw File Format Reference

## Overview

LDraw is a text-based file format for describing LEGO models. Each line is a command. Files use the `.ldr` extension (model files) or `.dat` extension (part files). BrickLink Studio (stud.io) reads and renders LDraw files.

## Line Types

Each line starts with a type number:

| Type | Purpose | Usage |
|------|---------|-------|
| 0 | Meta command / comment | Headers, STEP, FILE/NOFILE, comments |
| 1 | Part reference | Places a part in the model |
| 2 | Line | Draw a line segment (rarely used in models) |
| 3 | Triangle | Geometry primitive (parts only) |
| 4 | Quadrilateral | Geometry primitive (parts only) |
| 5 | Optional line | Conditional line (parts only) |

For building generation, we only use **Type 0** (meta) and **Type 1** (part placement).

## Type 0 — Meta Commands

```
0 FILE <filename>          Start of a file/submodel
0 <filename>               Model description (usually same as FILE)
0 Name: <filename>         Model name
0 Author: <name>           Author name
0 !LDRAW_ORG Model         File type declaration
0 !LICENSE <license>       License info
0 STEP                     Build step separator
0 NOFILE                   End of submodel block
0 // <text>                Comment
0 BFC CERTIFY CCW          Back-face culling directive
0 !COLOUR ...              Custom color definition
```

### FILE / NOFILE Blocks

Multi-part models use FILE/NOFILE to define submodels:

```
0 FILE main_model.ldr
0 main_model.ldr
0 Author: Builder
1 16 0 0 0 1 0 0 0 1 0 0 0 1 sub_model.ldr
0 STEP
0 NOFILE

0 FILE sub_model.ldr
0 sub_model.ldr
1 15 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat
0 NOFILE
```

The main model references submodels by filename (like `sub_model.ldr`), and submodels are defined later in the same file using FILE/NOFILE blocks.

### STEP Markers

STEP separates logical build stages. Place them between major phases:
- After foundation/baseplate
- After each floor's walls
- After floor separation plates
- After roof construction
- After decorative details

## Type 1 — Part Placement

```
1 <color> <x> <y> <z> <a> <b> <c> <d> <e> <f> <g> <h> <i> <part.dat>
```

| Field | Description |
|-------|-------------|
| `1` | Line type |
| `color` | LDraw color code (integer) |
| `x y z` | Position coordinates (in LDU) |
| `a b c d e f g h i` | 3x3 rotation matrix |
| `part.dat` | Part filename |

### Example
```
1 15 40 140 10 1 0 0 0 1 0 0 0 1 3001.dat
```
Places a white (15) Brick 2x4 (3001.dat) at position (40, 140, 10) with no rotation.

## Coordinate System

```
        Y- (up)
        |
        |
        +-------> X+ (right)
       /
      /
     Z+ (toward viewer / front)
```

- **X-axis**: Left to right. Positive X = right.
- **Y-axis**: INVERTED. Positive Y = downward. Negative Y = upward.
- **Z-axis**: Front to back. Positive Z = toward the viewer.

### Units (LDU — LDraw Units)

| Measure | LDU |
|---------|-----|
| 1 stud width | 20 |
| 1 brick height | 24 |
| 1 plate height | 8 |
| Stud protrusion above brick top | 4 |
| 1 stud pitch | 20 |
| Half stud | 10 |

### Part Reference Point

Parts are positioned by their **center-top** point:
- X, Z: Center of the part
- Y: Top surface of the part

A 2x4 brick (3001.dat) placed at (40, 140, 30):
- Spans X: 0 to 80 (center at 40, half-width = 40)
- Spans Z: 10 to 50 (center at 30, half-depth = 20)
- Top at Y=140, bottom at Y=164 (140 + 24 for brick height)

### Ground Level Convention

In modular buildings:
- **Y=140** is ground level (top of baseplate, bottom of first brick course)
- Buildings go **up** by **decreasing Y**: Y=116, Y=92, Y=68, ...
- Each brick row: Y decreases by 24
- Each plate row: Y decreases by 8

## Rotation Matrix

The 3x3 rotation matrix controls part orientation:

```
| a b c |     Transforms the part's local axes
| d e f |     into world coordinates
| g h i |
```

### Standard Orientations

| Orientation | Matrix | Use Case |
|-------------|--------|----------|
| Default (along X) | `1 0 0 0 1 0 0 0 1` | Front/back walls |
| 90 deg CW (along Z) | `0 0 -1 0 1 0 1 0 0` | Left/right side walls |
| 180 deg | `-1 0 0 0 1 0 0 0 -1` | Back wall (facing opposite) |
| 270 deg CW | `0 0 1 0 1 0 -1 0 0` | Side wall (opposite direction) |

### Rotation Effects on Position

When a part is rotated, its center-point still refers to the center of the rotated bounding box. A 1x4 brick:
- Default orientation: spans 4 studs along X (80 LDU), 1 stud along Z (20 LDU)
- 90 deg rotation: spans 1 stud along X (20 LDU), 4 studs along Z (80 LDU)

Adjust X/Z coordinates accordingly when building walls in different orientations.

## Color Codes

Color is specified as an integer. Common colors:

```
0   = Black           1   = Blue            2   = Green
4   = Red             14  = Yellow          15  = White
19  = Tan             25  = Orange          28  = Dark Tan
47  = Trans Clear     70  = Reddish Brown   71  = Light Bluish Gray
72  = Dark Bluish Gray  84  = Medium Dark Flesh
150 = Medium Nougat   272 = Dark Blue       378 = Sand Green
```

Special color code **16** means "inherit color from parent" — used in submodel references.

See `color-palette.md` for full color tables and palette recommendations.

## File Header Template

```
0 FILE <ModelName>.ldr
0 <ModelName>.ldr
0 Name: <ModelName>.ldr
0 Author: Claude.Bricks
0 !LDRAW_ORG Model
0 !LICENSE Redistributable under CCAL version 2.0 : see CAreadme.txt
```

## Stud.io Compatibility Notes

- Stud.io uses LDraw format but has some extensions (flex parts, custom decorations)
- Standard LDraw parts (.dat) work in stud.io without issues
- Custom color definitions (0 !COLOUR) may be ignored by stud.io
- FILE/NOFILE submodels are supported
- STEP markers map to stud.io's step-by-step build instructions
