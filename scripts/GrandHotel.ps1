# GrandHotel.ps1
# 3-story colorful Parisian hotel with ground-floor colonnade,
# upper-floor windows with awnings and flower boxes, dentil cornices
# 32x32 baseplate, Victorian style

param([string]$OutputFile = "output/GrandHotel.ldr")

Import-Module (Join-Path $PSScriptRoot "..\modules\LDraw.psm1") -Force

# ============================================================
# COLORS
# ============================================================
$Tan       = 19    # Primary walls
$White     = 15    # Columns, window frames, trim
$SandGreen = 378   # Floor bands, parapet cap, cornices
$DarkRed   = 320   # Awnings
$RBrown    = 70    # Flower box planters
$DkGray    = 72    # Baseplate, roof plates
$LtGray    = 71    # Floor plates, door glass
$Glass     = 47    # Trans Clear
$Yellow    = 14
$Red       = 4
$Green     = 2
$LtBlue    = 9

$flowerColors = @($Yellow, $Red, $Green, $LtBlue)
$script:boxIdx = 0

# ============================================================
# DIMENSIONS
# ============================================================
$FZ = 10;  $BZ = 630
$LX = 10;  $RX = 630
$Ground = 140

$gfRows = 10   # Ground floor (tall colonnade)
$ufRows = 8    # Upper floors

# Y calculations
$gfTopY  = $Ground - $gfRows * 24       # -100

$fs1y1   = $gfTopY - 8                  # -108
$fs1y2   = $fs1y1 - 8                   # -116
$f2BaseY = $fs1y2                        # -116
$f2TopY  = $f2BaseY - $ufRows * 24      # -308

$fs2y1   = $f2TopY - 8                  # -316
$fs2y2   = $fs2y1 - 8                   # -324
$f3BaseY = $fs2y2                        # -324
$f3TopY  = $f3BaseY - $ufRows * 24      # -516

$roofY1  = $f3TopY - 8                  # -524
$roofY2  = $roofY1 - 8                  # -532

# ============================================================
# COLUMN POSITIONS
# ============================================================
$frontColX = @(10, 110, 210, 310, 410, 510, 630)
$rightColZ = @(110, 210, 310, 410, 510, 630)

# Gaps in entablature where columns stand (front wall, X coords)
$frontColGaps = @()
foreach ($cx in $frontColX) { $frontColGaps += @{s=($cx-10); e=($cx+10)} }

# Gaps in entablature where columns stand (right wall, Z coords)
$rightColZAll = @(10) + $rightColZ
$rightColGaps = @()
foreach ($cz in $rightColZAll) { $rightColGaps += @{s=($cz-10); e=($cz+10)} }

# Glass panel centers between columns (skip entrance gap at X=260)
$frontGlassCenters = @(60, 160, 360, 460, 570)
$rightGlassCenters = @(60, 160, 260, 360, 460, 570)

# ============================================================
# UPPER FLOOR OPENINGS
# ============================================================
# 4 windows per facade, rows 3-5 (3 bricks = 72 LDU for 1x4x3 frame)
$winCentersX = @(120, 260, 400, 540)
$winCentersZ = @(120, 260, 400, 540)

$ufFrontOpenings = @(
    @{xMin=80;  xMax=160; fromRow=3; toRow=5}
    @{xMin=220; xMax=300; fromRow=3; toRow=5}
    @{xMin=360; xMax=440; fromRow=3; toRow=5}
    @{xMin=500; xMax=580; fromRow=3; toRow=5}
)
$ufRightOpenings = @(
    @{zMin=80;  zMax=160; fromRow=3; toRow=5}
    @{zMin=220; zMax=300; fromRow=3; toRow=5}
    @{zMin=360; zMax=440; fromRow=3; toRow=5}
    @{zMin=500; zMax=580; fromRow=3; toRow=5}
)
$ufBackOpenings = @(
    @{xMin=200; xMax=280; fromRow=3; toRow=5}
    @{xMin=360; xMax=440; fromRow=3; toRow=5}
)
$ufLeftOpenings = @(
    @{zMin=200; zMax=280; fromRow=3; toRow=5}
    @{zMin=360; zMax=440; fromRow=3; toRow=5}
)

$backWinX = @(240, 400)
$leftWinZ = @(240, 400)

