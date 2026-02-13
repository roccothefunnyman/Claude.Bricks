# Parts Catalog

Comprehensive reference of LDraw parts commonly used in modular building design. Parts are organized by category with dimensions in both studs and LDU.

## Bricks

| Part | Name | Width (studs) | Length (studs) | Height | LDU (WxLxH) | Notes |
|------|------|:---:|:---:|:---:|---|---|
| 3005.dat | Brick 1x1 | 1 | 1 | 1 brick | 20x20x24 | Corners, fill |
| 3004.dat | Brick 1x2 | 1 | 2 | 1 brick | 20x40x24 | Fill, small gaps |
| 3622.dat | Brick 1x3 | 1 | 3 | 1 brick | 20x60x24 | Fill |
| 3010.dat | Brick 1x4 | 1 | 4 | 1 brick | 20x80x24 | Common wall brick |
| 3009.dat | Brick 1x6 | 1 | 6 | 1 brick | 20x120x24 | Wall spans |
| 3008.dat | Brick 1x8 | 1 | 8 | 1 brick | 20x160x24 | Largest 1-wide |
| 6112.dat | Brick 1x12 | 1 | 12 | 1 brick | 20x240x24 | Long spans |
| 3003.dat | Brick 2x2 | 2 | 2 | 1 brick | 40x40x24 | Columns, corners |
| 3002.dat | Brick 2x3 | 2 | 3 | 1 brick | 40x60x24 | Floor fill |
| 3001.dat | Brick 2x4 | 2 | 4 | 1 brick | 40x80x24 | Classic brick |
| 2456.dat | Brick 2x6 | 2 | 6 | 1 brick | 40x120x24 | Floor fill |
| 3007.dat | Brick 2x8 | 2 | 8 | 1 brick | 40x160x24 | Floor fill |

### Center-Point Offset Reference (for positioning)

A brick's reference point is its **center-top**. To calculate placement coordinates:
```
X = left_edge + (length_LDU / 2)
Z = front_edge + (width_LDU / 2)
Y = top_of_brick (brick body extends downward)
```

Example: 1x4 brick at left edge X=0, front edge Z=0:
- Center X = 0 + 80/2 = 40
- Center Z = 0 + 20/2 = 10
- Place at: X=40, Z=10

## Plates (height = 8 LDU, 1/3 brick)

| Part | Name | Width (studs) | Length (studs) | LDU (WxLxH) |
|------|------|:---:|:---:|---|
| 3024.dat | Plate 1x1 | 1 | 1 | 20x20x8 |
| 3023.dat | Plate 1x2 | 1 | 2 | 20x40x8 |
| 3623.dat | Plate 1x3 | 1 | 3 | 20x60x8 |
| 3710.dat | Plate 1x4 | 1 | 4 | 20x80x8 |
| 3666.dat | Plate 1x6 | 1 | 6 | 20x120x8 |
| 3460.dat | Plate 1x8 | 1 | 8 | 20x160x8 |
| 4477.dat | Plate 1x10 | 1 | 10 | 20x200x8 |
| 3022.dat | Plate 2x2 | 2 | 2 | 40x40x8 |
| 3021.dat | Plate 2x3 | 2 | 3 | 40x60x8 |
| 3020.dat | Plate 2x4 | 2 | 4 | 40x80x8 |
| 3795.dat | Plate 2x6 | 2 | 6 | 40x120x8 |
| 3034.dat | Plate 2x8 | 2 | 8 | 40x160x8 |
| 3832.dat | Plate 2x10 | 2 | 10 | 40x200x8 |
| 3031.dat | Plate 4x4 | 4 | 4 | 80x80x8 |
| 3032.dat | Plate 4x6 | 4 | 6 | 80x120x8 |
| 3035.dat | Plate 4x8 | 4 | 8 | 80x160x8 |
| 3958.dat | Plate 6x6 | 6 | 6 | 120x120x8 |
| 3036.dat | Plate 6x8 | 6 | 8 | 120x160x8 |
| 3028.dat | Plate 6x12 | 6 | 12 | 120x240x8 |
| 3033.dat | Plate 6x10 | 6 | 10 | 120x200x8 |
| 3030.dat | Plate 4x10 | 4 | 10 | 80x200x8 |
| 3029.dat | Plate 4x12 | 4 | 12 | 80x240x8 |

## Tiles (plates with no studs on top, height = 8 LDU)

