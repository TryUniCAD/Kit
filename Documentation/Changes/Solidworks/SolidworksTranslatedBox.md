# Translated standalone box primitives

## Behavior

A standalone FreeCAD `Part::Box` or `PartDesign::AdditiveBox` whose placement is a
pure XY translation now lowers to the exact rectangle-pad SOLIDWORKS program instead of
being rejected. The projection writes the translated rectangle corners into the recovered
sketch record and validates the source B-rep against the same translated corners, so the
emitted length, width, height, feature order, and body are unchanged.

Only the placement translation participates. Rotation, a nonzero Z translation, and a
nonidentity attachment offset still decline native encoding and the public writer falls
back to its normal carrier or usability error.

## Usage

The behavior is automatic through `write_document` for a FreeCAD-sourced document that
contains exactly one primitive box feature, three positive `Length`/`Width`/`Height`
parameters, one active `Default` configuration, and a matching eight-vertex B-rep:

```python
from convert import write_document

write_document(source_document, "TranslatedBox.SLDPRT", allow_carrier=False)
```

No option or donor stream is required.

## Limitations

- the placement must be a translation only; any rotation declines native encoding
- `Pz` must be zero because the recovered blind-pad program starts on the sketch plane
- `AttachmentOffset` must stay identity
- the B-rep must still be exactly one box: eight vertices, twelve edges, six faces,
  one region, and one body
- SOLIDWORKS acceptance of the translated variant has not been re-run in this session;
  the existing box family was previously measured in SOLIDWORKS and this change only
  moves the rectangle within the sketch plane

## Verification

`tests/convert/solidworks/core/SolidworksWriterTests.py` adds `TestFCBTrans`,
`TestFCBRotate`, and `TestFCBZShift`:

- `TestFCBTrans` writes a box translated by `(12.5, -7.25)` through the public writer
  with `allow_carrier=False`, requires vendor-loadable and application-usable output,
  and decodes the emitted rectangle bounds `(12.5, -7.25, 22.5, 2.75)`.
- `TestFCBRotate` uses a 90-degree quaternion and requires native preflight to return
  false plus `ApplicationUsabilityError` from the public writer.
- `TestFCBZShift` uses `Pz = 5` and requires the same rejection.

The test corpus is synthetic and corpus-independent, so it runs without FreeCAD,
SOLIDWORKS, or the absent `.rescratch` box fixtures.
