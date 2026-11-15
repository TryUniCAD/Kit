# Fresh SOLIDWORKS 2026 part composition

Status: research candidate, with no generated-output native acceptance yet.

The base composition now includes twelve authored system folders and the
annotation cabinet in addition to the three principal planes. Presentation
requires an ordered `folder_names` mapping and `cabinet_name`; provenance supplies
their creation time. The serialized root environment pointer aliases the same
constructed environment feature. All nodes share one persistent-id allocator.
System-node initialization clears their native pending flags while the model's
pending state and unresolved user-feature/sketch lifecycle remain separate.
The [model record](ModelConstruction2026.md) binds this extension to native
folder callbacks and serializer fields. The complete candidate is still
unaccepted until fresh vendor measurements pass.

`builders.Part.construct_part` joins constructor-backed graphs without reading
source CAD. It supports one ordinary closed polygon on a principal plane and a
single one-direction blind boss with four live length/angle parameter chains.
It also constructs the three principal planes and an origin profile. All
geometry coordinates and depth are neutral inputs in metres.

## Ownership

| Output | Construction rule | Owning evidence |
| --- | --- | --- |
| Config-0 | New part root, native unit tables and fresh detail graph; direct-reference count zero because both header reference lists are null | [model constructors](ModelConstruction2026.md), [style constructors](StyleConstruction2026.md), [header construction](HeaderConstruction2026.md) |
| ResolvedFeatures | Constructed principal planes, origin, polygon profile and blind extrusion; roots count is collection length | [profile construction](ProfileConstruction2026.md) |
| Resolved map prefix | Exact `Store.map_state().count` from Config-0; same class/object identities seed resolved serialization | [archive map construction](ArchiveMapConstruction2026.md) |
| CMgr | New manager and single local configuration, independent configuration-id namespace | [model constructors](ModelConstruction2026.md) |
| Definition | Fresh part document preferences and authored density | [model constructors](ModelConstruction2026.md) |
| Header2, ModelHeader | Allocator next id, authored user/company/time/log state, separate owner-model presence | [metadata construction](MetadataConstruction2026.md) |
| Biography, History | Empty persisted biography, one truthful non-native-save provenance record | [metadata construction](MetadataConstruction2026.md) |
| KeyWords | Actual constructed feature ids/names and depth in the authored presentation unit | [metadata construction](MetadataConstruction2026.md) |

The caller supplies an initialized registry so that construction does not scan
schema directories. Importing Python modules is outside the conversion data
boundary. The constructor takes no stream, path, donor payload or captured
program input. The normal container serializer receives only the new stream map.

The origin and ordinary profiles now own separate `moCompRefPlane_c` objects.
Each wrapper contains a separate copied unit component; both copies retain the
same actual model owner and target principal plane. The composer previously
passed one wrapper to both profiles despite the native setters' exclusive
ownership. The [plane-wrapper dataflow](ModelConstruction2026.md#plane-wrappers)
proves the required lifetimes. A complete-file subprocess check decodes the
shared configuration/resolved graph and reports these identities under the
strict construction audit. The process check passed on `f374f8319` in remote
job `132788308932`, run `43706398170`. Strict typing failed on the newly added
test helper imports and was corrected in `dcee1cf18`, whose checks remain pending.
The generated `H3_scalene.SLDPRT`, SHA-256
`3b68ad9e4d77c180b02cb59423aaa25be1d8b560d03b23470347055ffa03f03d`,
still failed native measurement with RPC error `-2147023170` between two healthy
original controls on executable build `34.5.2.0604`. Each control rebuilt one
solid, volume `8.000000000000001e-6 m³`, area `0.0028 m²`, center `(0,0,0.005) m`,
with zero open/rebuild/feature warnings or errors. The
[negative measurement](../measurements/2026/FreshPartProfileOwnership.json)
retains exact executable and artifact identity. Reference ownership was a real
graph invariant, but this repair did not resolve the remaining native failure.
The original aggregate helper did not preserve partial open/rebuild results,
so it cannot identify the exact failed public API call. The subsequent staged
measurement helper corrects this evidence gap; old open-specific attribution
from a missing `opened` value is not established.

The origin profile retains an explicit unresolved native update state. Fresh
header update/body counters start at the native constructor seed 101; their
post-build state is not proven. Root/detail cache seeds have static constructor
or native dataflow evidence, not an oracle-proven neutralization. The selected
dimension leader remains an explicit presentation input. These limitations must
remain visible until closed; byte identity alone cannot clear them.

## Verification

No local tests were run. Remote process integration and native application
acceptance are pending. No writer capability has been enabled in the production
adapter. Source corpus files and hash-locked held-out controls are not generated
outputs and are excluded from generated coverage.

## Reference creation identity

The principal planes currently have no authored revision-log entries. Their
FRData wrappers therefore use `logged_creation_time(timestamps=())`, the native
absent-log sentinel, rather than the root document's authored creation date.
Feature FILETIME fields remain separate. The
[model record](ModelConstruction2026.md) traces this rule to native log access
and `ut_getUnsetTime`; this correction has not yet passed native acceptance.
