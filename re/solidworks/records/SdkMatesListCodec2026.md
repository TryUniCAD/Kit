# Typed SDK MatesList codec for SOLIDWORKS 2026

The six disclosed mate streams and one independently generated distance-mate bundle pass typed SDK read/store/read identity, inherited alias checks, and malformed-context rejection. This is a linked codec result only. Public mate dispatch, held-out qualification, and new native output acceptance are not established by this tranche.

| Ownership | Value |
| --- | --- |
| Task | `B04-SW2026-MATESLIST-CODEC` |
| Owner | `/root/assembly_occurrence` |
| Delivery | PR #121 |
| Scope | Ordinary version-19000 empty lists and two-plane coincident, parallel, and positive-distance lists using an actual SDK `ResolvedGraph` |
| Dependencies | ModelHeader → Config-0 → CMgr branch context → ResolvedFeatures → MatesList, plus the existing ordinary body grammar and typed native object map |
| Exit for this tranche | Six disclosed byte identities, six independently retained maps, complete typed readback, empty-list framing, malformed negatives, and a neutral generated-bundle process proof |
| Remaining product exit | Linked semantic adapter integration and the applicable native and held-out CAD criteria |

## Framing and ownership

The format rule is **confirmed for the ordinary 2026 object archive**. `Config-0-MatesList` starts with the final ResolvedFeatures map counter as signed little-endian i32. A directly serialized `suObList` follows; no class or object tag wraps the list. Its count uses the shared archive count format. An empty list is six bytes and allocates no map slots. [Original save/load trace](AssemblyMatesList2026.md)

`ReadMatesMut` and `WriteMatesMut` take the actual `ResolvedGraph`, not a counter and fabricated table. Their context requires archive version 19000, compressed ordinary model state, and an inherited `moAssembly_c`. The prefix must equal that snapshot's counter. Map membership is copied, preserving every inherited class and object identity. The separate stream does not change the resolved mate group's stored children. [Reader](../../../src/convert/adapters/solidworks/Archive/Mates/ReadMatesMut.py) · [Writer](../../../src/convert/adapters/solidworks/Archive/Mates/WriteMatesMut.py)

The codec extends layouts, descriptor schemas, and virtual dispatch only inside its new `Archive/Mates` context. The preexisting Config and Resolved admission tables are unchanged. Source fields are read into ordinary SDK nodes and re-encoded from their field values; no recorded field programs, captured rows, donor payloads, research imports, or CAD runtime are used by the SDK modules.

## Owner grammar

The table records format vocabulary. It supplies field order and class dispatch, never document-specific member values. All addresses below refer to pinned `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, SOLIDWORKS 2026 SP05.2. The regenerated 2026 dispatch map independently binds the concrete descriptors. [2026 serializer map](../../data/Serialization/SerializeMap2026.json) · [Native wrapper and factory evidence](PlanarMateWrapperNative2026.json)

| Owner | Serializer | Ordinary version-19000 contribution | Status |
| --- | --- | --- | --- |
| `moMateParent` | `0x4b66b620` | Model-feature base; i32 `f390`, `f394`, `f388`; counted i32 auxiliary entries | Confirmed wire |
| `moMate` | `0x4b668d90` | Parent; u16 alignment and independent solved state; optional vector; ordinal/detached-wrapper rows | Confirmed wire |
| `moMateNGeoms_c` | `0x4b66ad10` | Mate; extra object; resolved wrappers; auxiliary lists; three objects; u16 option; normalized i32 boolean; two strings | Confirmed wire |
| `moMate2Geoms_c`, coincident, parallel | `0x4b668a60` | Shared N-geometries base | Confirmed wire |
| `moMateDim_c` | `0x4b669510` | Two-geometries base; distance-display object; u16 option | Confirmed wire |
| `moMateDistanceDim_c` | `0x4b669690` | Dimension base; u16 mode; three signed option words | Confirmed wire |
| `moRefWrapper_c` | `0x4c2773d0` | Component reference; context; stamps; independently present transforms; acquisition, ordinal and configuration state | Confirmed ordinary plane path |
| `moSurfaceRef_w` | `0x4c2797d0` | Wrapper base and four binary64 surface-bound values | Confirmed wire |
| `moPlaneRef_w` | `0x4c274810` | Surface wrapper; root, normal, transform and final point | Confirmed wire |
| `moAbsoluteRefPlnData_c` | `0x4c276e30` | Existing shared plane-data grammar without default-plane-only display root | Confirmed reached wire |

The wrapper context admits only the ordinary component-plane endpoint path. Its explicit guard rejects another reference class before the plane-only framing continues. A Node rule's type hint alone does not perform this guard. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/MateWrapperKindNeedsAnExplicitGuard.md)

The three concrete mate descriptors have the shared concept virtual rules: feature XML at slot 1000, the native true predicate at 1016, lightweight concept data at 1208, and resolved concept data at 1216. The inherited reference chain/component/list grammar is reused directly. Those objects resolve the exact earlier occurrence and its `f4f8` external-feature object. [Reference-chain proof](PlanarMateReferenceChains2026.md) · [Factory state](PlanarMateWrapperWriteState2026.md)

Native boolean normalization of `f480` retains its independent raw i32 in `f480#wire`, following the existing SDK Boolean field operation. Distance display packed data uses the shared count-times-binary64 codec. In A18 it contains one typed value 0.06323; the generated distance input contains one zero cache value. These fields are reported explicitly with their element counts and observed lengths. They are not described as absent or opaque. [Typed resolved grammar](ResolvedBodyGrammar2026.md)

