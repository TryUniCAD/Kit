# the selected fresh part profile requires explicit authored instances of the twelve independently classified native folder types
KSystemFolders = frozenset(
    (
        "moCommentsFolder_c",
        "moDocsFolder_c",
        "moEnvFolder_c",
        "moEqnFolder_c",
        "moFavoriteFolder_c",
        "moHistoryFolder_c",
        "moMaterialFolder_c",
        "moInkMarkupFolder_c",
        "moSelectionSetFolder_c",
        "moSensorFolder_c",
        "moSolidBodyFolder_c",
        "moSurfaceBodyFolder_c",
    )
)

# nonfolder system nodes have independently documented derived constructors beyond their shared native feature base
KSystemExtras = frozenset(
    ("moDetailCabinet_c", "moRefPlane_c", "moOriginProfileFeature_c")
)

# folder registration binds semantic runtime caches while only the environment relationship appears in the configuration wire graph
KFolderCaches = {
    "f1e0": "moEnvFolder_c",
    "f1f0": "moDocsFolder_c",
    "f1f8": "moCommentsFolder_c",
    "f200": "moSensorFolder_c",
    "f218": "moFavoriteFolder_c",
    "f220": "moSelectionSetFolder_c",
    "f228": "moHistoryFolder_c",
    "f1500": "moSurfaceBodyFolder_c",
    "f1508": "moSolidBodyFolder_c",
}
