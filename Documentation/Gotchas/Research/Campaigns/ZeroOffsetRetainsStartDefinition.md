# A zero offset retains the explicit extrusion start definition

## Expectation

An OffsetStart definition with a zero scalar can appear geometrically equivalent to a ProfilePlane start.

## Actual behavior

Fusion `2706.1.17` preserves the explicit offset-start type even at zero.
The existing native inspector reports `start.kind = Offset`, stored code 1 and a bound `ProfileOffset` parameter with value zero.
The campaign's frozen reader `91a73de348894a5791a51b977cd6fe0fe677a617` requires `DcExtrudeFeature.profileLocaltionType` zero and rejects these explicit OffsetStart controls.
The scalar value alone does not replace the start-definition identity.

## Workaround

Keep start kind, scalar and parameter ownership separate.
Preserve the campaign's historical refusals and partial research receipts. The subsequent [bounded SDK/CLI reader](../../../Changes/Fusion/Readers/FusionOffsetStartReader.md) admits its qualified identity-XY, single-circle, untapered two-sided NewBody sources while retaining the signed offset parameter and read-only publication. Other source envelopes keep their existing refusal.
Do not erase the native type or call a known policy guard missing wire grammar.
The [offset-start campaign](../../../../re/Fusion/OffsetStart20261127/README.md) retains zero, positive, negative and zero-crossing controls.
