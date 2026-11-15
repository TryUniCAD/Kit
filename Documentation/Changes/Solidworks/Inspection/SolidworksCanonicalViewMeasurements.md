# Publish bounded canonical-view measurements

The negative-half-angle view generator now has a published native measurement batch for three generated polygon parts.
The [evidence directory](../../../../re/solidworks/measurements/2026/CanonicalViews/README.md) contains native results, derived comparisons, provenance and ten unchanged PNGs.
The [construction record](../../../../re/solidworks/records/StandardViewsConstruction2026.md) links the measured result to the recovered native rules.
Its refuted positive-half-angle history remains available.

## Evidence

The generator and inspector revision is `b9a599fdc95f8f8aa6534343568ba6c9ca11bb49`.
The original native report has SHA-256 `7b690c431d7997827058763239945d2c3135f1273cefcc883b9fd0cb150f044b`.
The publication replaces only home-share paths and reformats JSON.
Provenance distinguishes that original digest from the published report digest.
It also labels the original manifest's false measurement flags as a pre-run staging snapshot.

Two healthy controls bracket H3, H5 and H7 in five distinct recorded native processes.
All five cases opened with zero errors and warnings, rebuilt successfully and returned one body.
All source hashes remained unchanged, with no recorded dialog or cleanup errors.
Each oracle identity matches build `34.5.2.0604` and the pinned executable hash.

All nine standard-view rotation arrays match both controls before and after selection.
The maximum absolute coefficient discrepancy is `7.888609052210118e-31`, against a declared tolerance of `1e-12`.
All returned arrays have the required numeric lengths and contain finite values.
Candidate mass properties and extrusion-depth readback match independent baseline metrics and neutral models within declared tolerances.

The oracle owner inspected all ten PNGs.
Candidates initially show small, nonempty front-facing polygons.
After isometric selection and zoom, all three show extrusion depth and side faces.
The initial active camera is not identical to the controls.
The original BMPs remain external, with their hashes recorded beside the unchanged PNG hashes.
Lossless conversion provenance names macOS `sips`; decoded-pixel equality was not independently measured here.

## Use

Read the [native report](../../../../re/solidworks/measurements/2026/CanonicalViews/NativeViewReport.json) and
[derived analysis](../../../../re/solidworks/measurements/2026/CanonicalViews/Analysis.json) together.
Use the [image manifest](../../../../re/solidworks/measurements/2026/CanonicalViews/ImageManifest.json) to bind each initial and selected-view image.
From the checkout root, reproduce the derived analysis with:

```sh
python3 re/solidworks/measurements/2026/CanonicalViews/Analyze.py
pnpm dlx prettier@3.6.2 --write re/solidworks/measurements/2026/CanonicalViews/Analysis.json
```

This standalone analysis reads published measurements and neutral inputs.
It does not invoke CAD, open native source documents or import repository modules.
It rewrites only `Analysis.json`.
It does not repeat the oracle batch or execute product tests.

## Limits and verification

The evidence applies only to the stated source revision and three polygon cases.
Later configuration and profile changes need their own native measurements.
This batch did not edit driving dimensions or save and reopen the documents.
Initial-camera parity, the full CAD goal and curve or assembly writer acceptance remain unestablished.
The production SOLIDWORKS adapter remains read-only.
The publication agent did not launch, attach to or automate the oracle.
No local tests or held-out native stream inspection occurred during publication.
The published numeric comparisons and image hashes were recomputed from the recorded evidence.
