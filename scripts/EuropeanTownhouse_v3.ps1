# EuropeanTownhouse_v3.ps1
# v3 fixes: floor separation plates use building colors on all exterior faces,
#           Z=30 row gapped behind front windows to reduce grey bars through glass
# v2 fixes: corbel collision, floor plates behind windows, parapet wrapping,
#           balcony overlap, accent band between floors

param(
    [string]$OutputFile = "output/EuropeanTownhouse_v3.ldr",
    [string]$ModelName = "European Townhouse v3"
)

$sb = [System.Text.StringBuilder]::new()
function L([string]$t) { [void]$sb.AppendLine($t) }

# ============================================================
# ROTATION MATRICES
# ============================================================
$R0   = "1 0 0 0 1 0 0 0 1"
$R90  = "0 0 -1 0 1 0 1 0 0"

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
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) { B $c ($x + $s.w/2) $y $z $s.p $R0; $x += $s.w; break }
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

# Plate row along X with gaps
function PlateRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[array]$gaps=@()) {
    $sorted = $gaps | Sort-Object { $_.s }
    $x = $xMin
    foreach ($g in $sorted) {
        if ($g.s -gt $x + 0.1) { FillXPlate $c $x $g.s $y $z }
        $x = $g.e
    }
    if ($x -lt $xMax - 0.1) { FillXPlate $c $x $xMax $y $z }
}

function PlaceWindow([int]$fc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60594.dat" $r
    B 47  $x $y $z "60592.dat" $r
}

function PlaceDoor([int]$fc,[int]$dc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60596.dat" $r
    B $dc $x $y $z "57895.dat" $r
}

function WindowBox([double]$x,[double]$y,[double]$z) {
    B $Brown $x $y $z "3710.dat" $R0
    $fy = $y - 8
    B $Yellow ($x - 20) $fy $z "4073.dat" $R0
    B $Green  $x        $fy $z "4073.dat" $R0
    B $Yellow ($x + 20) $fy $z "4073.dat" $R0
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

# Gap definitions
$archGap        = @(@{s=60; e=180})
$gfRightAll     = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})
$ffRightWindows = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# All front openings combined (for floor plate gaps)
$allFrontGaps   = @(@{s=60; e=180}, @{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

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

# --- LEFT SECTION FRONT WALL (Tan, X=0 to 240) ---
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 8) {
        WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }
}

# Arch brick: 3307.dat (Arch 1x6x2) at top of opening
B $Tan 120 -28 $FZ "3307.dat" $R0

# Window + glass in arch opening
PlaceWindow $White 120 -4 $FZ

# Interior bathroom detail
B $White 120 116 30 "3004.dat" $R0
B $White 120 92  30 "3003.dat" $R0

# --- RIGHT SECTION FRONT WALL (Blue, X=240 to 640) ---
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 6) {
        WallRowX $Blue $DivX 640 $y $FZ $gfRightAll $off
    } else {
        FillX $Blue $DivX 640 $y $FZ $off
    }
}

# Door + windows
PlaceDoor $White $LtGray 440 -4 $FZ
B $White 370 44 $FZ "3069b.dat" $R0    # sign tile
PlaceWindow $White 320 -4 $FZ
PlaceWindow $White 560 -4 $FZ

# Window boxes at ground level in front of wall
WindowBox 320 140 -10
WindowBox 560 140 -10

# --- SIDE WALLS ---
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Tan  0 640 $y $LX $off
    FillZ $Blue 0 640 $y $RX $off
}

# --- BACK WALL ---
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
# SUBMODEL: FIRST FLOOR
# ============================================================
L "0 FILE first_floor.ldr"
L "0 first_floor"
L "0 Name: first_floor.ldr"
L "0 Author: Claude.Bricks"
L ""

# --- FLOOR SEPARATION PLATES ---
# v3 FIX: exterior-facing plate rows use building colors instead of grey.
# Side wall edges (1 stud at X=0-20 and X=620-640) also colored to prevent
# grey floor plates showing through the side wall gap at floor sep height.
# Z=30 row gapped at window positions to reduce grey bars visible through glass.
L "0 // Floor separation"
foreach ($yp in @(-156, -164)) {
    # Front row (Z=10): colored plates matching wall sections, with gaps at openings
    PlateRowX $Tan  0 $DivX $yp $FZ $archGap
    PlateRowX $Blue $DivX 640 $yp $FZ $ffRightWindows

    # Row Z=30: colored side edges + grey middle with gaps behind front windows
    FillXPlate $Tan    0  20  $yp 30
    PlateRowX  $LtGray 20 620 $yp 30 $allFrontGaps
    FillXPlate $Blue   620 640 $yp 30

    # Interior rows (Z=50 to Z=610): colored side edges + grey middle
    for ($z = 50; $z -le 610; $z += 20) {
        FillXPlate $Tan    0  20  $yp $z
        FillXPlate $LtGray 20 620 $yp $z
        FillXPlate $Blue   620 640 $yp $z
    }

    # Back row (Z=630): colored plates matching wall sections
    FillXPlate $Tan  0 $DivX $yp $BZ
    FillXPlate $Blue $DivX 640 $yp $BZ
}

