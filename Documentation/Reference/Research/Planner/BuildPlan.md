# Whole hybrid planner build plan

This plan covers deterministic coverage, optional model proposals, execution, evidence, native integration and cost comparison.
It extends existing programme work rather than replacing the controller.
Read the [decision](Decision.md) and [contracts](Contracts.md) first.

## Planning task register

| Field          | Value                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| Task ID        | HybridPlannerPlan                                                                                            |
| Owner          | Codex, requested by Stephen316                                                                               |
| Scope          | Design and implementation milestones only                                                                    |
| Status         | Proposed planning supplement; no implementation claimed                                                      |
| Dependencies   | Existing A03/A07/A08/A09/A10 contracts and independent native acceptance                                     |
| Delivery       | This separate PR, branch `codex/hybrid-planner-main`, targeting `TryUniCAD/Kit:main`                         |
| Exit condition | Reviewable whole-build plan, accurate programme mapping, validation contracts and documented evidence limits |

Implementation owners must claim their scoped work in the active programme register before coding.
This document does not claim existing tasks or override their delivery PR.
Update this supplement when a dependency, owner or evidence boundary changes.

## Existing programme mapping

The [inspected register](Decision.md#context-and-current-ownership) supplies the following starting point.
Refresh its revision before implementation.

| Programme step | Existing scope                                        | Proposed planner work                                                                                    |
| -------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| A02            | Pinned corpus and paired recipes                      | Add explicit coverage obligations and sealed validation partitions                                       |
| A03            | Durable controller and evidence store                 | Reuse persistence, leases and invalidation; extend only missing proposal/reservation contracts           |
| A07            | Deterministic inference and priority scheduling       | Add bounded contrast selection and measured-cost scoring without weakening current evidence requirements |
| A08            | Controlled workers and supervisor                     | Integrate approved recipes, fencing, capture reconciliation and per-stage metrics                        |
| A09            | Field maps and typed codec candidates                 | Consume proven formulas and retain unresolved ownership                                                  |
| A10            | Optional model investigation                          | Add structured proposals, prediction checks, replay and cost comparison                                  |
| A13/A14/A15    | Native acceptance, regression and unattended evidence | Preserve all gates and record whether advice reduces measured work                                       |

Keep the existing models-off path operational.
Use the installed [research CLI](../../../Tasks/ResearchCommandLine.md) for user-facing execution.
Extend commands through their owning delivery scope instead of bypassing the launcher with private scripts.

## Implementation structure

Extend `re/automation/` in the programme's trusted research checkout.
Reuse its controller, evidence, inference, worker and supervisor modules.
Do not create another planner service, database, artifact protocol or production conversion dependency.
Use focused modules for catalog validation, coverage, proposal validation, scoring, accounting and reports.

Keep maintained guides in `Documentation/`.
Add integration, compatibility and end-to-end coverage through the existing suite and merge-queue execution path.
The research exemption does not qualify a production feature or native output.

## Dependency-ordered milestones

### A. Inventory and contract gaps

Inspect the exact accepted controller, inference, worker and model-packet revisions.
Map the proposed records to existing schemas and identify only missing contracts.
Record source hashes, ownership, migrations and required recipes.

**Pass:** every proposed capability is classified as reused, needing extension or blocked.
Preserve current job identities, immutable evidence and historical acceptance records.

### B. Fixed coverage and deterministic selection

Implement missing family specifications, lazy grids, interaction coverage, controls, sealed holdouts and deduplication.
Record priority terms, cost estimates, impossible cells and starvation prevention.

**Depends on:** A.
**Pass:** equivalent state produces the same plan.
Every required legal cell is covered or explicitly blocked.
Oversized grids fail or select a configured reduced design before authoring.

### C. Reservations, recovery and compute metrics

Extend existing resource and budget admission for sample, CPU, elapsed, token and monetary limits.
Preserve fenced claims and reconcile uncertain native attempts before retry.
Add missing stage clocks, memory accounting, cancellation and resumable reporting.

**Depends on:** A and B.
**Pass:** process-level failure scenarios preserve verified evidence and avoid duplicate native work.
Two claimants cannot capture concurrently in Fusion.
Nested metrics have independently checked totals.
Pause and stop prevent new side effects without closing user documents.

### D. Real Fusion investigation pilot

Use an approved parametric extrusion recipe with controlled dimensions and modes.
Run its grid through actual authoring, export, decoding and evidence comparison.
Respect authorization, capture holds, owned-document cleanup and application health.
Keep SDK projection and research decoding separate.

**Depends on:** B, C and the existing A08 worker prerequisites.
**Pass:** real archives, controls, decoded observations and unresolved fields have source-bound receipts.
Measure cold/warm startup and each native/decoder stage separately.
No model calls occur in this fixed-only pilot.
Unavailable geometry or semantics remain unresolved.

### E. Optional model-directed experiments

Extend A10 packets with competing executable predictions and typed experiment proposals.
Add deterministic validation, duplicate rejection, budget reservation and decision replay.
Preserve the existing escalation and repeated-failure routing contracts.

**Depends on:** D and the programme's A07/A09/A10 prerequisites.
**Pass:** malformed, unsupported, duplicate, indistinguishable and holdout-leaking proposals fail before capture.
Timeouts and exhausted limits terminate predictably.
Stored advice replays without a provider call.
Fixed-only operation requires no provider credential.

### F. Field ownership, proof and regression

Integrate proven field maps with independently generative codecs.
Retain strict semantic coverage, fixed points, native geometry/tree checks and independent driving-dimension edits.
Include restoration, save/reopen and healthy controls.
Do not treat typed ownership or reproduction of a vendor save as independent byte generation.

**Depends on:** D and the relevant A09/A11/A12/A13/A14 capabilities.
**Pass:** residual bytes, unresolved required fields and failed native checks prevent support completion.
Unavailable writers remain blocked rather than replaced by recorded field programs.
Regression failures prevent completion commits and retain evidence.

### G. SOLIDWORKS integration

Reuse the programme's Windows worker, recipes, debugger traces and bounded recovery.
Apply the same proposal, coverage and compute contracts.
Use the existing solved-family research evidence as a control without restoring donor-based writers.

**Depends on:** C, F's proof contracts and the native worker prerequisites.
**Pass:** native Windows evidence validates authoring, tracing and owned cleanup.
Segmentation re-emission remains a diagnostic, not proof of a generative writer.
Missing native acceptance blocks qualification without blocking independent offline work.

### H. Comparison and operating release

Compare fixed-only and hybrid modes from equivalent evidence, recipes and cost caps.
Use a solved control and an unresolved case with executable competing predictions.
Predeclare tasks, stopping rules and sealed final validation.
Alternate mode order across repeated runs and tag cold/warm conditions.

**Depends on:** E, F and G for each declared format scope.
**Pass:** advice preserves coverage and proof gates while all costs remain bounded.
Report captures, bytes explained, confirmed hypothesis eliminations, parked work, elapsed/CPU time, memory and model spend.
Include unsuccessful advice and environmental outliers.
Keep advice disabled by default if no measured benefit appears.
Retain A15's unattended operating requirement instead of substituting one successful run.

## Validation and handoff

Use process-level integration scenarios for schema validation, durable state, invalid advice and replay.
Inject failures before dispatch, after native completion and during artifact publication.
Run native checks explicitly on their supported hosts through the existing acceptance path.
Ordinary offline checks must work with CAD applications unavailable.

Record exact source revisions, commands, outcomes and unresolved conditions for each milestone.
An interface or simulated success does not complete an integration milestone.
Do not claim the planner or all CAD routes are implemented when this planning PR is accepted.
Re-estimate delivery after A through D establish integration costs.
