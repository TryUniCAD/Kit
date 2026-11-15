# Drawing view geometry is not in the keyword streams

## Expectation

A `.SLDDRW` archive that contains `Contents/Definition`,
`Contents/DisplayLists`, and `Contents/VBLists` can be decoded into view
positions, projection directions, outlines, and annotations.

## Actual behavior

The recovered `swXmlContents/KeyWords` stream contains only a view name and the
referenced model path. The sheet-format property contains only name, offset,
width, height, and scale. View centres are recoverable from
`Contents/DisplayLists` as described in
[the position-record gotcha](SolidworksDrawingPositionRecords.md), but projected
edges, hidden-line state, dimensions, annotations, and projection direction are
not decoded.

A reader that reports outlines or annotation geometry by parsing the remaining
binary streams would be guessing.

## Workaround

Use `ReadDrawing` for document, sheet, scale, view-name, model-path, reference,
and note metadata. Requesting `IncludeGeometry=True` raises `SldprtFormatError`. Treat view geometry as unavailable and do not infer it from
the referenced part's B-rep, because the drawing carries its own projection and
hidden-line state.

## Evidence

`re/solidworks/examples/Drawings/standard.SLDDRW` has four views authored at
known positions by `re/tooling/harness/AuthorDrawings.vbs`, and
`swXmlContents/KeyWords` still lists only the view names and model paths.
`tests/convert/solidworks/drawing/SolidworksDrawingTests.py` asserts that
metadata and deliberately does not assert a view position.
