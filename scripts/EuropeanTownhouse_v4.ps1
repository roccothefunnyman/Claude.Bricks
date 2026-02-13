# EuropeanTownhouse_v4.ps1
# v4 fixes based on analysis of official LEGO modular sets (10246, 10218):
#   - CORRECTED window glass: 60603.dat (was 60592.dat, a completely different part)
#   - CORRECTED wall gaps: 3 rows for 1x4x3 windows (was 6-8 rows)
#   - CORRECTED floor separation: walls continuous, interior-only floor plates
#   - CORRECTED door gaps: 6 rows for 1x4x6 door frame
#   - Window boxes repositioned below actual windows

param(
    [string]$OutputFile = "output/EuropeanTownhouse_v4.ldr",
    [string]$ModelName = "European Townhouse v4"
)

$sb = [System.Text.StringBuilder]::new()
function L([string]$t) { [void]$sb.AppendLine($t) }

# ============================================================
# ROTATION MATRICES
# ============================================================
$R0   = "1 0 0 0 1 0 0 0 1"
$R90  = "0 0 -1 0 1 0 1 0 0"
$R180 = "-1 0 0 0 1 0 0 0 -1"

# ============================================================
# CORE HELPER FUNCTIONS
# ============================================================

function B([int]$c,[double]$x,[double]$y,[double]$z,[string]$p,[string]$r=$R0) {
    L("1 $c $([math]::Round($x,1)) $([math]::Round($y,1)) $([math]::Round($z,1)) $r $p")
}

function FillX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[int]$offset=0) {
    $sizes = @(
        @{w=160;p="3008.dat"},@{w=120;p="3009.dat"},@{w=80;p="3010.dat"},
        @{w=60;p="3622.dat"},@{w=40;p="3004.dat"},@{w=20;p="3005.dat"}
    )
    $x = $xMin + $offset
    if ($offset -gt 0 -and $offset -lt 160) {
        foreach ($s in $sizes) {
            if ($s.w -le $offset + 0.1) { B $c ($xMin + $s.w/2) $y $z $s.p $R0; break }
        }
    }
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        if ($rem -lt 19.9) { break }
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c ($x + $s.w/2) $y $z $s.p $R0; $x += $s.w; break }
        }
    }
}

function FillZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x,[int]$offset=0) {
    $sizes = @(
        @{w=160;p="3008.dat"},@{w=120;p="3009.dat"},@{w=80;p="3010.dat"},
        @{w=60;p="3622.dat"},@{w=40;p="3004.dat"},@{w=20;p="3005.dat"}
    )
    $z = $zMin + $offset
    if ($offset -gt 0 -and $offset -lt 160) {
        foreach ($s in $sizes) {
            if ($s.w -le $offset + 0.1) { B $c $x $y ($zMin + $s.w/2) $s.p $R90; break }
        }
    }
    while ($z -lt $zMax - 0.1) {
        $rem = $zMax - $z
        if ($rem -lt 19.9) { break }
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c $x $y ($z + $s.w/2) $s.p $R90; $z += $s.w; break }
        }
    }
}

function FillXPlate([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z) {
    $sizes = @(
        @{w=160;p="3460.dat"},@{w=120;p="3666.dat"},@{w=80;p="3710.dat"},
        @{w=60;p="3623.dat"},@{w=40;p="3023.dat"},@{w=20;p="3024.dat"}
    )
    $x = $xMin
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        if ($rem -lt 19.9) { break }
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c ($x + $s.w/2) $y $z $s.p $R0; $x += $s.w; break }
        }
    }
}

function FillZPlate([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x) {
    $sizes = @(
        @{w=160;p="3460.dat"},@{w=120;p="3666.dat"},@{w=80;p="3710.dat"},
        @{w=60;p="3623.dat"},@{w=40;p="3023.dat"},@{w=20;p="3024.dat"}
    )
    $z = $zMin
    while ($z -lt $zMax - 0.1) {
        $rem = $zMax - $z
        if ($rem -lt 19.9) { break }
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c $x $y ($z + $s.w/2) $s.p $R90; $z += $s.w; break }
        }
    }
}

function FillXTile([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z) {
    $sizes = @(
        @{w=160;p="4162.dat"},@{w=120;p="6636.dat"},@{w=80;p="2431.dat"},
        @{w=60;p="63864.dat"},@{w=40;p="3069b.dat"},@{w=20;p="3070b.dat"}
    )
    $x = $xMin
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        if ($rem -lt 19.9) { break }
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c ($x + $s.w/2) $y $z $s.p $R0; $x += $s.w; break }
        }
    }
}

function WallRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[array]$gaps=@(),[int]$offset=0) {
    $sorted = $gaps | Sort-Object { $_.s }
    $x = $xMin
    foreach ($g in $sorted) {
        if ($g.s -gt $x + 0.1) { FillX $c $x $g.s $y $z $offset }
        $x = $g.e
    }
    if ($x -lt $xMax - 0.1) { FillX $c $x $xMax $y $z $offset }
}

function PlateRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[array]$gaps=@()) {
    $sorted = $gaps | Sort-Object { $_.s }
    $x = $xMin
    foreach ($g in $sorted) {
        if ($g.s -gt $x + 0.1) { FillXPlate $c $x $g.s $y $z }
        $x = $g.e
    }
    if ($x -lt $xMax - 0.1) { FillXPlate $c $x $xMax $y $z }
}

# v4 CORRECTED: 60603.dat is the correct glass for 1x4x3 window frame (60594.dat)
# 60592.dat was WRONG --it's a Window 1x2x2, a completely different part
function PlaceWindow([int]$fc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60594.dat" $r    # Window Frame 1x4x3
    B 47  $x $y $z "60603.dat" $r    # Glass for Window 1x4x3
}

function PlaceDoor([int]$fc,[int]$dc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60596.dat" $r    # Door Frame 1x4x6
    B $dc $x $y $z "57895.dat" $r    # Door Glass 1x4x6
}

function WindowBox([double]$x,[double]$y,[double]$z) {
    B $Brown $x $y $z "3710.dat" $R0          # planter plate
    $fy = $y - 8
    B $Yellow ($x - 20) $fy $z "4073.dat" $R0 # flower left
    B $Green  $x        $fy $z "4073.dat" $R0  # flower center
    B $Yellow ($x + 20) $fy $z "4073.dat" $R0  # flower right
}

# ============================================================
# COLORS
# ============================================================
$Tan     = 19
$Blue    = 212   # Bright Light Blue
$DkGray  = 72
$LtGray  = 71
$White   = 15
$Brown   = 6
$Yellow  = 14
$Green   = 10

# ============================================================
# DIMENSIONS
# ============================================================
$FZ   = 10       # Front wall Z
$BZ   = 630      # Back wall Z
$LX   = 10       # Left wall X
$RX   = 630      # Right wall X
$DivX = 240      # Section boundary (12 studs from left)

# ============================================================
# GAP DEFINITIONS
# ============================================================
# Arch opening: 120 LDU wide (6 studs) for 3307.dat (Arch 1x6x2)
$archGap = @(@{s=60; e=180})

# Ground floor right section:
# - Door: 80 LDU gap at center (X=400-480) --1x4x6 frame = 6 rows tall
# - Two windows flanking door: 80 LDU each --1x4x3 frame = 3 rows tall
$gfDoorGap      = @(@{s=400; e=480})
$gfAllOpenings  = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# First floor right section: 3 windows, each 80 LDU --3 rows tall
$ffRightWindows = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# ============================================================
# MASTER MODEL
# ============================================================
L "0 FILE $ModelName.ldr"
L "0 $ModelName"
L "0 Name: $ModelName.ldr"
L "0 Author: Claude.Bricks"
L "0 !LDRAW_ORG Model"
L ""
L "1 16 0 0 0 $R0 base.ldr"
L "1 16 0 0 0 $R0 ground_floor.ldr"
L "1 16 0 0 0 $R0 floor_sep.ldr"
L "1 16 0 0 0 $R0 first_floor.ldr"
L "1 16 0 0 0 $R0 roof.ldr"
L "0 NOFILE"
L ""

# ============================================================
# SUBMODEL: BASE
# ============================================================
L "0 FILE base.ldr"
L "0 base"
L "0 Name: base.ldr"
L "0 Author: Claude.Bricks"
L ""

B $DkGray 320 140 320 "3811.dat" $R0

# Raised sidewalk step (2 studs deep along front)
for ($z = 10; $z -le 30; $z += 20) {
    FillXPlate $LtGray 0 640 132 $z
    FillXTile  $LtGray 0 640 124 $z
}

L "0 STEP"
L "0 NOFILE"
L ""

# ============================================================
# SUBMODEL: GROUND FLOOR
# ============================================================
L "0 FILE ground_floor.ldr"
L "0 ground_floor"
L "0 Name: ground_floor.ldr"
L "0 Author: Claude.Bricks"
L ""

# --- GROUND FLOOR FRONT WALL ---
# Row N top Y = 140 - N*24. Window (1x4x3) at Y=-4 covers rows 4-6.
# Arch (1x6x2) at Y=-28 covers rows 6-7. Combined gap: rows 4-7.
# Door (1x4x6) at Y=-4 covers rows 1-6. Windows at Y=-4 cover rows 4-6.

L "0 // Ground floor front wall"

