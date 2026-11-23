SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.

# Release unused advice queue records

## Expectation

A caller that stops waiting before dispatch must not consume the retained-request allowance permanently.
Polling must leave shared database capacity available to other callers.

## Observed failure

The first shared advice implementation retained abandoned requests in the same bounded table as dispatched requests.
Ten thousand abandoned prompts could exhaust metadata capacity while provider calls remained available.
Every waiting caller also scanned global request history on each reservation poll under the database write transaction.
After those scans were removed, waiter expiry was still renewed on every 200 ms poll, causing repeated serialized durable commits while the provider was busy.

## Resolution

Remove an uncharged queued or abandoned request only after its last live waiter leaves or expires.
Keep every charged invocation record, including completed, failed and uncertain outcomes.
A provider timeout or caller crash after dispatch still requires explicit operator recovery before capacity is released.
Removing an unused queue entry does not refund a call or allow an uncertain request to be sent again.

Use one fixed lease for each caller's bounded waiting interval. Idle polls read shared state; they do not renew that lease or acquire the writer transaction.
A possible dispatch rechecks eligibility and reserves the call atomically.
Use an expiry index to clean expired waiter keys across providers, and a provider-scoped index for running deadlines.
Cross-provider waiter cleanup prevents a stopped provider from retaining the shared metadata allowance.
Transactional counters enforce the metadata limit without repeated history counts.
A one-time database migration removes only uncharged orphan records and preserves charged history.

See [automatic advice](../../../Changes/Research/Advice/AutomaticDecoderAdvice.md#share-provider-work-between-instances) for configuration and operator recovery.
