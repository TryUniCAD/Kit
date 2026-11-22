<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A matching fingerprint needs a valid dependency snapshot

## Expectation

A comparison worker checks that dependency receipts agree with every declared reader dependency before publishing evidence.
A dependency-selected document requires the corresponding dependency record.

## Original behavior

The worker reconstructed its fingerprint from the supplied dependency object without validating that object's roster, fields, or digest syntax.
Recalculated fingerprints therefore admitted missing, undeclared, and malformed dependency records.
A document selected from an absent reader dependency could still produce a completed comparison observation.

## Repair and recovery

Use the [shared session binding implementation](../../Changes/Research/Controller/SemanticSessionBinding.md).
It rejects inconsistent dependency metadata before evaluating documents or publishing outputs.
Prepare sessions through the actual controller and supervisor.
Submit changed jobs with a new immutable worker version instead of rewriting old receipts.

Authored worker process controls reproduce the contradictory packets without native application evidence.
The shared validation boundary checks snapshot consistency and does not independently qualify CAD semantics.
