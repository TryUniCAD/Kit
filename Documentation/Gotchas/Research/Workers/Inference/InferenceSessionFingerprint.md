<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Inference inputs need the controller session fingerprint

## Expectation

A worker checks that its job, bound inputs, and dependency receipts agree with the controller snapshot before publishing an observation.
Content digests detect changes relative to the scheduled input identity.

## Original behavior

The inference runner checked the session version and each consumed input's path and digest.
It omitted normalized job validation and reconstruction of the controller fingerprint.
A changed scope, rule version, tool version, or descriptor binding could therefore reach evaluation with a stale session fingerprint.
The input JSON parser also accepted duplicate object keys, which erased the earlier value before validation.

## Repair

Use the [inference session integrity implementation](../../../../Changes/Research/Controller/InferenceSessionIntegrity.md).
It validates the complete session before dispatching any inference kind and retains execution digests with the observation.
Use the actual supervisor to prepare sessions.
For a changed job or evidence input, submit its new immutable definition through the controller.
Retain earlier receipts with their original source identity.
The process coverage checks stale fingerprints and contradictory metadata through the worker command.
This boundary validates consistency with a controller snapshot and supplies no independent native qualification.
