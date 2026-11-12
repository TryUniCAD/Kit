# Complex ASM surface geometry and explicit NURBS bodies

The typed BRep journal codec now reads and writes spline surfaces, interpolated curves, parameter-space curves and tolerant topology. It also authors explicit NURBS sheets and closed NURBS solids from control points, knots and weights. Before this change, 113 corpus members stopped with `Unsupported Fusion journal entity kind: spline-surface`.

## Usage

`ReadJournal`, `ReadGeometry`, `EmitJournal`, `EmitGeometry`, `EmitStateSmb`, `PermuteJournal` and `PermuteGeometry` accept the new entities. There is no new reader entry point. Module paths in this entry are relative to `convert.formats.Fusion.BrepCodec.Journal`.

| ASM entity | Class | Module | Fields |
| --- | --- | --- | --- |
| `spline-surface` | `SplineNode` | `Spline.SplineNode` | `Prefix`, `Reversed`, `Surface`, `ULower`, `UUpper`, `VLower`, `VUpper` |
| `intcurve-curve` | `IntcurveNode` | `Spline.IntcurveNode` | `Prefix`, `Reversed`, `Curve`, `Lower`, `Upper` |
| `pcurve` | `PcurveNode` | `Spline.PcurveNode` | `Prefix`, `Reversed`, `Curve`, `OffsetU`, `OffsetV`, `Form`, `CurveRef` |
| `tcoedge-coedge` | `TcoedgeNode` | `Complex.Nodes.TcoedgeNode` | `Base`, `RangeLower`, `RangeUpper`, `CurveRef`, `CurveForm`, `Curve`, `Stamp` |
| `tedge-edge` | `TedgeNode` | `Complex.Nodes.TedgeNode` | `Base`, `Tolerance`, `SaveVersion`, `Stamp` |
| `tvertex-vertex` | `TvertexNode` | `Complex.Nodes.TvertexNode` | `Base`, `Sentinel`, `Tolerance`, `SavedTolerance`, `Stamp` |
| `stitch_hint-sys-attrib` | `StitchAttrib` | `Attributes.StitchAttrib` | `Links`, `HintValues` |
| `vertedge-sys-attrib` | `VertedgeAttrib` | `Attributes.VertedgeAttrib` | `Links`, `EdgeSlots` |

`KComplexTypes` in `Complex.ComplexEntity` lists the first six classes. `CoedgeNode.Pcurve` keeps the coedge reference to its `pcurve` entity, and -1 means no pcurve.

### Subtype values

`Surface` and `Curve` hold one subtype value. `SubtypeNode(SubtypeName, Body)` is an inline definition. `SubtypeRef(Family, Index)` refers to the `Index`th definition of the stream. `TsplineSurf` is the typed T-spline definition from the [Form document entry](../TSpline/FusionFormDocuments.md).

`Body` is a tree of `KGrammarValue` values from `Complex.Grammar.GrammarValue`. The tree uses tuples, `ChoiceValue`, nested subtype values, `LoftSubdata`, `BsCurve` and `BsSurface`. `KSubtypeRules` in `Complex.Grammar.SubtypeRules` gives the field sequence of each subtype.

