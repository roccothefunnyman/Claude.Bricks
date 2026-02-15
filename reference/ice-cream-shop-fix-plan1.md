# Ice Cream Shop Fix Plan

## Summary

The current IceCreamShop.ps1 produces a structurally sound building but differs from the
European Townhouse v4 reference in several key areas. This plan details each fix with
exact code changes, referencing line numbers in the current script and matching values
from EuropeanTownhouse_v4.ps1.

---

## Fix 1: Ground Floor Arch Gap — Too Tall

**Problem:** Arch opening spans rows 1-8 (192 LDU = 8 bricks). The v4 reference uses
rows 4-7 (96 LDU = 4 bricks), creating a much more proportional opening above a solid
brick base.

**Current code (lines 93-98):**
```powershell
if ($row -ge 1 -and $row -le 8) {
    Add-WallRowX $Tan 0 $DivX $y $FZ $archGap $off
} else {
    Fill-BricksX $Tan 0 $DivX $y $FZ $off
}
```

**Fix:** Change row range from `1-8` to `4-7`:
```powershell
if ($row -ge 4 -and $row -le 7) {
    Add-WallRowX $Tan 0 $DivX $y $FZ $archGap $off
} else {
    Fill-BricksX $Tan 0 $DivX $y $FZ $off
}
```

**Impact:** Rows 1-3 and 8 become solid brick, creating a 3-course base under the arch
and 1 row of brick above (where the arch piece sits). This matches the v4 proportions.

---

## Fix 2: Ground Floor Arch Piece Y Position

**Problem:** Arch piece placed at row 8 (Y = Ground - 8*24 = -52). Should be at row 7
(Y = Ground - 7*24 = -28) since the gap now ends at row 7.

**Current code (lines 111-112):**
```powershell
$archY = $Ground - 8 * 24   # -52
Add-Part $Tan 120 $archY $FZ "3307.dat" $R0
```

**Fix:**
```powershell
$archY = $Ground - 7 * 24   # -28
Add-Part $Tan 120 $archY $FZ "3307.dat" $R0
```

---

## Fix 3: First Floor Arch — Wrong Size and Part

**Problem:** First floor uses a narrower arch gap (80 LDU, rows 4-8) with a different
part (3659.dat = Arch 1x4x2). The v4 reference uses the SAME arch size on both floors:
120 LDU gap (rows 4-7) with 3307.dat (Arch 1x6x2).

### Fix 3a: Change gap definition (line 39)

**Current:**
```powershell
$ffArchGap = @(@{s=80; e=160})
```

**Fix:** Use the same gap as the ground floor:
```powershell
$ffArchGap = @(@{s=60; e=180})
```

### Fix 3b: Change gap row range (lines 206-210)

**Current:**
```powershell
if ($row -ge 4 -and $row -le 8) {
    Add-WallRowX $Tan 0 $DivX $y $FZ $ffArchGap $off
```

**Fix:**
```powershell
if ($row -ge 4 -and $row -le 7) {
    Add-WallRowX $Tan 0 $DivX $y $FZ $ffArchGap $off
```

### Fix 3c: Change arch piece part and Y (lines 220-222)

**Current:**
```powershell
$ffArchY = $ffBaseY - 8 * 24   # -356
Add-Part $Tan 120 $ffArchY $FZ "3659.dat" $R0
```

**Fix:**
```powershell
$ffArchY = $ffBaseY - 7 * 24   # -332
Add-Part $Tan 120 $ffArchY $FZ "3307.dat" $R0
```

---

## Fix 4: Remove Back Wall Windows

**Problem:** IceCreamShop has windows on the back wall (both floors). The v4 reference
has completely solid back walls — no windows at all.

### Fix 4a: Remove back gap definitions (lines 48-50)

**Delete:**
```powershell
# Back wall windows (both floors)
$backGapL = @(@{s=80; e=160})
$backGapR = @(@{s=400; e=480})
```

### Fix 4b: Simplify ground floor back wall (lines 116-126)

**Current:**
```powershell
for ($row = 1; $row -le $Rows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    if ($row -ge 4 -and $row -le 6) {
        Add-WallRowX $Tan  0 $DivX $y $BZ $backGapL $off
        Add-WallRowX $Blue $DivX 640 $y $BZ $backGapR $off
    } else {
        Fill-BricksX $Tan  0 $DivX $y $BZ $off
        Fill-BricksX $Blue $DivX 640 $y $BZ $off
    }
}
```

**Fix:** Remove the conditional — all rows are solid:
```powershell
for ($row = 1; $row -le $Rows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksX $Tan  0 $DivX $y $BZ $off
    Fill-BricksX $Blue $DivX 640 $y $BZ $off
}
```

### Fix 4c: Simplify first floor back wall (lines 231-241)

Same change — remove conditional, make all rows solid.

