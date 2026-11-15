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
requested, `PositionX` and `PositionY` in metres plus `OutlineMinX`,
`OutlineMinY`, `OutlineMaxX`, `OutlineMaxY`, `ModelBounds`, and `ViewScale`.
`DrawingRef` carries `Name`
and `Description`. Note text is returned exactly, including leading or trailing
spaces.

`ReadDrawing(..., IncludePositions=True)` recovers view centres from
`Contents/DisplayLists`. The stream stores each centre as a little-endian double
pair followed by a zero Z value and a 1 or 2 record flag. Each view contributes
two records 384 bytes apart; the primary record carries a `1.0` marker and the
twin carries the view scale, so a custom view scale is recovered from the twin
rather than assumed to equal the sheet scale. The reader consumes each pair once
rather than collapsing equal coordinates, so two views that share a centre on
different sheets keep two positions. The vendor view outline follows the primary record
37 bytes later as four doubles: minimum X, minimum Y, maximum X, and maximum Y.
The cited model bounds follow 135 bytes after the primary pair as centre,
maximum, and minimum triples in metres; `ViewBounds` exposes them as `Center`,
`Maximum`, and `Minimum`. Invalid or truncated bounds raise `SldprtFormatError`. No one metre bound is applied, so a large sheet or an
off sheet centre is retained. The recovered positions are bound to views through the
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

`ReadDrawing(..., IncludeEdges=True)` recovers model-space view edges from
`Contents/VBLists`. Each view section is delimited by a UTF-16
`model@Drawing ViewN` string. The first count of at least two before the next
view name selects a block; edges start 20 bytes after that count and repeat every
204 bytes as six doubles: start XYZ and end XYZ. Every parsed view must have a
block, otherwise the read raises `SldprtFormatError`.

`ReadDrawing(..., IncludeSheetEdges=True)` recovers sheet-space view edges. It
implies `IncludePositions` and `IncludeEdges`, then reads the view orientation
records from `Contents/Definition`. Each record is a unit direction, a one-byte
flag, an optional nine-double row-major rotation, a three-double translation,
and a trailing `1.0`. The front view stores flag `0` and omits the identity
matrix; the top, right, and isometric views store flag `1` and a matrix. The
stored matrix is the sheet-to-model rotation, so the sheet position of a model
point is `view_centre + ViewScale * (R^T * (p - model_centre)).xy`. Records are kept
only when the translation equals the negated rotated model centre, and are bound
to views by the trailing integer of the view name, which is the creation index.
The reader requires one record per view and raises `SldprtFormatError`
otherwise. `DrawingView.Orientation` exposes the matrix and
`DrawingView.SheetEdges` exposes the projected segments.

`ReadDrawing(..., IncludeGeometry=True)` raises `SldprtFormatError`. View
centres and sheet-space edges are not a complete geometry path, so asking for
geometry still fails closed instead of returning a value that a caller could
mistake for a complete drawing. Request positions separately with
`IncludePositions=True` and sheet-space edges with `IncludeSheetEdges=True`.

`WriteDrawing(Source, Data)` rewrites the recovered view position and scale
records in a source drawing container and returns a new container. It writes the
`Contents/Definition` view record (`x`, `y`, `0.0`, scale, `1.0`) and the
`Contents/DisplayLists` primary and twin records. It requires the source view
count to equal `Data` view count, every view to carry `PositionX`, `PositionY`,
and `ViewScale`, and every value to be finite and in range; otherwise it raises
`SldprtFormatError`. It does not generate the document-level streams, does not
change the view orientation, and does not add or remove views.

## Limitations

- `open_document` and `write_document` still reject `.SLDDRW` at
  `src/convert/adapters/solidworks/container/Format.py`; `ReadDrawing` and
  `WriteDrawing` are explicit opt-in functions
- `WriteDrawing` is a view-record writer, not a from-scratch generator: it
  requires a source container and retains its document-level streams
- `WriteDrawing` does not change the view orientation, because the orientation
  is derived from the model view name (`*Front`, `*Top`, `*Right`,
  `*Isometric`) and rewriting that name invalidates the model reference
- view centres, sheet outline bounds, model bounds, model-space edges, view
  orientation, and sheet-space edges are recovered, but hidden-line state,
  dimensions, and annotations are not
- sheet-space edges are the visible model edges projected into the view frame;
  they are not the full display list, which also carries silhouettes and hidden
  lines
- edge recovery is fail-closed: `minimal.SLDDRW` and `large.SLDDRW` do not expose
  a complete per-view block and are rejected when edges are requested
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

`tests/convert/solidworks/drawing/SolidworksDrawingTests.py` reads seven real
drawings authored in SOLIDWORKS Design Premium 2026 SP5.2 and tracked under
`re/solidworks/examples/Drawings/`:

| Fixture             | Name    | Views | Scale |
| ------------------- | ------- | ----- | ----- |
| `standard.SLDDRW`   | `Draw1` | 4     | 2:1   |
| `minimal.SLDDRW`    | `Draw2` | 2     | 2:1   |
| `angled.SLDDRW`     | `Draw3` | 3     | 1:1   |
| `projected.SLDDRW`  | `Draw2` | 2     | 2:1   |
| `multisheet.SLDDRW` | `Draw1` | 1     | 2:1   |
| `large.SLDDRW`      | `Draw1` | 1     | 2:1   |
| `coincident.SLDDRW` | `Draw1` | 1     | 2:1   |

The first three use `Sheet1`, paper-size code `0`, and 0.2794 m by 0.2159 m.
`multisheet.SLDDRW` has `Sheet2` with paper code `12` and `Sheet1` with paper
code `0`; it also carries the template title-block notes. `projected.SLDDRW` was
authored by `re/tooling/harness/AuthorProjected.vbs` with a base view (`Type=7`)
and a projected view (`Type=4`); both carry the parent model path.
`large.SLDDRW` places a view at 1.10 m, outside the reported sheet rectangle, and
`coincident.SLDDRW` places the same centre on two sheets.

`TestOpen` checks the document name and path, `TestSheet` checks sheet geometry,
scale, view count, and referenced model, `TestText` checks the authored note and
references, and `TestNote` verifies that padded note whitespace survives.
`TestMulti` requires the `Sheet Format` pseudo-entry to be ignored and both real
sheets to decode; `TestProj` requires the base and projected views to decode.
`TestPos` requires every recovered `PositionX` and `PositionY` to equal the
authored location, including the 1.10 m center and the duplicated center across
sheets. `TestPosNo` rewrites the position doubles so the count no longer matches
the view list and requires `SldprtFormatError`. `TestFail` removes or corrupts
each required stream and requires `SldprtFormatError`; `TestGeom` requires the
geometry opt-in to fail; `TestWrite` confirms that the public document writer
still rejects every drawing.

The fixtures are outputs of the real SOLIDWORKS API. The authoring macros are
`re/tooling/harness/AuthorDrawings.vbs`, `AuthorMultiSheet.vbs`,
`AuthorProjected.vbs`, `AuthorLargeSheet.vbs`, and `AuthorCoincident.vbs`; their
runs are recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md).
