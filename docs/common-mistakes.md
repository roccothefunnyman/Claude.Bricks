# Common Mistakes and How to Fix Them

Lessons learned from building the European Townhouse (v1-v3) and analyzing
official LEGO modular building sets (10246 Detective's Office, 10218 Pet Shop).

---

## Mistake 1: Wrong Window Part Pairing

### What we did wrong
CLAUDE.md listed 60594.dat as "Window Frame 1x4x6" and 60592.dat as
"Window Glass 1x4x6". Both are wrong:

- **60594.dat** = Window Frame 1x4x**3** (3 bricks tall, 72 LDU)
- **60592.dat** = Window 1x2x**2** (completely different part!)

### Impact
- 6-row wall gaps for 3-row windows = huge holes in the wall
- Wrong glass part doesn't match frame at all
- Visible structural gaps in every stud.io render

### Correct pairings
```
1x4x3 window: 60594.dat (frame) + 60603.dat (glass)
1x4x6 door:   60596.dat (frame) + 57895.dat (door glass)
1x4x6 window: 60596.dat (frame) + 35295.dat (window glass)
```

### Wall gap calculation
For 1x4x3 window (60594.dat): skip **3 rows** (72 LDU)
For 1x4x6 window (60596.dat): skip **6 rows** (144 LDU)

---

## Mistake 2: Floor Plates Extending to Exterior Walls

### What we did wrong
Floor separation plates filled the entire footprint including the front wall
position (Z=10), side walls (X=10, X=630), and back wall (Z=630).

```powershell
# WRONG — plates at front wall Z=10
for ($z = 10; $z -le 630; $z += 20) {
    FillXPlate $LtGray 0 640 -156 $z
}
```

### Impact
- Grey floor plates visible on all exterior faces at floor separation level
- Collision with wall bricks at junction points
- Attempts to color the edge plates created complexity without fixing root cause

### What official sets do
Floor plates are **interior only**. Walls are continuous through the floor level.

```powershell
# CORRECT — walls continuous, floor plates interior only
# Wall continues at floor sep level
FillX $WallColor $LX $RX -156 $FZ   # front wall brick at floor sep Y
FillX $WallColor $LX $RX -156 $BZ   # back wall brick at floor sep Y
FillZ $WallColor 0 640 -156 $LX     # left side wall
FillZ $WallColor 0 640 -156 $RX     # right side wall

# Interior floor plates (not touching any exterior wall)
for ($z = $FZ + 20; $z -le $BZ - 20; $z += 20) {
    FillXPlate $LtGray ($LX + 20) ($RX - 20) -156 $z
}
```

---

## Mistake 3: Wall Gaps Not Matching Window Height

### What we did wrong
Cut 6-row gaps (144 LDU) in walls for 3-row (72 LDU) window frames.
The top 3 rows of each gap were completely empty.

### Visual impact
Large open sections in the first floor front wall visible in stud.io renders.
You could see through the wall to the interior.

### Fix
Match the gap height to the actual window part:

```powershell
# For 1x4x3 windows: only 3 rows gapped
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    if ($row -le 3) {
        WallRowX $color $xMin $xMax $y $FZ $windowGaps $off
    } else {
        FillX $color $xMin $xMax $y $FZ $off
    }
}
```

---

## Mistake 4: Not Understanding Y Inversion

### The trap
Y is inverted: -Y = up, +Y = down. Ground level = Y 140. Buildings go UP
by using decreasing (more negative) Y values.

A brick at Y=-148 has its **top** at Y=-148 and extends **down** to Y=-124.

### Common errors
- Placing parts at wrong Y (above or below intended position)
- Miscalculating floor separation gap sizes
- Confusing "above" and "below" in Y math

### Cheat sheet for 12-row ground floor
```
Y = 140    Ground (baseplate top)
Y = 116    Row 1 top  (140 - 24)
Y = 92     Row 2 top  (140 - 48)
Y = 68     Row 3 top  (140 - 72)
Y = 44     Row 4 top
Y = 20     Row 5 top
Y = -4     Row 6 top
Y = -28    Row 7 top
Y = -52    Row 8 top
Y = -76    Row 9 top
Y = -100   Row 10 top
Y = -124   Row 11 top
Y = -148   Row 12 top (ceiling level)
```

---

## Mistake 5: Corbels Colliding with Roof Plates

### What happened
3665.dat (inverted slope) placed at Z=0 (spanning Z=-10 to Z=10) collided
with roof plates at Z=10. Stud.io showed them greyed out / wireframe.

### Fix
Move corbels to Z=-10 (in front of the wall, spanning Z=-20 to Z=0).
They won't collide with anything at Z=10.

---

## Mistake 6: Balcony Plates Overlapping Floor Separation

### What happened
Balcony plates at Z=10 overlapped with floor separation plates at the same
Y and Z coordinates.

### Fix
Only place balcony plates at overhang positions (Z < front wall Z).
The floor separation already provides coverage at Z=10.

---

## Stud.io Collision Detection Notes

- When collision detection is on, **colliding parts display as wireframes**
  (greyed-out appearance)
- Detection accuracy depends on render quality settings
  (Edit > Preferences > Appearance > Render quality)
- Parts can be forced through collisions with keyboard movement
- Collision = two parts occupying the same physical space

Source: https://studiohelp.bricklink.com/hc/en-us/articles/5412820155927-Collision

---

## Summary Checklist

Before generating a building, verify:

- [ ] Window frame parts match their glass parts (see part-geometry.md)
- [ ] Wall gap rows match actual window height (3 rows for 1x4x3, 6 for 1x4x6)
- [ ] Floor plates are interior only (not at wall Z/X positions)
- [ ] Walls are continuous through floor separation Y-levels
- [ ] No parts share exact same position + orientation (collision)
- [ ] Corbels and decorative elements don't overlap structural parts
- [ ] Balcony/overhang plates don't duplicate floor separation coverage
