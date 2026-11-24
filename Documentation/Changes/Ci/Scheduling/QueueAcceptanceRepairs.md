# Queue acceptance repairs

Task: CI-QueueAcceptance; owner: Codex; delivery: [PR 285](https://github.com/TryUniCAD/Kit/pull/285).
Scope: acceptance fixture repairs and live queue scheduling recovery.
Dependencies: the existing containment implementation and PR 278’s measured signed-depth grammar.
Exit: current-head PR checks and configured approval, then successful native queue acceptance and live settings readback.

## Provider identity

On Windows, the cleanup fixture now records a child PID and creation identity before the provider exits.
Its independent probe compares both values after cleanup.
A reused PID cannot identify an unrelated process as a surviving provider child.
The existing job-object containment, verified-termination receipt, and no-surviving-child assertions remain required.
Missing Windows identity evidence fails the probe.
Other platforms retain their existing post-cleanup live-process check.
The timed provider does not start a new macOS `ps` identity query.
A missing provider receipt fails explicitly without increasing the one-second provider timeout.

The [failed Windows job](https://github.com/TryUniCAD/Kit/actions/runs/45384866420/job/138413726421) reported a live PID after verified job termination.
The old fixture recorded no creation identity, so its log cannot distinguish PID reuse from a surviving child.
The change repairs that ambiguous measurement; a fresh native Windows run remains required.

## Qualified Fusion grammar

The original signed-prism harness rejected plain negative millimeter literals.
[PR 278’s evidence](https://github.com/TryUniCAD/Kit/blob/8dab4096c2cf8267b9d3ce8a2a8b2801398b3bdd/re/Fusion/Reconstruction/SignedDepth/README.md) qualifies that spelling alongside wrapped literals.
The old refusal therefore contradicts the new measured contract.

The harness now requires rejection of an arithmetic formula instead of rejecting the qualified literal.
It accepts only the two exact grammar diagnostics from the legacy and current reader revisions.
Every mutation still requires successful wire decoding followed by the intended strict semantic rejection.
Numeric disagreement, physical depth, zero depth, taper, units, ownership, cached mass, and section-link refusals remain unchanged.
No product parser, native writer, or conversion qualification changes here.

## Live queue recovery

The requested live values are two candidate builds, one minimum merge entry, zero batching wait, and the documented ninety-minute response timeout.
All required checks, review rules, grouping strategy, bypass actors, and other protections must remain unchanged.
The authenticated API connection rejected the minimal ruleset update with HTTP 404 on 24 November 2026.
The available browser was signed out and could not apply an authenticated update.
The prepared request is `/tmp/KitQueueRulesPatch.json`; it contains the existing rules with only those four queue parameters changed.
The live queue therefore remains uncorrected until an authorized administration connection applies and reads back those values.

Formatting and static diff inspection are the local checks.
Tests remain on the existing shared-suite planner and native platform shards.
Remote verification of this repair revision is pending.
See [provider identity](../../../Gotchas/Ci/Scheduling/ProviderCleanupIdentity.md) and [qualified grammar transitions](../../../Gotchas/Ci/Scheduling/QualifiedLiteralRefusals.md).

## Deterministic report compatibility

Candidate `640378100f7bfb0af414829042cd19235a718623` completed the strict geometry command but failed its historical report hash.
The reported hash was `6452d4aa5148435e1ed6c790ddcb4b4ec46e415d274e2d813fb1581f6f1b13db`.
The deliberate replacement of `unwrapped_literal` with `reverse_formula` changes that report entry.

The archive comparison now requires exactly one new formula-refusal entry with one of the two known exact diagnostics.
It also requires the obsolete refusal entry to be absent.
Only that entry is normalized for comparison with the unchanged historical digest.
The actual command report retains its real case name and diagnostic.
Every other report byte, including geometry, capture custody, measurements, and all remaining refusal outcomes, remains pinned.
The verifier still rejects a command that accepts the arithmetic formula.
Fresh candidate acceptance must verify that this single deliberate delta explains the digest difference.
