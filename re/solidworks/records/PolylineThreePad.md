# Three-line blind-boss native research

## Scope and boundary

This record covers a closed, simple three-line sketch on the Front Plane followed by one forward blind boss extrusion. Native identities are sketch 26/`Sketch1`, pad 32/`Boss-Extrude1`, plane 2, and end codes `(0,0)`. There are no sketch dimensions, authored solver relations, construction entities, fixed entities, or additional loops in the controlled inputs.

The bounded three-line blind-boss family is now implemented and vendor-accepted as detailed below. Other sketch families, histories, assemblies, drawings, and broad B-rep coverage remain outside that claim. The captured source files are research inputs only; they are never read by production or embedded as donor streams.

## Vendor-authored inputs

SOLIDWORKS 34.5.2 created every source from an explicit ordered coordinate list through `re/tooling/harness/AuthorTriangles.vbs`. Each has three sketch segments, a native `Sketch1`, a native `Boss-Extrude1`, one solid body, and a successful rebuild.

| Input         | Vertices, millimetres        | Depth, mm | Area, mm² | Volume, mm³ |   Surface area, mm² |
| ------------- | ---------------------------- | --------: | --------: | ----------: | ------------------: |
| `tri3a`       | `(0,0), (42,0), (12,31)`     |         9 |       651 |       5,859 |  2,367.427645476918 |
| `tri3b`       | `(-7,-11), (39,-4), (17,38)` |        17 |     1,043 |      17,731 |  4,610.577015505639 |
| `tri3deep`    | `(0,0), (42,0), (12,31)`     |        21 |       651 |      13,671 | 3,787.9978394461414 |
| `tri3reverse` | `(12,31), (42,0), (0,0)`     |         9 |       651 |       5,859 |  2,367.427645476918 |
| `tri3tie`     | `(0,0), (36,0), (36,24)`     |        11 |       432 |       4,752 | 1,999.9327683612466 |

The areas are independently `abs(shoelace)/2`. Each measured volume is `area × depth`. Each measured surface area is `2 × area + perimeter × depth`. This is vendor evidence for the authored sources, not acceptance of a generated native file.

The author harness takes the host research root explicitly. It does not delete prior files; an existing target is reported as `PREEXISTING_SKIP`. The separate seeded branch permits up to 512 monotone-angle, nonzero-radius triangles with independent depths. A future corpus run still needs independent vendor acceptance, not just successful source creation.

## Native stream identity

All five source documents contain 40 streams and the 2026 envelope:

- `_MO_VERSION_19000/Biography` and `_MO_VERSION_19000/History`;
- `Contents/Definition`: 3,816 bytes;
- `Contents/CMgr`: 2,159 bytes;
- `Contents/Config-0`: 25,476 bytes;
- `Contents/Config-0-ResolvedFeatures`: 10,601 bytes.

The resolved-feature stream begins `6d 00 00 00 13 00 ff ff`, so the initial object-map continuation is `0x6d` (109). The five-line family has 11,205 bytes, so count substitution and direct reuse of its offsets are invalid.

The principal triangle's same-profile depth variant changes only requested depth. The reversed/source-start-shifted variant tests closure references independently of geometry. The right-angle case has two rightmost vertices; it prevents importing the five-line unique-rightmost attachment rule without evidence.

## Capture status

The attached object trace completed with `ORACLE_EXIT=0` and 300 reads of each object/class kind. Segmentation tiled all 10,601 bytes with 300 objects, 40 class definitions, base map 109, and zero counter mismatches.

The correct primitive capture uses direct `cdb` attachment and stream-span filtering, not the failing wrapper/lazy-symbol path. It records 2,946 events, all against the 10,601-byte stream. The generated program has 2,518 operations over 495 serializer owners and zero uncovered bytes. Independent re-emission yields `5088c5c909bc432b12ee2f50f8aaa7934f3232e62ef30bb0a6d1563ac340ced0`.

The dynamic field map contains 51 values: six coordinates, four positive-depth fields at 9408/9480/9968/9992, two negative-depth fields at 9806/9830, eight bbox fields at 8201/8209/8217/8225 and 8423/8431/8439/8447, 24 display-plane fields, four attachment witnesses at 9440/9448 and 9464/9472, two transformed attachment witnesses at 9637 and 9653, and the scaled attachment at 9726.

