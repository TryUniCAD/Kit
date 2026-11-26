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

Replay reads the prepared request and source witness. It checks an independently retained digest for each file before generation. The original source, logical JSON, capture data and Git checkout need not be available. The process uses the existing direct-owned Boss authoring path and a pinned deterministic generation helper. The report records the helper and SDK code identities and actual import origins. It records the candidate and report separately from the input custody files.

## Run the research replay

Use Python 3.14 and the checkout's pinned SDK. Prepare in a trusted checkout that contains the exact P03 capture objects. The command accepts unused output directories outside the checkout. Use the existing [constraint intent procedure](../../Encoder/ConstrainedBossIntent.md) to create the full source and logical JSON. Prepare the separate request and witness from those two files.

```sh
export PYTHONPATH=src:re/automation:re/solidworks/WriterResearch
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --prepare --source-json /private/Source.json --logical-json /private/Logical.json \
  --output /private/P03Prepared
```

Keep the reported digests independently of the files. Provision the exact committed `re/automation/EncoderRoundTrip/Fusion.py` blob from revision `a0c6e9f22082c7e0937f02af4464a1c06df9ed65`. Its Git object is `ff451cb90c337024401d87b9536275c07f43e9c2`. Its SHA-256 is `3cf89358a5ec58935d75135b171383f562f7b7b5defc1359594bf72c0e248826`. Copy its Git blob bytes to a trusted Python file before replay. [Pinned helper](https://github.com/TryUniCAD/Kit/blob/a0c6e9f22082c7e0937f02af4464a1c06df9ed65/re/automation/EncoderRoundTrip/Fusion.py)

Replay from the same SDK code and research Python files. Use the digests from preparation and pin Unix seconds. The command publishes the archive and report together after verification.

```sh
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossProbe.py \
  --request /private/P03Prepared/P03Request.json --request-sha256 "$REQUEST_SHA" \
  --source-witness /private/P03Prepared/P03SourceWitness.json \
  --source-witness-sha256 "$WITNESS_SHA" --seed-helper /private/Fusion.py \
  --written-at 1700000000 --output /private/P03Replay
```

## Readback and limits

The archive readback checks the four axis rules, distinct Origin coincidence and two driving dimensions. Fusion puts separate argument and observer orders in the saved records. The SOLIDWORKS baseline height points from the anchor to the upper corner. The generated Fusion height points from the upper corner to the anchor. The ordered width endpoints agree. The report marks the reversed height as unqualified. The source feature remains `join` in the witness and the target feature creates its first body. [Dimension operand order](../../../../Gotchas/Conversion/Fusion/Api/FusionDimensionSlots.md)

The archive readback checks the candidate's body and its parametric owner graph. The public strict reader refuses the candidate's direct-owned parameter inventory. Full source, material, Fusion application use, edit/save/reopen and held-out acceptance remain open. [Public reader limit](../../../../Gotchas/Conversion/Fusion/Api/FusionDirectBossParameterInventory.md)

## Verification

The Windows Python 3.14 integration case passed in 165.26 seconds. Two fresh processes emitted identical 99,756-byte candidates from the same request and witness. Both candidates have SHA-256 `b5a61f170caadac3305d6e852a83d664eb8943cff1e9247d25370ad60497b687`. The code-only checkout contained no Git data, native source or source and logical JSON. The generated body measured 40 × 20 × 10 mm, with a volume of 8,000 mm³ and centroid at (20, 10, 5) mm.

The command refused five altered requests even after their request digests were updated. The unchanged source witness rejected changes to the owner, physical span, operand order, relation inventory and Origin. An existing destination retained its contents. The report retains the checked SDK fingerprint, the seed helper identity and the independent source witness digest. [Process test](../../../../../tests/Research/Archives/FusionBossRequest/BossReplayTests.py)
