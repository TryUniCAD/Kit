# Bound constant-radius circular fillets

`RadiusFillet` preserves an edge-selection ID, distinct radius and tangency-weight parameter IDs, tangent propagation and rolling-ball corner mode. The existing `FilletFeature` value representation remains available. This bound definition avoids a stale copied radius when a driving parameter changes.

Import the definition from `interchange.Features.Fillets.RadiusFillet` and evaluate it with `GetFilletVals` from `interchange.Features.Fillets.GetFilletVals`. Pass the containing feature, its definition, the document parameter map and selection map. The result is radius in millimetres and dimensionless weight. JSON registration preserves the concrete definition through `CadDocument.from_json`.

The current qualified boundary is one upper circular rim of an existing canonical XY, positive untapered blind create extrusion. It requires one preceding feature, one shared final output body, a closed origin-centred circle, exact selected-edge query, owned driving parameters, unit tangency weight and enabled tangent/rolling-ball modes. Broken body/profile/dependency/selection references, nonfinite or nonpositive values, unsupported units/modes and a nonfitting radius refuse document validation.

All 22 recorded source archives read and JSON-restore with their original radius/weight owners. Their offline neutral radius edits agree with retained native edit/restoration measurements. Fifty malformed restored-document and CLI process cases exercise the reference, profile, value and history guards. These checks do not establish a new native writer or target acceptance; source fillet documents remain read-only.

[Reader contract and exact evidence](../../Fusion/Readers/FusionCircularRimReader.md)
