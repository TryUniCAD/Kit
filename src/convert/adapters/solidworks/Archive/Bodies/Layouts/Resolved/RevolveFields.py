from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# revolving feature archives require the measured axis selection end and angular display in the linked graph
KRevolveFields = MappingProxyType(
    {
        "moRevolution_c": (
            NativeField("Base", "moBodyFeature_c"),
            NativeField("Node", "f808", "moDisplayDim_c"),
            NativeField("Scalar", "f824", "u8"),
            NativeField("Node", "f810", "moDisplayDim_c"),
            NativeField("Scalar", "f820", "i32"),
            NativeField(
                "Branch",
                "",
                BodyValue=(
                    NativeField(
                        "Branch",
                        "ctx874",
                        BodyValue=(NativeField("Node", "f818", "suObList"),),
                        ModeValue="Context",
                    ),
                ),
                OtherValue=(NativeField("Node", "f818", "suObList"),),
                ModeValue="Condition",
                MaskValue=1,
            ),
            NativeField("Scalar", "f828", "i32"),
            NativeField("Scalar", "f870", "i32"),
            NativeField("Node", "f830", "moLineRef_w"),
            NativeField("Node", "f8d8", "moRevEndSpec_c"),
            NativeField("Scalar", "f8e8", "u8"),
        ),
        "moRevolutionThin_c": (
            NativeField("Base", "moRevolution_c"),
            NativeField("Node", "f8f0", "moThinSpec_c"),
        ),
        "moRevCut_c": (NativeField("Base", "moRevolution_c"),),
        "moThinSpec_c": (
            NativeField("Node", "f08", "moDisplayDim_c"),
            NativeField("Node", "f10", "moDisplayDim_c"),
            NativeField("Scalar", "f2c", "i32"),
            NativeField("Scalar", "f30", "f64"),
            NativeField("Scalar", "f38", "f64"),
            NativeField("Scalar", "f28", "i32"),
            NativeField("Scalar", "f40", "i32"),
            NativeField("Node", "f48", "moDisplayRadialDim_c"),
            NativeField("Scalar", "f50", "i32"),
            NativeField("Scalar", "f54", "i32"),
        ),
        "moRevEndSpec_c": (
            NativeField("Scalar", "f08", "i32"),
            NativeField("Scalar", "f138", "i32"),
            NativeField("Scalar", "f13c", "i32"),
            NativeField("Scalar", "f0c", "i32"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Node", "f118", "moRefWrapper_c"),
            NativeField("Node", "f120", "moRefWrapper_c"),
            NativeField("Node", "f128", "moPointRef_w"),
            NativeField("Node", "f130", "moPointRef_w"),
            NativeField("Scalar", "f38", "f64"),
            NativeField("Scalar", "f40", "f64"),
            NativeField("Scalar", "f140", "i32"),
            NativeField("Scalar", "f144", "i32"),
            NativeField("Node", "f18", "moDisplayDim_c"),
            NativeField("Node", "f20", "moDisplayDim_c"),
            NativeField("Node", "f28", "moDisplayDim_c"),
            NativeField("Node", "f30", "moDisplayDim_c"),
        ),
        "moCurveRef_w": (
            NativeField("Base", "moRefWrapper_c"),
            NativeField("Scalar", "fb0", "f64"),
            NativeField("Scalar", "fb8", "f64"),
        ),
        "moLineRef_w": (
            NativeField("Base", "moCurveRef_w"),
            NativeField("Embed", "fc8", "mgPoint_c.restore"),
            NativeField("Embed", "fe0", "mgVector_c.restore"),
            NativeField("Scalar", "ff8", "u8"),
        ),
    }
)
