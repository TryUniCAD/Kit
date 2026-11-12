# Draft section for the Fusion data model: Form documents

This draft is for a new section after "T-spline control cages and orientation" in `Documentation/Reference/Research/FusionDataModel.md`.
The section text starts at the next heading.
Links are relative to `Documentation/Reference/Research/`.

## Form documents

A Form document joins one T-spline control cage to one converted BRep body.
The cage is the `.tsm` member in `TSplines.BlobParts`.
The converted body is committed ACIS geometry in `Breps.BlobParts`.
`ReadDocument` reads the complete graph, and `EmitParsed` writes it again.
`DocumentModel.Forms` holds one `DocumentForm(Name, Surface)` for each TSM member.

### Design graph

The Design segment adds these classes to an ordinary body document.

| Class | Fields that join the graph | Target |
| --- | --- | --- |
| `DcTSplineFeature` | `rTSplineToolBody`, `subDInfoMap`, `dcBodies`, `childNodes`, `rProgenitorTable`, `rDirectModelingData` | Tool body, surface node, `DcBody`, progenitor tables |
| `493A89BA-E146-498D-9033-2783FE727AF4` | `rBaseFeature` | The Form feature |
| `DcTSplineToolBody` | `rTSplineFeature`, `toolbodyCaches` | The Form feature, `ETCachedTopology` |
| `TsSurface` | `rSerializer`, `frame`, `rVSurface`, `tess` | Serializer, control frame, surface node, `SurfaceTessellation` |
| `TSplineSerializer` | `partName`, `rSurface` | `TSplines.BlobParts/TSpline.<uuid>.tsm`, `TsSurface` |
| `ControlFrameMesh` | `facets`, `edges`, `vertices`, `grips`, `rSurface` | Frame entities, `TsSurface` |
| `ControlFrameFacet`, `ControlFrameEdge`, `ControlFrameVertex`, `ControlFrameGrip` | `rMesh`, `tsID` | `ControlFrameMesh`, TSM table index |
| `SubDSurfaceNode` | `rDcTSplineFeature`, `rSurface`, `rGroupParent`, named `BASEFEAT_PM_BODIES_REF` | Feature, `TsSurface`, cache `Bodies`, converted `Body` |
| `Body` | named `FORMFEAT_DM_SUBD_REF`, `rGroupParent` | `SubDSurfaceNode`, history `Bodies` |
| `TSplineEntityProgenitor` | `entityType`, `tsEntityProgenitors` | TSM faces and parameter windows |

The `subDInfoMap` maps the surface node to an operation identifier and a `ProgenitorTable`.
That table lists one `TSplineEntityProgenitor` for each named face or boundary edge of the converted body.
Each entry lists TSM face indexes with a `(uLow, uHigh, vLow, vHigh)` window.
Type 0 entries have full windows and name converted faces.
Type 1 entries collapse one parameter and name boundary edges.
The plane control has one type 0 and four type 1 entries.
The box controls have six type 0 entries.

The component has two `Bodies` groups.
The history group owns the converted `Body` and the `BRepHistorySerializer` of the `.smbh` member.
The cache group, `FusionComponent.rCacheBodies`, owns the surface node and the `BRepSerializer` of the `.smb` member.

### Kit joins

`CheckDocForms` runs during read and before emission.

| Join | Rule |
| --- | --- |
| Serializer and part | Each `partName` names one TSM member, and each member has one serializer |
| Serializer and surface | `TsSurface.rSerializer` names the serializer that names the surface |
| Control frame | Facet, edge, vertex and grip `tsID` values are `range(n)` for the TSM table counts |
| Surface node | `TsSurface.rVSurface` names the node, and the node names the surface |
| Converted body | The node vector names each `Body`, and each `Body` names the node back |
| Embedded program | Every T-spline program in the `.smb` and `.smbh` members equals a TSM member |

### Converted BRep grammar

The converted body uses three ACIS entity kinds that ordinary documents do not use.

| Entity | Subtype scope | Contents |
| --- | --- | --- |
| `spline-surface` | `t_spl_sur` or `ref` | Revision, cached bicubic `nubs` surface, fit tolerance, six jump arrays, four optional ranges, type code, `t_spl_subtrans_object` or `ref`, face index |
| `intcurve-curve` | `exact_int_cur` | Revision, cached `nubs` curve, fit tolerance, null supports, cache bounds, three jump arrays, extension, two ranges, two codes |
| `pcurve` | `exp_par_cur` | Cached 2D `nubs` curve, fit tolerance, `spline` support with a `t_spl_sur` definition or `ref`, four optional bounds, U and V offsets |

The `t_spl_subtrans_object` scope stores the complete TSM program and a patch program.
The patch program has one line for each converted face.
Each line lists TSM faces with a window and an offset.
A `ref N` scope indexes a table of subtype definitions in stream order.
Text uses tag 7 up to 255 bytes and tag 8 above.
The [subtype gotcha](../../Gotchas/Conversion/Fusion/TSpline/SplineSubtypeTable.md) and the [text width gotcha](../../Gotchas/Conversion/Fusion/TSpline/SplineTextWidth.md) give the measured values.

### Converted body authority

Fusion 2706.1.17 takes the editable cage from the TSM member.
It takes the body from the stored BRep members.
It did not convert the cage again on open, on `computeAll`, or on an empty edit.
It refused to open a Form document without the BRep members.
It accepted a stale BRep with health 0.
The [authority gotcha](../../Gotchas/Conversion/Fusion/TSpline/StoredFormBrepAuthority.md) gives the variants.
A writer must therefore store the exact converted body.
Kit has no T-spline conversion, so it does not author Form documents from a new cage.

### Form document verification

The production round trip read 32 local Form archives.
29 archives gave an equal model after emission and byte-equal members, except for canonical `.protein` packages.
Three edited archives stop in the graphics reader at world kind 2.
The [edited world gotcha](../../Gotchas/Conversion/Fusion/TSpline/EditedFormGraphicsWorld.md) gives the isolation result.
[Native acceptance](../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json), SHA-256 `b018171b82ad933a65611f5e56b54f0b48b6660bae06bc936267544f876fa552`, accepted four re-emitted controls in Fusion 2706.1.17.

| Case | Faces, edges, vertices | Area after edit (cm²) | Volume after edit (cm³) |
| --- | --- | --- | --- |
| Plane | 1, 4, 4 | 3.75882224444742 | None |
| Creased plane | 2, 7, 6 | 3.7597048123427688 | None |
| Box | 6, 12, 8 | 23.229292504382165 | 9.339333654763482 |
| Symmetric box | 6, 12, 8 | 22.896262895240067 | 9.137857029717933 |

Each re-emitted document equalled its native control within 1e-7 after open, edit, save, and reopen.
The Form health stayed 0, and zero documents remained open.
The [Form document change entry](../../Changes/Fusion/TSpline/FusionFormDocuments.md) gives the complete procedure.
