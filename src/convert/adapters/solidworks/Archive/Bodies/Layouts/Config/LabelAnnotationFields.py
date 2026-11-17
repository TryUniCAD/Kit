from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# current native field order supplies both directions without saved document values
KLabelAnnotationFields = MappingProxyType(
    {
        "moAuxLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
        ),
        "moDetailLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fcc", "u32"),
            NativeField("Scalar", "fc8", "i32"),
        ),
        "moDrViewLabelData_c": (
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
                        BodyValue=(NativeField("Node", "f50"),),
                        ModeValue="NotEquals",
                        MaskValue=-1,
                    ),
                ),
                ModeValue="Condition",
                MaskValue=1073741824,
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
        ),
        "moLabelDefs_c": (
            NativeField("Scalar", "f8", "i32"),
            NativeField("Scalar", "fc", "i32"),
            NativeField("Embed", "f18", "moDetailLabelData_c"),
            NativeField("Embed", "fe8", "moSectionLabelData_c"),
            NativeField("Embed", "f1e8", "moAuxLabelData_c"),
            NativeField("Embed", "f458", "utCharFormat_c"),
            NativeField("Embed", "f2b8", "moOrthoLabelData_c"),
            NativeField("Embed", "f388", "moMiscLabelData_c"),
        ),
        "moMiscLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
            NativeField("Scalar", "fcc", "i32"),
        ),
        "moOrthoLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "i32"),
            NativeField("Scalar", "fcc", "i32"),
        ),
        "moSectionLabelData_c": (
            NativeField("Base", "moDrViewLabelData_c"),
            NativeField("Scalar", "fc8", "f64"),
            NativeField("Scalar", "fd0", "f64"),
            NativeField("Scalar", "fd8", "f64"),
            NativeField("Scalar", "fe0", "i32"),
            NativeField("Scalar", "fe4", "i32"),
            NativeField("Scalar", "fec", "i32"),
            NativeField("Scalar", "ff0", "i32"),
            NativeField("Scalar", "fe8", "i32"),
        ),
    }
)