# ============================================================
# HELPER: Flower box (shelf + 3 flowers)
# ============================================================
function PlaceFlowerBox([double]$px, [double]$py, [double]$pz, [string]$axis) {
    $ci = $script:boxIdx % $flowerColors.Count
    $c1 = $flowerColors[$ci]
    $c2 = $flowerColors[($ci + 1) % $flowerColors.Count]
    $c3 = $flowerColors[($ci + 2) % $flowerColors.Count]

    if ($axis -eq "X") {
        Add-Part $RBrown $px $py $pz "3710.dat" $R0
        Add-Part $c1 ($px - 20) ($py - 8) $pz "4073.dat" $R0
        Add-Part $c2 $px ($py - 8) $pz "4073.dat" $R0
        Add-Part $c3 ($px + 20) ($py - 8) $pz "4073.dat" $R0
    } else {
        Add-Part $RBrown $px $py $pz "3710.dat" $R90
        Add-Part $c1 $px ($py - 8) ($pz - 20) "4073.dat" $R0
        Add-Part $c2 $px ($py - 8) $pz "4073.dat" $R0
        Add-Part $c3 $px ($py - 8) ($pz + 20) "4073.dat" $R0
    }
    $script:boxIdx++
}

# ============================================================
# HELPER: Build an upper floor (F2 or F3)
# ============================================================
function BuildUpperFloor([string]$Name, [double]$BaseY, [double]$PrevTopY) {
    Start-Submodel $Name

    # --- Floor separation plates ---
    Add-Comment "Floor separation"
    $fsy1 = $PrevTopY - 8
    $fsy2 = $PrevTopY - 16

    # Wall-color plates at wall positions (continuity)
    foreach ($yp in @($fsy1, $fsy2)) {
        Fill-PlatesX $Tan 0 640 $yp $FZ
        Fill-PlatesX $Tan 0 640 $yp $BZ
        Fill-PlatesZ $Tan 20 620 $yp $LX
        Fill-PlatesZ $Tan 20 620 $yp $RX
    }
    # Interior floor plates
    Add-FloorPlates $LtGray 20 620 30 610 $fsy1 2

    # --- Dentil cornice on front and right ---
    Add-Comment "Dentil cornice"
    $corniceY = $PrevTopY + 12
    Add-CorniceBand $SandGreen 0 640 $corniceY $FZ "Front" "Dentil"
    Add-CorniceBand $SandGreen 0 640 $corniceY $RX "Right" "Dentil"

    Add-Step

    # --- Walls ---
    Add-Comment "Walls with window openings"
    Add-WallX $Tan 0 640 $BaseY $ufRows $FZ $ufFrontOpenings
    Add-WallX $Tan 0 640 $BaseY $ufRows $BZ $ufBackOpenings
    Add-WallZ $Tan 0 640 $BaseY $ufRows $LX $ufLeftOpenings
    Add-WallZ $Tan 0 640 $BaseY $ufRows $RX $ufRightOpenings

    # --- Windows ---
    $winY = $BaseY - 5 * 24
    $awningY = $BaseY - 6 * 24
    $boxY = $winY + 72

    Add-Comment "Front windows, awnings, flower boxes"
    foreach ($wx in $winCentersX) {
        Add-WindowBay -FrameColor $White -WallColor $Tan `
            -X $wx -Y $winY -Z $FZ -Wall "Front" `
            -Sill $false -Header $false
        Add-Part $DarkRed $wx $awningY ($FZ - 20) "3037.dat" $R0
        PlaceFlowerBox $wx $boxY ($FZ - 20) "X"
    }

    Add-Comment "Right windows, awnings, flower boxes"
    foreach ($wz in $winCentersZ) {
        Add-WindowBay -FrameColor $White -WallColor $Tan `
            -X $RX -Y $winY -Z $wz -Wall "Right" `
            -Sill $false -Header $false
        Add-Part $DarkRed ($RX + 20) $awningY $wz "3037.dat" $R90
        PlaceFlowerBox ($RX + 20) $boxY $wz "Z"
    }

    Add-Comment "Back windows"
    foreach ($bx in $backWinX) {
        Add-WindowBay -FrameColor $White -WallColor $Tan `
            -X $bx -Y $winY -Z $BZ -Wall "Back" `
            -Sill $false -Header $false
    }

    Add-Comment "Left windows"
    foreach ($lz in $leftWinZ) {
        Add-WindowBay -FrameColor $White -WallColor $Tan `
            -X $LX -Y $winY -Z $lz -Wall "Left" `
            -Sill $false -Header $false
    }

    End-Submodel
}

