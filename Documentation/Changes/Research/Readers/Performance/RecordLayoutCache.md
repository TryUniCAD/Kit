<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Cache record layouts during JSON reconstruction

## Behavior

The decoder resolves mapping field annotations once per record class within each top-level `FromData` operation.
Repeated records reuse an immutable tuple of mapping field names.
The cache ends when that operation returns or raises an exception.
No cache survives into the next document read.

This scope preserves annotation changes between reads, including inherited annotations and changes made by compatibility binding.
It avoids a process-wide cache that could retain obsolete model metadata.
Each independent or nested public decode creates its own cache.

The recursive decoder retains wire validation, enum checks, migrations, field aliases, constructor calls, and mapping immutability.
Type lookup completes before recursive record construction to preserve the existing recursion structure.
There is no new option or dependency.
Use the existing JSON and mapping reader APIs.

## Verification

The baseline is main `625bdbf9efa35d0fdc4939c59f68561aa927db4b`.
Measurements used CPython 3.14.7 on macOS ARM64.
Each arm used its own interpreter and source tree.
Both interpreters remained loaded while five measured pairs alternated their execution order after one warm-up pair.

The inputs were canonical neutral documents from these native files:

- `re/solidworks/examples/.SLDPRT/example.SLDPRT`, default configuration and permissive public read.
- `re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d`, strict public read.

| Reconstruction input | JSON bytes | Baseline median | Candidate median | Type-hint calls before and after |
| -------------------- | ---------: | --------------: | ---------------: | -------------------------------: |
| SOLIDWORKS part      |    756,461 |        155.5 ms |          54.8 ms |                       1,826 → 47 |
| Fusion control       |  3,251,625 |        638.8 ms |         628.9 ms |                         198 → 34 |

The intervals measure `CadDocument.from_json`, including public document validation.
They exclude imports, native parsing, JSON output, receipt construction, and disk writes.
A separate profiler pass measured type-hint calls.
Every reconstructed document serialized to the original canonical JSON bytes.
The SOLIDWORKS JSON SHA-256 is `7636513a3a18daa8e2546f58b868e998a2b3d67d036e7685aa44cd365628a958`.
The Fusion JSON SHA-256 is `c5d945d47f525b017fa22272865ea841fc645d26398a1915a66d0214c2710862`.

The focused interchange and registry compatibility run passed 145 cases.
Added coverage reconstructs a complete document containing 300 parameters and checks canonical JSON equality.
Registered extension coverage checks inherited annotations, replacement annotations, and in-place annotation changes between reads.

## Scope and limits

Task: B14-RecordDecodeCache. Owner: Codex. Delivery branch: `codex/cache-record-types`.
Dependencies are the shared interchange codec and the existing public document APIs.
The exit requires unchanged canonical bytes, preserved rejection behavior, scoped verification, current-head CI, and configured review.

The measurements cover two documents on one host.
The SOLIDWORKS reconstruction reduction is about 65 percent.
The Fusion reduction is about 2 percent and does not establish a broad Fusion throughput gain.
This change does not include PR #284's root-validation or import optimizations.
Combined performance with that PR remains unmeasured.
Native application acceptance and merge-group acceptance remain separate.

See the [serialization reference](../../../../Reference/Data/Serialization.md).
