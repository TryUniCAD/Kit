# Fusion-saved constrained cuboid round trip

## Scope

Task A05c-FusionSavedCuboid20261125 follows the bounded constructor round trip in PR #297. It covers the positive XY cuboid that Fusion saves with four horizontal or vertical rules, two driving dimensions and one fixed rectangle corner. The separate sketch origin can occupy the same coordinates as the fixed corner. Their identities and roles remain distinct.

## Established observations

The [one-factor constraint capture](../Reconstruction/SketchConstraints/ConstraintModel.md) measured the assignment of the corner's fixed property. It left the geometric-rule count at four. The corner's stored `Point3D.isFixed` became true and remained distinct from the fixed origin. All four rectangle points kept their original per-point `isFullyConstrained` flags even when Fusion reported the entire sketch fully constrained.

The public reader at `c4e8a34186bdd173dad37d843b79bc8a3a59ebb9` refused all 12 available saved controls, edits and restores in this cohort. Its constrained-rectangle branch requires a fifth geometric-rule record. The lower document codec reads all 12. Each model records one typed prism history, one prism snapshot, two empty configuration parts and a graphics scene. The native files carry four geometric rules and two dimensions, plus both fixed points.

[AuditSavedArchive.py](AuditSavedArchive.py) measures the typed wire round trip with the production document codec. Provide one or more `--group BEFORE EDITED RESTORED` triples and an unused `--report` path. Run it from a checkout with the matching Kit SDK available to Python. It reads the three files independently, compares their member hashes after decompression, and reports positional typed differences between native saves.

The first run covered four groups and 12 archives from Fusion 2706.1.17. All 12 retained complete typed-model equality and the same 30 named ZIP members after re-emission. Each had three changed member digests, for the BRep history, BRep snapshot and material package. The Design segments, configuration parts, graphics world and mesh streams, and preview members retained their own original decompressed content. The aggregate codec measurement was 5.064 seconds, with a 0.295–0.679 second range across archives. The local report SHA-256 was `b023ada54e4dba356d195a1a458365c21bee2e995f1ee79337ab6bedeb66da93`.

For example, the saved edit with SHA-256 `1e7584c59f898b41af2ea3d5accf0c5c44e793bcd0ab7c5486a08feb55443aa2` re-emitted as `3d1d056e5f263e414759eae82f0f869bd22b6867cc5fdcc02cc5bc0851bbe3e5`. It retained its complete decoded model. A native receipt for the input or for an earlier constructor candidate cannot establish acceptance for those new bytes.

## Display bounds can retain the previous height

All eight native edited and restored saves in the reached groups had a 12-edge, six-face solid display node whose aggregate `BrepWorld.ModelBox` kept the previous height. For example, a 28.3 mm saved solid carried a 13.8 mm graphics Z bound and its 13.8 mm restored solid carried a 28.3 mm graphics Z bound. The typed snapshot and BRep history both followed the current dimensions. Four restored saves also carried a zero-height sketch display node. The 12 zero-LOD edge bounds and six zero-LOD face bounds already match the current solved geometry exactly in each save. The aggregate bound and its child bounds therefore have separate dependencies. Graphics references remain part of the saved graph, while current body dimensions come from modeled geometry. The audit reproduces the eight aggregate mismatches and sixteen exact child bound sets. The local follow-up report SHA-256 was `b1010d02290e4cc50c1f2bec289f161507e14bdaee711e12f97f4a6258686315`.

## Analytic height prediction

[PrismFramePrediction.py](PrismFramePrediction.py) takes native edited and restored `--pair BEFORE AFTER` inputs. It uses the target driving value from Design and predicts both solid frames from the original topology. It moves the four upper corners, the four top horizontal edge origins and the top plane origin. It changes each positive vertical edge's upper parameter with its unit carrier direction preserved.

Four prior native edit and restore pairs gave eight exact frame matches, covering the history and snapshot for each pair. The existing prism frame guard independently validated every predicted frame. The four restored extrusion values were 13.8 mm, 22.6 mm, 22.6 mm and 31.4 mm. This experiment predicts analytic geometry only. It does not emit a modified document.

The scalar search isolated the same three height values in each of the eight edited and restored Design graphs. The user driver, owning model parameter and `DcDoubleParameter` each store the value in centimetres. The body cache stores the corresponding volume, area and centroid. The holdout's procedural wood mapping carried a nonzero origin at the previous centroid across a native edit; the baseline mapping stayed at zero. That contrast requires a material/display ownership rule before an edited archive can be qualified.

## Height-edit dependency map

| Dependency | Existing evidence | Open measurement |
| --- | --- | --- |
| Driving user value and expression, owning model parameter, and numeric extrusion field | Native Design references connect the four parameter slots and three user drivers. Slot allocation changes across saves. | Measure changed and unchanged values by owning reference in same-document native exports. |
| Solved BRep history, prism snapshot and mass cache | The codecs verify the closed cuboid, carrier endpoints, identity joins and exact typed equality. The mass checks use the cuboid volume, centroid and inertia tensor. | The analytic solid frame matches eight of eight. Recompute the mass cache and verify the complete candidate and stored associations. |
| Graphics body bounds and draw data | The scene codec interprets typed entity links and mesh data. Every original graphics member re-emits byte-identically in the unchanged audit. | Isolate depth-dependent fields from camera, visibility and ordinary export variation. |
| Configuration, preview and material state | Two empty configuration sidecars remain bound to their Design references. All contents remain present in the unchanged decoded model. | Determine which preview and display fields change on a height edit and whether Fusion regenerates them. |

The large positional differences between separate native exports include identity allocation and ordering changes. This report does not assign those differences to the depth parameter. Use same-document repeats and one-factor controls with application measurements before coding an edit rule. The existing typed re-emission supplies a wire-level starting point. The edited JSON writer and native qualification remain pending.
