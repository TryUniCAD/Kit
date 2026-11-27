<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Navigate the Fusion and SOLIDWORKS decoders

Use Graphify to trace source relationships across both native readers.
The graph describes code structure. It does not establish decoded format coverage,
prove runtime behavior, or replace native acceptance evidence.

## Prepare the tool

Install the CLI in an isolated development environment:

```sh
uv tool install graphifyy==0.9.97
```

This workflow uses local AST extraction. It needs no API key, LLM backend,
CAD application, or production dependency change.

## Extract both source trees

Run these commands from the repository root. Use the path casing shown below.
Record `git rev-parse HEAD` with any findings so the source revision is explicit.

```sh
graphify extract src/convert/Formats/Fusion --code-only --force --no-cluster --out tmp/DecoderGraph/Fusion
graphify extract src/convert/adapters/solidworks --code-only --force --no-cluster --out tmp/DecoderGraph/Solidworks
```

Each extraction writes its own `graphify-out/` directory below its output path.
Keep these raw graphs. They retain relationship records that the merged overview
can collapse.
Read extraction warnings before using the result. A successful command can report
partially extracted syntax or skipped files. Inspect those files directly.

## Build the combined overview

```sh
graphify merge-graphs tmp/DecoderGraph/Fusion/graphify-out/graph.json tmp/DecoderGraph/Solidworks/graphify-out/graph.json --out tmp/DecoderGraph/graphify-out/graph.json
graphify cluster-only tmp/DecoderGraph --no-label --no-viz
graphify export html --graph tmp/DecoderGraph/graphify-out/graph.json
```

The combined directory contains `graph.json`, `GRAPH_REPORT.md`, and `graph.html`.
Open `graph.html` to inspect the visualization.
Graphs above 5,000 nodes use a community overview by default.
`--no-label` avoids LLM naming; community names can be generic.
The cluster-only report does not recover extraction-time file counts or costs.
Use the extraction logs and raw graphs for those facts.
Local AST extraction makes no LLM requests.

Generated outputs stay under ignored `tmp/`. Rebuild both extracts, merge,
cluster, and export after source changes. Keep the two source trees separate
when rebuilding so same-named files and symbols retain their format identity.

## Query an entry point

```sh
graphify explain 'Fusion::documentread_readfusiondoc' --graph tmp/DecoderGraph/graphify-out/graph.json
graphify explain 'Solidworks::core_native_decodenative' --graph tmp/DecoderGraph/graphify-out/graph.json
graphify query 'construction plane controls' --seed constructionplane_planecontrols_readplaneparams --context call --graph tmp/DecoderGraph/Fusion/graphify-out/graph.json
```

The merged graph prefixes internal node IDs with the extraction directory name.
External dependency nodes can be shared between formats.
Source paths remain relative to each extraction root:

| Node prefix    | Source root                       |
| -------------- | --------------------------------- |
| `Fusion::`     | `src/convert/Formats/Fusion`      |
| `Solidworks::` | `src/convert/adapters/solidworks` |

Use the node's format identity to resolve its source path.
Read the returned source and focused checks before recording a finding.
For supported scope and evidence, start with the [Fusion feature index](../../../re/Fusion/README.md)
or the [SOLIDWORKS research index](../../../re/solidworks/README.md).

## Check relationship integrity

```sh
graphify diagnose multigraph --graph tmp/DecoderGraph/Fusion/graphify-out/graph.json
graphify diagnose multigraph --graph tmp/DecoderGraph/Solidworks/graphify-out/graph.json
```

Inspect missing endpoints, dangling endpoints, self-loops, and parallel-edge
counts. The undirected overview keeps one edge per endpoint pair, so distinct
relations such as `calls`, `references`, and `uses` can collapse.
Use the raw extraction for the original relationship records.
See [parallel relationship collapse](../../Gotchas/Research/GraphifyParallelRelationships.md).

Files with no symbol declarations can still have file and import nodes.
Inferred AST relationships are navigation hints, not proof of runtime execution.

If a query finds no matching node, check the extraction's node IDs and source
revision. If extraction reports a partial file, use the source directly and retain
the warning with the finding. Stop treating the graph as complete until the
extraction limit is resolved.
