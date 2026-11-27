# SOLIDWORKS sketch circle and relation field candidates

The research record [Sketch circle and relation field candidates](../../../../../re/solidworks/SketchCircleRelationFields.md)
records where a SOLIDWORKS generation-19000 sketch circle (centre, radius) and a
geometric relation are stored, as field candidates with measured offsets and a
confidence label. It answers discovery-loop item 5 of the
SOLIDWORKS reader and writer plan (on PR #296, not yet on the base branch).

## What it establishes

Circle, in `Contents/Config-0-ResolvedFeatures` on all five committed P02 archives:

| field                    | offset          | encoding                                  |
| ------------------------ | --------------- | ----------------------------------------- |
| circle profile record    | `6561`, len 112 | typed archive record                      |
| seam point x, y          | `5989`, `5997`  | `f64` little-endian metres                |
| centre point x, y        | `5847`, `5855`  | `f64` little-endian metres (value is zero)|
| diameter dimension scalar| `6803`          | `f64` little-endian metres                |
| radius                   | not stored      | derived as the centre-to-seam distance    |

Relation, likewise on all five P02 archives: the origin↔centre coincidence is a
73-byte record at `6930` with type code `9`, two point operands and the trailer
`<2H` = `(65534, 0)`; the bytes are identical in all five files, including the
diameter edit, so that record carries no radius. Per-member axis relation rows
(type code `4` horizontal, `5` vertical, `sgLineHandle` target, 55 bytes each) and
origin↔corner coincidence (type code `9`, 73 bytes) are confirmed in
`Contents/Config-0` across all 11 P04 paired captures (88 axis rows and 11
coincidence rows).

## Usage

Read the record for the offsets, the held-out status and the driver scripts, then
run the drivers against a checkout to reproduce each candidate:

```sh
python3 re/automation/InferenceGrid/FeatureDispatch.py \
  --catalogue re/solidworks/PlannerCatalog/Sources/FeaturePlan.json manifest
```

`FeatureDispatch.py` reports `family:sketchconics:circle` as `blocked` with the P02
readback as its only available evidence, and every `family:sketchrelations:*` entry
as `blocked` pending a pinned native capture. No model options were used.

## Limitations

The record locates storage only. It claims no writer, no conversion and no application
acceptance. Every circle candidate rests on the five P02 discovery archives because no
held-out circle sketch exists in the repository (0 held-out files): P05, the reserved circular holdout,
decodes as an `AnnulusProfile` revolution with no circle. The centre coordinate encoding
is structural rather than search-proven, the remaining diameter copies have unproven
owners, and no relation type code beyond `4`, `5` and `9` was located. The record names
the exact captures that would settle each open item.

## Verification evidence

Offline only, at `main` `1619f00bf532caad262d1557bd69281179e5c497`, with no CAD runtime and
no model advice. Bounded searches through `re/automation/FieldSearch.py` confirmed the
diameter scalar and the seam coordinates on all five P02 archives, and refuted the
radius-as-stored-scalar hypothesis with zero candidates. A scan of 24
`re/NativePlacement2026/Cases/` and 37 `re/solidworks/FeatureLadderRecovery/Cases/`
variations, including the six held-out NativePlacement2026 cases, returned 244
`sketch-constraint` spans and no `sketch-axis-relation` span, while all 11 P04 paired
captures confirmed 88 `sketch-axis-relation` and 11 `sketch-origin-coincidence` spans
in `Contents/Config-0`. All seven P05 archives were decoded to establish that the reserved holdout is not a circle.
