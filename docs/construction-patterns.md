# Construction Patterns from Official LEGO Modular Buildings

Reference files analyzed:
- **10246 Detective's Office** (2,411 lines, 3 stories + roof)
- **10218 Pet Shop** (2,134 lines, 2 halves x 3 stories + roof)

---

## 1. Submodel Structure

Both official sets use the same pattern:

- All submodels referenced at **origin (0, 0, 0)** with **identity rotation**
- Each submodel uses **absolute Y-coordinates** (not relative to parent)
- Floors are independent — Y determines vertical position
- Reference color is typically **72** (neutral placeholder)

```
0 FILE MainModel.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 first_floor.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 second_floor.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 roof.ldr
0 NOFILE
```

Nested submodels (furniture, minifigures) ARE offset from parent when referenced.

---

## 2. Wall Construction

### Front Wall
- Wall bricks placed at a **fixed Z value** for the front face
- Parts centered on their X position
- **Running bond**: alternate rows offset by 20 LDU (1 stud)

### Side Walls
- Use **90-degree rotation** (0 0 -1 0 1 0 1 0 0) to run along Z-axis
- Same Y-level stacking as front wall

### Back Wall
- Use **180-degree rotation** (-1 0 0 0 1 0 0 0 -1)
- Same X positions as front wall

### Corner Construction
- Walls end at the corner — next wall takes over
- No overlapping corner bricks needed
- Clean perpendicular junction from rotation differences

### Masonry Pattern (98283.dat)
- Space masonry bricks every **40 LDU** (2 studs apart)
- Alternate rotation every row:
  - Odd rows: perpendicular (0 0 1 0 1 0 -1 0 0)
  - Even rows: identity (1 0 0 0 1 0 0 0 1)
- This prevents coincident studs between rows

---

## 3. Floor Separation (CRITICAL)

### Key Discovery: Floor plates do NOT extend to exterior walls

In both official sets, floor/ceiling plates are **interior only**:
- Pet Shop: floor plates at Z ~ -150 to -200, while front wall at Z = -290
  (100-140 LDU gap between floor plates and front wall)
- Detective's Office: interior tiles cluster in center area,
  walls at edges contain no floor plate references

### Wall Continuity Through Floor Level

Walls are **continuous through the floor separation zone**. There is no interruption.
The wall bricks stack from one floor to the next without gaps.

### Floor Transition Construction

Instead of simple plate layers, official sets use:
1. **Slope bricks** (91988.dat) at floor edges for visual separation
2. **Interior tiles/plates** for the actual floor surface
3. **Wall bricks continue** at the floor Y-level (no gap)

### What This Means for Our Builds

**WRONG approach (what we were doing):**
```
# Floor plates spanning full width at front wall Z
FillXPlate $LtGray 0 640 -156 10   # plates at Z=10 (front wall!)
FillXPlate $LtGray 0 640 -156 30
FillXPlate $LtGray 0 640 -156 50   # ... etc across full depth
```

**CORRECT approach (from reference files):**
```
# Walls are continuous — add wall brick rows at floor separation Y
FillX $WallColor 0 640 -156 $FZ    # wall continues at front
FillX $WallColor 0 640 -156 $BZ    # wall continues at back
FillZ $WallColor 0 640 -156 $LX    # side walls continue
FillZ $WallColor 0 640 -156 $RX    # side walls continue

# Floor plates are INTERIOR only (not at wall positions)
for ($z = $FZ + 20; $z -le $BZ - 20; $z += 20) {
    FillXPlate $LtGray 20 620 -156 $z   # interior only
}
```

---

## 4. Window Construction

### Window Sizing

Both official sets primarily use **1x4x3 windows** (60594.dat, 60593.dat).
These are **3 bricks tall (72 LDU)**, NOT 6 bricks.

A 1x4x3 window needs a **3-row gap** in the wall, not 6 rows.

### Frame + Glass Placement

Two approaches found in official sets:

**Approach A: Same coordinates (Pet Shop)**
```
1 15 -100 -224 150  -1 0 0 0 1 0 0 0 -1  60593.dat   # frame
1 47 -100 -224 150  -1 0 0 0 1 0 0 0 -1  60602.dat   # glass
```
Frame and glass at identical (X, Y, Z) with same rotation.

