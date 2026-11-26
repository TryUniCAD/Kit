# Research automation implementation steps

## Status and ownership

Task `A08c-SolidWorksOpenRetry` is active, owned by Codex on `codex/solidworks-open-retry`.
Scope: three bounded startup and part-open attempts, retained failure evidence and separate native stage measurements.
It depends on continuous capture in [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288), alongside its continuous capture dependency.
Exit: native compilation, bounded launch rejection, recovered native startup, measured stages and current-revision CI and review.
See [retry and timing behavior](../../Changes/Research/Supervisor/Catalogue/SolidWorksOpenRetriesAndTiming.md).
At `d36d7d4806`, the injected first startup exit recovered on attempt two, two P03 batches shared the new process, and same-file independent-process measurements matched.
Current-head CI and review remain open; a forced part-open failure was not induced.

Task `A08c-ContinuousSolidWorks` is active, owned by Codex on `codex/solidworks-capture-batching`.
It depends on the shared batch preparation, existing measured readback and the serial native resource.
Scope: persistent capture, document close/reopen verification, independent decoder dispatch and retained owner generations.
Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Exit: consecutive same-process native batches, same-file fresh-process comparison, decoder overlap, recovery checks and current-revision CI and review.
See [continuous SOLIDWORKS capture](../../Changes/Research/Supervisor/Catalogue/ContinuousSolidWorksSession.md).
The `5c3ae3810c` native comparison matched P01/P03/P04 same-file measurements across routine and fresh processes.
The `18d72e23ee` controller run completed four jobs, overlapped decoding with capture and preserved receipts across resume.
Current-head readiness, broader feature qualification and merge-group acceptance remain open.

PR #158 is based on main `5299eb2ffa5c287c93008bd221df6af2c2f9eb5b`. Its follow-on phase commits carry the remaining non-DLL work from the original PR #94 checkpoint `fb723e0a920b4d03ad2d5635882860b800a9b61c`. The entries below record the original programme and its revision-bound evidence. The licensed restart, native qualification, supplemental Fusion handoff, pending CI batch authority and two-week pilot retain their open exit criteria.

This register belongs to the [neutral-first plan](AutomationPlan.md).

## Deterministic encoder work

