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
Native recovery and stage measurements remain pending.