| Part | Name | Width (studs) | Length (studs) | Notes |
|------|------|:---:|:---:|---|
| 3070b.dat | Tile 1x1 | 1 | 1 | Sidewalk, detail |
| 3069b.dat | Tile 1x2 | 1 | 2 | Sidewalk, trim |
| 63864.dat | Tile 1x3 | 1 | 3 | Trim bands |
| 2431.dat | Tile 1x4 | 1 | 4 | Window sills, bands |
| 6636.dat | Tile 1x6 | 1 | 6 | Long trim |
| 4162.dat | Tile 1x8 | 1 | 8 | Long trim |
| 3068b.dat | Tile 2x2 | 2 | 2 | Floor, sidewalk |
| 87079.dat | Tile 2x4 | 2 | 4 | Floor surface |
| 15254.dat | Round Tile 1x1 | 1 | 1 | Decorative dots |

## Windows

| Part | Name | Size (studs) | Height | Notes |
|------|------|---|---|---|
| 60594.dat | Window Frame 1x4x6 | 1x4 | 6 bricks (144 LDU) | Standard large window |
| 60592.dat | Window Glass 1x4x6 | 1x4 | 6 bricks | Glass insert for 60594 |
| 3853.dat | Window 1x4x3 | 1x4 | 3 bricks (72 LDU) | Half-height window |
| 3856.dat | Window Glass 1x4x3 | 1x4 | 3 bricks | Glass for 3853 |
| 60603.dat | Window Glass 1x4x3 | 1x4 | 3 bricks | Alternate glass |
| 86209.dat | Window Frame 1x2x2 | 1x2 | 2 bricks (48 LDU) | Small window |
| 60601.dat | Window Glass 1x2x2 | 1x2 | 2 bricks | Glass for 86209 |
| 3854.dat | Window 1x4x5 | 1x4 | 5 bricks (120 LDU) | Tall window |
| 2493.dat | Window 1x4x5 w/ bars | 1x4 | 5 bricks | Barred window |

### Window Placement

Windows are placed at the **bottom** of the wall gap. The frame's reference Y is at its top, and it extends 6 bricks downward (144 LDU for 1x4x6).

```
Frame: 1 <color> <x> <y_bottom_of_gap + 144> <z> <rot> 60594.dat
Glass: 1 47     <x> <y_bottom_of_gap + 144> <z> <rot> 60592.dat
```

Glass color is typically 47 (Trans Clear).

## Doors

| Part | Name | Size | Height | Notes |
|------|------|---|---|---|
| 60596.dat | Door Frame 1x4x6 | 1x4 | 6 bricks (144 LDU) | Standard door frame |
| 57895.dat | Door 1x4x6 (right) | 1x4 | 6 bricks | Right-hinge door panel |
| 57896.dat | Door 1x4x6 (left) | 1x4 | 6 bricks | Left-hinge door panel |
| 60616.dat | Door 1x4x6 w/ stud | 1x4 | 6 bricks | Alternate frame |
| 60623.dat | Door 1x4x3 | 1x4 | 3 bricks | Half-height door/gate |

### Door Placement
Same approach as windows — placed at bottom of wall gap. Doors always go on the ground floor, typically on the front wall.

## Slopes

| Part | Name | Size | Angle | Notes |
|------|------|---|---|---|
| 3040b.dat | Slope 45 2x1 | 2x1 | 45 deg | Roof, cornice |
| 3039.dat | Slope 45 2x2 | 2x2 | 45 deg | Roof |
| 3038.dat | Slope 45 2x3 | 2x3 | 45 deg | Roof |
| 3037.dat | Slope 45 2x4 | 2x4 | 45 deg | Roof |
| 85984.dat | Slope 30 1x2x2/3 | 1x2 | 30 deg | Gentle cornice |
| 92946.dat | Slope 30 2x2x2/3 | 2x2 | 30 deg | Gentle cornice |
| 3665.dat | Slope Inv 45 2x1 | 2x1 | 45 deg inv | Under-cornice |
| 3660.dat | Slope Inv 45 2x2 | 2x2 | 45 deg inv | Under-cornice |

### Slope Orientation
Slopes face "down" in their default orientation. To make them face different directions, apply rotation matrices. A 45-degree slope on a left-to-right roof:
- Front-facing: default rotation
- Right-facing: 90 deg CW rotation
- Back-facing: 180 deg rotation
- Left-facing: 270 deg rotation

## Specialty / SNOT Parts

