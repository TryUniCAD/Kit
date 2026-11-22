from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# ordinary mate members follow native serializer inheritance rather than document specific record rows
KMateFields = MappingProxyType(
    {
        "moMateParent": (
            NativeField("Base", "moModelFeature_c"),
            NativeField("Scalar", "f390", "i32"),
            NativeField("Scalar", "f394", "i32"),
            NativeField("Scalar", "f388", "i32"),
            NativeField(
                "Array",
                "f370",
                "u32",
                BodyValue=(NativeField("Scalar", "v", "i32"),),
                ModeValue="Positive",
            ),
        ),
        "moMate": (
            NativeField("Base", "moMateParent"),
            NativeField("Scalar", "f3b4", "u16"),
            NativeField("Scalar", "f3b8", "u16"),
            NativeField(
                "Present",
                "has_f3c0",
                "u8",
                BodyValue=(NativeField("Embed", "f3c0", "mgVector_c.restore"),),
            ),
            NativeField(
                "Array",
                "f3c8",
                "i32",
                BodyValue=(
                    NativeField("Scalar", "k", "i32"),
                    NativeField("Node", "o", "moRefWrapper_c"),
                ),
                ModeValue="Positive",
            ),
        ),
        "moMateNGeoms_c": (
            NativeField("Base", "moMate"),
            NativeField("Node", "f430"),
            NativeField(
                "Array",
                "f410",
                "i32",
                BodyValue=(NativeField("Node", "o", "moRefWrapper_c"),),
                ModeValue="Positive",
            ),
            NativeField(
                "Array",
                "f448",
                "u32",
                BodyValue=(NativeField("Node", "o", "suObList"),),
                ModeValue="Positive",
            ),
            NativeField("Node", "f470"),
            NativeField("Node", "f468"),
            NativeField("Node", "f478"),
            NativeField("Scalar", "f438", "u16"),
            NativeField("Boolean", "f480", "i32"),
            NativeField("Text", "f488"),
            NativeField("Text", "f490"),
        ),
        "moMate2Geoms_c": (NativeField("Base", "moMateNGeoms_c"),),
        "moMateCoincident": (NativeField("Base", "moMate2Geoms_c"),),
        "moMateParallel": (NativeField("Base", "moMate2Geoms_c"),),
        "moMatePerpendicular": (NativeField("Base", "moMate2Geoms_c"),),
        "moMateConcentric": (
            NativeField("Base", "moMate2Geoms_c"),
            NativeField("Scalar", "f4b8", "i32"),
            NativeField("Scalar", "f4c4", "i32"),
        ),
        "moMateDim_c": (
            NativeField("Base", "moMate2Geoms_c"),
            NativeField("Node", "f4b8", "moDisplayDim_c"),
            NativeField("Scalar", "f4c0", "u16"),
        ),
        "moMateDistanceDim_c": (
            NativeField("Base", "moMateDim_c"),
            NativeField("Scalar", "f4d8", "u16"),
            NativeField("Scalar", "f4dc", "i32"),
            NativeField("Scalar", "f4e0", "i32"),
            NativeField("Scalar", "f4f4", "i32"),
        ),
    }
)
