from __future__ import annotations

# independent authored inputs prevent a fixed saved configuration or definition from satisfying this check
KBuild = """
ConfigNames = [NamePrefix + str(IndexValue) for IndexValue in range(CountCfg)]
ManagerNode = NewManager(
    owner=NativeObj("moPart_c"),
    names=ConfigNames,
    date_code=2026306,
    parasolid_version=370108,
    updated_at=1700000000,
)
DocumentDef = NewPartDef(
    density_kg_m3=DensityVal,
    drafting_standard="moISO_c",
    detail_flags=(0, 3, 48),
    tessellation=(20, 15, 3, False),
    system_preference_7a=False,
    journal_name=NamePrefix + " journal",
)
StreamMap = {
    "Contents/CMgr": StoreRooted(
        StreamDoc("rooted", {"base": 1}, [ManagerNode]), CodecReg, 19000
    ),
    "Contents/Definition": WritePartDef(registry=CodecReg, document=DocumentDef),
}
"""
