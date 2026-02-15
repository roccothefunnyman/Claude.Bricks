# ============================================================
# LDraw.psm1 - Shared LDraw Generation Module
# Claude.Bricks modular building toolkit
# ============================================================
# Import: Import-Module (Join-Path $PSScriptRoot "..\modules\LDraw.psm1") -Force

# --- Module State ---
$script:Lines = [System.Text.StringBuilder]::new()

# --- Rotation Constants ---
$script:R0   = "1 0 0 0 1 0 0 0 1"
$script:R90  = "0 0 -1 0 1 0 1 0 0"
$script:R180 = "-1 0 0 0 1 0 0 0 -1"
$script:R270 = "0 0 1 0 1 0 -1 0 0"

# --- Part Size Tables (sorted descending by width) ---
$script:BrickSizes = @(
    @{w=160;p="3008.dat"},  # 1x8
    @{w=120;p="3009.dat"},  # 1x6
    @{w=80;p="3010.dat"},   # 1x4
    @{w=60;p="3622.dat"},   # 1x3
    @{w=40;p="3004.dat"},   # 1x2
    @{w=20;p="3005.dat"}    # 1x1
)
$script:PlateSizes = @(
    @{w=160;p="3460.dat"},  # 1x8
    @{w=120;p="3666.dat"},  # 1x6
    @{w=80;p="3710.dat"},   # 1x4
    @{w=60;p="3623.dat"},   # 1x3
    @{w=40;p="3023.dat"},   # 1x2
    @{w=20;p="3024.dat"}    # 1x1
)
$script:TileSizes = @(
    @{w=160;p="4162.dat"},  # 1x8
    @{w=120;p="6636.dat"},  # 1x6
    @{w=80;p="2431.dat"},   # 1x4
    @{w=60;p="63864.dat"},  # 1x3
    @{w=40;p="3069b.dat"},  # 1x2
    @{w=20;p="3070b.dat"}   # 1x1
)

# ============================================================
# CORE OUTPUT
# ============================================================

function Add-LDrawLine {
    param([string]$Text)
    [void]$script:Lines.AppendLine($Text)
}

function Add-Part {
    param(
        [int]$Color,
        [double]$X, [double]$Y, [double]$Z,
        [string]$Part,
        [string]$Rotation = $script:R0
    )
    $xr = [math]::Round($X, 1)
    $yr = [math]::Round($Y, 1)
    $zr = [math]::Round($Z, 1)
    Add-LDrawLine "1 $Color $xr $yr $zr $Rotation $Part"
}

function Add-Step { Add-LDrawLine "0 STEP" }

function Add-Comment {
    param([string]$Text)
    Add-LDrawLine "0 // $Text"
}

# ============================================================
# MODEL STRUCTURE
# ============================================================

function Start-Model {
    param([string]$Name, [string]$Author = "Claude.Bricks")
    $script:Lines = [System.Text.StringBuilder]::new()
    Add-LDrawLine "0 FILE $Name.ldr"
    Add-LDrawLine "0 $Name"
    Add-LDrawLine "0 Name: $Name.ldr"
    Add-LDrawLine "0 Author: $Author"
    Add-LDrawLine "0 !LDRAW_ORG Model"
    Add-LDrawLine ""
}

function Add-SubmodelRef {
    param([string]$Name, [string]$Rotation = $script:R0)
    Add-LDrawLine "1 16 0 0 0 $Rotation $Name.ldr"
}

function Start-Submodel {
    param([string]$Name, [string]$Author = "Claude.Bricks")
    Add-LDrawLine ""
    Add-LDrawLine "0 FILE $Name.ldr"
    Add-LDrawLine "0 $Name"
    Add-LDrawLine "0 Name: $Name.ldr"
    Add-LDrawLine "0 Author: $Author"
    Add-LDrawLine ""
}

function End-Submodel {
    Add-Step
    Add-LDrawLine "0 NOFILE"
}

function End-Model {
    Add-LDrawLine "0 NOFILE"
}

function Save-LDrawFile {
    param([string]$Path)
    $script:Lines.ToString() | Out-File -FilePath $Path -Encoding UTF8 -NoNewline
    $lineCount = $script:Lines.ToString().Split("`n").Count
    Write-Host "Generated: $Path ($lineCount lines)"
}

# ============================================================
# FILL FUNCTIONS
# ============================================================

