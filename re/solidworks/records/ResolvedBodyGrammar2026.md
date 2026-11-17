# Ordinary version-19000 resolved body graph in the SDK

The SDK has a declared ordinary linked `ResolvedFeatures` graph codec using the
same typed objects, maps and field kernel as Config and CMgr. Full public linked
semantic admission, unexercised branches, held-out qualification and fresh native
writer acceptance remain unfinished.

## Task and evidence boundary

Task `B04-SW2026-RESOLVED` is owned by `/root/flag_ownership` and delivers
through PR #121. This evidence covers exact typed parity and inherited aliases
for the disclosed profile through the research entry point. The verification
uses static original PE metadata and host processes. [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
[Loader chapter](../../Playbook/LoaderAnalysis.md) [Writer chapter](../../Playbook/WriterModel.md)

This is the pinned SOLIDWORKS 2026 SP05.2 release, executable build
`34.5.2.0604`, ordinary archive version `19000`. The source-backed
[dependency census](LinkedGraphScalarConstruction2026.md) identifies 109 additional
owner and helper layouts beyond the 175 existing Config and CMgr layouts. The twelve
groups include sketch 25, dimension 19, folder 14, reference 10, body 8,
profile 8, feature 7, component 5, geometry 4, material 4, core 3 and assembly 2.
Registry availability and actual per-direction usage remain separate quantities.

Current native format knowledge comes from the existing Config/model, profile,
rectangle sketch/dimension, common owner, annotation, material, geometry and
assembly records.

- [Config grammar and exact header aliases](ConfigBodyGrammar2026.md)
- [Independent CMgr grammar/context](CmgrBodyGrammar2026.md)
- [Current profile construction](ProfileConstruction2026.md)
- [Rectangle sketch owners](RectangleSketchOwners2026.md)
- [Rectangle dimensions](RectangleDimensions2026.md)
- [Current geometry helpers](GeometryArchive2026.md)
- [Material/display archive fields](MaterialDisplayArchive2026.md)
- [Common display engine](RadialStyleAndEngine2026.md)
- [Common display field derivations](RadialEngineFieldRules2026.json)
- [Current assembly archive](AssemblyArchive2026.md)
- [Runtime descriptor metadata](ResolvedRuntimeDescriptors2026.json)

Field-order structure and directly read descriptor metadata are confirmed within
their stated current-version scopes. Model meaning, fresh construction domains,
cache neutrality and unexercised paths retain existing partial/unqualified status.
No saved values, field-offset programs or whole-word constructor defaults were
introduced.

## Framing and inherited ownership

`ReadResolvedMut` and `WriteResolMut` work from an explicit `MapSnapshot` and
three-field linked context. They use the existing shared scalar, CString, tag,
count, `ArchiveNode` and `ArchiveMaps` APIs. No production `re` import or file/CAD
runtime dependency exists.

The u32 stream prefix must equal the actual configuration snapshot counter.
The following vendor count gives the number of root object references. Reader
and writer extend `ArchiveMaps(base, configuration_snapshot)` directly, retaining
each inherited `MapEntry`, class and object identity. Header indices are not
reconstructed, and CMgr is never the seed. A unique concrete inherited
`moPart_c` or `moAssembly_c` identifies the owning model.

The explicit context is `model_compressed_stream=1`, `model_is_part` matching
that inherited owner, and raw `cmgr_f658` supplied by the separate manager.
`MakeLinkContext` remains the shared source for the configuration/manager pair.
Other context profiles, missing owners, mismatched bases, unsupported versions
and unbound external-class placeholders fail closed. This profile requires a
complete Config seed.

After the roots, a direct `moPartConfiguration_c.SerializeMBSMDataObjects` record
exists exactly when both `model_is_part` and `cmgr_f658` are nonzero. It has its
own mutable field mapping, no class tag and no archive slot. Omission or addition
against the context rejects serialization. Root counts and mapping counts derive
from actual modeled collections. Complete consumption is required; no tail is
returned as admitted typed data.

`ResolvedGraph` publishes roots, the optional direct mapping fields, the frozen
result map, actual base, initial linked context, version and usage. The result
counter can seed the later mate stream. This does not promote mate grammar or
semantic projection.

## Shared field operations

The new layouts reuse the current field DSL. The added closed expression
vocabulary handles native field/context lookup, typed node/class tests, exact
virtual predicates, integer/number operations, short-circuit Boolean selection,
comparisons and counted-row sums. Expressions are independently authored format
rules compiled from source, not executable document functions or saved programs.
There is no `eval`, arbitrary attribute access or document-supplied callable.

Concrete virtual slots retain their native integer/Boolean results rather than
being assumed to be serializer names. The current composite profile binds 133
slot entries. Existing Config/CMgr rules and archive bytes remain unchanged.

The ordinary live-section field `f378` has runtime normalization
`int(wire == 1)`, not `int(wire != 0)`. Its separate `#wire` value is preserved
under the same raw-wire-versus-runtime policy as other normalizations.
`moMateGroup_c.f4e8` uses high-u32 then low-u32 framing but one combined
`f4e8#count` field. The existing split-count mode with separate high/low field
keys remains unchanged. The new combined mode preserves its distinct ownership
and the existing ten-million repetition limit.

## Typed dynamic arrays and excluded payloads

Only two variable array payload definitions occur in this 109-layout source
closure: profile helper `FUN_4bb09f20` and display helper `dm.FUN_4bd03960`.
Disclosed report metadata observes 25 display payloads per direction, each eight
bytes, and no profile-helper payload. Those observations select the exercised
scope; they do not establish element semantics.

The independently pinned common display constructor/update establishes one
binary64 parameter element for `f5b0`: native evidence includes
`0x4c88a1e0`, `0x4c8a1498`, `0x4c8a1544` and `0x4c8a1550`, with complete
module/function hashes in the engine records. The SDK admits that packed
binary64 grammar only for the current linear/angular display owners with native
`elem=8`. It reads each scalar with the shared codec and computes emitted count
and bytes from individually decoded scalars. Existing research `data:bytes`
field compatibility remains, while usage records expose element type/count,
typed values, owner, length rule and observed byte count. It is not an opaque
payload re-emission operation or a value/default inferred from one corpus row.

The generic profile array admits only an empty payload. Nonempty unknown element
grammar rejects admission. The selected compressed-model context excludes the
separate embedded Parasolid raw path. Other body modes, drawing modes, unknown
subclasses, unproved array content and missing helper closure stop explicitly;
no raw remainder or recorded fallback is emitted by production code.

No constructor-zero, source observation, common update or reader normalization
is promoted to a final saved-state rule. In particular this tranche makes no
radial whole-word or post-owner callback-preservation claim.

## Runtime descriptors

[ResolvedRuntimeDescriptors2026.json](ResolvedRuntimeDescriptors2026.json)
binds 56 original exported current class records to their exact pinned modules.
All were found. 51 are serializable with registered wire schema one; five bases
have schema `0xffff` and remain inherited helper grammar only. The new concrete
profile combines those 51 with the existing 103 Config descriptor bindings.
No schema-one guess is substituted for actual native metadata.

The selected PE hashes are unchanged from the Config record: model
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, MFC support
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`, and archive
`5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`.
Geometry helpers additionally retain their separately pinned geometry-module
provenance. Proprietary images/listings remain outside the checkout.

## Actual research caller and diagnostics

`ResolvedCore.load_resolved` and `store_resolved_state` now delegate through
`ResolvedBridge` for the declared profile. The bridge retains the actual Config
snapshot and source-compatible `Obj` nodes, initial document context, map base,
member aliases and direct MBSM field mapping. Its reader still uses `Streams`
for the existing `load_rooted` helper. Production has no research import.

Other existing research profiles can use the previous typed reader/serializer
with `sdk_ordinary_resolved.admitted=false`, an incomplete SDK usage record and
an explicit diagnostic. This is not shared codec admission. Malformed known
fields fail; unread tails remain unqualified. Fingerprints cover the new bridge,
shared expression code, resolved framing and body layouts.

## Verification

The parent independently froze the 147-path initial SDK overlay, SHA-256
`6b3bff1e93fd00120e6767a7dc2b11f1e14e324be59db7b24dce3f41b8670c32`.
All twelve disclosed streams passed exact SDK read/store, inherited identity and
map checks, malformed cases and modeled feature-name edits. Raw report
`ResolvedSdkVerify01/ResolvedReadWrite.json` has SHA-256
`b8b0d96e0b76d5df59c3a1031569934f701c8faa56a19989af1992bd95b9cea6`.
These are source-process checks, with zero native application runs.

The staged 158-path research bridge/permanent integration overlay has SHA-256
`8c8431a101605588b5cc6aa7e2715ca2889a3659e02216207ecbf57dbfbcd9c4`.
Its results are recorded separately only after actual parent execution. No
initial result is transferred to changed executable bytes. C10, full public
linked semantics, native feature/geometry/editing checks and writer acceptance
remain outside this tranche.

The complete frozen bridge check passed all twelve decoded field/alias/position,
inline-record and stored-map comparisons. SDK body use is 138 schemas in each
direction; the research load union is 166 because it also reads the independent
manager context. Research store remains 138. The native scalar-array observations
are 25 per direction. Initial SDK checks rejected 72 malformed cases and passed
12 modeled name edits.

The permanent process regression generated an independent neutral part/assembly
pair under the runtime-input-read guard and passed the real SDK/bridge CLIs and
unqualified-tail behavior. It added twelve malformed rejections and two modeled
edits. The same frozen source passed 36 strict linked Config/CMgr/Resolved stream
comparisons and six complete dedicated seeded MatesList comparisons. The first
mate harness stopped after one comparison on an unused usage accessor; it earns
no batch credit. Only the corrected complete six-file receipt is counted.

The sanitized [receipt](../measurements/2026/SdkResolvedGraph01.json) binds source
snapshots, input identities and raw report hashes. Complete bridge parity hash:
`a5c156f4708c4d3e03c9e44e8532f9fce886c3e1135339403215560f8c525c60`.
Strict linked-core hash:
`78a63a7e3294ed9de6fb2e72f01b78953498a62f47e48642d056e030d9287b0c`.
Complete dedicated mate hash:
`bf239ea35e00644dda27dbd2129f6aaffea4bd0eba03bcbe362b6979b86e0452`.
No underlying native CAD file, saved stream payload or vendor listing is included
in this publication. These results do not transfer native/C10 acceptance.
