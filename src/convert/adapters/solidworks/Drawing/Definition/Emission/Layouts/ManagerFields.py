from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# empty drawing managers need explicit native owners while populated layer data remains unqualified
KManagerFields = MappingProxyType(
    {
        "moLayerMgr_c": (
            NativeField(
                "Array",
                "layers",
                "u32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
            NativeField("Node", "f08"),
            NativeField("Node", "f30"),
            NativeField("Node", "f20"),
            NativeField("Scalar", "f38", "i32"),
        ),
        "moLayerMask_c": (NativeField("Embed", "f08", "DrawingEmptyUIntArray"),),
        "DrawingEmptyUIntArray": (
            NativeField("Scalar", "n", "i32"),
            NativeField("Scalar", "f18", "i32"),
        ),
        "moBlockFolder_c": (NativeField("Base", "moFolder_c"),),
        "moMarkupCommentFolder_c": (NativeField("Base", "moFolder_c"),),
        "moAbsoluteRefPlnData_c": (
            NativeField("Base", "moRefPlnData_c.serializePlaneData"),
        ),
    }
)
