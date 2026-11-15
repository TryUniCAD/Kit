# Observe native feature unsuppression

The research observer accepts `ExerciseUnsuppression.py` as an explicit action on
a copied part. It records the original feature states and geometry, asks the
vendor API to unsuppress ordinary sketches and extrusions in the active
configuration, rebuilds, and records the result. It never requests a save.

Use the existing `Observe.py --action-script` interface with the retained
goal-owned controller and an explicit copied `--action-input`. The report keeps
stages and partial results even if a later operation fails. Exact application
identity and a healthy control remain required.

This is a diagnostic intervention, not writer acceptance. Geometry obtained
after an oracle changes suppression state does not count as generated-file
success and cannot become donor output.

The [controlled diagnostic](../../../re/solidworks/v2026/evidence/TupniUnsuppression.json)
passes its original control. On the generated candidate, both explicit API
unsuppression requests succeed, and rebuild produces one solid with volume
`9.932000000000002e-6 m³`, area `0.003166276360558158 m²` and center
`(0.006666666666666669, 0.007000000000000002, 0.0065) m`, without feature
errors or warnings. Both input hashes remain unchanged. This confirms the
diagnostic effect; native acceptance still requires a fresh generated file
that regenerates without this intervention.

The API describes [feature suppression actions](https://help.solidworks.com/2025/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFeatureSuppressionAction_e.html?id=e3d74be662f645ae8bcdec1c4eec3498)
and [configuration scope](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swInConfigurationOpts_e.html).
The exact 2026 runtime result is retained rather than inferred from the API documentation.
