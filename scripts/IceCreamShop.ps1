# IceCreamShop.ps1
# 2-story modular building: 32x32 studs
# Left section: Tan with arch entrance; Right section: Bright Light Blue with storefront
# Features: arches, balcony, window boxes, corbel cornice, sidewalk

param([string]$OutputFile = "output/IceCreamShop.ldr")

Import-Module (Join-Path $PSScriptRoot "..\modules\LDraw.psm1") -Force

# === COLORS ===
$Tan     = 19    # Left section
$Blue    = 212   # Right section (Bright Light Blue)
$White   = 15    # Window frames, cornice
$DkGray  = 72    # Baseplate, roof, parapet
$LtGray  = 71    # Sidewalk, floor plates, door glass
$Brown   = 6     # Window box planters
$Yellow  = 14    # Flowers
$Green   = 10    # Flowers

# === DIMENSIONS ===
$FZ = 10;  $BZ = 630
$LX = 10;  $RX = 630
$Ground = 140
$DivX = 240      # Section divider (12 studs from left)
$Rows = 12       # Rows per floor

# === Y CALCULATIONS ===
$gfTopY  = $Ground - $Rows * 24    # -148
$fsy1    = $gfTopY - 8             # -156
$fsy2    = $fsy1 - 8               # -164
$ffBaseY = $fsy2                   # -164
$ffTopY  = $ffBaseY - $Rows * 24   # -452

# === GAP DEFINITIONS ===
# Left section: arch opening (6 studs = 120 LDU centered at X=120)
$archGap = @(@{s=60; e=180})
# Left section upper: arch opening (6 studs = 120 LDU centered at X=120)
$ffArchGap = @(@{s=60; e=180})

# Right section ground floor
$gfDoorGap = @(@{s=400; e=480})
$gfAllGaps = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# Right section first floor
$ffWinGaps = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# Back walls are solid (no windows)

# === HELPERS ===
function WindowBox([double]$x, [double]$y, [double]$z) {
    Add-Part $Brown $x $y $z "3710.dat" $R0
    $fy = $y - 8
    Add-Part $Yellow ($x - 20) $fy $z "4073.dat" $R0
    Add-Part $Green  $x        $fy $z "4073.dat" $R0
    Add-Part $Yellow ($x + 20) $fy $z "4073.dat" $R0
}

# === MODEL STRUCTURE ===
Start-Model "Ice Cream Shop"
Add-SubmodelRef "base"
Add-SubmodelRef "ground_floor"
Add-SubmodelRef "floor_sep"
Add-SubmodelRef "first_floor"
Add-SubmodelRef "roof"
End-Model

# ============================================================
# BASE
# ============================================================
Start-Submodel "base"
Add-Part $DkGray 320 $Ground 320 "3811.dat"

Add-Comment "Sidewalk"
for ($z = $FZ; $z -le ($FZ + 20); $z += 20) {
    Fill-PlatesX $LtGray 0 640 ($Ground - 8) $z
    Fill-TilesX  $LtGray 0 640 ($Ground - 16) $z
}
End-Submodel

# ============================================================
# GROUND FLOOR
# ============================================================
Start-Submodel "ground_floor"
Add-Comment "Front wall - dual section"

for ($row = 1; $row -le $Rows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20

    # LEFT SECTION (Tan): rows 1-8 have arch gap (door + arch)
    if ($row -ge 1 -and $row -le 8) {
        Add-WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        Fill-BricksX $Tan 0 $DivX $y $FZ $off
    }

    # RIGHT SECTION (Blue): door rows 1-6, windows rows 4-6
    if ($row -ge 1 -and $row -le 3) {
        Add-WallRowX $Blue $DivX 640 $y $FZ $gfDoorGap $off
    } elseif ($row -ge 4 -and $row -le 6) {
        Add-WallRowX $Blue $DivX 640 $y $FZ $gfAllGaps $off
    } else {
        Fill-BricksX $Blue $DivX 640 $y $FZ $off
    }
}

# Arch piece at top of opening (row 8)
$archY = $Ground - 8 * 24   # -52
Add-Part $Tan 120 $archY $FZ "3307.dat" $R0

Add-Step
Add-Comment "Back wall (solid)"
for ($row = 1; $row -le $Rows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksX $Tan  0 $DivX $y $BZ $off
    Fill-BricksX $Blue $DivX 640 $y $BZ $off
}

Add-Comment "Side walls"
for ($row = 1; $row -le $Rows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksZ $Tan  20 620 $y $LX $off
    Fill-BricksZ $Blue 20 620 $y $RX $off
}

Add-Step
Add-Comment "Door and windows"

# Door inside arch opening (left section)
$doorTopY = $Ground - 6 * 24   # -4
Add-Part $White  120 $doorTopY $FZ "60596.dat" $R0
Add-Part $LtGray 120 $doorTopY $FZ "57895.dat" $R0

