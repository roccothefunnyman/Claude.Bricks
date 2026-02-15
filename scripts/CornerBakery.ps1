# CornerBakery.ps1
# Simple 1-story modular building: 32x16 studs, Georgian style
# Features: storefront door, 6 windows, dentil cornice, parapet roof

param(
    [string]$OutputFile = "output/CornerBakery.ldr",
    [string]$StyleName = "Georgian"
)

Import-Module (Join-Path $PSScriptRoot "..\modules\LDraw.psm1") -Force

# ============================================================
# STYLE + COLORS
# ============================================================
$style = Get-BuildingStyle $StyleName

$Wall   = 28    # Dark Tan - primary facade
$Trim   = 15    # White - window frames, cornice
$Accent = 378   # Sand Green - sills, headers, bands
$Door   = 70    # Reddish Brown - door panel
$Roof   = 72    # Dark Bluish Gray - parapet, roof plates
$Base   = 72    # Dark Bluish Gray - baseplate

$rows = $style.RowsPerFloor   # 10 for Georgian

# ============================================================
# DIMENSIONS (32x16 module)
# ============================================================
$FZ = 10;  $BZ = 310            # Front/back wall Z
$LX = 10;  $RX = 630            # Left/right wall X
$Ground = 140                    # Ground Y level

# Top of building walls
$topY = $Ground - $rows * 24    # 140 - 240 = -100

# Window/door placement Y (top of row 6 opening)
$openingTopY = $Ground - 6 * 24  # -4

# ============================================================
# OPENING DEFINITIONS
# ============================================================
# Front (X axis at Z=10): door center, windows flanking
$frontOpenings = @(
    @{xMin=100; xMax=180; fromRow=4; toRow=6}    # Left window
    @{xMin=280; xMax=360; fromRow=1; toRow=6}    # Center door
    @{xMin=460; xMax=540; fromRow=4; toRow=6}    # Right window
)

# Back (X axis at Z=310): 2 windows
$backOpenings = @(
    @{xMin=180; xMax=260; fromRow=4; toRow=6}    # Left window
    @{xMin=380; xMax=460; fromRow=4; toRow=6}    # Right window
)

# Left side (Z axis at X=10): 1 window
$leftOpenings = @(
    @{zMin=120; zMax=200; fromRow=4; toRow=6}
)

# Right side (Z axis at X=630): 1 window
$rightOpenings = @(
    @{zMin=120; zMax=200; fromRow=4; toRow=6}
)

# ============================================================
# BUILD MODEL
# ============================================================
Start-Model "Corner Bakery"

Add-SubmodelRef "base"
Add-SubmodelRef "walls"
Add-SubmodelRef "roof"
End-Model

# --- BASE ---
Start-Submodel "base"
Add-Part $Base 320 $Ground 160 "3867.dat"   # 16x32 baseplate centered
End-Submodel

# --- WALLS ---
Start-Submodel "walls"
Add-Comment "Front wall with door and windows"
Add-WallX $Wall 0 640 $Ground $rows $FZ $frontOpenings

Add-Comment "Back wall with windows"
Add-WallX $Wall 0 640 $Ground $rows $BZ $backOpenings

Add-Comment "Left side wall"
Add-WallZ $Wall 0 320 $Ground $rows $LX $leftOpenings

Add-Comment "Right side wall"
Add-WallZ $Wall 0 320 $Ground $rows $RX $rightOpenings

Add-Step

# --- DOOR ---
Add-Comment "Front door"
Add-DoorSurround -FrameColor $Trim -DoorColor $Door -WallColor $Accent `
    -X 320 -Y $openingTopY -Z $FZ -Wall "Front" `
    -Recessed $false -Header $style.WindowHeader

# --- FRONT WINDOWS ---
Add-Comment "Front windows"
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 140 -Y $openingTopY -Z $FZ -Wall "Front" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 500 -Y $openingTopY -Z $FZ -Wall "Front" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader

# --- BACK WINDOWS ---
Add-Comment "Back windows"
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 220 -Y $openingTopY -Z $BZ -Wall "Back" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X 420 -Y $openingTopY -Z $BZ -Wall "Back" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader

# --- SIDE WINDOWS ---
Add-Comment "Side windows"
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X $LX -Y $openingTopY -Z 160 -Wall "Left" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader
Add-WindowBay -FrameColor $Trim -WallColor $Accent `
    -X $RX -Y $openingTopY -Z 160 -Wall "Right" `
    -Recessed $false -Sill $style.WindowSill -Header $style.WindowHeader

Add-Step

# --- CORNICE ---
Add-Comment "Dentil cornice band"
$corniceY = $topY + 12
Add-CorniceBand $Trim 0 640 $corniceY $FZ "Front" $style.CorniceStyle
Add-CorniceBand $Trim 0 640 $corniceY $BZ "Back" $style.CorniceStyle
Add-CorniceBand $Trim 0 320 $corniceY $LX "Left" $style.CorniceStyle
Add-CorniceBand $Trim 0 320 $corniceY $RX "Right" $style.CorniceStyle

End-Submodel

# --- ROOF ---
Start-Submodel "roof"
Add-Comment "Roof plates"
Add-FloorPlates $Roof 0 640 0 320 ($topY - 8) 1

Add-Step
Add-Comment "Parapet"
$parY = $topY - 8 - 24
Add-Parapet $Roof 0 640 0 320 $parY $style.ParapetRows $style.ParapetCap "FBLR"

End-Submodel

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
Save-LDrawFile $outPath
