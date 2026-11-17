from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native field order is shared by both archive directions without document supplied programs
KReferenceFields = MappingProxyType(
    {
        "moChainComponent_c": (
            NativeField("Base", "moComponent_c"),
            NativeField("Node", "f20"),
            NativeField("Scalar", "f30", "u32"),
        ),
        "moComponent_c": (NativeField("Node", "owner"),),
        "moContextChainComponent_c": (
            NativeField("Base", "moChainComponent_c"),
            NativeField("Node", "f40"),
            NativeField("Scalar", "f48", "i32"),
        ),
        "moExtFeatureList_c": (
            NativeField(
                "Array",
                "f08",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
                ModeValue="Unsigned",
            ),
        ),
        "moExtFeature_c": (
            NativeField("Base", "moExtObjectInterface_c.FUN_4c179410"),
            NativeField("Node", "f50"),
            NativeField("Scalar", "f58", "i32"),
            NativeField("Validate", "OrdinaryExternalFeature"),
        ),
        "moExtObjectInterface_c.FUN_4c179410": (
            NativeField("Embed", "f10", "moSharedFileDef_c"),
            NativeField("Embed", "f18", "moReferencedConfiguration_c"),
            NativeField("Scalar", "f40", "u8"),
            NativeField("Scalar", "f44", "i32"),
            NativeField(
                "Branch",
                "plain_cstring_names",
                BodyValue=(NativeField("Node", "f38"),),
                OtherValue=(NativeField("Text", "f38"),),
                ModeValue="NotContext",
            ),
        ),
        "moReferenceChain_c": (
            NativeField("Branch", "", ModeValue="Condition", MaskValue=2147483649),
            NativeField("Scalar", "f24", "u16"),
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Scalar", "has_f18", "i32"),),
                ModeValue="Condition",
                MaskValue=2147483649,
            ),
            NativeField("Node", "f08"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Embed", "f40", "moReferencedConfiguration_c"),
        ),
    }
)