# Right section door
Add-DoorSurround -FrameColor $White -DoorColor $LtGray -WallColor $Blue `
    -X 440 -Y $doorTopY -Z $FZ -Wall "Front" -Recessed $false -Header $false

# Right section windows
$winY = $doorTopY
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 320 -Y $winY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 560 -Y $winY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false

# Shop sign tile above door
Add-Part $White 440 ($Ground - 4 * 24) $FZ "3069b.dat" $R0

# Window boxes (right section front, at ground level)
WindowBox 320 $Ground ($FZ - 20)
WindowBox 560 $Ground ($FZ - 20)

End-Submodel

# ============================================================
# FLOOR SEPARATION
# ============================================================
Start-Submodel "floor_sep"
Add-Comment "Floor separation plates"

foreach ($yp in @($fsy1, $fsy2)) {
    # Wall plates in building colors (continuous walls)
    Fill-PlatesX $Tan  0 $DivX $yp $FZ
    Fill-PlatesX $Blue $DivX 640 $yp $FZ
    Fill-PlatesX $Tan  0 $DivX $yp $BZ
    Fill-PlatesX $Blue $DivX 640 $yp $BZ
    Fill-PlatesZ $Tan  20 620 $yp $LX
    Fill-PlatesZ $Blue 20 620 $yp $RX

    # Interior floor plates
    for ($z = ($FZ + 20); $z -le ($BZ - 20); $z += 20) {
        Fill-PlatesX $LtGray ($LX + 20) ($RX - 20) $yp $z
    }
}

# Accent band overhang on front
Fill-TilesX $DkGray 0 $DivX $fsy1 ($FZ - 10)
Fill-TilesX $DkGray $DivX 640 $fsy1 ($FZ - 10)

End-Submodel

# ============================================================
# FIRST FLOOR
# ============================================================
Start-Submodel "first_floor"
Add-Comment "First floor walls"

# Front wall
for ($row = 1; $row -le $Rows; $row++) {
    $y = $ffBaseY - $row * 24
    $off = ($row % 2) * 20

    # LEFT SECTION: rows 4-7 have arch gap
    if ($row -ge 4 -and $row -le 7) {
        Add-WallRowX $Tan 0 $DivX $y $FZ $ffArchGap $off
    } else {
        Fill-BricksX $Tan 0 $DivX $y $FZ $off
    }

    # RIGHT SECTION: rows 4-6 have window gaps
    if ($row -ge 4 -and $row -le 6) {
        Add-WallRowX $Blue $DivX 640 $y $FZ $ffWinGaps $off
    } else {
        Fill-BricksX $Blue $DivX 640 $y $FZ $off
    }
}

# Upper arch piece (3307.dat = Arch 1x6x2, 120 LDU wide)
$ffArchY = $ffBaseY - 7 * 24   # -332
Add-Part $Tan 120 $ffArchY $FZ "3307.dat" $R0

# Left section window (inside arch)
$ffWinY = $ffBaseY - 6 * 24    # -308
Add-WindowBay -FrameColor $White -WallColor $Tan `
    -X 120 -Y $ffWinY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false

Add-Step
Add-Comment "Back wall (solid)"
for ($row = 1; $row -le $Rows; $row++) {
    $y = $ffBaseY - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksX $Tan  0 $DivX $y $BZ $off
    Fill-BricksX $Blue $DivX 640 $y $BZ $off
}

Add-Comment "Side walls"
for ($row = 1; $row -le $Rows; $row++) {
    $y = $ffBaseY - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksZ $Tan  20 620 $y $LX $off
    Fill-BricksZ $Blue 20 620 $y $RX $off
}

Add-Step
Add-Comment "First floor windows"

# Right section windows
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 320 -Y $ffWinY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 440 -Y $ffWinY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false
Add-WindowBay -FrameColor $White -WallColor $Blue `
    -X 560 -Y $ffWinY -Z $FZ -Wall "Front" -Recessed $false -Sill $false -Header $false

# Flower boxes (first floor right section)
$boxY = $ffWinY + 80   # Just below window sill
WindowBox 320 $boxY ($FZ - 20)
WindowBox 440 $boxY ($FZ - 20)
WindowBox 560 $boxY ($FZ - 20)

Add-Step
Add-Comment "Balcony (left section)"

# Platform plates (in front of wall, 2 studs deep)
for ($z = ($FZ - 40); $z -le ($FZ - 20); $z += 20) {
    Fill-PlatesX $LtGray 40 180 $fsy2 $z
}

# Railing posts (1x1 bricks at front edge, 60 LDU spacing)
foreach ($x in @(50, 110, 170)) {
    Add-Part $LtGray $x ($fsy2 - 24) ($FZ - 40) "3005.dat" $R0
}

# Top rail tile
Fill-TilesX $LtGray 40 180 ($fsy2 - 32) ($FZ - 40)

# Side posts (back edge of balcony)
Add-Part $LtGray 50  ($fsy2 - 24) ($FZ - 20) "3005.dat" $R0
Add-Part $LtGray 170 ($fsy2 - 24) ($FZ - 20) "3005.dat" $R0

Add-Step
Add-Comment "Corbels (right section front)"
$corbelPositions = @(300, 380, 500, 580)
foreach ($cx in $corbelPositions) {
    Add-Part $LtGray $cx ($ffTopY - 8) ($FZ - 10) "3665.dat" $R0
}

End-Submodel

# ============================================================
# ROOF
# ============================================================
Start-Submodel "roof"
Add-Comment "Roof plates"
Add-FloorPlates $LtGray 0 640 0 640 ($ffTopY - 8) 1

Add-Step
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

End-Submodel

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
Save-LDrawFile $outPath
