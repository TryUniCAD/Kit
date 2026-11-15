# Sheet format entries appear as sheet elements

## Expectation

Every `Sheet` element under `swXmlContents/KeyWords` describes a drawing sheet.

## Actual behavior

A drawing authored with the default template has one extra `Sheet` element whose
`Type` attribute is `Sheet Format` instead of `Sheet`. A two-sheet drawing
therefore lists three `Sheet` elements:

```
<Sheet id="14" Name="Sheet2" Type="Sheet">...</Sheet>
<Sheet id="18" Name="Sheet Format1" Type="Sheet Format">...</Sheet>
<Sheet id="4" Name="Sheet1" Type="Sheet">...</Sheet>
```

`Sheet Format1` has no row in the `SW-All Sheet Format Data` property. A reader
that treats every `Sheet` element as a real sheet raises a missing-format error.

## Workaround

Filter `Sheet` elements to `Type="Sheet"`. Do not use the element order as the
sheet order either: the format entry is interleaved between the real sheets, and
the real sheets can be listed out of index order.

## Evidence

`re/solidworks/examples/Drawings/multisheet.SLDDRW` is a real two-sheet drawing
authored by `re/tooling/harness/AuthorMultiSheet.vbs`. The reader returns
`Sheet2` then `Sheet1` and ignores `Sheet Format1`.
`tests/convert/solidworks/drawing/SolidworksDrawingTests.py::TestMulti` covers
it.
