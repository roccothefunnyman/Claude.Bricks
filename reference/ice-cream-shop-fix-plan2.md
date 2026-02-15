# Ice Cream Shop Fix Plan 2

## What Fix-Plan1 Got Wrong

Fix-plan1 was based on matching the v4 PowerShell code literally. But the v4 code
and the actual rendered reference image tell different stories. The close-up screenshot
of the original Tan section reveals:

- **Ground floor arch opening is TALL** — nearly full wall height with a DOOR inside
- **Fix-plan1 SHRANK the opening to rows 4-7** — this was wrong, it should be tall
- **Fix-plan1 kept the Reddish Brown door** — the original has light gray glass
- **The original IceCreamShop (rows 1-8 gap) was actually closer to correct**

## Fixes

### Fix A: Restore Ground Floor Arch Gap to Rows 1-8

The tall arch opening needs to accommodate the full-height door (rows 1-6) plus
the arch piece (rows 7-8). The 3307.dat arch is 48 LDU = 2 bricks tall, perfectly
filling the row 7-8 gap. Below it, the 60596.dat door (144 LDU = 6 bricks) fills
rows 1-6 down to ground level.

**Current (fix-plan1, WRONG):**
```powershell
# LEFT SECTION (Tan): rows 4-7 have arch gap
if ($row -ge 4 -and $row -le 7) {
```

**Fix — restore to rows 1-8:**
```powershell
# LEFT SECTION (Tan): rows 1-8 have arch gap (door + arch)
if ($row -ge 1 -and $row -le 8) {
```

### Fix B: Restore Arch Piece to Row 8

The arch at row 8 (Y=-52) aligns perfectly with the door top (Y=-4):
- Arch 3307.dat at Y=-52: spans Y=-52 to Y=-4 (48 LDU)
- Door 60596.dat at Y=-4: spans Y=-4 to Y=140 (144 LDU)
- Arch bottom meets door top exactly at Y=-4

**Current (fix-plan1):**
```powershell
$archY = $Ground - 7 * 24   # -28
```

**Fix — restore to row 8:**
```powershell
$archY = $Ground - 8 * 24   # -52
```

### Fix C: Change Door Glass Color from Reddish Brown to Light Gray

The reference shows a gray/glass door panel, not a brown one.

**Current:**
```powershell
$RBrown  = 70    # Door color
...
Add-Part $RBrown 120 $doorTopY $FZ "57895.dat" $R0
```

**Fix:**
```powershell
Add-Part $LtGray 120 $doorTopY $FZ "57895.dat" $R0
```

Remove the `$RBrown = 70` color variable (no longer used).

### Fix D: First Floor — Keep As-Is

The first floor arch gap (rows 4-7) with a 1x4x3 window inside is correct per the
reference image. The smaller opening + balcony matches what we see. No change needed.

## Y-Coordinate Verification

After these fixes, the ground floor left section layout will be:

```
Row 12: Y=-148  Solid brick
Row 11: Y=-124  Solid brick
Row 10: Y=-100  Solid brick
Row  9: Y=-76   Solid brick
Row  8: Y=-52   ARCH piece (3307.dat top, spans to Y=-4)
Row  7: Y=-28   ARCH piece (lower half)
Row  6: Y=-4    DOOR frame top (60596.dat, spans to Y=140)
Row  5: Y=20    DOOR frame
Row  4: Y=44    DOOR frame
Row  3: Y=68    DOOR frame
Row  2: Y=92    DOOR frame
Row  1: Y=116   DOOR frame bottom
         Y=140  Ground level
```

Gap rows 1-8 keep bricks out of X=60-180 zone. Rows 9-12 are solid = 4 brick
courses above the arch. This matches the reference image proportions.

## What This Does NOT Fix (Noted for Future)

- **Window glass appearance**: Module places frame + glass at identical coordinates
  (same approach as v4). If glass still looks off in Studio, this may be a part
  geometry issue in the LDraw library, not a script issue.
- **Parapet flush vs recessed**: Both v4 and IceCreamShop have flush parapets. If
  recessing is desired, that would be a new design choice (shift parapet Z by 20 LDU).

## Implementation

Only 3 lines change + 1 line deleted. Fast to implement and verify.
