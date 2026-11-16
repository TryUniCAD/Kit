# Derived collection counts reject assignment

An existing research archive collection may expose mapping-style fields while deriving its count lazily from the actual item sequence. Treating it as a plain dictionary and assigning a new count after appending is incorrect.

`Sketch.empty_object_list()` returns a `DerivedFields` mapping whose `n` field is computed from `items`. The circle display list already uses this object. The first radial process run at source `5c2dbe56331fcff85978081021236d363e89e8bd` appended a display and then assigned `n`, causing `ConstructionError: cannot replace derived field n` before serialization. No radial native file was generated and no acceptance was earned.

Mutate the owned `items` sequence and let the existing count provider observe it. Preserve the derived mapping and its identity rather than replacing it with a copied dictionary or deleting its guard. The same policy keeps counts dependent on graph topology during later serialization.

Evidence: [remote process job](https://github.com/TryUniCAD/Kit/actions/runs/43851652771/job/133245440376), one failed new radial process case with 183 other passing cases. The corrected source still requires its own remote run and native measurements; this failure is independent of SOLIDWORKS behavior.
