# Fresh drawing epoch experiment in SOLIDWORKS 2026

The independent construction and typed readback pass 26 host processes. The four generated pairs also pass 18 controlled native phases and 20 typed origin joins. [Native lifecycle and clock readback](DrawingSourceEpochNativeLifecycle2026.md)

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-DRAWING-ORIGIN-PROFILE, independent epoch experiment |
| Owner | `/root/flag_ownership`; `/root` owns execution, integration and native qualification |
| Delivery | PR #121 |
| Target | Ordinary SOLIDWORKS 2026 version 19000; native oracle 34.5.2.0604 |
| Dependencies | [Exact clock ownership](DrawingSourceEpochOwnership2026.md), the frozen origin constructor, SDK part/header/history/linked drawing codecs |
| Exit | Controlled native load/rebuild/edit/save/fresh reopen and archived clock/identity readback on the newly generated pairs |

## Construction boundary

`EpochPart.make_epoch_child` builds actual SDK model, configuration, profile, rectangle dimensions, corner anchor, boss and header nodes from an independently authored neutral request. It uses the existing shared allocator and constructors. Before the first child stream emission, `EpochClocks.apply_before_emit` applies the explicit discovery clock model to the actual header and root-event nodes. The history event is supplied through a separate fresh `HistoryInput` before `MakeFreshHist` runs.

The normal `CheckPartInput` first validates the unchanged baseline construction settings. Neither that function nor `HeaderInput` is edited. The private discovery boundary does not advertise a new supported normal-writer input.

Both actual child headers retain their one shared self-file object and equal header/self creation time. Their root event nodes remain distinct. Model/configuration ids, class/object maps, fields, counts, lengths, compression and containers are computed by the shared SDK codecs. No saved model, saved byte span, captured field program or byte patch enters construction.

The child's actual origin feature and its own `DatumTime` still drive the drawing reference. Changing the model-root or history event does not substitute that value into an origin reference. The complete drawing is composed from the fresh child's real model, configuration, headers and file identity.

The experiment deliberately does not alter configuration timestamps, feature FILETIME inputs, system dates, appearance, styles, units or other fresh defaults. Its scope is the three explicitly selected archive/event axes.

## Independent modeled inputs

The [specification](../../tooling/sw2026/EpochExperimentSpec01.json) contains new authored values, not the timestamps from the source observations. The common child creation time is `1760000123`. It declares a Front corner-anchored rectangle, width `0.031729 m`, height `0.023417 m` and blind depth `0.007183 m`. Drawing clocks and presentation are fixed.

| Case | Only changed clock axis | Difference from its separate unchanged-constructor counterpart |
| --- | --- | --- |
| ClockBaseline | None | All child streams and drawing bytes are identical |
| EarlierArchiveTime | Header archive time `ModifiedAt = CreatedAt - 43217` | Child Header2 and model-header streams only |
| EarlierRootEvent | First actual model-root event `CreatedAt - 86413` | Child Header2 and model-header streams only |
| LaterHistoryEvent | First history event `CreatedAt + 259` | Child History stream only |

Every case has its own declared directory. Comparisons are against the unchanged constructor at that same case path, not between different paths. Full drawings are identical to their per-case counterparts. All other child streams and actual origin/geometry owners are unchanged.

The fresh drawing family emits no independent `Contents/CMgrHdr2`. Therefore the executable specification omits the unused drawing-only `ManagerSavedAt` from the earlier frozen proposal. It still models and verifies the child's actual manager-header `f60`. The original proposal is retained by hash; the correction is explicit rather than assigning a fabricated owner.

The experimental modern-time range is narrower than the archive's integer representation. It avoids the native sentinel-year normalization on purpose. It is an experiment precondition, not a newly claimed global format domain.

## Independent process proof

Candidate02's complete source manifest is SHA-256 `7e0b70e7d1cf2933641d99214a9919601f9aabae3f3c8c3246c7668fcd5bfcf2`. It contains 5,047 files: all 5,037 prior frozen source files unchanged, plus nine research Python modules and the modeled input specification.

Root's exact result is SHA-256 `2ba35c5237cd84576e234aaba3bb60d043147b11224b2175ebc8c31d5019a83f`. The [sanitized receipt](../measurements/2026/DrawingSourceEpochConstruction01.json) binds every request, repeated build, preparation, counterpart and generated file.

