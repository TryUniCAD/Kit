<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Author catalogue samples before decoding

The catalogue runner can now select the existing native sample builders rather
than only replay saved discovery archives. Add `--author-samples` to author
selected cases, retain their native measurements, reopen them in a different
owned application process, and automatically decode the accepted native files.
The earlier archive assessment path remains available without this option.

SOLIDWORKS uses its installed Windows executable and interop assembly. Fusion
uses its existing macOS application worker and automatic owner lifecycle. The
catalogue starts a lifecycle coordinator against its own queue receipt directory;
it does not depend on an unrelated coordinator noticing those receipts. Native
resources retain capacity one. Independent decoder jobs can run concurrently.

## Executable scope

The existing builders cover a constrained rectangle, a centered circle, a blind
rectangular boss, a centered rectangular cut, and an annular revolution. Their
driving dimensions are configurable. Supported options include principal support
planes, a reversed boss, and a through-all cut, subject to each builder's input
checks. Invalid dimensions and unimplemented controls fail before native entry.

Discovery selects P01, P03, and P04. Use `--capture-mode qualification` for P02 or
`--capture-mode holdout` for P05. These modes create new samples; they do not
consume or change the sealed historical capture lineages. Aliases share one
sample, while different requested dimensions produce different sample identities.
Plain-language feature recipes without an executable builder remain unavailable.

Use `--authoring-cases Cases.json` to select a parameter grid:

```json
{
  "schema_version": 1,
  "cases": [
    {
      "application": "solidworks",
      "feature": "family:extrude:boss-base-extrude",
      "parameters": { "width_mm": 43, "height_mm": 23, "depth_mm": 12 },
      "options": { "basis": "XY", "direction": 1 }
    }
  ]
}
```

Prepare a plan without a licensed application:

```shell
python re/automation/InferenceGrid/RunFeatureCatalogue.py --solidworks-catalogue FeaturePlan.json --directory /private/AuthorPlan --author-samples --authoring-cases Cases.json --prepare-only
```

For a Windows run, supply `--solidworks-host Host.json`. The file must contain
absolute installed `executable` and `interop_assembly` paths. Optional
`phase_seconds` bounds each native phase. Run with Python 3.14 or newer and add
`--native-ready` after preparing the isolated native host. The launcher refuses
existing SOLIDWORKS sessions and never attaches to an unrelated document.
Preparation captures an allowlisted set of standard Windows application/profile
directories for the native phase subprocess. It retains the private worker
temporary directory and does not pass credentials, Python module paths, or the
native profile to decoder workers.

For Fusion, supply the existing `--native-config`, `--native-kind`, and
`--native-resource` options together with `--fusion-lifecycle Lifecycle.json`.
The installation must opt into the existing automatic macOS owner policy at the
same source revision. Its signed-in initial application session must be ready.
The catalogue then owns the coordinator that handles the required phase restart.
Native batches contain at most two cases to retain the existing spool limits.

## Evidence and continuation

Each native capture retains controls, the requested parameter values, geometry,
driving edits and restorations, archive hashes, and fresh-process evidence.
The decoder consumes controller-accepted native artifacts. It reads each archive
twice and compares the neutral output bytes. Unsupported input and unresolved
fields remain explicit in `CatalogueResult.json`; they do not become successful
decoding because a native capture succeeded. Only portably qualified neutral
outputs are retained as controller artifacts. This does not promote a new decoder rule or qualify a
cross-format conversion.

Pause and resume use the same directory and source revision. The saved plan,
worker registry, native host settings, and lifecycle settings are pinned.
Accepted native phases and decoder receipts are reused. The supervisor remains
alive through application restart and final acknowledgement waits. Coordinator
failure stops further supervised work and leaves the native recovery fences.

## Task and validation

