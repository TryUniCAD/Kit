# Drawing view orientation is a direction plus an optional matrix

## Expectation

Every drawing view stores a 3x3 orientation matrix and translation that maps
model-space edges to sheet-space polylines, so a reader can find the matrix by
searching for nine contiguous doubles.

## Actual behavior

The orientation record is variable length:

```
direction   3 doubles   unit view direction
flag        1 byte      0 = identity matrix omitted, 1 = matrix follows
matrix      9 doubles   row-major rotation, present only when flag is 1
translation 3 doubles   negated rotated model centre
scale       1 double    always 1.0
```

The front view stores `flag = 0` and no matrix, because its rotation is the
identity. The top, right, and isometric views store `flag = 1` and a matrix.
Searching for the exact identity matrix therefore finds nothing, and searching
for the top or right matrix as nine aligned doubles also finds nothing because
the record starts at an odd byte offset.

The stored matrix is the sheet-to-model rotation. The model-to-sheet rotation is
its transpose, so the sheet position of a model point is:

```
sheet = view_centre + scale * (R^T * (p - model_centre)).xy
```

The record translation is `-R^T * model_centre`, which is the discriminator that
separates view records from the other unit-vector records in the same stream.

## Workaround

Scan every byte for a unit direction, a 0 or 1 flag, an optional proper rotation,
a finite translation, and a trailing `1.0`. Keep only records whose translation
equals the negated rotated model centre. Bind the survivors to views by the
trailing integer of the view name, which is the creation index, because the
`KeyWords` order is not creation order. Require one record per view and fail
closed otherwise.

## Evidence

`re/tooling/harness/OracleOrient.cs` dumps `View.GetViewXform` for every view.
The recovered matrices match it for all four `standard.SLDDRW` views, and the
recovered sheet-space edges match the typed C# `View.GetPolylines5` edges for
`standard`, `angled`, `projected`, `multisheet`, and `coincident` with zero
residual after rounding to nine decimals.

`re/tooling/harness/AuthorOrient.vbs` authored one-view drawings for `*Front`,
`*Top`, `*Right`, and `*Isometric`; the front drawing is the only one without a
matrix record.
