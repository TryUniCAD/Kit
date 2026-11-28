# Portable plane-intersection axis

Task `B04-SW2026-LOCAL-LINEAR-PATTERN` under PR #121. The [authored oblique pattern projection](LocalLinearPatternNeutralInput2026.md) needed a directed finite reference axis bound to two owned planes. The Kit feature model now records those four fields with the existing `PlaneIntersectionAxis` wire shape. The SDK exposes `PlaneAxis` and registers it for ordinary `CadDocument` JSON and mapping reads.

The [neutral definition](../../../src/interchange/Features/FeaturePlaneAxis.py) validates finite distinct endpoints and a representable segment span. [Document validation](../../../src/interchange/document/Validation/PlaneAxisValidate.py) checks the reference feature kind and exact ordered selection roles, then resolves two different local support planes. The [geometry guard](../../../src/interchange/Features/CheckAxisFit.py) checks the two rigid frames, a unique intersection, direction and endpoint incidence using the existing neutral direction and station tolerances. The endpoints and supports share model coordinates in millimetres, independent of the document's display unit. The generic definition retains the supplied segment orientation and trim. The [scoped native hinge rule](LocalLinearPatternFiniteHinge2026.md) continues to bind first Top and second Right and compute the finite display intersection from the joined stock.

The [portable proof receipt](../measurements/2026/PortablePlaneIntersectionAxis01.json) binds two actual offset or oblique neutral documents, fifteen refused malformed variants, and two older neutral histories with byte-identical serialization and the same invalid-frame error. Both prior corrected oblique pattern files reproduce byte for byte after the real portable document read. The proof projects the four public axis fields to the existing research composer contract and uses the original typed presentation input. The wire payload of that read is exactly the prospective neutral model from the prior proof. The clean source-controlled generation used no runtime input reads or CAD application.

```sh
axis_proof="$(mktemp -d)"
python3.14 -I -B re/tooling/sw2026/linear_pattern/neutral/ProvePortableAxis.py \
  --disclosed /absolute/path/to/GeneratedLocalPatternNative02 \
  --output "$axis_proof/Receipt.json"
```

The [disclosed native scope](LocalLinearPatternParentScope2026.md) remains the source of original lifecycle evidence. This portable-model change earns zero additional native or held-out credit. Target-specific synthesis and annotation presentation remain within the existing research route.
