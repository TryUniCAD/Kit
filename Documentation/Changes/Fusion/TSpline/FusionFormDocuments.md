# Typed Fusion Form documents

Kit reads and writes complete Fusion Form documents through `ReadDocument` and `EmitParsed` in `convert.formats.Fusion.DocumentCodec`. A Form document joins a T-spline control cage, a Form feature graph and a converted BRep body. Earlier Kit readers rejected these documents.

Kit also converts qualified open grid cages exactly, and it puts a new cage of the same grid layout into a Form document. Kit refuses every other new cage.

## Model

`DocumentModel.Forms` contains one `DocumentForm(Name, Surface)` for each `TSplines.BlobParts/TSpline.<uuid>.tsm` member. `Surface` is the typed `TsplineSurface` from `ReadTspline`. The writer derives the member text with `EmitTspline`. The Design records stay in the typed entity model. `FormClasses.json` adds the Form vocabulary to the document schema catalog.

The converted body uses three new journal entity types in `convert.formats.Fusion.BrepCodec.Journal.Spline`.

| Entity | Type | Main fields |
| --- | --- | --- |
| `spline-surface` | `SplineNode` | `Surface` as `TsplineSurf`, `SubtypeRef` or a general `SubtypeNode`, four bounds |
| `intcurve-curve` | `IntcurveNode` | `Curve` as an `exact_int_cur` `SubtypeNode` or a `SubtypeRef` |
| `pcurve` | `PcurveNode` | `Curve` as an `exp_par_cur` `SubtypeNode` whose `spline` support holds a `TsplineSurf` or a `SubtypeRef` |

`TsplineSurf` holds the revision, the `NubsSurface` geometry, the fit tolerance, six jump arrays, four optional ranges, a type code and a face index. Its `Subtrans` field is a `SubtransNode` or a `SubtypeRef`. A `SubtransNode` holds the embedded `TsplineSurface` and the patch program as `PatchCell` rows. `CoedgeNode.Pcurve` now keeps the coedge reference to its `pcurve`.

The complex geometry change merged these entities with the general subtype grammar. The [complex geometry change entry](../Geometry/FusionComplexGeometry.md) describes that model.

`ListPrograms(Entities)` returns the embedded T-spline programs of a body. `ListTsplines(Entities)` returns each `TsplineSurf` in stream order. `ListSubtypes` and `CheckSubtypes` expose and check the subtype table. `ReadAsmToken` reads tag 8 text, and `EmitWireField` writes tags 8, 13 and 21. `NamedMetadata.ElementName` keeps the element metatype of `Vector` named metadata.

## Joins

`CheckDocForms` runs during `ReadDocument` and before `EmitParsed` writes a document. It raises `ValueError` when one of these joins fails.

| Join | Rule |
| --- | --- |
| Serializer and member | Each `TSplineSerializer.partName` names one TSM member, and each member has one serializer |
| Serializer and surface | `TsSurface.rSerializer` names the serializer that names the surface |
| Control frame | Facet, edge, vertex and grip `tsID` values equal `range(n)` for the TSM table counts |
| Surface node | `TsSurface.rVSurface` names the `SubDSurfaceNode`, and the node names the surface |
| Converted body | `BASEFEAT_PM_BODIES_REF` names each `Body`, and each `FORMFEAT_DM_SUBD_REF` names the node back |
| Embedded program | Each T-spline program in the `.smb` and `.smbh` members equals a TSM member |

The reader also checks the canonical patch program, the canonical text width and the order of subtype references. It rejects a knot multiplicity above the degree and a pole count above 65,536.

## Archives saved by current Fusion

Fusion 2706.1.17 often writes a few bytes after the final record of the ACT segment bulk stream. Kit refused these archives with `Unexplained trailing Fusion entity payload bytes`. The final record is a `RevGUIDACTDataMany` record, and its native member set has only `revGuidMap`.

`ReadDocSegment` now reads the last ACT record with `ReadSlack`. `DecodeSlack` returns the decoded record and its unread bytes. `ParsedSegment.BulkSlack` keeps those bytes, and `EmitDocSegment` writes them after the last record. Every other record and every other segment still refuses trailing bytes. `DecodeRecord` gives the new fields their defaults for legacy native state. The [ACT slack gotcha](../../../Gotchas/Conversion/Fusion/Records/FusionActBulkSlack.md) gives the save evidence.

