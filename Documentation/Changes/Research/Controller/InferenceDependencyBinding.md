SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.

# Inference dependency result binding

A07d now checks direct dependency selectors before an inference worker evaluates its inputs.
For a `{ "dependency": "parent" }` selector, the input digest must equal the dependency snapshot's accepted result digest.
A contradictory session fails before publishing `result.json`, including when its fingerprint correctly hashes the contradictory metadata.

Artifact selectors and candidate fingerprint selectors retain their existing controller semantics.
Their input digests can legitimately differ from the accepted result digest.
The check validates session consistency and does not authenticate an independently supplied controller snapshot.

Use the actual controller and supervisor to prepare inference sessions.
Submit changed evidence through the controller and update the immutable `tool_version` when deploying changed worker behavior.
Historical receipts retain their original implementation identity.
See [inference session integrity](InferenceSessionIntegrity.md) for the complete packet contract.

## Verification evidence

The actual worker command refused an independently authored, correctly fingerprinted packet containing a contradictory direct selector.
The real controller, supervisor, and inference worker completed an authored assessment and its dependent rescan.
The child execution recorded the parent's accepted result digest as its assessment input.
The authored source was outside the assessed scope, so the rescan published `no_longer_affected` without invoking a CAD reader.

On native Windows, the focused inference integrity suite passed all 24 process cases using Python 3.14.6.
Black, Ruff, and focused steering checks passed for the changed test source.
The controller fixture required normal Windows artifact and process permissions.
Sandbox runs refused artifact publication before the controller behavior assertions.

The [dependency selector gotcha](../../../Gotchas/Research/Workers/Inference/DependencySelectorNeedsReceiptBinding.md) records the original mismatch.
Native acceptance, semantic qualification, independent evidence, and remote queue acceptance remain separate requirements.
