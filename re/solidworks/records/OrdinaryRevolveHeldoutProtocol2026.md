# Preregistered held-out method for ordinary revolved bosses

This method covers `RevolveHeldoutFirst` and `RevolveHeldoutSecond` from the [ordinary revolve source lock](../v2026/heldout/OrdinaryRevolveSourceLock.json). The published lock's SHA-256 is `bf4a857b222a9ea61d5d74007fbde4090d95d1563aa8025de3b01454e1839b2f`. The private specification digest recorded in it is `35a3af9a5195b1c723d7a2e08f370465c016923cff3e07b625cccaf08314cccc`. This protocol was prepared while the two parameter sets and detailed measurements remained sealed. It tests partial one-direction sweeps. The full turn is a separate discovery case.

## Freeze and disclosure

1. Use the generator tree at `cd0cf5738f074ac9d4fe44490db2bb89cc18dfe6`, tree `efc6a8f176e7859e5d79069a707a462c259eb4b7`, which produced the three [measured clean discovery parts](../measurements/2026/GeneratedRevolveSketchLog02.json). Reproduce their candidate hashes with the frozen disclosed requests. The selected profile reference uses the no-log creation time, and the cold axis-cache wrapper remains as measured. [Load causality](OrdinaryRevolvedBossLoad2026.md).
2. Before disclosing held-out parameters, complete an edited save and fresh reopen of the disclosed generated parts. Record the generator revision and tree, this protocol's digest, source lock and private specification digests, the final oracle scripts and fixture digests, and the exact acceptance and output-path arguments. Pin the manifest before revealing the cases. Use `SldWorks.Application.34`, executable `34.5.2.0604` with SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`, and the source lock's known-good control.
3. After freeze, the oracle owner verifies the private specification digest before selecting the two locked `heldout` rows. The authored request fields are the input to neutral prediction. Keep native files, saved archive fields, and measured outcomes sealed from the generator and comparator until the generated files and analytic predictions are hashed. Verify the sealed native file and phase receipt digests against the lock before using them for comparison. The writer has no source-file path in its request.

## Neutral request mapping

Use the frozen `MakePartInput` fixture for provenance, degree presentation, date code `2026306` and Parasolid behavior `370108`. Apply the independently established `MakeTreeInput` folder names, annotation cabinet and single markup owner. Use the standard active configuration `Default`. The three disclosed native revolve controls use the standard 19-node feature tree. `RevolveFull` reports the active configuration `Default`. The updated neutral presentation supports ordered source-to-generated tree comparison. Verify the presentation against the disclosed native cases before revealing either held-out input. [Neutral request](../../../tests/Convert/Solidworks/Research/FreshPartInput.py) and [native English tree presentation](../../../tests/Convert/Solidworks/Research/Presentation/MakeTreeInput.py).

Give each generated part the stem `Kit` concatenated with the locked source case name, with the same generated stem in `document.name`, the COM request and its explicit `.SLDPRT` output path. Preserve the original locked name in the comparison receipt. Choose a dedicated external staging directory before freeze, and form the candidate path from that directory and its stem. Set `saved_at = modified_at + 1` as in the disclosed generation. [Prediction tool](../../tooling/sw2026/PrepareRevolvePredictions.py).

For a case with `axis_x_m = x0`, `radius_m = [ri, ro]`, `axial_m = [lo, hi]`, and `axis_axial_m = [a0, a1]`, the part request contains these semantic fields:

| Field | Value |
| --- | --- |
| `feature_kind` and `profile_kind` | `revolve` and the default polygon shape |
| `sketch_name` and `revolution_name` | `RevolveSketch` and `OrdinaryBossRevolve`, following the source authoring protocol |
| `vertices_m` | `[[x0 + ri, lo], [x0 + ro, lo], [x0 + ro, hi], [x0 + ri, hi]]` in order, with closure derived by the builder |
| `axis_start_m`, `axis_end_m` | `[x0, a0]`, `[x0, a1]`, preserving the source centerline's endpoint order |
| `angle_rad` | `math.radians(case["angle_deg"])`, always positive |
| `reverse_direction` | The source Boolean `reverse` |
| `plane_axis` | `z` for `front`, `y` for `top`, `x` for `right` |

