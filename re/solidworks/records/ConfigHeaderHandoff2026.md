# Ordinary configuration header handoff in SOLIDWORKS 2026

Status is a promoted typed map primitive. The semantic body grammar for a complete
public assembly graph remains a separate dependency. The target profile is
SOLIDWORKS 2026 SP05.2, ordinary archive version 19000.

## Recovered construction rules

For an already decoded `moHeader_c` of schema 1, define `H` as its present self
file `f38` followed by the objects in `f30`, traversed head to tail. An absent self
file contributes zero slots. An absent directory contributes zero slots. The
directory owner is `moExtObjectList_c` of schema 1 and each selected file owner is
a concrete `moExtObject_c` of schema 1. Unknown external-class placeholders fail
the concrete-class check.

Let `c` be the destination archive counter immediately before direct registration.
For each `H[i]`, insert that same object at map index `c + i`. The resulting
counter and inherited base are both `c + len(H)`. This operation emits zero bytes.
Its selected objects retain their original `IndexValue`, field mappings, offsets
and class descriptors. Map slots are derived from the destination traversal.
The source header's standalone object indices belong to that separate stream.

The ordinary Config root's class and object allocate indices 1 and 2 before
registration, so this measured entry point has `c = 3`. The generic SDK binding
operation uses its actual input counter. It also supports the existing drawing
subgraph callers' already selected owner objects. An empty batch still advances
the inherited base to the current counter.

The Config snapshot seeds its ResolvedFeatures reader/store. The resolved snapshot
then seeds MatesList. All stages retain the same selected header objects. An
occurrence's `moReference_c.f3b0` aliases its selected directory file by identity.
Persistent file IDs and filename strings do not determine this map allocation.

## Native provenance

The existing direct-object proof binds `sldmodu.dll`
`[0x4c17bd90, 0x4c17c6b3)`. The save calls at `0x4c17c0d8` and `0x4c17c11b`
register self then directory. The load calls at `0x4c17c3c2` and `0x4c17c3f2`
do the corresponding registration for versions at least `0x27bd`. Version 19000
reaches this branch. `swccu.dll` direct helpers `0x31a39d20` and `0x31a39d00`
perform store-map/load-array registration and counter advancement with no wire
payload. Cache handoff `sldmodu.dll` constructor `0x4c010120` and
`swccu.dll` `0x31a39210` carry the map/schema state to the next stream.

These identities and the recorded module hashes come from the existing pinned
2026 findings. This promotion performed source-level work and process checks.
Its evidence inventory contains independently authored rules and source hashes.

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

[Original map rule and bound module manifest](ArchiveMapConstruction2026.md)

[Standalone SDK header grammar](SharedSdkHeaderGraph2026.md)

## Shared implementation and compatibility

`HeaderRefNodes` selects from either the standalone SDK header graph or the
research decoder's same `ArchiveNode` objects through an explicit directory-item
callback. The production default accepts the SDK ordered tuple. The research
callback extracts its ordered `row['o']` entries. Both return the original nodes.

`BindNodesMut` validates the full input sequence and remaining counter capacity
before mutation, uses the shared `AddEntryMut` allocator and advances `BaseValue`.
It accepts node subclasses and field mappings such as lazily computed builder
fields. It allocates each supplied list position, including repeated node
identities, using the established map behavior.

`Core.ArchiveState.bind_direct_objects` delegates to this implementation for
both load and store. `ConfigPart.header_direct_objects` delegates version-19000
selection to the SDK. Older research selection remains explicitly outside this
promotion. Drawing Config's inline-header branch remains its own schema path.
The ordinary research loader retains `model_header_source`, field spans and
schema-usage tracing from its header reader.

`FieldScan` binds the new map module automatically and explicitly fingerprints
`HeaderRefNodes`, `ReadHeadItems` and their version owner `HeaderFields`.
The permanent inventory assertion requires those same fingerprints.

[Shared selection](../../../src/convert/adapters/solidworks/Archive/Header/HeaderRefNodes.py)

[Shared direct binding](../../../src/convert/adapters/solidworks/Archive/Maps/BindNodesMut.py)

[Actual configuration caller](../../tooling/sw2026/serial/defs/ConfigPart.py)

## Verification procedure and remaining boundary

The `CheckSdkHeaders --config-handoff` process reads each standalone header with
`ReadHeaderGraph`, supplies those exact nodes to the actual research Config body
decoder and writer, then performs seeded ResolvedFeatures and optional MatesList
round trips. It also requires agreement with the ordinary linked loader's map
counters, verifies occurrence aliases and re-emits the original header after
binding to confirm preservation of standalone indices and bytes.

The process regression builds an authored distance pair through the guarded
builder, checks the linked header handoff through the CLI and then projects the
typed mate through the SDK module. The existing synchronized-source regression
checks five independently hash-bound files, ten header streams, forty original
stream comparisons and five SDK-header handoffs. A separate disclosed comparison
uses only A17, A18, A19 and their three generated pairs, each verified against its
existing source lock or frozen generated manifest before parsing.

The final local run passed five relevant real assembly process integrations in
6.78 seconds with Python 3.11 and pytest 9.1.1. The twelve disclosed/generated
files passed twenty-four standalone header comparisons and twelve Config and
Resolved handoffs, including their available mate streams. All six projection
CLI outputs were byte-identical to the pinned earlier implementation. The
generated distance child's linked field inventory passed `--require-proven`,
and its permanent implementation assertion verified all 89 current source
fingerprints. The seven scoped source files passed Black, Ruff 0.17.4, Mypy 2.4.1,
Pyright 1.1.414 and the steering checker. Pyright also printed its three existing
unrecognized configuration setting notices.

The companion receipt records the actual executions and final implementation
hashes. It reconstructs independently authored summary metadata from the private
raw process reports and their custody hashes. Source inputs were checked against
the existing discovery lock or immutable generated manifests before every pair's
comparison. The original files stayed read-only.

No native application phases or held-out input payloads contributed to this
promotion. Full public Config/Resolved graph admission requires the remaining
body schemas and their qualification. These byte comparisons establish archive
linkage and compatibility for the recorded shapes. Vendor-loadable and
application-usable output require their separate controlled oracle measurements.

[Revision-bound process and source evidence](../measurements/2026/ConfigHeaderHandoff01.json)

The governing stopping condition remains “There are two acceptable stopping
conditions. The first is success under every criterion on this page. The second
is the end of the available context.”

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
