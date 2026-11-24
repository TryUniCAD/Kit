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

The measured native run used source `231ffae38c7a9ca83705c6705e7d382d05c1e208` and SOLIDWORKS build `34.4.1` on Windows.
One authoring process created P01, P03, and P04 baselines.
A separate verification process reopened all 25 saved baseline, edit, and variant files.
Both processes exited normally, with no forced cleanup.
All three cases passed the existing native checks, including healthy controls, driving edits, restoration, and fresh-process reopening.

The accepted batch automatically released three separate decoder jobs.
Their measured process intervals overlapped at a peak of three.
All four controller jobs completed on their first attempt, with no supervisor failures.
The [sanitized acceptance summary](../../../../../re/automation/BatchEvidence/PairedCaptureAcceptance.json) retains source fingerprints, native measurements, job identities, and receipt digests.
The native dependency fingerprints also match the later test-only revisions.

The command returned `2`, `coverage_incomplete`, because the decoders retained unresolved semantic findings.
Portable completeness and conversion qualification remain false.
This measurement establishes the three-case batch operation. Other native recipe modes retain their separate qualification requirements.
It establishes two application launches for this batch. It does not establish a general throughput improvement.

Process checks cover new and saved-plan submissions, a store created by pre-change code, per-case artifact selection, mixed preparation, duplicate rejection, and path limits.
Native compiler checks exercise mixed P01–P05 and written-recipe batches through Windows PowerShell 5.1.
Current-head CI and configured review are tracked on [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Merge-group acceptance remains separate.

Task `A08h-PairedBatch`, owned by Codex, depends on the existing catalogue authoring, native ownership, and controller artifact contracts.
Its exit requires native batch verification, separate accepted decoder receipts, and current-revision CI and review.
The owning register is [automation steps](../../../../Reference/Research/AutomationSteps.md).
