# Explicit authored SOLIDWORKS part-folder order

The research part constructor accepts optional `presentation.folder_order`, an explicit sequence of the classified folder classes already named by `folder_names`. A non-null sequence must be an exact permutation. The constructor validates it before allocating IDs and builds the existing native graph in that order. Omitting it preserves the existing mapping-order behavior and output bytes.

Use this when a neutral document carries an authored system-folder sequence across a JSON boundary. Sorted JSON object keys cannot represent that sequence reliably. The shared constructor consumes the array; it does not read a saved document or choose a per-case native order.

The disclosed paired drawing rehearsal exposed this issue: all eight native phases passed, while strict source/generated comparison failed on child system-tree order in all five states. The corrected child sequence is derived from the exact original independent Python recipe. Native qualification of the corrected candidate remains pending; held-out drawings remain sealed and the comparator is unchanged.

[The process checker](../../../../re/tooling/sw2026/CheckPartFolderOrder.py) verifies the real guarded writer in 19 fresh processes: five prior pairs twice with identical complete reports and artifacts, the ordered pair twice, and seven invalid-order requests that produce no output. The authorized local run recorded zero runtime input-file access attempts. This is integration evidence, not native acceptance.

The blind preparer admits the exact new 3,685-file source manifest as a separate closure. It retains the old manifest and does not inherit the old native discovery qualification for changed bytes. Existing packets remain immutable.

See the [construction evidence](../../../../re/solidworks/records/PartFolderOrder2026.md) and [JSON ordering gotcha](../../../Gotchas/Conversion/Solidworks/Model/Ordering/JsonObjectSortingChangesPartFolderOrder.md). This research addition does not change the production read-only adapter or establish full CAD acceptance.
