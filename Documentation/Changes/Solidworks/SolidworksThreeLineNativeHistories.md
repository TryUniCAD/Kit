# Native three-line blind boss histories

## Behavior

Kit now reads and writes one closed, simple three-line sketch on the canonical front plane, followed by a forward blind extrusion. The family uses sketch 26/`Sketch1`, pad 32/`Boss-Extrude1`, plane 2, direction zero, and blind termination.

Depth is an independent finite positive value. Source vertex order and the three-edge closed wire are retained. Native-to-neutral projection creates three line entities with per-marker provenance and one three-edge closed wire.

The recovered scope does not accept solver relations, sketch dimensions, construction or fixed entities, open or self-intersecting wires, degenerate profiles, other planes, reversed directions, or other termination conditions. Unsupported inputs fail closed instead of discarding semantic content.

Three-line candidates also inspect every original source parameter before length-only serialization. Only native `D1` length and the recognized, non-expression FreeCAD pad schema are admissible. The bound depth must equal the extrusion definition in a supported length unit, parameters must be driving, and the document must have one configuration with zero offsets and draft settings. Other owner values, extra or stale lengths, driven roles, extra configurations, sketch dimensions, and expressions decline native encoding instead of disappearing while parameter capabilities are granted. Public coverage rejects `CustomCount` on both the sketch and extrusion, an additional pad-owned `CustomLength`, a pad `FuzzyTolerance` of `-1 + 5e-11`, a custom `Label2`, an `Offset` of `5e-11` on both parameter and definition, a stale depth, an unsupported depth unit, a driven depth role, and a second configuration. The FreeCAD projection requires the exact complete property set, the measured `-1` tolerance, and default labels, validating every value exactly where loss would otherwise occur. The recognized unsupported-parameter path raises `SldprtFormatError` from native encoding, so the default public write cannot fall back to a carrier; native preflight still returns false.

The right-angle rightmost-vertex tie is supported. `tri3tie`, with two rightmost vertices, demonstrates that tying `x` does not require rejecting the profile. The measured first-rightmost attachment convention preserves its zero-y coordinate.

## Recovered native structure

The three-line 2026 `Contents/Config-0-ResolvedFeatures` program has 10,601 bytes, 300 objects, 40 class definitions, 2,518 typed operations, and 495 owner callsites. No triangle-specific class abstraction or opaque stream replacement is used.

The primitive capture has 2,946 scalar reads. Direct span filtering keeps only the 10,601-byte resolved-feature buffer. `re/tooling/windbg/Generation/GenerateResolvedProgram.py` accepts `--buffer` for captures that contain both buffer length and cursor position. Independent re-emission is byte-identical with SHA-256 `5088c5c909bc432b12ee2f50f8aaa7934f3232e62ef30bb0a6d1563ac340ced0`.

The 51 computed fields are:

- six coordinates at 6121, 6129, 6299, 6307, 6461, and 6469;
- positive depth at 9408, 9480, 9968, and 9992;
- negative annotation depth at 9806 and 9830;
- bbox centres and full sphere diameters at 8201/8209/8217/8225 and 8423/8431/8439/8447;
- 24 display-plane centres, signs, and expanded extents;
- two attachment-coordinate pairs at 9440/9448 and 9464/9472, their sign-changing transform partners at 9637 and 9653, and the scaled attachment scalar at 9726.

`BuildBounds`, `BuildDisplay`, and `BuildNotes` own independent field maps. `PadBounds`, `PadAttach`, `PadGeometry`, and `PadValidation` separate the bounds contract, attachment selection, geometry derivation, and validation.

Range expansion uses `(range * 1.1) / 2000`, preserving the observed operation order. Expanded z uses `(depth * 1.1) / 2000`. The scaled attachment uses `x / 5000`, not a reassociated product which would change floating-point encoding. Bbox diameter is `2*sqrt(half_x²+half_y²+half_z²)` metres, converted to millimetres by the native decoder.

The writer supplies both sphere diameters at their typed operation starts, 8225 and 8447. Public integration coverage checks both raw values for the shifted nonbaseline profile. Triangle coordinate overrides use the validated source marker's metre pairs directly; they do not reconstruct source data from the neutral reader's 12-decimal presentation values. A public regression case verifies all six emitted doubles exactly when source coordinates exceed 12 decimal places.

The 2026 generation uses the independently typed `Definition` (3,816 bytes), `CMgr` (2,159 bytes), and `Config-0` (25,476 bytes). `BuildPolyTree` explicitly chooses generation 19000 for this triangle and the existing five-line family. Other recovered families retain their declared generations.

## Additive program generation

`re/tooling/ProgramDecomposition/AddProgram.py` loads one `resolved/polyline/<family>/Program.py` source and renders only that family's registry and method tables. It requires an explicit `--program-root` destination rather than defaulting to production modules. It does not delete or regenerate other families.

An existing owner module can be reused only when every required owner key/value pair is already present. Extra entries for other families remain intact. A missing owner module may be added without changing existing entries. Conflicting values are rejected rather than silently merged.

