# EuropeanTownhouse.ps1
# Generates a 2-story European townhouse with dual facade sections
# Left section (12 studs): Tan with arched windows
# Right section (20 studs): Light blue with standard windows + door

param(
    [string]$OutputFile = "output/EuropeanTownhouse.ldr",
    [string]$ModelName = "European Townhouse"
)

$sb = [System.Text.StringBuilder]::new()
function L([string]$t) { [void]$sb.AppendLine($t) }

# ============================================================
# ROTATION MATRICES
# ============================================================
$R0   = "1 0 0 0 1 0 0 0 1"
$R90  = "0 0 -1 0 1 0 1 0 0"
$R180 = "-1 0 0 0 1 0 0 0 -1"
$R270 = "0 0 1 0 1 0 -1 0 0"
$RPerp = "0 0 1 0 1 0 -1 0 0"

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

function WallRowZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x,[array]$gaps=@(),[int]$offset=0) {
    $sorted = $gaps | Sort-Object { $_.s }
    $z = $zMin
    foreach ($g in $sorted) {
        if ($g.s -gt $z + 0.1) { FillZ $c $z $g.s $y $x $offset }
        $z = $g.e
    }
    if ($z -lt $zMax - 0.1) { FillZ $c $z $zMax $y $x $offset }
}

function PlaceWindow([int]$fc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60594.dat" $r
    B 47  $x $y $z "60592.dat" $r
}

function PlaceSmallWindow([int]$fc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "3853.dat" $r
    B 47  $x $y $z "3856.dat" $r
}

function PlaceDoor([int]$fc,[int]$dc,[double]$x,[double]$y,[double]$z,[string]$r=$R0) {
    B $fc $x $y $z "60596.dat" $r
    B $dc $x $y $z "57895.dat" $r
}

function WindowBox([double]$x,[double]$y,[double]$z) {
    # Brown shelf plate
    B $Brown $x $y $z "3710.dat" $R0
    # Flowers on top (1 plate up = y-8)
    $fy = $y - 8
    B $Yellow ($x - 20) $fy $z "4073.dat" $R0
    B $Green  $x        $fy $z "4073.dat" $R0
    B $Yellow ($x + 20) $fy $z "4073.dat" $R0
}

# ============================================================
# COLORS
# ============================================================
$Tan     = 19    # Left section walls
$Blue    = 212   # Right section walls (Bright Light Blue)
$DkGray  = 72    # Dark Bluish Gray - base
$LtGray  = 71    # Light Bluish Gray - roof/parapet
$White   = 15    # Window frames
$Brown   = 6     # Window boxes (LDraw Brown)
$Yellow  = 14    # Flowers
$Green   = 10    # Flowers / Bright Green
$Glass   = 47    # Trans Clear

# ============================================================
# DIMENSIONS
# ============================================================
$FZ  = 10       # Front wall Z center
$BZ  = 630      # Back wall Z center
$LX  = 10       # Left wall X center
$RX  = 630      # Right wall X center
$DivX = 240     # Left/right section boundary (12 studs)

# Y coordinates: ground=140, each brick row = -24
# Ground floor rows 1-12: Y = 140 - row*24
# Floor sep plates: Y = -156, -164
# First floor rows 1-12: Y = -164 - row*24
# Roof plates: Y = -460, -468

# Gap definitions for front wall openings
# Left section arch opening (6 studs wide centered in 12-stud section)
$archGap = @(@{s=60; e=180})

# Right section ground floor: door center + 2 windows
$gfRightDoorOnly    = @(@{s=400; e=480})
$gfRightAll         = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

# Right section first floor: 3 windows
$ffRightWindows     = @(@{s=280; e=360}, @{s=400; e=480}, @{s=520; e=600})

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

# 32x32 baseplate
B $DkGray 320 140 320 "3811.dat" $R0

# Raised sidewalk step along front (2 studs deep, inside baseplate)
# Plates at Y=132, tiles at Y=124
for ($z = 10; $z -le 30; $z += 20) {
    FillXPlate $LtGray 0 640 132 $z
}
for ($z = 10; $z -le 30; $z += 20) {
    FillXTile $LtGray 0 640 124 $z
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
# Rows 1-8: gap for arch opening (X=60 to 180)
# Rows 9-12: solid wall
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 8) {
        WallRowX $Tan 0 $DivX $y $FZ $archGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }
}

# Arch brick at top of opening: 3307.dat (Arch 1x6x2)
# Top at row 7 (Y=-28), extends down 48 LDU to Y=20
B $Tan 120 -28 $FZ "3307.dat" $R0

# Window glass in arch opening (1x4x6 glass centered)
B $White 120 -4 $FZ "60594.dat" $R0
B $Glass 120 -4 $FZ "60592.dat" $R0

# Interior bathroom detail (white 1x2 brick as fixture)
B $White 120 116 30 "3004.dat" $R0
B $White 120 92  30 "3003.dat" $R0

L "0 // Left section front wall complete"

# --- RIGHT SECTION FRONT WALL (Blue, X=240 to 640) ---
# Rows 1-6: gaps for door + windows
# Rows 7-12: solid wall above openings
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 6) {
        WallRowX $Blue $DivX 640 $y $FZ $gfRightAll $off
    } else {
        FillX $Blue $DivX 640 $y $FZ $off
    }
}

# Door (center of right section at X=440)
PlaceDoor $White $LtGray 440 -4 $FZ

# Sign beside door (1x2 white tile)
B $White 370 44 $FZ "3069b.dat" $R0

