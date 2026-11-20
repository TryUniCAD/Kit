# Fusion sketch geometry membership

The research reader compares each projected sketch's primitive backlinks with its saved managed-group child list. When every child decodes, every projected primitive belongs to that list and the list has no duplicates, the sketch exposes the ordered native ids in `fusion.geometry_child_ids`. Incomplete geometry retains its partial projection. This check proves geometry membership only. Constraints, dimensions, placement and edit behavior require separate evidence.

A hosted comparison matched all seven sketch geometry rosters across an extrusion, a parameter expression, a revolution and a scale with two input bodies. [Hosted comparison](https://github.com/TryUniCAD/Kit/actions/runs/44753881445/job/136348454494)

The reader also preserves the native point's fixed flag and exposes its origin flag in `fusion.point_is_origin`. A corner may share the origin’s coordinates and have a different fixed state. [Native solver observations](../../../../re/Fusion/Reconstruction/SketchConstraints/ConstraintModel.md)
