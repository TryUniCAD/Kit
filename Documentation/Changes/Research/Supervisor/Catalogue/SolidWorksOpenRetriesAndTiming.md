# Retry SOLIDWORKS startup and measure capture stages

SOLIDWORKS startup now permits three attempts before it reports failure.
Each attempt waits up to 120 seconds for the exact owned process to expose automation.
Failed startup processes must exit before the next attempt begins.
Cleanup verifies the held process identity and preserves unrelated sessions.
Retries occur before authoring starts and do not replay partially completed captures.
The persistent owner's startup deadline is 450 seconds, including retries and cleanup.

Native part opens also permit three attempts, separated by one second.
The last attempt must satisfy the original error and warning checks.
Before retrying, the returned document must close, document counts must match, and saved bytes must remain unchanged.
An unsafe cleanup or changed file stops the operation immediately.

`first-startup.json` and `second-startup.json` retain every launch result and elapsed time.
The corresponding `.jsonl` files publish launched identities before attachment.
`open-attempts.jsonl` retains each file-open result, error, warning and elapsed time.
Per-case `first-timings.json` and `second-timings.json` separate baseline authoring, baseline reopening, edits, variants, saved-file verification and healthy controls.
File-open timing includes retries and their delays.
Stage timing includes the actual work and document closure within each stage.
These are diagnostic observations and do not establish fresh-process CAD acceptance.

Task `A08c-SolidWorksOpenRetry` is owned by Codex on `codex/solidworks-open-retry`.
It depends on the continuous capture implementation in [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Its exit requires native compilation, bounded failed-launch evidence, a recovered native launch, stage measurements and current-revision CI and review.
Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Eleven Windows process and installed-interop compiler checks passed before publication.
At `d36d7d4806`, an injected first-launch exit recovered on attempt two.
Two P03 batches then shared the recovered process, with public decoding overlapping the second batch.
A separate process matched the same saved baseline measurements, and both completed processes exited without forced cleanup.
The complete comparison took 145.25 seconds.
Startup, including the failed attempt and delay, took 6.47 seconds.
The warmed second case spent 3.36 seconds authoring its baseline, 2.98 seconds generating edits and the unit variant, and 6.67 seconds building other variants.
Verification of all eight saved files took 14.56 seconds.
Its initial baseline reopen, rebuild and repeat save took another 2.19 seconds.
These P03 timings do not establish a general instance ratio.
See the [sanitized observation](../../../../../re/automation/BatchEvidence/OpenRetryTimingObservation.json).
A forced part-open failure was not induced.
The original receipt-shape rejection and its correction are [recorded separately](../../../../Gotchas/Research/Workers/SolidWorks/NativeOpenStatusShape.md).
Current-head CI, configured approval and merge-group acceptance remain separate gates.
