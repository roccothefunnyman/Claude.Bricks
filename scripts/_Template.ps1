# _Template.ps1
# PowerShell template for generating modular LEGO buildings in LDraw format.
# Copy this file and customize for each new building.
#
# Reference patterns from: Detective's Office (10246), Pet Shop (10218)

param(
    [string]$OutputFile = "output/BuildingName.ldr",
    [string]$ModelName = "Building Name"
)

$sb = [System.Text.StringBuilder]::new()
function L([string]$t) { [void]$sb.AppendLine($t) }

# ============================================================
# ROTATION MATRICES
# ============================================================
$R0   = "1 0 0 0 1 0 0 0 1"       # default (along X-axis)
$R90  = "0 0 -1 0 1 0 1 0 0"      # 90 CW (along Z-axis)
$R180 = "-1 0 0 0 1 0 0 0 -1"     # 180 deg
$R270 = "0 0 1 0 1 0 -1 0 0"      # 270 CW

# Slope rotations
$SlopeFront = $R0                   # slope faces forward (default)
$SlopeBack  = $R180                 # slope faces backward (inverted)
$SlopeLeft  = $R270                 # slope faces left
$SlopeRight = $R90                  # slope faces right

# Dentil/masonry perpendicular rotation (protrudes from wall)
$RPerp = "0 0 1 0 1 0 -1 0 0"

# ============================================================
# CORE HELPER FUNCTIONS
# ============================================================

# Place a single part
function B([int]$c,[double]$x,[double]$y,[double]$z,[string]$p,[string]$r=$R0) {
    L("1 $c $([math]::Round($x,1)) $([math]::Round($y,1)) $([math]::Round($z,1)) $r $p")
}

# Fill a span along X with optimal bricks (front/back walls)
function FillX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[int]$offset=0) {
    $sizes = @(
        @{w=160;p="3008.dat"},  # 1x8
        @{w=120;p="3009.dat"},  # 1x6
        @{w=80; p="3010.dat"},  # 1x4
        @{w=60; p="3622.dat"},  # 1x3
        @{w=40; p="3004.dat"},  # 1x2
        @{w=20; p="3005.dat"}   # 1x1
    )
    $x = $xMin + $offset
    # Place offset filler if needed
    if ($offset -gt 0 -and $offset -lt 160) {
        foreach ($s in $sizes) {
            if ($s.w -le $offset + 0.1) {
                B $c ($xMin + $s.w/2) $y $z $s.p $R0
                break
            }
        }
    }
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) {
                B $c ($x + $s.w/2) $y $z $s.p $R0
                $x += $s.w
                break
            }
        }
    }
}

# Fill a span along Z with optimal bricks (side walls)
function FillZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x,[int]$offset=0) {
    $sizes = @(
        @{w=160;p="3008.dat"},
        @{w=120;p="3009.dat"},
        @{w=80; p="3010.dat"},
        @{w=60; p="3622.dat"},
        @{w=40; p="3004.dat"},
        @{w=20; p="3005.dat"}
    )
    $z = $zMin + $offset
    if ($offset -gt 0 -and $offset -lt 160) {
        foreach ($s in $sizes) {
            if ($s.w -le $offset + 0.1) {
                B $c $x $y ($zMin + $s.w/2) $s.p $R90
                break
            }
        }
    }
    while ($z -lt $zMax - 0.1) {
        $rem = $zMax - $z
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) {
                B $c $x $y ($z + $s.w/2) $s.p $R90
                $z += $s.w
                break
            }
        }
    }
}

# Fill along X with plates
function FillXPlate([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z) {
    $sizes = @(
        @{w=160;p="3460.dat"},  # 1x8 plate
        @{w=120;p="3666.dat"},  # 1x6 plate
        @{w=80; p="3710.dat"},  # 1x4 plate
        @{w=60; p="3623.dat"},  # 1x3 plate
        @{w=40; p="3023.dat"},  # 1x2 plate
        @{w=20; p="3024.dat"}   # 1x1 plate
    )
    $x = $xMin
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) {
                B $c ($x + $s.w/2) $y $z $s.p $R0
                $x += $s.w
                break
            }
        }
    }
}