**Approach B: Offset glass (Detective's Office)**
```
1 70 -60 -128 190  1 0 0 0 1 0 0 0 1  60594.dat      # frame
1 47 -60 -120 195  1 0 0 0 0.97 -0.26 0 0.26 0.97  86210.dat  # glass
```
Glass offset +8 Y, +5 Z from frame, with 15-degree rotation (open position).

**For our builds**: Use Approach A (same coordinates) for simplicity.

### Wall Gap for 1x4x3 Windows

Window frame 60594.dat is 80 LDU wide (4 studs) and 72 LDU tall (3 bricks).

To place a window:
1. Leave a gap of **80 LDU** in wall X-positions (gap: {s=X-40, e=X+40})
2. Skip wall rows for **3 brick heights** at window location
3. Place frame at Y = top of gap (same Y as the highest skipped row)
4. Place glass at same coordinates as frame

**Example for window centered at X=320, with window top at Y=-188:**
```
# Gap in wall: rows at Y=-188, -212, -236 skip X=280 to X=360
$windowGap = @(@{s=280; e=360})

# Rows 1-3 have gap (window zone), rows 4+ are solid
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    if ($row -le 3) {
        WallRowX $color $xMin $xMax $y $FZ $windowGap $off
    } else {
        FillX $color $xMin $xMax $y $FZ $off
    }
}

# Window frame + glass (at Y of row 3 = -164 - 3*24 = -236)
B 15 320 -236 $FZ "60594.dat" $R0
B 47 320 -236 $FZ "60603.dat" $R0
```

### For Tall 1x4x6 Windows/Doors

If you want floor-to-ceiling windows (6 bricks, 144 LDU):
- Use **60596.dat** (frame) + **57895.dat** (glass/door panel)
- Skip **6 rows** of wall bricks
- These are the same parts as our door placement

---

## 5. Window Sill and Header

Official sets often include:

### Below Window (Sill)
- A plate or tile row at the window's bottom Y-level
- Creates a visual ledge
- Can use 3710.dat (1x4 plate) or 2431.dat (1x4 tile)

### Above Window (Header)
- A plate or tile spanning the gap width
- Often in accent color
- Creates visual frame around window

### Example
```
# Window sill (plate below window)
B $accent ($winX) ($winBottomY + 8) $FZ "3710.dat" $R0

# Window header (plate above window)
B $accent ($winX) ($winTopY - 8) $FZ "3710.dat" $R0
```

---

## 6. Roof and Parapet

### Roof Plate Platform
- Flat plates across the top of the building
- **Interior only** — don't extend past wall faces

### Parapet
- Additional brick rows above the roof plate
- Typically 1-2 bricks tall
- Cap with tile row (smooth top)
- Should wrap all 4 sides

### Slope Roof
- Paired slopes meeting at ridge:
  ```
  B $Roof $x $y $z     "3040b.dat" $R0     # front slope
  B $Roof $x $y ($z+20) "3040b.dat" $R180  # back slope (inverted)
  ```

### Decorative Corbels
- Place inverted slopes (3665.dat) below parapet overhang
- Position in FRONT of the wall (Z < wall Z) to avoid collision with roof plates

---

## 7. Color Conventions (from reference files)

| Role              | Typical Colors                                    |
|-------------------|---------------------------------------------------|
| Primary walls     | 72 (Dk Blue Gray), 28 (Dk Tan), 19 (Tan)         |
| Secondary walls   | 71 (Lt Blue Gray), 212 (Bright Lt Blue)           |
| Window frames     | 15 (White), 70 (Reddish Brown)                    |
| Window glass      | 47 (Trans Clear)                                  |
| Floor plates      | 71 (Lt Blue Gray) interior only                   |
| Trim/accent       | 72 (Dk Blue Gray), 0 (Black)                      |
| Submodel refs     | 72 (neutral) or 16 (inherit)                      |

---

## 8. Spacing and Collision Rules

### Standard Spacing
- Bricks: 40 LDU (2 studs) center-to-center for masonry
- Plates: 20 LDU (1 stud) for floor fills
- Windows: 80-100 LDU center-to-center

### Collision Prevention
- Parts at same (X, Y, Z) with same rotation = collision
- Parts at same (X, Y, Z) but perpendicular rotations = accepted at corners
- Floor plates + wall bricks at same position but different orientation = collision risk
- **Solution**: Keep floor plates interior, keep walls continuous

### Corner Handling
- No special corner pieces needed
- Walls naturally end at corner
- Perpendicular wall takes over
- Stagger between rows prevents visual seams
