# FCStd to SOLIDWORKS corpus coverage

Status: **no SOLIDWORKS output**. Kit reads SOLIDWORKS files and writes none. FCStd to SLDPRT or
SLDASM conversion raises `AdapterNotFoundError` for all 165 repository FCStd files. The writer
measured below re-emitted one recorded vendor stream per family, so it was removed from production.
See `Documentation/Changes/Solidworks/SolidworksRecordedPayloadRemoval.md`.

The figures below are the last audit of that removed writer. They record which source histories it
accepted and which oracle checks it passed. They are research evidence for a generative serializer,
not current capability.

## Last audit of the removed writer

The audit tool, `tools/audit/AuditFcstdSolidworks.py`, was deleted with the writer. Its 2026-08-11
recursive result was:

| measurement              | count |
| ------------------------ | ----: |
| FCStd files              |   165 |
| parser or writer errors  |     0 |
| vendor-loadable contract |    44 |
| application-usable       |    44 |
| near-lossless            |    44 |
| vendor-only              |     0 |
| unsupported              |   121 |

121 sources were unsupported. Each accepted part went through the public `write_document` path,
and the resulting compound file was read back with `SldprtArchive`. The increase from 40 to 44 was
the exact six-line polyline pad, full stepped-pin revolution,
90-degree stepped-pin revolution, and rectangular boss/two-cut chain ending in a circle. This was a
production-path structural proof, not a claim that all 44 files were individually opened
in SOLIDWORKS. Vendor-application oracle measurements remain separately recorded in
`archive/Multistream.md`.

## Families the removed writer accepted

Each accepted source history was built from one recorded typed program, with editable sketches,
dimensions, feature ordering, and body-producing operations:

- rectangular and circular pad, including blind depth, reverse direction, mid-plane, and principal
  sketch-plane variants where the recovered grammar supports them;
- exact standalone `Part::Box` solids lowered to an origin-based rectangle with independently
  editable length and width dimensions plus an editable blind-boss height;
- exact standalone origin-aligned `Part::Cylinder` solids lowered to a diameter-driven circle with
  an independently editable blind-boss height;
- blind and through-all pockets, including two- and three-pocket chains;
- the exact three-stage rectangular boss, rectangular pocket, and circular pocket chain;
- pad followed by a second pad;
- full rectangular revolution, exact full and 90-degree stepped-pin revolutions, and pad followed
  by a groove;
- the exact connected six-line Front-plane blind pad;
- pad followed by fillet, chamfer, or shell;
- pad followed by linear pattern; and
- pad followed by circular pattern, including occurrence count, total angle, and reverse direction.

Every byte of the load-critical reference streams had a typed owner for these families:

| stream family                      | reference bytes | opaque bytes |
| ---------------------------------- | --------------: | -----------: |
| `Contents/Definition`              |           3,618 |            0 |
| `Contents/CMgr`                    |           1,957 |            0 |
| `Contents/Config-0`                |   25,158–25,214 |            0 |
| assembly core field program        |          38,198 |            0 |
| family-specific `ResolvedFeatures` |   10,556–27,092 |            0 |

Those figures describe the removed reference programs. Typed ownership did not make them
generated, and it does not imply support for an unrecovered source feature family.

## Controlled feature campaign

Of the 25 focused FCStd inputs under `.rescratch/sw/fcstd`, 22 reached the native vendor-loadable and
application-usable path. These three failed closed:

- `.rescratch/sw/fcstd/kit_boss_disjoint_revolve.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_front.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_top_midplane.FCStd`.

They require one or more unrecovered semantics: a Front-plane stepped pin, a mid-plane revolution,
or a disjoint pad-plus-revolution body history.

## Unsupported families in the full corpus

The audit recorded each type at most once per unsupported document. `native`, `reference`,
`extrusion`, and `fillet` are Kit timeline kinds used when a source object has no more specific
FreeCAD type identifier.

