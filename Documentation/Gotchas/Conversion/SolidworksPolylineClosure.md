# Exact polyline closure

## Expectation

Two endpoints that differ by a negligible amount can safely be treated as the same point while serializing a polyline. The writer can then emit just the ordered line starts and recreate a closed loop.

## Actual behavior

`LineLoopPoints` previously used a tolerance when linking an edge's end to the next edge's start. A gap of 1e-13 mm therefore produced a three-edge wire that the writer accepted even though the original end coordinate was not retained. `EncodePolyMut` then serialized starts from an effectively repaired chain rather than the actual open chain.

This is not floating-point presentation normalization. It changes the source's geometry and can conceal a broken profile at the exact boundary the writer is expected to reject.

## Workaround

Require exact endpoint equality when linking serialized edges. The recovered three-line blind-pad scope accepts closed geometric profiles with three unique vertices and nonzero area, not approximately closed histories. A chain that declares a closed profile or is near-closed returns `None` before native encoding and raises `SldprtFormatError`, so even the default carrier-permitting write cannot silently close the gap or substitute a carrier. An unrelated three-edge profile with no declared closed profile and no near-closed line chain is not this family and keeps its existing generic fallback.

Public writer coverage perturbs one shared endpoint by 1e-13 mm and verifies both `HasVendorPartEncoding == False` and the write failure. Positive closed-wire and near-origin controls remain covered independently.

See [the native change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md) and [the integration coverage](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py).
