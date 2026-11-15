# SOLIDWORKS drawing reader

## Behavior

`convert.adapters.solidworks.drawing.ReadDrawing` reads sheet metadata from a
real `.SLDDRW` container and returns a frozen `DrawingData` value.

The reader uses two streams:

- `swXmlContents/KeyWords` supplies the document name, sheet names, paper-size
  description, scale fields, view names with model paths, references, and notes
- `docProps/ISolidWorksInformation.xml` supplies the `SW-All Sheet Format Data`
  row for each sheet, which gives the paper width and height in metres plus the
  sheet scale

`DrawingData` exposes `Name`, `Sheets`, `References`, `Notes`, and `SourcePath`.
Each `DrawingSheet` carries `Name`, `PaperSize`, `ScaleNumerator`,
`ScaleDenominator`, `WidthMetres`, `HeightMetres`, and its `DrawingView`
records. Each view carries `Name`, `ModelPath`, and `Description`. `DrawingRef`
carries `Name` and `Description`. Note text is returned exactly, including
leading or trailing spaces.

The reader accepts a file path, a `Path`, or raw container bytes. It is an
explicit opt-in module: it is not registered as a conversion adapter and it is
not reachable through `open_document`.

## Usage

```python
from convert.adapters.solidworks.drawing import ReadDrawing

drawing = ReadDrawing("standard.SLDDRW")
sheet = drawing.Sheets[0]
print(drawing.Name, sheet.Name, sheet.ScaleNumerator, sheet.ScaleDenominator)
print([view.ModelPath for view in sheet.Views])
```

`ReadDrawing(..., IncludeGeometry=True)` raises `SldprtFormatError`. The geometry
path is not implemented, so asking for it fails closed instead of returning a
metadata-only value that a caller could mistake for a complete drawing.

## Limitations

- this is a metadata reader only; `open_document` and `write_document` still
  reject `.SLDDRW` at `src/convert/adapters/solidworks/container/Format.py`
- geometry is not decoded: `Contents/Definition`, `Contents/DisplayLists`, and
  `Contents/VBLists` remain unrecovered, so view positions, projection
  direction, outlines, dimensions, and annotations are not exposed
- a missing or inconsistent stream raises `SldprtFormatError` instead of
  returning a partial drawing
- one sheet-format row is required per sheet name; an unmatched sheet fails
- the scale comes from the sheet-format row when both fields are positive,
  otherwise from the `KeyWords` scale elements

## Verification

`tests/convert/solidworks/drawing/SolidworksDrawingTests.py` reads three real
drawings authored in SOLIDWORKS Design Premium 2026 SP5.2 and tracked under
`re/solidworks/examples/Drawings/`:

| Fixture           | Name    | Views | Scale |
| ----------------- | ------- | ----- | ----- |
| `standard.SLDDRW` | `Draw1` | 4     | 2:1   |
| `minimal.SLDDRW`  | `Draw2` | 2     | 2:1   |
| `angled.SLDDRW`   | `Draw3` | 3     | 1:1   |

All three use `Sheet1`, paper-size code `0`, and 0.2794 m by 0.2159 m. `TestOpen`
checks the document name and path, `TestSheet` checks sheet geometry, scale, view
count, and referenced model, `TestText` checks the authored note and references,
and `TestNote` verifies that padded note whitespace survives. `TestFail` removes
or corrupts each required stream and requires `SldprtFormatError`; `TestGeom`
requires the geometry opt-in to fail; `TestWrite` confirms that the public
document writer still rejects every drawing.

The fixtures are outputs of the real SOLIDWORKS API. The authoring macro is
`re/tooling/harness/AuthorDrawings.vbs`; its run is recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md).