Remove the fixture's placeholder extrusion name and depth. Pass the authored edit separately to the oracle as `math.radians(case["edit_angle_deg"])`. The original five-case validator supplies the domain constraints, including positive radii, ordered upright axis and a strict partial sweep in both held-outs. [Source authoring contract](OrdinaryRevolvedBoss2026.md#source-and-acceptance-sequence).

## Frame and signed predictions

The canonical sketch has zero origin. With the following model-space unit basis `(u, v, n)`, convert sketch coordinates to model coordinates as `x*u + y*v + z*n`. The model-to-sketch map takes the three dot products with the same basis. Check the reopened native source and generated model frames against this common expectation.

| Plane | `u` | `v` | `n = u × v` |
| --- | --- | --- | --- |
| Front | `+X` | `+Y` | `+Z` |
| Top | `+X` | `−Z` | `+Y` |
| Right | `−Z` | `+Y` | `+X` |

The one-direction request uses the archival/COM mode `0`. The checked full and partial discovery observations establish the direction relative to the stored endpoint order. For partial sweeps, the transverse coefficient uses `sigma = -1` for forward and `sigma = +1` for reverse. Freeze that sign before disclosure and compare each phase directly to its signed target. The native inspector's reported `forward_handedness` is `-1` for both direction flags when the selected direction matches this rule.

For `theta = angle_rad` or the independently authored edit target, `h = hi - lo` and `d = ro² - ri²`, predict one solid, volume `h * theta * d / 2` and area `h * theta * (ri + ro) + theta * d + 2 * h * (ro - ri)`. With `q = 2 * (ro³ - ri³) / (3 * theta * d)`, the sketch-space centroid is `(x0 + q*sin(theta), (lo + hi)/2, sigma*q*(1 - cos(theta)))`. Map it to model space with the proved basis. Apply relative tolerance `2e-7` to positive volume and area and `2e-7` relative or `1e-10 m` absolute to each center coordinate. Record six-significant-digit values alongside the full measurements. Use the disclosed source protocol's numeric rules for unchanged sketch and angular values.

## Measurements and evidence

1. Generate each archive in an isolated process from the neutral request. Require all nine modeled stream round trips and zero tails, a clear runtime file-access audit, exact selected profile, line and angle identities, and a valid frame. Hash each generated file, request, reference expectation, and process receipt before reading semantic reference measurements.
2. Inspect the original candidate in its own native process between fresh healthy controls. Enable `inspect_before_rebuild`, `inspect_profile` and `verify_saved_edit`. Record open status and any dialogs, the first observable body count and feature tree, a clean explicit rebuild, and the post-rebuild geometry. Verify the single ordinary boss, its consumed profile containing the exact four perimeter segments and selected construction line, axis endpoints and frame, requested direction and positive `D1` angle. Match the analytic targets and the independently locked native reference metrics in the common frame. Compare ordered names, native types, suppression and rebuild flags before and after the edit. For a dimension's fully qualified name, normalize only the known source or candidate document suffix and compare the remaining feature-qualified name and driving value.
3. Locate the existing driving angular display, edit `D1`, and require a clean rebuild and the corresponding signed geometry. Verify document preference restoration. Save the edited document to a separate owned path and keep the candidate digest immutable. Close the process and open the edited copy in a different process. Require a clean reopen, one solid, the same feature ownership and edited driving value, and the expected edited geometry after rebuild. Keep both edited save and reopening receipts with the baseline.
4. Retain the original and edited tree measurements, all errors and warnings, exact paths and hashes, numeric comparisons, before and after controls, application identity, and distinct process creation identities. Publish evidence with private host paths scrubbed. Record each failed phase as a failure, and discard a batch if either control fails. The accepted discovery or held-out result is bounded to the feature scope and exact revision exercised. [Comparison tool](../../tooling/sw2026/CompareRevolvePredictions.py) and [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
