<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Remaining rectangle refusals

The 72 remaining refusals are unsupported datum/direction combinations:
48 XZ files and 24 reverse-YZ files. All first fail the same placement guard.
They are not missing-constraint failures or native-state parse failures.

## Revision and population

Investigated on 2026-11-23 against [PR #265](https://github.com/TryUniCAD/Kit/pull/265),
which was open and unmerged when checked. The isolated source checkout was
`14259fb00f2f54ef2501c4a9afd596318f16c676`; the user's working SDK was not substituted
for that revision. The original
[full replay receipt](https://github.com/TryUniCAD/Kit/blob/14259fb00f2f54ef2501c4a9afd596318f16c676/re/Fusion/RectangleRecovery/FinalReplayEvidence.json)
is bound to the earlier `10b0e7fe6656a195e4e97ef3e766f25ee9579a91` revision.

A fresh Python 3.14.7 public SDK replay checked all 144 source hashes against
that receipt, reproduced every outcome, and parsed all 144 typed native states.
Each row below contains eight batches with three saved files per batch:
control-before, variation and control-after. These are repeated controls within
one rectangle/extrusion family, not 144 independently qualified feature families.

| Campaign plane | Native frame | Distance | Batch IDs      | Files | Strict successes | Refusals |
| -------------- | ------------ | -------- | -------------- | ----: | ---------------: | -------: |
| front          | XY           | positive | fusion-000–007 |    24 |               24 |        0 |
| front          | XY           | negative | fusion-008–015 |    24 |               24 |        0 |
| top            | XZ           | positive | fusion-016–023 |    24 |                0 |       24 |
| top            | XZ           | negative | fusion-024–031 |    24 |                0 |       24 |
| right          | YZ           | positive | fusion-032–039 |    24 |               24 |        0 |
| right          | YZ           | negative | fusion-040–047 |    24 |                0 |       24 |

The fresh result is 72 successes, 72 refusals and zero differences from the
published classification. All refused sketches have zero geometric constraints
and zero linear dimensions. The broader constrained-annotation limitations in
the PR are separate from these 72 files.

## First refusal and later boundaries

Every refusal follows `ProjectPrism → CheckGraph → CheckBase → CheckPlacement →
CheckIdentity` and raises `Native Fusion profile requires identity placement`.
At the investigated revision the decisive call is `CheckPlacement.py:51`.

[ProjectPrism](https://github.com/TryUniCAD/Kit/blob/14259fb00f2f54ef2501c4a9afd596318f16c676/src/convert/adapters/Fusion/Native/Projection/ProjectPrism.py#L72)
sets `YzDatum` only when the saved distance is positive and the plane is exactly
`KYzMatrix`. Both XZ signs and reverse YZ therefore enter the ordinary identity
placement requirement in
[CheckPlacement](https://github.com/TryUniCAD/Kit/blob/14259fb00f2f54ef2501c4a9afd596318f16c676/src/convert/adapters/Fusion/Native/Policy/CheckPlacement.py#L48).
Changing `ReadRectRules` cannot address this failure: these files already take
its unconstrained path.

Independent diagnostic calls, without modifying the public reader, establish
additional boundaries:

- All 72 local rectangle and parameter readers succeed. Their bodies use
  `JournalModel` histories and `GeometryState` snapshots. `ReadInsert` and
  `ReadDatumSolid` recover both solid representations for every file, including
  the existing 170-entity datum snapshot layout.
- All 48 XZ files fail the independent `CheckExtrusion` check because their
  stored profile normal is +Y. The existing check admits +Z for XY or +X for YZ.
  The datum frame recipe and auxiliary sheet checks also encode YZ specifically.
- All 24 reverse-YZ files pass independent `ReadDatumFrame` and
  `CheckExtrusion(..., YzDatum=True)` calls. Their independent `ReadDatumBody`
  call fails at `CheckCuboid`'s volume comparison. Its local bounds are
  `(xmin, ymin, 0)` and `(xmax, ymax, negative_distance)`, producing a negative
  expected volume for a valid positive-volume solid.

These diagnostic calls do not establish public support or validate every later
ownership/tag check. Deleting the first guard alone is insufficient.

## Geometry corroboration

For every refused file, the eight journal vertices and eight snapshot vertices
match exactly the vertices derived from its native rectangle endpoints, signed
distance and saved frame. The stored normal equals the frame's third column.
The frame mappings in native centimeters are:

- XZ: `(x, y, z) → (x, z, -y)`; extrusion direction is +Y.
- YZ: `(x, y, z) → (z, y, -x)`; extrusion direction is +X.

The derivation uses all combinations of endpoint minima/maxima for local X/Y
and the stations `{0, signed_distance}` for local Z. It uses original native
coordinates, not coordinates rounded through neutral millimeters.

All 72 derived volumes, areas and rectangular centroids agree with the archived
`GroundTruth.json` measurements at relative tolerance `1e-8` for volume/area and
absolute tolerance `1e-8` cm for centroid. Source hashes, one native body and two
timeline entries also agree. Representative 23 × 20 × 10 mm variations are:

| File                     | Volume, mm³ | Area, mm² | Centroid, mm    |
| ------------------------ | ----------: | --------: | --------------- |
| fusion-016/variation.f3d |        4600 |      1780 | (11.5, 5, -10)  |
| fusion-024/variation.f3d |        4600 |      1780 | (11.5, -5, -10) |
| fusion-040/variation.f3d |        4600 |      1780 | (-5, 10, -11.5) |

This reuses the campaign's saved native measurements; no fresh CAD authoring or
vendor reopen was performed. It supports a frame/sign recovery hypothesis,
not complete feature semantics or native conversion acceptance.

## Reproduction and qualification

Use an isolated checkout of the investigated revision with its `src` and
`re/FeatureLadders2026` trees, Python 3.14 and the SDK dependencies. Run from that
checkout, choosing a fresh output path:

```sh
PYTHONPATH=src python3 -m convert decode re/FeatureLadders2026/Cases/fusion-016/variation.f3d -o /tmp/RectangleXzRefusal.json
```

Public CLI probes of `fusion-000`, `008`, `016`, `024`, `032` and `040` variation
files matched the SDK's six groups. The three refusals exited 1, emitted the
identity-placement diagnostic and created no output document.

Reproduce the complete outcome partition with the published, hash-bound inputs:

```python
import hashlib
import json
from collections import Counter
from pathlib import Path
from convert import open_document

root = Path("re/FeatureLadders2026")
receipt = json.loads(Path("re/Fusion/RectangleRecovery/FinalReplayEvidence.json").read_text())
counts = Counter()
for item in receipt["outcomes"]:
    source = root / item["source"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item["source_sha256"]
    try:
        open_document(source, source_format="fusion.f3d", strict=True)
        outcome = "success"
    except ValueError as error:
        assert str(error) == "Native Fusion profile requires identity placement"
        outcome = "refusal"
    assert (outcome == "success") == (item["exit_code"] == 0)
    counts[item["case"]["plane"], item["case"]["reverse"], outcome] += 1
print(counts)
```

The next bounded implementation should qualify XZ origin-datum ownership and
both signs, reuse the qualified YZ frame for either sign, normalize signed
local body bounds, and carry the selected frame through profile normals,
sections, face/edge tags, mass caches and neutral geometry. Retain reciprocal
ownership, exact geometry checks, absent constraints and read-only write guards.
Graphify tracing confirmed these checks cross the projection, policy, datum and
signed-body modules.

Before admitting those paths, author separate XZ-positive, XZ-negative and
YZ-negative holdouts, including decimal dimensions. Require independent body,
volume, area and centroid comparisons, malformed frame/normal/sign/tag/mass
negatives, marker-present and marker-stripped write refusals, and a full
144-file replay without regressions. Campaign inputs remain discovery evidence;
they cannot also be relabelled as independent holdouts.