### Fix 4d: Remove back wall window assemblies

**Delete from ground floor (lines 156-159):**
```powershell
Add-WindowBay -FrameColor $White -WallColor $Tan `
    -X 120 -Y $winY -Z $BZ -Wall "Back" ...
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 440 -Y $winY -Z $BZ -Wall "Back" ...
```

**Delete from first floor (lines 263-266):**
```powershell
Add-WindowBay -FrameColor $White -WallColor $Tan `
    -X 120 -Y $ffWinY -Z $BZ -Wall "Back" ...
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 440 -Y $ffWinY -Z $BZ -Wall "Back" ...
```

---

## Fix 5: Replace Full Cornice with Individual Corbels

**Problem:** IceCreamShop uses `Add-CorniceBand` in White on all 4 walls, creating a
formal Georgian-style cornice band. The v4 reference has NO full cornice. Instead, it
places 4 individual corbel pieces (3665.dat inverted slopes) under the right section
roofline only.

### Fix 5a: Remove all Add-CorniceBand calls (lines 295-300)

**Delete:**
```powershell
$corniceY = $ffTopY + 12
Add-CorniceBand $White 0 640 $corniceY $FZ "Front" "Corbel"
Add-CorniceBand $White 0 640 $corniceY $BZ "Back" "Corbel"
Add-CorniceBand $White 0 640 $corniceY $LX "Left" "Corbel"
Add-CorniceBand $White 0 640 $corniceY $RX "Right" "Corbel"
```

### Fix 5b: Add individual corbels (right section front only)

**Replace with:**
```powershell
Add-Comment "Corbels (right section)"
$corbelPositions = @(300, 380, 500, 580)
foreach ($cx in $corbelPositions) {
    Add-Part $LtGray $cx ($ffTopY - 8) ($FZ - 10) "3665.dat" $R0
}
```

- Part: 3665.dat (Slope Inv 45 2x1)
- Color: Light Gray (71)
- 4 corbels at X = 300, 380, 500, 580
- Y = ffTopY - 8 (just below roof plate)
- Z = FZ - 10 = 0 (overhanging front of wall by 10 LDU)

---

## Fix 6: Section-Specific Parapets (Different Heights)

**Problem:** IceCreamShop uses `Add-Parapet` which creates a uniform-height parapet
around all walls. The v4 reference has DIFFERENT parapets per section:
- **Left section (Tan):** 1 brick + tile cap (32 LDU tall)
- **Right section (Blue):** 2 bricks + tile cap (56 LDU tall, taller than left)

This height difference is a signature visual feature of the design.

### Fix 6a: Remove the module Add-Parapet call (lines 313-314)

**Delete:**
```powershell
$parY = $ffTopY - 8 - 24
Add-Parapet $DkGray 0 640 0 640 $parY 2 $true "FBLR"
```

### Fix 6b: Add custom section-specific parapet code

**Replace with:**
```powershell
Add-Comment "Left section parapet (1 brick + tile cap)"
$roofPlateY = $ffTopY - 8
$leftParY = $roofPlateY - 24
Fill-BricksX $Tan 0 $DivX $leftParY $FZ
Fill-TilesX  $Tan 0 $DivX ($leftParY - 8) $FZ
Fill-BricksZ $Tan 20 620 $leftParY $LX
Fill-BricksX $Tan 0 $DivX $leftParY $BZ

Add-Comment "Right section parapet (2 bricks + tile cap)"
$rightParY1 = $roofPlateY - 24
$rightParY2 = $roofPlateY - 48
Fill-BricksX $Blue   $DivX 640 $rightParY1 $FZ
Fill-BricksX $Blue   $DivX 640 $rightParY2 $FZ
Fill-TilesX  $LtGray $DivX 640 ($rightParY2 - 8) $FZ
Fill-BricksZ $Blue 20 620 $rightParY1 $RX
Fill-BricksX $Blue $DivX 640 $rightParY1 $BZ
```

**Note:** Left parapet is shorter (1 course) while right is taller (2 courses). The
tile cap on the right section uses Light Gray for contrast.

---

## Fix 7: Balcony Post Spacing

**Problem:** Posts are at X = 50, 120, 190 (70 LDU spacing). The v4 reference uses
X = 50, 110, 170 (60 LDU spacing). This also affects the top rail and side post X
positions.

### Fix 7a: Front posts (line 283)

**Current:**
```powershell
foreach ($x in @(50, 120, 190)) {
```

**Fix:**
```powershell
foreach ($x in @(50, 110, 170)) {
```

### Fix 7b: Side posts (lines 291-292)

**Current:**
```powershell
Add-Part $LtGray 50  ($fsy2 - 24) ($FZ - 10) "3005.dat" $R0
Add-Part $LtGray 190 ($fsy2 - 24) ($FZ - 10) "3005.dat" $R0
```

