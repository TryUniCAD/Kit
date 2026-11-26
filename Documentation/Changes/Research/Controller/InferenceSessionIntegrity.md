<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Inference session and input integrity

A07d binds every inference observation to the controller session that requested it.
The worker validates the normalized job, input roles and bindings, dependency receipts, and reconstructed controller fingerprint before evaluation.
This applies to `inference.fields`, `inference.paired-gap`, and `inference.rescan`.

The version 1 supervisor session already supplies these fields.
Existing valid controller submissions retain their input bindings, dependency selectors, scheduling behavior, and inference rules.
Handwritten incomplete packets must use the complete controller session contract.

Every new result records an `execution` object with the job definition digest, fingerprint, rule version, tool version, and input digests.
Generate the worker records schema again with `InferenceRunner.py --schema` when installing this revision.
Update the submitted job's immutable `tool_version` so the controller invalidates earlier results for changed worker behavior.
Previously retained receipts remain historical evidence for their original implementation.

Input reads require bounded plain regular files.
The worker checks file identity and timestamps before opening, after reading, and through the final path.
Links, directory inputs, changed identities, and digest mismatches fail before result publication.
Metadata refuses duplicate keys, nonfinite numbers, and excessive structure.
These checks also cover the session packet.

The [session fingerprint gotcha](../../../Gotchas/Research/Workers/Inference/InferenceSessionFingerprint.md) records the original failure mechanism.
The [inference procedure](DeterministicInference.md) defines scheduling and result interpretation.
The [step register](../../../Reference/Research/AutomationSteps.md) retains A07's independent qualification requirements.
Observations continue to record `semantic_qualification: unverified`, `native_acceptance: not_established`, and `portable_complete: false`.

## Verification evidence

Process coverage invokes the actual worker command with authored field searches, parked gaps, and source rescans.
Additional command cases change session fingerprints, job versions, descriptors, dependencies, output paths, metadata, and file types.
An accepted dependency-selector case preserves a complete matching snapshot.
The authored controller scenario verifies actual schema registration, completed and parked execution seals, unchanged receipt reuse, and dependency invalidation after a rule change.
Native Windows verification used Python 3.14.6, pytest 9.1.1, and NumPy 2.4.6 from the locked environment.
The combined worker and controller process suite passed all 36 cases.
Formatting, Ruff, and focused steering verification passed for the changed test sources.
The full historical controller archive gate passed after sanctioned capture-history hydration.
It verified 16 P03 archive rescans, reused 18 unchanged receipts, and reran exactly nine affected jobs after a rule change.
Its synthetic holdouts corroborated and refuted the same frozen hypothesis in separate scenarios.
The gate also refused repeated lineage and enforced the 24-hypothesis limit.
The retained `InferenceSessionGate.json` report has SHA-256 `54cf967fcb888800ea1d41aa3e97b790885c2c2874fe82294cb4905b8dd89e37`.
Native application acceptance and independent paired qualification retain their existing prerequisites.