# Fill along Z with plates
function FillZPlate([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x) {
    $sizes = @(
        @{w=160;p="3460.dat"},
        @{w=120;p="3666.dat"},
        @{w=80; p="3710.dat"},
        @{w=60; p="3623.dat"},
        @{w=40; p="3023.dat"},
        @{w=20; p="3024.dat"}
    )
    $z = $zMin
    while ($z -lt $zMax - 0.1) {
        $rem = $zMax - $z
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) {
                B $c $x $y ($z + $s.w/2) $s.p $R90
                $z += $s.w
                break
            }
        }
    }
}

# Fill along X with tiles (smooth, no studs)
function FillXTile([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z) {
    $sizes = @(
        @{w=160;p="4162.dat"},  # 1x8 tile
        @{w=120;p="6636.dat"},  # 1x6 tile
        @{w=80; p="2431.dat"},  # 1x4 tile
        @{w=60; p="63864.dat"}, # 1x3 tile
        @{w=40; p="3069b.dat"}, # 1x2 tile
        @{w=20; p="3070b.dat"}  # 1x1 tile
    )
    $x = $xMin
    while ($x -lt $xMax - 0.1) {
        $rem = $xMax - $x
        foreach ($s in $sizes) {
            if ($s.w -le $rem + 0.1) {
                B $c ($x + $s.w/2) $y $z $s.p $R0
                $x += $s.w
                break
            }
        }
    }
}

# Wall row along X with gaps for windows/doors
# $gaps = array of @{s=startX; e=endX}
function WallRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[array]$gaps=@(),[int]$offset=0) {
    $sorted = $gaps | Sort-Object { $_.s }
    $x = $xMin
    foreach ($g in $sorted) {
        if ($g.s -gt $x + 0.1) {
            FillX $c $x $g.s $y $z $offset
        }
        $x = $g.e
    }
    if ($x -lt $xMax - 0.1) {
        FillX $c $x $xMax $y $z $offset
    }
}

# Wall row along Z with gaps
function WallRowZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x,[array]$gaps=@(),[int]$offset=0) {
    $sorted = $gaps | Sort-Object { $_.s }
    $z = $zMin
    foreach ($g in $sorted) {
        if ($g.s -gt $z + 0.1) {
            FillZ $c $z $g.s $y $x $offset
        }
        $z = $g.e
    }
    if ($z -lt $zMax - 0.1) {
        FillZ $c $z $zMax $y $x $offset
    }
}

# ============================================================
# REFERENCE-CONFIRMED PATTERN HELPERS
# ============================================================

# Masonry row along X — uses 98283.dat (textured 1x2 brick)
# Alternate $rot between rows: $RPerp for odd, $R0 for even
function MasonryRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[string]$rot=$RPerp,[array]$gaps=@()) {
    $sorted = $gaps | Sort-Object { $_.s }
    $x = $xMin
    foreach ($g in $sorted) {
        while ($x + 40 -le $g.s + 0.1) {
            B $c ($x + 20) $y $z "98283.dat" $rot
            $x += 40
        }
        $x = $g.e
    }
    while ($x + 40 -le $xMax + 0.1) {
        B $c ($x + 20) $y $z "98283.dat" $rot
        $x += 40
    }
}

# Masonry row along Z
function MasonryRowZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x,[string]$rot=$R90,[array]$gaps=@()) {
    $sorted = $gaps | Sort-Object { $_.s }
    $z = $zMin
    foreach ($g in $sorted) {
        while ($z + 40 -le $g.s + 0.1) {
            B $c $x $y ($z + 20) "98283.dat" $rot
            $z += 40
        }
        $z = $g.e
    }
    while ($z + 40 -le $zMax + 0.1) {
        B $c $x $y ($z + 20) "98283.dat" $rot
        $z += 40
    }
}

# Dentil band along X — uses 3794b.dat tiles perpendicular to wall
# Spacing: every 40 LDU (2 studs). Each tile protrudes 1 stud from wall.
function DentilBandX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z) {
    for ($x = $xMin; $x -le $xMax; $x += 40) {
        B $c ($x + 20) $y $z "3794b.dat" $RPerp
    }
}