**Fix:**
```powershell
Add-Part $LtGray 50  ($fsy2 - 24) ($FZ - 10) "3005.dat" $R0
Add-Part $LtGray 170 ($fsy2 - 24) ($FZ - 10) "3005.dat" $R0
```

### Fix 7c: Platform plates X range (line 279)

**Current:**
```powershell
Fill-PlatesX $LtGray 40 200 $fsy2 $z
```

**Fix:**
```powershell
Fill-PlatesX $LtGray 40 180 $fsy2 $z
```

The platform should span X=40 to X=180 (7 studs) to match the post positions, not
extend to X=200.

### Fix 7d: Top rail tile X range (line 288)

**Current:**
```powershell
Fill-TilesX $LtGray 40 200 ($fsy2 - 32) ($FZ - 30)
```

**Fix:**
```powershell
Fill-TilesX $LtGray 40 180 ($fsy2 - 32) ($FZ - 30)
```

---

## Fix 8: Balcony Depth

**Problem:** Balcony extends from Z = FZ-30 = -20 to Z = FZ-10 = 0 (30 LDU in front
of wall). The v4 reference extends from Z = -30 to Z = -10 (40 LDU in front of wall).

### Fix 8a: Platform plates Z range (line 278)

**Current:**
```powershell
for ($z = ($FZ - 30); $z -le ($FZ - 10); $z += 20) {
```

**Fix:**
```powershell
for ($z = ($FZ - 40); $z -le ($FZ - 20); $z += 20) {
```

### Fix 8b: Front posts Z coordinate (line 284)

**Current:**
```powershell
Add-Part $LtGray $x ($fsy2 - 24) ($FZ - 30) "3005.dat" $R0
```

**Fix:**
```powershell
Add-Part $LtGray $x ($fsy2 - 24) ($FZ - 40) "3005.dat" $R0
```

### Fix 8c: Top rail tile Z (line 288)

**Current:** `($FZ - 30)` → **Fix:** `($FZ - 40)`

### Fix 8d: Side posts Z (lines 291-292)

**Current:** `($FZ - 10)` → **Fix:** `($FZ - 20)`

---

## Fix 9: Add Shop Sign Tile

**Problem:** Missing decorative detail above the ground floor door. The v4 reference has
a 1x2 white tile (3069b.dat) at X=440, Y=44 (row 4 level), Z=FZ.

### Add after door placement (after line 146):

```powershell
Add-Comment "Shop sign"
Add-Part $White 440 ($Ground - 4 * 24) $FZ "3069b.dat" $R0
```

---

## Fix 10: Roof Plate Coverage

**Problem:** The IceCreamShop's roof uses `Add-FloorPlates` spanning the full 0-640
range. With section-specific parapets at different heights, we need to verify the roof
plate is at a consistent Y that works with both parapet sections.

**Current (line 309):**
```powershell
Add-FloorPlates $LtGray 0 640 0 640 ($ffTopY - 8) 1
```

This should still work — both parapet sections build UP from the roof plate. No change
needed, but verify during implementation that the roof plate Y aligns correctly with
both the left (1-course) and right (2-course) parapets.

---

## Implementation Order

1. **Fixes 1-3** (Arch corrections) — straightforward value changes
2. **Fix 4** (Remove back windows) — delete code blocks
3. **Fix 5** (Corbels) — replace cornice band with individual parts
4. **Fix 6** (Parapets) — replace module call with custom code
5. **Fixes 7-8** (Balcony) — coordinate adjustments
6. **Fix 9** (Shop sign) — add new part
7. **Fix 10** (Roof verification) — no code change, just verify

## Testing

After implementing all fixes:
1. Run the script: `powershell -File scripts/IceCreamShop.ps1`
2. Validate output exists and has expected line count (~1200-1300 lines)
3. Spot-check key coordinates:
   - GF arch gap should appear only at rows 4-7 (Y = 44, 20, -4, -28)
   - Arch pieces at Y = -28 (GF) and Y = -332 (FF)
   - No back wall windows (no 60594.dat/60603.dat parts at Z=630)
   - Corbels at X = 300, 380, 500, 580 (only 4 total, front only)
   - Left parapet 1 course, right parapet 2 courses
   - Balcony posts at X = 50, 110, 170

## Risk Areas

- **Fix 6 (Parapets):** Moving from module function to inline code. Need to ensure
  left parapet tile cap and right parapet tile cap are at correct Y values. Also need
  to handle the back-wall parapet for both sections.
- **Fix 5 (Corbels):** The v4 only has corbels on the right section front. This is
  minimal — may want to consider adding them to back/sides too for visual completeness.
  But matching v4 exactly means front-right only.
- **Fix 3 (FF Arch):** Changing from 3659.dat (1x4x2) to 3307.dat (1x6x2) changes the
  visual width. This is correct per v4 but worth verifying the gap size matches.
