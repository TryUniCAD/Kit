# Sketch circle and relation field candidates

Offline field research for how a SOLIDWORKS sketch **circle** (centre, radius) and a
**geometric relation** are stored in a generation-19000 `.SLDPRT`.
Confidence words follow `records/Serialize.md`: **confirmed** = read out of the typed
reader *and* reproduced on real bytes; **partial** = read out of the reader or the
decompiled layout but not independently checked by a bounded search; **not found**.

Every offset below is measured on committed bytes. No offset is guessed and no donor
value is carried forward. This record claims no writer support and no application
acceptance; it locates storage only.

Pinned revision: `main` `1619f00bf532caad262d1557bd69281179e5c497`.
Tools: `re/automation/InferenceGrid/FeatureDispatch.py` and
`re/automation/FieldSearch.py`.
`FeatureDispatch.py` exposes no model options, and the inference runner's `--advisor`
and `--codex-on-stall` were left off. **No model advice was requested or used.**

## Corpora, and why the two named packages are the relation half only

| package                                    | files                    | content                                                       |
| ------------------------------------------ | ------------------------ | ------------------------------------------------------------- |
| `re/NativePlacement2026/Cases/`             | 24 SOLIDWORKS variations | one rectangular boss; `Manifest.json` marks `split` per case   |
| `re/solidworks/FeatureLadderRecovery/Cases/`| 37 variations            | one rectangular boss                                          |
| `re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/` | 5         | one dimensioned circle sketch (the circular cohort)           |

Neither `re/NativePlacement2026/Cases/` nor `re/solidworks/FeatureLadderRecovery/Cases/`
contains a circle. Their READMEs, `Manifest.json`, `Campaign.json` and
`re/solidworks/FeatureLadderRecovery/Manifest.json` describe only rectangular
cuboid bosses, and searching both manifests for `circle` returns nothing.
Their rectangle sketches do store relations, so they are the relation corpus.
The only committed circle sketches are the five P02 archives, which the planner
already names as this feature's evidence (`family:sketchconics:circle` →
"P02 SOLIDWORKS native circle binding readback").

Held-out split: `re/NativePlacement2026/Manifest.json` marks six SOLIDWORKS variations
as held-out — `solidworks-003`, `-007`, `-011`, `-015`, `-019`, `-023`. P02 is a
discovery cohort with no held-out sibling.

## Commands run

```sh
git fetch origin pull/296/head:pr296
git show pr296:Documentation/Maintenance/SolidworksReaderWriterPlan.md

python3 re/automation/InferenceGrid/FeatureDispatch.py \
  --catalogue re/solidworks/PlannerCatalog/Sources/FeaturePlan.json manifest
python3 re/automation/InferenceGrid/FeatureDispatch.py --feature family:sketchconics:circle recipe
python3 re/automation/InferenceGrid/FeatureDispatch.py --feature family:sketchrelations:coincident-relation recipe
python3 re/automation/InferenceGrid/FeatureDispatch.py --feature family:sketchrelations:horizontal-relation recipe

python3 /tmp/circle_fields.py       # driver A
python3 /tmp/circle_fields2.py      # driver B
python3 /tmp/relation_check2.py     # driver C
python3 /tmp/scan_relations.py      # driver D
python3 /tmp/scan_p045.py           # driver E
python3 /tmp/verify_offsets.py      # driver F
```

`FeatureDispatch.py` reports `family:sketchconics:circle` as `blocked` with
`available_evidence: "P02 SOLIDWORKS native circle binding readback"` and
`blockers: ["reviewed_decoder_route_for_readback_required"]`; every
`family:sketchrelations:*` entry is `blocked` with
`pinned_native_evidence_required`. The written `recipe` output for
`family:sketchconics:circle` is the paired P02 recipe, and for
`family:sketchrelations:horizontal-relation` it asks for a line from `(0, 0)` to about
`(20, 3)` with a horizontal relation.

The driver bodies are reproduced at the end of this record.

## Candidates: circles

All offsets are in `Contents/Config-0-ResolvedFeatures` and all five P02 archives agree
on them.

