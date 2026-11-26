# Saved Fusion cuboid parameter bindings

The research commands preserve the parameter names, order and feature bindings of a strict saved fixed-corner cuboid. They write a narrow semantic JSON request and build a new cuboid snapshot from that request. The generator needs the JSON file as its only document input.

## Use

Run the commands from a checkout with Python 3.14 and the checkout SDK on `PYTHONPATH`. Choose new output paths.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedParameterBindings/PrepareRequest.py Original.f3d Request.json
python -B re/Fusion/SavedParameterBindings/GenerateSavedCuboid.py Request.json Candidate.f3d
```

The request carries the three user drivers and four model parameters in saved table order. It retains each parameter's name, expression, unit, value and identified owner role. The generator creates its own object identities and reconnects the named parameters to the correct sketch or extrusion. See [why names alone cannot determine roles](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionModelParameterRoles.md).

Both commands refuse an occupied destination and print JSON receipts. The first receipt records the source and request hashes. The generator reports the request, candidate and generated snapshot hashes, analytical volume and strict SDK checks.

## Verification

Fresh CLI processes prepared and regenerated all four [saved cuboid controls](../../../../re/Fusion/SavedCuboidRoundTrip/Corpus) after the staged source files were removed. The generated candidates passed strict version-2 readback, public JSON round-trip and exact lower typed re-emission. The two measured parameter families kept their seven ordered rows, dimensions, extrusion and taper references, with a matching analytic cuboid and generated snapshot. The edited control produced byte-identical output in a second fresh process using a different destination name.

| Saved case | Generated archive SHA-256 |
| --- | --- |
| Baseline control | `0354dc762ab7dd2ef4f196e5be42c6aa0da2bb53e3bd596e463ba9b3e4604869` |
| Baseline edit | `7d9b710f9ce3cc2aa8879364ca49469952c5cfc5c35c7b3de860b1e8970b2718` |
| Baseline restore | `226d82f642160de71608aef13dcd217f18ada1daaf8db5d674dd981fe23e3505` |
| Held-out control | `7608aee633b7117cde73ca4c8a0c27e8ec169783b6b5fdc372ab2e1aad7b12b5` |

The saved-cuboid compatibility roster passed all 55 cases across two runs. The first run passed 54 cases in 113.54 seconds. Its missing sparse-checkout fixture was restored and the remaining case passed in 5.69 seconds. The parameter cases use the normal process and fixture boundaries in that roster. Separate CLI checks refused a foreign archive field, a formula, a mismatched model and driver value, duplicate roles and a nonzero taper. Both commands preserved occupied destinations.

## Limits

The commands qualify the parameter graph of one positive fixed-corner cuboid with two driving dimensions and a one-sided extrusion. The request describes the title, feature and body names, basic material label, density and color. The experiment leaves named views, visibility, graphic and preview state, configured designs and detailed material assignments unfinished. Its output retains strict version-2 read-only metadata. It has no new native Fusion verification or production writer admission.