`range * 1.1 / 2000` is the measured expansion order for range values and expanded z. The scaled attachment is `x / 5000`. These are not arbitrary reassociations of the assessed geometry-preserving formulas. The second sphere diameter is an eight-byte operation beginning at 8447, not 8451; replay overrides apply only at operation starts.

Triangle native serialization now passes the validated point-marker metre pairs directly to the six coordinate fields. The neutral reader's 12-decimal presentation values remain available for neutral display, but do not round high-precision source coordinates before native emission. Public coverage compares all six exact doubles and both nonbaseline diameters.

The attachment tie uses the first rightmost coordinate, verified by the two-rightmost right-angle control. It is not discovered through the five-line uniqueness heuristic.

## Accepted production path

`re/tooling/ProgramDecomposition/AddProgram.py` adds the three-line facade, registry, and typed methods without replacing unrelated owner catalogs or streams. Its `--program-root` destination is explicit rather than an implicit production-tree default. Complete verification now reports 45 programs, 77 streams, 215 catalogs, 2,461 owners, 3,995 methods, and 190,316 operations.

Fresh public neutral-document writes produce one three-line `Sketch1` and one forward `Boss-Extrude1`. Late-bound SOLIDWORKS 34.5.2 inspection confirms the native profile feature and extrusion, and `D1@Boss-Extrude1` remains live and editable. All four fresh files have zero load errors and warnings, one body, and a successful rebuild.

| Public input family          | Depth, mm | Volume, mm³ |           Area, mm² |
| ---------------------------- | --------: | ----------: | ------------------: |
| `(0,0), (42,0), (12,31)`     |         9 |       5,859 |  2,367.427645476918 |
| `(-7,-11), (39,-4), (17,38)` |        17 |      17,731 |  4,610.577015505639 |
| `(0,0), (42,0), (12,31)`     |        21 |      13,671 | 3,787.9978394461414 |
| `(0,0), (36,0), (36,24)`     |        11 |       4,752 | 1,999.9327683612466 |

Changing the shifted public part to 5 mm rebuilds to 5,215 mm³ and 2,828.5226516193 mm² before closing without saving. The measured values match `area × depth` and `2 × area + perimeter × depth`.

The capture digest is not expected to match arbitrary new documents' author metadata or all view-state floating-point values. Native open, feature-tree identity, body geometry, and live-edit acceptance are independently measured instead of using that digest as application acceptance.

## Seeded native corpus

`AuthorTriangles.vbs` authored 64 distinct source parts with seed 982711, six-decimal coordinates/dot-decimal text, and independent depths. Author inspection confirms native `Sketch1`/`ProfileFeature` with three segments and `Boss-Extrude1`/`Extrusion`, one body, and successful rebuild for every authored source.

The public-corpus builder recovers six-decimal neutral vertices from those research sources and exact depth from four matching binary positive-depth witnesses. `length_mm` is presentation text, not source precision. Ten-thousand-six-hundred-three-byte variants shift those witnesses by the stream-length delta. Reused public output is allowed only when all six coordinates and all four depth doubles match the requested neutral model.

`VerifyRandomOracle.py` then measures fresh public files in the compiled SOLIDWORKS 34.5.2 oracle against independently calculated volume, area, and centre of mass. Final result: `ORACLE_TOTAL=64 ORACLE_PASS=64`, with zero load errors and warnings, successful rebuild, and one body in every case. Depth spans 3.931416–49.774612 mm. Volume spans 7,886.94036988702–152,118.315621051 mm³. Case evidence is held in `.rescratch/triangle-research/random64/generated-exact/oracle-results.json`, never read by production.

The independent late-bound identity sweep also finishes `ORACLE_TOTAL=64 ORACLE_PASS=64`, with `OPEN_METHOD=OpenDoc`, three lines, `ProfileFeature`, `Extrusion`, one body, and successful rebuild on every output. Random case 19's live 17.995855→5 mm edit rebuilds to 7,533.64542964935 mm³ and 3,947.70779111985 mm² without saving, matching `area × depth` and `2 × area + perimeter × depth`.

The separate high-precision public control verifies 14,392.0569347259 mm³ and 4,171.2939338546 mm² at 13.375 mm, with centre `(16.5967040785597, 7.66251477736625, 6.6875)` mm. Its live 6.25 mm edit rebuilds to 6,725.26024987192 mm³ and 3,095.63966028405 mm² before closing without saving. Those values also match the analytic profile independently.

## Native source replay