| Family | Subtype names |
| --- | --- |
| `surface` | `exact_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `sweep_sur`, `loft_spl_sur`, `cl_loft_spl_sur`, `srf_srf_v_bl_spl_sur`, `VBL_SURF`, `g2_blend_spl_sur`, `t_spl_sur` |
| `curve` | `exact_int_cur`, `par_int_cur`, `int_int_cur`, `spring_int_cur`, `helix_int_cur` |
| `pcurve` | `exp_par_cur` |
| `subtrans` | `t_spl_subtrans_object` |

A `pcurve` with `Form` 0 holds its curve inline. With `Form` -2, -1, 1 or 2, `Curve` is `None` and `CurveRef` names an `intcurve-curve` entity.

| Function | Module | Result |
| --- | --- | --- |
| `ListSubtypes(Entity)` | `Spline.ListSubtypes` | `(name, None)` for each definition and `(family, index)` for each reference, in stream order |
| `CheckSubtypes(Entities)` | `Spline.CheckSubtypes` | `ValueError` for a forward reference or a family mismatch |
| `ListTsplines(Entities)` | `Spline.ListTsplines` | Each `TsplineSurf` in stream order |
| `WalkSubtypes(Value)` | `Complex.Subtypes.WalkSubtypes` | Each definition and reference inside one value, in pre-order |
| `MapSubtypes(Value, Mapping)` | `Complex.Subtypes.WalkSubtypes` | The value with its reference indexes replaced |
| `RelinkSubtypes(Entities, Chosen)` | `Complex.Subtypes.RelinkSubtypes` | The chosen entities with each missing definition inlined at its first reference |
| `ShiftSubtypes(Entities, Order)` | `Complex.Subtypes.ShiftSubtypes` | The entities with their references renumbered for a new order |

`EmitStateSmb` calls `RelinkSubtypes`. `PermuteJournal` and `PermuteGeometry` call `ShiftSubtypes`. The emitters run `CheckSubtypes`.

### NURBS authoring

`CreateNurbsBody(Model, History, Stamp)` in `Complex.Authoring.CreateNurbsBody` returns a complete `JournalModel`. `Model` is a `NurbsBody`. `History.MaxStateId` must be explicit. Emit the model with `EmitJournal` for an `.smbh` history and with `EmitStateSmb` for an `.smb` body.

| Class | Module | Fields |
| --- | --- | --- |
| `BsCurve` | `Complex.Spline.BsCurve` | `Rational`, `Degree`, `Closure`, `Knots`, `Multiplicity`, `Dimension`, `Poles`, `Weights` |
| `BsSurface` | `Complex.Spline.BsSurface` | `Rational`, `RationalForm`, `UDegree`, `VDegree`, `UClosure`, `VClosure`, `USingular`, `VSingular`, `UKnots`, `UMultiplicity`, `VKnots`, `VMultiplicity`, `Poles`, `Weights` |
| `NurbsEdge` | `Complex.Authoring.NurbsBody` | `StartVertex`, `EndVertex`, `Curve` |
| `NurbsUse` | `Complex.Authoring.NurbsBody` | `EdgeIndex`, `Reversed`, `Pcurve` |
| `NurbsFace` | `Complex.Authoring.NurbsBody` | `Surface`, `Uses` |
| `NurbsBody` | `Complex.Authoring.NurbsBody` | `PointsCm`, `Edges`, `Faces`, `EntityTag` |

The B-spline values use the ASM storage conventions.

| Item | Convention |
| --- | --- |
| Knots | `Knots` holds distinct values. `Multiplicity` holds the count of each value. |
| End multiplicity | Equal to the degree for a clamped curve |
| Pole count | `sum(Multiplicity) - Degree + 1` in each direction |
| Surface pole order | U changes fastest inside each V row |
| Weights | Separate from the poles. Empty for a nonrational value. |
| `RationalForm` | `both`, `u` or `v` for a rational surface. Empty for a nonrational surface. |
| Units | Centimeters for 3D poles. Surface parameters for 2D pcurve poles. |

Give each `NurbsUse.Pcurve` in the direction and range of its edge curve. The writer negates the pcurve of a reversed use. Each face has one loop.

| Helper | Module | Result |
| --- | --- | --- |
| `PatchSheet(Surface, EntityTag)` | `Complex.Authoring.PatchSheet` | A one-face open sheet with four boundary edges and linear pcurves |
| `BoundaryCurve(Surface, SideIndex)` | `Complex.Authoring.PatchSheet` | Side 0 is the low V row, 1 the high U column, 2 the high V row and 3 the low U column |
| `NegateCurve(Curve)` | `Complex.Authoring.NegateCurve` | The curve on the negated, reversed parameter range |
| `PointOnCurve`, `PointOnSurface` | `Complex.Authoring.SplineEval` | Rational de Boor evaluation |
| `ExactSurface`, `ExactCurve`, `ParamCurve` | `Complex.Authoring.ExactSubtypes` | `exact_spl_sur`, `exact_int_cur` and `exp_par_cur` subtype nodes |
| `SplineSurface`, `SplineCurve`, `PcurveSpline` | `Complex.Authoring.ExactSubtypes` | The B-spline inside those three subtype nodes |

## Semantic checks

The reader consumes each subtype with an exact field sequence. It raises `ValueError` for an unknown subtype, a subtype in the wrong family and a reference before its definition. B-spline blocks must have a degree from 1 to 25 and 2 to 4096 strictly increasing finite knots. Each multiplicity is from 1 to the degree plus 1. Poles must be finite and match the knot count. Weights must be positive and finite.

`CreateNurbsBody` adds these checks before it writes records.

| Check | Rule |
| --- | --- |
| Shell | Each edge has one use in an open sheet, or two uses in a closed shell |
| Shared edge | The two uses have opposite senses |
| Vertices | 2 to 4096 points, and each point bounds an edge |
| Edge curve | The curve ends are within 1e-6 cm of their vertices |
| Pcurve range | The pcurve knot range equals the edge knot range |
| Pcurve position | The surface point of the pcurve is within 1e-6 cm of the edge point at 17 samples and every knot |
| Loop | Each use ends where the next use starts |

`StitchAttrib` requires three finite doubles. `VertedgeAttrib` admits at most `KVertedgeCap` (64) edge slots. A vertex with a `vertedge-sys-attrib` can omit its edge reference. A `sketch_attrib_def` custom attribute can name a vertex.

## Reconciliation with Form documents

The Form document change added the `Spline` package with narrower classes. This change keeps its class names, module paths and joins. `CheckDocForms` still uses `ListPrograms`.

| Form model | This change | Reason |
| --- | --- | --- |
| `SubtypeRef(Index)` | `SubtypeRef(Family, Index)` | Corpus references also name other surface subtypes, `curve` definitions and `pcurve` definitions |
| `PcurveNode.Curve` as `ParCurve` with `Support` | `exp_par_cur` `SubtypeNode`, plus `Form` and `CurveRef` | Corpus supports include `plane` surfaces and procedural `spline` surfaces. 372 corpus pcurves use the referenced forms. |
| `IntcurveNode.Curve` as `ExactCurve` | Any curve subtype value | `ExactCurve` admitted null supports only |
| `ExactCurve`, `ParCurve`, `NubsCurve`, `ListSurface` | Removed | The general grammar reads the same records |
| `ListSubtypes` with subtype names for references | Families for references | A reference slot accepts any definition of its family |
| None | `ListTsplines` | Gives the Form joins the T-spline definitions in stream order |

`TsplineSurf`, `SubtransNode`, `NubsSurface`, `PatchCell`, wide text and `CoedgeNode.Pcurve` keep their Form definitions. `Complex.Authoring.ExactSubtypes.ExactCurve` is a new builder function and not the removed class.

## Corpus coverage

The study corpus has 712 F3D archives, and 582 of them contain BRep members. These give 1170 members and 1083 unique members. The [inventory](../../../../re/Fusion/Reconstruction/ComplexGeometry/InventorySummary.json) gives these active record counts.

| Record | Active records | Members |
| --- | --- | --- |
| `pcurve` | 2076 | 116 |
| `intcurve-curve` | 1242 | 112 |
| `spline-surface` | 475 | 116 |
| `tcoedge-coedge` | 16 | 2 |
| `tedge-edge` | 8 | 2 |
| `tvertex-vertex` | 8 | 2 |
| `stitch_hint-sys-attrib` | 4 | 4 |
| `vertedge-sys-attrib` | 4 | 2 |

The next table counts the outer subtype scope of each active record. Nested scopes are not in these counts.

| Subtype | Count | Subtype | Count |
| --- | --- | --- | --- |
| `exp_par_cur` | 1612 | `cyl_spl_sur` | 43 |
| `par_int_cur` | 572 | `loft_spl_sur` | 40 |
| Referenced `pcurve` form | 372 | `exact_spl_sur` | 37 |
| `exact_int_cur` | 234 | `cl_loft_spl_sur` | 10 |
| `intcurve` reference | 194 | `srf_srf_v_bl_spl_sur` | 8 |
| `spline` reference | 167 | `helix_int_cur` | 8 |
| `spring_int_cur` | 160 | `sum_spl_sur` | 4 |
| `sweep_sur` | 102 | `helix_spl_line` | 4 |
| `pcurve` reference | 96 | `g2_blend_spl_sur` | 1 |
| `int_int_cur` | 74 | `VBL_SURF` | 60 |

The [complete verification](../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyAll.json) read and re-emitted every unique member with Python 3.14. 943 of 1083 members were byte-exact. 113 of the 116 members with complex records were byte-exact. The reader at the base commit `5a7949c81` read 820 members.

| Base result | Members | Result now |
| --- | --- | --- |
| `spline-surface` entity kind | 112 | Byte-exact |
| `spline-surface` entity kind | 1 | `Oversized Fusion ASM record` |
| `intcurve-curve` entity kind | 1 | Byte-exact |
| `vertedge-sys-attrib` entity kind | 1 | Byte-exact |
| Historical reference absent or class-incompatible | 9 | Byte-exact |
| Oversized journal entity table | 13 | 8 `Oversized Fusion bulletin board`, 5 `Oversized Fusion ASM record` |

## Limits

- Three complex members are not read as a whole. `two_texts.f3d` has a history record above 4096 tokens. The `modeled_full.f3d` members of the tapped-hole and thread studies have an unsupported attribute family.
- The 379 complex records of these three members read and re-emit exactly one at a time ([records](../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyRecords.json)). All 8 `helix_int_cur` and 4 `helix_spl_line` corpus definitions are in the two `modeled_full.f3d` members. These two subtypes therefore have record-level evidence only.
- Procedural subtype bodies are positional grammar trees. Only B-spline blocks, T-spline values and loft subdata have named dataclasses.
- Kit does not evaluate procedural surfaces or curves. The authoring path writes `exact_spl_sur`, `exact_int_cur` and `exp_par_cur` only.
- Authored faces have one loop. Native acceptance covers open, nonperiodic and nonsingular B-spline surfaces only.
- `wire` records are not typed. The five members that contain them stop earlier with `Unsupported Fusion journal qualified field`.
- The entity table limit is now 4096 entities.

## Verification evidence

[Native acceptance](../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json), SHA-256 `92e56ed767afee3a0ac69583b3c6cb6d14dd04b17f145b10cef622b84e08f4f7`, has status `accepted` in Fusion 2706.1.17. Zero documents were open before and after the run. The [preparation](../../../../re/Fusion/LocalOracle/ComplexGeometry/Preparation.json), SHA-256 `e6429d77642bd10d615be946e6998a5d1737c5ce0eb10bd09cf644ab63c446a8`, binds each input and output hash.

Each authored body went through `TemporaryBRepManager` import, a persisted body, save and reopen. The values after reopen were equal to the values before.

| Body | Topology | Area (cm²) | Volume (cm³) | Native surface | Native edges |
| --- | --- | --- | --- | --- | --- |
| `AuthoredPatch`, bicubic 5×4, interior U knot | 1 face, 4 edges, 4 vertices | 7.366308780834109 | None, open sheet | `NurbsSurface` | 4 `NurbsCurve3D` |
| `AuthoredRational`, rational biquadratic | 1 face, 4 edges, 4 vertices | 11.361644058057117 | None, open sheet | `NurbsSurface` | 4 `NurbsCurve3D` |
| `AuthoredPillow`, six bicubic faces | 6 faces, 12 edges, 8 vertices | 25.0885564915581 | 10.501319359009246 | 6 `NurbsSurface` | 12 `Line3D` |

| Body | Area relative error | Volume relative error | Worst sample drift (cm) | Pole, knot and weight drift | Bounds excess (cm) |
| --- | --- | --- | --- | --- | --- |
| `AuthoredPatch` | 1.29e-9 | None | 5.24e-16 | 0 | 8.1e-5 |
| `AuthoredRational` | 8.6e-13 | None | 1.40e-15 | 0, edge poles 4.4e-16 | 2.1e-4 |
| `AuthoredPillow` | 1.43e-7 | 3.18e-8 | 1.83e-15 | 0 | 0 |

The expected values come from an independent research evaluator. The pillow centroid differs by 1.10e-8 cm. Every sample point was on its face, and each body was valid.

`EditedPatch` changes pole 4 (u=1, v=1) of a corpus `exact_spl_sur` from z 1.2 cm to z 2.0 cm. Fusion accepted it with area 6.782947284786066 cm² against 6.432285222128447 cm² for the control. The changed surface had zero pole, knot and weight drift.

Eight decoded corpus snapshots were byte-exact. Each imported as valid bodies and gave equal values after save and reopen. Six corpus histories were re-emitted byte-exact. Each control and re-emitted history went through every rollback marker, rebuild, a parameter edit, save and reopen.

| History | Subtypes other than `exp_par_cur` | Edit | Volume before edit (cm³) | Volume after edit (cm³) | Comparison |
| --- | --- | --- | --- | --- | --- |
| `LoftDirection` | `loft_spl_sur`, `exact_int_cur` | `d1` ×1.25 | 7.113009471009052 | 9.124514387086997 | Equal within 1e-8 |
| `SweepRail` | `sweep_sur`, `par_int_cur` | `d2` ×0.8 | 0.31536 | 0.26929152 | Equal within 1e-8 |
| `SolidSweep` | `sweep_sur`, `exact_spl_sur`, `par_int_cur` | `d5` ×0.8 | 143.08127683038546 | 143.24915129513576 | Equal within 1e-8 |
| `ChordFillet` | `srf_srf_v_bl_spl_sur`, `exact_int_cur`, `int_int_cur`, `spring_int_cur` | `d4` ×1.25 | 23.987122505214554 | 23.97987969406579 | Equal within 1e-8 |
| `CurvatureFillet` | `g2_blend_spl_sur`, `int_int_cur` | `d4` ×1.25 | 23.974732651090335 | 23.960519767328645 | Equal within 1e-8 |
| `RuleFillet` | `VBL_SURF`, `srf_srf_v_bl_spl_sur`, `par_int_cur`, `spring_int_cur` | `d7` ×1.5 | 37.96756373315546 | 37.95187567917283 | Relative drift 4.24e-5 against a control self drift of 5.06e-5 |

The [rule fillet gotcha](../../../Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md) explains the last row. The [native coverage](../../../../re/Fusion/Reconstruction/ComplexGeometry/NativeCoverage.json) lists the subtypes in every member that Fusion opened.

The native cases have these boundaries.

- Only the authored bodies and `EditedPatch` contain bytes that Fusion did not write. The corpus snapshots and histories are byte-identical re-emissions.
- The four fillet snapshots contain no complex records. Their complex subtypes were opened through the history members only.
- `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `cl_loft_spl_sur` and `helix_int_cur` did not occur in a native case.
- Curve references, `pcurve` references and referenced `pcurve` forms did not occur in a native case.
- Tolerant topology, stitch hints and vertex edge attributes did not occur in a native case.
- `EmitStateSmb` output for a corpus history was not opened in Fusion. In all 62 history archives it differs from the archive snapshot ([states](../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyStates.json)).

