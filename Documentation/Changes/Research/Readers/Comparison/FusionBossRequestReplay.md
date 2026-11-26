<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic P03 Fusion Boss request replay

The existing Fusion Boss probe can prepare a replay from the saved P03 SOLIDWORKS baseline. Preparation preserves the existing typed Boss request and independently binds it to the original sketch, support, Origin and measurement evidence. It records all seven ordered saved relations. The four corner aliases remain separate. The source custody records all 25 native definitions outside the logical writer view. [Source admission evidence](PinnedPublicAdmission.md)

Replay reads the prepared request and source witness. It checks an independently retained digest for each file before generation. The original source, logical JSON, capture data and Git checkout need not be available. The process uses the existing direct-owned Boss authoring path, a pinned deterministic helper, and two pinned snapshot builders. The report records the helper and SDK code identities and actual import origins. It records the candidate and report separately from the input custody files.

## Run the research replay

Use Python 3.14 and the checkout's pinned SDK. Prepare in a trusted checkout that contains the exact P03 capture objects. The command accepts unused output directories outside the checkout. Use the existing [constraint intent procedure](../../Encoder/ConstrainedBossIntent.md) to create the full source and logical JSON. Prepare the separate request and witness from those two files.

```sh
export PYTHONPATH=src:re/automation:re/solidworks/WriterResearch
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --prepare --source-json /private/Source.json --logical-json /private/Logical.json \
  --output /private/P03Prepared
```

Keep the reported digests independently of the files. Provision the exact code blobs from the trusted revision `a0c6e9f22082c7e0937f02af4464a1c06df9ed65`. Copy the Git blob bytes to separate Python files before starting replay. Replay checks each SHA-256 before import.

| Role | Source | Git object | SHA-256 |
| --- | --- | --- | --- |
| Deterministic clock and allocator | [`Fusion.py`](https://github.com/TryUniCAD/Kit/blob/a0c6e9f22082c7e0937f02af4464a1c06df9ed65/re/automation/EncoderRoundTrip/Fusion.py) | `ff451cb90c337024401d87b9536275c07f43e9c2` | `3cf89358a5ec58935d75135b171383f562f7b7b5defc1359594bf72c0e248826` |
| Typed prism snapshot | [`ProbePrismSnapshot.py`](https://github.com/TryUniCAD/Kit/blob/a0c6e9f22082c7e0937f02af4464a1c06df9ed65/re/Fusion/SavedCuboidGeneration/ProbePrismSnapshot.py) | `1bfa84c3d808411df7cdd5d388703d598c466d59` | `13ecde0884f7338d5e10548c511688b9e004d92e05686f9830dc9cb972e6a7b0` |
| Snapshot owners | [`SnapshotOwners.py`](https://github.com/TryUniCAD/Kit/blob/a0c6e9f22082c7e0937f02af4464a1c06df9ed65/re/Fusion/SavedCuboidSnapshot/SnapshotOwners.py) | `ad311697e6424176286f6409fb77cd8e73bc250f` | `81f2f57ea44063ad278f5d5d0dae086b98bfaa91428a4a7913c421bd11872814` |

Replay from the same SDK code and research Python files. Use the digests from preparation and pin Unix seconds. The command publishes the archive and report together after verification.

```sh
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --request /private/P03Prepared/P03Request.json --request-sha256 "$REQUEST_SHA" \
  --source-witness /private/P03Prepared/P03SourceWitness.json \
  --source-witness-sha256 "$WITNESS_SHA" --seed-helper /private/Fusion.py \
  --snapshot-builder /private/ProbePrismSnapshot.py \
  --snapshot-owners /private/SnapshotOwners.py \
  --written-at 1700000000 --output /private/P03Replay
```

## Readback and limits

The archive readback checks the four axis rules, distinct Origin coincidence and two driving dimensions. Fusion puts separate argument and observer orders in the saved records. The SOLIDWORKS baseline height points from the anchor to the upper corner. The generated Fusion height points from the upper corner to the anchor. The ordered width endpoints agree. The report marks the reversed height as unqualified. The source feature remains `join` in the witness and the target feature creates its first body. [Dimension operand order](../../../../Gotchas/Conversion/Fusion/Api/FusionDimensionSlots.md)

The sketch line normals use the generated positive XY frame. The two Browser settings observers precede the width and height observers. The replay verifies all four references in the generated graph. The older `--output` probe keeps its original layout. [Observer order](../../../../Gotchas/Conversion/Fusion/Api/FusionDimensionSlots.md)

The snapshot follows the generated solid, tagged profile and sketch geometry. The part has separate reciprocal tool, region and sketch owners. The snapshot uses the existing eight-byte wire. Its cache addresses use an experimental zero reset. Fusion application verification of that reset remains open.

The unchanged public strict reader returns the generated part with native state version 2 and the `fusion.read_only` marker. Its seven relations, body and owners match the lower prism projection. Full source, material, licensed Fusion usability, edit/save/reopen and held-out acceptance remain open. [Public reader dispatch](../../../../Gotchas/Conversion/Fusion/Api/FusionDirectBossParameterInventory.md)

## Verification

The Windows Python 3.14.6 integration case passed in 165.26 seconds with zlib-ng 1.3.1. Two fresh processes emitted identical 117,070-byte archives and matching reports. The producer revision was `752e1d5bf3a85e1e2ed0d730c1fef8ed6eb4875c`. The code-only checkout contained no Git data, source archive, source JSON or logical JSON. The established direct Boss and Origin cases both passed in 30.13 seconds. [Process test](../../../../../tests/Research/Archives/FusionBossRequest/BossReplayTests.py)

| Verified data | SHA-256 |
| --- | --- |
| Prepared typed request | `d460d8352b7e34526a5e95d451d5671454d8b30d8ef96e5adf90111d67812a49` |
| Source witness | `205f7c5f53307145b7ddeeae064404d51f1534cec144a3bc0e1129d93addf8c7` |
| Both final Fusion archives | `2ee2ae42c2a07eb9b08fab530f7741f8b1eeb45cc9542923438764cd291e10a5` |
| Raw generated snapshot | `e04ab8cd73f46f6d5fa433c6c73b5dbc8384ca65f73adf96d4206f302bf3937b` |
| Public strict document JSON | `5f23f5928b9b1736fe08391ca60a28a8f26196d3c7aae1ff1cbdf0329557991e` |

An independently audited fresh process produced the same archive. The audit allowed the prepared request, witness, checked helper code and codec vocabulary. It recorded no original source, logical JSON, native archive or Git access during replay. The body measured 40 × 20 × 10 mm and 8,000 mm³. Its centroid was (20, 10, 5) mm.

Five request mutations refused even after the request digests were updated. The unchanged witness rejected altered ownership, span, operand order, relation inventory and Origin. An existing destination retained its contents. A changed helper file, wrong Browser role, wrong rank and redirected snapshot tool owner also refused. [Refusal checks](../../../../../tests/Research/Archives/FusionBossRequest/CheckRefusals.py)
