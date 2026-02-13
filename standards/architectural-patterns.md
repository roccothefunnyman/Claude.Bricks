# Architectural Patterns

Proven design patterns for modular LEGO building facades, roofs, and details. Each pattern includes the parts used and placement logic for use in generation scripts.

---

## Facade Patterns

### 1. Smooth Brick Wall
The simplest wall — standard bricks with staggered joints.

```
Row 1: FillX with offset=0  →  |--1x4--|--1x6--|--1x8--|--1x4--|...
Row 2: FillX with offset=20 →  |-1x2|--1x8--|--1x6--|--1x4--|--1x2|
Row 3: FillX with offset=0  →  (repeat pattern)
```
Stagger by alternating a half-brick (1x1 or 1x2) offset every other row.

### 2. Masonry / Textured Wall
Uses 98283.dat (Brick 1x2 with masonry profile) for a stone-block look.

**Confirmed pattern from Detective's Office (10246):**
```
APPROACH A — Masonry in every row, alternating rotation:
  Odd rows:  rotation  0 0 1 0 1 0 -1 0 0   (perpendicular, runs along Z)
  Even rows: rotation  1 0 0 0 1 0  0 0 1   (identity, runs along X)
  Offset 20-40 LDU between rows to prevent vertical seams.
  Color: alternate 71/72 between rows for visual interest.

APPROACH B — Masonry as horizontal trim band (Pet Shop 10218):
  Place masonry at a SEPARATE Z-plane from main wall (e.g., Z=-160 vs wall at Z=-150).
  Space every 20 LDU (1 stud) in X direction.
  Rotation: 0 0 -1 0 1 0 1 0 0 (90° CW, perpendicular to wall).
  Use different color from wall (e.g., 19 Tan band on 71 Gray wall).
  Creates a water table / accent band effect.
```

**Script helper pattern:**
```powershell
function MasonryRowX($color, $x1, $x2, $y, $z, $rot) {
    for ($x = $x1; $x -lt $x2; $x += 40) {
        B $color $x $y $z $rot "98283.dat"
    }
}
# Alternate rotation each row:
MasonryRowX $Primary $x1 $x2 $y $z "0 0 1 0 1 0 -1 0 0"      # odd row
MasonryRowX $Primary $x1 $x2 ($y - 24) $z "1 0 0 0 1 0 0 0 1" # even row
```
Works well with Dark Tan (28), Tan (19), or Light Bluish Gray (71).

### 3. SNOT Panel (Sideways Detail)
Uses 87087.dat (Brick 1x1 with stud on side) to attach tiles/plates sideways for smooth or decorative panels.

```
1. Place row of 87087.dat bricks on the facade, studs facing outward
2. Attach tiles (3070b, 3069b) sideways onto the outward-facing studs
3. Creates a flush decorative panel
```
Common for shop signs, decorative panels between windows.

### 4. Pilaster / Column
Vertical decorative column on a facade using brick stacking:

```
Stack 1x1 bricks or 1x2 bricks vertically at fixed X position
Use contrasting color (e.g., white pilasters on a tan wall)
Top with a 1x1 plate or tile cap
```
Place at building corners and between windows for classical look.

### 5. Quoin Pattern (Corner Stones)
Alternating-size blocks at building corners:

```
Row 1: 1x2 brick at corner
Row 2: 1x1 brick at corner
Row 3: 1x2 brick at corner
(alternate)
```
Use contrasting color. Common in Georgian/Classical architecture.

---

## Between-Floor Patterns

### 6. Accent Band
A horizontal color band separating floors, built from plates or tiles:

```
1 plate layer in accent color:
  FillXPlate($AccentColor, $x1, $x2, $Y_between_floors, $z)

Or 1 tile layer for smooth look:
  FillXTile($AccentColor, $x1, $x2, $Y_between_floors, $z)
```
Width: full building span. Color: secondary or trim color.

### 7. Corbel / Ledge Band
A protruding band between floors created by offsetting plates:

```
Layer 1: Standard plates at wall line (Z=10)
Layer 2: Plates offset outward by half stud (Z=0 for front wall)
Creates a visible ledge / drip molding effect
```
Requires careful Z-coordinate adjustment.

### 8. Dentil Band
Alternating brick/gap pattern for classical detailing.