function Fill-Span {
    param(
        [int]$Color,
        [double]$Start,
        [double]$End,
        [double]$Y,
        [double]$Cross,      # Position on the other axis
        [string]$Axis,       # "X" or "Z"
        [array]$Sizes,
        [int]$Offset = 0
    )

    $rot = if ($Axis -eq "X") { $script:R0 } else { $script:R90 }
    $pos = $Start + $Offset

    # Place offset piece at start if staggering
    if ($Offset -gt 0 -and $Offset -lt 160) {
        foreach ($s in $Sizes) {
            if ($s.w -le $Offset + 0.1) {
                $center = $Start + $s.w / 2
                if ($Axis -eq "X") {
                    Add-Part $Color $center $Y $Cross $s.p $rot
                } else {
                    Add-Part $Color $Cross $Y $center $s.p $rot
                }
                break
            }
        }
    }

    while ($pos -lt $End - 0.1) {
        $rem = $End - $pos
        if ($rem -lt 19.9) { break }
        foreach ($s in $Sizes) {
            if ($s.w -le $rem + 0.1) {
                $center = $pos + $s.w / 2
                if ($Axis -eq "X") {
                    Add-Part $Color $center $Y $Cross $s.p $rot
                } else {
                    Add-Part $Color $Cross $Y $center $s.p $rot
                }
                $pos += $s.w
                break
            }
        }
    }
}

function Fill-BricksX {
    param([int]$Color, [double]$XMin, [double]$XMax, [double]$Y, [double]$Z, [int]$Offset=0)
    Fill-Span $Color $XMin $XMax $Y $Z "X" $script:BrickSizes $Offset
}

function Fill-BricksZ {
    param([int]$Color, [double]$ZMin, [double]$ZMax, [double]$Y, [double]$X, [int]$Offset=0)
    Fill-Span $Color $ZMin $ZMax $Y $X "Z" $script:BrickSizes $Offset
}

function Fill-PlatesX {
    param([int]$Color, [double]$XMin, [double]$XMax, [double]$Y, [double]$Z)
    Fill-Span $Color $XMin $XMax $Y $Z "X" $script:PlateSizes
}

function Fill-PlatesZ {
    param([int]$Color, [double]$ZMin, [double]$ZMax, [double]$Y, [double]$X)
    Fill-Span $Color $ZMin $ZMax $Y $X "Z" $script:PlateSizes
}

function Fill-TilesX {
    param([int]$Color, [double]$XMin, [double]$XMax, [double]$Y, [double]$Z)
    Fill-Span $Color $XMin $XMax $Y $Z "X" $script:TileSizes
}

function Fill-TilesZ {
    param([int]$Color, [double]$ZMin, [double]$ZMax, [double]$Y, [double]$X)
    Fill-Span $Color $ZMin $ZMax $Y $X "Z" $script:TileSizes
}

# ============================================================
# WALL GENERATION
# ============================================================

function Add-WallRowX {
    param(
        [int]$Color,
        [double]$XMin, [double]$XMax,
        [double]$Y, [double]$Z,
        [array]$Gaps = @(),
        [int]$Offset = 0
    )
    $sorted = $Gaps | Sort-Object { $_.s }
    $x = $XMin
    foreach ($g in $sorted) {
        if ($g.s -gt $x + 0.1) { Fill-BricksX $Color $x $g.s $Y $Z $Offset }
        $x = $g.e
    }
    if ($x -lt $XMax - 0.1) { Fill-BricksX $Color $x $XMax $Y $Z $Offset }
}

function Add-WallRowZ {
    param(
        [int]$Color,
        [double]$ZMin, [double]$ZMax,
        [double]$Y, [double]$X,
        [array]$Gaps = @(),
        [int]$Offset = 0
    )
    $sorted = $Gaps | Sort-Object { $_.s }
    $z = $ZMin
    foreach ($g in $sorted) {
        if ($g.s -gt $z + 0.1) { Fill-BricksZ $Color $z $g.s $Y $X $Offset }
        $z = $g.e
    }
    if ($z -lt $ZMax - 0.1) { Fill-BricksZ $Color $z $ZMax $Y $X $Offset }
}

# --- High-Level Wall: generates all rows for one floor ---

