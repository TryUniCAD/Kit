from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# edge and face wrappers preserve their separate branch state and shared mapped references
KEdgeFields = MappingProxyType(
    {
        "moCompBEntRef_c": (
            NativeField("Base", "moCompRef_c"),
            NativeField("Scalar", "has_alias", "u8"),
            NativeField(
                "Branch",
                "has_alias",
                BodyValue=(
                    NativeField(
                        "Fail",
                        "fillet component reference alias",
                    ),
                ),
                ModeValue="Nonzero",
            ),
            NativeField("Node", "fe8"),
            NativeField("Node", "ff0", "moExtObject_c"),
        ),
        "moCompCompositeEdge_c": (
            NativeField("Base", "moCompBEntRef_c"),
            NativeField("Scalar", "f188", "i32"),
            NativeField(
                "Branch",
                "f188",
                BodyValue=(NativeField("Fail", "fillet composite edge mode"),),
                ModeValue="Nonzero",
            ),
            NativeField("Embed", "f158", "mgPoint_c.restore"),
            NativeField("Embed", "f170", "mgPoint_c.restore"),
            NativeField("Scalar", "f18c", "u32"),
            NativeField(
                "Array",
                "f130",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n140",
            ),
        ),
        "moCompEdge_c": (NativeField("Base", "moCompCompositeEdge_c"),),
        "moCompFace_c": (NativeField("Base", "moCompBEntRef_c"),),
        "moEdgeRef_c": (NativeField("Base", "moBEntRef_c"),),
    }
)
