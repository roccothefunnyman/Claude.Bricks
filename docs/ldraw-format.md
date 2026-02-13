# LDraw File Format Reference

Source: https://www.ldraw.org/article/218.html

## Coordinate System

- **Right-handed** with **-Y as up**
- X = left/right, Y = vertical (inverted), Z = depth
- 1 LDU = 0.4mm

## Line Types

### Type 0: Comment / Meta Command
```
0 // This is a comment
0 FILE modelname.ldr
0 Name: modelname.ldr
0 Author: Name
0 !LDRAW_ORG Model
0 STEP
0 NOFILE
```

### Type 1: Part Reference (the main one we use)
```
1 <color> <x> <y> <z> <a> <b> <c> <d> <e> <f> <g> <h> <i> <part.dat>
```

The 9 values form a 3x3 transformation matrix:
```
| a b c |     Transformation:
| d e f |     x' = a*x + b*y + c*z + px
| g h i |     y' = d*x + e*y + f*z + py
              z' = g*x + h*y + i*z + pz
```

### Types 2-5: Lines, Triangles, Quads, Optional Lines
Used inside .dat part files, not in building scripts.

## Rotation Matrices

| Name    | Matrix                               | Use                  |
|---------|--------------------------------------|----------------------|
| R0      | `1 0 0 0 1 0 0 0 1`                 | Identity (default)   |
| R90     | `0 0 -1 0 1 0 1 0 0`               | 90 deg CW around Y   |
| R180    | `-1 0 0 0 1 0 0 0 -1`              | 180 deg around Y     |
| R270    | `0 0 1 0 1 0 -1 0 0`               | 270 deg CW around Y  |

### Special Rotations
```
15 deg:   0.965926 0 0.258819 0 1 0 -0.258819 0 0.965926
30 deg:   0.866025 0 0.5 0 1 0 -0.5 0 0.866025
45 deg:   0.707107 0 0.707107 0 1 0 -0.707107 0 0.707107

Perpendicular (Z-running variant):
          0 0 1 0 1 0 -1 0 0
```

## File Structure

### Multi-Part Document (MPD)
```
0 FILE MainModel.ldr
0 MainModel
0 Name: MainModel.ldr
0 Author: Claude.Bricks
0 !LDRAW_ORG Model

1 16 0 0 0 1 0 0 0 1 0 0 0 1 submodel1.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 submodel2.ldr
0 NOFILE

0 FILE submodel1.ldr
0 submodel1
0 Name: submodel1.ldr
0 Author: Claude.Bricks
1 <color> <x> <y> <z> <matrix> <part.dat>
...
0 STEP
0 NOFILE
```

### Rules
- UTF-8 encoding
- Submodels referenced at origin with identity rotation (convention)
- Each submodel uses absolute coordinates
- Color 16 = inherit from parent reference line
- `0 STEP` marks build step boundaries

## Color Reference

### Standard Colors
```
Code  Color                Code  Color
----  -----                ----  -----
0     Black                14    Yellow
1     Blue                 15    White
2     Green                19    Tan
4     Red                  28    Dark Tan
5     Pink                 47    Trans Clear
6     Brown                70    Reddish Brown
9     Light Blue           71    Light Bluish Gray
10    Bright Green         72    Dark Bluish Gray
                           212   Bright Light Blue
                           378   Sand Green
                           484   Dark Orange
```

### Special Colors
- **16**: Main color (inherits from reference line)
- **24**: Complement color (for edges)
