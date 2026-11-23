<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Semantic comparison session binding

The comparison worker now uses the same session validator as the inference worker.
It requires dependency receipt records to match the normalized job's complete declared dependency roster.
Receipt records require exact supported fields and lowercase SHA-256 digests.
Direct result selectors must match their dependency result digest.
Artifact selectors retain their separate artifact digests.

Previously, a recalculated fingerprint could accompany missing, undeclared, or malformed dependency records and still publish a comparison report.
The [dependency snapshot gotcha](../../../Gotchas/Research/SemanticDependencySnapshot.md) records the failure mechanism and recovery procedure.

Session metadata also uses the existing bounded plain-file reader and strict JSON parser.
Linked packets, duplicate keys, and nonfinite metadata fail before report or result publication.
The existing controller prepares the required version 1 session without operator changes.
Update the job's immutable `tool_version` when deploying the changed worker.
Retain earlier receipts with their original implementation identity.

The [comparison guide](../../../Reference/Research/SemanticComparison.md) defines scheduling and observation limits.
Comparison statuses, semantic differences, tolerances, and qualification fields retain their existing behavior.
Every accepted observation remains semantically unverified with native acceptance unestablished.
This repair supplies no independent source custody, native qualification, or conversion acceptance.

## Verification evidence

Authored process controls invoke the real worker with recalculated fingerprints and contradictory dependency snapshots.
Positive controls retain artifact selectors, direct result selectors, and pending-CI dependency metadata.
Negative controls cover missing and undeclared dependencies, malformed or incomplete receipts, unexpected fields, invalid pending digests, and mismatched direct selectors.
Additional controls cover stale fingerprints, duplicate metadata, linked session files, and nonfinite metadata.
The existing native reader bridge verifies accepted controller artifact selectors for the P01 Fusion and SOLIDWORKS controls.
Native Windows verification used the existing CPython 3.14.6 environment without dependency changes.
The focused comparison session, controller runner, native reader bridge, and direction controls passed all 25 cases in 104.85 seconds.
The P03 sketch-reference controller case passed separately in 26.26 seconds.
The broader comparison sweep passed 113 cases and encountered seven sandbox permission refusals during controller input binding.
Every refused case passed in the elevated focused executions recorded above.
The original refusals occurred before job submission and did not indicate semantic comparison failures.
Black, Prettier, Ruff, focused steering, Mypy, and Pyright checks passed for the changed files within their applicable scopes.
