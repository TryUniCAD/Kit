# SOLIDWORKS sketch stream inventory

Inventory of the archive streams and native records that carry sketch data in the committed
`.SLDPRT` files under `re/solidworks/FeatureLadderRecovery/`, `re/NativePlacement2026/Cases/`
and `re/FeatureLadders2026/Cases/`.

This is item 2 of the repeat discovery loop in the SOLIDWORKS reader and writer plan delivered on
PR #296: inventory the affected streams, then separate authored dimensions and references from
derived geometry, caches and archive bookkeeping. It records what the existing readers under
`src/convert/adapters/solidworks/` already decode; no reader was changed.

## Scope and provenance

- Revision: `1619f00bf532caad262d1557bd69281179e5c497` (default branch).
- Corpus: 217 committed `.SLDPRT` files that all contain one sketch.
  - `re/solidworks/FeatureLadderRecovery/`: 113 files (37 case folders `solidworks-059` to
    `solidworks-095`, three files each, plus `FailedAttempt/solidworks-068`, two files).
  - `re/NativePlacement2026/Cases/`: 71 files (`solidworks-000` to `solidworks-023`;
    `solidworks-020` has no `control-after.SLDPRT`).
  - `re/FeatureLadders2026/Cases/`: 33 files (`solidworks-048` to `solidworks-058`, three each).
- Every scoped file carries the same sketch shape: one rectangular profile of four lines plus a
  construction point, two horizontal and two vertical axis relations, four coincident relations,
  and no driving sketch dimension.
- The carried sketch is a rectangle; no scoped file contains a circle, arc, ellipse, spline or
  point-to-point dimension.

## Commands run

Run from the repository root with the checkout's own CLI (`.venv/bin/kit`). `AGENTS.md` documents
`uv tool install --python 3.14 .`; this checkout exposes the same entry point at `.venv/bin/kit`.

```sh
# enumerate the scoped corpus
find re/solidworks/FeatureLadderRecovery re/NativePlacement2026/Cases re/FeatureLadders2026/Cases \
  -name '*.SLDPRT' | sort > /tmp/verify/files.txt
wc -l < /tmp/verify/files.txt   # 217

# public decoded document (sketch provenance, entities, constraints, parameters)
.venv/bin/kit decode re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT \
  --layer neutral --partial -o /tmp/n058.json --overwrite

# container member inventory (which streams exist)
.venv/bin/kit decode re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT \
  --layer container -o /tmp/c058.json --overwrite

# one decompressed stream as base64, to locate the sketch markup
.venv/bin/kit decode re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT \
  --layer container --stream Contents/Config-0-ResolvedFeatures -o /tmp/rf.json --overwrite
.venv/bin/kit decode re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT \
  --layer container --stream swXmlContents/KeyWords -o /tmp/kw.json --overwrite

# registered readers and writers
.venv/bin/kit formats
```

Verbatim outputs from the key checks:

```text
$ .venv/bin/kit formats
format	read	write	extensions	write_extensions
"catia.v5"	true	true	[".catpart", ".catproduct"]	[".catpart", ".catproduct"]
"freecad.fcstd"	true	true	[".FCStd"]	[".FCStd"]
"fusion.f3d"	true	true	[".f3d"]	[".f3d"]
"interchange.json"	true	true	[".json"]	[".json"]
"solidworks.sldprt"	true	true	[".sldprt", ".sldasm"]	[".sldprt"]

$ .venv/bin/kit decode re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT --layer native
{"error": "ValueError", "message": "Native decoding currently supports Fusion F3D only"}
```

The same `decode` calls were repeated for all 217 files, and the emitted JSON was aggregated with
`python3 -c`:

```text
files: 217
sketches per file: {1: 217}
sketches with driving parameters: 0
entity kinds: {'line': 868, 'point': 217, 'native': 217}
constraint kinds: {'horizontal': 434, 'vertical': 434, 'coincident': 868}
Contents/Config-0-ResolvedFeatures sketch-constraint: 217
Contents/Config-0-ResolvedFeatures sketch-native-marker: 217
Contents/Config-0-ResolvedFeatures sketch-profile-line: 217
Contents/Config-0-ResolvedFeatures sketch-record: 217
```

Raw marker counts across extracted streams of `re/FeatureLadders2026/Cases/solidworks-058/variation.SLDPRT`:

```text
Contents/Config-0                      len= 25508 sgSketch=0 sgLineHandle=0 sgPointHandle=0 sgArcHandle=0 sgPntPnt=0 DimensionTag=0
Contents/Config-0-ResolvedFeatures     len= 11369 sgSketch=1 sgLineHandle=1 sgPointHandle=1 sgArcHandle=0 sgPntPnt=0 DimensionTag=0
Contents/Config-0-Partition            len=  3784 sgSketch=0 sgLineHandle=0 sgPointHandle=0 sgArcHandle=0 sgPntPnt=0 DimensionTag=0
Contents/DisplayLists                  len= 12572 sgSketch=0 sgLineHandle=0 sgPointHandle=0 sgArcHandle=0 sgPntPnt=0 DimensionTag=0
```

## Archive streams that carry sketch data

