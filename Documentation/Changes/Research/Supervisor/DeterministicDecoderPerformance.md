<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic decoder performance

The A03 controller can bind multiple input files in one invocation.
The offline pilot uses this command to prepare its pinned inputs.
The controller publishes verified file bytes before committing the bindings.
It then reconciles dependent jobs against the complete batch.

## Bind a batch of evidence

Write a UTF-8 JSON manifest with one to 256 entries and up to 256 MiB of input files.
Each entry supplies a unique binding name and a file path.
Relative paths start at the manifest directory.

```json
{
  "bindings": [
    { "name": "source:left", "file": "left.bin" },
    { "name": "source:right", "file": "right.bin" }
  ]
}
```

```shell
python re/automation/Controller.py --store /private/ResearchStore bind-batch /private/Bindings.json
```

The response lists each accepted binding name and SHA-256 in manifest order.
A failed batch leaves earlier bindings intact.
Published content objects can remain unreferenced after a failure.
[Artifact rollback boundary](../../../Gotchas/Research/ArtifactPublicationOutlivesRollback.md)

## Stage inputs and read Fusion files

The built-in A03 supervisor resolves artifacts directly after verifying its store owner.
This uses the same read-only lookup previously used on Windows.
Each worker still receives a private copy verified against the scheduled digest.

The strict Fusion reader reuses parsed class definitions for matching vocabulary text.
Each read checks the current vocabulary text to detect data changes in research checkouts.
The native-state serializer reuses field layouts for its registered types.
Input validation, native state and canonical output retain their existing formats.

## Verification

Eight focused integration and round-trip checks passed locally.
Three serial 21-job P03 runs used the new bind and staging paths.
The pipeline median was 6.83 seconds.
Both neutral document artifacts matched the earlier baseline byte for byte.
The comparison, assessments, and rescans retained their results.

The strict Fusion run repeated 20 fresh archives three times.
The warm median was 66.3 ms per read, compared with the audit baseline of 111.6 ms.
The 20 fresh archives and eight archived controls retained their exact neutral JSON hashes.

[Controller commands](../../../Reference/Research/ResearchController.md#bind-inputs-in-a-batch) · [Supervisor adapter](../../../Reference/Research/ResearchSupervisor.md#controller-adapters)
