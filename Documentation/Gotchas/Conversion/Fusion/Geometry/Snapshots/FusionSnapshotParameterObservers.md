# Parameter observers use the parameter table order

The authored cuboid's name lookup map correctly resolves all seven parameters. Its entries can occur in an order different from the parameter table's children. On two constructor archives, the observer list followed the lookup map and placed the width model parameter before the independent depth driver.

The strict saved-cuboid path expects the lookup helper to observe the parameter table first and then its seven child parameters in table order. Each observer uses rank zero. A freshly generated snapshot moves the archive into that saved read path, where the original observer list was rejected despite having the correct membership and parameter values.

Derive the observer list from the actual authored parameter roles in creation order. Retain the lookup map, the parameter table and all authored driver expressions. Changes to the old snapshot-free generator are not needed. See the [independent snapshot generator](../../../../../Changes/Research/Encoder/FusionGeneratedCuboidSnapshot.md).
