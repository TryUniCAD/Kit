<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cloudflare database capacity and atomic coordination

## Expectation

A 5 GB free storage allowance can appear to describe one D1 database.
A SQLite-compatible interface can also appear to support the existing local controller without transaction changes.

## Observed contract

On 2026-11-18, Cloudflare documented 500 MB per free database and 5 GB total storage across the free account.
Each database processes queries serially.
The account's free daily allowance is 100,000 written rows, including index maintenance.
See [D1 limits](https://developers.cloudflare.com/d1/platform/limits/) and [pricing](https://developers.cloudflare.com/d1/platform/pricing/).

D1 operates in auto-commit and exposes transactional prepared-statement batches.
A failed statement rolls back its batch.
A conditional update that matches zero rows does not itself provide that failure.
See [the batch contract](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch).
This is documentation evidence, not an executed concurrency measurement.

## Planned workaround

Keep the initial metadata database below 500 MB and place file bodies in R2.
Measure written rows and indexed updates instead of treating API request count as database cost.
Use indexed, bounded coordination operations and aggregate node heartbeats.
Port claims and reservations into one guarded transition with constraints or transactional triggers.
Test simultaneous claims and forced intermediate failures against hosted D1 before releasing the remote adapter.
Do not translate PostgreSQL locking syntax or a local SQLite transaction sequence by assumption.

The [coordinator plan](../../../Reference/Research/CloudflareCoordinatorPlan.md) defines the proposed protocol and acceptance gates.