function Add-WallX {
    param(
        [int]$Color,
        [double]$XMin, [double]$XMax,
        [double]$GroundY,        # Y of ground level (140 for baseplate)
        [int]$Rows,              # Brick rows for this floor
        [double]$Z,
        [array]$Openings = @()   # @{xMin; xMax; fromRow; toRow}
    )
    for ($row = 1; $row -le $Rows; $row++) {
        $y = $GroundY - $row * 24
        $off = ($row % 2) * 20

        $rowGaps = @()
        foreach ($op in $Openings) {
            if ($row -ge $op.fromRow -and $row -le $op.toRow) {
                $rowGaps += @{s=$op.xMin; e=$op.xMax}
            }
        }

        if ($rowGaps.Count -gt 0) {
            Add-WallRowX $Color $XMin $XMax $y $Z $rowGaps $off
        } else {
            Fill-BricksX $Color $XMin $XMax $y $Z $off
        }
    }
}

function Add-WallZ {
    param(
        [int]$Color,
        [double]$ZMin, [double]$ZMax,
        [double]$GroundY,
        [int]$Rows,
        [double]$X,
        [array]$Openings = @()   # @{zMin; zMax; fromRow; toRow}
    )
    for ($row = 1; $row -le $Rows; $row++) {
        $y = $GroundY - $row * 24
        $off = ($row % 2) * 20

        $rowGaps = @()
        foreach ($op in $Openings) {
            if ($row -ge $op.fromRow -and $row -le $op.toRow) {
                $rowGaps += @{s=$op.zMin; e=$op.zMax}
            }
        }

        if ($rowGaps.Count -gt 0) {
            Add-WallRowZ $Color $ZMin $ZMax $y $X $rowGaps $off
        } else {
            Fill-BricksZ $Color $ZMin $ZMax $y $X $off
        }
    }
}

# ============================================================
# ASSEMBLIES - Window, Door, Cornice
# ============================================================

# Wall directions and their depth offsets:
#   Front (Z=10):  recess = +Z, protrude = -Z, rotation = R0
#   Back  (Z=630): recess = -Z, protrude = +Z, rotation = R180
#   Left  (X=10):  recess = +X, protrude = -X, rotation = R270
#   Right (X=630): recess = -X, protrude = +X, rotation = R90

function Get-WallInfo {
    param([string]$Wall)
    switch ($Wall) {
        "Front" { return @{ Axis="X"; Rot=$script:R0;   RecessSign=1;  DepthAxis="Z" } }
        "Back"  { return @{ Axis="X"; Rot=$script:R180; RecessSign=-1; DepthAxis="Z" } }
        "Left"  { return @{ Axis="Z"; Rot=$script:R270; RecessSign=1;  DepthAxis="X" } }
        "Right" { return @{ Axis="Z"; Rot=$script:R90;  RecessSign=-1; DepthAxis="X" } }
    }
}

function Add-WindowBay {
    # Places a 1x4x3 window with optional recess, sill plate, and header plate.
    # The recess shifts the window 10 LDU (half stud) into the building,
    # creating visible depth from the exterior.
    param(
        [int]$FrameColor = 15,     # White frame
        [int]$WallColor,           # For sill/header accents
        [double]$X,                # Window center X
        [double]$Y,                # Window top Y (top of opening)
        [double]$Z,                # Window center Z
        [string]$Wall = "Front",
        [bool]$Recessed = $true,
        [bool]$Sill = $true,
        [bool]$Header = $true
    )

    $wi = Get-WallInfo $Wall
    $rot = $wi.Rot

    # Calculate recessed position (shift half-stud into building)
    $frameX = $X; $frameZ = $Z
    if ($Recessed) {
        if ($wi.DepthAxis -eq "Z") {
            $frameZ = $Z + (10 * $wi.RecessSign)
        } else {
            $frameX = $X + (10 * $wi.RecessSign)
        }
    }

    # Window frame (60594.dat = 1x4x3, 72 LDU tall) and glass
    Add-Part $FrameColor $frameX $Y $frameZ "60594.dat" $rot
    Add-Part 47 $frameX $Y $frameZ "60603.dat" $rot

    # Sill plate at bottom of window opening (at wall face, not recessed)
    if ($Sill) {
        $sillY = $Y + 72   # Bottom of 1x4x3 window
        if ($wi.Axis -eq "X") {
            Add-Part $WallColor $X $sillY $Z "3710.dat" $script:R0
        } else {
            Add-Part $WallColor $X $sillY $Z "3710.dat" $script:R90
        }
    }

    # Header plate above window (at wall face)
    if ($Header) {
        $headerY = $Y - 8
        if ($wi.Axis -eq "X") {
            Add-Part $WallColor $X $headerY $Z "3710.dat" $script:R0
        } else {
            Add-Part $WallColor $X $headerY $Z "3710.dat" $script:R90
        }
    }
}

