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
success and cannot become donor output. Native execution is pending.

The API describes [feature suppression actions](https://help.solidworks.com/2025/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFeatureSuppressionAction_e.html?id=e3d74be662f645ae8bcdec1c4eec3498)
and [configuration scope](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swInConfigurationOpts_e.html).
The exact 2026 runtime result is retained rather than inferred from the API documentation.
