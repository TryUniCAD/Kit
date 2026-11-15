# Drawing view positions are duplicated display-list records

## Expectation

A single display-list record per view carries the sheet position, so one scan
yields one position per view.

## Actual behavior

`Contents/DisplayLists` contains two records per view. They are identical
little-endian double pairs 384 bytes apart. A four-view drawing therefore holds
eight matching pairs, and a naive scan reports twice as many views as exist.

The pair is followed by a zero Z value and a 1 or 2 flag. Interpreting the
record as a plain 4x4 matrix or assuming 8-byte alignment fails because some
pairs start at odd byte offsets.

## Workaround

Scan every byte for a pair whose X and Y lie inside the plausible sheet range,
whose Z is zero, and whose following flag is 1 or 2. Collapse only consecutive
duplicates, preserving repeated positions that belong to different views. Bind
the resulting positions to views through `SW-Config-Model-View-Sheet-List`, not
through `KeyWords` order. Require the position count to equal the view-list
count; otherwise raise `SldprtFormatError` instead of guessing.

## Evidence

All five tracked drawings yield exactly one position per view after collapsing
consecutive duplicates, and each position equals the location passed to
`CreateDrawViewFromModelView3` or `CreateUnfoldedViewAt3` in
`re/tooling/harness/AuthorDrawings.vbs`, `AuthorMultiSheet.vbs`, and
`AuthorProjected.vbs`.

`tests/convert/solidworks/drawing/SolidworksDrawingTests.py::TestPos` asserts
the recovered positions and `TestPosNo` requires a mismatch to fail.
