# A zero offset retains the explicit extrusion start definition

## Expectation

An OffsetStart definition with a zero scalar can appear geometrically equivalent to a ProfilePlane start.

## Actual behavior

Fusion `2706.1.17` preserves the explicit offset-start type even at zero.
The existing native inspector reports `start.kind = Offset`, stored code 1 and a bound `ProfileOffset` parameter with value zero.
The public strict policy requires `DcExtrudeFeature.profileLocaltionType` zero and rejects these explicit OffsetStart controls.
The scalar value alone does not replace the start-definition identity.

## Workaround

Keep start kind, scalar and parameter ownership separate.
Retain the strict refusal and use explicit partial mode for research inspection.
Do not erase the native type or call a known policy guard missing wire grammar.
The [offset-start campaign](../../../../re/Fusion/OffsetStart20261127/README.md) retains zero, positive, negative and zero-crossing controls.