Existing stream aliases and owner catalogs were left at their approved forms. The combined verifier reports 45 programs, 77 streams, 215 catalogs, 2,461 owners, 3,995 methods, and 190,316 operations.

No production conversion reads a vendor part, captured stream, stored byte span, or oracle executable. The method/source-generation path contains typed scalar, string, archive-reference, and counted-record operations rather than donor files or donor blocks.

## SOLIDWORKS acceptance

Fresh public `write_document(..., allow_carrier=False)` output was checked with SOLIDWORKS 34.5.2 on Parallels. All four cases had zero load errors and warnings, `OPENED=True`, `REBUILT=True`, one body, and the requested `D1@Boss-Extrude1`.

| Public case                  | Depth, mm | Volume, mm³ |   Surface area, mm² |
| ---------------------------- | --------: | ----------: | ------------------: |
| `(0,0), (42,0), (12,31)`     |         9 |       5,859 |  2,367.427645476918 |
| `(-7,-11), (39,-4), (17,38)` |        17 |      17,731 |  4,610.577015505639 |
| `(0,0), (42,0), (12,31)`     |        21 |      13,671 | 3,787.9978394461414 |
| `(0,0), (36,0), (36,24)`     |        11 |       4,752 | 1,999.9327683612466 |

The values satisfy `area(profile) × depth` and `2 × area(profile) + perimeter × depth`.

Late-bound `re/tooling/harness/OracleTriangleFeatures.vbs` independently confirms `Sketch1` as a `ProfileFeature` with exactly three lines and `Boss-Extrude1` as an `Extrusion`. Editing the shifted public file from 17 mm to 5 mm rebuilt to 5,215 mm³ and 2,828.5226516193 mm² before closing without saving.

The separate high-precision control also opens with zero load errors and warnings, one body, and a successful rebuild. At 13.375 mm it measures 14,392.0569347259 mm³, 4,171.2939338546 mm², and centre `(16.5967040785597, 7.66251477736625, 6.6875)` mm. Its live 6.25 mm edit rebuilds to 6,725.26024987192 mm³ and 3,095.63966028405 mm² without saving, matching the independent analytic values.

The baseline re-emission digest above is capture evidence, not a claim that new independent documents have identical author stamps or every floating-point scalar from the vendors' document state. Whole-body geometry, feature naming, depth edits, volume, and surface acceptance were measured afresh in the target application.

## Seeded corpus evidence

`re/tooling/harness/AuthorTriangles.vbs` authored 64 distinct native sources from seed 982711 using six-decimal coordinates and independent depths. Each source has a three-line `Sketch1`, a native `Boss-Extrude1`, one body, and a successful rebuild. The source corpus covers positive, negative, clockwise, counterclockwise, translated, and differently shaped triangles rather than repetitions of one baseline.

`re/tooling/harness/BuildRandomTriangles.py` recovers neutral source points and four matching binary depth witnesses before making fresh public `write_document(..., allow_carrier=False)` calls. The source display text is not used as the exact depth. Reused output files must match all six coordinate and four depth doubles exactly; other outputs must be newly written, and no source stream becomes a writer input.

`re/tooling/harness/VerifyRandomOracle.py` independently compares every output against analytic volume, area, and centre-of-mass expectations through the compiled SOLIDWORKS 34.5.2 oracle. The completed result is `ORACLE_TOTAL=64 ORACLE_PASS=64`: all cases report zero load errors and warnings, `OPENED=True`, `REBUILT=True`, one body, and the authored depth. Depth ranges from 3.931416 to 49.774612 mm; measured volumes range from 7,886.94036988702 to 152,118.315621051 mm³. Per-case values are retained in `.rescratch/triangle-research/random64/generated-exact/oracle-results.json` during verification and are not production inputs.

The oracle harness distinguishes missing transport measurements from model failures, preserves passing results across bounded retries, and uses compiled `OpenDoc6` evidence for load errors. The separate late-bound identity sweep also completes `ORACLE_TOTAL=64 ORACLE_PASS=64`: every output has three lines, `ProfileFeature`, `Extrusion`, one body, and a successful rebuild. Its unavailable `OpenDoc6` outputs are never replaced with hardcoded successes.

Random case 19 demonstrates a live 17.995855→5 mm edit, rebuilding to 7,533.64542964935 mm³ and 3,947.70779111985 mm² before closing without saving. Both edited mass values match the independent analytic computation.

These 64 independently rebuilt blind pads demonstrate this family's seeded variability. They do not establish arbitrary SLDPRT histories, other feature families, assemblies, drawings, or complete B-rep coverage.

## Native replay acceptance

Native reads retain `NativeProfile.native_coordinates_mm` separately from the normalized presentation coordinates. Public neutral sketch construction uses the measured coordinates instead of discarding digits after 12 decimal places. Both source-metre consistency checks use the same `Clean(round(..., 12))` normalization, including a 1e-12-mm-to-zero boundary; they do not introduce a second incompatible comparison.

