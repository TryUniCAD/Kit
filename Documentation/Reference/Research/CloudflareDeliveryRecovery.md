<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cloudflare delivery and recovery specification

## Scope and existing persistence

This specification extends the proposed [Cloudflare coordinator](CloudflareCoordinatorPlan.md) on [PR #161](https://github.com/TryUniCAD/Kit/pull/161).
It defines local delivery, disconnection behavior, acknowledgements, backups, restore, and interruption acceptance.
All new behavior remains planned, with implementation tasks unassigned.
No database, cloud resource, backup, or deletion operation is created by this document.

Reuse PR #158's SQLite and immutable file-storage foundation.
Do not introduce a local PostgreSQL service or a second local job scheduler.
Each node owns its private local store; D1 remains authoritative for remote job claims and results.
Never share a node's SQLite file across machines.

At inspected revision `0b66cc014`, [Ledger.py](https://github.com/TryUniCAD/Kit/blob/0b66cc014/re/automation/Ledger.py) uses `ledger.sqlite3` and full synchronous transactions.
[Artifacts.py](https://github.com/TryUniCAD/Kit/blob/0b66cc014/re/automation/Artifacts.py) stages, hashes, flushes, and publishes immutable files.
[Supervisor.py](https://github.com/TryUniCAD/Kit/blob/0b66cc014/re/automation/Supervisor.py) writes `finish.json` before submitting an outcome to its adapter.
Its ordinary restart recovery releases orphaned sessions and removes their directories.
These mechanisms are useful persistence primitives, not an implemented disconnected-delivery protocol.
See [local persistence and delivery receipts](../../Gotchas/Research/Cloudflare/LocalPersistenceNeedsDeliveryReceipts.md).

## Local outbox record and commit boundary

Extend the node's versioned SQLite storage with delivery tables and preserve existing controller records.
Give the local extension a separate migration version and explicit rollback behavior.
The remote adapter may record delivery state, but cannot create runnable local copies of remote jobs.

| Local record      | Required fields and invariants                                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| OutboxDeliveries  | Project, run, job generation, attempt, node session, coordinator recovery epoch, request digest, immutable mutation key, state |
| OutboxArtifacts   | Delivery, artifact role, SHA-256, byte count, owned local object reference; unique delivery and role                           |
| OutboxReceipts    | Delivery, acknowledgement type, canonical receipt digest, verified receipt object reference, observed coordinator identity     |
| OutboxRetries     | Delivery, persisted attempt count, next retry time, bounded last error, retry class                                            |
| OutboxCheckpoints | Project, recovery epoch, checkpoint digest, verified local destination, accepted time, backup age                              |

Keep lease secrets in the existing protected credential boundary and store only references in delivery records.
Exclude credentials from manifests, logs, backups, and GitHub exports.
The unique delivery identity includes the complete remote generation and attempt, not only the human-readable job ID.

Before a session can be removed:

1. Verify and publish every required result, receipt, and output into the owned local artifact store.
2. Flush the manifest and artifact bytes through the existing publication boundary.
3. Commit a SQLite transaction binding those objects to one `pending_remote` delivery record.
4. Confirm the transaction committed before allowing ordinary session cleanup.

File publication precedes metadata commit.
A crash between these operations can leave collectible orphan objects, but cannot create an accepted reference to missing bytes.
Protect committed outbox references from cache eviction, session cleanup, orphan recovery, and disk-pressure deletion.
Reconcile published files without committed records during restart without silently deleting an unexplained session result.
One database transaction does not make separate filesystem writes atomic.

On restart, inspect and validate the outbox before the supervisor processes leftover session directories.
Keep existing owned-process identity checks and orphan shutdown behavior.
Recover delivery independently from process recovery; a finished result must not be converted into an empty orphan retry.
Corrupt or missing referenced bytes enter `blocked_local_integrity` and stop new admission for that node.
Do not acknowledge or erase the affected delivery.

## Delivery states and acknowledgements

| State or observation      | Permitted next action                                                    | Deletion rule                       |
| ------------------------- | ------------------------------------------------------------------------ | ----------------------------------- |
| `pending_remote`          | Request upload grants or retry the same immutable mutation               | Retain all required local bytes     |
| `uploading`               | Resume a supported transfer or obtain a new bounded staging grant        | Retain local source bytes           |
| `awaiting_receipt`        | Query mutation status, then retry the identical request if still unknown | Retain bytes and mutation identity  |
| `remotely_accepted`       | Store the verified coordinator receipt and await final export            | Retain local recovery copy          |
| `retained_unaccepted`     | Export for inspection or obtain an explicit discard disposition          | No automatic deletion or acceptance |
| `blocked_local_integrity` | Repair from a verified copy and repeat digest checks                     | Block eviction and new claims       |
| `export_verified`         | Verify final destination manifest and local retention obligations        | Cleanup may now be authorized       |
| `cleaned`                 | Retain only the bounded cleanup acknowledgement                          | Never recreate the remote run       |

The first acknowledgement confirms durable Cloudflare acceptance of the exact attempt, input snapshot, result, and verified artifact set.
The second acknowledgement confirms the final export's exact GitHub commit or approved download destinations and manifest digest.
Cloudflare acceptance alone cannot authorize removal of the last local recovery copy.
Final GitHub or operator exports survive temporary Cloudflare cleanup.

Every successful completion response must contain the project, run, job generation, attempt, node session, recovery epoch, and mutation key.
It also contains the request digest, accepted result and artifact-manifest digests, receipt digest, and accepted outcome.
The worker checks every identity before committing the receipt locally.
An HTTP success, uploaded object, connection close, or empty response is insufficient acknowledgement.

Provide an authenticated receipt lookup by immutable mutation identity.
Lookup must distinguish `accepted`, `rejected`, and `unknown` without inventing acceptance after a timeout.
An accepted lookup returns the same canonical receipt as the original response.
Repeated completion cannot advance state twice or replace a different result.
A reused mutation key with different content returns a conflict.
Current node credentials can inspect that node's earlier delivery receipts without reviving the earlier session lease.

Bind every receipt to the coordinator's recovery epoch.
A new epoch requires reconciliation; it cannot silently reuse pre-restore ownership or cleanup authority.
A stale, expired, cancelled, changed-dependency, or superseded attempt enters `retained_unaccepted` when its bytes remain unacknowledged.
Retain those observations without treating them as a newly accepted result.
Any reuse under a new attempt requires explicit coordinator authorization and complete current input and tool validation.
Never silently rerun a native application operation to repair a missing acknowledgement.

## Network loss and bounded execution

After a failed coordinator exchange, stop requesting new claims and new native phases.
Persist retry state and use exponential backoff from 5 seconds to a 60-second maximum, with jitter.
Honor server retry instructions and quotas; authentication refusal requires credential repair instead of an unbounded retry loop.
Expired transfer grants can be replaced only through an authorized current attempt or receipt-reconciliation operation.

| Work type                       | Behavior while disconnected                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Already running offline decoder | Continue only within the last acknowledged lease and fixed execution deadline; spool completed results locally |
| Queued or not-started work      | Remain queued; start nothing without a current remote claim                                                    |
| Native application phase        | Start no subsequent phase; request bounded owned-session shutdown before the conservative stop deadline        |
| Delivery or verification        | Retain local bytes, suspend unavailable network operations, and retry by immutable delivery identity           |
| Final export or cleanup         | Pause destructive actions until verified delivery and current cleanup authorization are available              |

Derive a local monotonic stop deadline from the last acknowledged server lease duration and remaining execution deadline.
Subtract the measured request round-trip and a margin covering the configured stop grace plus 30 seconds.
If that remaining interval is not positive, start no new work.
Failed heartbeats and local clock changes cannot extend authorization.
An expired lease ends execution authority even when the local computer remains healthy.

Use the existing watchdog and exact process-identity protections for native shutdown.
If shutdown cannot be confirmed, retain local ownership evidence and quarantine the remote installation when communication returns.
A process or network timeout cannot release an installation by assumption.
The server may retry offline work elsewhere after expiry; completion still accepts at most one current attempt.
Offline nodes preserve their unacknowledged copies and reconcile before accepting new work on reconnect.

Set explicit per-node outbox byte and record limits during enrollment.
Reserve space for finishing already admitted jobs.
When space is insufficient, pause claims and report `outbox_full`; never evict an unacknowledged result to make room.
Disk corruption and loss of the worker's only disk remain separate failure cases requiring a verified independent copy.

## Backup contract and recovery targets

Live database history, delivery persistence, and an independent backup have different failure boundaries.
D1 [Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/) can recover database state within the selected plan's retained history.
It does not by itself provide a separately controlled copy of R2 objects, GitHub exports, or worker-local files.

The pilot requires an approved backup destination outside the Cloudflare account.
An existing operator or worker computer can hold that copy without becoming an always-on coordination server.
Keep private CAD evidence in a private destination, not a public source repository.
Before admitting a run, verify that each original input has a retained copy outside Cloudflare.
Completed outputs stay in the local outbox until final export verification.

Target an independent metadata checkpoint every hour while runs are active, and before schema migration, restore, or destructive cleanup.
Pause new claims if the newest verified checkpoint is more than two hours old.
Continue bounded settlement and recovery using the reserved quota and storage budgets.
These intervals are proposed operating targets, not demonstrated recovery guarantees.
Measure achieved recovery point and recovery time during the pilot.

A checkpoint contains a versioned schema description, recovery epoch, frozen coordination records, accepted receipts, and artifact inventory.
It includes source/tool/rule fingerprints and final export or deletion acknowledgements available at that checkpoint.
The backup catalog records verified copies outside Cloudflare for all referenced required bytes.
An object listing or database dump without the referenced bytes cannot be called a complete backup.

Freeze admissions and job mutations for the bounded checkpoint interval, then export one consistent database revision.
Retain node lease renewal and abort checkpointing before existing lease safety windows are exhausted.
Release the mutation freeze after sealing, or after aborting without replacing the previous verified checkpoint.
An aborted checkpoint permits current attempts to settle; the backup-age rule still controls new admission.
Use documented [D1 import/export](https://developers.cloudflare.com/d1/best-practices/import-export-data/) procedures rather than assuming raw SQLite-file upload compatibility.
For a live local SQLite store, use the [SQLite backup API](https://www.sqlite.org/backup.html) or a quiescent verified snapshot.
Do not copy only the main database file during concurrent writes and call that a verified backup.
Charge checkpoint reads, transfer operations, and retained bytes against the pilot's quota reservations.

Keep checkpoint bundles per run so cleanup can remove temporary run backups without deleting another run's evidence.
After final export verification, purge temporary run backups under the same cleanup policy as Cloudflare objects.
Retain only the intentionally published results and their export/deletion acknowledgements outside temporary coordination storage.
Keep the latest verified final acknowledgements available to restoration even after Cloudflare tombstones expire.
Provider recovery history can still retain earlier bytes; immediate secure erasure is not claimed.

## Restore procedure and outage boundary

1. Pause claims, uploads, completion mutations, and cleanup on the affected coordinator.
2. Obtain the newest verified checkpoint and later final export/deletion acknowledgements from the independent destination.
3. Restore into an isolated, paused coordinator and verify schema compatibility, record integrity, and referenced artifact hashes.
4. Reconcile exports and deleted runs against the latest independent acknowledgements before making any artifact accessible.
5. Establish a new recovery epoch and revoke earlier session ownership and attempt credentials.
6. Ask each returning node to reconcile its outbox and report owned-process state.
7. Restore accepted immutable results only when matching evidence and fingerprints remain available.
8. Requeue eligible offline work after fencing old attempts; quarantine every uncertain native installation.
9. Prove known completed, pending, and deleted cases through a bounded restore smoke run.
10. Enable admission only after the recovery operator records successful reconciliation and verifies the remaining capacity budget.

Missing bytes, unresolved deletion history, incompatible schemas, or uncertain native ownership block the affected recovery scope.
Do not manufacture missing evidence or restore a deleted run into an active state.
If the independent backup is unavailable, retain worker-local copies and report the specific unrecoverable interval.

Automatic second-cloud failover is outside the initial design.
A provider outage pauses coordination while existing workers preserve bounded local progress.
Do not silently select a local controller or another cloud and run duplicate native tasks under separate authorities.
A deliberate coordinator replacement follows the same fencing, acknowledgement reconciliation, and operator restore procedure.

## Interruption acceptance matrix

All rows require process or service-boundary evidence at the exact implementation revision.
Include real D1/R2 observations for hosted behavior and preserve the repository's merge-queue acceptance path.

| Failure injected                                          | Required observable result                                                                    |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Process death after file flush, before outbox commit      | Restart finds uncommitted artifacts; no missing-byte reference or false acceptance            |
| Process death after outbox commit, before session cleanup | One durable pending delivery survives; cleanup cannot erase its objects                       |
| Power loss or supervisor restart during delivery          | SQLite and artifact integrity checks pass; the original immutable mutation resumes            |
| Upload interrupted or grant expires                       | Local source survives; partial staging is retried or collected without acceptance             |
| Cloud accepts completion but response is lost             | Receipt lookup recovers the original result without creating another accepted completion      |
| Completion response arrives after lease expiry            | Identity reconciliation resolves accepted versus stale status; old authority never revives    |
| Node reconnects after its job was reassigned              | Earlier output remains retained and unaccepted unless independently authorized for reuse      |
| Disk fills during execution                               | Admission stops; reserved space protects already admitted results and receipts                |
| Native host disconnects or shutdown blocks                | No new native phase starts; installation stays quarantined until exact owned-process recovery |
| D1 restored while workers still hold old leases           | New recovery epoch fences earlier completion, heartbeat, and cleanup requests                 |
| R2 object missing after metadata restore                  | Restore blocks the affected result and repairs from a verified independent copy               |
| Old backup predates a completed wipe                      | Latest external acknowledgement prevents the deleted run from becoming active or readable     |
| GitHub export fails or final acknowledgement is lost      | Outbox and Cloudflare data remain; verified destination lookup resolves the same export       |
| Deletion process crashes or a node remains offline        | Cleanup resumes idempotently; local wipe remains explicitly outstanding                       |
| Backup destination is unavailable beyond its age limit    | New claims pause; settlement and preservation continue without automatic failover             |

## Delivery tasks and evidence

| Task                                                   | Dependency                         | Exit condition                                                                                                    |
| ------------------------------------------------------ | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| C04a: local outbox and restart integration             | C01, PR #158 storage contracts     | Verified files precede local commit; process recovery preserves delivery state without a local PostgreSQL service |
| C04b: receipt reconciliation and offline policy        | C02-C03, C04a                      | Both acknowledgement levels, immutable retries, deadline stops, stale outputs, and disk-pressure controls pass    |
| C05a: checkpoint, restore, and deletion reconciliation | C04b-C05 and approved destinations | Independent complete backup restores accepted work while fencing old sessions and preserving completed wipes      |
| C06a: interruption campaign                            | C04a-C05a                          | Every failure-matrix row has exact-revision evidence, measured recovery targets, and recorded quota cost          |

All implementation owners remain unassigned, under the parent B15 register and PR #161 planning boundary.
The SQL migrations, exact versioned API schemas, and cleanup/restore commands must accompany C01-C05 implementation before pilot enrollment.
No failure campaign, backup, restore, cloud deployment, or deletion was executed while writing this specification.