| source or timeline type      | documents |
| ---------------------------- | --------: |
| `App::FeaturePython`         |         3 |
| `App::GeometryPython`        |         2 |
| `Part::Box`                  |         9 |
| `Part::Compound`             |         1 |
| `Part::Cut`                  |         7 |
| `Part::Cylinder`             |         3 |
| `Part::Extrusion`            |         2 |
| `Part::Feature`              |         5 |
| `Part::FeaturePython`        |        11 |
| `Part::Line`                 |         1 |
| `Part::Mirroring`            |         2 |
| `Part::MultiCommon`          |         1 |
| `Part::MultiFuse`            |         4 |
| `Part::Offset2D`             |         1 |
| `Part::Part2DObjectPython`   |         6 |
| `Part::Plane`                |         1 |
| `Part::Sphere`               |         1 |
| `PartDesign::AdditiveBox`    |         1 |
| `PartDesign::AdditiveSphere` |         1 |
| `PartDesign::LinearPattern`  |         2 |
| `PartDesign::Pad`            |        16 |
| `PartDesign::Plane`          |         2 |
| `PartDesign::Pocket`         |         9 |
| `PartDesign::PolarPattern`   |         2 |
| `PartDesign::Revolution`     |        20 |
| `Path::FeaturePython`        |         4 |
| `extrusion`                  |        42 |
| `fillet`                     |        21 |
| `native`                     |        54 |
| `reference`                  |        54 |

`PartDesign::Pad`, `Pocket`, `Revolution`, `LinearPattern`, and `PolarPattern` in this table are
outside the exact profile, plane, termination, dependency, or operation sequences listed in the
recovered section; their type name alone is not sufficient for acceptance. The three
`Part::Cylinder` rows are likewise cylinders embedded in unrecovered multi-object histories, not
standalone primitives satisfying the exact cylinder gate.

## Assembly corpus result

All five FCStd documents detected as assemblies failed the portable native SLDASM contract:

- `.rescratch/out.FCStd`;
- `.rescratch/freecad/FreeCAD_1.1.3-Windows-x86_64-py311/data/examples/AssemblyExample.FCStd`;
- `re/solidworks/examples/Random/V8_engine.FCStd`;
- `re/solidworks/examples/Random/V8_engine/Conrod_2.FCStd`; and
- `re/solidworks/examples/Random/V8_engine/Piston_2.FCStd`.

The removed assembly writer had a typed zero-opaque core, which was itself a recorded payload, and
these inputs required unsupported component feature histories or assembly semantics.

## Completion boundary

The stream programs used by the accepted families had no opaque bytes, but each one was a recorded
payload: a typed re-encoding of one saved stream, re-emitted at its saved length with selected fields
overridden. They held 185,090 recorded field operations and were removed. A generative serializer is
the remaining SOLIDWORKS writer work, starting with a profile whose stream length and topology vary
with the input. Feature-semantic work also remains across the corpus, especially arbitrary sketch
profiles, multi-object primitive and Boolean Part histories, broader revolution modes, non-campaign
pattern histories, and the five real assemblies.

## Native box oracle

The removed standalone box program was not inferred from its internal decoder alone. Its output
was opened and rebuilt in SOLIDWORKS 2025 between healthy controls with zero load errors or
warnings, one solid body, `Sketch1`, `Boss-Extrude1`, volume 1,000 mm³, surface area 600 mm², and
centre of mass `(5, 5, 5)` mm. Independent live parameter drives on that generated file produced:

| parameter          | value | volume mm³ | centre of mass mm |
| ------------------ | ----: | ---------: | ----------------- |
| `D1@Sketch1`       | 20 mm |      2,000 | `(10, 5, 5)`      |
| `D2@Sketch1`       | 15 mm |      1,500 | `(5, 7.5, 5)`     |
| `D1@Boss-Extrude1` | 12 mm |      1,200 | `(5, 5, 6)`       |

The box-specific 14,855-byte `ResolvedFeatures` program contained 3,522 typed operations, and its
25,158-byte `Config-0` program contained 4,345 typed operations. Both tiled their reference streams
exactly with zero opaque spans. This shows SOLIDWORKS accepted the recorded program, not that the
program was generated.

## Native cylinder oracle

The removed standalone cylinder path used a separate, diameter-dimensioned circle program. Its
12,514-byte `ResolvedFeatures` stream contained 338 objects, 49 class definitions,
2,873 typed operations, 538 serializer owners, zero missing fields, and zero opaque spans.
The matching 25,158-byte `Config-0` stream reused the 4,345-operation field program and
specialized 29 typed fields for the circle's identities, bounds, cache metadata, radius, and depth.