function Add-DoorSurround {
    # Places a 1x4x6 door frame with glass, optional recess and header.
    param(
        [int]$FrameColor = 15,
        [int]$DoorColor = 71,      # Door glass color
        [int]$WallColor,
        [double]$X, [double]$Y, [double]$Z,
        [string]$Wall = "Front",
        [bool]$Recessed = $true,
        [bool]$Header = $true
    )

    $wi = Get-WallInfo $Wall
    $rot = $wi.Rot

    $frameX = $X; $frameZ = $Z
    if ($Recessed) {
        if ($wi.DepthAxis -eq "Z") {
            $frameZ = $Z + (10 * $wi.RecessSign)
        } else {
            $frameX = $X + (10 * $wi.RecessSign)
        }
    }

    Add-Part $FrameColor $frameX $Y $frameZ "60596.dat" $rot
    Add-Part $DoorColor $frameX $Y $frameZ "57895.dat" $rot

    if ($Header) {
        $headerY = $Y - 8
        if ($wi.Axis -eq "X") {
            Add-Part $WallColor $X $headerY $Z "3710.dat" $script:R0
        } else {
            Add-Part $WallColor $X $headerY $Z "3710.dat" $script:R90
        }
    }
}

# ============================================================
# CORNICE AND TRIM BANDS
# ============================================================

function Add-CorniceBand {
    # Horizontal decorative band along a wall face.
    # Dentil: alternating small plates protruding from wall
    # Corbel: inverted slopes as decorative brackets
    # Plain: continuous plate overhang
    param(
        [int]$Color,
        [double]$Start, [double]$End,  # Range along wall axis
        [double]$Y,
        [double]$WallPos,              # Z for Front/Back walls, X for Left/Right
        [string]$Wall = "Front",
        [string]$Style = "Dentil"      # Dentil, Corbel, Plain
    )

    $wi = Get-WallInfo $Wall
    $isXWall = ($wi.Axis -eq "X")
    # Protrude = shift outward from wall face
    $protrude = $WallPos - (10 * $wi.RecessSign)

    switch ($Style) {
        "Dentil" {
            # 1x2 plates perpendicular to wall, every 2 studs
            $perpRot = if ($isXWall) { $script:R90 } else { $script:R0 }
            for ($pos = $Start + 10; $pos -lt $End - 0.1; $pos += 40) {
                if ($isXWall) {
                    Add-Part $Color $pos $Y $protrude "3023.dat" $perpRot
                } else {
                    Add-Part $Color $protrude $Y $pos "3023.dat" $perpRot
                }
            }
        }
        "Corbel" {
            # Inverted slopes protruding from wall
            $slopeRot = $wi.Rot
            for ($pos = $Start + 10; $pos -lt $End - 0.1; $pos += 40) {
                if ($isXWall) {
                    Add-Part $Color $pos $Y $protrude "3665.dat" $slopeRot
                } else {
                    Add-Part $Color $protrude $Y $pos "3665.dat" $slopeRot
                }
            }
        }
        "Plain" {
            if ($isXWall) {
                Fill-PlatesX $Color $Start $End $Y $protrude
            } else {
                Fill-PlatesZ $Color $Start $End $Y $protrude
            }
        }
    }
}

function Add-FloorBand {
    # Decorative horizontal band between floors (plate + optional dentil/trim)
    param(
        [int]$Color,
        [double]$Start, [double]$End,
        [double]$Y,
        [double]$WallPos,
        [string]$Wall = "Front",
        [string]$Style = "Plain"    # Plain, Dentil
    )

    $wi = Get-WallInfo $Wall
    $isXWall = ($wi.Axis -eq "X")

    # Base plate at wall face
    if ($isXWall) {
        Fill-PlatesX $Color $Start $End $Y $WallPos
    } else {
        Fill-PlatesZ $Color $Start $End $Y $WallPos
    }

    # Add trim below the plate
    if ($Style -eq "Dentil") {
        Add-CorniceBand $Color $Start $End ($Y + 8) $WallPos $Wall "Dentil"
    }
}

# ============================================================
# FLOOR PLATES
# ============================================================