**Confirmed pattern from Detective's Office (10246):**
Uses 3794b.dat (1x2 tile) instead of regular bricks, mounted wall-perpendicular:
```
Part:     3794b.dat (1x2 tile)
Rotation: 0 0 1 0 1 0 -1 0 0  (perpendicular to wall face)
Spacing:  40 LDU (2 studs) between each tile along wall
Effect:   Each tile protrudes 1 stud from wall face
Color:    Same as wall (71) or accent (72)

Script pattern:
  for ($x = $x1; $x -le $x2; $x += 40) {
      B $color $x $y $z "0 0 1 0 1 0 -1 0 0" "3794b.dat"
  }
```

**Alternative from Pet Shop (10218):**
Uses 3794a.dat (1x2 masonry profile) for a heavier dentil appearance:
```
Same rotation and spacing as above.
Creates a more pronounced relief pattern.
```
Place below cornice for classical/neoclassical buildings. Runs along all exterior walls (wrap corners).

---

## Cornice / Crown Molding Patterns

### 9. Simple Plate Overhang
The easiest roof cornice:

```
1. Wall ends at Y_top
2. Plate layer at Y_top - 8, extending 1 stud beyond wall face:
   - Front wall plates at Z=0 instead of Z=10 (overhang toward viewer)
   - Side wall plates similarly offset outward
3. Optional: tile on top of overhang plate for smooth finish
```

### 10. Slope Cornice
More elaborate cornice with slope elements.

**Confirmed multi-layer pattern from references:**
```
Visual cross-section (front wall):
  [   tile cap   ]  ← tile at Z=-10
  [ inv slope    ]  ← 3665.dat at Z=0, angled
  [  plate       ]  ← plate at Z=0 (overhanging)
  |    wall      |  ← wall at Z=10

Inverted slope rotation (facing outward from front wall):
  3665.dat with rotation: -1 0 0 0 1 0 0 0 -1  (180° = inverted, faces viewer)

Serrated fascia edge (Detective's Office):
  3665.dat (1x1 slope 45°) placed every 20-40 LDU along wall edge
  Creates sawtooth silhouette at roofline
  Combined with 3062b.dat (1x2 slope) for complementary pattern
```

**Tiered cornice (Pet Shop):**
```
Layer 1 (Y=base):    Palisade trim (30136.dat) rotated 90°
Layer 2 (Y=base-8):  Plate (3023.dat) as transition
Layer 3 (Y=base-32): 2x2 brick cap (3062b.dat)
Each layer 8-24 LDU apart, creating stepped pyramid profile
```

### 11. Stepped Cornice
Multiple plate layers stepping outward:

```
Layer 1: Plate at wall line (Z=10)
Layer 2: Plate offset out 1 stud (Z=-10 or Z=0)
Layer 3: Plate offset out another stud (Z=-30 or Z=-10)
Each layer: Y decreases by 8 (plate height)
```
Creates a pyramid-profile overhang. Classic on brownstones.

---

## Window Patterns

### 12. Standard Window with Sill
```
1. Wall gap: 4 studs wide, 6 rows tall
2. Window frame (60594.dat) placed at bottom of gap
3. Window glass (60592.dat) at same position
4. Below window: tile across gap width as window sill
   - 2431.dat (1x4 tile) in trim color, Y = one plate below frame bottom
```

### 13. Window with Lintel
```
1. Same as standard window
2. Above window gap: contrasting color brick row spanning gap + 1 stud on each side
   - E.g., 1x6 brick in trim color where the gap is only 4 studs
   - Creates a stone lintel effect
```

### 14. Arched Window
```
1. Wall gap: 4 studs wide (for 1x4 arch), 7+ rows tall
2. Arch piece (3659.dat) at top of gap
3. Window frame below arch
4. Or: arch only (no glass) for decorative openings
```

### 14b. Wide Arched Window with Frame (Townhouse pattern)
Combines a wide arch (6-8 studs) with a standard 4-stud window frame inside.

