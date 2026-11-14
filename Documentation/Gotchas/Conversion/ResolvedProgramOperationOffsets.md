# Resolved program operation offsets

## Expectation

A dynamic-field override can use any offset inside the target scalar's byte range. An eight-byte value contained in a range ending at 8451 would then appear to accept 8451 as its key.

## Actual behavior

`ReplayResolved` applies overrides only at exact operation-start offsets. An override at an interior byte is ignored without changing the captured default. In the triangle program, both sphere diameters are eight-byte doubles: the first starts at 8225 and the second starts at 8447. Using 8451 updated only the first diameter, leaving nonbaseline files with conflicting native bounds.

## Workaround

Derive override keys from the typed `KResolvedOps` records and their source ownership, not from the end of a documented byte span. The second `moFaceRefPlnData_c` diameter operation starts at 8447, and `BuildBounds` must override both 8225 and 8447.

Integration coverage must inspect both raw native doubles for a nonbaseline profile. Checking only the native decoder's first bounding-box result cannot detect a stale second copy.

See [the native triangle change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md), [the shift regression](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the shared replay encoder](../../../../src/convert/adapters/solidworks/programs/Common/FieldEncoder.py).