A generated 5 mm radius by 10 mm high cylinder opened and rebuilt in SOLIDWORKS 2025 with zero load
errors or warnings, one body, `Sketch1`, `Boss-Extrude1`, volume 785.3981633974485 mm³, surface area
471.238898038469 mm², and centre of mass `(0, 0, 5)` mm. Independent live edits produced:

| parameter          | value |         volume mm³ |  surface area mm² | centre of mass mm |
| ------------------ | ----: | -----------------: | ----------------: | ----------------- |
| `D1@Sketch1`       | 16 mm | 2,010.619298297468 | 904.7786842338604 | `(0, 0, 5)`       |
| `D1@Boss-Extrude1` | 12 mm |   942.477796076938 | 534.0707511102650 | `(0, 0, 6)`       |

An independently generated 8 mm radius by 12 mm high FCStd also opened with one body, volume
2,412.74315795696 mm³, surface area 1,005.3096491487335 mm², and centre of mass `(0, 0, 6)` mm.
An off-origin generic circle was observed rebuilding at the origin; that case failed closed
and was not reported as lossless. A reverse-direction oracle proved that the high feature flag alone
is insufficient, then complete field tracing recovered the entire coupled history. After saved
path and document-name metadata are canonicalized, both reverse streams retained the normal 12,514-
and 25,158-byte widths with zero opaque spans. The generated negative-Z body opened and
rebuilt without warnings, and independent diameter and depth edits remained parametric. The removed
writer accepted strict origin-centred Front-plane reversed blind circles and rejected off-origin and
non-front variants.

## Feature family x SOLIDWORKS version coverage

