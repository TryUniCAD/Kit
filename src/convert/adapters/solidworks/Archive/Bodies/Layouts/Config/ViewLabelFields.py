from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# every concrete view label keeps the same raw base and conditional layer boundary
KViewLabelFields = (
    NativeField("Scalar", "f8", "i32"),
    NativeField("Scalar", "fc", "i32"),
    NativeField("Scalar", "f18", "i32"),
    NativeField("Scalar", "f14", "i32"),
    NativeField("Scalar", "f1c", "i32"),
    NativeField("Scalar", "f20", "i32"),
    NativeField("Scalar", "f24", "i32"),
    NativeField("Scalar", "f28", "i32"),
    NativeField("Scalar", "f44", "i32"),
    NativeField("Scalar", "f2c", "i32"),
    NativeField("Scalar", "f38", "i32"),
    NativeField("Scalar", "f48", "i16"),
    NativeField(
        "Branch",
        "",
        BodyValue=(
            NativeField(
                "Branch",
                "f48",
                BodyValue=(
                    NativeField("Fail", "moDrViewLabelData_c.f50 layer object"),
                ),
                ModeValue="NotEquals",
                MaskValue=-1,
            ),
        ),
        ModeValue="Condition",
        MaskValue=0x40000000,
    ),
    NativeField("Text", "f88"),
    NativeField("Text", "f90"),
    NativeField("Scalar", "f5c", "u32"),
    NativeField("Scalar", "f10", "i32"),
    NativeField("Scalar", "f58", "i32"),
    NativeField("Embed", "f98", "utCharFormat_c"),
    NativeField("Embed", "fa0", "utCharFormat_c"),
    NativeField("Embed", "f30", "utLineWidth_c.Serialize0"),
    NativeField("Embed", "f3c", "utLineWidth_c.Serialize0"),
    NativeField("Embed", "fa8", "utCharFormat_c"),
    NativeField("Embed", "fb0", "utCharFormat_c"),
    NativeField("Embed", "fb8", "utCharFormat_c"),
    NativeField("Embed", "fc0", "utCharFormat_c"),
)
