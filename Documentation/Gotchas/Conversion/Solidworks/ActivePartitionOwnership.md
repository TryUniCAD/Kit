# Active partition ownership

A SOLIDWORKS part can contain a readable Parasolid model even when its active body cannot be decoded. Two V8 fasteners contain readable packets under `ResolvedFeatures`. The gas inlet contains a readable `GhostPartition`. Treating the first readable model as the finished part previously allowed all three through the FreeCAD B-rep corpus check.

Use the selected configuration’s `Partition` stream for the active body. Keep its B-rep unavailable when the reader cannot resolve its topology. The integration checks confirm both the readable secondary stream and the unsupported active partition on the same input. [Hosted comparison](https://github.com/TryUniCAD/Kit/actions/runs/44752639846/job/136344158215)
