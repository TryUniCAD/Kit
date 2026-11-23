<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Share research work between instances

Use one local controller store when several instances request the same research experiments.
Run one supervisor for that store. Instances submit requests and inspect results; they do not start competing supervisors.
The store must remain on one local filesystem. It is not a network service or a database for remote machines.

## Prepare the shared workers

Initialize the store with the existing controller command:

```sh
kit research --root /path/to/Kit controller --store /private/var/tmp/KitShared init --max-running 8
kit research --root /path/to/Kit controller --store /private/var/tmp/KitShared queue-config --max-pending 1000
```

Use the [supervisor configuration](ResearchSupervisor.md#configuration) to select that same store and the trusted worker registry.
Configure separate pools for offline decoding and application work.
Keep each application installation at capacity one.
The supervisor still enforces CPU, memory, logical-job capacity, application ownership and existing acceptance fences.
A queue does not create a runner or qualify a CAD operation.

Start the configured supervisor once:

```sh
kit research --root /path/to/Kit supervisor --config /private/var/tmp/SharedSupervisor.json run
```

## Submit a request

Write a request file using the existing [job contract](ResearchController.md#job-contract):

```json
{
  "queue_version": 1,
  "request": "research:fusion-prisms",
  "revision": 1,
  "priority": 50,
  "jobs": [
    {
      "id": "decode:source",
      "kind": "inference.rescan",
      "inputs": {
        "assessment": "assessment:prisms",
        "source": "source:prism"
      },
      "rule_version": "prism-reader@reviewed",
      "tool_version": "kit@reviewed",
      "options": {
        "scope": "p03-blind-boss.fusion",
        "source_format": "fusion.f3d",
        "source_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
      }
    }
  ]
}
```

This example describes the request format. Bind the actual assessment and source files first, and use their real digest and reviewed code versions.
Only configure job kinds supported by the trusted worker registry.
A request may include a dependency graph. Local dependency references and input selectors are remapped together.
Worker-specific identifiers embedded in arbitrary options are preserved; they are not rewritten.

Submit the request:

```sh
kit research --root /path/to/Kit controller --store /private/var/tmp/KitShared enqueue /private/var/tmp/Request.json
kit research --root /path/to/Kit controller --store /private/var/tmp/KitShared queue-status --request research:fusion-prisms
```

The enqueue response and request-filtered status map each requested ID to its canonical shared job ID. Global status pages contain request summaries and job counts.
Equivalent normalized definitions share a job even when callers use different local IDs.
Job kind, input binding names, dependency identities, options, resource declarations, retry policy and rule/tool versions remain part of identity.
Different binding names are conservatively distinct, even when their current bytes match.
Use digest-qualified immutable binding names for independent revision campaigns. Rebinding a shared mutable name changes the evidence for every subscriber.
Existing input fingerprints still invalidate dependent results when bound evidence changes.

Requests must use stable owner-specific names. Two instances working on different tasks must use different request names.
Only a newer revision replaces an existing request. Repeating the same revision and content is idempotent; changed content at that revision or an older revision is refused.
This protects a new request from a delayed instance's stale submission.

## Replace or cancel obsolete work

Submit the next revision of the same request to replace its subscriptions atomically.
A superseded job stays available while another active request or a standalone dependent job still needs it.
Admission and cancellation reconcile only the affected upstream dependency closure. Transactional counters enforce quotas without queue-wide recounts.
The response fields `shared_reconciled_jobs` and `shared_reconcile_passes` expose the work examined in that transaction.
Completed evidence remains available for reuse.

Cancel an entire request with a newer revision:

```sh
kit research --root /path/to/Kit controller --store /private/var/tmp/KitShared cancel-request research:fusion-prisms --revision 2
```

Cancellation revokes an orphan's active lease. The supervisor observes the stale lease and stops its own worker through its normal cleanup path.
Late results cannot complete replacement work.
A revoked resource-owning job makes its resources unavailable until the owner confirms cleanup and healthy controls.
See [shared cancellation and resource recovery](../../Gotchas/Research/Supervisor/SharedQueueResourceRecovery.md).

## Admission and scheduling

The pending limit controls admission of new shared requests using the count of unique unfinished work, including jobs waiting for evidence or applications.
Duplicate subscribers do not consume another execution slot.
A request that would exceed the limit is refused atomically; it does not cancel the previous revision or publish a partial graph.
A request contains at most 1,000 jobs. Shared metadata retains at most 10,000 request names and 100,000 subscriptions.
Evidence invalidation or a standalone consumer can make existing jobs pending again above the admission ceiling. Those jobs remain intact; subsequent admissions wait for capacity or an explicit limit change.
The existing total controller metadata limits still apply to retained history.

Request priority is between zero and one hundred; the default is fifty.
Waiting jobs gain priority over time. Both single and grouped claim paths use the same ordering.
Existing application reservations and priority-schedule lanes remain authoritative.
A blocked application job does not consume an offline worker slot.

Use `queue-status` to inspect active subscriptions, unique jobs, recorded states and waiting time.
It reports `scope: queue_metadata`, `acceptance_verified: false` and zero artifact bytes hashed.
Status polling does not reconcile jobs or read CAD payloads while holding the controller transaction.
Use the existing `controller status --job SHARED_JOB_ID` command for integrity-checked job inspection.
Normal claim, heartbeat and finish operations retain their existing reconciliation and evidence checks.
Treat job completion, evidence integrity, semantic verification and native target acceptance as separate outcomes.
This feature does not change the production support matrix.

## Existing catalogue runs

Existing `kit run` catalogue directories retain their private controller stores and their current resume and ownership contracts.
They do not automatically join this queue.
Use the shared controller endpoint for explicitly submitted, compatible worker jobs.
Check any native worker's ID-dependent contract before moving its jobs to canonical shared IDs.
Optional advice can share its own budget across private catalogue runs; see [automatic advice](../../Changes/Research/Advice/AutomaticDecoderAdvice.md).