| # | field | stream / record | offset | encoding | confirmed on | held-out |
| - | ----- | --------------- | ------ | -------- | ------------ | -------- |
| 1 | circle profile record | `ResolvedFeatures`, record kind `sketch-profile-circle` | `6561`, length `112` | typed archive sub-record, no scalar | all 5 P02 | no |
| 2 | circle centre coordinates | point record at `5771`, length `142`; x at `record+76 = 5847`, y at `record+84 = 5855` | `5847`, `5855` | 2 × `f64` little-endian, **metres** | **partial**: the position is the shared point-record layout and the bytes read `0000000000000000` twice; value contrast is absent so the search cannot confirm it | no |
| 3 | circle seam (rim) coordinates | point record at `5913`, length `167`; x at `record+76 = 5989`, y at `record+84 = 5997` | `5989`, `5997` | 2 × `f64` little-endian, metres | all 5 P02 by `FieldSearch` (`f64:little:m:signed` and `:magnitude`, relative `76` and `84`) | no |
| 4 | radius | — | **not stored** | derived: `radius = ‖seam − centre‖` in metres | refuted hypothesis: searching the seam body with the radius value returns **0** candidates (100 models, 64 `predicted_bytes_absent`) | n/a |
| 5 | diameter dimension scalar | `ResolvedFeatures`, record kind `sketch-diameter`, record span `6707` length `215` | `6803`, 8 bytes | `f64` little-endian metres | all 5 P02 by `FieldSearch` (`f64:little:m:signed`); `0.01` m for the 10 mm circle, `0.016` m for the 16 mm edit | no |
| 6 | further diameter copies | `ResolvedFeatures` | `7863`, `8097`, `8121` | `f64` little-endian metres | all 5 P02 by byte search of the exact 8-byte pattern; `8121` is preceded by `08000000 10000000 01000000 01000000` (`8105:8121`) and followed by `fffeff00ffff010012006d6f4661766f` (`8129:8145`) | no |
| 7 | diameter copy in the configuration stream | `Contents/Config-0` | **absent** | — | the 16 mm edit file has zero occurrences of `fca9f1d24d62903f` in `Config-0`; the baseline's apparent hits are the many generic `0.01` defaults | n/a |
| 8 | origin-proxy point entity | `ResolvedFeatures`, record kind `sketch-origin-point` | `6080`, length `465` | typed archive record | all 5 P02 | no |

Measured values (driver B): for `baseline-a` the seam coordinates are
`(0.004781523779815177, 0.0014618585236136866)` m whose norm is exactly `0.005` m, and
for `edit-diameter_mm-16` `(0.007650438047704283, 0.0023389736377818987)` m whose norm
is exactly `0.008` m. The centre is `(0, 0)` in all five files. The seam is at an
arbitrary angle, which is why the raw coordinate is not the radius.

The public reader already emits these locations as provenance:
`sketch-profile-circle` at `6561`/`112`, `sketch-diameter` at `6707`/`215`, and the
`diameter_mm` parameter as 10 mm / 16 mm owned by `sldprt:feature:26`.

## Candidates: relations

| # | relation | stream / record | offset | encoding | confirmed on | held-out |
| - | -------- | --------------- | ------ | -------- | ------------ | -------- |
| 1 | origin↔centre coincidence | `ResolvedFeatures`, record kind `sketch-origin-coincidence` | `6930`, length `73` | little-endian ints plus archive pointer tokens: dim id `-1`, **type code 9**, operand count 2, reserved 0, suppressed/deleted flags, then `<2H` = `(65534, 0)`, then two `sgPointHandle` objects; point indices `[2, 0]` | all 5 P02; the 73 bytes are **byte-identical** in all five, including the diameter edit, so this record carries no radius | no |
| 2 | per-member axis relation rows | `ResolvedFeatures`, inline in the `sgSketch` body | **offset not established on any committed file** | one row = dimension fields + `<2H` flags + `sgLineHandle` target; **type code 4 = horizontal, 5 = vertical** (`Sketch/Geometry.py` `KAxisRelations`) | reader-only: `Sketch/Relations.py` `ReadRelations` → `Sketch/Geometry.py` `BindRelations` → `Core/RectRelations.py` `ProjectAxes` (record kind `sketch-axis-relation`) | no |
| 3 | axis relations as the reader actually emits them | `ResolvedFeatures`, record kind `sketch-constraint` | `6996`, `7088`, `7180`, `7272`, each length `8` | none — geometry inference from the rectangle profile; `native_code` is `null` | 24 NativePlacement2026 + 37 FeatureLadderRecovery variations (61 files), 244 constraints | **yes** — the same 2 horizontal / 2 vertical / 4 coincident pattern holds on all six held-out NativePlacement2026 files |
| 4 | relation manager | `Contents/Config-0` `moRelMgr_c` | layout only (`Archive/Bodies/Layouts/Config/RelMgrFields.py`) | `suObList` at `f58`, `RelCacheDimValueMap_c` at `f10` as an array of text key + `f64` value, text `f170`, ints, `suObList` `fa0`, repeated node rows at `f1c0` | **not found** — no reader consumes it and no committed file ties a relation to a cache entry | n/a |

