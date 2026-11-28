# Value dimensions require concrete object nodes

Sketch dimension arrays have different archive ownership. A one-geometry value entry uses an object reference; a logical-one entry embeds its fields. Copying the logical constraint's representation into a value array loses its concrete class identity.

The active 2026 `ResolvedSketch` grammar defines `val_g1` entries with `xo("d", "sgValG1Dim")`, while `log_g1` uses an embedded logical-one schema. The initial radial graph at source `0b1ef9d6e6d882215b246d5a03ea39e2cc9d320a` supplied `dimension.f` to the value entry. The typed writer correctly rejected it as a non-node before output, with `archive object must be an archive node`. No radial candidate was generated or measured.

Keep the actual `sgCircleDim` node in the value array and its owned mutable field mapping on that node. This retains concrete class/tag identity and allows its independent parameter, handle, owner and shared-map references to serialize normally. Keep the logical constraint's embedded form where that separate schema requires it. Do not loosen the typed writer to accept a field dictionary as an object.

See [the grammar](../../../../../re/tooling/sw2026/serial/defs/ResolvedSketch.py), [2026 class/construction evidence](../../../../../re/solidworks/records/CurvedSketchConstruction2026.md) and [the failed remote process job](https://github.com/TryUniCAD/Kit/actions/runs/43852378978/job/133248082337). The corrected graph requires its own process and native measurements.
