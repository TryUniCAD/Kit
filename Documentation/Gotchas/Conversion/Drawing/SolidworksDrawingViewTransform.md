# Only custom view orientations store a matrix

## Expectation

Every drawing view stores a 3x3 orientation matrix and translation that maps
model-space edges to sheet-space polylines.

## Actual behavior

The isometric view stores an exact matrix in `Contents/Definition` as nine
doubles followed by three translation doubles:

```
0.7071067811865464  -0.4082040559113551   0.5773815451999837
0.0                  0.8165408118857499   0.5772877120855426
-0.7071067811865488 -0.4082040559113538   0.5773815451999819
-0.009899494936611639 -0.003675959704210837 -0.0225163789329683
```

The front, top, and right views do not store their identity or axis-permutation
matrices as contiguous doubles or floats. Searching for the exact 9-double or
9-float identity, top, and right matrices finds nothing. Their orientation is
therefore not recoverable from the same record.

Testing all 24 proper axis-aligned frames against the model bounds and sheet
outline leaves four candidates per standard view. The candidates differ by
180-degree rotations or reflections, so the projected bounding box is identical
and the stream does not disambiguate them. The view name is generic and the
referenced model view name is not stored.

## Workaround

Recover sheet-space edges only for views whose matrix is present, and fail closed
for views without one. Do not infer a standard view orientation from the view
name, because the name is generic (`Drawing View1`) and the referenced model view
is not stored in the keyword stream.

## Evidence

The isometric matrix maps the recovered model edges to the typed C# API edges
with a maximum residual of `1.3e-16`. The front view maps by subtracting the
model centre `(0.0185,0.016,0.0045)`, but that transform is not stored as a
matrix. `standard.SLDDRW` has four views; only the isometric view exposes the
matrix record.