Driver D confirms candidate 3 and the negative for candidate 2: across all 61 rectangle
variations the public reader returns exactly
`{'horizontal': 122, 'vertical': 122, 'coincident': 244}` with every constraint span
kind `sketch-constraint` and none `sketch-axis-relation`. The four span offsets each
begin `ffff1f0003`, the current marker prefix, so those provenance spans point at the
line-marker records rather than at stored relation rows.

The committed decode reports `re/NativePlacement2026/Reports/solidworks-003/variation.json.gz`
and `re/NativePlacement2026/Reports/solidworks-023/variation.json.gz` agree with the same
2 horizontal / 2 vertical / 4 coincident pattern:

```sh
python3 -c '
import gzip, json
from collections import Counter
for cid in ("solidworks-003", "solidworks-023"):
    p = f"re/NativePlacement2026/Reports/{cid}/variation.json.gz"
    d = json.loads(gzip.decompress(open(p, "rb").read()))
    for sk in d["document"]["sketches"]["$tuple"]:
        c = Counter(row["kind"] for row in sk["constraints"]["$tuple"])
        print(p, sk["name"], dict(c))
'
```

```text
re/NativePlacement2026/Reports/solidworks-003/variation.json.gz Sketch1 {'horizontal': 2, 'vertical': 2, 'coincident': 4}
re/NativePlacement2026/Reports/solidworks-023/variation.json.gz Sketch1 {'horizontal': 2, 'vertical': 2, 'coincident': 4}
```

No relation type-code enum beyond `4`, `5` and `9` was located, so equal, parallel,
perpendicular, concentric, tangent, symmetric, midpoint, collinear, fixed, normal,
pierce and along-axis codes are **not found**.

## Held-out result

- **Relations (inferred):** held. The emitted axis and coincidence pattern reproduced on
  six held-out NativePlacement2026 files and all 37 FeatureLadderRecovery files.
- **Relations (stored rows):** not exercised on any file, so unproven.
- **Circles: no held-out file exists.** `Documentation/Changes/Research/Workers/SolidWorks/CircleBindingReadback.md`
  reserves P05 as the circular holdout, but decoding all seven P05 archives (driver E)
  returns one `AnnulusProfile` sketch each — 4 `LineGeometry`, 4 `PointGeometry`,
  2 `NativeGeometry` — with no `CircleGeometry`. P05 therefore cannot serve as the
  circle holdout, and every circle candidate above rests on the five P02 discovery
  files only.

## Still ambiguous

1. **Off-origin circle centre.** All five P02 centres are `(0, 0)`, so `FieldSearch`
   refuses the centre body (`field search needs distinct samples and finite contrasting
   values`). The centre coordinate encoding is therefore structural, not search-proven.
2. **Whether any stored scalar carries the radius or diameter besides the dimension
   scalar.** The same 8-byte value appears four times in the resolved stream
   (`6803`, `7863`, `8097`, `8121`). Which copies are the driving parameter, a display
   cache, and a value pair is unresolved, and their owners are unproven.
3. **The stored axis-relation rows.** Their type codes `4`/`5` and `sgLineHandle` target
   are read by `ReadRelations`, but no committed file surfaces them, so their offsets and
   even their presence in the rectangle family are unconfirmed.
4. **Every other relation type code**, the operand counts, and whether a two-member
   relation row shares the axis-row layout.
5. **The relation manager cache.** `RelCacheDimValueMap_c` keys and the unit of its `f64`
   values are unknown.
