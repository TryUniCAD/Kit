from __future__ import annotations

# system folder coverage preserves native ownership across all currently recovered concrete folder classes
KFolders = """
ClassNames = (
    "moCommentsFolder_c",
    "moDocsFolder_c",
    "moEnvFolder_c",
    "moEqnFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moMaterialFolder_c",
    "moNotesAreaFtrFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moSolidBodyFolder_c",
    "moSurfaceBodyFolder_c",
)
SystemOwner = NativeObj("moPart_c")
SystemOwner.f["f9d0"] = NewRelations(owner=SystemOwner)
FolderNodes = NewFolders(
    names={ClassName: NamePrefix + ClassName for ClassName in ClassNames},
    owner=SystemOwner,
    allocator=IdAllocator,
    date_code=2026306,
    parasolid_version=370108,
    created_at=1700000000,
)
"""