[Kernel evidence](../../../../re/Fusion/Reconstruction/ComplexGeometry/KernelEvidence.json) binds the field order to the save routines of the installed ASM kernel. It covers `exp_par_cur`, `exact_spl_sur`, `spl_sur`, `TCOEDGE`, `TEDGE`, `TVERTEX`, `ATTRIB_STITCH_HINT`, `ATTRIB_VERTEDGE` and `ATTRIB_SYS`. The current arm64 slice has SHA-256 `5ad7bc0099f1093e82f99110355ad2100b77fc47446c3d75befaaac81484d4a4`.

Remote integration cases cover the 113 byte-exact members, a stable reorder of each member, and a forward-reference reorder of each of the 62 histories. Other cases cover the 62 history states, the three boundary members and their complex records, stitch hints and vertex edges. They also cover the three authored bodies against the accepted fixtures, nine authoring faults, three guards and three subtype table cases. Local tests did not run. Black, Ruff, Mypy, Pyright and steering checks passed.

## Related information

- [Pole order](../../../Gotchas/Conversion/Fusion/Geometry/SplinePoleOrder.md)
- [End knot multiplicity](../../../Gotchas/Conversion/Fusion/Geometry/SplineEndKnots.md)
- [Pcurve sense](../../../Gotchas/Conversion/Fusion/Geometry/PcurveSense.md)
- [Subtype families](../../../Gotchas/Conversion/Fusion/Geometry/SubtypeFamilies.md)
- [Straight spline edges](../../../Gotchas/Conversion/Fusion/Geometry/StraightSplineEdges.md)
- [Snapshot feature inputs](../../../Gotchas/Conversion/Fusion/Geometry/SnapshotFeatureInputs.md)
- [Spline subtype table of Form bodies](../../../Gotchas/Conversion/Fusion/TSpline/SplineSubtypeTable.md)