| Stream | What it holds | Sample files | Decoded by the reader? |
| ------ | ------------- | ------------ | ---------------------- |
| `Contents/Config-0-ResolvedFeatures` | The resolved feature graph. The inline `sgSketch` markup lives here: sketch points, lines, circles/arcs, dimensions and relations, their display records, the closed region and chain, and external-entity proxies. Confirmed by the public decode provenance (`sketch-record`, `sketch-profile-line`, `sketch-native-marker`, `sketch-constraint`) and by finding `sgSketch`/`sgLineHandle`/`sgPointHandle` in this stream only. | all 217 | Yes - the public neutral reader and the `Sketch/` typed readers (`Resolved/ProfileSketch.py`, `Sketch/InlineSketch.py`) both read it |
| `Contents/Config-0` | Configuration object/class map and the region, annotation and equation side tables that reference sketch objects by index (`Config/OrdinaryMap.py`, `Config/Regions.py`, `Config/CutEquation.py`, `Config/CutEqRefs.py`). No sketch class markup is present in the raw stream. | all 217 | Yes - as the resolving map; sketch geometry is not stored here |
| `swXmlContents/KeyWords` | XML feature history. Carries the feature `Dimension` elements, for example `<Dimension Name="D1">10</Dimension>` under `Boss-Extrude1`. The only dimension in every scoped file is the boss depth, not a sketch dimension. | all 217 | Yes - parsed by `Core/Native.py` `ParseKeywords` |
| `swXmlContents/Features` | OPC model/configuration list (`swModelList`, `swConfigurationList`). No sketch data. | all 217 | No - constant only; not read by the part reader |
| `Contents/DisplayLists` | Assembly tessellation display lists. No sketch markup in these parts. | all 217 | Assemblies only (`Assembly/Assembly.py`) |
| `Contents/Config-0-Partition` | Parasolid/body partition. No sketch data. | all 217 | Separate body path |

## Native records inside `Contents/Config-0-ResolvedFeatures`

Record names are the native class names reported by the decode (`metadata.native_class_names`).
`Sketch/`, `Resolved/`, `Config/` and `Core/` reader modules are the decode owners.

| Record | What it holds | Sample files | Decoded by the reader? |
| ------ | ------------- | ------------ | ---------------------- |
| `sgSketch` | Sketch header, counts and owning feature (`Sketch/InlineSketch.py`, `Sketch/Cursor.py`) | all 217 | Yes - one `sldprt:sketch:*` record per file |
| `sgPointHandle` | Sketch point: slot identity, coordinates, relation tally (`Sketch/Members.py`) | all 217 | Yes - one point entity per file |
| `sgLineHandle` | Sketch line: member identity, endpoint slots, flags (`Sketch/Members.py`) | all 217 | Yes - four line entities per file |
| `moLengthParameter_c` | Named length scalar owned by a dimension (`Sketch/Cursor.py` `ReadLengthMut`) | all 217 | Yes |
| `moNodeName_c` | Saved node name (`Sketch/Cursor.py`, `Core/TypedResolved/ReadNativeName.py`) | all 217 | Yes |
| `moPointBackedUpData_c` | Backed-up point payload (`Sketch/Cursor.py`) | all 217 | Yes |
| `sgExtEnt_c`, `moSketchExtRef_w`, `moCompSketchEntHandle_c` | External-entity reference proxy (`Sketch/Cursor.py` `ReadProxyMut`) | all 217 | Partial - the referenced feature/entity identity is decoded, but the proxy line entity is surfaced as raw `native` geometry bytes, not as line geometry |
| `moSketchRegion_c` | Closed region over the sketch perimeter (`Sketch/Regions.py`) | all 217 | Yes |
| `moSketchChain_c` | Profile chain (`Resolved/ContourChain.py`) | all 217 | Yes |
| `moDisplayDistanceDim_c`, `moFavoriteHandle_c` | Linear dimension display and its tail (`Sketch/Displays.py`) | all 217 | Yes |
| `moFeatureDimHandle_c`, `ParallelPlaneDistanceDim_c` | Dimension handle route and the boss depth dimension (`Resolved/BossDepth.py`) | all 217 | Yes - feature depth, not the sketch |

## Sketch records unexercised by the scoped corpus

These record types appear in the readers but in no scoped file, so their decode is unverified here.
Evidence: `metadata.native_class_names` for all 217 files, and a raw byte search of
`Contents/Config-0-ResolvedFeatures`, contain none of them.

| Record | What it would hold | Reader that expects it |
| ------ | ------------------ | ---------------------- |
| `sgArcHandle` | Full circle/arc member with seam and centre slots | `Sketch/CircularMembers.py` `ReadCircle`, `Sketch/Cursor.py` `ReadArcSlotMut` |
| `sgEntHandle` | Inactive second radial operand placeholder | `Sketch/Cursor.py` `ReadArcSlotMut` |
| `sgCircleDim` | Diameter dimension bound to its arc | `Sketch/CircularMembers.py` `ReadDiameter` |
| `sgPntPntDist`, `sgPntPntHorDist`, `sgPntPntVertDist` | Point-to-point distance dimensions | `Sketch/Cursor.py` `ReadDistanceMut`, `Sketch/Relations.py` `ReadDims` |
| `moDisplayRadialDim_c`, `moSkDimHandleRadial_c` | Radial/diameter display and its dimension handle | `Sketch/CircularDisplay.py` `ReadRadialLink` |

The scoped corpus also carries no circle, arc, ellipse, spline or parabola geometry, so the generic
marker geometry path (`Core/Adapter.py` `MarkerCurved`) is not exercised by these files either.

## Limitations

- `kit decode --layer native` refuses SOLIDWORKS input: it reports
  `{"error": "ValueError", "message": "Native decoding currently supports Fusion F3D only"}`.
  SOLIDWORKS sketch inspection therefore uses the `container` and `neutral` layers.
- The public neutral reader reports the sketch through its provenance spans; the lower-level
  `Sketch/` readers are not directly reachable through `kit decode`, so their record coverage was
  read from the source modules named above.
- This inventory records stream and record ownership only. It is not acceptance evidence and does
  not qualify any writer.