for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)

    # LEFT SECTION (Tan): gap rows 4-7 for arch + window
    if ($row -ge 4 -and $row -le 7) {
        WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }

    # RIGHT SECTION (Blue):
    # Door (1x4x6 = 6 bricks): rows 1-6 have door gap
    # Windows (1x4x3 = 3 bricks): rows 4-6 have window gaps
    # Combined: rows 1-3 door only, rows 4-6 all openings, rows 7-12 solid
    if ($row -ge 1 -and $row -le 3) {
        WallRowX $Blue $DivX 640 $y $FZ $gfDoorGap $off
    } elseif ($row -ge 4 -and $row -le 6) {
        WallRowX $Blue $DivX 640 $y $FZ $gfAllOpenings $off
    } else {
        FillX $Blue $DivX 640 $y $FZ $off
    }
}

# Arch brick above the window opening (at top of gap area)
# Row 7: Y = 140 - 7*24 = -28. Arch placed here.
B $Tan 120 -28 $FZ "3307.dat" $R0

# Window in arch opening (1x4x3 frame + glass)
# Place at Y = row 6 = 140 - 6*24 = -4
# Frame top at Y=-4, extends down to Y=68 (3 bricks)
PlaceWindow $White 120 -4 $FZ

# Door (1x4x6 frame + glass)
# Place at Y = row 6 = -4
# Frame top at Y=-4, extends down to Y=-4+144=140 (ground level)
PlaceDoor $White $LtGray 440 -4 $FZ

# Shop sign tile above door
B $White 440 44 $FZ "3069b.dat" $R0

# Windows flanking door (1x4x3 at Y=-4, gap rows 4-6)
PlaceWindow $White 320 -4 $FZ
PlaceWindow $White 560 -4 $FZ

# Window boxes at ground level in front of wall
WindowBox 320 140 -10
WindowBox 560 140 -10

# --- SIDE WALLS (ground floor) ---
L "0 // Side walls"
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Tan  0 640 $y $LX $off
    FillZ $Blue 0 640 $y $RX $off
}

# --- BACK WALL (ground floor) ---
L "0 // Back wall"
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillX $Tan  0 $DivX $y $BZ $off
    FillX $Blue $DivX 640 $y $BZ $off
}

L "0 STEP"
L "0 NOFILE"
L ""

# ============================================================
# SUBMODEL: FLOOR SEPARATION
# ============================================================
# KEY FIX: Official sets have walls CONTINUOUS through floor level.
# Floor plates are INTERIOR ONLY --never at exterior wall positions.
L "0 FILE floor_sep.ldr"
L "0 floor_sep"
L "0 Name: floor_sep.ldr"
L "0 Author: Claude.Bricks"
L ""

L "0 // Floor separation --walls continuous, interior plates only"

# Floor sep Y levels: 2 plate layers
# Ground floor row 12 top = 140 - 12*24 = -148
# Floor sep plates at Y = -148 - 8 = -156 and -156 - 8 = -164
$fsy1 = -156
$fsy2 = -164

foreach ($yp in @($fsy1, $fsy2)) {
    # --- CONTINUOUS WALL BRICKS at floor sep level ---
    # Front wall: full building-color bricks (no gaps - floor sep is solid)
    FillX $Tan  0 $DivX $yp $FZ
    FillX $Blue $DivX 640 $yp $FZ

    # Back wall
    FillX $Tan  0 $DivX $yp $BZ
    FillX $Blue $DivX 640 $yp $BZ

    # Side walls
    FillZ $Tan  0 640 $yp $LX
    FillZ $Blue 0 640 $yp $RX

    # --- INTERIOR FLOOR PLATES (not touching any exterior wall) ---
    for ($z = ($FZ + 20); $z -le ($BZ - 20); $z += 20) {
        FillXPlate $LtGray ($LX + 20) ($RX - 20) $yp $z
    }
}

# Accent band: tile overhang in front (purely decorative, Z offset)
L "0 // Accent band"
FillXTile $DkGray 0 $DivX $fsy1 ($FZ - 10)
FillXTile $DkGray $DivX 640 $fsy1 ($FZ - 10)

L "0 STEP"
L "0 NOFILE"
L ""

# ============================================================
# SUBMODEL: FIRST FLOOR
# ============================================================
L "0 FILE first_floor.ldr"
L "0 first_floor"
L "0 Name: first_floor.ldr"
L "0 Author: Claude.Bricks"
L ""

# First floor starts at Y = -164 (top of floor sep)
# Row 1: Y = -164 - 24 = -188
# Row 2: Y = -212, Row 3: Y = -236, Row 4: Y = -260
# Row 5: Y = -284, Row 6: Y = -308, Row 7: Y = -332
# Row 8: Y = -356, Row 9: Y = -380, Row 10: Y = -404
# Row 11: Y = -428, Row 12: Y = -452

L "0 // First floor front wall"

