# Authored solids are oriented before Parasolid encoding

## Behaviour

`EncodeBrepModel` now orients every planar face of a model it writes so that the
face's outer loop winds against the face's surface normal, and it selects an
edge's first fin from the non-reversed coedge instead of the first coedge in
topology order.

Both rules matter only for models that were authored rather than decoded. A
decoded body already satisfies them, so re-encoding one is unchanged.

## Why it was needed

NX 2506 lists a body from an authored stream, reports `IsSolidBody` true, and
still measures `VOLUME 0.0`. Two separate causes were found by measurement:

- the loop winding of an authored prism is the opposite of the winding in every
  body NX itself saves, so the shell arrives inside out
- without `parasolid.first_fin`, the encoder started each edge's fin ring at an
  arbitrary coedge, and NX then bound one face instead of six (`8000` of
  `24000` for a `40 x 30 x 20` box)

## Verification

An authored `60 x 30 x 20` box built by `BuildPrism` from constants, spliced into
a part and opened in NX 2506:

```text
BODIES 1
FEATURES 1   BLOCK
VOLUME 36000.0
AREA 7199.999999999999
CENTROID [X=30.000000000000004,Y=15.000000000000002,Z=10.000000000000002]
MASS 0.28190304
```

The same path for `40 x 30 x 20` reports `VOLUME 23999.999999999996, AREA 5200.0`
and for `25 x 30 x 20` reports `VOLUME 15000.0, AREA 3699.9999999999995`, all
matching the analytic values. A decoded NX body re-encoded through the same
function still reports `VOLUME 23999.999999999996`.

`tests/convert/geometry/PrismTests.py::TestBoxWinding` checks the invariant at
the encode/decode boundary: every face of an encoded prism winds against its
plane normal, the input model is not mutated, and re-encoding the decoded stream
reproduces the same bytes.

## Limits

- Orientation is only computed for planar surfaces, which are the ones that
  carry a single normal. Curved faces keep the winding the caller supplied.
- The container, object-model sections and feature records still come from a
  retained native part. This change makes authored geometry measurable; it does
  not make an NX part writable without a source document.
