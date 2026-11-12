# Sphere and torus persistence research

Owned native sphere and torus controls now bind analytic geometry, native SMT text, F3D binary snapshots and installed kernel serialization instructions. This is research evidence, not a new production carrier or independent native writer claim.

[The capture](../../../../re/Fusion/LocalOracle/RoundCarriers/Capture.json) creates one sphere and two tori through the native temporary-BRep API, then persists them in direct-design documents. Each has one face, zero edges and zero vertices. A closed periodic surface can therefore bound a valid solid without explicit trim loops. A polygon-only Euler check cannot classify such a model.

[The named field inventory](../../../../re/Fusion/Reconstruction/RoundCarriers/Evidence.json) covers 28 sphere/torus records in 16 initial geometry tables across 11 archives, including the four new controls. It retains the complete field sequences and the accompanying transform records. The capture/evidence scripts and compressed instruction excerpts are adjacent to their reports. Native SMT files are retained byte-exact in `.smt.xz` artifacts, including their original trailing spaces; `NativeText.json` binds compressed and uncompressed hashes.

After the common attribute reference, entity tag and reserved reference, a sphere stores center, signed radius, reference direction, pole direction, V reversal and four optional parameter bounds. Native `sphere::save_data` at `0x445300` and `restore_data` at `0x445374` establish that exact order. The object offsets are center `0x40`, radius `0x58`, reference direction `0x60`, pole direction `0x78` and reversal `0x90`. The two directions and sense are present for save versions at least 10300. The installed version is 23200.

The native evaluator at `0x442d94` uses latitude `u` and longitude `v`:

`p = center + abs(radius) × [sin(u) × pole + cos(u) × (cos(v) × reference + sign × sin(v) × (pole × reference))]`

Here `sign` is −1 for reversed V and +1 otherwise. Signed radius remains a distinct stored field; this position equation does not by itself qualify orientation semantics for every signed-radius case.

A torus stores center, axis, major radius, signed minor radius, reference direction, V reversal and the same four optional bounds. Native save/restore addresses are `0x47d3f4` and `0x47d470`. The signed minor radius must not be normalized away. General horn/spindle/self-intersecting parameterizations remain outside this research qualification.

The native sphere radius 1.7 cm has volume 20.579526276115537 cm³. Native tori with major/minor radii 2.3/0.7 cm have volume 22.246088320055406 cm³. The tilted axis `(0,0.6,0.8)` and an explicitly translated axial control preserve center `(1.1,-0.7,0.5)` cm. The first axial API call unexpectedly returned an origin-centered torus; the [specific API gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionTorusPlacement.md) records that discrepancy and its measured workaround. No format rule is inferred from the unsuccessful placement request.

No local tests ran. All observations came from owned native captures and read-only binary/archive inspection. Product readers, writers and native acceptance for independently generated sphere/torus bodies remain separate work.
