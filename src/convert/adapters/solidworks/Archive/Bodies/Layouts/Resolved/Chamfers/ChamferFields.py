from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the ordinary chamfer stores separate selected edges and linear and angular dimensions
KChamferFields = MappingProxyType(
    {
        "rf.suObArray": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Node", "o"),),
                CountValue="n",
            ),
        ),
        "moPartConfiguration_c.SerializeMBSMDataObjects": (
            NativeField(
                "Array",
                "fcd8",
                "u32",
                BodyValue=(
                    NativeField("Fail", "chamfer without a cold inline body map"),
                ),
                CountValue="n",
            ),
        ),
        "Chamfer_c": (
            NativeField("Base", "moBodyFeature_c"),
            NativeField("Embed", "f880", "moFilletSIdKeeper_c"),
            NativeField("Node", "f888", "suObList"),
            NativeField("Node", "f890", "suObList"),
            NativeField("Node", "f898", "suObList"),
            NativeField("Node", "f810", "moDisplayDim_c"),
            NativeField("Node", "f818", "moDisplayAngularDim_c"),
            NativeField("Node", "f820", "moDisplayDistanceDim_c"),
            NativeField("Scalar", "f860", "u8"),
            NativeField("Scalar", "f8a0", "u8"),
            NativeField("Scalar", "f878", "u8"),
            NativeField("Node", "f8a8", "moCompEdge_c"),
            NativeField("Node", "f8b0", "moCompFace_c"),
            NativeField("Node", "f8b8", "moCompFace_c"),
            NativeField("Scalar", "f8c0", "i32"),
            NativeField("Embed", "f8c8", "su_CDWordArray"),
            NativeField("Node", "f828", "moDisplayDistanceDim_c"),
            NativeField("Node", "f830", "moDisplayDistanceDim_c"),
            NativeField("Node", "f838", "moDisplayDistanceDim_c"),
            NativeField("Node", "f840", "moCompEdge_c"),
            NativeField("Node", "f848", "moCompEdge_c"),
            NativeField("Node", "f850", "moCompEdge_c"),
            NativeField("Node", "f858", "moCompVertex_c"),
            NativeField("Scalar", "f87c", "u8"),
            NativeField("Scalar", "has_f808", "i32"),
            NativeField(
                "Branch",
                "has_f808",
                BodyValue=(NativeField("Fail", "chamfer alternate reference"),),
                ModeValue="Nonzero",
            ),
            NativeField("Scalar", "f8f0", "u8"),
        ),
    }
)