## Process evidence

[Sanitized receipt](../measurements/2026/SdkMatesListCodec01.json) binds the exact six physical file hashes, their independently established mate-stream hashes, the code closure, new source files, and the separate generated-bundle proof. The source cohort and prior linked receipt are disclosed-only. No sealed mate, offset, nested, or drawing input was accessed.

| Input | List bytes | Start counter | End counter |
| --- | ---: | ---: | ---: |
| A17 native coincident | 3304 | 168 | 196 |
| A18 native positive distance | 5117 | 168 | 207 |
| A19 native parallel | 3234 | 168 | 196 |
| Generated coincident | 2776 | 133 | 161 |
| Generated parallel | 2842 | 133 | 161 |
| Generated distance | 4643 | 133 | 172 |

Six fresh host Python 3.11 processes each verify byte identity, full typed map readback, two endpoint ordinals, assembly owner identity, the actual external-feature/occurrence aliases, and an unchanged inherited resolved graph. Each also reads and writes an empty list without map growth. The additional neutral bundle goes through the guarded native research generator, physical artifacts, then a fresh SDK codec process. It passes the same checks.

The SDK walk reaches 43 registered schemas for coincident/parallel and 66 for distance, with a union of 68. The earlier research census has one additional `suObList` call because it runs the top-level count and object loop through that registered owner. This codec handles the same direct list framing in its entry point. The lower call count does not remove an archive object or payload field; the complete bytes and map growth agree with the independent prior receipt.

Each populated process rejects 14 malformed cases: counter-only context, unsupported version, mismatched or negative prefix, a trailing byte, truncated graph or prefix, null read/write roots, unrelated root, unsupported mate schema, a missing owner snapshot, a missing actual external-feature alias, and a nonplane wrapper reference. The six disclosed runs therefore contain 84 explicit negative outcomes; the generated bundle adds 14.

Use the declared disclosed manifest and prior linked comparison, with a fresh output path:

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -I -B re/tooling/sw2026/SdkMatesProcess.py \
  --cohort /absolute/path/to/InputManifest.json \
  --linked-proof /absolute/path/to/LinkedMatesExact06.json \
  --output /absolute/path/to/UnusedDisclosedProof.json
```

The tool records a separate complete source manifest before returning the receipt and checks that the source closure stayed unchanged throughout all six processes. It refuses used output paths. The normal complete test suite includes the generated process integration at `tests/Convert/Solidworks/Research/Mates/MatesCodecTests.py`. Black and steering pass for the 14 new SDK/test files. Remote CI remains a separate gate owned by the parent agent.

## Remaining limits

The codec does not connect mates to the public adapter and does not replace legacy selection-string validation. It does not infer semantic acceptance from empty entities, nor mutate Config/Resolved roots to make a mate appear present. Existing public part and assembly routes remain unchanged.

The entry points re-encode the supplied model graph. They do not construct a generated native document by themselves. New mate kinds, face/edge references, multi-hop selection, alternate archive conditions or releases, and broad distance modes remain outside this admission scope. Current native family measurements remain in their existing independent receipts. No new SOLIDWORKS launch, output file, native acceptance, or held-out pass is claimed here.