| Process boundary | Count | Measured result |
| --- | ---: | --- |
| Fresh guarded builds | 8 | Two identical builds per case; zero runtime input reads and no SDK research imports |
| Unchanged-constructor counterparts | 4 | Exact permitted stream differences above; all other bytes and owners unchanged |
| Separate linked typed preparations | 4 | Exact clock inputs in both headers/history, actual self identity, linked maps and origin owners |
| Published constructor refusal probes | 2 | Existing earlier-modification and independent-history refusals preserved |
| Atomic invalid-request processes | 8 | No child or drawing payload returned |

The separate reader parses Header2, model header, CMgr, CMgrHdr2, Config, ResolvedFeatures and History using their actual independent/shared map contexts. It re-emits those typed streams and the drawing Definition/Header2/History for byte identity. It checks the modeled values through decoded field owners rather than borrowing the factory's generated clock report.

A data-only audit rehashed all 5,047 source files, all 78 stdin/stdout/stderr captures and all eight generated artifacts. Its SHA-256 is `d3d29fcfaee51f48bde0a7227d3548b578b2994e3ed4515252f2c07a4f553179`. The worker performed source/static/data checks only; root executed the product processes.

## Retained first failure

Candidate01 remains immutable: source manifest SHA-256 `aa4927bdaf9ea440b5e8fd079f006add32c9141dfd20eba8b2090a3b5ebf13a7`, false result `c5d0a8878986e07844fce9e7c6560e09a4b7939995c4e5558d47b7f7673f8105`. Its first guarded baseline worker rejected `planar mate graph expected text f50`, with zero runtime input reads and before native execution.

The private observer used a plain nonempty datum-name accessor on `moLogs_c.f50`. Fresh header construction stores that field as `CStringValue`; it is distinct from numeric `moHeader_c.f50`. Candidate02 reads only an actual `CStringValue` or decoded `str` for owned log text. It also preserves valid empty stamp comments. No codec, native field, clock value or production guard changed to repair the observer.

See [the text-owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/HeaderLogTextHasItsOwnRepresentation.md).

## Root-run host deck

[EpochPairFlow](../../tooling/sw2026/EpochPairFlow.py) is the frozen source-only controller. Run it from its exact copied source closure with `-I -B`, its manifest hash and a nonexistent output directory. It stores every complete neutral request and every raw process result before preparing any native work.

[PrepareEpochNativeDeck](../../tooling/sw2026/epoch/PrepareEpochNativeDeck.py) requires that exact 26-process result and the frozen host-tools manifest. It rehashes the source closure, captures and generated pairs, copies the nine unchanged ordinary lifecycle tools and known control, and emits a new immutable private packet. It never calls CAD, COM, the VM or a service.

The existing native prediction uses the new neutral dimensions, real driver names, paths, configuration, sheet and view. The prior independently declared default part tree is used only as an oracle expectation after checking the system inputs are unchanged. Those prediction rows never enter a writer or generated archive.

The packet prescribes 18 fresh native processes: leading control, four phases per case, trailing control. It edits the actual boss driver by `+0.001931 m`, moves the view by `[+0.01371, -0.00923] m`, and requires complete trees, live dimensions/relations, analytic solid measures, actual resolved child/configuration and fresh reopen. The original placement-frame prediction and independently projected edited body bounds remain intact.

[InspectEpochClocks](../../tooling/sw2026/epoch/InspectEpochClocks.py) runs on the host only after a completed native batch. It parses the actual immutable inputs and native saved snapshots. It records both header domains, complete root-log events, history events/date-code/provenance fields, self and manager timestamps, and the actual origin event. Native provenance fields are retained as unprojected semantics. Clock changes remain phase-wide observations; the tool does not assert a live setter or helper-mode cause.

## Limits

The controlled batch verifies the three modeled clock variations through native edit, save and fresh reopen. It measures the resulting header, root-log, history, and save times in the archive. Live helper-mode attribution and earlier upstream setters remain open. The original drawings still require complete neutral projection of their metadata, presentation and additional fields.

The CAD stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This research process result does not complete the broader CAD goal.