Edited Form archives also store graphics world kind 2. `XferTSplineMut` reads and writes it with the BRep level-of-detail layout of `XferLodsMut`, without a `ValidBody` flag. The attribute rules add `OpacityAttribute` with `Absolute` and `Opacity`. The [edited world gotcha](../../../Gotchas/Conversion/Fusion/TSpline/EditedFormGraphicsWorld.md) gives the layout.

## Grid cage conversion

`ConvertGrid(Surface)` in `convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion` returns a `GridResult`. The result holds the exact `NubsSurface`, the patch cells, four boundary curves, four corner points and the discontinuity lists.

| Step | Function | Result |
| --- | --- | --- |
| Qualify the cage | `CheckGridCage` | The grip mapping, or `ValueError` |
| Number the spokes | `SpokeIndices` | One spoke index from 0 to 3 for each link |
| Place the vertices | `PlaceVertices` | One grid position for each vertex |
| Place the grips | `PlaceGrips` | Pole counts and the grip order of the poles |
| Make the knots | `GridKnots` | Integer knots with end multiplicity 3 |
| Make the patch program | `GridPatches` | One `PatchCell` for each face |
| Make the boundary | `GridBounds` | Four boundary curves in loop order |
| Find the discontinuities | `GridJumps`, `ThirdJumps` | Interior knots with a third-derivative jump |
| Write a curve list | `JumpCurve` | An `exact_int_cur` with its order-3 discontinuity list |

`SwapEntity` replaces the converted surface, curves and corner points of one entity. It first checks that the entity holds the conversion of the old cage. It raises `ValueError` on a stale surface, a stale boundary curve, a stale corner point or another patch program.

`SwapGridCage(Model, Surface)` in `convert.formats.Fusion.DocumentCodec.Auxiliary.Form` returns a new `DocumentModel`. It needs exactly one Form and the same patch cells and knots for the old and the new cage. It replaces the cage, every converted history and snapshot entity, and sets `Graphics` to `None`. Fusion regenerates the graphics when it opens the document.

The [grid pole order gotcha](../../../Gotchas/Conversion/Fusion/TSpline/GridCagePoleOrder.md) gives the conversion rules. The [discontinuity gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedDiscontinuityLists.md) gives the jump rule.

## Authoring boundary

The stored surface of a converted Form face is exact geometry. `t_spl_sur` derives from `exact_spl_sur`, and the kernel refuses a surface without its B-spline data. Fusion 2706.1.17 used a moved stored surface as the face geometry and kept it after `computeAll`. A set `TsSurface.bConversionFailed` flag did not start a conversion. No procedural surface route exists, so a writer must store the exact conversion. The [converted surface gotcha](../../../Gotchas/Conversion/Fusion/TSpline/ConvertedSurfaceIsExact.md) gives the evidence.

Kit therefore authors only the cases that `ConvertGrid` qualifies.

| Cage | Kit result | Reason |
| --- | --- | --- |
| Open plane grid without interior creases | Exact conversion and document swap | Each interior vertex has valence 4, and the limit surface is one B-spline |
| Box and symmetric box | `ValueError` | Valence-3 corners give G1 caps with double knots |
| Plane or box with interior creases | `ValueError` | The crease changes the face partition or adds knots, and the poles are not grips |
| Non-unit knot intervals or weights | `ValueError` | No local native evidence |
| A new grid layout | `ValueError` | The Design progenitor tables and frame entities would change |

The grid census records the native box surfaces. Each box face has 13 × 13 poles, double knots at 0.25, 0.5, 1.5 and 1.75, and four patch cells. Kit has no exact rule for those caps. The [stored body authority gotcha](../../../Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) shows that Fusion keeps a stale body without a warning.

## Verification

[The production round trip](../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json) read 32 local Form archives with Python 3.14.7. All 32 archives gave an equal model after `EmitParsed` and equal member names. All members were byte-equal after decompression, except the `.protein` material packages. The existing material writer emits those packages in canonical form.

