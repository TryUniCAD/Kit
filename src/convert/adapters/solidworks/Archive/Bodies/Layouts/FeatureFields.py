from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native field order is shared by both archive directions without document supplied programs
KFeatureFields = MappingProxyType(
    {
        "moConcept_c.SerializeLWData": (
            NativeField("Base", "moNode_c.SerializeLWData"),
            NativeField("Scalar", "has_list68", "i32"),
            NativeField(
                "Branch",
                "has_list68",
                BodyValue=(NativeField("Embed", "f68", "moNodeList_c.Serialize"),),
                ModeValue="Nonzero",
            ),
            NativeField("Node", "f78"),
        ),
        "moEntVisProp_c": (
            NativeField("Scalar", "f00", "u16"),
            NativeField("Scalar", "f02", "u16"),
            NativeField("Scalar", "f04", "u8"),
            NativeField("Embed", "f08", "moVisProp_c"),
        ),
        "moFeature_c": (
            NativeField("Base", "moNode_c.SerializeNode"),
            NativeField("Scalar", "f298", "i32"),
            NativeField("Scalar", "f28c", "i32"),
            NativeField("Scalar", "f29c", "u32"),
            NativeField("Scalar", "has_f1e8", "u8"),
            NativeField(
                "Branch",
                "has_f1e8",
                BodyValue=(NativeField("Text", "f1e8"),),
                ModeValue="Nonzero",
            ),
            NativeField("Scalar", "f2a8", "i32"),
            NativeField("Scalar", "f2b8", "i32"),
            NativeField("Scalar", "f2bc", "i32"),
            NativeField("Scalar", "f2b0", "i32"),
            NativeField("Scalar", "f1e0", "f64"),
            NativeField("Scalar", "f2b4", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Scalar", "cond1_a", "i32"),
                    NativeField("Scalar", "cond1_b", "i32"),
                ),
                ModeValue="Condition",
                MaskValue=1,
            ),
            NativeField("Node", "f258"),
            NativeField("Text", "f1f8"),
            NativeField("Scalar", "f1f4", "u8"),
            NativeField("Embed", "f2c8", "moEntVisProp_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "",
                        BodyValue=(NativeField("Scalar", "pe_noise", "u8"),),
                        ModeValue="ConditionsClear",
                    ),
                ),
                ModeValue="PeNoise",
            ),
            NativeField("Scalar", "f2ec", "i32"),
            NativeField("Scalar", "fa8", "i32"),
            NativeField("Node", "f2f0"),
            NativeField("Scalar", "f208", "u32"),
            NativeField("Scalar", "f300", "u8"),
            NativeField("Scalar", "f301", "u8"),
            NativeField("Scalar", "f318", "i32"),
            NativeField("Scalar", "hidden", "i32"),
            NativeField("Scalar", "f30c", "i32"),
            NativeField("Scalar", "f2a4", "i32"),
            NativeField("Scalar", "f2a0", "i32"),
            NativeField("Scalar", "f98", "u16"),
            NativeField("Scalar", "f2ac", "i32"),
            NativeField("Scalar", "f344", "i32"),
            NativeField(
                "Virtual",
                "",
                BodyValue=(NativeField("Virtual", "", MaskValue=1000),),
                ModeValue="Flag",
                MaskValue=1016,
            ),
        ),
        "moFeature_c.SerializeXmlData": (
            NativeField(
                "Branch",
                "",
                BodyValue=(NativeField("Text", "f200"),),
                ModeValue="Condition",
                MaskValue=98465,
            ),
        ),
        "moNode_c.SerializeLWData": (
            NativeField("Node", "f18"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f28", "u32"),
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f2c", "i32"),
            NativeField("Text", "f20"),
        ),
        "moNode_c.SerializeNode": (
            NativeField("Virtual", "", MaskValue=1208),
            NativeField("Virtual", "", MaskValue=1216),
        ),
        "moVisProp_c": (
            NativeField("Scalar", "f00", "u32"),
            NativeField("Scalar", "f04", "u16"),
            NativeField("Embed", "f08", "utLineWidth_c.Serialize2"),
        ),
        "utLineWidth_c.Serialize2": (
            NativeField("Scalar", "f06", "i16"),
            NativeField("Scalar", "f00", "f32"),
        ),
    }
)
