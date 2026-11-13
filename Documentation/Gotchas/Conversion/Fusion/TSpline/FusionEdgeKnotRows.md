# TSM members can hold an edge knot block

## Expectation

A TSM member holds only the blocks that Kit-authored Form documents use.

## Actual behavior

`TsmCensus.py` lists the record order of all 253 TSM members in the corpus. Two members hold a `106ek` block. They are in `re/Fusion/LocalOracle/FormDocuments/Intervals/Plane4x4/Single.f3d` and `re/Fusion/LocalOracle/FormDocuments/Intervals/Box/Single.f3d`. Fusion wrote them after it rewrote an inconsistent edge interval. The reader raised `TSM record order or kind is unsupported: tol`.

The block has these rules:

- It has one row per `e` row, in edge order.
- Each row has one number. Its text equals the second field of its `e` row.
- It sits after the `100edges` and `100verts` crease blocks, after any `105` symmetry block, and before `50000grip`.
- Extension blocks are in ascending order of their numeric prefix.

## Workaround

Read a surface with the block as a `KnotSurface`, a `TsplineSurface` with `EdgeKnots`. Write the block back in its place. A surface without the block stays a plain `TsplineSurface`, so its model and its semantic hash do not change.

The two files then stop in the converted patch program. Fusion writes each patch word as a double in `%.17g` form. `ReadPatchRow` in `BrepCodec/Journal/Spline/Reading` parses each word as an integer.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#tsm-edge-knot-rows)
- [TSM census](../../../../../re/Fusion/Reconstruction/ReadGaps/TsmCensus.json)
- [Patch words](../../../../../re/Fusion/Reconstruction/ReadGaps/PatchWords.py)