6. **Coincidence operand order** — `[proxy, centre]` in P02 — and whether it is stable
   when the coincidence joins two sketch-local points rather than a document origin.
7. **Unit independence.** P02 `units-inch` stores the diameter scalar in metres, like the
   millimetre files, but a single inch-display capture does not settle whether any
   inch-mode copy exists elsewhere in the archive.

## Captures that would settle it

Each capture needs the paired-capture controls (control before, variation, control after)
and an independent SOLIDWORKS measurement of the values named.

1. **Off-origin circle centres.** One Front-plane sketch per capture with a single
   dimensioned circle at a distinct non-zero centre — for example `(12.5, 7.25)` mm and
   `(31.75, -4.5)` mm at the same diameter. Two captures give the centre search the
   contrast it needs.
2. **Radius ownership.** One sketch containing two circles of different diameters, each
   with its own driving dimension, so a per-circle radius scalar would be distinguishable
   from the shared pattern.
3. **Relation type codes.** One sketch per relation with that relation alone and nothing
   else — the planner's `rel-*` recipes already specify them, e.g. `rel-horizontal` as a
   line `(0, 0)`→`(20, 3)` plus a horizontal relation — differenced against a
   no-relation control of the same sketch. This is the only way to obtain codes for
   equal, parallel, perpendicular, concentric, tangent, symmetric, midpoint, collinear,
   fixed, normal, pierce and along-axis.
4. **Stored axis rows in the rectangle family.** One rectangle whose edge is drawn
   off-axis and then constrained horizontal, plus a control without the relation,
   differenced to locate the stored row.
5. **Relation manager cache.** The same sketch saved with and without one named relation,
   compared over `Contents/Config-0` `moRelMgr_c` to learn the key text and value unit.
6. **Coincidence between two sketch points.** A sketch with two points made coincident
   with no document-origin operand, to test the operand order and the `(65534, 0)`
   trailer.

## Reproduction drivers

Driver A — offsets and bounded searches over the P02 cohort. `ROOT` is the checkout.

```python
import json, sys
from pathlib import Path
ROOT = Path("/path/to/Kit")
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/automation")]
from FieldSearch import Sample, search
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.Circular.ReadCircleOnly import ReadCircleOnly
from convert.adapters.solidworks.Config.RootLayout import KConfigGen

COHORT = ROOT / "re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39"
CASES = (("baseline-a", 5.0), ("baseline-b", 5.0), ("edit-diameter_mm-16", 8.0),
         ("units-inch", 5.0), ("plane-yz", 5.0))
RESOLVED = "Contents/Config-0-ResolvedFeatures"
resolved, cases = {}, {}
for name, radius_mm in CASES:
    archive = SldprtArchive.from_bytes((COHORT / f"P02-solidworks-{name}.SLDPRT").read_bytes())
    resolved[name] = archive.streams[RESOLVED]
    parsed = ReadCircleOnly(archive.streams["Contents/Config-0"], resolved[name], KConfigGen)
    centre = parsed.Points[parsed.Circle["center_slot"]]
    seam = parsed.Points[parsed.Circle["seam_slot"]]
    cases[name] = {"centre": centre, "seam": seam, "diameter": parsed.Diameter}

def body(name, span):
    return resolved[name][span[0]:span[1]]

# the diameter scalar and the seam coordinates are located by aligned hits
print(search([Sample(n, cases[n]["diameter"]["diameter_m"] * 1000.0,
                     resolved[n][cases[n]["diameter"]["parameter_offset"]:
                                 cases[n]["diameter"]["parameter_offset"] + 8])
              for n, _ in CASES]))
print(search([Sample(n, cases[n]["seam"]["xy_m"][0] * 1000.0, body(n, cases[n]["seam"]["span"]))
              for n, _ in CASES]))
```

Driver B — the same search with the seam y coordinate and the whole diameter record, plus
the radius hypothesis that must fail.

```python
# driver A's imports and cases, then:
print(search([Sample(n, cases[n]["seam"]["xy_m"][1] * 1000.0, body(n, cases[n]["seam"]["span"]))
              for n, _ in CASES]))
print(search([Sample(n, cases[n]["diameter"]["diameter_m"] * 1000.0,
                     body(n, cases[n]["diameter"]["span"])) for n, _ in CASES]))
print(search([Sample(n, radius_mm, body(n, cases[n]["seam"]["span"]))
              for n, radius_mm in CASES]))          # 0 candidates: the radius is derived
```

