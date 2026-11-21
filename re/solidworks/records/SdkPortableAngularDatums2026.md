# Portable hinge and angular datum history from SOLIDWORKS patterns

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121, takeover team. The normal strict reader now retains the finite hinge and the constrained plane in neutral feature definitions. The scope follows the [typed saved pattern](SdkWarmAngularPatternRead2026.md), the [cache-free joined pattern](SdkColdObliquePatternRead2026.md) and the [portable plane-axis definition](PortablePlaneIntersectionAxis2026.md).

The finite axis keeps two ordered direct support-plane picks, the same actual archive feature ID, and the stored endpoints converted to millimetres. Each selection carries provenance from the linked wrapper and resolves to the real Top or Right support. The angular plane records its actual Right-plane and axis constraint selections, as well as its independent driving D1. Both matched reference owners preserve their native feature dependencies.

A bound angle plane derives its current frame from the unchanged Right plane's local basis and live D1. Hinge coincidence through the origin implies zero independent offset. The neutral model includes this value as a derived length with provenance at the actual coincidence constraint. The model validates the evaluated plane, finite axis and ordered selections together. Its four new selection records replace their earlier approximation only when they belong to the affected owners.

Six independent normal path and stream pairs retain the exact previously compiled archive hashes and all prior measured model outputs. Their JSON round trips preserve both portable definitions. Four disclosed native saves retain the same original B-rep fingerprint and scoped pattern state. The overhanging case keeps its generic pattern while admitting the portable datums. The normal writer continues to refuse unsupported full native documents. [Combined receipt](../measurements/2026/SdkPortableAngularDatums01.json)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProveColdPatternRead.py \
  --output /absolute/path/to/ColdPatternDatums.json
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPortableAngularRead.py \
  --share /absolute/path/to/Oracle121Takeover \
  --cold /absolute/path/to/ColdPatternDatums.json \
  --output /absolute/path/to/SdkPortableAngularDatums01.json
```

No native application or protected file is used by this readback proof. The earlier independently locked native lifecycle remains the separate exact-build writer evidence. Remaining public writer work includes selected production composition and binding the owned annotation presentation.
