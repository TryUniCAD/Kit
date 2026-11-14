# NX body length needs p0 to match the body

## Expectation

Changing a block dimension and its body should be independent of the value that
the file already stores, because the writer recomputes the geometry.

## Observed behavior

The writer scales the body from its measured length, so the stored `p0` glyph
must equal that measured length. When the two disagree the override is refused
instead of writing a part whose feature and body describe different sizes.

NX also keeps the body geometry, not a rebuild recipe: a part whose dimension is
edited without new body data loads with the old volume. See
[the expression value gotcha](NxExpressionValue.md).

## Workaround

Keep the dimension and the body in step: `nx.body_length` writes both. For a
part whose body is not a single solid block, edit the feature record and the
body separately.

## Evidence

`dim40.prt` (`40 x 30 x 20`, `p0 40`) written with `nx.body_length = 60`
reports in NX 2506:

```text
BODIES 1
FEATURES 1   BLOCK
EXPRESSION p0 60.0
VOLUME 36000.0
AREA 7200.0
MASS 0.28190304
```