```
Y coordinate calculation (ground floor, ground=140):
  Window (60594.dat, 6 bricks):  Y_win = 140 - 144 = -4
  Arch (3307.dat, 2 bricks):    Y_arch = -4 - 48 = -52

Wall gap: X=60 to X=180 (6 studs), rows 1-8 (Y=116 to Y=-52)
  - Rows 1-6: clear opening (window fills this)
  - Rows 7-8: arch piece fills this
  - Rows 9+: solid wall above

Script pattern:
  # Wall rows with arch gap
  for ($row = 1; $row -le 12; $row++) {
      $y = 140 - $row * 24
      if ($row -le 8) {
          WallRowX $color $x1 $x2 $y $z $archGap ($row % 2 * 20)
      } else {
          FillX $color $x1 $x2 $y $z ($row % 2 * 20)
      }
  }
  # Arch above window
  B $color $archCenterX -52 $z "3307.dat" $R0
  # Window inside arch
  PlaceWindow $White $archCenterX -4 $z
```

**Note:** The window (4 studs) is narrower than the arch (6 studs), creating a recessed alcove effect. The 1-stud gap on each side looks like reveal/depth in the arch opening.

### 15. Symmetric Window Arrangement
For a 32-stud-wide facade with 3 windows on upper floor:

```
Window 1 center: X = 6 studs from left  → X = 120 LDU
Window 2 center: X = 16 studs (center)  → X = 320 LDU
Window 3 center: X = 26 studs from left → X = 520 LDU

Gap between windows: 6 studs (120 LDU) of wall
Gap at edges: 4 studs (80 LDU) of wall
```

For 2 windows:
```
Window 1 center: X = 10 studs → X = 200 LDU
Window 2 center: X = 22 studs → X = 440 LDU
```

---

## Roof Patterns

### 16. Flat Roof with Parapet
Most common for modular buildings:

```
1. Roof plates spanning full building footprint at ceiling level
2. Parapet walls: 1-2 brick rows on all 4 edges above roof plates
3. Parapet cap: tiles on top of parapet for finished look
4. Optional: coping stones (1x1 tiles in alternating color)
```

### 17. Roof with Raised Parapet (varying height)
```
Front parapet: 3 bricks tall (visible from street)
Side parapets: 2 bricks, tapering to 1 brick toward back
Back parapet: 1 brick tall
Creates a graded profile
```

### 18. Sloped Roof (simple)
```
1. Roof plates at ceiling level
2. Slope bricks (3037.dat = 2x4 slope, 3039.dat = 2x2 slope) on front and back
   - Front slopes face forward (default rotation)
   - Back slopes face backward (180 deg rotation)
3. Ridge cap: tiles or plates along the peak
4. Side walls: stepped gable or filled with slopes
```

**Confirmed rotation matrices for slopes:**
```
Front-facing slope:  1 0 0 0 1 0 0 0 1    (identity — default direction)
Back-facing slope:  -1 0 0 0 1 0 0 0 -1   (180° — inverted for opposite side)
Left-facing slope:   0 0 1 0 1 0 -1 0 0   (90° CW)
Right-facing slope:  0 0 -1 0 1 0 1 0 0   (270° CW)
```

**Paired slope ridge (Pet Shop):**
```
Two slopes meeting at a ridge line, 20 LDU (1 stud) apart in Z:
  B $RoofColor $x $y  $z      "1 0 0 0 1 0 0 0 1"    "3040b.dat"  # up-slope
  B $RoofColor $x $y ($z+20) "-1 0 0 0 1 0 0 0 -1"   "3040b.dat"  # down-slope
Creates a peaked/V-shaped ridge profile.
```

