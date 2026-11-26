# Fusion encoder lengths cross the native centimetre boundary

## Expectation

An extrusion set to 5.3 mm can appear as exactly 5.3 mm in the strict SDK projection.

## Actual behavior

The Fusion archive stores the driving value as 0.53 cm and the expression as `5.3 mm`.
The strict projection converts the value to the adjacent double `5.300000000000001` mm.
Reusing that projected value as an authored literal changes the encoded expression and record positions.
An exact comparison to the requested neutral float also used to reject the newly generated archive.

## Workaround

Before reconstructing, verify that each original constructor expression encodes the exact stored centimetre value.
Preserve the validated expression when rebuilding the typed candidate.
For readback, compute the expected dimensions with the same millimetre-to-centimetre conversion as the SDK.
Treat two values as a no-op if they encode the same centimetre value.
Reject expressions that disagree with the stored value.

See the [Fusion encoder change entry](../../../../Changes/Research/Encoder/FusionEncoderRoundTrip.md) and its boundary smoke.
