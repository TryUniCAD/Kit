# Through-all CMgr feature events in SOLIDWORKS 2026

**The component host checks pass. Complete original-source preparation remains refused. No new native lifecycle or original held-out qualification ran.**

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-EXTRUDE-THROUGHALL-CMGR-EVENTS |
| Owner | `/root/configuration_header`; `/root` owns integration and the vendor oracle |
| Delivery | PR #121, additive private source tranche |
| Target | SOLIDWORKS 2026 SP05.2, archive version 19000 |
| Inputs | The same previously disclosed D01 forward and D02 reverse through-all controls |
| Dependency | The frozen UI scalar layer, shared precise feature times, explicit creation targets, fresh manager/configuration and archive codecs |
| Exit reached | Separate typed event owners, exact source correlation, generative construction and guarded host process proof |
| Remaining exit | All remaining original owners, native component qualification and pre-writer original-source qualification |

## Actual owners and dispatch

The [numeric source ledger](CmgrFeatureEventConstruction2026.json) binds the original `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, complete native function ranges, selected operand ranges, imports and concrete runtime-class dispatch. No vendor software or listings are included.

The model-taking manager constructor is `0x4b8802f0`. It retains the actual model separately in R15 and calls `moFeature_c` at `0x4bb38350` with a null concept owner. In the ordinary part branch, `0x4b880ad5` calls the concrete part-configuration constructor `0x4b595780`, supplying the actual model in RDX and manager in R8. The concrete configuration calls `moBaseConfiguration_c` at `0x4bdbf820`, which calls the same inherited feature constructor with the actual model/concept. The fresh SDK `owner` key is a symbolic construction relationship; this record does not claim that the manager's native base owner pointer is nonnull or that the key is serialized.

The manager then activates the actual constructed configuration with `setCurConfig` at `0x4b880cc5`. The second selector and `setConfigurationMgr` call at `0x4b880ce9` retain distinct manager/configuration ownership. Existing typed directory and activation constructors remain in use.

The concrete serializer slot is `+0x28`, not the framework bridge at `+0x10`:

| Concrete owner | Primary vtable | Serializer | Inherited call |
| --- | ---: | ---: | ---: |
| `moConfigurationMgr_c` | `0x4cec6bb0` | `0x4c21ef40` | `0x4c21efd3` → `moFeature_c::Serialize` |
| `moPartConfiguration_c` | `0x4ce2d008` | `0x4c228a30` | `0x4c228b48` → base configuration |
| `moBaseConfiguration_c` | `0x4d027498` | `0x4c217e30` | `0x4c217ec5` → `moFeature_c::Serialize` |

The modern inherited feature serializer is `0x4bb11aa0`. The existing field executor retains its order and map rules; this tranche adds no layout or recorded program.

## Separate time and provenance

| Typed input | Actual fields | Derivation or source rule |
| --- | --- | --- |
| `ConfigEvent.MomentValue` | `f2a0`, `f2a4` | Shared `FeatureInstant` and `MakeFeatTime`; whole Unix seconds plus a separate 100 ns fraction |
| `CreatedBy.FileVersion` | `f2b0` | Explicit inherited creation file version, current component requires 19000 |
| `CreatedBy.DateCode` | `f2b4` | Explicit inherited creation build code, required to match the declared construction target |
| `CreatedBy.ParasolidVersion` | `f2ac` | Explicit creation behavior token, required to match the declared target |
| `CreatedBy.ServicePack` | `f300` | Explicit creation service byte, current component requires 5 |
| `CreatedBy.SubservicePack` | `f301` | Explicit creation subservice byte, current component admits 0 and 2 |
| Existing fresh state | `f29c`, `f2b8`, `f2bc` | Retain update stamp 101 and zero last-update provenance; all other states refuse |

The ordinary explicit `setCreateVersion` at `0x4bb50a20` and `getCreateVersion` at `0x4bb42a40` bind these creation owners. `getLastUpdateVersion` at `0x4bb45c10` instead reads `f2b8/f2bc`. The source's creation subservice 0 is not replaced with the current save target's subservice 2. None of these fields is a save epoch.

The common update routine at `0x4bb4a4b0` separately stores `f29c`, calls imported `GetSystemTimeAsFileTime`, and stores the high and low words at `f2a4/f2a0`, with the exact frozen-model condition retained in the source ledger. A feature moment can describe an update. It is not universally a creation time, header time or revision event.

The shared time constructor derives `ticks = (seconds + 11644473600) * 10000000 + fraction`, splits its words, and represents each as signed 32-bit in the typed graph. The native archive emits the corresponding 32-bit words. No wall clock is read by the new constructor.

## Disclosed correlation

Both disclosed native managers have schema one, actual native ID -1 and no name. Each owns one distinct schema-one `moPartConfiguration_c`, ID 0, name `Default`. Its actual object is shared by `f360`, `f368` and the sole `f370` row. The Config stream separately owns a `moPart_c` with ID 0. Equal integers are not object identity.

The [source observation ledger](ThroughAllCmgrEventOwners2026.json) records the exact separate manager and configuration states and both source hashes. Their observed moments happen to coincide within each document:

| Source | Whole seconds | Fractional ticks | Creation file/build/kernel | Service/subservice |
| --- | ---: | ---: | --- | --- |
| D01 | 1795020274 | 3043842 | 19000 / 2026306 / 370108 | 5 / 0 |
| D02 | 1795020529 | 5374070 | 19000 / 2026306 / 370108 | 5 / 0 |

These values are source observations and source-conversion inputs. They are not defaults or per-case generator tables. No equality between the two owners or other document clocks is inferred.

## Typed component

Seven additive SDK modules define `ConfigEvent`, `CmgrEvents`, `RequireCmgr`, `ApplyCmgrMut`, `ReadCfgEvent`, `ReadThruEvents` and `MakeThruEvents`.

`ReadThruEvents` retains the existing source envelope and Config/Resolved linkage checks, then resolves the actual selected CMgr directory object. The native configuration name must agree with the public selected configuration. The method's caller must bind CMgr, Config, Resolved and the public document to the same source archive. Matching names alone do not prove custody across arbitrary files.

`MakeThruEvents` composes the existing fresh UI/document graph, then initializes event fields on its actual `PartSystem.ManagerValue` and `ConfigValues[0]`. `ApplyCmgrMut` requires concrete schema-one owners, the actual selected/directory aliases, the fresh part ownership relationships, matching declared target provenance, zero prior feature moments and unchanged fresh update state. It validates both owners and derives all pending operands before changing either one. Parsed source graphs are not accepted as fresh construction objects.

The two immutable semantic event inputs remain separate. Independent tests deliberately vary their seconds, fractions and creation subservice in opposite directions. No node is replaced, no saved field dictionary is copied, no runtime file is read and no stream is patched.

## Verification and unchanged boundaries

The [host receipt](../measurements/2026/ThroughAllCmgrFeatureEvents01.json) binds all source, SDK, tool and result hashes. Its main matrix runs 102 fresh SDK workers, including 64 SDK refusals. Eight additional fresh workers compare entire before/after typed CMgr graphs and exactly re-emit both streams.

Two source projections retain the original document JSON, previous projections and complete-source diagnostic. Two deterministic builds per disclosed input match both event owners exactly. Six independently chosen moment/subservice pairs retain the real ownership graph and exact integer-word prediction. Eight separate generated seven-fragment readbacks re-emit all streams. Each full CMgr comparison proves that only the requested event operands changed; all other fields, classes and collection cardinalities remain identical.

The new source-paired construction changes only the `Contents/CMgr` fragment. The complete Definition and five other owner fragments remain identical to the previous UI component. Existing callers preserve both complete generated compatibility cases and the earlier six-fragment and Definition results byte for byte.

Negative processes cover wrong concrete classes/schemas, detached equal-name selector copies, directory/allocation disagreement, wrong local IDs, source update state, missing/malformed time/provenance fields, unsupported releases, boolean/range errors, foreign/fabricated fresh owners, preinitialized moments, mismatched creation targets, corrupted CMgr and wrong Resolved map context. Failed fresh operations leave both event-word sets unchanged. No observer exception is counted as an SDK refusal.

Black, Ruff, strict Mypy, strict Pyright, steering and the donor scan pass the seven new SDK modules. Initial static-only local-variable typing and rationale punctuation failures remain recorded separately from the passing freeze. The installed Pyright prints existing unrecognized configuration-key notices; it reports zero errors and warnings for the new modules.

The residual comparison is **23 CMgr frontier paths**, down from 29 in each disclosed source. Definition retains the same two environment-window paths. Frontier counts use one marker for a differing collection length and are not semantic coverage percentages.

Remaining CMgr owners include source external file/config references; activation/visibility/saved flags; actual update/allocation progress; populated appearance; atom/body/feature mappings; the manager's separate per-configuration timestamp map; Resolved mapping context; and the empty saved manager list. None is substituted from source rows or declared disposable. Per-user environment windows remain a separate Definition frontier. Complete source preparation, public activation, new native acceptance and original held-out credit all remain false.

[Change entry](../../../Documentation/Changes/Solidworks/Writing/Parts/ThroughAll/SolidworksThroughAllCmgrFeatureEvents.md) · [Guide](../../../Documentation/Reference/Research/Solidworks/Construction/ThroughAll/CmgrFeatureEvents.md)