**Multi-layer roof (Detective's Office — 4 layers):**
```
Layer 1 (Y=base):      Platform plates (3036.dat 6x8, tiles)
Layer 2 (Y=base-8):    Support structure (32028.dat 1x6 plates, slopes)
Layer 3 (Y=base-32):   Gable walls (3009.dat 1x6 bricks) + fascia
Layer 4 (Y=base-40+):  Serrated edge (3665.dat slopes) + SNOT finials (4070.dat)
Total roof height: ~56-80 LDU (2-3 bricks)
```

### 19. Chimney
```
1. Rectangular stack of bricks (2x2 or 2x1) rising from roof
2. Typically 3-5 bricks tall above roof line
3. Cap: plate overhang + tiles on top
4. Color: match roof (Dark Bluish Gray) or contrasting (Reddish Brown)

Position: offset from center, typically rear half of building
```

---

## Ground Level Patterns

### 20. Sidewalk
```
1. 2-3 stud strip along front of building (Z direction)
2. Covered with tiles in Light Bluish Gray (71):
   - FillXTile(71, $x1, $x2, $Y_ground, $z_sidewalk)
3. Optional: round tiles (15254.dat) at corners for texture
4. Optional: dark gray (72) grate tile pattern
```

### 21. Storefront Window
Large ground-floor display window:

```
1. Wall gap: 8-12 studs wide, 6 rows tall
2. Multiple window frames side by side, or
3. Trans Clear plates stacked to create a plate-glass window
4. 1-brick knee wall below window (solid wall section at bottom)
```

### 22. Awning / Canopy
```
1. Row of brackets (44728.dat) mounted to wall via SNOT
2. Slope bricks (3040b.dat) on top of brackets, angled outward
3. Or: plate overhang supported by bracket pieces

Color: accent or contrasting (common: 4=Red, 1=Blue, 2=Green)
Position: above storefront window or door
```

### 23. Door Surround
```
1. Door frame (60596.dat) in gap
2. Door panel (57895.dat) in accent color
3. Pilaster bricks flanking the door (1x1 brick columns in trim color)
4. Lintel above door: contrasting brick or arch piece
5. Optional: 1x1 round plate (4073.dat) as door knob in Pearl Gold (297)
```

---

## Detail Patterns

### 24. Flower Box / Window Box
```
1. Bracket (44728.dat) mounted below window
2. Small plate on bracket
3. Flower/plant elements on plate
4. Color: Green (2) or Bright Green (326) for plants
```

**Simplified window box (no bracket, Townhouse pattern):**
```
For upper-floor windows: place a 1x4 plate (3710.dat) in Brown (6) at
the floor separation plate level (Y = floor_sep_Y), offset 1 stud
in front of wall (Z = wall_Z - 20). Add 1x1 round plates (4073.dat)
on top in Yellow (14) and Green (10) as flowers.

Script pattern:
  function WindowBox($x, $y, $z) {
      B $Brown $x $y $z "3710.dat" $R0        # shelf
      B $Yellow ($x-20) ($y-8) $z "4073.dat"  # flower
      B $Green  $x      ($y-8) $z "4073.dat"  # flower
      B $Yellow ($x+20) ($y-8) $z "4073.dat"  # flower
  }

Ground-floor caveat: if windows start at ground level (Y=140),
there is no room below them for a wall-mounted box. Options:
  A. Place the box AT ground level in front of the wall as a planter
     (Y=140, Z = wall_Z - 20)
  B. Use half-height windows (3853.dat) raised 2-3 rows above ground
     to leave room for a box below
  C. Skip ground-floor boxes (common in real architecture)
```

### 25. Lamp / Lantern
```
1. 1x1 round plate (4073.dat) or bar piece mounted to wall
2. Trans Yellow (46) round tile or plate as light
3. Position: beside door or between windows on upper floors
```

### 26. Sign / Lettering
```
1. SNOT bricks (87087.dat) placed on facade
2. Tiles attached sideways in contrasting colors to spell text
3. Or: printed tile parts if available
4. Position: above storefront, between floors
```

### 27. Balcony
```
1. Plate extending 2-3 studs beyond wall face at floor separation level
2. Fence elements (3633.dat, 15332.dat) around plate edges
3. Tile on top of plate for smooth floor
4. Support: brackets or corbel pieces underneath
```

---

## Reference-Confirmed Patterns

Patterns verified across Detective's Office (10246), Pet Shop (10218), and Assembly Square:

### Submodel Organization (confirmed in all sets)
```
Split building into floor-level submodels:
  0 FILE BuildingName FIRST FLOOR.ldr
  0 FILE BuildingName SECOND FLOOR.ldr
  0 FILE BuildingName THIRD FLOOR.ldr
  0 FILE BuildingName ROOF.ldr

Detail submodels for reusable elements:
  0 FILE BuildingName STAIRS.ldr
  0 FILE BuildingName SIGN.ldr
  (furniture, minifigs, mechanical elements)

All referenced from master file at origin with identity rotation.
```

### Color Hierarchy (confirmed in all sets)
```
Ground floor:   Warm tones (70 Reddish Brown, 28 Dark Tan) or neutral (71)
Upper floors:   Light neutral (71 Light Bluish Gray)
Roof:           Dark (72 Dark Bluish Gray, 0 Black)
Window frames:  15 White (always)
Glass:          47 Trans Clear (always)
Trim/accents:   Contrasting secondary color

Transition: No sharp color breaks. Use accent bands or gradual mixing.
Upper floors get MORE decorative detail (most visible from street).
```

### Floor Separation (confirmed: multi-layer, not single plate)
```
NOT just 2 plates (16 LDU). Real buildings use 40-56 LDU multi-layer:
  Layer 1: Plates at wall-top level
  Layer 2: Support bricks/connectors (cross-grain for locking)
  Layer 3: Major floor plates (2x4, 2x6, spanning full width)
  Layer 4: Base bricks for next floor

This distributes load and allows complex geometry between stories.
```

### Window/Door Framing (confirmed standard)
```
Frame:    60594.dat (window) or 60596.dat (door) in color 15 (White)
Glass:    60592.dat or 60602.dat in color 47 (Trans Clear)
Rotation: Identity for front wall, 90° for side walls
Surround: 60623.dat (door trim) offset from frame center

Always place frame and glass at SAME coordinates.
Glass offset 5-10 LDU in Z for depth effect (optional).
```

### SNOT Mounting Grid (confirmed in both sets)
```
87087.dat (stud-on-side) placed at building corners and detail points
4070.dat (headlight brick) in regular grids (every 60 LDU) for lighting/detail

Cardinal rotations only — studs point toward ±X or ±Z, never ±Y:
  +X facing:  1 0 0 0 1 0 0 0 1   (identity)
  -X facing: -1 0 0 0 1 0 0 0 -1  (180°)
  +Z facing:  0 0 1 0 1 0 -1 0 0  (90°)
  -Z facing:  0 0 -1 0 1 0 1 0 0  (270°)
```

### Palisade Brick Usage (confirmed in Pet Shop)
```
30136.dat (Palisade Brick 1x2) used for:
  - Vertical wall posts at regular intervals (corners, between windows)
  - Decorative roof trim (rotated 90°, creates fence-like edge)
  - Log cabin / rustic texture

Rotation: 0 0 -1 0 1 0 1 0 0 for perpendicular placement
```

### Cylindrical Construction (Detective's Office tank)
```
12 tiles (63864.dat 1x3 tile) arranged radially at 30° increments:
  For angle θ (0°, 30°, 60°, ... 330°):
    X = center_x + radius × cos(θ)
    Z = center_z + radius × sin(θ)
    Rotation matrix (around Y-axis):
      cos(θ)  0  sin(θ)
        0     1    0
     -sin(θ)  0  cos(θ)

  Common values: cos(30°)=0.866025, sin(30°)=0.5
                 cos(60°)=0.5,      sin(60°)=0.866025
                 cos(45°)=0.707107, sin(45°)=0.707107
```

### 45° Diagonal Elements (Pet Shop chevron roof)
```
Bricks rotated 45° around Y-axis for herringbone/chevron patterns:
  Rotation: 0.707107 0 -0.707107 0 1 0 0.707107 0 0.707107
  (or negative variant for opposite direction)

Space every 40 LDU (2 studs) in X direction.
Creates dynamic visual pattern on roofs or facade panels.
```

### Staircase Construction (confirmed in both sets)
```
Base platform:  2x4 plate (3020.dat) at Y=0 (local)
Steps:          Plates at Y-8 increments (1/3 brick per step)
Risers:         30413.dat slope or 3660.dat bricks
Handrails:      1x4 bricks (3021.dat) rotated 90° at ±20 LDU from center
Total drop:     32 LDU (1⅓ bricks) per staircase section
```

### Sign / Billboard (Detective's Office enseigne)
```
SNOT sandwich construction:
  1. Back support: plates and slopes as structural frame
  2. SNOT bricks: 4081b.dat (4-side studs) as mounting points
  3. Front face: tiles/printed elements attach to forward-facing studs
  4. Dual-layer for depth (back panel mirrored)
Place as submodel, reference from main building at sign location.
```

### Furniture Rotation Conventions
```
Aligned with room:   1 0 0 0 1 0 0 0 1     (identity)
Angled 30°:          0.866025 0 0.5 0 1 0 -0.5 0 0.866025
Angled 45°:          0.707107 0 0.707107 0 1 0 -0.707107 0 0.707107
Perpendicular:       0 0 1 0 1 0 -1 0 0    (90°)
Opposite wall:      -1 0 0 0 1 0 0 0 -1    (180°)

Use varied angles for realistic room layouts (not everything grid-aligned).
```