# Dentil band along Z
function DentilBandZ([int]$c,[double]$zMin,[double]$zMax,[double]$y,[double]$x) {
    for ($z = $zMin; $z -le $zMax; $z += 40) {
        B $c $x $y ($z + 20) "3794b.dat" $R90
    }
}

# Place window assembly (frame + glass) at position
function PlaceWindow([int]$frameColor,[double]$x,[double]$y,[double]$z,[string]$rot=$R0) {
    B $frameColor $x $y $z "60594.dat" $rot  # frame
    B 47 $x $y $z "60592.dat" $rot           # glass (Trans Clear)
}

# Place door assembly (frame + panel) at position
function PlaceDoor([int]$frameColor,[int]$doorColor,[double]$x,[double]$y,[double]$z,[string]$rot=$R0) {
    B $frameColor $x $y $z "60596.dat" $rot  # frame
    B $doorColor $x $y $z "57895.dat" $rot   # door panel
}

# Paired slope ridge — two slopes meeting at a peak
function SlopeRidge([int]$c,[double]$x,[double]$y,[double]$z,[string]$part="3040b.dat") {
    B $c $x $y $z $SlopeFront $part           # up-slope
    B $c $x $y ($z + 20) $SlopeBack $part     # down-slope (inverted)
}

# SNOT finial row along X — 4070.dat headlight bricks at regular intervals
function FinialRowX([int]$c,[double]$xMin,[double]$xMax,[double]$y,[double]$z,[int]$spacing=60) {
    for ($x = $xMin; $x -le $xMax; $x += $spacing) {
        B $c $x $y $z "4070.dat" $R0
    }
}

# ============================================================
# COLORS (customize per building)
# ============================================================
$Primary   = 28   # Dark Tan (Medium Nougat fallback)
$Secondary = 378  # Sand Green
$Accent    = 72   # Dark Bluish Gray
$Trim      = 15   # White
$Roof      = 72   # Dark Bluish Gray
$Window    = 47   # Trans Clear
$Door      = 70   # Reddish Brown
$MN        = 28   # Medium Nougat (use 28 as safe fallback for 150)

# ============================================================
# BUILDING DIMENSIONS (customize per building)
# ============================================================
$Width = 640      # 32 studs along X
$Depth = 320      # 16 studs along Z
$FZ = 10          # front wall Z (center of 1-stud wall)
$BZ = 310         # back wall Z
$LX = 10          # left wall X
$RX = 630         # right wall X
$yGround = 0      # ground level Y

# ============================================================
# FILE HEADER
# ============================================================
L "0 FILE $ModelName.ldr"
L "0 $ModelName"
L "0 Name: $ModelName"
L "0 Author: Claude"

# ============================================================
# BUILDING GENERATION
# (Replace everything below with actual building logic)
# ============================================================

# --- Foundation ---
L "0 STEP"
# FillXPlate, FillZPlate for base plates

# --- Ground floor walls (row by row, Y decreasing) ---
L "0 STEP"
# WallRowX / MasonryRowX for each row
# Skip gaps for windows/doors

# --- Ground floor windows & doors ---
L "0 STEP"
# PlaceWindow / PlaceDoor

# --- Floor separation ---
L "0 STEP"
# FillXPlate layers

# --- Upper floor walls ---
L "0 STEP"
# Same pattern as ground floor

# --- Upper floor windows ---
L "0 STEP"

# --- Cornice / dentil band ---
L "0 STEP"
# DentilBandX / DentilBandZ

# --- Roof ---
L "0 STEP"
# FillXPlate for platform
# SlopeRidge for peaked roof
# FinialRowX for decorative edge

# --- Details ---
L "0 STEP"
# Awnings, signs, flower boxes, lamps

# ============================================================
# OUTPUT
# ============================================================
$outPath = Join-Path $PSScriptRoot "..\$OutputFile"
$sb.ToString() | Out-File -FilePath $outPath -Encoding UTF8 -NoNewline
Write-Host "Generated: $outPath"
Write-Host "Lines: $($sb.ToString().Split("`n").Count)"
