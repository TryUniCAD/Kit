# Draft section for the Fusion data model: complex surface geometry

This draft is for a new section after "Authored round bodies and trimmed round histories" in `Documentation/Reference/Research/FusionDataModel.md`.
The section text starts at the next heading.
Links are relative to `Documentation/Reference/Research/`.
The draft also proposes one row for the tag table in "ASM envelope".

| Tag | Observed payload | Interpretation |
| --- | --- | --- |
| 8 | Unsigned 16-bit length and UTF-8 bytes | String token above 255 bytes |

## Complex surface geometry and explicit NURBS bodies

Spline surfaces, interpolated curves and parameter-space curves are subtype scopes inside ordinary ASM records.
Kit reads and writes them in the typed journal codec.
It also authors explicit NURBS sheets and closed solids.
The [complex geometry entry](../../Changes/Fusion/Geometry/FusionComplexGeometry.md) gives the API, the limits and the native acceptance.

### Record kinds

| Entity | Subtype slot | Other fields |
| --- | --- | --- |
| `spline-surface` | `surface` | Reversal flag, four optional parameter bounds |
| `intcurve-curve` | `curve` | Reversal flag, two optional parameter bounds |
| `pcurve` | `pcurve` for form 0 | Form, reversal flag, U and V offsets |
| `tcoedge-coedge` | None | Coedge fields, parameter range, curve reference, curve form, inline curve, stamp |
| `tedge-edge` | None | Edge fields, tolerance, save version, stamp |
| `tvertex-vertex` | None | Vertex fields, sentinel, two tolerances, stamp |
| `stitch_hint-sys-attrib` | None | System attribute links, three doubles |
| `vertedge-sys-attrib` | None | System attribute links, count, edge pointer and version-gated integer pairs |

A `pcurve` of form -2, -1, 1 or 2 has no subtype scope.
It names an `intcurve-curve` record that holds the parameter curve.
In the corpus, negative forms occur only on reversed coedges and positive forms only on forward coedges.
A coedge record keeps a pointer to its `pcurve` record, and -1 means no pcurve.

### Subtype grammar

A subtype scope opens with tag 15 and a name and closes with tag 16.
The name selects a fixed field sequence.
The sequence can contain nested subtype scopes, B-spline blocks and optional fields.
Every field of the 113 byte-exact corpus members is consumed by a typed rule.

| Family | Subtype names |
| --- | --- |
| `surface` | `exact_spl_sur`, `cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `sweep_sur`, `loft_spl_sur`, `cl_loft_spl_sur`, `srf_srf_v_bl_spl_sur`, `VBL_SURF`, `g2_blend_spl_sur`, `t_spl_sur` |
| `curve` | `exact_int_cur`, `par_int_cur`, `int_int_cur`, `spring_int_cur`, `helix_int_cur` |
| `pcurve` | `exp_par_cur` |
| `subtrans` | `t_spl_subtrans_object` |

Every corpus subtype except `helix_int_cur` and `helix_spl_line` contains at least one B-spline block.
In `exact_spl_sur`, `exact_int_cur` and `exp_par_cur`, the B-spline is the definition itself.
In the procedural subtypes, B-spline blocks are approximations or nested definitions beside the defining data.
The installed kernel save routines give the field order of `exp_par_cur`, `exact_spl_sur` and the shared `spl_sur` data.
The [kernel evidence](../../../re/Fusion/Reconstruction/ComplexGeometry/KernelEvidence.json) records each routine and its address range.

### Subtype references

A `ref N` scope indexes one table for the complete stream.
Each inline definition adds one entry in pre-order, and a reference adds none.
The target is always earlier in the stream.
The slot sets the family of the target, but not its subtype name.
A surface slot of the corpus names nine different surface subtypes.
The [reference targets](../../../re/Fusion/Reconstruction/ComplexGeometry/SubtypeTargets.json) give the counts.

An entity permutation must renumber every reference.
A subset of entities must inline each definition that it no longer contains.
An order that puts a reference before its definition cannot be written.
The [subtype family gotcha](../../Gotchas/Conversion/Fusion/Geometry/SubtypeFamilies.md) gives the workaround.

### B-spline blocks

| Item | Stored form |
| --- | --- |
| Header | Rational form, degrees, closure and singularity codes |
| Knots | Distinct values with their multiplicities |
| Clamped end | Multiplicity equal to the degree |
| Pole count | `sum(multiplicity) - degree + 1` in each direction |
| Surface poles | V rows, with U changing fastest inside each row |
| Weights | Separate from the Euclidean poles |
| Surface rational form | `both`, `u` or `v` |

The Fusion API uses p+1 end copies and a U-major pole order.
The [end knot gotcha](../../Gotchas/Conversion/Fusion/Geometry/SplineEndKnots.md) and the [pole order gotcha](../../Gotchas/Conversion/Fusion/Geometry/SplinePoleOrder.md) give the conversions.

### Pcurve sense

A pcurve runs on the edge range when the coedge and pcurve reversal flags agree.
It runs on the negated edge range when they differ.
The [pcurve sense gotcha](../../Gotchas/Conversion/Fusion/Geometry/PcurveSense.md) gives the corpus counts and the exceptions.

### Corpus coverage

712 study archives contain 1083 unique BRep members.
116 of them contain complex records, and 113 of them round-trip byte for byte.

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

The three other members stop on an oversized history record or an unsupported attribute family.
Their 379 complex records read and re-emit exactly one at a time.

### Native evidence

Fusion 2706.1.17 accepted three authored NURBS bodies, one typed pole edit, eight byte-exact snapshots and six byte-exact histories.
The authored bodies reported `adsk::core::NurbsSurface` faces with zero pole, knot and weight drift.
The closed authored solid had a volume relative error of 3.18e-8.
Fusion reported its straight cubic edges as `Line3D`.

Fusion did not repeat its own rebuild of a rule fillet.
Two control runs differed by a relative 5.06e-5.
The [rule fillet gotcha](../../Gotchas/Conversion/Fusion/Geometry/RuleFilletRebuildDrift.md) gives the comparison rule.
The `.smb` snapshot of a fillet archive holds the bodies before the fillet.
The [snapshot gotcha](../../Gotchas/Conversion/Fusion/Geometry/SnapshotFeatureInputs.md) gives the measured bodies.

### Boundaries

Procedural subtype bodies are typed as positional grammar trees.
Kit does not evaluate procedural surfaces.
The authoring path writes exact B-spline subtypes only, with one loop per face.
`cyl_spl_sur`, `sum_spl_sur`, `helix_spl_line`, `cl_loft_spl_sur`, `helix_int_cur`, tolerant topology and both system attributes have byte-level evidence only.
Curve and pcurve references and the referenced pcurve forms also have byte-level evidence only.
