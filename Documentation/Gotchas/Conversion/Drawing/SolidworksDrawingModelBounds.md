# Model bounds sit after the view outline

## Expectation

The display-list record after a view centre contains only the sheet outline, so
the referenced model extents must be read from the part or assembly.

## Actual behavior

The primary display-list record carries both. The sheet outline starts 37 bytes
after the centre pair. The referenced model bounds start 135 bytes after the
same pair as nine doubles:

```
centreX, centreY, centreZ, maxX, maxY, maxZ, minX, minY, minZ
```

The values are in metres and match the referenced part B-rep exactly. For
`poly5a` they are `0.0185,0.016,0.0045`, `0.042,0.032,0.009`, and
`-0.005,0,0`.

## Workaround

Read the nine doubles at the fixed offset, require finite values and
`min <= centre <= max`, and expose them as `ViewBounds`. Do not derive them from
the sheet outline, which includes view padding and is not the model box.

## Evidence

`re/solidworks/examples/Drawings/standard.SLDDRW` returns the same nine doubles
for all four views. `TestModel` compares every recovered view against the part
reader's B-rep bounding box for `poly5a`, `poly5deep`, and `poly5b`.