The user assigned the first two-format encoder milestone to Codex on 2026-11-25.
The delivery is [PR #297](https://github.com/TryUniCAD/Kit/pull/297), branch `codex/deterministic-encoder-roundtrip`.
Three worker chats own the shared pipeline, SOLIDWORKS adapter, and Fusion adapter respectively.
Each worker uses three subagents. Routine encoder jobs keep model advice disabled.
PR #158 is closed. Its retained programme requirements and evidence remain the basis for these child steps.

| ID   | Scope                                                         | Owner                   | Depends on                                    | Status   | Exit condition                                                                                                                                |
| ---- | ------------------------------------------------------------- | ----------------------- | --------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| A11c | Qualified cuboid JSON reconstruction and extrusion-depth edit | Codex Fusion worker     | A05, A06, qualified public Fusion writer, A14 | checking | Generated candidates pass deterministic process checks and independent native open, edit, rebuild, save, and reopen measurements.             |
| A12a | Bounded line-loop boss JSON reconstruction and depth edit     | Codex SOLIDWORKS worker | A04, A06, measured part writer, A14           | checking | Held-out candidates pass native measurements and the public SDK publishes bytes bound to a valid exact-build receipt.                         |
| A13a | Shared encoder jobs and receipt handling                      | Codex shared worker     | A03, A11c, A12a, A14                          | checking | The existing research CLI generates both formats, preserves evidence through retries, and distinguishes generation from native qualification. |

The SOLIDWORKS starting scope is a qualified cold part or supported authored graph.
Ordinary vendor partition layouts still need reader semantics before they can enter this path.
The [measured SOLIDWORKS build extension](../../Changes/Solidworks/Construction/SolidworksEncoderOracleBuild.md) qualifies exact build `34.4.1.1011` alongside `34.5.2.0604`.
Four candidates passed twenty owned process lifetimes and 616 numeric comparisons on the observed SP04.1 executable.
Eight SDK publications reproduced those measured archives through the registry and direct writer.
Fusion measurements target the observed installed build `2706.1.17`.
Native execution, output acceptance, public publication, PR checks, and merge-queue acceptance each retain their own evidence.

### A13a-FusionPreparedInputs: per-role Fusion writer input replay

The Codex shared encoder worker owns this checking task on `codex/fusion-prepared-encoder-inputs`.
Delivery is [PR #305](https://github.com/TryUniCAD/Kit/pull/305), based on the [encoder round-trip branch in PR #297](https://github.com/TryUniCAD/Kit/pull/297).
The task depends on A11c's constrained constructor and A13a's schema 2 artifact and receipt checks.
The exit requires source-free process replay of exact measured candidate bytes and continued acceptance of earlier schema 1 evidence.
Unsupported and changed source states must still be refused. A05c saved-source generation remains separate.

The Fusion worker owns the vendor-resaved constrained cuboid reader in [PR #299](https://github.com/TryUniCAD/Kit/pull/299).
[PR #303](https://github.com/TryUniCAD/Kit/pull/303) records the same-source writer research and native measurements. Independent archive-free generation and complete acceptance remain open.
The SOLIDWORKS worker owns vendor-authored blind boss work under A12b. [PR #300](https://github.com/TryUniCAD/Kit/pull/300) records reader and custody evidence.
[PR #304](https://github.com/TryUniCAD/Kit/pull/304) records the single Top annotation research generator and fresh native observations for its exact output.
Broader source-family admission and measured public writer acceptance remain open.

## Programme status

A01 is complete as a source-backed contract and capability audit.
**Current work: A02d capture evidence, A04c/A05 semantic qualification, A06 comparison implementation, A08c/A08e workers and A14b regression evidence.**
A05a reader integration and A08a supervisor process gates passed at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
A05 includes fresh licensed observations for the four circular controls and the scoped packaged reader. Editable target acceptance remains open.
The original deterministic work was coordinated in dependency order on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
A04a–A04b and A03e are verified at code checkpoint `eba0ab488a6a00e2a31fd5ed8ab0bee564b371db`.
The work is published on the shared PR head.
A02's corpus tooling and paired specifications are complete; independent capture qualification remains blocked.
Claim subsequent runnable child steps explicitly.
Model execution and policy exceptions retain the approvals described in the plan.
Read the [A01 decision and evidence](NeutralContractAudit.md) before claiming subsequent authorized work.

Keep identifiers stable when splitting work or revising estimates.
Use suffixes for new child steps and retain the parent identifier.
Each contributor claims a step through a PR comment before starting authorized work.
Record the owner, task branch, dependencies and current revision.
Check existing claims before claiming overlapping work.
Coordinate shared files explicitly and preserve other contributors' changes.

The document is the durable register.
It is the only maintained record of step status.
Other pages link here instead of repeating status.
PR comments provide the event history and evidence links.
Update the owner and status cells when an accepted documentation change records a new claim or disposition.
The controller's SQLite ledger is a separate runtime artifact.

Statuses are `planned`, `active`, `blocked`, `checking` and `complete`.
Use `complete` only after the row's exit criterion has matching evidence.
A local patch, model answer or posted review request does not establish completion.
If work pauses or changes owner, post a handoff with remaining tasks.

## Step register

### PR 158 implementation follow-up

#### A08b-CatalogueThroughput: catalogue rescan groups and A03 overhead

Codex owns this checking task on [PR #282](https://github.com/TryUniCAD/Kit/pull/282) from `14570404846c8aa1f90b02e68d6f70a419719ca7`.
Dependencies are A03 owner and lease fencing, A08b grouped sessions and the pinned offline calibration.
The scope covers the fresh catalogue rescan cap, grouped staging renewal and grouped settlement lease checks.
Exit requires matched calibration, equal per-archive output hashes, and coverage of grouped receipts, restart recovery and singleton retries.
The Windows sweep and candidate replay accepted the same 64 archives once per arm with equal neutral hashes.
The candidate cap-eight arm removed eight heartbeat calls, with higher total wall time in the replay.
The short physical probe reached six simultaneous readers and did not sustain the requested overlaps.
The matched P03 catalogue replay changed two groups of four into one group of eight and retained equal neutral outputs and job results.
See [catalogue rescan throughput](../../Changes/Research/Supervisor/Catalogue/CatalogueRescanThroughput.md) for revisions, timings and limits.

#### A04-PlanePlacement: timestamp-independent principal references

Codex owns this reader repair on `codex/solidworks-plane-placement`, based on main `9e2049c73028b8f4d00d142a35a3fb42f1c23b92`.
Delivery is [PR #270](https://github.com/TryUniCAD/Kit/pull/270), authorized for publication on 2026-11-23.
Dependencies are the native ladder inputs and measured source observations from merged PRs #263 and #267.
The [change entry](../../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) records the original offline evidence for 144 files, 288 public-reader comparisons, 24 timestamp variants, ten principal-pose refusals, and nine explicitly unqualified fallbacks.
All captured centroids agree; the 58 older pinned part documents retain identical serialized output.
Review found that accepted in-plane rotation was lost at the neutral datum reference. The owned-sketch reader now explicitly refuses that unsupported rotation.
Origin owner lookup retains its existing unavailable-owner fallback. A scoped process witness checks this boundary without changing a captured archive.
The circular and rectangle attachment corruption cases now require the documented format error in both public read modes.
Status is checking. Fresh revision-bound CI, review, source-audit and merge-group evidence must cover these follow-ups before completion.
The exit covers source placement and its shared-suite process regressions.
Fresh native acceptance, complete typed rectangle admission, and conversion qualification remain outside this result.

#### A08b-SharedQueue: shared research requests and advice budgets

Codex owns this checking task on `codex/shared-research-queue`; delivery is [PR #272](https://github.com/TryUniCAD/Kit/pull/272).
Dependencies are the A03 controller, A07 scheduling, A08 supervisor pools and the existing optional advisor integration.
The scope is local shared request deduplication, subscriber-aware supersession, bounded priority queues and shared advisor admission.
Independent instances explicitly select the same local controller store and advisor state; one supervisor owns the controller store.
The exit requires real process-boundary concurrency, cancellation, recovery and provider-budget evidence, plus current-head PR checks and configured review.
Six real-process queue scenarios and five disposable-provider advice groups passed locally with Python 3.14.7. The source and verification details are in the [change entry](../../Changes/Research/Supervisor/Coordination/SharedResearchScheduling.md).
No CAD capability, native acceptance flag or production conversion route changes.

#### A05-RectangleRecovery: bounded reader qualification

Codex owns this active follow-up on `fix/native-rectangle-qualification-20261122`, based on main `7a0a987ec2f1ab4099c839621a8e51d18bcfa872`.
Delivery PR is [#265](https://github.com/TryUniCAD/Kit/pull/265); current-head CI and configured review are pending. Queue candidate `06b002441448d2e961629215cdc09768ea8b1530` was rejected for the combined policy/native deadline after its subprocess tests passed. The [scheduling repair](../../Changes/Ci/NativeCompatibilityScheduling.md) shards the complete roster with the user-authorized twelve-minute buffer; fresh queue acceptance remains required. Dependencies are merged PR #263, the strict reader, and licensed native workers.
Scope is unconstrained millimeter XY reverse and positive YZ rectangle evidence, plus native worker recovery investigation.
Fresh constrained controls and separately authored unconstrained controls distinguish authoring deficiencies from unsupported reader grammar.
The exit requires strict CLI replay, native numerical comparisons, retained negative cases, shared-suite integration, and current-head CI and review.
This child does not close conversion acceptance, XZ or reverse-YZ support, or the full native catalogue.

#### A08h-LadderRecovery: recovered native corpus

Codex published this evidence on `feat/solidworks-ladder-recovery-20261122`, based on fresh main `5b9f330282e5c3a3a41b3f04bf9ab7f02d2da538`.
Delivery PR [#267](https://github.com/TryUniCAD/Kit/pull/267) merged as `b9b9430ac3ce09afb171183cfc778878be90bfdb`. Dependencies are merged PR #263, the existing research controller and licensed source captures.
The [package](../../../re/solidworks/FeatureLadderRecovery/README.md) retains 37 complete native cases and 111 strict decodes, plus two failed-batch salvage files.
Original controller failures remain recorded. The archived reports retain fifteen matching front-plane centroids and 96 wrong top/right placements.
The exit requires verified artifact hashes, sanitized provenance, explicit semantic failures and current-head publication checks and review.
The separately verified A04-PlanePlacement repair above preserves those historical reports; this evidence does not close conversion acceptance.

#### A08h-Ladders2026: native campaign evidence

Codex owns this scoped research-evidence follow-up on `feat/deterministic-campaign-20261122`.
Delivery PR: [#263](https://github.com/TryUniCAD/Kit/pull/263). Dependencies are merged PR #158, merged PR #207, and licensed native API workers.
The [package](../../../re/FeatureLadders2026/README.md) records 96 planned batches at `c8d85d713dc357770115329e9f1bcb027dbfca4f`.
Fifty-nine batches produced 177 files; 57 strictly projected to neutral documents and 120 retained explicit neutral refusals.
All 120 refused Fusion files parsed at the typed native-state layer. Thirty-seven SOLIDWORKS cases failed or remained dispatch-blocked.
Status: checking for publication; native recovery and semantic qualification remain blocked.
The packaging exit requires verified corpus hashes, sanitized evidence, documented failures, and current-head PR readiness.
This child does not close A07, A08c, A13, A15, B02, B03 or any supported production boundary.
Production reader repairs require a separately scoped follow-up with independently corroborated rules and held-out evidence.

A08h is checking on [PR #207](https://github.com/TryUniCAD/Kit/pull/207), branch
`codex/catalogue-native-authoring`, owned by Codex. It
connects catalogue selection to the existing native builders with parameter
overrides and automatic downstream decoding. One complete configured P03 run
created eight native archives, verified them in fresh processes, and automatically
completed the dependent deterministic decoder job. Its 53 findings per sample
remain explicit. Dependencies are A03/A08 worker
ownership, the P01–P05 builders, and the catalogue/resume implementation. Its
remaining native and process acceptance is recorded in
[catalogue sample authoring](../../Changes/Research/Supervisor/Catalogue/CatalogueSampleAuthoring.md).
This child does not close A07 inference, A13 conversion acceptance, or A15 pilot
requirements.

#### A08h-OwnedExit: catalogue capture shutdown

Codex owns the shutdown repair on `codex/solidworks-capture-shutdown`.
Delivery is [PR #289](https://github.com/TryUniCAD/Kit/pull/289).
It depends on PR #207's configured native worker,
the licensed SOLIDWORKS host and its exclusive application lease. [PR #288](https://github.com/TryUniCAD/Kit/pull/288)
owns the separate paired-case batching work. Exit requires normal owned process
exit, independent reopen and recorded decoder results for the failed P04 cases,
plus batch and control coverage and the applicable CI and review gates.
All six previously failed cut-extrude cases passed capture, reopen and
decoder execution across the exact and paired replays. The written-recipe
replay completed both native process exits and reached a separate thin-wall
geometry check. PR #291 recovered all three written recipes. The standalone
driving-dimension case passed after a retry. The combined probe verified
both phases on the first attempt after adding the empty-session exit request.
The final combined batch worker reproduced two shutdown timeouts and
recovered on the third fresh attempt with six reopened archives and a
completed decoder job. The applicable PR and queue gates remain separate.
[Change entry](../../Changes/Research/Supervisor/Catalogue/SolidWorksCaptureShutdown.md)

#### A08h-CaseIsolation

Codex owns the consolidated SOLIDWORKS repair and case isolation on
`codex/solidworks-capture-resilience`. It depends on the catalogue worker
and artifact intake from PR #207. Delivery combines the changes from PRs
#289 and #291. Exit requires proven shutdown recovery, held-out thin-wall
measurements, and a process check showing that a refused case cannot block
or supply evidence to a healthy sibling decoder.
[Delivery PR #292](https://github.com/TryUniCAD/Kit/pull/292)
[Change entry](../../Changes/Research/Supervisor/Catalogue/SolidWorksBatchRejectionIsolation.md)

A08i uses branch `codex/reusable-feature-builders`. The user authorized source-only
publication with A08j/A08k on [PR #207](https://github.com/TryUniCAD/Kit/pull/207)
on 2026-11-21. The bounded offset-start run at `7a868f5e` passed native creation,
edits, restoration and fresh reopen, then automatically completed its decoder job
with unresolved findings. One of the nine new bindings is native verified; full
decoder qualification remains incomplete. The focused process checks passed 103 cases.
See [reusable recipe builders](../../Changes/Research/Supervisor/Catalogue/ReusableRecipeBuilders.md)
for the nine bindings, parameter grid, retained attempts, and execution limits.

Task `A08h-PairedBatch` is owned by Codex on `codex/solidworks-capture-batching`.
It extends the existing three-case native batches to P01–P05, preserving independent reopen verification and per-case decoder artifacts.
Dependencies are A08h/A08i, owned native lifetimes, and controller artifact admission.
Native verification passed on source `231ffae38c7a9ca83705c6705e7d382d05c1e208`. Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
The measured P01/P03/P04 batch reused two application processes for 25 saved files and automatically completed three overlapping decoder jobs.
Both native processes exited normally. Decoder semantic findings remain explicit.
Current-head publication checks and configured review are tracked in the delivery PR.
Exit requires measured native batching, automatic decoder receipts, and current-revision CI and configured review.
Saved plans retain their original submissions. Full decoding and conversion qualification remain separate requirements.
See [paired-case batching](../../Changes/Research/Supervisor/Catalogue/PairedCaseBatching.md).

#### A08i-ThinWall

Codex owns the correction on `codex/solidworks-thin-wall-side`. The
correction depends on the written-recipe worker from PR #207 and the
licensed SOLIDWORKS measurement host. Its exit requires matching wall side
with XY, YZ and XZ controls, edits, independent reopen and downstream
decoder receipts plus the applicable publication gates. The combined native
replay passed all three written recipes and ran the three dependent decoders.
[Thin-wall change entry](../../Changes/Research/Supervisor/Catalogue/SolidWorksThinWallSide.md)
[Delivery PR #291](https://github.com/TryUniCAD/Kit/pull/291)

A08j, owned by Codex on the same local branch, is checking the
[written recipe campaign](../../Changes/Research/Supervisor/Catalogue/WrittenRecipeCampaign.md).
It depends on A08h/A08i and drives every written recipe through the existing
runner with a persistent assistant handoff for missing mappings and failures.
Its workflow checks cover the complete selected written roster, restart and
rejection of unsupported assistant completion claims. Native recipe coverage and
full decoder qualification remain separate exit criteria.

A08k's bounded first delivery is complete on local branch `codex/automatic-builder-development`, owned by
Codex, with dependencies A08h/A08i/A08j and the existing provider/native ownership
contracts. The [automatic builder-development loop](../../Changes/Research/Supervisor/Catalogue/AutomaticBuilderDevelopment.md)
implements opt-in generation, bounded repair, independently reserved qualification,
immutable runtime registration and dependent capture/decoding for the scoped positive
XY offset plane. At frozen source `d61c3be4`, an actual two-call loop repaired an
injected distance defect, rejected a wrong-support plane, passed three reserved
cases, registered its source and accepted a separate sample. The dependent decoder
ran deterministically with 55 unresolved findings per archive; conversion remains
unqualified. Eighteen new and two unchanged campaign process checks pass. This work
does not close decoder, conversion or Fusion qualification. On 2026-11-21 the user
authorized publishing the source changes to [PR #207](https://github.com/TryUniCAD/Kit/pull/207),
head `codex/catalogue-native-authoring`. The isolated implementation branch and all
private native evidence are preserved. Vendor binaries and native capture archives
remain excluded from publication.

The user assigned SOLIDWORKS and CAD-independent implementation to Codex on 2026-11-17.
Delivery remains on [PR #158](https://github.com/TryUniCAD/Kit/pull/158), from isolated branch `codex/pr158-solidworks-completion`.
The starting source revision is `a6cc279f629d088c526a654149bb9dc99a8b2bb6`.

| Child ID | Owner | Scope                                                                                   | Depends on                                             | Status   | Exit condition                                                                                                                                                            |
| -------- | ----- | --------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A07d     | Codex | Bind every inference execution to its normalized job, inputs and dependency fingerprint | A03 session contract and existing A07 process coverage | complete | Actual runner processes reject changed session identities and malformed evidence while valid controller sessions retain their existing outcomes                           |
| A08f     | Codex | Queue the existing P02 circular SOLIDWORKS readback and pin ownership helpers           | Existing P02 collector, A03 and A08e                   | complete | Queue, timeout recovery and source-integrity process checks pass. The licensed queue accepted all five P02 observations with healthy controls                             |
| A08g     | Codex | Fence supervised Windows worker entry after durable session publication                 | A03 ownership and leases, A08a                         | complete | Real worker processes enter only after metadata publication and current-owner lease validation, including grouped claims and startup failure cleanup                      |
| A08i     | Codex | Reusable builders for nine named SOLIDWORKS catalogue recipes                           | PR #207 catalogue authoring and A03/A08 ownership      | checking | Source-pinned native creation, edits, fresh reopen, healthy controls, and dependent decoder receipts demonstrate each claimed binding without hiding unresolved semantics |

Commit [`c572f1ac`](https://github.com/TryUniCAD/Kit/commit/c572f1ac8dfa613e8ff6bf9ea99e2be375deb63c) passed 63 combined inference, Windows launch, readback, and rearm process checks.
The [inference session change](../../Changes/Research/Controller/InferenceSessionIntegrity.md) also records a passing historical archive gate.
The [Windows launch change](../../Changes/Research/Supervisor/WindowsLaunchAuthorization.md) records the 18-case Windows regression.
The [native progress record](../../Changes/Research/Workers/SolidWorks/NativeReadbackProgress.md) identifies the pending SOLIDWORKS control close.
The [session lifetime change](../../Changes/Research/Workers/SolidWorks/OwnedReadbackLifetime.md) records the trace, recovery and subsequent owned-session checks.
At [`ee53cf7`](https://github.com/TryUniCAD/Kit/commit/ee53cf759f08a1f5608311fea0447e97a4a681fa), SOLIDWORKS accepted five P02 and 14 P01/P03 readbacks.
Both healthy controls matched in each run, each owned process exited normally, and both acceptance fences cleared.
P04 timed out in the final control close after all 11 capture calls and retained zero accepted observations.
The [original-order P04 rerun](../../Changes/Research/Workers/SolidWorks/FinalControlVisibility.md#original-order-queued-confirmation) then accepted all 11 captures and both controls at `9fc3c9a2`, with normal owned exit and acknowledgement.

The A04d [standalone circle reader](../../Changes/Research/Readers/SolidWorks/StandaloneCircleSketch.md) matched five pinned P02 controls through the public SDK.
The change preserves the driving diameter, Origin coincidence and principal support while reporting zero bodies for the proved sketch-only history.
A12 now has an optional [constructive VisualStates member](../../Changes/Research/Writers/SolidWorks/Metadata/SolidWorksConstructiveVisualState.md) for research packages.
Eight saved members reconstructed exactly, and a separately authored state passed offline package checks.
The integrated reader and writer research passed 80 focused checks.
The [native Student-context Boss witness](../../Changes/Research/Writers/SolidWorks/Metadata/NativeStudentBossWitness.md) confirms one independently generated rectangular Boss opened, accepted three live dimension edits and restorations, saved, and rebuilt in a fresh process.
The saved display-state name and feature visibility persisted. The default appearance reset to gray, and qualified public writer acceptance remains open.
The [explicit appearance work](../../Changes/Research/Writers/SolidWorks/Metadata/SolidWorksConstructiveVisualState.md#explicit-document-appearance) adds source-free document RGB and strict readback of the observed native saved locator across all three appearance owners. Both saved colors persisted through fresh read-only reopen and normal owned exit. The earlier writable-session exit failures remain recorded.

The registered SOLIDWORKS application points to build `34.4.1.1011`, matching the retained native readback.
A separate older installation reports build `33.0.0.5050`.
Native execution must use the registered matching installation and preserve unrelated sessions.
Independent source admission, qualified graph pairs, complete native writing, bidirectional acceptance and the two-week pilot retain their existing exit conditions.

| ID  | Deliverable                                            | Depends on                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------ | ------------------------------------ | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Neutral contract and capability audit                  | None                                 | jdharcourt | complete | Existing fields, demonstrated gaps, version scope and independent acceptance requirements documented                                                                                                                               |
| A02 | Pinned corpus and paired authoring specifications      | A01                                  | jdharcourt | blocked  | Hashed inputs, actual measurements, missing dependencies and independent holdout families recorded                                                                                                                                 |
| A03 | Durable evidence store and job controller              | A01                                  | jdharcourt | complete | Transactional jobs, dependency invalidation, leases, bounded retries and interruption recovery verified remotely                                                                                                                   |
| A04 | SOLIDWORKS → neutral reader integration                | A01, A02a                            | jdharcourt | active   | Initial sketches and feature variants preserve required semantics and report unresolved records accurately                                                                                                                         |
| A05 | Fusion → neutral reader integration                    | A01, A02a                            | Stephen316 | active   | Equivalent initial designs serialize through the same contract with independently supported meaning                                                                                                                                |
| A06 | Semantic graph comparison                              | A02c, A04, A05                       | jdharcourt | active   | Equal, intentionally different and ambiguous paired cases report correctly without broad identity masking                                                                                                                          |
| A07 | Bounded deterministic inference and priority scheduler | A03, A06                             | Codex A07  | blocked  | Real shared gaps yield traceable hypotheses, counterexamples and affected-file rescans without models                                                                                                                              |
| A08 | Controlled sample and trace workers                    | A02b, A03                            | jdharcourt | active   | Exact recipes and versioned receipts work with healthy controls; absent workers block only dependent jobs                                                                                                                          |
| A09 | Scoped field maps and typed codec candidates           | A07                                  | Unassigned | blocked  | Solved pad-then-pad family is reproduced without model calls, with independent proof and zero donor blocks                                                                                                                         |
| A10 | Optional model investigation packets                   | A08a, A07, A09                       | Unassigned | planned  | Models-off operation, fixed two-step escalation, a failure log, repeat-failure start-step routing, validated responses, cost limits and false-proposal rejection verified                                                          |
| A11 | Portable neutral → Fusion writer                       | A01, A06, A09                        | jdharcourt | blocked  | Qualified portable graphs generate native files without source replay, proprietary runtime or opaque replacements                                                                                                                  |
| A12 | Portable neutral → SOLIDWORKS writer                   | A01, A06, A09                        | Codex      | blocked  | Qualified portable graphs generate native files from understood fields and reject unsupported required semantics                                                                                                                   |
| A13 | Bidirectional native acceptance                        | A04, A05, A08, A11, A12              | Unassigned | planned  | Both routes match body count, volume, center of mass and feature history, preserve all required constraints/dependencies, and pass independent driving-parameter edits, restoration, rebuild and save/reopen with healthy controls |
| A13-P03AdmissionMatrix | Evidence for the first public writer admission prerequisites on the exact archived P03 pair | A04c, A05c, A06d, A11b, A12b and prior A13 route preflight | Shared encoder worker | checking | [PR #335](https://github.com/TryUniCAD/Kit/pull/335) from `codex/p03-public-admission-matrix`. Repeat the two installed public routes on exact source pins. Record the first refusal, full SOLIDWORKS native and unresolved reader inventory, typed Fusion material ownership, and source-measured evidence with distinct owner responsibilities. The [pinned admission matrix](../../Changes/Research/Readers/Comparison/PinnedPublicAdmission.md) records both current refusals, every native definition and the measured changes with the paired handoff. No widened writer admission or native acceptance. |
| A13-P03FusionBossRequest | Persist and replay the P03 sketch and Boss request through the existing Fusion research writer | A13-P03AdmissionMatrix, A06d-P03DirectionOwner, A11b, [PR #121](https://github.com/TryUniCAD/Kit/pull/121) reader `c0a401a607` and [PR #325](https://github.com/TryUniCAD/Kit/pull/325) request `e0bd3718c6` | Shared encoder worker | checking | Branch `codex/p03-fusion-boss-request` from [PR #335](https://github.com/TryUniCAD/Kit/pull/335) `3990a5e369`. The [delivery PR #339](https://github.com/TryUniCAD/Kit/pull/339) is open. The [claim](https://github.com/TryUniCAD/Kit/pull/335#issuecomment-7183095207) records the agreed Fusion research file ownership. Reuse the [Origin-aware source Boss probe](../../Changes/Research/Readers/Comparison/FusionSourceBossProbe.md) and its independent source capture. Bind the exact source Origin owner and span, Front support, corner aliases and seven ordered saved relations. Verify distinct target argument and observer roles through strict readback. Two fresh source-absent processes must produce identical candidates. A changed source, owner, span, operand order or missing Origin must refuse before output. Record the reversed height operands and the Join and Create difference. The [verified replay](../../Changes/Research/Readers/Comparison/FusionBossRequestReplay.md) reproduces the candidate and returns a read-only document in the unchanged public reader. Full source and native acceptance remain open. |
| A13-P03FusionNativePlan | Prepare a sealed licensed verification plan for the exact generated P03 Fusion Boss | A13-P03FusionBossRequest, [PR #339](https://github.com/TryUniCAD/Kit/pull/339) `97620392e7`, existing P03 Fusion witness, source reopen and healthy Fusion control | Shared encoder worker | checking | Branch `codex/p03-fusion-native-plan`. The [delivery PR #342](https://github.com/TryUniCAD/Kit/pull/342) is open. The [claim](https://github.com/TryUniCAD/Kit/pull/339#issuecomment-7183845750) records the agreed scope. Reuse the existing witness and plan preparation. Bind the input archive, replay report, original request, source witness, checked helper bytes, SDK fingerprints and loaded control to exact digests. Repeat full strict public and typed owner readback. Seal the same two-phase launch contract without executing it. Non-macOS plans remain offline only. The existing native entry checks the sealed host and absolute paths before loading helpers. Reject changed input or pre-existing output. Legacy plans and receipt checks stay available. The [verified offline plan](../../Changes/Research/Readers/Comparison/FusionBossNativePlan.md) retains the exact inputs and refuses changed custody. Native execution, full source preservation and writer qualification remain open. |
| A14 | Independent remote compatibility and regression gates  | A03; A06 for reader and writer gates | jdharcourt | active   | Exact-revision checks reject stale receipts, shared-reader/writer mistakes and unsupported input through real boundaries                                                                                                           |
| A15 | Unattended operation, reports and forecast pilot       | A07, A08b, A14; A10 when enabled     | Unassigned | planned  | Two-week operating evidence records recovery, no-progress parking, blockers and verified documents unlocked. Record model spend when enabled                                                                                       |
| A16 | Broader features and additional CAD families           | A13, A15                             | jdharcourt | blocked  | Each scoped feature/version/route has independent native acceptance; FreeCAD and CATIA use the same contract                                                                                                                       |

A04 and A05 start on the pinned corpus from A02a.
Paired captures from A02c gate paired comparison and native acceptance, not reader integration.
A08 needs the paired recipes from A02b, not the captures that it produces.
A14 starts its controller and corpus gates after A03; its reader and writer gates wait for A06.
A14 is developed alongside the steps it checks.
The [archive steering repair](../../Changes/Research/Readers/Policy/ArchiveSteeringRepair.md) addresses three source violations observed at `7f65ede9`.
Its current-revision hosted verification remains separate from the older checkpoints below.
Any dependent step requiring verification must wait for its applicable gates.
A08 can wait for application access while saved-file research continues.
A10 remains optional and never blocks deterministic operation.
A13 requires actual application evidence and cannot pass in offline-only mode.
A16 is an expansion milestone, not a promise of universal support.

A07's [deterministic inference and queue implementation](../../Changes/Research/Controller/DeterministicInference.md)
passed [hosted process verification](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/job/132964230460)
on saved discovery archives at `ebe6130c`. Qualified A06 paired evidence
remains required for full acceptance.

## A02 implementation and remaining evidence

Shared PR head: `Stephen316/Kit:docs/automation-plan` on PR #94.
A02 source checkpoint: `93bbf684c323e28176f7bb329ab04b092e097b37`, consolidated into this PR with its implementation history preserved.
The corpus pins main `74a0bc353421c25f7a6c539897baadf593a05766`.
PR #94 records the original A01–A16 delivery and associated evidence.

| Child ID | Deliverable                                                 | Status   | Evidence or remaining requirement                                                                                                                                                                                                                                                                                                                                                    |
| -------- | ----------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A02a     | Hashed native inputs and historical evidence index          | complete | 778 native files, 232 JSON evidence files and two historical notes pinned; remote corpus verification passed at `0dd47cda`                                                                                                                                                                                                                                                           |
| A02b     | Five paired recipes and controlled-variation specifications | complete | Explicit parameters, frames, constraints, edits, analytic expectations, tolerances and reserved family splits; source review and digest checks passed                                                                                                                                                                                                                                |
| A02c     | Independently authored and measured native pairs            | complete | Fusion and SOLIDWORKS captures for P01–P05 recorded. The [SOLIDWORKS capture entry](../../Changes/Research/SolidWorksPairedCaptures.md) links the native files, application build, controls, and edit, rebuild, and reopen evidence                                                                                                                                                  |
| A02d     | Independent qualification and holdout ancestry              | blocked  | The lineage audit verifies 74 files and ten receipts. Licensed SOLIDWORKS readback includes P01, P03 and P04 plus all five [P02 diameter bindings](../../Changes/Research/Workers/SolidWorks/CircleBindingReadback.md). Licensed Fusion P01–P04 was reported on PR #94. Admission of the independent evidence and frozen-rule evaluation remain open. P05 stays reserved for holdout |

Historical measurements retain their original values and failures.
Relative filenames do not establish capture-time hash bindings.
Analytic expectations are labelled separately from observed values.
Zero native pairs are currently qualified; no conversion capability is claimed.
A02 evidence does not establish completion of later steps.
The A02 owner [reserved the supplemental baseline](../../Changes/Research/Controller/SupplementalEvidenceBaseline.md) at `f8a4dc7686dece8d44719b12721105a63864a365` on 2026-11-16.
This new reservation follows existing discovery observations and does not assert an earlier freeze.
Private verifier admission, the complete qualification protocol and P05 holdout evaluation remain separate.
The [sealed public-chain preflight](../../Changes/Research/Controller/PairedEvidenceManifest.md#verification-evidence) was subsequently reported at that exact reserved checkout: all three SOLIDWORKS lanes replayed their raw originals, while Fusion source handoff remained unavailable.
It exited `2`, retained `qualification: not_evaluated` and admitted zero pairs.
The [remote workflow-quality job](https://github.com/TryUniCAD/Kit/actions/runs/43419522392/job/131865721189) passed pinned-object verification and all three process cases at `0dd47cdab9d51d24b87acae61ffb1f174ba44d81`.
That observation completes the A02a–A02b artifact criteria. The A02d audit verified the committed capture bytes and found no exact-byte aliases in the audited tree or the pinned historical corpus.

## A03 implementation and verification

Task branch: `feat/a03-durable-research-controller-20261113`; publication remains on this PR's shared `docs/automation-plan` head.
A03 depends on completed A01, so it can proceed while A02c–A02d wait for captures.
The [controller guide](ResearchController.md) records the implemented protocol and limits.

| Child ID | Deliverable                                             | Status   | Remaining evidence                                                                                            |
| -------- | ------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| A03a     | SQLite metadata and immutable hashed artifacts          | complete | Remote persistence, integrity, rollback and schema-upgrade checks passed at `6a846c7d`                        |
| A03b     | Dependency fingerprints and transitive invalidation     | complete | Remote reuse, changed inputs/rules, cycle checks and incremental large-queue execution passed                 |
| A03c     | Claims, leases, bounded retries and exclusive resources | complete | Remote concurrency, interruption recovery, waits, backoff, fencing and resource recovery passed               |
| A03d     | Controller workflow and maintained usage information    | complete | Process workflow and configured approval passed at `eba0ab48`; current PR readiness remains separate          |
| A03e     | Metadata-only lease renewal                             | complete | Twelve controller process scenarios passed at `eba0ab48`, including a 64 MiB payload and corruption rejection |

A03e is the review repair owned by jdharcourt on PR #94.
It removes artifact-content reads from heartbeat renewal while retaining token, deadline and prerequisite checks.
Claims, result submission, status and artifact access retain integrity checks.
The 64 MiB process scenario passed remotely without a schema change.
See [the change entry](../../Changes/Research/MetadataOnlyLeaseRenewal.md).

**A03 design decision:** adopt standard-library SQLite metadata and SHA-256 files in the existing `re/automation/` tree.
Use a local rollback journal, explicit write transactions and full synchronization; do not introduce a second case-variant research directory.
Worker result submission uses the controller protocol, not direct database writes.
No model, CAD worker launcher, decoder integration or neutral schema change is added by this step.
The [remote controller verification job](https://github.com/TryUniCAD/Kit/actions/runs/43427628978/job/131892879264) passed all eleven process scenarios on Python 3.14 at `6a846c7d1a6e144cf04a7c30e32261c7be84ea68`.
Coverage includes 250 completed steps in a 10,000-job chain, 300 individual submissions and schema upgrades, as well as the lifecycle/integrity scenarios.
All verified review findings on that code revision are addressed and its threads are resolved.
The earlier approval was dismissed.
At `eba0ab48`, all 26 displayed checks passed and configured review `5894929093` was `APPROVED` for that exact head.
The [updated workflow-quality job](https://github.com/TryUniCAD/Kit/actions/runs/43467308910/job/132029763989) passed twelve controller scenarios in 71.61 seconds.
All configured findings were resolved.
GitHub separately reported `REVIEW_REQUIRED` under its enforced review rules despite that configured approval.
Current-head PR readiness and deferred merge-group acceptance remain separate from the completed artifact scope recorded here.

## A04 integration and semantic qualification

| Child ID | Deliverable                                          | Depends on                              | Owner      | Status   | Exit criterion or remaining evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------- | ---------------------------------------------------- | --------------------------------------- | ---------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A04a     | Pinned SLDPRT reader and typed neutral serialization | A01, A02a                               | jdharcourt | complete | All 58 pinned parts decoded/reconstructed; strict per-asset success, overwrite and tamper checks passed at `eba0ab48`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| A04b     | Separate field-path evidence and unresolved census   | A04a                                    | jdharcourt | complete | Remote receipts at `eba0ab48` retain native-only content, bytes, codes, diagnostics and unqualified direction/frame mappings                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| A04c     | Initial profile and variant semantic qualification   | A04a, A04b; independent source evidence | jdharcourt | active   | The [P04 sketch reader](../../Changes/Research/Readers/SolidWorksSketchGeometry.md) matches 66 dimensions, 88 axis bindings and eleven coincidences. The [P04 list replay](../../Changes/Research/Readers/SolidWorksResolvedEntry.md) verifies the cap, termination and depth. The [P01/P03 replay](../../Changes/Research/Readers/SolidWorksRectangularPlaneEvidence.md) verifies both YZ supports, signed boss geometry and the ordered operands of 28 dimensions, 56 line-axis relations and fourteen coincidences. The [public reader](../../Changes/Research/Readers/SolidWorksPublicSketchSupport.md) resolves ordinary P01/P03 placement from the saved typed support. The P03 boss reader retains the exact profile, direction and depth source, including the 10 mm depth on the inch-display capture. The public rectangle reader retains [saved axis relations and origin coincidence](../../Changes/Research/Readers/SolidWorksPublicSketchGeometry.md). The ordinary P04 reader follows the [saved centering dependency slots](../../Changes/Research/Readers/SolidWorksCutCentering.md) to both resolved sketch owners. The [P04 outer rectangle and Boss](../../Changes/Research/Readers/SolidWorks/SolidWorksOuterRectangle.md) retain the two source streams and the authored dimensions. The [public cut record](../../Changes/Research/Readers/SolidWorks/SolidWorksCutOperation.md) preserves the resolved target and termination. The [cut perimeter and saved face](../../Changes/Research/Readers/SolidWorks/SolidWorksCutFacePlacement.md) now enter the normal neutral document. The [CutSketch constraints](../../Changes/Research/Readers/SolidWorks/SolidWorksCutDimensionRoles.md) retain their ordered operands and distinguish driving sizes from equation-owned offsets. The [active partition](../../Changes/Research/Readers/SolidWorks/SolidWorksActivePartition.md) supplies the saved SOLIDWORKS body and its topology. Independent editable acceptance remains open |

The [reader guide](SolidworksResearchReader.md) defines the command and its research-only receipt.
A04a–A04b do not close A04c or qualify native conversion.
The reader does not infer missing constraints, repair the SDK mappings, launch applications or execute models.
A04c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
The [licensed two-body scope replay](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutScope.md) reads the three accepted SOLIDWORKS controls from Config-0 through the resolved Cut footer. The [public adapter](../../Changes/Research/Readers/SolidWorks/SolidWorksScopedNeutral.md) projects both saved bodies, both Bosses, the face-attached Cut and its authored scope. All three public reads matched the independently measured volumes, centroids and topology counts. Bidirectional acceptance remains open.
The [configuration replay](../../Changes/Research/Readers/SolidWorksConfigPresentation.md) derives length units, views, dimension styles, table and label settings, geometric tolerance frames, environment, views, managers and inline regions through the final part fields. The [packaged configuration map](../../Changes/Research/Readers/SolidWorksOrdinaryConfigMap.md) opens the ordinary resolved list through its saved counter. The [packaged plane reader](../../Changes/Research/Readers/SolidWorksArchivePlaneRefs.md) reads typed local components, placements and principal datums on the shared archive cursor. All fourteen P01/P03 sources reached the profile boundary and preserved their saved datum IDs and axes. Hosted API coverage checks the neutral support and its raw four-byte provenance. The [sketch presentation replay](../../Changes/Research/Readers/SolidWorksSketchRegionRecords.md) follows all 36 sketch bodies through counted displays and the region return.
Its blocked status does not prevent A05 integration or A08a implementation.
The updated workflow-quality job passed all three reader scenarios in 60.15 seconds with 58 decoded and zero rejected.
The earlier sequential process harness took 172.97 seconds on `7f8a7425`; these are CI observations, not a universal speed guarantee.
A05 is claimed separately below.
A08a process gates passed at `c1c3fcce`; see the [supervisor guide](ResearchSupervisor.md).
A08b bounded logging, restart cleanup and resource controls passed eleven Linux process scenarios at `b86f30c7`.

## A05 integration and semantic qualification

| Child ID | Deliverable                                                        | Depends on                              | Owner      | Status   | Exit criterion or remaining evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------- | ------------------------------------------------------------------ | --------------------------------------- | ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A05a     | Pinned F3D/F3Z reader, run summary and typed neutral serialization | A01, A02a                               | Stephen316 | complete | Five remote scenarios passed at `c1c3fcce`: 714 inputs, 12 strict, 685 partial and 17 rejected                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A05b     | Exact per-file outcome gate                                        | A05a                                    | jdharcourt | complete | Full report pinned at `480d9d3a`; exact 714-file baseline passed all five reader scenarios again at `22a59e68`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A05c     | Initial profile and variant semantic qualification                 | A05a, A05b; independent source evidence | Stephen316 | active   | The [P01 rectangle replay](../../Changes/Research/Readers/FusionRectangleSketchEvidence.md) verifies six plane and operand sets. The [P03 boss replay](../../Changes/Research/Readers/FusionBossProfileEvidence.md) binds eight bosses to measured loops and [signed directions](../../Changes/Research/Readers/FusionBossDirectionEvidence.md). P04 replay verifies [selected contours](../../Changes/Research/Readers/FusionCutSketch/FusionCutProfileEvidence.md), [boss-edge projections](../../Changes/Research/Readers/FusionCutProjectionEvidence.md), [center expression bindings](../../Changes/Research/Readers/FusionCutSketch/FusionCutCenterEvidence.md) and ownership of [110 relations and 66 dimensions](../../Changes/Research/Readers/FusionCutSketch/FusionCutRelationEvidence.md). The partial reader carries [44 saved cap-edge projections](../../Changes/Fusion/Adapter/FusionSavedCapRim.md) and the [saved Cut result topology](../../Changes/Fusion/Adapter/FusionSavedCutBody.md) over eleven variants. Fresh native readback and editable acceptance remain open |

The [reader guide](FusionResearchReader.md) defines the command, its run summary and its research-only receipts.
A05a uses the strict SDK reader first and accepts the partial legacy reader only with an explicit option.
A05a does not close A05b or A05c or qualify native conversion.

`A05c-FusionSavedMaterialProperties20261126` is owned by the Fusion worker on `codex/fusion-saved-material-properties`, based on the saved configuration work in [PR #331](https://github.com/TryUniCAD/Kit/pull/331). The [authored material delivery](https://github.com/TryUniCAD/Kit/pull/333) records source-free typed material mechanics, thermal and finish data with exact ownership and readback. Keep the saved aliases, textures and mappings explicitly unresolved until supported. Require independent authored edits and structural refusal controls. Native verification and public writer admission stay open.

`A05c-FusionDistinctMaterialAppearances20261126` is owned by the Fusion worker. The [delivery](https://github.com/TryUniCAD/Kit/pull/337) at `a9de3acc12` preserves distinct typed body and physical-asset appearances for the scoped source-free edits. Eight replays and sixteen refusal cases passed. Legacy textures and native verification remain open.

The [typed Fusion texture-placement delivery](https://github.com/TryUniCAD/Kit/pull/341) at `679e0d61d5` measures source-free generation and reprepare of the supported Design mapping origin. Full mixed texture interpretation and licensed target acceptance remain open.

`A05c-FusionMaterialFolderJson` is owned by the Fusion worker, based on the saved configuration work in [PR #331](https://github.com/TryUniCAD/Kit/pull/331). It registers the existing package folder in typed JSON and checks exact actual strict resource archive serialization and the package contract. The [implementation](https://github.com/TryUniCAD/Kit/pull/336) at `93ae0c59d4` passed six strict archive, public JSON and guard cases. The read-only status and writer admission stay unchanged.
A05c needs independent source inventories and distinguishing evidence rather than agreement with the same reader.
The public Fusion partial reader now carries the [saved principal-plane identity](../../Changes/Fusion/Adapter/FusionPrincipalSketchSupport.md) and [signed axis-dimension operand order](../../Changes/Fusion/Adapter/FusionAxisDimensionOrder.md) into the neutral document. The hosted archive step passed all 25 checks at `fa7e92d8`. The partial reader also preserves the [saved point coincidence arguments](../../Changes/Fusion/Adapter/FusionPointCoincidence.md). Its three public-reader cases passed at `011ddb8b`. The latest reader also checks the [saved selected-profile proxy and descriptor](../../Changes/Fusion/Adapter/FusionOwnedProfileSelection.md) for the witnessed P03 and P04 extrusion layouts and projects the [historical P04 cut target body](../../Changes/Fusion/Adapter/FusionCutTargetSelection.md). Those cases passed on `b6ce2ec9`. The [P04 sketch's saved face recipe](../../Changes/Fusion/Adapter/FusionSketchFaceProvenance.md) passed its hosted checks at `f15b9cea`. The partial reader now joins that recipe to the [exact saved face occurrence](../../Changes/Fusion/Adapter/FusionSavedFaceOccurrence.md) on the verified prior body. It reads the [saved blind and through-all cut ends](../../Changes/Fusion/Adapter/FusionSavedCutEnds.md) and retains the [projected origin and center expression operands](../../Changes/Fusion/Adapter/FusionSavedCutCenter.md). All eleven saved P04 controls corroborate these reads. Hosted public checks, fresh licensed readback and editable acceptance remain open. [Hosted archive checks](https://github.com/TryUniCAD/Kit/actions/runs/43728415623/job/132855298357)
See [the change entry](../../Changes/Research/PinnedFusionReader.md).

### A05a-DecodeEfficiency

Codex owns the strict Fusion decoding and receipt efficiency follow-up on `codex/fusion-decoder-efficiency-pr`.
Delivery PR is [#280](https://github.com/TryUniCAD/Kit/pull/280).
It depends on the A05a pinned reader and A05b exact outcome contract.
The exit requires byte-exact neutral documents, equivalent receipts, unchanged refusal diagnostics, measured offline timings, and current-head PR checks and review.
Offline verification matched 16 reader outcomes and preserved the ordered native profiles.
Three pinned strict inputs had 11% to 15% lower median receipt times.
Native read medians were mixed.
The [change entry](../../Changes/Research/Readers/Fusion/FusionDecodeEfficiency.md) records the implementation and evidence.

### A05c-FusionSavedCuboid20261125: vendor-resaved cuboid reading and writing

The Codex Fusion encoder worker owns this active task on `codex/fusion-saved-cuboid-roundtrip`.
[PR #299](https://github.com/TryUniCAD/Kit/pull/299) delivers the read-only reader and is checking.
The saved-graph writer and independent native acceptance remain open.
Dependencies are A05c, A11c, and the [research round-trip command in PR #297](https://github.com/TryUniCAD/Kit/pull/297).
The scope is the supported vendor-resaved constrained cuboid family.
The exit requires exact saved-state reading and deterministic native generation from JSON alone.
Independent source controls and held-out native open, edit, rebuild, save, and reopen evidence remain required.

## A06 comparison implementation and qualification

### A06g-BulkDecodedComparison: standalone bulk command

Codex delivered the [standalone bulk comparison command](../../Tasks/CompareDecodedDocuments.md) in [PR #273](https://github.com/TryUniCAD/Kit/pull/273).
Dependencies are the existing A06a comparator and interchange codec, integrated through merged PR #158 (`22075ee5e77c3db9b56bd8c2bc8c415d6baf237d`).
Scope is bulk comparison of existing decoded JSON, directory or manifest pairing, retained correspondence evidence, and outcome summaries.
The exit requires process evidence for matching, differences, ambiguity, invalid inputs, unit declarations, output preservation, CI and review.
The [final source audit](https://github.com/TryUniCAD/Kit/actions/runs/45186955636) passed all 50 bulk process cases on `0a137c5e`.
Status is complete for the standalone command. The [merge-group checks](https://github.com/TryUniCAD/Kit/actions/runs/45215523176) passed on `12b98c78`, the merged revision.
This scope does not change decoder behavior, complete A06b qualification, or establish native conversion acceptance.

#### A06g CLI follow-up

Codex owns the shorter research command on `codex/bulk-comparison-cli`.
Delivery is [PR #275](https://github.com/TryUniCAD/Kit/pull/275), now targeting `main` after [PR #273](https://github.com/TryUniCAD/Kit/pull/273) merged as `12b98c78`.
The scope is positional folders, manifest mode, shared explicit units, short output syntax, trusted checkout dispatch and unified copies for exact resolved pairs.
The exit requires installed-command process evidence for both pairing modes, copy provenance and refusal, older checkout diagnostics and current-revision CI and review.
See the [bulk comparison CLI change](../../Changes/Commands/BulkComparisonCli.md).

### Existing comparison implementation

The [portable graph comparator](../../Changes/Research/Readers/Comparison/SemanticGraphComparison.md) reads sealed neutral documents through the actual codec and validator.
It compares typed fields and dependency roles, normalizes explicitly declared quantities and retains ambiguous correspondences.
Unclassified references, unsupported domains and exhausted budgets cannot produce equality.
The [guide](SemanticComparison.md) defines its input seals, bounds and research-only result scope.

| Child ID | Deliverable                                                          | Owner      | Status   | Remaining evidence                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------- | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A06a     | Bounded portable graph projection, matching and process command      | jdharcourt | checking | Static checks passed; hosted process execution remains required                                                                                                                                            |
| A06b     | Independently qualified equal, different and ambiguous native pairs  | jdharcourt | blocked  | A02d evidence admission, frozen rules and A04/A05 source inventories remain required; zero pairs qualified                                                                                                 |
| A06c     | Controller comparison worker and immutable report artifacts          | jdharcourt | checking | The [worker](../../Changes/Research/Controller/SemanticComparisonWorker.md) implements the existing protocol; hosted controller process execution remains required                                         |
| A06d     | Native reader artifacts chained into comparison jobs                 | jdharcourt | checking | The [reader bridge](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md) preserves full codec documents and source evidence; hosted native-file/controller process execution remains required |
| A06d-P03DirectionOwner | Bounded source-reported P03 Boss direction-axis ownership observation | Shared encoder worker | checking | [PR #329](https://github.com/TryUniCAD/Kit/pull/329) from `codex/p03-direction-owner-evidence`. Depends on A06d comparison, [PR #121](https://github.com/TryUniCAD/Kit/pull/121) reader at `c0a401a607` and [PR #325](https://github.com/TryUniCAD/Kit/pull/325) generated evidence. Require source-bound unique Boss, sketch, principal direction and native span on both archives. The [tested observation](../../Changes/Research/Readers/Comparison/ConstrainedBossDirectionOwner.md) binds both local owners. Contradictions produce no ownership observation. Retain all unresolved findings, comparison status and qualification gates. |
| A06e     | Recovered Fusion raw-chain supplemental admission                    | Codex      | complete | Original sealed Phase A/B replay passed through the public preflight; missing SOLIDWORKS custody and zero qualified pairs remain explicit                                                                  |
| A06f     | Typed native driving roles and value-preserving graph correspondence | Codex      | complete | Local decoder/codec and process corrections verified at the commit containing this entry; A06b remains blocked with zero qualified pairs                                                                   |

The local A06b follow-up starts from PR #158 head `5018f106b8287c83756233c677cc155e8b963357` on `codex/pr158-pair-qualification`.
The original Fusion source handoff and corrected private run were recovered from their existing task custody.
The [recovered admission change](../../Changes/Research/Controller/Admission/RecoveredFusionEvidence.md) records replay scope and the public verifier contract.
The SOLIDWORKS raw chains, coordinated manifest, frozen-rule evaluation, and independent equal/different/ambiguous case adjudication remain required.
Native ambiguous evidence cannot be replaced by synthetic duplicated graph candidates.
The source recovery and supplemental observation do not complete A06b or qualify a conversion.

A06f is the bounded implementation in the commit containing this entry, delivered through PR #158.
The [typed dimension-role correction](../../Changes/Fusion/Adapter/FusionLinearDrivingRoles.md) promotes only uniquely bound, validated native driving dimensions; the [correspondence correction](../../Changes/Research/Readers/Comparison/NativeDirectionMatching.md) preserves unique equal line fields before neighborhood preferences.
An independent local replay of the sealed Fusion Phase B observations checked 28 native driving dimensions and 56 ordered targets across fourteen P01/P03 discovery archives.
The final local 151-case process sweep passed decoder/codec, role safety, radial compatibility, public rectangle, semantic comparison, worker, and native-reader bridge controls.
The direct P03 direction comparison retains all eight loop-reference differences, signed depth and body-bound differences, and all seventy unresolved source issues.
These are local results, not a fresh native application run or hosted acceptance.
A06f depends on the recovered A06e evidence and existing typed decoders; its exit condition is the bounded corrections and focused local verification recorded above.
The SOLIDWORKS raw chains remain unavailable within the searched repository, reachable-history, compressed-asset, and linked Windows CI artifact scope; this is not a claim of global nonexistence.
A06b remains blocked with zero qualified pairs, and its profile semantics, coordinated manifest, frozen-rule evaluation, genuine native ambiguity, hosted checks, target acceptance, and held-out requirements remain open.

Observed graph equality does not qualify a reader, writer or native conversion.
The [sketch-reference repair](../../Changes/Research/Readers/Comparison/SemanticSketchReferences.md) recognizes a definition-free reference to a unique declared sketch in both graph projection and reader inventory, retaining operation-definition and unresolved-target findings.
The [primitive-domain repair](../../Changes/Research/Readers/Comparison/SemanticValueDomains.md) keeps malformed or unknown parameter value kinds unresolved.
These A06a/A06d source repairs remain checking hosted process execution.
The [source-bound private P03 controller observation](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md#verification-evidence) records three strict reads and two dependent comparisons at `7317092e37f52d6bfc3f26449e2b16a5bd82e86b`, now preserved in the shared ancestry.
All five completed on their first attempts; the operator reopened and hash-checked five result/receipt pairs and eight artifacts.
The reports remained `different` and `ambiguous`, with semantics unverified and native acceptance unestablished.
This observation does not replace current-head hosted A06c/A06d checks or A06b qualification.
The subsequent [fresh P03 replay at `880bf0be`](../../Changes/Research/Readers/Comparison/SemanticSketchReferences.md#verification-evidence) removed only the false sketch-definition finding in both reader inventories and dependent comparisons, retaining `different` and `ambiguous` results and preserving the original `7317092e` run.
A07 acceptance and A09 continue to depend on A06b.

### A06d-NativeSketchOwnership: saved SOLIDWORKS sketch ownership in comparison

The Codex shared encoder worker owns this checking task on `codex/native-sketch-ownership`.
Delivery is [PR #302](https://github.com/TryUniCAD/Kit/pull/302), based on the [encoder round-trip branch in PR #297](https://github.com/TryUniCAD/Kit/pull/297).
The task depends on A04c typed saved source reads, A06a comparison, and A06d reader evidence.
[PR #121](https://github.com/TryUniCAD/Kit/pull/121) retains ownership of its SOLIDWORKS reader changes.
The exit requires a real comparison report that relates one uniquely typed sketch to its same-source native timeline owner.
The report must preserve ordered constraint references and keep the original unresolved findings and verdict.
The P01 and P03 sources remain discovery evidence. Independent source inventory and native acceptance remain open.
The [change entry](../../Changes/Research/Encoder/NativeSketchOwnership.md) records the observed report and comparison boundary.

## A09 scoped codec research

Stephen316's accepted research constructs the [two configured atom owners](../../Changes/Research/Writers/SolidWorks/Boss/SolidWorksTwoPadConfigAtoms.md), the upper sketch's [ordered same-length relation](../../Changes/Research/Writers/SolidWorks/Boss/SolidWorksTwoPadEqualRelation.md) and the earlier boss's [cap and boundary occurrences](../../Changes/Research/Writers/SolidWorks/Boss/SolidWorksTwoPadCapRefs.md).
These scoped constructors retain caller-supplied ownership and allocation state; their entries distinguish saved-control observations from independently generated record controls.
They do not establish a complete two-pad archive or qualify A09.

The cap constructor starts after the enclosing face header.
The [matched-owner component prefix](../../Changes/Research/Writers/SolidWorks/Boss/SolidWorksTwoPadFaceComponent.md) now derives the component flags and atom references from the native ownership rules, while the selected earlier kernel-face handle and live candidate inventory remain open.
The upper sketch, joined kernel and rollback ownership, two-atom resolved composition and configuration-cache bindings remain construction dependencies.
The [scoped ghost and relation managers](../../Changes/Research/Writers/SolidWorks/Boss/SolidWorksTwoPadGhosts.md) emit the two inline point records and following empty relation manager; the separate ghost-partition stream and whole-package integration remain open.
A06b/A07 proof, complete donor-free generation and licensed load, independent edits, rebuild, save and fresh reopen remain required.

## A11 Fusion writer research

| Child ID | Deliverable                                                                   | Owner      | Status   | Remaining evidence                                                                                                                                                                                                                                |
| -------- | ----------------------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A11a     | Explicit directly owned dimensions in the scoped positive-XY Boss constructor | jdharcourt | checking | The [real-stage authoring composition](../../Changes/Fusion/Authoring/FusionDirectDimensionAuthoring.md) replaces temporary profile changes and shared-function replacement; hosted Boss and historical Origin process execution remains required |
| A11b     | Native writing from qualified portable graphs                                 | jdharcourt | blocked  | A06b/A09 evidence, complete required-semantic admission and licensed target acceptance remain required; the public writer guard remains enforced                                                                                                  |

The [source-derived Boss probe](../../Changes/Research/Readers/Comparison/FusionSourceBossProbe.md) retains four measured discovery controls and the exact parameter, geometry, material and archive checks.
The reported separate 37 × 21 × 11 mm feasibility case supports the composition change, not native application acceptance of this revision.
The owned licensed witness still needs driving edits, restoration, rebuild, save and fresh-process reopen with healthy controls.
Neither the scoped constructor nor its observation receipt closes A11 or qualifies a conversion route.

## A12 SOLIDWORKS writer research

### A12b: vendor-authored blind boss admission

The Codex SOLIDWORKS encoder worker owns this active task on `codex/solidworks-vendor-boss-admission`.
[PR #300](https://github.com/TryUniCAD/Kit/pull/300) delivers the research evidence and a safe manifest for exact private replay.
The task depends on A04, A06, A08, A12a, A14, and [PR #297](https://github.com/TryUniCAD/Kit/pull/297).
[PR #121](https://github.com/TryUniCAD/Kit/pull/121) retains property-reader ownership at `c0a401a607`.
[PR #288](https://github.com/TryUniCAD/Kit/pull/288) retains ownership of catalogue capture supervision.
The scope is ordinary version-19000 parts with one supported straight-line loop and a driving blind boss.
Whole-source admission requires complete feature, manager, partition, and presentation semantics in archive-free JSON.
Generation, independent held-out native verification, and the exact SDK publication evidence remain open.

### A12b-P03ConstraintIntent

The [native P03 SOLIDWORKS witness](https://github.com/TryUniCAD/Kit/pull/338) at `1158fff0ed` passed seven licensed stages in 95.524 seconds. It covers the generated sample and a depth edit with separate reopen. The original source history and public writer admission remain open.

| Child | Scope and owner | Dependencies | Delivery and exit |
| --- | --- | --- | --- |
| A12b-P03ConstraintIntent | Shared encoder worker. Project one source-bound positive XY P03 SOLIDWORKS rectangle and first blind Boss into the existing research logical constructor input. | A04c saved relations, A06d source-bound owner evidence, the catalogue logical Boss input on main and existing generative archive work. Coordinate with PR #121 and A12b exact SI, plane and depth owners. | [PR #314](https://github.com/TryUniCAD/Kit/pull/314) from `codex/p03-constrained-boss-intent`. Require deterministic source JSON replay, ordered native operands, distinct Origin, loop point aliases and owner/span checks. Reject changed evidence without publishing output. Native generation, editable measurement and public writer admission stay open. |
| A12b-P03ConstrainedCandidate | Shared encoder worker. Bind proved implicit body ownership and source relation evidence to a source-free constructor request for the one positive P03 baseline. | PR #314 source proof and the authored logical Boss constructor on main. The SOLIDWORKS owner retains public writer and licensed measurements. | [PR #325](https://github.com/TryUniCAD/Kit/pull/325) from `codex/p03-constrained-boss-candidate`. Require atomic request custody, exact fresh-process generation from that request and explicit target settings, and strict target graph and body readback. Record source Join separately from target first-body Create. Native merge/edit behavior, held-out generalization and public publication remain open. |
| A12b-P03SdkReadback | Shared encoder worker. Compare the exact generated P03 native archive with its pinned saved source at the independent public SDK reader boundary. | [PR #325](https://github.com/TryUniCAD/Kit/pull/325) generated bytes and [PR #121](https://github.com/TryUniCAD/Kit/pull/121) reader at `c0a401a607`. The SOLIDWORKS owner retains native measurement and derived-state code. | [PR #328](https://github.com/TryUniCAD/Kit/pull/328) from `codex/p03-independent-sdk-readback`. Require fresh default strict reads and separate supported option results, exact input hashes, ordered sketch operands and Origin references, driving dimension owners, full unresolved remainder and the first actual semantic mismatch or refusal. The [pinned readback](../../Changes/Research/Encoder/ConstrainedBossSdkReadback.md) recorded default strict refusal, design-only graph differences, keyword order and the full unresolved inventory. Licensed qualification and public writer admission remain open. |

Related deliveries preserve narrower boundaries. The [absolute depth units fix](https://github.com/TryUniCAD/Kit/pull/306) applies millimetre edits to already qualified authored requests. The [document plane visibility research](https://github.com/TryUniCAD/Kit/pull/308), [exact depth intent](https://github.com/TryUniCAD/Kit/pull/309) and [native plane witness](https://github.com/TryUniCAD/Kit/pull/310) remain separate. The plane witness measured the generated pair and On-state edit/save/reopen on the exact build in seven normal lifetimes, in 87.994 seconds. PR #310 has passing current-head CI and configured review on `95e76f0a4b`. Held-out plane coverage, visibility overrides, complete vendor-source state, public admission and merge-queue acceptance stay open. The [native exact-depth witness](https://github.com/TryUniCAD/Kit/pull/311) preserved the original D1 bits through an unchanged save and reopen in a nine-lifetime qualified batch. The [exact SI sketch intent research](https://github.com/TryUniCAD/Kit/pull/312) replays exact coordinates from prepared JSON. It still needs independent held-out and native acceptance. The [Fusion source-free cuboid candidate research](https://github.com/TryUniCAD/Kit/pull/307) remains a separate A11 delivery. Its bounded held-out candidate completed four guarded native stages. The [saved snapshot ownership fix](https://github.com/TryUniCAD/Kit/pull/313) refuses nine corruptions and preserves the existing constructor route. Two saved zero-address contrasts each passed seven native stages. Independently generated snapshots, complete vendor-source state and native qualification of that writer remain open. The [native exact-coordinate witness](https://github.com/TryUniCAD/Kit/pull/315) measures the generated SI sketch. The [combined authored intent research](https://github.com/TryUniCAD/Kit/pull/316) composes exact SI geometry and depth, Top annotation, construction planes and the supported Default configuration. Full vendor-source state and licensed combined acceptance remain separate. The [document precision research](https://github.com/TryUniCAD/Kit/pull/317) generates two and four decimal places across 16 MMGS rows with exact offline geometry preservation. Native acceptance of the new precision, other formatting and density or analysis defaults remain open.

Recent independent writer evidence remains separately owned. The [Fusion snapshot generator](https://github.com/TryUniCAD/Kit/pull/318) generates snapshot geometry and ownership links from a fixed-cuboid request. Full saved-source writing remains open. The [combined SOLIDWORKS native witness](https://github.com/TryUniCAD/Kit/pull/319) records twelve healthy lifetimes across geometry and supported presentation. The [document precision native witness](https://github.com/TryUniCAD/Kit/pull/320) records four fresh controlled lifetimes. The [resaved renderer diagnostic](https://github.com/TryUniCAD/Kit/pull/321) identifies the appearance-allocator disagreement and preserves the strict reader refusals. The [generated appearance witness](https://github.com/TryUniCAD/Kit/pull/323) binds two appearance scalars through fresh Definition generation and independent readback. The [empty cut-list property owner](https://github.com/TryUniCAD/Kit/pull/324) binds a Boolean intent to a fresh typed property substream, with exact standalone comparisons. The [Fusion saved parameter handoff](https://github.com/TryUniCAD/Kit/pull/326) retains named bindings and expressions from both observed allocation families through source-free generation. The [Fusion saved camera roles](https://github.com/TryUniCAD/Kit/pull/327) records exact source-free named camera generation and retained limits. Native application verification remains open. The [P03 keyword-order fix](https://github.com/TryUniCAD/Kit/pull/330) corrects the strict design projection while retaining the other 31 members. The [Fusion empty configuration envelope](https://github.com/TryUniCAD/Kit/pull/331) preserves both empty member orders and explicit absence. The [SOLIDWORKS empty-owner composition](https://github.com/TryUniCAD/Kit/pull/332) combines the typed empty property and appearance scopes in one generated part. Whole-source, native appearance and public conversion qualification remain open.

### Existing A12 evidence

The [caller-supplied rectangular Boss candidate](../../Changes/Research/Writers/SolidWorks/Metadata/SolidWorksPortableBossCandidate.md) accepts a validated neutral document and explicit typed target state for the bounded Front/Right, signed blind-extrusion scope.
It refuses unsupported required state and independently reads the complete generated archive before optional no-replace publication.
Two independent source reviews of `02d32d220eae0809988f1f52c442903a58a3de6b` found no actionable defects; this does not replace hosted execution, licensed acceptance or public writer qualification.

The [generation-19000 writer research](../../Changes/Research/Writers/SolidWorksWriterResearch.md) records evidence for the P03 rectangular blind boss, including the configuration-to-feature join, model header, and Definition notebook, appearance manager and terminal fields.
The [typed Definition constructor](../../Changes/Research/Writers/SolidWorksDefinitionStream.md) reproduced the complete stream in all 25 pinned saves at `2fc4acbd`. The [CMgr visual properties analysis](../../../re/solidworks/WriterResearch/CmgrVisual.md) reproduced the measured 300-byte DSPBR record on the same hosted run. The [blind boss display analysis](../../../re/solidworks/WriterResearch/DisplayStyle.md) reproduced the 94-byte style in eight P03 saves. The subsequent 284 bytes passed the archive gate at `f0962377`. [Hosted archive results for f0962377](https://github.com/TryUniCAD/Kit/actions/runs/43847585169/job/133231531685)
The hosted archive step at `af78da00` verified the [empty configuration mass record](../../Changes/Research/Writers/SolidWorksEmptyCmgrMass.md) across six P01 saves and the [blind boss handle and distance codecs](../../Changes/Research/Writers/SolidWorksBlindDistanceVerification.md) across eight P03 saves. [Hosted archive results for af78da00](https://github.com/TryUniCAD/Kit/actions/runs/43854211290/job/133254196499)
The [configuration manager part return](../../Changes/Research/Writers/SolidWorksCmgrPartReturn.md) reached both active-part object aliases in all 25 receipt-pinned saves. The hosted constructor comparison passed at `408f6ba3`. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43858305980/job/133268369127)
The [populated mass replay](../../Changes/Research/Writers/SolidWorksBossCmgrMass.md) matched the twelve physical fields across all eight P03 saves within declared tolerances. The [configuration atom link replay](../../Changes/Research/Writers/SolidWorksCmgrAtomLinks.md) reached the same typed allocations across six P01 and eight P03 saves. The constructor checks passed in the hosted archive step at `33c3f56d`. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43862799425/job/133283627698)
The [configuration manager external file](../../Changes/Research/Writers/SolidWorksCmgrExternalFile.md) carries the part allocator into the terminal lists for both path forms across 25 pinned saves. The [base return and aliases](../../Changes/Research/Writers/SolidWorksCmgrReturns.md) and [manager opening and inherited feature](../../Changes/Research/Writers/SolidWorksCmgrOpening.md) preserve both P01/P03 histories in all 14 saves. The hosted archive step passed these comparisons and the [blind-boss display placement](../../Changes/Research/Writers/SolidWorksBlindDisplayTail.md) at `f832a3b8`. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43865736099/job/133293681800)
The [ModelHeader revision constructor](../../Changes/Research/Writers/SolidWorksModelHeaderLogs.md), individual [CMgr visual](../../Changes/Research/Writers/SolidWorksCmgrVisualPrefix.md), [base header](../../Changes/Research/Writers/SolidWorksCmgrBaseState.md) and [base collection](../../Changes/Research/Writers/SolidWorksCmgrCollections.md) records, and the [blind-boss display cache](../../Changes/Research/Writers/SolidWorksBlindDisplayCache.md) passed the hosted archive gate at `ce413404`. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43869234190/job/133305694339)
The [complete ModelHeader constructor](../../Changes/Research/Writers/SolidWorks/SolidWorksModelHeaderTail.md) checked the document stamps and independently measured bounds across 25 saves. The [complete CMgr constructor](../../Changes/Research/Writers/SolidWorks/SolidWorksCmgrComposition.md) matched all six sketch-only P01 streams exactly. The eight P03 streams matched outside the twelve geometry-derived mass values, with all twelve within their declared tolerances. Both full-stream comparisons passed the hosted archive gate at `d4e2baa8`. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43873906447/job/133321858013)
The [named Config-0 root](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigurationRoot.md), its [visual body](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigurationVisual.md), the [favorite handle and distance return](../../Changes/Research/Writers/SolidWorks/SolidWorksBlindDisplayFavorite.md) and the [base display fields](../../Changes/Research/Writers/SolidWorks/SolidWorksBlindDisplayBase.md) passed the hosted archive gate at `d4e2baa8`. The [inactive selector](../../Changes/Research/Writers/Display/SolidWorksInactiveBossSelector.md) adds a guarded zero in the last four-byte field. The licensed one-field candidate preserved the boss measurements and exited normally. The independent stock control failed during exit, so the watchdog campaign remains unaccepted. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43873906447/job/133321858013)

The [paired archive gate](https://github.com/TryUniCAD/Kit/actions/runs/43878525516/job/133337869438) passed at `3cdcaca6` with the resolved system folders, annotation cabinet, unit table and configuration view checks. Subsequent read-only evidence fixes the boundaries for the [body and material folders](../../Changes/Research/Writers/SolidWorks/SolidWorksResolvedFolderTail.md), [model settings and hatch](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigurationModelBody.md), [configuration and resolved archive framing](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigResolvedArchive.md) and [complete blind-boss display](../../Changes/Research/Writers/Display/SolidWorksBlindBossDisplay.md). Hosted reconstruction and complete native part acceptance require their own observations.

At `ce538c42` the hosted archive check and its bound receipt passed with the complete first configuration split, the resolved folders through the environment and material, and the blind-boss display and start specification. The [principal planes](../../Changes/Research/Writers/SolidWorks/SolidWorksResolvedPrincipalPlanes.md) and [Origin](../../Changes/Research/Writers/SolidWorks/SolidWorksResolvedOrigin.md) extend the resolved writer through the first authored profile boundary. Full part acceptance remains open. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43883397404/job/133354975112)

The hosted archive receipt at `0a70ff7e` covers the [framed resolved opening](../../Changes/Research/Writers/SolidWorks/SolidWorksOrdinaryResolvedOpening.md) through the first authored point count. The [standard Config-0 view writer](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigSavedViews.md) computes the ten camera bases and handles their native class and object slots. Its read-only evidence covers all 14 P01 and P03 saves up to the sketch-block manager. [Hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43890240800/job/133379363468)

The [licensed P03 omission witness](../../Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md) opened a repack without the physical partition, ghost partition, lightweight data or display list streams. A depth edit and restore preserved the expected volume and center of mass, and the stock controls exited normally. A synthesized P03 candidate can use this evidenced member set. The P01 omission witness and full generated native acceptance remain open.
The [first six resolved system folders](../../Changes/Research/Writers/SolidWorks/SolidWorksResolvedFolders.md) and the [annotation cabinet](../../Changes/Research/Writers/SolidWorks/SolidWorksResolvedCabinet.md) join the licensed tree names and header IDs in all 14 saves. Together they allocate 26 slots and preserve the cabinet's reciprocal Notes references. The [Config-0 units table](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigurationUnits.md) and [model presentation fields](../../Changes/Research/Writers/SolidWorks/SolidWorksConfigurationModelView.md) preserve unit ownership, optional curvature state and reference-plane presentation.
The [configuration storage index](../../Changes/Research/Writers/SolidWorks/SolidWorksPartConfigurationIndex.md) reconstructs the active-config stream. The [archive framing](../../Changes/Research/Writers/SolidWorks/SolidWorksPartArchiveFraming.md) derives the paired ZIP timestamps and supplies typed generation-19000 storage entries. The [native Student-context Boss witness](../../Changes/Research/Writers/SolidWorks/Metadata/NativeStudentBossWitness.md) records the licensed opening and editable lifecycle of one independently assembled part.
The saved controls support offline format research while A06 graph qualification and A09 codec evidence remain open.
A12 still needs complete native generation from a qualified portable graph, refusal at the writer boundary, and controlled application evidence for that public route.
The separate SOLIDWORKS generative research in PR #121 records controlled load, edit, rebuild and fresh-reopen evidence for radius and diameter sketches and bounded blind circle bosses on build 34.5.2.0604. That source supplies independent constructor and oracle evidence for A12 and A16. The current public writer and qualified routes on PR #94 remain open. [PR #121 source and scope](https://github.com/TryUniCAD/Kit/pull/121)

## A16 FreeCAD end-owner bindings

| Child ID | Deliverable                                                 | Owner      | Status   | Remaining evidence                                                                                                                                                                                                                                      |
| -------- | ----------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A16a     | Explicit forward and reverse FreeCAD extrusion dependencies | jdharcourt | checking | The [native emission repair](../../Changes/Freecad/FreeCadTwoLengthBindings.md) preserves ordered end owners and physical units; an exact `abfba60a` operator replay reported correct links, with native acceptance still required                      |
| A16b     | Native FreeCAD symmetry and reversal preservation           | jdharcourt | checking | The [native reader repair](../../Changes/Freecad/FreeCadNativeEndSemantics.md) reads saved flags independently of distances; native-only public process and native acceptance evidence remain required                                                  |
| A16c     | Independent FreeCAD direction and reversal emission         | jdharcourt | checking | The [inline writer repair](../../Changes/Freecad/FreeCadReversedExtrusion.md) emits the normalized base direction and native reversal flag independently; hosted public-write process and native acceptance evidence remain required                    |
| A16d     | Calculated initial FreeCAD extrusion geometry               | jdharcourt | checking | The [initial-shape implementation](../../Changes/Freecad/FreeCadInitialExtrusionShapes.md) calculates an owned cache for the scoped inline profile family; hosted process checks and independent initial-open evidence before recompute remain required |
| A16e     | Honest fresh FreeCAD extrusion acceptance flags             | jdharcourt | checking | The [attestation repair](../../Changes/Freecad/FreeCadInitialGeometryAttestation.md) keeps fresh unqualified extrusion output explicitly incomplete and strict destinations protected; hosted process checks remain required                            |
| A16f     | Refusal of changed inline FreeCAD snapshots                 | jdharcourt | checking | The [inline manifest guard](../../Changes/Freecad/FreeCadInlineManifestGuard.md) checks scoped native controls before returning a snapshot; hosted process coverage, saved native edit controls and full edit reconstruction remain required            |
| A16g     | Native FreeCAD spreadsheet alias dependencies               | jdharcourt | checking | The [alias recovery](../../Changes/Freecad/FreeCadNativeSheetAliases.md) requires unique actual cells, raw saved numeric evidence and quantity corroboration; hosted read/replay process coverage remains required                                      |

The [earlier readiness observation](../../Changes/Research/Readers/Comparison/FreeCadTwoLengthReadiness.md) records the missing reverse link and equal-length roster crossing on its original checkpoint.
The repair does not admit unsupported linked definitions or fallback carriers.
The [installed FreeCAD 1.1.4 witness](../../Changes/Freecad/FreeCadEndNativeWitness.md) records scoped end-driver edits, restoration, save and fresh reopen at `b32222b5`; original packages required native recompute before exposing solids, so initial geometry availability and broader qualification remain unresolved.
Calculated cache presence does not qualify the route or establish the initial-open result.
The [later calculated-cache witness](../../Changes/Freecad/FreeCadInitialOpenWitness.md) at `161885d8` closes the pre-recompute initial-open measurement for three rectangular controls and records independent edits, restoration, save and fresh reopen.
It retains false research flags and leaves the other cache families and route qualification unfinished.
The PR #158 [rectangle verification](../../Changes/Freecad/FreeCadRectangleVerification.md) records a fresh FreeCAD 1.1.4 witness for three rectangular controls, plus supplemental saved-edit and spreadsheet alias cases. The [exact replay repair](../../Changes/Freecad/FreeCadExactReplayOrdering.md) preserves admitted source bytes while retaining the strict usability flags and fresh-output checks. The broader A16 checking and qualification requirements remain open.
The next independent native witness must measure the original package immediately after open and before explicit recompute, then repeat driving edits, restoration, rebuild, save and fresh reopen with healthy controls.
A13, A15 and the remaining route-specific acceptance requirements stay open.
The inline guard and alias recovery are separate reader repairs, not native qualification.
Unsupported edited graph reconstruction, cached BREP freshness and native body inventory remain separate work.

## Parallel-session child steps

These rows incorporate the [parallel-session design](ParallelSessions.md#delivery).
Their parent identifiers remain stable.
They are not implemented by documenting the rows.

| Child ID | Deliverable                                                                          | Depends on                                           | Owner      | Status   | Exit criterion                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A08a     | Supervisor, private session directories, pools, controller interface and A03 adapter | A03 technical substeps                               | Stephen316 | complete | Six supervisor process scenarios passed at `c1c3fcce`, alongside fifteen controller scenarios covering counted resources and pool claims                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A08b     | Headroom, adaptive limits, calibration and grouped small-file sessions               | A08a                                                 | jdharcourt | complete | Capacity accounting, adaptive growth and all three reductions, grouped execution and standalone calibration verified. The [Linux reserve witness](../../Changes/Research/Supervisor/AmbientMemoryReserve.md) passed at `5605c58f`. The [matched Windows sweep](../../Changes/Research/Supervisor/SixteenWorkerCalibration.md#windows-sweep-with-the-warm-claim-helper) verified five concurrency levels and clean teardown                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A08c     | Isolated application authoring, trace and acceptance workers                         | A02b, A08a                                           | jdharcourt | active   | The supervisor recovered acknowledgement of a [licensed P04 readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md#licensed-job-evidence). The [Fusion queue](../../Changes/Research/Workers/FusionPhaseQueue.md) bounds the restart wait and retains timeout request custody. The [owner archive command](../../Changes/Research/Workers/FusionPhaseAudit.md) preserves a proven unclaimed Phase A probe and releases that probe's quarantine, with archive and refusal cases verified on macOS at `f15b9cea`. The phase audit verified its archived receipt at `32ccaf06`. The owner command can queue one exact archived retry after validating the manifest, parked attempt, retry budget and resource ownership. The [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43723299668/job/132839798075) verified the Phase A parking repair and both Phase B restart cases. Licensed Fusion dispatch, automatic CAD restart and the unattended pilot remain open |
| A08d     | Installed CLI compatibility, delivered separately in PR #119                         | A03, A04a, A05a, A08a source interfaces              | jdharcourt | complete | PR #119 merged as `249cf7dc`. The installed CLI verified an independent research checkout of PR #94 tested merge `e60486e0`. Linux passed 27 cases with one Windows-only skip. Windows passed 17 cases.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| A08e     | Windows host support for the supervisor and application workers                      | A08a                                                 | jdharcourt | active   | The [licensed Windows queue](../../Changes/Research/Workers/SolidWorksQueuedReadback.md) accepted 25 fresh SOLIDWORKS observations across P01, P03 and P04. Licensed [timeout rearm](../../Changes/Research/Workers/SolidWorks/TimeoutRearm.md#licensed-two-attempt-witness) and [restart replay](../../Changes/Research/Workers/SolidWorks/TimeoutRearmReplay.md#licensed-restart-witness) verified archival, a second native dispatch and the configured attempt limit for P04. Native Fusion execution remains open                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| A10a     | Optional Codex runner and private data boundary                                      | A08a, A07, A09; explicit model-command authorization | Unassigned | planned  | Candidate validation, isolated reads, bounded packets/patch paths and verified runner contracts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| A10b     | Step validation, selector, failure log and start-step routing                        | A10a                                                 | Unassigned | planned  | Separate infrastructure/model failures, exact cache keys, stable packet prefixes, budgets, fallback after a first-step failure and two-failure start-step routing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| A10c     | Use report for each model step and route key                                         | A10b, A09                                            | Unassigned | planned  | Recorded attempts, passes, model failures and tokens per pass for each step. The report never changes the selected models                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| A10d     | Optional Claude API and Claude Code runners                                          | A08a, A07, A09; applicable authorization             | Unassigned | planned  | Provider validation, serving-model attribution, bounded errors and private-data/policy gates                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| A14a     | Controller and corpus process gates                                                  | A03 technical substeps                               | jdharcourt | complete | Seven corpus and fifteen controller scenarios passed at `22a59e68`; extend the gate when interfaces change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A14b     | Reader, comparator and writer regression gates                                       | A04a, A05; A06 for paired gates                      | jdharcourt | active   | Pinned reader/outcome and native-field refusal gates passed at `22a59e68`. The nine [discovery archive reports](../../Changes/Research/DiscoveryArchiveGate.md) and 45 public Fusion reader cases passed in the [hosted archive step](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400807) at `f15b9cea`. Paired comparator and writer acceptance still require A06 and independent native evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A14c     | Batched remote verification receipts                                                 | A03, A09, A14b                                       | jdharcourt | blocked  | The [paired discovery runner](../../Changes/Research/Controller/PairedDiscoveryReplay.md) settled 25 archive pairs in `waiting_ci`. The [paired CI release](../../Changes/Research/Controller/PairedCiBatchRelease.md) and [candidate selector](../../Changes/Research/Controller/PendingCandidateDependencies.md) preserve the exact attempts and provisional dependencies. Further work waits for A09 and A14b completion. Live successful release and per-member failure isolation remain open                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| A15a     | Two-week deterministic operating pilot, with optional enabled model pools            | A07, A08b, A14; A10c/A10d only when enabled          | Unassigned | planned  | Measure elapsed and active agent time, throughput, recovery, blockers, verified capability gains, and any operator intervention. Track model spend when enabled                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

The model pairs do not become runtime requirements for a models-off pilot.
The coordinating agent runs remote CI in batches. See [batched remote verification](AutomationPlan.md#batched-remote-verification).
A08c includes the [always-busy application loop](ParallelSessions.md#application-workers-that-stay-busy): continuous claims, work ahead of decoding, scheduled resets and batch controls.
A08e targets the controller, supervisor and both applications running on one Windows host. The queued SOLIDWORKS P04 readback has run on that host. Native Fusion execution remains open.
The local-check proposal is not in force: all test execution remains remote.
A10 must not silently approve model-run shell commands or transmit private designs.

## Required PR progress comments

Post a top-level comment on [PR #94](https://github.com/TryUniCAD/Kit/pull/94) when claiming authorized work.
Post whenever any change or stage starts, progresses meaningfully, completes, becomes blocked or is handed off.
Post after every accepted push and failed verification.
A chat update or PR-body edit does not replace a top-level comment.
During sustained work, post at least one consolidated update per working day.
Do not post repetitive polling messages.
Implementation step IDs must appear in PR descriptions, relevant commits and progress comments.
All implementation stays on PR #94 and identifies the matching register rows.
Do not open separate PRs for A01–A16 unless the user changes this instruction.

Use a short, readable Markdown comment with these sections.
Replace every bracketed value and link evidence directly.

```markdown
### Current step: Axx — [step name]

**Status:** [active / blocked / checking / complete]
**Owner:** [github login]
**Revision:** [exact SHA or explicitly uncommitted]
**Work:** [branch and PR link]

**Completed**

- [Concrete result since the last update]

**Evidence**

- [Source/report link and exact-revision CI result]

**Remaining**

- [Unfinished exit criteria, or none for this step]

**Blockers:** [Missing prerequisite or none]
**Next:** [Specific next action or handoff]
```

For a claim, identify dependencies and the files the contributor owns.
For a blocker, state what change would make the job runnable.
For completion, link every required observation and identify the validated capability scope.
Do not use same-format success to close a cross-format conversion step.

## Documentation checkpoint

The current change aligns the plan, adds this register and records contributor instructions.
A01 now supplies the audited neutral-format decision and capability boundaries.
PR #94 now includes A02 corpus tooling, specifications and remote process coverage.
A03 and its heartbeat repair passed remote process verification at the recorded code checkpoints; PR readiness remains separate.
A04 adds a research reader boundary and evidence receipt around the existing codec.
No comparator, schema extension or application worker is established by that integration.
Native capture qualification remains blocked separately.
A04a–A04b passed remote verification. A04c has independent SOLIDWORKS measurements for bounded discovery comparisons.
At PR head `1bdb6743`, the remote discovery checks decoded all 25 parts. They verified six P01 edge counts and five XY endpoint comparisons, eight P03 boss direction cases, both P03 Front Plane directional Z bounds, both P04 equation bindings in eleven captures, and the resolved inch-length checks. The two expected Z intervals came from the independently measured boss centroids and depths. P01 and P03 YZ variants still fall back to the Front plane. [Discovery checks](https://github.com/TryUniCAD/Kit/actions/runs/43652490420/job/132623817084)
The P04 configuration-stream investigation links both sketches to resolved feature records in all eleven discovery captures. Licensed baseline A and YZ traces confirm both exact sketch boundaries and show that each profile reads the same live object from the shared map. The production reader still needs the corresponding versioned walk and a decode of the supporting face occurrence. The independent readback verifies the persistent boss face and both sketch transforms in all eleven. [Licensed archive trace](../../../re/solidworks/records/P04SketchResidence.md#licensed-sketch-boundaries-and-resolved-references), [native readback](../../Changes/Research/Workers/SolidWorksCutFaceReadback.md)
At `cdf53e1f`, the discovery reader agreed with all eleven measured native cut terminations. Ten blind cuts had matching neutral depths, including the 5 mm edit. The through-all cut preserved native code 1 and a missing authored depth. Its neutral definition was a native fallback.
At `dd9dfa9b`, the 25-file local discovery census verified the [typed through-all projection](../../Changes/Research/Readers/SolidWorksThroughAllProjection.md) with no authored length. The change leaves native reconstruction subject to the existing writer gates.
At PR head `5605c58f` and tested merge `c4f34448`, the hosted census matched all 1,136 comparisons across the 25 discovery files. The archive step passed the P04 through-all Parasolid re-export and independent area checks for both holed caps. The [P04 partition identity audit](../../Changes/Research/Workers/SolidWorks/DiscoveryPartitionIdentity.md) also joined the sole saved body to its typed resolved identity in eleven independently measured captures. Licensed editable acceptance remains open. [Hosted discovery and archive checks](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521405)
Later deterministic child steps remain available when their prerequisites pass.

### Reconciled remote evidence and current limits

The latest verified source checkpoint is PR head `22a59e68c839354f3e6672eec6f67aa647aa1dce` against main `d85e42479bccc79bea5e0c7eeca6a0411cc9e2a9`.
The Linux job tested GitHub merge revision `6267defee23cfaee79c68d79a5fffb46c1c00253` for those inputs.
Every PR CI report, including [CI Agg](https://github.com/TryUniCAD/Kit/actions/runs/43678423564/job/132703569338), passed at that checkpoint.
Subsequent documentation heads require their own CI; this records a verified source checkpoint rather than predicting their results.

| Gate                             | Actual result                                                              | Evidence                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Linux CI contracts               | 136 passed, 19.26 seconds                                                  | [Linux job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622509)   |
| Native/API/registry              | 327 passed, 159 existing unavailable-corpus/platform skips, 74.46 seconds  | Same Linux job                                                                            |
| Typed carrier boundaries         | 31 passed, 148.54 seconds                                                  | Same Linux job                                                                            |
| Corpus/preparation               | 7 passed, 12.14 seconds                                                    | Same Linux job                                                                            |
| SOLIDWORKS reader                | 3 passed, 44.24 seconds; 58 decoded, zero rejected                         | Same Linux job                                                                            |
| Output/application transport     | 17 passed, 35.38 seconds                                                   | Same Linux job                                                                            |
| Fusion reader                    | 5 passed, 50.64 seconds; exact 714-file baseline unchanged                 | Same Linux job                                                                            |
| Durable controller               | 15 passed, 67.21 seconds                                                   | Same Linux job                                                                            |
| Linux supervisor                 | 57 passed, 393.51 seconds                                                  | Same Linux job                                                                            |
| macOS worker processes           | 74 passed, 514.07 seconds                                                  | [macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622604)   |
| Windows worker processes         | 22 passed, 77.49 seconds                                                   | [Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43678423785/job/132703622723) |
| Fusion archive/API compatibility | 2,960 passed, 3 existing unavailable drawing-example skips, 515.95 seconds | [Fusion job](https://github.com/TryUniCAD/Kit/actions/runs/43678423837/job/132703567976)  |

A05b compares every file against the original complete report pinned at `480d9d3a`.
The outcomes remain 12 strict, 685 partial and 17 rejected; aggregate agreement alone cannot pass that gate.
These results verify reader integration and outcome stability, not geometry, constraints, dependency semantics or native conversion.

A08b now has passing process evidence for [bounded logs and cleanup](../../Changes/Research/Supervisor/BoundedSessionLogs.md), [version-scoped memory estimates](../../Changes/Research/Supervisor/VersionedMemoryEstimates.md), [adaptive limits](../../Changes/Research/Supervisor/AdaptivePoolLimits.md), [grouped sessions](../../Changes/Research/Supervisor/GroupedSmallFileSessions.md), [owner-epoch fencing](../../Changes/Research/Workers/SupervisorOwnerEpoch.md), [POSIX launch gating](../../Changes/Research/Supervisor/PosixWorkerLaunchGate.md) and [offline calibration](../../Changes/Research/Supervisor/OfflineDecoderCalibration.md).
The Linux log explicitly records a measured healthy-minute increase to two sessions and deadline-pair backoff from two to one.
Both POSIX selections include all fourteen calibration cases; no saturated throughput recommendation is established.
The earlier Windows calibration completed 100 decodes and fell short of the eight-worker overlap threshold. The subsequent 64-input sweep qualified all five levels, and the hosted cgroup trial verified kernel OOM backoff. [Matched Windows sweep](../../Changes/Research/Supervisor/SixteenWorkerCalibration.md#windows-sweep-with-the-warm-claim-helper), [kernel OOM witness](../../Changes/Research/Supervisor/HostedSupervisorOom.md)
The corrected `cdf53e1f` Windows and macOS research suites passed 29 and 74 cases respectively. [Windows run](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412625), [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43693322495/job/132748412270)

At `69b9b773`, Windows passed 42 research cases and macOS passed 90, including the recovery and dependency-input process cases. [Windows run](https://github.com/TryUniCAD/Kit/actions/runs/43701120684/job/132772337494), [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43701120684/job/132772337490)
At `fa7e92d8`, the Windows calibration passed. The claim-group restart fixture failed when its reader and replacement producer opened the same owner barrier pathname. The updated fixture publishes a separate immutable barrier per owner digest. At `b6ce2ec9`, all 55 Windows checks passed, including the updated fixture. [Earlier Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43725708342/job/132847061624), [passing Windows research job](https://github.com/TryUniCAD/Kit/actions/runs/43728415623/job/132855298282)
At `f15b9cea`, macOS passed 94 worker checks with one Linux-only skip, including the owner archive and its restart replay. Linux passed all 58 supervisor checks at `f15b9cea`. [macOS research job](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400795), [Linux research job](https://github.com/TryUniCAD/Kit/actions/runs/43730082272/job/132860400807)
At `8b65c015`, macOS again passed 94 worker checks with one Linux-only skip, including the archived Fusion retry. The Windows calibration sweep passed, while two ownership fixtures required restoration of the member-list interface. The follow-up restores that callable through a complete checked native list. [macOS retry](https://github.com/TryUniCAD/Kit/actions/runs/43733838789/job/132871965585), [Windows sweep and ownership cases](https://github.com/TryUniCAD/Kit/actions/runs/43733838789/job/132871965525)
At `3d683585`, hosted native archive and read/write checks passed. The pre-pilot activity report passed its process fixture on Linux, Windows and macOS. The Windows job passed 56 cases, macOS passed 95 with one Linux-only skip, and Linux passed all 58 supervisor checks. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43739105328)
At `62853433`, the Linux archive gate passed 162 cases, the native read/write gate passed 350 with 159 skips, and the supervisor passed 58. macOS passed 97 with one Linux-only skip, including the between-job restart and startup fence checks. Windows passed 61 and failed the single timeout-link case. Its rerun checks single cancellation publication and preserves the first attempt's terminal diagnosis. [Linux job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634724), [macOS job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634705), [Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43743507082/job/132901634428)
At `a006c275`, Windows passed all 64 supervisor checks, including first-attempt timeout linkage and failure to publish cancellation. macOS passed 97 with one Linux-only skip. Linux passed 163 archive checks, 350 native read/write checks with 159 skips, and all 58 supervisor checks. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43745878592)
Legacy no-owner controller calls and custom adapters without the fence capability remain explicitly unfenced.

A08c's five [durable-output intake](../../Changes/Research/Workers/DurableWorkerOutputs.md) cases passed on all three platforms.
The twelve [application transport/publication](../../Changes/Research/Workers/LocalApplicationDispatch.md) cases passed Linux/macOS.
Windows passed both unsupported-application parking cases and all four [immutable-record](../../Changes/Research/Workers/WindowsImmutableRecords.md) cases.
The revised sharing case proves refusal through CRT and native APIs plus successful same-path operations after handle release; successful pytest capture did not retain individual numeric error values.
These fixtures did not call native CAD APIs.
Licensed Fusion execution, automatic Fusion startup and CAD restart, batch resets and unattended operation remain open.
Completed and abandoned application spools stay retained until owner verification of actual controller acceptance; the completed-spool bound is 32 files and 520 MiB, not an OS write quota.

A04c records [hashed principal support candidates](../../Changes/Research/PrincipalSupportEvidence.md) for 25 measured identifiers, including three YZ variants.
Licensed traces resolve the principal-plane class in four captures and locate the enclosing profile transform in both traced YZ rectangle profiles. The public reader binds the P01/P03 support records and the later typed P04 face support and constraints. [Licensed loader observations](../../../re/solidworks/records/PrincipalSupportCandidates.md#licensed-loader-observations), [P04 face support](../../Changes/Research/Readers/SolidWorks/SolidWorksCutFacePlacement.md)
The [native-field refusal](../../Changes/Research/Readers/NativeFieldWriteRefusal.md) and [writer qualification](../../Changes/Research/Readers/NativeSemanticWriteQualification.md) regressions passed, preserving required-semantic refusal and destinations through real public/direct boundaries.
The full Fusion run also verifies the corrected explicit/inferred writer-ordering cases.
None of those refusals supplies the missing positive native qualification.

A02d has fresh owned SOLIDWORKS sessions for the 25 discovery files. The queue recorded passing controls, an unchanged source roster, observed process exit and acknowledgement. The standalone licensed P02 run verified all five circle archives before and after rebuild with healthy controls, zero recorded open errors and warnings, and unchanged source hashes. [Licensed discovery readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md), [licensed P02 readback](../../Changes/Research/Workers/SolidWorks/CircleBindingReadback.md)
The Fusion owner reported a licensed P01–P04 two-process capture on build 2706.1.17, including the corrected P04 support and participant bindings. The owner reported the separately integrated intake at a local revision. The shared qualification gate still needs to admit both sources. Automatic Fusion queue dispatch retains its A08c requirement. [Fusion native result](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6917450974), [Fusion intake checkpoint](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6918533807)
P05 stays reserved for holdout. Zero native pairs are qualified.
The Fusion owner also reopened the four pinned A05c radial archive controls on build 2706.1.17. All eight before/after recompute observations found one outer circular loop, the same sketch-owned circle as the radial or diameter dimension's operand, the original driving/reference state and a closed full-turn runtime evaluator. The saved Design and ASM parameter intervals retain their own archive meanings. The scoped packaged strict reader now binds the verified radial parameter graph for the single-circle XY controls. It preserves both driving and reference roles and keeps native writer admission separate. [Licensed circular observations](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921804904)

A06 waits for qualified A02d/A04c/A05c evidence. The [P01 and P03 archive comparison](../../Changes/Research/Readers/Comparison/RectangularPairEvidence.md) matches all fourteen principal perimeters, twenty-eight dimension sizes, and eight signed blind Boss displacements while preserving the tools' dimension and profile declarations. The [P04 archive comparison](../../Changes/Research/Readers/Comparison/ArchivedCutHistory.md) joins each Cut to its target and support on the earlier extrusion. All eleven pairs agree on the saved solid measurements, perimeter edges, Cut support plane, and compared extent fields. Fusion uses a midpoint with driving expressions, and SOLIDWORKS uses derived perimeter offsets. The hosted discovery gate includes blind versus through-all and an ambiguous edge control. The perimeter report now retains ambiguous alternatives with their endpoint distances. A07 paired rescans require the saved archive hash and format from the accepted report. Both changes passed local pinned archive replay at the [published checkpoint](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6919282530). A06/A07 qualification, A09 and both native writers retain their declared dependencies.
The [A11 origin-coincidence probe](../../Changes/Fusion/Authoring/FusionOriginCoincidenceProbe.md) generates a rectangle with a distinct sketch origin and verifies the archived constraint operands and observer slots against fourteen controls. The [sketch-owned dimension probe](../../Changes/Fusion/Authoring/FusionOwnedDimensionProbe.md) generates two direct driving parameters without global duplicates and compares their saved links with six P01 captures. The Fusion owner verified both fixed generated candidates on build 2706.1.17. Each candidate passed independent width and height edits, restoration and a separate fresh-process reopen. All eight controls passed. The native outputs retained a distinct corner-to-Origin coincidence, and the sketch-owned candidate retained exactly two owned drivers. This evidence covers the manual sketch-only probes. Queued native dispatch, source-derived target acceptance and the full A11 writer scope remain open. [Licensed Fusion witness](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921349933)

The [A07 signed depth search](../../Changes/Research/Inference/FusionSignedDepthSearch.md) replayed all eight P03 Fusion saves. Signed little-endian float64 centimetres matched both typed locations. The [affected replay](../../Changes/Research/Inference/FusionDepthAffectedReplay.md) queued one A03 rescan when the signed hypothesis changed to magnitude-only. Seven save predictions stayed unchanged. Which copy controls rebuild remains open.

The [A09 two-pad discovery grid](../../Changes/Research/Writers/SolidWorksTwoPadDiscovery.md) contains five licensed SOLIDWORKS saves with independent rebuild and edit measurements. Both owned native processes exited with code zero. The upper sketch followed a base depth change from 10 to 11 mm and returned to its original support on restoration. A07 qualification, the complete typed archive map, donor-free generation and native acceptance of the generated part remain open.

The [A12 rectangle field synthesis](../../Changes/Research/Writers/SolidWorksRectangleFieldSynthesis.md) regenerated 114 field spans across six P01 saves. The [sketch style replay](../../Changes/Research/Writers/SolidWorksSketchStyleFields.md) generated 60 visual records and widths. The [part bookkeeping emitter](../../Changes/Research/Writers/SolidWorksPartBookkeeping.md) independently constructed and read back a metadata container. Reference allocation, the remaining configuration streams and complete native part generation remain open.

The [A04c licensed support replay](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutSupport.md) matched the saved support owner, plane and visible cap area to both native observation phases on all eleven P04 parts. The [licensed sketch replay](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutDimensions.md) matched 132 dimension values and roles, 44 centering equation assignments, 264 ordered dimension attachment slots and 330 sketch relations.

The [independent circular Boss discovery](../../Changes/Research/Readers/SolidWorks/SolidWorksRadialDiscovery.md) traces the typed primary circle, driving diameter and Origin coincidence against three licensed source archives. A separate [native edit witness](../../Changes/Research/Readers/SolidWorks/SolidWorksDrivingEdits.md) confirms independent diameter and depth edits, restoration and fresh reopen on those source copies. Radial display ownership, circular profile return and native conversion qualify separately.

The [A04c face producer census](../../Changes/Research/Readers/SolidWorks/SolidWorksCensusFaceProducer.md) reports `BlindBoss` for all eleven P04 cut supports. The [expanded timeline census](../../Changes/Research/Readers/SolidWorks/SolidWorksDiscoveryTimeline.md) matched 818 comparisons, including 25 active configurations and 66 ordered authored features, at hosted merge `41084574`. The [profile section census](../../Changes/Research/Readers/SolidWorks/SolidWorksDiscoveryProfileSections.md) matched the area and centroid of all 36 licensed sections at hosted merge `b008c6a8`. The [local body replay](../../Changes/Research/Readers/SolidWorks/SolidWorksDiscoveryBodyMeasurements.md) matched volume and centroid for all 19 measured solids at `68f73df3`.

The [A04c parameter replay](../../Changes/Research/Readers/SolidWorks/SolidWorksDiscoveryParameterRoles.md) matched 25 named rosters, 101 driving dimensions and 22 equation-derived dimensions at `ff9f38d7`. Hosted merge `7d662f29` reproduced all 1,076 comparison results across the 25 files. The [extrusion direction replay](../../Changes/Research/Readers/SolidWorks/SolidWorksDiscoveryOperationAxes.md) added 30 profile links and 30 signed directions at `32647c26`. Hosted merge `918a148d` reproduced all 1,136 matches. Explicit body-scope controls and held-out qualification remain open. [Expanded hosted census](https://github.com/TryUniCAD/Kit/actions/runs/43777157645/artifacts/14186622487)

The [A08b grouped settlement change](../../Changes/Research/Supervisor/GroupedAdaptiveSettlement.md) excludes a physical worker group from adaptive capacity decisions when the controller fences every member's completion. The [deadline-pair event](../../Changes/Research/Supervisor/AdaptiveDeadlineEvidence.md) records both accepted physical sessions and their elapsed interval. At `786736c55`, 59 hosted Linux supervisor cases passed. The observed deadline pair recorded two distinct sessions, about 0.206 seconds between their accepted stop observations, and a numeric reduction from two workers to one. [Hosted Linux supervisor evidence](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986201011)

The [kernel OOM estimate](../../Changes/Research/Supervisor/KernelOomMemoryEstimate.md) doubles the persisted reservation floor for the affected kind, tool version and group size after one accepted, verified Linux kernel OOM. At hosted merge `b008c6a8`, the cgroup OOM increased the reservation from 64 to 128 MiB, the ordinary `SIGKILL` control stayed at 64 MiB, and both runs cleaned up successfully.

The [A08b capacity status](../../Changes/Research/Supervisor/LiveSupervisorCapacity.md) reports the running supervisor's last admission decision and per-kind reservations. It validates owner identity, configuration, pause generation and freshness before returning the observations. At `648ddf5c`, the live status checks passed in the 59-case Linux, 92-case Windows and 143-case macOS supervisor runs. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43774889237)

Codex owns the A08b Windows adaptive CPU follow-up on [PR #281](https://github.com/TryUniCAD/Kit/pull/281).
It depends on the existing supervisor resource measurements and keeps the configured CPU and memory reserves.
Exit requires a real Windows supervisor to observe a valid CPU interval and increase only when headroom and the existing interval permit it.
The 256-job Windows replay observed increases from nine to eleven with equal neutral digests and intact reserves.
[Windows adaptive CPU measurement](../../Changes/Research/Supervisor/Adaptive/WindowsAdaptiveCpu.md)

The [A08b controller capacity refusal](../../Changes/Research/Supervisor/ControllerCapacityRefusal.md) at `c4526025` reports a real A03 concurrency refusal alongside the locally calculated headroom. The two-pool case passed on Linux, Windows and macOS at `b9efdb5e`. The Windows job failed an independent SOLIDWORKS rearm case. The [sampled A03 capacity view](../../Changes/Research/Supervisor/ControllerCapacitySnapshot.md) at `863c157b` counts shared logical slots separately from physical worker sessions. Its grouped-plus-singleton process check passed on hosted Linux and macOS at `3cd136ad`. [Earlier workflow](https://github.com/TryUniCAD/Kit/actions/runs/43779565898), [capacity process results](https://github.com/TryUniCAD/Kit/actions/runs/43781577583)

The [A08b grouped offline calibration](../../Changes/Research/Supervisor/GroupedOfflineCalibration.md) accepted the same 64 pinned Fusion discovery archives once per arm and produced the same neutral output digest in two Windows runs at `50a4892b` and `ed0aa4bd`. The second run used 64 singleton sessions in 224.825 seconds and ten verified group sessions in 60.507 seconds. The grouped archive process case passed on hosted Linux and macOS at `f3e6b6cd`. Linux and macOS throughput remain unmeasured. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43777547783)

At PR head `5605c58f` and tested merge `c4f34448`, all 63 Linux supervisor cases and all 95 Windows supervisor cases passed. The [ambient reserve witness](../../Changes/Research/Supervisor/AmbientMemoryReserve.md) verified one limit reduction while both workers kept running and completed their first attempts. Linux separately verified healthy growth and the deadline-pair reduction. The kernel OOM artifact from the same merge records a limit decrease from two to one, an estimate increase from 64 to 128 MiB and verified cleanup. Its ordinary signal control held the limit and estimate. The separate macOS A08c two-pair acknowledgement case failed while waiting for the first replay marker. [Linux supervisor](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521405) · [Windows supervisor](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521425) · [Kernel OOM artifact](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/artifacts/14193359201) · [macOS application failure](https://github.com/TryUniCAD/Kit/actions/runs/43794606581/job/133060521248)

The [A08e archive verifier](../../Changes/Research/Workers/SolidWorks/OfflineRearmEvidence.md) checked 94 retained objects across four licensed Windows runs after their listeners exited. The P04 run at `5770f1b3` also proved replacement-supervisor recovery from separately pinned event and spool records.

The [Windows owner fixture](../../Gotchas/Research/Workers/WindowsOwnerFixtureCollector.md) now uses an isolated Python collector to supply its exit code. At `47de6ad0`, the updated owner and rearm cases passed in the 91-case Windows job. [Hosted Windows evidence](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/job/132992935662)

The [Windows process identity helper](../../Changes/Research/Workers/WindowsStdlibIdentity.md) reads the exact FILETIME through Python's standard library. Its isolated process case passed in the hosted run at `47de6ad0`. Windows Fusion Phase A also requires pinned peer helper loading, protected records and locks, and SID and desktop-session admission.

The [Windows record custody helper](../../Changes/Research/Workers/WindowsStdlibRecords.md) uses standard-library Win32 calls for protected reads and endpoint locks. All 92 hosted Windows supervisor cases passed at PR head `648ddf5c`, including the isolated protocol read and lock case and the live-capacity recovery case. [Hosted Windows evidence](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/job/132998931881)

The [A08e Windows Fusion Phase A admission](../../Changes/Research/Workers/WindowsFusionPhaseA.md) at `a01f6e7f` requires owner opt-in, pinned startup bytes and live same-owner, same-session process identity. The hosted open-document refusal used the actual A03 store, add-in bootstrap and queue with a disposable document-state stub. It passed in the 93-case run at `f3e6b6cd`. A licensed Windows Fusion capture remains open. Windows Phase B and the two-body scope workflow stay parked. [Hosted Windows job](https://github.com/TryUniCAD/Kit/actions/runs/43777547783/job/133007249020)

At `b9efdb5e`, Windows passed 93 cases and failed the SOLIDWORKS P01/P03 rearm case after its first accepted rearm. The [rearm timing repair](../../Changes/Research/Workers/SolidWorks/TimeoutRearm.md) at `d5281135` coordinates native cleanup with the exact disposable client's exit and cancellation. The supervisor counts completed settlement as progress before evaluating idle shutdown. All three repaired rearm cases passed on tested merge `e1fa7f1d`. That job reported a collection error and a separate calibration failure. The collaborator fix at `d7a2f3ce` renames the helper and gives only the Windows success sweep a 12-second lease. [Earlier rearm failure](https://github.com/TryUniCAD/Kit/actions/runs/43779565898/job/133013444004), [repaired rearm cases](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019771915)

The [hosted archive producer](../../Changes/Research/Controller/HostedPairedArchiveMergeParents.md) used the actual tested merge's first parent and checked the event base ancestry. At `41084574` and `7d662f29` it passed both archive checks, and the downloaded receipts matched their authenticated artifact digests. The separate consumer and batch release retain their pending evidence requirements. [Current hosted archive receipt](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/artifacts/14186525068)

The [Fusion restart intent](../../Changes/Research/Workers/FusionOwnerRestart.md) binds the accepted Phase A result, cleared acknowledgement, retained fence and exact earlier process. The [main-thread readiness grant](../../Changes/Research/Workers/FusionRestartReadiness.md) verifies an idle Fusion process with zero open documents before issuance and consumption. The [exit observer](../../Changes/Research/Workers/FusionQuitObserver.md) records the exact owned macOS process exit under that fence. Its first hosted run passed the disappeared and mismatched peer cases and failed four arming scenarios. The fixture now preserves the observer's failure output. The [owner-directed replacement](../../Changes/Research/Workers/FusionReplacementLaunch.md) submits one exact-bundle launch request, records the new process, and separately checks accepted Phase B evidence on that same process. A [disposable AppKit witness](../../Changes/Research/Workers/AppKitQuitDelegateWitness.md) covers normal quit acceptance and cancellation. Hosted verification of the new fixtures, automatic graceful quit and signed-in Fusion verification remain open. The [hosted paired archive receipt](../../Changes/Research/Controller/HostedPairedArchiveGate.md) records the exact tested tree and the public discovery gate when that workflow step succeeds.

At `786736c55`, all three disposable AppKit delegate cases passed on hosted macOS. Four Python observer cases refused the recorded peer identity at arming. The replacement fixture separately failed before the Swift provider returned the live peer. The signed-in Fusion witness remains open. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986201023)

At `47de6ad0`, all six Python exit-watcher cases and all three disposable AppKit delegate cases passed. The only hosted macOS failure was replacement launch. Its valid-bundle fence control refused the bundle before checking the fence. The [physical-path correction](../../Gotchas/Research/Workers/FoundationPrivatePathAlias.md) replaces the Foundation path alias comparison. [Earlier hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43772995626/job/132992935696)

At PR head `648ddf5c` and tested merge `7d662f29`, hosted macOS passed 143 cases with one Linux-only skip. The disposable replacement fixture rejected linked requests, changed pins, changed fences and duplicate launches. It also started the pinned bundle through LaunchServices and observed its normal exit. The licensed Fusion quit, replacement and native Phase B still need a signed-in macOS session. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43774889237/job/132998931836)

The [A08c Cocoa quit bridge](../../Changes/Research/Workers/MacCocoaQuitBridge.md) at `1a7d999a` invokes the existing AppKit instance on the native main thread. The disposable process fixture loaded the exact Git-pinned bridge and passed in the 145-case hosted macOS suite at `b9efdb5e`. Licensed use remains open. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43779565898/job/133013443832)

The [A08c guarded Cocoa quit](../../Changes/Research/Workers/FusionArmedCocoaQuit.md) at `9c5ab364` binds one request to the armed Darwin watch, exact accepted restart intent and idle, empty application. A fresh add-in keeps an outstanding automatic handoff fenced until it matches exact exit and authorized replacement evidence. The disposable process cases passed in the 154-case macOS suite at `3cd136ad`. A licensed Fusion run remains open. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019772047)

The [recoverable Fusion queue receipt](../../Changes/Research/Workers/FusionDurableQueueReceipt.md) at `0c9e9722` seals the exact submission intent before A03 commits the pair. It can restore the same receipt from the bound plan and the two job definitions after an interrupted publication. Its interruption case passed on hosted macOS at `3cd136ad`. [Hosted macOS results](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019772047)

The [resumable macOS owner coordinator](../../Changes/Research/Workers/FusionLifecycleOwner.md) at `03a21e5c` waits for the exact Phase B claim and advances guarded quit, replacement and accepted Phase B receipt publication. It keeps sealed ambiguous requests parked. The four coordinator recovery cases and the Swift launch-deadline refusal passed in the 158-case suite at `135e4b37`. Native Fusion acceptance remains open. [Hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43786827110/job/133036246862)

At `7e8e98b8`, the exact hosted Windows suite passed all 94 cases, including the three SOLIDWORKS rearm cases and the collaborator's renewable calibration lease repair. The macOS suite reached the 15-minute job timeout without publishing the lifecycle verdicts. The [macOS job budget](../../Changes/Research/Supervisor/MacSupervisorJobBudget.md) gives the full suite 20 minutes on the next run. [Windows run](https://github.com/TryUniCAD/Kit/actions/runs/43784421558/job/133028849181), [macOS run](https://github.com/TryUniCAD/Kit/actions/runs/43784421558/job/133028849064)

At `14f4a1f2`, all 95 hosted Windows cases passed, including the [standalone scope watchdog](../../Changes/Research/Workers/SolidWorks/ScopeWatchdog.md). The disposable collector and its child drained while an identical process outside the job stayed live. [Hosted Windows evidence](https://github.com/TryUniCAD/Kit/actions/runs/43788486237/job/133041436830)

The same revision passed 161 macOS cases with two platform skips. The [startup receipt](../../Changes/Research/Workers/FusionStartupProvision.md) and both [restart reservation](../../Changes/Research/Workers/FusionRestartResourceReservation.md) contention cases used disposable application processes. A signed-in Fusion session still needs to supply native Phase A and Phase B acceptance. [Hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43788486237/job/133041436716)

At `2bde5f07`, the [Fusion cold-start case](../../Changes/Research/Workers/FusionStartup/FusionOwnerColdStart.md) passed in the 162-case macOS suite with two platform skips. All 95 hosted Windows cases also passed. The P04 re-export refused its generated payload before the independent Linux supervisor stage. The [readback diagnostics](../../Changes/Research/Readers/SolidWorks/ParasolidReadbackErrors.md) retain the failing boundary on the next run. [macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099510), [Windows evidence](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099506), [Linux archive failure](https://github.com/TryUniCAD/Kit/actions/runs/43791586077/job/133051099512)

At PR head `27cb8d54` and tested merge `bcf9040b`, the macOS suite passed 164 cases with two platform skips. The [two-pair acknowledgement case](../../Changes/Research/Workers/FusionLifecycle/FusionPhaseBAcknowledgement.md) drained the lost reply before admitting the next pair. The [reset evidence case](../../Changes/Research/Workers/FusionLifecycle/FusionResetEvidence.md) replayed exact attempt identities and measured the disposable application's resident memory. Both cases used disposable app processes. Signed-in Fusion and the [owner's timeout archival](../../Changes/Research/Workers/FusionLifecycle/FusionOwnerProbeArchive.md) need their applicable follow-up evidence. [Hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43797562452/job/133069853452)

At `3cdcaca6`, the two-pair macOS case entered its replay barrier before confirming cleanup. The [fixture repair](../../Gotchas/Research/Workers/FusionLifecycle/FusionAckBarriersFollowCleanup.md) advances from the cleanup stage when the real acknowledgement has returned and the cleanup marker is visible. Hosted confirmation is pending. [Hosted macOS failure](https://github.com/TryUniCAD/Kit/actions/runs/43878525516/job/133337869233)

The supplemental two-body scope control holds Cut geometry fixed across All bodies, explicit A, and explicit A+B. The [earlier provisional SOLIDWORKS saves](../../Changes/Research/Workers/SolidWorks/AutomaticScopeRepeat.md) preserved both body owners and the same scope word despite distinct resolved stream hashes. The [typed archive replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopeTypedCut.md) closes both Bosses, identifies the Cut sketch on the first Boss cap, and reaches both scope entries. The second Boss has a 5 mm blind depth and separate 10 mm start offset. The [terminal Cut replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopeCutTerminal.md) binds both result choosers and the ordered atom/body pairs, reads the depthless through-all extent, and closes both 25,362-byte resolved streams.

The [licensed SOLIDWORKS run](../../Changes/Research/Workers/SolidWorks/ThroughAllScopeNativeEvidence.md) completed all three cases at `e3d1d66e` with independent reopen and rebuild. The [Fusion phase queue](../../Changes/Research/Workers/FusionPhaseQueue.md) accepts the same scope plan. Windows commissioning kept Phase A in `waiting_application` and Phase B in `waiting_evidence`. The licensed Fusion campaign and paired comparison remain open. [Fusion scope control](../../Changes/Research/FusionReadback/FusionScopeControl.md)
The [A04c active-partition replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopePartitionGeometry.md) independently measures both automatic-scope solids and all four cap openings in the two retained saves. Body A measures 7,200 mm³ and B 600 mm³. The [native body identity replay](../../Changes/Research/Workers/SolidWorks/AutomaticScopeBodyIdentity.md) joins each solid to its typed resolved body through a reciprocal shell chain and its saved atom attribute. The [packaged classifier](../../Changes/Research/Readers/SolidWorks/ParasolidLoopRoles.md) corrects twelve holed cap faces across all eleven P04 variants. The [scope case checkpoints](../../Changes/Research/Workers/SolidWorks/ScopeCaseCheckpoints.md) keep completed native case evidence and distinguish authoring and reopen failures. A fresh licensed explicit campaign is still required.

The [A13 public route preflight](../../Changes/Research/Readers/Comparison/RectangleRoutePreflight.md) recorded the first public refusal in both directions and independently isolated the next SOLIDWORKS source-history guard behind the support check. Bidirectional native acceptance remains open.

The [A15 activity report](../../Changes/Research/Supervisor/OfflinePilotEventReport.md) replays recorded controller activity to a fixed cutoff. The [private pre-pilot report](../../Changes/Research/Supervisor/PrivatePilotEvidence.md) combines a fixed controller window with independently sourced interventions, agent intervals, acceptance evidence and GitHub job timings. The [acceptance timing report](../../Changes/Research/Supervisor/PilotAcceptanceTiming.md) records readiness-to-acceptance duration and measurement coverage when the attestation includes a pinned readiness observation. Two [offline commissioning batches](../../Changes/Research/Supervisor/OfflinePilotCommissioning.md) measured scheduling, scoped invalidation and recovery after an interruption. The two-week A15 pilot remains pending.
The archived evidence replays and licensed readbacks above used their pinned inputs. Automated test suites run in hosted CI.

At e6cf245e, hosted Linux Pyright and the deterministic inference gate passed. The path policy still rejects four vendor DLL paths from earlier commits. The guard scans incoming ancestry and the new work passes the same guard on its own commit range. The PR remains open with its history preserved. [Hosted Python quality](https://github.com/TryUniCAD/Kit/actions/runs/43886272049/job/133365157974), [hosted inference](https://github.com/TryUniCAD/Kit/actions/runs/43886271791/job/133365360277), [path policy](https://github.com/TryUniCAD/Kit/actions/runs/43886272139/job/133365154858)

A16 includes richer part histories, assemblies, configurations and drawings, and additional CAD families. Each feature, format version and direction needs independent native acceptance after A13 and A15. The prior NX, CATIA and Creo pull requests closed without merging and supply research history for that audit. [Conversion backlog](../../Maintenance/ConversionBacklog.md#work-register), [NX PR](https://github.com/TryUniCAD/Kit/pull/115), [CATIA PR](https://github.com/TryUniCAD/Kit/pull/116), [Creo PR](https://github.com/TryUniCAD/Kit/pull/117)

All forty-one reported review threads were resolved at this checkpoint, but both configured native review reports were failed, one reported that review did not finish, and there was no approval for this head.
Green PR CI therefore did not establish readiness.
GitHub independently reported `REVIEW_REQUIRED` and enforced one approving review, code-owner review, last-push approval and resolved threads.
The PR merge-queue report does not establish successful heavy acceptance on an actual merge-group candidate.
No queue enrollment or merge was requested or performed.

## A08d deterministic research CLI compatibility

Owner: jdharcourt. Delivery: [separate CLI PR #119](https://github.com/TryUniCAD/Kit/pull/119).
The user clarified that the installed CLI belongs in its own PR and must remain compatible with PR #94's tools.
The CLI implementation, CLI-only tests, packaging changes, and guides are removed from this PR without rewriting history.
The research readers, controller, supervisor, export safeguards, and native decoding repairs remain here.
Compatibility checks in the separate PR select a pinned PR #94 checkout and preserve its existing document/receipt and runtime contracts.
No automatic model runner, persistent session-artifact ingestion, or native conversion qualification is claimed.

At PR #119 head `10f19a046a75d0409631eeb447af85167369132d`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016477) passed seventeen cases with one platform skip, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43666848649/job/132668016227) passed seventeen cases. Both jobs checked out PR #94 revision `b86f30c7e41abdc3812ada795a193377f6ddd220` explicitly.
The independently registered [CLI conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43666848335/job/132668015805) failed twelve kind-classification cases with 617 passes, so PR #119's CI aggregator failed. Research protocol passes do not make that separate PR ready, and they do not verify later PR #94 heads. That failed checkpoint is superseded by the results below; CLI changes remain in PR #119.

At PR #119 head `ffc86c978ebce37b855c9665b08780e311b94ff4`, [Linux research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633472) passed seventeen cases with one platform skip in 67.10 seconds, and [Windows research compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43669001024/job/132674633505) passed seventeen in 80.96 seconds. Both still pinned PR #94 `b86f30c7e41abdc3812ada795a193377f6ddd220`. The [conversion/inspection gate](https://github.com/TryUniCAD/Kit/actions/runs/43669001060/job/132674633067) passed all 639 cases in 381.82 seconds and the [CI aggregator](https://github.com/TryUniCAD/Kit/actions/runs/43668999659/job/132674630942) passed.

PR #119 merged into `main` at `249cf7dcde6197c41fafb052eda8afb210bcf49e`. Synchronizing PR #94 brings in that implementation and retains both sets of hosted checks. The next compatibility run selects the installed CLI and a separate research checkout at the workflow candidate SHA on Linux and Windows. A merge-queue shard uses the same checkout rule when it selects research CLI cases. [CLI delivery](https://github.com/TryUniCAD/Kit/pull/119), [candidate compatibility](../../Changes/Commands/ResearchCandidateCompatibility.md)

The two compatibility jobs for `a006c275` independently checked the installed CLI and isolated research checkout at the workflow merge SHA `8d66aa9b38bb3f436678cdad6af3206d0189fb51`. Linux passed 27 with one Windows-only skip and Windows passed 17. [Linux](https://github.com/TryUniCAD/Kit/actions/runs/43745878592/job/132908934845), [Windows](https://github.com/TryUniCAD/Kit/actions/runs/43745878592/job/132908934840)

PR head `b9efdb5ee15da0f802880b97816a8422865545b4` repeated the installed CLI verification on exact tested merge `e60486e0532b92b66a5637a490acea934cb03959`. Both jobs asserted that the installed source and the physically separate research checkout matched the candidate SHA. Linux passed 27 cases with one Windows-only skip. Windows passed 17 cases. The result completes the installed CLI compatibility milestone for the selected reader, receipt, controller and supervisor contracts. Native qualification remains open under its owning steps. [Linux compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43779565898/job/133013443659), [Windows compatibility](https://github.com/TryUniCAD/Kit/actions/runs/43779565898/job/133013444080)

### A08d-PinnedReaderBatches: pinned corpus reader overhead

Codex owns this checking task on `codex/pinned-decoder-batches`, based on main `14570404846c8aa1f90b02e68d6f70a419719ca7`.
Delivery is [PR #279](https://github.com/TryUniCAD/Kit/pull/279).
Dependencies are the A04a and A05a readers, the sealed A02 corpus, and the A08d CLI bridge.
The scope covers Git transport for both formats, the additive SOLIDWORKS batch, and the feature inventory session.
The exit requires public CLI timings, exact neutral byte comparisons, intact pin and refusal behavior, current-head CI and configured review.
At reader revision `654f00108c3e151c28b5e3e84eb48bd2ff7f9f2a`, the three-part SOLIDWORKS median fell from 37.20 s to 17.97 s.
The eight-part Fusion median moved from 16.93 s to 17.01 s with fifteen fewer blob processes.
The measured neutral documents matched exactly in both comparisons.
See the [change entry](../../Changes/Research/Offline/PinnedReaderBatches.md).

### A08d-FileScopeAttribution: stream provenance for strict Fusion inputs

The Codex shared encoder worker owns this checking task on `codex/deterministic-encoder-admission`.
Delivery is [PR #298](https://github.com/TryUniCAD/Kit/pull/298), based on the [encoder round-trip branch in PR #297](https://github.com/TryUniCAD/Kit/pull/297).
Dependencies are the A08d file-driven CLI, source-bound Fusion decode layers, and the container member inventory.
The exit requires a real CLI run with strict features, source-bound partial spans, and both saved reports.
The existing partial-only P04 run must preserve its recipe selection and incomplete coverage result.
Both installed CLI cases passed on Windows at `d3b2cb982c` in 84.79 seconds. Hosted verification and review remain pending.
See the [change entry](../../Changes/Research/Encoder/FileScopeAttribution.md) for the range and qualification limits.

## A08h-Placement20261123: decimal native reader evidence

Codex owns this evidence publication on `feat/native-placement-decoding-20261123`, from main `f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2`. Delivery PR is [#274](https://github.com/TryUniCAD/Kit/pull/274).
The [package](../../../re/NativePlacement2026/README.md) retains 47 complete native batches, one COM failure, 143 saved native files and all 255 committed-input replay outcomes. One expected after-control is missing.
Dependencies are merged PRs #263, #265 and #267, the deterministic controller and licensed source workers. All executable capture/replay work has settled; publication CI and configured review remain pending.
[PR 270](https://github.com/TryUniCAD/Kit/pull/270) owns the SOLIDWORKS attachment implementation. Its exact `78a1367e81b5748702289c2b2e733f24576df46e` candidate passes 138 comparisons on 69 fresh complete-batch inputs. [PR 269](https://github.com/TryUniCAD/Kit/pull/269) owns the remaining Fusion placement/sign investigation; this scope supplies fresh decimal controls.
The exit requires sealed hashes, sanitized provenance, native/neutral comparisons, retained refusals/failures and current-head publication readiness. Numerical source acceptance is limited to the recorded cuboids. Full semantics, generative writing and editable target conversion remain open under B02–B05; this task does not duplicate either owning PR or close those milestones.

## A08h-CutsRevolutions20261123: cut and revolution evidence

Task `A08h-CutsRevolutions20261123` is owned by Codex on `feat/native-feature-campaign-20261123b`. Delivery PR: [#278](https://github.com/TryUniCAD/Kit/pull/278).
Dependencies are merged PRs #158/#207, the verified catalogues, existing controller and licensed personal API.
The [campaign summary](../../../re/CutsRevolutions2026/README.md) retains exact native scopes, cut sign failures, correction attempts, COM failures and strict reader outcomes.
The same scope now repairs signed Fusion depth authoring and qualifies plain negative millimeter literals in the production reader against native discovery and parameter-holdout inputs. Exit requires measured public CLI decoding, retained conversion refusals, complete outcome accounting and current-head CI and configured review.
Native integration gaps, complete sketch and feature semantics, and editable target conversion remain open under B02–B05.
Existing SOLIDWORKS PR #121 and revolution PR #244 retain their separate delivery ownership.

## A08h-LargeSolidWorksBatches: larger fresh verification groups

Codex owns the scope on
[`codex/solidworks-large-verification-batches`](https://github.com/TryUniCAD/Kit/tree/codex/solidworks-large-verification-batches).
It builds on the paired-case batching delivery in
[PR #288](https://github.com/TryUniCAD/Kit/pull/288). New plans group up to
twelve cases while older plans retain their immutable jobs. The exit requires
revision-bound Windows preparation, previous-job compatibility, native
authoring and independent reopen of a full batch, and current CI and review.
See the
[change entry](../../Changes/Research/Supervisor/Catalogue/LargeSolidWorksVerificationBatches.md).
A licensed run accepted 12 selected cases and 111 archives at
`1afeb59cc9a86f5e8a7ce981126a254073a806ac` with two normal process exits.
All twelve offline decoder jobs completed. Hosted CI and review remain open.

#### A08h-RimFillet20261125: circular rim fillet read/write packs

Codex owns this checking task on `feat/native-conversion-campaign-20261125`, based on main `66d4f5b856833833bbf67fe62a61c3450d8dc76f`.
Delivery: [PR #301](https://github.com/TryUniCAD/Kit/pull/301).
Dependencies are the native API, source-free constructor, controller and typed codecs.
The [pack](../../../re/Fusion/RimFilletPack/README.md) retains 48 passing native checks, 12 exact generated-payload cycles, five native-source cycles and seven snapshot-width refusals.
All strict neutral and public conversion refusals remain explicit.
The exit requires revision-bound native evidence, shared-suite regressions, current-head CI/review and retained failures.
The bounded width repair now has 22 passing complete-model/native comparisons, six measured depth edits and four post-freeze cases in the [qualification pack](../../../re/Fusion/RimFilletPack/Qualification/Audit.json). Original failures remain retained. Current-head CI/review remains the delivery gate; B02–B05 and complete neutral conversion remain unfinished.
