# Ice Cream Shop Fix Plan 3

## Problem: Window Glass Appears Partially Empty

In every window on the building, the trans-clear glass (60603.dat) appears to only
fill the upper portion of the frame (60594.dat). The bottom of each window looks
dark/blocked. This is visible on all 6 windows (2 ground floor right, 1 first floor
left, 3 first floor right).

## Root Cause

The module's `Add-WindowBay` adds **sill plates** (3710.dat, 1x4 plate) at the bottom
of every window when `-Sill $true`. The sill plate is placed at Y+72 (the bottom edge
of the 72 LDU tall window frame).

**The problem:** 3710.dat is a PLATE (with studs). The studs extend 4 LDU upward from
the plate surface — directly INTO the window frame opening. These colored studs
(in the wall color) are visible through the trans-clear glass, making the bottom of
every window appear blocked or dark.

The v4 reference script's `PlaceWindow` function places ONLY frame + glass (no sill,
no header). That's why v4 windows render cleanly.

```
v4 PlaceWindow:     frame + glass (2 parts)
Module Add-WindowBay: frame + glass + sill plate + header plate (4 parts)
```

## Fix A: Remove Sill Plates from All Windows

Change all `Add-WindowBay` calls from `-Sill $true` to `-Sill $false`.

**Ground floor right section (lines 145-148):**
```powershell
# BEFORE:
Add-WindowBay ... -Sill $true -Header $true
# AFTER:
Add-WindowBay ... -Sill $false -Header $false
```

**First floor left section (line 226-227):**
```powershell
# BEFORE:
Add-WindowBay ... -Sill $true -Header $false
# AFTER:
Add-WindowBay ... -Sill $false -Header $false
```

**First floor right section (lines 255-260):**
```powershell
# BEFORE:
Add-WindowBay ... -Sill $true -Header $true
# AFTER:
Add-WindowBay ... -Sill $false -Header $false
```

This removes the interfering plates and matches v4's clean window approach.

## Fix B: Also Remove Header from Right Section Door

The `Add-DoorSurround` at line 140-141 has `-Header $true`. The header plate above
the door adds a colored plate that v4 doesn't use. Remove it for consistency.

```powershell
# BEFORE:
Add-DoorSurround ... -Header $true
# AFTER:
Add-DoorSurround ... -Header $false
```

## Impact

- Removes 12 extra plate parts (6 sills + 5 headers + 1 door header)
- All windows will render with clean trans-clear glass filling the full frame
- Matches v4's visual quality for window clarity

## Future Consideration: Module Fix

The module's `Add-WindowBay` could be improved to use TILES (no studs) instead of
PLATES for sills, which would prevent the stud intrusion. But that's a module-level
change that affects all scripts. For now, the per-script `-Sill $false` fix is safer.