The [spline census](../../../../re/Fusion/Reconstruction/FormDocuments/SplineCensus.json) read all 64 BRep members of the 32 archives. Every embedded program equals the TSM member of its archive.

The [ACT slack census](../../../../re/Fusion/Reconstruction/ActSlack/SlackCensus.json) read 72 focus archives that earlier stopped on the trailing bytes. All 72 read, gave an equal model after `EmitParsed` and gave byte-equal ACT streams. In the 308-archive corpus, 76 archives read with slack bytes and 164 without. The remaining 68 stop for other reasons.

The [grid census](../../../../re/Fusion/Reconstruction/FormDocuments/GridCensus.json) compared `ConvertGrid` with every converted Form body in 68 local Form archives.

| Result | Archives | Detail |
| --- | --- | --- |
| Equal | 28 | Knots, patch cells, discontinuity lists and curve forms equal, points within 8.9e-16 cm |
| Refused | 35 | Box, symmetric box and interior crease cages |
| Different | 4 | Deliberately stale probe variants |
| No body | 1 | The probe variant without BRep members |

[Grid acceptance](../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json), SHA-256 `360d7d4c9335e0840c4c95cd41ec28c6ba161b0a33f63862923de3267e761546`, has status `accepted` in Fusion 2706.1.17. Zero documents were open before and after the run. `PrepareGrid.py` wrote an affine and a warped 2 × 3 plane cage, and `SwapGridCage` put each cage into the native plane document. The [preparation](../../../../re/Fusion/LocalOracle/FormDocuments/Grid/Preparation.json) binds each input to its SHA-256.

For each case, Fusion converted the same TSM in a new Form as the oracle. Both documents then ran `computeAll`, moved the first cage vertex by (0.11, 0.07, 0.13) cm, converted, saved and reopened. The run compared body counts, area, NURBS poles and knots, 49 face points, 28 edge points and vertices within 1e-8.

| Case | Area as loaded (cm²) | Area after edit (cm²) | Largest Kit and oracle gap (cm) | Problems |
| --- | --- | --- | --- | --- |
| Affine | 3.981294020792737 | 3.9230459543150173 | 4.4e-16 before the edit, 0 after | 0 |
| Warped | 4.005512887961321 | 3.9455217633195576 | 4.4e-16 before the edit, 0 after | 0 |

The Form health and the timeline health were 0 at every stage. The cage TSM digests were equal, and the reopened Kit body equalled the edited body. The same run converted four new plane primitives, which the grid census found equal.

| Faces | Size (cm) | Poles | Area (cm²) |
| --- | --- | --- | --- |
| 1 × 1 | 2.0 × 1.5 | 4 × 4 | 3.0 |
| 3 × 2 | 3.0 × 2.0 | 6 × 5 | 6.000000000000001 |
| 4 × 4 | 2.5 × 2.5 | 7 × 7 | 6.249999999999998 |
| 2 × 5 | 1.7 × 4.1 | 5 × 8 | 6.969999999999999 |

[Form acceptance](../../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json), SHA-256 `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552`, has status `completed` in Fusion 2706.1.17. All four re-emitted cases have status `accepted`, and zero documents remained open. Each case compared the native control and its `EmitParsed` output within 1e-7 through open, edit, conversion, save and reopen.

| Case | Faces, edges, vertices | Area before edit (cm²) | Area after edit (cm²) | Volume after edit (cm³) |
| --- | --- | --- | --- | --- |
| Plane | 1, 4, 4 | 3.831410566653259 | 3.75882224444742 | None, open sheet |
| Creased plane | 2, 7, 6 | 3.8314105666532576 | 3.7597048123427688 | None, open sheet |
| Box | 6, 12, 8 | 23.395349005089184 | 23.229292504382165 | 9.339333654763482 |
| Symmetric box | 6, 12, 8 | 23.229718749711484 | 22.896262895240067 | 9.137857029717933 |

Remote integration cases cover the 32 Form archives, the ACT slack archives, the edited worlds and 58 spline journal members. Grid cases cover 17 native archives, three refusals, two document swaps with their emitted SHA-256, three cage faults, a stale body and a layout change. No local tests ran.
