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

`PrepareSdkNestedTrial.py` freezes an independent geometry and feature-tree
prediction and the native observer. Both disclosed generated hierarchies
pass controlled native open, rebuild, a live leaf-depth edit, deepest-first
synchronized save and fresh reopen. The repeated hierarchy retains seven
expanded paths and five solids. Eight fresh SOLIDWORKS processes pass.
Public writing and held-out qualification remain open.

[Frozen process evidence](../../../../../re/solidworks/measurements/2026/SdkNestedAssemblyConstruction01.json)

[Native assembly measurements](../../../../../re/solidworks/measurements/2026/SdkNestedAssemblyNative01.json)

[Scope, native evidence and current verification](../../../../../re/solidworks/records/SdkNestedAssemblyConstruction2026.md)
