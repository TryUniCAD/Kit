# Bind the complete FreeCAD cylinder property semantics

The source-only [record](../../../../../re/solidworks/records/FreecadCylinderPropertySemantics2026.md) and [typed classification](../../../../../re/solidworks/records/FreecadCylinderPropertySemantics2026.json) bind the disclosed thirteen-parameter cylinder envelope to the exact public FreeCAD 1.1.4 revision used to author it. Five properties are geometric inputs. The two prism angles create oblique displacement; labels and visibility are metadata, and inactive attachment fields retain authored state and restore semantics.

The [offline auditor](../../../../../re/tooling/sw2026/freecad_cylinder/AuditCylinderSemantics.py) checks thirteen pinned public source files, all twenty-six scalar owners and twelve nonscalar owners across the two declared strict documents. Supply the exact cached public sources and disclosed current neutral files, then choose a new output path:

```sh
python re/tooling/sw2026/freecad_cylinder/AuditCylinderSemantics.py \
  --record re/solidworks/records/FreecadCylinderPropertySemantics2026.json \
  --source-root /path/to/PinnedFreecadPublicSources \
  --case-a /path/to/CurrentNeutral/CylinderA.json \
  --case-b /path/to/CurrentNeutral/CylinderB.json \
  --output /unused/path/CylinderSemanticsAudit.json
```

The [receipt](../../../../../re/solidworks/measurements/2026/FreecadCylinderPropertySemantics01.json) binds deterministic repeat evidence. No source or writer behavior changes, CAD launches, held-out reads or target output bytes. Nonzero prism angles, partial sweeps, active attachment and native primitive lowering remain unqualified. The [gotcha](../../../../Gotchas/Conversion/Freecad/Primitives/CylinderScalarRolesDoNotIdentifyGeometryDrivers.md) explains why generic decoded driving roles do not authorize dropping fields or turning metadata into dimensions.
