# Modular Building Specification

## Overview

LEGO Modular Buildings follow a set of conventions that allow them to connect side-by-side on a street layout. This document defines the standard dimensions, construction patterns, and structural requirements.

## Base Dimensions

### Standard Module: 32x32 studs
```
Width:  32 studs = 640 LDU (along X-axis)
Depth:  32 studs = 640 LDU (along Z-axis)
```

### Half-Width Module: 16x32 studs
```
Width:  16 studs = 320 LDU (along X-axis)
Depth:  32 studs = 640 LDU (along Z-axis)
```

### Common Variation: 32x16 studs
```
Width:  32 studs = 640 LDU (along X-axis)
Depth:  16 studs = 320 LDU (along Z-axis)
```

## Floor Heights

### Ground Floor
- **Standard**: 10 brick rows = 240 LDU
- **Tall ground floor** (storefronts): 12 brick rows = 288 LDU
- Includes space for doors (6 bricks / 144 LDU tall) and large windows

### Upper Floors
- **Standard**: 10 brick rows = 240 LDU
- Can be shorter (8 rows = 192 LDU) for compact designs

### Floor Separation
**Simple approach:** 2 plates between floors = 16 LDU

**Reference-confirmed approach (Detective's Office, Pet Shop):**
Real LEGO modulars use multi-layer floor assemblies of 40-56 LDU:
```
Layer 1 (Y = wall_top):      Plates/tiles at wall-top level
Layer 2 (Y = wall_top - 8):  Cross-grain support bricks (rotated 90° for locking)
Layer 3 (Y = wall_top - 16): Major spanning plates (2x4, 2x6, full width)
Layer 4 (Y = wall_top - 24): Connector bricks bridging to next floor

Total: 3-4 layers, 40-56 LDU thick (~2 brick heights)
```
Benefits: distributes load, allows geometry nesting, saves weight vs solid plate.

For generation scripts, a simplified 2-plate (16 LDU) separation works fine.
Use multi-layer only when replicating reference-quality builds.

### Total Building Heights
| Stories | Rows | LDU Height | Notes |
|---------|------|------------|-------|
| 1 story | 10 | ~240 | Single shopfront |
| 2 stories | 20 + sep | ~496 | Most common |
| 3 stories | 30 + 2 sep | ~752 | Tall buildings |

## Wall Construction

### Wall Thickness
- **Exterior walls**: 1 stud wide (20 LDU)
- **Interior walls**: 1 stud wide (optional for exterior-only models)

### Wall Position (32x16 stud building)
```
Front wall:  Z = 10  (center of 1-stud-wide wall at front edge)
Back wall:   Z = 310 (center of 1-stud-wide wall at back edge)
Left wall:   X = 10  (center of 1-stud-wide wall at left edge)
Right wall:  X = 630 (center of 1-stud-wide wall at right edge)
```

For walls along X-axis (front/back): Use default rotation `1 0 0 0 1 0 0 0 1`
For walls along Z-axis (left/right): Use 90 deg rotation `0 0 -1 0 1 0 1 0 0`

### Wall Row Pattern

Each horizontal row of a wall is built from bricks of varying sizes to fill the span. Standard approach:

1. Start from one end
2. Fill with largest bricks first (1x8, then 1x6, 1x4, 1x2, 1x1)
3. Skip gaps for windows and doors
4. Stagger joints between rows (offset by 1-2 studs for realism)

### Brick Staggering

Real LEGO walls stagger brick joints for structural integrity and visual appeal:
```
Row 1: |---1x4---|--1x3--|---1x4---|--1x2-|
Row 2: |--1x2-|---1x4---|---1x4---|--1x3--|
```
This is handled automatically by the FillX helper with an offset parameter.

### Masonry Texture (reference-confirmed)

For realistic stone-block appearance, use 98283.dat (masonry profile 1x2):
```
Option A: Replace regular bricks in every row with masonry bricks.
           Alternate rotation between rows (identity vs 90°).
           Offset 20-40 LDU between rows.

Option B: Use masonry as horizontal accent bands at a different Z-plane.
           Space every 20 LDU (1 stud) along the wall.
           Creates water-table or stringcourse effect.
```
See architectural-patterns.md Pattern 2 for detailed implementation.

### Submodel Organization (reference-confirmed)

Split buildings into floor-level submodels for clarity:
```
0 FILE BuildingName.ldr           ← master (references floors)
0 FILE BuildingName FIRST FLOOR.ldr
0 FILE BuildingName SECOND FLOOR.ldr
0 FILE BuildingName ROOF.ldr
0 FILE BuildingName STAIRS.ldr    ← detail submodels
0 FILE BuildingName SIGN.ldr
```
All submodels use absolute coordinates. Reference from master at origin with identity rotation.
PowerShell scripts should generate the complete multi-model file with FILE/NOFILE blocks.

## Window and Door Placement

### Standard Window (1x4x6 frame)
- **Part**: 60594.dat (frame) + 60592.dat (glass)
- **Size**: 4 studs wide (80 LDU) x 6 bricks tall (144 LDU)
- **Gap in wall**: 4 studs wide, 6 rows tall
- Place frame at the bottom of the gap
- Glass is placed at same position as frame (it fits inside)

### Standard Door (1x4x6 frame)
- **Part**: 60596.dat (frame) + 57895.dat (door panel)
- **Size**: 4 studs wide (80 LDU) x 6 bricks tall (144 LDU)
- **Gap in wall**: 4 studs wide, 6 rows tall
- Typically on ground floor only, front wall

### Small Window (1x4x3)
- **Part**: 3853.dat (frame) + 3856.dat (glass)
- **Size**: 4 studs wide x 3 bricks tall (72 LDU)

### Window Placement Rules
- Center windows symmetrically on the facade
- Leave at least 2 studs (40 LDU) between window edges
- Align upper and lower floor windows vertically
- Ground floor may have larger or more windows than upper floors

## Foundation / Baseplate

### Plate Foundation
Build the base from overlapping plates rather than a single baseplate:
```
Layer 1 (Y=140): 2x4 and 4x8 plates covering full footprint
Layer 2 (Y=132): Offset plates for structural interlock
```

### Sidewalk
- 2-3 stud strip along the front (Z direction)
- Covered with tiles (3070b.dat, 3069b.dat) for smooth surface
- Color: Light Bluish Gray (71) is standard

## Roof Options

### Flat Roof with Parapet
```
- Roof plates at top floor ceiling level
- 1-2 brick rows extending above roof as parapet walls
- Optional: tile capping on parapet top
```

### Sloped Roof
```
- Slope parts (3040b, 3037, 3038, 3039) angled from walls to ridge
- Ridge line runs along X or Z axis
- Requires careful slope angle calculation
```

### Cornice / Crown Molding
Overhang detail at roof line:
```
- Plate extended 1 stud beyond wall face
- Inverted slope or bracket underneath
- Tile on top for finished look
```

## Connection Between Modules

Modular buildings connect side-by-side via:
- Aligned baseplates (same Y level)
- Technic pin holes at standard positions (optional)
- Stud-to-stud contact at wall edges

## Coordinate Quick Reference (32x16 module)

```
Baseplate:   X: 0-640, Z: 0-320, Y: 140
Front wall:  Z = 10
Back wall:   Z = 310
Left wall:   X = 10
Right wall:  X = 630

Ground floor brick rows (Y values, top of each brick):
  Row 1: Y = 116   (140 - 24)
  Row 2: Y = 92    (116 - 24)
  Row 3: Y = 68
  Row 4: Y = 44
  Row 5: Y = 20
  Row 6: Y = -4
  Row 7: Y = -28
  Row 8: Y = -52
  Row 9: Y = -76
  Row 10: Y = -100

Floor separation plates:
  Plate 1: Y = -108  (-100 - 8)
  Plate 2: Y = -116  (-108 - 8)

Second floor brick rows (Y values):
  Row 1: Y = -140  (-116 - 24)
  Row 2: Y = -164
  ...continues decreasing by 24...
```

## Build Order

Standard build sequence for a 2-story modular:

1. **Foundation plates** (Y=140, Y=132)
2. **Ground floor walls** — row by row, Y decreasing
3. **Ground floor windows/doors** — placed in wall gaps
4. **Floor separation plates**
5. **Second floor walls** — row by row
6. **Second floor windows**
7. **Roof plates**
8. **Cornice/parapet**
9. **Roof details** (chimney, dormers, railings)
10. **Facade details** (awnings, signs, lamps)
11. **Sidewalk**
