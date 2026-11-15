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

A sheet element is only accepted when its `Type` is `Sheet`; the default
template also emits a `Sheet Format` element with no format row, and treating it
as a sheet would fail a valid two-sheet drawing.

`DrawingData` exposes `Name`, `Sheets`, `References`, `Notes`, and `SourcePath`.
Each `DrawingSheet` carries `Name`, `PaperSize`, `ScaleNumerator`,
`ScaleDenominator`, `WidthMetres`, `HeightMetres`, and its `DrawingView`
records. Each view carries `Name`, `ModelPath`, `Description`, and, when
requested, `PositionX` and `PositionY` in metres. `DrawingRef` carries `Name`
and `Description`. Note text is returned exactly, including leading or trailing
spaces.

`ReadDrawing(..., IncludePositions=True)` recovers view centres from
`Contents/DisplayLists`. The stream stores each centre as a little-endian double
pair followed by a zero Z value and a 1 or 2 record flag. Each view contributes
two identical records 384 bytes apart, so consecutive duplicates are collapsed.
The recovered positions are bound to views through the
`SW-Config-Model-View-Sheet-List` property, not through `KeyWords` order, because
a multi-sheet drawing can list its sheets and views in a different order. The
reader requires the position count to equal the view-list count, every listed
view to exist, and every parsed view to be listed; otherwise it raises
`SldprtFormatError`.

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

`ReadDrawing(..., IncludeGeometry=True)` raises `SldprtFormatError`. View
centres are not a complete geometry path, so asking for geometry still fails
closed instead of returning a value that a caller could mistake for a complete
drawing. Request positions separately with `IncludePositions=True`.

## Limitations

- this is a metadata reader only; `open_document` and `write_document` still
  reject `.SLDDRW` at `src/convert/adapters/solidworks/container/Format.py`
- view centres are recovered, but projected outlines, hidden-line state,
  dimensions, annotations, and projection direction are not; `Contents/Definition`
  and `Contents/VBLists` remain largely unrecovered
- a missing or inconsistent stream raises `SldprtFormatError` instead of
  returning a partial drawing
- one sheet-format row is required per sheet name; an unmatched sheet fails
- the scale comes from the sheet-format row when both fields are positive,
  otherwise from the `KeyWords` scale elements
- `Notes` contains every `Note` element in `KeyWords`, which can include the
  template title-block text as well as authored notes
- sheet order follows the `KeyWords` element order, which is not guaranteed to
  match the sheet tab order
- view type (base, projected, section, detail) is an API value and is not in the
  keyword stream; every model view is decoded by name and model path only

## Verification

`tests/convert/solidworks/drawing/SolidworksDrawingTests.py` reads five real
drawings authored in SOLIDWORKS Design Premium 2026 SP5.2 and tracked under
`re/solidworks/examples/Drawings/`:

| Fixture           | Name    | Views | Scale |
| ----------------- | ------- | ----- | ----- |
| `standard.SLDDRW` | `Draw1` | 4     | 2:1   |
| `minimal.SLDDRW`  | `Draw2` | 2     | 2:1   |
| `angled.SLDDRW`   | `Draw3` | 3     | 1:1   |

The first three use `Sheet1`, paper-size code `0`, and 0.2794 m by 0.2159 m.
`multisheet.SLDDRW` has `Sheet2` with paper code `12` and `Sheet1` with paper
code `0`, each with one view and a `2:1` scale; it also carries the template
title-block notes. `TestMulti` requires that the `Sheet Format` pseudo-entry is
ignored and that both real sheets decode. `projected.SLDDRW` was authored by
`re/tooling/harness/AuthorProjected.vbs` with a base view (`Type=7`) and a
projected view (`Type=4`); both carry the parent model path, and `TestProj`
requires both to decode. `TestOpen`
checks the document name and path, `TestSheet` checks sheet geometry, scale, view
count, and referenced model, `TestText` checks the authored note and references,
and `TestNote` verifies that padded note whitespace survives. `TestFail` removes
or corrupts each required stream and requires `SldprtFormatError`; `TestGeom`
requires the geometry opt-in to fail; `TestWrite` confirms that the public
document writer still rejects every drawing.

The fixtures are outputs of the real SOLIDWORKS API. The authoring macro is
`re/tooling/harness/AuthorDrawings.vbs`; its run is recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md).