# Windows (X=320 left, X=560 right)
PlaceWindow $White 320 -4 $FZ
PlaceWindow $White 560 -4 $FZ

# Window boxes on ground floor windows
WindowBox 320 140 -10
WindowBox 560 140 -10

L "0 // Right section front wall complete"

# --- SIDE WALLS ---
# Left wall (X=10, Tan)
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Tan 0 640 $y $LX $off
}

# Right wall (X=630, Blue)
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillZ $Blue 0 640 $y $RX $off
}

# --- BACK WALL ---
# Left section back (Tan)
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
    FillX $Tan 0 $DivX $y $BZ $off
}
# Right section back (Blue)
for ($row = 1; $row -le 12; $row++) {
    $y = 140 - $row * 24
    $off = (($row % 2) * 20)
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
L "0 // Floor separation"
for ($z = 10; $z -le 630; $z += 20) {
    FillXPlate $LtGray 0 640 -156 $z
    FillXPlate $LtGray 0 640 -164 $z
}

L "0 STEP"

# First floor Y: row N => Y = -164 - N*24
# Row 1: -188, Row 2: -212, ... Row 12: -452

# --- LEFT SECTION FRONT WALL (Tan, arch window + balcony) ---
$ffArchGap = @(@{s=60; e=180})

for ($row = 1; $row -le 12; $row++) {
    $y = -164 - $row * 24
    $off = (($row % 2) * 20)
    if ($row -le 8) {
        WallRowX $Tan 0 $DivX $y $FZ $ffArchGap $off
    } else {
        FillX $Tan 0 $DivX $y $FZ $off
    }
}

# Arch at top of first floor opening
# Row 7: Y = -164-7*24 = -332, Row 8: Y = -356
B $Tan 120 (-164 - 7*24) $FZ "3307.dat" $R0

# Window in arch
B $White 120 (-164 - 6*24) $FZ "60594.dat" $R0
B $Glass 120 (-164 - 6*24) $FZ "60592.dat" $R0

# --- BALCONY ---
L "0 // Balcony on first floor left section"
# Balcony floor plates extending outward (3 studs in front of wall)
for ($z = -30; $z -le 10; $z += 20) {
    FillXPlate $LtGray 40 200 -164 $z
}
# Balcony railing - front edge at Z=-30
# Posts (1x1 bricks, 1 brick tall)
B $LtGray 50  -188 -30 "3005.dat" $R0
B $LtGray 110 -188 -30 "3005.dat" $R0
B $LtGray 170 -188 -30 "3005.dat" $R0
# Top rail (tiles)
FillXTile $LtGray 40 200 -196 -30

# Side rails
B $LtGray 50  -188 -10 "3005.dat" $R0
B $LtGray 170 -188 -10 "3005.dat" $R0

L "0 // Balcony complete"

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
$ffWinY = -164 - 6*24  # Y = -308
PlaceWindow $White 320 $ffWinY $FZ
PlaceWindow $White 440 $ffWinY $FZ
PlaceWindow $White 560 $ffWinY $FZ

# Window boxes below first floor windows
$wbY = -156   # at floor separation plate level
WindowBox 320 $wbY -10
WindowBox 440 $wbY -10
WindowBox 560 $wbY -10

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

# Roof level: top of first floor row 12 = -164-12*24 = -452
$roofBase = -452

# --- ROOF PLATES (full footprint) ---
L "0 // Roof plates"
for ($z = 10; $z -le 630; $z += 20) {
    FillXPlate $LtGray 0 640 ($roofBase - 8) $z
}

L "0 STEP"

# --- LEFT SECTION ROOF CAP (Tan, slightly lower) ---
# Left section cap: 1 brick lower than right section
$leftCapY = $roofBase - 16  # 2 plates above roof base plate
for ($z = 10; $z -le 630; $z += 20) {
    FillXTile $Tan 0 $DivX $leftCapY $z
}

# --- RIGHT SECTION PARAPET ---
L "0 // Parapet walls"
$parapetY1 = $roofBase - 8 - 24   # 1 brick above roof plate
$parapetY2 = $roofBase - 8 - 48   # 2 bricks above roof plate

# Front parapet (right section only - left has lower cap)
FillX $LtGray $DivX 640 $parapetY1 $FZ
FillX $LtGray $DivX 640 $parapetY2 $FZ

# Parapet tile cap on right section
FillXTile $LtGray $DivX 640 ($parapetY2 - 8) $FZ

# Side parapets (1 brick tall)
FillZ $LtGray 0 640 $parapetY1 $RX

# Back parapet
FillX $LtGray 0 640 $parapetY1 $BZ

# --- DECORATIVE CORBELS ---
L "0 // Corbels - inverted slopes as decorative brackets"
# 4 evenly spaced across right section front (X=280 to X=600)
# Using 3665.dat (Slope Inverted 45 2x1)
$corbelY = $parapetY1 + 24  # just below parapet, at roof plate level
$corbelPositions = @(300, 380, 500, 580)
foreach ($cx in $corbelPositions) {
    # Inverted slope facing outward (toward viewer)
    B $LtGray $cx $corbelY ($FZ - 10) "3665.dat" $R0
}

# --- LEFT SECTION PARAPET TRIM ---
# Small parapet on left section (1 brick, lower than right)
$leftParY = $leftCapY - 24
FillX $Tan 0 $DivX $leftParY $FZ
FillXTile $Tan 0 $DivX ($leftParY - 8) $FZ

L "0 STEP"
L "0 NOFILE"

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
$sb.ToString() | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
Write-Host "Generated: $outPath"
Write-Host "Lines: $($sb.ToString().Split("`n").Count)"
