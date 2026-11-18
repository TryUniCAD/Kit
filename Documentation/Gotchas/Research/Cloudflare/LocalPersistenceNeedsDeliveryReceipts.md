<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Local persistence needs remote delivery receipts

## Expectation

An existing local database and `finish.json` can appear to provide a complete disconnected-worker outbox.

## Observed source behavior

At PR #158 revision `0b66cc014`, the research controller uses SQLite and immutable local artifact files, not PostgreSQL.
The [supervisor settlement path](https://github.com/TryUniCAD/Kit/blob/0b66cc014/re/automation/Supervisor.py) writes `finish.json` before calling `FinishJob`.
It removes the session after ordinary settlement, including a stale result disposition.
The restart path records orphan recovery, releases claims, and removes leftover session directories.
It does not implement durable retry of a remote completion whose acknowledgement was lost.
This observation is source inspection, not an executed crash or network test.

## Planned workaround

Reuse the existing SQLite and artifact publication primitives through a versioned per-node outbox extension.
Commit owned output references before any session cleanup.
Process durable delivery state before orphan session recovery after restart.
Preserve unacknowledged artifacts outside session-directory ownership.
Resolve uncertain completion through an authenticated, idempotent receipt lookup.
Keep a local recovery copy until the final export is verified, even after Cloudflare accepts the result.
Do not add PostgreSQL or start an independent local scheduler for this delivery role.

The [delivery and recovery specification](../../../Reference/Research/CloudflareDeliveryRecovery.md) defines the state transitions and interruption acceptance.