for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)

    # LEFT SECTION (Tan): arch + window, gap rows 4-7 (same pattern as ground floor)
    if ($row -ge 4 -and $row -le 7) {
        WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }

    # RIGHT SECTION (Blue): 3 windows (1x4x3 = 3 rows), gap rows 4-6
    if ($row -ge 4 -and $row -le 6) {
        WallRowX $Blue $DivX 640 $y $FZ $ffRightWindows $off
    } else {
        FillX $Blue $DivX 640 $y $FZ $off
    }
}

# Arch at top of opening (row 7: Y = -164 - 7*24 = -332)
B $Tan 120 -332 $FZ "3307.dat" $R0

# Window in arch (Y = row 6 = -164 - 6*24 = -308)
PlaceWindow $White 120 -308 $FZ

# --- BALCONY (left section) ---
# Overhang plates in front of wall only (Z < FZ)
L "0 // Balcony"
for ($z = -30; $z -le -10; $z += 20) {
    FillXPlate $LtGray 40 200 -164 $z
}
# Railing posts
B $LtGray 50  -188 -30 "3005.dat" $R0
B $LtGray 110 -188 -30 "3005.dat" $R0
B $LtGray 170 -188 -30 "3005.dat" $R0
# Top rail
FillXTile $LtGray 40 200 -196 -30
# Side posts
B $LtGray 50  -188 -10 "3005.dat" $R0
B $LtGray 170 -188 -10 "3005.dat" $R0

# Right section windows (Y = row 6 = -308)
PlaceWindow $White 320 -308 $FZ
PlaceWindow $White 440 -308 $FZ
PlaceWindow $White 560 -308 $FZ

# Window boxes below first floor windows
# Window bottom: Y = -308 + 72 = -236. Place box at Y = -236 + 8 = -228 (just below)
WindowBox 320 -228 -10
WindowBox 440 -228 -10
WindowBox 560 -228 -10

# --- SIDE WALLS (first floor) ---
L "0 // Side walls"
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Tan  0 640 $y $LX $off
    FillZ $Blue 0 640 $y $RX $off
}

# --- BACK WALL (first floor) ---
L "0 // Back wall"
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    FillX $Tan  0 $DivX $y $BZ $off
    FillX $Blue $DivX 640 $y $BZ $off
}

L "0 STEP"
L "0 NOFILE"
L ""

# ============================================================
# SUBMODEL: ROOF
# ============================================================
L "0 FILE roof.ldr"
L "0 roof"
L "0 Name: roof.ldr"
L "0 Author: Claude.Bricks"
L ""

# Top of first floor row 12: Y = -164 - 12*24 = -452
$roofBase = -452

# --- ROOF PLATES (interior only, matching official set pattern) ---
L "0 // Roof plates"
for ($z = ($FZ + 20); $z -le ($BZ - 20); $z += 20) {
    FillXPlate $LtGray ($LX + 20) ($RX - 20) ($roofBase - 8) $z
}

L "0 STEP"

# --- LEFT SECTION ROOF CAP (Tan tiles, slightly higher than right) ---
$leftCapY = $roofBase - 16   # -468
L "0 // Left section roof cap"
for ($z = 0; $z -le 640; $z += 20) {
    FillXTile $Tan 0 $DivX $leftCapY $z
}

# --- LEFT SECTION PARAPET ---
$leftParY = $leftCapY - 24   # -492
L "0 // Left section parapet"
# Front
FillX $Tan 0 $DivX $leftParY $FZ
FillXTile $Tan 0 $DivX ($leftParY - 8) $FZ
# Left side
FillZ $Tan 0 640 $leftParY $LX
# Back
FillX $Tan 0 $DivX $leftParY $BZ

# --- RIGHT SECTION PARAPET ---
$parapetY1 = $roofBase - 8 - 24   # -484 (1 brick above roof plate)
$parapetY2 = $roofBase - 8 - 48   # -508 (2 bricks above roof plate)

L "0 // Right section parapet"
# Front (2 bricks tall + tile cap)
FillX $Blue $DivX 640 $parapetY1 $FZ
FillX $Blue $DivX 640 $parapetY2 $FZ
FillXTile $LtGray $DivX 640 ($parapetY2 - 8) $FZ

# Right side parapet (1 brick)
FillZ $Blue 0 640 $parapetY1 $RX

# Right back parapet (1 brick)
FillX $Blue $DivX 640 $parapetY1 $BZ

# --- DECORATIVE CORBELS ---
# Placed at Z=-10 (in front of wall) to avoid collision with roof plates at Z>=10
L "0 // Corbels"
$corbelPositions = @(300, 380, 500, 580)
foreach ($cx in $corbelPositions) {
    B $LtGray $cx ($roofBase - 8) -10 "3665.dat" $R0
}

L "0 STEP"
L "0 NOFILE"

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
$sb.ToString() | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
Write-Host "Generated: $outPath"
$lineCount = $sb.ToString().Split([Environment]::NewLine).Count
Write-Host "Lines: $lineCount"
