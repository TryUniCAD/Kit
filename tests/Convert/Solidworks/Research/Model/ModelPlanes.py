from __future__ import annotations

# principal plane coverage protects frame orientation and persistent identifiers from unrelated graph changes
KPlanes = """
IdAllocator = PersistentIds()
PlaneNodes = NewPlanes(
    names={AxisName: NamePrefix + AxisName for AxisName in ("x", "y", "z")},
    owner=NativeObj("moPart_c"),
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
    retain_construction_flag=True,
)
StreamMap["Research/PrincipalPlanes"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, list(PlaneNodes.values())), CodecReg, 19000
)
NextPlaneId = IdAllocator.next_id
"""
