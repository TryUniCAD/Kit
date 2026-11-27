<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Shared decoder graph workflow

The [Graphify guide](../../../Reference/Research/DecoderGraph.md) covers both Fusion
and SOLIDWORKS. It replaces the Fusion-only navigation instructions with a shared
workflow for isolated AST extraction, merging, clustering, HTML export, entry-point
inspection, and raw-relationship diagnostics.

Graphify is an optional development tool. Generated graphs remain under ignored
`tmp/`; the runtime and decoder behavior do not change.
The guide pins the tested tool version and preserves the input graphs because
the merged overview can collapse parallel relationships.
The [gotcha](../../../Gotchas/Research/GraphifyParallelRelationships.md) records that limit.

Task: shared decoder source navigation. Owner: Codex.
Scope: documentation for both readers. Dependency: Graphify 0.9.97 and the source
revision used for extraction. Delivery: this change's PR.
Exit: both extraction roots, combined graph outputs, source paths, entry-point
inspection, and diagnostics verified on the documented revision.

## Verification

The extraction ran against base `14570404846c8aa1f90b02e68d6f70a419719ca7`
with Graphify 0.9.97. Fusion supplied 2,459 code files; SOLIDWORKS supplied 980.
The merged graph contains 11,879 nodes, 61,113 overview edges, and 205 communities.
Graphify reported a partial syntax extraction for Fusion's
`BrepCodec/Journal/Spline/Writing/MakeKnots.py` and skipped `NativeClasses.xz`.
These limits remain visible; the graph is a source-navigation aid.
Both entry-point inspections and HTML export succeeded.
Raw-graph diagnostics found no missing or dangling endpoints, 43 self-loops,
and 9,175 relationships that can collapse in the undirected overview.
Prettier 3.10.1 formatting and validation of 71 local links passed.
Remote PR checks and configured review determine PR readiness; merge-group
acceptance remains separate. Graph structure does not establish CAD acceptance.
