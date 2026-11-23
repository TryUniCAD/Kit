<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Coordinate shared research queues

Multiple local research instances can subscribe to equivalent controller jobs instead of issuing duplicate experiments.
`controller enqueue` publishes a revisioned request graph, maps local IDs to canonical shared IDs, and commits its subscriptions in the same transaction as the jobs.
Replacing or cancelling a request retains work still needed by other requests or standalone dependants.
Orphaned active work loses its lease; late publication remains fenced by the existing controller.

Use `queue-config --max-pending` to bound unfinished unique shared work and `queue-status` to inspect its current demand.
Queue status reads bounded metadata only; it reports no acceptance and does not hash CAD payloads or reconcile jobs. Integrity-checked job inspection remains available through the existing controller status command.
Request priority and aging use the same admission path for single and grouped claims.
Existing CPU, memory, resource, application-ownership and native acceptance checks remain enabled.
Shared admission performs one reconciliation over the affected upstream closure; transactional counters enforce request, subscription and pending-work limits.

The optional advisor coordination directory shares provider limits and identical-prompt results between research instances.
Advice remains an unverified experiment proposal. Deterministic results remain available when a provider is unavailable or its budget is exhausted.

[Configuration and request procedure](../../../../Reference/Research/SharedResearchQueue.md)

## Scope and limitations

The queue uses one local A03 store with one supervisor. It is not a distributed service.
Private catalogue runs retain their existing stores; compatible jobs must explicitly use the shared enqueue endpoint.
Canonicalization retains input binding names and arbitrary worker options rather than guessing semantic equivalence.
Completed job reuse does not establish current licensed CAD or cross-format acceptance.
No production reader, writer, native acceptance flag, capability boundary or merge-queue gate changes.

Task: `A08b-SharedQueue`; owner: Codex; branch: `codex/shared-research-queue`.
Dependencies: existing A03 controller, A07 scheduler, A08 supervisor and optional advisor.
The [owning register](../../../../Reference/Research/AutomationSteps.md#a08b-sharedqueue-shared-research-requests-and-advice-budgets) retains the implementation and acceptance status.

## Verification

Process integration coverage exercises concurrent submissions and claims, request revisions, shared subscribers, dependency graphs, result reuse, resource exclusion, pending limits and obsolete lease rejection.
Advisor coverage uses a disposable provider process. It does not call a paid API or establish live-account acceptance.
The scenarios join the existing complete suite, planner and shards.
Local process execution with Python 3.14.7 passed all six queue scenarios: races, lifecycle, scheduling, supervisor, legal notices and metadata polling.
Six concurrent enqueue clients shared one execution claim. A corrupted large evidence object remains visible to metadata polling without payload hashing, while integrity-checked job inspection still refuses it. Lifecycle checks retained another subscriber's work, refused stale completion, preserved historical receipts and prevented orphan resurrection.
The real supervisor executed the existing inference runner with canonical IDs, then stopped its owned cancelled worker on a stale lease.
The supervisor scenario required native macOS process-inspection access outside the restricted filesystem sandbox; the ownership check was retained.
Five shared-advice process groups passed, including timeout and caller-crash recovery, with zero live provider calls. Separate transport-failure controls retain charged capacity and prevent another request from dispatching before explicit recovery.
Black 26.10.1 and focused steering checks passed for the normal-suite wrappers and the legal-notice policy change.
Ninety-six independent requests each examined one job in one reconciliation pass. Separate checks cover diamond dependencies, standalone retention, quota rollback, counter state transitions and migration from existing shared stores.
Seven changed queue-policy modules and a missing module were refused by the actual native lifecycle source check; clean restored sources passed without launching CAD.
Current-head PR checks and configured review remain separate publication gates.
Heavy security and complete native merge-group acceptance remain assigned to the existing queue.
The [bounded transaction finding](../../../../Gotchas/Research/Supervisor/SharedQueueTransactionWork.md) records the metadata and incremental-admission repairs.
The [policy import finding](../../../../Gotchas/Research/Supervisor/LifecyclePolicyImports.md) records the native source-inventory repair.
No throughput improvement is claimed without a measured campaign comparison.

The [historical legal-notice finding](../../../../Gotchas/Tooling/HistoricalNoticeValidation.md) records why the policy checker also recognizes the exact original workspace-required notice. Malformed and partial notices remain rejected.