# ============================================================
# MODEL STRUCTURE
# ============================================================
Start-Model "Grand Hotel"
Add-SubmodelRef "base"
Add-SubmodelRef "ground_floor"
Add-SubmodelRef "floor2"
Add-SubmodelRef "floor3"
Add-SubmodelRef "roof"
End-Model

# ============================================================
# BASE
# ============================================================
Start-Submodel "base"
Add-Part $DkGray 320 $Ground 320 "3811.dat"
End-Submodel

# ============================================================
# GROUND FLOOR
# ============================================================
Start-Submodel "ground_floor"

# --- Front columns ---
Add-Comment "Front colonnade columns"
foreach ($cx in $frontColX) {
    for ($row = 1; $row -le $gfRows; $row++) {
        $y = $Ground - $row * 24
        Add-Part $White $cx $y $FZ "3005.dat" $R0
    }
}

# --- Right columns (skip Z=10 corner, already placed by front) ---
Add-Comment "Right colonnade columns"
foreach ($cz in $rightColZ) {
    for ($row = 1; $row -le $gfRows; $row++) {
        $y = $Ground - $row * 24
        Add-Part $White $RX $y $cz "3005.dat" $R90
    }
}

Add-Step

# --- Glass panels between front columns ---
Add-Comment "Front glass panels (1x4x6 door frames)"
$glassTopY = $Ground - 6 * 24   # -4
foreach ($gx in $frontGlassCenters) {
    Add-Part $LtGray $gx $glassTopY $FZ "60596.dat" $R0
    Add-Part $Glass  $gx $glassTopY $FZ "57895.dat" $R0
}

# --- Glass panels between right columns ---
Add-Comment "Right glass panels"
foreach ($gz in $rightGlassCenters) {
    Add-Part $LtGray $RX $glassTopY $gz "60596.dat" $R90
    Add-Part $Glass  $RX $glassTopY $gz "57895.dat" $R90
}

Add-Step

# --- Entablature: solid wall rows 7-10 between columns ---
Add-Comment "Front entablature (rows 7-10)"
for ($row = 7; $row -le $gfRows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Add-WallRowX $Tan 0 640 $y $FZ $frontColGaps $off
}

Add-Comment "Right entablature (rows 7-10)"
for ($row = 7; $row -le $gfRows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Add-WallRowZ $Tan 0 640 $y $RX $rightColGaps $off
}

Add-Step

# --- Back wall (solid) ---
Add-Comment "Back wall (solid)"
for ($row = 1; $row -le $gfRows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksX $Tan 0 640 $y $BZ $off
}

# --- Left wall (solid) ---
Add-Comment "Left wall (solid)"
for ($row = 1; $row -le $gfRows; $row++) {
    $y = $Ground - $row * 24
    $off = ($row % 2) * 20
    Fill-BricksZ $Tan 20 620 $y $LX $off
}

End-Submodel

# ============================================================
# FLOOR 2
# ============================================================
BuildUpperFloor "floor2" $f2BaseY $gfTopY

# ============================================================
# FLOOR 3
# ============================================================
BuildUpperFloor "floor3" $f3BaseY $f2TopY

# ============================================================
# ROOF
# ============================================================
Start-Submodel "roof"

# --- Roof plates ---
Add-Comment "Roof plates"
Add-FloorPlates $DkGray 0 640 0 640 $roofY1 2

# --- Roof cornice ---
Add-Comment "Roof cornice"
$roofCorniceY = $f3TopY + 12
Add-CorniceBand $SandGreen 0 640 $roofCorniceY $FZ "Front" "Dentil"
Add-CorniceBand $SandGreen 0 640 $roofCorniceY $RX "Right" "Dentil"

Add-Step

# --- Parapet ---
Add-Comment "Parapet"
$parY = $roofY2 - 24
Add-Parapet $DkGray 0 640 0 640 $parY 2 $true "FBLR"

# --- Parapet cap in Sand Green ---
Add-Comment "Sand Green parapet cap tiles (overwrite gray cap)"
$capY = $parY - 24 - 8   # top of 2nd parapet row - tile height
Fill-TilesX $SandGreen 0 640 $capY $FZ
Fill-TilesX $SandGreen 0 640 $capY $BZ
Fill-TilesZ $SandGreen 20 620 $capY $LX
Fill-TilesZ $SandGreen 20 620 $capY $RX

End-Submodel

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
Save-LDrawFile $outPath
