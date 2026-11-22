# Repair attribution migration queue failures

## Cause

PR #253 was removed from the native merge queue twice because Gitleaks failed.
Both candidates contained a public standards checksum next to a filename containing `Token`.
The generic credential detector interpreted that checksum as a credential assignment.
See [the first aggregate](https://github.com/TryUniCAD/Kit/actions/runs/45058131353)
and [the second aggregate](https://github.com/TryUniCAD/Kit/actions/runs/45063182692).

The first candidate also failed seven process cases across four test shards.
Attribution edits changed four sealed capture-input blobs and the raw corpus manifest hash.
The existing provenance checks correctly rejected those unbound changes.
PR static checks had deferred these security and full-suite checks to the queue.

## Behavior

The Gitleaks configuration classifies exactly one known public SHA-256 at `.github/workflows/SteeringSync.yml` under the generic rule.
It does not exempt a file, commit, arbitrary checksum, or another detector rule.
The job runs the actual scanner against the allowed pair, the same value elsewhere, and an unknown value at the allowed path.
Both negative controls must still fail detection.
The probe loads its policy and fixture from the immutable workflow harness revision.
Manual audits can still select historical source revisions that predate the checksum entry.
The full-history audit remains unchanged.

Capture intake preserves the historical contract, input digest, roster, native blobs, and qualification status.
It binds only four exact original/current text-blob pairs, each with mode `100644`.
The report exposes `current_input_tree_sha256` and `attribution_migrations` separately from the historical identity.
Unknown content, mode changes, missing inputs, and extra inputs remain errors.

The Fusion census accepts one directional historical/current manifest hash pair for the reviewed path-label migration.
The historical manifest SHA-256 is `4cc8fb707641ecde29a04b5dafa1ecbf7e706a839550a4af3b8807d19b64d4e2`.
The migrated manifest SHA-256 is `905b547f47e6b649b190bee11964067ce8dfa81ec8d43fd15e1c37f8d6eda05c`.
Exactly 201 recorded host-path labels changed; every native asset record and non-evidence top-level field remained identical.
The historical outcome baseline remains unchanged.
Every native outcome and corpus revision still must match.
Comparison output reports both manifest hashes and the explicit migration binding.

## Usage and limits

Existing CLI and research commands need no additional flags.
These bindings do not qualify research data or establish native CAD acceptance.
They do not permit generic metadata normalization or silently accept future input migrations.
Future migrations require their own inspected provenance and exact identities.

See [merge queue operations](../../../MergeQueue.md)
and [research commands](../../Tasks/ResearchCommandLine.md).

## Verification

Remote failure logs identified the exact checksum finding and the sealed-input mismatch.
Read-only comparison verified the four input blob pairs and the 201 path-only manifest edits.
Process coverage mutates content, mode, and presence for each migrated input while retaining the existing graph and alias cases.
The positive process cases independently derive the current Git input-tree digest and both directions of every migrated blob identity.
The census coverage retains unknown-manifest rejection and adds a corpus-revision mismatch case.
`git diff --check` and Black formatting are local static checks.
No local tests or security scans ran.
Fresh remote audit, PR checks, current-head review, and native queue acceptance remain separate evidence.
