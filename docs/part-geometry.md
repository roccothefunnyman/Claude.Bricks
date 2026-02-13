# LDraw Part Geometry Reference

## Part Origin Convention

For studded parts, the origin is **centered on the topmost stud group**. The bottom
of studs lies on the x-z plane (y=0 in part space).

When you place a brick at `(x, y, z)`:
- The **top surface** (stud base) is at `y`
- The brick body extends **downward** to `y + height`
- The brick is **centered** at `(x, z)` in the horizontal plane

Since Y is inverted in LDraw (-Y = up), "downward" means increasing Y.

## Core Dimensions (in LDU)

| Measurement         | LDU  | Notes                          |
|---------------------|------|--------------------------------|
| 1 stud width        | 20   | Brick/plate length unit        |
| 1 brick height      | 24   | Full brick                     |
| 1 plate height      | 8    | 3 plates = 1 brick             |
| 1 tile height       | 8    | Same as plate, no studs on top |
| 1 stud diameter     | 12   | Physical stud cylinder         |
| 1 stud protrusion   | 4    | Height above brick surface     |
| 1 LDU               | 0.4mm| Physical equivalence           |

## Window & Door Parts (CORRECTED)

### 1x4x3 Windows (3 bricks tall = 72 LDU)

| Part        | Description                        | Size (studs) | Height (LDU) |
|-------------|------------------------------------|--------------|--------------:|
| 60594.dat   | Window Frame 1x4x3 (no shutters)  | 1 x 4 x 3   | 72            |
| 60593.dat   | Window Frame 1x4x3 (with hinges)  | 1 x 4 x 3   | 72            |
| 60603.dat   | Glass for Window 1x4x3 (opening)  | 1 x 4 x 3   | 72            |
| 86210.dat   | Glass for Window 1x4x3 (deco)     | 1 x 4 x 3   | 72            |

**Correct pairing:** `60594.dat` + `60603.dat` (or `86210.dat`)

### 1x4x6 Door/Window (6 bricks tall = 144 LDU)

| Part        | Description                        | Size (studs) | Height (LDU) |
|-------------|------------------------------------|--------------|--------------:|
| 60596.dat   | Door/Window Frame 1x4x6           | 1 x 4 x 6   | 144           |
| 57895.dat   | Glass for Frame 1x4x6 (right hnd) | 1 x 4 x 6   | 144           |
| 57896.dat   | Glass for Frame 1x4x6 (left hnd)  | 1 x 4 x 6   | 144           |
| 35295.dat   | Glass for Window 1x4x6 (flat)     | 1 x 4 x 6   | 144           |

**Correct pairing:** `60596.dat` + `57895.dat` (door) or `60596.dat` + `35295.dat` (window)

### 1x4x3 Older Windows

| Part        | Description                        | Size (studs) | Height (LDU) |
|-------------|------------------------------------|--------------|--------------:|
| 3853.dat    | Window Frame 1x4x3 (old style)    | 1 x 4 x 3   | 72            |
| 3856.dat    | Glass for Window 1x4x3 (old)      | 1 x 4 x 3   | 72            |

### WRONG Pairings (common mistakes)

| Frame       | Glass       | Problem                                      |
|-------------|-------------|----------------------------------------------|
| 60594.dat   | 60592.dat   | 60592 is Window 1x2x2, NOT glass for 1x4x3  |
| 60594.dat   | 57895.dat   | 57895 is 1x4x6 glass, twice as tall as frame |

## Brick Parts Quick Reference

### Standard Bricks (24 LDU tall)

