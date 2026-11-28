# Native sketch handles retain sparse array indices

A line's array slot, persistent ID, creation ID and position in a public entity tuple are different identities. Removing a deleted native row from geometry must not compact the handle namespace.

The disclosed native corner rectangle retains five line rows: a deleted slot zero followed by four actual live edges. Their persistent IDs in stored order are `1,4,3,2`. The H/V relations and cached region refer to actual live slots 1–4. The generated rectangle instead has four live slots 0–3 with persistent IDs `1,2,3,4`. Treating those native indices as emitted tuple positions binds constraints to the wrong edges or makes a correct rectangle appear incomplete.

The pinned 2026 `sgEntHandle::isDeleted` resolves the actual entity and tests entity `+0x54` bit 0. `moSketchRegion_c::hasSameBoundaryEntities` compares actual handle membership and concrete kinds rather than a dense geometric ordering. A cached region is not another authored contour.

Keep the original row index on each live line. Preserve supported deleted rows and region owners/handles as source metadata, join all constraints in their actual index domain, and translate to public tuple positions only when emitting references. Derive stable public line IDs from persistent IDs. Reject unqualified retired histories or incomplete/foreign region membership before claiming a typed projection.

[Array-count prerequisite](../NativeSketchArrayCounts.md) · [Exact source/reader proof](../../../../../../re/solidworks/records/SdkOriginCoincidenceRead2026.md) · [Process receipt](../../../../../../re/solidworks/measurements/2026/SdkOriginCoincidenceRead01.json)
