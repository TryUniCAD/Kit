<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Keep shared queue transactions bounded

## Expectation

Progress polling and independent job submissions should leave controller capacity available for claims, renewals and completion.

## Observed failure

The first shared status implementation called `verify_job` for every active shared job inside the controller write transaction.
Each distinct large CAD input could therefore be hashed again during a status request.
The first enqueue implementation also reconciled all subscriptions twice, so successive independent requests repeatedly traversed unrelated work.
Both behaviors held the same transaction needed by worker lease operations.
The later metadata-only status still scanned retained subscriptions and jobs to compute global totals.
Paging the request list did not bound those aggregate scans.
Shared claim ordering also recomputed subscriber priority for every queued candidate before selecting work.

## Resolution

`queue-status` reads recorded metadata only, reports `acceptance_verified: false`, and hashes zero artifact bytes.
The existing `status --job` interface retains integrity-checked inspection.
Claims and result acceptance retain their normal evidence checks.

Global status uses transactionally maintained subscription and job-state totals, plus an indexed oldest-queued lookup.
Request pages read bounded summaries. A selected request uses its indexed memberships rather than a global conditional filter.
Existing shared stores build the status read model once; subsequent polls do not recount retained history.

Enqueue updates subscriptions before one reconciliation over the affected upstream closure.
Transactional counters enforce quotas without global recounts for each admission.
The response exposes the examined closure and reconciliation pass count.

Claim ranking caches subscriber priority when membership, request activity or priority changes.
A stable score gives continuous aging at one point per minute and supports indexed selection for ordinary shared queues.
Existing native scheduling lanes, resource reservations and evidence checks remain authoritative.
The process scenarios cover corrupted payloads, ninety-six independent requests, quota rollback, shared dependency graphs and counter migration.

These observations describe scheduler work. They do not measure CAD coverage or an end-to-end throughput improvement.