| Part | Name | Notes |
|------|------|---|
| 87087.dat | Brick 1x1 w/ stud on side | SNOT - sideways building |
| 4070.dat | Brick 1x1 w/ headlight | SNOT - recessed stud, lighting grid |
| 98283.dat | Brick 1x2 w/ masonry profile | Textured facade (heavy use in refs) |
| 2877.dat | Brick 1x2 w/ grille | Ventilation, texture |
| 30136.dat | Palisade Brick 1x2 | Wall texture, roof trim (rotated 90°) |
| 98138.dat | Round Tile 1x1 | Button, rivet detail |
| 4073.dat | Round Plate 1x1 | Lamp, rivet, roof finial |
| 6141.dat | Round Plate 1x1 | Alternate round plate |
| 3062b.dat | Round Brick 1x1 | Column detail, roof ridge |
| 85080.dat | Pin Tile 2x2 Round | Decorative circle |
| 4081b.dat | Brick 1x1 w/ studs on 4 sides | Sign/billboard SNOT mounting |
| 3794b.dat | Plate 1x2 w/ door rail | Dentil cornice element |
| 62113.dat | Turntable 2x2 | Revolving door/secret door |

### Reference Usage Context

**98283.dat (Masonry):** Detective's Office uses 46x in wall rows. Place with alternating rotation between rows: odd rows use `0 0 1 0 1 0 -1 0 0`, even rows use identity. Offset 20-40 LDU between rows to prevent vertical seams.

**87087.dat (SNOT):** Cardinal rotations only (studs face ±X or ±Z). Used at building corners for depth, and in interior for shelf/detail mounting.

**4070.dat (Headlight):** Place in grids every 60 LDU for lighting/detail. Use inverted rotation `1 0 0 0 -1 0 0 0 -1` for ceiling mounts. Also used as roof finials along roofline.

**30136.dat (Palisade):** Pet Shop uses for vertical wall texture AND rotated 90° (`0 0 -1 0 1 0 1 0 0`) as decorative roof trim. Creates fence-like edge.

**4073.dat (Round plate):** Detective's Office uses 19x as decorative roof finials at 60 LDU spacing along roofline. Also above doors as ornamental accent.

**3794b.dat (Door rail plate):** Both reference sets use for dentil cornice bands. Rotation `0 0 1 0 1 0 -1 0 0` makes it protrude 1 stud from wall face. Space every 40 LDU.

## Fence / Railing Parts

| Part | Name | Notes |
|------|------|---|
| 3633.dat | Fence 1x4x1 | Simple picket fence |
| 15332.dat | Fence 1x4x2 | Ornamental fence |
| 30055.dat | Fence 1x4x2 | Spindled railing |
| 3185.dat | Fence 1x4x2 | Lattice style |

## Baseplates

| Part | Name | Size (studs) | LDU | Notes |
|------|------|:---:|---|---|
| 3811.dat | Baseplate 32x32 | 32x32 | 640x640 | Standard modular base |
| 3867.dat | Baseplate 16x32 | 16x32 | 320x640 | Half-width module |
| 3865.dat | Baseplate 8x16 | 8x16 | 160x320 | Small vignette |

### Baseplate Placement
Baseplates are positioned by **center-top**, same as all parts. For a 32x32 baseplate:
```
Center X = 320, Center Z = 320
Place at: (320, 140, 320) for standard ground level
```
Baseplates are very thin (~3 LDU) and serve as the foundation layer.

## Arch Parts

| Part | Name | Size | Height | Notes |
|------|------|---|---|---|
| 3659.dat | Arch 1x4 | 1x4 | 2 bricks (48 LDU) | Simple arch |
| 6183.dat | Arch 1x4x3 | 1x4 | 3 bricks (72 LDU) | Tall arch |
| 3307.dat | Arch 1x6x2 | 1x6 | 2 bricks (48 LDU) | Wide arch |
| 3308.dat | Arch 1x8x2 | 1x8 | 2 bricks (48 LDU) | Very wide arch |
| 2339.dat | Arch 1x5x4 | 1x5 | 4 bricks (96 LDU) | Doorway arch |

### Arch Placement with Windows
When combining an arch piece above a window frame, calculate Y positions carefully:
```
Window frame (60594.dat, 6 bricks = 144 LDU):
  Place at Y where frame bottom = ground level
  Y_window = ground_Y - 144   (e.g., 140 - 144 = -4)

Arch (3307.dat, 2 bricks = 48 LDU):
  Place so arch bottom touches window top
  Y_arch = Y_window - 48      (e.g., -4 - 48 = -52)

Wall gap: must span from ground to arch top
  Gap rows = rows covering Y_ground to Y_arch
```
The arch is typically wider than the window (e.g., 6-stud arch over 4-stud window), creating a recessed look.

## Bracket Parts

| Part | Name | Notes |
|------|------|---|
| 44728.dat | Bracket 1x2 - 2x2 | Right-angle SNOT |
| 99207.dat | Bracket 1x2 - 1x2 | Compact SNOT |
| 28802.dat | Bracket 1x2 - 1x2 inv | Inverted bracket |
| 93274.dat | Bracket 1x2 - 2x4 | Large SNOT bracket |
