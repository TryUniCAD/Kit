<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Graphify can collapse parallel relationships

An extraction can record several relationships between the same two nodes.
For example, a function can call another symbol and reference its type.
Expecting the combined overview to retain every relationship record is incorrect.

Graphify 0.9.97 merges graphs into an undirected simple graph.
That graph keeps one edge for each endpoint pair.
Distinct `calls`, `references`, or `uses` relationships can therefore collapse.
A lower merged edge count does not, by itself, mean that extraction failed.

Keep each `extract --no-cluster` output before merging.
Run `graphify diagnose multigraph --graph PATH` on those raw graphs to inspect
missing endpoints, dangling endpoints, self-loops, and collapse counts.
Use the raw relationship records when exact relation types or directions matter.
Do not treat a successful HTML export as an integrity check.

The [decoder graph guide](../../Reference/Research/DecoderGraph.md) gives the
separate extraction and diagnostic commands for Fusion and SOLIDWORKS.
