from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# external point owners must remain limited to the independently proved ordinary part archive context
KAnchorContext = (
    NativeField(
        "Branch",
        "model_is_part",
        OtherValue=(
            NativeField("Fail", "external point anchor requires ordinary part context"),
        ),
        ModeValue="Context",
    ),
    NativeField(
        "Branch",
        "conditions",
        BodyValue=(
            NativeField("Fail", "external point anchor alternate archive conditions"),
        ),
        ModeValue="Context",
    ),
    NativeField(
        "Branch",
        "ctx874",
        BodyValue=(
            NativeField("Fail", "external point anchor referenced configuration mode"),
        ),
        ModeValue="Context",
    ),
)

# point and dimension wrappers share the reference metadata following their actual target
KRefWrapperTailFields = (
    NativeField("Scalar", "f68", "u16"),
    NativeField("Node", "f60", "moComponent_c"),
    NativeField("Scalar", "f6c", "i32"),
    NativeField("Scalar", "f08", "i32"),
    NativeField("Scalar", "has_f10", "u16"),
    NativeField(
        "Branch",
        "has_f10",
        BodyValue=(NativeField("Embed", "f10", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "has_f18", "u16"),
    NativeField(
        "Branch",
        "has_f18",
        BodyValue=(NativeField("Embed", "f18", "mgXform_c.restore"),),
        ModeValue="Nonzero",
    ),
    NativeField("Scalar", "f0c", "i32"),
    NativeField("Scalar", "f20", "i32"),
    NativeField("Scalar", "f74", "i32"),
    NativeField("Scalar", "f78", "i32"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f50", "i32"),
    NativeField("Scalar", "f70", "i32"),
    NativeField("Scalar", "f34", "i32"),
    NativeField("Scalar", "f30", "i32"),
    NativeField("Scalar", "f98", "i32"),
    NativeField("Scalar", "f38", "i32"),
)


# source proven external point field order shares existing component and geometry codecs without saved payloads
KAnchorFields = MappingProxyType(
    {
        "sk.sgLogG2Dim.FUN_4c58b970": (
            *KAnchorContext,
            NativeField("Base", "sk.sgLogDim.Serialize"),
            NativeField("Node", "h1", "sgEntHandle"),
            NativeField("Node", "h2", "sgEntHandle"),
            NativeField("Scalar", "ff8", "u16"),
            NativeField("Scalar", "ffc", "u16"),
            NativeField("Node", "f108"),
            NativeField("Scalar", "f100", "u16"),
            NativeField("Scalar", "f110", "i32"),
            NativeField("Scalar", "f114", "i32"),
            NativeField("Scalar", "f118", "f64"),
            NativeField("Scalar", "f120", "f64"),
            NativeField("Node", "ext1", "sgEntHandle"),
            NativeField("Node", "ext2", "sgEntHandle"),
            NativeField("Node", "ext3", "sgEntHandle"),
            NativeField("Scalar", "f150", "u16"),
            NativeField("Scalar", "f154", "i32"),
        ),
        "moCompSketchEntHandle_c": (
            *KAnchorContext,
            NativeField("Base", "moCompFeature_c"),
            NativeField("Node", "f0f8", "sgEntHandle"),
            NativeField("Scalar", "f100", "u32"),
        ),
        "moPointBackedUpData_c": (
            *KAnchorContext,
            NativeField("Embed", "f08", "mgPoint_c.restore"),
        ),
        "moRefWrapper_c": (
            NativeField("Node", "f58", "moCompSketchEntHandle_c"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Fail", "anchor wrapper requires its component sketch selection"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=(
                    "compare",
                    ("NotEq",),
                    ("class_of", ("lookup", ("scope",), ("literal", "f58"))),
                    ("literal", "moCompSketchEntHandle_c"),
                ),
            ),
            *KRefWrapperTailFields,
        ),
        "moSketchExtRef_w": (
            *KAnchorContext,
            NativeField("Base", "moRefWrapper_c"),
            NativeField("Scalar", "fb0", "u16"),
            NativeField("Node", "fb8", "moPointBackedUpData_c"),
        ),
        "sgExtEnt_c": (
            *KAnchorContext,
            NativeField("Node", "f08", "moSketchExtRef_w"),
            NativeField("Node", "f10"),
            NativeField("Node", "f18", "moSkIntersectInfo_c"),
            NativeField("Node", "f20", "moSkIsoCurveInfo_c"),
            NativeField("Text", "f28"),
        ),
    }
)
