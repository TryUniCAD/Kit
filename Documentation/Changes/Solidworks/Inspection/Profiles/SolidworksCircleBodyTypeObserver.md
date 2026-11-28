# Use the native COM body type in the SOLIDWORKS circle observer

`InspectSdkCircleBodyTypes.py` observes actual solid type with
`IBody2.GetType`, and obtains vertex cardinality from
`IBody2.GetVertexCount`. The registered SOLIDWORKS 2026 SP05.2 wrapper
exposes both methods. The earlier observer stopped on the first original
reference because its assumed `IsSolidBody` method was unavailable. Both
controls passed, and the generated lanes never launched.

The corrected API on an independent disclosed cylinder reports three faces,
two closed circular edges and zero vertices. The topology check now
requires those exact counts and still compares every native topology value
across both lanes and all lifecycle stages.

Use the new runner with a frozen packet and `--packet-sha256`. The disclosed
probe exercises the complete observer using an independent generated circle.
The original comparison uses the exact pre-existing source, predictions and
generated files once the disclosed probe passes. Geometry, edit, tree,
topology and lifecycle predicates are retained. The observer repair alone
establishes no native or public writer qualification.

Original failure record
`bb42f6bbdcf07831cd73d4c548b0813cc8074c2fc7197c919fc0035b6469a2d4`.
Corrected runner
`eb20f005a371ead45cbd569d9574c9e871b5a145b37a32db01dfe318b01c9254`.

[Original circle method](../../../../../re/solidworks/records/SdkCircleOriginalHeldoutProtocol2026.md)

[Actual COM body type](../../../../Gotchas/Conversion/Solidworks/Oracle/Parts/BodyTypeUsesGetType.md)

[Closed circular edge topology](../../../../Gotchas/Conversion/Solidworks/Oracle/Parts/ClosedCircleEdgesHaveNoVertices.md)
