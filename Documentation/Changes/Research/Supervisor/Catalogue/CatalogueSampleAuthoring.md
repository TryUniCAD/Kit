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
decoding because a native capture succeeded. Neutral outputs are retained as
controller artifacts. This does not promote a new decoder rule or qualify a
cross-format conversion.

Pause and resume use the same directory and source revision. The saved plan,
worker registry, native host settings, and lifecycle settings are pinned.
Accepted native phases and decoder receipts are reused. The supervisor remains
alive through application restart and final acknowledgement waits. Coordinator
failure stops further supervised work and leaves the native recovery fences.

## Task and validation

A08h, owner Codex, branch `codex/catalogue-authoring-integration`, connects the
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

See [owned native attachment](../../../../Gotchas/Research/Workers/SolidWorks/OwnedNativeAttachment.md)
for the startup and lifetime corrections exposed by the native trial.
