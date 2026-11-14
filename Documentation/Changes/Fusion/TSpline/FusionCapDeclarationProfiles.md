# Fusion TSM cap declaration profiles

## Behavior

`ReadTspline` now accepts `G0CAPS`, `G1CAPS`, and `G2CAPS` declarations. It also accepts `star-smoothness` values 0, 1, and 2.
The existing degree, unit, end-condition, knot-rule, version, counter, and tolerance checks remain unchanged.
Other cap names and star values still raise `ValueError`.

`ConvertCage` uses `CheckSurface` as its single declaration gate. It no longer applies a second G1-only restriction.
`SurfaceHeader` keeps `G1CAPS` and star value 0 as the defaults for new cages.
`WriteHeader` preserves the declaration stored in a parsed surface.
`SwapFormCage` still requires matching declarations in the old and new layouts.

Fusion ignores these two declarations when it selects the cap solve for the qualified profiles. The cage topology and grips determine the resulting body.
This rule has no per-layout table, saved geometry, donor payload, CAD runtime, or research-file dependency in production.

## Preparation

`PrepareCapVariants.py` applies each declaration through `dataclasses.replace` and emits the TSM through `EmitTspline`.
It builds each converted body through `ConvertForm` and each complete F3D through `EmitFormDoc`.
The five Box3 cases reproduce the existing one-field controls.
The five HeldPrism5 cases use a separate held-out cage with valence-five caps.

Each prepared Box3 body has 6 faces, 12 edges, and 8 vertices.
Each prepared HeldPrism5 body has 15 faces, 35 edges, and 22 vertices.
The [preparation report](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/Preparation.json) binds every generated TSM and F3D digest.

## Fusion acceptance

Fusion 2706.1.17 accepted all 10 independently emitted documents.
The [native acceptance report](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) has SHA-256 `46b1cd7392fcd1dd26a602ea9e01becf71140c2999f68bdb734ead4877d6c3e6`.
It contains 190 comparisons, zero problems, and a largest absolute deviation of `6.195044477408373e-14` cm.
Zero documents were open before and after the run.

For each case, Fusion imported the same TSM as the native control. Kit's F3D opened separately.
Both documents ran `computeAll`, moved the same control point, exported, and reopened.
The comparison covered topology, health, NURBS data, face grids, edge curves, vertices, area, and volume.

| Cage                              | Loaded area and volume                        | Edited and reopened area and volume           |
| --------------------------------- | --------------------------------------------- | --------------------------------------------- |
| Box3, all five declarations       | 28.19774998549261 cm²; 12.441043578278578 cm³ | 28.08639550286362 cm²; 12.398528701468491 cm³ |
| HeldPrism5, all five declarations | 14.693249836881733 cm²; 4.640593243655995 cm³ | 14.67340314680529 cm²; 4.622316303609363 cm³  |

The [static artifact inspection](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/ContainerInspection.json) independently inventoried the held-out `G2CAPS` F3D.
It found 24 ZIP occurrences, including 16 files, with zero integrity contradictions.
Its digest matched the preparation record. The static inspection did not execute Fusion or establish runtime semantics.

The [scrub validation](../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/ScrubValidation.json) compared all 10 retained native controls before and after scrubbing.
The scrubber changed zero bytes, and every typed document model remained identical.

## Compatibility coverage

The compressed TSM archive catalog now contains 22 cases, including all 10 declaration variants.
`TestTsmArchive` checks typed read, semantic digests, byte-exact emission, and a second read.
`TestTsmReject` adds unknown cap-name and star-value rejection through the public reader.
`TestGeneralCase` compares `ConvertForm` against the retained native body for all 10 variants.
These integration cases run in remote CI, not locally.

Run the reproducible research preparation with:

```sh
PYTHONPATH=src python3.14 re/Fusion/Reconstruction/FormDocuments/General/PrepareCapVariants.py
```

The separate local-Fusion oracle requires an available frontend bridge. Set `General/tmp/AcceptancePlan.txt` to `CapAccept` before dispatching `AcceptGeneral.py`.
The production codec does not use that bridge.
