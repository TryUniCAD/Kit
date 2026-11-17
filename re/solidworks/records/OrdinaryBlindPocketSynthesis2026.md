# Ordinary SOLIDWORKS 2026 blind-pocket discovery

Confidence is **partial**. This experiment constructs the two sketches and two features from new dimensions and explicit body-scope choices. Both choices start with the cut's constructor body state. The usability of that state after opening a generated file remains unmeasured.

## Inputs and ownership

The request extends an ordinary Front Plane rectangular blind-boss request with a `blind_cut_discovery` mapping. The mapping contains `sketch_name`, `feature_name`, `center_m`, `radius_m`, `depth_m`, `dimension_text_point_m`, and `scope`. The centre is a 2D sketch coordinate. The dimension text is a 3D point in the same plane. The circle lies strictly inside the rectangle with a different centre. Its positive cut depth is smaller than the boss depth. The request has one part, one configuration, one body-producing boss, and one pocket.

The [shared part composer](../../tooling/sw2026/builders/Part.py) allocates the four user roots in dependency order, from the boss sketch and boss to the pocket sketch and cut. Both sketches use the same principal plane and own separately constructed reference wrappers. Both profile dependencies point to the actual sketch objects. Each feature's `D1` owns a separate length parameter. The pocket sketch also owns a fixed-centre constraint and a driving radius on its single circle. The existing configuration progress, map handoff and container builder process the complete graph after all nodes are allocated. [Fresh composition](FreshPartComposition2026.md) · [fixed circle boss construction](CircleExtrusionSynthesis2026.md).

| Owner | Rule | Classification |
| --- | --- | --- |
| Cut profile and radial value | Centre and radius supply the shared circle model. Separate centre and seam roles yield one closed arc. The existing fixed-centre constraint and radial handle target those actual roles. | Authored geometry and derived topology |
| `moICE_c.f28`, `f810`, `f838` | Preserve inherited node flags and the `0x40 \| 0x100` extrusion mask, then add `0x2 \| 0x8 \| 0x80 \| 0x20000`. The cut operation is `1`. The typed extrusion constructor starts `f838` at zero. | Composed flags, operation vocabulary and constructor value |
| `moEndSpec_c` | Forward driver `f18` is the actual cut `D1` display. Single blind direction uses `f08=1`, `f0c=f10=f88=0`, `f8c=1`. The inactive reverse and draft displays are null. The start comes from the sketch plane and uses `f140.t=0`. The capped mid-plane surface field `f158` is inactive and starts at zero. | Authored depth, derived display, and bound end vocabulary |
| `moAtomFeature_c.f544` | The caller explicitly chooses `all_bodies` (0) or `empty_feature_scope` (1). The latter describes the persisted scope word with absent selections. | Authored discovery conditions |
| `moAtomFeature_c.f528/f530/f538/f548`, output IDs and chooser fields | Absent constructor body and chooser state. `f558` is runtime state without a field in this wire branch. The experiment supplies neither a guessed atom ID nor a body chooser row. | Constructor-state hypothesis for the generated cut's cold rebuild |
| KeyWords | The `Extrusion` element omits `Type`. Its child ID comes from the cut profile and its single `D1` text comes from the actual cut parameter converted to the selected document length unit. | Derived metadata |

The [2026 cut record](OrdinaryBlindCutConstruction2026.md) binds the constructor, operation mask, end flag and selected-body lifecycle. The [scope gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/FeatureScope/AutomaticBodyScopeHasRuntimeState.md) explains why the empty scoped condition remains an experiment.

## Structural process checks

The two requests use the same independently authored inputs and differ only in their scope argument. Each uses the strict construction file/process audit and the actual container writer and reader. The process compares eight complete binary streams, consumes a linked Config-0 seed, and checks the resulting object identities, profile geometry, cut display/parameter chain, wire flags, configuration progress, and keyword dependency. It compares sibling primary stream hashes and requires only ResolvedFeatures to differ, with equal map counts and byte lengths. Both passed locally on Python 3.11. Results report `body_scope_qualified=false` and `vendor_acceptance=unverified`. Remote execution is pending. [Process receipt](../measurements/2026/GeneratedBlindPocketProcess01.json).

## Ordinary COM discovery

Freeze the input, generator revision and generated file hash for each sibling. Use the existing qualified control before and after the two generated candidates. For this batch use SOLIDWORKS 2026 SP05.2 executable `34.5.2.0604`, SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`, and the ordinary prism control SHA-256 `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`. Use fresh owned processes and the ordinary COM inspector. Retain the initial open result and body/tree queries before an explicit rebuild, then check zero rebuild errors or warnings, one visible solid, and the ordered two-sketch/two-feature history. Verify rectangle and circle dimensions, separate profile dependencies, shared frame, inside blind cut and the cut's driving `D1@BlindPocket`. Compare the numerical values below to six significant figures.

With rectangle area `A` and perimeter `P`, circle radius `r`, boss depth `B`, and cut depth `d`, the remaining volume is `A*B - pi*r*r*d`. Surface area is `2*A + P*B + 2*pi*r*d`. Compute the centre by subtracting the removed cylinder moment from the original rectangle prism moment and dividing by remaining volume. On this front frame the axial coordinates of the prism and cylinder centroids are `B/2` and `d/2`.

| Geometry | Volume (m³) | Area (m²) | Centre of mass (m) |
| --- | ---: | ---: | --- |
| Uncut boss | 3.9928868e-5 | 0.00828928 | (-0.0026, -0.0024, 0.00785) |
| 0.00483 m pocket | 3.93054015869e-5 | 0.00848380930207 | (-0.0027951038934, -0.00232227568474, 0.00793621054152) |
| 0.00831 m pocket | 3.88561959725e-5 | 0.00862396706008 | (-0.00293955629491, -0.00226472960609, 0.00795200491949) |

For a healthy initial result, save to a separate path, reopen in a fresh process, edit the cut depth to 0.00831 m through its driving parameter, and rebuild. Verify that the boss depth, circle, centre, frame and dependencies survive. Save the edited result and reopen in another fresh process. Compare the final geometry and query the driving parameter. Preserve candidate and control hashes and all load, rebuild and edit results.

If the all-bodies sibling passes and the empty scoped sibling keeps the uncut geometry or reports rebuild errors between healthy controls, the observed difference isolates the chosen persisted scope encoding on this input. If both pass, both cold encodings work on this input. COM results alone leave the internal route that selects bodies unresolved. If both fail or either control fails, this batch gives no discriminator. These generated discovery cases carry no held-out or production coverage.
