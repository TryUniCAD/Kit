# SOLIDWORKS drawing reader

## Behavior

`convert.adapters.solidworks.drawing.read_slddrw` reads a real `.SLDDRW`
container and returns a frozen `DrawingData` value.

The reader uses two streams:

- `swXmlContents/KeyWords` supplies the document name, sheet names, paper-size
  description, scale fields, view names with model paths, references, and notes
- `docProps/ISolidWorksInformation.xml` supplies the `SW-All Sheet Format Data`
  row for each sheet, which gives the paper width and height in metres plus the
  sheet scale

`DrawingData` exposes `name`, `sheets`, `references`, `notes`, and
`source_path`. Each `DrawingSheet` carries `name`, `paper_size`,
`scale_numerator`, `scale_denominator`, `width_m`, `height_m`, and its
`DrawingView` records. Each view carries the view name, the referenced model
path, and the description. `DrawingRef` carries the reference name and
description.

The reader accepts a file path, a `Path`, or raw container bytes.

## Usage

```python
from convert.adapters.solidworks.drawing import read_slddrw

drawing = read_slddrw("standard.SLDDRW")
sheet = drawing.sheets[0]
print(drawing.name, sheet.name, sheet.scale_numerator, sheet.scale_denominator)
print([view.model_path for view in sheet.views])
```

## Limitations

- this is a reader only; `open_document` and `write_document` still reject
  `.SLDDRW` at `src/convert/adapters/solidworks/container/Format.py:208`
- geometry is not decoded: `Contents/Definition`, `Contents/DisplayLists`, and
  `Contents/VBLists` remain unrecovered, so view positions, projection
  direction, outlines, dimensions, and annotations are not exposed
- the recovered fields are metadata from `KeyWords` and the sheet-format
  property; a missing or inconsistent stream raises `SldprtFormatError` instead
  of returning a partial drawing
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
`TestFail` removes or corrupts each required stream and requires
`SldprtFormatError`, and `TestWrite` confirms that the public document writer
still rejects every drawing.

The fixtures are outputs of the real SOLIDWORKS API. The authoring macro is
`re/tooling/harness/AuthorDrawings.vbs`; its run is recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md).
