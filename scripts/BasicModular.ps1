# BasicModular.ps1
# Proof-of-concept: Georgian-style modular using the shared LDraw module
# 32x32 base, 2 stories, recessed windows, dentil cornice, proper parapet

param(
    [string]$OutputFile = "output/BasicModular.ldr",
    [string]$StyleName = "Georgian"
)

Import-Module (Join-Path $PSScriptRoot "..\modules\LDraw.psm1") -Force

# ============================================================
# STYLE + COLORS
# ============================================================
$style = Get-BuildingStyle $StyleName

$Wall  = 28    # Dark Tan - primary facade
$Trim  = 15    # White - window frames, cornices
$Roof  = 71    # Light Bluish Gray - parapet, floor plates
$Base  = 72    # Dark Bluish Gray - baseplate
$Door  = 70    # Reddish Brown - door color
$Accent = 19   # Tan - sills, headers, bands

$rows = $style.RowsPerFloor   # 10 for Georgian

# ============================================================
# DIMENSIONS
# ============================================================
$FZ = 10;  $BZ = 630           # Front/back wall Z
$LX = 10;  $RX = 630           # Left/right wall X
$Ground = 140                   # Ground Y level

# Ground floor: rows 1-N from Y=(Ground-24) downward
# Top of ground floor = Ground - rows*24
$gfTopY = $Ground - $rows * 24

# Floor separation: 2 plates (16 LDU) above ground floor top
$floorSepY = $gfTopY

# First floor base Y: below floor separation
$ffBaseY = $floorSepY - 16
$ffTopY = $ffBaseY - $rows * 24

# Roof plate Y
$roofY = $ffTopY

# ============================================================
# OPENING DEFINITIONS
# ============================================================
# Window opening = 4 studs wide (80 LDU), 3 rows tall (for 1x4x3 window)
# Door opening = 4 studs wide (80 LDU), 6 rows tall (for 1x4x6 door)
# Rows count from bottom: row 1 = ground level

# Ground floor front: 1 door (center), 2 windows (flanking)
# Windows at rows 4-6 (elevated above floor, 3 rows for 1x4x3)
# Door at rows 1-6 (full height)
$gfFrontOpenings = @(
    @{xMin=100; xMax=180; fromRow=4; toRow=6}    # Left window
    @{xMin=280; xMax=360; fromRow=1; toRow=6}    # Center door
    @{xMin=460; xMax=540; fromRow=4; toRow=6}    # Right window
)

# First floor front: 3 windows at rows 4-6
$ffFrontOpenings = @(
    @{xMin=100; xMax=180; fromRow=4; toRow=6}
    @{xMin=280; xMax=360; fromRow=4; toRow=6}
    @{xMin=460; xMax=540; fromRow=4; toRow=6}
)

# ============================================================
# BUILD MODEL
# ============================================================
Start-Model "Basic Modular"

Add-SubmodelRef "base"
Add-SubmodelRef "ground_floor"
Add-SubmodelRef "first_floor"
Add-SubmodelRef "roof"
End-Model

# --- BASE ---
Start-Submodel "base"
Add-Part $Base 320 $Ground 320 "3811.dat"
End-Submodel

# --- GROUND FLOOR ---
Start-Submodel "ground_floor"
Add-Comment "Ground floor walls"

# Front wall with openings
Add-WallX $Wall 0 640 $Ground $rows $FZ $gfFrontOpenings

# Back wall (solid)
Add-WallX $Wall 0 640 $Ground $rows $BZ

# Side walls (solid)
Add-WallZ $Wall 0 640 $Ground $rows $LX
Add-WallZ $Wall 0 640 $Ground $rows $RX

# Door assembly (top of door opening = ground - 6*24 = ground - 144)
$doorY = $Ground - 6 * 24
Add-DoorSurround -FrameColor $Trim -DoorColor $Door -WallColor $Accent `
    -X 320 -Y $doorY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Header $style.WindowHeader

# Window assemblies (top of 3-row window opening = ground - 6*24)
$winY = $Ground - 6 * 24
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 140 -Y $winY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 500 -Y $winY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Sill $style.WindowSill -Header $style.WindowHeader

End-Submodel

# --- FIRST FLOOR ---
Start-Submodel "first_floor"
Add-Comment "Floor separation plates (interior only)"
Add-FloorPlates $Roof 20 620 30 610 $floorSepY 2

# Floor band across front facade
if ($style.FloorBand) {
    Add-FloorBand $Accent 0 640 $floorSepY $FZ "Front" $style.FloorBandStyle
}

Add-Step
Add-Comment "First floor walls"

# Front wall with window openings
Add-WallX $Wall 0 640 $ffBaseY $rows $FZ $ffFrontOpenings

# Back wall (solid)
Add-WallX $Wall 0 640 $ffBaseY $rows $BZ

# Side walls (solid)
Add-WallZ $Wall 0 640 $ffBaseY $rows $LX
Add-WallZ $Wall 0 640 $ffBaseY $rows $RX

# First floor windows (top of opening = ffBaseY - 6*24)
$ffWinY = $ffBaseY - 6 * 24
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 140 -Y $ffWinY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 320 -Y $ffWinY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 500 -Y $ffWinY -Z $FZ -Wall "Front" `
    -Recessed $style.WindowRecess -Sill $style.WindowSill -Header $style.WindowHeader

# Cornice band under roofline across front
if ($style.CorniceStyle -ne "None") {
    $corniceY = $ffTopY + 12
    Add-CorniceBand $Trim 0 640 $corniceY $FZ "Front" $style.CorniceStyle
}

End-Submodel

# --- ROOF ---
Start-Submodel "roof"
Add-Comment "Roof plates"
Add-FloorPlates $Roof 0 640 0 640 ($roofY - 8) 1

Add-Step
Add-Comment "Parapet"
$parY = $roofY - 8 - 24
Add-Parapet $Roof 0 640 0 640 $parY $style.ParapetRows $style.ParapetCap "FBLR"

End-Submodel

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
Save-LDrawFile $outPath
