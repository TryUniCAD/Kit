# Strict Fusion reading does not authorize encoder reconstruction

## Expectation

A strict-read document carries `fusion.native_state` and can appear suitable for any Fusion reconstruction workflow.
The public writer can reconstruct the complete qualified typed state.

## Actual behavior

The bounded encoder creates a source-free cuboid from its semantic specification.
That operation has a narrower admission boundary than the public reader and unchanged-state writer.
It must prove that every input native field belongs to the supported constructor graph.
The public semantic comparison does not compare every container field and preview.
Using it alone could silently replace input data outside the bounded constructor profile.

The encoder therefore compares the complete typed native model before both unchanged reconstruction and a driving edit.
It permits only recognized generated UUID relationships and validated provenance differences.
A custom valid preview can pass strict SDK reading and still fail encoder admission.
The input remains valid for its existing qualified public contract.

The native `BodyIdentity.AuthoredMicros` field is a finite nonnegative float.
The encoder's `written_at` argument is a nonnegative integer count of Unix seconds.
An integer-only native provenance check rejected the encoder's own generated cuboid.
The boundary smoke exposed that rejection before publication.

## Workaround

Use a complete supported constructor graph for bounded encoder work.
Retain the entire typed native contract when persisting JSON.
Record and resolve an admission diagnostic before requesting broader reconstruction support.
Do not remove metadata, ignore previews, or relax the complete-state comparison.

See the [encoder change entry](../../../../Changes/Research/FusionEncoderRoundTrip.md) and its revision-bound verification record.
The [boundary smoke](../../../../../re/Fusion/EncoderRoundTrip/BoundarySmoke.py) covers the custom-preview and provenance cases.