# --- ACCENT BAND between floors (trim overhang on front) ---
L "0 // Accent band"
FillXTile $LtGray 0 $DivX -156 ($FZ - 10)
FillXTile $LtGray $DivX 640 -156 ($FZ - 10)

L "0 STEP"

# --- LEFT SECTION FRONT WALL (Tan, arch window + balcony) ---
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 8) {
        WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }
}

# Arch at top of first floor opening
B $Tan 120 (-164 - 7*24) $FZ "3307.dat" $R0

# Window in arch
$ffArchWinY = -164 - 6*24   # -308
PlaceWindow $White 120 $ffArchWinY $FZ

# --- BALCONY ---
# Only overhang plates (Z=-30, Z=-10); Z=10 is covered by floor sep
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

# --- RIGHT SECTION FRONT WALL (Blue, 3 windows) ---
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 6) {
        WallRowX $Blue $DivX 640 $y $FZ $ffRightWindows $off
    } else {
        FillX $Blue $DivX 640 $y $FZ $off
    }
}

# First floor windows
$ffWinY = -164 - 6*24  # -308
PlaceWindow $White 320 $ffWinY $FZ
PlaceWindow $White 440 $ffWinY $FZ
PlaceWindow $White 560 $ffWinY $FZ

# Window boxes below first floor windows (in front of wall)
WindowBox 320 -148 -10
WindowBox 440 -148 -10
WindowBox 560 -148 -10

# --- SIDE WALLS (first floor) ---
for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Tan  0 640 $y $LX $off
    FillZ $Blue 0 640 $y $RX $off
}

# --- BACK WALL (first floor) ---
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

$roofBase = -452   # top of first floor row 12

# --- ROOF PLATES ---
L "0 // Roof plates"
for ($z = 10; $z -le 630; $z += 20) {
    FillXPlate $LtGray 0 640 ($roofBase - 8) $z
}

L "0 STEP"

# --- LEFT SECTION ROOF CAP (Tan tiles, slightly higher than right) ---
$leftCapY = $roofBase - 16   # -468
for ($z = 10; $z -le 630; $z += 20) {
    FillXTile $Tan 0 $DivX $leftCapY $z
}

# --- RIGHT SECTION PARAPET ---
$parapetY1 = $roofBase - 8 - 24   # -484 (1 brick above roof plate)
$parapetY2 = $roofBase - 8 - 48   # -508 (2 bricks above roof plate)

L "0 // Right section parapet"
# Front (2 bricks tall + tile cap)
FillX $LtGray $DivX 640 $parapetY1 $FZ
FillX $LtGray $DivX 640 $parapetY2 $FZ
FillXTile $LtGray $DivX 640 ($parapetY2 - 8) $FZ

# Right side wall parapet (1 brick)
FillZ $LtGray 0 640 $parapetY1 $RX

# Right section back parapet (1 brick)
FillX $LtGray $DivX 640 $parapetY1 $BZ

# --- DECORATIVE CORBELS ---
# At Z=-10 to avoid collision with roof plates at Z=10
L "0 // Corbels"
$corbelPositions = @(300, 380, 500, 580)
foreach ($cx in $corbelPositions) {
    B $LtGray $cx ($roofBase - 8) -10 "3665.dat" $R0
}

# --- LEFT SECTION PARAPET ---
$leftParY = $leftCapY - 24   # -492
L "0 // Left section parapet"
# Front (1 brick + tile cap)
FillX $Tan 0 $DivX $leftParY $FZ
FillXTile $Tan 0 $DivX ($leftParY - 8) $FZ

# Left side wall parapet (1 brick)
FillZ $Tan 0 640 $leftParY $LX

# Left section back parapet (1 brick)
FillX $Tan 0 $DivX $leftParY $BZ

L "0 STEP"
L "0 NOFILE"

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
$sb.ToString() | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
Write-Host "Generated: $outPath"
Write-Host "Lines: $($sb.ToString().Split("`n").Count)"
