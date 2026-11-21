# Face role map uses previously allocated rows

Allocating all kernel downstream IDs first makes every adjacent face ID available in the partition. Applying that complete inventory to a new face reference's initial role map changes its meaning.

The native face constructor looks up rows already inserted into the standalone cache as it builds each face's inline IDs. Even a real adjacent surface has no role-map value until its row exists. The new row becomes available after construction, so the first ordinary face's map is empty. The validator can rebuild an invalid reference later using the then-current lookup.

Walk the linked faces in order. Build the initial role map from preceding insertions and register the current face after taking that snapshot. Keep the validator's later replacements separate. The [source trace](../../../../../../re/solidworks/records/DownstreamFreshFaceRows2026.md) and [generated control](../../../../../../re/solidworks/records/DownstreamGeneratedCollector2026.md) show both boundaries.