Driver C — the public reader's circle and relation provenance.

```python
import sys
from pathlib import Path
ROOT = Path("/path/to/Kit")
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from convert.adapters.solidworks import read_sldprt as ReadSldprt

for name in ("baseline-a", "edit-diameter_mm-16"):
    path = ROOT / f"re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39/P02-solidworks-{name}.SLDPRT"
    document = ReadSldprt(path.read_bytes())
    for sketch in document.sketches:
        for entity in sketch.entities:
            for span in (entity.provenance.spans if entity.provenance else ()):
                print(name, "entity", span.stream, span.offset, span.length, span.record_kind)
        for constraint in sketch.constraints:
            for span in (constraint.provenance.spans if constraint.provenance else ()):
                print(name, "constraint", constraint.kind, span.stream, span.offset,
                      span.length, span.record_kind)
```

Driver D — relation record kinds across both rectangle corpora, including the held-out
split.

```python
import glob, sys
from collections import Counter
from pathlib import Path
ROOT = Path("/path/to/Kit")
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from convert.adapters.solidworks import read_sldprt as ReadSldprt

files = (sorted(glob.glob(str(ROOT / "re/NativePlacement2026/Cases/solidworks-*/variation.SLDPRT")))
         + sorted(glob.glob(str(ROOT / "re/solidworks/FeatureLadderRecovery/Cases/solidworks-*/variation.SLDPRT"))))
kinds, spans = Counter(), Counter()
for path in files:
    for sketch in ReadSldprt(Path(path).read_bytes()).sketches:
        for constraint in sketch.constraints:
            kinds[constraint.kind] += 1
            for span in (constraint.provenance.spans if constraint.provenance else ()):
                spans[span.record_kind] += 1
print(len(files), dict(kinds), dict(spans))
```

Driver E — the P05 holdout check.

```python
# driver D's imports, then:
files = sorted(glob.glob(str(ROOT / "re/automation/PairedCaptures/P05/solidworks-*/P05-*.SLDPRT")))
for path in files:
    for sketch in ReadSldprt(Path(path).read_bytes()).sketches:
        print(Path(path).name, sketch.name,
              Counter(type(entity.geometry).__name__ for entity in sketch.entities))
```

Driver F — the centre coordinate bytes and the diameter copies.

```python
import struct, sys
from pathlib import Path
ROOT = Path("/path/to/Kit")
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.Circular.ReadCircleOnly import ReadCircleOnly
from convert.adapters.solidworks.Config.RootLayout import KConfigGen

COHORT = ROOT / "re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39"
for name in ("baseline-a", "edit-diameter_mm-16"):
    archive = SldprtArchive.from_bytes((COHORT / f"P02-solidworks-{name}.SLDPRT").read_bytes())
    resolved = archive.streams["Contents/Config-0-ResolvedFeatures"]
    parsed = ReadCircleOnly(archive.streams["Contents/Config-0"], resolved, KConfigGen)
    centre = parsed.Points[parsed.Circle["center_slot"]]
    print(name, "centre", struct.unpack_from("<2d", resolved, centre["span"][0] + 76))
    pattern = struct.pack("<d", parsed.Diameter["diameter_m"])
    found, index = [], resolved.find(pattern)
    while index != -1:
        found.append(index)
        index = resolved.find(pattern, index + 1)
    print(name, "diameter copies", found,
          "config copies", archive.streams["Contents/Config-0"].count(pattern))
```

## Related evidence

- `records/Sketch.md` — the `sg*` record layouts, and the finding that an arc and a full
  circle share `sgArc` and store no radius.
- `records/CircleReverse.md` — the reversed circular boss field diff.
- `records/CircularSketchOnly.md` — the standalone circular framing and its refusals.
- `Documentation/Changes/Research/Workers/SolidWorks/CircleBindingReadback.md` — the
  licensed P02 circle and relation observations.
- `Documentation/Gotchas/Conversion/SolidWorksSketchRelationOperands.md` — the current and
  definition operands of a sketch relation.
- `Documentation/Maintenance/SolidworksReaderWriterPlan.md` (PR #296) — the discovery loop
  this record answers.