`NativeProfile.native_coordinates_mm` carries the measured metre-pair values into neutral sketch geometry without the 12-decimal presentation rounding. Both semantic consistency checks use `Clean(round(..., 12))`, avoiding the false rejection at a 1e-12-mm coordinate that using `round` alone caused.

`RecoverTriDepth` replaces presentation-only depth only within the recovered 10,601/10,603 triangle layouts. It requires four identical positive values and two exactly negated values, validates the rounded label, and updates `StateData.NativeFeatures` plus the operation so `DimensionParam` can preserve the native scalar. There is no general stream-size offset rule or arbitrary history claim.

Fresh public open/read/write cycles accepted four native inputs in SOLIDWORKS:

| Input                                | Exact depth, mm |       Volume, mm³ |         Area, mm² |
| ------------------------------------ | --------------: | ----------------: | ----------------: |
| `tri3r010` with display 19.53        |       19.529617 | 74,669.2099156988 | 13,182.8305763142 |
| `tri3r019` with display 18           |       17.995855 | 27,114.8781546765 | 6,375.98230826179 |
| SOLIDWORKS-authored `tri3precise`    |          13.375 | 14,392.0569347259 |  4,171.2939338546 |
| SOLIDWORKS-authored `tri3nearorigin` |               9 | 5,858.99999999989 | 2,367.42764547688 |

Every result has zero load errors/warnings, one body, successful rebuild, correct centre of mass, and the exact source depth. The near-origin input uses 8e-13 mm for its first x coordinate and remains supported. The high-precision replay's 6.25 mm edit yields 6,725.26024987192 mm³ and 3,095.63966028405 mm² before closing without saving.

Closure extraction now uses exact endpoint equality rather than the previous 1e-12-mm tolerance. A self-authored 1e-13-mm gap is rejected through the public writer, so starts are never used as permission to invent a closed chain. Bound pattern counts remain numeric counts rather than being converted into millimetres. Three-line candidate selection also inspects every source parameter before `WriteDimensions` can filter it. Only native `D1` and recognized, non-expression FreeCAD pad properties are admitted; the depth must equal the extrusion definition in a supported unit, roles must be driving, and only one configuration with zero offset/draft settings is supported. Public writer cases reject `CustomCount` on both owners, `CustomLength` on the extrusion, an extrusion `FuzzyTolerance` of `-1 + 5e-11`, a custom `Label2`, an `Offset` of `5e-11` on both parameter and definition, a stale depth, an unsupported depth unit, a driven depth role, and a second configuration. The FreeCAD projection requires the exact complete property set with the measured `-1` tolerance and default labels, validating each value exactly, so merely naming a property as supported is insufficient. The recognized loss path raises `SldprtFormatError` from native encoding, so even the default carrier-permitting public write cannot silently substitute a carrier.

A family-shaped triangle whose binary depth is unsupported or contradictory now raises `SldprtFormatError` through native reading instead of retaining approximate display text. A typed resolved-stream witness mutation exercises this fail-closed path through a valid archive built with `BuildSldprt`. Rounded label metadata is edited through the untrusted-XML parser with its pre-XML prefix retained, then rebuilt with the container's own matched signatures rather than changing compressed archive bytes directly. The edited fixtures omit `Kit/Interchange` and `Kit/Native`; remote CI exposed that retaining those streams made public `open_document` return the embedded neutral model and bypass both native-depth assertions. The feature-only native read also uses `include_brep=False` because no Parasolid payload is present. The labelled 17.995855-mm fixture also opens successfully with one body and correct depth in SOLIDWORKS, but the resulting self-emulated freecad/proof rewrite still remains outside the accepted scope.

A separate self-emulated freecad/proof compatibility path remains outside this acceptance; it is not substituted for these independently authored native replay results. `AuthorTriangles.vbs /precise` supplies the last two source documents.

Transport-only failures and disagreements in harness parsing are not counted as model acceptance or rejection. The final corpus uses successful compiled `OpenDoc6` results only. `OracleRandomTriangles.vbs` performs an independent late-bound `OpenDoc` identity sweep, scoped to native feature names, three sketch segments, body count, and rebuild status; it does not invent unavailable `OpenDoc6` error variables or duplicate mass measurement.

This completion is scoped to this bounded feature family and its 64-case seeded corpus. Arbitrary SLDPRT history support, wider feature/API/reference corpora, complete B-rep grammar, SLDASM, and SLDDRW remain unclaimed.
