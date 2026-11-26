from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# labels and detail definitions share raw character and print width formats
KFormatAnnotationFields = MappingProxyType(
    {
        "utCharFormat_c": (
            NativeField("Text", "f08"),
            NativeField("Scalar", "f10", "f64"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f20", "f64"),
            NativeField("Scalar", "f30", "u32"),
            NativeField("Scalar", "f28", "f64"),
            NativeField("Scalar", "f38", "f64"),
            NativeField("Scalar", "f40", "f64"),
            NativeField("Scalar", "f48", "f64"),
            NativeField("Scalar", "f50", "f64"),
            NativeField("Scalar", "f58", "u32"),
        ),
        "utLineWidthPrintData_c": (
            NativeField("Scalar", "f8", "f32"),
            NativeField("Scalar", "fc", "f32"),
            NativeField("Scalar", "f10", "f32"),
            NativeField("Scalar", "f14", "f32"),
            NativeField("Scalar", "f18", "f32"),
            NativeField("Scalar", "f1c", "f32"),
            NativeField("Scalar", "f20", "f32"),
            NativeField("Scalar", "f24", "f32"),
        ),
    }
)
