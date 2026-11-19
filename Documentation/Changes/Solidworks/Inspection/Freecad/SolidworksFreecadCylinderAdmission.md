# Inspect complete FreeCAD cylinder source intent

The research admission auditor accepts the two disclosed full origin FreeCAD 1.1.4 `Part::Cylinder` sources through ordinary strict SDK reads. It retains the actual feature and configuration names, the reader-generated body name, all thirteen driving parameter IDs and roles, placement, metadata, payload ownership and the current analytic B-rep. It does not reduce the source to a new two-driver circle document.

The [source mapping record](../../../../../re/solidworks/records/FreecadCylinderAdmission2026.md) describes the reusable SDK circle, dimension, blind-end and metadata owners and the unresolved primitive-lowering boundary. [`CheckCylinderAdmission.py`](../../../../../re/tooling/sw2026/freecad_cylinder/CheckCylinderAdmission.py) runs the isolated process audit using pinned source and input manifests and an unused output directory.

The [receipt](../../../../../re/solidworks/measurements/2026/FreecadCylinderAdmission01.json) records thirty host SDK processes, eighteen malformed-source refusals and fifty independent comparisons with the existing native source observations. The actual preparation and normal registry refuse both unqualified complete sources without writing any native bytes. Predictions are frozen before the observation receipt is read.

No primitive writer, public admission or generated-output native acceptance is added. Independent native held-out source locks and complete mapping of the retained additional owners remain required before lowering. See the [specific source-ownership gotcha](../../../../Gotchas/Conversion/Freecad/Primitives/CylinderPrimitiveIsNotATwoParameterSketch.md).
