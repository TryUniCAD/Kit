# A clean drawing annotation save can bypass the selected child-cache call

The exact two-stop cache trial failed its added observer gate: neither control delivered the selected lookup call. Both controls completed the ordinary note edit, rebuild and save cleanly. The generated lane and trace fresh-reopen phases were not run. The separately passed six-process depth baseline remains valid evidence for its own lifecycle.

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID`; owner `/root/assembly_occurrence`; delivery PR #121. Root owns all VM execution and integration. This work follows the [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [RE playbook](../../Playbook/README.md), and [passed-baseline trace protocol](DrawingDepthBaselineCacheTrace2026.md).

## Actual negative result

The actual cache trial hash is `60e40b3ba1a084959b04ca1a91317915f86074a8455e6d17b63701a73041723d`. Its terminal result hash is `040e859f432f6b0b3999a0e65b74706a4f7d5d9d385fe43a0f17e4196289c468`. The exact baseline result remains `92f51a9a5c5e7c7136b01d7a56d73c840e1a5e81df8f7af4a612ca36aa644401`.

Both trace workers opened with zero errors and warnings, completed ordinary annotation checks, and saved `[true,0,0]`. Both observers armed the original `slduiu+0x13aaed7` stop before SaveAs, received save events `[7,9,28]`, restored the instruction and detached cleanly. Both actual routes are `call_unobserved`; no call or return operand was sampled. The source clock verifier is false because the required source stops are absent, not because a contradictory ordering was measured.

The raw aggregate remains failed, with failed cache-control gates and the generated lane skipped. Its text says the control did not prove the annotation lifecycle, but the more precise interpretation is that the ordinary save passed while the added cache-source requirement did not. This record does not rewrite that aggregate. [Sanitized native negative](../measurements/2026/DrawingEdgeCacheUnobserved01.json)

## Exact native gates before the lookup

The [numeric source record](DrawingPreparationGateSources2026.json) pins three original modules, six complete functions, three instruction windows, four direct calls and five named imports. The existing [source verifier](../../tooling/sw2026/downstream/VerifyLinkedEdgeSources.py) independently reproduced every pin. [Source receipt](../measurements/2026/DrawingPreparationGateSource01.json)

| Stage                | Pinned source condition                                                                                                                                                                                                                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Per-view preparation | `slddrwu!0x3df07aa0` obtains actual SaveModelData, a computed view-eligibility flag, view `f614 &0x40`, and the actual native caller arguments. The next detailing branch at `0x3df07bd4` requires both the computed eligibility and sixth native i32 argument to be nonzero.                              |
| Ordinary bucket      | The path beginning `0x3df07ce6` needs a real bucket, nonnull bucket `+0x10` data, and nonzero data `+0x760`. Its postprocessor call at `0x3df07d7f` additionally requires bucket `f70 &0x200`.                                                                                                             |
| UI postprocessor     | `slduiu!0x4a246400` has its own application-state, view eligibility, SaveModelData and actual bucket predicates before calling `0x4a24aa40`.                                                                                                                                                               |
| Actual edge lookup   | The selected branch obtains the real edge downstream attribute at `0x4a24aeaf`; zero skips the lookup. A separate nonempty local CString guard at `0x4a24aec4` must also pass before `0x4a24aed7`. That string is populated through the actual component map. Its full normalization is not newly claimed. |

These are conditional source rules. The missed call does not identify which condition failed, prove a null cache result, or demonstrate fallback. No UI flag, register, field, or source document is changed to force this path.

## Drawing-owned references remain a separate path

Read-only typed inspection of the two declared original drawing inputs finds one `moAbsoluteView`, native feature ID 11, in each. Both stored `f614` values are 7406852, with bit `0x40` clear. This is stored state, not a substitute for the runtime observation.

The disclosed native control already contains four drawing `f1570` entries, downstream IDs 11 through 14 under component text `generatedchildfile`. The independent generated input has no `f1570` group. Those observed IDs are not writer defaults and do not enter construction.

The existing [resolver record](DownstreamLinkedEdgeResolution2026.md) distinguishes this drawing-owned map from the child's `f380/f60` cache. Ordinary attachment and persistence therefore remain meaningful, but they cannot qualify the selected child-cache consumer. A better persistent-reference proof must bind the actual reference owner and surface representations, not infer cache use from a successful SaveAs.

## Frozen next diagnostic

The new [freezer](../../tooling/sw2026/drawing_edges/FreezeDrawingPreparationGate01.py) prepares three fresh processes from the exact same disclosed control: ordinary control before, one preparation observer, ordinary control after. It preserves the baseline's 24 files and all existing geometry, correspondence, note, persistent-reference, save and cleanup checks. It runs no generated native candidate. Fresh reopen remains the separate prior baseline evidence and is not repeated or claimed by this three-process diagnostic.

The [observer](../../tooling/sw2026/drawing_edges/DrawingPreparationGateTrace01.py) allows one source site only: `slddrwu!0x3df07bce`, RVA `0x347bce`. It samples the actual SaveModelData i32, computed eligibility, view `f614 &0x40`, detail-definition `f224` i32 and sixth native i32 argument immediately before the common branch decision. The semantic name of `f224` and the UI document virtual `+0x1150` remain unbound. The probe does not invent them.

The actual view pointer is RDI and the live source frame is RBP at this exact instruction. The only data reads are four bytes at `view+8` to filter the independently decoded disclosed view ID, and four bytes at `RBP+0x2e8` for that native argument. Other view IDs are counted with a finite limit. The observer reports no raw pointer and makes no vendor call from a stop. It retains the proven exact owned process, AMD64 context, original instruction hash, bounded wait, pre-event-7 check, restoration and detach rules.

The [runner](../../tooling/sw2026/drawing_edges/RunDrawingPreparationGate01.py) reports `diagnostic_completed` separately from `preparation_gate_observed`. A completed diagnostic can legitimately record an unobserved site. An observed false branch gate remains false. Neither outcome is cache acceptance. All results retain `cache_lookup_observed=false`, `generated_native_inputs_run=0` and `native_acceptance=false`.

| Frozen item              | SHA-256                                                            |
| ------------------------ | ------------------------------------------------------------------ |
| Probe trial              | `2af0a40c0f3d0a096cb28c02bc00cd126cb25bafec6ec9733b59e472221e1f94` |
| Native recipe            | `de097cc176a743cd49d2d9895af8ea4389c57b3d409712a2dcbb2075cfc71062` |
| Complete packet manifest | `5b67fe12710767d07ff1a38f204a304577ec927f4c5a555f454413f71d8afc48` |

The recipe uses explicit Windows paths and places the VM name before `--current-user`. Root captures the source before running its verify and run argument arrays. Host verification and static checks pass. No VM, COM, held-out input, shared source, or Hopper target was used by this preparation.
