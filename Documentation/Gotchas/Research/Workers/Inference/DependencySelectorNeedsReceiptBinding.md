SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.

# Direct dependency selectors need the accepted result digest

## Expectation

A direct dependency selector consumes the accepted result identified by its dependency snapshot.
Its staged input digest must equal that result digest.

## Original behavior

The inference session reader checked normalized bindings, dependency digest syntax, and the reconstructed fingerprint.
It did not compare a direct selector's input digest with its selected dependency result digest.
An independently authored packet could therefore contain different digests and still pass when its fingerprint included both values.
The actual worker command accepted that contradictory packet and published a completed observation.

## Repair

The [dependency binding change](../../../../Changes/Research/Controller/InferenceDependencyBinding.md) rejects that contradiction before inference evaluation.
Prepare sessions through the controller and supervisor instead of constructing packets manually.
For changed dependency evidence, submit the replacement through the controller.

This comparison applies to direct `{ "dependency": "parent" }` selectors.
Artifact and candidate fingerprint selectors intentionally consume different controller objects and retain their existing behavior.
A matching packet establishes internal consistency, not independent authentication or native acceptance.
