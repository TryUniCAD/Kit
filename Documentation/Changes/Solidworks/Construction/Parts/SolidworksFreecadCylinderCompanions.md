# SOLIDWORKS native companions for FreeCAD cylinders

Two disclosed FreeCAD origin cylinders now have independent SOLIDWORKS 2026 SP05.2 controls. Each native part uses a radius dimension on a Front Plane sketch and a forward blind depth dimension on its boss. Both parts reopen and rebuild after separate radius and depth edits.

On the reserved Windows oracle, use `RunCylinderCompanions.py verify PACKET --packet-sha256 SHA256` to check the frozen source inputs and tools. Its `run` mode authors, reopens and edits both sources with a known part before and after the batch. The supplied packet binds the FreeCAD source hashes and native settings.

The [native receipt](../../../../../re/solidworks/measurements/2026/FreecadCylinderNativeSources01.json) records eight distinct applications, healthy bracket controls, and 50 comparisons against analytic volume, area and centre of mass values. Each inspected state retained one solid body and no feature rebuild errors or warnings. Both native source hashes remained stable after edits. Primitive lowering and sealed source qualification remain open.
