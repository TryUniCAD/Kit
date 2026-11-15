# Drawing view positions are duplicated display-list records

## Expectation

A single display-list record per view carries the sheet position, so one scan
yields one position per view.

## Actual behavior

`Contents/DisplayLists` contains two records per view. They are identical
little-endian double pairs 384 bytes apart. A four-view drawing therefore holds
eight matching pairs, and a naive scan reports twice as many views as exist.

The pair is followed by a zero Z value and a scale value. The primary record
carries `1.0` and the twin carries the view scale, so a 3:1 view stores `1.0`
and `3.0` rather than two equal values. The view outline
starts 37 bytes after the primary pair as four doubles: minimum X, minimum Y,
maximum X, and maximum Y. The referenced model bounds start 135 bytes after the
same pair as nine doubles: centre XYZ, maximum XYZ, then minimum XYZ. Interpreting the record as a plain 4x4 matrix or
assuming 8-byte alignment fails because some pairs start at odd byte offsets.

## Workaround

Scan every byte for a finite pair whose Z is zero and whose following value is a
plausible positive scale. Accept a pair only when an identical pair occurs exactly 384 bytes later,
then consume both records and emit one position with its sheet outline and model
bounds. Do not collapse
equal coordinates from different pairs, because distinct views can share a
centre. Do not impose a one metre bound: a valid view centre can sit outside the
reported sheet rectangle. Bind the resulting positions to views through
`SW-Config-Model-View-Sheet-List`, not through `KeyWords` order. Require the
position count to equal the view-list count; otherwise raise `SldprtFormatError`
instead of guessing.

## Evidence

All five tracked drawings yield exactly one position per view after collapsing
consecutive duplicates, and each position equals the location passed to
`CreateDrawViewFromModelView3` or `CreateUnfoldedViewAt3` in
`re/tooling/harness/AuthorDrawings.vbs`, `AuthorMultiSheet.vbs`, and
`AuthorProjected.vbs`.

`tests/convert/solidworks/drawing/SolidworksDrawingTests.py::TestPos` asserts
the recovered positions and `TestPosNo` requires a mismatch to fail.