function Add-FloorPlates {
    # Interior floor separation plates (does NOT extend to exterior walls)
    param(
        [int]$Color,
        [double]$XMin, [double]$XMax,
        [double]$ZMin, [double]$ZMax,
        [double]$Y,
        [int]$Layers = 2
    )

    for ($layer = 0; $layer -lt $Layers; $layer++) {
        $plateY = $Y - ($layer * 8)
        for ($z = $ZMin; $z -le $ZMax; $z += 20) {
            Fill-PlatesX $Color $XMin $XMax $plateY $z
        }
    }
}

# ============================================================
# PARAPET
# ============================================================

function Add-Parapet {
    # Parapet wall around roof perimeter
    param(
        [int]$Color,
        [double]$XMin, [double]$XMax,
        [double]$ZMin, [double]$ZMax,
        [double]$Y,                    # Y of first parapet row
        [int]$Rows = 2,
        [bool]$CapTiles = $true,
        [string]$Sides = "FBLR"        # Which sides: F=front, B=back, L=left, R=right
    )

    for ($row = 0; $row -lt $Rows; $row++) {
        $rowY = $Y - ($row * 24)
        if ($Sides -match "F") { Fill-BricksX $Color $XMin $XMax $rowY $ZMin }
        if ($Sides -match "B") { Fill-BricksX $Color $XMin $XMax $rowY $ZMax }
        if ($Sides -match "L") { Fill-BricksZ $Color $ZMin $ZMax $rowY $XMin }
        if ($Sides -match "R") { Fill-BricksZ $Color $ZMin $ZMax $rowY $XMax }
    }

    if ($CapTiles) {
        $capY = $Y - ($Rows * 24) + 24 - 8   # On top of last row
        if ($Sides -match "F") { Fill-TilesX $Color $XMin $XMax $capY $ZMin }
        if ($Sides -match "B") { Fill-TilesX $Color $XMin $XMax $capY $ZMax }
        if ($Sides -match "L") { Fill-TilesZ $Color $ZMin $ZMax $capY $XMin }
        if ($Sides -match "R") { Fill-TilesZ $Color $ZMin $ZMax $capY $XMax }
    }
}

# ============================================================
# STYLE TEMPLATES
# ============================================================

function Get-BuildingStyle {
    param([string]$StyleName)

    switch ($StyleName) {
        "Georgian" {
            return @{
                Name           = "Georgian"
                RowsPerFloor   = 10
                WindowRecess   = $true
                WindowSill     = $true
                WindowHeader   = $true
                CorniceStyle   = "Dentil"
                ParapetRows    = 2
                ParapetCap     = $true
                FloorBand      = $true
                FloorBandStyle = "Plain"
            }
        }
        "Victorian" {
            return @{
                Name           = "Victorian"
                RowsPerFloor   = 12
                WindowRecess   = $true
                WindowSill     = $true
                WindowHeader   = $true
                CorniceStyle   = "Corbel"
                ParapetRows    = 3
                ParapetCap     = $true
                FloorBand      = $true
                FloorBandStyle = "Dentil"
            }
        }
        "Simple" {
            return @{
                Name           = "Simple"
                RowsPerFloor   = 8
                WindowRecess   = $false
                WindowSill     = $false
                WindowHeader   = $false
                CorniceStyle   = "None"
                ParapetRows    = 1
                ParapetCap     = $false
                FloorBand      = $false
                FloorBandStyle = "None"
            }
        }
        default {
            Write-Warning "Unknown style '$StyleName', defaulting to Georgian"
            return Get-BuildingStyle "Georgian"
        }
    }
}

# ============================================================
# EXPORTS
# ============================================================

Export-ModuleMember -Function @(
    # Core
    'Add-LDrawLine', 'Add-Part', 'Add-Step', 'Add-Comment',
    'Start-Model', 'Add-SubmodelRef', 'Start-Submodel', 'End-Submodel', 'End-Model',
    'Save-LDrawFile',
    # Fill
    'Fill-Span', 'Fill-BricksX', 'Fill-BricksZ',
    'Fill-PlatesX', 'Fill-PlatesZ', 'Fill-TilesX', 'Fill-TilesZ',
    # Walls
    'Add-WallRowX', 'Add-WallRowZ', 'Add-WallX', 'Add-WallZ',
    # Assemblies
    'Add-WindowBay', 'Add-DoorSurround',
    'Add-CorniceBand', 'Add-FloorBand',
    'Add-FloorPlates', 'Add-Parapet',
    # Styles
    'Get-BuildingStyle', 'Get-WallInfo'
) -Variable @(
    'R0', 'R90', 'R180', 'R270',
    'BrickSizes', 'PlateSizes', 'TileSizes'
)
