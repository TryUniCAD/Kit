# Drawing view geometry is not in the keyword streams

## Expectation

A `.SLDDRW` archive that contains `Contents/Definition`,
`Contents/DisplayLists`, and `Contents/VBLists` can be decoded into view
positions, projection directions, outlines, and annotations.

## Actual behavior

The recovered `swXmlContents/KeyWords` stream contains only a view name and the
referenced model path. The sheet-format property contains only name, offset,
width, height, and scale. The three geometry-bearing streams are binary
serializations whose grammar is not recovered, so a reader cannot derive view
placement or projected edges from them.

The SOLIDWORKS API exposes view position on `View.GetPosition()` at authoring
time, but that value is not present in the XML metadata streams. A reader that
reports positions by parsing the binary streams would be guessing.

## Workaround

Use `read_slddrw` for document, sheet, scale, view-name, model-path, reference,
and note metadata. Treat view geometry as unavailable and do not infer it from
the referenced part's B-rep, because the drawing carries its own projection and
hidden-line state.

## Evidence

`re/solidworks/examples/Drawings/standard.SLDDRW` has four views authored at
known positions by `re/tooling/harness/AuthorDrawings.vbs`, and
`swXmlContents/KeyWords` still lists only the view names and model paths.
`tests/convert/solidworks/drawing/SolidworksDrawingTests.py` asserts that
metadata and deliberately does not assert a view position.
