from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# native field order is shared by both archive directions without document supplied programs
KAssemblyFields = MappingProxyType(
    {
        "moAssyMassPropsCache_c": (
            NativeField("Scalar", "fc8", "f64"),
            NativeField(
                "Array",
                "f08",
                "u32",
                BodyValue=(
                    NativeField("Scalar", "hi", "u32"),
                    NativeField("Scalar", "lo", "u32"),
                    NativeField("Embed", "cache", "moBodyMassPropsCache_c"),
                ),
            ),
        ),
        "moBaseConfiguration_c.SerializeXmlData": (
            NativeField("Base", "moFeature_c.SerializeXmlData"),
        ),
        "moBodyMassPropsCache_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Scalar", "f18", "u32"),
            NativeField("Boolean", "f1c", "u8"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Text", "f238"),
            NativeField("Embed", "f28", "moMassProp_c"),
        ),
        "moConfigObject_c": (
            NativeField("Node", "f08"),
            NativeField("Node", "f10"),
            NativeField("Embed", "f28", "moReferencedConfiguration_c"),
            NativeField("Node", "f40"),
            NativeField("Embed", "f48", "moFeatherWeightChildrenCache_c"),
            NativeField(
                "Present",
                "has_f140",
                "i32",
                BodyValue=(NativeField("Embed", "f140", "mgXform_c.restore"),),
                CountValue="f140",
            ),
            NativeField("Embed", "f78", "suObList"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f148", "i32"),
            NativeField(
                "Present",
                "has_f170",
                "i32",
                BodyValue=(NativeField("Embed", "f170", "mgXform_c.restore"),),
                CountValue="f170",
            ),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Node", "fc0"),
                    NativeField("Node", "fc8"),
                ),
                ModeValue="NotCondition",
                MaskValue=1,
            ),
            NativeField("Text", "f178"),
            NativeField("Boolean", "f190", "u8"),
            NativeField("Embed", "f118", "suObList"),
            NativeField(
                "Mask",
                "conditions",
                BodyValue=(NativeField("Embed", "fd0", "suObList"),),
                MaskValue=512,
            ),
        ),
        "moConfig_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f14", "i32"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f20", "i32"),
            NativeField("Scalar", "f34", "i32"),
            NativeField("Scalar", "f38", "i32"),
            NativeField("Scalar", "f3c", "i32"),
            NativeField("Scalar", "f40", "i32"),
            NativeField("Text", "f48"),
            NativeField("Scalar", "f50", "i32"),
            NativeField("Scalar", "f58", "i32"),
            NativeField("Scalar", "f5c", "i32"),
            NativeField("Scalar", "f60", "i32"),
            NativeField("Scalar", "f64", "i32"),
            NativeField("Scalar", "f68", "i32"),
            NativeField("Scalar", "f6c", "i32"),
            NativeField("Scalar", "f70", "i32"),
            NativeField("Boolean", "f74", "u8"),
        ),
        "moConfiguration_c": (
            NativeField("Base", "moBaseConfiguration_c"),
            NativeField("Node", "fc48"),
            NativeField("Node", "fc50"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Node", "fca0"),
                    NativeField("Node", "fca8"),
                ),
                ModeValue="NotCondition",
                MaskValue=1,
            ),
            NativeField(
                "Array",
                "fce8",
                "i32",
                BodyValue=(NativeField("Node", "o"),),
                ModeValue="Positive",
            ),
            NativeField("Node", "fba8"),
            NativeField("Node", "fbb0"),
            NativeField("Scalar", "fbc0", "i32"),
            NativeField("Scalar", "fbc4", "i32"),
            NativeField("Node", "fbc8"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField("Fail", "moConfiguration_c visual-state callback"),
                ),
                ModeValue="Condition",
                MaskValue=1,
            ),
            NativeField("Node", "fce0"),
        ),
        "moFeatherWeightChildrenCache_c": (
            NativeField("Embed", "f08", "su_CObArray"),
            NativeField("Scalar", "f28", "u32"),
        ),
    }
)
