# Typed Fusion Form documents

Kit reads and writes complete Fusion Form documents through `ReadDocument` and `EmitParsed` in `convert.formats.Fusion.DocumentCodec`. A Form document joins a T-spline control cage, a Form feature graph and a converted BRep body. Earlier Kit readers rejected these documents.

## Model

`DocumentModel.Forms` contains one `DocumentForm(Name, Surface)` for each `TSplines.BlobParts/TSpline.<uuid>.tsm` member. `Surface` is the typed `TsplineSurface` from `ReadTspline`. The writer derives the member text with `EmitTspline`. The Design records stay in the typed entity model. `FormClasses.json` adds the Form vocabulary to the document schema catalog.

The converted body uses three new journal entity types in `convert.formats.Fusion.BrepCodec.Journal.Spline`.

| Entity | Type | Main fields |
| --- | --- | --- |
| `spline-surface` | `SplineNode` | `Surface` as `TsplineSurf` or `SubtypeRef`, four bounds |
| `intcurve-curve` | `IntcurveNode` | `Curve` as `ExactCurve` with a `NubsCurve` cache |
| `pcurve` | `PcurveNode` | `Curve` as `ParCurve` with a `NubsCurve` cache and a T-spline support |

`TsplineSurf` holds the revision, the `NubsSurface` cache, the fit tolerance, six jump arrays, four optional ranges, a type code and a face index. Its `Subtrans` field is a `SubtransNode` or a `SubtypeRef`. A `SubtransNode` holds the embedded `TsplineSurface` and the patch program as `PatchCell` rows. `CoedgeNode.Pcurve` now keeps the coedge reference to its `pcurve`.

`ListPrograms(Entities)` returns the embedded T-spline programs of a body. `ListSubtypes` and `CheckSubtypes` expose and check the subtype table. `ReadAsmToken` reads tag 8 text, and `EmitWireField` writes tags 8, 13 and 21. `NamedMetadata.ElementName` keeps the element metatype of `Vector` named metadata.

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

## Authoring boundary

Kit does not author a Form document from a new cage. Fusion 2706.1.17 refused to open a Form document without its BRep members. It also kept a stale converted body without a warning and did not convert the cage again. A correct document therefore needs the exact converted body. Kit has no T-spline conversion that gives Fusion's converted body. The [authority gotcha](../../../Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) gives the measured variants.

## Verification

[The production round trip](../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json) read 32 local Form archives with Python 3.14.7. 29 archives gave an equal model after `EmitParsed` and equal member names. All their members were byte-equal after decompression, except the `.protein` material packages. The existing material writer emits those packages in canonical form.

The three failing archives are the edited captures. Each stops in the graphics reader at world kind 2. The [edited world gotcha](../../../Gotchas/Conversion/Fusion/TSpline/EditedFormGraphicsWorld.md) gives the isolation result.

The [spline census](../../../../re/Fusion/Reconstruction/FormDocuments/SplineCensus.json) read all 64 BRep members of the 32 archives. Every embedded program equals the TSM member of its archive. A scan of 282 local F3D archives found 142 model-equal round trips after the change and 113 at the base commit. All 32 changed results are Form archives: 29 now pass, and three now stop at the graphics world.

[Native acceptance](../../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json), SHA-256 `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552`, has status `completed` in Fusion 2706.1.17. All four cases have status `accepted`, and zero documents remained open. Each case opened the native control and its `EmitParsed` output. Each case then ran `computeAll`, read the Form health and the cage, and moved the first cage vertex in coordinate order by (0.11, 0.07, 0.13) cm. It then converted the form, saved, reopened and compared each stage within 1e-7. The [preparation](../../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/Preparation.json) binds each input to its SHA-256.

| Case | Faces, edges, vertices | Area before edit (cm²) | Area after edit (cm²) | Volume after edit (cm³) |
| --- | --- | --- | --- | --- |
| Plane | 1, 4, 4 | 3.831410566653259 | 3.75882224444742 | None, open sheet |
| Creased plane | 2, 7, 6 | 3.8314105666532576 | 3.7597048123427688 | None, open sheet |
| Box | 6, 12, 8 | 23.395349005089184 | 23.229292504382165 | 9.339333654763482 |
| Symmetric box | 6, 12, 8 | 23.229718749711484 | 22.896262895240067 | 9.137857029717933 |

The control and the re-emitted document gave the same printed values at every stage. The Form health and the timeline health were 0 at every stage. The cage digests of the two documents were equal before the edit, after the edit and after reopen. Kit cannot read the eight Fusion-saved archives. Each stops on unexplained trailing bytes in one `RevGUIDACTDataMany` record of the ACT segment. This boundary is not specific to Form documents. 64 other local archives stop with the same error message, and the two that were checked stop at the same class.

Black, Ruff, Mypy, Pyright and steering checks passed for the production and test modules. Remote integration cases cover the 29 Form archives, the three edited archives and 58 spline journal members. Other cases cover subtype faults, patch text faults, text widths, pole counts and four join faults. No local tests ran.
