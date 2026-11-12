from convert.formats.Fusion.MetaIndex import SegmentKind

KAssetPrefix = "FusionAssetName[Active]/"
KRootName = "Manifest.dat"
KPropertiesName = "Properties.dat"
KAssetName = KAssetPrefix + KRootName
KPreviewNames = ("Previews/big.png", "Previews/small.png")
KPartFolders = frozenset(
    (
        "Breps.BlobParts",
        "ProteinAssets.BlobParts",
        "Images.BlobParts",
        "OGS.BlobFolder",
        "DesignConfigurationTable.BlobParts",
    )
)
KCoreSegments = (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)
KMaxProperties = 1024
KMaxPreviewSize = 16 * 1024 * 1024
KMaxPreviewSide = 4096
