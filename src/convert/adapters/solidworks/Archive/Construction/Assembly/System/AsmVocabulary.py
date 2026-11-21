# named assembly construction allocates these qualified folders before the annotation cabinet and ordered principal planes
KAsmEarly = (
    "moCommentsFolder_c",
    "moFavoriteFolder_c",
    "moHistoryFolder_c",
    "moSelectionSetFolder_c",
    "moSensorFolder_c",
    "moLiveSectionFolder_c",
    "moDocsFolder_c",
)

# late assembly folders retain their separate resolved order after the native annotation cabinet without changing allocation ownership
KAsmLate = ("moEnvFolder_c", "moInkMarkupFolder_c", "moEqnFolder_c")

# the complete ordinary assembly folder vocabulary excludes part material and body folders and includes native live section planes
KAsmFolders = (*KAsmEarly, *KAsmLate)