| Part        | Description | Width (LDU) | Depth (LDU) |
|-------------|-------------|------------:|------------:|
| 3005.dat    | Brick 1x1   | 20          | 20          |
| 3004.dat    | Brick 1x2   | 40          | 20          |
| 3622.dat    | Brick 1x3   | 60          | 20          |
| 3010.dat    | Brick 1x4   | 80          | 20          |
| 3009.dat    | Brick 1x6   | 120         | 20          |
| 3008.dat    | Brick 1x8   | 160         | 20          |
| 6112.dat    | Brick 1x12  | 240         | 20          |
| 3003.dat    | Brick 2x2   | 40          | 40          |
| 3002.dat    | Brick 2x3   | 60          | 40          |
| 3001.dat    | Brick 2x4   | 80          | 40          |
| 2456.dat    | Brick 2x6   | 120         | 40          |

### Standard Plates (8 LDU tall)

| Part        | Description | Width (LDU) |
|-------------|-------------|------------:|
| 3024.dat    | Plate 1x1   | 20          |
| 3023.dat    | Plate 1x2   | 40          |
| 3623.dat    | Plate 1x3   | 60          |
| 3710.dat    | Plate 1x4   | 80          |
| 3666.dat    | Plate 1x6   | 120         |
| 3460.dat    | Plate 1x8   | 160         |
| 4477.dat    | Plate 1x10  | 200         |
| 3020.dat    | Plate 2x4   | 80          |
| 3795.dat    | Plate 2x6   | 120         |
| 3034.dat    | Plate 2x8   | 160         |

### Tiles (8 LDU tall, no studs)

| Part        | Description | Width (LDU) |
|-------------|-------------|------------:|
| 3070b.dat   | Tile 1x1    | 20          |
| 3069b.dat   | Tile 1x2    | 40          |
| 63864.dat   | Tile 1x3    | 60          |
| 2431.dat    | Tile 1x4    | 80          |
| 6636.dat    | Tile 1x6    | 120         |
| 4162.dat    | Tile 1x8    | 160         |

## Arch Parts

| Part        | Description          | Width (LDU) | Height (LDU) |
|-------------|----------------------|------------:|--------------:|
| 3659.dat    | Arch 1x4             | 80          | 24 (1 brick)  |
| 6183.dat    | Arch 1x6x2           | 120         | 48 (2 bricks) |
| 3307.dat    | Arch 1x6x2 (thick)   | 120         | 48            |
| 3308.dat    | Arch 1x8x2           | 160         | 48            |

## Slope Parts

| Part        | Description          | Width (LDU) | Height (LDU) |
|-------------|----------------------|------------:|--------------:|
| 3040b.dat   | Slope 45 2x1         | 20          | 24            |
| 3039.dat    | Slope 45 2x2         | 40          | 24            |
| 3038.dat    | Slope 45 2x3         | 60          | 24            |
| 3037.dat    | Slope 45 2x4         | 80          | 24            |
| 85984.dat   | Slope 30 1x2x2/3     | 40          | 16            |
| 92946.dat   | Slope 30 2x2x2/3     | 40          | 16            |
| 3665.dat    | Slope Inverted 45 2x1| 20          | 24            |

## Specialty Parts

| Part        | Description             | Notes                            |
|-------------|-------------------------|----------------------------------|
| 98283.dat   | Brick 1x2 masonry       | Textured face, 40 LDU spacing   |
| 87087.dat   | Brick 1x1 stud-on-side  | SNOT building                    |
| 4070.dat    | Brick 1x1 headlight     | Recessed stud mount              |
| 30136.dat   | Palisade Brick 1x2      | Decorative vertical lines        |
| 2877.dat    | Brick 1x2 grille        | Ventilation texture              |
| 4073.dat    | Round Plate 1x1         | Flowers, buttons, details        |
| 91988.dat   | Slope Brick 1x2x2      | Floor transition edges           |

## Baseplate Parts

| Part        | Description        | Center Placement                        |
|-------------|--------------------|-----------------------------------------|
| 3811.dat    | Baseplate 32x32    | Center at (320, Y, 320) for 0-640 range |
| 3867.dat    | Baseplate 16x32    | Center at (320, Y, 160) for 0-640/0-320 |
| 3865.dat    | Baseplate 8x16     | Center at (160, Y, 80)                  |
