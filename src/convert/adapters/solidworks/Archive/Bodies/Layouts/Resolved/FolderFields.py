from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current resolved owner field order comes from proven serializer rules rather than saved programs
KFolderFields = MappingProxyType(
    {
        "moCommentsFolder_c": (NativeField("Base", "moFolder_c"),),
        "moDetailCabinet_c": (
            NativeField("Base", "moModelFeature_c"),
            NativeField("Embed", "f368", "rf.suObArray"),
            NativeField("Scalar", "f370", "f64"),
            NativeField("Scalar", "f378", "f64"),
            NativeField("Embed", "f388", "rf.suObArray"),
            NativeField(
                "Array",
                "f3d8",
                "i32",
                BodyValue=(NativeField("Fail", "alternate moDetailCabinet_c f3d8"),),
                CountValue="n3d8",
            ),
            NativeField("Scalar", "f3f0", "i32"),
        ),
        "moDocsFolder_c": (NativeField("Base", "moFolder_c"),),
        "moEqnFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Base", "moFeature_c.FUN_4bb2b240"),
        ),
        "moFavoriteFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Embed", "f3c8", "rf.suObArray"),
            NativeField("Embed", "f3e8", "rf.suObArray"),
            NativeField("Scalar", "f408", "i32"),
        ),
        "moHistoryFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Embed", "f3c8", "rf.suObArray"),
        ),
        "moInkMarkupFolder_c": (NativeField("Base", "moFolder_c"),),
        "moMaterialFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Text", "f378"),
            NativeField("Scalar", "flags380", "u32"),
        ),
        "moSelectionSetFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Embed", "f3c0", "rf.suObArray"),
            NativeField("Scalar", "f3e0", "i32"),
        ),
        "moSensorFolder_c": (NativeField("Base", "moFolder_c"),),
        "moSolidBodyFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Scalar", "f37c", "i32"),
            NativeField("Scalar", "f380", "i32"),
            NativeField("Node", "f388", "moMaterialFolder_c"),
            NativeField("Node", "f3d8", "moCutListSortOptions_c"),
        ),
        "moSurfaceBodyFolder_c": (
            NativeField("Base", "moFolder_c"),
            NativeField("Scalar", "f37c", "i32"),
            NativeField("Scalar", "f380", "i32"),
            NativeField("Node", "f388", "moMaterialFolder_c"),
            NativeField("Node", "f3d8", "moCutListSortOptions_c"),
        ),
    }
)
