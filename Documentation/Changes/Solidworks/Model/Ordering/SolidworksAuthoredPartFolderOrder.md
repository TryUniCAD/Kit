# Explicit authored SOLIDWORKS part-folder order

The research part constructor accepts optional `presentation.folder_order`, an explicit sequence of the classified folder classes already named by `folder_names`. A non-null sequence must be an exact permutation. The constructor validates it before allocating IDs and builds the existing native graph in that order. Omitting it preserves the existing mapping-order behavior and output bytes.

Use the array when a neutral document carries an authored system-folder sequence across a JSON boundary. Sorting the object keys changes the order of the mapping. The constructor takes the order from the explicit array.

The disclosed paired drawing rehearsal exposed this issue: all eight native phases passed, while strict source/generated comparison failed on child system-tree order in all five states. The corrected child sequence is derived from the exact original independent Python recipe. Native qualification of the corrected candidate remains pending; held-out drawings remain sealed and the comparator is unchanged.

The guarded writer passed 19 fresh processes. Five prior pairs and the ordered pair each built twice with identical outputs. Seven invalid order requests failed before output. The run recorded zero runtime input-file access attempts. [Process checker](../../../../../re/tooling/sw2026/CheckPartFolderOrder.py)

The blind preparer admits the exact new 3,685-file source manifest as a separate closure. It retains the old manifest and does not inherit the old native discovery qualification for changed bytes. Existing packets remain immutable.

See the [construction evidence](../../../../../re/solidworks/records/PartFolderOrder2026.md) and [JSON ordering gotcha](../../../../Gotchas/Conversion/Solidworks/Model/Ordering/JsonObjectSortingChangesPartFolderOrder.md).
