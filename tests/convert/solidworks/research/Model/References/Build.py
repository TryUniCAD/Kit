from __future__ import annotations

# separate wrapper allocations are required because native destruction owns both the wrapper and its component copy
KReferences = """
ReferenceNodes = [
    NewComponentPlane(
        plane=BaseGraph.planes["z"],
        component=BaseGraph.part["f990"],
        created_at=LoggedCreationTime(timestamps=()),
        principal_normal=(0.0, 0.0, 1.0),
    )
    for ReferenceIndex in range(2)
]
ReferenceDocument = StreamDoc(
    "resolved",
    {"base": BaseStoreMap.count, "context": BaseContext},
    ReferenceNodes,
)
StreamMap["Research/PlaneReferences"] = StoreResolved(
    ReferenceDocument, CodecReg, 19000, seed=BaseStoreMap
)
"""
