# Locate SOLIDWORKS sketch dimension and ladder geometry fields

A new research page,
[Sketch dimension fields](../../../../re/solidworks/SketchDimensionFields.md),
records where the rectangle sketch width and height and the blind boss depth are
stored in the committed SOLIDWORKS sample families. It is discovery evidence for
discovery-loop item 5 of the
reader and writer plan on
[PR #296](https://github.com/TryUniCAD/Kit/pull/296)
(`Documentation/Maintenance/SolidworksReaderWriterPlan.md`); it
does not change reader or writer behaviour.

`re/automation/FieldSearch.py` was run over each family's `control-before`,
`variation` and `control-after` grid with the values from `GroundTruth.json` and
`PairSpecs.json`, with no AI options and no edits to the search tools. The body
searched is the named archive stream taken through the repository's own
`SldprtArchive` container reader.

The page records these findings:

- The ladder rectangles are authored unconstrained
  (`SketchManager.CreateCornerRectangle` with no `AddDimension`), so they carry
  no sketch driving-dimension record. Their width and height exist as sketch
  point coordinates, a little-endian binary64 length in metres at
  `Contents/Config-0-ResolvedFeatures`, at `marker + 66` (x) and `marker + 74`
  (y). The only authored dimension is the extrusion `D1`, an f64 metre value at
  the distance-dimension record's public reader `native_offset`.
- The committed P04 paired captures do author `width_mm`/`height_mm` distance
  dimensions; their value fields are f64 metres at the `RectangleSketch`
  dimension record `native_offset` in `Contents/Config-0`.
- Absolute stream offsets vary with archive layout. The recorded field
  definition is record-relative, and the page lists the absolute offsets that
  `FieldSearch.py` reported on the discovery files beside it.

Limitations: no angular sketch dimension exists in these families, so angles
remain unlocated; the page states the dimension-authoring capture still needed
to locate a real sketch driving-dimension record for both length and angle
dimensions.

Verification evidence: the record-relative rule found on three files satisfies
all 48 `variation` files in the two ladder directories (45 held out), and the P04
rule found on 7 same-layout edit captures satisfies all 11 P04 captures (4 held
out). Exact commands, their observed output,
and the reader attribution output are reproduced on the page.
