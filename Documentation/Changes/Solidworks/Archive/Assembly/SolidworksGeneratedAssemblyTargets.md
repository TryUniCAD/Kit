# Share actual generated targets across assembly construction

The internal SDK assembly construction layer now has one generated-target
contract for actual part and assembly definitions. It retains the original
configuration and header owners, local bounds, direct child graph, computed
activity and output bytes. Directory and reference construction share the
ordinary native factory rules. True subassembly occurrences select their
assembly insertion options and recursive target stamp sources.

Use `MakePartTarget` with an actual `PartCandidate`, then pass explicit
`TargetPlacement` records into `MakeNestedAsm`. The resulting target can serve
another assembly directly. `MakeAsmTarget` adapts an existing complete single
or ordered mate candidate; native qualification of such a new nested
composition remains separate. The first recursive profile requires visible,
fully resolved rigid placements, one active configuration per definition and
empty new mate groups. Unsupported states and inconsistent or cyclic graphs
fail explicitly.

The stdin research process produces a complete generated dependency bundle,
using the SDK serializers for every stream and container byte. Its frozen
proof covers both a three-definition hierarchy and a four-definition mixed,
repeated hierarchy, 156 typed stream round trips, seven rejected malformed
DAGs and zero runtime input reads or SDK research imports. All 12 ordered and
18 single-mate baseline bundles retain exact container and stream bytes.

`PrepareSdkNestedTrial.py` freezes an independent geometry/tree prediction and
the separate native observer. Its serial recipe checks disclosed N01 controls,
open/rebuild, a live leaf-depth edit, deepest-first synchronized save and fresh
reopen. Host verification starts no CAD process. This constructor tranche does
not enable public writing or claim new native or held-out acceptance.

[Frozen process evidence](../../../../../re/solidworks/measurements/2026/SdkNestedAssemblyConstruction01.json)

[Scope, native evidence and current verification](../../../../../re/solidworks/records/SdkNestedAssemblyConstruction2026.md)
