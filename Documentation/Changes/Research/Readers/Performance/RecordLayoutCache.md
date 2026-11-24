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
Migration callbacks invalidate all cached layouts before reconstruction continues.
This includes changes to annotations or their namespace during a single decode.

This scope preserves annotation changes between reads, including inherited annotations and changes made by compatibility binding.
It avoids a process-wide cache that could retain obsolete model metadata.
Each independent or nested public decode creates its own cache.

The recursive decoder retains wire validation, enum checks, migrations, field aliases, constructor calls, and mapping immutability.
After integration with PR #284, wire validation runs once at the root before the cache is shared across recursive reconstruction.
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
| SOLIDWORKS part      |    756,461 |        165.9 ms |          59.4 ms |                       1,826 → 57 |
| Fusion control       |  3,251,625 |        716.6 ms |         694.5 ms |                         198 → 34 |

The intervals measure `CadDocument.from_json`, including public document validation.
They exclude imports, native parsing, JSON output, receipt construction, and disk writes.
A separate profiler pass measured type-hint calls.
Every reconstructed document serialized to the original canonical JSON bytes.
The SOLIDWORKS JSON SHA-256 is `7636513a3a18daa8e2546f58b868e998a2b3d67d036e7685aa44cd365628a958`.
The Fusion JSON SHA-256 is `c5d945d47f525b017fa22272865ea841fc645d26398a1915a66d0214c2710862`.

The focused interchange and registry compatibility run passed 148 cases.
Added coverage reconstructs a complete document containing 300 parameters and checks canonical JSON equality.
Registered extension coverage checks inherited annotations, replacement annotations, and in-place annotation changes between reads.
Migration coverage changes mapping annotations between records within one decode.
A separate case changes another class whose layout was cached before the migration.
All five cache compatibility cases join the existing Python 3.11 native compatibility shards.
The shared collector, allocator, reports, and completeness gate retain their existing execution path.
Local Python 3.11 collection produced 663 cases across four shards.
All five cache cases appeared exactly once across those selections.
The workflow passed the local offline Zizmor pedantic audit with no findings.
A linked assembly case preserves the 75-level public JSON roundtrip on CPython 3.11.15.
The Python 3.11 selection passed 126 cases with the locked `typing-extensions==4.16.0`.
The complete 148-case selection passed on Python 3.14.7.
The 22 existing Fusion face-offset cases require ZIP Zstandard support from Python 3.14.
They fail on Python 3.11 before record reconstruction, including an independently reproduced baseline failure.
Those cases remain in the unchanged suite and passed on Python 3.14.7.

The combined PR #284 conflict repair passed 163 interchange, registry, JSON format, deep assembly, and production import policy cases on Python 3.14.7.
Six cache and deep assembly cases passed on Python 3.11.15, including the 80-level linked assembly roundtrip.
A public decoding profile confirmed one root wire-validation call across 165 wire values.
These checks verify the combined behavior without a new performance measurement.

The follow-up review repair restricts deferred discovery to the two known Kit facades and their declared exports.
Third-party plugins retain direct namespace discovery when unrelated optional exports cannot load.
The [optional export gotcha](../../../../Gotchas/Conversion/Runtime/OptionalFacadeDiscovery.md) records this boundary and its filesystem integration coverage.
Deferred imports now share the original audited plugin import call without another security-rule suppression.
The Python 3.11 compatibility roster also includes the actual 80-level `CheckDeepJson` case in its existing four shards.
The revised roster collected 664 cases and selected that case exactly once across the four complete shards.
The focused review repair passed 18 cases on Python 3.11.15 and 39 cases on Python 3.14.7.
The nonliteral-import security rule reported zero findings across the discovery boundary and deferred facade loader.
The offline pedantic workflow audit also reported zero findings.

## Scope and limits

Task: B14-RecordDecodeCache. Owner: Codex. Delivery branch: `codex/cache-record-types`.
Dependencies are the shared interchange codec and the existing public document APIs.
The exit requires unchanged canonical bytes, preserved rejection behavior, scoped verification, current-head CI, and configured review.

The measurements cover two documents on one host.
The SOLIDWORKS reconstruction reduction is about 64 percent.
The Fusion reduction is about 3 percent and does not establish a broad Fusion throughput gain.
The conflict repair integrates PR #284's root-validation and import optimizations.
Combined performance remains unmeasured.
Native application acceptance and merge-group acceptance remain separate.

See the [serialization reference](../../../../Reference/Data/Serialization.md).

The [bound callback depth gotcha](../../../../Gotchas/Conversion/Json/BoundDecoderDepth.md) records the initial Python 3.11 regression and its repair.
