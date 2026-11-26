<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Prepare a sealed Fusion Boss replay witness

`prepare-replay` admits the request-based P03 Fusion Boss into the existing two-phase witness planner. It retains the exact generated archive, report, request, independent source witness and three pinned authoring helper files. The planner verifies the source reopen receipt and the SDK and generator revisions. It reconstructs the complete replay report and rechecks the generated snapshot, reciprocal owners and public read-only document. [Generated replay and helper pins](FusionBossRequestReplay.md)

The command writes a schema 2 plan and seven sealed inputs only after all checks pass. The original schema 1 preparation and native phase receipt formats stay available. The phase launchers follow the existing build, independent process, healthy control and owned-document cleanup contract. The original source archive and logical JSON are not required for this preparation.

## Prepare and inspect

Use Python 3.14 and a trusted checkout holding the pinned Git revisions and healthy control. Use independently retained SHA-256 values for the archive, report, request and witness. Pass the exact helper code from the replay's three recorded Git blobs. Use a new private destination outside the checkout.

```sh
export PYTHONPATH=src:re/automation:re/solidworks/WriterResearch
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossWitness.py prepare-replay \
  --candidate /private/P03Replay --output /private/P03NativePlan \
  --archive-sha256 "$ARCHIVE_SHA" --manifest-sha256 "$REPORT_SHA" \
  --request /private/P03Prepared/P03Request.json --request-sha256 "$REQUEST_SHA" \
  --source-witness /private/P03Prepared/P03SourceWitness.json \
  --source-witness-sha256 "$WITNESS_SHA" --seed-helper /private/Fusion.py \
  --snapshot-builder /private/ProbePrismSnapshot.py --snapshot-owners /private/SnapshotOwners.py \
  --fusion-version 2706.1.17
```

Keep the returned plan digest independently. Inspect the same directory with the existing command. Inspection rechecks the sealed inputs, launchers and checked model without writing evidence or opening Fusion.

```sh
python -B re/Fusion/Reconstruction/DimensionAuthoring/SourceBossWitness.py inspect-plan \
  --witness /private/P03NativePlan --plan-sha256 "$PLAN_SHA"
```

## Host and acceptance limits

Windows and other non-macOS preparations return `prepared_p03_custody_offline`. Each offline launcher refuses before loading any native code. The native entry also rejects an offline plan before it loads any helper or opens a phase directory. Prepare and independently reseal on the approved licensed macOS host before any authorized execution. The schema 2 seal binds that checkout and plan location. A Windows plan cannot be used as evidence of host readiness.

The healthy control archive is pinned for the existing before-and-after checks. A successful offline inspection measures its custody. The native phases still need an exclusive matching Fusion build and separate process lifetimes. After a successful Phase A, the existing Phase B checks the archived restoration and that the earlier process exited. The retained offline verifier accepts separate externally held phase receipt hashes. [Licensed witness procedure](FusionSourceBossWitness.md)

The generated Fusion height arguments remain reversed relative to the source. The source Join and target first-body Create remain distinct. The generated snapshot still uses unmeasured zero-reset cache addresses. The previous Windows native tool failed before launch with `failed to write kernel assets` and OS error 3. No retry or native acceptance is part of this preparation. [Earlier tool outcome](https://github.com/TryUniCAD/Kit/blob/6639e85ef7b5715c0aac1e0f0a430f5fcf24c939/Documentation/Changes/Research/Encoder/FusionGeneratedCuboidSnapshot.md)

## Verification

On revision `08b17d481ffa9bbb4d2f49327f0727f79cf46213`, the exact PR #339 bundle prepared in 9.31 seconds and inspected in 9.20 seconds using Python 3.14.6 on Windows. The plan SHA-256 was `c635c861971516b4c99bd8e4849d0d9dc9663505738c68431516abb4fb269e0c`. It retained all seven inputs and both explicit offline launchers. It produced no phase results and no application process started.

The checked archive SHA-256 was `2ee2ae42c2a07eb9b08fab530f7741f8b1eeb45cc9542923438764cd291e10a5`. The unchanged public SDK returned the same v2 read-only document with SHA-256 `5f23f5928b9b1736fe08391ca60a28a8f26196d3c7aae1ff1cbdf0329557991e`. The healthy control was sealed with SHA-256 `09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c`.

An independent audited process prepared and inspected offline plan `0ae9d109dda6b8443579f991c68e777ecc7b35541a206f752a07b87db80403f5`. The archive, all seven retained inputs and both launchers stayed byte-identical through inspection. The audit recorded only pinned metadata and code reads. It opened no original source, logical JSON or native application.

The extended integration case passed in 187.26 seconds on the same producer revision. Two fresh replays from a newly prepared witness produced identical archives and reports. The plan retained all seven files, and `inspect-plan` preserved every prepared byte. The process refused a changed archive or report and rehashed claims about the snapshot and generator. It refused a changed helper and an occupied destination. A modified retained archive also refused under the original plan digest. [Process test](../../../../../tests/Research/Archives/FusionBossRequest/BossReplayTests.py)

The original Boss generation, schema 1 prepare and read-only inspection completed in 34.89 seconds. The schema 1 plan digest was `ac27ddc8e021d3bb4926f0f17bbcd7225c1a55b9cb92581d4ded22c736789f93`. No launcher or phase ran in either test.

The independent final guard test prepared and inspected offline plan `a6dc92c7f9b8436c8a97bb37b79ac1a842ad7f2bab847ae7bc7d750e8ccfdac1`. A fresh execution check refused before reading any helper or input archive. A new hash over a changed host label also refused because the execution path binding was absent. The valid plan and all seven files remained unchanged.

The final maintained integration case passed in 173.62 seconds with the execution guard. Three fresh validation processes rejected native execution of the offline plan, its changed host under the original seal, and its changed host after rehashing. The valid plan SHA-256 remained `613e8be6465754a49de7f1c8ce12c6c51227ebd93a3b12c0f7307f8298284243`. No phase directories were created.

The final execution guard keeps schema 1 valid. At producer revision `8e1e79ae387200661bad7f6081702d98becaef58`, a fresh schema 1 preparation and execution validation passed in 24.97 seconds with no phase directory. The plan SHA-256 was `5202d2b332b7ff963fe7f5394614230af074b72189fb764b58a45adb3c326fc6`.

The isolated checkout originally failed to resolve a deep chain of alternate object stores. The verified workaround restored the pinned checkout without changing other worktrees. [Git alternate stores](../../../../Gotchas/Research/Workers/Windows/GitAlternateObjectStores.md)
