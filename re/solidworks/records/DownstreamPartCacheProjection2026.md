# Generated standalone part cache projection, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns this projection and native qualification. The pinned native build is 2026 SP05.2 `34.5.2.0604`, with effective archive version 19000. The current implementation is a research entry point.

## Named storage

The [standalone save dispatch](DownstreamStandaloneStore2026.md) selects the configuration and its eligible cache before it attaches a stream. [`getStorageName` source proof](DownstreamConfigurationStorage2026.json) binds `moBaseConfiguration_c::getStorageName` at `[0x4bdda870,0x4bdda964)` and the same configuration-ID getter in four concrete table entries. The branch with runtime `fbf0 == 0` uses `Config-` followed by the base-10 signed configuration ID at `f08`. The alternate branch uses `FlexCfg-`, signed `fbec`, a hyphen and signed `fbe8`. The visible configuration caption is independent of these names.

[`store_part_caches`](../../tooling/sw2026/downstream/Storage.py) takes generated streams and explicit configuration/cache state. It selects `Contents/<storage name>-DownstreamIdData`. Unopened models and rebuild-pending noncurrent configurations skip the stream. For an eligible opened model, an absent or stale cache removes the named stream. A current cache supplies the byte stream through the direct typed body encoder. The encoder starts its own logical map at one. Identical storage names in one call refuse.

The container exercise attaches a modeled cache body to the actual generated part configuration with ID zero and retains all ten generated input streams. A separate two-stream exercise uses ordinary ID 42 and the flexible pair (12, 9). It changes a typed collection and reads back both sizes. These are checks of the archive envelope and generated logical body. Native compression selection, flexible model creation and live cache activation remain outside the exercise.

## Populated prefix

The [numeric source record](DownstreamCachePrefixSources2026.json) binds the actual part table at `0x4d1252d8`. Its slot `+0x11f0` reaches the leaf at `0x4b285b20` and returns the model's owned header at runtime `+0xa8`. The ordinary creation call at `0x4b578824` reaches `0x4b5263c0`. The update branch at `0x4b58f760` reaches `0x4b53a480`. Both selected finalization windows apply the same five assignments once the actual header is available.

| Word | Classification and rule |
| --- | --- |
| `f08` | The actual next downstream ID from the modeled traversal. The scoped surface witness supplies its initial counter because it populates only its explicit `f40` collection. |
| `f0c,f10` | The starting format version and exact build code. The selected fresh 2026 profile constructs these as 19000 and 2026306. |
| `f14,f18` | The native current format version and full date code at cache finalization. The exact build supplies 19000 and 2026306. |
| `f1c` | The model update counter from `moHeader_c::getCurrentUpdateStamp(NULL)`. Its imported leaf reads header `f40`. |
| `f20` | The model body counter, read directly from header `f44`. |
| `f28` | The owning header's update time at `f48`. The native cache retains the runtime time and the archive carries its 32-bit time word. |

The freshness predicate at `0x4b535b80` returns zero for a missing runtime model owner. With an owner, it checks the cached time against that model header's current update time. The selected comparison uses the runtime words. It supplies the stale part-cache condition in the save dispatch. The independent generated-header replay checks the precise prefix of both scoped cache bodies against the corresponding ModelHeader bytes, including distinct update counters, body counters and update times. [Constructor and populated-state gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/PopulatedCachesReplaceConstructorPrefix.md)

## Projected owners

| Value | Classification and owner |
| --- | --- |
| Cache suffix and ordinary/flexible prefixes | Exact-build constants from the pinned save method and configuration helper. |
| Configuration IDs and save lane | Inputs from explicit configuration state. The ordinary generated part uses the owned configuration ID. |
| Keys 0 through 3 | Exact-build ordered roles. The selected positive fin and its partner supply 0 and 1. The partners of the previous and next fins supply 2 and 3. All values come from the shared generated face allocation. |
| Surface ID representations | Derived from actual `FACE_ID_2001` attributes, their generating feature ID and creation epoch, and the sketch arc or native cap selector. The local B-rep walk checks face and atom ownership. |
| `moFR_c.f08` | Typed file/configuration owner supplied to the projection. The projection checks its file name, recorded path and configuration against the actual generated part. |
| `moFR_c.f10` | Derived feature reference ID and creation epoch. The side and two cap representations each keep a separate typed record. |
| Local `moUnitComponent_c` | Independently allocated for each downstream reference. The ordinary part store context contributes the null filed-owner tag and the zero extension byte. The observed load context restores the model binding. |

The [boundary source](DownstreamBoundaryRoles2026.md) selects the fallback only for the ordinary branch with no special map and no participating permanent edge representation. The host projection checks real edge inventory and the generated partition's `EDGE_PERM_ID_2001` presence. Four generated prisms and cylinders confirm 56 adjacent and 56 boundary roles, including repeated face IDs under distinct role keys. It refuses a present special map, a permanent edge attribute on a participating edge and a foreign partition.

Two generated cylinder attachments exercise actual side and cap owners and include the resulting three typed references in a scoped `f40` cache witness. Each modeled container preserves all eleven generated part streams. The supplied file object in this exercise uses Kit's existing generated file builder. The [local-owner source](DownstreamLocalOwnerContext2026.md) binds the ordinary fresh external reference's live file, list index and conditional configuration fields. Actual list reuse and `f40` membership remain to be established for the populated cache.

The local-unit exercise places two separate clones in explicit `f48` and `f60` witnesses. The shared runtime class receives one slot and each clone receives one object slot. Both three-byte bodies read back and re-emit exactly. The profile refuses a stored foreign owner on a local clone. Actual entity graph population and the [assembly attachment store context](DownstreamAttachmentStore2026.md) have separate dependencies.

## Reproduction and qualification

```sh
export PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial
python -B -m downstream.CheckStorage
python -B -m downstream.CheckBoundaryRoles cylinder 1
python -B -m downstream.CheckSurfaceIdentities 1
python -B -m downstream.CheckUnitComponents
```

Use `prism` or `cylinder` and variant `1` or `2` for boundary roles. Both cylinder surface variants accept the same replay command. The [receipt](../measurements/2026/DownstreamPartCacheProjection01.json) binds the source and fresh process results. Each guarded construction recorded zero file opens, subprocess launches and network connections. Zero vendor application runs, saved CAD reads and held-out qualifications apply to this change.

Completing the cache requires the actual root memberships, reference modes and live ownership, followed by a disclosed native cache replay and generated drawing open, rebuild, edit, save and reopen. [Prior linked codec](DownstreamLinkedReferenceCodec2026.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