The SOLIDWORKS reader and writer delivery plan (PR #296) asks each feature and file version to be
recorded in a coverage table, tracking reading and writing separately. This section covers the 68
curated families in
[`PlannerCatalog/Sources/FeaturePlan.json`](PlannerCatalog/Sources/FeaturePlan.json) against the
`.SLDPRT` files actually committed to the repository.

`read` means the reader has a typed decode for the family: it maps one of the family's native records
to a concrete neutral `FeatureKind` in
[`Core/FeatureKindByNative.py`](../../src/convert/adapters/solidworks/Core/FeatureKindByNative.py),
or reads it through the documented document-state codecs (definition, headers, configuration,
presentation). `tree only` means the reader retains the node without typed feature semantics (its
native classes map to `FeatureKind.NATIVE`). It is **typed decode, not native acceptance**; see the
[SOLIDWORKS adapter reference](../../Documentation/Reference/Adapters/Solidworks.md).

`write` means Kit emits the family from format rules. Only the
[bounded part writer](../../Documentation/Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md)
exists: one Front-plane line loop and one forward blind boss, which is the `extrude` family at
version 19000. Every other family is `no`, and the matched `extrude` output is a bounded subset, not
the whole family. The earlier recorded-payload writer that reached more families was removed; it was
not generative.

### Method

All numbers below were produced by the following commands at commit `1619f00b`. The count is a shell
command; the per-family sample counts and version counts are one Python census that opens every
committed part, reads the `swXmlContents/KeyWords` feature `Type` values, and reads the container's
`_MO_VERSION_<n>` storage (falling back to `swVersion` in `swXmlContents/Features`). Run it from the
repository root with the project interpreter.

```sh
git ls-files '*.SLDPRT' | wc -l
```

```python
import collections, re, subprocess
from convert.adapters.solidworks.Container.Container import SldprtArchive

CROSS = {
    "boss-extrude": "extrude", "cut-extrude": "extrude", "extrusion": "extrude",
    "revolve": "revolve", "cut-revolve": "revolve",
    "sweep": "sweep", "cut-sweep": "sweep",
    "loft": "loft", "cut-loft": "loft",
    "fillet": "fillet", "varfillet": "fillet", "chamfer": "chamfer",
    "shell": "prismatic", "mirror": "bodytransform",
    "cirpattern": "pattern", "lpattern": "pattern",
    "holewizard": "holes", "advancedhole": "holes", "hole thread": "holes",
    "3dsketch": "sketch", "sketch": "sketch",
    "axis": "reference", "plane": "planes", "imported": "interchange",
    "sheet-metal master": "sheetbase", "body-delete/keep": "bodyboolean",
    "helix/spiral": "curves",
}

files = [f for f in subprocess.check_output(
    ["git", "ls-files", "-z", "*.SLDPRT"]).decode().split("\0") if f]
samples = collections.defaultdict(set)
versions = collections.defaultdict(collections.Counter)
opened = 0
for path in files:
    archive = SldprtArchive.OpenAction(path)
    opened += 1
    found = [int(m.group(1)) for name in (r.name for r in archive.records)
             for m in [re.match(r"_MO_VERSION_([0-9]+)/", name)] if m]
    if not found:
        head = archive.GetAction("swXmlContents/Features") or b""
        m = re.search(rb'swVersion="([0-9]+)"', head)
        found = [int(m.group(1))] if m else [0]
    version = max(found)
    keywords = (archive.GetAction("swXmlContents/KeyWords") or b"").decode("utf-8", "replace")
    families = set()
    for raw in re.findall(r'Type="([^"]+)"', keywords):
        name = raw.strip().lower()
        if name.startswith("croquis"):
            families.add("sketch")
        elif name in CROSS:
            families.add(CROSS[name])
    for family in families:
        samples[family].add(path)
        versions[family][version] += 1

print("committed", len(files), "opened", opened)
for family in sorted(samples, key=lambda k: -len(samples[k])):
    print(family, len(samples[family]), dict(sorted(versions[family].items())))
```

Result: **322** committed `.SLDPRT` files, **322** opened. The version census is
`19000: 264`, `14000: 57`, `18000: 1`. Version keys are container document-version generations:
`19000` is SOLIDWORKS 2026
([archive compatibility](records/Solidworks2026ArchiveCompatibility.md)), `18000` is SOLIDWORKS 2025
([revolve authoring](features/RevolveAuthoredOneEightZeroZeroZero.md)), and `14000` is the older
real-world corpus ([GroundTruth](GroundTruth.md)).

### Table

Sample counts are the files matching each family; version counts are `generation x files`. Families
with no footprint in the committed census show `0`. Sketch sub-families (lines, conics, slots,
splines, relations, dimensions) are not separately tagged in `KeyWords`, so they show `0` even
where a matched sketch is present.

| family                          | wave          | read      | write        | samples | versions                          |
| ------------------------------- | ------------- | --------- | ------------ | ------: | --------------------------------- |
| document foundations            | foundation    | yes       | no           |       0 | -                                 |
| selection and topology          | foundation    | tree only | no           |       0 | -                                 |
| history and execution state     | foundation    | yes       | no           |       0 | -                                 |
| reference geometry              | foundation    | yes       | no           |      11 | 14000 x11                         |
| plane definitions               | foundation    | yes       | no           |     320 | 14000 x57, 18000 x1, 19000 x262   |
| sketch ownership and support    | alpha         | yes       | no           |      32 | 14000 x32                         |
| sketch linear geometry          | alpha         | yes       | no           |       0 | -                                 |
| sketch conics                   | alpha         | yes       | no           |       0 | -                                 |
| sketch slots                    | solid         | yes       | no           |       0 | -                                 |
| sketch splines and curves       | surface       | yes       | no           |       0 | -                                 |
| sketch constraints              | alpha         | yes       | no           |       0 | -                                 |
| sketch dimensions               | alpha         | yes       | no           |       0 | -                                 |
| sketch transformations and tools | solid         | tree only | no           |       0 | -                                 |
| sketch patterns and blocks      | solid         | yes       | no           |       0 | -                                 |
| extrusion family                | alpha         | yes       | yes (bounded) |    299 | 14000 x54, 18000 x1, 19000 x244   |
| revolution family               | solid         | yes       | no           |      24 | 14000 x17, 19000 x7               |
| sweep family                    | solid         | yes       | no           |       8 | 14000 x8                          |
| loft family                     | surface       | yes       | no           |      10 | 14000 x10                         |
| boundary family                 | surface       | yes       | no           |       0 | -                                 |
| holes and threads               | solid         | yes       | no           |       7 | 14000 x7                          |
| fillet family                   | alpha         | yes       | no           |      33 | 14000 x32, 18000 x1               |
| chamfer family                  | solid         | yes       | no           |      30 | 14000 x30                         |
| rib shell and draft             | solid         | yes       | no           |       4 | 14000 x4                          |
| multibody operations            | solid         | yes       | no           |       3 | 14000 x3                          |
| body transforms and derivation  | solid         | yes       | no           |      16 | 14000 x16                         |
| direct face editing             | solid         | yes       | no           |       0 | -                                 |
| shape deformation               | surface       | yes       | no           |       0 | -                                 |
| part feature and body patterns  | solid         | yes       | no           |      15 | 14000 x15                         |
| surface creation                | surface       | yes       | no           |       0 | -                                 |
| surface modification            | surface       | yes       | no           |       0 | -                                 |
| surface to solid operations     | surface       | yes       | no           |       0 | -                                 |
| reference curves                | surface       | yes       | no           |       4 | 14000 x4                          |
| sheet metal foundations         | manufacturing | tree only | no           |       3 | 14000 x2, 19000 x1                |
| sheet metal flanges and bends   | manufacturing | tree only | no           |       0 | -                                 |
| sheet metal corners and forming | manufacturing | tree only | no           |       0 | -                                 |
| sheet metal fold state          | manufacturing | tree only | no           |       0 | -                                 |
| weldment framework              | manufacturing | tree only | no           |       0 | -                                 |
| structure system                | manufacturing | tree only | no           |       0 | -                                 |
| weldment cut lists              | manufacturing | tree only | no           |       0 | -                                 |
| mold tooling                    | manufacturing | tree only | no           |       0 | -                                 |
| mesh and scan geometry          | extended      | no        | no           |       0 | -                                 |
| scan and recognition tools      | extended      | no        | no           |       0 | -                                 |
| assembly hierarchy              | assembly      | yes       | no           |       0 | -                                 |
| assembly context and references | assembly      | yes       | no           |       0 | -                                 |
| standard mates                  | assembly      | tree only | no           |       0 | -                                 |
| advanced mates                  | assembly      | tree only | no           |       0 | -                                 |
| mechanical mates                | assembly      | tree only | no           |       0 | -                                 |
| assembly repetition             | assembly      | tree only | no           |       0 | -                                 |
| assembly features and evaluation | assembly     | tree only | no           |       0 | -                                 |
| assembly representations        | assembly      | tree only | no           |       0 | -                                 |
| motion studies                  | extended      | tree only | no           |       0 | -                                 |
| configurations and equations    | foundation    | yes       | no           |       0 | -                                 |
| materials and document data     | foundation    | yes       | no           |       0 | -                                 |
| presentation state              | strict        | yes       | no           |       0 | -                                 |
| drawing document and sheets     | drawing       | no        | no           |       0 | -                                 |
| drawing base views              | drawing       | no        | no           |       0 | -                                 |
| drawing derived views           | drawing       | no        | no           |       0 | -                                 |
| drawing view display            | drawing       | no        | no           |       0 | -                                 |
| dimensions and annotations      | drawing       | no        | no           |       0 | -                                 |
| manufacturing symbols           | drawing       | no        | no           |       0 | -                                 |
| drawing and model tables        | drawing       | no        | no           |       0 | -                                 |
| model based definition          | extended      | no        | no           |       0 | -                                 |
| routing                         | extended      | no        | no           |       0 | -                                 |
| simulation studies and inputs   | extended      | tree only | no           |       0 | -                                 |
| extended product and add in boundaries | extended | no     | no           |       0 | -                                 |
| import export and interoperability | extended   | yes       | no           |       2 | 19000 x2                          |
| custom and extensible features  | strict        | tree only | no           |       0 | -                                 |
| strict fidelity beyond editable alpha | strict  | no        | no           |       0 | -                                 |

### Headline gaps

- **17 of 68 families** have any committed sample. Writing covers **one** family, and only as a
  bounded single blind boss.
- **Reading is broad, writing is not.** 36 families have a typed decode; 19 are tree-only (sheet
  metal, weldments, structure, mates, motion, simulation, custom features) and 13 have no reader
  path at all (all seven drawing families, MBD, routing, mesh and scan, and the add-in boundaries).
- **Version skew.** 264 of 322 samples are the 19000 (2026) generation, and 57 are the older 14000
  corpus. The rich multi-feature families (fillet, chamfer, revolve, loft, sweep, pattern) exist in
  the committed corpus almost only at 14000, so write acceptance at 19000 is measured only against
  the bounded boss.
- **Under-tested families.** The 51 families with `0` samples have no committed `.SLDPRT` at all;
  these need authoring before any read, write, reopen, rebuild or held-out claim can be made.
