<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cloudflare delivery and interruption recovery planning

The [delivery specification](../../../Reference/Research/CloudflareDeliveryRecovery.md) extends [PR #161](https://github.com/TryUniCAD/Kit/pull/161).
It reuses PR #158's SQLite and immutable file-storage foundation for a planned per-node delivery outbox.
A local PostgreSQL service is unnecessary.
The [persistence gotcha](../../../Gotchas/Research/Cloudflare/LocalPersistenceNeedsDeliveryReceipts.md) identifies the existing source boundary.

The plan now specifies durable output publication before local commit and session cleanup.
It separates Cloudflare acceptance from verified final export and retains local recovery copies between those acknowledgements.
It defines lost-response lookup, stale-attempt retention, bounded disconnected execution, retry backoff, and disk-pressure refusal.

The backup design requires an independent destination, verified input copies, hourly metadata checkpoint targets, and admission pauses for stale backups.
Restoration starts paused, advances ownership epochs, reconciles external export/deletion acknowledgements, and quarantines uncertain native sessions.
Temporary backup copies follow the same run cleanup policy.
Provider outages do not automatically start a second coordinator or duplicate native work.

The interruption matrix and C04a-C06a child tasks define implementation acceptance.
Exact SQL migrations, API schemas, and executable restore procedures remain required implementation deliverables.

## Verification boundary

Existing persistence and recovery source was inspected at PR #158 revision `0b66cc014`.
Official SQLite backup and Cloudflare database export/recovery documentation was inspected on 2026-11-18.
The PR records Markdown formatting, link, path-policy, and actual current-head remote CI/review evidence.
No outbox implementation, backup, restore, hosted failure campaign, native application run, or deletion operation was executed.
