from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# assembly manager rows retain their actual component chain and external file identities
KAsmMgrRefs = MappingProxyType(
    {
        "moChainComponent_c": (
            NativeField("Base", "moComponent_c"),
            NativeField("Node", "f20"),
            NativeField("Scalar", "f30", "u32"),
        ),
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
