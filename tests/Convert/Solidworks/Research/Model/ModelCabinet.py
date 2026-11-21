from __future__ import annotations

# annotation cabinets need separate coverage because their native base differs from ordinary folders
KAnnotations = """
CabinetNode = NewCabinet(
    name=NamePrefix + "annotations",
    owner=SystemOwner,
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
)
StreamMap["Research/SystemFeatures"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, [*FolderNodes, CabinetNode]), CodecReg, 19000
)
"""