`RecoverTriDepth` recovers exact binary depth only for the independently recovered 10,601- and 10,603-byte three-line layouts. It requires four matching positive doubles at shifted 9408/9480/9968/9992, two exactly negated doubles at shifted 9806/9830, and consistency with the presentation label. The result supplies both the operation length and neutral feature scalar with a native offset. `DimensionParam` uses this native scalar when available rather than reusing rounded display text.

`IsTriSource` also identifies the family-shaped case where an unbound depth cannot be recovered. For a canonical forward blind boss in that case, `DecodePadMut` now raises `SldprtFormatError` instead of preserving an approximate dimension label. This prevents a conflicting or unsupported depth witness from being rewritten as though it were authoritative. The same rejection applies to another resolved-stream layout or a later-feature history whose `D1` remains unbound; these are unsupported histories, not permission to retain a rounded label. A valid rebuilt archive with one deliberately corrupted positive witness exercises the rejection through `open_document` after removal of the embedded neutral channel.

Native polyline closure now requires exact shared endpoints before line starts are serialized. A 1e-13-mm endpoint gap is rejected as an open wire instead of being silently replaced with a new closed wire. Exact near-origin writing remains supported.

Bound `instance_count` is also kept as a unitless count instead of being multiplied by 1000 and labelled in millimetres. Length and angle conversions remain separate.

Regression fixtures now use typed XML and `BuildSldprt` rather than searching or replacing raw container bytes. Compressed payloads, checksums, directory offsets, and file signatures are re-emitted correctly for both the rounded-label input and invalid-depth input. Native-reader fixtures remove `Kit/Interchange` and `Kit/Native`, preserve the keyword prefix, and request `include_brep=False` because these feature-only files intentionally have no Parasolid payload. The self-emulated freecad/proof compatibility path remains outside the accepted native replay scope and is not replaced by these fixture repairs.

Public `open_document` followed by `write_document(..., allow_carrier=False)` succeeds for all four replay controls. SOLIDWORKS 34.5.2 measured zero load errors and warnings, one body, and successful rebuild for each:

| Replay control                                | Depth, mm |       Volume, mm³ | Surface area, mm² |
| --------------------------------------------- | --------: | ----------------: | ----------------: |
| `tri3r010`, rounded display 19.53             | 19.529617 | 74,669.2099156988 | 13,182.8305763142 |
| `tri3r019`, rounded display 18                | 17.995855 | 27,114.8781546765 | 6,375.98230826179 |
| vendor-authored high precision                |    13.375 | 14,392.0569347259 |  4,171.2939338546 |
| vendor-authored near-origin, first x 8e-13 mm |         9 | 5,858.99999999989 | 2,367.42764547688 |

The near-origin output retains its 8e-16-metre first coordinate through the common normalization rule. The high-precision replay's live 6.25 mm edit rebuilds to 6,725.26024987192 mm³ and 3,095.63966028405 mm² before closing without saving. These measurements match the independent source and analytic results.

`AuthorTriangles.vbs /precise` authors the last two independent controls. `tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py` additionally covers a self-authored rounded label, exact native depth/vertex reads, exact writer doubles, and the near-origin boundary without assuming a broader freecad interpretation for all neutral histories.

## Verification and scope

Compilation, repository steering, Ruff, mypy, pyright, Prettier, path policy, and the full additive program verifier pass. Integration coverage lives in `tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py` and is exercised by remote CI, not a prohibited local unit-test run.

This remains one bounded native feature family with four controls and a seeded 64-case corpus. Arbitrary SLDPRT histories, a broad multi-feature/API/reference corpus, full B-rep grammar, SLDASM, and SLDDRW are not demonstrated. No file named by this change is merged or declared merge-ready on the strength of this bounded acceptance alone.

## Related information

- [Triangle research record](../../../re/solidworks/records/PolylineThreePad.md)
- [Archive capture gotcha](../../Gotchas/Conversion/CdbArchiveCapturePipeline.md)
- [Isolated share-path gotcha](../../Gotchas/Conversion/OracleWorktreeSharePaths.md)
- [Triangle arithmetic gotcha](../../Gotchas/Conversion/SolidworksTriangleArithmeticOrder.md)
- [Registry-alias gotcha](../../Gotchas/Conversion/ProgramRegistryAliasContract.md)
- [Resolved operation offsets](../../Gotchas/Conversion/ResolvedProgramOperationOffsets.md)
- [Triangle coordinate precision](../../Gotchas/Conversion/SolidworksTriangleCoordinatePrecision.md)
- [Triangle depth recovery](../../Gotchas/Conversion/SolidworksTriangleDepthRecovery.md)
- [Late-bound OpenDoc evidence](../../Gotchas/Conversion/OracleLateBoundOpenDoc.md)
- [Exact polyline closure](../../Gotchas/Conversion/SolidworksPolylineClosure.md)
- [Archive fixture editing](../../Gotchas/Conversion/SolidworksArchiveFixtureEditing.md)
- [Scalar kind handling](../../Gotchas/Conversion/SolidworksScalarKinds.md)
- [Polyline parameter loss](../../Gotchas/Conversion/SolidworksPolylineParameterLoss.md)
- [Dependent Code Quality reporting](../../Gotchas/Ci/StackedCodeQualityReport.md)
