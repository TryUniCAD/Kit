# Hybrid planner contracts

These proposed contracts extend the [existing research programme](Decision.md#context-and-current-ownership).
They are not new implemented APIs or commands.
Version records and preserve their source revision, stable identity and provenance.

## Records and identity

| Record               | Required fields                                                                                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Family specification | Format/family IDs, recipe hash, prerequisites, typed parameters, units, ranges, legal combinations, coverage, controls, holdout policy, capabilities and limits |
| Coverage obligation  | Specification version, required slice, planned samples, completed evidence, impossible-cell reasons and outstanding work                                        |
| Hypothesis           | Field IDs/spans, registered formula and arguments, evidence references, predictions and failed tests                                                            |
| Proposal             | Specification version, recipe, complete parameters, hypothesis IDs, distinct predictions, target fields and estimated costs                                     |
| Job                  | Stage/source hashes, input artifact hashes, dependencies, key, runner requirements, reservations, state and attempts                                            |
| Artifact             | Content hash, size, kind, relative location, producing attempt, native version and integrity result                                                             |
| Decision             | Candidates, deterministic scores, selected job, rule version, cost estimates, response hashes and rejection reasons                                             |
| Result               | Outcome, failure class, outputs, unresolved fields, cleanup state, runner health and measured costs                                                             |
| Budget               | Sample, attempt, elapsed, CPU, token and monetary limits, consumed totals and outstanding reservations                                                          |

Use finite canonical numbers and explicit units in sample keys.
Include specification, recipe, parameter and compatibility versions.
Stage keys also include input hashes, implementation source, decoder version and relevant options.
Give each attempt a separate directory and identity.
Never overwrite previous evidence during a retry.

## Deterministic selection

1. Validate prerequisite IDs, cycles, parameter domains and available capabilities before side effects.
2. Count the grid before expansion or authoring.
   When it exceeds budget, use an explicitly configured reduced design or park.
   Record the reduced design's coverage guarantee.
3. Generate control pairs and required coverage slices reproducibly.
   Allocate the configured holdout partition from a recorded seed.
4. Seal holdout observations from advice and fitting.
   After a failed holdout informs a repair, allocate fresh independent validation before acceptance.
5. Rank families using weighted backlog, dependency unlocks, measured cost, waiting age and stable identifiers.
   Record every scoring term and scheduler epoch.
6. Deduplicate queued and completed samples.
   Track impossible cells separately from successful coverage.
   Preserve explicit starvation prevention and sample caps.

## Model proposal validation

Send bounded training evidence, unresolved fields, allowed recipes and competing hypotheses.
Exclude credentials, unrelated files and sealed observations.
Treat document text as data rather than instructions.

Use a configured provider behind the existing A10 boundary.
Verify actual provider API parameters and pricing when implementing the adapter.
Persist requests, schema/model settings, responses, usage, latency and rejection reasons.

Validate proposals before dispatch:

1. Check schema, size, specification version and referenced hypothesis identities.
2. Validate the recipe, parameters, units, bounds and legal combinations.
3. Evaluate each predicted observation through registered formulas.
4. Reject equivalent predictions, duplicate work and holdout conflicts.
5. Reserve resource and model budgets atomically.
6. Rank valid contrasts by hypothesis pairs separated per estimated cost, with stable ties.
7. Execute through the normal worker path and compare measured observations with predictions.

Model confidence is neither the selection score nor an acceptance criterion.
Hypotheses without executable predictions remain investigation notes.
They cannot independently authorize new captures.
Use the programme's fixed escalation, repeated-failure routing and cost limits.
Persist no-progress counts and park when the configured bound is reached.
Keep schema retries and provider retries inside the same overall budget.
Reconcile reservations against actual usage, retaining conservative charges when billing is uncertain.

## Durable execution

Reuse the programme's local SQLite ledger and immutable artifact contracts.
Do not introduce another store or share SQLite over a network filesystem.
Remote workers return manifests through the existing transport.
Publish verified artifact files atomically before committing their references.

Preserve existing job states and migration compatibility.
Add new states only through versioned migrations and process-level recovery checks.
Dependencies require verified successful results before releasing a consumer.
Claims, resource limits and budget reservations remain atomic.

Dispatch carries a fencing token.
The worker rejects stale ownership and unresolved previous capture attempts.
Lease expiry does not establish that a native action stopped.
Reconcile documents and published artifacts before retrying an uncertain capture.
Pure analysis may rerun idempotently against identical source-bound inputs.

Pause prevents new dispatches.
Stop also cancels pending advice and queued work.
Native work records its outcome at a safe boundary and closes only owned documents.
Unsafe cleanup halts the runner under the existing lifecycle protocol.
Neither operation force-quits an application or closes unrelated documents.

## Compute accounting

Record elapsed time, process CPU time, queue delay and peak resident memory by stage.
Measure native work in the actual application or worker process.
Orchestrator CPU does not represent Fusion's compute cost.
Unavailable metrics carry an explicit reason instead of a fabricated zero.

Separate application startup, document creation, feature construction, rebuild, inspection, export, reopen, edit/restore and close.
For decoding, separate imports, loading/decompression, indexing, projection and geometry reconstruction.
Measure formula search, coupling, generation, regression and model requests independently.
Nested stages expose inclusive and exclusive costs to prevent double counting.

Tag cold/warm state, sample size, features, versions, decoder mode and instrumentation.
Record host load and memory-pressure observations where available.
CPU totals may exceed elapsed time because multiple threads execute.
Label environmental outliers and retain the original measurements beside clean reruns.
Keep partial-decoding diagnostics with timings.
Do not extrapolate a format-wide maximum from one cylinder.

## Acceptance

Report coverage, unexplained fields, hypothesis eliminations, rejected proposals and native proof results separately.
A completed or parked investigation does not establish qualified support.
Retain all [CAD acceptance requirements](../../Operations/CadSuccessCriteria.md), including independent controls and editable native history.