A08h, owner Codex, delivery [PR #207](https://github.com/TryUniCAD/Kit/pull/207)
from `codex/catalogue-native-authoring`, connects the
catalogue to parameterized native authoring. It depends on the existing A03/A08
controller, worker ownership, P01–P05 builders, and catalogue/resume work. Its exit
requires process integration coverage and measured native authoring, fresh reopen,
and downstream decoder evidence on each supported host. Product conversion
qualification remains separate.

The focused native Windows process suite passed 36 checks at `e533d094`. It covers
catalogue selection and parameter overrides, controller queueing and resume,
configuration tamper rejection, Fusion preparation, SOLIDWORKS compiler/admission,
retained receipt checks, lifecycle ownership, and real artifact-to-public-decoder
execution. Fixture transport checks explicitly claim no native acceptance.
The expanded suite passed all 38 checks at `27cc80b9` after the native environment
repair. Five affected controller/resume/public-decoder checks also passed after
integrating the merged catalogue prerequisites.

Review follow-up adds the three Windows native process checks to the shared
merge-queue platform selection and splits independent fixture helpers into
focused modules. All ten affected process checks passed after those changes.
The measured native authoring source files remain unchanged. A subsequent
review correction prevents unresolved or unqualified neutral bytes from being
published as translation artifacts. Research records retain the findings,
repeatability result, and neutral hash; portable qualification is required before
a neutral artifact can be accepted.
All four affected controller-to-decoder process checks passed after this guard.
Re-decoding the eight accepted SOLIDWORKS samples completed on attempt one:
all remained deterministic with 53 findings each, and no translation artifacts
were accepted. The replay receipt is
`1dde593ba7ab6451d8c7b4909b3533c8ce1027703f286201ef0d46639f881884`;
its retained evidence digest is
`0534e9c910b5dc9c2ef098e4f3c6b668c724912eb5af05be984554233f74181b`.

A separate configured SOLIDWORKS 34.4.1 run authored a 43 × 23 × 12 mm forward
XY boss: one solid, volume 11868.000000000002 mm³, center of mass
`[21.5, 11.5, 6]` mm. All eight saved archives passed fresh-process reopen and
rebuild, independent width/height/depth edits and restoration, and inch/YZ/reverse
variants. Both owned processes exited normally. Both controls matched at
881814.348203801 mm³. All 126 sealed captures, paired specifications, control,
and measured authoring source hashes remained unchanged. Earlier failed startup
attempts are retained separately.

The retained native acceptance report SHA-256 is
`8804559d89e79d319ef656b1cf1d270d83aa1df1c5342be3dda82ea0198c9901`.
The identical before/after evidence-map digest is
`fe30b3f2337f0a4e84434e1b5657b6b5bf507800a7090ec95fdb233dd328b521`.
This measures that configured P03 case. Native Fusion and other newly configured
recipe families retain their separate application acceptance requirements.

The complete catalogue command subsequently ran without intervention at
`27cc80b9`, whose source tree is identical to review commit `cfe1e913`. It authored
a fresh 47 × 29 × 13 mm boss: one solid, volume 17719 mm³, center of mass
approximately `[23.5, 14.5, 6.5]` mm. All eight archives passed native edits,
restoration, variants, fresh reopen, and rebuild. Both controls matched at
881814.3482038013 mm³; both native processes exited normally. The native capture
and dependent decoder each completed on attempt one with accepted controller
receipts and zero supervisor failures, orphans, or stale jobs. The standard
4096 MiB memory reserve remained enabled.

Capture receipt:
`771e471c17054de38d9dccdbdce170bbab41793205c90300e7ff3ba4dfa087a6`.
Decoder receipt:
`1581b76cced34772ee1424cc05b73609fecd73728ce36ef1200cb6679b1e780c`.
The native report digest is
`e3f376443f18182170d214dce95c8788b1a581964a65866157cdbd8e75ee7a34`;
the identical before/after evidence-map digest is
`1f5f8c4a38f2e7e2b05326f82e0a151b7c8bd8f2abbe6e8040a8104b2890b8af`.

The command correctly returned `2`, `coverage_incomplete`. All eight reader
outputs were deterministic, with 53 findings each: 25 native-only records,
26 retained byte spans without portable semantics, one direction/frame/operation
evidence finding, and one independent source inventory/native acceptance finding.
These are retained decoder gaps, not an interrupted pipeline. The decoder summary
digest is `82ced15e559fe6b763fd4ec9a335141e38283aee95236b2be793e2650d81ef6d`.

See [owned native attachment](../../../../Gotchas/Research/Workers/SolidWorks/OwnedNativeAttachment.md)
for the startup and lifetime corrections exposed by the native trial.
