<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cloudflare research coordination planning

The [coordinator plan](../../../Reference/Research/CloudflareCoordinatorPlan.md) defines a proposed hosted alternative to one local research controller.
Cloudflare Workers handles small coordination requests, D1 stores metadata, and private R2 storage holds files.
Existing computers retain CAD execution and local supervisor safeguards.
The mini PC and GitHub job synchronization are unnecessary in this design.

The plan includes a database record inventory, atomic job claims, session leases, resource quarantine, idempotency, and artifact verification.
It separates live coordination from PR #158's existing research and native acceptance boundaries.
It also defines an ephemeral run lifecycle, verified final delivery, resumable cleanup, and provider recovery-history limits.
The user selected deletion of all cloud run data after verified final delivery.
Reviewed source, documentation, and selected evidence go to GitHub; other required artifacts need explicit verified export destinations.
The [delivery recovery extension](CloudflareDeliveryRecovery.md) specifies reuse of local SQLite/files, acknowledgement recovery, independent backups, and interruption acceptance.

Use the plan's C01-C07 task register for later implementation claims.
The conversion backlog tracks the parent B15 delivery boundary.
No remote adapter, schema migration, cloud account, deployment, credential, or deletion operation is implemented by this change.

## Verification

Cloudflare's official database, Worker, object-storage, transaction, and quota documentation was inspected on 2026-11-18.
The single-database free limit is 500 MB, not the 5 GB aggregate account allowance.
The [database limits gotcha](../../../Gotchas/Research/Cloudflare/CloudflareDatabaseLimits.md) records this distinction and transaction constraints.

The PR records the actual formatting, link, path-policy, CI, and review results.
No local product tests, hosted load tests, native application runs, uploads, or cleanup operations were executed for this planning change.
The plan does not establish implemented distributed operation, native qualification, guaranteed free operation, or immediate secure erasure.
