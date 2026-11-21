# Inspect native depth edits and saved-copy reopening

`re/tooling/sw2026/InspectEdit.py` accepts a JSON job and report path for clean
vendor inspection. A job names an original control and copied generated part
cases, each with a new output destination, native parameter name, positive SI
depth and independently derived before/after body, volume, area and center-of-mass
expectations. The expected metric groups use `bodies`, `volume`, `area` and `com`.

For each case it opens the generated part, records the baseline, edits the depth
through COM, rebuilds, saves to the distinct destination and reopens that saved
copy in a fresh application process. It retains stages, exact oracle executable
identity, native error status, parameter readback, feature status, hashes and
geometry. The original generated input must remain unchanged. Existing output
destinations are rejected.

Metric comparison uses relative tolerance `5e-7` with absolute tolerance `1e-15`
for near-zero coordinates. A passing result requires healthy controls before and
after the cases, baseline and edited geometry matches, parameter readback, clean
save/reopen and unchanged original inputs. This covers only the selected polygon
blind-extrusion family and depth edit. It does not enable production writing or
establish any other feature-family acceptance.

The [controlled three-case batch](../../../../re/solidworks/measurements/2026/PolygonDepthEdits.json)
passes all baseline, depth-edit, save and reopen checks with healthy controls,
unchanged original inputs and zero errors or warnings on build `34.5.2.0604`.
The [measurement entry](../SolidworksPolygonNativeMeasurements.md) records the
exact scope and limits.
