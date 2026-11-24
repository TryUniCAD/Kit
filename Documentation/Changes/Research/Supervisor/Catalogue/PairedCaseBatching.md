# SOLIDWORKS paired-case batching

New SOLIDWORKS catalogue authoring runs automatically batch P01–P05 cases with the existing written-recipe cases.
Each batch contains at most three configured cases.
The authoring process handles every case before closing.
A separate process then reopens and measures each case's saved files.
This reduces a three-case batch from six application launches to two.

## Use

Use the existing `kit run --root CHECKOUT solidworks` command with `--author-samples` and the configured native host.
No extra batching option is required.
The `--authoring-grid three-values` option also uses the batch path.
Each case retains a separate native bundle, decoder dependency, measurement record, and acceptance result.
Decoder jobs start automatically when their batch's native evidence is accepted.

New plans record `solidworks_batch_version` as `1`.
Saved plans without that field retain their original single-case P01–P05 job definitions during resubmission.
Resume requires the original source revision and saved configuration.
Use a fresh output directory to start a run with this change.

## Limits

One owned SOLIDWORKS process runs at a time.
Restarting between authoring and independent verification remains required.
The three-case limit bounds the retained batch and its failure scope.
A failed native phase prevents that batch's decoder jobs from consuming unverified files.
Native path checks include a conservative bound for legacy edit-value filenames.
The single-case worker remains available for existing plans.
The existing hidden read-only control close path now applies to leading controls in empty owned sessions.
The [repeated-control finding](../../../../Gotchas/Research/Workers/SolidWorks/RepeatedStockControlClose.md) records the stalled native proof and the repair.

## Verification

Verification is in progress on `codex/solidworks-capture-batching`.
Process checks cover new and saved-plan submissions, per-case artifact selection, mixed recipe preparation, duplicate rejection, and long-path rejection.
Native compiler checks exercise mixed P01–P05 and written-recipe batches through Windows PowerShell 5.1.
Real native batch acceptance, automatic decoder execution, hosted CI, and configured review remain pending.
No throughput or CAD conversion acceptance claim is made from these checks.

Task `A08h-PairedBatch`, owned by Codex, depends on the existing catalogue authoring, native ownership, and controller artifact contracts.
Its exit requires native batch verification, separate accepted decoder receipts, and current-revision CI and review.
The owning register is [automation steps](../../../../Reference/Research/AutomationSteps.md).
