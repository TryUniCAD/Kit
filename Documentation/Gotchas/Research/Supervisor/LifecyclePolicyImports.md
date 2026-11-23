<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Pin transitive queue policy imports

## Expectation

A reviewed native lifecycle source pin must reject changes to code that controls its queue admission and cancellation.

## Observed gap

The lifecycle inventory pinned `Controller.py`, `Ledger.py` and `PriorityClaims.py`.
Those modules gained imports from the shared queue package.
Without corresponding inventory entries, a changed imported module could alter admission behavior while the listed files remained unchanged.

## Resolution

The existing lifecycle source inventory now includes all seven shared queue policy modules.
The source-bound process scenario compares an isolated committed source checkout, changes each new member separately, removes one member, and restores the original files.
Clean sources pass; changed and missing policy members refuse.
The scenario starts no CAD application and does not establish native model acceptance.
Future policy imports must extend the same inventory and drift controls.
