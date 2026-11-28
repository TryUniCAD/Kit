# Sketch dimension fields in the pinned ladder families and P04 controls

This page records where the rectangle sketch width and height, and the blind
boss depth, are stored in the committed SOLIDWORKS sample families. It is the
evidence for discovery-loop item 5 of the
SOLIDWORKS reader and writer plan on
[PR #296](https://github.com/TryUniCAD/Kit/pull/296)
(`Documentation/Maintenance/SolidworksReaderWriterPlan.md`).
It is discovery evidence, not a writer rule and not conversion acceptance.

## 1. Files searched and the question

The instruction was to use committed families where one dimension changes
between files with known values. The two families named are
`re/solidworks/FeatureLadderRecovery/Cases/` (cases 059-095) and
`re/FeatureLadders2026/Cases/solidworks-*` (cases 048-058). Every case saves a
rectangle sketch and a blind extrusion three times: `control-before`,
`variation`, and `control-after`. The `variation` changes exactly one of
`width_mm`, `height_mm`, or `depth_mm`, and `GroundTruth.json` records the
values.

**The ladder rectangles carry no sketch dimensions.** Each recipe calls
`SketchManager.CreateCornerRectangle` and then `FeatureExtrusion2`; it never
calls `AddDimension`. The only `<Dimension>` in the saved
`swXmlContents/KeyWords` XML belongs to the extrusion
(`<Extrusion ...><Dimension Name="D1">10</Dimension>`), and the public reader
reports zero dimensions on `Sketch1`. So in these files the rectangle width and
height exist only as **sketch point coordinates**, and the one authored
dimension is the extrusion depth `D1`.

Real sketch distance dimensions do exist in another committed family with known
values, the P04 paired captures under
`re/automation/PairedCaptures/P04/solidworks-c1986308375a/`, whose driving
parameters and independent edits are in
`re/automation/PairSpecs.json`. That family is where the dimension records were
located, and its control grid supplies the strongest holdout. It is included
below so the question is actually answered, not left at "nothing found".

## 2. Method

`re/automation/FieldSearch.py` searches aligned record bodies for the
byte patterns of a measured value across a sample grid and keeps only offsets
that agree in every sample (aligned from the body start or the body end). No
AI options were used: `--advisor` and `--codex-on-stall` stay off, and
`FieldSearch.py` and `InferenceRunner.py` were not edited.

Each family's three files were treated as one sample grid with the value from
`GroundTruth.json` (ladders) or `PairSpecs.json` (P04). The body passed to
`FieldSearch.py` is the named archive stream, extracted with the repository's
own container reader, `SldprtArchive.from_bytes(...).require(stream)`. Where a
field has to survive a layout change, its position is also expressed relative
to the enclosing record reported by the public reader
(`convert.adapters.solidworks.Core.Adapter.NativePartModel`), not as an
absolute stream offset.

## 3. Candidate fields

All encodings found were `f64:little:m:signed` (IEEE-754 binary64,
little-endian, metres); the `magnitude` variant is the same bytes for these
positive values and adds no information. `marker` is a sketch point record in
`Contents/Config-0-ResolvedFeatures`; the reader reports these as circle
markers carrying `(x, y)` millimetres.

### 3.1 Ladder families (values are sketch point coordinates, not dimensions)

| Quantity | Stream | Record | Offset | Encoding | Found on | Held out |
| --- | --- | --- | --- | --- | --- | --- |
| Sketch-x (rectangle width) | `Contents/Config-0-ResolvedFeatures` | `Sketch1` point marker, x component | marker start + 66 (absolute 6015 = 5949+66 on the discovery file) | f64 LE metres | `solidworks-062` (`variation` 40 -> 31 mm) | yes, 45 other `variation` files |
| Sketch-y (rectangle height) | `Contents/Config-0-ResolvedFeatures` | `Sketch1` point marker, y component | marker start + 74 (absolute 6023 = 5949+74) | f64 LE metres | `solidworks-059` (`variation` 20 -> 37 mm) | yes, 45 other `variation` files |
| Boss depth `D1` (authored dimension) | `Contents/Config-0-ResolvedFeatures` | `Boss-Extrude1` distance-dimension record, value field | record start = reader `native_offset` (10176 on the discovery layout) | f64 LE metres | `solidworks-060` (`variation` 10 -> 4 mm) | yes, 45 other `variation` files |

Full candidate set returned by `FieldSearch.py` on the discovery batch, in
`Contents/Config-0-ResolvedFeatures`:

| Dimension | Variation | Candidate offsets in the stream |
| --- | --- | --- |
| height | 20 -> 37 mm | 6023, 6185, 10216, 10240 |
| width | 40 -> 31 mm | 6015, 6339, 10208, 10232 |
| depth | 10 -> 4 mm | 10176, 10574, 10598, 10736, 10760 |

On `solidworks-059` the reader places `Sketch1` at stream span
`[5578, 8351)` with markers at 5771 `(0, 0)`, 5949 `(40, 37)`, 6111 `(0, 37)`,
and 6273 `(40, 0)` mm. That first block of offsets is exactly the marker
coordinate fields: 5949+66 / 5949+74 is `(40, 37)`, 6111+74 is the second
height copy, and 6273+66 is the second width copy.

The remaining offsets are **derived copies**, not authored fields:

- 10208/10216/10232/10240 sit inside `Boss-Extrude1`'s resolved
  feature record right after its `D1` value at 10176; they repeat the
  profile-corner `(width, height)` twice.
- 10574/10598/10736/10760 sit in the extrusion's end-spec region. On the
  direction-negative batches (cases 048-055) 10574 and 10598 carry the signed
  value (`-depth`) while 10176, 10736 and 10760 stay positive, which shows they
  are direction-dependent derived copies rather than the driving value.

These copies move together with the archive layout: on `solidworks-064` the
feature-record block shifts by +72 (the reader reports `D1` at 10248 = 10.0 mm,
width repeats at 10280/10304 = 23.0 mm, and 10288/10312 decode to 0.0 mm and
10.0 mm rather than the 20.0 mm height). That is why the absolute
offsets are only valid for a fixed layout and the record-relative form is the
one recorded above.

The same height value also occurs as an f64 in several other streams of the
`solidworks-059` grid (`Contents/Config-0` @ 2604, `Contents/Config-0-ModelHeader`
@ 2189, `Header2` @ 2189, `Contents/Config-0-LWDATA` @ 36, `Contents/DisplayLists`
at ten further offsets). These are the same geometry mirrored into header,
lightweight, and display caches; they are stable only within one layout too, so
`Contents/Config-0-ResolvedFeatures` is the stream to read.

### 3.2 P04 paired captures (real sketch distance dimensions)

P04 authors a `RectangleSketch` with two distance dimensions, `width_mm` and
`height_mm`, plus a face-supported `CutSketch` with four more. The reader
reports `width_mm`/`height_mm` with `native_stream = Contents/Config-0`.

| Quantity | Stream | Record | Offset | Encoding | Found on | Held out |
| --- | --- | --- | --- | --- | --- | --- |
| `width_mm` | `Contents/Config-0` | `RectangleSketch` distance-dimension record, value field | record start = reader `native_offset` (14556 in the edit layout, 14518 in `baseline-a`) | f64 LE metres | 7 same-layout P04 edit captures (44 vs 40 mm) | yes, 4 held-out captures |
| `height_mm` | `Contents/Config-0` | `RectangleSketch` distance-dimension record, value field | record start = reader `native_offset` (14712 edit layout, 14674 `baseline-a`) | f64 LE metres | 7 same-layout P04 edit captures (24 vs 20 mm) | yes, 4 held-out captures |

`FieldSearch.py` on the seven same-length (`Contents/Config-0` = 42925 bytes)
edit captures returns `width_mm` at 14556 and `height_mm` at 14712, matching the
reader's `native_offset` for those files. The offsets shift with layout
(`baseline-a` 14518/14674, `plane-yz` and `termination-through-all` 14516/14672),
so the field is defined by the record and its reader `native_offset`, never by a
fixed stream offset.

## 4. Holdout evidence

The rule "sketch-x at marker+66, sketch-y at marker+74, `D1` at the dimension
record's `native_offset`" was located on `solidworks-059`, `solidworks-062`, and
`solidworks-060` and then applied unchanged to every other `variation` file in
both directories. All 48 `variation` files satisfy it (45 of them were not used
to find the field), so the width/height/depth values are read correctly on files
with different planes and extrusion directions.

The P04 rule "`width_mm`/`height_mm` value at the dimension record's
`native_offset` in `Contents/Config-0`" was located on the 7 same-layout
edit captures (`edit-width_mm-44`, `edit-height_mm-24`, `edit-depth_mm-12`,
`edit-cut_width_mm-12`, `edit-cut_height_mm-10`, `edit-cut_depth_mm-5`,
`units-inch`) and verified on all 11 P04 captures, including the 4 held-out
captures (`baseline-a`, `baseline-b`, `plane-yz`,
`termination-through-all`). All 11 read back the values recorded in
`PairSpecs.json`.

No angular sketch dimension was found in either family, because none of the
pinned files authors one; the only angle in the wider corpora (P05
`angle_deg`) is a revolve feature parameter, not a sketch dimension.

## 5. Limits and the capture still needed

The ladder families cannot answer "where is a sketch driving dimension stored",
because their rectangles are unconstrained. For a generative reader/writer rule
the following capture is needed, and does not exist yet:

1. A part that calls `AddDimension` on a rectangle so the rectangle has real
   driving sketch dimensions (a length, a distance, and an angular dimension),
   with two distinct values per dimension across separate saves.
2. Repeat saves at one value so incidental fields can be separated from authored
   ones, and a dimension edit inside SOLIDWORKS followed by rebuild and reopen.
3. The same grid on the top and right planes and on a non-default sketch frame.

Running the same `FieldSearch.py` grid over that capture would give the dimension
records the same way this page gives the ladder geometry fields. Until then, the
only authored dimension field located in these families is the extrusion `D1`,
and the rectangle width/height remain geometry coordinates.

## 6. Exact commands

Run from the repository root. The ladder search wrote this script to a scratch
path and ran it; the body is reproduced so the command is repeatable.

```shell
cat > SketchDimensionSearch.py <<'PY'
"""Locate the rectangle width/height and extrusion depth fields in the pinned ladder families."""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, "re/automation")
from FieldSearch import Sample, search
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel

STREAM = "Contents/Config-0-ResolvedFeatures"
RECOVERY = Path("re/solidworks/FeatureLadderRecovery/Cases")
LADDERS = Path("re/FeatureLadders2026/Cases")
DISCOVERY = (("solidworks-059", RECOVERY, "height"),
             ("solidworks-062", RECOVERY, "width"),
             ("solidworks-060", RECOVERY, "depth"))

def value(body, offset):
    return struct.unpack_from("<d", body, offset)[0]

for case, root, dim in DISCOVERY:
    gt = json.load(open(root / case / "GroundTruth.json"))
    files = {row["case"]: float(row["parameters_mm"][dim]) for row in gt["cases"]}
    samples = []
    for label, millimetres in files.items():
        raw = (root / case / f"{label}.SLDPRT").read_bytes()
        samples.append(Sample(label, millimetres, SldprtArchive.from_bytes(raw, label).require(STREAM)))
    result = search(samples)
    print(f"{case} dim={dim} values_mm={files}")
    for candidate in result["candidates"]:
        if candidate["encoding"] != "f64:little:m:signed":
            continue
        offsets = {label: row["body_offset"] for label, row in candidate["samples"].items()}
        print(f"  candidate f64:little:m:signed at {offsets} -> {value(samples[1].body, offsets['variation'])*1000} mm")

def holdout():
    checked = passed = 0
    for root in (RECOVERY, LADDERS):
        for case_dir in sorted(root.glob("solidworks-*")):
            gt = json.load(open(case_dir / "GroundTruth.json"))
            for row in gt["cases"]:
                if row["case"] != "variation":
                    continue
                pm = row["parameters_mm"]
                raw = (case_dir / f"{row['case']}.SLDPRT").read_bytes()
                archive = SldprtArchive.from_bytes(raw, row["case"])
                body = archive.require(STREAM)
                model = NativePartModel(archive, None)
                xs = [round(value(body, m.offset + 66) * 1000, 3) for m in model.sketches[0].markers if m.coordinates_mm is not None]
                ys = [round(value(body, m.offset + 74) * 1000, 3) for m in model.sketches[0].markers if m.coordinates_mm is not None]
                (dimension,) = [d for f in model.features for d in f.dimensions if d.name == "D1"]
                depth = round(value(body, dimension.native_offset) * 1000, 3)
                checked += 1
                if set(xs) <= {0.0, float(pm["width"])} and set(ys) <= {0.0, float(pm["height"])} and depth == pm["depth"]:
                    passed += 1
    print(f"holdout: {passed}/{checked} variation files satisfy x in {{0,width}}, y in {{0,height}}, D1 value == depth")

holdout()
PY
uv run python SketchDimensionSearch.py
```

Observed output:

```
solidworks-059 dim=height values_mm={'control-before': 20.0, 'variation': 37.0, 'control-after': 20.0}
  candidate f64:little:m:signed at {'control-before': 6023, 'variation': 6023, 'control-after': 6023} -> 37.0 mm
  candidate f64:little:m:signed at {'control-before': 6185, 'variation': 6185, 'control-after': 6185} -> 37.0 mm
  candidate f64:little:m:signed at {'control-before': 10216, 'variation': 10216, 'control-after': 10216} -> 37.0 mm
  candidate f64:little:m:signed at {'control-before': 10240, 'variation': 10240, 'control-after': 10240} -> 37.0 mm
solidworks-062 dim=width values_mm={'control-before': 40.0, 'variation': 31.0, 'control-after': 40.0}
  candidate f64:little:m:signed at {'control-before': 6015, 'variation': 6015, 'control-after': 6015} -> 31.0 mm
  candidate f64:little:m:signed at {'control-before': 6339, 'variation': 6339, 'control-after': 6339} -> 31.0 mm
  candidate f64:little:m:signed at {'control-before': 10208, 'variation': 10208, 'control-after': 10208} -> 31.0 mm
  candidate f64:little:m:signed at {'control-before': 10232, 'variation': 10232, 'control-after': 10232} -> 31.0 mm
solidworks-060 dim=depth values_mm={'control-before': 10.0, 'variation': 4.0, 'control-after': 10.0}
  candidate f64:little:m:signed at {'control-before': 10176, 'variation': 10176, 'control-after': 10176} -> 4.0 mm
  candidate f64:little:m:signed at {'control-before': 10574, 'variation': 10574, 'control-after': 10574} -> 4.0 mm
  candidate f64:little:m:signed at {'control-before': 10598, 'variation': 10598, 'control-after': 10598} -> 4.0 mm
  candidate f64:little:m:signed at {'control-before': 10736, 'variation': 10736, 'control-after': 10736} -> 4.0 mm
  candidate f64:little:m:signed at {'control-before': 10760, 'variation': 10760, 'control-after': 10760} -> 4.0 mm
holdout: 48/48 variation files satisfy x in {0,width}, y in {0,height}, D1 value == depth
```

The record attribution used the public reader's own inventory:

```shell
cat > SketchDimensionAttribution.py <<'PY'
from pathlib import Path
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel

raw = Path("re/solidworks/FeatureLadderRecovery/Cases/solidworks-059/variation.SLDPRT").read_bytes()
archive = SldprtArchive.from_bytes(raw, "variation")
model = NativePartModel(archive, None)
for sketch in model.sketches:
    print("sketch", sketch.name, sketch.native_stream, sketch.native_offset, sketch.native_end)
    for marker in sketch.markers:
        print("  marker", marker.offset, marker.native_kind, marker.coordinates_mm)
for feature in model.features:
    for dimension in feature.dimensions:
        print("dimension", feature.name, dimension.name, dimension.value_mm, dimension.native_stream, dimension.native_offset)
PY
uv run python SketchDimensionAttribution.py
```

The P04 search over the same-layout edit captures:

```shell
cat > P04DimensionSearch.py <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "re/automation")
from FieldSearch import Sample, search
from convert.adapters.solidworks.Container.Container import SldprtArchive

base = Path("re/automation/PairedCaptures/P04/solidworks-c1986308375a")
dp = [r for r in json.load(open("re/automation/PairSpecs.json"))["recipes"] if r["id"] == "P04"][0]["driving_parameters"]
values = {
    "baseline-a": (dp["width_mm"], dp["height_mm"]),
    "baseline-b": (dp["width_mm"], dp["height_mm"]),
    "edit-width_mm-44": (44, dp["height_mm"]),
    "edit-height_mm-24": (dp["width_mm"], 24),
    "edit-depth_mm-12": (dp["width_mm"], dp["height_mm"]),
    "edit-cut_width_mm-12": (dp["width_mm"], dp["height_mm"]),
    "edit-cut_height_mm-10": (dp["width_mm"], dp["height_mm"]),
    "edit-cut_depth_mm-5": (dp["width_mm"], dp["height_mm"]),
    "plane-yz": (dp["width_mm"], dp["height_mm"]),
    "termination-through-all": (dp["width_mm"], dp["height_mm"]),
    "units-inch": (dp["width_mm"], dp["height_mm"]),
}
for dim, index in (("width", 0), ("height", 1)):
    samples = []
    for name in ("edit-width_mm-44", "edit-height_mm-24", "edit-depth_mm-12",
                 "edit-cut_width_mm-12", "edit-cut_height_mm-10", "edit-cut_depth_mm-5", "units-inch"):
        raw = (base / f"P04-solidworks-{name}.SLDPRT").read_bytes()
        body = SldprtArchive.from_bytes(raw, name).require("Contents/Config-0")
        samples.append(Sample(name, float(values[name][index]), body))
    result = search(samples)
    print(dim, [(c["encoding"], sorted({v["body_offset"] for v in c["samples"].values()}))
                for c in result["candidates"] if c["encoding"] == "f64:little:m:signed"])
PY
uv run python P04DimensionSearch.py
```

Observed output:

```
width [('f64:little:m:signed', [2636]), ('f64:little:m:signed', [12839]), ('f64:little:m:signed', [13203]), ('f64:little:m:signed', [13527]), ('f64:little:m:signed', [14556]), ('f64:little:m:signed', [15968]), ('f64:little:m:signed', [15992]), ('f64:little:m:signed', [16138]), ('f64:little:m:signed', [16162])]
height [('f64:little:m:signed', [2644]), ('f64:little:m:signed', [13211]), ('f64:little:m:signed', [13373]), ('f64:little:m:signed', [14712]), ('f64:little:m:signed', [17419]), ('f64:little:m:signed', [17443]), ('f64:little:m:signed', [17581]), ('f64:little:m:signed', [17605]), ('f64:little:m:signed', [19591])]
```
14556 and 14712 are the `RectangleSketch` dimension record offsets the reader
also reports for those files.

The P04 holdout used the reader's `native_offset` on every capture:

```shell
cat > P04DimensionHoldout.py <<'PY'
import json, struct
from pathlib import Path
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import NativePartModel

base = Path("re/automation/PairedCaptures/P04/solidworks-c1986308375a")
expected = {"baseline-a": (40, 20), "baseline-b": (40, 20), "edit-width_mm-44": (44, 20),
            "edit-height_mm-24": (40, 24), "edit-depth_mm-12": (40, 20), "edit-cut_width_mm-12": (40, 20),
            "edit-cut_height_mm-10": (40, 20), "edit-cut_depth_mm-5": (40, 20), "plane-yz": (40, 20),
            "termination-through-all": (40, 20), "units-inch": (40, 20)}
passed = 0
for name, (width_mm, height_mm) in expected.items():
    raw = (base / f"P04-solidworks-{name}.SLDPRT").read_bytes()
    archive = SldprtArchive.from_bytes(raw, name)
    body = archive.require("Contents/Config-0")
    dims = {d.name: d for f in NativePartModel(archive, None).features for d in f.dimensions}
    got = tuple(round(struct.unpack_from("<d", body, dims[k].native_offset)[0] * 1000, 3)
                for k in ("width_mm", "height_mm"))
    passed += got == (width_mm, height_mm)
    print(name, got, (width_mm, height_mm))
print(f"{passed}/{len(expected)} P04 captures verified")
PY
uv run python P04DimensionHoldout.py
```

Observed: `11/11 P04 captures verified`.
