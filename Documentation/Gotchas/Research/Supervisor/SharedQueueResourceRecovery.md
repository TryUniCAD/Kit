<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Shared cancellation retains resource recovery fences

## Expectation

Replacing a request removes obsolete work and appears to free its application resource immediately.

## Actual behavior

An active worker can outlive the transaction that revokes its controller lease.
Removing the database claim does not prove that its application process or provider request has stopped.
The existing controller therefore makes resources held by a revoked attempt unavailable.
The supervisor observes a stale lease and performs its normal owned-process cleanup.
Other requests keep their subscriptions, but cannot acquire that unavailable resource prematurely.

A completed evidence object remains valid only under its recorded inputs and verification scope.
Cancellation does not delete its history or promote it to native acceptance.

## Recovery

Wait for the owning supervisor's cleanup evidence.
Confirm that the previous owned process has stopped and that the application controls are healthy.
Then mark the exact resource available through the existing controller command.
Do not raise its capacity or start another supervisor to bypass the fence.
Offline pools can continue while application recovery is pending.

See [shared queue configuration](../../../Reference/Research/SharedResearchQueue.md) and [controller resource recovery](../../../Reference/Research/ResearchController.md#leases-retries-and-resource-recovery).
