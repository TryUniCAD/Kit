# Verify large generated planning review coverage

The hosted reviewer found the deliberate CLI defect in temporary PR #401 and recognized its repair.
The [repair review](https://github.com/TryUniCAD/Kit/pull/401#pullrequestreview-6099686787) could not approve head `fa405f5b0710d5cc971985901232519a9acaba63` because both generated BoardData files exceeded the source limit.
This change adds exact reconstruction evidence for those two derived outputs without raising model input limits or trusting a proposed generator.

## Coverage requirements

Only modified `Documentation/Planning/Generated/BoardData.json` and `BoardData.js` qualify.
The live target and merge base must equal the trusted workflow revision.
Every tracked Python file in the planning generator and every other recorded generator dependency must remain byte-identical to that revision.
Only changes to `Links.json` and `PullRequests.json` are supported, and their complete proposed sources must already be present in the review context.

The trusted host copies immutable accepted code and data into a temporary directory.
It rebuilds the previous outputs, applies the fully reviewed input changes, and rebuilds the proposed outputs.
Both reconstructed files must match their respective Git objects byte for byte.
The compiler process receives no app token, account authentication or inherited environment secrets.
Proposed Python or JavaScript is never executed.
The model receives exact revision, byte-count and SHA-256 receipts and the changed input sources.
It still assesses their semantics and may report incomplete review when other required context is missing.

Any unsupported dependency change, altered generator, stale base, incomplete input, failed reconstruction or byte mismatch retains partial source coverage and blocks approval.
Other binary and oversized files retain their existing limits.
All finding, score, identity, current-head, CI, mergeability and merge-queue requirements remain in force.
AGENTS.md, the canonical skill and the review prompt describe these boundaries consistently.
The prompt also distinguishes a bounded delivery from unfinished parent scopes and does not make a review fixture's future approval a prerequisite for assessing its repair.

## Verification and operation

The source-context builder supports an offline process invocation:

```sh
python .github/scripts/Review/BuildContext.py /path/to/Request.json
```

The JSON request supplies `Evidence`, `PullData`, `FileList` and `Settings`, matching the trusted preparation inputs.
This process does not publish reviews or access account authentication.
The merge-queue suite gains a real Git and planning-process compatibility check using the repository's complete register and catalogue data.
It checks valid reconstruction and rejection of modified output, modified generator, unsupported input and stale base.
It creates no branches, pushes no refs and uses an isolated index.
The real context CLI was run against retained hosted input artifact `15277185273` for PR #401 head `fa405f5b0710d5cc971985901232519a9acaba63` and trusted base `141f396f183220e691194907cdcacb7ba56d9ce6`.
Both generated files matched their previous and proposed Git objects exactly, producing complete coverage of all nine files with zero omissions and 471,798 encoded context bytes.
The [receipt](GeneratedPlanningCoverage.json) pins implementation hashes, output hashes, byte counts and input provenance.
This real process smoke used no mocked APIs or account credentials and did not run the model or publish an approval.
Local Black and Python steering checks passed; remote negative process cases and hosted approval acceptance remain pending.

Scope `ReviewerCoverage`, parent `ReviewerHosted`, owner `jdharcourt`, branch `fix/reviewer-live-acceptance-20261128` is recorded in the [owning register](../../Planning/Links.json).
The existing deployed runtime cannot establish full coverage of this replacement's generated planning files before deployment.
No bootstrap merge authorization is assumed for this change.
Temporary PR #401 must never merge and remains separate from this production repair.
Native project synchronization remains unavailable because project permission is missing.
